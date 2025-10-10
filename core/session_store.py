"""
Session Store - Framework-agnostic session persistence

Manages persistent sessions with optional SQLite storage and compression.
Supports session reconnection and automatic cleanup of expired sessions.
"""

import asyncio
import gzip
import sqlite3
import time
import uuid
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Session:
    """Represents a persistent Claude session."""

    id: str
    created_at: float = field(default_factory=time.time)
    last_activity: float = field(default_factory=time.time)
    rows: int = 24
    cols: int = 80
    history: bytes = b""
    compressed: bool = False

    def is_expired(self, timeout_seconds: int = 3600) -> bool:
        """
        Check if session has expired.

        Args:
            timeout_seconds: Expiry timeout in seconds (default: 1 hour)

        Returns:
            True if session has expired, False otherwise
        """
        return time.time() - self.last_activity > timeout_seconds

    def touch(self) -> None:
        """Update last activity timestamp."""
        self.last_activity = time.time()

    def age_seconds(self) -> float:
        """Get session age in seconds."""
        return time.time() - self.created_at

    def compress_history(self) -> None:
        """Compress session history using gzip."""
        if not self.compressed and self.history:
            self.history = gzip.compress(self.history)
            self.compressed = True

    def decompress_history(self) -> bytes:
        """
        Get decompressed session history.

        Returns:
            Decompressed history bytes
        """
        if self.compressed:
            return gzip.decompress(self.history)
        return self.history


