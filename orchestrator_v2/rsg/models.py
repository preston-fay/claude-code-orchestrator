"""
Ready/Set/Code models for Orchestrator v2.

Defines status and overview models for the RSC abstraction layer.
"""

from pydantic import BaseModel, Field

from orchestrator_v2.engine.state_models import PhaseType, RscStage


class ReadyStatus(BaseModel):
    """Status of the Ready stage (PLANNING + ARCHITECTURE)."""
    stage: RscStage
    completed: bool = False
    current_phase: PhaseType | None = None
    completed_phases: list[PhaseType] = Field(default_factory=list)
    governance_passed: bool | None = None
    messages: list[str] = Field(default_factory=list)


class SetStatus(BaseModel):
    """Status of the Set stage (DATA + early DEVELOPMENT)."""
    stage: RscStage
    completed: bool = False
    current_phase: PhaseType | None = None
    completed_phases: list[PhaseType] = Field(default_factory=list)
    artifacts_count: int = 0
    data_ready: bool | None = None
    messages: list[str] = Field(default_factory=list)


class CodeStatus(BaseModel):
    """Status of the Code stage (DEVELOPMENT + QA + DOCUMENTATION)."""
    stage: RscStage
    completed: bool = False
    current_phase: PhaseType | None = None
    completed_phases: list[PhaseType] = Field(default_factory=list)
    checkpoints_count: int = 0
    governance_blocked: bool = False
    messages: list[str] = Field(default_factory=list)


# Backward compatibility alias (deprecated - use CodeStatus)
GoStatus = CodeStatus


class RscOverview(BaseModel):
    """Combined overview of all RSC (Ready/Set/Code) stages."""
    project_id: str
    project_name: str
    stage: RscStage
    ready: ReadyStatus
    set: SetStatus
    code: CodeStatus


# Backward compatibility alias (deprecated - use RscOverview)
RsgOverview = RscOverview


class PhaseAdvanceResult(BaseModel):
    """Result of advancing a single phase.
    
    This model is returned by the advance_phase() method to give
    the user explicit control and feedback after each phase execution.
    """
    phase_executed: PhaseType
    success: bool
    message: str
    error: str | None = None
    current_phase: PhaseType
    completed_phases: list[PhaseType]
    rsc_stage: RscStage
    has_more_phases: bool = True
