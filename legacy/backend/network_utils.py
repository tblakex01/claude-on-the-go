"""
Network utilities for Claude-onTheGo
Detects hostname, IP addresses, and generates QR codes for easy mobile connection
"""

import socket
import subprocess
from typing import List, Tuple

import qrcode
from security.sanitizer import redact_logs


def get_hostname() -> str:
    """Get local hostname for mDNS/Bonjour"""
    try:
        # Try to get the Bonjour hostname (macOS/Linux)
        result = subprocess.run(
            ["scutil", "--get", "LocalHostName"],
            capture_output=True,
            text=True,
            check=True,
            timeout=2,
        )
        hostname = result.stdout.strip()
        return f"{hostname}.local"
    except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
        # Fallback to socket hostname
        return socket.gethostname()


def get_active_ips() -> List[str]:
    """
    Get all active IP addresses (excluding localhost)
    Returns list of IPs, prioritizing non-loopback addresses
    """
    ips = []

    try:
        # Get hostname and resolve it
        hostname = socket.gethostname()

        # Get all addresses for this host
        addr_infos = socket.getaddrinfo(hostname, None)

        for addr_info in addr_infos:
            ip = addr_info[4][0]
            # Skip localhost and IPv6
            if ip != "127.0.0.1" and ":" not in ip:
                if ip not in ips:
                    ips.append(ip)

    except Exception as e:
        print(f"[NETWORK] Error getting IPs via socket: {e}")

    # Fallback: Try ifconfig parsing (Unix-like systems)
    if not ips:
        try:
            result = subprocess.run(["ifconfig"], capture_output=True, text=True, timeout=2)
            lines = result.stdout.split("\n")
            for line in lines:
                if "inet " in line and "127.0.0.1" not in line:
                    parts = line.split()
                    if len(parts) >= 2:
                        ip = parts[1]
                        if ip not in ips:
                            ips.append(ip)
        except (FileNotFoundError, subprocess.TimeoutExpired, Exception) as e:
            print(f"[NETWORK] Error getting IPs via ifconfig: {e}")

    return ips


def generate_qr_code(url: str, size: int = 3) -> str:
    """
    Generate ASCII QR code for terminal display

    Args:
        url: URL to encode
        size: QR code size (1-3, smaller is better for terminal)

    Returns:
        ASCII art QR code as string
    """
    try:
        qr = qrcode.QRCode(
            version=1,  # Small QR code
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=1,
            border=2,
        )
        qr.add_data(url)
        qr.make(fit=True)

        # Generate ASCII art using Unicode blocks
        matrix = qr.get_matrix()
        ascii_qr = []

        for row in matrix:
            line = []
            for cell in row:
                # Use full block for filled cells, space for empty
                line.append("██" if cell else "  ")
            ascii_qr.append("".join(line))

        return "\n".join(ascii_qr)

    except Exception as e:
        print(f"[QR] Error generating QR code: {e}")
        return "[QR code generation failed]"


def get_connection_info(frontend_port: int = 8001) -> Tuple[str, List[str], str]:
    """
    Get all connection information needed for startup banner

    Args:
        frontend_port: Port where frontend is served (default 8001)

    Returns:
        Tuple of (mdns_url, ip_urls, qr_code_ascii)
    """
    hostname = get_hostname()
    mdns_url = f"http://{hostname}:{frontend_port}"

    ips = get_active_ips()
    ip_urls = [f"http://{ip}:{frontend_port}" for ip in ips]

    # Generate QR code for primary URL (prefer mDNS)
    qr_code = generate_qr_code(mdns_url)

    return mdns_url, ip_urls, qr_code


def print_startup_banner(frontend_port: int = 8001):
    """
    Print beautiful startup banner with connection info and QR code

    Args:
        frontend_port: Port where frontend is served (default 8001)
    """
    mdns_url, ip_urls, qr_code = get_connection_info(frontend_port)

    # Build the banner
    banner = []
    banner.append("")
    banner.append("╭────────────────────────────────────────────────────────╮")
    banner.append("│                                                        │")
    banner.append("│        🚀 Claude-onTheGo Ready!                        │")
    banner.append("│                                                        │")
    banner.append("╰────────────────────────────────────────────────────────╯")
    banner.append("")
    banner.append("📱 Open on your mobile device:")
    banner.append("")
    banner.append("   🏠 mDNS (recommended):")
    banner.append(f"      {mdns_url}")
    banner.append("")

    if ip_urls:
        banner.append("   🌐 Direct IP (fallback):")
        for ip_url in ip_urls:
            banner.append(f"      {ip_url}")
        banner.append("")

    banner.append("📷 Scan to connect:")
    banner.append("")

    # Add QR code
    qr_lines = qr_code.split("\n")
    for line in qr_lines:
        banner.append(f"   {line}")

    banner.append("")
    banner.append("💡 Tip: mDNS URL works on WiFi and Personal Hotspot!")
    banner.append("")
    banner.append("─" * 58)
    banner.append("")

    # Print all lines
    for line in banner:
        print(line)
