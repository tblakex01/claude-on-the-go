"""
Core Module - Framework-agnostic business logic

This package provides clean, testable, framework-independent modules for:
- PTY (pseudoterminal) management with flow control
- Session persistence with optional SQLite storage
- Configuration management with validation

All modules use async/await and are designed to work with any web framework.
"""

from .config import Config, config
from .pty_manager import FlowControl, PTYManager
from .session_store import Session, SessionStore

__version__ = "0.1.0"

__all__ = [
    # Configuration
    "Config",
    "config",
    # PTY Management
    "PTYManager",
    "FlowControl",
    # Session Management
    "Session",
    "SessionStore",
]
