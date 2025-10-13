# claude-on-the-go

[![CI](https://github.com/MatthewJamisonJS/claude-on-the-go/actions/workflows/ci.yml/badge.svg)](https://github.com/MatthewJamisonJS/claude-on-the-go/actions/workflows/ci.yml)
[![Security](https://img.shields.io/badge/security-actively%20maintained-brightgreen)]()
[![License](https://img.shields.io/badge/license-MIT-blue.svg)]()

> Control your Mac's `claude` CLI from your phone. Because sometimes you just want to code from the couch.

Use Claude on your iPhone, Android, or any device with a browser - while your Mac does the heavy lifting. No cloud sync, no data leaks, just your local network keeping things fast and private.

## Table of Contents

- [Quick Start](#quick-start)
  - [Local WiFi (Same Network)](#local-wifi-same-network)
  - [Remote Access (Anywhere)](#remote-access-anywhere)
- [SSH + Terminal Access](#ssh--terminal-access)
  - [Why SSH?](#why-ssh)
  - [Connection Options](#connection-options)
- [What's New in v1.3](#whats-new-in-v13)
- [Requirements](#requirements)
- [Features](#features)
- [Configuration](#configuration)
- [Troubleshooting](#troubleshooting)
- [Documentation](#documentation)
- [Contributing](#contributing)
- [License](#license)

## Quick Start

### Local WiFi (Same Network)

```bash
git clone https://github.com/MatthewJamisonJS/claude-on-the-go.git
cd claude-on-the-go
./install.sh
./start.sh
```

📲 Scan the QR code with your phone → instant access!

### Remote Access (Anywhere)

**Two approaches:** Access via browser UI or direct SSH terminal

**Option 1: Browser UI (WebSocket)**
- Use VPN (Tailscale, ZeroTier, etc.) or port forwarding
- See [Remote Access Setup](docs/REMOTE_ACCESS.md) for detailed VPN configuration
- Run `./start.sh` on Mac, access from phone browser

**Option 2: SSH Terminal (Recommended for CLI users)**
- Direct access to Claude CLI, no server needed
- Connect via SSH, run `claude` commands directly
- See [SSH + Terminal Access](#ssh--terminal-access) below for setup options

**Quick example using Tailscale + SSH:**
```bash
# One-time: Install VPN and enable SSH on Mac
./scripts/tailscale-setup.sh

# From phone terminal (Termius, Blink Shell, iSH)
ssh your-username@your-tailscale-ip
claude "help me refactor this code"
```

📖 **Comprehensive guides:** [Remote Access Setup](docs/REMOTE_ACCESS.md) | [SSH Authentication](docs/TAILSCALE_SSH_CLAUDE.md)

## SSH + Terminal Access

### Why SSH?

SSH gives you **direct access** to Claude CLI on your Mac - no WebSocket server, no browser, just the real `claude` command.

**Benefits:**
- ✅ **Fastest workflow:** `ssh → claude "your prompt"` (2 commands, done)
- ✅ **Works anywhere:** Same WiFi, cellular, coffee shop, airport
- ✅ **Native experience:** Real terminal, not browser emulation
- ✅ **Zero overhead:** No server to start, no port conflicts
- ✅ **Better for CLI users:** Full terminal features (tmux, vim, etc.)

**When to use:**
- Quick commands and interactions
- You're comfortable with terminal apps
- Want the absolute fastest access
- Remote access without starting a server

**When to use Browser UI instead:**
- Prefer visual interface over terminal
- Need rich formatting/styling
- Want to use from desktop browser
- Demo/presentation purposes

### Connection Options

Choose the method that fits your use case:

#### Option A: Local Network SSH (Simplest)

Connect directly via WiFi when you're home.

**Requirements:**
- Mac and phone on same WiFi network
- SSH enabled on Mac: `sudo systemsetup -setremotelogin on`
- Terminal app on phone (Termius, Blink Shell, iSH)

**Steps:**
```bash
# 1. Find your Mac's IP (on Mac)
ifconfig | grep "inet " | grep -v 127.0.0.1
# Example output: inet 192.168.1.100

# 2. Connect from phone terminal
ssh your-username@192.168.1.100

# 3. Use Claude
claude "help me debug this Python code"
```

**Pros:** Zero setup, instant, no external services
**Cons:** Same WiFi only, IP changes on network switch

---

#### Option B: VPN (Recommended for Remote Access)

Create a private network that works anywhere with internet.

**VPN Options:**

| Solution | Setup Time | Cost | Best For |
|----------|------------|------|----------|
| **Tailscale** | 5 min | Free | Beginners, easiest setup |
| **ZeroTier** | 10 min | Free | Alternative to Tailscale |
| **WireGuard** | 30+ min | Free | DIY, full control |
| **Headscale** | 60+ min | Free | Self-hosted Tailscale |

**Example: Using Tailscale**

**One-time setup:**
```bash
# On Mac: Install and configure
./scripts/tailscale-setup.sh  # Automated script
# OR manual: https://tailscale.com/download/mac

# On phone: Install Tailscale app from App Store/Play Store
# Log in with same account as Mac
```

**Daily use:**
```bash
# From phone terminal (Termius, Blink Shell, etc.)
ssh your-username@100.101.102.103  # Your Mac's VPN IP
claude "write a function to parse JSON"
```

**Pros:** Works anywhere, survives network changes, encrypted
**Cons:** Requires VPN app, slight latency increase (20-50ms)

**Other VPN solutions work similarly:**
- ZeroTier: Create network at https://my.zerotier.com
- WireGuard: Configure peers manually
- Headscale: Self-hosted Tailscale coordinator

📖 **Detailed VPN setup:** [Remote Access Guide](docs/REMOTE_ACCESS.md)
📖 **SSH authentication:** [Tailscale SSH Claude](docs/TAILSCALE_SSH_CLAUDE.md)

---

#### Option C: Port Forwarding (Advanced Users)

Expose SSH through your router to the internet.

**Requirements:**
- Router admin access
- Static/dynamic DNS (DuckDNS, No-IP, afraid.org)
- Understanding of security implications

**Steps:**
1. Configure router port forwarding: External 22 → Mac internal IP port 22
2. Set up dynamic DNS (if no static IP)
3. Harden SSH security (`/etc/ssh/sshd_config`)
4. Connect from anywhere: `ssh user@your-domain.duckdns.org`

**Security considerations:**
- ⚠️ Exposed to internet (SSH attacks common)
- ✅ Use SSH keys only, disable password auth
- ✅ Change default SSH port (22 → 2222)
- ✅ Use fail2ban to block brute force attempts
- ✅ Consider Cloudflare Tunnel as alternative

**Pros:** No third-party VPN service, full control
**Cons:** Security responsibility, complex setup, port conflicts

**Alternative: Temporary tunnels**
```bash
# ngrok (quick testing, not for production)
brew install ngrok
ngrok tcp 22
# Gives you: tcp://0.tcp.ngrok.io:12345

# Cloudflare Tunnel (better for long-term)
brew install cloudflared
cloudflared tunnel create claude-ssh
```

---

### Comparison Table

| Method | Setup Time | Works Remote | Latency | Security | Best For |
|--------|------------|--------------|---------|----------|----------|
| **Local SSH** | 30 sec | ❌ WiFi only | 5-10ms | Excellent | At home |
| **VPN (Tailscale)** | 5 min | ✅ Anywhere | 20-50ms | Excellent | Most users |
| **Port Forward** | 30+ min | ✅ Anywhere | 10-30ms | DIY | Power users |
| **Tunnel (ngrok)** | 2 min | ✅ Anywhere | 50-100ms | Good | Testing only |

### Terminal Apps

**iOS:**
- [**Termius**](https://termius.com/) - Free tier, beautiful UI, SSH key management
- [**Blink Shell**](https://blink.sh/) - $20/year, mosh support, best for developers
- [**iSH**](https://ish.app/) - Free, full Linux environment, Alpine-based

**Android:**
- [**Termux**](https://termux.com/) - Free, powerful Linux terminal, package manager
- [**JuiceSSH**](https://juicessh.com/) - Free, SSH-focused, port forwarding
- [**Termius**](https://termius.com/) - Cross-platform, sync across devices

### Quick Tips

**Skip password entry (SSH keys):**
```bash
# On phone terminal
ssh-keygen -t ed25519
ssh-copy-id user@your-mac-ip
# Now SSH works without password
```

**Use hostname instead of IP (mDNS):**
```bash
# Instead of: ssh user@192.168.1.100
ssh your-username@your-macbook.local
# Example: ssh john@Johns-MacBook-Pro.local
# Works on local networks automatically
```

**Keep connection alive:**
```bash
# Add to ~/.ssh/config on phone
Host *
  ServerAliveInterval 60
  ServerAliveCountMax 10
```

**For unstable connections (trains, planes):**
```bash
# Use mosh instead of SSH
brew install mosh  # On Mac
mosh user@your-ip  # From phone (Blink Shell includes mosh)
# Survives network changes, instant local echo
```

## What's New in v1.3

**SSH + Terminal Access:** Direct CLI access to Claude Code via SSH - no WebSocket server needed. Choose from multiple connection methods:
- Local SSH (same WiFi, instant)
- VPN solutions (Tailscale, ZeroTier, WireGuard)
- Port forwarding (advanced users)

**Access Methods Comparison:**
- **Browser UI** (local): 5-15ms latency, visual interface, same WiFi only
- **SSH Terminal** (remote): 20-50ms latency, works anywhere, CLI-first workflow

Use browser UI for visual experience at home. Use SSH + terminal for CLI workflow anywhere. Both methods are fully supported.

## Requirements

**Mac/Linux:**
- Python 3.9+
- [Claude Code CLI](https://claude.ai/download) installed
- Same WiFi network for Mac and phone (local access only)

**Mobile Device:**
- Any modern browser (Safari, Chrome, Firefox) for local access
- OR terminal app ([Blink Shell](https://blink.sh/), [Termius](https://termius.com/), [iSH](https://ish.app/)) for remote access

## Features

- ✅ **Security**: Rate limiting, auth tokens, input validation, CSP headers
- ✅ **Session Persistence**: Reconnect seamlessly, sessions survive disconnections
- ✅ **Clipboard Sync**: Bidirectional sync between Mac and phone
- ✅ **Terminal Themes**: Auto-detects Ghostty, iTerm2, Alacritty, Kitty, Terminal.app
- ✅ **Mobile Optimized**: iOS safe areas, responsive sizing, keyboard-aware
- ✅ **Remote Access**: SSH + VPN (multiple options) or port forwarding for anywhere connectivity
- ✅ **Production Ready**: 60-min stability testing, memory leak detection

📖 **Detailed features:** [FEATURES.md](FEATURES.md)

## Configuration

Edit `.env` to customize (all optional):

```bash
# Network (for remote browser UI access)
HOST=100.101.102.103            # Your VPN IP (secure) or localhost (local only)
BACKEND_PORT=8000               # Backend WebSocket port
FRONTEND_PORT=8001              # Frontend HTTP port
ALLOWED_ORIGINS=http://100.101.102.103:8001,http://localhost:8001  # VPN + local

# Security
ENABLE_AUTH=false               # Require token authentication
AUTH_TOKEN=your-secret-token    # Set your auth token

# Features
ENABLE_CLIPBOARD_SYNC=true      # Enable clipboard synchronization
CLIPBOARD_SYNC_INTERVAL=1.0     # Clipboard check interval (seconds)

# Logging
LOG_LEVEL=INFO                  # DEBUG, INFO, WARNING, ERROR
LOG_REDACTION=true              # Redact IPs/tokens from logs
```

## Troubleshooting

### Claude CLI Not Found
📥 Install from [https://claude.ai/download](https://claude.ai/download)

### Can't Connect from Phone (Local WiFi)
- Ensure you're on the same WiFi network
- Try the direct IP URL instead of `.local`
- Check Mac firewall settings (allow Python)

### Browser UI Not Loading (Remote Access)
```bash
# Check configuration
cat .env | grep -E "HOST|ALLOWED_ORIGINS"

# Should show (with your actual VPN IP):
# HOST=100.101.102.103
# ALLOWED_ORIGINS=http://100.101.102.103:8001,...

# If missing, add them (example using Tailscale):
VPN_IP=$(tailscale ip -4)  # Or get from your VPN solution
echo "HOST=$VPN_IP" >> .env
echo "ALLOWED_ORIGINS=http://$VPN_IP:8001,http://localhost:8001" >> .env
./stop.sh && ./start.sh
```

📖 **More troubleshooting:** [Remote Access Guide](docs/REMOTE_ACCESS.md#troubleshooting)

## Documentation

- **[SSH + Terminal Access](#ssh--terminal-access)** - Direct CLI access guide (this page)
- **[Remote Access Guide](docs/REMOTE_ACCESS.md)** - VPN setup and browser UI configuration
- **[SSH Authentication](docs/TAILSCALE_SSH_CLAUDE.md)** - Claude auth over SSH/Tailscale
- **[Features](FEATURES.md)** - Comprehensive feature documentation
- **[Security Policy](docs/SECURITY.md)** - Security best practices
- **[Architecture](ARCHITECTURE.md)** - Technical architecture details
- **[Adding Terminals](docs/ADDING_TERMINALS.md)** - How to add terminal parser support

## Contributing

Contributions welcome! Especially:
- New terminal parsers (see `docs/ADDING_TERMINALS.md`)
- Bug fixes and documentation improvements
- Performance optimizations

Please read [SECURITY.md](SECURITY.md) and [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md) before contributing.

## License

MIT License - see [LICENSE](LICENSE) file

Built for developers who want Claude in their pocket without compromising on security or control.

---

**Questions?** [Open an issue](https://github.com/MatthewJamisonJS/claude-on-the-go/issues)

**Security concern?** [Report privately](https://github.com/MatthewJamisonJS/claude-on-the-go/security/advisories/new)
