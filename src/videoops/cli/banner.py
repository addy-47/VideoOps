"""Hollow box ASCII banner generator for VOPS CLI with terminal-theme adaptive ANSI colors."""

import os
import sys

HOLLOW_BANNER_ASCII = r"""
 ║     ║  ╔═════╗   ╔═════╗  ╔═════╗
  ║   ║   ║     ║   ║     ║  ║      
  ╚╗ ╔╝   ║     ║   ╠═════╝  ╚═════╗
   ║ ║    ║     ║   ║              ║
   ╚═╝    ╚═════╝   ╩        ╚═════╝
"""


def _supports_color() -> bool:
    """Check if terminal supports color and NO_COLOR environment variable is not set."""
    if os.getenv("NO_COLOR"):
        return False
    return sys.stdout.isatty() or bool(os.getenv("CLICOLOR_FORCE"))


def print_banner(version: str = "0.2.3") -> None:
    """Print the theme-adaptive hollow box ASCII banner for VOPS CLI.
    
    Uses standard terminal ANSI 16-color codes (Red, Bright Red, Dim Red)
    so the banner automatically adapts to the user's active terminal theme
    (e.g., Catppuccin, Gruvbox, Tokyo Night, Dracula, Solarized).
    """
    banner_lines = HOLLOW_BANNER_ASCII.strip("\n").split("\n")
    num_lines = len(banner_lines)
    use_color = _supports_color()

    # Terminal ANSI Codes (theme-adaptive)
    BOLD = "\033[1m" if use_color else ""
    RESET = "\033[0m" if use_color else ""
    WHITE = "\033[97m" if use_color else ""
    GRAY = "\033[90m" if use_color else ""
    
    # Vertical line color mapping to standard terminal palette:
    # Top/Bottom lines -> Standard Red (\033[31m - adapts to theme dark red)
    # Middle lines -> Bright Red (\033[91m - adapts to theme bright red)
    ANSI_COLORS = [
        "\033[31m",   # Top line: Standard Red
        "\033[91m",   # Mid-high: Bright Red
        "\033[1;91m", # Center: Bold Bright Red
        "\033[91m",   # Mid-low: Bright Red
        "\033[31m",   # Bottom line: Standard Red
    ]

    print()
    for line_idx, line in enumerate(banner_lines):
        color_code = ANSI_COLORS[line_idx % len(ANSI_COLORS)] if use_color else ""
        print(f"{color_code}{line}{RESET}")

    accent = ANSI_COLORS[2] if use_color else ""
    print(
        f"  {BOLD}{WHITE}VIDEOOPS{RESET} {accent}v{version}{RESET}  "
        f"{GRAY}— Code-to-Canvas AI Short Video Production Engine{RESET}"
    )
    print(f"  {GRAY}{'─' * 60}{RESET}\n")
