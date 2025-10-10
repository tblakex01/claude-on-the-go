"""
Terminal auto-detection for Claude-onTheGo
Detects which terminal is installed and loads appropriate config parser
"""

import os
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

from .alacritty_parser import AlacrittyParser

# Import all terminal parsers
from .ghostty_parser import GhosttyParser
from .hyper_parser import HyperParser
from .iterm2_parser import ITerm2Parser
from .kitty_parser import KittyParser
from .terminal_app_parser import TerminalAppParser
from .warp_parser import WarpParser
from .windows_terminal_parser import WindowsTerminalParser

# Terminal detection patterns
TERMINALS = [
    {
        "name": "Ghostty",
        "config_path": "~/.config/ghostty/config",
        "parser": GhosttyParser,
        "priority": 1,
    },
    {
        "name": "iTerm2",
        "config_path": "~/Library/Preferences/com.googlecode.iterm2.plist",
        "parser": ITerm2Parser,
        "priority": 2,
    },
    {
        "name": "Alacritty",
        "config_path": "~/.config/alacritty/alacritty.yml",
        "alt_path": "~/.alacritty.yml",
        "parser": AlacrittyParser,
        "priority": 3,
    },
    {
        "name": "Kitty",
        "config_path": "~/.config/kitty/kitty.conf",
        "parser": KittyParser,
        "priority": 4,
    },
    {
        "name": "Warp",
        "config_path": "~/.warp",
        "parser": WarpParser,
        "priority": 5,
    },
    {
        "name": "Hyper",
        "config_path": "~/.hyper.js",
        "parser": HyperParser,
        "priority": 6,
    },
    {
        "name": "Terminal.app",
        "config_path": "~/Library/Preferences/com.apple.Terminal.plist",
        "parser": TerminalAppParser,
        "priority": 7,
    },
    {
        "name": "Windows Terminal",
        "config_path": os.path.expandvars(
            "%LOCALAPPDATA%\\Packages\\Microsoft.WindowsTerminal_8wekyb3d8bbwe\\LocalState\\settings.json"
        ),
        "parser": WindowsTerminalParser,
        "priority": 8,
    },
]


def detect_terminal() -> Optional[Tuple[str, Path, type]]:
    """
    Auto-detect which terminal is installed

    Returns:
        Tuple of (terminal_name, config_path, parser_class) or None if not found
    """
    detected = []

    for terminal in TERMINALS:
        config_path = Path(os.path.expanduser(terminal["config_path"]))

        # Check main path
        if config_path.exists():
            detected.append(
                (terminal["name"], config_path, terminal["parser"], terminal["priority"])
            )
            continue

        # Check alternative path if exists
        if "alt_path" in terminal:
            alt_path = Path(os.path.expanduser(terminal["alt_path"]))
            if alt_path.exists():
                detected.append(
                    (terminal["name"], alt_path, terminal["parser"], terminal["priority"])
                )

    if not detected:
        return None

    # Sort by priority and return highest priority terminal
    detected.sort(key=lambda x: x[3])
    name, path, parser, _ = detected[0]

    print(f"[TERMINAL] Detected: {name} at {path}")
    return name, path, parser


def parse_terminal_config(config_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Parse terminal config and return xterm.js theme

    Args:
        config_path: Optional path to specific terminal config.
                    If not provided, auto-detects terminal.

    Returns:
        Dict with colors, font, fontSize for xterm.js
    """
    if config_path:
        # Try to parse the specific file
        # Determine parser based on file extension/path
        path = Path(config_path)

        if "ghostty" in str(path):
            parser = GhosttyParser(config_path)
        elif "iterm2" in str(path) or path.suffix == ".plist":
            parser = ITerm2Parser(config_path)
        elif "alacritty" in str(path):
            parser = AlacrittyParser(config_path)
        elif "kitty" in str(path):
            parser = KittyParser(config_path)
        elif "warp" in str(path):
            parser = WarpParser(config_path)
        elif "hyper" in str(path):
            parser = HyperParser(config_path)
        elif "Terminal" in str(path):
            parser = TerminalAppParser(config_path)
        elif "WindowsTerminal" in str(path) or "settings.json" in str(path):
            parser = WindowsTerminalParser(config_path)
        else:
            # Unknown terminal, use default
            from .default_theme import get_default_theme

            print(f"[TERMINAL] Unknown config format, using default theme")
            return get_default_theme()

        return parser.to_xterm_theme()

    # Auto-detect terminal
    detection = detect_terminal()

    if detection:
        name, path, parser_class = detection
        parser = parser_class(str(path))
        return parser.to_xterm_theme()

    # No terminal detected, use default theme
    from .default_theme import get_default_theme

    print("[TERMINAL] No terminal config detected, using default theme")
    return get_default_theme()
