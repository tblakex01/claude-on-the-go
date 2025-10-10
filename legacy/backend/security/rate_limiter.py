"""
Rate limiting for WebSocket connections to prevent DoS attacks.
"""

import time
from collections import deque
from dataclasses import dataclass
from typing import Dict, Tuple


@dataclass
class RateLimit:
    """Rate limit configuration."""

    messages_per_second: int
    bytes_per_second: int


class RateLimiter:
    """
    Token bucket rate limiter for WebSocket connections.
    Tracks both message count and byte volume.
    """

    def __init__(self, messages_per_second: int = 10, bytes_per_second: int = 100000):
        """
        Initialize rate limiter.

        Args:
            messages_per_second: Maximum messages allowed per second
            bytes_per_second: Maximum bytes allowed per second
        """
        self.limit = RateLimit(messages_per_second, bytes_per_second)

        # Track messages and bytes per connection
        self._message_timestamps: Dict[str, deque] = {}
        self._byte_history: Dict[str, deque] = {}

    def check_rate_limit(self, connection_id: str, message_size: int) -> Tuple[bool, str]:
        """
        Check if message is within rate limits.

        Args:
            connection_id: Unique identifier for the connection
            message_size: Size of the message in bytes

        Returns:
            Tuple of (allowed: bool, reason: str)
        """
        now = time.time()

        # Initialize tracking for new connections
        if connection_id not in self._message_timestamps:
            self._message_timestamps[connection_id] = deque()
            self._byte_history[connection_id] = deque()

        # Clean up old entries (older than 1 second)
        self._cleanup_old_entries(connection_id, now)

        # Check message rate limit
        message_count = len(self._message_timestamps[connection_id])
        if message_count >= self.limit.messages_per_second:
            return False, f"Message rate limit exceeded ({self.limit.messages_per_second}/sec)"

        # Check byte rate limit
        total_bytes = sum(size for _, size in self._byte_history[connection_id])
        if total_bytes + message_size > self.limit.bytes_per_second:
            return False, f"Bandwidth limit exceeded ({self.limit.bytes_per_second} bytes/sec)"

        # Record this message
        self._message_timestamps[connection_id].append(now)
        self._byte_history[connection_id].append((now, message_size))

        return True, ""

    def _cleanup_old_entries(self, connection_id: str, current_time: float) -> None:
        """Remove entries older than 1 second."""
        cutoff = current_time - 1.0

        # Clean message timestamps
        messages = self._message_timestamps[connection_id]
        while messages and messages[0] < cutoff:
            messages.popleft()

        # Clean byte history
        bytes_history = self._byte_history[connection_id]
        while bytes_history and bytes_history[0][0] < cutoff:
            bytes_history.popleft()

    def reset(self, connection_id: str) -> None:
        """Reset rate limit tracking for a connection."""
        self._message_timestamps.pop(connection_id, None)
        self._byte_history.pop(connection_id, None)

    def get_stats(self, connection_id: str) -> Dict[str, int]:
        """
        Get current rate limit stats for a connection.

        Returns:
            Dictionary with current message count and byte usage
        """
        if connection_id not in self._message_timestamps:
            return {"messages": 0, "bytes": 0}

        messages = len(self._message_timestamps[connection_id])
        total_bytes = sum(size for _, size in self._byte_history[connection_id])

        return {
            "messages": messages,
            "bytes": total_bytes,
            "messages_limit": self.limit.messages_per_second,
            "bytes_limit": self.limit.bytes_per_second,
        }
