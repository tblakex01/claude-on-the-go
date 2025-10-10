# CLI

User-friendly command-line interface for claude-on-the-go.

## Purpose

This directory contains the CLI tool that provides a simple and intuitive way to manage claude-on-the-go.

## Commands

### Start Server
```bash
claude-on-the-go start [--legacy]
```
Start the server with the new architecture (or legacy mode with `--legacy` flag).

**Options:**
- `--port <port>` - Custom port (default: 8000)
- `--host <host>` - Bind address (default: auto-detect)
- `--legacy` - Use legacy v1.0 architecture
- `--no-qr` - Skip QR code display

### Generate QR Code
```bash
claude-on-the-go qr [--tailscale]
```
Generate a QR code for easy mobile connection.

**Options:**
- `--tailscale` - Use Tailscale IP instead of local IP
- `--output <file>` - Save QR code to file (PNG/SVG)

### Session Management
```bash
claude-on-the-go sessions list
claude-on-the-go sessions show <session-id>
claude-on-the-go sessions close <session-id>
claude-on-the-go sessions cleanup
```

### Configuration
```bash
claude-on-the-go config show
claude-on-the-go config set <key> <value>
claude-on-the-go config reset
```

### Health Check
```bash
claude-on-the-go health
```
Check server status and display diagnostics.

### Logs
```bash
claude-on-the-go logs [--follow]
```
View server logs with optional tail mode.

## Usage Example

```bash
# Install CLI
pip install -e .

# Start server
claude-on-the-go start

# View active sessions
claude-on-the-go sessions list

# Generate QR code with Tailscale
claude-on-the-go qr --tailscale
```

## Implementation

The CLI is built with:
- `click` or `typer` for command parsing
- Rich text formatting with `rich`
- Progress indicators and spinners
- Color-coded output
- Interactive prompts when needed

## Configuration File

The CLI uses a config file at `~/.claude-on-the-go/config.yaml`:

```yaml
server:
  port: 8000
  host: auto
  legacy_mode: false

integrations:
  pushover_enabled: false
  tailscale_enabled: false

display:
  show_qr: true
  color_output: true
```

## Error Handling

The CLI provides helpful error messages and suggestions:
- Claude CLI not found → Installation instructions
- Port already in use → Suggests alternative ports
- Permission denied → Suggests running with appropriate permissions
- Network unreachable → Checks WiFi and firewall settings
