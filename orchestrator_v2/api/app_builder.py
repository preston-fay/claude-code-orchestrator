"""
App Builder API router for RSC Orchestrator.

Provides endpoints for planning and executing app builds through the orchestrator.
"""

import uuid
from datetime import datetime
from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from ..capabilities.skills.app_builder import (
    ReactAppScaffolder,
    ReactFeatureGenerator,
    FastAPIScaffolder,
    AppScaffoldInput,
    FeatureGeneratorInput,
    FastAPIScaffoldInput,
)
from ..capabilities.skills.app_builder.models import AppBuildPlan, AppBuildResult
from ..engine.state_models import PhaseType

router = APIRouter(
    prefix="/app-builder",
    tags=["app-builder"],
)


# -----------------------------------------------------------------------------
# Request/Response Models
# -----------------------------------------------------------------------------

class AppBuildPlanRequest(BaseModel):
    """Request for planning an app build."""
    description: str
    app_name: str | None = None
    stack: list[str] = Field(default_factory=lambda: ["react", "fastapi"])
    target_repo_url: str | None = None


class AppBuildPlanResponse(BaseModel):
    """Response from app build planning."""
    plan_id: str
    app_name: str
    prd_summary: str
    architecture_decisions: list[str]
    scaffolding_steps: list[str]
    feature_list: list[str]
    estimated_files: int
    created_at: datetime


class AppBuildRunRequest(BaseModel):
    """Request to run an app build."""
    plan_id: str | None = None  # Use existing plan or create new one
    description: str | None = None  # For ad-hoc builds without plan
    app_name: str | None = None
    output_repo_path: str | None = None
    include_scaffolding: bool = True
    features: list[str] = Field(default_factory=list)  # Features to generate
    api_endpoints: list[dict[str, Any]] = Field(default_factory=list)  # API endpoints to create


class AppBuildRunResponse(BaseModel):
    """Response from app build execution."""
    success: bool
    project_id: str
    plan_id: str
    files_created: list[str]
    files_modified: list[str]
    phases_completed: list[str]
    commit_messages: list[str]
    documentation: str
    errors: list[str]


class AppBuildOutputsResponse(BaseModel):
    """Response containing all build outputs."""
    project_id: str
    plan: AppBuildPlan | None
    prd_content: str | None
    adrs: list[dict[str, str]]
    files_summary: dict[str, list[str]]
    test_results: dict[str, Any]
    documentation: str


class ScaffoldRequest(BaseModel):
    """Request to scaffold an app."""
    app_name: str
    style: str = "kearney"
    include_api_client: bool = True
    api_base_url: str = "http://localhost:8000"
    initial_pages: list[str] = Field(default_factory=lambda: ["Home", "Settings"])


class FeatureRequest(BaseModel):
    """Request to generate a feature."""
    feature_description: str
    target_route: str | None = None
    component_name: str | None = None
    include_tests: bool = True


class EndpointRequest(BaseModel):
    """Request to generate an API endpoint."""
    endpoint_name: str
    resource_model: dict[str, Any] = Field(default_factory=dict)
    summary: str = ""
    methods: list[str] = Field(default_factory=lambda: ["GET", "POST"])


# -----------------------------------------------------------------------------
# In-memory storage (replace with persistence in production)
# -----------------------------------------------------------------------------

_plans: dict[str, AppBuildPlan] = {}
_results: dict[str, AppBuildResult] = {}


# -----------------------------------------------------------------------------
# Endpoints
# -----------------------------------------------------------------------------

