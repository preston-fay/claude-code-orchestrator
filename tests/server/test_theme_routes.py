"""Tests for theme management API endpoints."""

import pytest
from fastapi.testclient import TestClient
from pathlib import Path
import tempfile
import json
import shutil

from src.server.app import app


@pytest.fixture
def temp_project_root():
    """Create temporary project structure for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        temp_root = Path(tmpdir)

        # Create directory structure
        clients_dir = temp_root / "clients"
        clients_dir.mkdir()

        schema_dir = clients_dir / ".schema"
        schema_dir.mkdir()

        design_dir = temp_root / "design_system"
        design_dir.mkdir()

        # Copy schema from actual project
        project_root = Path(__file__).parent.parent.parent
        schema_src = project_root / "clients" / ".schema" / "theme.schema.json"
        schema_dst = schema_dir / "theme.schema.json"

        with open(schema_src, "r") as f:
            schema = json.load(f)
        with open(schema_dst, "w") as f:
            json.dump(schema, f)

        # Copy base tokens
        tokens_src = project_root / "design_system" / "tokens.json"
        tokens_dst = design_dir / "tokens.json"

        with open(tokens_src, "r") as f:
            tokens = json.load(f)
        with open(tokens_dst, "w") as f:
            json.dump(tokens, f)

        yield temp_root


@pytest.fixture
def client(temp_project_root, monkeypatch):
    """Create test client with mocked paths."""
    import src.server.theme_routes as theme_routes

    # Monkey patch paths
    monkeypatch.setattr(theme_routes, "PROJECT_ROOT", temp_project_root)
    monkeypatch.setattr(theme_routes, "CLIENTS_DIR", temp_project_root / "clients")
    monkeypatch.setattr(theme_routes, "SCHEMA_PATH", temp_project_root / "clients" / ".schema" / "theme.schema.json")
    monkeypatch.setattr(theme_routes, "BASE_TOKENS_PATH", temp_project_root / "design_system" / "tokens.json")

    return TestClient(app)


@pytest.fixture
def valid_theme():
    """Valid test theme."""
    return {
        "client": {
            "slug": "test-client",
            "name": "Test Client"
        },
        "colors": {
            "light": {
                "primary": "#1E3A8A",
                "emphasis": "#7823DC"
            }
        },
        "constraints": {
            "allowEmojis": False,
            "allowGridlines": False,
            "labelFirst": True
        }
    }


@pytest.fixture
def invalid_theme():
    """Invalid test theme (missing constraints)."""
    return {
        "client": {
            "slug": "invalid-client",
            "name": "Invalid Client"
        }
    }


class TestListClients:
    """Test GET /api/theme/clients endpoint."""

    def test_list_clients_empty(self, client):
        """Should return empty list when no clients exist."""
        response = client.get("/api/theme/clients")
        assert response.status_code == 200
        data = response.json()
        assert "clients" in data
        assert data["clients"] == []

    def test_list_clients_with_themes(self, client, temp_project_root, valid_theme):
        """Should return list of client slugs."""
        # Create two test clients
        for slug in ["client-a", "client-b"]:
            client_dir = temp_project_root / "clients" / slug
            client_dir.mkdir()
            theme_file = client_dir / "theme.json"

            theme = valid_theme.copy()
            theme["client"]["slug"] = slug
            theme["client"]["name"] = slug.replace("-", " ").title()

            with open(theme_file, "w") as f:
                json.dump(theme, f)

        response = client.get("/api/theme/clients")
        assert response.status_code == 200
        data = response.json()
        assert data["clients"] == ["client-a", "client-b"]

    def test_list_clients_ignores_hidden_dirs(self, client, temp_project_root):
        """Should ignore directories starting with dot."""
        # Create hidden directory
        hidden_dir = temp_project_root / "clients" / ".hidden"
        hidden_dir.mkdir()
        (hidden_dir / "theme.json").write_text("{}")

        response = client.get("/api/theme/clients")
        assert response.status_code == 200
        data = response.json()
        assert ".hidden" not in data["clients"]


class TestGetClientTheme:
    """Test GET /api/theme/clients/{slug} endpoint."""

    def test_get_theme_success(self, client, temp_project_root, valid_theme):
        """Should return theme for existing client."""
        # Create client theme
        client_dir = temp_project_root / "clients" / "test-client"
        client_dir.mkdir()
        theme_file = client_dir / "theme.json"

        with open(theme_file, "w") as f:
            json.dump(valid_theme, f)

        response = client.get("/api/theme/clients/test-client")
        assert response.status_code == 200
        data = response.json()
        assert data["client"]["slug"] == "test-client"
        assert data["constraints"]["allowEmojis"] is False

    def test_get_theme_not_found(self, client):
        """Should return 404 for non-existent client."""
        response = client.get("/api/theme/clients/nonexistent")
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_get_theme_invalid_json(self, client, temp_project_root):
        """Should return 400 for malformed JSON."""
        client_dir = temp_project_root / "clients" / "broken"
        client_dir.mkdir()
        theme_file = client_dir / "theme.json"

        # Write invalid JSON
        with open(theme_file, "w") as f:
            f.write("{invalid json}")

        response = client.get("/api/theme/clients/broken")
        assert response.status_code == 400
        assert "invalid json" in response.json()["detail"].lower()


class TestSaveClientTheme:
    """Test POST /api/theme/clients/{slug} endpoint."""

    def test_save_theme_success(self, client, temp_project_root, valid_theme):
        """Should save valid theme."""
        response = client.post("/api/theme/clients/test-client", json=valid_theme)
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "test-client" in data["message"]

        # Verify file was created
        theme_file = temp_project_root / "clients" / "test-client" / "theme.json"
        assert theme_file.exists()

        with open(theme_file, "r") as f:
            saved_theme = json.load(f)
        assert saved_theme["client"]["slug"] == "test-client"

    def test_save_theme_creates_directory(self, client, temp_project_root, valid_theme):
        """Should create client directory if it doesn't exist."""
        response = client.post("/api/theme/clients/new-client", json={
            "client": {"slug": "new-client", "name": "New Client"},
            "constraints": {
                "allowEmojis": False,
                "allowGridlines": False,
                "labelFirst": True
            }
        })
        assert response.status_code == 200

        client_dir = temp_project_root / "clients" / "new-client"
        assert client_dir.exists()
        assert client_dir.is_dir()

    def test_save_theme_slug_mismatch(self, client, valid_theme):
        """Should fail if URL slug doesn't match theme slug."""
        response = client.post("/api/theme/clients/different-slug", json=valid_theme)
        assert response.status_code == 400
        assert "mismatch" in response.json()["detail"].lower()

    def test_save_theme_invalid_data(self, client):
        """Should fail with invalid theme data."""
        # Missing required constraints
        invalid = {
            "client": {"slug": "test", "name": "Test"}
        }
        response = client.post("/api/theme/clients/test", json=invalid)
        assert response.status_code == 422  # Pydantic validation error


