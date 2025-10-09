# Claude-onTheGo: Lessons Learned

## TL;DR: What We Built

**Claude-onTheGo** lets you use your Mac's `claude` CLI from your iPhone over WiFi. Your Mac runs the claude process, your phone displays the terminal.

### Architecture

**Backend (Python + FastAPI):**
- Spawns and controls `claude` CLI using Pexpect with PTY
- Captures all terminal output in real-time with watermark flow control (100KB high / 10KB low)
- Parses `~/.config/ghostty/config` to extract theme colors and fonts
- Native WebSockets with binary frames and 30ms message batching
- Single-user connection mode to prevent output duplication

**Frontend (HTML + xterm.js):**
- Mobile-first terminal rendering with xterm.js 5.3+
- Auto-detects hostname for both localhost and network access
- DOM renderer on mobile for proper ANSI escape sequence handling
- Exponential backoff reconnection (1s base, 1.5x decay, 30s max, ±30% jitter)
- Terminal sizing with proper PTY window dimension updates

**Network:**
- mDNS/Bonjour support for easy `.local` domain access
- Works on WiFi, Personal Hotspot, or any local network
- QR code generation for quick mobile connection

---

## TOP 3 Problems & How We Solved Them

### Problem 1: Terminal Sizing Race Condition

**Symptom:** Claude's UI borders rendered as full-width horizontal lines filling the screen. "Thinking..." status appeared 8 times stacked vertically.

**Root Cause:** Terminal remained at default 80 columns while iPhone screen was only ~30 characters wide. WebSocket connected *before* terminal was properly fitted, so the backend received wrong dimensions.

**Solution:**
```javascript
// frontend/terminal.js
const fitDelay = isMobile ? 300 : 100;
setTimeout(() => {
    this.fitAddon.fit();
    // Connect WebSocket AFTER terminal is properly fitted
    this.connect();
}, fitDelay);

// Also send size after theme application changes font
setTimeout(() => {
    this.fitAddon.fit();
    this.sendTerminalSize(); // CRITICAL
}, 100);
```

**Key Learning:** Terminal sizing is a multi-step dance on mobile - fit → connect → send size → apply theme → re-fit → send size again. Each font change requires a new PTY resize.

---

### Problem 2: ANSI Status Message Duplication

**Symptom:** Claude's animated status messages like "Puttering...", "Coalescing..." appeared 6-8 times vertically instead of updating in-place.

**Root Cause:** Canvas renderer on mobile doesn't properly handle ANSI cursor positioning escape codes (CUP, CUU, CHA). Claude uses these to update status messages in-place, but canvas kept drawing new lines.

**Solution:**
```javascript
// frontend/terminal.js
// CRITICAL: Use DOM renderer on mobile for proper ANSI cursor positioning
rendererType: isMobile ? 'dom' : 'canvas',
```

**Key Learning:** Canvas renderer prioritizes performance but sacrifices ANSI compliance. DOM renderer is slower but handles cursor positioning correctly. Choose renderer based on use case.

---

### Problem 3: Multiple Connection Duplication

**Symptom:** Same 574-byte message sent 6 times. Backend logs showed 6 active WebSocket connections. Output appeared duplicated "when I type" on iPhone.

**Root Cause:** Multiple WebSocket connections from browser tabs, zombie connections, or rapid reconnection cycles. Each connection received the same claude output.

**Solution:**
```python
# backend/app.py
class ConnectionManager:
    def __init__(self):
        self.current_connection: Optional[WebSocket] = None  # Track single user

    async def connect(self, websocket: WebSocket):
        # SINGLE-USER GUARD: Close all existing connections
        if self.active_connections:
            print(f"[WS] ⚠️  Single-user mode: Closing {len(self.active_connections)} existing connection(s)")
            for old_ws in list(self.active_connections):
                await old_ws.close(code=1000, reason="New connection established")

            self.active_connections.clear()
            self.batchers.clear()

        # Now accept the new connection
        await websocket.accept()
        self.active_connections.add(websocket)
        self.current_connection = websocket
```

**Key Learning:** For single-user applications, explicitly enforce connection limits. Auto-cleanup prevents zombie connections from accumulating.

---

## Skills Learned

### Backend Development
- **FastAPI Native WebSockets** - Binary frames (`websocket.send_bytes()`) for efficiency
- **Pexpect PTY Control** - Spawning/controlling terminal processes with proper window sizing
- **Watermark Flow Control** - Pause reading at 100KB, resume at 10KB to prevent buffer overflow
- **Message Batching** - 30ms batching window reduces WebSocket frame overhead
- **Ghostty Config Parsing** - Key-value format with repeatable keys, built-in theme handling

### Frontend Development
- **Xterm.js Mobile Optimization** - DOM vs canvas rendering, font size scaling
- **Terminal Sizing** - FitAddon usage, visualViewport API for iOS keyboard handling
- **WebSocket Reconnection** - Exponential backoff with jitter for robust connection handling
- **ANSI Escape Sequences** - Understanding cursor positioning codes (CUP, CUU, CHA)

### Debugging Techniques
- **Video Frame Analysis** - Extracting frames from screen recordings to debug visual issues
- **Playwright E2E Testing** - iPhone 13 device emulation for automated mobile testing
- **Connection Tracking** - Logging WebSocket lifecycle events to debug duplication
- **PTY Window Size Debugging** - Comparing terminal dimensions vs actual screen width

### Network & Infrastructure
- **mDNS/Bonjour** - Service discovery using `.local` domains
- **QR Code Generation** - Terminal-based QR codes for easy mobile connection
- **Dynamic Network Detection** - Auto-detecting hostname for localhost vs network access
- **Process Management** - Proper cleanup, PID tracking, graceful shutdown

### Mobile-First Design
- **iOS Safe Areas** - `env(safe-area-inset-*)` for notch/home indicator
- **Viewport Handling** - visualViewport API for keyboard show/hide
- **Touch Optimization** - Preventing body scroll, touch-action CSS properties
- **Font Scaling** - Mobile-specific font size limits to prevent text wrapping

---

## Production Ready Features

✅ Single-user mode with auto-cleanup
✅ Terminal fidelity matching Ghostty exactly
✅ Mobile-optimized rendering (DOM on mobile, canvas on desktop)
✅ Message batching for performance
✅ Watermark flow control to prevent buffer overflow
✅ Exponential backoff reconnection
✅ mDNS/Bonjour support
✅ QR code for easy connection
✅ Proper terminal sizing with PTY window updates
✅ Beautiful startup banner with network info

---

## Future Improvements

- [ ] Authentication for remote access
- [ ] Session persistence/reconnection to same claude process
- [ ] File upload/download support
- [ ] Multi-user mode with isolated sessions
- [ ] Native iOS app (Turbo Native wrapper)
- [ ] Clipboard sync between devices
- [ ] Keyboard shortcuts on mobile

---

**Built with:** Python, FastAPI, Pexpect, Xterm.js, Native WebSockets, mDNS

**Final Status:** ✅ Production ready for personal use over local WiFi
