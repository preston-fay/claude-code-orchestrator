"""
Checkpoint models for Orchestrator v2.

Defines checkpoint data structures.

See ADR-002 for checkpoint architecture.
"""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from orchestrator_v2.core.state_models import (
    AgentState,
    ArtifactInfo,
    CheckpointType,
    GovernanceResults,
    PhaseType,
)


class Checkpoint(BaseModel):
    """Complete checkpoint state snapshot.

    See ADR-002 for checkpoint structure.
    """
    # Identity
    id: str
    phase: PhaseType
    checkpoint_type: CheckpointType
    version: int = 1

    # Timing
    created_at: datetime = Field(default_factory=datetime.utcnow)
    duration_ms: int = 0

    # Orchestrator state
    run_id: str
    current_phase: PhaseType
    completed_phases: list[PhaseType] = Field(default_factory=list)
    intake_summary: dict[str, Any] = Field(default_factory=dict)

    # Agent states
    agent_states: dict[str, AgentState] = Field(default_factory=dict)

    # Artifacts
    artifacts: dict[str, ArtifactInfo] = Field(default_factory=dict)

    # Governance
    governance_results: GovernanceResults = Field(default_factory=GovernanceResults)

    # Lineage
    parent_checkpoint_id: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class CheckpointSummary(BaseModel):
    """Summary of a checkpoint for listing."""
    id: str
    phase: PhaseType
    checkpoint_type: CheckpointType
    version: int
    created_at: datetime
    passed: bool = True
    artifact_count: int = 0


class CheckpointDiff(BaseModel):
    """Difference between two checkpoints."""
    checkpoint_a: str
    checkpoint_b: str
    added_artifacts: list[str] = Field(default_factory=list)
    removed_artifacts: list[str] = Field(default_factory=list)
    modified_artifacts: list[str] = Field(default_factory=list)
    phase_changes: list[str] = Field(default_factory=list)
    governance_changes: dict[str, Any] = Field(default_factory=dict)
