# Features

Comprehensive feature documentation for claude-on-the-go.

## Table of Contents

- [Security](#security)
- [Session Persistence](#session-persistence)
- [Clipboard Sync](#clipboard-sync)
- [Terminal Theme Support](#terminal-theme-support)
- [Mobile Optimizations](#mobile-optimizations)
- [Remote Access](#remote-access)
- [Stability & Performance](#stability--performance)

## Security

### Rate Limiting
- **Message throttling**: 10 messages per second per client
- **Bandwidth throttling**: 100KB per second per client
- **Token bucket algorithm**: Prevents burst attacks while allowing normal usage

### Input Validation
- All WebSocket messages validated before processing
- Terminal size validation (1-500 rows/cols)
- Input size limits (10KB per message)
- Command injection prevention

### Headers & Policies
- Content Security Policy (CSP)
- X-Frame-Options: DENY
- X-XSS-Protection: 1; mode=block
- Secure WebSocket upgrade handling

### Authentication
- Optional token-based authentication
- Constant-time token comparison (prevents timing attacks)
- Environment variable configuration
- No tokens stored in code or logs

### Log Redaction
- Automatic redaction of sensitive data:
  - IP addresses
  - Authentication tokens
  - Email addresses
  - Session IDs
- Configurable via `LOG_REDACTION` environment variable

## Session Persistence

### Architecture
- UUID-based session IDs (cryptographically random)
- In-memory session store with automatic cleanup
- 1-hour session timeout (configurable)
- Terminal state preserved across disconnections

### Reconnection Handling
- Automatic reconnection with exponential backoff
- Session history replay on reconnect
- Seamless resume from where you left off
- No data loss during brief network interruptions

### Implementation
```python
# Core components
core/session_store.py  # Session state management
core/pty_manager.py    # PTY process lifecycle
legacy/backend/app.py  # WebSocket reconnection logic
```

## Clipboard Sync

### Bidirectional Synchronization
- **Mac → Phone**: Automatic sync when Mac clipboard changes
- **Phone → Mac**: Automatic sync when phone clipboard changes
- **Conflict resolution**: Content hashing prevents infinite loops

### Configuration
```bash
# .env settings
ENABLE_CLIPBOARD_SYNC=true      # Enable/disable feature
CLIPBOARD_SYNC_INTERVAL=1.0     # Check interval (seconds)
```

### Implementation
- Uses `pbcopy`/`pbpaste` on macOS
- Content hashing (SHA-256) to detect changes
- Background polling with minimal CPU impact
- WebSocket messages for sync events

### Security Considerations
- Only syncs within authenticated session
- No clipboard data persisted to disk
- Rate limited to prevent abuse

## Terminal Theme Support

### Fully Supported Terminals

#### Ghostty
- **Config location**: `~/.config/ghostty/config`
- **Parser**: Key-value format
- **Features**: Complete theme and font extraction
- **Colors**: All 16 ANSI colors + background/foreground
- **Fonts**: Family, size, bold, italic variants

#### iTerm2
- **Config location**: `~/Library/Preferences/com.googlecode.iterm2.plist`
- **Parser**: Binary plist with `plutil` conversion
- **Features**: RGB color extraction (float → hex conversion)
- **Profiles**: Extracts from active profile
- **Colors**: Full color scheme with opacity support

#### Alacritty
- **Config location**: `~/.config/alacritty/alacritty.yml`
- **Parser**: YAML with multi-file import support
- **Features**: Handles `import:` directives recursively
- **Colors**: Named colors + hex codes
- **Fonts**: Full font family configuration

#### Kitty
- **Config location**: `~/.config/kitty/kitty.conf`
- **Parser**: Key-value with `include` directives
- **Features**: Recursive include file parsing
- **Colors**: All color definitions
- **Fonts**: Font family and size

#### Terminal.app
- **Config location**: `~/Library/Preferences/com.apple.Terminal.plist`
- **Parser**: NSColor/NSFont heuristic parsing
- **Features**: Best-effort extraction from binary format
- **Note**: Limited support due to proprietary format

### Partial Support
Terminals with default theme fallback:
- Warp
- Hyper
- Windows Terminal

### Fallback Behavior
If no terminal config detected:
- Uses clean, readable default theme
- High contrast for accessibility
- Optimized for mobile screens

### Adding New Terminals
See `docs/ADDING_TERMINALS.md` for parser implementation guide.

## Mobile Optimizations

### Responsive Design
- **Dynamic terminal sizing**: Adapts to screen width/height
- **Font scaling**: Adjusts for mobile readability (14px minimum)
- **Touch-optimized**: Tap targets sized for finger input
- **Orientation handling**: Works in portrait and landscape

### iOS-Specific
- **Safe area support**: Respects notch and home indicator
- **Keyboard avoidance**: Terminal repositions when keyboard appears
- **Touch gestures**: Scroll, zoom, select with native feel
- **PWA support**: Install to home screen for app-like experience

### Android-Specific
- **System bars**: Handles navigation and status bars
- **Keyboard types**: Optimal keyboard for terminal input
- **Back button**: Proper back navigation handling

### Rendering
- **DOM renderer** (mobile): Better ANSI color support
- **Canvas renderer** (desktop): Better performance
- **Automatic selection**: Detects device and chooses optimal renderer

### Performance
- **Lazy loading**: Terminal content loaded as needed
- **Virtual scrolling**: Only render visible lines
- **Debounced resize**: Prevents excessive re-renders
- **Efficient WebSocket**: Binary frames for lower bandwidth

## Remote Access

### SSH + Tailscale Architecture
- **End-to-end encryption**: WireGuard (ChaCha20-Poly1305)
- **NAT traversal**: Automatic, no port forwarding needed
- **Network roaming**: Survives WiFi → cellular switches
- **Zero configuration**: Works out of the box after setup

### Latency Comparison
| Connection Type | Typical Latency | Use Case |
|----------------|-----------------|----------|
| Local WebSocket | 5-15ms | Same WiFi, fastest |
| SSH + Tailscale (direct) | 20-50ms | Remote, direct connection |
| SSH + Tailscale (relay) | 80-150ms | Remote, via DERP relay |
| Mosh + Tailscale | < 5ms keystroke echo | Unstable networks |

### Mosh Support
For flaky connections (trains, planes):
- **Local echo**: Instant keystroke feedback
- **Roaming**: Survives network changes
- **Packet loss resilience**: 50x better than SSH under 29% loss
- **Session persistence**: Reconnects automatically

### Security Model
- **SSH authentication**: Public key or password
- **Tailscale ACLs**: Control who can access your devices
- **No exposed ports**: Never opens ports to internet
- **Audit trail**: Both SSH and Tailscale log connections

## Stability & Performance

### Testing Methodology
- **60-minute stability tests**: Long-running sessions
- **Live metrics**: Real-time monitoring during tests
- **Automated scoring**: 90+/100 required for passing
- **Multiple scenarios**: Normal usage, stress tests, edge cases

### Metrics Tracked
1. **Memory usage**: Leak detection and growth monitoring
2. **CPU utilization**: Sustained load and spike detection
3. **Latency**: Keystroke echo time (p50, p95, p99)
4. **Error rate**: WebSocket errors, PTY crashes, reconnection failures
5. **Message throughput**: Sustained message rate handling

### Performance Targets
| Metric | Target | Actual |
|--------|--------|--------|
| First byte latency | < 200ms | ~100ms |
| Keystroke echo | < 50ms | ~20ms |
| Reconnect time | < 2s | ~1s |
| Memory per session | < 50MB | ~30MB |
| WebSocket latency | < 16ms | ~8ms |

### Flow Control
- **Watermark system**: Pause at 100KB buffer, resume at 10KB
- **Message batching**: 30ms window to reduce overhead
- **Backpressure handling**: Prevents memory exhaustion
- **Graceful degradation**: Slows output instead of crashing

### Resource Management
- **Single-user mode**: Auto-closes old connections
- **Automatic cleanup**: Orphaned sessions removed
- **PID tracking**: Process lifecycle management
- **Graceful shutdown**: SIGTERM handling, cleanup on exit

---

**See Also:**
- [ARCHITECTURE.md](ARCHITECTURE.md) - Technical architecture details
- [docs/REMOTE_ACCESS.md](docs/REMOTE_ACCESS.md) - Remote access setup guide
- [docs/SECURITY.md](docs/SECURITY.md) - Security policy and best practices
