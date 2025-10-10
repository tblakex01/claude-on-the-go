"""
Configuration Management - Framework-agnostic settings

Uses pydantic-settings for environment variable loading with validation.
Provides sensible defaults for all settings.
"""

import os
from pathlib import Path
from typing import Annotated

try:
    from pydantic import Field, field_validator
    from pydantic_settings import BaseSettings, SettingsConfigDict
except ImportError:
    raise ImportError("pydantic-settings is required. Install with: pip install pydantic-settings")


class Config(BaseSettings):
    """Application configuration loaded from environment variables."""

    # Server settings
    BACKEND_PORT: Annotated[int, Field(ge=1024, le=65535)] = 8000
    FRONTEND_PORT: Annotated[int, Field(ge=1024, le=65535)] = 8001
    BACKEND_HOST: str = "127.0.0.1"  # LAN-only by default for security
    HOST: str = "127.0.0.1"  # Alias for BACKEND_HOST for backward compatibility

    # Claude CLI
    CLAUDE_CODE_PATH: str = "claude"

    # Session management
    SQLITE_PATH: str | None = None
    SESSION_TIMEOUT_HOURS: Annotated[int, Field(ge=0)] = 1

    # Security
    ENABLE_AUTH: bool = False
    AUTH_TOKEN: str | None = None
    MAX_CONNECTIONS: Annotated[int, Field(ge=1)] = 1

    # Rate limiting
    RATE_LIMIT_MESSAGES: Annotated[int, Field(ge=1)] = 10
    RATE_LIMIT_BYTES: Annotated[int, Field(ge=1000)] = 100000

    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_REDACTION: bool = True

    # Features
    ENABLE_CLIPBOARD_SYNC: bool = True
    CLIPBOARD_SYNC_INTERVAL: Annotated[float, Field(ge=0.1)] = 1.0

    # PTY flow control
    PTY_HIGH_WATERMARK: Annotated[int, Field(ge=10000)] = 100000
    PTY_LOW_WATERMARK: Annotated[int, Field(ge=1000)] = 10000

    # CORS settings (for legacy compatibility)
    ALLOWED_ORIGINS: str = "http://localhost:8001,http://127.0.0.1:8001"

    # Environment detection
    ENV: str = "development"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",  # Ignore extra environment variables
    )

    @field_validator("HOST")
    @classmethod
    def sync_host(cls, v: str, info) -> str:
        """Sync HOST with BACKEND_HOST if BACKEND_HOST is set."""
        # Use BACKEND_HOST if it was explicitly set
        backend_host = info.data.get("BACKEND_HOST")
        if backend_host and backend_host != "127.0.0.1":
            return backend_host
        return v

    @field_validator("PTY_LOW_WATERMARK")
    @classmethod
    def validate_watermarks(cls, v: int, info) -> int:
        """Ensure low watermark is less than high watermark."""
        # Note: This validator only has access to previously validated fields
        # The full watermark validation happens in validate_config()
        if v <= 0:
            raise ValueError("PTY_LOW_WATERMARK must be positive")
        return v

    @field_validator("CLAUDE_CODE_PATH")
    @classmethod
    def validate_claude_path(cls, v: str) -> str:
        """Validate that Claude CLI path exists if it's an absolute path."""
        # Only validate if it's an absolute path
        # Relative paths will be resolved by shell PATH
        if v.startswith("/") or v.startswith("~"):
            expanded = Path(v).expanduser()
            if not expanded.exists():
                raise ValueError(
                    f"Claude CLI not found at {expanded}. "
                    "Set CLAUDE_CODE_PATH to the correct path."
                )
        return v

    @field_validator("SQLITE_PATH")
    @classmethod
    def validate_sqlite_path(cls, v: str | None) -> str | None:
        """Validate SQLite path and ensure parent directory exists."""
        if v is None:
            return v

        # Expand user and resolve path
        path = Path(v).expanduser().resolve()

        # Ensure parent directory exists
        parent = path.parent
        if not parent.exists():
            try:
                parent.mkdir(parents=True, exist_ok=True)
            except Exception as e:
                raise ValueError(f"Cannot create directory {parent}: {e}")

        return str(path)

    @field_validator("AUTH_TOKEN")
    @classmethod
    def validate_auth_token(cls, v: str | None, info) -> str | None:
        """Ensure auth token is set if authentication is enabled."""
        # Access ENABLE_AUTH from values if it exists
        values_data = info.data
        if values_data.get("ENABLE_AUTH") and not v:
            raise ValueError("AUTH_TOKEN must be set when ENABLE_AUTH is true")
        return v

    @field_validator("LOG_LEVEL")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        """Validate log level is a valid Python logging level."""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        v_upper = v.upper()
        if v_upper not in valid_levels:
            raise ValueError(f"Invalid LOG_LEVEL: {v}. Must be one of {valid_levels}")
        return v_upper

    def validate_config(self) -> None:
        """
        Validate configuration after all fields are loaded.

        This allows cross-field validation that can't be done in field validators.
        """
        # Validate watermarks
        if self.PTY_LOW_WATERMARK >= self.PTY_HIGH_WATERMARK:
            raise ValueError(
                f"PTY_LOW_WATERMARK ({self.PTY_LOW_WATERMARK}) must be less than "
                f"PTY_HIGH_WATERMARK ({self.PTY_HIGH_WATERMARK})"
            )

        # Validate ports don't conflict
        if self.BACKEND_PORT == self.FRONTEND_PORT:
            raise ValueError(
                f"BACKEND_PORT and FRONTEND_PORT cannot be the same ({self.BACKEND_PORT})"
            )

    def is_production(self) -> bool:
        """Check if running in production mode."""
        return self.ENV.lower() == "production"

    def get_allowed_origins(self) -> list[str]:
        """Parse ALLOWED_ORIGINS into a list."""
        return [origin.strip() for origin in self.ALLOWED_ORIGINS.split(",")]

    def get_session_timeout_seconds(self) -> int:
        """Get session timeout in seconds."""
        return self.SESSION_TIMEOUT_HOURS * 3600


# Global config instance
# This will be loaded from .env file when imported
try:
    config = Config()
    config.validate_config()
except Exception as e:
    # If config fails to load, provide helpful error message
    print(f"Configuration error: {e}")
    print("Please check your .env file and environment variables.")
    raise


# Export config and Config class
__all__ = ["Config", "config"]
