# Progressive Web App (PWA) Implementation

## Overview

Claude-onTheGo is now a fully installable Progressive Web App, providing a native app experience on mobile and desktop devices.

## Features

### 1. App Installation
- **Add to Home Screen**: One-tap installation from browser
- **Standalone Display**: Runs in fullscreen without browser chrome
- **App Icons**: Custom icons for all platforms (72px - 512px)
- **Splash Screen**: Branded loading screen on launch

### 2. Offline Support
- **Service Worker**: Caches app shell for offline access
- **Network-First Strategy**: Attempts network, falls back to cache
- **Offline Page**: Custom offline indicator when server unavailable
- **Background Sync**: Updates cache in background

### 3. Native Features
- **Install Banner**: Smart prompts for app installation
- **Share Target**: Receive shared content from other apps
- **Shortcuts**: Quick actions from home screen icon
- **Theme Color**: Matches system UI with app brand

## Files Structure

```
client/pwa/
├── manifest.json          # PWA manifest with app metadata
├── sw.js                  # Service Worker for caching
├── offline.html           # Offline fallback page
├── generate-icons.html    # Icon generator tool
└── icons/                 # App icons (generated)
    ├── icon-72x72.png
    ├── icon-96x96.png
    ├── icon-128x128.png
    ├── icon-144x144.png
    ├── icon-152x152.png
    ├── icon-192x192.png
    ├── icon-384x384.png
    └── icon-512x512.png
```

## Installation

### Generate Icons

1. Open `client/pwa/generate-icons.html` in browser
2. Icons will auto-download
3. Save them to `legacy/frontend/icons/` directory

Or use an online tool like [PWA Asset Generator](https://www.pwabuilder.com/):
```bash
npx pwa-asset-generator logo.svg legacy/frontend/icons/
```

### Deploy PWA Files

PWA files are automatically copied to `legacy/frontend/` for production:

```bash
# Already done - files are in place
# - manifest.json
# - sw.js
# - offline.html
```

## Testing

### Desktop (Chrome)
1. Start server: `./start.sh`
2. Open `http://localhost:8001` in Chrome
3. Look for install icon in address bar
4. Click to install as PWA

### Mobile (iOS Safari)
1. Start server: `./start.sh`
2. Open on iPhone Safari
3. Tap share button → "Add to Home Screen"
4. App installs with custom icon

### Mobile (Android Chrome)
1. Start server: `./start.sh`
2. Open on Android Chrome
3. Banner appears: "Install Claude-onTheGo"
4. Tap "Install" button

## Lighthouse PWA Audit

Target scores (run with `npx lighthouse`):

```bash
npx lighthouse http://localhost:8001 \
  --only-categories=pwa \
  --view
```

**Target Metrics:**
- ✅ Installable: 100%
- ✅ PWA Optimized: 100%
- ✅ Fast and reliable: > 90%
- ✅ Works offline: Yes
- ✅ Service Worker registered: Yes

## Manifest Configuration

Key settings in `manifest.json`:

```json
{
  "name": "Claude-onTheGo",
  "short_name": "ClaudeGo",
  "display": "standalone",        // Fullscreen, no browser UI
  "theme_color": "#1e1e1e",       // System UI color
  "background_color": "#1e1e1e",  // Splash screen color
  "orientation": "portrait-primary" // Lock to portrait
}
```

## Service Worker Strategy

### Caching Strategy

1. **App Shell** (precached on install):
   - index.html
   - style.css
   - terminal.js
   - xterm.js libraries

2. **Runtime** (cached on first use):
   - Icons
   - Fonts
   - Other assets

3. **Network-First** (always fresh):
   - WebSocket connections
   - API calls

### Cache Versioning

Service worker auto-updates with version bumps:

```javascript
// sw.js
const CACHE_VERSION = 'v1';
const CACHE_NAME = `claude-on-the-go-${CACHE_VERSION}`;
```

Update `CACHE_VERSION` to force cache refresh.

## Push Notifications (Foundation)

Service worker includes push notification handlers:

```javascript
// Already implemented in sw.js
self.addEventListener('push', event => {
  // Handle push notifications
});

self.addEventListener('notificationclick', event => {
  // Handle notification clicks
});
```

**Next Steps** (Week 3 roadmap):
- Web Push API integration
- Notification permission flow
- Claude prompt detection
- One-tap to open from notification

## iOS Specific Features

### Add to Home Screen

iOS uses different meta tags:

```html
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
<meta name="apple-mobile-web-app-title" content="ClaudeGo">
<link rel="apple-touch-icon" href="/icons/icon-192x192.png">
```

### iOS Limitations

- No install banner (user must manually add)
- No push notifications (Web Push not supported)
- Service Worker support limited

**Workarounds:**
- Show manual instructions for iOS
- Use app shortcuts as alternative to notifications

## Android Specific Features

### Install Banner

Custom install prompt with dismiss option:

```javascript
window.addEventListener('beforeinstallprompt', (e) => {
  e.preventDefault();
  deferredPrompt = e;
  // Show custom banner
});
```

### WebAPK

Chrome on Android can generate a WebAPK for better integration:
- Appears in app drawer
- Share target registration
- Deep linking support

## Debugging

### Chrome DevTools

1. Open DevTools → Application tab
2. Check:
   - **Manifest**: Verify all fields
   - **Service Workers**: Check registration
   - **Cache Storage**: Inspect cached files

### Console Logs

Service Worker logs:
```
[SW] Install event
[SW] Precaching app shell
[SW] Activate event
[SW] Service Worker loaded
```

PWA logs:
```
[PWA] Service Worker registered
[PWA] Running as installed app
```

### Common Issues

**Service Worker not registering:**
- Must use HTTPS or localhost
- Check console for errors
- Verify sw.js path is correct

**Install banner not showing:**
- PWA criteria not met (check Lighthouse)
- User already dismissed
- Already installed

**Icons not loading:**
- Check icon paths in manifest
- Verify icons exist in /icons/ directory
- Check browser console for 404s

## Production Checklist

Before deploying PWA to production:

- [ ] Generate all icon sizes (72px - 512px)
- [ ] Test installation on iOS Safari
- [ ] Test installation on Android Chrome
- [ ] Verify offline fallback works
- [ ] Run Lighthouse PWA audit (score > 90)
- [ ] Test service worker updates
- [ ] Verify manifest loads correctly
- [ ] Test on multiple devices
- [ ] Check analytics (optional)

## Analytics (Optional)

Track PWA installations:

```javascript
// Track install
window.addEventListener('appinstalled', () => {
  gtag('event', 'pwa_installed');
});

// Track if running as PWA
if (window.matchMedia('(display-mode: standalone)').matches) {
  gtag('event', 'pwa_launch');
}
```

## Future Enhancements

### Week 3: Push Notifications
- Web Push API integration
- Background sync
- Badge notifications

### Week 5: Native App
- Capacitor wrapper
- App Store submission
- Native features (biometric auth)

### Week 7: Advanced PWA
- Background fetch
- Periodic background sync
- File handling API

## Resources

- [PWA Checklist](https://web.dev/pwa-checklist/)
- [Service Worker API](https://developer.mozilla.org/en-US/docs/Web/API/Service_Worker_API)
- [Web App Manifest](https://developer.mozilla.org/en-US/docs/Web/Manifest)
- [PWA Builder](https://www.pwabuilder.com/)

---

**Status**: ✅ PWA Implementation Complete (Week 2)

**Next**: Push Notifications (Week 3)