@router.post("/{project_id}/plan", response_model=AppBuildPlanResponse)
async def plan_app_build(
    project_id: str,
    request: AppBuildPlanRequest,
) -> AppBuildPlanResponse:
    """
    Plan an app build for a project.

    This endpoint generates a PRD and architecture plan based on the description.
    The plan can then be executed with the /run endpoint.
    """
    plan_id = f"plan-{uuid.uuid4().hex[:8]}"

    # Derive app name from description if not provided
    app_name = request.app_name or _derive_app_name(request.description)

    # Generate PRD summary (in production, this would use an LLM)
    prd_summary = f"""
## Product Requirements Document

### Overview
{request.description}

### Application Name
{app_name}

### Technology Stack
- Frontend: React + Vite + TypeScript
- Backend: FastAPI + Pydantic
- Styling: Kearney Design System

### Key Features
Based on the description, the following features are identified for implementation.
"""

    # Generate architecture decisions
    architecture_decisions = [
        f"ADR-001: Use React with TypeScript for type safety",
        f"ADR-002: Use FastAPI for performant async API",
        f"ADR-003: Apply Kearney Design System for brand compliance",
        f"ADR-004: Structure code for maintainability and testing",
    ]

    # Generate scaffolding steps
    scaffolding_steps = [
        "Create React project structure with Vite",
        "Set up TypeScript configuration",
        "Create KDS stylesheet and theme",
        "Set up routing with React Router",
        "Create API client with Axios",
        "Create initial page components",
    ]

    if "fastapi" in request.stack:
        scaffolding_steps.extend([
            "Create FastAPI project structure",
            "Set up Pydantic models",
            "Create API routers",
            "Configure CORS middleware",
        ])

    # Extract features from description
    feature_list = _extract_features(request.description)

    # Estimate files
    estimated_files = 15 + (len(feature_list) * 3)  # Base + 3 files per feature

    # Create plan
    plan = AppBuildPlan(
        plan_id=plan_id,
        app_name=app_name,
        description=request.description,
        prd_summary=prd_summary,
        architecture_decisions=architecture_decisions,
        scaffolding_steps=scaffolding_steps,
        feature_list=feature_list,
        estimated_files=estimated_files,
        stack=request.stack,
    )

    # Store plan
    _plans[plan_id] = plan

    return AppBuildPlanResponse(
        plan_id=plan_id,
        app_name=app_name,
        prd_summary=prd_summary,
        architecture_decisions=architecture_decisions,
        scaffolding_steps=scaffolding_steps,
        feature_list=feature_list,
        estimated_files=estimated_files,
        created_at=datetime.utcnow(),
    )


