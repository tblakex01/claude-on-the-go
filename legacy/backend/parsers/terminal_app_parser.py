"""
Terminal.app (macOS default) config parser

Config location: ~/Library/Preferences/com.apple.Terminal.plist
Format: Binary plist

Parses Terminal.app's color profiles and font settings
Note: Terminal.app stores colors as archived NSColor objects, which is complex to parse.
This parser handles basic cases and falls back to defaults for complex formats.
"""

import plistlib
import struct
from pathlib import Path
from typing import Any, Dict, Optional

from .default_theme import get_default_theme


class TerminalAppParser:
    """Parses Terminal.app plist config and provides xterm.js theme"""

    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize parser with config path

        Args:
            config_path: Path to Terminal.app plist file
        """
        if config_path:
            self.config_path = Path(config_path).expanduser()
        else:
            self.config_path = Path("~/Library/Preferences/com.apple.Terminal.plist").expanduser()

    def _parse_nscolor(self, data: bytes) -> Optional[str]:
        """
        Attempt to parse NSColor data to hex color

        Terminal.app stores colors as archived NSColor objects (NSData).
        This is a simplified parser that handles common RGB formats.

        Args:
            data: NSData bytes containing archived NSColor

        Returns:
            Hex color string or None if parsing fails
        """
        if not data or not isinstance(data, bytes):
            return None

        try:
            # NSColor can be in various formats. This is a simplified approach.
            # For full support, you'd need pyobjc to properly unarchive NSColor.

            # Try to find RGB values in the data
            # This is a heuristic approach - look for 3 consecutive float values
            # that could be RGB components (0.0-1.0)

            data_str = data.decode("latin1", errors="ignore")

            # Look for "RGB" or "DeviceRGB" color space indicators
            if "RGB" in data_str or "rgb" in data_str:
                # Try to extract float values
                # This is fragile but works for common cases
                import re

                # Look for sequences of bytes that might be floats
                floats = []
                for i in range(0, len(data) - 4, 1):
                    try:
                        val = struct.unpack(">f", data[i : i + 4])[0]  # Big-endian float
                        if 0.0 <= val <= 1.0:
                            floats.append(val)
                            if len(floats) >= 3:
                                # Found 3 valid floats, assume RGB
                                r = int(floats[-3] * 255)
                                g = int(floats[-2] * 255)
                                b = int(floats[-1] * 255)
                                return f"#{r:02x}{g:02x}{b:02x}"
                    except:
                        continue

        except Exception:
            pass

        return None

    def _parse_font(self, data: bytes) -> tuple[str, int]:
        """
        Attempt to parse NSFont data to font family and size

        Args:
            data: NSData bytes containing archived NSFont

        Returns:
            Tuple of (font_family, font_size)
        """
        if not data or not isinstance(data, bytes):
            return ("monospace", 13)

        try:
            data_str = data.decode("latin1", errors="ignore")

            # Look for font size (usually a small float like 11.0, 12.0, etc.)
            import re

            size_match = re.search(r"([0-9]{1,2}\.[0-9])", data_str)
            font_size = 13
            if size_match:
                try:
                    font_size = int(float(size_match.group(1)))
                except:
                    pass

            # Font family is harder to extract reliably
            # Common fonts: Menlo, Monaco, SF Mono
            for font in ["Menlo", "Monaco", "SF Mono", "Courier"]:
                if font in data_str:
                    return (font, font_size)

            return ("monospace", font_size)

        except Exception:
            return ("monospace", 13)

    def to_xterm_theme(self) -> Dict[str, Any]:
        """
        Convert Terminal.app config to xterm.js theme format

        Returns:
            Dict with colors, font, fontSize for xterm.js
        """
        if not self.config_path.exists():
            print(f"[Terminal.app] Config not found at {self.config_path}, using default theme")
            return get_default_theme()

        try:
            # Read plist file
            with open(self.config_path, "rb") as f:
                plist_data = plistlib.load(f)

            # Get default profile name
            default_profile_name = plist_data.get("Default Window Settings", "Basic")

            # Get all profiles
            profiles = plist_data.get("Window Settings", {})

            if default_profile_name not in profiles:
                print(
                    f"[Terminal.app] Default profile '{default_profile_name}' not found, using default theme"
                )
                return get_default_theme()

            profile = profiles[default_profile_name]

            theme = {"colors": {}, "font": "monospace", "fontSize": 13}

            # Color mapping
            color_keys = {
                "TextColor": "foreground",
                "BackgroundColor": "background",
                "CursorColor": "cursor",
                "ANSIBlackColor": "black",
                "ANSIRedColor": "red",
                "ANSIGreenColor": "green",
                "ANSIYellowColor": "yellow",
                "ANSIBlueColor": "blue",
                "ANSIMagentaColor": "magenta",
                "ANSICyanColor": "cyan",
                "ANSIWhiteColor": "white",
                "ANSIBrightBlackColor": "brightBlack",
                "ANSIBrightRedColor": "brightRed",
                "ANSIBrightGreenColor": "brightGreen",
                "ANSIBrightYellowColor": "brightYellow",
                "ANSIBrightBlueColor": "brightBlue",
                "ANSIBrightMagentaColor": "brightMagenta",
                "ANSIBrightCyanColor": "brightCyan",
                "ANSIBrightWhiteColor": "brightWhite",
            }

            # Try to parse colors
            parsed_colors = 0
            for terminal_key, xterm_key in color_keys.items():
                if terminal_key in profile:
                    color_data = profile[terminal_key]
                    hex_color = self._parse_nscolor(color_data)
                    if hex_color:
                        theme["colors"][xterm_key] = hex_color
                        parsed_colors += 1

            # If we couldn't parse any colors, fall back to default
            if parsed_colors == 0:
                print("[Terminal.app] Could not parse NSColor data, using default theme")
                return get_default_theme()

            # Try to parse font
            if "Font" in profile:
                font_data = profile["Font"]
                font_family, font_size = self._parse_font(font_data)
                theme["font"] = font_family
                theme["fontSize"] = font_size

            print(
                f"[Terminal.app] Loaded theme from profile '{default_profile_name}' (parsed {parsed_colors} colors)"
            )
            return theme

        except Exception as e:
            print(f"[Terminal.app] Error parsing config: {e}, using default theme")
            return get_default_theme()
