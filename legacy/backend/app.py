"""
FastAPI backend for Claude-onTheGo
Secure WebSockets with rate limiting, validation, and message batching
"""

import asyncio
import json
import os
import sys
import time
from typing import Optional, Set

from claude_wrapper import ClaudeWrapper
from clipboard_manager import ClipboardManager
from config import Config
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, status
from fastapi.middleware.cors import CORSMiddleware
from network_utils import print_startup_banner
from parsers import parse_terminal_config
from security import AuthManager, RateLimiter, redact_logs, sanitize_input, validate_message
from session_manager import SessionManager

# Add parent directory to path for integrations import
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))
from integrations import NotificationService, PromptDetector

app = FastAPI(title="Claude-onTheGo Backend")

# CORS with configurable origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=Config.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


class MessageBatcher:
    """Batches messages to reduce websocket frame overhead"""

    def __init__(self, window_ms: int = 30):
        """
        Initialize batcher

        Args:
            window_ms: Batching window in milliseconds (10-50ms recommended)
        """
        self.window_ms = window_ms
        self.window_sec = window_ms / 1000.0
        self.buffer = []
        self.last_send = 0
        self.pending_task = None

    def add(self, text: str):
        """Add text to batch buffer"""
        self.buffer.append(text)

    def should_flush(self) -> bool:
        """Check if should flush buffer"""
        if not self.buffer:
            return False

        now = time.time()
        elapsed = now - self.last_send

        # Flush if window expired or buffer is large
        return elapsed >= self.window_sec or len(self.buffer) > 100

    def get_and_clear(self) -> str:
        """Get batched text and clear buffer"""
        if not self.buffer:
            return ""

        text = "".join(self.buffer)
        self.buffer.clear()
        self.last_send = time.time()
        return text


