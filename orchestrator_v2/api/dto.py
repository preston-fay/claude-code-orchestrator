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


# -----------------------------------------------------------------------------
# User Provider Settings DTOs
# -----------------------------------------------------------------------------

class UpdateProviderSettingsDTO(BaseModel):
    """Request to update LLM provider settings."""
    llm_provider: str  # "anthropic" or "bedrock"
    api_key: str | None = None
    default_model: str | None = None


class ProviderTestResultDTO(BaseModel):
    """Result of a provider connectivity test."""
    success: bool
    provider: str
    model: str | None = None
    message: str


class EventDTO(BaseModel):
    """Event data transfer object."""
    id: str
    event_type: str
    timestamp: datetime
    project_id: str
    phase: str | None = None
    agent_id: str | None = None
    message: str
    data: dict[str, Any] = Field(default_factory=dict)


# -----------------------------------------------------------------------------
# Ready/Set/Go DTOs
# -----------------------------------------------------------------------------

class ReadyStatusDTO(BaseModel):
    """Ready stage status DTO."""
    stage: str
    completed: bool
    current_phase: str | None = None
    completed_phases: list[str] = Field(default_factory=list)
    governance_passed: bool | None = None
    messages: list[str] = Field(default_factory=list)


class SetStatusDTO(BaseModel):
    """Set stage status DTO."""
    stage: str
    completed: bool
    current_phase: str | None = None
    completed_phases: list[str] = Field(default_factory=list)
    artifacts_count: int = 0
    data_ready: bool | None = None
    messages: list[str] = Field(default_factory=list)


class GoStatusDTO(BaseModel):
    """Go stage status DTO."""
    stage: str
    completed: bool
    current_phase: str | None = None
    completed_phases: list[str] = Field(default_factory=list)
    checkpoints_count: int = 0
    governance_blocked: bool = False
    messages: list[str] = Field(default_factory=list)


class RsgOverviewDTO(BaseModel):
    """RSG overview DTO."""
    project_id: str
    project_name: str
    stage: str
    ready: ReadyStatusDTO
    set: SetStatusDTO
    go: GoStatusDTO


# -----------------------------------------------------------------------------
# DTO Conversion Helpers
# -----------------------------------------------------------------------------

def ready_status_to_dto(status) -> ReadyStatusDTO:
    """Convert ReadyStatus to DTO."""
    return ReadyStatusDTO(
        stage=status.stage.value,
        completed=status.completed,
        current_phase=status.current_phase.value if status.current_phase else None,
        completed_phases=[p.value for p in status.completed_phases],
        governance_passed=status.governance_passed,
        messages=status.messages,
    )


def set_status_to_dto(status) -> SetStatusDTO:
    """Convert SetStatus to DTO."""
    return SetStatusDTO(
        stage=status.stage.value,
        completed=status.completed,
        current_phase=status.current_phase.value if status.current_phase else None,
        completed_phases=[p.value for p in status.completed_phases],
        artifacts_count=status.artifacts_count,
        data_ready=status.data_ready,
        messages=status.messages,
    )


def go_status_to_dto(status) -> GoStatusDTO:
    """Convert GoStatus to DTO."""
    return GoStatusDTO(
        stage=status.stage.value,
        completed=status.completed,
        current_phase=status.current_phase.value if status.current_phase else None,
        completed_phases=[p.value for p in status.completed_phases],
        checkpoints_count=status.checkpoints_count,
        governance_blocked=status.governance_blocked,
        messages=status.messages,
    )


def rsg_overview_to_dto(overview) -> RsgOverviewDTO:
    """Convert RsgOverview to DTO."""
    return RsgOverviewDTO(
        project_id=overview.project_id,
        project_name=overview.project_name,
        stage=overview.stage.value,
        ready=ready_status_to_dto(overview.ready),
        set=set_status_to_dto(overview.set),
        go=go_status_to_dto(overview.go),
    )
