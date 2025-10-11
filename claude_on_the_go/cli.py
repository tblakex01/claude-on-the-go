#!/usr/bin/env python3
"""
Claude-onTheGo CLI

Command-line interface for starting, stopping, and managing the claude-on-the-go server.
"""

import argparse
import os
import signal
import subprocess
import sys
import time
from pathlib import Path


def get_project_root() -> Path:
    """Get the project root directory"""
    # When installed via pip, this will be in site-packages
    # We need to find the legacy/ directory
    module_path = Path(__file__).parent

    # Check if we're in development mode (running from source)
    if (module_path.parent / "legacy").exists():
        return module_path.parent

    # In installed mode, legacy/ should be in package data
    if (module_path / "legacy").exists():
        return module_path

    # Fallback: current directory
    return Path.cwd()


def read_pid_file(pid_file: Path) -> int | None:
    """Read PID from file"""
    try:
        if pid_file.exists():
            return int(pid_file.read_text().strip())
    except (ValueError, OSError):
        pass
    return None


def is_process_running(pid: int) -> bool:
    """Check if process with given PID is running"""
    try:
        os.kill(pid, 0)
        return True
    except OSError:
        return False


def cmd_start(args):
    """Start the claude-on-the-go server"""
    root = get_project_root()

    # Check if already running
    backend_pid_file = root / ".backend.pid"
    frontend_pid_file = root / ".frontend.pid"

    backend_pid = read_pid_file(backend_pid_file)
    if backend_pid and is_process_running(backend_pid):
        print("❌ Server is already running!")
        print(f"   Backend PID: {backend_pid}")
        print()
        print("To stop: claude-on-the-go stop")
        print("To restart: claude-on-the-go restart")
        return 1

    # Run the launcher
    launcher_script = root / "legacy" / "launcher.py"
    if not launcher_script.exists():
        print(f"❌ Error: launcher.py not found at {launcher_script}")
        print("   Make sure claude-on-the-go is properly installed")
        return 1

    print("🚀 Starting claude-on-the-go...")

    try:
        # Run launcher (it handles daemonization)
        subprocess.run([sys.executable, str(launcher_script)], check=True)
        return 0
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to start server: {e}")
        return 1
    except KeyboardInterrupt:
        print("\n⚠️  Startup interrupted")
        return 1


def cmd_stop(args):
    """Stop the claude-on-the-go server"""
    root = get_project_root()

    backend_pid_file = root / ".backend.pid"
    frontend_pid_file = root / ".frontend.pid"

    backend_pid = read_pid_file(backend_pid_file)
    frontend_pid = read_pid_file(frontend_pid_file)

    if not backend_pid and not frontend_pid:
        print("⚠️  Server is not running")
        return 0

    print("🛑 Stopping claude-on-the-go...")

    stopped_any = False

    # Stop backend
    if backend_pid and is_process_running(backend_pid):
        print(f"   Stopping backend (PID {backend_pid})...")
        try:
            os.kill(backend_pid, signal.SIGTERM)
            time.sleep(1)

            # Force kill if still running
            if is_process_running(backend_pid):
                os.kill(backend_pid, signal.SIGKILL)

            stopped_any = True
        except OSError:
            pass

        # Clean up PID file
        backend_pid_file.unlink(missing_ok=True)

    # Stop frontend
    if frontend_pid and is_process_running(frontend_pid):
        print(f"   Stopping frontend (PID {frontend_pid})...")
        try:
            os.kill(frontend_pid, signal.SIGTERM)
            time.sleep(1)

            # Force kill if still running
            if is_process_running(frontend_pid):
                os.kill(frontend_pid, signal.SIGKILL)

            stopped_any = True
        except OSError:
            pass

        # Clean up PID file
        frontend_pid_file.unlink(missing_ok=True)

    if stopped_any:
        print("✅ Server stopped")
    else:
        print("⚠️  No running processes found (cleaning up PID files)")
        backend_pid_file.unlink(missing_ok=True)
        frontend_pid_file.unlink(missing_ok=True)

    return 0


def cmd_restart(args):
    """Restart the claude-on-the-go server"""
    print("🔄 Restarting claude-on-the-go...")
    cmd_stop(args)
    time.sleep(1)
    return cmd_start(args)


