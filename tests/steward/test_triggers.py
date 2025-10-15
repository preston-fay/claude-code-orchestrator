"""Test natural language triggers for hygiene commands."""

import pytest
from src.orchestrator.nl_triggers import route_nl_command


class TestHygieneTriggers:
    """Test NL trigger routing for hygiene commands."""

    def test_tidy_repo_trigger(self):
        """Test 'tidy repo' phrase maps to repo-hygiene."""
        cmd, msg = route_nl_command("tidy repo", busy=False)
        assert cmd == ["run", "repo-hygiene"]
        assert msg is None

    def test_cleanup_repository_trigger(self):
        """Test 'cleanup repository' phrase."""
        cmd, msg = route_nl_command("cleanup repository", busy=False)
        assert cmd == ["run", "repo-hygiene"]
        assert msg is None

    def test_hygiene_check_trigger(self):
        """Test 'hygiene check' phrase."""
        cmd, msg = route_nl_command("hygiene check", busy=False)
        assert cmd == ["run", "repo-hygiene"]
        assert msg is None

    def test_clean_up_repo_trigger(self):
        """Test 'clean up repo' phrase."""
        cmd, msg = route_nl_command("clean up repo", busy=False)
        assert cmd == ["run", "repo-hygiene"]
        assert msg is None

    def test_repo_cleanup_trigger(self):
        """Test 'repo cleanup' phrase."""
        cmd, msg = route_nl_command("repo cleanup", busy=False)
        assert cmd == ["run", "repo-hygiene"]
        assert msg is None

    def test_busy_state_blocks_hygiene_trigger(self):
        """Test that hygiene triggers are blocked when orchestrator is busy."""
        cmd, msg = route_nl_command("tidy repo", busy=True)
        assert cmd == []
        assert "busy" in msg.lower() or "running" in msg.lower()

    def test_case_insensitivity(self):
        """Test triggers work regardless of case."""
        cmd, msg = route_nl_command("TIDY REPO", busy=False)
        assert cmd == ["run", "repo-hygiene"]

        cmd, msg = route_nl_command("Cleanup Repository", busy=False)
        assert cmd == ["run", "repo-hygiene"]

    @pytest.mark.parametrize(
        "phrase,expected_cmd",
        [
            ("tidy repo", ["run", "repo-hygiene"]),
            ("cleanup repository", ["run", "repo-hygiene"]),
            ("hygiene check", ["run", "repo-hygiene"]),
            ("clean up repo", ["run", "repo-hygiene"]),
            ("repo cleanup", ["run", "repo-hygiene"]),
        ],
    )
    def test_trigger_table(self, phrase, expected_cmd):
        """Table-driven test for hygiene trigger phrases."""
        cmd, msg = route_nl_command(phrase, busy=False)
        assert cmd == expected_cmd
        assert msg is None
