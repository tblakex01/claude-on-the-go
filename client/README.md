# Client

Modern web client and Progressive Web App (PWA) for claude-on-the-go.

## Purpose

This directory contains the frontend implementations that connect to the server and provide terminal access.

## Structure

### `/web`
Standard web client for desktop and mobile browsers.

**Features:**
- Responsive terminal display (xterm.js)
- WebSocket connection management
- Exponential backoff reconnection
- Mobile-optimized UI
- Clipboard synchronization
- iOS safe area support

### `/pwa`
Progressive Web App with enhanced mobile capabilities.

**Features:**
- Installable on home screen
- Offline capability with service workers
- Background sync for clipboard
- Push notification support
- App manifest for native feel

## Technology Stack

- **xterm.js 5.3+**: Terminal emulation
  - DOM renderer on mobile (better ANSI support)
  - Canvas renderer on desktop (better performance)
- **Vanilla JavaScript**: No framework dependencies
- **CSS Grid/Flexbox**: Modern responsive layout
- **Service Workers**: PWA offline support
- **Web APIs**: Clipboard, Notifications, WebSocket

## Mobile Optimizations

1. **Viewport Handling**
   - iOS safe area insets
   - Keyboard-aware layout
   - Dynamic viewport resize

2. **Touch Interactions**
   - Smooth scrolling with momentum
   - Pinch to zoom for terminal
   - Long-press for context menu

3. **Performance**
   - Lazy loading of terminal themes
   - Efficient DOM updates
   - Debounced resize handlers

## Development

```bash
# Serve web client
cd client/web
python -m http.server 8001

# Build PWA
cd client/pwa
npm run build
```

## Configuration

The client auto-detects the server URL from:
1. Current page origin (if served by backend)
2. Environment variable `BACKEND_URL`
3. localStorage cached URL
4. Falls back to scanning local network
