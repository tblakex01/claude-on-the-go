# Security Policy

Claude-onTheGo is designed with security as a top priority. This document outlines our security practices, how to report vulnerabilities, and best practices for users.

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 1.0.x   | :white_check_mark: |

## Security Features

### 🛡️ Built-In Protections

1. **🚦 Rate Limiting**
   - 10 messages per second per connection
   - 100KB data per second per connection
   - Token bucket algorithm with burst protection

2. **✅ Input Validation**
   - Maximum message size: 10KB
   - Terminal dimensions: 1-500 rows/cols
   - Null byte detection and removal
   - Type checking for all inputs

3. **🔐 Output Sanitization**
   - Log redaction for IPs, tokens, emails
   - Configurable via `LOG_REDACTION` env variable
   - Removes sensitive data before logging

4. **🛡️ HTTP Security Headers**
   - Content Security Policy (CSP)
   - X-Frame-Options: SAMEORIGIN
   - X-Content-Type-Options: nosniff
   - X-XSS-Protection: enabled
   - Referrer-Policy: strict-origin-when-cross-origin
   - Permissions-Policy: restrictive

5. **🎫 Authentication** (Optional)
   - Token-based authentication
   - Constant-time comparison (prevents timing attacks)
   - Environment-based configuration

6. **🌐 Network Security**
   - Local network only by default
   - No hardcoded IPs or credentials
   - Environment-based configuration
   - mDNS for easy discovery without exposing IPs

### Single-User Mode

By default, Claude-onTheGo only allows **one active connection at a time**. When a new connection is established, all existing connections are automatically closed.

**Why?** Prevents:
- Output duplication from multiple tabs
- Unauthorized access from other devices
- Resource exhaustion from zombie connections

To disable: Set `MAX_CONNECTIONS=0` in `.env` (not recommended)

## 🎯 Security Best Practices

### 🏠 For Local Network Use (Default)

1. **✅ Use on trusted WiFi networks only**
   - 🏡 Your home network
   - 📱 Your phone's personal hotspot
   - 🏢 Corporate networks you trust

2. **🔄 Keep dependencies updated**
   ```bash
   pip install --upgrade -r requirements.txt
   ```

3. **🔍 Run security checks regularly**
   ```bash
   safety check
   bandit -r backend/
   ```

4. **📝 Review logs for suspicious activity**
   ```bash
   grep "rate limit" backend.log
   grep "Invalid" backend.log
   ```

### 🌐 For Remote Access (Advanced)

If you need to access Claude-onTheGo over the internet:

1. **Enable authentication** (`.env`):
   ```bash
   ENABLE_AUTH=true
   AUTH_TOKEN=<random-secure-token>
   ```

2. **Generate a strong token**:
   ```bash
   python3 -c "import secrets; print(secrets.token_hex(32))"
   ```

3. **Use HTTPS reverse proxy** (nginx, Caddy):
   ```nginx
   server {
       listen 443 ssl;
       server_name your-domain.com;

       ssl_certificate /path/to/cert.pem;
       ssl_certificate_key /path/to/key.pem;

       location / {
           proxy_pass http://localhost:8001;
       }

       location /ws {
           proxy_pass http://localhost:8000;
           proxy_http_version 1.1;
           proxy_set_header Upgrade $http_upgrade;
           proxy_set_header Connection "upgrade";
       }
   }
   ```

4. **Restrict access by IP** (if possible):
   ```nginx
   allow 1.2.3.4;  # Your IP
   deny all;
   ```

5. **Use a VPN** instead of exposing directly

## What We Don't Do

To be transparent, Claude-onTheGo does **NOT** currently include:

- End-to-end encryption (uses plain WebSockets)
- Built-in HTTPS support (use a reverse proxy)
- User authentication beyond simple tokens
- Audit logging of all commands
- Sandboxing of the claude process

**What we DO include:**
- Session persistence across reconnections (UUID-based, 1-hour timeout)
- Bidirectional clipboard synchronization
- Rate limiting and input validation

**For local network use, these are not necessary.** For internet exposure, use a reverse proxy with HTTPS and strong authentication.

## Reporting a Vulnerability

If you discover a security vulnerability, please report it responsibly:

**Option 1: GitHub Security Advisories (Preferred)**

Visit: **https://github.com/MatthewJamisonJS/claude-on-the-go/security/advisories/new**

This creates a **private** security report that only maintainers can see. The general public won't see your report until we've had time to fix the issue.

**How to use it:**
1. Click the link above (you'll need to be logged into GitHub)
2. Fill out the vulnerability report form
3. Click "Submit report"

**Option 2: GitHub Issues (For non-critical bugs or questions)**

Visit: **https://github.com/MatthewJamisonJS/claude-on-the-go/issues**

Use this for:
- Non-security bugs
- Feature requests
- General questions
- Less critical security concerns that don't need immediate privacy

**Please include:**
- Description of the vulnerability
- Steps to reproduce
- Potential impact
- Suggested fix (if you have one)
- Your environment (Python version, OS, etc.)

**You can expect:**
- Response within 48 hours
- Regular updates on our progress
- Credit in the security advisory (unless you prefer anonymity)
- A fix in the next patch release for critical issues

## Security Checklist for Contributors

Before submitting code:

- [ ] No hardcoded credentials, IPs, or sensitive data
- [ ] Input validation for all user-provided data
- [ ] Sanitization of any data written to logs
- [ ] Rate limiting for any new endpoints
- [ ] CSRF protection where applicable
- [ ] SQL injection prevention (if adding database)
- [ ] XSS prevention in any HTML generation
- [ ] Dependency security check (`safety check`)
- [ ] Code security scan (`bandit -r backend/`)

## Threat Model

### In Scope

- Input validation bypass
- Rate limit bypass
- Authentication bypass (if enabled)
- XSS vulnerabilities
- Injection attacks
- DoS attacks
- Information disclosure
- Privilege escalation

### Out of Scope

- Physical access to the Mac running the server
- Social engineering
- Attacks requiring compromised WiFi network
- Attacks on the Claude CLI itself
- Attacks on Python/FastAPI/underlying OS

## Dependency Security

We use:
- `safety` to check for known vulnerabilities in dependencies
- `bandit` to scan Python code for security issues
- Pinned versions in `requirements.txt` for reproducibility

To update dependencies safely:

```bash
# Check for vulnerabilities
safety check

# Update specific package
pip install --upgrade package-name

# Test thoroughly
./start.sh
# Test all functionality

# Update requirements.txt
pip freeze > requirements.txt
```

## Incident Response Plan

If a security incident occurs:

1. **Immediate**: Stop the server (`./stop.sh`)
2. **Assess**: Review `backend.log` and `frontend.log`
3. **Contain**: Block malicious IPs in firewall
4. **Report**: Email security vulnerability contact
5. **Patch**: Update code and dependencies
6. **Test**: Verify fix works and doesn't break functionality
7. **Deploy**: Update production instance
8. **Post-mortem**: Document what happened and how we fixed it

## Security Updates

Security patches will be released as:
- Patch versions (1.0.x) for critical fixes
- Minor versions (1.x.0) for new security features
- Major versions (x.0.0) for breaking security changes

Subscribe to the repository to get notified of security releases.

## Questions?

Not sure if something is a security issue? Report it anyway - we'd rather hear about a non-issue than miss a real vulnerability.

---

**Last updated**: January 2025
**Version**: 1.0.0
