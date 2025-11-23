"""
FastAPI HTTP server for Orchestrator v2.

Provides REST API endpoints for orchestrator operations.

See ADR-002 for API design.
"""

from datetime import datetime
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from orchestrator_v2.api.dto import (
    CheckpointDTO,
    EventDTO,
    GovernanceResultDTO,
    GoStatusDTO,
    PhaseDTO,
    ProjectDTO,
    ProjectTemplateDTO,
    ProviderTestResultDTO,
    ReadyStatusDTO,
    RsgOverviewDTO,
    SetStatusDTO,
    StatusDTO,
    UpdateProviderSettingsDTO,
    go_status_to_dto,
    ready_status_to_dto,
    rsg_overview_to_dto,
    set_status_to_dto,
)
from orchestrator_v2.config.templates import (
    TEMPLATES,
    get_template_by_id,
)
from orchestrator_v2.telemetry.events_repository import get_event_repository
from orchestrator_v2.rsg.service import RsgService, RsgServiceError
from orchestrator_v2.workspace.manager import WorkspaceManager
from orchestrator_v2.engine.engine import WorkflowEngine
from orchestrator_v2.engine.state_models import (
    CheckpointType,
    GateStatus,
    PhaseType,
    ProjectState,
    get_phases_for_capabilities,
)
from orchestrator_v2.planning import get_planning_service
from orchestrator_v2.phases import get_execution_service
from orchestrator_v2.persistence.fs_repository import (
    FileSystemArtifactRepository,
    FileSystemCheckpointRepository,
    FileSystemGovernanceLogRepository,
    FileSystemProjectRepository,
)
from orchestrator_v2.auth.dependencies import (
    get_current_user,
    get_user_repository,
    require_role,
    require_admin,
)
from orchestrator_v2.user.models import (
    UserProfile,
    UserPublicProfile,
    UserRole,
    ApiKeyUpdate,
    UserProfileUpdate,
    to_public_profile,
)


# Request/Response models
class CreateProjectRequest(BaseModel):
    """Request to create a new project."""
    project_name: str
    client: str = "kearney-default"
    project_type: str = "generic"
    template_id: str | None = None
    description: str | None = None
    brief: str | None = None
    capabilities: list[str] = Field(default_factory=list)
    app_repo_url: str | None = None
    app_url: str | None = None
    intake_path: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class ChatRequest(BaseModel):
    """Request for project chat/console."""
    message: str
    model_override: str | None = None


class ChatResponse(BaseModel):
    """Response from project chat."""
    reply: str
    model: str
    tokens: dict[str, int]
    agent: str = "chat"


class ArtifactDTO(BaseModel):
    """Artifact information."""
    id: str
    name: str
    path: str
    artifact_type: str
    phase: str
    size_bytes: int
    created_at: datetime | None = None


class ArtifactsResponse(BaseModel):
    """Response containing artifacts grouped by phase."""
    project_id: str
    artifacts_by_phase: dict[str, list[ArtifactDTO]]
    total_count: int


class ArtifactContentResponse(BaseModel):
    """Response with full artifact content and metadata."""
    id: str
    name: str
    phase: str
    path: str
    artifact_type: str
    content: str
    metadata: dict[str, Any]


class DiagnosticsDTO(BaseModel):
    """Phase diagnostics data."""
    phase: str
    agents: list[str] = Field(default_factory=list)
    skills: list[str] = Field(default_factory=list)
    artifacts: list[str] = Field(default_factory=list)
    governance: dict[str, Any] = Field(default_factory=dict)
    token_usage: dict[str, int] = Field(default_factory=dict)
    timestamp: str | None = None
    errors: list[str] = Field(default_factory=list)


class HealthResponse(BaseModel):
    """Health check response."""
    status: str = "healthy"
    timestamp: str
    version: str = "2.0.0"


class ErrorResponse(BaseModel):
    """Error response."""
    error: str
    detail: str | None = None


# Initialize repositories
project_repo = FileSystemProjectRepository()
checkpoint_repo = FileSystemCheckpointRepository()
artifact_repo = FileSystemArtifactRepository()
governance_repo = FileSystemGovernanceLogRepository()

# Initialize workspace manager and RSG service
workspace_manager = WorkspaceManager()
rsg_service = RsgService(
    project_repository=project_repo,
    checkpoint_repository=checkpoint_repo,
    artifact_repository=artifact_repo,
    workspace_manager=workspace_manager,
)

# Track active engines per project
_engines: dict[str, WorkflowEngine] = {}


def get_engine(project_id: str) -> WorkflowEngine:
    """Get or create workflow engine for project."""
    if project_id not in _engines:
        _engines[project_id] = WorkflowEngine()
    return _engines[project_id]


# Create FastAPI app
app = FastAPI(
    title="RSC API",
    description="Ready-Set-Code (RSC) Engine API – multi-agent orchestration platform",
    version="2.0.0",
)

# Configure CORS for development
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:3001",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    return HealthResponse(
        status="healthy",
        timestamp=datetime.utcnow().isoformat(),
    )


# -----------------------------------------------------------------------------
# User Management Endpoints
# -----------------------------------------------------------------------------

@app.get("/users/me", response_model=UserPublicProfile)
async def get_current_user_profile(user: UserProfile = Depends(get_current_user)):
    """Get current user's profile with sanitized API key."""
    return to_public_profile(user)


# Keep /me as alias for backward compatibility
@app.get("/me")
async def get_me_legacy(user: UserProfile = Depends(get_current_user)):
    """Get current user's profile (legacy endpoint)."""
    return to_public_profile(user)


@app.post("/users/me/provider-settings", response_model=UserPublicProfile)
async def update_provider_settings(
    payload: UpdateProviderSettingsDTO,
    user: UserProfile = Depends(get_current_user),
):
    """Update LLM provider settings for current user."""
    # Validate provider
    if payload.llm_provider not in ("anthropic", "bedrock"):
        raise HTTPException(status_code=400, detail="Unsupported provider. Use 'anthropic' or 'bedrock'.")

    user.llm_provider = payload.llm_provider

    # Only store api_key if provider == anthropic
    if payload.llm_provider == "anthropic" and payload.api_key:
        user.llm_api_key = payload.api_key

    if payload.default_model:
        user.default_model = payload.default_model

    user.updated_at = datetime.utcnow()

    # Save user
    user_repo = get_user_repository()
    await user_repo.save(user)

    return to_public_profile(user)


@app.post("/users/me/provider-test", response_model=ProviderTestResultDTO)
async def test_provider(
    payload: UpdateProviderSettingsDTO | None = None,
    user: UserProfile = Depends(get_current_user),
):
    """
    Test if current (or proposed) provider settings work.

    If payload provided, test against those values without persisting them.
    """
    from orchestrator_v2.llm import get_provider_registry
    from orchestrator_v2.engine.state_models import AgentContext, TaskDefinition, ProjectState

    provider_name = payload.llm_provider if payload and payload.llm_provider else user.llm_provider
    temp_api_key = payload.api_key if (payload and payload.api_key) else user.llm_api_key
    model = payload.default_model if (payload and payload.default_model) else user.default_model

    registry = get_provider_registry()

    # Create a minimal context for testing
    context = AgentContext(
        project_state=ProjectState(
            project_id="test",
            run_id="test",
            project_name="Test",
        ),
        task=TaskDefinition(
            task_id="test",
            description="Provider test",
        ),
        user_id=user.user_id,
        llm_api_key=temp_api_key,
        llm_provider=provider_name,
        model=model,
    )

    test_prompt = "You are a health check. Reply with exactly: READY-SET-CODE-OK"

    try:
        result = await registry.generate(
            prompt=test_prompt,
            model=model,
            context=context,
        )
        ok = "READY-SET-CODE-OK" in result.text
        return ProviderTestResultDTO(
            success=ok,
            provider=provider_name,
            model=model,
            message="LLM provider responded successfully" if ok else "Provider responded but did not echo sentinel text",
        )
    except Exception as e:
        return ProviderTestResultDTO(
            success=False,
            provider=provider_name,
            model=model,
            message=f"Error testing provider: {str(e)}",
        )


