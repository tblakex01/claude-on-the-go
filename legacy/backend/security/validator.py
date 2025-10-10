"""
Input validation for WebSocket messages and terminal commands.
"""

from typing import Any, Dict, Tuple

# Security limits
MAX_MESSAGE_SIZE = 10_000  # 10KB per message
MAX_TERMINAL_ROWS = 500
MAX_TERMINAL_COLS = 500
MIN_TERMINAL_ROWS = 1
MIN_TERMINAL_COLS = 1


class ValidationError(Exception):
    """Raised when validation fails."""

    pass


def validate_message(message: Dict[str, Any]) -> Tuple[bool, str]:
    """
    Validate incoming WebSocket message structure and content.

    Args:
        message: The message dictionary to validate

    Returns:
        Tuple of (valid: bool, error_message: str)
    """
    # Check message type exists
    if "type" not in message:
        return False, "Message missing 'type' field"

    msg_type = message["type"]

    # Validate based on message type
    if msg_type == "input":
        return _validate_input_message(message)
    elif msg_type == "resize":
        return _validate_resize_message(message)
    else:
        return False, f"Unknown message type: {msg_type}"


def _validate_input_message(message: Dict[str, Any]) -> Tuple[bool, str]:
    """Validate input message."""
    if "text" not in message:
        return False, "Input message missing 'text' field"

    text = message["text"]

    if not isinstance(text, str):
        return False, "Input text must be a string"

    if len(text) > MAX_MESSAGE_SIZE:
        return False, f"Input text exceeds maximum size ({MAX_MESSAGE_SIZE} bytes)"

    # Check for null bytes (potential injection attack)
    if "\x00" in text:
        return False, "Input contains null bytes"

    return True, ""


def _validate_resize_message(message: Dict[str, Any]) -> Tuple[bool, str]:
    """Validate terminal resize message."""
    if "rows" not in message or "cols" not in message:
        return False, "Resize message missing 'rows' or 'cols' field"

    rows = message["rows"]
    cols = message["cols"]

    if not isinstance(rows, int) or not isinstance(cols, int):
        return False, "Rows and cols must be integers"

    if rows < MIN_TERMINAL_ROWS or rows > MAX_TERMINAL_ROWS:
        return False, f"Rows must be between {MIN_TERMINAL_ROWS} and {MAX_TERMINAL_ROWS}"

    if cols < MIN_TERMINAL_COLS or cols > MAX_TERMINAL_COLS:
        return False, f"Cols must be between {MIN_TERMINAL_COLS} and {MAX_TERMINAL_COLS}"

    return True, ""


def validate_terminal_size(rows: int, cols: int) -> Tuple[bool, str]:
    """
    Validate terminal dimensions.

    Args:
        rows: Number of rows
        cols: Number of columns

    Returns:
        Tuple of (valid: bool, error_message: str)
    """
    if not isinstance(rows, int) or not isinstance(cols, int):
        return False, "Rows and cols must be integers"

    if rows < MIN_TERMINAL_ROWS or rows > MAX_TERMINAL_ROWS:
        return False, f"Rows must be between {MIN_TERMINAL_ROWS} and {MAX_TERMINAL_ROWS}"

    if cols < MIN_TERMINAL_COLS or cols > MAX_TERMINAL_COLS:
        return False, f"Cols must be between {MIN_TERMINAL_COLS} and {MAX_TERMINAL_COLS}"

    return True, ""


def validate_auth_token(token: str, expected_token: str) -> bool:
    """
    Validate authentication token using constant-time comparison.

    Args:
        token: The provided token
        expected_token: The expected token

    Returns:
        True if tokens match, False otherwise
    """
    if not token or not expected_token:
        return False

    # Constant-time comparison to prevent timing attacks
    if len(token) != len(expected_token):
        return False

    result = 0
    for a, b in zip(token, expected_token):
        result |= ord(a) ^ ord(b)

    return result == 0
