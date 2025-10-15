"""Tests for registry integrity verification."""

import pytest
import tempfile
from pathlib import Path

from src.registry.manager import RegistryManager


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


class TestIntegrityVerification:
    """Test integrity verification detects tampering."""

    def test_verify_valid_registry(self, temp_project):
        """Should pass for valid registry with no tampering."""
        manager = RegistryManager(temp_project)

        # Publish model
        manager.publish_model(
            name="test_model",
            version="1.0.0",
            artifacts=["models/test_model.pkl"],
        )

        # Register dataset
        manager.register_dataset(
            name="test_dataset",
            version="1.0.0",
            artifacts=["datasets/test_data.parquet"],
            row_count=1000,
        )

        # Verify
        results = manager.verify_integrity()

        assert results["valid"] is True
        assert results["models_checked"] == 1
        assert results["datasets_checked"] == 1
        assert len(results["errors"]) == 0

    def test_detect_tampered_model_artifact(self, temp_project):
        """Should detect when model artifact is modified."""
        manager = RegistryManager(temp_project)

        # Publish model
        manager.publish_model(
            name="test_model",
            version="1.0.0",
            artifacts=["models/test_model.pkl"],
        )

        # Tamper with artifact (modify content)
        artifact_path = temp_project / "models" / "test_model.pkl"
        artifact_path.write_bytes(b"tampered model data")

        # Verify should detect mismatch
        results = manager.verify_integrity()

        assert results["valid"] is False
        assert len(results["errors"]) > 0
        assert "hash mismatch" in results["errors"][0].lower()
        assert "test_model" in results["errors"][0]

    def test_detect_missing_model_artifact(self, temp_project):
        """Should detect when model artifact is deleted."""
        manager = RegistryManager(temp_project)

        # Publish model
        manager.publish_model(
            name="test_model",
            version="1.0.0",
            artifacts=["models/test_model.pkl"],
        )

        # Delete artifact
        artifact_path = temp_project / "models" / "test_model.pkl"
        artifact_path.unlink()

        # Verify should detect missing file
        results = manager.verify_integrity()

        assert results["valid"] is False
        assert len(results["errors"]) > 0
        assert "not found" in results["errors"][0].lower()

    def test_detect_tampered_dataset_artifact(self, temp_project):
        """Should detect when dataset artifact is modified."""
        manager = RegistryManager(temp_project)

        # Register dataset
        manager.register_dataset(
            name="test_dataset",
            version="1.0.0",
            artifacts=["datasets/test_data.parquet"],
            row_count=1000,
        )

        # Tamper with artifact
        artifact_path = temp_project / "datasets" / "test_data.parquet"
        artifact_path.write_bytes(b"tampered dataset data")

        # Verify should detect mismatch
        results = manager.verify_integrity()

        assert results["valid"] is False
        assert len(results["errors"]) > 0
        assert "hash mismatch" in results["errors"][0].lower()
        assert "test_dataset" in results["errors"][0]

    def test_detect_multiple_issues(self, temp_project):
        """Should detect multiple integrity issues."""
        manager = RegistryManager(temp_project)

        # Publish model
        manager.publish_model(
            name="model_a",
            version="1.0.0",
            artifacts=["models/test_model.pkl"],
        )

        # Register dataset
        manager.register_dataset(
            name="dataset_a",
            version="1.0.0",
            artifacts=["datasets/test_data.parquet"],
            row_count=1000,
        )

        # Tamper with both
        (temp_project / "models" / "test_model.pkl").write_bytes(b"tampered")
        (temp_project / "datasets" / "test_data.parquet").unlink()

        # Verify should detect both issues
        results = manager.verify_integrity()

        assert results["valid"] is False
        assert len(results["errors"]) == 2
        assert any("model_a" in err for err in results["errors"])
        assert any("dataset_a" in err for err in results["errors"])
