"""
Secure frontend server with Content Security Policy headers
Serves static files with security headers to prevent XSS attacks
"""

import http.server
import logging
import os
import socket
import socketserver
import sys
from pathlib import Path

logger = logging.getLogger(__name__)


def _get_default_host() -> str:
    """
    Auto-detect local IP address for secure binding (LAN only, never 0.0.0.0).

    Returns first active non-localhost IP, or 127.0.0.1 if none found.
    Can be overridden by FRONTEND_HOST env var (use with caution).
    """
    env_host = os.getenv("FRONTEND_HOST")
    if env_host:
        # Allow explicit override (including 0.0.0.0 for advanced users)
        if env_host == "0.0.0.0":  # nosec B104 - String comparison, not binding
            logger.warning(
                "[SECURITY WARNING] Binding to 0.0.0.0 exposes service to all network interfaces!"
            )
            logger.warning(
                "[SECURITY WARNING] Only use this on trusted networks or behind a firewall."
            )
        return env_host  # Return user-specified host (validated above)

    # Auto-detect first active local IP
    try:
        hostname = socket.gethostname()
        addr_infos = socket.getaddrinfo(hostname, None)

        for addr_info in addr_infos:
            ip = addr_info[4][0]
            # Return first non-localhost IPv4 address
            if ip != "127.0.0.1" and ":" not in ip:
                return ip
    except Exception:
        # Socket detection can fail safely - fallback to 127.0.0.1 below
        pass

    # Fallback to localhost (secure default)
    return "127.0.0.1"


class SecureHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    """HTTP handler with security headers"""

    def end_headers(self):
        """Add security headers before ending HTTP headers"""
        # Content Security Policy - only allow resources from specific sources
        # Allow cdn.jsdelivr.net for xterm.js library
        # data: URIs allowed for fonts (embedded fonts in CSS) and images
        self.send_header(
            "Content-Security-Policy",
            "default-src 'self'; "
            "script-src 'self' https://cdn.jsdelivr.net 'unsafe-inline'; "
            "style-src 'self' https://cdn.jsdelivr.net 'unsafe-inline' data:; "
            "connect-src 'self' ws: wss:; "
            "img-src 'self' data:; "
            "font-src 'self' data: https://cdn.jsdelivr.net; "
            "object-src 'none'; "
            "base-uri 'self'; "
            "form-action 'self';",
        )

        # Prevent clickjacking
        self.send_header("X-Frame-Options", "SAMEORIGIN")

        # Prevent MIME sniffing
        self.send_header("X-Content-Type-Options", "nosniff")

        # Enable XSS protection
        self.send_header("X-XSS-Protection", "1; mode=block")

        # Referrer policy
        self.send_header("Referrer-Policy", "strict-origin-when-cross-origin")

        # Permissions policy (disable unnecessary features)
        self.send_header(
            "Permissions-Policy", "geolocation=(), microphone=(), camera=(), payment=()"
        )

        super().end_headers()

    def log_message(self, format, *args):
        """Override to add timestamp to logs"""
        sys.stderr.write(f"[FRONTEND] {self.address_string()} - {format % args}\n")


def serve(port=8001, host=None):
    """
    Start secure frontend server

    Args:
        port: Port to serve on (default 8001)
        host: Host to bind to (default auto-detect local IP, never 0.0.0.0)
    """
    # Auto-detect host if not specified
    if host is None:
        host = _get_default_host()

    # Change to frontend directory
    frontend_dir = Path(__file__).parent
    os.chdir(frontend_dir)  # Actually change to the directory!
    socketserver.TCPServer.allow_reuse_address = True

    with socketserver.TCPServer((host, port), SecureHTTPRequestHandler) as httpd:
        logger.info(f"[FRONTEND] Serving on http://{host}:{port}")
        logger.info(f"[FRONTEND] Directory: {frontend_dir}")
        logger.info("[FRONTEND] Security headers enabled:")
        logger.info("  - Content Security Policy (CSP)")
        logger.info("  - X-Frame-Options")
        logger.info("  - X-Content-Type-Options")
        logger.info("  - X-XSS-Protection")
        logger.info("")

        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            logger.info("\n[FRONTEND] Shutting down...")
            httpd.shutdown()


if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8001
    serve(port)
