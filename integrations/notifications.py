"""
Push Notification Integration for claude-on-the-go

Supports multiple notification services:
- Pushover: Simple push API with high priority support
- ntfy.sh: Free, self-hostable push service
- Telegram: Bot API for Telegram notifications

All notifiers are async and handle errors gracefully.
"""

import asyncio
import os
from abc import ABC, abstractmethod
from typing import Optional
from urllib.parse import quote

import httpx


class Notifier(ABC):
    """Base class for notification services"""

    @abstractmethod
    async def send(
        self,
        title: str,
        message: str,
        priority: str = "normal",
        url: Optional[str] = None,
    ) -> bool:
        """
        Send a push notification.

        Args:
            title: Notification title
            message: Notification message body
            priority: Priority level (low, normal, high)
            url: Optional URL to open on notification click

        Returns:
            True if notification sent successfully, False otherwise
        """
        pass


class PushoverNotifier(Notifier):
    """
    Pushover push notification service.

    Requires:
        - PUSHOVER_USER_KEY: User/group key
        - PUSHOVER_APP_TOKEN: Application token (optional, uses default if not set)
    """

    API_URL = "https://api.pushover.net/1/messages.json"

    def __init__(self, user_key: str, app_token: Optional[str] = None):
        """
        Initialize Pushover notifier.

        Args:
            user_key: Pushover user or group key
            app_token: Pushover application token (optional)
        """
        self.user_key = user_key
        # Use default app token or custom one
        self.app_token = app_token or os.getenv(
            "PUSHOVER_APP_TOKEN", "azGDORePK8gMaC0QOYAMyEEuzJnyUi"  # Default token
        )

    async def send(
        self,
        title: str,
        message: str,
        priority: str = "normal",
        url: Optional[str] = None,
    ) -> bool:
        """Send Pushover notification"""
        # Map priority to Pushover values (-2=lowest, -1=low, 0=normal, 1=high, 2=emergency)
        priority_map = {
            "low": -1,
            "normal": 0,
            "high": 1,
        }

        payload = {
            "token": self.app_token,
            "user": self.user_key,
            "title": title,
            "message": message,
            "priority": priority_map.get(priority, 0),
        }

        if url:
            payload["url"] = url
            payload["url_title"] = "Open Claude"

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(self.API_URL, data=payload)
                return response.status_code == 200
        except Exception as e:
            print(f"[PUSHOVER] Error sending notification: {e}")
            return False


class NtfyNotifier(Notifier):
    """
    ntfy.sh push notification service.

    Supports both ntfy.sh cloud and self-hosted instances.

    Requires:
        - NTFY_TOPIC: Unique topic name
        - NTFY_SERVER: Server URL (default: https://ntfy.sh)
        - NTFY_TOKEN: Optional authentication token
    """

    def __init__(
        self,
        topic: str,
        server: str = "https://ntfy.sh",
        token: Optional[str] = None,
    ):
        """
        Initialize ntfy notifier.

        Args:
            topic: Unique topic name (create your own)
            server: ntfy server URL
            token: Optional authentication token for private topics
        """
        self.topic = topic
        self.server = server.rstrip("/")
        self.token = token

    async def send(
        self,
        title: str,
        message: str,
        priority: str = "normal",
        url: Optional[str] = None,
    ) -> bool:
        """Send ntfy notification"""
        # Map priority to ntfy values (1=min, 3=default, 5=max)
        priority_map = {
            "low": "2",
            "normal": "3",
            "high": "5",
        }

        headers = {
            "Title": title,
            "Priority": priority_map.get(priority, "3"),
            "Tags": "terminal,claude",
        }

        if url:
            headers["Click"] = url

        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(
                    f"{self.server}/{self.topic}",
                    content=message.encode("utf-8"),
                    headers=headers,
                )
                return response.status_code == 200
        except Exception as e:
            print(f"[NTFY] Error sending notification: {e}")
            return False


class TelegramNotifier(Notifier):
    """
    Telegram Bot API notification service.

    Requires:
        - TELEGRAM_BOT_TOKEN: Bot token from @BotFather
        - TELEGRAM_CHAT_ID: Your chat ID (get from @userinfobot)
    """

    API_URL = "https://api.telegram.org/bot{token}/sendMessage"

    def __init__(self, bot_token: str, chat_id: str):
        """
        Initialize Telegram notifier.

        Args:
            bot_token: Bot token from @BotFather
            chat_id: Chat ID to send messages to
        """
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.api_url = self.API_URL.format(token=bot_token)

    async def send(
        self,
        title: str,
        message: str,
        priority: str = "normal",
        url: Optional[str] = None,
    ) -> bool:
        """Send Telegram notification"""
        # Format message with title
        text = f"*{title}*\n\n{message}"

        payload = {
            "chat_id": self.chat_id,
            "text": text,
            "parse_mode": "Markdown",
        }

        # Add inline button if URL provided
        if url:
            payload["reply_markup"] = {"inline_keyboard": [[{"text": "Open Claude", "url": url}]]}

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(self.api_url, json=payload)
                return response.status_code == 200
        except Exception as e:
            print(f"[TELEGRAM] Error sending notification: {e}")
            return False


