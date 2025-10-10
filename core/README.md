# Core

Framework-agnostic business logic for claude-on-the-go.

## Purpose

This directory contains the pure business logic that is independent of any web framework, database, or UI implementation.

## Components

### PTY Manager
- Spawns and manages Claude Code CLI processes
- Handles pseudo-terminal (PTY) I/O
- Process lifecycle management
- Output buffering and flow control

### Session Store
- Session persistence and retrieval
- Optional SQLite backend
- Session cleanup and expiration
- UUID-based session identifiers

### Configuration
- Environment variable loading
- Default value management
- Configuration validation
- Centralized config access

### Network Utilities
- Local IP detection (mDNS-friendly)
- QR code generation
- Network interface enumeration

## Design Principles

1. **Framework Independence**: No FastAPI, Flask, or other web framework dependencies
2. **Testability**: Pure functions and minimal side effects where possible
3. **Reusability**: Can be imported by server, CLI, or other tools
4. **Separation of Concerns**: Business logic separate from presentation and infrastructure

## Usage Example

```python
from core.pty_manager import PTYManager
from core.session_store import SessionStore

# Create PTY manager
pty = PTYManager(claude_path="/usr/local/bin/claude")
pty.start()

# Store session
store = SessionStore(db_path="./sessions.db")
store.save_session(session_id="abc123", pty_instance=pty)
```

## Dependencies

- Minimal external dependencies (pexpect, sqlite3)
- No web framework dependencies
- No UI dependencies
