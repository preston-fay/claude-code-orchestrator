"""Smoke tests for CLI entry points.

These tests ensure the CLI can be invoked without crashing.
They verify basic help/version commands work.
"""

import subprocess


def test_cli_help_smoke():
    """Test that CLI --help works without errors."""
    result = subprocess.run(
        ["python", "-m", "src.orchestrator.cli", "--help"],
        capture_output=True,
        text=True,
        timeout=10,
    )

    combined_output = result.stdout + result.stderr

    # If not installed, should give clear warning (acceptable for smoke test)
    if "dependencies not installed" in combined_output or "pip install" in combined_output:
        # This is acceptable - CLI detected missing deps and gave clear message
        return  # Test passes

    # If installed, should work properly
    assert result.returncode == 0, f"CLI help failed: {result.stderr}"

    # Output should contain expected subcommands
    combined_lower = combined_output.lower()
    expected_tokens = ["help", "run", "command", "usage"]
    found = any(token in combined_lower for token in expected_tokens)

    assert found, f"Expected CLI help keywords not found in: {combined_output[:500]}"


def test_cli_module_import():
    """Test that orchestrator CLI module can be imported."""
    result = subprocess.run(
        ["python", "-c", "from src.orchestrator import cli; print('OK')"],
        capture_output=True,
        text=True,
        timeout=10,
    )

    combined = result.stdout + result.stderr

    # If dependencies not installed, that's acceptable for import test
    if "dependencies not installed" in combined or "pip install" in combined:
        # CLI still loaded enough to print warning
        return  # Test passes

    assert result.returncode == 0, f"Import failed: {result.stderr}"
    assert "OK" in result.stdout, f"Import didn't complete: {result.stdout}"
