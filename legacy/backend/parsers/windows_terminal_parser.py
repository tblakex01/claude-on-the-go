"""
Windows Terminal config parser

Config location: %LOCALAPPDATA%\\Packages\\Microsoft.WindowsTerminal_8wekyb3d8bbwe\\LocalState\\settings.json
Format: JSON

TODO for AI assistants: Implement Windows Terminal JSON parsing
- Parse settings.json
- Extract default profile from "defaultProfile"
- Find matching profile in "profiles.list"
- Extract colorScheme and font settings
- Parse color scheme from "schemes" array
- Convert colors to xterm.js format
"""

from pathlib import Path
from typing import Any, Dict, Optional

from .default_theme import get_default_theme


class WindowsTerminalParser:
    """Parses Windows Terminal JSON config and provides xterm.js theme"""

    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize parser with config path

        Args:
            config_path: Path to Windows Terminal settings.json
        """
        self.config_path = Path(config_path) if config_path else None

    def to_xterm_theme(self) -> Dict[str, Any]:
        """
        Convert Windows Terminal config to xterm.js theme format

        Returns:
            Dict with colors, font, fontSize for xterm.js
        """
        # TODO: Implement Windows Terminal JSON parsing
        # For now, return default theme
        print("[Windows Terminal] Parser not yet fully implemented, using default theme")
        return get_default_theme()
