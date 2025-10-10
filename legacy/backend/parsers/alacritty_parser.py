"""
Alacritty terminal config parser

Config location: ~/.config/alacritty/alacritty.yml or ~/.alacritty.yml
Format: YAML

Parses Alacritty's color schemes and font settings
"""

from pathlib import Path
from typing import Any, Dict, Optional

import yaml

from .default_theme import get_default_theme


class AlacrittyParser:
    """Parses Alacritty YAML config and provides xterm.js theme"""

    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize parser with config path

        Args:
            config_path: Path to Alacritty YAML file
        """
        if config_path:
            self.config_path = Path(config_path).expanduser()
        else:
            # Try both common locations
            paths = [
                Path("~/.config/alacritty/alacritty.yml").expanduser(),
                Path("~/.config/alacritty/alacritty.yaml").expanduser(),
                Path("~/.alacritty.yml").expanduser(),
                Path("~/.alacritty.yaml").expanduser(),
            ]
            self.config_path = next((p for p in paths if p.exists()), paths[0])

    def _normalize_color(self, color: str) -> str:
        """
        Normalize color string to hex format

        Alacritty supports: "#rrggbb", "0xrrggbb", or named colors

        Args:
            color: Color string from config

        Returns:
            Normalized hex color string
        """
        if not color:
            return "#000000"

        color = str(color).strip()

        # Handle 0x format
        if color.startswith("0x"):
            return "#" + color[2:]

        # Handle # format
        if color.startswith("#"):
            return color

        # Fallback for unexpected formats
        return color

    def to_xterm_theme(self) -> Dict[str, Any]:
        """
        Convert Alacritty config to xterm.js theme format

        Returns:
            Dict with colors, font, fontSize for xterm.js
        """
        if not self.config_path.exists():
            print(f"[Alacritty] Config not found at {self.config_path}, using default theme")
            return get_default_theme()

        try:
            # Read YAML config
            with open(self.config_path, "r") as f:
                config = yaml.safe_load(f)

            if not config:
                print("[Alacritty] Empty config file, using default theme")
                return get_default_theme()

            theme = {"colors": {}, "font": "monospace", "fontSize": 13}

            # Extract colors
            colors_section = config.get("colors", {})

            # Primary colors (foreground, background, cursor)
            primary = colors_section.get("primary", {})
            if "foreground" in primary:
                theme["colors"]["foreground"] = self._normalize_color(primary["foreground"])
            if "background" in primary:
                theme["colors"]["background"] = self._normalize_color(primary["background"])

            # Cursor colors
            cursor = colors_section.get("cursor", {})
            if "cursor" in cursor:
                theme["colors"]["cursor"] = self._normalize_color(cursor["cursor"])
            if "text" in cursor:
                theme["colors"]["cursorAccent"] = self._normalize_color(cursor["text"])

            # Selection colors
            selection = colors_section.get("selection", {})
            if "background" in selection:
                theme["colors"]["selectionBackground"] = self._normalize_color(
                    selection["background"]
                )

            # Normal colors (ANSI 0-7)
            normal = colors_section.get("normal", {})
            color_map_normal = {
                "black": "black",
                "red": "red",
                "green": "green",
                "yellow": "yellow",
                "blue": "blue",
                "magenta": "magenta",
                "cyan": "cyan",
                "white": "white",
            }

            for alacritty_key, xterm_key in color_map_normal.items():
                if alacritty_key in normal:
                    theme["colors"][xterm_key] = self._normalize_color(normal[alacritty_key])

            # Bright colors (ANSI 8-15)
            bright = colors_section.get("bright", {})
            color_map_bright = {
                "black": "brightBlack",
                "red": "brightRed",
                "green": "brightGreen",
                "yellow": "brightYellow",
                "blue": "brightBlue",
                "magenta": "brightMagenta",
                "cyan": "brightCyan",
                "white": "brightWhite",
            }

            for alacritty_key, xterm_key in color_map_bright.items():
                if alacritty_key in bright:
                    theme["colors"][xterm_key] = self._normalize_color(bright[alacritty_key])

            # Extract font information
            font_section = config.get("font", {})

            # Font family
            normal_font = font_section.get("normal", {})
            if isinstance(normal_font, dict) and "family" in normal_font:
                theme["font"] = normal_font["family"]
            elif isinstance(normal_font, str):
                # Older config format might have font as string
                theme["font"] = normal_font

            # Font size
            if "size" in font_section:
                try:
                    theme["fontSize"] = int(float(font_section["size"]))
                except (ValueError, TypeError):
                    theme["fontSize"] = 13

            print(f"[Alacritty] Loaded theme from {self.config_path.name}")
            return theme

        except yaml.YAMLError as e:
            print(f"[Alacritty] YAML parsing error: {e}, using default theme")
            return get_default_theme()
        except Exception as e:
            print(f"[Alacritty] Error parsing config: {e}, using default theme")
            return get_default_theme()