@app.get("/users")
async def list_users(user: UserProfile = Depends(require_role(UserRole.ADMIN))):
    """List all users (admin only)."""
    user_repo = get_user_repository()
    users = await user_repo.list_users()

    # Mask API keys
    result = []
    for u in users:
        u_dict = u.model_dump()
        if u_dict.get("llm_api_key"):
            u_dict["llm_api_key"] = "***" + u_dict["llm_api_key"][-4:] if len(u_dict["llm_api_key"]) > 4 else "***"
        result.append(u_dict)

    return result


@app.get("/users/{user_id}")
async def get_user(
    user_id: str,
    current_user: UserProfile = Depends(get_current_user)
):
    """Get user profile by ID."""
    # Users can only view their own profile unless admin
    if current_user.user_id != user_id and current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Not authorized to view other users")

    user_repo = get_user_repository()
    user = await user_repo.get_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail=f"User not found: {user_id}")

    # Mask API key
    user_dict = user.model_dump()
    if user_dict.get("llm_api_key"):
        user_dict["llm_api_key"] = "***" + user_dict["llm_api_key"][-4:] if len(user_dict["llm_api_key"]) > 4 else "***"

    return user_dict


@app.post("/users/{user_id}/key")
async def set_user_api_key(
    user_id: str,
    key_update: ApiKeyUpdate,
    current_user: UserProfile = Depends(get_current_user)
):
    """Set BYOK LLM API key for a user."""
    # Users can only set their own key unless admin
    if current_user.user_id != user_id and current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Not authorized to modify other users")

    user_repo = get_user_repository()
    user = await user_repo.get_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail=f"User not found: {user_id}")

    user.llm_api_key = key_update.api_key
    user.llm_provider = key_update.provider
    await user_repo.save(user)

    return {"status": "updated", "user_id": user_id, "provider": key_update.provider}


@app.post("/users/{user_id}/entitlements")
async def set_user_entitlements(
    user_id: str,
    entitlements: dict[str, list[str]],
    current_user: UserProfile = Depends(require_role(UserRole.ADMIN))
):
    """Set model entitlements for a user (admin only)."""
    user_repo = get_user_repository()
    user = await user_repo.get_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail=f"User not found: {user_id}")

    user.model_entitlements = entitlements
    await user_repo.save(user)

    return {"status": "updated", "user_id": user_id, "entitlements": entitlements}


@app.post("/users/{user_id}/projects/{project_id}/grant")
async def grant_project_access(
    user_id: str,
    project_id: str,
    current_user: UserProfile = Depends(require_role(UserRole.ADMIN))
):
    """Grant user access to a project (admin only)."""
    user_repo = get_user_repository()
    success = await user_repo.grant_project_access(user_id, project_id)
    if not success:
        raise HTTPException(status_code=404, detail=f"User not found: {user_id}")

    return {"status": "granted", "user_id": user_id, "project_id": project_id}


@app.delete("/users/{user_id}/projects/{project_id}/revoke")
async def revoke_project_access(
    user_id: str,
    project_id: str,
    current_user: UserProfile = Depends(require_role(UserRole.ADMIN))
):
    """Revoke user access to a project (admin only)."""
    user_repo = get_user_repository()
    success = await user_repo.revoke_project_access(user_id, project_id)
    if not success:
        raise HTTPException(status_code=404, detail=f"User not found: {user_id}")

    return {"status": "revoked", "user_id": user_id, "project_id": project_id}


# -----------------------------------------------------------------------------
# Project Endpoints
# -----------------------------------------------------------------------------

@app.get("/projects", response_model=list[ProjectDTO])
async def list_projects():
    """List all projects."""
    project_ids = await project_repo.list_projects()
    projects = []

    for pid in project_ids:
        try:
            state = await project_repo.load(pid)
            projects.append(ProjectDTO(
                project_id=state.project_id,
                project_name=state.project_name,
                client=state.client,
                project_type=state.project_type,
                workspace_path=state.workspace_path,
                template_id=state.template_id,
                current_phase=state.current_phase.value,
                completed_phases=[p.value for p in state.completed_phases],
                created_at=state.created_at,
                status="complete" if state.current_phase == PhaseType.COMPLETE else "active",
            ))
        except Exception:
            continue

    return projects


@app.get("/project-templates", response_model=list[ProjectTemplateDTO])
async def list_project_templates():
    """List available project templates."""
    return [
        ProjectTemplateDTO(
            id=t.id,
            name=t.name,
            description=t.description,
            project_type=t.project_type,
            category=t.category,
        )
        for t in TEMPLATES
    ]


@app.post("/projects", response_model=ProjectDTO, status_code=201)
async def create_project(request: CreateProjectRequest):
    """Create a new project with automatic workspace creation."""
    engine = WorkflowEngine()

    # Resolve template if specified
    project_type = request.project_type
    template_id = request.template_id
    intake_path = request.intake_path

    if template_id:
        template = get_template_by_id(template_id)
        if template:
            project_type = template.project_type
            if not intake_path and template.default_intake_path:
                intake_path = template.default_intake_path

    # Start the project
    state = await engine.start_project(
        intake_path=Path(intake_path) if intake_path else None,
        project_name=request.project_name,
        client=request.client,
        metadata=request.metadata,
    )

    # Set additional fields
    state.project_type = project_type
    state.template_id = template_id
    state.brief = request.brief
    state.capabilities = request.capabilities if request.capabilities else ["generic"]
    state.app_repo_url = request.app_repo_url
    state.app_url = request.app_url

    # Create workspace for the project
    try:
        workspace_config = workspace_manager.create_data_workspace(
            project_id=state.project_id,
            project_type=project_type,
            metadata={
                "project_name": request.project_name,
                "template_id": template_id,
                "description": request.description,
                "brief": request.brief,
                "capabilities": state.capabilities,
            },
        )
        state.workspace_path = str(workspace_config.workspace_root)
    except Exception as e:
        # Log error but don't fail project creation
        import logging
        logging.warning(f"Failed to create workspace: {e}")

    # Save to persistence
    await project_repo.save(state)

    # Track engine
    _engines[state.project_id] = engine

    return ProjectDTO(
        project_id=state.project_id,
        project_name=state.project_name,
        client=state.client,
        project_type=state.project_type,
        workspace_path=state.workspace_path,
        template_id=state.template_id,
        current_phase=state.current_phase.value,
        completed_phases=[p.value for p in state.completed_phases],
        created_at=state.created_at,
        status="active",
    )


