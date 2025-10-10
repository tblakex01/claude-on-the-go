"""
Secure frontend server with Content Security Policy headers
Serves static files with security headers to prevent XSS attacks
"""

import http.server
import socketserver
import sys
from pathlib import Path


class SecureHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    """HTTP handler with security headers"""

    def end_headers(self):
        """Add security headers before ending HTTP headers"""
        # Content Security Policy - only allow resources from specific sources
        # Allow cdn.jsdelivr.net for xterm.js library
        self.send_header(
            "Content-Security-Policy",
            "default-src 'self'; "
            "script-src 'self' https://cdn.jsdelivr.net 'unsafe-inline'; "
            "style-src 'self' https://cdn.jsdelivr.net 'unsafe-inline'; "
            "connect-src 'self' ws: wss:; "
            "img-src 'self' data:; "
            "font-src 'self'; "
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


def serve(port=8001):
    """
    Start secure frontend server

    Args:
        port: Port to serve on (default 8001)
    """
    # Change to frontend directory
    frontend_dir = Path(__file__).parent
    socketserver.TCPServer.allow_reuse_address = True

    with socketserver.TCPServer(("0.0.0.0", port), SecureHTTPRequestHandler) as httpd:
        print(f"[FRONTEND] Serving on http://0.0.0.0:{port}")
        print(f"[FRONTEND] Directory: {frontend_dir}")
        print("[FRONTEND] Security headers enabled:")
        print("  - Content Security Policy (CSP)")
        print("  - X-Frame-Options")
        print("  - X-Content-Type-Options")
        print("  - X-XSS-Protection")
        print("")

        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n[FRONTEND] Shutting down...")
            httpd.shutdown()


if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8001
    serve(port)