@router.post("/{project_id}/run", response_model=AppBuildRunResponse)
async def run_app_build(
    project_id: str,
    request: AppBuildRunRequest,
) -> AppBuildRunResponse:
    """
    Execute an app build for a project.

    This runs through the APP_BUILD phases:
    PLANNING -> ARCHITECTURE -> SCAFFOLDING -> DEVELOPMENT -> QA -> DOCUMENTATION
    """
    # Get or create plan
    plan_id = request.plan_id
    if plan_id and plan_id in _plans:
        plan = _plans[plan_id]
    else:
        # Create ad-hoc plan
        plan_id = f"plan-{uuid.uuid4().hex[:8]}"
        app_name = request.app_name or "MyApp"
        plan = AppBuildPlan(
            plan_id=plan_id,
            app_name=app_name,
            description=request.description or "Ad-hoc app build",
            feature_list=request.features,
            estimated_files=20,
        )
        _plans[plan_id] = plan

    # Determine output path
    output_path = request.output_repo_path
    if not output_path:
        output_path = f"/tmp/rsc-builds/{project_id}/{plan.app_name.lower().replace(' ', '-')}"

    repo_path = Path(output_path)
    repo_path.mkdir(parents=True, exist_ok=True)

    files_created: list[str] = []
    files_modified: list[str] = []
    commit_messages: list[str] = []
    errors: list[str] = []
    phases_completed: list[str] = []

    # Phase 1: PLANNING (already done)
    phases_completed.append(PhaseType.PLANNING.value)

    # Phase 2: ARCHITECTURE (already done via plan)
    phases_completed.append(PhaseType.ARCHITECTURE.value)

    # Phase 3: SCAFFOLDING
    if request.include_scaffolding:
        scaffolder = ReactAppScaffolder()
        scaffold_result = scaffolder.execute(AppScaffoldInput(
            repo_path=str(repo_path),
            app_name=plan.app_name,
            style="kearney",
            initial_pages=["Home", "Settings"],
        ))

        if scaffold_result.success:
            files_created.extend(scaffold_result.files_created)
            commit_messages.append(scaffold_result.commit_message)
        else:
            errors.extend(scaffold_result.errors)

        phases_completed.append(PhaseType.SCAFFOLDING.value)

    # Phase 4: DEVELOPMENT (features)
    feature_gen = ReactFeatureGenerator()
    for feature_desc in plan.feature_list:
        if feature_desc in ["Home", "Settings"]:
            continue  # Already created in scaffolding

        result = feature_gen.execute(FeatureGeneratorInput(
            repo_path=str(repo_path),
            feature_description=feature_desc,
            include_tests=True,
        ))

        if result.success:
            files_created.extend(result.files_created)
            files_modified.extend(result.files_modified)
            commit_messages.append(result.commit_message)
        else:
            errors.extend(result.errors)

    # Create API endpoints if requested
    if request.api_endpoints:
        api_scaffolder = FastAPIScaffolder()
        for endpoint in request.api_endpoints:
            result = api_scaffolder.execute(FastAPIScaffoldInput(
                repo_path=str(repo_path),
                endpoint_name=endpoint.get("name", "items"),
                resource_model=endpoint.get("model", {}),
                summary=endpoint.get("summary", ""),
                methods=endpoint.get("methods", ["GET", "POST"]),
            ))

            if result.success:
                files_created.extend(result.files_created)
                commit_messages.append(result.commit_message)
            else:
                errors.extend(result.errors)

    phases_completed.append(PhaseType.DEVELOPMENT.value)

    # Phase 5: QA (placeholder - in production would run tests)
    phases_completed.append(PhaseType.QA.value)

    # Phase 6: DOCUMENTATION
    documentation = f"""# {plan.app_name}

{plan.description}

## Getting Started

### Frontend

```bash
cd {output_path}
npm install
npm run dev
```

### Backend (if included)

```bash
cd {output_path}/api
pip install -r requirements.txt
uvicorn main:app --reload
```

## Features

{chr(10).join(f'- {f}' for f in plan.feature_list)}

## Architecture Decisions

{chr(10).join(f'- {adr}' for adr in plan.architecture_decisions)}

---
*Built with RSC App Builder*
"""

    # Write README
    readme_path = repo_path / "README.md"
    readme_path.write_text(documentation)
    files_created.append("README.md")

    phases_completed.append(PhaseType.DOCUMENTATION.value)

    # Store result
    result = AppBuildResult(
        success=len(errors) == 0,
        plan=plan,
        total_files_created=len(files_created),
        documentation=documentation,
        errors=errors,
    )
    _results[project_id] = result

    return AppBuildRunResponse(
        success=len(errors) == 0,
        project_id=project_id,
        plan_id=plan_id,
        files_created=files_created,
        files_modified=files_modified,
        phases_completed=phases_completed,
        commit_messages=commit_messages,
        documentation=documentation,
        errors=errors,
    )


@router.get("/{project_id}/outputs", response_model=AppBuildOutputsResponse)
async def get_build_outputs(
    project_id: str,
) -> AppBuildOutputsResponse:
    """
    Get all outputs from an app build.

    Returns the PRD, ADRs, file summary, test results, and documentation.
    """
    result = _results.get(project_id)
    if not result:
        raise HTTPException(status_code=404, detail="Build outputs not found")

    plan = result.plan

    return AppBuildOutputsResponse(
        project_id=project_id,
        plan=plan,
        prd_content=plan.prd_summary if plan else None,
        adrs=[
            {"id": f"ADR-{i+1:03d}", "decision": adr}
            for i, adr in enumerate(plan.architecture_decisions if plan else [])
        ],
        files_summary={
            "created": [f for f in (result.scaffold_output.files_created if result.scaffold_output else [])],
            "features": [
                f for out in result.feature_outputs for f in out.files_created
            ],
        },
        test_results=result.test_results,
        documentation=result.documentation,
    )


@router.post("/{project_id}/scaffold")
async def scaffold_app(
    project_id: str,
    request: ScaffoldRequest,
):
    """Scaffold a new React application."""
    # Get workspace path from project (placeholder)
    output_path = f"/tmp/rsc-builds/{project_id}/{request.app_name.lower().replace(' ', '-')}"
    repo_path = Path(output_path)
    repo_path.mkdir(parents=True, exist_ok=True)

    scaffolder = ReactAppScaffolder()
    result = scaffolder.execute(AppScaffoldInput(
        repo_path=str(repo_path),
        app_name=request.app_name,
        style=request.style,
        include_api_client=request.include_api_client,
        api_base_url=request.api_base_url,
        initial_pages=request.initial_pages,
    ))

    return {
        "success": result.success,
        "files_created": result.files_created,
        "structure_summary": result.structure_summary,
        "commit_message": result.commit_message,
        "output_path": str(repo_path),
        "errors": result.errors,
    }