class TestValidateTheme:
    """Test POST /api/theme/validate endpoint."""

    def test_validate_valid_theme(self, client, valid_theme):
        """Should validate correct theme."""
        response = client.post("/api/theme/validate", json=valid_theme)
        assert response.status_code == 200
        data = response.json()
        assert data["valid"] is True
        assert data["errors"] == []

    def test_validate_invalid_theme_missing_constraints(self, client, invalid_theme):
        """Should fail for theme missing required constraints."""
        response = client.post("/api/theme/validate", json=invalid_theme)
        assert response.status_code == 200  # Validation returns 200 with errors
        data = response.json()
        assert data["valid"] is False
        assert len(data["errors"]) > 0

    def test_validate_invalid_color_format(self, client, valid_theme):
        """Should fail for invalid hex color."""
        theme = valid_theme.copy()
        theme["colors"]["light"]["primary"] = "#GGGGGG"  # Invalid hex

        response = client.post("/api/theme/validate", json=theme)
        data = response.json()
        assert data["valid"] is False

    def test_validate_invalid_slug(self, client, valid_theme):
        """Should fail for invalid slug format."""
        theme = valid_theme.copy()
        theme["client"]["slug"] = "Invalid_Slug"  # Uppercase and underscore

        response = client.post("/api/theme/validate", json=theme)
        data = response.json()
        assert data["valid"] is False

    def test_validate_constraint_violations(self, client, valid_theme):
        """Should fail when constraints violate Kearney brand."""
        theme = valid_theme.copy()
        theme["constraints"]["allowEmojis"] = True  # Must be false

        response = client.post("/api/theme/validate", json=theme)
        data = response.json()
        assert data["valid"] is False


