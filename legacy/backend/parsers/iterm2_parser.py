"""
iTerm2 terminal config parser

Config location: ~/Library/Preferences/com.googlecode.iterm2.plist
Format: Binary plist (XML plist)

Parses iTerm2's color profiles and font settings
"""

import plistlib
from pathlib import Path
from typing import Any, Dict, Optional

from .default_theme import get_default_theme


class ITerm2Parser:
    """Parses iTerm2 plist config and provides xterm.js theme"""

    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize parser with config path

        Args:
            config_path: Path to iTerm2 plist file
        """
        if config_path:
            self.config_path = Path(config_path).expanduser()
        else:
            self.config_path = Path(
                "~/Library/Preferences/com.googlecode.iterm2.plist"
            ).expanduser()

    def _rgb_to_hex(self, color_dict: Dict[str, float]) -> str:
        """
        Convert iTerm2 RGB color dict to hex string

        iTerm2 stores colors as floats 0-1 for each component

        Args:
            color_dict: Dict with "Red Component", "Green Component", "Blue Component"

        Returns:
            Hex color string like "#ff00aa"
        """
        r = int(color_dict.get("Red Component", 0) * 255)
        g = int(color_dict.get("Green Component", 0) * 255)
        b = int(color_dict.get("Blue Component", 0) * 255)
        return f"#{r:02x}{g:02x}{b:02x}"

    def _extract_font_name(self, font_string: str) -> str:
        """
        Extract font family name from iTerm2 font string

        iTerm2 format: "FontName-Style Size"
        Examples: "Menlo-Regular 12", "JetBrainsMono-Regular 14"

        Args:
            font_string: Font string from plist

        Returns:
            Font family name
        """
        if not font_string:
            return "monospace"

        # Split on space to separate name from size
        parts = font_string.split()
        if not parts:
            return "monospace"

        # First part is "FontName-Style", extract just the font name
        font_with_style = parts[0]
        font_name = font_with_style.split("-")[0]

        return font_name if font_name else "monospace"

    def _extract_font_size(self, font_string: str) -> int:
        """
        Extract font size from iTerm2 font string

        Args:
            font_string: Font string from plist

        Returns:
            Font size in points
        """
        if not font_string:
            return 13

        # Split on space, last part is usually the size
        parts = font_string.split()
        if len(parts) < 2:
            return 13

        try:
            return int(float(parts[-1]))
        except (ValueError, IndexError):
            return 13

    def _parse_profile(self, profile: Dict[str, Any]) -> Dict[str, Any]:
        """
        Parse a single iTerm2 profile

        Args:
            profile: Profile dict from plist

        Returns:
            Xterm.js theme dict
        """
        theme = {"colors": {}, "font": "monospace", "fontSize": 13}

        # Extract colors
        color_map = {
            "foreground": "Foreground Color",
            "background": "Background Color",
            "cursor": "Cursor Color",
            "cursorAccent": "Cursor Text Color",
            "selectionBackground": "Selection Color",
            "black": "Ansi 0 Color",
            "red": "Ansi 1 Color",
            "green": "Ansi 2 Color",
            "yellow": "Ansi 3 Color",
            "blue": "Ansi 4 Color",
            "magenta": "Ansi 5 Color",
            "cyan": "Ansi 6 Color",
            "white": "Ansi 7 Color",
            "brightBlack": "Ansi 8 Color",
            "brightRed": "Ansi 9 Color",
            "brightGreen": "Ansi 10 Color",
            "brightYellow": "Ansi 11 Color",
            "brightBlue": "Ansi 12 Color",
            "brightMagenta": "Ansi 13 Color",
            "brightCyan": "Ansi 14 Color",
            "brightWhite": "Ansi 15 Color",
        }

        for xterm_key, iterm_key in color_map.items():
            if iterm_key in profile:
                color_dict = profile[iterm_key]
                if isinstance(color_dict, dict):
                    theme["colors"][xterm_key] = self._rgb_to_hex(color_dict)

        # Extract font information
        # iTerm2 stores font as "FontName-Style Size"
        if "Normal Font" in profile:
            font_string = profile["Normal Font"]
            theme["font"] = self._extract_font_name(font_string)
            theme["fontSize"] = self._extract_font_size(font_string)

        return theme

    def to_xterm_theme(self) -> Dict[str, Any]:
        """
        Convert iTerm2 config to xterm.js theme format

        Returns:
            Dict with colors, font, fontSize for xterm.js
        """
        if not self.config_path.exists():
            print(f"[iTerm2] Config not found at {self.config_path}, using default theme")
            return get_default_theme()

        try:
            # Read plist file
            with open(self.config_path, "rb") as f:
                plist_data = plistlib.load(f)

            # iTerm2 stores profiles in "New Bookmarks" array
            # We'll use the first profile (default profile)
            profiles = plist_data.get("New Bookmarks", [])
            if not profiles:
                print("[iTerm2] No profiles found in plist, using default theme")
                return get_default_theme()

            # Parse the first profile (or look for "Default" profile)
            default_profile = None
            for profile in profiles:
                # Check if this is marked as the default profile
                if profile.get("Default Bookmark", False) or profile.get("Guid") == plist_data.get(
                    "Default Bookmark Guid"
                ):
                    default_profile = profile
                    break

            # If no default found, use first profile
            if default_profile is None:
                default_profile = profiles[0]

            theme = self._parse_profile(default_profile)
            print(f"[iTerm2] Loaded theme from profile: {default_profile.get('Name', 'Default')}")
            return theme

        except Exception as e:
            print(f"[iTerm2] Error parsing config: {e}, using default theme")
            return get_default_theme()
