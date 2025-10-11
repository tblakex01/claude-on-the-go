# Push Notifications for claude-on-the-go

## Overview

Get instant notifications on your phone when Claude needs your input. Works even when the app is closed or your phone is locked.

**Supported Services:**
- **Pushover**: Simple, reliable push notifications ($5 one-time)
- **ntfy.sh**: Free, self-hostable, no account required
- **Telegram**: Free via Telegram Bot API

## Quick Start

### Option 1: Pushover (Recommended for iOS)

1. **Install Pushover app** ($5 one-time purchase)
   - iOS: https://apps.apple.com/us/app/pushover-notifications/id506088175
   - Android: https://play.google.com/store/apps/details?id=net.superblock.pushover

2. **Get your User Key**
   - Log in to https://pushover.net
   - Copy your User Key from the dashboard

3. **Configure claude-on-the-go**
   ```bash
   echo "PUSHOVER_USER_KEY=your_user_key_here" >> .env
   ```

4. **Restart server**
   ```bash
   ./start.sh
   ```

That's it! You'll now receive notifications when Claude needs input.

### Option 2: ntfy.sh (Free, No Account)

1. **Install ntfy app** (free)
   - iOS: https://apps.apple.com/us/app/ntfy/id1625396347
   - Android: https://play.google.com/store/apps/details?id=io.heckel.ntfy

2. **Choose a unique topic name** (e.g., `claude-alice-iphone`)
   - Must be unique across all ntfy users
   - Use a random string for privacy

3. **Subscribe in the app**
   - Open ntfy app
   - Tap "+" to add subscription
   - Enter your topic name
   - Done!

4. **Configure claude-on-the-go**
   ```bash
   echo "NTFY_TOPIC=your-unique-topic-name" >> .env
   ```

5. **Restart server**
   ```bash
   ./start.sh
   ```

### Option 3: Telegram Bot

1. **Create a Telegram bot**
   - Message @BotFather on Telegram
   - Send `/newbot` and follow instructions
   - Copy the bot token

2. **Get your Chat ID**
   - Message @userinfobot on Telegram
   - Copy your numeric chat ID

3. **Configure claude-on-the-go**
   ```bash
   echo "TELEGRAM_BOT_TOKEN=your_bot_token" >> .env
   echo "TELEGRAM_CHAT_ID=your_chat_id" >> .env
   ```

4. **Restart server**
   ```bash
   ./start.sh
   ```

## How It Works

### Prompt Detection

The system automatically detects when Claude is waiting for user input by analyzing terminal output patterns:

- "What would you like to do?"
- "How would you like to proceed?"
- "Would you like me to..."
- "Should I..."
- And many more patterns

### Debouncing

To prevent notification spam, the system uses a 30-second debounce window. If Claude asks multiple questions rapidly, you'll only receive one notification.

### Session URL

Notifications include a direct link to your Claude session. Tapping the notification opens the PWA immediately.

## Advanced Configuration

### Multiple Services

You can enable multiple notification services simultaneously:

```bash
# .env file
PUSHOVER_USER_KEY=your_pushover_key
NTFY_TOPIC=your_ntfy_topic
TELEGRAM_BOT_TOKEN=your_bot_token
TELEGRAM_CHAT_ID=your_chat_id
```

Notifications will be sent to ALL enabled services in parallel.

### Custom ntfy Server

If you're self-hosting ntfy:

```bash
NTFY_TOPIC=your_topic
NTFY_SERVER=https://your-ntfy-server.com
NTFY_TOKEN=your_auth_token  # Optional, for private topics
```

### Custom Pushover App Token

By default, claude-on-the-go uses its own Pushover app token. To use your own:

```bash
PUSHOVER_USER_KEY=your_user_key
PUSHOVER_APP_TOKEN=your_app_token
```

### Notification Priority

All Claude prompt notifications are sent with **high priority** to ensure they break through Do Not Disturb mode.

## Testing Notifications

Test your notification setup:

```bash
# From project root
python3 -m integrations.notifications
```

This will:
1. Check which services are configured
2. Send a test notification
3. Report success/failure

Expected output:
```
[NOTIFICATIONS] Pushover notifier enabled
✅ Test notification sent successfully!
```

## Troubleshooting

### Notifications not arriving

**Check backend logs:**
```bash
# Look for notification service initialization
[NOTIFICATIONS] Pushover notifier enabled
[NOTIFICATIONS] ntfy notifier enabled
```

If you don't see these logs, your environment variables aren't set correctly.

**Verify environment variables:**
```bash
# From project root
source venv/bin/activate
python3 -c "import os; print(os.getenv('PUSHOVER_USER_KEY'))"
```

