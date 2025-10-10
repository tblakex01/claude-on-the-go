"""
PTY Manager - Framework-agnostic pseudoterminal management for Claude CLI

This module provides a clean interface for spawning and managing Claude CLI
processes in a pseudoterminal with watermark-based flow control.
"""

import asyncio
import time
from collections import deque
from typing import Optional

import pexpect


class FlowControl:
    """
    Manages watermark-based flow control for PTY output.

    Prevents buffer overflow by pausing reads when buffer size exceeds
    high watermark and resuming when it drops below low watermark.
    """

    def __init__(self, high_watermark: int = 100_000, low_watermark: int = 10_000):
        """
        Initialize flow control.

        Args:
            high_watermark: Pause reading at this buffer size (bytes)
            low_watermark: Resume reading at this buffer size (bytes)
        """
        if low_watermark >= high_watermark:
            raise ValueError("low_watermark must be less than high_watermark")

        self.high_watermark = high_watermark
        self.low_watermark = low_watermark
        self.buffer_size = 0
        self.paused = False

    def add_bytes(self, count: int) -> bool:
        """
        Add bytes to buffer and check if reading should pause.

        Args:
            count: Number of bytes to add

        Returns:
            True if reading should pause, False otherwise
        """
        self.buffer_size += count

        if not self.paused and self.buffer_size >= self.high_watermark:
            self.paused = True
            return True

        return False

    def remove_bytes(self, count: int) -> bool:
        """
        Remove bytes from buffer and check if reading should resume.

        Args:
            count: Number of bytes to remove

        Returns:
            True if reading should resume, False otherwise
        """
        self.buffer_size = max(0, self.buffer_size - count)

        if self.paused and self.buffer_size <= self.low_watermark:
            self.paused = False
            return True

        return False

    def reset(self) -> None:
        """Reset flow control state."""
        self.buffer_size = 0
        self.paused = False