class NotificationService:
    """
    Unified notification service that manages multiple notifiers.

    Automatically configures notifiers based on environment variables.
    """

    def __init__(self):
        """Initialize notification service with available notifiers"""
        self.notifiers: list[Notifier] = []

        # Configure Pushover
        pushover_key = os.getenv("PUSHOVER_USER_KEY")
        if pushover_key:
            pushover_token = os.getenv("PUSHOVER_APP_TOKEN")
            self.notifiers.append(PushoverNotifier(pushover_key, pushover_token))
            print("[NOTIFICATIONS] Pushover notifier enabled")

        # Configure ntfy
        ntfy_topic = os.getenv("NTFY_TOPIC")
        if ntfy_topic:
            ntfy_server = os.getenv("NTFY_SERVER", "https://ntfy.sh")
            ntfy_token = os.getenv("NTFY_TOKEN")
            self.notifiers.append(NtfyNotifier(ntfy_topic, ntfy_server, ntfy_token))
            print("[NOTIFICATIONS] ntfy notifier enabled")

        # Configure Telegram
        telegram_token = os.getenv("TELEGRAM_BOT_TOKEN")
        telegram_chat = os.getenv("TELEGRAM_CHAT_ID")
        if telegram_token and telegram_chat:
            self.notifiers.append(TelegramNotifier(telegram_token, telegram_chat))
            print("[NOTIFICATIONS] Telegram notifier enabled")

        if not self.notifiers:
            print("[NOTIFICATIONS] No notifiers configured (set env vars to enable)")

    @property
    def enabled(self) -> bool:
        """Check if any notifiers are configured"""
        return len(self.notifiers) > 0

    async def send(
        self,
        title: str,
        message: str,
        priority: str = "normal",
        url: Optional[str] = None,
    ) -> bool:
        """
        Send notification through all configured services.

        Args:
            title: Notification title
            message: Notification message body
            priority: Priority level (low, normal, high)
            url: Optional URL to open on notification click

        Returns:
            True if at least one notification was sent successfully
        """
        if not self.notifiers:
            return False

        # Send to all notifiers in parallel
        tasks = [notifier.send(title, message, priority, url) for notifier in self.notifiers]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Check if at least one succeeded
        success = any(r is True for r in results if not isinstance(r, Exception))

        if success:
            print(f"[NOTIFICATIONS] Sent: {title}")
        else:
            print(f"[NOTIFICATIONS] Failed to send: {title}")

        return success

    async def notify_claude_prompt(self, session_url: str) -> bool:
        """
        Send notification when Claude is waiting for user input.

        Args:
            session_url: URL to open Claude session

        Returns:
            True if notification sent successfully
        """
        return await self.send(
            title="Claude needs your input",
            message="Tap to continue your Claude session",
            priority="high",
            url=session_url,
        )

    async def notify_command_complete(self, command: str, duration_seconds: float) -> bool:
        """
        Send notification when a long-running command completes.

        Args:
            command: Command that completed
            duration_seconds: How long the command took

        Returns:
            True if notification sent successfully
        """
        duration_str = (
            f"{duration_seconds:.1f}s" if duration_seconds < 60 else f"{duration_seconds/60:.1f}m"
        )

        return await self.send(
            title="Command completed",
            message=f"{command}\n\nTook {duration_str}",
            priority="normal",
        )


# Example usage
if __name__ == "__main__":
    import sys

    async def test_notifications():
        """Test notification services"""
        service = NotificationService()

        if not service.enabled:
            print("No notifiers configured!")
            print("\nSet environment variables:")
            print("  PUSHOVER_USER_KEY=your_key")
            print("  NTFY_TOPIC=your_topic")
            print("  TELEGRAM_BOT_TOKEN=your_token TELEGRAM_CHAT_ID=your_chat_id")
            sys.exit(1)

        # Test notification
        success = await service.send(
            title="Test Notification",
            message="This is a test from claude-on-the-go",
            priority="normal",
            url="http://localhost:8001",
        )

        if success:
            print("\n✅ Test notification sent successfully!")
        else:
            print("\n❌ Failed to send test notification")
            sys.exit(1)

    asyncio.run(test_notifications())