@app.get("/projects/{project_id}", response_model=ProjectDTO)
async def get_project(project_id: str):
    """Get project by ID."""
    try:
        state = await project_repo.load(project_id)
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Project not found: {project_id}")

    return ProjectDTO(
        project_id=state.project_id,
        project_name=state.project_name,
        client=state.client,
        project_type=state.project_type,
        workspace_path=state.workspace_path,
        template_id=state.template_id,
        current_phase=state.current_phase.value,
        completed_phases=[p.value for p in state.completed_phases],
        created_at=state.created_at,
        status="complete" if state.current_phase == PhaseType.COMPLETE else "active",
    )


@app.get("/projects/{project_id}/status", response_model=StatusDTO)
async def get_project_status(project_id: str):
    """Get project workflow status."""
    try:
        state = await project_repo.load(project_id)
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Project not found: {project_id}")

    # Calculate progress
    all_phases = [
        PhaseType.PLANNING, PhaseType.ARCHITECTURE, PhaseType.DATA,
        PhaseType.DEVELOPMENT, PhaseType.QA, PhaseType.DOCUMENTATION,
    ]
    completed_count = len(state.completed_phases)
    total_count = len(all_phases)
    progress = (completed_count / total_count * 100) if total_count > 0 else 0

    # Get pending phases
    pending = [
        p.value for p in all_phases
        if p not in state.completed_phases and p != state.current_phase
    ]

    # Get latest checkpoint
    latest_checkpoint = await checkpoint_repo.get_latest(project_id)
    checkpoint_dto = None
    if latest_checkpoint:
        checkpoint_dto = CheckpointDTO(
            id=latest_checkpoint.id,
            phase=latest_checkpoint.phase.value,
            checkpoint_type=latest_checkpoint.checkpoint_type.value,
            version=latest_checkpoint.version,
            created_at=latest_checkpoint.created_at,
            passed=latest_checkpoint.governance_results.passed,
            artifact_count=len(latest_checkpoint.artifacts),
        )

    return StatusDTO(
        project_id=state.project_id,
        run_id=state.run_id,
        current_phase=state.current_phase.value,
        progress_percent=progress,
        completed_phases=[p.value for p in state.completed_phases],
        pending_phases=pending,
        token_usage={
            "input_tokens": state.total_token_usage.input_tokens,
            "output_tokens": state.total_token_usage.output_tokens,
            "total_tokens": state.total_token_usage.total_tokens,
        },
        cost_usd=float(state.total_token_usage.cost_usd),
        last_checkpoint=checkpoint_dto,
    )


@app.post("/projects/{project_id}/advance", response_model=PhaseDTO)
async def advance_project(project_id: str):
    """Advance project to next phase."""
    try:
        state = await project_repo.load(project_id)
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Project not found: {project_id}")

    # Check if complete
    if state.current_phase == PhaseType.COMPLETE:
        raise HTTPException(status_code=400, detail="Project already complete")

    # Get or create engine
    engine = get_engine(project_id)

    # Restore state to engine
    engine._state = state

    # Run current phase
    try:
        phase_state = await engine.run_phase()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    # Save updated state
    await project_repo.save(engine.state)

    # Save checkpoint
    checkpoint = await engine._checkpoint_manager.save_checkpoint(
        phase=phase_state.phase,
        checkpoint_type=CheckpointType.POST,
        state=engine.state,
        agent_states=engine.state.agent_states,
        artifacts={},
        governance=engine.state.phase_states.get(phase_state.phase.value, phase_state).artifacts if hasattr(phase_state, 'artifacts') else {},
    )
    await checkpoint_repo.save(checkpoint)

    return PhaseDTO(
        phase=phase_state.phase.value,
        status=phase_state.status,
        started_at=phase_state.started_at,
        completed_at=phase_state.completed_at,
        agent_ids=phase_state.agent_ids,
        artifact_count=len(phase_state.artifacts),
        error_message=phase_state.error_message,
    )


@app.get("/projects/{project_id}/checkpoints", response_model=list[CheckpointDTO])
async def get_checkpoints(project_id: str):
    """Get checkpoints for a project."""
    try:
        await project_repo.load(project_id)
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Project not found: {project_id}")

    checkpoint_ids = await checkpoint_repo.list_for_project(project_id)
    checkpoints = []

    for cid in checkpoint_ids:
        try:
            cp = await checkpoint_repo.load(cid)
            checkpoints.append(CheckpointDTO(
                id=cp.id,
                phase=cp.phase.value,
                checkpoint_type=cp.checkpoint_type.value,
                version=cp.version,
                created_at=cp.created_at,
                passed=cp.governance_results.passed,
                artifact_count=len(cp.artifacts),
            ))
        except Exception:
            continue

    return checkpoints


@app.get("/projects/{project_id}/events", response_model=list[EventDTO])
async def get_project_events(
    project_id: str,
    limit: int = 50,
    event_type: str | None = None,
):
    """Get events for a project.

    Args:
        project_id: Project identifier.
        limit: Maximum number of events to return (default 50).
        event_type: Optional filter by event type.
    """
    try:
        await project_repo.load(project_id)
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Project not found: {project_id}")

    event_repo = get_event_repository()

    # Get events from repository
    from orchestrator_v2.telemetry.events import EventType as ET

    type_filter = None
    if event_type:
        try:
            type_filter = ET(event_type)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid event type: {event_type}")

    events = event_repo.get_events(
        project_id=project_id,
        event_type=type_filter,
        limit=limit,
    )

    return [
        EventDTO(
            id=e.id,
            event_type=e.event_type.value,
            timestamp=e.timestamp,
            project_id=e.project_id,
            phase=e.phase,
            agent_id=e.agent_id,
            message=e.message,
            data=e.data,
        )
        for e in events
    ]


@app.post("/projects/{project_id}/rollback/{checkpoint_id}")
async def rollback_project(project_id: str, checkpoint_id: str):
    """Rollback project to a checkpoint."""
    try:
        await project_repo.load(project_id)
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Project not found: {project_id}")

    try:
        checkpoint = await checkpoint_repo.load(checkpoint_id)
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Checkpoint not found: {checkpoint_id}")

    # Restore state from checkpoint
    restored_state = ProjectState(
        project_id=project_id,
        run_id=checkpoint.run_id,
        project_name="Restored Project",  # Would need to track this
        client="kearney-default",
        current_phase=checkpoint.current_phase,
        completed_phases=checkpoint.completed_phases,
        agent_states=checkpoint.agent_states,
    )

    await project_repo.save(restored_state)

    return {"status": "rolled_back", "checkpoint_id": checkpoint_id}


@app.get("/projects/{project_id}/governance/{phase}", response_model=GovernanceResultDTO)
async def get_governance_results(project_id: str, phase: str):
    """Get governance results for a phase."""
    try:
        await project_repo.load(project_id)
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Project not found: {project_id}")

    try:
        phase_type = PhaseType(phase)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid phase: {phase}")

    logs = await governance_repo.get_logs(project_id, phase_type)

    if not logs:
        return GovernanceResultDTO(
            passed=True,
            gate_results=[],
            compliance_results=[],
            warnings=[],
        )

    # Get latest
    latest = logs[-1]

    return GovernanceResultDTO(
        passed=latest.get("passed", True),
        gate_results=latest.get("quality_gates", []),
        compliance_results=latest.get("compliance_checks", []),
        warnings=[],
    )


# -----------------------------------------------------------------------------
# Artifacts Endpoint
# -----------------------------------------------------------------------------