class ConnectionManager:
    """Manages WebSocket connections and claude process with security

    SINGLE-USER MODE: Only allows one active WebSocket connection at a time.
    When a new connection is established, all existing connections are automatically closed.

    SESSION PERSISTENCE: Sessions survive disconnections and can be reconnected.
    """

    def __init__(self):
        self.active_connections: Set[WebSocket] = set()
        self.claude: ClaudeWrapper = None
        self.batchers = {}  # WebSocket -> MessageBatcher
        self.flush_task = None
        self.heartbeat_task = None
        self.current_connection: Optional[WebSocket] = None
        self.current_session_id: Optional[str] = None

        # Session management
        self.session_manager = SessionManager(session_timeout=3600)  # 1 hour

        # Clipboard sync
        self.clipboard_manager = (
            ClipboardManager(sync_interval=Config.CLIPBOARD_SYNC_INTERVAL)
            if Config.ENABLE_CLIPBOARD_SYNC
            else None
        )

        # Security components
        self.rate_limiter = RateLimiter(
            messages_per_second=Config.RATE_LIMIT_MESSAGES,
            bytes_per_second=Config.RATE_LIMIT_BYTES,
        )
        self.auth_manager = AuthManager(
            enabled=Config.ENABLE_AUTH,
            token=Config.AUTH_TOKEN if Config.ENABLE_AUTH else None,
        )

        # Push notifications (optional - enabled via env vars)
        self.notification_service = NotificationService()
        self.prompt_detector = (
            PromptDetector(debounce_seconds=30.0) if self.notification_service.enabled else None
        )

    def _log(self, message: str):
        """Log with optional redaction"""
        print(redact_logs(message, enabled=Config.LOG_REDACTION))

    async def connect(
        self,
        websocket: WebSocket,
        auth_token: Optional[str] = None,
        session_id: Optional[str] = None,
    ):
        """Handle new WebSocket connection with authentication and security

        SINGLE-USER MODE: Automatically closes all existing connections before
        accepting the new one. This prevents output duplication from multiple tabs/devices.

        SESSION PERSISTENCE: If session_id provided, reconnects to existing session.
        """
        # Check authentication if enabled
        if not self.auth_manager.verify(auth_token):
            self._log("[WS] Authentication failed")
            await websocket.close(
                code=status.WS_1008_POLICY_VIOLATION, reason="Authentication required"
            )
            return

        self._log("[WS] Starting connection...")

        # Check for session reconnection
        if session_id:
            existing_session = self.session_manager.get_session(session_id)
            if existing_session:
                self._log(f"[WS] Reconnecting to existing session {session_id}")
                self.claude = existing_session.claude_wrapper
                self.current_session_id = session_id

        # SINGLE-USER GUARD: Close all existing connections
        if self.active_connections:
            self._log(
                f"[WS] Single-user mode: Closing {len(self.active_connections)} existing connection(s)"
            )
            for old_ws in list(self.active_connections):
                try:
                    await old_ws.close(code=1000, reason="New connection established")
                    self._log("[WS] Closed old connection")
                except Exception as e:
                    self._log(f"[WS] Error closing old connection: {e}")

            # Clear all tracking
            self.active_connections.clear()
            self.batchers.clear()
            self._log("[WS] All old connections cleared")

        # Now accept the new connection
        await websocket.accept()
        self.active_connections.add(websocket)
        self.batchers[websocket] = MessageBatcher(window_ms=30)
        self.current_connection = websocket
        self._log("[WS] New connection accepted (single-user mode active)")

        # Send theme config on connect
        try:
            self._log("[WS] Parsing terminal config...")
            theme_config = parse_terminal_config()
            self._log(f"[WS] Theme config loaded")
            theme_msg = {
                "type": "theme",
                "colors": theme_config["colors"],
                "font": theme_config["font"],
                "fontSize": theme_config["fontSize"],
            }
            self._log("[WS] Sending theme to client...")
            await self._send_json(websocket, theme_msg)
            self._log("[WS] Theme sent successfully")
        except Exception as e:
            self._log(f"[WS] Failed to send theme: {e}")

        # Start claude process if not running
        self._log(f"[WS] Claude status: alive={self.claude.is_alive() if self.claude else False}")
        if self.claude is None or not self.claude.is_alive():
            self._log("[WS] Starting claude process...")
            self.claude = ClaudeWrapper(
                command=Config.CLAUDE_COMMAND,
                high_watermark=100_000,
                low_watermark=10_000,
            )
            await self.claude.start(self._handle_claude_output)
            self._log("[WS] Claude process started")

            # Create new session
            self.current_session_id = self.session_manager.create_session(self.claude)
            await self._send_json(
                websocket, {"type": "session", "session_id": self.current_session_id}
            )

        # Start flush task if not running
        if self.flush_task is None or self.flush_task.done():
            self._log("[WS] Starting flush task...")
            self.flush_task = asyncio.create_task(self._flush_loop())

        # Start heartbeat task if not running
        if self.heartbeat_task is None or self.heartbeat_task.done():
            self._log("[WS] Starting heartbeat task...")
            self.heartbeat_task = asyncio.create_task(self._heartbeat_loop())

        # Start clipboard monitoring if enabled
        if self.clipboard_manager and Config.ENABLE_CLIPBOARD_SYNC:
            self._log("[WS] Starting clipboard sync...")
            self.clipboard_manager.start_monitoring(self._sync_clipboard_to_remote)

        self._log("[WS] Connection setup complete!")

    def disconnect(self, websocket: WebSocket):
        """Handle WebSocket disconnection"""
        self.active_connections.discard(websocket)
        self.batchers.pop(websocket, None)

        # Clear current connection if it's the one disconnecting
        if self.current_connection == websocket:
            self.current_connection = None

        # Stop clipboard monitoring if no connections
        if not self.active_connections and self.clipboard_manager:
            self.clipboard_manager.stop_monitoring()
            self._log("[WS] No active connections, stopping clipboard sync")

        # Stop claude if no connections
        if not self.active_connections and self.claude:
            asyncio.create_task(self.claude.stop())
            self.claude = None
            self._log("[WS] No active connections, stopping Claude process")

    async def _handle_claude_output(self, text: str):
        """Handle output from claude process"""
        # Add to all batchers
        for ws in list(self.active_connections):
            if ws in self.batchers:
                self.batchers[ws].add(text)

        # Detect Claude prompts for push notifications
        if self.prompt_detector and not self.active_connections:
            self.prompt_detector.add_output(text)
            if self.prompt_detector.should_notify():
                # User is away (no active connections), send notification
                session_url = f"http://{Config.BACKEND_HOST}:{Config.FRONTEND_PORT}"
                await self.notification_service.notify_claude_prompt(session_url)

    async def _flush_loop(self):
        """Periodically flush batched messages"""
        task_id = id(asyncio.current_task())
        self._log(f"[FLUSH] Starting flush loop")

        while self.active_connections:
            try:
                # Check each connection's batcher
                for ws in list(self.active_connections):
                    batcher = self.batchers.get(ws)
                    if batcher and batcher.should_flush():
                        text = batcher.get_and_clear()
                        if text:
                            msg = {
                                "type": "output",
                                "text": text,
                                "is_prompt": False,
                            }
                            await self._send_json(ws, msg)

                            # Notify flow control
                            if self.claude:
                                self.claude.notify_bytes_sent(len(text))

                await asyncio.sleep(0.01)  # 10ms check interval

            except Exception as e:
                self._log(f"[FLUSH] Error: {e}")
                await asyncio.sleep(0.1)

        self._log("[FLUSH] Flush loop exiting (no connections)")

    async def _heartbeat_loop(self):
        """Send heartbeat pings every 30s"""
        while self.active_connections:
            try:
                await asyncio.sleep(30)

                # Send ping to all connections
                for ws in list(self.active_connections):
                    try:
                        await ws.send_json({"type": "ping"})
                    except Exception as e:
                        self._log(f"[HEARTBEAT] Failed to ping: {e}")
                        self.disconnect(ws)

            except Exception as e:
                self._log(f"[HEARTBEAT] Error: {e}")

    async def _send_json(self, websocket: WebSocket, data: dict):
        """Send JSON as binary frame"""
        try:
            # Encode to JSON bytes
            json_bytes = json.dumps(data).encode("utf-8")
            # Send as binary frame for efficiency
            await websocket.send_bytes(json_bytes)
        except Exception as e:
            self._log(f"[WS] Send failed: {e}")
            self.disconnect(websocket)

    async def handle_input(self, text: str, connection_id: str):
        """Handle user input with validation and sanitization"""
        # Sanitize input
        sanitized = sanitize_input(text, allow_ansi=True)

        if self.claude and self.claude.is_alive():
            await self.claude.send_input(sanitized)

    async def handle_control(self, char: str):
        """Handle control character"""
        if self.claude and self.claude.is_alive():
            await self.claude.send_control(char)

    async def handle_resize(self, rows: int, cols: int):
        """Handle terminal resize"""
        self._log(f"[WS] Terminal resized to {rows}x{cols}")
        if self.claude and self.claude.is_alive():
            self.claude.set_window_size(rows, cols)

    async def _sync_clipboard_to_remote(self, text: str):
        """
        Sync Mac clipboard to remote device

        Args:
            text: Clipboard content to sync
        """
        if not self.current_connection:
            return

        try:
            msg = {"type": "clipboard_sync", "text": text}
            await self._send_json(self.current_connection, msg)
            self._log(f"[CLIPBOARD] Synced to remote ({len(text)} chars)")
        except Exception as e:
            self._log(f"[CLIPBOARD] Failed to sync to remote: {e}")

    async def handle_clipboard_set(self, text: str):
        """
        Handle clipboard content from remote device (phone)

        Args:
            text: Clipboard content from phone
        """
        if not self.clipboard_manager:
            self._log("[CLIPBOARD] Clipboard sync is disabled")
            return

        try:
            await self.clipboard_manager.set_from_remote(text)
        except Exception as e:
            self._log(f"[CLIPBOARD] Error setting clipboard: {e}")


