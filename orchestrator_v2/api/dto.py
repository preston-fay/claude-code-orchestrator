"""
Data Transfer Objects for Orchestrator v2 API.

These DTOs define the data structures for API communication.
"""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class ProjectDTO(BaseModel):
    """Project data transfer object."""
    project_id: str
    project_name: str
    client: str
    current_phase: str
    completed_phases: list[str] = Field(default_factory=list)
    created_at: datetime
    status: str = "active"


class PhaseDTO(BaseModel):
    """Phase data transfer object."""
    phase: str
    status: str
    started_at: datetime | None = None
    completed_at: datetime | None = None
    agent_ids: list[str] = Field(default_factory=list)
    artifact_count: int = 0
    error_message: str | None = None


class CheckpointDTO(BaseModel):
    """Checkpoint data transfer object."""
    id: str
    phase: str
    checkpoint_type: str
    version: int
    created_at: datetime
    passed: bool
    artifact_count: int


class StatusDTO(BaseModel):
    """Workflow status data transfer object."""
    project_id: str
    run_id: str
    current_phase: str
    progress_percent: float = 0.0
    completed_phases: list[str] = Field(default_factory=list)
    pending_phases: list[str] = Field(default_factory=list)
    token_usage: dict[str, Any] = Field(default_factory=dict)
    cost_usd: float = 0.0
    last_checkpoint: CheckpointDTO | None = None


class AgentStatusDTO(BaseModel):
    """Agent status data transfer object."""
    agent_id: str
    status: str
    task_id: str | None = None
    token_usage: dict[str, int] = Field(default_factory=dict)
    artifacts: list[str] = Field(default_factory=list)


class GovernanceResultDTO(BaseModel):
    """Governance result data transfer object."""
    passed: bool
    gate_results: list[dict[str, Any]] = Field(default_factory=list)
    compliance_results: list[dict[str, Any]] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