class TestMergeTheme:
    """Test POST /api/theme/merge endpoint."""

    def test_merge_theme_success(self, client, temp_project_root, valid_theme):
        """Should merge base tokens with client overrides."""
        # Create client theme
        client_dir = temp_project_root / "clients" / "test-client"
        client_dir.mkdir()
        theme_file = client_dir / "theme.json"

        with open(theme_file, "w") as f:
            json.dump(valid_theme, f)

        response = client.post("/api/theme/merge?slug=test-client")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["client"] == "test-client"
        assert "tokens" in data

        # Should have merged tokens
        tokens = data["tokens"]
        assert "colors" in tokens
        assert "typography" in tokens  # From base
        assert tokens["colors"]["light"]["primary"] == "#1E3A8A"  # From override

    def test_merge_preserves_base_tokens(self, client, temp_project_root, valid_theme):
        """Should preserve base tokens not overridden."""
        client_dir = temp_project_root / "clients" / "test-client"
        client_dir.mkdir()

        with open(client_dir / "theme.json", "w") as f:
            json.dump(valid_theme, f)

        response = client.post("/api/theme/merge?slug=test-client")
        data = response.json()
        tokens = data["tokens"]

        # Base typography should be present
        assert "typography" in tokens

    def test_merge_theme_not_found(self, client):
        """Should return 404 for non-existent client."""
        response = client.post("/api/theme/merge?slug=nonexistent")
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()


class TestGetSchema:
    """Test GET /api/theme/schema endpoint."""

    def test_get_schema_success(self, client):
        """Should return theme JSON schema."""
        response = client.get("/api/theme/schema")
        assert response.status_code == 200
        schema = response.json()

        # Should be valid JSON Schema
        assert "$schema" in schema
        assert "type" in schema
        assert schema["type"] == "object"
        assert "properties" in schema

        # Should have required theme properties
        assert "client" in schema["properties"]
        assert "constraints" in schema["properties"]


class TestDeleteClientTheme:
    """Test DELETE /api/theme/clients/{slug} endpoint."""

    def test_delete_theme_success(self, client, temp_project_root, valid_theme):
        """Should delete existing theme."""
        # Create client theme
        client_dir = temp_project_root / "clients" / "test-client"
        client_dir.mkdir()
        theme_file = client_dir / "theme.json"

        with open(theme_file, "w") as f:
            json.dump(valid_theme, f)

        response = client.delete("/api/theme/clients/test-client")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

        # File should be deleted
        assert not theme_file.exists()

    def test_delete_theme_removes_empty_directory(self, client, temp_project_root, valid_theme):
        """Should remove client directory if empty after deletion."""
        client_dir = temp_project_root / "clients" / "test-client"
        client_dir.mkdir()
        theme_file = client_dir / "theme.json"

        with open(theme_file, "w") as f:
            json.dump(valid_theme, f)

        client.delete("/api/theme/clients/test-client")

        # Directory should be removed
        assert not client_dir.exists()

    def test_delete_theme_keeps_directory_with_other_files(self, client, temp_project_root, valid_theme):
        """Should keep directory if other files exist."""
        client_dir = temp_project_root / "clients" / "test-client"
        client_dir.mkdir()
        theme_file = client_dir / "theme.json"
        other_file = client_dir / "other.txt"

        with open(theme_file, "w") as f:
            json.dump(valid_theme, f)
        with open(other_file, "w") as f:
            f.write("keep me")

        client.delete("/api/theme/clients/test-client")

        # Theme deleted but directory remains
        assert not theme_file.exists()
        assert client_dir.exists()
        assert other_file.exists()

    def test_delete_theme_not_found(self, client):
        """Should return 404 for non-existent client."""
        response = client.delete("/api/theme/clients/nonexistent")
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()


class TestRoundTrip:
    """Test complete save-retrieve-validate-merge workflow."""

    def test_full_theme_workflow(self, client, temp_project_root, valid_theme):
        """Test complete workflow: save -> get -> validate -> merge -> delete."""
        slug = "workflow-test"
        theme = valid_theme.copy()
        theme["client"]["slug"] = slug
        theme["client"]["name"] = "Workflow Test"

        # 1. Save theme
        save_response = client.post(f"/api/theme/clients/{slug}", json=theme)
        assert save_response.status_code == 200

        # 2. List clients (should include new one)
        list_response = client.get("/api/theme/clients")
        assert slug in list_response.json()["clients"]

        # 3. Get theme back
        get_response = client.get(f"/api/theme/clients/{slug}")
        assert get_response.status_code == 200
        retrieved = get_response.json()
        assert retrieved["client"]["slug"] == slug

        # 4. Validate retrieved theme
        validate_response = client.post("/api/theme/validate", json=retrieved)
        assert validate_response.json()["valid"] is True

        # 5. Merge theme
        merge_response = client.post(f"/api/theme/merge?slug={slug}")
        assert merge_response.status_code == 200
        merged = merge_response.json()["tokens"]
        assert merged["colors"]["light"]["primary"] == theme["colors"]["light"]["primary"]

        # 6. Delete theme
        delete_response = client.delete(f"/api/theme/clients/{slug}")
        assert delete_response.status_code == 200

        # 7. Verify deletion
        get_after_delete = client.get(f"/api/theme/clients/{slug}")
        assert get_after_delete.status_code == 404
