"""Tests for client theme JSON schema validation."""

import pytest
import json
import jsonschema
from pathlib import Path

# Paths
PROJECT_ROOT = Path(__file__).parent.parent.parent
SCHEMA_PATH = PROJECT_ROOT / "clients" / ".schema" / "theme.schema.json"


@pytest.fixture
def schema():
    """Load theme schema."""
    with open(SCHEMA_PATH, "r") as f:
        return json.load(f)


@pytest.fixture
def valid_minimal_theme():
    """Minimal valid theme."""
    return {
        "client": {
            "slug": "test-client",
            "name": "Test Client"
        },
        "constraints": {
            "allowEmojis": False,
            "allowGridlines": False,
            "labelFirst": True
        }
    }


@pytest.fixture
def valid_full_theme():
    """Full valid theme with all optional fields."""
    return {
        "client": {
            "slug": "full-client",
            "name": "Full Client",
            "logo": "logo.svg"
        },
        "colors": {
            "light": {
                "primary": "#7823DC",
                "secondary": "#A855F7",
                "emphasis": "#E63946",
                "background": "#FFFFFF",
                "surface": "#F5F5F5",
                "text": "#1A1A1A",
                "text_secondary": "#666666",
                "border": "#D1D5DB"
            },
            "dark": {
                "primary": "#A855F7",
                "secondary": "#C084FC",
                "emphasis": "#EF476F",
                "background": "#1A1A1A",
                "surface": "#2D2D2D",
                "text": "#FFFFFF",
                "text_secondary": "#A3A3A3",
                "border": "#404040"
            }
        },
        "typography": {
            "fontFamilyPrimary": "Inter, Arial, sans-serif",
            "fontFamilyMonospace": "SF Mono, Courier New, monospace",
            "fontSizeBase": "16px",
            "fontWeightNormal": 400,
            "fontWeightBold": 700
        },
        "spacing": {
            "base": 8
        },
        "constraints": {
            "allowEmojis": False,
            "allowGridlines": False,
            "labelFirst": True
        }
    }


class TestSchemaValidation:
    """Test schema validation with valid and invalid themes."""

    def test_minimal_valid_theme(self, schema, valid_minimal_theme):
        """Minimal theme should validate."""
        jsonschema.validate(instance=valid_minimal_theme, schema=schema)

    def test_full_valid_theme(self, schema, valid_full_theme):
        """Full theme with all fields should validate."""
        jsonschema.validate(instance=valid_full_theme, schema=schema)

    def test_missing_client_fails(self, schema):
        """Theme without client info should fail."""
        theme = {
            "constraints": {
                "allowEmojis": False,
                "allowGridlines": False,
                "labelFirst": True
            }
        }

        with pytest.raises(jsonschema.ValidationError):
            jsonschema.validate(instance=theme, schema=schema)

    def test_missing_constraints_fails(self, schema):
        """Theme without constraints should fail."""
        theme = {
            "client": {
                "slug": "test",
                "name": "Test"
            }
        }

        with pytest.raises(jsonschema.ValidationError):
            jsonschema.validate(instance=theme, schema=schema)

    def test_invalid_slug_fails(self, schema, valid_minimal_theme):
        """Slug with uppercase or special chars should fail."""
        invalid_slugs = [
            "Test-Client",  # Uppercase
            "test_client",  # Underscore
            "test client",  # Space
            "test@client",  # Special char
        ]

        for slug in invalid_slugs:
            theme = valid_minimal_theme.copy()
            theme["client"]["slug"] = slug

            with pytest.raises(jsonschema.ValidationError):
                jsonschema.validate(instance=theme, schema=schema)

    def test_valid_slug_passes(self, schema, valid_minimal_theme):
        """Valid slugs should pass."""
        valid_slugs = [
            "test-client",
            "test123",
            "client-2024",
            "a",
            "123",
        ]

        for slug in valid_slugs:
            theme = valid_minimal_theme.copy()
            theme["client"]["slug"] = slug
            jsonschema.validate(instance=theme, schema=schema)


class TestColorValidation:
    """Test color value validation."""

    def test_valid_hex_colors(self, schema, valid_minimal_theme):
        """Valid hex colors should pass."""
        valid_colors = [
            "#000000",
            "#FFFFFF",
            "#7823DC",
            "#abc123",
            "#ABC123",
        ]

        for color in valid_colors:
            theme = valid_minimal_theme.copy()
            theme["colors"] = {
                "light": {"primary": color}
            }
            jsonschema.validate(instance=theme, schema=schema)

    def test_invalid_hex_colors_fail(self, schema, valid_minimal_theme):
        """Invalid hex colors should fail."""
        invalid_colors = [
            "#00000",      # Too short
            "#0000000",    # Too long
            "#GGGGGG",     # Invalid hex
            "000000",      # Missing #
            "#000",        # Short form not allowed
            "rgb(0,0,0)",  # RGB format not allowed
        ]

        for color in invalid_colors:
            theme = valid_minimal_theme.copy()
            theme["colors"] = {
                "light": {"primary": color}
            }

            with pytest.raises(jsonschema.ValidationError):
                jsonschema.validate(instance=theme, schema=schema)


