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

__all__ = [
    "get_design",
    "get_css",
    "html_shell",
    "pdf_theme",
    "pptx_theme",
    "kds_classes",
    "enforce_kds_html",
]
