"""
Configuration management for Claude-on-the-Go.
Loads settings from environment variables with secure defaults.
"""

import os
from typing import List


class Config:
    """Application configuration loaded from environment variables."""

    # Security settings
    ALLOWED_ORIGINS: List[str] = os.getenv(
        "ALLOWED_ORIGINS", "http://localhost:8001,http://127.0.0.1:8001"
    ).split(",")

    MAX_CONNECTIONS: int = int(os.getenv("MAX_CONNECTIONS", "1"))
    ENABLE_AUTH: bool = os.getenv("ENABLE_AUTH", "false").lower() == "true"
    AUTH_TOKEN: str = os.getenv("AUTH_TOKEN", "")

    # Network settings - auto-detect if not specified
    BACKEND_HOST: str = os.getenv("BACKEND_HOST", "0.0.0.0")
    BACKEND_PORT: int = int(os.getenv("BACKEND_PORT", "8000"))
    FRONTEND_PORT: int = int(os.getenv("FRONTEND_PORT", "8001"))

    # Rate limiting
    RATE_LIMIT_MESSAGES: int = int(os.getenv("RATE_LIMIT_MESSAGES", "10"))
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
