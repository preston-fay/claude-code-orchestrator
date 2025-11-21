"""
Ready/Set/Go models for Orchestrator v2.

Defines status and overview models for the RSG abstraction layer.
"""

from pydantic import BaseModel, Field

from orchestrator_v2.core.state_models import PhaseType, RsgStage


class ReadyStatus(BaseModel):
    """Status of the Ready stage (PLANNING + ARCHITECTURE)."""
    stage: RsgStage
    completed: bool = False
    current_phase: PhaseType | None = None
    completed_phases: list[PhaseType] = Field(default_factory=list)
    governance_passed: bool | None = None
    messages: list[str] = Field(default_factory=list)


class SetStatus(BaseModel):
    """Status of the Set stage (DATA + early DEVELOPMENT)."""
    stage: RsgStage
    completed: bool = False
    current_phase: PhaseType | None = None
    completed_phases: list[PhaseType] = Field(default_factory=list)
    artifacts_count: int = 0
    data_ready: bool | None = None
    messages: list[str] = Field(default_factory=list)


class GoStatus(BaseModel):
    """Status of the Go stage (DEVELOPMENT + QA + DOCUMENTATION)."""
    stage: RsgStage
    completed: bool = False
    current_phase: PhaseType | None = None
    completed_phases: list[PhaseType] = Field(default_factory=list)
    checkpoints_count: int = 0
    governance_blocked: bool = False
    messages: list[str] = Field(default_factory=list)


class RsgOverview(BaseModel):
    """Combined overview of all RSG stages."""
    project_id: str
    project_name: str
    stage: RsgStage
    ready: ReadyStatus
    set: SetStatus
    go: GoStatus
