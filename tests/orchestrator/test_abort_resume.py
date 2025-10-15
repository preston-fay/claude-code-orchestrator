"""Test abort and resume functionality."""

import pytest
import yaml
from src.orchestrator.runloop import Orchestrator
from src.orchestrator.types import RunStatus


@pytest.fixture
def temp_project(tmp_path):
    """Create temporary project."""
    config_dir = tmp_path / ".claude"
    config_dir.mkdir()

    config = {
        "orchestrator": {"state_file": ".claude/orchestrator_state.json"},
        "workflow": {
            "phases": {
                "planning": {
                    "enabled": True,
                    "agents": ["architect"],
                    "requires_consensus": False,
                    "artifacts_required": [],
                },
                "development": {
                    "enabled": True,
                    "agents": ["developer"],
                    "requires_consensus": False,
                    "artifacts_required": [],
                },
            }
        },
        "subagents": {
            "architect": {"enabled": True},
            "developer": {"enabled": True},
        },
    }

    with open(config_dir / "config.yaml", "w") as f:
        yaml.dump(config, f)

    # Create subagent prompts
    prompts_dir = tmp_path / "subagent_prompts"
    prompts_dir.mkdir()

    for agent in ["architect", "developer"]:
        with open(prompts_dir / f"{agent}.md", "w") as f:
            f.write(f"# {agent}\n")

    return tmp_path


def test_abort_sets_status(temp_project):
    """Test that abort sets status to ABORTED."""
    orch = Orchestrator(temp_project)

    # Start run
    orch.start_run()
    assert orch.state.status == RunStatus.RUNNING

    # Abort
    orch.abort_run()

    # Verify status
    assert orch.state.status == RunStatus.ABORTED


def test_abort_preserves_state(temp_project):
    """Test that abort preserves run state."""
    orch = Orchestrator(temp_project)

    # Start run
    orch.start_run()
    run_id = orch.state.run_id
    current_phase = orch.state.current_phase

    # Abort
    orch.abort_run()

    # Verify state preserved
    assert orch.state.run_id == run_id
    assert orch.state.current_phase == current_phase
    assert orch.state.created_at != ""


def test_resume_from_aborted(temp_project):
    """Test resuming from aborted status."""
    orch = Orchestrator(temp_project)

    # Start and abort
    orch.start_run()
    run_id = orch.state.run_id
    orch.abort_run()

    # Resume
    orch.resume_run()

    # Verify status back to running
    assert orch.state.status == RunStatus.RUNNING
    assert orch.state.run_id == run_id


def test_resume_from_needs_revision(temp_project):
    """Test that resume works from NEEDS_REVISION status."""
    orch = Orchestrator(temp_project)

    # Manually set to needs revision
    orch.start_run()
    orch.state.status = RunStatus.NEEDS_REVISION
    orch._save_state()

    # Resume
    orch.resume_run()

    assert orch.state.status == RunStatus.RUNNING


def test_cannot_resume_from_running(temp_project):
    """Test that resume raises error if already running."""
    orch = Orchestrator(temp_project)

    orch.start_run()
    assert orch.state.status == RunStatus.RUNNING

    # Try to resume when already running
    with pytest.raises(RuntimeError, match="Cannot resume"):
        orch.resume_run()


def test_cannot_abort_idle_run(temp_project):
    """Test that aborting idle run raises error."""
    orch = Orchestrator(temp_project)

    # Don't start run - should be idle
    assert orch.state.status == RunStatus.IDLE

    # Try to abort
    with pytest.raises(RuntimeError, match="No active run"):
        orch.abort_run()


def test_abort_after_phase_execution(temp_project):
    """Test aborting after executing a phase."""
    orch = Orchestrator(temp_project)

    # Start and execute one phase
    orch.start_run()
    orch.next_phase()

    # Verify phase completed
    assert "planning" in orch.state.completed_phases

    # Abort
    orch.abort_run()

    # Verify completed phases preserved
    assert "planning" in orch.state.completed_phases
    assert orch.state.status == RunStatus.ABORTED

    # Resume and continue
    orch.resume_run()
    assert orch.state.current_phase == "development"
    assert "planning" in orch.state.completed_phases


def test_state_persists_across_abort_resume(temp_project):
    """Test that state file persists through abort/resume cycle."""
    orch = Orchestrator(temp_project)

    # Start run
    orch.start_run()
    run_id = orch.state.run_id

    # Abort
    orch.abort_run()

    # Create new orchestrator instance (simulates restart)
    orch2 = Orchestrator(temp_project)

    # Verify state loaded
    assert orch2.state.run_id == run_id
    assert orch2.state.status == RunStatus.ABORTED

    # Resume from new instance
    orch2.resume_run()
    assert orch2.state.status == RunStatus.RUNNING
