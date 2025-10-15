"""Matplotlib theme for Kearney brand."""

import matplotlib.pyplot as plt
import matplotlib as mpl
from matplotlib import rcParams
from .tokens import (
    FONT_FAMILY,
    FONT_SIZE_BASE,
    FONT_SIZE_SM,
    FONT_SIZE_LG,
    get_theme_colors,
    CATEGORICAL_PRIMARY,
)


def apply_kearney_mpl(theme: str = "light", dpi: int = 150) -> None:
    """
    Apply Kearney brand theme to matplotlib.

    Features:
    - No gridlines (brand requirement)
    - Inter/Arial font stack
    - Kearney color palette
    - Clean, minimal axes
    - Label-first emphasis

    Args:
        theme: "light" or "dark"
        dpi: Figure DPI for high-quality output
    """
    colors = get_theme_colors(theme)

    # Reset to defaults first
    mpl.rcdefaults()

    # Figure and DPI
    rcParams["figure.dpi"] = dpi
    rcParams["figure.facecolor"] = colors["background"]
    rcParams["figure.edgecolor"] = colors["background"]
    rcParams["savefig.dpi"] = dpi
    rcParams["savefig.facecolor"] = colors["background"]
    rcParams["savefig.edgecolor"] = colors["background"]

    # Font family - Inter with Arial fallback
    rcParams["font.family"] = "sans-serif"
    rcParams["font.sans-serif"] = ["Inter", "Arial", "Helvetica", "DejaVu Sans"]
    rcParams["font.size"] = FONT_SIZE_BASE
    rcParams["axes.labelsize"] = FONT_SIZE_BASE
    rcParams["axes.titlesize"] = FONT_SIZE_LG
    rcParams["xtick.labelsize"] = FONT_SIZE_SM
    rcParams["ytick.labelsize"] = FONT_SIZE_SM
    rcParams["legend.fontsize"] = FONT_SIZE_SM
    rcParams["figure.titlesize"] = FONT_SIZE_LG

    # Colors
    rcParams["axes.facecolor"] = colors["background"]
    rcParams["axes.edgecolor"] = colors["border"]
    rcParams["axes.labelcolor"] = colors["text"]
    rcParams["text.color"] = colors["text"]
    rcParams["xtick.color"] = colors["text_muted"]
    rcParams["ytick.color"] = colors["text_muted"]

    # NO GRIDLINES - Critical brand requirement
    rcParams["axes.grid"] = False
    rcParams["axes.grid.which"] = "neither"
    rcParams["grid.alpha"] = 0  # Ensure grids never show
    rcParams["grid.linewidth"] = 0

    # Axes spines - minimal, clean
    rcParams["axes.linewidth"] = 1.0
    rcParams["axes.spines.top"] = False
    rcParams["axes.spines.right"] = False
    rcParams["axes.spines.left"] = True
    rcParams["axes.spines.bottom"] = True

    # Ticks
    rcParams["xtick.major.size"] = 4
    rcParams["ytick.major.size"] = 4
    rcParams["xtick.minor.size"] = 0  # No minor ticks
    rcParams["ytick.minor.size"] = 0
    rcParams["xtick.major.width"] = 1.0
    rcParams["ytick.major.width"] = 1.0
    rcParams["xtick.direction"] = "out"
    rcParams["ytick.direction"] = "out"

    # Color cycle - Kearney categorical palette
    rcParams["axes.prop_cycle"] = mpl.cycler(color=CATEGORICAL_PRIMARY)

    # Legend
    rcParams["legend.frameon"] = False
    rcParams["legend.loc"] = "best"
    rcParams["legend.fancybox"] = False

    # Lines and markers
    rcParams["lines.linewidth"] = 2.0
    rcParams["lines.markersize"] = 6
    rcParams["lines.markeredgewidth"] = 0

    # Patch (bars, etc.)
    rcParams["patch.linewidth"] = 0
    rcParams["patch.edgecolor"] = colors["background"]

    print(f"Kearney matplotlib theme applied ({theme} mode)")
    print("Key features:")
    print("  - No gridlines")
    print("  - Inter/Arial font stack")
    print("  - Minimal axes (top/right spines off)")
    print("  - Kearney color palette")


def remove_chart_junk(ax=None) -> None:
    """
    Remove chart junk from axis.

    Ensures:
    - No gridlines
    - Top and right spines removed
    - Clean, minimal appearance

    Args:
        ax: Matplotlib axis (None = current axis)
    """
    if ax is None:
        ax = plt.gca()

    # NO GRIDLINES
    ax.grid(False)
    ax.set_axisbelow(False)

    # Remove top and right spines
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    # Ensure left and bottom spines are thin
    ax.spines["left"].set_linewidth(1.0)
    ax.spines["bottom"].set_linewidth(1.0)


def add_spot_color_highlight(ax, x_value, color=None, label=None, theme="light") -> None:
    """
    Add spot color highlight to emphasize a specific data point.

    Args:
        ax: Matplotlib axis
        x_value: X coordinate to highlight
        color: Highlight color (None = use theme spot color)
        label: Optional label for the highlight
        theme: "light" or "dark"
    """
    if color is None:
        colors = get_theme_colors(theme)
        color = colors["spot_color"]

    # Add vertical line at x_value
    ax.axvline(x=x_value, color=color, linewidth=2, linestyle="--", alpha=0.7, label=label)


def add_mark_label(ax, x, y, text, theme="light", **kwargs) -> None:
    """
    Add label directly on data mark (label-first approach).

    Args:
        ax: Matplotlib axis
        x: X coordinate
        y: Y coordinate
        text: Label text
        theme: "light" or "dark"
        **kwargs: Additional text properties
    """
    colors = get_theme_colors(theme)

    default_props = {
        "fontsize": FONT_SIZE_SM,
        "color": colors["text"],
        "ha": "center",
        "va": "bottom",
        "fontweight": "medium",
    }
    default_props.update(kwargs)

    ax.text(x, y, text, **default_props)
