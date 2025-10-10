# Core

Framework-agnostic business logic for claude-on-the-go.

## Purpose

This directory contains the pure business logic that is independent of any web framework, database, or UI implementation. All modules use async/await and are designed to work with any async Python framework.

## Components

### PTY Manager (`pty_manager.py`)
Manages pseudoterminal for Claude CLI process with watermark-based flow control.

**Key Features:**
- Spawns Claude CLI in PTY with pexpect
- Non-blocking async I/O with output queue
- Watermark-based flow control (pause at 100KB, resume at 10KB)
- Auto-restart with rate limiting
- Terminal resize support
- Control character handling (Ctrl+C, Ctrl+D, etc.)

**Public API:**
- `spawn()` - Spawn Claude process
- `start_reading()` - Start background read loop
- `send_input(data)` - Send text to process
- `send_control(char)` - Send control character
- `read_output(timeout)` - Read output (non-blocking)
- `resize(rows, cols)` - Resize terminal
- `notify_bytes_sent(count)` - Update flow control
- `close()` - Gracefully shutdown
- `is_alive` - Check if process is running

### Session Store (`session_store.py`)
Manages session persistence with optional SQLite storage and compression.

**Key Features:**
- In-memory sessions with optional SQLite persistence
- Automatic gzip compression for large histories
- Session expiry and cleanup
- Thread-safe async operations with locks
- Background cleanup task
- Session reconnection support

**Public API:**
- `create_session(session_id)` - Create new session
- `get_session(session_id)` - Retrieve session
- `save_output(session_id, output)` - Append output
- `get_history(session_id)` - Get full history (decompressed)
- `update_size(session_id, rows, cols)` - Update terminal size
- `delete_session(session_id)` - Delete session
- `cleanup_expired(max_age_hours)` - Remove expired sessions
- `list_sessions()` - List all active sessions
- `start_cleanup_task()` - Start background cleanup
- `stop_cleanup_task()` - Stop background cleanup

### Configuration (`config.py`)
Centralized configuration using pydantic-settings with validation.

**Key Features:**
- Loads from `.env` file automatically
- Type validation with pydantic
- Port range validation (1024-65535)
- Cross-field validation (watermarks, auth)
- Sensible defaults for all settings
- Helper methods for common operations

**Configuration Fields:**
```python
# Server
BACKEND_HOST = "127.0.0.1"
BACKEND_PORT = 8000
FRONTEND_PORT = 8001

# Claude CLI
CLAUDE_CODE_PATH = "claude"

# Session
SQLITE_PATH = None  # In-memory by default
SESSION_TIMEOUT_HOURS = 1

# Security
ENABLE_AUTH = False
AUTH_TOKEN = None
MAX_CONNECTIONS = 1

# Rate Limiting
RATE_LIMIT_MESSAGES = 10
RATE_LIMIT_BYTES = 100000

# Logging
LOG_LEVEL = "INFO"
LOG_REDACTION = True

# Features
ENABLE_CLIPBOARD_SYNC = True
CLIPBOARD_SYNC_INTERVAL = 1.0

# PTY Flow Control
PTY_HIGH_WATERMARK = 100000
PTY_LOW_WATERMARK = 10000
```

## Design Principles

1. **Framework Independence**: No FastAPI, Flask, or other web framework dependencies
2. **Async First**: All I/O operations use async/await
3. **Testability**: Pure functions and minimal side effects where possible
4. **Reusability**: Can be imported by server, CLI, or other tools
5. **Type Safety**: Comprehensive type hints throughout
6. **Error Handling**: Graceful error handling with helpful messages

## Usage Example

```python
import asyncio
from core import PTYManager, SessionStore, config

async def main():
    # 1. Load configuration
    print(f"Backend: {config.BACKEND_HOST}:{config.BACKEND_PORT}")
    print(f"Claude CLI: {config.CLAUDE_CODE_PATH}")

    # 2. Create session store
    store = SessionStore(db_path=config.SQLITE_PATH)
    session = await store.create_session()

    # 3. Create PTY manager
    pty = PTYManager(
        command=config.CLAUDE_CODE_PATH,
        high_watermark=config.PTY_HIGH_WATERMARK,
        low_watermark=config.PTY_LOW_WATERMARK,
    )

    # 4. Spawn and start reading
    await pty.spawn()
    await pty.start_reading()

    # 5. Send input
    await pty.send_input("Hello Claude!\n")

    # 6. Read output
    output = await pty.read_output(timeout=1.0)
    if output:
        await store.save_output(session.id, output)
        pty.notify_bytes_sent(len(output))

    # 7. Cleanup
    await pty.close()
    await store.delete_session(session.id)
    store.close()

asyncio.run(main())
```

## Dependencies

- `pexpect` - PTY management
- `pydantic-settings` - Configuration with validation
- `sqlite3` - Optional session persistence (built-in)
- `asyncio` - Async operations (built-in)
- `gzip` - Session compression (built-in)

**No web framework dependencies** - can be used with FastAPI, Flask, Django, etc.
