# Adding Terminal Support

This guide explains how to implement terminal config parsers for Claude-onTheGo.

## Overview

Claude-onTheGo currently has **full support for Ghostty** and **stub implementations** for 7 other popular terminals. Each stub parser returns a default theme with clear TODOs for implementation.

## Supported Terminals

| Terminal | Status | Config Location | Format |
|----------|--------|----------------|---------|
| **Ghostty** | ✅ **Fully Implemented** | `~/.config/ghostty/config` | Key-value |
| iTerm2 | ⏳ Stub | `~/Library/Preferences/com.googlecode.iterm2.plist` | Binary plist |
| Alacritty | ⏳ Stub | `~/.config/alacritty/alacritty.yml` | YAML |
| Kitty | ⏳ Stub | `~/.config/kitty/kitty.conf` | Key-value |
| Warp | ⏳ Stub | `~/.warp/themes/` | YAML |
| Hyper | ⏳ Stub | `~/.hyper.js` | JavaScript |
| Terminal.app | ⏳ Stub | `~/Library/Preferences/com.apple.Terminal.plist` | Binary plist |
| Windows Terminal | ⏳ Stub | `%LOCALAPPDATA%\\Packages\\...\\settings.json` | JSON |

## How Terminal Detection Works

1. `terminal_detector.py` checks for each terminal's config file in priority order
2. When a config is found, it instantiates the appropriate parser
3. Parser converts terminal-specific config → xterm.js theme format
4. If no config is found, uses default theme

## Parser Interface

Every parser must implement:

```python
class TerminalParser:
    def __init__(self, config_path: Optional[str] = None):
        """Initialize with path to config file"""
        pass

    def to_xterm_theme(self) -> Dict[str, Any]:
        """Convert terminal config to xterm.js theme format

        Returns:
            {
                "colors": {
                    "foreground": "#ffffff",
                    "background": "#000000",
                    "cursor": "#ffffff",
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
                },
                "font": "JetBrains Mono",
                "fontSize": 14
            }
        """
        pass
```

## Implementation Guide for Each Terminal

### 1. iTerm2 (`iterm2_parser.py`)

**Config Format:** Binary plist (Property List)

**Key Steps:**
1. Use Python's `plistlib` module to read binary plist
2. Navigate to `New Bookmarks` → find default profile
3. Extract colors from profile (e.g., `Ansi 0 Color`, `Foreground Color`)
4. Colors are stored as dictionaries with `Red Component`, `Green Component`, `Blue Component` (0.0-1.0)
5. Convert RGB 0.0-1.0 → hex format
6. Extract font from `Normal Font` field

**Example iTerm2 plist structure:**
```python
{
    "New Bookmarks": [
        {
            "Name": "Default",
            "Foreground Color": {"Red": 1.0, "Green": 1.0, "Blue": 1.0},
            "Background Color": {"Red": 0.0, "Green": 0.0, "Blue": 0.0},
            "Ansi 0 Color": {...},  # Black
            "Ansi 1 Color": {...},  # Red
            # ... Ansi 2-15
            "Normal Font": "JetBrainsMono-Regular 14"
        }
    ]
}
```

**Dependencies needed:** None (plistlib is stdlib)

---

### 2. Alacritty (`alacritty_parser.py`)

**Config Format:** YAML

**Key Steps:**
1. Use `PyYAML` to parse config
2. Extract `colors.primary.foreground`, `colors.primary.background`
3. Extract `colors.normal` (black, red, green, yellow, blue, magenta, cyan, white)
4. Extract `colors.bright` for bright variants
5. Extract `font.normal.family` and `font.size`
6. Handle both old config format (top-level) and new format (nested)

**Example Alacritty YAML structure:**
```yaml
colors:
  primary:
    foreground: '#ffffff'
    background: '#000000'
  normal:
    black:   '#000000'
    red:     '#cc0000'
    # ... other colors
  bright:
    black:   '#555753'
    # ... other colors

font:
  normal:
    family: "JetBrains Mono"
  size: 14
```

**Dependencies needed:** `pyyaml` (add to requirements.txt)

---

### 3. Kitty (`kitty_parser.py`)

**Config Format:** Key-value pairs (similar to Ghostty!)

**Key Steps:**
1. Parse file line-by-line like Ghostty parser
2. Extract `foreground`, `background`, `cursor` colors
3. Extract `color0` through `color15` for ANSI palette
4. Map color0-7 → normal colors, color8-15 → bright colors
5. Extract `font_family` and `font_size`
6. Handle `include` directives for theme files

**Example Kitty config:**
```conf
foreground #ffffff
background #000000
cursor #ffffff

color0  #000000
color1  #cc0000
# ... color2-15

font_family JetBrains Mono
font_size 14.0

# May include external theme
include ./theme.conf
```