class SessionStore:
    """
    Manages session persistence and reconnection.

    Provides optional SQLite persistence with in-memory fallback.
    Includes automatic compression and cleanup of expired sessions.
    """

    def __init__(
        self,
        db_path: str | None = None,
        auto_compress: bool = True,
        compression_threshold: int = 10_000,
    ):
        """
        Initialize session store.

        Args:
            db_path: Path to SQLite database (None for in-memory)
            auto_compress: Automatically compress large session histories
            compression_threshold: Compress when history exceeds this size (bytes)
        """
        self.db_path = db_path or ":memory:"
        self.auto_compress = auto_compress
        self.compression_threshold = compression_threshold

        # In-memory session cache
        self._sessions: dict[str, Session] = {}
        self._lock = asyncio.Lock()

        # SQLite connection (lazy init)
        self._db: Optional[sqlite3.Connection] = None
        self._db_initialized = False

        # Cleanup task
        self._cleanup_task: Optional[asyncio.Task] = None

    def _init_db(self) -> None:
        """Initialize SQLite database schema."""
        if self._db_initialized:
            return

        self._db = sqlite3.connect(self.db_path, check_same_thread=False)
        self._db.execute(
            """
            CREATE TABLE IF NOT EXISTS sessions (
                id TEXT PRIMARY KEY,
                created_at REAL NOT NULL,
                last_activity REAL NOT NULL,
                rows INTEGER NOT NULL,
                cols INTEGER NOT NULL,
                history BLOB,
                compressed INTEGER NOT NULL
            )
        """
        )
        self._db.commit()
        self._db_initialized = True

    async def create_session(self, session_id: str | None = None) -> Session:
        """
        Create new session with UUID.

        Args:
            session_id: Optional session ID (generates UUID if not provided)

        Returns:
            Created Session object
        """
        async with self._lock:
            sid = session_id or str(uuid.uuid4())

            # Check if session already exists
            if sid in self._sessions:
                raise ValueError(f"Session {sid} already exists")

            session = Session(id=sid)
            self._sessions[sid] = session

            # Persist to DB if using SQLite
            if self.db_path != ":memory:":
                await self._save_to_db(session)

            return session

    async def get_session(self, session_id: str) -> Session | None:
        """
        Retrieve session by ID.

        Args:
            session_id: Session UUID

        Returns:
            Session object or None if not found
        """
        async with self._lock:
            # Check in-memory cache first
            if session_id in self._sessions:
                session = self._sessions[session_id]
                session.touch()
                return session

            # Try to load from DB
            if self.db_path != ":memory:":
                session = await self._load_from_db(session_id)
                if session:
                    session.touch()
                    self._sessions[session_id] = session
                    return session

            return None

    async def save_output(self, session_id: str, output: bytes) -> None:
        """
        Save terminal output to session history.

        Args:
            session_id: Session UUID
            output: Terminal output bytes

        Raises:
            ValueError: If session not found
        """
        async with self._lock:
            session = self._sessions.get(session_id)
            if session is None:
                raise ValueError(f"Session {session_id} not found")

            # Decompress if needed before appending
            if session.compressed:
                current = session.decompress_history()
                session.history = current
                session.compressed = False

            # Append new output
            session.history += output
            session.touch()

            # Auto-compress if threshold exceeded
            if (
                self.auto_compress
                and not session.compressed
                and len(session.history) > self.compression_threshold
            ):
                session.compress_history()

            # Persist to DB if using SQLite
            if self.db_path != ":memory:":
                await self._save_to_db(session)

    async def get_history(self, session_id: str) -> bytes:
        """
        Get full session history (decompressed).

        Args:
            session_id: Session UUID

        Returns:
            Decompressed session history

        Raises:
            ValueError: If session not found
        """
        async with self._lock:
            session = self._sessions.get(session_id)
            if session is None:
                raise ValueError(f"Session {session_id} not found")

            return session.decompress_history()

    async def update_size(self, session_id: str, rows: int, cols: int) -> None:
        """
        Update session terminal size.

        Args:
            session_id: Session UUID
            rows: Terminal rows
            cols: Terminal columns

        Raises:
            ValueError: If session not found
        """
        async with self._lock:
            session = self._sessions.get(session_id)
            if session is None:
                raise ValueError(f"Session {session_id} not found")

            session.rows = rows
            session.cols = cols
            session.touch()

            # Persist to DB if using SQLite
            if self.db_path != ":memory:":
                await self._save_to_db(session)

    async def delete_session(self, session_id: str) -> None:
        """
        Delete a session.

        Args:
            session_id: Session UUID
        """
        async with self._lock:
            # Remove from memory
            if session_id in self._sessions:
                del self._sessions[session_id]

            # Remove from DB
            if self.db_path != ":memory:" and self._db:
                self._db.execute("DELETE FROM sessions WHERE id = ?", (session_id,))
                self._db.commit()

    async def cleanup_expired(self, max_age_hours: int = 1) -> int:
        """
        Remove expired sessions.

        Args:
            max_age_hours: Maximum session age in hours

        Returns:
            Number of sessions removed
        """
        max_age_seconds = max_age_hours * 3600
        expired_ids: list[str] = []

        async with self._lock:
            # Find expired sessions
            for session_id, session in self._sessions.items():
                if session.is_expired(max_age_seconds):
                    expired_ids.append(session_id)

            # Remove expired sessions
            for session_id in expired_ids:
                del self._sessions[session_id]

                # Remove from DB
                if self.db_path != ":memory:" and self._db:
                    self._db.execute("DELETE FROM sessions WHERE id = ?", (session_id,))

            if self._db:
                self._db.commit()

        return len(expired_ids)

    async def list_sessions(self) -> list[Session]:
        """
        List all active sessions.

        Returns:
            List of all Session objects
        """
        async with self._lock:
            return list(self._sessions.values())

    async def _save_to_db(self, session: Session) -> None:
        """Save session to SQLite database."""
        if not self._db_initialized:
            self._init_db()

        if self._db is None:
            return

        self._db.execute(
            """
            INSERT OR REPLACE INTO sessions
            (id, created_at, last_activity, rows, cols, history, compressed)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                session.id,
                session.created_at,
                session.last_activity,
                session.rows,
                session.cols,
                session.history,
                1 if session.compressed else 0,
            ),
        )
        self._db.commit()

    async def _load_from_db(self, session_id: str) -> Session | None:
        """Load session from SQLite database."""
        if not self._db_initialized:
            self._init_db()

        if self._db is None:
            return None

        cursor = self._db.execute(
            """
            SELECT id, created_at, last_activity, rows, cols, history, compressed
            FROM sessions
            WHERE id = ?
            """,
            (session_id,),
        )

        row = cursor.fetchone()
        if row is None:
            return None

        return Session(
            id=row[0],
            created_at=row[1],
            last_activity=row[2],
            rows=row[3],
            cols=row[4],
            history=row[5] or b"",
            compressed=bool(row[6]),
        )

    async def start_cleanup_task(self, interval_seconds: int = 60, max_age_hours: int = 1) -> None:
        """
        Start background cleanup task.

        Args:
            interval_seconds: How often to check for expired sessions
            max_age_hours: Maximum session age before cleanup
        """
        if self._cleanup_task is not None and not self._cleanup_task.done():
            return

        async def cleanup_loop():
            while True:
                try:
                    await asyncio.sleep(interval_seconds)
                    removed = await self.cleanup_expired(max_age_hours)
                    if removed > 0:
                        print(f"[SESSION] Cleaned up {removed} expired session(s)")
                except asyncio.CancelledError:
                    break
                except Exception as e:
                    print(f"[SESSION] Cleanup error: {e}")

        self._cleanup_task = asyncio.create_task(cleanup_loop())

    async def stop_cleanup_task(self) -> None:
        """Stop background cleanup task."""
        if self._cleanup_task is not None:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
            self._cleanup_task = None

    def close(self) -> None:
        """Close database connection."""
        if self._db is not None:
            self._db.close()
            self._db = None
            self._db_initialized = False
