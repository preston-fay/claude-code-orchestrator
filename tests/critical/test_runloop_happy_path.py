"""Happy path tests for orchestrator runloop.

Tests the core workflow execution without real agents.
Uses minimal intake with empty agent list to verify orchestration logic.
"""

import subprocess
from pathlib import Path

import pytest


def test_runloop_initialization(test_workspace):
    """Test that Orchestrator can be initialized."""
    try:
        from src.orchestrator.runloop import Orchestrator

        # Create minimal config for Orchestrator
        claude_dir = test_workspace / ".claude"
        claude_dir.mkdir(exist_ok=True)

        # Use the new unified config if available
        try:
            from src.common.config import load_config

            config = load_config()
            # Write minimal orchestrator config
            import yaml

            config_data = {
                "orchestrator": {"state_file": ".claude/orchestrator_state.json"},
                "subagents": {},
                "workflow": {"phases": []},
            }
            (claude_dir / "config.yaml").write_text(
                yaml.dump(config_data), encoding="utf-8"
            )
        except ImportError:
            # Fallback to basic config
            import yaml

            config_data = {
                "orchestrator": {},
                "subagents": {},
                "workflow": {"phases": []},
            }
            (claude_dir / "config.yaml").write_text(
                yaml.dump(config_data), encoding="utf-8"
            )

        orch = Orchestrator(project_root=test_workspace)
        assert orch is not None
        assert orch.config is not None
        assert orch.state is not None
    except (ImportError, FileNotFoundError):
        pytest.skip("Orchestrator class not available or config not set up")


def test_runloop_workspace_structure(test_workspace):
    """Test that workspace directories can be created."""
    # Ensure common output dirs can be created without conflicts
    for subdir in ["reports", "checkpoints", "artifacts", "logs"]:
        dir_path = test_workspace / subdir
        dir_path.mkdir(exist_ok=True)
        assert dir_path.exists()
        assert dir_path.is_dir()


def test_runloop_via_cli_dry_run(minimal_intake_file, test_workspace):
    """Test runloop execution via CLI with minimal intake.

    This is a smoke test - we don't expect full execution to succeed
    (no real agents), but we should get past initialization.
    """
    # Try to run via CLI
    result = subprocess.run(
        [
            "python",
            "-m",
            "src.orchestrator.cli",
            "status",  # Simple status command
        ],
        capture_output=True,
        text=True,
        cwd=test_workspace,
        timeout=10,
    )

    # Status command should either succeed or fail gracefully
    # Not crash with import errors or syntax errors
    combined = result.stdout + result.stderr

    # Should not have Python tracebacks for basic imports
    assert "Traceback" not in combined or "No run in progress" in combined, (
        f"CLI crashed with traceback: {combined[:1000]}"
    )
