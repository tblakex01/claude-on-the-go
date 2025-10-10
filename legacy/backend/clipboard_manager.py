"""
Clipboard Manager for Claude-onTheGo
Handles bidirectional clipboard synchronization between Mac and mobile devices
"""

import asyncio
import hashlib
import subprocess
from typing import Callable, Optional


class ClipboardManager:
    """Manages clipboard synchronization between Mac and mobile device"""

    def __init__(self, sync_interval: float = 1.0):
        """
        Initialize clipboard manager

        Args:
            sync_interval: How often to check for clipboard changes (seconds)
        """
        self.sync_interval = sync_interval
        self.last_content_hash: Optional[str] = None
        self.monitor_task: Optional[asyncio.Task] = None
        self.on_change_callback: Optional[Callable] = None

    def _get_clipboard_content(self) -> Optional[str]:
        """
        Get current clipboard content from macOS

        Returns:
            Clipboard content as string, or None if error
        """
        try:
            result = subprocess.run(["pbpaste"], capture_output=True, text=True, timeout=1.0)
            if result.returncode == 0:
                return result.stdout
        except Exception as e:
            print(f"[CLIPBOARD] Error reading clipboard: {e}")
        return None

    def _set_clipboard_content(self, text: str) -> bool:
        """
        Set clipboard content on macOS

        Args:
            text: Content to set

        Returns:
            True if successful, False otherwise
        """
        try:
            process = subprocess.Popen(["pbcopy"], stdin=subprocess.PIPE, text=True)
            process.communicate(input=text, timeout=1.0)
            return process.returncode == 0
        except Exception as e:
            print(f"[CLIPBOARD] Error setting clipboard: {e}")
            return False

    def _hash_content(self, content: str) -> str:
        """
        Generate hash of clipboard content for change detection

        Args:
            content: Content to hash

        Returns:
            SHA256 hash of content
        """
        return hashlib.sha256(content.encode("utf-8")).hexdigest()

    async def set_from_remote(self, text: str):
        """
        Set Mac clipboard from remote device (phone)

        Args:
            text: Clipboard content from phone
        """
        print(f"[CLIPBOARD] Setting Mac clipboard from remote ({len(text)} chars)")

        # Set the clipboard
        success = self._set_clipboard_content(text)

        if success:
            # Update our hash so we don't sync it back
            self.last_content_hash = self._hash_content(text)
            print("[CLIPBOARD] Mac clipboard updated from remote")
        else:
            print("[CLIPBOARD] Failed to set Mac clipboard")

    async def _monitor_loop(self):
        """Monitor Mac clipboard for changes and trigger callback"""
        print(f"[CLIPBOARD] Starting monitor (checking every {self.sync_interval}s)")

        # Initialize with current clipboard content
        initial_content = self._get_clipboard_content()
        if initial_content:
            self.last_content_hash = self._hash_content(initial_content)

        while True:
            try:
                await asyncio.sleep(self.sync_interval)

                # Get current clipboard
                current_content = self._get_clipboard_content()

                if current_content is None:
                    continue

                # Check if changed
                current_hash = self._hash_content(current_content)

                if current_hash != self.last_content_hash:
                    print(f"[CLIPBOARD] Mac clipboard changed ({len(current_content)} chars)")
                    self.last_content_hash = current_hash

                    # Trigger callback to sync to remote
                    if self.on_change_callback:
                        await self.on_change_callback(current_content)

            except Exception as e:
                print(f"[CLIPBOARD] Monitor error: {e}")
                await asyncio.sleep(1.0)

    def start_monitoring(self, on_change: Callable):
        """
        Start monitoring Mac clipboard for changes

        Args:
            on_change: Async callback function called when clipboard changes
                      Signature: async def on_change(text: str)
        """
        if self.monitor_task and not self.monitor_task.done():
            print("[CLIPBOARD] Monitor already running")
            return

        self.on_change_callback = on_change
        self.monitor_task = asyncio.create_task(self._monitor_loop())
        print("[CLIPBOARD] Monitor started")

    def stop_monitoring(self):
        """Stop monitoring clipboard"""
        if self.monitor_task:
            self.monitor_task.cancel()
            print("[CLIPBOARD] Monitor stopped")

    def get_current_content(self) -> Optional[str]:
        """
        Get current clipboard content without monitoring

        Returns:
            Current clipboard content
        """
        return self._get_clipboard_content()
