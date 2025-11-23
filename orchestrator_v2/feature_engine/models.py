"""
Feature Engine Models

Pydantic models for feature requests and tracking.
"""

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class FeatureStatus(str, Enum):
    """Status of a feature request."""
    SUBMITTED = "submitted"
    PLANNED = "planned"
    BUILDING = "building"
    COMPLETED = "completed"
    FAILED = "failed"


class ArtifactInfo(BaseModel):
    """Lightweight artifact reference."""
    id: str
    name: str
    path: str
    artifact_type: str
    created_at: datetime | None = None


class FeatureRequest(BaseModel):
    """A feature request within a project."""
    feature_id: str
    title: str
    description: str
    status: FeatureStatus = FeatureStatus.SUBMITTED
    created_at: datetime
    updated_at: datetime
    artifacts: list[ArtifactInfo] = Field(default_factory=list)
    plan_summary: str | None = None
    build_summary: str | None = None

    # Optional metadata
    priority: str = "medium"  # low, medium, high, critical
    tags: list[str] = Field(default_factory=list)
    dependencies: list[str] = Field(default_factory=list)  # Other feature IDs


class CreateFeatureRequest(BaseModel):
    """Request to create a new feature."""
    title: str
    description: str = ""
    priority: str = "medium"
    tags: list[str] = Field(default_factory=list)


class FeatureDTO(BaseModel):
    """Feature data transfer object for API responses."""
    feature_id: str
    title: str
    description: str
    status: str
    created_at: datetime
    updated_at: datetime
    artifact_count: int
    plan_summary: str | None
    build_summary: str | None
    priority: str
    tags: list[str]


class FeatureListResponse(BaseModel):
    """Response for listing features."""
    project_id: str
    features: list[FeatureDTO]
    total_count: int


class FeatureOperationResult(BaseModel):
    """Result of a feature operation (plan/build)."""
    feature_id: str
    status: str
    artifacts: list[dict[str, Any]]
    summary: str
    token_usage: dict[str, Any] = Field(default_factory=dict)
