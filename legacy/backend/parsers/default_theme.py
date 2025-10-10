"""
Default terminal theme for Claude-onTheGo
Used when no terminal config is detected
"""

from typing import Any, Dict

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


def get_default_theme() -> Dict[str, Any]:
    """
    Get default xterm.js theme configuration

    Returns:
        Dict with colors, font, fontSize
    """
    return {
        "colors": DEFAULT_THEME.copy(),
        "font": "monospace",
        "fontSize": 14,
    }
