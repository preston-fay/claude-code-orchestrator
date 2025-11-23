"""
App Builder Models

Pydantic models for app build state and artifact tracking.
"""

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class AppBuildStatus(str, Enum):
    """Status of the app build process."""
    NOT_STARTED = "not_started"
    PLANNING = "planning"
    SCAFFOLDING = "scaffolding"
    COMPLETED = "completed"
    FAILED = "failed"


class ArtifactInfo(BaseModel):
    """Lightweight artifact reference."""
    id: str
    name: str
    path: str
    artifact_type: str
    created_at: datetime | None = None


class AppBuildState(BaseModel):
    """State of the app build for a project."""
    status: AppBuildStatus = AppBuildStatus.NOT_STARTED
    last_error: str | None = None
    last_run_id: str | None = None
    last_updated_at: datetime | None = None
    artifacts: list[ArtifactInfo] = Field(default_factory=list)

    # Build configuration
    target_stack: str | None = None  # e.g., "react-fastapi", "next-express"
    build_options: dict[str, Any] = Field(default_factory=dict)


class AppBuildPlanRequest(BaseModel):
    """Request to plan an app build."""
    # Optional overrides
    brief_override: str | None = None
    capabilities_override: list[str] | None = None


class AppScaffoldRequest(BaseModel):
    """Request to run app scaffolding."""
    target_stack: str | None = None  # Override project's default stack
    include_tests: bool = True
    include_docs: bool = True


class AppBuildStatusResponse(BaseModel):
    """Response for app build status endpoint."""
    project_id: str
    status: AppBuildStatus
    last_error: str | None
    last_run_id: str | None
    last_updated_at: datetime | None
    artifact_count: int
    target_stack: str | None


class AppBuildArtifactsResponse(BaseModel):
    """Response for app build artifacts endpoint."""
    project_id: str
    artifacts: list[ArtifactInfo]
    total_count: int
