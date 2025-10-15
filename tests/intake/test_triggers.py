"""Tests for natural language trigger routing."""

import pytest
from pathlib import Path
import sys

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.orchestrator.nl_triggers import route_nl_command


class TestNLTriggers:
    """Test natural language trigger routing."""

    def test_new_project_simple(self):
        """Test basic 'new project' trigger."""
        cmd, msg = route_nl_command("new project", busy=False)
        assert cmd == ["intake", "new"]
        assert msg is None

    def test_create_new_project(self):
        """Test 'create new project' trigger."""
        cmd, msg = route_nl_command("create new project", busy=False)
        assert cmd == ["intake", "new"]
        assert msg is None

    def test_start_new_project(self):
        """Test 'start a new project' trigger."""
        cmd, msg = route_nl_command("start a new project", busy=False)
        assert cmd == ["intake", "new"]
        assert msg is None

    def test_begin_project_intake(self):
        """Test 'begin project intake' trigger."""
        cmd, msg = route_nl_command("begin project intake", busy=False)
        assert cmd == ["intake", "new"]
        assert msg is None

    def test_new_web_project(self):
        """Test type-specific 'new web project' trigger."""
        cmd, msg = route_nl_command("new web project", busy=False)
        assert cmd == ["intake", "new", "--type", "webapp"]
        assert msg is None

    def test_new_webapp(self):
        """Test 'new webapp' trigger."""
        cmd, msg = route_nl_command("new webapp", busy=False)
        assert cmd == ["intake", "new", "--type", "webapp"]
        assert msg is None

    def test_new_analytics_project(self):
        """Test 'new analytics project' trigger."""
        cmd, msg = route_nl_command("new analytics project", busy=False)
        assert cmd == ["intake", "new", "--type", "analytics"]
        assert msg is None

    def test_new_ml_project(self):
        """Test 'new ml project' trigger."""
        cmd, msg = route_nl_command("new ml project", busy=False)
        assert cmd == ["intake", "new", "--type", "ml"]
        assert msg is None

    def test_case_insensitive(self):
        """Test that triggers are case-insensitive."""
        cmd, msg = route_nl_command("NEW PROJECT", busy=False)
        assert cmd == ["intake", "new"]

        cmd, msg = route_nl_command("Create New Project", busy=False)
        assert cmd == ["intake", "new"]

    def test_type_detection_in_phrase(self):
        """Test type detection from keywords in phrase."""
        # "new project analytics" should detect analytics type
        cmd, msg = route_nl_command("new project analytics", busy=False)
        assert "--type" in cmd
        assert "analytics" in cmd

        # "new project for machine learning" should detect ml type
        cmd, msg = route_nl_command("new project for machine learning", busy=False)
        assert "--type" in cmd
        assert "ml" in cmd

    def test_busy_state_blocks_trigger(self):
        """Test that triggers are blocked when orchestrator is busy."""
        cmd, msg = route_nl_command("new project", busy=True)
        assert cmd == []
        assert "busy" in msg.lower() or "running" in msg.lower()

    def test_no_match(self):
        """Test that non-matching phrases return empty command."""
        cmd, msg = route_nl_command("something else entirely", busy=False)
        assert cmd == []
        assert msg is None

    def test_with_default_type(self):
        """Test default_type parameter."""
        cmd, msg = route_nl_command("new project", busy=False, default_type="library")
        # Basic trigger doesn't use default_type (only partial matches do)
        assert cmd == ["intake", "new"]

    @pytest.mark.parametrize("phrase,expected_cmd", [
        ("new project", ["intake", "new"]),
        ("create new project", ["intake", "new"]),
        ("new web project", ["intake", "new", "--type", "webapp"]),
        ("new service", ["intake", "new", "--type", "service"]),
        ("new library", ["intake", "new", "--type", "library"]),
    ])
    def test_trigger_table(self, phrase, expected_cmd):
        """Table-driven test for multiple trigger phrases."""
        cmd, msg = route_nl_command(phrase, busy=False)
        assert cmd == expected_cmd
        assert msg is None

    def test_whitespace_handling(self):
        """Test that extra whitespace doesn't break matching."""
        cmd, msg = route_nl_command("  new project  ", busy=False)
        assert cmd == ["intake", "new"]

    def test_busy_note_includes_abort_command(self):
        """Test that busy message includes abort command."""
        cmd, msg = route_nl_command("new project", busy=True)
        assert "abort" in msg.lower()
        assert "orchestrator run" in msg.lower() or "orchestrator" in msg.lower()
