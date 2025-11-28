"""FastAPI HTTP server for Ready-Set-Code Orchestrator v2.

Provides REST API endpoints for RSC workflow orchestration.
"""

import os
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
    CodeStatusDTO,
    GoStatusDTO,
    PhaseAdvanceResultDTO,
    PhaseDTO,
    ProjectDTO,
    ProjectTemplateDTO,
    ProviderTestResultDTO,
    ReadyStatusDTO,
    RscOverviewDTO,
    RsgOverviewDTO,
    SetStatusDTO,
    StatusDTO,
    UpdateProviderSettingsDTO,
    code_status_to_dto,
    go_status_to_dto,
    phase_advance_result_to_dto,
    ready_status_to_dto,
    rsc_overview_to_dto,
    rsg_overview_to_dto,
    set_status_to_dto,
)
from orchestrator_v2.config.templates import (
    TEMPLATES,
    get_template_by_id,
)
from orchestrator_v2.telemetry.events_repository import get_event_repository
from orchestrator_v2.rsg.service import RscService, RscServiceError, RsgService, RsgServiceError
from orchestrator_v2.workspace.manager import WorkspaceManager
from orchestrator_v2.engine.engine import WorkflowEngine
from orchestrator_v2.engine.state_models import (
    CheckpointType,
    PhaseType,
    ProjectState,
)
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
)
from orchestrator_v2.user.models import (
    UserProfile,
    UserPublicProfile,
    UserRole,
    ApiKeyUpdate,
    to_public_profile,
)
from orchestrator_v2.api.routes import runs, intake
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pathlib import Path


# Request/Response models
class CreateProjectRequest(BaseModel):
    """Request to create a new project."""
    project_name: str
    client: str = "kearney-default"
    project_type: str = "generic"
    template_id: str | None = None
    # INTAKE: Project description/requirements - CRITICAL for agents to know what to build
    description: str | None = None
    intake_path: str | None = None
    # NEW: Intake session integration
    intake_session_id: str | None = None  # Link to completed intake session
    metadata: dict[str, Any] = Field(default_factory=dict)


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

