"""Tests for feature flags system."""

import json
from pathlib import Path
import pytest
import yaml

from src.governance.flags import is_enabled, get_all_flags, set_flag, unset_flag


@pytest.fixture
def temp_flags_file(tmp_path, monkeypatch):
    """Create a temporary flags file for testing."""
    flags_file = tmp_path / "flags.yaml"

    # Mock the FLAGS_FILE constant
    import src.governance.flags as flags_module
    monkeypatch.setattr(flags_module, "FLAGS_FILE", flags_file)

    return flags_file


def test_is_enabled_default_false(temp_flags_file):
    """Test that non-existent flags default to False."""
    assert is_enabled("nonexistent.flag") is False


def test_set_flag_creates_file(temp_flags_file):
    """Test that set_flag creates the flags file."""
    set_flag("test.flag", True)

    assert temp_flags_file.exists()

    with open(temp_flags_file) as f:
        config = yaml.safe_load(f)

    assert config["flags"]["test.flag"] is True


def test_set_flag_updates_existing(temp_flags_file):
    """Test updating an existing flag."""
    set_flag("test.flag", True)
    set_flag("test.flag", False)

    with open(temp_flags_file) as f:
        config = yaml.safe_load(f)

    assert config["flags"]["test.flag"] is False


def test_get_all_flags(temp_flags_file):
    """Test retrieving all flags."""
    set_flag("ui.feature1", True)
    set_flag("ui.feature2", False)
    set_flag("pipeline.feature1", True)

    flags = get_all_flags()

    assert len(flags) == 3
    assert flags["ui.feature1"] is True
    assert flags["ui.feature2"] is False
    assert flags["pipeline.feature1"] is True


def test_unset_flag(temp_flags_file):
    """Test removing a flag."""
    set_flag("test.flag", True)
    unset_flag("test.flag")

    flags = get_all_flags()
    assert "test.flag" not in flags


def test_flag_audit_logging(temp_flags_file, tmp_path, monkeypatch):
    """Test that flag changes are logged to audit trail."""
    audit_dir = tmp_path / "audit"
    audit_dir.mkdir()

    # Mock audit directory
    import src.governance.flags as flags_module
    original_log_func = flags_module._log_flag_change

    def mock_log_func(key: str, value):
        audit_file = audit_dir / "flags.ndjson"
        entry = {
            "timestamp": "2024-01-01T00:00:00",
            "event": "flag_change",
            "flag": key,
            "value": value,
            "action": "set" if value is not None else "unset",
        }
        with open(audit_file, "a") as f:
            f.write(json.dumps(entry) + "\n")

    monkeypatch.setattr(flags_module, "_log_flag_change", mock_log_func)

    set_flag("test.flag", True)

    audit_file = audit_dir / "flags.ndjson"
    assert audit_file.exists()

    with open(audit_file) as f:
        entry = json.loads(f.readline())

    assert entry["event"] == "flag_change"
    assert entry["flag"] == "test.flag"
    assert entry["value"] is True
    assert entry["action"] == "set"
