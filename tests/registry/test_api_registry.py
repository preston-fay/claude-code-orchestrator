"""Tests for registry API endpoints."""

import pytest
from fastapi.testclient import TestClient
from pathlib import Path
import tempfile
import json

from src.server.app import app


@pytest.fixture
def temp_project():
    """Create temporary project for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        temp_root = Path(tmpdir)

        # Create directories
        (temp_root / "models" / "registry").mkdir(parents=True)
        (temp_root / "datasets").mkdir(parents=True)

        # Create test artifacts
        test_model = temp_root / "models" / "test_model.pkl"
        test_model.write_bytes(b"test model data")

        test_dataset = temp_root / "datasets" / "test_data.parquet"
        test_dataset.write_bytes(b"test dataset data")

        yield temp_root


@pytest.fixture
def client(temp_project, monkeypatch):
    """Create test client with mocked paths."""
    import src.server.registry_routes as registry_routes

    monkeypatch.setattr(registry_routes, "PROJECT_ROOT", temp_project)

    return TestClient(app)


@pytest.fixture
def api_key():
    """Return test API key."""
    return "kearney-registry-key"


class TestListModels:
    """Test GET /api/registry/models endpoint."""

    def test_list_models_empty(self, client):
        """Should return empty list when no models."""
        response = client.get("/api/registry/models")

        assert response.status_code == 200
        data = response.json()
        assert data["count"] == 0
        assert data["models"] == []

    def test_list_models(self, client, temp_project, api_key):
        """Should list models after publishing."""
        from src.registry.manager import RegistryManager

        manager = RegistryManager(temp_project)

        # Publish model
        manager.publish_model(
            name="test_model",
            version="1.0.0",
            artifacts=["models/test_model.pkl"],
        )

        response = client.get("/api/registry/models")

        assert response.status_code == 200
        data = response.json()
        assert data["count"] == 1
        assert data["models"][0]["name"] == "test_model"


class TestGetModel:
    """Test GET /api/registry/models/{name} endpoint."""

    def test_get_model_success(self, client, temp_project):
        """Should return model metadata."""
        from src.registry.manager import RegistryManager

        manager = RegistryManager(temp_project)

        # Publish
        manager.publish_model(
            name="test_model",
            version="1.0.0",
            artifacts=["models/test_model.pkl"],
            metrics={"rmse": 0.12},
        )

        response = client.get("/api/registry/models/test_model")

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "test_model"
        assert data["version"] == "1.0.0"
        assert data["metrics"]["rmse"] == 0.12

    def test_get_model_not_found(self, client):
        """Should return 404 for nonexistent model."""
        response = client.get("/api/registry/models/nonexistent")

        assert response.status_code == 404


class TestPublishModel:
    """Test POST /api/registry/models endpoint."""

    def test_publish_model_success(self, client, temp_project, api_key):
        """Should publish model with valid API key."""
        payload = {
            "name": "test_model",
            "version": "1.0.0",
            "artifacts": ["models/test_model.pkl"],
            "metrics": {"rmse": 0.12, "r2": 0.89},
            "client": "acme-corp",
        }

        response = client.post(
            "/api/registry/models",
            json=payload,
            headers={"X-API-Key": api_key},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["model"]["name"] == "test_model"

    def test_publish_model_no_api_key(self, client):
        """Should reject without API key."""
        payload = {
            "name": "test_model",
            "version": "1.0.0",
            "artifacts": ["models/test_model.pkl"],
        }

        response = client.post("/api/registry/models", json=payload)

        assert response.status_code == 401

    def test_publish_model_invalid_api_key(self, client):
        """Should reject with invalid API key."""
        payload = {
            "name": "test_model",
            "version": "1.0.0",
            "artifacts": ["models/test_model.pkl"],
        }

        response = client.post(
            "/api/registry/models",
            json=payload,
            headers={"X-API-Key": "invalid-key"},
        )

        assert response.status_code == 401

    def test_publish_model_missing_artifact(self, client, api_key):
        """Should fail when artifact doesn't exist."""
        payload = {
            "name": "test_model",
            "version": "1.0.0",
            "artifacts": ["models/nonexistent.pkl"],
        }

        response = client.post(
            "/api/registry/models",
            json=payload,
            headers={"X-API-Key": api_key},
        )

        assert response.status_code == 400


class TestListDatasets:
    """Test GET /api/registry/datasets endpoint."""

    def test_list_datasets(self, client, temp_project):
        """Should list datasets."""
        from src.registry.manager import RegistryManager

        manager = RegistryManager(temp_project)

        # Register dataset
        manager.register_dataset(
            name="test_dataset",
            version="1.0.0",
            artifacts=["datasets/test_data.parquet"],
            row_count=1000,
        )

        response = client.get("/api/registry/datasets")

        assert response.status_code == 200
        data = response.json()
        assert data["count"] == 1
        assert data["datasets"][0]["name"] == "test_dataset"


class TestRegisterDataset:
    """Test POST /api/registry/datasets endpoint."""

    def test_register_dataset_success(self, client, temp_project, api_key):
        """Should register dataset with valid API key."""
        payload = {
            "name": "test_dataset",
            "version": "1.0.0",
            "artifacts": ["datasets/test_data.parquet"],
            "row_count": 3200000,
            "client": "acme-corp",
        }

        response = client.post(
            "/api/registry/datasets",
            json=payload,
            headers={"X-API-Key": api_key},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["dataset"]["row_count"] == 3200000


class TestGetMetrics:
    """Test GET /api/registry/metrics endpoint."""

    def test_get_metrics(self, client, temp_project):
        """Should return aggregate stats."""
        from src.registry.manager import RegistryManager

        manager = RegistryManager(temp_project)

        # Publish models
        manager.publish_model(
            name="model_a",
            version="1.0.0",
            artifacts=["models/test_model.pkl"],
            client="acme-corp",
            cleanliness_score=90,
        )
        manager.publish_model(
            name="model_b",
            version="1.0.0",
            artifacts=["models/test_model.pkl"],
            client="acme-corp",
            cleanliness_score=95,
        )

        response = client.get("/api/registry/metrics")

        assert response.status_code == 200
        data = response.json()
        assert data["models_total"] == 2
        assert data["models_by_client"]["acme-corp"] == 2
        assert data["avg_model_cleanliness"] == 92.5


class TestVerifyIntegrity:
    """Test POST /api/registry/verify endpoint."""

    def test_verify_integrity_valid(self, client, temp_project, api_key):
        """Should pass verification for valid registry."""
        from src.registry.manager import RegistryManager

        manager = RegistryManager(temp_project)

        # Publish model
        manager.publish_model(
            name="test_model",
            version="1.0.0",
            artifacts=["models/test_model.pkl"],
        )

        response = client.post(
            "/api/registry/verify",
            headers={"X-API-Key": api_key},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["valid"] is True
        assert data["models_checked"] == 1