# Global connection manager
manager = ConnectionManager()


@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "service": "Claude-onTheGo Backend",
        "status": "running",
        "connections": len(manager.active_connections),
        "claude_alive": manager.claude.is_alive() if manager.claude else False,
    }


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for terminal communication with security"""
    # Generate connection ID for rate limiting
    connection_id = id(websocket)

    # Extract auth token from query params if authentication is enabled
    auth_token = None
    if Config.ENABLE_AUTH:
        auth_token = websocket.query_params.get("token")

    await manager.connect(websocket, auth_token=auth_token)

    try:
        while True:
            # Receive message (as binary frame)
            data = await websocket.receive_bytes()

            # Rate limiting check
            allowed, reason = manager.rate_limiter.check_rate_limit(str(connection_id), len(data))
            if not allowed:
                manager._log(f"[WS] Rate limit exceeded: {reason}")
                await websocket.send_json({"type": "error", "message": reason})
                continue

            # Decode JSON
            try:
                message = json.loads(data.decode("utf-8"))
            except json.JSONDecodeError:
                # Try as text frame fallback
                try:
                    text_data = await websocket.receive_text()
                    message = json.loads(text_data)
                except:
                    manager._log("[WS] Invalid JSON received")
                    continue

            # Validate message structure
            valid, error_msg = validate_message(message)
            if not valid:
                manager._log(f"[WS] Invalid message: {error_msg}")
                await websocket.send_json({"type": "error", "message": error_msg})
                continue

            # Handle message types
            msg_type = message.get("type")

            if msg_type == "input":
                text = message.get("text", "")
                await manager.handle_input(text, str(connection_id))

            elif msg_type == "control":
                char = message.get("char", "c")
                await manager.handle_control(char)

            elif msg_type == "resize":
                rows = message.get("rows", 24)
                cols = message.get("cols", 80)
                await manager.handle_resize(rows, cols)

            elif msg_type == "pong":
                # Client responded to ping
                pass

            elif msg_type == "clipboard_set":
                # Client setting Mac clipboard from phone
                text = message.get("text", "")
                await manager.handle_clipboard_set(text)

    except WebSocketDisconnect:
        manager.disconnect(websocket)
        manager._log("[WS] Client disconnected")

    except Exception as e:
        manager._log(f"[WS] Error: {e}")
        manager.disconnect(websocket)


@app.on_event("startup")
async def startup_event():
    """Run on app startup"""
    print("[APP] Claude-onTheGo backend starting...")
    print(f"[APP] WebSocket endpoint: ws://{Config.BACKEND_HOST}:{Config.BACKEND_PORT}/ws")
    print()
    # Print beautiful startup banner with mDNS URL and QR code
    print_startup_banner(frontend_port=Config.FRONTEND_PORT)


@app.on_event("shutdown")
async def shutdown_event():
    """Run on app shutdown"""
    print("[APP] Shutting down...")

    # Stop claude process
    if manager.claude:
        await manager.claude.stop()

    # Close all connections
    for ws in list(manager.active_connections):
        try:
            await ws.close()
        except:
            pass


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app:app",
        host=Config.BACKEND_HOST,
        port=Config.BACKEND_PORT,
        log_level=Config.LOG_LEVEL.lower(),
        reload=False,
    )
