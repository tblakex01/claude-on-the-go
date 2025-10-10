# Legacy Architecture (v1.0)

This directory contains the original frozen architecture of claude-on-the-go v1.0.

## Purpose

- Maintained for backward compatibility
- Production-stable codebase
- Reference implementation for new architecture

## Structure

- `backend/` - Original FastAPI server with WebSocket support
- `frontend/` - Original web client with xterm.js
- `tests/` - Original test suite
- `launcher.py` - Original Python launcher script

## Running Legacy Mode

From the project root:

```bash
./start.sh
```

This will start both the backend (port 8000) and frontend (port 8001) servers using the legacy architecture.

## Status

- **Frozen**: No new features will be added
- **Maintained**: Bug fixes and security updates only
- **Deprecated**: Users should migrate to the new modular architecture when available

## Migration Path

New features and improvements are being developed in the modular architecture:
- `/core` - Business logic
- `/server` - New API implementation
- `/client` - New web client
- `/integrations` - External service integrations
- `/cli` - Command-line interface

See the root `ARCHITECTURE.md` for detailed documentation on the new architecture.
