"""
iTerm2 terminal config parser

Config location: ~/Library/Preferences/com.googlecode.iterm2.plist
Format: Binary plist (XML plist)

TODO for AI assistants: Implement plist parsing
- Use plistlib to read binary plist
- Extract color scheme from profiles
- Parse RGB values and convert to hex
- Extract font family and size
"""

from pathlib import Path
from typing import Dict, Any, Optional

from .default_theme import get_default_theme


class ITerm2Parser:
    """Parses iTerm2 plist config and provides xterm.js theme"""

    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize parser with config path

        Args:
            config_path: Path to iTerm2 plist file
        """
        self.config_path = Path(config_path) if config_path else None

    def to_xterm_theme(self) -> Dict[str, Any]:
        """
        Convert iTerm2 config to xterm.js theme format

        Returns:
            Dict with colors, font, fontSize for xterm.js
        """
        # TODO: Implement iTerm2 plist parsing
        # For now, return default theme
        print("[iTerm2] Parser not yet fully implemented, using default theme")
        return get_default_theme()
