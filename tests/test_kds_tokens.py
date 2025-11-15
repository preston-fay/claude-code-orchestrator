"""Tests for KDS token loading and single source of truth."""

import pytest
import json
import os
from src.orchestrator.design import (
    load_kearney_tokens,
    BrandTokensError,
    validate_tokens,
    get_token_version,
    get_chart_colors,
    kds_classes,
    html_shell,
    enforce_kds_html,
    pdf_theme,
)


class TestTokenLoading:
    """Tests for token loading from YAML."""

    def test_tokens_load_successfully(self):
        """Test that tokens load without errors."""
        tokens = load_kearney_tokens()
        assert isinstance(tokens, dict)
        assert len(tokens) > 0

    def test_tokens_have_required_fields(self):
        """Test that all required keys are present."""
        tokens = load_kearney_tokens()

        # Required top-level keys
        required_keys = ["colors", "fonts", "spacing", "classes", "css_bundle"]
        for key in required_keys:
            assert key in tokens, f"Missing required key: {key}"

    def test_colors_are_valid(self):
        """Test that all colors are valid hex strings."""
        tokens = load_kearney_tokens()
        colors = tokens["colors"]

        # All colors should start with #
        for color_name, color_value in colors.items():
            assert isinstance(color_value, str), f"Color {color_name} is not a string"
            assert color_value.startswith("#"), f"Color {color_name} does not start with #"
            assert len(color_value) in [4, 7], f"Color {color_name} has invalid length"

    def test_primary_color_is_kearney_purple(self):
        """Test that primary color is Kearney purple (#7823DC)."""
        tokens = load_kearney_tokens()
        assert tokens["colors"]["primary"] == "#7823DC"

    def test_fonts_exist(self):
        """Test that required fonts are defined."""
        tokens = load_kearney_tokens()
        fonts = tokens["fonts"]

        assert "headline" in fonts
        assert "body" in fonts
        assert isinstance(fonts["headline"], str)
        assert isinstance(fonts["body"], str)

    def test_spacing_defined(self):
        """Test that spacing values are defined."""
        tokens = load_kearney_tokens()
        spacing = tokens["spacing"]

        assert "page_margin_x" in spacing
        assert "page_margin_y" in spacing
        assert isinstance(spacing["page_margin_x"], (int, float))
        assert isinstance(spacing["page_margin_y"], (int, float))

    def test_classes_defined(self):
        """Test that CSS classes are defined."""
        tokens = load_kearney_tokens()
        classes = tokens["classes"]

        # Check for core utility classes
        expected_classes = ["card", "btn", "badge", "row", "h1", "h2"]
        for cls in expected_classes:
            assert cls in classes, f"Missing class: {cls}"

    def test_css_bundle_not_empty(self):
        """Test that CSS bundle is non-empty."""
        tokens = load_kearney_tokens()
        css = tokens["css_bundle"]

        assert isinstance(css, str)
        assert len(css) > 0
        assert ".kds" in css


class TestTokenValidation:
    """Tests for token validation logic."""

    def test_validate_tokens_accepts_valid(self):
        """Test that validation accepts valid tokens."""
        tokens = load_kearney_tokens()
        # Should not raise
        validate_tokens(tokens)

    def test_validate_rejects_missing_colors(self):
        """Test that validation rejects missing colors key."""
        tokens = {"fonts": {}, "spacing": {}, "classes": {}, "css_bundle": ""}
        with pytest.raises(BrandTokensError):
            validate_tokens(tokens)

    def test_validate_rejects_invalid_color_format(self):
        """Test that validation rejects non-hex colors."""
        tokens = {
            "colors": {"primary": "not-a-hex"},
            "fonts": {"headline": "Inter", "body": "Inter"},
            "spacing": {},
            "classes": {},
            "css_bundle": "x",
        }
        with pytest.raises(BrandTokensError):
            validate_tokens(tokens)

    def test_validate_rejects_missing_headline_font(self):
        """Test that validation requires headline font."""
        tokens = {
            "colors": {"primary": "#000"},
            "fonts": {"body": "Inter"},
            "spacing": {},
            "classes": {},
            "css_bundle": "x",
        }
        with pytest.raises(BrandTokensError):
            validate_tokens(tokens)

    def test_validate_rejects_empty_css_bundle(self):
        """Test that validation requires non-empty CSS bundle."""
        tokens = {
            "colors": {"primary": "#000"},
            "fonts": {"headline": "Inter", "body": "Inter"},
            "spacing": {},
            "classes": {},
            "css_bundle": "",
        }
        with pytest.raises(BrandTokensError):
            validate_tokens(tokens)


class TestTokenVersion:
    """Tests for token version management."""

    def test_get_token_version(self):
        """Test that version can be retrieved."""
        version = get_token_version()
        assert isinstance(version, str)
        assert len(version) > 0

    def test_version_in_tokens(self):
        """Test that version is stored in tokens metadata."""
        tokens = load_kearney_tokens()
        assert "meta" in tokens
        assert "version" in tokens["meta"]