**Dependencies needed:** None

---

### 4. Warp (`warp_parser.py`)

**Config Format:** YAML theme files + JSON preferences

**Key Steps:**
1. Read `~/.warp/preferences.json` to find active theme name
2. Look for theme YAML in `~/.warp/themes/{theme_name}.yaml`
3. Parse YAML for `accent`, `background`, `foreground`, `terminal_colors`
4. `terminal_colors` contains `normal` and `bright` color arrays
5. Extract font settings from preferences.json

**Example Warp theme YAML:**
```yaml
accent: '#89b4fa'
background: '#1e1e2e'
foreground: '#cdd6f4'
terminal_colors:
  normal:
    black: '#45475a'
    red: '#f38ba8'
    # ... other colors
  bright:
    black: '#585b70'
    # ... other colors
```

**Dependencies needed:** `pyyaml`

---

### 5. Hyper (`hyper_parser.py`)

**Config Format:** JavaScript module

**Key Steps:**
1. Read `.hyper.js` file
2. Parse JavaScript to extract `module.exports.config` object
3. Look for `foregroundColor`, `backgroundColor`, `cursorColor`
4. Extract `colors` array (16 ANSI colors in order)
5. Extract `fontFamily` and `fontSize`
6. Handle potential plugins that modify config

**Example Hyper config:**
```javascript
module.exports = {
  config: {
    foregroundColor: '#fff',
    backgroundColor: '#000',
    cursorColor: '#fff',
    colors: [
      '#000000',  // black
      '#cc0000',  // red
      // ... 14 more colors
    ],
    fontFamily: '"JetBrains Mono", monospace',
    fontSize: 14
  }
};
```

**Dependencies needed:** Could use regex or a JavaScript parser like `js2py`

---

### 6. Terminal.app (`terminal_app_parser.py`)

**Config Format:** Binary plist

**Key Steps:**
1. Similar to iTerm2, use `plistlib`
2. Find default profile in `Default Window Settings`
3. Extract from `Window Settings` dictionary
4. Colors may be stored as NSData (archived color objects)
5. Parse archived NSColor objects if needed
6. Extract font name and size

**Example Terminal.app plist:**
```python
{
    "Default Window Settings": "Basic",
    "Window Settings": {
        "Basic": {
            "ANSIBlackColor": <NSData...>,
            "Font": <NSData...>,
            # ... other settings
        }
    }
}
```

**Dependencies needed:** None (plistlib), may need `biplist` for NSData parsing

---

### 7. Windows Terminal (`windows_terminal_parser.py`)

**Config Format:** JSON

**Key Steps:**
1. Parse `settings.json`
2. Find `defaultProfile` GUID
3. Find matching profile in `profiles.list` by GUID
4. Extract `colorScheme` name from profile
5. Find color scheme in `schemes` array
6. Extract all colors from scheme
7. Extract `font.face` and `font.size` from profile

**Example Windows Terminal JSON:**
```json
{
  "defaultProfile": "{...guid...}",
  "profiles": {
    "list": [
      {
        "guid": "{...guid...}",
        "name": "PowerShell",
        "colorScheme": "One Half Dark",
        "font": {
          "face": "Cascadia Code",
          "size": 12
        }
      }
    ]
  },
  "schemes": [
    {
      "name": "One Half Dark",
      "foreground": "#DCDFE4",
      "background": "#282C34",
      "black": "#282C34",
      // ... other colors
    }
  ]
}
```

**Dependencies needed:** None (json is stdlib)

---

## Testing Your Implementation

1. Create a test config file for your terminal
2. Run the parser:
```python
from backend.parsers.your_terminal_parser import YourTerminalParser

parser = YourTerminalParser("/path/to/config")
theme = parser.to_xterm_theme()

print(theme)
# Should output valid xterm.js theme format
```

3. Test with auto-detection:
```python
from backend.parsers import parse_terminal_config

theme = parse_terminal_config()
print(theme)
```

## Fallback Behavior

- If config file doesn't exist → return default theme
- If parsing fails → catch exception and return default theme
- Always log warnings when using defaults

## Example: Fully Implemented Ghostty Parser

See `backend/parsers/ghostty_parser.py` for a complete reference implementation.

## Questions?

Each stub parser file contains additional TODOs and hints. If implementing a parser, please:

1. Test with real config files
2. Handle parsing errors gracefully
3. Return default theme on any failure
4. Add clear print statements for debugging

## Dependencies

Add any new dependencies to `requirements.txt` with pinned versions:

```
pyyaml==6.0.1  # For Alacritty and Warp
biplist==1.0.3  # For macOS plist parsing (if needed)
```

---

**Happy coding! May your terminals be colorful and your parsers be robust.** 🎨✨