@app.get("/projects/{project_id}/artifacts", response_model=ArtifactsResponse)
async def get_project_artifacts(project_id: str):
    """Get artifacts for a project grouped by phase."""
    try:
        state = await project_repo.load(project_id)
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Project not found: {project_id}")

    artifacts_by_phase: dict[str, list[ArtifactDTO]] = {}
    total_count = 0

    # Get artifacts from workspace if available
    if state.workspace_path:
        workspace_path = Path(state.workspace_path)
        artifacts_dir = workspace_path / "artifacts"

        if artifacts_dir.exists():
            # Scan for artifacts in phase subdirectories
            for phase_dir in artifacts_dir.iterdir():
                if phase_dir.is_dir():
                    phase_name = phase_dir.name
                    phase_artifacts = []

                    for artifact_file in phase_dir.iterdir():
                        if artifact_file.is_file():
                            stat = artifact_file.stat()
                            phase_artifacts.append(ArtifactDTO(
                                id=f"{phase_name}_{artifact_file.name}",
                                name=artifact_file.name,
                                path=str(artifact_file),
                                artifact_type=artifact_file.suffix[1:] if artifact_file.suffix else "file",
                                phase=phase_name,
                                size_bytes=stat.st_size,
                                created_at=datetime.fromtimestamp(stat.st_ctime),
                            ))
                            total_count += 1

                    if phase_artifacts:
                        artifacts_by_phase[phase_name] = phase_artifacts

    return ArtifactsResponse(
        project_id=project_id,
        artifacts_by_phase=artifacts_by_phase,
        total_count=total_count,
    )


@app.get("/projects/{project_id}/artifacts/{artifact_id}", response_model=ArtifactContentResponse)
async def get_artifact_content(project_id: str, artifact_id: str):
    """Get single artifact with full content and metadata."""
    import hashlib

    try:
        state = await project_repo.load(project_id)
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Project not found: {project_id}")

    if not state.workspace_path:
        raise HTTPException(status_code=404, detail="Project has no workspace")

    # Parse artifact_id (format: phase_filename)
    parts = artifact_id.split("_", 1)
    if len(parts) != 2:
        raise HTTPException(status_code=400, detail=f"Invalid artifact ID format: {artifact_id}")

    phase_name, filename = parts
    artifact_path = Path(state.workspace_path) / "artifacts" / phase_name / filename

    if not artifact_path.exists():
        raise HTTPException(status_code=404, detail=f"Artifact not found: {artifact_id}")

    # Read content
    try:
        content = artifact_path.read_text(encoding="utf-8")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to read artifact: {str(e)}")

    # Get file stats
    stat = artifact_path.stat()

    # Determine artifact type
    suffix = artifact_path.suffix.lower()
    type_map = {
        ".md": "markdown",
        ".json": "json",
        ".py": "code",
        ".ts": "code",
        ".js": "code",
        ".yaml": "yaml",
        ".yml": "yaml",
        ".txt": "text",
    }
    artifact_type = type_map.get(suffix, "text")

    # Load metadata from index if available
    index_path = Path(state.workspace_path) / "artifacts" / phase_name / "_index.json"
    metadata = {
        "created_at": datetime.fromtimestamp(stat.st_ctime).isoformat(),
        "size_bytes": stat.st_size,
        "hash": hashlib.sha256(content.encode()).hexdigest(),
    }

    if index_path.exists():
        try:
            import json
            index_data = json.loads(index_path.read_text())
            if filename in index_data:
                metadata.update(index_data[filename])
        except Exception:
            pass

    return ArtifactContentResponse(
        id=artifact_id,
        name=filename,
        phase=phase_name,
        path=str(artifact_path),
        artifact_type=artifact_type,
        content=content,
        metadata=metadata,
    )


@app.get("/projects/{project_id}/diagnostics/{phase}", response_model=DiagnosticsDTO)
async def get_phase_diagnostics(project_id: str, phase: str):
    """Get diagnostics for a specific phase."""
    try:
        state = await project_repo.load(project_id)
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Project not found: {project_id}")

    # Validate phase
    try:
        phase_type = PhaseType(phase)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid phase: {phase}")

    # Load diagnostics from file
    if state.workspace_path:
        diagnostics_path = Path(state.workspace_path) / ".diagnostics" / f"{phase}.json"

        if diagnostics_path.exists():
            try:
                import json
                data = json.loads(diagnostics_path.read_text())
                return DiagnosticsDTO(
                    phase=phase,
                    agents=data.get("agents", []),
                    skills=data.get("skills", []),
                    artifacts=data.get("artifacts", []),
                    governance=data.get("governance", {}),
                    token_usage=data.get("token_usage", {}),
                    timestamp=data.get("timestamp"),
                    errors=data.get("errors", []),
                )
            except Exception:
                pass

    # Return empty diagnostics if not found
    return DiagnosticsDTO(
        phase=phase,
        agents=[],
        skills=[],
        artifacts=[],
        governance={},
        token_usage={},
        timestamp=None,
        errors=[],
    )


# -----------------------------------------------------------------------------
# Project Console/Chat Endpoint
# -----------------------------------------------------------------------------

