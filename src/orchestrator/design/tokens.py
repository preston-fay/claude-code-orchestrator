"""Kearney Design System tokens loader - single source of truth."""

from __future__ import annotations
import os
import json
import yaml
from pathlib import Path
from typing import Dict, Any


class BrandTokensError(RuntimeError):
    """Raised when brand tokens are missing or invalid."""
    pass


# Required top-level keys in tokens
_REQUIRED_KEYS = ["colors", "fonts", "spacing", "classes", "css_bundle"]


def load_kearney_tokens() -> Dict[str, Any]:
    """
    Load Kearney brand tokens from canonical YAML file.

    This is the ONLY way to access Kearney design tokens. All outputs
    (HTML/PDF/PPTX) must use these tokens via orchestrator helpers.

    Priority:
    1. KDS_TOKENS_JSON environment variable (emergency override)
    2. Packaged kearney_brand.yml (normal operation)

    Returns:
        Dictionary of Kearney brand tokens

    Raises:
        BrandTokensError: If tokens are missing or invalid

    Examples:
        >>> tokens = load_kearney_tokens()
        >>> tokens["colors"]["primary"]
        '#7823DC'
        >>> tokens["fonts"]["headline"]
        'Inter'
    """
    # Option 1: Emergency override via environment variable
    env_json = os.environ.get("KDS_TOKENS_JSON")
    if env_json:
        try:
            tokens = json.loads(env_json)
        except json.JSONDecodeError as e:
            raise BrandTokensError(
                f"Failed to parse KDS_TOKENS_JSON environment variable: {e}"
            )
    else:
        # Option 2: Load from packaged YAML file (normal path)
        try:
            # Try importlib.resources first (Python 3.9+)
            try:
                from importlib.resources import files
                yaml_path = files("src.orchestrator.design").joinpath("kearney_brand.yml")
                with open(yaml_path, "r", encoding="utf-8") as f:
                    tokens = yaml.safe_load(f)
            except (ImportError, TypeError, AttributeError):
                # Fallback: relative path from this file
                yaml_path = Path(__file__).parent / "kearney_brand.yml"
                if not yaml_path.exists():
                    raise FileNotFoundError(f"Kearney brand tokens not found: {yaml_path}")
                with open(yaml_path, "r", encoding="utf-8") as f:
                    tokens = yaml.safe_load(f)
        except FileNotFoundError as e:
            raise BrandTokensError(
                f"Kearney brand tokens file not found. "
                f"Expected: src/orchestrator/design/kearney_brand.yml. Error: {e}"
            )
        except yaml.YAMLError as e:
            raise BrandTokensError(
                f"Failed to parse Kearney brand tokens YAML: {e}"
            )

    # Validate required keys
    for key in _REQUIRED_KEYS:
        if key not in tokens:
            raise BrandTokensError(
                f"Missing required key '{key}' in Kearney brand tokens. "
                f"Required keys: {', '.join(_REQUIRED_KEYS)}"
            )

    # Validate primary color exists
    if "primary" not in tokens.get("colors", {}):
        raise BrandTokensError(
            "Missing 'colors.primary' in Kearney brand tokens. "
            "Primary brand color is required."
        )

    # Sanity check: primary color should appear in CSS bundle
    # This catches divergence between tokens and embedded CSS
    primary_color = tokens["colors"]["primary"].lower()
    css_bundle = tokens["css_bundle"].lower()

    if primary_color not in css_bundle:
        # Not fatal, but log warning
        import logging
        logger = logging.getLogger(__name__)
        logger.warning(
            f"Primary color {primary_color} not found in CSS bundle. "
            "Tokens and CSS may be out of sync."
        )

    return tokens


def validate_tokens(tokens: Dict[str, Any]) -> None:
    """
    Validate token structure and values.

    Args:
        tokens: Token dictionary to validate

    Raises:
        BrandTokensError: If validation fails
    """
    # Check required keys
    for key in _REQUIRED_KEYS:
        if key not in tokens:
            raise BrandTokensError(f"Missing required key: {key}")

    # Validate color format (should start with #)
    for color_name, color_value in tokens.get("colors", {}).items():
        if not isinstance(color_value, str) or not color_value.startswith("#"):
            raise BrandTokensError(
                f"Invalid color format for '{color_name}': {color_value}. "
                "Colors must be hex strings starting with #"
            )

    # Validate fonts exist
    if "headline" not in tokens.get("fonts", {}):
        raise BrandTokensError("Missing 'fonts.headline' in tokens")

    if "body" not in tokens.get("fonts", {}):
        raise BrandTokensError("Missing 'fonts.body' in tokens")

    # Validate CSS bundle is non-empty
    if not tokens.get("css_bundle") or not tokens["css_bundle"].strip():
        raise BrandTokensError("CSS bundle is empty or missing")


def get_token_version() -> str:
    """
    Get the current KDS token version.

    Returns:
        Version string from tokens metadata

    Examples:
        >>> get_token_version()
        '1.0.0'
    """
    tokens = load_kearney_tokens()
    return tokens.get("meta", {}).get("version", "unknown")


def get_chart_colors() -> list[str]:
    """
    Get the ordered chart color palette.

    Returns:
        List of hex colors for data visualization (in order)

    Examples:
        >>> colors = get_chart_colors()
        >>> colors[0]
        '#D2D2D2'
    """
    tokens = load_kearney_tokens()

    # Try chart_theme first (structured)
    if "chart_theme" in tokens and "colors" in tokens["chart_theme"]:
        return tokens["chart_theme"]["colors"]

    # Fallback: extract chart_1, chart_2, etc. from colors
    chart_colors = []
    i = 1
    while f"chart_{i}" in tokens.get("colors", {}):
        chart_colors.append(tokens["colors"][f"chart_{i}"])
        i += 1

    if not chart_colors:
        raise BrandTokensError("No chart colors defined in tokens")

    return chart_colors
