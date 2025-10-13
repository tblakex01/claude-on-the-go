#!/bin/bash

# tailscale-setup.sh
# Automated setup for remote access via SSH + Tailscale

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Helper functions
print_header() {
    echo -e "\n${BLUE}═══════════════════════════════════════════════════════════${NC}"
    echo -e "${BLUE}  $1${NC}"
    echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}\n"
}

print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

print_info() {
    echo -e "${BLUE}ℹ${NC} $1"
}

# Check if running on macOS or Linux
if [[ "$OSTYPE" == "darwin"* ]]; then
    OS="macos"
elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
    OS="linux"
else
    print_error "Unsupported operating system: $OSTYPE"
    print_info "This script supports macOS and Linux only."
    exit 1
fi

print_header "claude-on-the-go Remote Access Setup"

echo "This script will configure remote access to your Mac/Linux machine using SSH + Tailscale."
echo ""
echo "${YELLOW}Prerequisites:${NC}"
echo "  📥 Tailscale must be installed first!"
echo "     macOS: https://tailscale.com/download/mac"
echo "     Linux: https://tailscale.com/download/linux"
echo ""
echo "What this script does:"
echo "  1. Verify Tailscale is installed"
echo "  2. Enable SSH server"
echo "  3. Start Tailscale daemon (with verification)"
echo "  4. Connect to Tailscale network (authentication required)"
echo "  5. Display your SSH connection details"
echo ""
echo "${YELLOW}Note:${NC} You may be prompted to:"
echo "  • Authenticate in your browser (first-time Tailscale setup)"
echo "  • Enter your sudo password (for system changes)"
echo ""
read -p "Continue? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Setup cancelled."
    exit 0
fi

# Step 1: Verify Tailscale is installed
print_header "Step 1: Verifying Tailscale Installation"

if command -v tailscale &> /dev/null; then
    print_success "Tailscale is installed"
    TAILSCALE_VERSION=$(tailscale version | head -n 1)
    print_info "Version: $TAILSCALE_VERSION"
else
    print_error "Tailscale is not installed"
    echo ""
    print_info "📥 Please download and install Tailscale from the official website:"
    echo ""

    if [[ "$OS" == "macos" ]]; then
        echo "  ${BLUE}https://tailscale.com/download/mac${NC}"
        echo ""
        print_info "Download the .pkg file, install it, then re-run this script."
    elif [[ "$OS" == "linux" ]]; then
        echo "  ${BLUE}https://tailscale.com/download/linux${NC}"
        echo ""
        print_info "Follow the installation instructions for your distribution, then re-run this script."
    fi

    echo ""
    print_info "${YELLOW}Why not use brew/apt?${NC} Tailscale's official installers provide"
    print_info "the most reliable daemon management and are the recommended method."
    echo ""
    exit 1
fi

# Step 2: Enable SSH
print_header "Step 2: Enabling SSH Server"

if [[ "$OS" == "macos" ]]; then
    SSH_STATUS=$(sudo systemsetup -getremotelogin 2>/dev/null | grep -o "On\|Off")

    if [[ "$SSH_STATUS" == "On" ]]; then
        print_success "SSH (Remote Login) is already enabled"
    else
        print_info "Enabling SSH (Remote Login)..."
        sudo systemsetup -setremotelogin on > /dev/null
        print_success "SSH enabled successfully"
    fi

elif [[ "$OS" == "linux" ]]; then
    if systemctl is-active --quiet ssh || systemctl is-active --quiet sshd; then
        print_success "SSH server is already running"
    else
        print_info "Starting SSH server..."
        if systemctl list-unit-files | grep -q "^ssh.service"; then
            sudo systemctl start ssh
            sudo systemctl enable ssh
        elif systemctl list-unit-files | grep -q "^sshd.service"; then
            sudo systemctl start sshd
            sudo systemctl enable sshd
        else
            print_error "SSH server not found. Please install openssh-server:"
            print_info "  Debian/Ubuntu: sudo apt install openssh-server"
            print_info "  Fedora/RHEL: sudo dnf install openssh-server"
            exit 1
        fi
        print_success "SSH server started and enabled"
    fi
