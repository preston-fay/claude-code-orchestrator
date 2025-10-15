"""Test CLI commands for repository hygiene."""

import subprocess
import pytest


class TestHygieneCLI:
    """Test orchestrator hygiene CLI commands."""

    def test_repo_hygiene_help(self):
        """Test orchestrator run repo-hygiene --help works."""
        result = subprocess.run(
            ["python3", "-m", "src.orchestrator", "run", "repo-hygiene", "--help"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        assert result.returncode == 0
        assert "repo-hygiene" in result.stdout.lower()
        assert "--apply" in result.stdout

    def test_run_command_group_exists(self):
        """Test that 'run' command group exists."""
        result = subprocess.run(
            ["python3", "-m", "src.orchestrator", "run", "--help"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        assert result.returncode == 0
        assert "repo-hygiene" in result.stdout.lower()

    def test_repo_hygiene_in_triggers(self):
        """Test that hygiene triggers are listed in orchestrator triggers."""
        result = subprocess.run(
            ["python3", "-m", "src.orchestrator", "triggers"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        assert result.returncode == 0
        assert "tidy repo" in result.stdout.lower() or "repo-hygiene" in result.stdout.lower()
