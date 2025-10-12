"""
Configuration management for Claude-on-the-Go.
Loads settings from environment variables with secure defaults.
"""

import logging
import os
import socket
from typing import List

logger = logging.getLogger(__name__)


def _get_default_host() -> str:
    """
    Auto-detect local IP address for secure binding (LAN only, never 0.0.0.0).

    Returns first active non-localhost IP, or 127.0.0.1 if none found.
    Can be overridden by BACKEND_HOST env var (use with caution).
    """
    env_host = os.getenv("BACKEND_HOST")
    if env_host:
        # Allow explicit override (including 0.0.0.0 for advanced users)
        if env_host == "0.0.0.0":  # nosec B104 - String comparison, not binding
            logger.warning(
                "[SECURITY WARNING] Binding to 0.0.0.0 exposes service to all network interfaces!"
            )
            logger.warning(
                "[SECURITY WARNING] Only use this on trusted networks or behind a firewall."
            )
        return env_host  # Return user-specified host (validated above)

    # Auto-detect first active local IP
    try:
        hostname = socket.gethostname()
        addr_infos = socket.getaddrinfo(hostname, None)

        for addr_info in addr_infos:
            ip = addr_info[4][0]
            # Return first non-localhost IPv4 address
            if ip != "127.0.0.1" and ":" not in ip:
                return ip
    except Exception:
        # Socket detection can fail safely - fallback to 127.0.0.1 below
        pass

    # Fallback to localhost (secure default)
    return "127.0.0.1"


class Config:
    """Application configuration loaded from environment variables."""

    # Security settings
    ALLOWED_ORIGINS: List[str] = os.getenv(
        "ALLOWED_ORIGINS", "http://localhost:8001,http://127.0.0.1:8001"
    ).split(",")

    MAX_CONNECTIONS: int = int(os.getenv("MAX_CONNECTIONS", "1"))
    ENABLE_AUTH: bool = os.getenv("ENABLE_AUTH", "false").lower() == "true"
    AUTH_TOKEN: str = os.getenv("AUTH_TOKEN", "")

    # Network settings - auto-detect local IP for security (no 0.0.0.0 by default)
    BACKEND_HOST: str = _get_default_host()
    BACKEND_PORT: int = int(os.getenv("BACKEND_PORT", "8000"))
    FRONTEND_PORT: int = int(os.getenv("FRONTEND_PORT", "8001"))

    # Rate limiting
    # Increased to 100 msg/sec to support real-time typing (each keystroke = 1 message)
    RATE_LIMIT_MESSAGES: int = int(os.getenv("RATE_LIMIT_MESSAGES", "100"))
    RATE_LIMIT_BYTES: int = int(os.getenv("RATE_LIMIT_BYTES", "100000"))

    # Logging
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_REDACTION: bool = os.getenv("LOG_REDACTION", "true").lower() == "true"

    # Claude CLI configuration
    CLAUDE_COMMAND: str = os.getenv("CLAUDE_COMMAND", "claude")

    # Feature flags
    ENABLE_CLIPBOARD_SYNC: bool = os.getenv("ENABLE_CLIPBOARD_SYNC", "true").lower() == "true"
    CLIPBOARD_SYNC_INTERVAL: float = float(os.getenv("CLIPBOARD_SYNC_INTERVAL", "1.0"))

    @classmethod
    def validate(cls) -> None:
        """Validate configuration and raise if invalid."""
        if cls.ENABLE_AUTH and not cls.AUTH_TOKEN:
            raise ValueError("AUTH_TOKEN must be set when ENABLE_AUTH is true")

        if cls.MAX_CONNECTIONS < 1:
            raise ValueError("MAX_CONNECTIONS must be at least 1")

        if cls.RATE_LIMIT_MESSAGES < 1:
            raise ValueError("RATE_LIMIT_MESSAGES must be at least 1")

        if cls.RATE_LIMIT_BYTES < 1000:
            raise ValueError("RATE_LIMIT_BYTES must be at least 1000")

    @classmethod
    def is_production(cls) -> bool:
        """Check if running in production mode."""
        return os.getenv("ENV", "development").lower() == "production"


# Validate configuration on module import
Config.validate()
