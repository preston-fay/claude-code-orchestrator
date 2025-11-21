"""
FastAPI HTTP server for Orchestrator v2.

Provides REST API endpoints for orchestrator operations.

See ADR-002 for API design.
"""

from datetime import datetime
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel, Field

from orchestrator_v2.api.dto import (
    CheckpointDTO,
    GovernanceResultDTO,
    GoStatusDTO,
    PhaseDTO,
    ProjectDTO,
    ReadyStatusDTO,
    RsgOverviewDTO,
    SetStatusDTO,
    StatusDTO,
    go_status_to_dto,
    ready_status_to_dto,
    rsg_overview_to_dto,
    set_status_to_dto,
)
from orchestrator_v2.rsg.service import RsgService, RsgServiceError
from orchestrator_v2.workspace.manager import WorkspaceManager
from orchestrator_v2.core.engine import WorkflowEngine
from orchestrator_v2.core.state_models import (
    CheckpointType,
    GateStatus,
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
    require_admin,
)
from orchestrator_v2.user.models import (
    UserProfile,
    UserRole,
    ApiKeyUpdate,
    UserProfileUpdate,
)


# Request/Response models
class CreateProjectRequest(BaseModel):
    """Request to create a new project."""
    project_name: str
    client: str = "kearney-default"
    intake_path: str | None = None
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
    title="Orchestrator v2 API",
    description="HTTP API for Claude Code Orchestrator v2",
    version="2.0.0",
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

@app.get("/me")
async def get_current_user_profile(user: UserProfile = Depends(get_current_user)):
    """Get current user's profile."""
    # Don't expose the API key in the response
    user_dict = user.model_dump()
    if user_dict.get("llm_api_key"):
        user_dict["llm_api_key"] = "***" + user_dict["llm_api_key"][-4:] if len(user_dict["llm_api_key"]) > 4 else "***"
    return user_dict


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
                current_phase=state.current_phase.value,
                completed_phases=[p.value for p in state.completed_phases],
                created_at=state.created_at,
                status="complete" if state.current_phase == PhaseType.COMPLETE else "active",
            ))
        except Exception:
            continue

    return projects


@app.post("/projects", response_model=ProjectDTO, status_code=201)
async def create_project(request: CreateProjectRequest):
    """Create a new project."""
    engine = WorkflowEngine()

    # Start the project
    state = await engine.start_project(
        intake_path=Path(request.intake_path) if request.intake_path else None,
        project_name=request.project_name,
        client=request.client,
        metadata=request.metadata,
    )

    # Save to persistence
    await project_repo.save(state)

    # Track engine
    _engines[state.project_id] = engine

    return ProjectDTO(
        project_id=state.project_id,
        project_name=state.project_name,
        client=state.client,
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
