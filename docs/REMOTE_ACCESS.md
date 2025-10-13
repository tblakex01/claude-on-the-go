# Remote Access Guide

## Overview

claude-on-the-go's WebSocket implementation is optimized for local WiFi access. For remote access (when you're not on the same network as your Mac), we recommend **SSH + Tailscale** instead of exposing the WebSocket server to the internet.

This guide explains:
- Why SSH + Tailscale is the best approach for remote access
- How to set it up (2-minute process)
- Architecture comparison
- Advanced options for unstable networks

## Quick Setup

### Prerequisites

- Mac with claude-on-the-go already installed and working locally
- iPhone/Android with internet connection
- 2 minutes of your time

### Step 1: Mac Setup (One-Time)

**Part A: Install Tailscale**

📥 **Download and install Tailscale from the official website:**

- **macOS**: https://tailscale.com/download/mac
- **Linux**: https://tailscale.com/download/linux

**Why not use `brew install`?** Tailscale's GUI app provides more reliable daemon management and is the officially recommended installation method.

**Part B: Configure Remote Access (Automated)**

After installing Tailscale, run the setup script:

```bash
cd claude-on-the-go
./scripts/tailscale-setup.sh
```

The script will:
- Verify Tailscale is installed
- Start Tailscale daemon (with verification)
- Enable SSH (Remote Login)
- Connect to Tailscale network (authentication in browser)
- Display your SSH connection details

**What to expect:**
- Browser will open for Tailscale authentication (first time only)
- You'll be prompted for your Mac password (for SSH enable)
- Takes ~2 minutes total

**Part C: Manual Configuration (Alternative)**

If you prefer manual setup after installing Tailscale:

```bash
# 1. Enable SSH
sudo systemsetup -setremotelogin on

# 2. Start Tailscale (open the app or use CLI)
# macOS: Open Tailscale.app from Applications
# Or via CLI: sudo tailscale up

# 3. Connect to Tailscale network
sudo tailscale up
# Login when browser opens (use Google/GitHub/Microsoft account)

# 4. Get your Tailscale IP
tailscale ip -4
# Example output: 100.101.102.103
```

### Step 2: Mobile Setup (One-Time)

