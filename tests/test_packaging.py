"""Tests for artifact packaging."""

import pytest
import json
import zipfile
from pathlib import Path
from src.orchestrator.packaging import (
    package_phase_artifacts,
    extract_manifest,
    list_phase_bundles,
    get_metrics_digest,
)
from src.orchestrator.types import AgentOutcome
from src.orchestrator.checkpoints import ValidationResult, ValidationStatus


class TestPackaging:
    """Test artifact packaging for phase handoffs."""

    @pytest.fixture
    def test_artifacts(self, tmp_path):
        """Create test artifacts."""
        # Create some test files
        (tmp_path / "output").mkdir()
        (tmp_path / "output" / "file1.txt").write_text("test content 1")
        (tmp_path / "output" / "file2.json").write_text('{"key": "value"}')
        (tmp_path / "models").mkdir()
        (tmp_path / "models" / "model.pkl").write_text("model data")

        return ["output/file1.txt", "output/file2.json", "models/model.pkl"]

    def test_package_phase_artifacts(self, tmp_path, test_artifacts):
        """Test basic artifact packaging."""
        run_id = "test_run_123"
        phase_name = "development"

        zip_path = package_phase_artifacts(
            phase_name=phase_name,
            artifact_paths=test_artifacts,
            project_root=tmp_path,
            run_id=run_id,
        )

        # Verify zip was created
        assert zip_path.exists()
        assert zip_path.name == f"{phase_name}.zip"
        assert zip_path.parent.name == run_id

        # Verify zip contents
        with zipfile.ZipFile(zip_path, "r") as zipf:
            names = zipf.namelist()
            assert "MANIFEST.json" in names
            assert "output/file1.txt" in names
            assert "output/file2.json" in names
            assert "models/model.pkl" in names

    def test_manifest_content(self, tmp_path, test_artifacts):
        """Test manifest contains correct metadata."""
        run_id = "test_run_456"
        phase_name = "testing"

        metrics_digest = {
            "phase": phase_name,
            "agents_executed": 2,
            "agents_succeeded": 2,
            "total_duration_s": 42.5,
        }

        zip_path = package_phase_artifacts(
            phase_name=phase_name,
            artifact_paths=test_artifacts,
            project_root=tmp_path,
            run_id=run_id,
            metrics_digest=metrics_digest,
        )

        # Extract and verify manifest
        manifest = extract_manifest(zip_path)

        assert manifest["phase"] == phase_name
        assert manifest["run_id"] == run_id
        assert manifest["artifact_count"] == len(test_artifacts)
        assert manifest["artifacts"] == test_artifacts
        assert manifest["metrics_digest"] == metrics_digest
        assert "created_at" in manifest

    def test_package_directory(self, tmp_path):
        """Test packaging entire directories."""
        # Create directory structure
        (tmp_path / "reports").mkdir()
        (tmp_path / "reports" / "summary.md").write_text("# Summary")
        (tmp_path / "reports" / "data.csv").write_text("a,b,c")
        (tmp_path / "reports" / "subdir").mkdir()
        (tmp_path / "reports" / "subdir" / "detail.txt").write_text("details")

        artifact_paths = ["reports"]

        zip_path = package_phase_artifacts(
            phase_name="analysis",
            artifact_paths=artifact_paths,
            project_root=tmp_path,
            run_id="test_run",
        )

        # Verify all files in directory were included
        with zipfile.ZipFile(zip_path, "r") as zipf:
            names = zipf.namelist()
            assert "reports/summary.md" in names
            assert "reports/data.csv" in names
            assert "reports/subdir/detail.txt" in names

    def test_missing_artifacts_warning(self, tmp_path, capsys):
        """Test that missing artifacts generate warnings but don't fail."""
        artifact_paths = ["existing.txt", "missing.txt", "also_missing.txt"]

        # Create only one file
        (tmp_path / "existing.txt").write_text("exists")

        zip_path = package_phase_artifacts(
            phase_name="test",
            artifact_paths=artifact_paths,
            project_root=tmp_path,
            run_id="test_run",
        )

        # Verify zip was still created
        assert zip_path.exists()

        # Verify only existing file is in zip
        with zipfile.ZipFile(zip_path, "r") as zipf:
            names = zipf.namelist()
            assert "existing.txt" in names
            assert "missing.txt" not in names

    def test_list_phase_bundles(self, tmp_path):
        """Test listing all phase bundles."""
        # Create multiple bundles
        for run_id in ["run_1", "run_2"]:
            for phase in ["planning", "development"]:
                artifacts_dir = tmp_path / "artifacts" / run_id
                artifacts_dir.mkdir(parents=True, exist_ok=True)
                zip_path = artifacts_dir / f"{phase}.zip"
                zip_path.write_text("dummy")

        # List all bundles
        all_bundles = list_phase_bundles(tmp_path)
        assert len(all_bundles) == 4

        # List bundles for specific run
        run1_bundles = list_phase_bundles(tmp_path, run_id="run_1")
        assert len(run1_bundles) == 2
        assert all("run_1" in str(b) for b in run1_bundles)

    def test_get_metrics_digest(self):
        """Test metrics digest generation."""
        agent_outcomes = [
            AgentOutcome(
                agent_name="planner",
                success=True,
                artifacts=["plan.md"],
                exit_code=0,
                execution_time=12.3,
            ),
            AgentOutcome(
                agent_name="validator",
                success=True,
                artifacts=["validation.json"],
                exit_code=0,
                execution_time=5.7,
            ),
        ]

        validation = ValidationResult(
            status=ValidationStatus.PASS,
            required=["plan.md", "validation.json"],
            found=["plan.md", "validation.json"],
            missing=[],
            validation_report_path=Path("reports/validation.md"),
        )

        digest = get_metrics_digest("planning", agent_outcomes, validation)

        assert digest["phase"] == "planning"
        assert digest["agents_executed"] == 2
        assert digest["agents_succeeded"] == 2
        assert digest["total_duration_s"] == 18.0
        assert digest["validation"]["status"] == "pass"
        assert digest["validation"]["artifacts_found"] == 2
        assert digest["validation"]["artifacts_missing"] == 0

        # Verify agent details
        assert len(digest["agents"]) == 2
        assert digest["agents"][0]["name"] == "planner"
        assert digest["agents"][0]["success"] is True
        assert digest["agents"][0]["duration_s"] == 12.3

    def test_digest_with_failures(self):
        """Test metrics digest with failed agents."""
        agent_outcomes = [
            AgentOutcome(
                agent_name="agent1", success=True, artifacts=[], exit_code=0, execution_time=10.0
            ),
            AgentOutcome(
                agent_name="agent2",
                success=False,
                artifacts=[],
                exit_code=1,
                execution_time=5.0,
                errors=["Something failed"],
            ),
        ]

        digest = get_metrics_digest("test_phase", agent_outcomes, None)

        assert digest["agents_executed"] == 2
        assert digest["agents_succeeded"] == 1
        assert digest["total_duration_s"] == 15.0
