"""Kearney Design System (KDS) registry and utilities."""

from .registry import (
    get_design,
    get_css,
    html_shell,
    pdf_theme,
    pptx_theme,
    kds_classes,
    enforce_kds_html,
)
from .tokens import (
    load_kearney_tokens,
    BrandTokensError,
    validate_tokens,
    get_token_version,
    get_chart_colors,
)

__all__ = [
    "get_design",
    "get_css",
    "html_shell",
    "pdf_theme",
    "pptx_theme",
    "kds_classes",
    "enforce_kds_html",
    "load_kearney_tokens",
    "BrandTokensError",
    "validate_tokens",
    "get_token_version",
    "get_chart_colors",
]
