#!/usr/bin/env bash
# Claude-onTheGo - Start Script
# Launches backend and frontend servers using Python launcher

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Load environment variables if .env exists
if [ -f ".env" ]; then
    export $(grep -v '^#' .env | xargs)
fi

# Default ports from config or fallback
export BACKEND_PORT=${BACKEND_PORT:-8000}
export FRONTEND_PORT=${FRONTEND_PORT:-8001}

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo -e "${RED}❌ Virtual environment not found${NC}"
    echo "Please run ./install.sh first"
    exit 1
fi

# Activate virtual environment
source venv/bin/activate

# Check if claude is available
if ! command -v claude &> /dev/null; then
    echo -e "${YELLOW}⚠️  Claude CLI not found in PATH${NC}"
    echo "The server will start, but you may need to install Claude CLI:"
    echo "https://claude.ai/download"
    echo ""
fi

# Launch using Python launcher (legacy mode)
python3 legacy/launcher.py
