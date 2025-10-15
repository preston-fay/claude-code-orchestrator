"""Test that run next pauses on consensus gates."""

import pytest
import yaml
from pathlib import Path
from src.orchestrator.runloop import Orchestrator
from src.orchestrator.types import RunStatus


@pytest.fixture
def temp_project_with_consensus(tmp_path):
    """Create temporary project with consensus gate."""
    # Create config directory
    config_dir = tmp_path / ".claude"
    config_dir.mkdir()

    # Create config with consensus-gated phase
    config = {
        "orchestrator": {"state_file": ".claude/orchestrator_state.json"},
        "workflow": {
            "phases": {
                "planning": {
                    "enabled": True,
                    "agents": ["architect"],
                    "requires_consensus": True,  # Requires consensus
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

    # Create subagent_prompts directory with dummy templates
    prompts_dir = tmp_path / "subagent_prompts"
    prompts_dir.mkdir()

    for agent in ["architect", "developer"]:
        with open(prompts_dir / f"{agent}.md", "w") as f:
            f.write(f"# {agent.capitalize()} Prompt\n\nAgent: {{{{agent}}}}\nPhase: {{{{phase}}}}")

    return tmp_path


def test_run_next_pauses_on_consensus(temp_project_with_consensus):
    """Test that run next pauses when consensus required."""
    orch = Orchestrator(temp_project_with_consensus)

    # Start run
    orch.start_run()
    assert orch.state.current_phase == "planning"

    # Execute next phase (planning - requires consensus)
    outcome = orch.next_phase()

    # Verify consensus required
    assert outcome.requires_consensus is True
    assert outcome.awaiting_consensus is True

    # Verify state updated
    assert orch.state.status == RunStatus.AWAITING_CONSENSUS
    assert orch.state.awaiting_consensus is True
    assert orch.state.consensus_phase == "planning"

    # Verify still on same phase
    assert orch.state.current_phase == "planning"


def test_consensus_request_file_created(temp_project_with_consensus):
    """Test that consensus REQUEST.md is created."""
    orch = Orchestrator(temp_project_with_consensus)

    # Start and execute phase
    orch.start_run()
    outcome = orch.next_phase()

    # Verify consensus request file created
    consensus_file = temp_project_with_consensus / ".claude" / "consensus" / "REQUEST.md"
    assert consensus_file.exists()

    # Verify content
    content = consensus_file.read_text()
    assert "Consensus Request: planning" in content
    assert "orchestrator run approve" in content
    assert "orchestrator run reject" in content


def test_cannot_run_next_while_awaiting_consensus(temp_project_with_consensus):
    """Test that next_phase raises error when awaiting consensus."""
    orch = Orchestrator(temp_project_with_consensus)

    # Start and execute phase
    orch.start_run()
    orch.next_phase()

    # Verify awaiting consensus
    assert orch.state.awaiting_consensus is True

    # Try to run next again - should raise error
    with pytest.raises(RuntimeError, match="awaiting consensus"):
        orch.next_phase()


def test_phase_not_completed_while_awaiting_consensus(temp_project_with_consensus):
    """Test that phase is not marked completed until approved."""
    orch = Orchestrator(temp_project_with_consensus)

    # Start and execute phase
    orch.start_run()
    orch.next_phase()

    # Phase should not be in completed list yet
    assert "planning" not in orch.state.completed_phases


def test_approve_advances_to_next_phase(temp_project_with_consensus):
    """Test that approving consensus advances workflow."""
    orch = Orchestrator(temp_project_with_consensus)

    # Start and execute phase requiring consensus
    orch.start_run()
    orch.next_phase()

    # Approve consensus
    orch.approve_consensus()

    # Verify state updated
    assert orch.state.awaiting_consensus is False
    assert orch.state.consensus_phase is None
    assert orch.state.status == RunStatus.RUNNING

    # Verify phase marked completed
    assert "planning" in orch.state.completed_phases

    # Verify advanced to next phase
    assert orch.state.current_phase == "development"


def test_reject_sets_needs_revision(temp_project_with_consensus):
    """Test that rejecting consensus marks for revision."""
    orch = Orchestrator(temp_project_with_consensus)

    # Start and execute phase
    orch.start_run()
    orch.next_phase()

    # Reject consensus
    orch.reject_consensus("Needs more detail")

    # Verify state
    assert orch.state.awaiting_consensus is False
    assert orch.state.status == RunStatus.NEEDS_REVISION

    # Verify phase NOT marked completed
    assert "planning" not in orch.state.completed_phases

    # Verify decision file created
    consensus_dir = temp_project_with_consensus / ".claude" / "consensus"
    decision_files = list(consensus_dir.glob("DECISION_*.md"))
    assert len(decision_files) > 0

    # Verify decision content
    content = decision_files[0].read_text()
    assert "REJECTED" in content
    assert "Needs more detail" in content