fi

# Verify SSH is listening
if lsof -i :22 &> /dev/null || ss -ln | grep -q ":22"; then
    print_success "SSH server is listening on port 22"
else
    print_warning "SSH server might not be running properly"
    print_info "Try manually: sudo systemctl status ssh"
fi

# Step 3: Start Tailscale
print_header "Step 3: Starting Tailscale"

# First, ensure the Tailscale daemon is running
if [[ "$OS" == "macos" ]]; then
    DAEMON_STATUS=$(brew services list | grep tailscale | awk '{print $2}')

    if [[ "$DAEMON_STATUS" == "error" ]]; then
        print_warning "Tailscale daemon is in error state, restarting..."
        brew services restart tailscale
        sleep 5
    elif [[ "$DAEMON_STATUS" == "started" ]]; then
        print_success "Tailscale daemon is already running"
    else
        # Status is "none" or other - need to start it
        print_info "Starting Tailscale daemon..."
        brew services start tailscale
        sleep 5  # Give it time to fully start
    fi

    # Verify daemon is now running by testing actual connectivity
    print_info "Verifying Tailscale daemon..."
    for i in {1..5}; do
        if tailscale status &>/dev/null; then
            print_success "Tailscale daemon is responding"
            break
        else
            if [ $i -eq 5 ]; then
                print_error "Tailscale daemon not responding after 5 attempts"
                print_info "Current status: $(brew services list | grep tailscale | awk '{print $2}')"
                print_info "Try manually: brew services restart tailscale && tailscale status"
                exit 1
            fi
            print_info "Waiting for daemon to respond... (attempt $i/5)"
            sleep 2
        fi
    done
elif [[ "$OS" == "linux" ]]; then
    if ! systemctl is-active --quiet tailscaled; then
        print_info "Starting Tailscale daemon..."
        sudo systemctl start tailscaled
        sudo systemctl enable tailscaled
        sleep 2
        print_success "Tailscale daemon started"
    else
        print_success "Tailscale daemon is already running"
    fi
fi

# Now check Tailscale connection status
TAILSCALE_STATUS=$(tailscale status 2>&1 || true)

if echo "$TAILSCALE_STATUS" | grep -q "Logged out\|not running"; then
    print_info "Connecting to Tailscale network..."
    print_info "A browser window will open for authentication."
    print_info "Please login using Google, GitHub, or Microsoft account."
    echo ""

    sudo tailscale up

    # Wait for Tailscale to be ready
    sleep 2

    print_success "Tailscale connected successfully"
elif echo "$TAILSCALE_STATUS" | grep -qE "100\.|fd7a:"; then
    print_success "Tailscale is already connected"
else
    print_warning "Tailscale status unclear, attempting to connect..."
    sudo tailscale up
    sleep 2
fi

# Get Tailscale information
print_header "Step 4: Connection Details"

print_info "Retrieving Tailscale IP address..."

# Try multiple times with backoff
TAILSCALE_IP=""
for i in {1..3}; do
    TAILSCALE_IP=$(tailscale ip -4 2>&1 || echo "")

    # Check if we got a valid IP (starts with 100.)
    if [[ "$TAILSCALE_IP" =~ ^100\. ]]; then
        print_success "Got Tailscale IP: $TAILSCALE_IP"
        break
    fi

    if [ $i -eq 3 ]; then
        print_error "Failed to get Tailscale IP address after 3 attempts"
        print_info "Daemon appears to be running, but no IP assigned yet."
        echo ""
        print_info "This usually means you need to authenticate with Tailscale."
        print_info "Run this command to authenticate:"
        echo ""
        echo "  ${BLUE}sudo tailscale up${NC}"
        echo ""
        print_info "Then re-run this script to get your connection details."
        echo ""
        print_info "Already authenticated? Check Tailscale status:"
        echo "  ${BLUE}tailscale status${NC}"
        echo ""
        exit 1
    fi

    print_info "Waiting for IP assignment... (attempt $i/3)"
    sleep 3
