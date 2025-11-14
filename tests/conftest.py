"""Shared pytest fixtures for orchestrator tests."""

from pathlib import Path

import pytest


@pytest.fixture
def minimal_intake_file(tmp_path: Path) -> Path:
    """Provide a minimal intake YAML file for testing.

    Args:
        tmp_path: Pytest temporary directory

    Returns:
        Path to minimal_intake.yaml in tmp directory
    """
    intake_file = tmp_path / "minimal_intake.yaml"
    source = Path("tests/fixtures/minimal_intake.yaml")

    if source.exists():
        intake_file.write_text(source.read_text(encoding="utf-8"), encoding="utf-8")
    else:
        # Fallback inline content if fixture file missing
        content = """project:
  name: "test-project"
workflow:
  phases:
    - name: "test_phase"
      agents: []
runtime:
  auto_advance: false
"""
        intake_file.write_text(content, encoding="utf-8")

    return intake_file


@pytest.fixture
def test_workspace(tmp_path: Path) -> Path:
    """Provide a clean workspace directory for testing.

    Args:
        tmp_path: Pytest temporary directory

    Returns:
        Path to .work directory in tmp
    """
    workspace = tmp_path / ".work"
    workspace.mkdir(exist_ok=True)
    return workspace
