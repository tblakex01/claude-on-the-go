"""
Ghostty config parser for Claude-onTheGo
Parses key-value format and converts to xterm.js theme format
"""

import os
from pathlib import Path
from typing import Any, Dict, List, Optional

# Built-in ghostty themes mapped to xterm.js color format
GHOSTTY_THEMES = {
    "Duotone Dark": {
        "foreground": "#b7a8ff",
        "background": "#1f1d27",
        "cursor": "#b7a8ff",
        "cursorAccent": "#1f1d27",
        "selectionBackground": "#353147",
        "black": "#1f1d27",
        "red": "#d8393d",
        "green": "#2dcd73",
        "yellow": "#d8b122",
        "blue": "#fea44c",
        "magenta": "#b7a8ff",
        "cyan": "#c0c5ce",
        "white": "#eeeeee",
        "brightBlack": "#6a6977",
        "brightRed": "#d8393d",
        "brightGreen": "#2dcd73",
        "brightYellow": "#d8b122",
        "brightBlue": "#fea44c",
        "brightMagenta": "#b7a8ff",
        "brightCyan": "#c0c5ce",
        "brightWhite": "#ffffff",
    },
    "Catppuccin Mocha": {
        "foreground": "#cdd6f4",
        "background": "#1e1e2e",
        "cursor": "#f5e0dc",
        "cursorAccent": "#1e1e2e",
        "selectionBackground": "#585b70",
        "black": "#45475a",
        "red": "#f38ba8",
        "green": "#a6e3a1",
        "yellow": "#f9e2af",
        "blue": "#89b4fa",
        "magenta": "#f5c2e7",
        "cyan": "#94e2d5",
        "white": "#bac2de",
        "brightBlack": "#585b70",
        "brightRed": "#f38ba8",
        "brightGreen": "#a6e3a1",
        "brightYellow": "#f9e2af",
        "brightBlue": "#89b4fa",
        "brightMagenta": "#f5c2e7",
        "brightCyan": "#94e2d5",
        "brightWhite": "#a6adc8",
    },
}

# Default theme if config missing or theme not found
DEFAULT_THEME = {
    "foreground": "#ffffff",
    "background": "#000000",
    "cursor": "#ffffff",
    "cursorAccent": "#000000",
    "selectionBackground": "#444444",
    "black": "#000000",
    "red": "#cc0000",
    "green": "#4e9a06",
    "yellow": "#c4a000",
    "blue": "#3465a4",
    "magenta": "#75507b",
    "cyan": "#06989a",
    "white": "#d3d7cf",
    "brightBlack": "#555753",
    "brightRed": "#ef2929",
    "brightGreen": "#8ae234",
    "brightYellow": "#fce94f",
    "brightBlue": "#729fcf",
    "brightMagenta": "#ad7fa8",
    "brightCyan": "#34e2e2",
    "brightWhite": "#eeeeec",
}


class GhosttyConfig:
    """Parses ghostty config and provides xterm.js theme"""

    # Keys that can appear multiple times in config
    REPEATABLE_KEYS = {"keybind", "palette", "font-family"}

    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize parser with config path

        Args:
            config_path: Path to ghostty config file.
                        Defaults to ~/.config/ghostty/config
        """
        if config_path is None:
            config_path = os.path.expanduser("~/.config/ghostty/config")

        self.config_path = Path(config_path)
        self.config = self._parse_config()

    def _parse_config(self) -> Dict[str, Any]:
        """Parse ghostty config file into dict"""
        config = {}

        if not self.config_path.exists():
            return config

        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()

                    # Skip empty lines and comments
                    if not line or line.startswith("#"):
                        continue

                    # Split on FIRST equals sign only
                    if "=" not in line:
                        continue

                    key, _, value = line.partition("=")
                    key = key.strip()
                    value = value.strip()

                    # Handle repeatable keys as lists
                    if key in self.REPEATABLE_KEYS:
                        if key not in config:
                            config[key] = []
                        config[key].append(value)
                    else:
                        config[key] = value

        except Exception as e:
            print(f"Warning: Failed to parse ghostty config: {e}")
            return {}

        return config

    def get_theme_colors(self) -> Dict[str, str]:
        """
        Get theme colors for xterm.js

        Returns:
            Dict with xterm.js color keys
        """
        theme_name = self.config.get("theme", "").strip()

        # Look up theme in built-in themes
        if theme_name in GHOSTTY_THEMES:
            colors = GHOSTTY_THEMES[theme_name].copy()
        else:
            # Use default theme
            colors = DEFAULT_THEME.copy()
            if theme_name:
                print(f"Warning: Theme '{theme_name}' not found, using default")

        # Override with custom palette colors if present
        if "palette" in self.config:
            # TODO: Parse palette entries like "0 = #000000"
            pass

        return colors

    def get_font_family(self) -> str:
        """Get font family from config"""
        # font-family can be repeatable, use first one
        font = self.config.get("font-family", "monospace")
        if isinstance(font, list):
            font = font[0] if font else "monospace"
        return font

    def get_font_size(self) -> int:
        """Get font size from config"""
        try:
            size = int(self.config.get("font-size", "14"))
            return size
        except (ValueError, TypeError):
            return 14

    def to_xterm_theme(self) -> Dict[str, Any]:
        """
        Convert ghostty config to xterm.js theme format

        Returns:
            Dict with colors, font, fontSize for xterm.js
        """
        return {
            "colors": self.get_theme_colors(),
            "font": self.get_font_family(),
            "fontSize": self.get_font_size(),
        }


def parse_ghostty_config(config_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Convenience function to parse ghostty config and return xterm.js theme

    Args:
        config_path: Path to ghostty config file

    Returns:
        Dict with colors, font, fontSize
    """
    parser = GhosttyConfig(config_path)
    return parser.to_xterm_theme()
