"""
Alacritty terminal config parser

Config location: ~/.config/alacritty/alacritty.yml or ~/.alacritty.yml
Format: YAML

TODO for AI assistants: Implement YAML parsing
- Use PyYAML to parse config
- Extract colors from colors.primary, colors.normal, colors.bright
- Extract font family and size from font.normal and font.size
- Handle both old and new config formats
"""

from pathlib import Path
from typing import Dict, Any, Optional

from .default_theme import get_default_theme


class AlacrittyParser:
    """Parses Alacritty YAML config and provides xterm.js theme"""

    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize parser with config path

        Args:
            config_path: Path to Alacritty YAML file
        """
        self.config_path = Path(config_path) if config_path else None

    def to_xterm_theme(self) -> Dict[str, Any]:
        """
        Convert Alacritty config to xterm.js theme format

        Returns:
            Dict with colors, font, fontSize for xterm.js
        """
        # TODO: Implement Alacritty YAML parsing
        # For now, return default theme
        print("[Alacritty] Parser not yet fully implemented, using default theme")
        return get_default_theme()
