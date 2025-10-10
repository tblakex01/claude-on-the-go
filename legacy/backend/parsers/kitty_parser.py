"""
Kitty terminal config parser

Config location: ~/.config/kitty/kitty.conf
Format: Key-value pairs (similar to Ghostty)

Parses Kitty's color schemes and font settings
"""

from pathlib import Path
from typing import Any, Dict, Optional

from .default_theme import get_default_theme


class KittyParser:
    """Parses Kitty config and provides xterm.js theme"""

    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize parser with config path

        Args:
            config_path: Path to Kitty config file
        """
        if config_path:
            self.config_path = Path(config_path).expanduser()
        else:
            self.config_path = Path("~/.config/kitty/kitty.conf").expanduser()

    def _parse_config(self) -> Dict[str, str]:
        """
        Parse Kitty config file into key-value dict

        Returns:
            Dict of config keys to values
        """
        config = {}

        if not self.config_path.exists():
            return config

        try:
            with open(self.config_path, "r") as f:
                for line in f:
                    line = line.strip()

                    # Skip comments and empty lines
                    if not line or line.startswith("#"):
                        continue

                    # Handle include directives (for theme files)
                    if line.startswith("include "):
                        include_path = line.split(None, 1)[1]
                        # Resolve relative to kitty config directory
                        include_file = self.config_path.parent / include_path
                        if include_file.exists():
                            # Recursively parse included file
                            included_config = self._parse_file(include_file)
                            config.update(included_config)
                        continue

                    # Parse key-value pairs (space-separated)
                    parts = line.split(None, 1)
                    if len(parts) == 2:
                        key, value = parts
                        config[key] = value

        except Exception as e:
            print(f"[Kitty] Error reading config: {e}")

        return config

    def _parse_file(self, file_path: Path) -> Dict[str, str]:
        """Parse a single Kitty config file"""
        config = {}
        try:
            with open(file_path, "r") as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith("#"):
                        continue

                    parts = line.split(None, 1)
                    if len(parts) == 2:
                        key, value = parts
                        config[key] = value
        except Exception:
            pass
        return config

    def to_xterm_theme(self) -> Dict[str, Any]:
        """
        Convert Kitty config to xterm.js theme format

        Returns:
            Dict with colors, font, fontSize for xterm.js
        """
        if not self.config_path.exists():
            print(f"[Kitty] Config not found at {self.config_path}, using default theme")
            return get_default_theme()

        try:
            config = self._parse_config()

            if not config:
                print("[Kitty] Empty config, using default theme")
                return get_default_theme()

            theme = {"colors": {}, "font": "monospace", "fontSize": 13}

            # Extract basic colors
            if "foreground" in config:
                theme["colors"]["foreground"] = config["foreground"]
            if "background" in config:
                theme["colors"]["background"] = config["background"]
            if "cursor" in config:
                theme["colors"]["cursor"] = config["cursor"]
            if "cursor_text_color" in config:
                theme["colors"]["cursorAccent"] = config["cursor_text_color"]
            if "selection_background" in config:
                theme["colors"]["selectionBackground"] = config["selection_background"]
            if "selection_foreground" in config:
                theme["colors"]["selectionForeground"] = config["selection_foreground"]

            # Extract ANSI colors (color0-color15)
            color_map = {
                "color0": "black",
                "color1": "red",
                "color2": "green",
                "color3": "yellow",
                "color4": "blue",
                "color5": "magenta",
                "color6": "cyan",
                "color7": "white",
                "color8": "brightBlack",
                "color9": "brightRed",
                "color10": "brightGreen",
                "color11": "brightYellow",
                "color12": "brightBlue",
                "color13": "brightMagenta",
                "color14": "brightCyan",
                "color15": "brightWhite",
            }

            for kitty_key, xterm_key in color_map.items():
                if kitty_key in config:
                    theme["colors"][xterm_key] = config[kitty_key]

            # Extract font settings
            if "font_family" in config:
                theme["font"] = config["font_family"]

            if "font_size" in config:
                try:
                    theme["fontSize"] = int(float(config["font_size"]))
                except (ValueError, TypeError):
                    theme["fontSize"] = 13

            print(f"[Kitty] Loaded theme from {self.config_path.name}")
            return theme

        except Exception as e:
            print(f"[Kitty] Error parsing config: {e}, using default theme")
            return get_default_theme()
