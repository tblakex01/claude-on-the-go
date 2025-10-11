# Installation Guide

## Quick Install (PyPI)

The easiest way to install claude-on-the-go is via pip:

```bash
# Install from PyPI
pip install claude-on-the-go

# Start the server
claude-on-the-go start

# Open on your phone
# Scan the QR code or visit http://your-mac-ip:8001
```

That's it! The `claude-on-the-go` command is now available system-wide.

## Prerequisites

### Required

- **Python 3.9+** - Check with `python3 --version`
- **Claude Code CLI** - Install from https://claude.ai/download
- **macOS or Linux** - Windows support via WSL

### Optional

- **Push Notifications**: Sign up for Pushover, ntfy.sh, or Telegram
- **Tailscale**: For remote access over the internet

## Installation Methods

### Method 1: PyPI (Recommended)

Install the latest stable release from PyPI:

```bash
# Create virtual environment (recommended)
python3 -m venv ~/.claude-on-the-go-env
source ~/.claude-on-the-go-env/bin/activate

# Install
pip install claude-on-the-go

# Verify installation
claude-on-the-go version
```

### Method 2: From Source (Development)

Clone and install from GitHub:

```bash
# Clone repository
git clone https://github.com/MatthewJamisonJS/claude-on-the-go.git
cd claude-on-the-go

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install in editable mode
pip install -e .

# Verify installation
claude-on-the-go version
```

### Method 3: Using start.sh (Legacy)

For backward compatibility, you can still use the legacy startup script:

```bash
# Clone repository
git clone https://github.com/MatthewJamisonJS/claude-on-the-go.git
cd claude-on-the-go

# Run install script
./install.sh

# Start servers
./start.sh
```

## First Run

After installation, start the server:

```bash
claude-on-the-go start
```

You should see:

```
🚀 Starting claude-on-the-go...

╔══════════════════════════════════════════════════════════╗
║  Claude-onTheGo - Mobile Terminal Access                ║
╚══════════════════════════════════════════════════════════╝

📱 Connect from your phone:
   http://192.168.1.100:8001

🔍 Or scan this QR code:
[QR CODE appears here]

Backend:  http://192.168.1.100:8000
Frontend: http://192.168.1.100:8001

Press Ctrl+C to stop
```

## Configuration

### Environment Variables

Create a `.env` file in your project directory:

```bash
# Server Configuration
HOST=0.0.0.0                    # Bind address (auto-detect by default)
FRONTEND_PORT=8001              # Frontend port
BACKEND_PORT=8000               # Backend port

# Claude Configuration
CLAUDE_CODE_PATH=/usr/local/bin/claude  # Path to Claude CLI

# Session Configuration
SESSION_EXPIRE_DAYS=7           # Auto-cleanup expired sessions

# Push Notifications (Optional)
PUSHOVER_USER_KEY=              # Pushover user key
NTFY_TOPIC=                     # ntfy.sh topic name
TELEGRAM_BOT_TOKEN=             # Telegram bot token
TELEGRAM_CHAT_ID=               # Telegram chat ID

# Security (Optional)
REQUIRE_PASSWORD=false          # Enable password auth
AUTH_TOKEN=                     # Authentication token

# Features
ENABLE_CLIPBOARD_SYNC=true      # Mac ↔ Phone clipboard sync
CLIPBOARD_SYNC_INTERVAL=2.0     # Sync interval (seconds)
```

### Push Notifications Setup

See [PUSH_NOTIFICATIONS.md](./PUSH_NOTIFICATIONS.md) for detailed setup instructions.

**Quick start:**

```bash
# Pushover (recommended for iOS)
echo "PUSHOVER_USER_KEY=your_key" >> .env

# ntfy.sh (free, no account)
echo "NTFY_TOPIC=your-unique-topic" >> .env

# Telegram Bot
echo "TELEGRAM_BOT_TOKEN=your_token" >> .env
echo "TELEGRAM_CHAT_ID=your_chat_id" >> .env
```

## CLI Commands

The `claude-on-the-go` command provides several subcommands:

### Start Server
```bash
claude-on-the-go start
```

### Stop Server
```bash
claude-on-the-go stop
```

### Restart Server
```bash
claude-on-the-go restart
```

### Check Status
```bash
claude-on-the-go status
```

Output:
```
Claude-onTheGo Status
==================================================
✅ Backend:  Running (PID 12345)
✅ Frontend: Running (PID 12346)

📱 Frontend: http://192.168.1.100:8001
🔌 Backend:  http://192.168.1.100:8000
```

