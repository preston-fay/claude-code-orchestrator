"""Tests for registry CLI commands."""

import pytest
import subprocess
import sys
import json
import tempfile
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.parent


@pytest.fixture
def temp_project():
    """Create temporary project structure for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        temp_root = Path(tmpdir)

        # Create directories
        (temp_root / "models" / "registry").mkdir(parents=True)
        (temp_root / "datasets").mkdir(parents=True)

        # Create test artifact
        test_model = temp_root / "models" / "test_model.pkl"
        test_model.write_bytes(b"test model data")

        test_dataset = temp_root / "datasets" / "test_data.parquet"
        test_dataset.write_bytes(b"test dataset data")

        # Create metrics file
        metrics = temp_root / "models" / "metrics.json"
        metrics.write_text(json.dumps({"rmse": 0.12, "r2": 0.89}))

        yield temp_root


class TestModelPublish:
    """Test 'orchestrator registry model-publish' command."""

    def test_publish_model_basic(self, temp_project):
        """Should publish model with basic info."""
        # Use RegistryManager directly for easier testing
        from src.registry.manager import RegistryManager

        manager = RegistryManager(temp_project)

        # Publish
        entry = manager.publish_model(
            name="test_model",
            version="1.0.0",
            artifacts=["models/test_model.pkl"],
        )

        assert entry.name == "test_model"
        assert entry.version == "1.0.0"
        assert len(entry.artifacts) == 1
        assert entry.sha256

    def test_publish_model_with_metrics(self, temp_project):
        """Should publish model with metrics."""
        from src.registry.manager import RegistryManager

        manager = RegistryManager(temp_project)

        # Publish with metrics
        entry = manager.publish_model(
            name="test_model",
            version="1.0.0",
            artifacts=["models/test_model.pkl"],
            metrics={"rmse": 0.12, "r2": 0.89},
        )

        assert entry.metrics["rmse"] == 0.12
        assert entry.metrics["r2"] == 0.89

    def test_publish_model_with_client(self, temp_project):
        """Should publish model with client info."""
        from src.registry.manager import RegistryManager

        manager = RegistryManager(temp_project)

        entry = manager.publish_model(
            name="test_model",
            version="1.0.0",
            artifacts=["models/test_model.pkl"],
            client="acme-corp",
            cleanliness_score=93,
            release_tag="v1.0.0",
            notes="Initial model",
        )

        assert entry.client == "acme-corp"
        assert entry.cleanliness_score == 93
        assert entry.release_tag == "v1.0.0"
        assert entry.notes == "Initial model"

    def test_publish_duplicate_fails(self, temp_project):
        """Should fail when publishing duplicate model+version."""
        from src.registry.manager import RegistryManager

        manager = RegistryManager(temp_project)

        # Publish first time
        manager.publish_model(
            name="test_model",
            version="1.0.0",
            artifacts=["models/test_model.pkl"],
        )

        # Second publish should fail
        with pytest.raises(ValueError, match="already exists"):
            manager.publish_model(
                name="test_model",
                version="1.0.0",
                artifacts=["models/test_model.pkl"],
            )

    def test_publish_missing_artifact_fails(self, temp_project):
        """Should fail when artifact doesn't exist."""
        from src.registry.manager import RegistryManager

        manager = RegistryManager(temp_project)

        with pytest.raises(FileNotFoundError):
            manager.publish_model(
                name="test_model",
                version="1.0.0",
                artifacts=["models/nonexistent.pkl"],
            )


class TestDatasetRegister:
    """Test 'orchestrator registry dataset-register' command."""

    def test_register_dataset_basic(self, temp_project):
        """Should register dataset with basic info."""
        from src.registry.manager import RegistryManager

        manager = RegistryManager(temp_project)

        entry = manager.register_dataset(
            name="test_dataset",
            version="1.0.0",
            artifacts=["datasets/test_data.parquet"],
            row_count=1000,
        )

        assert entry.name == "test_dataset"
        assert entry.version == "1.0.0"
        assert entry.row_count == 1000
        assert entry.sha256
        assert entry.schema_hash

    def test_register_dataset_with_client(self, temp_project):
        """Should register dataset with client info."""
        from src.registry.manager import RegistryManager

        manager = RegistryManager(temp_project)

        entry = manager.register_dataset(
            name="test_dataset",
            version="1.0.0",
            artifacts=["datasets/test_data.parquet"],
            row_count=3200000,
            client="acme-corp",
            cleanliness_score=95,
            release_tag="v1.0.0",
            notes="Sales dataset",
        )

        assert entry.row_count == 3200000
        assert entry.client == "acme-corp"
        assert entry.cleanliness_score == 95

    def test_register_duplicate_fails(self, temp_project):
        """Should fail when registering duplicate dataset+version."""
        from src.registry.manager import RegistryManager

        manager = RegistryManager(temp_project)

        # Register first time
        manager.register_dataset(
            name="test_dataset",
            version="1.0.0",
            artifacts=["datasets/test_data.parquet"],
            row_count=1000,
        )

        # Second register should fail
        with pytest.raises(ValueError, match="already exists"):
            manager.register_dataset(
                name="test_dataset",
                version="1.0.0",
                artifacts=["datasets/test_data.parquet"],
                row_count=1000,
            )


