#!/usr/bin/env bash
# Claude-onTheGo - One-Command Installer
# Install dependencies and set up environment

set -e  # Exit on error

echo "╭────────────────────────────────────────────────────────╮"
echo "│                                                        │"
echo "│        Claude-onTheGo Installation                     │"
echo "│                                                        │"
echo "╰────────────────────────────────────────────────────────╯"
echo ""

# Check Python 3
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is required but not installed."
    echo "   Please install Python 3.8+ and try again."
    exit 1
fi

PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
echo "✓ Python 3 found: $PYTHON_VERSION"

# Check if claude CLI is installed
if ! command -v claude &> /dev/null; then
    echo "⚠️  Claude CLI not found in PATH"
    echo "   Claude-onTheGo requires the claude command-line tool."
    echo "   Please install it from: https://claude.ai/download"
    echo ""
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
else
    echo "✓ Claude CLI found"
fi

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo ""
    echo "Creating virtual environment..."
    python3 -m venv venv
    echo "✓ Virtual environment created"
else
    echo "✓ Virtual environment already exists"
fi

# Activate virt env and install dependencies
echo ""
echo "Installing dependencies..."
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip --quiet

# Install requirements
pip install -r requirements.txt --quiet

echo "✓ Dependencies installed"

# Create .env if it doesn't exist
if [ ! -f ".env" ]; then
    echo ""
    echo "Creating .env file from template..."
    cp .env.example .env
    echo "✓ .env file created"
    echo ""
    echo "⚠️  Review .env file to customize settings (optional)"
else
    echo "✓ .env file already exists"
fi

# Run security checks
echo ""
echo "Running security checks..."

# Check for known vulnerabilities in dependencies
echo "  - Checking for known vulnerabilities..."
safety check || echo "    ⚠️  Some vulnerabilities found (review above)"

# Run bandit security linter on backend
echo "  - Running security linter..."
bandit -r backend/ -q -f txt || echo "    ⚠️  Some security issues found (review above)"

echo ""
echo "╭────────────────────────────────────────────────────────╮"
echo "│                                                        │"
echo "│        ✅  Installation Complete! 🎉                   │"
echo "│                                                        │"
echo "╰────────────────────────────────────────────────────────╯"
echo ""
echo "🚀 Next steps:"
echo ""
echo "  1️⃣  Start the server:"
echo "     ./start.sh"
echo ""
echo "  2️⃣  Open on your mobile device:"
echo "     📲 Scan the QR code or visit the URL shown"
echo ""
echo "  3️⃣  Enjoy Claude on your phone!"
echo "     🎉 Happy coding!"
echo ""
echo "📚 Documentation: ./docs/README.md"
echo ""
