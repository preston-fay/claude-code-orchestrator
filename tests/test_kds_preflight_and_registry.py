"""Tests for KDS preflight gate and design registry."""

import pytest
from src.orchestrator.preflight.design_gate import ensure_design_selection, DesignSelection
from src.orchestrator.design import (
    get_design,
    get_css,
    html_shell,
    pdf_theme,
    pptx_theme,
    kds_classes,
    enforce_kds_html,
)


class TestDesignPreflight:
    """Tests for design system preflight gate."""

    def test_kearney_from_config(self):
        """Test Kearney selection from config."""
        config = {"design_system": "kearney"}
        result = ensure_design_selection(config, env={})

        assert isinstance(result, DesignSelection)
        assert result.system == "kearney"
        assert result.overrides is None

    def test_kearney_from_env(self):
        """Test Kearney selection from environment."""
        config = {}
        env = {"DESIGN_SYSTEM": "kearney"}
        result = ensure_design_selection(config, env=env)

        assert result.system == "kearney"
        assert result.overrides is None

    def test_client_system_from_config(self):
        """Test client system selection from config."""
        config = {
            "design_system": "client:acme",
            "design_overrides": {
                "client_name": "ACME Corp",
                "colors": {"accent": "#FF6600"},
            },
        }
        result = ensure_design_selection(config, env={})

        assert result.system == "client:acme"
        assert result.overrides is not None
        assert result.overrides["client_name"] == "ACME Corp"
        assert result.overrides["colors"]["accent"] == "#FF6600"

    def test_client_system_from_env(self):
        """Test client system selection from environment."""
        config = {"design_overrides": {"logo_url": "https://example.com/logo.png"}}
        env = {"DESIGN_SYSTEM": "client:xyz"}
        result = ensure_design_selection(config, env=env)

        assert result.system == "client:xyz"
        assert result.overrides["logo_url"] == "https://example.com/logo.png"

    def test_config_takes_precedence_over_env(self):
        """Test that config takes precedence over env."""
        config = {"design_system": "kearney"}
        env = {"DESIGN_SYSTEM": "client:acme"}
        result = ensure_design_selection(config, env=env)

        # Config wins
        assert result.system == "kearney"

    def test_missing_design_system_raises(self):
        """Test that missing design system raises RuntimeError."""
        config = {}
        env = {}

        with pytest.raises(RuntimeError) as exc_info:
            ensure_design_selection(config, env=env)

        assert "Design system selection is required" in str(exc_info.value)

    def test_invalid_design_system_raises(self):
        """Test that invalid design system raises RuntimeError."""
        config = {"design_system": "invalid"}
        env = {}

        with pytest.raises(RuntimeError) as exc_info:
            ensure_design_selection(config, env=env)

        assert "Invalid 'design_system' value" in str(exc_info.value)


class TestDesignRegistry:
    """Tests for design registry and KDS tokens."""

    def test_kearney_tokens(self):
        """Test Kearney baseline tokens."""
        design = get_design("kearney")

        assert "colors" in design
        assert "fonts" in design
        assert "spacing" in design  # New: spacing instead of margins
        assert "classes" in design
        assert "css_bundle" in design  # New: css_bundle instead of css

        # Verify color palette (official Kearney colors)
        assert design["colors"]["fg"] == "#1E1E1E"  # Official Kearney dark gray
        assert design["colors"]["primary"] == "#7823DC"  # Official Kearney purple
        assert design["colors"]["accent"] == "#7823DC"  # Same as primary
        assert design["colors"]["bg"] == "#FFFFFF"

        # Verify fonts
        assert design["fonts"]["headline"] == "Inter"
        assert design["fonts"]["body"] == "Inter"

        # Verify spacing (replaces margins)
        assert design["spacing"]["page_margin_x"] == 72
        assert design["spacing"]["page_margin_y"] == 72

    def test_client_override_colors(self):
        """Test client color overrides."""
        design = get_design(
            "client:acme",
            overrides={"colors": {"accent": "#FF6600", "primary": "#003366"}},
        )

        # Client colors should override
        assert design["colors"]["accent"] == "#FF6600"
        assert design["colors"]["primary"] == "#003366"

        # Base colors should remain (official Kearney colors)
        assert design["colors"]["fg"] == "#1E1E1E"  # Official Kearney dark gray
        assert design["colors"]["bg"] == "#FFFFFF"

    def test_client_override_fonts(self):
        """Test client font overrides."""
        design = get_design(
            "client:acme",
            overrides={"fonts": {"headline": "Roboto"}},
        )

        # Client font should override
        assert design["fonts"]["headline"] == "Roboto"

        # Base font should remain
        assert design["fonts"]["body"] == "Inter"

    def test_client_metadata(self):
        """Test client-specific metadata."""
        design = get_design(
            "client:acme",
            overrides={
                "logo_url": "https://acme.com/logo.png",
                "wcag_target": "AAA",
            },
        )

        assert design["client"] == "client:acme"
        assert design["logo_url"] == "https://acme.com/logo.png"
        assert design["wcag_target"] == "AAA"

    def test_invalid_system_raises(self):
        """Test that invalid system raises ValueError."""
        with pytest.raises(ValueError) as exc_info:
            get_design("unknown")

        assert "Unknown design system" in str(exc_info.value)


