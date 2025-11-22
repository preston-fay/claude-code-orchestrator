"""
Data models for App Builder skills.

Defines input/output schemas for React and FastAPI scaffolding operations.
"""

from typing import Any
from pydantic import BaseModel, Field


class AppScaffoldInput(BaseModel):
    """Input for React app scaffolding."""
    repo_path: str  # Local workspace path for the app
    app_name: str
    style: str = "kearney"  # kearney | minimal | custom
    include_routing: bool = True
    include_api_client: bool = True
    api_base_url: str = "http://localhost:8000"
    initial_pages: list[str] = Field(default_factory=lambda: ["Home", "Settings"])


class AppScaffoldOutput(BaseModel):
    """Output from React app scaffolding."""
    success: bool = True
    files_created: list[str] = Field(default_factory=list)
    structure_summary: str = ""
    commit_message: str = ""
    errors: list[str] = Field(default_factory=list)


class FeatureGeneratorInput(BaseModel):
    """Input for generating a React feature/page."""
    repo_path: str  # Local workspace path for the app
    feature_description: str
    target_route: str | None = None  # e.g., "/map", "/scenario"
    component_name: str | None = None  # Auto-generated if not provided
    include_tests: bool = True
    include_state: bool = False  # Add local state management


class FeatureGeneratorOutput(BaseModel):
    """Output from React feature generation."""
    success: bool = True
    files_created: list[str] = Field(default_factory=list)
    files_modified: list[str] = Field(default_factory=list)
    component_name: str = ""
    route_path: str = ""
    commit_message: str = ""
    errors: list[str] = Field(default_factory=list)


class FastAPIScaffoldInput(BaseModel):
    """Input for FastAPI endpoint scaffolding."""
    repo_path: str  # Local workspace path for the app
    endpoint_name: str  # e.g., "territories"
    resource_model: dict[str, Any] = Field(default_factory=dict)  # Pydantic model fields
    summary: str = ""
    methods: list[str] = Field(default_factory=lambda: ["GET", "POST"])
    include_tests: bool = True


class FastAPIScaffoldOutput(BaseModel):
    """Output from FastAPI scaffolding."""
    success: bool = True
    files_created: list[str] = Field(default_factory=list)
    router_registered: bool = False
    endpoint_paths: list[str] = Field(default_factory=list)
    commit_message: str = ""
    errors: list[str] = Field(default_factory=list)


class AppBuildPlan(BaseModel):
    """Plan for building an application."""
    plan_id: str
    app_name: str
    description: str
    prd_summary: str = ""
    architecture_decisions: list[str] = Field(default_factory=list)
    scaffolding_steps: list[str] = Field(default_factory=list)
    feature_list: list[str] = Field(default_factory=list)
    estimated_files: int = 0
    stack: list[str] = Field(default_factory=lambda: ["react", "fastapi"])


class AppBuildResult(BaseModel):
    """Result of an app build operation."""
    success: bool = True
    plan: AppBuildPlan | None = None
    scaffold_output: AppScaffoldOutput | None = None
    feature_outputs: list[FeatureGeneratorOutput] = Field(default_factory=list)
    api_outputs: list[FastAPIScaffoldOutput] = Field(default_factory=list)
    documentation: str = ""
    test_results: dict[str, Any] = Field(default_factory=dict)
    total_files_created: int = 0
    errors: list[str] = Field(default_factory=list)