1. **Install Tailscale:**
   - iPhone: [App Store](https://apps.apple.com/us/app/tailscale/id1470499037)
   - Android: [Google Play](https://play.google.com/store/apps/details?id=com.tailscale.ipn)

2. **Login to Tailscale:**
   - Use the **same account** you used on your Mac
   - Grant network permissions when prompted

3. **Install a Terminal App:**

   **iPhone:**
   - [Blink Shell](https://blink.sh/) - $20/year, best experience, supports mosh
   - [Termius](https://termius.com/) - Free tier available, good UI
   - [iSH](https://ish.app/) - Free, full Linux environment

   **Android:**
   - [Termux](https://termux.com/) - Free, powerful Linux terminal
   - [JuiceSSH](https://juicessh.com/) - Free, SSH-focused
   - [Termius](https://termius.com/) - Cross-platform

### Step 3: Connect

**From your phone's terminal app:**

```bash
# Basic connection (will ask for password)
ssh your-mac-username@100.101.102.103

# Once connected, use claude normally
claude "help me refactor this Python function"
```

**Optional but recommended - Set up SSH keys (skip password):**

```bash
# On your phone's terminal
ssh-keygen -t ed25519
# Press enter for all prompts (accept defaults)

ssh-copy-id your-mac-username@100.101.102.103
# Enter your Mac password one last time

# Now SSH works without password!
ssh your-mac-username@100.101.102.103
```

**Pro tip - Use MagicDNS instead of IP:**

Tailscale provides automatic hostname resolution:

```bash
# Instead of remembering 100.101.102.103
ssh your-mac-username@your-mac-name

# Example (replace with your actual username and hostname)
ssh john@johns-macbook
```

Enable in Tailscale admin console → DNS settings → MagicDNS.

### Step 3.5: Configure claude-on-the-go for Remote Access (One-Time)

**⚠️ Important:** Before you can use the browser UI remotely, configure claude-on-the-go to accept connections from Tailscale.

**Automated Setup (Recommended):**

The `tailscale-setup.sh` script (Step 1) includes an optional Step 5 that automatically configures your `.env` file with secure settings. If you used the script and answered "yes" to configuration, you're all set!

**Manual Setup:**

**On your Mac (via SSH or locally):**

1. **Get your Tailscale IP:**
   ```bash
   tailscale ip -4
   # Example output: 100.101.102.103
   ```

2. **Edit the `.env` file:**
   ```bash
   cd claude-on-the-go
   nano .env  # or vim, code, etc.
   ```

3. **Add these settings (use YOUR Tailscale IP):**
   ```bash
   # Bind to your Tailscale IP (most secure)
   HOST=100.101.102.103  # Replace with your actual Tailscale IP

   # Allow connections from Tailscale network
   ALLOWED_ORIGINS=http://100.101.102.103:8001,http://localhost:8001

   # Optional: Set ports if defaults conflict
   BACKEND_PORT=8000
   FRONTEND_PORT=8001
   ```

4. **Save and exit** (Ctrl+O, Enter, Ctrl+X in nano)

**Quick manual setup (one command):**
```bash
cd claude-on-the-go
TAILSCALE_IP=$(tailscale ip -4)
echo "HOST=$TAILSCALE_IP" >> .env
echo "ALLOWED_ORIGINS=http://$TAILSCALE_IP:8001,http://localhost:8001" >> .env
```

**Security Note:** Binding to your specific Tailscale IP (instead of `0.0.0.0`) provides the best security:
- ✅ **Only Tailscale network can connect** - No exposure to other interfaces
- ✅ **Defense in depth** - Even if firewall misconfigured, only Tailscale access works
- ✅ **Clear intent** - Explicitly specifies which network interface to use

**Alternative (Less Secure):** Bind to all interfaces:
```bash
# Only use if you need to bind to multiple interfaces
HOST=0.0.0.0  # Allows connections from ANY network interface

# Security considerations:
# - Exposes service to all network interfaces (WiFi, Ethernet, VPN)
# - Relies solely on ALLOWED_ORIGINS for access control
# - Use only if you understand the security implications
```

### Step 4: Using Claude via Remote Access

Now that you're connected via Tailscale and SSH, here's how to use Claude:

**Option A: Direct Claude CLI (Simplest)**

Once connected via SSH, just use Claude normally:

```bash
# You're now SSH'd into your Mac
claude "explain this code"
claude "help me refactor this function"
claude "write a Python script to parse CSV files"
```

That's it! Claude runs directly on your Mac, output shows in your phone's terminal.

**Option B: Start claude-on-the-go Server (Browser UI)**

If you want to use the browser-based UI remotely:

1. **Ensure you've completed Step 3.5 (Configuration)** - This is required!

2. **Start the server on your Mac (via SSH):**
   ```bash
   cd claude-on-the-go
   ./start.sh

   # Verify it's listening on your Tailscale IP:
   # Look for "Uvicorn running on http://100.101.102.103:8000"
   ```

3. **Access from your phone's browser:**
   - Keep Tailscale connected
   - Open browser on your phone
   - Visit: `http://100.101.102.103:8001` (use your Mac's Tailscale IP)
   - Use Claude with full browser UI!

**Which option should I use?**

| Method | Best For | Pros | Cons |
|--------|----------|------|------|
| **Direct CLI** (Option A) | Quick commands, terminal lovers | Zero setup, instant | Terminal-only, no visual UI |
| **Browser UI** (Option B) | Longer sessions, prefer visual interface | Full browser experience, easier copy/paste | Requires starting server first |

**Pro tip:** You can use both! Start with Direct CLI for quick tasks, then launch the browser UI when you need a richer interface.

## Why SSH + Tailscale?

### The Problem with Remote WebSocket

To expose the WebSocket server remotely, you'd need:

**Security implementation:**
- Authentication system (JWT/OAuth)
- Per-user rate limiting
- HTTPS certificates (Let's Encrypt automation)
- Origin validation (prevent CSRF)
- Input sanitization (prevent injection)
- Session management

**Infrastructure:**
- Domain name + DNS
- Reverse proxy (nginx/Caddy)
- Firewall rules
- Certificate renewal automation
- DDoS protection

**Ongoing maintenance:**
- Security patches (your responsibility)
- Monitor for attacks
- Handle abuse/spam
- Keep up with CVEs

### The SSH + Tailscale Advantage

**Zero maintenance:** Tailscale handles all infrastructure, updates, and security.

**Better security:** WireGuard end-to-end encryption + SSH authentication = defense in depth.

**Simpler architecture:** No code changes, no new attack surface in your Python backend.

**Native experience:** Users interact with the real `claude` CLI, not a browser proxy.

**Proven reliability:** SSH has 30+ years of hardening. WireGuard is formally verified. Both are battle-tested.

## Architecture Comparison

### Local WiFi (Current WebSocket Implementation)

```
[iPhone Browser] ──WebSocket──> [FastAPI Backend] ──pexpect──> [claude CLI]
      :8001            :8000           PTY manager         subprocess

Latency: 5-15ms (optimized)
Security: Token auth + rate limiting
Requires: Same WiFi network
```

**Strengths:**
- Fastest possible latency on local network
- Browser-based (zero client installation)
- QR code convenience
- Works great for demos

**Limitations:**
- Local network only
- You maintain security
- Browser terminal limitations

### Remote Access (SSH over Tailscale)

```
[iPhone Terminal] ──SSH──> [Tailscale VPN] ──WireGuard──> [Mac SSH] ──shell──> [claude CLI]
   Blink Shell        encrypted     mesh network        built-in      direct

Latency: 20-50ms typical (depending on distance)
Security: WireGuard + SSH (double encryption)
Works: Anywhere with internet
```

**Strengths:**
- Works from anywhere
- Automatic NAT traversal
- Survives network roaming
- Zero maintenance burden
- Strong security by default

**Trade-offs:**
- Requires terminal app
- Slightly higher latency than local
- Two-step setup (Tailscale + terminal)

**Critical insight:** These are **complementary**, not competing. Use local WebSocket when you're home, SSH + Tailscale when you're away.

## Advanced: Mosh for Unstable Networks

If you frequently use `claude` on trains, planes, or flaky connections, consider **Mosh (Mobile Shell)**.

### What is Mosh?

Mosh is a replacement for SSH that works better on high-latency, packet-lossy, or changing networks. It provides:

- **Instant local echo:** Typing feels immediate even on 300ms+ connections
- **Roaming support:** Survives laptop sleep, network switches (WiFi → cellular)
- **Packet loss resilience:** 50x better response time under 29% packet loss

### Setup

**On your Mac:**

```bash
brew install mosh
# That's it - mosh server installed
```

**On your iPhone (Blink Shell):**

Blink Shell includes mosh by default. Just use `mosh` instead of `ssh`:

```bash
# Instead of: ssh user@host
mosh user@100.101.102.103

# Works over Tailscale
mosh user@your-mac-name
```

**On your iPhone (iSH):**

```bash
apk add mosh-client
mosh user@100.101.102.103
```

### When to Use Mosh

| Scenario | Recommended Tool | Why |
|----------|------------------|-----|
| Stable home WiFi | SSH | Simpler, full features |
| Coffee shop WiFi | SSH or Mosh | Either works fine |
| Train/plane | **Mosh** | Handles packet loss, roaming |
| Switching networks | **Mosh** | Survives WiFi → cellular |
| Behind strict firewall | SSH | Mosh requires UDP 60000-61000 |

### Mosh Limitations

- **No scrollback in terminal:** You must use `tmux` or `screen`
  ```bash
  # Connect to mosh inside tmux
  mosh user@host -- tmux
  ```

- **No X11 forwarding or port forwarding:** Mosh only does terminal

- **UTF-8 only:** Refuses to run without proper locale

- **Requires UDP ports 60000-61000:** Tailscale handles this automatically

### Mosh vs SSH Performance

Real-world testing on 3G network with 29% packet loss:

| Metric | SSH | Mosh |
|--------|-----|------|
| Median keystroke response | 503ms | < 5ms |
| 99th percentile response | 16.8s | 0.33s |
| Survives network change | ❌ No | ✅ Yes |
| Survives laptop sleep | ❌ No | ✅ Yes |

## Troubleshooting

### Browser UI Not Loading Remotely

**Symptom:** Visiting `http://100.101.102.103:8001` in your phone's browser doesn't work

**Fix:**

1. **Check configuration (most common issue):**
   ```bash
   # On your Mac (via SSH)
   cd claude-on-the-go
   cat .env | grep -E "HOST|ALLOWED_ORIGINS"

   # Should show (with your actual Tailscale IP):
   # HOST=100.101.102.103
   # ALLOWED_ORIGINS=http://100.101.102.103:8001,...

   # If missing or wrong, fix it:
   TAILSCALE_IP=$(tailscale ip -4)
   echo "HOST=$TAILSCALE_IP" >> .env
   echo "ALLOWED_ORIGINS=http://$TAILSCALE_IP:8001,http://localhost:8001" >> .env

   # Then restart the server:
   ./stop.sh && ./start.sh
   ```

2. **Verify claude-on-the-go is running on your Mac:**
   ```bash
   # Via SSH
   cd claude-on-the-go
   ./start.sh

   # Check if it's actually running
   ps aux | grep python | grep legacy
   ```

3. **Confirm you're using the correct Tailscale IP:**
   ```bash
   # On your Mac (via SSH)
   tailscale ip -4
   # Use THIS exact IP in your browser: http://[IP]:8001
   ```

4. **Check Tailscale connection on your phone:**
   - Open Tailscale app on your phone
   - Verify your Mac shows as "Connected" (green dot)
   - If offline, tap your Mac name to reconnect

5. **Firewall might be blocking:**
   ```bash
   # On your Mac (via SSH)
   # Allow Python through firewall
   sudo /usr/libexec/ApplicationFirewall/socketfilterfw --listapps | grep python

   # If not listed, add it:
   sudo /usr/libexec/ApplicationFirewall/socketfilterfw --add $(which python3)
   ```

6. **Try localhost tunneling (advanced):**
   ```bash
   # On your phone's terminal
   ssh -L 8001:localhost:8001 your-username@100.101.102.103

   # Then visit http://localhost:8001 on your phone's browser
   ```

### Tailscale daemon not starting (macOS)

**Symptom:** `tailscale status` shows "not running" or "Failed to connect to local Tailscale daemon"

**Check daemon status:**
```bash
brew services list | grep tailscale
# May show "none", "error", or "started"
```

**Common fixes:**

**Option 1: Start via Homebrew services (most common)**
```bash
# If status is "none" (daemon never started)
brew services start tailscale
sleep 5
tailscale status

# If status is "error" (daemon crashed)
brew services restart tailscale
sleep 5
tailscale status
```

**Note:** The automated setup script (`./scripts/tailscale-setup.sh`) handles this automatically with verification loops!

**Option 2: Reinstall Tailscale completely**
```bash
brew services stop tailscale
brew uninstall tailscale
brew install tailscale
brew services start tailscale
sleep 5
sudo tailscale up
```

**Option 3: Check for port conflicts**
```bash
# Check if anything is blocking Tailscale's socket
lsof /var/run/tailscaled.socket
# If something else is using it, kill that process
```

**Option 4: Check Homebrew service logs**
```bash
tail -50 ~/Library/Logs/Homebrew/tailscale.log
# Look for permission errors or missing dependencies
```

**Still not working?**

1. **Reinstall Tailscale from official website:**
   - Download from: https://tailscale.com/download/mac
   - Install the .pkg file, then open Tailscale.app
   - The GUI app provides the most reliable daemon management

2. **Check official troubleshooting guide:**
   - Tailscale KB: https://tailscale.com/kb/1023/troubleshooting
   - Covers daemon issues, connectivity problems, and more

### "Connection refused" when SSHing

**Check if SSH is enabled:**
```bash
sudo systemsetup -getremotelogin
# Should say: Remote Login: On
```

**Enable if needed:**
```bash
sudo systemsetup -setremotelogin on
```

**Verify SSH is listening:**
```bash
sudo lsof -i :22
# Should show sshd listening
```

### "Mac not showing up in Tailscale"

**Check Tailscale status:**
```bash
tailscale status
# Should show your Mac and other devices
```

**Restart Tailscale:**
```bash
sudo tailscale down
sudo tailscale up
```

**Check network permissions:**
System Settings → Privacy & Security → Network
Ensure Tailscale has permission.

### "Can't resolve hostname"

If `ssh user@your-mac-name` doesn't work:

1. **Enable MagicDNS:**
   - Open Tailscale admin console
   - DNS settings → Enable MagicDNS

2. **Use IP address instead:**
   ```bash
   tailscale ip -4
   # Use this IP directly
   ssh user@100.101.102.103
   ```

### Connection works but is slow

**Check if direct connection succeeded:**
```bash
tailscale status
# Look for "direct" next to your device
# If it says "relay", you're using DERP relay
```

**Force better connection:**
```bash
# Restart Tailscale on both devices
sudo tailscale down && sudo tailscale up
```

**Check ping times:**
```bash
ping $(tailscale ip -4)
# Should be < 50ms for direct connection
# > 100ms suggests DERP relay
```

### Mosh specific issues

**"mosh-server not found"**
```bash
# Ensure mosh is installed on Mac
brew install mosh

# Verify it's in PATH
which mosh-server
# Should output: /opt/homebrew/bin/mosh-server
```

**"Connection timed out"**

Mosh requires UDP ports 60000-61000. Tailscale handles this automatically, but verify:

```bash
# Check firewall on Mac
sudo /usr/libexec/ApplicationFirewall/socketfilterfw --getglobalstate
# If enabled, add mosh:
sudo /usr/libexec/ApplicationFirewall/socketfilterfw --add /opt/homebrew/bin/mosh-server
```

## Security Hardening (Optional)

### SSH Configuration

Edit `/etc/ssh/sshd_config` on your Mac:

```bash
# Disable password authentication (keys only)
PasswordAuthentication no
ChallengeResponseAuthentication no

# Disable root login
PermitRootLogin no

# Only allow specific user
AllowUsers your-mac-username

# Use strong key exchange algorithms
KexAlgorithms curve25519-sha256,curve25519-sha256@libssh.org

# Use strong ciphers
Ciphers chacha20-poly1305@openssh.com,aes256-gcm@openssh.com

# Use strong MACs
MACs hmac-sha2-512-etm@openssh.com,hmac-sha2-256-etm@openssh.com
```

Restart SSH:
```bash
sudo launchctl stop com.openssh.sshd
sudo launchctl start com.openssh.sshd
```

### Tailscale ACLs

For team/shared environments, restrict who can access your Mac:

1. Open Tailscale admin console
2. Access Controls → Edit
3. Add policy:

```json
{
  "acls": [
    {
      "action": "accept",
      "users": ["your-email@example.com"],
      "ports": ["your-mac-tag:22"]
    }
  ]
}
```

### Two-Factor Authentication

Add 2FA to SSH (optional, high security):

```bash
# Install Google Authenticator
brew install libpam-google-authenticator

# Configure
google-authenticator
# Follow prompts, scan QR code with phone
```

Edit `/etc/pam.d/sshd`:
```
auth required pam_google_authenticator.so
```

Edit `/etc/ssh/sshd_config`:
```
ChallengeResponseAuthentication yes
AuthenticationMethods publickey,keyboard-interactive
```

Restart SSH.

## For Contributors: Why We Don't Build This

You might wonder: "Why not add Tailscale integration to the Python backend?"

**Because it's the wrong abstraction layer.**

Tailscale solves networking. The Python backend solves "WebSocket terminal streaming over local WiFi." These are separate concerns that should stay separate.

Adding Tailscale to the backend would require:
- Embedding VPN management in Python (complex)
- Handling Tailscale auth flows (OAuth integration)
- Managing coordination server communication
- Monitoring peer connectivity states
- Dealing with Tailscale API changes
- Testing network edge cases

Instead:
- Tailscale runs as a system service
- SSH uses it as transport (built-in, zero config)
- Clean separation of concerns
- Each tool does what it's best at

**The unix philosophy:** Do one thing well. Compose tools.

## Tailscale Security Model

Understanding what you're trusting:

**End-to-end encryption:** All traffic uses WireGuard (ChaCha20-Poly1305). Private keys never leave your devices.

**Coordination server:** Exchanges public keys and helps establish connections. Cannot decrypt your traffic.

**DERP relays:** Forward encrypted packets when direct connection fails. Cannot read packet contents.

**Authentication:** OAuth (Google/GitHub/Microsoft). No Tailscale-specific passwords.

**Open source:** Client code is fully open source. You can audit it.

**Threat model:** Tailscale coordination server is trusted for key exchange, but cannot access your data. DERP relays see encrypted packets only. Perfect for personal/team use. For paranoid security, run your own coordination server (Headscale).

## Comparison to Other Solutions

| Solution | Setup Time | Maintenance | Works Remote | Security | Cost |
|----------|------------|-------------|--------------|----------|------|
| **SSH + Tailscale** | 2 min | Zero | ✅ Anywhere | Excellent | Free |
| Port forwarding | 30+ min | Medium | ✅ Yes | Good (if configured) | Free |
| VPN (OpenVPN) | 60+ min | High | ✅ Yes | Excellent | Free/Paid |
| ngrok/cloudflared | 5 min | Low | ✅ Yes | Good | Free/Paid |
| Expose WebSocket | Hours | Very high | ✅ Yes | DIY (risky) | Domain costs |

**Winner:** SSH + Tailscale balances all factors optimally for a solo developer maintaining an open-source project.

## Next Steps

1. **Try it:** Run `./scripts/tailscale-setup.sh` and connect from your phone
2. **Bookmark this:** Save your Tailscale IP for quick access
3. **Set up keys:** Use `ssh-copy-id` to skip password entry
4. **Try mosh:** If you travel frequently, test mosh for mobile resilience
5. **Share feedback:** Open an issue if you hit problems or have suggestions

## Resources

- [Tailscale Documentation](https://tailscale.com/kb/)
- [Tailscale Troubleshooting Guide](https://tailscale.com/kb/1023/troubleshooting)
- [Tailscale Download (macOS)](https://tailscale.com/download/mac)
- [Tailscale Download (Linux)](https://tailscale.com/download/linux)
- [SSH Hardening Guide](https://stribika.github.io/2015/01/04/secure-secure-shell.html)
- [Mosh Official Site](https://mosh.org/)
- [WireGuard Whitepaper](https://www.wireguard.com/papers/wireguard.pdf)

---

**Questions?** Open an issue: https://github.com/MatthewJamisonJS/claude-on-the-go/issues
