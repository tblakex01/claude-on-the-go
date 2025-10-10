"""
Authentication manager for optional token-based auth.
"""

import secrets
from typing import Optional

from .validator import validate_auth_token


class AuthManager:
    """Manages authentication for WebSocket connections."""

    def __init__(self, enabled: bool = False, token: Optional[str] = None):
        """
        Initialize authentication manager.

        Args:
            enabled: Whether authentication is enabled
            token: The expected authentication token
        """
        self.enabled = enabled
        self._token = token

        if enabled and not token:
            raise ValueError("Authentication enabled but no token provided")

    def verify(self, provided_token: Optional[str]) -> bool:
        """
        Verify an authentication token.

        Args:
            provided_token: The token to verify

        Returns:
            True if authentication succeeds or is disabled, False otherwise
        """
        if not self.enabled:
            return True

        if not provided_token:
            return False

        return validate_auth_token(provided_token, self._token)

    @staticmethod
    def generate_token(length: int = 32) -> str:
        """
        Generate a secure random token.

        Args:
            length: Length of the token in bytes

        Returns:
            Hex-encoded random token
        """
        return secrets.token_hex(length)

    def set_token(self, token: str) -> None:
        """
        Update the authentication token.

        Args:
            token: The new token
        """
        if not token:
            raise ValueError("Token cannot be empty")
        self._token = token

    def enable(self, token: Optional[str] = None) -> None:
        """
        Enable authentication.

        Args:
            token: Optional new token. If not provided, uses existing token.
        """
        if token:
            self.set_token(token)

        if not self._token:
            raise ValueError("Cannot enable authentication without a token")

        self.enabled = True

    def disable(self) -> None:
        """Disable authentication."""
        self.enabled = False