done

TAILSCALE_HOSTNAME=$(hostname | tr '[:upper:]' '[:lower:]')
CURRENT_USER=$(whoami)

print_success "Setup complete!"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "📱 ${GREEN}On your iPhone/Android:${NC}"
echo ""
echo "  1. Install Tailscale app"
echo "     • iOS: https://apps.apple.com/app/tailscale/id1470499037"
echo "     • Android: https://play.google.com/store/apps/details?id=com.tailscale.ipn"
echo ""
echo "  2. Login with the ${YELLOW}SAME ACCOUNT${NC} you just used"
echo ""
echo "  3. Install a terminal app:"
echo "     • Blink Shell (iOS, paid, excellent): https://blink.sh"
echo "     • Termius (iOS/Android, freemium): https://termius.com"
echo "     • iSH (iOS, free): https://ish.app"
echo "     • Termux (Android, free): https://termux.com"
echo ""
echo "  4. Connect via SSH:"
echo ""
echo "     ${GREEN}ssh ${CURRENT_USER}@${TAILSCALE_IP}${NC}"
echo ""
echo "     Or using hostname (if MagicDNS enabled):"
echo "     ${GREEN}ssh ${CURRENT_USER}@${TAILSCALE_HOSTNAME}${NC}"
echo ""
echo "  5. Run claude commands:"
echo ""
echo "     ${BLUE}claude \"help me refactor this code\"${NC}"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "💡 ${YELLOW}Pro Tips:${NC}"
echo ""
echo "  • Set up SSH keys to skip password:"
echo "    ${BLUE}ssh-keygen -t ed25519${NC}"
echo "    ${BLUE}ssh-copy-id ${CURRENT_USER}@${TAILSCALE_IP}${NC}"
echo ""
echo "  • Enable MagicDNS in Tailscale admin console for easier hostnames"
echo ""
echo "  • For unstable networks (trains/planes), install mosh:"
echo "    ${BLUE}brew install mosh${NC}"
echo "    Then connect with: ${BLUE}mosh ${CURRENT_USER}@${TAILSCALE_IP}${NC}"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "📚 Need help? Check out: ${BLUE}docs/REMOTE_ACCESS.md${NC}"
echo ""
echo "❓ Issues? Open a ticket: ${BLUE}https://github.com/MatthewJamisonJS/claude-on-the-go/issues${NC}"
echo ""

# Save connection info to file
CONFIG_FILE="$HOME/.claude-on-the-go-remote"
cat > "$CONFIG_FILE" << EOF
# claude-on-the-go Remote Access Configuration
# Generated: $(date)

TAILSCALE_IP=$TAILSCALE_IP
TAILSCALE_HOSTNAME=$TAILSCALE_HOSTNAME
USERNAME=$CURRENT_USER

# Quick connect command:
# ssh $CURRENT_USER@$TAILSCALE_IP
EOF

print_success "Connection details saved to: $CONFIG_FILE"
echo ""

# Step 5: Configure claude-on-the-go (Optional)
print_header "Step 5: Configure claude-on-the-go for Browser UI (Optional)"

echo "Would you like to configure claude-on-the-go for remote browser access?"
echo ""
echo "${BLUE}What this does:${NC}"
echo "  • Binds to your Tailscale IP (secure)"
echo "  • Allows browser connections from your Tailscale network"
echo "  • Updates .env automatically"
echo ""
read -p "Configure now? (y/n) " -n 1 -r
echo

