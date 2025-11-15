"""Central design registry with Kearney Design System tokens and helpers."""

from typing import Dict, Any, Optional
import re
import json
from .tokens import load_kearney_tokens, BrandTokensError


def json_deepcopy(obj: Any) -> Any:
    """Deep copy an object via JSON serialization."""
    return json.loads(json.dumps(obj))


# ---- Kearney baseline tokens ----
def _kearney_tokens() -> Dict[str, Any]:
    """
    Return Kearney Design System (KDS) baseline tokens.

    Loads tokens from canonical kearney_brand.yml file.
    This is the ONLY source of truth for Kearney design tokens.

    Returns:
        Dictionary of Kearney brand tokens

    Raises:
        BrandTokensError: If tokens cannot be loaded
    """
    return load_kearney_tokens()


def get_design(system: str, overrides: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Get design tokens for the specified system.

    Args:
        system: Design system identifier ("kearney" or "client:<slug>")
        overrides: Optional client-specific overrides (colors, fonts, logo, etc.)

    Returns:
        Dictionary of design tokens

    Raises:
        ValueError: If system is not recognized

    Examples:
        >>> get_design("kearney")
        {'colors': {...}, 'fonts': {...}, ...}

        >>> get_design("client:acme", {"colors": {"accent": "#FF6600"}})
        {'colors': {'accent': '#FF6600', ...}, 'client': 'client:acme', ...}
    """
    base = _kearney_tokens()

    if system == "kearney":
        return base

    if system.startswith("client:"):
        # Start with Kearney base and merge client overrides
        d = json_deepcopy(base)
        ov = overrides or {}

        # Merge colors (client colors take precedence)
        if "colors" in ov:
            d["colors"] = {**d["colors"], **ov["colors"]}

        # Merge fonts
        if "fonts" in ov:
            d["fonts"] = {**d["fonts"], **ov["fonts"]}

        # Merge classes (rare, but allowed)
        if "classes" in ov:
            d["classes"] = {**d["classes"], **ov["classes"]}

        # Add client-specific metadata
        d["client"] = system
        d["logo_url"] = ov.get("logo_url")
        d["wcag_target"] = ov.get("wcag_target", base.get("meta", {}).get("wcag_target", "AA"))

        return d

    raise ValueError(f"Unknown design system: {system}")


def get_css(design: Optional[Dict[str, Any]] = None) -> str:
    """
    Get CSS stylesheet for the design.

    Args:
        design: Design tokens (defaults to Kearney baseline)

    Returns:
        CSS string for embedding in HTML
    """
    d = design or _kearney_tokens()
    # Support both "css_bundle" (new) and "css" (legacy) keys
    return d.get("css_bundle") or d.get("css", "")


def kds_classes(design: Optional[Dict[str, Any]] = None) -> Dict[str, str]:
    """
    Get KDS CSS class names.

    Args:
        design: Design tokens (defaults to Kearney baseline)

    Returns:
        Dictionary mapping semantic names to CSS classes

    Examples:
        >>> classes = kds_classes()
        >>> classes["card"]
        'kds-card'
    """
    return (design or _kearney_tokens())["classes"]


def html_shell(title: str, body_html: str, design: Optional[Dict[str, Any]] = None) -> str:
    """
    Wrap HTML body in a complete HTML document with KDS styling.

    Args:
        title: Document title
        body_html: Inner HTML content
        design: Design tokens (defaults to Kearney baseline)

    Returns:
        Complete HTML document string

    Examples:
        >>> html = html_shell("Report", "<div class='kds-card'>Hello</div>")
        >>> "<style>" in html
        True
    """
    d = design or _kearney_tokens()
    css = get_css(d)

    return (
        f"<!doctype html>"
        f"<html>"
        f"<head>"
        f"<meta charset='utf-8'>"
        f"<meta name='viewport' content='width=device-width,initial-scale=1'>"
        f"<title>{title}</title>"
        f"<style>{css}</style>"
        f"</head>"
        f"<body class='kds'>"
        f"{body_html}"
        f"</body>"
        f"</html>"
    )


def pdf_theme(design: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Get PDF theme settings (colors, fonts, margins).

    Args:
        design: Design tokens (defaults to Kearney baseline)

    Returns:
        Dictionary with PDF theme settings
    """
    d = design or _kearney_tokens()

    # Build standardized PDF theme structure
    return {
        "colors": d["colors"],
        "fonts": d["fonts"],
        "margins": {
            "x": d.get("spacing", {}).get("page_margin_x", 72),
            "y": d.get("spacing", {}).get("page_margin_y", 72),
        },
    }


def pptx_theme(prs: Any, design: Optional[Dict[str, Any]] = None) -> None:
    """
    Apply design theme to a PowerPoint presentation object.

    This is a minimal hook for PPTX theming. Projects can extend this
    to customize master slides, layouts, and color schemes.

    Args:
        prs: python-pptx Presentation object
        design: Design tokens (defaults to Kearney baseline)
    """
    # Hook for future PPTX theming
    # Projects can extend this to set master slide colors, fonts, etc.
    _ = design or _kearney_tokens()
    return


# ---- HTML guardrails ----

# Regex patterns for detecting inline styles and colors
_INLINE_HEX = re.compile(r"#[0-9a-fA-F]{3,6}")
_INLINE_STYLE = re.compile(r'style\s*=\s*["\']', re.IGNORECASE)


def enforce_kds_html(html: str) -> str:
    """
    Enforce KDS compliance by rejecting inline styles and hex colors.

    This guardrail prevents developers from bypassing the design system
    by using inline CSS or hardcoded colors.

    Args:
        html: HTML string to validate

    Returns:
        Original HTML if compliant

    Raises:
        ValueError: If inline styles or hex colors are detected

    Examples:
        >>> enforce_kds_html("<div class='kds-card'>OK</div>")
        "<div class='kds-card'>OK</div>"

        >>> enforce_kds_html('<div style="color:red">Bad</div>')
        Traceback (most recent call last):
        ...
        ValueError: Inline style attribute detected; use KDS classes.
    """
    if _INLINE_STYLE.search(html):
        raise ValueError(
            "Inline style attribute detected; use KDS classes instead.\n"
            "Use kds_classes() to get semantic CSS classes: "
            "kds-card, kds-btn, kds-badge, etc."
        )

    if _INLINE_HEX.search(html):
        raise ValueError(
            "Inline hex color detected; use KDS tokens instead.\n"
            "Use get_design() to access color tokens: "
            "colors['accent'], colors['fg'], etc."
        )

    return html