# Initialize workspace manager and RSC service
workspace_manager = WorkspaceManager()
rsc_service = RscService(
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


def get_cors_origins() -> list[str]:
    """Get list of allowed CORS origins."""
    origins = [
        "http://localhost:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:3001",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ]
    extra_origins = os.environ.get("CORS_ALLOWED_ORIGINS", "")
    if extra_origins:
        origins.extend([o.strip() for o in extra_origins.split(",") if o.strip()])
    return origins


# Create FastAPI app
app = FastAPI(
    title="Ready-Set-Code Orchestrator API",
    description="HTTP API for Ready-Set-Code workflow orchestration",
    version="2.0.0",
)

# Configure CORS - allow Railway subdomains via regex
app.add_middleware(
    CORSMiddleware,
    allow_origins=get_cors_origins(),
    allow_origin_regex=r"https://.*\.up\.railway\.app",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(runs.router)
app.include_router(intake.router)


# Root endpoint removed - will be handled by frontend serving in production


@app.get("/health", include_in_schema=False)
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "2.0.0",
    }


# -----------------------------------------------------------------------------
# User Management Endpoints
# -----------------------------------------------------------------------------

@app.get("/users/me", response_model=UserPublicProfile)
async def get_current_user_profile(user: UserProfile = Depends(get_current_user)):
    """Get current user's profile with sanitized API key."""
    return to_public_profile(user)


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
    if payload.llm_provider not in ("anthropic", "bedrock"):
        raise HTTPException(status_code=400, detail="Unsupported provider. Use 'anthropic' or 'bedrock'.")

    user.llm_provider = payload.llm_provider
    if payload.llm_provider == "anthropic" and payload.api_key:
        user.llm_api_key = payload.api_key
    if payload.default_model:
        user.default_model = payload.default_model
    user.updated_at = datetime.utcnow()

    user_repo = get_user_repository()
    await user_repo.save(user)
    return to_public_profile(user)


@app.post("/users/me/provider-test", response_model=ProviderTestResultDTO)
async def test_provider(
    payload: UpdateProviderSettingsDTO | None = None,
    user: UserProfile = Depends(get_current_user),
):
    """Test if current (or proposed) provider settings work."""
    from orchestrator_v2.llm import get_provider_registry
    from orchestrator_v2.engine.state_models import AgentContext, TaskDefinition

    provider_name = payload.llm_provider if payload and payload.llm_provider else user.llm_provider
    temp_api_key = payload.api_key if (payload and payload.api_key) else user.llm_api_key
    model = payload.default_model if (payload and payload.default_model) else user.default_model

    registry = get_provider_registry()
    context = AgentContext(
        project_state=ProjectState(project_id="test", run_id="test", project_name="Test"),
        task=TaskDefinition(task_id="test", description="Provider test"),
        user_id=user.user_id,
        llm_api_key=temp_api_key,
        llm_provider=provider_name,
        model=model,
    )

    try:
        result = await registry.generate(
            prompt="You are a health check. Reply with exactly: READY-SET-CODE-OK",
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
    result = []
    for u in users:
        u_dict = u.model_dump()
        if u_dict.get("llm_api_key"):
            u_dict["llm_api_key"] = "***" + u_dict["llm_api_key"][-4:] if len(u_dict["llm_api_key"]) > 4 else "***"
        result.append(u_dict)
    return result


@app.get("/users/{user_id}")
async def get_user(user_id: str, current_user: UserProfile = Depends(get_current_user)):
    """Get user profile by ID."""
    if current_user.user_id != user_id and current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Not authorized to view other users")

    user_repo = get_user_repository()
    user = await user_repo.get_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail=f"User not found: {user_id}")

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
                intake=state.intake,
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
    project_type = request.project_type
    template_id = request.template_id
    intake_path = request.intake_path
    intake_description = request.description

    # NEW: If intake session provided, load session data
    if request.intake_session_id:
        from orchestrator_v2.services.intake_service import IntakeSessionService
        intake_service = IntakeSessionService()
        
        try:
            session = await intake_service.session_repo.get(request.intake_session_id)
            if session and session.is_complete:
                # Use intake session data to populate project
                if not request.project_name and "project_name" in session.responses:
                    request.project_name = session.responses["project_name"]
                if not intake_description:
                    template = await intake_service._load_template(session.template_id)
                    if template:
                        intake_description = await intake_service._format_intake_description(session, template)
                project_type = session.template_id
                template_id = session.template_id
                # Add intake session metadata
                request.metadata.update({
                    "intake_session_id": request.intake_session_id,
                    "intake_responses": session.responses,
                    "derived_responses": session.derived_responses,
                    "governance_data": session.governance_data.dict() if session.governance_data else None
                })
            else:
                raise HTTPException(status_code=400, detail="Intake session not found or not completed")
        except Exception as e:
            import logging
            logging.warning(f"Failed to load intake session {request.intake_session_id}: {e}")
            # Continue with regular project creation

    if template_id:
        template = get_template_by_id(template_id)
        if template:
            project_type = template.project_type
            if not intake_path and template.default_intake_path:
                intake_path = template.default_intake_path

    state = await engine.start_project(
        intake_path=Path(intake_path) if intake_path else None,
        project_name=request.project_name,
        client=request.client,
        metadata=request.metadata,
    )
    state.project_type = project_type
    state.template_id = template_id
    
    # CRITICAL: Store the description as intake for agents to use
    state.intake = intake_description

    try:
        workspace_config = workspace_manager.create_data_workspace(
            project_id=state.project_id,
            project_type=project_type,
            metadata={"project_name": request.project_name, "template_id": template_id, "description": intake_description},
        )
        state.workspace_path = str(workspace_config.workspace_root)
    except Exception as e:
        import logging
        logging.warning(f"Failed to create workspace: {e}")

    await project_repo.save(state)
    _engines[state.project_id] = engine

    return ProjectDTO(
        project_id=state.project_id,
        project_name=state.project_name,
        client=state.client,
        project_type=state.project_type,
        workspace_path=state.workspace_path,
        template_id=state.template_id,
        intake=state.intake,
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
        intake=state.intake,
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

    all_phases = [PhaseType.PLANNING, PhaseType.ARCHITECTURE, PhaseType.DATA, PhaseType.DEVELOPMENT, PhaseType.QA, PhaseType.DOCUMENTATION]
    completed_count = len(state.completed_phases)
    total_count = len(all_phases)
    progress = (completed_count / total_count * 100) if total_count > 0 else 0
    pending = [p.value for p in all_phases if p not in state.completed_phases and p != state.current_phase]

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
async def advance_project(
    project_id: str,
    user: UserProfile = Depends(get_current_user),
):
    """Advance project to next phase.
    
    Requires authenticated user with API key configured to make real LLM calls.
    """
    try:
        state = await project_repo.load(project_id)
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Project not found: {project_id}")

    if state.current_phase == PhaseType.COMPLETE:
        raise HTTPException(status_code=400, detail="Project already complete")

    engine = get_engine(project_id)
    engine._state = state

    try:
        # Pass user to run_phase so agents can use their API key for real LLM calls
        phase_state = await engine.run_phase(user=user)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    await project_repo.save(engine.state)

    from orchestrator_v2.engine.state_models import GovernanceResults
    checkpoint = await engine._checkpoint_manager.save_checkpoint(
        phase=phase_state.phase,
        checkpoint_type=CheckpointType.POST,
        state=engine.state,
        agent_states=engine.state.agent_states,
        artifacts=phase_state.artifacts if hasattr(phase_state, 'artifacts') else {},
        governance=GovernanceResults(),
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
async def get_project_events(project_id: str, limit: int = 50, event_type: str | None = None):
    """Get events for a project."""
    try:
        await project_repo.load(project_id)
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Project not found: {project_id}")

    event_repo = get_event_repository()
    from orchestrator_v2.telemetry.events import EventType as ET

    type_filter = None
    if event_type:
        try:
            type_filter = ET(event_type)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid event type: {event_type}")

    events = event_repo.get_events(project_id=project_id, event_type=type_filter, limit=limit)
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

    restored_state = ProjectState(
        project_id=project_id,
        run_id=checkpoint.run_id,
        project_name="Restored Project",
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
        return GovernanceResultDTO(passed=True, gate_results=[], compliance_results=[], warnings=[])

    latest = logs[-1]
    return GovernanceResultDTO(
        passed=latest.get("passed", True),
        gate_results=latest.get("quality_gates", []),
        compliance_results=latest.get("compliance_checks", []),
        warnings=[],
    )


@app.delete("/projects/{project_id}")
async def delete_project(project_id: str):
    """Delete a project."""
    try:
        await project_repo.load(project_id)
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Project not found: {project_id}")

    await project_repo.delete(project_id)
    if project_id in _engines:
        del _engines[project_id]
    return {"status": "deleted", "project_id": project_id}


# -----------------------------------------------------------------------------
# Ready/Set/Code (RSC) Endpoints - Primary API
# -----------------------------------------------------------------------------

@app.post("/rsc/{project_id}/advance", response_model=PhaseAdvanceResultDTO)
async def advance_phase(
    project_id: str,
    user: UserProfile = Depends(get_current_user),
):
    """Advance exactly ONE phase, then return control to user.
    
    This is the primary endpoint for user-controlled phase execution.
    Each call runs only one phase, giving the user explicit control
    over when the next phase runs.
    """
    try:
        await project_repo.load(project_id)
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Project not found: {project_id}")

    try:
        result = await rsc_service.advance_phase(project_id, user=user)
        return phase_advance_result_to_dto(result)
    except RscServiceError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/rsc/{project_id}/ready/start", response_model=ReadyStatusDTO)
async def start_ready_rsc(
    project_id: str,
    user: UserProfile = Depends(get_current_user),
):
    """Start the Ready stage (PLANNING + ARCHITECTURE)."""
    try:
        await project_repo.load(project_id)
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Project not found: {project_id}")

    try:
        status = await rsc_service.start_ready(project_id, user=user)
        return ready_status_to_dto(status)
    except RscServiceError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/rsc/{project_id}/ready/status", response_model=ReadyStatusDTO)
async def get_ready_status_rsc(project_id: str):
    """Get Ready stage status."""
    try:
        await project_repo.load(project_id)
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Project not found: {project_id}")

    status = await rsc_service.get_ready_status(project_id)
    return ready_status_to_dto(status)


@app.post("/rsc/{project_id}/set/start", response_model=SetStatusDTO)
async def start_set_rsc(
    project_id: str,
    user: UserProfile = Depends(get_current_user),
):
    """Start the Set stage (DATA + early DEVELOPMENT)."""
    try:
        await project_repo.load(project_id)
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Project not found: {project_id}")

    try:
        status = await rsc_service.start_set(project_id, user=user)
        return set_status_to_dto(status)
    except RscServiceError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/rsc/{project_id}/set/status", response_model=SetStatusDTO)
async def get_set_status_rsc(project_id: str):
    """Get Set stage status."""
    try:
        await project_repo.load(project_id)
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Project not found: {project_id}")

    status = await rsc_service.get_set_status(project_id)
    return set_status_to_dto(status)


@app.post("/rsc/{project_id}/code/start", response_model=CodeStatusDTO)
async def start_code_rsc(
    project_id: str,
    user: UserProfile = Depends(get_current_user),
):
    """Start the Code stage (DEVELOPMENT + QA + DOCUMENTATION)."""
    try:
        await project_repo.load(project_id)
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Project not found: {project_id}")

    try:
        status = await rsc_service.start_code(project_id, user=user)
        return code_status_to_dto(status)
    except RscServiceError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/rsc/{project_id}/code/status", response_model=CodeStatusDTO)
async def get_code_status_rsc(project_id: str):
    """Get Code stage status."""
    try:
        await project_repo.load(project_id)
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Project not found: {project_id}")

    status = await rsc_service.get_code_status(project_id)
    return code_status_to_dto(status)


@app.get("/rsc/{project_id}/overview", response_model=RscOverviewDTO)
async def get_rsc_overview(project_id: str):
    """Get combined RSC overview."""
    try:
        await project_repo.load(project_id)
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Project not found: {project_id}")

    overview = await rsc_service.get_overview(project_id)
    return rsc_overview_to_dto(overview)


# -----------------------------------------------------------------------------
# Legacy /rsg/ Endpoints (Backward Compatibility - Deprecated)
# -----------------------------------------------------------------------------

@app.post("/rsg/{project_id}/ready/start", response_model=ReadyStatusDTO, deprecated=True)
async def start_ready(
    project_id: str,
    user: UserProfile = Depends(get_current_user),
):
    """Deprecated: Use /rsc/{project_id}/ready/start instead."""
    return await start_ready_rsc(project_id, user)


@app.get("/rsg/{project_id}/ready/status", response_model=ReadyStatusDTO, deprecated=True)
async def get_ready_status(project_id: str):
    """Deprecated: Use /rsc/{project_id}/ready/status instead."""
    return await get_ready_status_rsc(project_id)


@app.post("/rsg/{project_id}/set/start", response_model=SetStatusDTO, deprecated=True)
async def start_set(
    project_id: str,
    user: UserProfile = Depends(get_current_user),
):
    """Deprecated: Use /rsc/{project_id}/set/start instead."""
    return await start_set_rsc(project_id, user)


@app.get("/rsg/{project_id}/set/status", response_model=SetStatusDTO, deprecated=True)
async def get_set_status(project_id: str):
    """Deprecated: Use /rsc/{project_id}/set/status instead."""
    return await get_set_status_rsc(project_id)


@app.post("/rsg/{project_id}/go/start", response_model=CodeStatusDTO, deprecated=True)
async def start_go(
    project_id: str,
    user: UserProfile = Depends(get_current_user),
):
    """Deprecated: Use /rsc/{project_id}/code/start instead."""
    return await start_code_rsc(project_id, user)


@app.get("/rsg/{project_id}/go/status", response_model=CodeStatusDTO, deprecated=True)
async def get_go_status(project_id: str):
    """Deprecated: Use /rsc/{project_id}/code/status instead."""
    return await get_code_status_rsc(project_id)


@app.get("/rsg/{project_id}/overview", response_model=RscOverviewDTO, deprecated=True)
async def get_rsg_overview(project_id: str):
    """Deprecated: Use /rsc/{project_id}/overview instead."""
    return await get_rsc_overview(project_id)


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


# Serve the React frontend
# Check if we're running in production (Railway sets NODE_ENV)
import os
if os.getenv("RAILWAY_ENVIRONMENT") or os.getenv("NODE_ENV") == "production":
    # Path to the built React app
    frontend_path = Path(__file__).parent.parent.parent / "rsg-ui" / "dist"
    
    if frontend_path.exists():
        # Mount static files from React build
        app.mount("/assets", StaticFiles(directory=str(frontend_path / "assets")), name="static")
        
        # Serve index.html for root
        @app.get("/")
        async def serve_root():
            index_path = frontend_path / "index.html"
            if index_path.exists():
                return FileResponse(str(index_path))
            return {"error": "Frontend not built"}
        
        # Serve index.html for all non-API routes (React Router support)
        @app.get("/{full_path:path}")
        async def serve_frontend(full_path: str):
            # Don't serve frontend for API routes
            if full_path.startswith("api/") or full_path.startswith("health") or full_path.startswith("rsc/") or full_path.startswith("assets/"):
                raise HTTPException(status_code=404, detail="Not found")
            
            index_path = frontend_path / "index.html"
            if index_path.exists():
                return FileResponse(str(index_path))
            return {"error": "Frontend not built"}
    else:
        print(f"WARNING: Frontend build not found at {frontend_path}")
else:
    print("Running in development mode - frontend served separately")
