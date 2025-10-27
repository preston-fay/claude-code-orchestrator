"""
Pydantic schemas for Model Registry and Dataset Catalog.

Defines validation models for:
- Model entries with metrics and artifacts
- Dataset entries with schema and row counts
- Registry manifests
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, Dict, Any, List, Literal
from datetime import datetime
import re


class ModelEntry(BaseModel):
    """Model registry entry."""

    id: str = Field(..., description="Unique identifier (UUID)")
    name: str = Field(..., pattern=r"^[a-z0-9_-]+$", description="Model name (lowercase, hyphens/underscores)")
    version: str = Field(..., pattern=r"^\d+\.\d+\.\d+$", description="Semantic version (e.g., 1.0.0)")
    type: Literal["model"] = Field(default="model", description="Entry type")
    created_at: str = Field(..., description="ISO8601 timestamp")
    sha256: str = Field(..., pattern=r"^[a-f0-9]{64}$", description="SHA256 hash of primary artifact")
    metrics: Dict[str, float] = Field(default_factory=dict, description="Model metrics (e.g., rmse, r2)")
    artifacts: List[str] = Field(..., description="Paths to model artifacts")
    cleanliness_score: Optional[int] = Field(None, ge=0, le=100, description="Data cleanliness score")
    release_tag: Optional[str] = Field(None, pattern=r"^v\d+\.\d+\.\d+$", description="Release tag (e.g., v1.0.0)")
    client: Optional[str] = Field(None, pattern=r"^[a-z0-9-]+$", description="Client slug")
    notes: Optional[str] = Field(None, max_length=500, description="Release notes")

    @validator("created_at")
    def validate_iso8601(cls, v):
        """Validate ISO8601 timestamp format."""
        try:
            datetime.fromisoformat(v.replace("Z", "+00:00"))
        except ValueError:
            raise ValueError(f"Invalid ISO8601 timestamp: {v}")
        return v

    @validator("artifacts")
    def validate_artifacts_not_empty(cls, v):
        """Ensure at least one artifact."""
        if not v:
            raise ValueError("At least one artifact required")
        return v


class DatasetEntry(BaseModel):
    """Dataset catalog entry."""

    id: str = Field(..., description="Unique identifier (UUID)")
    name: str = Field(..., pattern=r"^[a-z0-9_-]+$", description="Dataset name (lowercase, hyphens/underscores)")
    version: str = Field(..., pattern=r"^\d+\.\d+\.\d+$", description="Semantic version (e.g., 1.0.0)")
    type: Literal["dataset"] = Field(default="dataset", description="Entry type")
    created_at: str = Field(..., description="ISO8601 timestamp")
    sha256: str = Field(..., pattern=r"^[a-f0-9]{64}$", description="SHA256 hash of dataset file")
    row_count: int = Field(..., ge=0, description="Number of rows in dataset")
    schema_hash: str = Field(..., pattern=r"^[a-f0-9]{64}$", description="SHA256 hash of schema")
    artifacts: List[str] = Field(..., description="Paths to dataset files")
    cleanliness_score: Optional[int] = Field(None, ge=0, le=100, description="Data cleanliness score")
    release_tag: Optional[str] = Field(None, pattern=r"^v\d+\.\d+\.\d+$", description="Release tag (e.g., v1.0.0)")
    client: Optional[str] = Field(None, pattern=r"^[a-z0-9-]+$", description="Client slug")
    notes: Optional[str] = Field(None, max_length=500, description="Dataset description")

    @validator("created_at")
    def validate_iso8601(cls, v):
        """Validate ISO8601 timestamp format."""
        try:
            datetime.fromisoformat(v.replace("Z", "+00:00"))
        except ValueError:
            raise ValueError(f"Invalid ISO8601 timestamp: {v}")
        return v


class ModelRegistry(BaseModel):
    """Model registry manifest."""

    schema_: str = Field("https://json-schema.org/draft-07/schema#", alias="$schema")
    version: str = Field("1.0.0", description="Registry version")
    updated_at: str = Field(..., description="Last update timestamp")
    models: List[ModelEntry] = Field(default_factory=list, description="Registered models")

    class Config:
        populate_by_name = True


class DatasetCatalog(BaseModel):
    """Dataset catalog manifest."""

    schema_: str = Field("https://json-schema.org/draft-07/schema#", alias="$schema")
    version: str = Field("1.0.0", description="Catalog version")
    updated_at: str = Field(..., description="Last update timestamp")
    datasets: List[DatasetEntry] = Field(default_factory=list, description="Registered datasets")

    class Config:
        populate_by_name = True


class PublishModelRequest(BaseModel):
    """Request to publish a model."""

    name: str = Field(..., pattern=r"^[a-z0-9_-]+$")
    version: str = Field(..., pattern=r"^\d+\.\d+\.\d+$")
    artifacts: List[str]
    metrics: Optional[Dict[str, float]] = None
    client: Optional[str] = None
    notes: Optional[str] = None


class RegisterDatasetRequest(BaseModel):
    """Request to register a dataset."""

    name: str = Field(..., pattern=r"^[a-z0-9_-]+$")
    version: str = Field(..., pattern=r"^\d+\.\d+\.\d+$")
    artifacts: List[str]
    row_count: int = Field(..., ge=0)
    client: Optional[str] = None
    notes: Optional[str] = None
