# UI/UX Overview
Mobile-first terminal UI for Claude Code access. PWA architecture, instant browser access, WiFi-local streaming.

**Design principles**: Terminal-native, zero friction, touch-optimized, auto-reconnect, privacy-first

# Tech Stack
- **Terminal**: xterm.js with mobile addons
- **Framework**: Vanilla JS + Web Components (no React initially)
- **Styling**: CSS Grid/Flexbox only
- **PWA**: Service worker + manifest from day 1
- **Font**: JetBrains Mono (embedded, not CDN)

# Component Structure
```
components/
├── terminal/         # TerminalView, PTYStream
├── connection/       # QRCode, StatusIndicator, Reconnector
├── session/          # SessionList, SessionPlayer
├── mobile/           # MobileKeyboard, VoiceInput, GestureHandler
├── notifications/    # PromptAlert, NotificationConfig
└── shared/           # EmptyState, ErrorBoundary, LoadingPulse
```

# Mobile Gestures
- **Pinch**: Zoom terminal text (persist in localStorage)
- **Double-tap**: Fit to width
- **Long-press**: Selection mode for copying
- **Swipe up/down**: Show/hide keyboard
- **Two-finger tap**: Paste from clipboard

# URL Structure
```
/                    # Main terminal
/sessions            # Session history
/sessions/:id        # Replay specific session
/share/:token        # Read-only shared view
/settings            # Connection, notifications
/qr                  # QR code for current server
```

# Mobile Optimizations

## Touch Targets
```css
.toolbar button {
    min-height: 44px;  /* iOS minimum */
    min-width: 44px;
    padding: 12px;
}
```

## Viewport Configuration
```html
<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=5.0, user-scalable=yes">
```

## Wake Lock
```javascript
// Keep screen on while terminal active
if ('wakeLock' in navigator) {
    wakeLock = await navigator.wakeLock.request('screen');
}
```

## Keyboard Handling
```javascript
// Prevent viewport shift when keyboard appears
terminal.onFocus = () => {
    document.body.style.height = window.innerHeight + 'px';
};
```

# Color System
```css
:root {
    --bg-primary: #0f172a;      /* Deep navy */
    --bg-secondary: #1e293b;    /* Slate */
    --text-primary: #f1f5f9;    /* Off-white */
    --accent-green: #10b981;    /* Connected */
    --accent-red: #ef4444;      /* Disconnected */
    --accent-yellow: #f59e0b;   /* Reconnecting */
    --terminal-bg: #1a1a2e;     /* Terminal background */
}
```

# Typography
```css
/* Terminal */
.terminal {
    font-family: 'JetBrains Mono', 'SF Mono', Consolas, monospace;
    font-size: 14px;
    line-height: 1.4;
}

/* UI */
body {
    font-family: -apple-system, system-ui, sans-serif;
}
```

# Responsive Breakpoints
```css
/* Phone (default): 320-768px */
.terminal { font-size: 12px; }

/* Tablet: 768px+ */
@media (min-width: 768px) {
    .terminal { font-size: 14px; }
}

/* Desktop: 1024px+ */
@media (min-width: 1024px) {
    .terminal { font-size: 16px; }
    .container { max-width: 1200px; }
}
```

# Connection States

## Loading
```html
<div class="terminal-skeleton">
    <div class="line-skeleton"></div>
    <div class="cursor-blink">█</div>
</div>
```

## Disconnected
```html
<div class="connection-overlay">
    <div class="status-card">
        <div class="spinner"></div>
        <p>Reconnecting...</p>
        <button>Retry Now</button>
    </div>
</div>
```

## Empty State
```html
<div class="empty-state">
    <div class="empty-icon">📱</div>
    <h3>No sessions yet</h3>
    <p>Start Claude Code on your Mac</p>
</div>
```

# PWA Configuration
```json
{
    "name": "Claude on the Go",
    "short_name": "Claude Go",
    "display": "standalone",
    "orientation": "portrait",
    "theme_color": "#1e293b",
    "background_color": "#0f172a"
}
```

# Performance Targets
- Time to connect: < 3 seconds
- Terminal latency: < 50ms
- Memory footprint: < 30MB
- Lighthouse PWA score: > 95
- Reconnection success: > 95%

# Accessibility
- ARIA labels on all interactive elements
- Keyboard navigation support
- High contrast mode support
- Screen reader compatible terminal output

# Common Issues
- **Text too small**: Pinch to zoom, persists per device
- **Keyboard covers terminal**: Viewport management handles this
- **Connection drops on sleep**: Wake lock + auto-reconnect
- **Can't paste**: Long-press or two-finger tap
- **Voice input fails**: HTTPS required (use ngrok for testing)

# Native App Path
- **Phase 1** (Current): PWA only
- **Phase 2** (Month 4): Capacitor wrapper for app stores
- **Phase 3** (Month 6+): Native features (biometric, notifications, Siri)