@router.post("/{project_id}/feature")
async def add_feature(
    project_id: str,
    request: FeatureRequest,
):
    """Add a feature to an existing app."""
    # Get workspace path from project (placeholder)
    output_path = f"/tmp/rsc-builds/{project_id}"

    # Find the app directory
    repo_path = Path(output_path)
    if not repo_path.exists():
        raise HTTPException(status_code=404, detail="Project app not found. Run scaffold first.")

    # Find first subdirectory (the app)
    app_dirs = [d for d in repo_path.iterdir() if d.is_dir()]
    if not app_dirs:
        raise HTTPException(status_code=404, detail="No app found in project")

    app_path = app_dirs[0]

    generator = ReactFeatureGenerator()
    result = generator.execute(FeatureGeneratorInput(
        repo_path=str(app_path),
        feature_description=request.feature_description,
        target_route=request.target_route,
        component_name=request.component_name,
        include_tests=request.include_tests,
    ))

    return {
        "success": result.success,
        "component_name": result.component_name,
        "route_path": result.route_path,
        "files_created": result.files_created,
        "files_modified": result.files_modified,
        "commit_message": result.commit_message,
        "errors": result.errors,
    }


@router.post("/{project_id}/endpoint")
async def add_endpoint(
    project_id: str,
    request: EndpointRequest,
):
    """Add a FastAPI endpoint to an existing app."""
    # Get workspace path from project (placeholder)
    output_path = f"/tmp/rsc-builds/{project_id}"

    repo_path = Path(output_path)
    if not repo_path.exists():
        raise HTTPException(status_code=404, detail="Project app not found")

    app_dirs = [d for d in repo_path.iterdir() if d.is_dir()]
    if not app_dirs:
        raise HTTPException(status_code=404, detail="No app found in project")

    app_path = app_dirs[0]

    scaffolder = FastAPIScaffolder()
    result = scaffolder.execute(FastAPIScaffoldInput(
        repo_path=str(app_path),
        endpoint_name=request.endpoint_name,
        resource_model=request.resource_model,
        summary=request.summary,
        methods=request.methods,
    ))

    return {
        "success": result.success,
        "endpoint_paths": result.endpoint_paths,
        "files_created": result.files_created,
        "router_registered": result.router_registered,
        "commit_message": result.commit_message,
        "errors": result.errors,
    }


# -----------------------------------------------------------------------------
# Helper Functions
# -----------------------------------------------------------------------------

def _derive_app_name(description: str) -> str:
    """Derive an app name from description."""
    # Extract key nouns from description
    words = description.split()

    # Look for common patterns
    for i, word in enumerate(words):
        if word.lower() in ["build", "create", "make"]:
            # Take next 1-2 words as name
            name_words = words[i+1:i+3]
            return " ".join(w.capitalize() for w in name_words if w.lower() not in ["a", "an", "the"])

    # Fallback: first few significant words
    stop_words = {"a", "an", "the", "for", "to", "with", "and", "or"}
    significant = [w for w in words[:5] if w.lower() not in stop_words]
    return " ".join(w.capitalize() for w in significant[:2]) or "MyApp"


def _extract_features(description: str) -> list[str]:
    """Extract feature list from description."""
    features = ["Home", "Settings"]  # Always include these

    # Look for feature-indicating words
    keywords = {
        "map": "Map View",
        "chart": "Charts Dashboard",
        "scenario": "Scenario Manager",
        "report": "Reports",
        "dashboard": "Dashboard",
        "analytics": "Analytics",
        "settings": "Settings",
        "profile": "User Profile",
        "admin": "Admin Panel",
        "data": "Data Explorer",
        "upload": "File Upload",
        "export": "Export",
    }

    description_lower = description.lower()
    for keyword, feature in keywords.items():
        if keyword in description_lower and feature not in features:
            features.append(feature)

    return features