class PTYManager:
    """
    Manages pseudoterminal for Claude CLI process.

    Provides async interface for spawning, reading from, and writing to
    a Claude CLI process with built-in flow control and auto-restart.
    """

    def __init__(
        self,
        command: str = "claude",
        args: list[str] | None = None,
        high_watermark: int = 100_000,
        low_watermark: int = 10_000,
        max_restarts: int = 5,
        restart_window: int = 60,
    ):
        """
        Initialize PTY manager.

        Args:
            command: Command to spawn (e.g., "claude" or path to binary)
            args: Optional command arguments
            high_watermark: Pause reading at this buffer size (bytes)
            low_watermark: Resume reading at this buffer size (bytes)
            max_restarts: Maximum number of restarts within restart_window
            restart_window: Time window for restart limiting (seconds)
        """
        self.command = command
        self.args = args or []
        self.process: Optional[pexpect.spawn] = None
        self.flow_control = FlowControl(high_watermark, low_watermark)
        self._running = False

        # Restart rate limiting
        self.max_restarts = max_restarts
        self.restart_window = restart_window
        self.restart_times: deque = deque(maxlen=max_restarts)

        # Read loop task
        self._read_task: Optional[asyncio.Task] = None
        self._output_queue: asyncio.Queue = asyncio.Queue()

    def _can_restart(self) -> bool:
        """Check if restart is allowed based on rate limiting."""
        now = time.time()

        # Remove old restart times outside the window
        while self.restart_times and (now - self.restart_times[0]) > self.restart_window:
            self.restart_times.popleft()

        # Check if we're under the limit
        return len(self.restart_times) < self.max_restarts

    def _record_restart(self) -> None:
        """Record a restart attempt."""
        self.restart_times.append(time.time())

    async def spawn(self) -> bool:
        """
        Spawn Claude process in PTY.

        Returns:
            True if spawn was successful, False otherwise
        """
        # Close existing process if any
        if self.process is not None:
            try:
                self.process.close(force=True)
            except Exception:
                pass

        # Check restart rate limit
        if not self._can_restart():
            raise RuntimeError(f"Too many restarts ({self.max_restarts} in {self.restart_window}s)")

        try:
            # Build full command
            full_command = self.command
            if self.args:
                full_command = f"{self.command} {' '.join(self.args)}"

            # Spawn with pexpect
            self.process = pexpect.spawn(
                full_command,
                encoding="utf-8",
                echo=False,
                timeout=None,
            )

            # Set default window size (can be updated via resize())
            self.process.setwinsize(24, 80)

            self._running = True
            self.flow_control.reset()
            self._record_restart()

            return True

        except Exception as e:
            print(f"[PTY] Failed to spawn process: {e}")
            self.process = None
            self._running = False
            return False

    async def _read_loop(self) -> None:
        """
        Internal read loop that continuously reads from PTY.

        Respects flow control watermarks and handles process lifecycle.
        """
        read_size = 4096

        while self._running and self.process is not None:
            try:
                # Check if flow control says to pause
                if self.flow_control.paused:
                    await asyncio.sleep(0.01)
                    continue

                # Try non-blocking read
                try:
                    output = self.process.read_nonblocking(size=read_size, timeout=0)

                    if output:
                        # Update flow control
                        should_pause = self.flow_control.add_bytes(len(output))

                        if should_pause:
                            print(
                                f"[PTY] Flow control paused at {self.flow_control.buffer_size} bytes"
                            )

                        # Put output in queue for consumers
                        await self._output_queue.put(output)

                except pexpect.TIMEOUT:
                    # No data available, sleep briefly
                    await asyncio.sleep(0.01)

                except pexpect.EOF:
                    # Process ended
                    print("[PTY] Process ended (EOF)")
                    self._running = False
                    break

            except Exception as e:
                print(f"[PTY] Read error: {e}")
                self._running = False
                break

        # Signal end of output
        await self._output_queue.put(None)

    async def start_reading(self) -> None:
        """
        Start background task to read from PTY.

        Output can be consumed via read_output() method.
        """
        if self._read_task is None or self._read_task.done():
            if not self._running:
                success = await self.spawn()
                if not success:
                    raise RuntimeError("Failed to spawn process")

            self._read_task = asyncio.create_task(self._read_loop())

    async def send_input(self, data: str) -> None:
        """
        Send input to Claude process.

        Args:
            data: Text to send to process (should be sanitized by caller)

        Raises:
            RuntimeError: If process is not running
        """
        if self.process is None or not self._running:
            raise RuntimeError("Process is not running")

        try:
            self.process.send(data)
        except Exception as e:
            print(f"[PTY] Failed to send input: {e}")
            raise

    async def send_control(self, char: str) -> None:
        """
        Send control character to process.

        Args:
            char: Control character (e.g., 'c' for Ctrl+C, 'd' for Ctrl+D)

        Raises:
            RuntimeError: If process is not running
        """
        if self.process is None or not self._running:
            raise RuntimeError("Process is not running")

        try:
            char_lower = char.lower()

            if char_lower == "c":
                self.process.sendintr()
            elif char_lower == "d":
                self.process.sendeof()
            else:
                # Send as control character (Ctrl+A = 1, Ctrl+B = 2, etc.)
                control_char = chr(ord(char_lower) - ord("a") + 1)
                self.process.send(control_char)

        except Exception as e:
            print(f"[PTY] Failed to send control character: {e}")
            raise

    async def read_output(self, timeout: float = 0.1) -> bytes:
        """
        Read output from Claude process (non-blocking).

        Args:
            timeout: Maximum time to wait for output (seconds)

        Returns:
            Output bytes, or empty bytes if no output available
        """
        try:
            output = await asyncio.wait_for(self._output_queue.get(), timeout=timeout)
            if output is None:
                # End of stream
                return b""
            return output.encode("utf-8") if isinstance(output, str) else output
        except asyncio.TimeoutError:
            return b""

    def notify_bytes_sent(self, count: int) -> None:
        """
        Notify flow control that bytes were sent to client.

        This allows flow control to resume reading if buffer has drained
        below the low watermark.

        Args:
            count: Number of bytes sent to client
        """
        should_resume = self.flow_control.remove_bytes(count)

        if should_resume:
            print(f"[PTY] Flow control resumed at {self.flow_control.buffer_size} bytes")

    async def resize(self, rows: int, cols: int) -> None:
        """
        Resize PTY terminal window.

        Args:
            rows: Number of terminal rows
            cols: Number of terminal columns
        """
        if self.process is None or not self._running:
            return

        try:
            self.process.setwinsize(rows, cols)
        except Exception as e:
            print(f"[PTY] Failed to resize terminal: {e}")

    async def close(self) -> None:
        """Close PTY and terminate Claude process gracefully."""
        self._running = False

        # Cancel read task
        if self._read_task is not None:
            self._read_task.cancel()
            try:
                await self._read_task
            except asyncio.CancelledError:
                pass
            self._read_task = None

        # Close process
        if self.process is not None:
            try:
                self.process.close(force=True)
            except Exception:
                pass
            self.process = None

    @property
    def is_alive(self) -> bool:
        """Check if Claude process is still running."""
        return self.process is not None and self.process.isalive() and self._running

    @property
    def pid(self) -> int | None:
        """Get process ID of running Claude process."""
        if self.process is not None:
            return self.process.pid
        return None
