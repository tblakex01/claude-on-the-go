"""
Integrations package for claude-on-the-go

Provides third-party service integrations including push notifications,
remote access, and QR code generation.
"""

from .notifications import (
    NotificationService,
    NtfyNotifier,
    PushoverNotifier,
    TelegramNotifier,
)
from .prompt_detector import PromptDetector

__all__ = [
    "NotificationService",
    "PushoverNotifier",
    "NtfyNotifier",
    "TelegramNotifier",
    "PromptDetector",
]
