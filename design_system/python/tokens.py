"""Kearney design system tokens for Python."""

import json
from pathlib import Path
from typing import Dict, Any

# Load tokens
_TOKENS_PATH = Path(__file__).parent.parent / "tokens.json"
_PALETTES_PATH = Path(__file__).parent.parent / "palettes.json"

with open(_TOKENS_PATH) as f:
    TOKENS: Dict[str, Any] = json.load(f)

with open(_PALETTES_PATH) as f:
    PALETTES: Dict[str, Any] = json.load(f)

# Core colors
CHARCOAL = "#1E1E1E"
SILVER = "#A5A5A5"
PURPLE = "#7823DC"
GREY200 = "#D2D2D2"
GREY500 = "#787878"
GREY700 = "#4B4B4B"
VIOLET1 = "#E6D2FA"
VIOLET2 = "#C8A5F0"
VIOLET3 = "#AF7DEB"
VIOLET4 = "#9150E1"

# Extended greys
WHITE = "#FFFFFF"
BLACK = "#000000"
GREY100 = "#F5F5F5"
GREY300 = "#BEBEBE"
GREY600 = "#5A5A5A"
GREY800 = "#2D2D2D"
GREY900 = "#1A1A1A"

# Theme colors
class LightTheme:
    """Light theme colors."""

    BACKGROUND = "#FFFFFF"
    SURFACE = "#F5F5F5"
    SURFACE_ELEVATED = "#FFFFFF"
    TEXT = "#1E1E1E"
    TEXT_MUTED = "#787878"
    TEXT_INVERSE = "#FFFFFF"
    BORDER = "#D2D2D2"
    EMPHASIS = "#7823DC"
    EMPHASIS_HOVER = "#9150E1"
    SUCCESS = "#2E7D32"
    SUCCESS_TINT = "#E8F5E9"
    WARNING = "#ED6C02"
    WARNING_TINT = "#FFF3E0"
    ERROR = "#D32F2F"
    ERROR_TINT = "#FFEBEE"
    SPOT_COLOR = "#7823DC"
    CHART_MUTED = "#A5A5A5"
    CHART_HIGHLIGHT = "#7823DC"


class DarkTheme:
    """Dark theme colors."""

    BACKGROUND = "#000000"
    SURFACE = "#1E1E1E"
    SURFACE_ELEVATED = "#2D2D2D"
    TEXT = "#FFFFFF"
    TEXT_MUTED = "#A5A5A5"
    TEXT_INVERSE = "#1E1E1E"
    BORDER = "#4B4B4B"
    EMPHASIS = "#AF7DEB"
    EMPHASIS_HOVER = "#C8A5F0"
    SUCCESS = "#66BB6A"
    SUCCESS_TINT = "#1B5E20"
    WARNING = "#FFA726"
    WARNING_TINT = "#E65100"
    ERROR = "#EF5350"
    ERROR_TINT = "#B71C1C"
    SPOT_COLOR = "#AF7DEB"
    CHART_MUTED = "#787878"
    CHART_HIGHLIGHT = "#C8A5F0"


# Typography
FONT_FAMILY = "Inter, Arial, sans-serif"
FONT_FAMILY_MONO = "'SF Mono', 'Roboto Mono', 'Courier New', monospace"

# Font sizes (in points for matplotlib)
FONT_SIZE_XS = 8
FONT_SIZE_SM = 10
FONT_SIZE_BASE = 12
FONT_SIZE_MD = 15
FONT_SIZE_LG = 19
FONT_SIZE_XL = 23
FONT_SIZE_2XL = 29
FONT_SIZE_3XL = 37

# Color palettes
SEQUENTIAL_PURPLE = PALETTES["sequential"]["purple"]["colors"]
SEQUENTIAL_NEUTRAL = PALETTES["sequential"]["neutral"]["colors"]
CATEGORICAL_PRIMARY = PALETTES["categorical"]["primary"]["colors"]
CATEGORICAL_EXTENDED = PALETTES["categorical"]["extended"]["colors"]

# Semantic colors
SUCCESS_COLOR = "#2E7D32"
WARNING_COLOR = "#ED6C02"
ERROR_COLOR = "#D32F2F"
INFO_COLOR = "#7823DC"

# Trend colors
POSITIVE_COLOR = "#2E7D32"
NEGATIVE_COLOR = "#D32F2F"
NEUTRAL_COLOR = "#787878"


def get_theme_colors(theme: str = "light") -> Dict[str, str]:
    """
    Get theme color dictionary.

    Args:
        theme: "light" or "dark"

    Returns:
        Dictionary of color names to hex values
    """
    theme_class = LightTheme if theme == "light" else DarkTheme

    return {
        "background": theme_class.BACKGROUND,
        "surface": theme_class.SURFACE,
        "surface_elevated": theme_class.SURFACE_ELEVATED,
        "text": theme_class.TEXT,
        "text_muted": theme_class.TEXT_MUTED,
        "text_inverse": theme_class.TEXT_INVERSE,
        "border": theme_class.BORDER,
        "emphasis": theme_class.EMPHASIS,
        "emphasis_hover": theme_class.EMPHASIS_HOVER,
        "success": theme_class.SUCCESS,
        "warning": theme_class.WARNING,
        "error": theme_class.ERROR,
        "spot_color": theme_class.SPOT_COLOR,
        "chart_muted": theme_class.CHART_MUTED,
        "chart_highlight": theme_class.CHART_HIGHLIGHT,
    }


def get_sequential_palette(name: str = "purple", n: int = None) -> list:
    """
    Get sequential color palette.

    Args:
        name: Palette name ("purple" or "neutral")
        n: Number of colors (None = all)

    Returns:
        List of hex colors
    """
    palette = PALETTES["sequential"][name]["colors"]
    if n is not None:
        return palette[:n]
    return palette


def get_categorical_palette(n: int = 6) -> list:
    """
    Get categorical color palette.

    Args:
        n: Number of colors needed

    Returns:
        List of hex colors
    """
    if n <= 6:
        return CATEGORICAL_PRIMARY[:n]
    return CATEGORICAL_EXTENDED[:n]
