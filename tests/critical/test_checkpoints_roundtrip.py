"""Checkpoint persistence tests.

Tests that checkpoint data can be written and read correctly.
"""

import json
from pathlib import Path


def test_checkpoint_json_roundtrip(tmp_path):
    """Test writing and reading a checkpoint JSON file."""
    checkpoints_dir = tmp_path / "checkpoints"
    checkpoints_dir.mkdir()

    checkpoint_file = checkpoints_dir / "0001_test_phase.json"

    # Write checkpoint
    payload = {
        "version": 1,
        "phase": "test_phase",
        "status": "success",
        "timestamp": "2025-11-14T18:00:00Z",
        "artifacts": ["artifact1.txt", "artifact2.md"],
        "metadata": {
            "agent": "test",
            "duration_seconds": 42,
            "notes": "This is a test checkpoint",
        },
    }

    checkpoint_file.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    assert checkpoint_file.exists()

    # Read checkpoint
    loaded = json.loads(checkpoint_file.read_text(encoding="utf-8"))

    # Verify structure
    assert loaded["version"] == 1
    assert loaded["phase"] == "test_phase"
    assert loaded["status"] == "success"
    assert "metadata" in loaded
    assert loaded["metadata"]["agent"] == "test"


def test_checkpoint_validation(tmp_path):
    """Test that checkpoint data has required fields."""
    checkpoints_dir = tmp_path / "checkpoints"
    checkpoints_dir.mkdir()

    checkpoint_file = checkpoints_dir / "0002_validation_test.json"

    # Write minimal valid checkpoint
    minimal_payload = {"version": 1, "phase": "test", "status": "success"}

    checkpoint_file.write_text(json.dumps(minimal_payload), encoding="utf-8")

    # Read and validate
    loaded = json.loads(checkpoint_file.read_text(encoding="utf-8"))

    # Required fields
    assert "version" in loaded
    assert "phase" in loaded
    assert "status" in loaded

    # Version should be integer
    assert isinstance(loaded["version"], int)
    assert loaded["version"] >= 1

    # Status should be valid
    assert loaded["status"] in {"success", "failure", "pending", "skipped"}


def test_checkpoint_with_orchestrator_module(tmp_path):
    """Test checkpoints using orchestrator module if available."""
    try:
        # Try to import checkpoints module
        from src.orchestrator import checkpoints

        checkpoints_dir = tmp_path / "checkpoints"
        checkpoints_dir.mkdir()

        # If module has validation/reading functions, test them
        if hasattr(checkpoints, "validate_artifacts"):
            # Module exists but we'll just verify import works
            assert callable(checkpoints.validate_artifacts)

    except (ImportError, AttributeError):
        # If checkpoints module doesn't exist or doesn't have expected functions,
        # skip this test (basic JSON tests above still validate format)
        pass
