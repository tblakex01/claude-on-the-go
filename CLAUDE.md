# Project Overview
Mobile access to Claude Code CLI via local WiFi. FastAPI backend streams terminal I/O over WebSocket.

**Core concept**: Access your Mac's Claude Code from your phone - zero cloud, zero auth, zero cost.

# Architecture
- **legacy/**: Original open source (maintain backward compatibility)
- **core/**: PTY manager, session storage, mDNS discovery
- **server/**: FastAPI WebSocket streaming, REST endpoints
- **client/**: PWA for mobile access
- **integrations/**: Push notifications, Tailscale, QR codes

# Key Components
- `core/pty_manager.py`: Spawns Claude Code process, handles I/O
- `core/session_store.py`: Optional SQLite session persistence
- `server/websocket.py`: Real-time terminal streaming with reconnection
- `integrations/notifications.py`: Forwards Claude prompts to Pushover/ntfy/Telegram

# Commands
- `python legacy/server.py`: Start legacy server
- `claude-on-the-go start`: Start new architecture server
- `claude-on-the-go qr`: Generate connection QR code
- `claude-on-the-go sessions`: List active sessions

# Code Style
- Use async/await for all I/O operations
- FastAPI for web framework
- SQLite for optional persistence (no external DB)
- WebSocket for terminal streaming
- **See VIEWS.md for all UI/UX, CSS, and mobile-first design decisions**

# Security
- Bind to LAN only (not 0.0.0.0)
- Network isolation is primary security
- Optional password auth via REQUIRE_PASSWORD env var
- Read-only sharing via time-limited tokens

# Environment Variables
```bash
# Required
CLAUDE_CODE_PATH=/usr/local/bin/claude

# Optional
PORT=8000
SQLITE_PATH=./sessions.db
REQUIRE_PASSWORD=false
PUSHOVER_USER_KEY=
NTFY_TOPIC=
TELEGRAM_BOT_TOKEN=
```

# Common Issues
- **Can't connect from phone**: Check firewall, ensure same WiFi
- **Terminal text too small**: Use PWA or pinch to zoom
- **Connection drops**: Enable auto-reconnect in settings
- **Claude Code not found**: Set CLAUDE_CODE_PATH explicitly

# Testing
- Unit tests: PTY I/O cycles, session compression
- Integration: WebSocket reconnection, multi-client
- E2E: Playwright mobile viewport, voice input

# Product Strategy

**Market positioning**: Privacy-first alternative to omnara ($9/mo subscription)
- Target: Privacy-conscious devs, homelab enthusiasts, budget users
- Value prop: "Same mobility, zero cloud, zero recurring cost"

**Revenue model** (timeline-based):
- Core server: Free forever (open source, community building)
- Mobile app: $2.99 one-time (Month 4+, native iOS/Android)
- Hosted option: $3/month (Month 6+, optional convenience)
- Enterprise support: $99/month (Year 2+)

**Success metrics**:
- 1,000 GitHub stars (community validation)
- 100 daily active users (product-market fit)
- 10% mobile app conversion ($300 revenue target)
- 5 contributors (long-term sustainability)

**Key principle**: Never gate core features behind subscription. Simplicity and self-hosting are selling points, not limitations.