class TestFetch:
    """Test 'orchestrator registry fetch' command."""

    def test_fetch_model_by_name_version(self, temp_project):
        """Should fetch model by name and version."""
        from src.registry.manager import RegistryManager

        manager = RegistryManager(temp_project)

        # Publish
        manager.publish_model(
            name="test_model",
            version="1.0.0",
            artifacts=["models/test_model.pkl"],
        )

        # Fetch
        entry = manager.get_model("test_model", "1.0.0")

        assert entry is not None
        assert entry.name == "test_model"
        assert entry.version == "1.0.0"

    def test_fetch_model_latest(self, temp_project):
        """Should fetch latest version when version not specified."""
        from src.registry.manager import RegistryManager

        manager = RegistryManager(temp_project)

        # Publish multiple versions
        manager.publish_model(
            name="test_model",
            version="1.0.0",
            artifacts=["models/test_model.pkl"],
        )
        manager.publish_model(
            name="test_model",
            version="2.0.0",
            artifacts=["models/test_model.pkl"],
        )

        # Fetch latest
        entry = manager.get_model("test_model")

        assert entry is not None
        assert entry.version == "2.0.0"

    def test_fetch_nonexistent_model(self, temp_project):
        """Should return None for nonexistent model."""
        from src.registry.manager import RegistryManager

        manager = RegistryManager(temp_project)

        entry = manager.get_model("nonexistent")

        assert entry is None


class TestList:
    """Test 'orchestrator registry list' command."""

    def test_list_models_empty(self, temp_project):
        """Should return empty list when no models."""
        from src.registry.manager import RegistryManager

        manager = RegistryManager(temp_project)

        models = manager.list_models()

        assert models == []

    def test_list_models(self, temp_project):
        """Should list all models."""
        from src.registry.manager import RegistryManager

        manager = RegistryManager(temp_project)

        # Publish models
        manager.publish_model(
            name="model_a",
            version="1.0.0",
            artifacts=["models/test_model.pkl"],
        )
        manager.publish_model(
            name="model_b",
            version="1.0.0",
            artifacts=["models/test_model.pkl"],
        )

        models = manager.list_models()

        assert len(models) == 2
        names = {m.name for m in models}
        assert names == {"model_a", "model_b"}

    def test_list_models_by_client(self, temp_project):
        """Should filter models by client."""
        from src.registry.manager import RegistryManager

        manager = RegistryManager(temp_project)

        # Publish models with different clients
        manager.publish_model(
            name="model_a",
            version="1.0.0",
            artifacts=["models/test_model.pkl"],
            client="acme-corp",
        )
        manager.publish_model(
            name="model_b",
            version="1.0.0",
            artifacts=["models/test_model.pkl"],
            client="other-corp",
        )

        models = manager.list_models(client="acme-corp")

        assert len(models) == 1
        assert models[0].name == "model_a"


class TestVerify:
    """Test 'orchestrator registry verify' command."""

    def test_verify_valid_registry(self, temp_project):
        """Should pass verification for valid registry."""
        from src.registry.manager import RegistryManager

        manager = RegistryManager(temp_project)

        # Publish model
        manager.publish_model(
            name="test_model",
            version="1.0.0",
            artifacts=["models/test_model.pkl"],
        )

        # Verify
        results = manager.verify_integrity()

        assert results["valid"] is True
        assert results["models_checked"] == 1
        assert len(results["errors"]) == 0

    def test_verify_missing_artifact(self, temp_project):
        """Should detect missing artifact."""
        from src.registry.manager import RegistryManager

        manager = RegistryManager(temp_project)

        # Publish model
        manager.publish_model(
            name="test_model",
            version="1.0.0",
            artifacts=["models/test_model.pkl"],
        )

        # Delete artifact
        (temp_project / "models" / "test_model.pkl").unlink()

        # Verify
        results = manager.verify_integrity()

        assert results["valid"] is False
        assert len(results["errors"]) > 0
        assert "not found" in results["errors"][0].lower()

    def test_verify_hash_mismatch(self, temp_project):
        """Should detect hash mismatch."""
        from src.registry.manager import RegistryManager

        manager = RegistryManager(temp_project)

        # Publish model
        manager.publish_model(
            name="test_model",
            version="1.0.0",
            artifacts=["models/test_model.pkl"],
        )

        # Modify artifact
        (temp_project / "models" / "test_model.pkl").write_bytes(b"modified data")

        # Verify
        results = manager.verify_integrity()

        assert results["valid"] is False
        assert len(results["errors"]) > 0
        assert "hash mismatch" in results["errors"][0].lower()


class TestStats:
    """Test 'orchestrator registry stats' command."""

    def test_stats_empty(self, temp_project):
        """Should return zero stats for empty registry."""
        from src.registry.manager import RegistryManager

        manager = RegistryManager(temp_project)

        stats = manager.get_stats()

        assert stats["models_total"] == 0
        assert stats["datasets_total"] == 0

    def test_stats_with_models(self, temp_project):
        """Should return stats for models."""
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

        stats = manager.get_stats()

        assert stats["models_total"] == 2
        assert stats["models_by_client"]["acme-corp"] == 2
        assert stats["avg_model_cleanliness"] == 92.5