### View Logs
```bash
# View all logs
claude-on-the-go logs

# Backend logs only
claude-on-the-go logs --backend

# Frontend logs only
claude-on-the-go logs --frontend
```

### Show QR Code
```bash
claude-on-the-go qr
```

### Version Info
```bash
claude-on-the-go version
```

## Upgrading

### From PyPI

```bash
pip install --upgrade claude-on-the-go
```

### From Source

```bash
cd claude-on-the-go
git pull
pip install -e . --upgrade
```

## Uninstallation

### PyPI Installation

```bash
pip uninstall claude-on-the-go
```

### Source Installation

```bash
cd claude-on-the-go
pip uninstall claude-on-the-go
rm -rf venv  # Remove virtual environment
```

## Troubleshooting

### Command not found: claude-on-the-go

**Problem**: Shell can't find the command after installation.

**Solutions**:

1. **Ensure pip install location is in PATH**:
   ```bash
   # Check where pip installs scripts
   python3 -m site --user-base

   # Add to PATH (add to ~/.bashrc or ~/.zshrc)
   export PATH="$HOME/.local/bin:$PATH"
   ```

2. **Use full path**:
   ```bash
   ~/.local/bin/claude-on-the-go start
   ```

3. **Reinstall in user mode**:
   ```bash
   pip install --user claude-on-the-go
   ```

### ModuleNotFoundError: No module named 'claude_on_the_go'

**Problem**: Python can't find the installed package.

**Solutions**:

1. **Check installation**:
   ```bash
   pip list | grep claude-on-the-go
   ```

2. **Reinstall**:
   ```bash
   pip uninstall claude-on-the-go
   pip install claude-on-the-go
   ```

3. **Check Python version**:
   ```bash
   python3 --version  # Should be 3.9+
   ```

### Server won't start

**Problem**: `claude-on-the-go start` fails or hangs.

**Solutions**:

1. **Check Claude CLI installation**:
   ```bash
   which claude
   claude --version
   ```

2. **Check ports availability**:
   ```bash
   lsof -i :8000  # Backend
   lsof -i :8001  # Frontend
   ```

3. **View detailed logs**:
   ```bash
   claude-on-the-go logs
   ```

4. **Check for existing instances**:
   ```bash
   claude-on-the-go status
   claude-on-the-go stop  # Stop if running
   ```

### Can't connect from phone

**Problem**: Phone can't reach the server.

**Solutions**:

1. **Verify same WiFi network**: Mac and phone must be on the same network

2. **Check firewall**:
   ```bash
   # macOS: Allow ports 8000-8001
   # System Preferences > Security & Privacy > Firewall
   ```

3. **Check IP address**:
   ```bash
   ifconfig | grep "inet "  # Find your local IP
   ```

4. **Try alternative ports**:
   ```bash
   FRONTEND_PORT=8080 claude-on-the-go start
   ```

### Permission denied errors

**Problem**: Can't write to directories or execute files.

**Solutions**:

1. **Install in user mode**:
   ```bash
   pip install --user claude-on-the-go
   ```

2. **Check directory permissions**:
   ```bash
   ls -la ~/.claude-on-the-go-env
   ```

3. **Use virtual environment**:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install claude-on-the-go
   ```

## Platform-Specific Notes

### macOS

- **Firewall**: Allow incoming connections for ports 8000-8001
- **Gatekeeper**: May prompt on first run (click "Open" in System Preferences)
- **Terminal permissions**: Grant Terminal.app access to Claude if prompted

### Linux

- **Port binding**: May need sudo for ports < 1024
- **Systemd service**: Consider creating a systemd unit for auto-start
- **SELinux**: May need to adjust policies if enabled

### Windows (WSL)

- **WSL2 required**: Install from Microsoft Store
- **Network bridge**: WSL2 uses NAT, may need port forwarding
- **Firewall**: Allow ports in Windows Firewall

## Next Steps

After successful installation:

1. **Test connection**: Open http://your-ip:8001 on your phone
2. **Install as PWA**: Tap "Add to Home Screen" for app-like experience
3. **Configure notifications**: Set up Pushover, ntfy, or Telegram
4. **Customize settings**: Edit .env file for your preferences
5. **Read documentation**: Check docs/ directory for advanced features

## Getting Help

- **Documentation**: [README.md](../README.md)
- **Issues**: https://github.com/MatthewJamisonJS/claude-on-the-go/issues
- **Discussions**: https://github.com/MatthewJamisonJS/claude-on-the-go/discussions

---

**Installation complete!** 🎉

Run `claude-on-the-go start` to begin using claude-on-the-go.
