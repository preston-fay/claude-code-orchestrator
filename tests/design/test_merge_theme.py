"""Tests for theme merge script functionality."""

import pytest
import json
import tempfile
import subprocess
import sys
from pathlib import Path

# Paths
PROJECT_ROOT = Path(__file__).parent.parent.parent
MERGE_SCRIPT = PROJECT_ROOT / "scripts" / "merge_theme.py"
BASE_TOKENS = PROJECT_ROOT / "design_system" / "tokens.json"


@pytest.fixture
def temp_client_dir():
    """Create temporary client directory for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        temp_path = Path(tmpdir)
        clients_dir = temp_path / "clients"
        clients_dir.mkdir()

        # Copy schema
        schema_dir = clients_dir / ".schema"
        schema_dir.mkdir()
        schema_src = PROJECT_ROOT / "clients" / ".schema" / "theme.schema.json"
        schema_dst = schema_dir / "theme.schema.json"

        with open(schema_src, "r") as f:
            schema = f.read()
        with open(schema_dst, "w") as f:
            f.write(schema)

        yield temp_path


@pytest.fixture
def minimal_theme():
    """Minimal valid theme."""
    return {
        "client": {
            "slug": "test-client",
            "name": "Test Client"
        },
        "colors": {
            "light": {
                "primary": "#1E3A8A"
            }
        },
        "constraints": {
            "allowEmojis": False,
            "allowGridlines": False,
            "labelFirst": True
        }
    }


class TestMergeScript:
    """Test merge_theme.py script execution."""

    def test_script_exists(self):
        """Merge script should exist and be executable."""
        assert MERGE_SCRIPT.exists()
        assert MERGE_SCRIPT.stat().st_mode & 0o111  # Check executable bit

    def test_validation_only_mode(self, temp_client_dir, minimal_theme):
        """Script should validate without generating files."""
        # Create client theme
        client_dir = temp_client_dir / "clients" / "test-client"
        client_dir.mkdir()
        theme_file = client_dir / "theme.json"

        with open(theme_file, "w") as f:
            json.dump(minimal_theme, f)

        # Copy base tokens
        design_dir = temp_client_dir / "design_system"
        design_dir.mkdir()
        with open(BASE_TOKENS, "r") as f:
            base = json.load(f)
        with open(design_dir / "tokens.json", "w") as f:
            json.dump(base, f)

        # Run script in validate-only mode
        result = subprocess.run(
            [
                sys.executable,
                str(MERGE_SCRIPT),
                "--client",
                "test-client",
                "--validate-only",
            ],
            cwd=temp_client_dir,
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0
        assert "Theme validation passed" in result.stdout

        # No files should be generated
        generated_dir = temp_client_dir / "design_system" / ".generated"
        assert not generated_dir.exists() or not any(generated_dir.iterdir())

    def test_generates_css_file(self, temp_client_dir, minimal_theme):
        """Script should generate CSS file with custom properties."""
        # Setup
        client_dir = temp_client_dir / "clients" / "test-client"
        client_dir.mkdir()

        with open(client_dir / "theme.json", "w") as f:
            json.dump(minimal_theme, f)

        design_dir = temp_client_dir / "design_system"
        design_dir.mkdir()

        with open(BASE_TOKENS, "r") as f:
            base = json.load(f)
        with open(design_dir / "tokens.json", "w") as f:
            json.dump(base, f)

        # Run script
        result = subprocess.run(
            [
                sys.executable,
                str(MERGE_SCRIPT),
                "--client",
                "test-client",
            ],
            cwd=temp_client_dir,
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0

        # Check CSS file
        css_file = design_dir / ".generated" / "test-client.css"
        assert css_file.exists()

        css_content = css_file.read_text()
        assert ":root {" in css_content
        assert "--primary: #1E3A8A;" in css_content
        assert "Auto-generated" in css_content
        assert "DO NOT EDIT MANUALLY" in css_content

    def test_generates_typescript_file(self, temp_client_dir, minimal_theme):
        """Script should generate TypeScript file with token exports."""
        # Setup
        client_dir = temp_client_dir / "clients" / "test-client"
        client_dir.mkdir()

        with open(client_dir / "theme.json", "w") as f:
            json.dump(minimal_theme, f)

        design_dir = temp_client_dir / "design_system"
        design_dir.mkdir()

        with open(BASE_TOKENS, "r") as f:
            base = json.load(f)
        with open(design_dir / "tokens.json", "w") as f:
            json.dump(base, f)

        # Run script
        result = subprocess.run(
            [
                sys.executable,
                str(MERGE_SCRIPT),
                "--client",
                "test-client",
            ],
            cwd=temp_client_dir,
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0

        # Check TypeScript file
        ts_file = design_dir / ".generated" / "test-client.ts"
        assert ts_file.exists()

        ts_content = ts_file.read_text()
        assert "export const tokens" in ts_content
        assert "as const" in ts_content
        assert "export type Theme" in ts_content
        assert "export function getThemeColors" in ts_content

    def test_generates_json_file(self, temp_client_dir, minimal_theme):
        """Script should generate merged JSON with metadata."""
        # Setup
        client_dir = temp_client_dir / "clients" / "test-client"
        client_dir.mkdir()

        with open(client_dir / "theme.json", "w") as f:
            json.dump(minimal_theme, f)

        design_dir = temp_client_dir / "design_system"
        design_dir.mkdir()

        with open(BASE_TOKENS, "r") as f:
            base = json.load(f)
        with open(design_dir / "tokens.json", "w") as f:
            json.dump(base, f)

        # Run script
        result = subprocess.run(
            [
                sys.executable,
                str(MERGE_SCRIPT),
                "--client",
                "test-client",
            ],
            cwd=temp_client_dir,
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0

        # Check JSON file
        json_file = design_dir / ".generated" / "test-client.json"
        assert json_file.exists()

        with open(json_file, "r") as f:
            merged = json.load(f)

        # Should have client metadata
        assert "_client" in merged
        assert merged["_client"]["slug"] == "test-client"
        assert merged["_client"]["name"] == "Test Client"

        # Should have merged colors
        assert "colors" in merged
        assert "light" in merged["colors"]
        assert merged["colors"]["light"]["primary"] == "#1E3A8A"

    def test_fails_on_invalid_theme(self, temp_client_dir):
        """Script should fail with invalid theme."""
        # Create invalid theme (missing constraints)
        invalid_theme = {
            "client": {
                "slug": "invalid",
                "name": "Invalid"
            }
        }

        client_dir = temp_client_dir / "clients" / "invalid"
        client_dir.mkdir()

        with open(client_dir / "theme.json", "w") as f:
            json.dump(invalid_theme, f)

        design_dir = temp_client_dir / "design_system"
        design_dir.mkdir()

        with open(BASE_TOKENS, "r") as f:
            base = json.load(f)
        with open(design_dir / "tokens.json", "w") as f:
            json.dump(base, f)

        # Run script
        result = subprocess.run(
            [
                sys.executable,
                str(MERGE_SCRIPT),
                "--client",
                "invalid",
                "--validate-only",
            ],
            cwd=temp_client_dir,
            capture_output=True,
            text=True,
        )

        assert result.returncode != 0
        assert "Validation failed" in result.stderr

    def test_fails_on_missing_client(self, temp_client_dir):
        """Script should fail if client doesn't exist."""
        design_dir = temp_client_dir / "design_system"
        design_dir.mkdir()

        with open(BASE_TOKENS, "r") as f:
            base = json.load(f)
        with open(design_dir / "tokens.json", "w") as f:
            json.dump(base, f)

        result = subprocess.run(
            [
                sys.executable,
                str(MERGE_SCRIPT),
                "--client",
                "nonexistent",
            ],
            cwd=temp_client_dir,
            capture_output=True,
            text=True,
        )

        assert result.returncode != 0
        assert "not found" in result.stderr.lower()