@app.post("/projects/{project_id}/chat", response_model=ChatResponse)
async def project_chat(
    project_id: str,
    request: ChatRequest,
    user: UserProfile = Depends(get_current_user),
):
    """Chat with the orchestrator about a project.

    Supports free-form chat and slash commands:
    - /plan-phase <phase>: Generate/update planning artifacts for a phase
    - /run-phase <phase>: Execute a specific phase
    - /feature "<title>" "<description>": Create a feature request
    """
    try:
        state = await project_repo.load(project_id)
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Project not found: {project_id}")

    message = request.message.strip()
    model = request.model_override or user.default_model or "claude-sonnet-4-5-20250514"

    # Check for slash commands
    if message.startswith("/"):
        return await _handle_slash_command(project_id, state, message, user, model)

    # Regular chat - build context and call LLM
    from orchestrator_v2.llm import get_provider_registry
    from orchestrator_v2.engine.state_models import AgentContext, TaskDefinition

    registry = get_provider_registry()

    # Build system prompt with project context
    system_prompt = f"""You are an AI assistant for the Ready-Set-Code orchestrator.
You are helping with project: {state.project_name}
Client: {state.client}
Project Type: {state.project_type}

Brief: {state.brief or 'No brief provided'}

Capabilities: {', '.join(state.capabilities) if state.capabilities else 'generic'}

Current Phase: {state.current_phase.value}
Completed Phases: {', '.join(p.value for p in state.completed_phases) if state.completed_phases else 'None'}

You can help the user understand their project status, answer questions about artifacts,
and provide guidance on next steps. Be concise and helpful.

Available slash commands:
- /plan-phase <phase>: Generate planning artifacts
- /run-phase <phase>: Execute a phase
- /feature "<title>" "<description>": Create a feature request
"""

    # Create context for LLM call
    context = AgentContext(
        project_state=state,
        task=TaskDefinition(
            task_id="chat",
            description="Project chat",
        ),
        user_id=user.user_id,
        llm_api_key=user.anthropic_api_key,
        llm_provider=user.default_provider or "anthropic",
        model=model,
    )

    try:
        result = await registry.generate(
            prompt=f"{system_prompt}\n\nUser: {message}\n\nAssistant:",
            model=model,
            context=context,
            max_tokens=1024,
        )

        return ChatResponse(
            reply=result.text,
            model=model,
            tokens={
                "input": result.usage.input_tokens if result.usage else 0,
                "output": result.usage.output_tokens if result.usage else 0,
            },
            agent="chat",
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Chat failed: {str(e)}")


async def _handle_slash_command(
    project_id: str,
    state: ProjectState,
    message: str,
    user: UserProfile,
    model: str,
) -> ChatResponse:
    """Handle slash commands in chat."""
    import json
    import re

    parts = message.split(maxsplit=2)
    command = parts[0].lower()

    # /help - Show all available commands
    if command == "/help":
        help_text = """**RSC Console Commands**

**Phase Execution:**
- `/plan-phase <phase>` - Generate planning artifacts
- `/run-phase <phase>` - Execute a specific phase

**Artifacts:**
- `/artifacts phase=<phase>` - List artifacts for a phase
- `/open <artifact_id>` - View artifact content

**Analysis:**
- `/next-actions` - Get recommended next steps
- `/summarize-prd` - Get executive summary of PRD
- `/diagnose-phase <phase>` - View phase diagnostics

**Other:**
- `/help` - Show this help message

**Valid phases:** planning, architecture, data, development, qa, documentation"""

        return ChatResponse(
            reply=help_text,
            model=model,
            tokens={"input": 0, "output": 0},
            agent="console",
        )

    # /artifacts phase=<phase> - List artifacts for a phase
    elif command == "/artifacts":
        # Parse phase=<phase> argument
        phase_match = re.search(r'phase=(\w+)', message)
        if not phase_match:
            return ChatResponse(
                reply="Usage: /artifacts phase=<phase>\nExample: /artifacts phase=planning",
                model=model,
                tokens={"input": 0, "output": 0},
                agent="system",
            )

        phase_name = phase_match.group(1).lower()

        if not state.workspace_path:
            return ChatResponse(
                reply="Project has no workspace configured.",
                model=model,
                tokens={"input": 0, "output": 0},
                agent="system",
            )

        artifacts_dir = Path(state.workspace_path) / "artifacts" / phase_name
        if not artifacts_dir.exists():
            return ChatResponse(
                reply=f"No artifacts found for phase: {phase_name}",
                model=model,
                tokens={"input": 0, "output": 0},
                agent="console",
            )

        # List artifacts
        artifact_list = []
        for f in sorted(artifacts_dir.iterdir()):
            if f.is_file() and not f.name.startswith("_"):
                stat = f.stat()
                artifact_list.append(f"- **{f.name}** ({stat.st_size} bytes) - ID: `{phase_name}_{f.name}`")

        if not artifact_list:
            return ChatResponse(
                reply=f"No artifacts found for phase: {phase_name}",
                model=model,
                tokens={"input": 0, "output": 0},
                agent="console",
            )

        reply = f"**Artifacts for {phase_name} phase:**\n\n" + "\n".join(artifact_list)
        reply += "\n\nUse `/open <artifact_id>` to view content."

        return ChatResponse(
            reply=reply,
            model=model,
            tokens={"input": 0, "output": 0},
            agent="console",
        )

    # /open <artifact_id> - View artifact content
    elif command == "/open":
        if len(parts) < 2:
            return ChatResponse(
                reply="Usage: /open <artifact_id>\nExample: /open planning_PRD.md",
                model=model,
                tokens={"input": 0, "output": 0},
                agent="system",
            )

        artifact_id = parts[1]

        # Parse artifact_id (format: phase_filename)
        id_parts = artifact_id.split("_", 1)
        if len(id_parts) != 2:
            return ChatResponse(
                reply=f"Invalid artifact ID format: {artifact_id}\nExpected format: phase_filename",
                model=model,
                tokens={"input": 0, "output": 0},
                agent="system",
            )

        phase_name, filename = id_parts

        if not state.workspace_path:
            return ChatResponse(
                reply="Project has no workspace configured.",
                model=model,
                tokens={"input": 0, "output": 0},
                agent="system",
            )

        artifact_path = Path(state.workspace_path) / "artifacts" / phase_name / filename
        if not artifact_path.exists():
            return ChatResponse(
                reply=f"Artifact not found: {artifact_id}",
                model=model,
                tokens={"input": 0, "output": 0},
                agent="system",
            )

        try:
            content = artifact_path.read_text(encoding="utf-8")
            stat = artifact_path.stat()

            # Truncate if too long
            max_preview = 3000
            truncated = len(content) > max_preview
            preview = content[:max_preview] + ("\n\n... (truncated)" if truncated else "")

            reply = f"**{filename}** ({phase_name} phase)\n"
            reply += f"Size: {stat.st_size} bytes\n\n"
            reply += "```\n" + preview + "\n```"

            return ChatResponse(
                reply=reply,
                model=model,
                tokens={"input": 0, "output": 0},
                agent="console",
            )
        except Exception as e:
            return ChatResponse(
                reply=f"Failed to read artifact: {str(e)}",
                model=model,
                tokens={"input": 0, "output": 0},
                agent="system",
            )

    # /diagnose-phase <phase> - View phase diagnostics
    elif command == "/diagnose-phase":
        if len(parts) < 2:
            return ChatResponse(
                reply="Usage: /diagnose-phase <phase>\nExample: /diagnose-phase data",
                model=model,
                tokens={"input": 0, "output": 0},
                agent="system",
            )

        phase_name = parts[1].lower()

        if not state.workspace_path:
            return ChatResponse(
                reply="Project has no workspace configured.",
                model=model,
                tokens={"input": 0, "output": 0},
                agent="system",
            )

        # Load diagnostics
        diagnostics_path = Path(state.workspace_path) / ".diagnostics" / f"{phase_name}.json"

        if not diagnostics_path.exists():
            return ChatResponse(
                reply=f"No diagnostics found for phase: {phase_name}\nRun the phase first with `/run-phase {phase_name}`",
                model=model,
                tokens={"input": 0, "output": 0},
                agent="console",
            )

        try:
            data = json.loads(diagnostics_path.read_text())

            reply = f"**Diagnostics for {phase_name} phase:**\n\n"
            reply += f"**Agents:** {', '.join(data.get('agents', [])) or 'None'}\n"
            reply += f"**Skills:** {', '.join(data.get('skills', [])) or 'None'}\n"
            reply += f"**Artifacts:** {', '.join(data.get('artifacts', [])) or 'None'}\n\n"

            token_usage = data.get('token_usage', {})
            if token_usage:
                reply += f"**Token Usage:**\n"
                reply += f"- Input: {token_usage.get('input', 0)}\n"
                reply += f"- Output: {token_usage.get('output', 0)}\n"
                reply += f"- Total: {token_usage.get('total', 0)}\n\n"

            governance = data.get('governance', {})
            if governance:
                reply += f"**Governance:** {'Passed' if governance.get('passed', True) else 'Failed'}\n"

            if data.get('timestamp'):
                reply += f"\n**Timestamp:** {data['timestamp']}"

            return ChatResponse(
                reply=reply,
                model=model,
                tokens={"input": 0, "output": 0},
                agent="console",
            )
        except Exception as e:
            return ChatResponse(
                reply=f"Failed to read diagnostics: {str(e)}",
                model=model,
                tokens={"input": 0, "output": 0},
                agent="system",
            )

    # /next-actions - Get recommended next steps
    elif command == "/next-actions":
        from orchestrator_v2.llm import get_provider_registry
        from orchestrator_v2.engine.state_models import AgentContext, TaskDefinition

        registry = get_provider_registry()

        # Build context for LLM
        completed = [p.value for p in state.completed_phases]
        current = state.current_phase.value
        capabilities = state.capabilities or ["generic"]

        prompt = f"""Based on the following project state, recommend 3-5 concrete next actions:

Project: {state.project_name}
Brief: {state.brief or 'No brief provided'}
Capabilities: {', '.join(capabilities)}
Current Phase: {current}
Completed Phases: {', '.join(completed) if completed else 'None'}

Provide actionable recommendations in markdown format. Focus on:
1. What phase to run next
2. What artifacts to review
3. Any potential issues to address

Be concise and specific."""

        context = AgentContext(
            project_state=state,
            task=TaskDefinition(task_id="next-actions", description="Generate next actions"),
            user_id=user.user_id,
            llm_api_key=user.llm_api_key,
            llm_provider=user.llm_provider or "anthropic",
            model=model,
        )

        try:
            result = await registry.generate(
                prompt=prompt,
                model=model,
                context=context,
                max_tokens=1024,
            )

            return ChatResponse(
                reply=f"**Recommended Next Actions:**\n\n{result.text}",
                model=model,
                tokens={
                    "input": result.usage.input_tokens if result.usage else 0,
                    "output": result.usage.output_tokens if result.usage else 0,
                },
                agent="advisor",
            )
        except Exception as e:
            return ChatResponse(
                reply=f"Failed to generate recommendations: {str(e)}",
                model=model,
                tokens={"input": 0, "output": 0},
                agent="system",
            )

    # /summarize-prd - Get executive summary of PRD
    elif command == "/summarize-prd":
        if not state.workspace_path:
            return ChatResponse(
                reply="Project has no workspace configured.",
                model=model,
                tokens={"input": 0, "output": 0},
                agent="system",
            )

        prd_path = Path(state.workspace_path) / "artifacts" / "planning" / "PRD.md"
        if not prd_path.exists():
            return ChatResponse(
                reply="PRD not found. Run `/plan-phase planning` first.",
                model=model,
                tokens={"input": 0, "output": 0},
                agent="system",
            )

        try:
            prd_content = prd_path.read_text(encoding="utf-8")

            from orchestrator_v2.llm import get_provider_registry
            from orchestrator_v2.engine.state_models import AgentContext, TaskDefinition

            registry = get_provider_registry()

            prompt = f"""Create a concise executive summary (3-5 bullet points) of this PRD:

{prd_content[:8000]}

Focus on:
- Project purpose
- Key features
- Technical approach
- Success criteria"""

            context = AgentContext(
                project_state=state,
                task=TaskDefinition(task_id="summarize-prd", description="Summarize PRD"),
                user_id=user.user_id,
                llm_api_key=user.llm_api_key,
                llm_provider=user.llm_provider or "anthropic",
                model=model,
            )

            result = await registry.generate(
                prompt=prompt,
                model=model,
                context=context,
                max_tokens=512,
            )

            return ChatResponse(
                reply=f"**PRD Executive Summary:**\n\n{result.text}",
                model=model,
                tokens={
                    "input": result.usage.input_tokens if result.usage else 0,
                    "output": result.usage.output_tokens if result.usage else 0,
                },
                agent="analyst",
            )
        except Exception as e:
            return ChatResponse(
                reply=f"Failed to summarize PRD: {str(e)}",
                model=model,
                tokens={"input": 0, "output": 0},
                agent="system",
            )

    # /run-phase <phase> - Execute a phase
    elif command == "/run-phase":
        if len(parts) < 2:
            return ChatResponse(
                reply="Usage: /run-phase <phase>\nExample: /run-phase data",
                model=model,
                tokens={"input": 0, "output": 0},
                agent="system",
            )

        phase_name = parts[1].lower()
        try:
            phase_type = PhaseType(phase_name)
        except ValueError:
            valid_phases = ", ".join(p.value for p in PhaseType if p != PhaseType.COMPLETE)
            return ChatResponse(
                reply=f"Invalid phase: {phase_name}\nValid phases: {valid_phases}",
                model=model,
                tokens={"input": 0, "output": 0},
                agent="system",
            )

        # Use execution service for phase execution
        try:
            execution_service = get_execution_service()
            result = await execution_service.execute_phase(phase_type, state, user)

            artifacts = result.get("artifacts", [])
            artifact_names = [Path(p).name for p in artifacts]
            agents = result.get("agents", [])
            summary = result.get("summary", "Phase completed")

            # Update state
            if phase_type not in state.completed_phases:
                state.completed_phases.append(phase_type)
            await project_repo.save(state)

            # Save diagnostics
            if state.workspace_path:
                diagnostics_dir = Path(state.workspace_path) / ".diagnostics"
                diagnostics_dir.mkdir(parents=True, exist_ok=True)
                diagnostics_path = diagnostics_dir / f"{phase_name}.json"

                diagnostics_data = {
                    "phase": phase_name,
                    "agents": agents,
                    "skills": result.get("skills", []),
                    "artifacts": artifact_names,
                    "governance": {"passed": True},
                    "token_usage": result.get("token_usage", {}),
                    "timestamp": datetime.utcnow().isoformat(),
                    "errors": [],
                }
                diagnostics_path.write_text(json.dumps(diagnostics_data, indent=2))

            return ChatResponse(
                reply=f"Phase {phase_name} completed successfully.\n\n"
                      f"Summary: {summary}\n\n"
                      f"Agents: {', '.join(agents)}\n\n"
                      f"Artifacts generated:\n"
                      f"{chr(10).join(f'- {name}' for name in artifact_names) if artifact_names else 'None'}\n\n"
                      f"View artifacts with: /artifacts phase={phase_name}",
                model=model,
                tokens={"input": 0, "output": 0},
                agent=agents[0] if agents else "orchestrator",
            )
        except Exception as e:
            return ChatResponse(
                reply=f"Failed to run phase {phase_name}: {str(e)}",
                model=model,
                tokens={"input": 0, "output": 0},
                agent="system",
            )

    # /plan-phase <phase> - Generate planning artifacts
    elif command == "/plan-phase":
        if len(parts) < 2:
            return ChatResponse(
                reply="Usage: /plan-phase <phase>\nExample: /plan-phase planning",
                model=model,
                tokens={"input": 0, "output": 0},
                agent="system",
            )

        phase_name = parts[1].lower()

        if phase_name == "planning":
            # Run the actual planning pipeline
            try:
                planning_service = get_planning_service()
                result = await planning_service.run_planning_pipeline(state, user)

                artifacts = result.get("artifacts", [])
                artifact_names = [Path(p).name for p in artifacts]

                # Save diagnostics
                if state.workspace_path:
                    diagnostics_dir = Path(state.workspace_path) / ".diagnostics"
                    diagnostics_dir.mkdir(parents=True, exist_ok=True)
                    diagnostics_path = diagnostics_dir / "planning.json"

                    diagnostics_data = {
                        "phase": "planning",
                        "agents": result.get("agents", []),
                        "skills": [],
                        "artifacts": artifact_names,
                        "governance": {"passed": True},
                        "token_usage": result.get("token_usage", {}),
                        "timestamp": datetime.utcnow().isoformat(),
                        "errors": [],
                    }
                    diagnostics_path.write_text(json.dumps(diagnostics_data, indent=2))

                return ChatResponse(
                    reply=f"Planning pipeline completed successfully!\n\n"
                          f"Agents: {', '.join(result.get('agents', []))}\n\n"
                          f"Artifacts generated:\n"
                          f"{chr(10).join(f'- {name}' for name in artifact_names)}\n\n"
                          f"View artifacts with: /artifacts phase=planning",
                    model=model,
                    tokens={"input": 0, "output": 0},
                    agent="documentarian",
                )
            except Exception as e:
                return ChatResponse(
                    reply=f"Planning pipeline failed: {str(e)}",
                    model=model,
                    tokens={"input": 0, "output": 0},
                    agent="system",
                )
        else:
            return ChatResponse(
                reply=f"Phase '{phase_name}' planning not yet implemented.\n"
                      f"Currently supported: planning",
                model=model,
                tokens={"input": 0, "output": 0},
                agent="system",
            )

    # Unknown command
    else:
        return ChatResponse(
            reply=f"Unknown command: {command}\n\nType `/help` for a list of available commands.",
            model=model,
            tokens={"input": 0, "output": 0},
            agent="system",
        )


@app.delete("/projects/{project_id}")
async def delete_project(project_id: str):
    """Delete a project."""
    try:
        await project_repo.load(project_id)
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Project not found: {project_id}")

    await project_repo.delete(project_id)

    # Clean up engine
    if project_id in _engines:
        del _engines[project_id]

    return {"status": "deleted", "project_id": project_id}


# -----------------------------------------------------------------------------
# Ready/Set/Go Endpoints
# -----------------------------------------------------------------------------

@app.post("/rsg/{project_id}/ready/start", response_model=ReadyStatusDTO)
async def start_ready(project_id: str):
    """Start the Ready stage (PLANNING + ARCHITECTURE)."""
    try:
        await project_repo.load(project_id)
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Project not found: {project_id}")

    try:
        status = await rsg_service.start_ready(project_id)
        return ready_status_to_dto(status)
    except RsgServiceError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/rsg/{project_id}/ready/status", response_model=ReadyStatusDTO)
async def get_ready_status(project_id: str):
    """Get Ready stage status."""
    try:
        await project_repo.load(project_id)
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Project not found: {project_id}")

    status = await rsg_service.get_ready_status(project_id)
    return ready_status_to_dto(status)


@app.post("/rsg/{project_id}/set/start", response_model=SetStatusDTO)
async def start_set(project_id: str):
    """Start the Set stage (DATA + early DEVELOPMENT)."""
    try:
        await project_repo.load(project_id)
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Project not found: {project_id}")

    try:
        status = await rsg_service.start_set(project_id)
        return set_status_to_dto(status)
    except RsgServiceError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/rsg/{project_id}/set/status", response_model=SetStatusDTO)
async def get_set_status(project_id: str):
    """Get Set stage status."""
    try:
        await project_repo.load(project_id)
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Project not found: {project_id}")

    status = await rsg_service.get_set_status(project_id)
    return set_status_to_dto(status)


@app.post("/rsg/{project_id}/go/start", response_model=GoStatusDTO)
async def start_go(project_id: str):
    """Start the Go stage (DEVELOPMENT + QA + DOCUMENTATION)."""
    try:
        await project_repo.load(project_id)
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Project not found: {project_id}")

    try:
        status = await rsg_service.start_go(project_id)
        return go_status_to_dto(status)
    except RsgServiceError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/rsg/{project_id}/go/status", response_model=GoStatusDTO)
async def get_go_status(project_id: str):
    """Get Go stage status."""
    try:
        await project_repo.load(project_id)
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Project not found: {project_id}")

    status = await rsg_service.get_go_status(project_id)
    return go_status_to_dto(status)


@app.get("/rsg/{project_id}/overview", response_model=RsgOverviewDTO)
async def get_rsg_overview(project_id: str):
    """Get combined RSG overview."""
    try:
        await project_repo.load(project_id)
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Project not found: {project_id}")

    overview = await rsg_service.get_overview(project_id)
    return rsg_overview_to_dto(overview)


# -----------------------------------------------------------------------------
# Territory POC Endpoints
# -----------------------------------------------------------------------------

class TerritoryScoreRequest(BaseModel):
    """Request to run territory scoring."""
    workspace_path: str
    intake_config: dict[str, Any] | None = None


class TerritoryClusterRequest(BaseModel):
    """Request to run territory clustering."""
    workspace_path: str
    intake_config: dict[str, Any] | None = None


class TerritoryResultDTO(BaseModel):
    """Territory operation result."""
    success: bool
    skill_id: str
    artifacts: list[dict[str, Any]]
    metadata: dict[str, Any]
    error: str | None = None


class TerritoryKpiDTO(BaseModel):
    """Territory KPI data."""
    territory_id: str
    retailer_count: int
    total_revenue: float
    avg_rvs: float
    avg_ros: float
    avg_rws: float
    avg_composite: float
    centroid_lat: float
    centroid_lon: float
    coverage_km: float


class TerritoryAssignmentDTO(BaseModel):
    """Territory assignment for a retailer."""
    retail_id: str
    retail_name: str
    state: str
    territory_id: str
    rvs: float
    ros: float
    rws: float
    latitude: float | None
    longitude: float | None


@app.post("/territory/score", response_model=TerritoryResultDTO)
async def run_territory_scoring(request: TerritoryScoreRequest):
    """Run territory scoring skill.

    Computes RVS/ROS/RWS scores for retailers in workspace.
    """
    import logging
    from orchestrator_v2.capabilities.skills.territory_poc import TerritoryScoringSkill
    from orchestrator_v2.engine.state_models import ProjectState

    logger = logging.getLogger(__name__)
    logger.info(f"Territory scoring requested for workspace: {request.workspace_path}")

    # Create minimal project state for skill execution
    state = ProjectState(
        project_id="territory-poc",
        run_id="scoring-run",
        project_name="Territory POC",
    )

    skill = TerritoryScoringSkill()

    try:
        result = skill.apply(
            state=state,
            workspace_path=Path(request.workspace_path),
            intake_config=request.intake_config,
        )

        logger.info(f"Scoring complete: {result.metadata.get('retailer_count', 0)} retailers scored")

        return TerritoryResultDTO(
            success=result.success,
            skill_id=result.skill_id,
            artifacts=[
                {
                    "path": a.path,
                    "hash": a.hash,
                    "size_bytes": a.size_bytes,
                    "type": a.artifact_type,
                }
                for a in result.artifacts
            ],
            metadata=result.metadata,
        )
    except FileNotFoundError as e:
        logger.error(f"File not found during scoring: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except ValueError as e:
        logger.error(f"Value error during scoring: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error during scoring: {e}")
        raise HTTPException(status_code=500, detail=f"Scoring failed: {str(e)}")


@app.post("/territory/cluster", response_model=TerritoryResultDTO)
async def run_territory_clustering(request: TerritoryClusterRequest):
    """Run territory clustering skill.

    Assigns scored retailers to territories using k-means.
    Requires scoring to be run first.
    """
    import logging
    from orchestrator_v2.capabilities.skills.territory_poc import TerritoryAlignmentSkill
    from orchestrator_v2.engine.state_models import ProjectState

    logger = logging.getLogger(__name__)
    logger.info(f"Territory clustering requested for workspace: {request.workspace_path}")

    # Create minimal project state for skill execution
    state = ProjectState(
        project_id="territory-poc",
        run_id="cluster-run",
        project_name="Territory POC",
    )

    skill = TerritoryAlignmentSkill()

    try:
        result = skill.apply(
            state=state,
            workspace_path=Path(request.workspace_path),
            intake_config=request.intake_config,
        )

        logger.info(f"Clustering complete: {result.metadata.get('territory_count', 0)} territories created")

        return TerritoryResultDTO(
            success=result.success,
            skill_id=result.skill_id,
            artifacts=[
                {
                    "path": a.path,
                    "hash": a.hash,
                    "size_bytes": a.size_bytes,
                    "type": a.artifact_type,
                }
                for a in result.artifacts
            ],
            metadata=result.metadata,
        )
    except FileNotFoundError as e:
        logger.error(f"File not found during clustering: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except ValueError as e:
        logger.error(f"Value error during clustering: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error during clustering: {e}")
        raise HTTPException(status_code=500, detail=f"Clustering failed: {str(e)}")


class TerritoryRunFullRequest(BaseModel):
    """Request to run full territory pipeline (scoring + clustering)."""
    workspace_path: str
    intake_config: dict[str, Any] | None = None


class TerritoryRunFullResultDTO(BaseModel):
    """Result of full territory pipeline."""
    success: bool
    scoring: TerritoryResultDTO
    clustering: TerritoryResultDTO | None = None
    error: str | None = None


@app.post("/territory/run-full", response_model=TerritoryRunFullResultDTO)
async def run_territory_full_pipeline(request: TerritoryRunFullRequest):
    """Run full territory pipeline (scoring then clustering).

    This runs both scoring and clustering in sequence, stopping on first error.
    """
    import logging
    from orchestrator_v2.capabilities.skills.territory_poc import TerritoryScoringSkill, TerritoryAlignmentSkill
    from orchestrator_v2.engine.state_models import ProjectState

    logger = logging.getLogger(__name__)
    logger.info(f"Full territory pipeline requested for workspace: {request.workspace_path}")

    workspace_path = Path(request.workspace_path)
    intake_config = request.intake_config

    # Create minimal project state for skill execution
    state = ProjectState(
        project_id="territory-poc",
        run_id="full-pipeline-run",
        project_name="Territory POC",
    )

    # Step 1: Run scoring
    scoring_skill = TerritoryScoringSkill()
    try:
        scoring_result = scoring_skill.apply(
            state=state,
            workspace_path=workspace_path,
            intake_config=intake_config,
        )

        logger.info(f"Scoring complete: {scoring_result.metadata.get('retailer_count', 0)} retailers scored")

        scoring_dto = TerritoryResultDTO(
            success=scoring_result.success,
            skill_id=scoring_result.skill_id,
            artifacts=[
                {
                    "path": a.path,
                    "hash": a.hash,
                    "size_bytes": a.size_bytes,
                    "type": a.artifact_type,
                }
                for a in scoring_result.artifacts
            ],
            metadata=scoring_result.metadata,
        )
    except Exception as e:
        logger.error(f"Scoring failed in full pipeline: {e}")
        scoring_dto = TerritoryResultDTO(
            success=False,
            skill_id=scoring_skill.metadata.id,
            artifacts=[],
            metadata={},
            error=str(e),
        )
        return TerritoryRunFullResultDTO(
            success=False,
            scoring=scoring_dto,
            clustering=None,
            error=f"Scoring failed: {str(e)}",
        )

    # Step 2: Run clustering
    clustering_skill = TerritoryAlignmentSkill()
    try:
        clustering_result = clustering_skill.apply(
            state=state,
            workspace_path=workspace_path,
            intake_config=intake_config,
        )

        logger.info(f"Clustering complete: {clustering_result.metadata.get('territory_count', 0)} territories created")

        clustering_dto = TerritoryResultDTO(
            success=clustering_result.success,
            skill_id=clustering_result.skill_id,
            artifacts=[
                {
                    "path": a.path,
                    "hash": a.hash,
                    "size_bytes": a.size_bytes,
                    "type": a.artifact_type,
                }
                for a in clustering_result.artifacts
            ],
            metadata=clustering_result.metadata,
        )
    except Exception as e:
        logger.error(f"Clustering failed in full pipeline: {e}")
        clustering_dto = TerritoryResultDTO(
            success=False,
            skill_id=clustering_skill.metadata.id,
            artifacts=[],
            metadata={},
            error=str(e),
        )
        return TerritoryRunFullResultDTO(
            success=False,
            scoring=scoring_dto,
            clustering=clustering_dto,
            error=f"Clustering failed: {str(e)}",
        )

    # Both succeeded
    return TerritoryRunFullResultDTO(
        success=True,
        scoring=scoring_dto,
        clustering=clustering_dto,
    )


@app.get("/territory/assignments")
async def get_territory_assignments(workspace_path: str):
    """Get territory assignments from workspace.

    Returns retailer-to-territory mapping with scores and coordinates.
    """
    import pandas as pd

    assignments_path = Path(workspace_path) / "artifacts" / "territory_assignments.csv"

    if not assignments_path.exists():
        raise HTTPException(
            status_code=404,
            detail="Territory assignments not found. Run scoring and clustering first."
        )

    df = pd.read_csv(assignments_path)

    # Convert to list of dicts
    assignments = []
    for _, row in df.iterrows():
        assignments.append({
            "retail_id": str(row.get("retail_id", "")),
            "retail_name": str(row.get("retail_name", "")),
            "state": str(row.get("state", "")),
            "territory_id": str(row.get("territory_id", "")),
            "rvs": float(row.get("RVS", 0)),
            "ros": float(row.get("ROS", 0)),
            "rws": float(row.get("RWS", 0)),
            "composite_score": float(row.get("composite_score", 0)),
            "latitude": float(row.get("latitude")) if pd.notna(row.get("latitude")) else None,
            "longitude": float(row.get("longitude")) if pd.notna(row.get("longitude")) else None,
        })

    return {"assignments": assignments, "count": len(assignments)}


@app.get("/territory/kpis")
async def get_territory_kpis(workspace_path: str):
    """Get territory KPIs from workspace.

    Returns per-territory summary statistics.
    """
    import pandas as pd

    kpis_path = Path(workspace_path) / "artifacts" / "territory_kpis.csv"

    if not kpis_path.exists():
        raise HTTPException(
            status_code=404,
            detail="Territory KPIs not found. Run scoring and clustering first."
        )

    df = pd.read_csv(kpis_path)

    # Convert to list of dicts
    kpis = []
    for _, row in df.iterrows():
        kpis.append({
            "territory_id": str(row.get("territory_id", "")),
            "retailer_count": int(row.get("retailer_count", 0)),
            "total_revenue": float(row.get("total_revenue", 0)),
            "avg_rvs": float(row.get("avg_rvs", 0)),
            "avg_ros": float(row.get("avg_ros", 0)),
            "avg_rws": float(row.get("avg_rws", 0)),
            "avg_composite": float(row.get("avg_composite", 0)),
            "centroid_lat": float(row.get("centroid_lat", 0)),
            "centroid_lon": float(row.get("centroid_lon", 0)),
            "coverage_km": float(row.get("coverage_km", 0)),
        })

    return {"kpis": kpis, "territory_count": len(kpis)}


# Factory function for creating configured app
def create_app(
    project_repo_override=None,
    checkpoint_repo_override=None,
    artifact_repo_override=None,
    governance_repo_override=None,
) -> FastAPI:
    """Create FastAPI app with optional repository overrides."""
    global project_repo, checkpoint_repo, artifact_repo, governance_repo

    if project_repo_override:
        project_repo = project_repo_override
    if checkpoint_repo_override:
        checkpoint_repo = checkpoint_repo_override
    if artifact_repo_override:
        artifact_repo = artifact_repo_override
    if governance_repo_override:
        governance_repo = governance_repo_override

    return app