def cmd_status(args):
    """Check server status"""
    root = get_project_root()

    backend_pid_file = root / ".backend.pid"
    frontend_pid_file = root / ".frontend.pid"

    backend_pid = read_pid_file(backend_pid_file)
    frontend_pid = read_pid_file(frontend_pid_file)

    print("Claude-onTheGo Status")
    print("=" * 50)

    # Backend status
    if backend_pid and is_process_running(backend_pid):
        print(f"✅ Backend:  Running (PID {backend_pid})")
    else:
        print("❌ Backend:  Stopped")
        if backend_pid:
            backend_pid_file.unlink(missing_ok=True)

    # Frontend status
    if frontend_pid and is_process_running(frontend_pid):
        print(f"✅ Frontend: Running (PID {frontend_pid})")
    else:
        print("❌ Frontend: Stopped")
        if frontend_pid:
            frontend_pid_file.unlink(missing_ok=True)

    print()

    # If running, show URLs
    if (backend_pid and is_process_running(backend_pid)) or (
        frontend_pid and is_process_running(frontend_pid)
    ):

        # Try to get host from environment or config
        host = os.getenv("HOST", "localhost")
        frontend_port = int(os.getenv("FRONTEND_PORT", "8001"))
        backend_port = int(os.getenv("BACKEND_PORT", "8000"))

        print(f"📱 Frontend: http://{host}:{frontend_port}")
        print(f"🔌 Backend:  http://{host}:{backend_port}")
        print()

    return 0


def cmd_logs(args):
    """Show server logs"""
    root = get_project_root()
    log_dir = root / "logs"

    if not log_dir.exists():
        print("⚠️  No logs directory found")
        return 1

    # Find most recent log files
    backend_logs = sorted(log_dir.glob("backend-*.log"), reverse=True)
    frontend_logs = sorted(log_dir.glob("frontend-*.log"), reverse=True)

    if args.backend and backend_logs:
        print(f"📄 Backend log: {backend_logs[0]}")
        print("=" * 50)
        print(backend_logs[0].read_text())
    elif args.frontend and frontend_logs:
        print(f"📄 Frontend log: {frontend_logs[0]}")
        print("=" * 50)
        print(frontend_logs[0].read_text())
    else:
        # Show tail of both
        if backend_logs:
            print(f"📄 Backend (last 20 lines): {backend_logs[0]}")
            print("=" * 50)
            lines = backend_logs[0].read_text().split("\n")
            print("\n".join(lines[-20:]))
            print()

        if frontend_logs:
            print(f"📄 Frontend (last 20 lines): {frontend_logs[0]}")
            print("=" * 50)
            lines = frontend_logs[0].read_text().split("\n")
            print("\n".join(lines[-20:]))

    return 0


def cmd_qr(args):
    """Show QR code for mobile connection"""
    # Import here to avoid startup delay
    try:
        import qrcode
    except ImportError:
        print("❌ Error: qrcode library not installed")
        print("   Install with: pip install qrcode[pil]")
        return 1

    # Get host and port
    host = os.getenv("HOST")
    if not host:
        # Try to detect local IP
        import socket

        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            s.connect(("8.8.8.8", 80))
            host = s.getsockname()[0]
        except Exception:
            host = "localhost"
        finally:
            s.close()

    port = int(os.getenv("FRONTEND_PORT", "8001"))
    url = f"http://{host}:{port}"

    # Generate QR code
    qr = qrcode.QRCode()
    qr.add_data(url)
    qr.make()

    print()
    print(f"📱 Scan to connect: {url}")
    print()
    qr.print_ascii(invert=True)
    print()

    return 0


def cmd_version(args):
    """Show version information"""
    from . import __version__

    print(f"claude-on-the-go v{__version__}")
    return 0


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        prog="claude-on-the-go",
        description="Access Claude Code CLI from your mobile device",
        epilog="For more information: https://github.com/MatthewJamisonJS/claude-on-the-go",
    )

    parser.add_argument("--version", action="version", version="%(prog)s 1.0.0")

    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # Start command
    parser_start = subparsers.add_parser("start", help="Start the server")
    parser_start.set_defaults(func=cmd_start)

    # Stop command
    parser_stop = subparsers.add_parser("stop", help="Stop the server")
    parser_stop.set_defaults(func=cmd_stop)

    # Restart command
    parser_restart = subparsers.add_parser("restart", help="Restart the server")
    parser_restart.set_defaults(func=cmd_restart)

    # Status command
    parser_status = subparsers.add_parser("status", help="Check server status")
    parser_status.set_defaults(func=cmd_status)

    # Logs command
    parser_logs = subparsers.add_parser("logs", help="Show server logs")
    parser_logs.add_argument("--backend", action="store_true", help="Show backend logs only")
    parser_logs.add_argument("--frontend", action="store_true", help="Show frontend logs only")
    parser_logs.set_defaults(func=cmd_logs)

    # QR command
    parser_qr = subparsers.add_parser("qr", help="Show QR code for mobile connection")
    parser_qr.set_defaults(func=cmd_qr)

    # Version command
    parser_version = subparsers.add_parser("version", help="Show version")
    parser_version.set_defaults(func=cmd_version)

    # Parse arguments
    args = parser.parse_args()

    # Show help if no command
    if not args.command:
        parser.print_help()
        return 0

    # Run command
    try:
        return args.func(args)
    except KeyboardInterrupt:
        print("\n⚠️  Interrupted")
        return 130
    except Exception as e:
        print(f"❌ Error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
