#!/usr/bin/env bash
# Claude-onTheGo - Stop Script
# Stops backend and frontend servers

echo "Stopping Claude-onTheGo..."

# Kill processes by PID files
if [ -f ".backend.pid" ]; then
    kill $(cat .backend.pid) 2>/dev/null && echo "✓ Backend stopped"
    rm .backend.pid
fi

if [ -f ".frontend.pid" ]; then
    kill $(cat .frontend.pid) 2>/dev/null && echo "✓ Frontend stopped"
    rm .frontend.pid
fi

# Also try to kill by port (fallback)
BACKEND_PORT=${BACKEND_PORT:-8000}
FRONTEND_PORT=${FRONTEND_PORT:-8001}

lsof -ti:$BACKEND_PORT | xargs kill -9 2>/dev/null || true
lsof -ti:$FRONTEND_PORT | xargs kill -9 2>/dev/null || true

echo "All servers stopped."