### Pushover: "Invalid user key"

- Double-check your user key from https://pushover.net
- Make sure there are no extra spaces or quotes
- User key should be 30 characters

### ntfy: Notifications delayed

- ntfy.sh free tier has no delivery guarantees
- Consider self-hosting ntfy for better reliability
- Check ntfy app settings (notification permissions, battery optimization)

### Telegram: "Unauthorized"

- Verify bot token from @BotFather
- Make sure you've started a conversation with your bot
- Chat ID must be numeric (not username)

### Still not working?

Enable debug mode and check logs:

```bash
# Add to .env
LOG_LEVEL=DEBUG

# Restart and watch logs
./start.sh
```

## Privacy & Security

### Data Transmission

- Notifications are sent directly from your Mac to the notification service
- No data is sent to claude-on-the-go servers (we don't have any!)
- Notification content is minimal: "Claude needs your input"

### Service Security

- **Pushover**: Encrypted, US-based, established company
- **ntfy.sh**: Open source, self-hostable, end-to-end encryption available
- **Telegram**: Encrypted, widely used, open protocol

### Best Practices

1. **Use unique ntfy topics** - don't use obvious names like "claude"
2. **Enable private topics** - use NTFY_TOKEN for authentication
3. **Rotate tokens regularly** - especially for Telegram bots
4. **Don't share .env** - add it to .gitignore (already done)

## Architecture

### Backend Integration

```python
# In legacy/backend/app.py
from integrations import NotificationService, PromptDetector

# Initialize in ConnectionManager
self.notification_service = NotificationService()
self.prompt_detector = PromptDetector(debounce_seconds=30.0)

# In output handler
async def _handle_claude_output(self, text: str):
    if self.prompt_detector and not self.active_connections:
        self.prompt_detector.add_output(text)
        if self.prompt_detector.should_notify():
            await self.notification_service.notify_claude_prompt(session_url)
```

### Notification Services

Located in `integrations/notifications.py`:

- **NotificationService**: Manages multiple notifiers
- **PushoverNotifier**: Pushover API client
- **NtfyNotifier**: ntfy.sh API client
- **TelegramNotifier**: Telegram Bot API client

All notifiers are async and handle errors gracefully.

### Prompt Detection

Located in `integrations/prompt_detector.py`:

- Pattern-based detection using regex
- Debouncing to prevent spam
- Context extraction for notification body
- Ignore patterns (exit messages, etc.)

## Future Enhancements

### Planned (Week 4)

- [ ] Web Push API integration (browser-based notifications)
- [ ] Custom notification sounds
- [ ] Notification actions (reply from notification)
- [ ] Notification history in app

### Under Consideration

- [ ] Smart Do Not Disturb (quiet hours)
- [ ] Notification grouping (multiple prompts)
- [ ] Custom prompt patterns (user-defined)
- [ ] iOS/Android native apps (better notification control)

## FAQ

**Q: Do notifications work when my phone is locked?**
A: Yes! All three services support lock screen notifications.

**Q: Will I get notifications if I'm actively using the app?**
A: No. Notifications only trigger when there are no active WebSocket connections (you're away).

**Q: Can I customize the notification message?**
A: Not yet. The message is currently fixed to prevent leaking sensitive terminal output. Custom messages are planned for a future release.

**Q: Does this work with Do Not Disturb mode?**
A: Yes, with high-priority notifications. You may need to configure your notification app's DND settings.

**Q: Can I use multiple devices?**
A: Yes! Set up the same notification service on multiple devices (phone, tablet, watch).

**Q: What about battery life?**
A: Minimal impact. Notifications are push-based (server-to-device), not polling.

## Cost Comparison

| Service | Cost | Pros | Cons |
|---------|------|------|------|
| **Pushover** | $5 one-time | Reliable, iOS-optimized, rich notifications | One-time cost |
| **ntfy.sh** | Free | Open source, self-hostable, no account | Delivery not guaranteed (free tier) |
| **Telegram** | Free | Widely used, free forever, easy setup | Requires Telegram app |

## Recommendations

- **iOS users**: Use Pushover (best reliability)
- **Android users**: Use ntfy.sh (free, works great on Android)
- **Already use Telegram**: Use Telegram (easiest setup)
- **Privacy-conscious**: Self-host ntfy.sh

## Support

Having issues? Check:
1. [Troubleshooting](#troubleshooting) section above
2. Project README.md
3. GitHub Issues: https://github.com/yourusername/claude-on-the-go/issues

---

**Status**: ✅ Push Notifications Complete (Week 3)

**Next**: PWA Native Features (Week 4)
