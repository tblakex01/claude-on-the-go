# Server

FastAPI WebSocket + REST API implementation for claude-on-the-go.

## Purpose

This directory contains the web server implementation that exposes the core business logic via HTTP and WebSocket APIs.

## Components

### WebSocket Handler
- Real-time terminal streaming
- Bidirectional I/O between client and PTY
- Connection management and reconnection
- Flow control and backpressure handling

### REST API
- Session management endpoints
- Health check and status
- Configuration endpoints
- Authentication and authorization

### Middleware
- Rate limiting (token bucket algorithm)
- Request validation and sanitization
- Security headers (CSP, X-Frame-Options)
- Logging and monitoring

## API Endpoints

### WebSocket
- `ws://host:8000/ws` - Terminal I/O stream

### REST
- `GET /health` - Health check
- `GET /api/sessions` - List active sessions
- `POST /api/sessions` - Create new session
- `GET /api/sessions/{id}` - Get session details
- `DELETE /api/sessions/{id}` - Close session

## Security Features

- Token bucket rate limiting (10 msg/sec, 100KB/sec)
- Input size validation (10KB max per message)
- Terminal size validation (1-500 rows/cols)
- Content Security Policy headers
- Log redaction for sensitive data
- Optional token authentication

## Usage Example

```python
from fastapi import FastAPI
from server.websocket import websocket_endpoint
from server.api import router

app = FastAPI()
app.include_router(router)
app.add_api_websocket_route("/ws", websocket_endpoint)
```

## Dependencies

- FastAPI for web framework
- uvicorn for ASGI server
- python-multipart for form data
- Core module for business logic