if [[ $REPLY =~ ^[Yy]$ ]]; then
    # Check if claude-on-the-go directory exists
    COTG_DIR="$HOME/claude-on-the-go"

    if [ ! -d "$COTG_DIR" ]; then
        # Try current directory
        if [ -f "./install.sh" ] && [ -f "./start.sh" ]; then
            COTG_DIR="$(pwd)"
        else
            print_warning "claude-on-the-go directory not found"
            print_info "Expected location: $HOME/claude-on-the-go"
            print_info "Skipping configuration. You can configure manually later:"
            echo ""
            echo "  ${BLUE}cd claude-on-the-go${NC}"
            echo "  ${BLUE}echo \"HOST=$TAILSCALE_IP\" >> .env${NC}"
            echo "  ${BLUE}echo \"ALLOWED_ORIGINS=http://$TAILSCALE_IP:8001,http://localhost:8001\" >> .env${NC}"
            echo ""
        fi
    fi

    if [ -d "$COTG_DIR" ]; then
        print_info "Configuring claude-on-the-go at: $COTG_DIR"

        ENV_FILE="$COTG_DIR/.env"

        # Create .env if it doesn't exist
        if [ ! -f "$ENV_FILE" ]; then
            touch "$ENV_FILE"
            print_success "Created .env file"
        fi

        # Backup existing .env
        cp "$ENV_FILE" "$ENV_FILE.backup.$(date +%s)" 2>/dev/null || true

        # Remove old HOST and ALLOWED_ORIGINS if they exist
        if [[ "$OS" == "macos" ]]; then
            sed -i '' '/^HOST=/d' "$ENV_FILE"
            sed -i '' '/^ALLOWED_ORIGINS=/d' "$ENV_FILE"
        else
            sed -i '/^HOST=/d' "$ENV_FILE"
            sed -i '/^ALLOWED_ORIGINS=/d' "$ENV_FILE"
        fi

        # Add new configuration
        echo "" >> "$ENV_FILE"
        echo "# Remote Access Configuration (added by tailscale-setup.sh)" >> "$ENV_FILE"
        echo "# Generated: $(date)" >> "$ENV_FILE"
        echo "HOST=$TAILSCALE_IP" >> "$ENV_FILE"
        echo "ALLOWED_ORIGINS=http://$TAILSCALE_IP:8001,http://localhost:8001" >> "$ENV_FILE"

        print_success "Configuration updated!"
        echo ""
        echo "  ${GREEN}HOST=$TAILSCALE_IP${NC}"
        echo "  ${GREEN}ALLOWED_ORIGINS=http://$TAILSCALE_IP:8001,http://localhost:8001${NC}"
        echo ""
        print_info "${YELLOW}Security:${NC} Binding to Tailscale IP (not 0.0.0.0) is more secure"
        print_info "Start claude-on-the-go: ${BLUE}cd $COTG_DIR && ./start.sh${NC}"
    fi
else
    print_info "Skipping configuration."
    echo ""
    echo "To configure manually later, add to $HOME/claude-on-the-go/.env:"
    echo "  ${BLUE}HOST=$TAILSCALE_IP${NC}"
    echo "  ${BLUE}ALLOWED_ORIGINS=http://$TAILSCALE_IP:8001,http://localhost:8001${NC}"
    echo ""
fi

# Offer to test connection
echo ""
read -p "Would you like to test the SSH connection now? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    print_info "Testing SSH connection to localhost..."
    if ssh -o ConnectTimeout=5 -o StrictHostKeyChecking=no "$CURRENT_USER@localhost" "echo 'SSH connection successful!'" 2>/dev/null; then
        print_success "SSH is working correctly!"
        print_info "You can now connect from your phone using the command above."
    else
        print_warning "SSH test failed. This might be normal if you haven't set up SSH keys yet."
        print_info "Try connecting from your phone - you'll be prompted for your Mac password."
    fi
fi

echo ""
print_success "All done! Happy coding from your couch! 🛋️"
echo ""