class TestTypographyValidation:
    """Test typography validation."""

    def test_valid_font_families(self, schema, valid_minimal_theme):
        """Valid font families with fallbacks should pass."""
        valid_fonts = [
            "Inter, Arial, sans-serif",
            "Roboto, Helvetica, sans-serif",
            "Georgia, Times New Roman, serif",
            "SF Mono, Courier New, monospace",
            "CustomFont, sans-serif",
        ]

        for font in valid_fonts:
            theme = valid_minimal_theme.copy()
            theme["typography"] = {"fontFamilyPrimary": font}
            jsonschema.validate(instance=theme, schema=schema)

    def test_missing_fallback_fails(self, schema, valid_minimal_theme):
        """Font family without fallback should fail."""
        invalid_fonts = [
            "Inter",
            "Roboto, Arial",  # Missing generic fallback
            "CustomFont",
        ]

        for font in invalid_fonts:
            theme = valid_minimal_theme.copy()
            theme["typography"] = {"fontFamilyPrimary": font}

            with pytest.raises(jsonschema.ValidationError):
                jsonschema.validate(instance=theme, schema=schema)

    def test_valid_font_sizes(self, schema, valid_minimal_theme):
        """Valid font sizes should pass."""
        valid_sizes = ["12px", "16px", "18px", "24px"]

        for size in valid_sizes:
            theme = valid_minimal_theme.copy()
            theme["typography"] = {"fontSizeBase": size}
            jsonschema.validate(instance=theme, schema=schema)

    def test_invalid_font_sizes_fail(self, schema, valid_minimal_theme):
        """Invalid font sizes should fail."""
        invalid_sizes = ["16", "16pt", "1rem", "medium"]

        for size in invalid_sizes:
            theme = valid_minimal_theme.copy()
            theme["typography"] = {"fontSizeBase": size}

            with pytest.raises(jsonschema.ValidationError):
                jsonschema.validate(instance=theme, schema=schema)

    def test_valid_font_weights(self, schema, valid_minimal_theme):
        """Valid font weights should pass."""
        valid_weights = {
            "fontWeightNormal": [300, 400, 500],
            "fontWeightBold": [600, 700, 800]
        }

        for key, weights in valid_weights.items():
            for weight in weights:
                theme = valid_minimal_theme.copy()
                theme["typography"] = {key: weight}
                jsonschema.validate(instance=theme, schema=schema)

    def test_invalid_font_weights_fail(self, schema, valid_minimal_theme):
        """Invalid font weights should fail."""
        invalid_weights = {
            "fontWeightNormal": [100, 200, 600, 700],
            "fontWeightBold": [300, 400, 500, 900]
        }

        for key, weights in invalid_weights.items():
            for weight in weights:
                theme = valid_minimal_theme.copy()
                theme["typography"] = {key: weight}

                with pytest.raises(jsonschema.ValidationError):
                    jsonschema.validate(instance=theme, schema=schema)


class TestConstraintsValidation:
    """Test Kearney brand constraints validation."""

    def test_allow_emojis_must_be_false(self, schema, valid_minimal_theme):
        """allowEmojis must be false."""
        theme = valid_minimal_theme.copy()
        theme["constraints"]["allowEmojis"] = True

        with pytest.raises(jsonschema.ValidationError):
            jsonschema.validate(instance=theme, schema=schema)

    def test_allow_gridlines_must_be_false(self, schema, valid_minimal_theme):
        """allowGridlines must be false."""
        theme = valid_minimal_theme.copy()
        theme["constraints"]["allowGridlines"] = True

        with pytest.raises(jsonschema.ValidationError):
            jsonschema.validate(instance=theme, schema=schema)

    def test_label_first_must_be_true(self, schema, valid_minimal_theme):
        """labelFirst must be true."""
        theme = valid_minimal_theme.copy()
        theme["constraints"]["labelFirst"] = False

        with pytest.raises(jsonschema.ValidationError):
            jsonschema.validate(instance=theme, schema=schema)

    def test_all_constraints_required(self, schema):
        """All three constraints must be present."""
        theme = {
            "client": {
                "slug": "test",
                "name": "Test"
            },
            "constraints": {
                "allowEmojis": False,
                "allowGridlines": False,
                # Missing labelFirst
            }
        }

        with pytest.raises(jsonschema.ValidationError):
            jsonschema.validate(instance=theme, schema=schema)


class TestExistingThemes:
    """Test that existing client themes validate."""

    def test_acme_corp_theme_validates(self, schema):
        """ACME Corp example theme should validate."""
        acme_path = PROJECT_ROOT / "clients" / "acme-corp" / "theme.json"

        if not acme_path.exists():
            pytest.skip("ACME Corp theme not found")

        with open(acme_path, "r") as f:
            acme_theme = json.load(f)

        jsonschema.validate(instance=acme_theme, schema=schema)

    def test_all_client_themes_validate(self, schema):
        """All client themes in repository should validate."""
        clients_dir = PROJECT_ROOT / "clients"

        if not clients_dir.exists():
            pytest.skip("Clients directory not found")

        themes_found = 0
        for theme_file in clients_dir.glob("*/theme.json"):
            themes_found += 1

            with open(theme_file, "r") as f:
                theme = json.load(f)

            try:
                jsonschema.validate(instance=theme, schema=schema)
            except jsonschema.ValidationError as e:
                pytest.fail(f"Theme {theme_file.parent.name} failed validation: {e.message}")

        if themes_found == 0:
            pytest.skip("No client themes found")
