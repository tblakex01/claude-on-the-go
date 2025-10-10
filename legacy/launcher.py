#!/usr/bin/env python3
"""
Claude-onTheGo Launcher
Manages backend and frontend processes with beautiful output and live monitoring
"""

import os
import select
import signal
import subprocess
import sys
import time
from pathlib import Path
from typing import List, Optional


class Colors:
    """ANSI color codes"""

    RED = "\033[0;31m"
    GREEN = "\033[0;32m"
    YELLOW = "\033[1;33m"
    BLUE = "\033[0;34m"
    MAGENTA = "\033[0;35m"
    CYAN = "\033[0;36m"
    WHITE = "\033[1;37m"
    GRAY = "\033[0;90m"
    NC = "\033[0m"  # No Color


class ProcessManager:
    """Manages backend and frontend processes"""

    def __init__(self):
        self.backend_process: Optional[subprocess.Popen] = None
        self.frontend_process: Optional[subprocess.Popen] = None
        self.backend_log: Optional[object] = None
        self.frontend_log: Optional[object] = None
        self.running = True

        # Setup signal handlers
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

    def _signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        print(f"\n\n{Colors.YELLOW}Stopping services...{Colors.NC}")
        self.running = False
        self.cleanup()
        sys.exit(0)

    def print_header(self):
        """Print launcher header"""
        print(f"\n{Colors.CYAN}╭{'─' * 54}╮{Colors.NC}")
        print(f"{Colors.CYAN}│{Colors.WHITE}  Claude-onTheGo Launcher{' ' * 29}│{Colors.NC}")
        print(f"{Colors.CYAN}╰{'─' * 54}╯{Colors.NC}\n")

    def start_backend(self, backend_port: int = 8000) -> bool:
        """Start backend process and capture startup output"""
        print(f"{Colors.GRAY}🧹 Cleaning up any existing instances...{Colors.NC}")

        # Kill processes on ports
        os.system(f"lsof -ti:{backend_port} | xargs kill -9 2>/dev/null || true")

        print(f"{Colors.GREEN}🚀 Starting backend...{Colors.NC}")

        # Create log file
        backend_log_path = Path("backend.log")
        self.backend_log = open(backend_log_path, "w")

        # Start backend process
        # Get the script directory and construct path to legacy/backend
        script_dir = Path(__file__).parent
        backend_dir = script_dir / "backend"

        self.backend_process = subprocess.Popen(
            ["python3", "-u", "app.py"],
            cwd=str(backend_dir),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
        )

        # Wait and capture startup output (including banner)
        print(f"   {Colors.GRAY}Backend PID: {self.backend_process.pid}{Colors.NC}\n")
        print(f"{Colors.GRAY}⏳ Waiting for backend to initialize...{Colors.NC}")

        startup_lines = []
        banner_started = False
        banner_complete = False
        max_wait = 10  # seconds
        start_time = time.time()

        while time.time() - start_time < max_wait:
            if self.backend_process.poll() is not None:
                print(f"{Colors.RED}❌ Backend failed to start{Colors.NC}")
                print(f"Check backend.log for errors")
                return False

            # Use select to check if output is available
            if self.backend_process.stdout:
                ready, _, _ = select.select([self.backend_process.stdout], [], [], 0.1)
                if ready:
                    line = self.backend_process.stdout.readline()
                    if line:
                        # Write to log file
                        self.backend_log.write(line)
                        self.backend_log.flush()

                        # Capture startup output
                        startup_lines.append(line)

                        # Detect banner start (look for the box top)
                        if "╭" in line and "─" in line:
                            banner_started = True

                        # Detect banner end (look for the separator line near the end)
                        if banner_started and line.strip().startswith("──────"):
                            banner_complete = True
                            # Wait a bit more to capture any final lines
                            time.sleep(0.5)
                            # Capture any remaining lines
                            while True:
                                ready, _, _ = select.select(
                                    [self.backend_process.stdout], [], [], 0.1
                                )
                                if ready:
                                    extra_line = self.backend_process.stdout.readline()
                                    if extra_line:
                                        self.backend_log.write(extra_line)
                                        self.backend_log.flush()
                                        startup_lines.append(extra_line)
                                    else:
                                        break
                                else:
                                    break
                            break

        # Display captured startup output (the beautiful banner!)
        if banner_started:
            print()
            for line in startup_lines:
                # Skip deprecation warnings and some internal logs
                if "DeprecationWarning" in line or "on_event is deprecated" in line:
                    continue
                if "FastAPI docs" in line or "@app.on_event" in line:
                    continue
                # Skip uvicorn INFO logs but keep APP logs with important info
                if (
                    "INFO:" in line
                    and "Started server" not in line
                    and "Uvicorn running" not in line
                ):
                    continue
                # Skip [APP] prefix lines except the ones with WebSocket info
                if "[APP]" in line and "WebSocket" not in line:
                    continue
                print(line.rstrip())
            print()

        # Wait a bit more for backend to be fully ready
        time.sleep(1)

        # Verify backend is still running
        if self.backend_process.poll() is not None:
            print(f"{Colors.RED}❌ Backend failed to start{Colors.NC}")
            return False

        # Save PID
        with open(".backend.pid", "w") as f:
            f.write(str(self.backend_process.pid))

        return True

    def start_frontend(self, frontend_port: int = 8001) -> bool:
        """Start frontend process"""
        # Kill any process on frontend port
        os.system(f"lsof -ti:{frontend_port} | xargs kill -9 2>/dev/null || true")

        print(f"{Colors.CYAN}🌐 Starting frontend...{Colors.NC}")

        # Create log file
        frontend_log_path = Path("frontend.log")
        self.frontend_log = open(frontend_log_path, "w")

        # Start frontend process
        # Get the script directory and construct path to legacy/frontend
        script_dir = Path(__file__).parent
        frontend_dir = script_dir / "frontend"

        self.frontend_process = subprocess.Popen(
            ["python3", "-u", "serve.py", str(frontend_port)],
            cwd=str(frontend_dir),
            stdout=self.frontend_log,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
        )

        print(f"   {Colors.GRAY}Frontend PID: {self.frontend_process.pid}{Colors.NC}\n")

        # Wait for frontend to start
        time.sleep(1)

        # Verify frontend is running
        if self.frontend_process.poll() is not None:
            print(f"{Colors.RED}❌ Frontend failed to start{Colors.NC}")
            return False

        # Save PID
        with open(".frontend.pid", "w") as f:
            f.write(str(self.frontend_process.pid))

        return True

    def print_status(self, backend_port: int, frontend_port: int):
        """Print service status"""
        print(f"{Colors.GREEN}✨ All services started!{Colors.NC}\n")

        print(f"{Colors.WHITE}📋 Process IDs:{Colors.NC}")
        print(f"   Backend:  {self.backend_process.pid if self.backend_process else 'N/A'}")
        print(f"   Frontend: {self.frontend_process.pid if self.frontend_process else 'N/A'}\n")

        print(f"{Colors.WHITE}📝 Logs:{Colors.NC}")
        print(f"   Backend:  {Path('backend.log').absolute()}")
        print(f"   Frontend: {Path('frontend.log').absolute()}\n")

        print(f"{Colors.WHITE}🛑 To stop all services:{Colors.NC}")
        print(f"   {Colors.GRAY}pkill -f 'python.*app.py'{Colors.NC}")
        print(f"   {Colors.GRAY}pkill -f 'python.*http.server'{Colors.NC}\n")
        print(f"   {Colors.GRAY}Or simply close this terminal.{Colors.NC}\n")

        print(f"{Colors.GRAY}{'─' * 58}{Colors.NC}\n")

    def monitor_logs(self):
        """Monitor logs and display in real-time"""
        print(f"{Colors.CYAN}👀 Monitoring services (Ctrl+C to stop)...{Colors.NC}\n")

        # Reopen log files for tailing
        backend_log = open("backend.log", "r")
        frontend_log = open("frontend.log", "r")

        # Seek to end
        backend_log.seek(0, 2)
        frontend_log.seek(0, 2)

        while self.running:
            # Check if processes are still alive
            if self.backend_process.poll() is not None:
                print(f"{Colors.RED}❌ Backend process died{Colors.NC}")
                break
            if self.frontend_process.poll() is not None:
                print(f"{Colors.RED}❌ Frontend process died{Colors.NC}")
                break

            # Read new lines from backend log
            backend_line = backend_log.readline()
            if backend_line:
                # Color code based on content
                if "ERROR" in backend_line or "Error" in backend_line:
                    print(f"{Colors.RED}{backend_line.rstrip()}{Colors.NC}")
                elif "WARNING" in backend_line or "Warning" in backend_line:
                    print(f"{Colors.YELLOW}{backend_line.rstrip()}{Colors.NC}")
                elif "INFO" in backend_line:
                    print(f"{Colors.CYAN}{backend_line.rstrip()}{Colors.NC}")
                else:
                    # Show request logs in gray
                    print(f"{Colors.GRAY}{backend_line.rstrip()}{Colors.NC}")

            # Read new lines from frontend log
            frontend_line = frontend_log.readline()
            if frontend_line:
                print(f"{Colors.MAGENTA}{frontend_line.rstrip()}{Colors.NC}")

            time.sleep(0.1)

        backend_log.close()
        frontend_log.close()

    def cleanup(self):
        """Clean up processes and files"""
        # Close log files
        if self.backend_log:
            self.backend_log.close()
        if self.frontend_log:
            self.frontend_log.close()

        # Kill processes
        if self.backend_process:
            try:
                self.backend_process.terminate()
                self.backend_process.wait(timeout=5)
            except:
                self.backend_process.kill()

        if self.frontend_process:
            try:
                self.frontend_process.terminate()
                self.frontend_process.wait(timeout=5)
            except:
                self.frontend_process.kill()

        # Remove PID files
        try:
            os.remove(".backend.pid")
        except:
            pass
        try:
            os.remove(".frontend.pid")
        except:
            pass

        print(f"{Colors.GREEN}✓ Stopped.{Colors.NC}")


def main():
    """Main launcher function"""
    # Get ports from environment or use defaults
    backend_port = int(os.getenv("BACKEND_PORT", "8000"))
    frontend_port = int(os.getenv("FRONTEND_PORT", "8001"))

    manager = ProcessManager()

    try:
        # Print header
        manager.print_header()

        # Start backend
        if not manager.start_backend(backend_port):
            manager.cleanup()
            sys.exit(1)

        # Start frontend
        if not manager.start_frontend(frontend_port):
            manager.cleanup()
            sys.exit(1)

        # Print status
        manager.print_status(backend_port, frontend_port)

        # Monitor logs
        manager.monitor_logs()

    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}Interrupted by user{Colors.NC}")
    except Exception as e:
        print(f"{Colors.RED}Error: {e}{Colors.NC}")
    finally:
        manager.cleanup()


if __name__ == "__main__":
    main()
