"""
Terminal.app (macOS default) config parser

Config location: ~/Library/Preferences/com.apple.Terminal.plist
Format: Binary plist

TODO for AI assistants: Implement Terminal.app plist parsing
- Use plistlib to read binary plist
- Extract default profile from "Default Window Settings"
- Parse profile colors (ANSI colors stored as NSData/XML)
- Extract font name and size
- Handle multiple profiles
"""

from pathlib import Path
from typing import Dict, Any, Optional

from .default_theme import get_default_theme


class TerminalAppParser:
    """Parses Terminal.app plist config and provides xterm.js theme"""

    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize parser with config path

        Args:
            config_path: Path to Terminal.app plist file
        """
        self.config_path = Path(config_path) if config_path else None

    def to_xterm_theme(self) -> Dict[str, Any]:
        """
        Convert Terminal.app config to xterm.js theme format

        Returns:
            Dict with colors, font, fontSize for xterm.js
        """
        # TODO: Implement Terminal.app plist parsing
        # For now, return default theme
        print("[Terminal.app] Parser not yet fully implemented, using default theme")
        return get_default_theme()