class TestDeepMerge:
    """Test deep merge algorithm."""

    def test_merge_preserves_base_tokens(self, temp_client_dir, minimal_theme):
        """Merge should preserve unoverrid base tokens."""
        # Setup
        client_dir = temp_client_dir / "clients" / "test-client"
        client_dir.mkdir()

        with open(client_dir / "theme.json", "w") as f:
            json.dump(minimal_theme, f)

        design_dir = temp_client_dir / "design_system"
        design_dir.mkdir()

        with open(BASE_TOKENS, "r") as f:
            base = json.load(f)
        with open(design_dir / "tokens.json", "w") as f:
            json.dump(base, f)

        # Run merge
        subprocess.run(
            [sys.executable, str(MERGE_SCRIPT), "--client", "test-client"],
            cwd=temp_client_dir,
            check=True,
            capture_output=True,
        )

        # Check merged JSON
        with open(design_dir / ".generated" / "test-client.json", "r") as f:
            merged = json.load(f)

        # Base typography should still be present
        assert "typography" in merged
        assert "font" in merged["typography"]

    def test_merge_overrides_specified_values(self, temp_client_dir):
        """Merge should override specified values."""
        theme = {
            "client": {"slug": "test", "name": "Test"},
            "colors": {
                "light": {
                    "primary": "#FF0000",  # Override
                    "emphasis": "#00FF00",  # Override
                }
            },
            "constraints": {
                "allowEmojis": False,
                "allowGridlines": False,
                "labelFirst": True
            }
        }

        client_dir = temp_client_dir / "clients" / "test"
        client_dir.mkdir()

        with open(client_dir / "theme.json", "w") as f:
            json.dump(theme, f)

        design_dir = temp_client_dir / "design_system"
        design_dir.mkdir()

        with open(BASE_TOKENS, "r") as f:
            base = json.load(f)
        with open(design_dir / "tokens.json", "w") as f:
            json.dump(base, f)

        # Run merge
        subprocess.run(
            [sys.executable, str(MERGE_SCRIPT), "--client", "test"],
            cwd=temp_client_dir,
            check=True,
            capture_output=True,
        )

        # Check merged JSON
        with open(design_dir / ".generated" / "test.json", "r") as f:
            merged = json.load(f)

        assert merged["colors"]["light"]["primary"] == "#FF0000"
        assert merged["colors"]["light"]["emphasis"] == "#00FF00"
