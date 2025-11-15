"""Central design registry with Kearney Design System tokens and helpers."""

from typing import Dict, Any, Optional
import re


# ---- Kearney baseline tokens ----
def _kearney_tokens() -> Dict[str, Any]:
    """
    Return Kearney Design System (KDS) baseline tokens.

    These tokens define the default Kearney branding:
    - Colors: Professional blue/slate palette with high contrast
    - Fonts: Inter for consistency and accessibility
    - Margins: Standard spacing for PDF/PPTX (72pt = 1 inch)
    - Classes: Reusable CSS classes for HTML deliverables
    - CSS: Embedded stylesheet for consistent rendering
    """
    return {
        "colors": {
            "fg": "#0F172A",  # Slate 900 - primary text
            "muted": "#475569",  # Slate 600 - secondary text
            "bg": "#FFFFFF",  # White background
            "card": "#F8FAFC",  # Slate 50 - card backgrounds
            "accent": "#0EA5E9",  # Sky 500 - Kearney blue accent
        },
        "fonts": {
            "headline": "Inter",
            "body": "Inter",
        },
        "margins": {
            "x": 72,  # 1 inch horizontal margin (PDF)
            "y": 72,  # 1 inch vertical margin (PDF)
        },
        "classes": {
            "card": "kds-card",
            "btn": "kds-btn",
            "badge": "kds-badge",
            "row": "kds-row",
            "input": "kds-input",
            "section": "kds-section",
            "h1": "kds-h1",
            "h2": "kds-h2",
        },
        "css": (
            ".kds{font-family:Inter,system-ui,Arial,sans-serif;color:#0F172A;background:#fff;margin:24px}"
            ".kds .kds-card{background:#F8FAFC;border-radius:14px;padding:16px;margin:12px 0;border:1px solid #E2E8F0}"
            ".kds .kds-btn{padding:8px 12px;border-radius:10px;border:1px solid #E2E8F0;background:#fff;cursor:pointer}"
            ".kds .kds-badge{display:inline-block;background:#0EA5E9;color:#fff;padding:2px 8px;border-radius:999px;font-size:12px}"
            ".kds .kds-row{display:flex;gap:12px;flex-wrap:wrap}"
            ".kds .kds-input{padding:8px 10px;border:1px solid #CBD5E1;border-radius:10px;width:100%}"
            ".kds .kds-section{margin:16px 0}"
            ".kds .kds-h1{font-size:28px;margin:0 0 8px}"
            ".kds .kds-h2{font-size:18px;margin:16px 0 8px}"
        ),
    }


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
        d = base.copy()
        ov = overrides or {}

        # Merge colors (client colors take precedence)
        if "colors" in ov:
            d["colors"] = {**d["colors"], **ov["colors"]}

        # Merge fonts
        if "fonts" in ov:
            d["fonts"] = {**d["fonts"], **ov["fonts"]}

        # Add client-specific metadata
        d["client"] = system
        d["logo_url"] = ov.get("logo_url")
        d["wcag_target"] = ov.get("wcag_target", "AA")

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
    return (design or _kearney_tokens())["css"]


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
    css = d["css"]

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
    return design or _kearney_tokens()


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