class TestKDSHelpers:
    """Tests for KDS helper functions."""

    def test_get_css(self):
        """Test CSS retrieval."""
        css = get_css()

        assert isinstance(css, str)
        assert ".kds" in css
        assert ".kds-card" in css
        assert ".kds-btn" in css

    def test_get_css_with_design(self):
        """Test CSS with custom design."""
        design = get_design("kearney")
        css = get_css(design)

        assert isinstance(css, str)
        assert len(css) > 0

    def test_kds_classes(self):
        """Test KDS class mapping."""
        classes = kds_classes()

        assert classes["card"] == "kds-card"
        assert classes["btn"] == "kds-btn"
        assert classes["badge"] == "kds-badge"
        assert classes["row"] == "kds-row"
        assert classes["input"] == "kds-input"
        assert classes["section"] == "kds-section"
        assert classes["h1"] == "kds-h1"
        assert classes["h2"] == "kds-h2"

    def test_html_shell(self):
        """Test HTML shell generation."""
        html = html_shell("Test Report", "<div class='kds-card'>Hello World</div>")

        assert "<!doctype html>" in html
        assert "<title>Test Report</title>" in html
        assert "<style>" in html
        assert ".kds" in html
        assert "<body class='kds'>" in html
        assert "<div class='kds-card'>Hello World</div>" in html

    def test_pdf_theme(self):
        """Test PDF theme retrieval."""
        theme = pdf_theme()

        assert "colors" in theme
        assert "fonts" in theme
        assert "margins" in theme

    def test_pptx_theme(self):
        """Test PPTX theme application (no-op for now)."""
        # This is a hook for future PPTX theming
        # Should not raise any errors
        pptx_theme(None)


class TestHTMLGuardrails:
    """Tests for HTML sanitizer guardrails."""

    def test_enforce_valid_html(self):
        """Test that valid HTML passes."""
        html = "<div class='kds-card'>Hello</div>"
        result = enforce_kds_html(html)
        assert result == html

    def test_enforce_rejects_inline_style(self):
        """Test that inline style attribute is rejected."""
        html = '<div style="color:red">Bad</div>'

        with pytest.raises(ValueError) as exc_info:
            enforce_kds_html(html)

        assert "Inline style attribute detected" in str(exc_info.value)
        assert "use KDS classes" in str(exc_info.value)

    def test_enforce_rejects_inline_style_single_quote(self):
        """Test that inline style with single quotes is rejected."""
        html = "<div style='background:blue'>Bad</div>"

        with pytest.raises(ValueError) as exc_info:
            enforce_kds_html(html)

        assert "Inline style attribute detected" in str(exc_info.value)

    def test_enforce_rejects_hex_color(self):
        """Test that inline hex colors are rejected."""
        html = '<span>#ff00aa</span>'

        with pytest.raises(ValueError) as exc_info:
            enforce_kds_html(html)

        assert "Inline hex color detected" in str(exc_info.value)
        assert "use KDS tokens" in str(exc_info.value)

    def test_enforce_rejects_short_hex(self):
        """Test that short hex colors (#RGB) are rejected."""
        html = '<p>#f0a</p>'

        with pytest.raises(ValueError) as exc_info:
            enforce_kds_html(html)

        assert "Inline hex color detected" in str(exc_info.value)

    def test_enforce_allows_kds_classes(self):
        """Test that KDS classes are allowed."""
        html = """
        <div class='kds'>
            <div class='kds-card'>
                <h1 class='kds-h1'>Title</h1>
                <div class='kds-row'>
                    <button class='kds-btn'>Click</button>
                    <span class='kds-badge'>New</span>
                </div>
            </div>
        </div>
        """
        result = enforce_kds_html(html)
        assert result == html


class TestIntegration:
    """Integration tests for preflight + registry."""

    def test_preflight_to_design_workflow(self):
        """Test complete workflow from preflight to design."""
        # Step 1: Preflight selection
        config = {"design_system": "kearney"}
        selection = ensure_design_selection(config, env={})

        assert selection.system == "kearney"

        # Step 2: Get design tokens
        design = get_design(selection.system, selection.overrides)

        assert design["colors"]["accent"] == "#7823DC"  # Official Kearney purple
        assert design["fonts"]["headline"] == "Inter"

        # Step 3: Generate HTML with KDS
        classes = kds_classes(design)
        body = f"<div class='{classes['card']}'>Hello KDS</div>"
        html = html_shell("Report", body, design)

        assert "kds-card" in html
        assert "<style>" in html

        # Step 4: Enforce guardrails
        result = enforce_kds_html(body)
        assert result == body

    def test_client_override_workflow(self):
        """Test workflow with client overrides."""
        # Step 1: Preflight with client system
        config = {
            "design_system": "client:acme",
            "design_overrides": {
                "colors": {"accent": "#FF6600"},
                "logo_url": "https://acme.com/logo.png",
            },
        }
        selection = ensure_design_selection(config, env={})

        assert selection.system == "client:acme"
        assert selection.overrides is not None

        # Step 2: Get design with overrides
        design = get_design(selection.system, selection.overrides)

        # Client accent should override
        assert design["colors"]["accent"] == "#FF6600"

        # Kearney base should remain (official Kearney colors)
        assert design["colors"]["fg"] == "#1E1E1E"  # Official Kearney dark gray

        # Client metadata
        assert design["client"] == "client:acme"
        assert design["logo_url"] == "https://acme.com/logo.png"
