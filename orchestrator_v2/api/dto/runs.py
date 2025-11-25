"""
Data Transfer Objects for Orchestrator Runs API.

These DTOs define the data structures for the /runs endpoints
that expose orchestrator execution and artifact management.
"""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class CreateRunRequest(BaseModel):
    """Request to create a new orchestrator run."""
    profile: str = Field(..., description="Profile name (e.g., 'analytics_forecast_app')")
    intake: str | None = Field(None, description="Optional intake text or requirements")
    project_name: str | None = Field(None, description="Optional project name")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class PhaseInfo(BaseModel):
    """Information about a single phase in the workflow."""
    phase: str
    status: str  # "pending", "in_progress", "completed", "failed"
    started_at: datetime | None = None
    completed_at: datetime | None = None
    duration_seconds: float | None = None
    agent_ids: list[str] = Field(default_factory=list)
    artifacts_count: int = 0


class RunSummary(BaseModel):
    """Summary information about an orchestrator run."""
    run_id: str
    profile: str
    project_name: str | None = None
    current_phase: str
    status: str  # "running", "completed", "failed", "paused"
    created_at: datetime
    updated_at: datetime


class RunDetail(BaseModel):
    """Detailed information about an orchestrator run."""
    run_id: str
    profile: str
    intake: str | None = None
    project_name: str | None = None
    current_phase: str
    status: str
    phases: list[PhaseInfo] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime
    completed_at: datetime | None = None
    total_duration_seconds: float | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class ArtifactSummary(BaseModel):
    """Summary of an artifact generated during a phase."""
    artifact_id: str
    phase: str
    path: str
    name: str
    description: str | None = None
    artifact_type: str  # "prd", "architecture", "code", "test", etc.
    size_bytes: int = 0
    created_at: datetime


class ArtifactsResponse(BaseModel):
    """Response containing artifacts grouped by phase."""
    run_id: str
    artifacts_by_phase: dict[str, list[ArtifactSummary]] = Field(default_factory=dict)
    total_count: int = 0


class PhaseMetrics(BaseModel):
    """Metrics for a single phase."""
    phase: str
    duration_seconds: float
    token_usage: dict[str, int] = Field(default_factory=dict)  # {"input": 0, "output": 0}
    cost_usd: float = 0.0
    agents_executed: list[str] = Field(default_factory=list)
    artifacts_generated: int = 0
    governance_passed: bool = True
    governance_warnings: list[str] = Field(default_factory=list)


class MetricsSummary(BaseModel):
    """Comprehensive metrics for an orchestrator run."""
    run_id: str
    total_duration_seconds: float
    total_token_usage: dict[str, int] = Field(default_factory=dict)
    total_cost_usd: float = 0.0
    phases_metrics: list[PhaseMetrics] = Field(default_factory=list)
    governance_score: float = 1.0  # 0.0 to 1.0
    hygiene_score: float = 1.0  # 0.0 to 1.0
    artifacts_total: int = 0
    errors_count: int = 0


class AdvanceRunRequest(BaseModel):
    """Request to advance a run to the next phase."""
    skip_validation: bool = Field(False, description="Skip governance validation")


class AdvanceRunResponse(BaseModel):
    """Response after advancing a run."""
    run_id: str
    previous_phase: str
    current_phase: str
    status: str
    message: str
