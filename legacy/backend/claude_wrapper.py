"""
Claude process wrapper with pexpect and watermark flow control
Spawns claude CLI and manages output with buffer thresholds
"""

import asyncio
import time
from collections import deque
from typing import Awaitable, Callable, Optional

import pexpect


class FlowControl:
    """Manages watermark-based flow control for PTY output"""

    def __init__(self, high_watermark: int = 100_000, low_watermark: int = 10_000):
        """
        Initialize flow control

        Args:
            high_watermark: Pause reading at this buffer size (bytes)
            low_watermark: Resume reading at this buffer size (bytes)
        """
        self.high_watermark = high_watermark
        self.low_watermark = low_watermark
        self.buffer_size = 0
        self.paused = False

    def add_bytes(self, count: int) -> bool:
        """
        Add bytes to buffer, check if should pause

        Returns:
            True if should pause reading
        """
        self.buffer_size += count

        if not self.paused and self.buffer_size >= self.high_watermark:
            self.paused = True
            return True

        return False

    def remove_bytes(self, count: int) -> bool:
        """
        Remove bytes from buffer, check if should resume

        Returns:
            True if should resume reading
        """
        self.buffer_size = max(0, self.buffer_size - count)

        if self.paused and self.buffer_size <= self.low_watermark:
            self.paused = False
            return True

        return False

    def reset(self):
        """Reset flow control state"""
        self.buffer_size = 0
        self.paused = False


class ClaudeWrapper:
    """Wraps claude CLI process with pexpect and flow control"""

    def __init__(
        self,
        command: str = "claude",
        high_watermark: int = 100_000,
        low_watermark: int = 10_000,
        max_restarts: int = 5,
        restart_window: int = 60,
    ):
        """
        Initialize claude wrapper

        Args:
            command: Command to spawn claude (e.g., "claude" or "claude --provider anthropic")
            high_watermark: Pause at this buffer size
            low_watermark: Resume at this buffer size
            max_restarts: Max restarts in restart_window
            restart_window: Time window for restart limit (seconds)
        """
        self.command = command
        self.process: Optional[pexpect.spawn] = None
        self.flow_control = FlowControl(high_watermark, low_watermark)
        self.running = False
        self.output_callback: Optional[Callable[[str], Awaitable[None]]] = None

        # Restart tracking
        self.max_restarts = max_restarts
        self.restart_window = restart_window
        self.restart_times: deque = deque(maxlen=max_restarts)

        # Read buffer
        self.read_task: Optional[asyncio.Task] = None

    def can_restart(self) -> bool:
        """Check if we can restart based on rate limiting"""
        now = time.time()

        # Remove old restart times outside window
        while self.restart_times and (now - self.restart_times[0]) > self.restart_window:
            self.restart_times.popleft()

        # Check if we're under the limit
        return len(self.restart_times) < self.max_restarts

    def record_restart(self):
        """Record a restart attempt"""
        self.restart_times.append(time.time())

    def spawn(self):
        """Spawn the claude process"""
        if self.process is not None:
            try:
                self.process.close(force=True)
            except:
                pass

        # Spawn with pexpect
        self.process = pexpect.spawn(
            self.command,
            encoding="utf-8",
            echo=False,
            timeout=None,
        )

        # Set reasonable window size (will be updated by client)
        self.process.setwinsize(24, 80)

        self.running = True
        self.flow_control.reset()

    async def start(self, output_callback: Callable[[str], Awaitable[None]]):
        """
        Start claude process and begin reading output

        Args:
            output_callback: Async function to call with output chunks
        """
        self.output_callback = output_callback

        if not self.can_restart():
            raise RuntimeError(f"Too many restarts ({self.max_restarts} in {self.restart_window}s)")

        self.spawn()
        self.record_restart()

        # Start reading task
        self.read_task = asyncio.create_task(self._read_loop())

    async def _read_loop(self):
        """Main read loop with flow control"""
        read_size = 4096

        while self.running and self.process is not None:
            try:
                # Check if flow control says to pause
                if self.flow_control.paused:
                    await asyncio.sleep(0.01)  # Wait 10ms before checking again
                    continue

                # Try non-blocking read
                try:
                    output = self.process.read_nonblocking(size=read_size, timeout=0)

                    if output:
                        # Check flow control
                        should_pause = self.flow_control.add_bytes(len(output))

                        if should_pause:
                            print(f"[FLOW CONTROL] Paused at {self.flow_control.buffer_size} bytes")

                        # Send to callback
                        if self.output_callback:
                            await self.output_callback(output)

                except pexpect.TIMEOUT:
                    # No data available, sleep briefly
                    await asyncio.sleep(0.01)

                except pexpect.EOF:
                    # Process ended
                    print("[CLAUDE] Process ended (EOF)")
                    self.running = False
                    break

            except Exception as e:
                print(f"[CLAUDE] Read error: {e}")
                self.running = False
                break

        # Process died, attempt restart if allowed
        if self.can_restart():
            print("[CLAUDE] Attempting auto-restart...")
            await self.start(self.output_callback)
        else:
            print("[CLAUDE] Max restarts reached, giving up")

    async def send_input(self, text: str):
        """
        Send input to claude process

        Args:
            text: Text to send (should already be sanitized by caller)
        """
        if self.process is not None and self.running:
            try:
                # Use send() instead of sendline() - don't add newline
                # The terminal emulator will send \r when Enter is pressed
                self.process.send(text)
            except Exception as e:
                print(f"[CLAUDE] Failed to send input: {e}")

    async def send_control(self, char: str):
        """
        Send control character (e.g., 'c' for Ctrl+C)

        Args:
            char: Control character (a-z)
        """
        if self.process is not None and self.running:
            try:
                if char.lower() == "c":
                    self.process.sendintr()
                elif char.lower() == "d":
                    self.process.sendeof()
                else:
                    # Send as control character
                    control_char = chr(ord(char.lower()) - ord("a") + 1)
                    self.process.send(control_char)
            except Exception as e:
                print(f"[CLAUDE] Failed to send control: {e}")

    def notify_bytes_sent(self, count: int):
        """
        Notify flow control that bytes were sent to client

        Args:
            count: Number of bytes sent
        """
        should_resume = self.flow_control.remove_bytes(count)

        if should_resume:
            print(f"[FLOW CONTROL] Resumed at {self.flow_control.buffer_size} bytes")

    async def stop(self):
        """Stop the claude process gracefully"""
        self.running = False

        if self.read_task:
            self.read_task.cancel()
            try:
                await self.read_task
            except asyncio.CancelledError:
                pass

        if self.process is not None:
            try:
                self.process.close(force=True)
            except:
                pass

            self.process = None

    def is_alive(self) -> bool:
        """Check if process is alive"""
        return self.process is not None and self.process.isalive() and self.running

    def set_window_size(self, rows: int, cols: int):
        """
        Update PTY window size

        Args:
            rows: Number of rows
            cols: Number of columns
        """
        if self.process is not None and self.running:
            try:
                self.process.setwinsize(rows, cols)
                print(f"[CLAUDE] Window size updated to {rows}x{cols}")
            except Exception as e:
                print(f"[CLAUDE] Failed to set window size: {e}")
