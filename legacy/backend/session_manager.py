"""
Session Manager for Claude-onTheGo
Manages persistent sessions that survive disconnections
"""

import asyncio
import time
import uuid
from dataclasses import dataclass
from typing import Dict, Optional, Tuple


@dataclass
class Session:
    """Represents a persistent claude session"""

    id: str
    pid: int
    created_at: float
    last_activity: float
    rows: int
    cols: int
    claude_wrapper: any  # ClaudeWrapper instance

    def is_expired(self, timeout: int = 3600) -> bool:
        """Check if session has expired (default: 1 hour)"""
        return time.time() - self.last_activity > timeout

    def touch(self):
        """Update last activity timestamp"""
        self.last_activity = time.time()

    def age_seconds(self) -> float:
        """Get session age in seconds"""
        return time.time() - self.created_at


class SessionManager:
    """Manages persistent sessions across reconnections"""

    def __init__(self, session_timeout: int = 3600):
        """
        Initialize session manager

        Args:
            session_timeout: How long to keep inactive sessions (seconds)
        """
        self.sessions: Dict[str, Session] = {}
        self.session_timeout = session_timeout
        self.cleanup_task: Optional[asyncio.Task] = None

    def create_session(self, claude_wrapper, rows: int = 24, cols: int = 80) -> str:
        """
        Create a new session

        Args:
            claude_wrapper: The ClaudeWrapper instance
            rows: Terminal rows
            cols: Terminal columns

        Returns:
            Session ID (UUID)
        """
        session_id = str(uuid.uuid4())

        session = Session(
            id=session_id,
            pid=claude_wrapper.process.pid if claude_wrapper.process else 0,
            created_at=time.time(),
            last_activity=time.time(),
            rows=rows,
            cols=cols,
            claude_wrapper=claude_wrapper,
        )

        self.sessions[session_id] = session
        print(f"[SESSION] Created session {session_id} (PID: {session.pid})")

        return session_id

    def get_session(self, session_id: str) -> Optional[Session]:
        """
        Get session by ID

        Args:
            session_id: The session UUID

        Returns:
            Session object or None if not found/expired
        """
        if session_id not in self.sessions:
            return None

        session = self.sessions[session_id]

        # Check if expired
        if session.is_expired(self.session_timeout):
            print(f"[SESSION] Session {session_id} expired")
            self.destroy_session(session_id)
            return None

        # Touch to update activity
        session.touch()
        print(f"[SESSION] Reconnected to session {session_id} (age: {session.age_seconds():.0f}s)")

        return session

    def destroy_session(self, session_id: str):
        """
        Destroy a session and cleanup resources

        Args:
            session_id: The session UUID
        """
        if session_id not in self.sessions:
            return

        session = self.sessions[session_id]

        # Stop claude process
        if session.claude_wrapper:
            asyncio.create_task(session.claude_wrapper.stop())

        del self.sessions[session_id]
        print(f"[SESSION] Destroyed session {session_id}")

    def list_sessions(self) -> Dict[str, dict]:
        """
        List all active sessions

        Returns:
            Dict of session info keyed by session ID
        """
        return {
            sid: {
                "id": s.id,
                "pid": s.pid,
                "age_seconds": s.age_seconds(),
                "last_activity": s.last_activity,
                "rows": s.rows,
                "cols": s.cols,
                "is_alive": s.claude_wrapper.is_alive() if s.claude_wrapper else False,
            }
            for sid, s in self.sessions.items()
        }

    async def cleanup_expired_sessions(self):
        """Cleanup expired sessions periodically"""
        while True:
            try:
                await asyncio.sleep(60)  # Check every minute

                expired = [
                    sid
                    for sid, session in self.sessions.items()
                    if session.is_expired(self.session_timeout)
                ]

                for sid in expired:
                    print(f"[SESSION] Cleaning up expired session {sid}")
                    self.destroy_session(sid)

            except Exception as e:
                print(f"[SESSION] Cleanup error: {e}")

    async def start_cleanup_task(self):
        """Start background cleanup task"""
        if self.cleanup_task is None or self.cleanup_task.done():
            self.cleanup_task = asyncio.create_task(self.cleanup_expired_sessions())
            print("[SESSION] Started session cleanup task")

    async def stop_cleanup_task(self):
        """Stop background cleanup task"""
        if self.cleanup_task:
            self.cleanup_task.cancel()
            try:
                await self.cleanup_task
            except asyncio.CancelledError:
                pass
            print("[SESSION] Stopped session cleanup task")

    def get_session_count(self) -> int:
        """Get count of active sessions"""
        return len(self.sessions)
