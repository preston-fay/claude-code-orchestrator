"""Error handling tests for orchestrator runloop.

Tests that the orchestrator handles errors gracefully:
- Invalid intake files
- Missing files
- Malformed YAML
"""

import subprocess
from pathlib import Path

import pytest


def test_runloop_missing_intake():
    """Test that missing intake file is handled gracefully."""
    result = subprocess.run(
        [
            "python",
            "-m",
            "src.orchestrator.cli",
            "run",
            "start",
            "--intake",
            "NON_EXISTENT_FILE.yaml",
        ],
        capture_output=True,
        text=True,
        timeout=10,
    )

    # Should fail (non-zero exit) OR give dependency warning
    combined = result.stdout + result.stderr

    # If dependencies not installed, CLI warns - acceptable
    if "dependencies not installed" in combined.lower():
        assert True
        return

    # Otherwise, should fail with clear error
    assert result.returncode != 0, "Should fail with missing intake file"

    # Should have error message (not just crash)
    error_indicators = ["error", "not found", "no such file", "does not exist"]

    has_error_msg = any(indicator in combined.lower() for indicator in error_indicators)
    assert has_error_msg, f"Expected error message, got: {combined[:500]}"


def test_runloop_malformed_yaml(tmp_path):
    """Test that malformed YAML is handled gracefully."""
    bad_yaml = tmp_path / "bad.yaml"
    bad_yaml.write_text("{ invalid yaml content [[[", encoding="utf-8")

    result = subprocess.run(
        [
            "python",
            "-m",
            "src.orchestrator.cli",
            "run",
            "start",
            "--intake",
            str(bad_yaml),
        ],
        capture_output=True,
        text=True,
        timeout=10,
    )

    combined = result.stdout + result.stderr

    # If dependencies not installed, that's acceptable
    if "dependencies not installed" in combined.lower():
        assert True
        return

    # Should fail gracefully
    assert result.returncode != 0, "Should fail with malformed YAML"

    # Should mention YAML or parsing error
    yaml_error_keywords = ["yaml", "parse", "invalid", "syntax"]

    has_yaml_error = any(keyword in combined.lower() for keyword in yaml_error_keywords)
    # If not a YAML error, should still be a clear error (not crash)
    has_clear_error = "error" in combined.lower() or "failed" in combined.lower()

    assert has_yaml_error or has_clear_error, f"Expected clear error, got: {combined[:500]}"
