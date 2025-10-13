# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [1.3.0] - 2025-10-13

### Added
- Remote access via SSH + Tailscale for anywhere connectivity
  - Automated setup script (`./scripts/tailscale-setup.sh`) with daemon verification
  - Handles daemon error states and "none" status automatically
  - Retry loops for IP assignment with 3-attempt backoff
  - Comprehensive troubleshooting documentation
- Connection method comparison (WebSocket vs SSH+Tailscale)
  - WebSocket: 5-15ms latency, browser-based, same WiFi only
  - SSH+Tailscale: 20-50ms latency, works anywhere, survives network roaming

### Changed
- Improved Tailscale setup script reliability
  - Automatic daemon startup via `brew services` (macOS) or `systemctl` (Linux)
  - Verification loops to ensure daemon responds before proceeding
  - Better error messages with platform-specific troubleshooting commands
- Enhanced documentation in `docs/REMOTE_ACCESS.md`
  - Added daemon startup troubleshooting section
  - Manual setup now includes daemon start step

## [1.2.0] - 2025-10-12

### Added
- Progressive Web App (PWA) support with offline capability
  - Install directly to home screen like a native app
  - Works offline with intelligent caching
  - Full-screen experience without browser chrome
  - Service worker for offline functionality
- PyPI package distribution for easy installation via `pip install claude-on-the-go`
- Complete CLI with commands: start, stop, status, logs, qr
- Professional packaging with all dependencies included
- Push notification support (Pushover, ntfy.sh, Telegram)
  - Notifications when Claude needs input
  - Configurable notification providers
- Enhanced session persistence with PTY state tracking
  - Sessions survive disconnections and reconnect seamlessly
  - Automatic session cleanup with configurable expiration
  - UUID-based session IDs with 1-hour timeout
- Bidirectional clipboard synchronization between Mac and phone
  - Mac to phone clipboard sync
  - Phone to Mac clipboard sync
  - Configurable sync interval (default 1 second)
  - Content hashing prevents sync loops

### Changed
- Improved mobile reconnection UX with rocket launch screen
  - Progressive status messages: "Launching..." → "Starting Claude..." → Error detection
  - Overlay stays visible until Claude responds
  - 15-second timeout with helpful error messages
- Enhanced terminal rendering with theme caching and session buffering
- Optimized WebSocket error handling and flow control
- Updated documentation with comprehensive installation guide

### Fixed
- Mobile reconnection black screen bug - overlay now stays visible during reconnection
- Session replay infinite reconnection loop resolved
- Content Security Policy (CSP) font loading issues
- Mobile scrolling performance issues with rendering and keyboard handling
- Terminal scrolling now smooth with momentum
- Keyboard-aware layout improvements

### Security
- Eliminated 0.0.0.0 binding, auto-detect local IP for better security (resolves Bandit B104)
- Applied comprehensive security formatting and validation
- Rate limiting to prevent DoS attacks (10 msg/sec, 100KB/sec)
- Content Security Policy (CSP) headers
- Log redaction for sensitive data

## [1.1.0] - 2025-10-11

### Added
- Mobile keyboard toolbar with special key support
  - Tab key for completion triggering
  - Shift+Tab for cycling backwards through completions
  - Ctrl+C for interrupting commands
  - Esc key for canceling operations
  - Ctrl+D for EOF/logout
  - Touch-friendly 44px minimum button height (iOS HIG)
  - Semi-transparent dark background with blur effect
  - Purple accent colors matching app theme
  - Automatically hidden on desktop (>768px width)

### Fixed
- Critical WebSocket session reconnection bug
  - Backend now correctly stores session_id for reconnection
  - Session persistence now works across disconnections
- Stale session localStorage poisoning
  - Automatic clearing of localStorage after 3 failed reconnection attempts
  - Users no longer get stuck in reconnection loops
  - Fresh session automatically started after failures
- WebSocket connection stability improvements
- Session ID persistence in backend WebSocket handler

### Changed
- Improved session reconnection reliability
- Enhanced error handling for connection failures
- Better localStorage management for session persistence

## [1.0.0] - 2025-10-09

### Added
- Initial release of claude-on-the-go
- FastAPI backend with WebSocket streaming
- xterm.js-based terminal emulator
- Multi-terminal theme detection and parsing
  - Ghostty - Complete theme and font parsing
  - iTerm2 - Binary plist with RGB color extraction
  - Alacritty - YAML config with multiple file support
  - Kitty - Key-value config with include directives
  - Terminal.app - NSColor/NSFont parsing (best-effort)
- QR code generation for instant mobile connection
- Mobile-optimized responsive design
  - iOS safe area support (handles notch/home indicator)
  - Smooth scrolling with momentum
  - Keyboard-aware layout
- Security features
  - Token bucket rate limiting (10 msg/sec, 100KB/sec)
  - Input size limits (10KB per message)
  - Terminal size validation (1-500 rows/cols)
  - CSP, X-Frame-Options, X-XSS-Protection headers
  - Constant-time auth token comparison
  - Log redaction for IPs, tokens, emails
- Session management with in-memory storage
- Automatic terminal configuration detection
- Installation and launcher scripts
- Comprehensive documentation
  - Security policy and best practices
  - Terminal parser development guide
  - Technical architecture documentation

### Security
- Network isolation: Bind to LAN only
- Optional password authentication
- CORS restrictions to local origins
- No logging of sensitive data
- Read-only sharing with time-limited tokens

[Unreleased]: https://github.com/MatthewJamisonJS/claude-on-the-go/compare/v1.3.0...HEAD
[1.3.0]: https://github.com/MatthewJamisonJS/claude-on-the-go/compare/v1.2.0...v1.3.0
[1.2.0]: https://github.com/MatthewJamisonJS/claude-on-the-go/compare/v1.1.0...v1.2.0
[1.1.0]: https://github.com/MatthewJamisonJS/claude-on-the-go/compare/v1.0.0...v1.1.0
[1.0.0]: https://github.com/MatthewJamisonJS/claude-on-the-go/releases/tag/v1.0.0
