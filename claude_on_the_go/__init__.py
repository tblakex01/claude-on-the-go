"""
claude-on-the-go: Access Claude Code CLI from your mobile device

A mobile-first web interface for Claude Code CLI that streams terminal I/O
over WebSocket. Works on any device with a browser - no apps, no cloud, no cost.
"""

__version__ = "1.0.0"
__author__ = "Matthew Jamison"
__license__ = "MIT"

from .cli import main

__all__ = ["main", "__version__"]
