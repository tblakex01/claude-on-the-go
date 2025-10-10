# Integrations

External service integrations for claude-on-the-go.

## Purpose

This directory contains integrations with external services and platforms to enhance the claude-on-the-go experience.

## Components

### Push Notifications
Forward Claude Code prompts to your mobile device via push notifications.

**Supported Services:**
- **Pushover**: Simple push notifications with priority levels
- **ntfy**: Self-hosted push notification service
- **Telegram**: Bot-based notifications with rich formatting

**Features:**
- Configurable notification triggers
- Priority levels (info, warning, error)
- Rate limiting to prevent spam
- Message truncation for long outputs

### Tailscale Integration
Access your claude-on-the-go server from anywhere via Tailscale VPN.

**Features:**
- Auto-detect Tailscale IP addresses
- QR code generation with Tailscale URL
- Seamless integration with existing setup
- No port forwarding required

### QR Code Generation
Generate QR codes for easy mobile connection.

**Features:**
- Auto-detect local IP addresses
- mDNS-friendly URLs (.local domains)
- Fallback to direct IP if mDNS unavailable
- Terminal-friendly ASCII QR codes
- PNG/SVG export for sharing

### Voice Input (Experimental)
Voice-to-text for mobile terminal input.

**Features:**
- Web Speech API integration
- Push-to-talk interface
- Background noise filtering
- Auto-submit on silence detection

## Configuration

Set environment variables in `.env`:

```bash
# Pushover
PUSHOVER_USER_KEY=your_user_key
PUSHOVER_APP_TOKEN=your_app_token

# ntfy
NTFY_TOPIC=your_topic_name
NTFY_SERVER=https://ntfy.sh  # Optional, defaults to ntfy.sh

# Telegram
TELEGRAM_BOT_TOKEN=your_bot_token
TELEGRAM_CHAT_ID=your_chat_id

# Tailscale
TAILSCALE_ENABLED=true
```

## Usage Example

```python
from integrations.notifications import send_notification

send_notification(
    message="Claude Code is requesting input",
    priority="high",
    service="pushover"
)
```

## Dependencies

- `requests` for HTTP API calls
- `qrcode` for QR code generation
- `python-telegram-bot` for Telegram integration
- Tailscale CLI (`tailscale` command)
