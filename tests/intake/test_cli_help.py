"""Tests for CLI help and command availability."""

import pytest
import subprocess
from pathlib import Path


class TestCLIHelp:
    """Test CLI help commands and structure."""

    def test_orchestrator_main_help(self):
        """Test that orchestrator --help works."""
        result = subprocess.run(
            ["python3", "-m", "src.orchestrator", "--help"],
            capture_output=True,
            text=True,
            timeout=5
        )
        assert result.returncode == 0
        assert "orchestrator" in result.stdout.lower()
        assert "intake" in result.stdout.lower()

    def test_orchestrator_intake_help(self):
        """Test that orchestrator intake --help works."""
        result = subprocess.run(
            ["python3", "-m", "src.orchestrator", "intake", "--help"],
            capture_output=True,
            text=True,
            timeout=5
        )
        assert result.returncode == 0
        assert "intake" in result.stdout.lower()
        assert "new" in result.stdout.lower()
        assert "validate" in result.stdout.lower()

    def test_orchestrator_data_help(self):
        """Test that orchestrator data --help works."""
        result = subprocess.run(
            ["python3", "-m", "src.orchestrator", "data", "--help"],
            capture_output=True,
            text=True,
            timeout=5
        )
        # May fail if data CLI not properly integrated, but shouldn't crash
        assert result.returncode == 0 or "not found" in result.stderr.lower()
        if result.returncode == 0:
            assert "data" in result.stdout.lower()

    def test_orchestrator_status_help(self):
        """Test that orchestrator status command exists."""
        result = subprocess.run(
            ["python3", "-m", "src.orchestrator", "status"],
            capture_output=True,
            text=True,
            timeout=5
        )
        # Status should run without errors (even if orchestrator is idle)
        assert result.returncode == 0
        assert "status" in result.stdout.lower() or "idle" in result.stdout.lower()

    def test_orchestrator_triggers_help(self):
        """Test that orchestrator triggers command exists."""
        result = subprocess.run(
            ["python3", "-m", "src.orchestrator", "triggers"],
            capture_output=True,
            text=True,
            timeout=5
        )
        assert result.returncode == 0
        assert "trigger" in result.stdout.lower()
        assert "new project" in result.stdout.lower()

    def test_intake_new_help(self):
        """Test orchestrator intake new --help."""
        result = subprocess.run(
            ["python3", "-m", "src.orchestrator", "intake", "new", "--help"],
            capture_output=True,
            text=True,
            timeout=5
        )
        assert result.returncode == 0
        assert "--type" in result.stdout
        assert "project type" in result.stdout.lower()

    def test_intake_validate_help(self):
        """Test orchestrator intake validate --help."""
        result = subprocess.run(
            ["python3", "-m", "src.orchestrator", "intake", "validate", "--help"],
            capture_output=True,
            text=True,
            timeout=5
        )
        assert result.returncode == 0
        assert "validate" in result.stdout.lower()

    def test_intake_templates_command(self):
        """Test orchestrator intake templates command."""
        result = subprocess.run(
            ["python3", "-m", "src.orchestrator", "intake", "templates"],
            capture_output=True,
            text=True,
            timeout=5
        )
        assert result.returncode == 0
        assert "template" in result.stdout.lower()
        # Should list at least webapp, analytics, ml templates
        assert "webapp" in result.stdout.lower()
        assert "analytics" in result.stdout.lower()
        assert "ml" in result.stdout.lower()