class TestChartColors:
    """Tests for chart color palette."""

    def test_get_chart_colors(self):
        """Test that chart colors can be retrieved."""
        colors = get_chart_colors()
        assert isinstance(colors, list)
        assert len(colors) > 0

    def test_chart_colors_are_hex(self):
        """Test that all chart colors are hex strings."""
        colors = get_chart_colors()
        for color in colors:
            assert isinstance(color, str)
            assert color.startswith("#")

    def test_chart_colors_ordered(self):
        """Test that chart colors are in correct order."""
        colors = get_chart_colors()
        # First color should be light gray #D2D2D2
        assert colors[0] == "#D2D2D2"


class TestRegistryIntegration:
    """Tests for registry integration with tokens."""

    def test_html_shell_and_guardrails(self):
        """Test HTML shell generation and guardrails."""
        tokens = load_kearney_tokens()
        html = html_shell("Test Title", "<div class='kds-card'>Content</div>", tokens)

        assert "<!doctype html>" in html.lower()
        assert "<title>Test Title</title>" in html
        assert "<style>" in html
        assert "kds-card" in html

        # Test guardrails
        valid_html = "<div class='kds-card'>x</div>"
        assert enforce_kds_html(valid_html) == valid_html

        with pytest.raises(ValueError):
            enforce_kds_html('<div style="color:red">x</div>')

        with pytest.raises(ValueError):
            enforce_kds_html('<span>#ff00aa</span>')

    def test_pdf_theme_structure(self):
        """Test PDF theme has correct structure."""
        theme = pdf_theme()

        assert "colors" in theme
        assert "fonts" in theme
        assert "margins" in theme
        assert "x" in theme["margins"]
        assert "y" in theme["margins"]

    def test_kds_classes_returns_dict(self):
        """Test that kds_classes returns class mappings."""
        classes = kds_classes()

        assert isinstance(classes, dict)
        assert "card" in classes
        assert "kds-card" in classes["card"]


class TestEnvironmentOverride:
    """Tests for environment variable override."""

    def test_env_override_with_json(self, monkeypatch):
        """Test that KDS_TOKENS_JSON environment variable works."""
        # Create minimal valid tokens
        override_tokens = {
            "meta": {"name": "Test", "version": "0.0.1"},
            "colors": {"primary": "#FF0000", "fg": "#000", "bg": "#FFF"},
            "fonts": {"headline": "Arial", "body": "Arial"},
            "spacing": {"page_margin_x": 50, "page_margin_y": 50},
            "classes": {"card": "test-card"},
            "css_bundle": ".test{}",
        }

        monkeypatch.setenv("KDS_TOKENS_JSON", json.dumps(override_tokens))

        tokens = load_kearney_tokens()

        # Should use override
        assert tokens["colors"]["primary"] == "#FF0000"
        assert tokens["fonts"]["headline"] == "Arial"

    def test_env_override_invalid_json_raises(self, monkeypatch):
        """Test that invalid JSON raises BrandTokensError."""
        monkeypatch.setenv("KDS_TOKENS_JSON", "not valid json {")

        with pytest.raises(BrandTokensError) as exc_info:
            load_kearney_tokens()

        assert "parse KDS_TOKENS_JSON" in str(exc_info.value)


class TestBackwardCompatibility:
    """Tests for backward compatibility with old token structure."""

    def test_get_css_supports_both_keys(self):
        """Test that get_css supports both 'css_bundle' and 'css' keys."""
        from src.orchestrator.design.registry import get_css

        # Test with css_bundle (new)
        design_new = {"css_bundle": ".new{}", "css": ".old{}"}
        assert get_css(design_new) == ".new{}"

        # Test with only css (legacy)
        design_legacy = {"css": ".legacy{}"}
        assert get_css(design_legacy) == ".legacy{}"

    def test_pdf_theme_handles_spacing(self):
        """Test that pdf_theme correctly extracts margins from spacing."""
        tokens = load_kearney_tokens()
        theme = pdf_theme(tokens)

        # Should convert spacing.page_margin_x to margins.x
        assert theme["margins"]["x"] == tokens["spacing"]["page_margin_x"]
        assert theme["margins"]["y"] == tokens["spacing"]["page_margin_y"]


class TestErrorCases:
    """Tests for error handling."""

    def test_load_handles_missing_primary_color(self, monkeypatch):
        """Test that missing primary color is caught."""
        override_tokens = {
            "colors": {},  # Missing primary
            "fonts": {"headline": "A", "body": "B"},
            "spacing": {},
            "classes": {},
            "css_bundle": "x",
        }

        monkeypatch.setenv("KDS_TOKENS_JSON", json.dumps(override_tokens))

        with pytest.raises(BrandTokensError) as exc_info:
            load_kearney_tokens()

        assert "primary" in str(exc_info.value).lower()

    def test_load_handles_missing_required_keys(self, monkeypatch):
        """Test that missing required keys are caught."""
        incomplete_tokens = {
            "colors": {"primary": "#000"},
            # Missing fonts, spacing, classes, css_bundle
        }

        monkeypatch.setenv("KDS_TOKENS_JSON", json.dumps(incomplete_tokens))

        with pytest.raises(BrandTokensError) as exc_info:
            load_kearney_tokens()

        assert "Missing required key" in str(exc_info.value)
