"""Test reject then approve workflow."""

import pytest
import yaml
from src.orchestrator.runloop import Orchestrator
from src.orchestrator.types import RunStatus


@pytest.fixture
def temp_project_with_consensus(tmp_path):
    """Create temporary project with consensus gate."""
    config_dir = tmp_path / ".claude"
    config_dir.mkdir()

    config = {
        "orchestrator": {"state_file": ".claude/orchestrator_state.json"},
        "workflow": {
            "phases": {
                "planning": {
                    "enabled": True,
                    "agents": ["architect"],
                    "requires_consensus": True,
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
            f.write(f"# {agent.capitalize()}\n\nAgent: {{{{agent}}}}")

    return tmp_path


def test_reject_sets_needs_revision(temp_project_with_consensus):
    """Test that rejecting consensus sets status to needs_revision."""
    orch = Orchestrator(temp_project_with_consensus)

    # Start run and execute phase
    orch.start_run()
    orch.next_phase()

    # Verify awaiting consensus
    assert orch.state.awaiting_consensus is True

    # Reject
    orch.reject_consensus("Architecture needs improvement")

    # Verify status
    assert orch.state.status == RunStatus.NEEDS_REVISION
    assert orch.state.awaiting_consensus is False
    assert "planning" not in orch.state.completed_phases


def test_resume_after_reject(temp_project_with_consensus):
    """Test resuming after rejection."""
    orch = Orchestrator(temp_project_with_consensus)

    # Start, execute, reject
    orch.start_run()
    orch.next_phase()
    orch.reject_consensus("Needs work")

    # Verify needs revision
    assert orch.state.status == RunStatus.NEEDS_REVISION

    # Resume
    orch.resume_run()

    # Verify status back to running
    assert orch.state.status == RunStatus.RUNNING
    assert orch.state.current_phase == "planning"


def test_approve_after_resume(temp_project_with_consensus):
    """Test full workflow: reject → resume → execute → approve."""
    orch = Orchestrator(temp_project_with_consensus)

    # Start and execute
    orch.start_run()
    orch.next_phase()

    # Reject
    orch.reject_consensus("Needs revision")
    assert orch.state.status == RunStatus.NEEDS_REVISION

    # Resume
    orch.resume_run()
    assert orch.state.status == RunStatus.RUNNING

    # Execute again
    outcome = orch.next_phase()
    assert outcome.awaiting_consensus is True

    # This time approve
    orch.approve_consensus()

    # Verify approved and advanced
    assert orch.state.status == RunStatus.RUNNING
    assert "planning" in orch.state.completed_phases
    assert orch.state.current_phase == "development"


def test_multiple_reject_approve_cycles(temp_project_with_consensus):
    """Test multiple rejection cycles on same phase."""
    orch = Orchestrator(temp_project_with_consensus)

    orch.start_run()

    # First cycle: reject
    orch.next_phase()
    orch.reject_consensus("Iteration 1")
    assert orch.state.status == RunStatus.NEEDS_REVISION

    # Resume and try again
    orch.resume_run()
    orch.next_phase()

    # Second cycle: reject again
    orch.reject_consensus("Iteration 2")
    assert orch.state.status == RunStatus.NEEDS_REVISION

    # Resume and approve this time
    orch.resume_run()
    orch.next_phase()
    orch.approve_consensus()

    # Verify finally approved
    assert orch.state.status == RunStatus.RUNNING
    assert "planning" in orch.state.completed_phases
    assert orch.state.current_phase == "development"


def test_reject_reason_recorded(temp_project_with_consensus):
    """Test that rejection reason is recorded in decision file."""
    orch = Orchestrator(temp_project_with_consensus)

    orch.start_run()
    orch.next_phase()

    reason = "Architecture needs more detail on database schema"
    orch.reject_consensus(reason)

    # Find decision file
    consensus_dir = temp_project_with_consensus / ".claude" / "consensus"
    decision_files = list(consensus_dir.glob("DECISION_*.md"))

    assert len(decision_files) == 1

    # Verify reason in file
    content = decision_files[0].read_text()
    assert reason in content
    assert "REJECTED" in content
