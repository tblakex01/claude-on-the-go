"""
Input sanitization and log redaction for security.
"""

import re
from typing import Any

# Patterns for sensitive data that should be redacted from logs
IP_PATTERN = re.compile(
    r"\b(?:\d{1,3}\.){3}\d{1,3}\b"  # IPv4
    r"|"
    r"\b(?:[0-9a-fA-F]{1,4}:){7}[0-9a-fA-F]{1,4}\b"  # IPv6
)

TOKEN_PATTERN = re.compile(
    r'(?:token|auth|api[_-]?key|password|secret)["\s:=]+([a-zA-Z0-9_\-\.]+)', re.IGNORECASE
)

EMAIL_PATTERN = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b")

# Characters that could be used for injection attacks
DANGEROUS_CHARS = [
    "\x00",  # Null byte
    "\x1b[",  # ANSI escape (except in terminal output context)
]


def sanitize_input(text: str, allow_ansi: bool = False) -> str:
    """
    Sanitize user input to prevent injection attacks.

    Args:
        text: The input text to sanitize
        allow_ansi: Whether to allow ANSI escape sequences

    Returns:
        Sanitized text
    """
    # Remove null bytes
    text = text.replace("\x00", "")

    # Remove ANSI escape sequences if not allowed
    if not allow_ansi:
        text = re.sub(r"\x1b\[[0-9;]*[a-zA-Z]", "", text)

    # Limit line length to prevent buffer overflow attacks
    lines = text.split("\n")
    sanitized_lines = [line[:1000] for line in lines[:100]]

    return "\n".join(sanitized_lines)


def redact_logs(message: str, enabled: bool = True) -> str:
    """
    Redact sensitive information from log messages.

    Args:
        message: The log message to redact
        enabled: Whether redaction is enabled

    Returns:
        Redacted message
    """
    if not enabled:
        return message

    # Redact IP addresses
    message = IP_PATTERN.sub("[IP_REDACTED]", message)

    # Redact tokens and secrets
    message = TOKEN_PATTERN.sub(r"\1=[TOKEN_REDACTED]", message)

    # Redact email addresses
    message = EMAIL_PATTERN.sub("[EMAIL_REDACTED]", message)

    return message


def sanitize_path(path: str) -> str:
    """
    Sanitize file paths to prevent directory traversal.

    Args:
        path: The file path to sanitize

    Returns:
        Sanitized path
    """
    # Remove null bytes
    path = path.replace("\x00", "")

    # Normalize path separators
    path = path.replace("\\", "/")

    # Remove directory traversal attempts
    while "../" in path or "./" in path:
        path = path.replace("../", "").replace("./", "")

    # Remove leading slashes to prevent absolute path access
    path = path.lstrip("/")

    return path


def is_safe_hostname(hostname: str) -> bool:
    """
    Check if hostname is safe (not an IP address or private hostname).

    Args:
        hostname: The hostname to check

    Returns:
        True if safe, False otherwise
    """
    # Check for IP addresses
    if IP_PATTERN.match(hostname):
        return False

    # Check for localhost variants
    localhost_variants = [
        "localhost",
        "127.0.0.1",
        "::1",
        "0.0.0.0",
        "::",
    ]

    if hostname.lower() in localhost_variants:
        return False

    # Check for .local domains (mDNS)
    if hostname.endswith(".local"):
        return True

    # Check for valid domain format
    domain_pattern = re.compile(
        r"^(?:[a-zA-Z0-9](?:[a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?\.)*[a-zA-Z0-9](?:[a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?$"
    )

    return bool(domain_pattern.match(hostname))


def sanitize_for_json(obj: Any) -> Any:
    """
    Recursively sanitize an object for JSON serialization.

    Args:
        obj: The object to sanitize

    Returns:
        Sanitized object safe for JSON
    """
    if isinstance(obj, dict):
        return {k: sanitize_for_json(v) for k, v in obj.items()}
    elif isinstance(obj, (list, tuple)):
        return [sanitize_for_json(item) for item in obj]
    elif isinstance(obj, str):
        # Remove non-printable characters except newlines and tabs
        return "".join(char for char in obj if char.isprintable() or char in "\n\t")
    else:
        return obj
