"""Test checkpoint artifact validation."""

import pytest
from pathlib import Path
from src.orchestrator.checkpoints import validate_artifacts, ValidationStatus


@pytest.fixture
def temp_project_with_artifacts(tmp_path):
    """Create temporary project with some artifacts."""
    # Create some test files
    src_dir = tmp_path / "src"
    src_dir.mkdir()

    (src_dir / "main.py").write_text("print('hello')")
    (src_dir / "utils.py").write_text("def helper(): pass")

    docs_dir = tmp_path / "docs"
    docs_dir.mkdir()

    (docs_dir / "README.md").write_text("# Docs")

    # Create reports directory
    reports_dir = tmp_path / "reports"
    reports_dir.mkdir()

    return tmp_path


def test_validate_all_artifacts_found(temp_project_with_artifacts):
    """Test validation when all artifacts exist."""
    required = ["src/*.py", "docs/README.md"]

    result = validate_artifacts(
        artifacts_required=required,
        project_root=temp_project_with_artifacts,
        phase_name="test_phase",
    )

    assert result.status == ValidationStatus.PASS
    assert len(result.found) >= 3  # main.py, utils.py, README.md
    assert len(result.missing) == 0


def test_validate_partial_artifacts(temp_project_with_artifacts):
    """Test validation when some artifacts missing."""
    required = ["src/*.py", "docs/README.md", "missing/*.txt"]

    result = validate_artifacts(
        artifacts_required=required,
        project_root=temp_project_with_artifacts,
        phase_name="test_phase",
    )

    assert result.status == ValidationStatus.PARTIAL
    assert len(result.found) >= 3
    assert "missing/*.txt" in result.missing


def test_validate_no_artifacts_found(temp_project_with_artifacts):
    """Test validation when no artifacts exist."""
    required = ["nonexistent/*.xyz", "missing/file.txt"]

    result = validate_artifacts(
        artifacts_required=required,
        project_root=temp_project_with_artifacts,
        phase_name="test_phase",
    )

    assert result.status == ValidationStatus.FAIL
    assert len(result.found) == 0
    assert len(result.missing) == 2


def test_validation_report_generated(temp_project_with_artifacts):
    """Test that validation report is generated."""
    required = ["src/*.py"]

    result = validate_artifacts(
        artifacts_required=required,
        project_root=temp_project_with_artifacts,
        phase_name="test_phase",
    )

    # Verify report path
    assert result.validation_report_path is not None

    report_path = Path(result.validation_report_path)
    assert report_path.exists()

    # Verify report content
    content = report_path.read_text()
    assert "Checkpoint Validation: test_phase" in content
    assert "PASS" in content or "PARTIAL" in content or "FAIL" in content


def test_validation_report_format(temp_project_with_artifacts):
    """Test validation report markdown format."""
    required = ["src/*.py", "docs/README.md"]

    result = validate_artifacts(
        artifacts_required=required,
        project_root=temp_project_with_artifacts,
        phase_name="test_phase",
    )

    report_path = Path(result.validation_report_path)
    content = report_path.read_text()

    # Check for required sections
    assert "# Checkpoint Validation:" in content
    assert "## Required Artifacts" in content
    assert "## Validation Results" in content
    assert "### Found Artifacts" in content


def test_empty_files_ignored(temp_project_with_artifacts):
    """Test that empty files are not counted as valid artifacts."""
    # Create an empty file
    empty_file = temp_project_with_artifacts / "src" / "empty.py"
    empty_file.write_text("")

    required = ["src/empty.py"]

    result = validate_artifacts(
        artifacts_required=required,
        project_root=temp_project_with_artifacts,
        phase_name="test_phase",
    )

    # Empty file should not be in 'found' list
    assert "src/empty.py" not in result.found


def test_glob_pattern_matching(temp_project_with_artifacts):
    """Test that glob patterns match correctly."""
    # Test wildcard pattern
    result = validate_artifacts(
        artifacts_required=["src/**/*.py"],
        project_root=temp_project_with_artifacts,
        phase_name="test_phase",
    )

    assert result.status == ValidationStatus.PASS
    assert any("main.py" in f for f in result.found)
    assert any("utils.py" in f for f in result.found)
