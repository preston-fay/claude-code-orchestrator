"""
Runs API Routes.

Endpoints for orchestrator run management, execution, and artifact tracking.
"""

import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Header

from orchestrator_v2.api.dto.runs import (
    CreateRunRequest,
    RunSummary,
    RunDetail,
    ArtifactsResponse,
    MetricsSummary,
    AdvanceRunRequest,
    AdvanceRunResponse,
    ListRunsResponse,
)
from orchestrator_v2.services.orchestrator_service import OrchestratorService
from orchestrator_v2.user.models import UserProfile
from orchestrator_v2.user.repository import FileSystemUserRepository

logger = logging.getLogger(__name__)

# Create API router
router = APIRouter(prefix="/runs", tags=["runs"])

# Dependency for getting user profile from headers
async def get_current_user(
    x_user_id: Annotated[str | None, Header()] = None,
    x_user_email: Annotated[str | None, Header()] = None,
) -> UserProfile:
    """Get current user from request headers."""
    if not x_user_id or not x_user_email:
        raise HTTPException(
            status_code=401,
            detail="Missing user authentication headers (X-User-Id, X-User-Email)",
        )

    user_repo = FileSystemUserRepository()
    user = await user_repo.get_by_id(x_user_id)
    if user is None:
        # Create default user if not exists
        user = UserProfile(
            user_id=x_user_id,
            email=x_user_email,
            name=x_user_email.split("@")[0],
        )
        await user_repo.save(user)

    return user


# Dependency for orchestrator service
def get_orchestrator_service() -> OrchestratorService:
    """Get orchestrator service instance."""
    return OrchestratorService()


# -----------------------------------------------------------------------------
# Endpoint 1: GET /runs - List orchestrator runs
# -----------------------------------------------------------------------------

@router.get("", response_model=ListRunsResponse)
async def list_runs(
    status: str | None = None,
    profile: str | None = None,
    limit: int = 50,
    offset: int = 0,
    service: OrchestratorService = Depends(get_orchestrator_service),
) -> ListRunsResponse:
    """
    List all orchestrator runs with optional filtering and pagination.

    Returns a list of run summaries with support for filtering by status and profile,
    as well as pagination via limit and offset parameters.

    **Query Parameters:**
    - status: Filter by run status ("running", "completed", "failed")
    - profile: Filter by profile name (e.g., 'analytics_forecast_app')
    - limit: Maximum number of runs to return (default: 50)
    - offset: Number of runs to skip for pagination (default: 0)

    **Returns:**
    - ListRunsResponse with array of RunSummary objects and pagination info

    **Example:**
    ```
    GET /runs?status=running&limit=10&offset=0
    ```

    **Example Response:**
    ```json
    {
        "runs": [
            {
                "run_id": "abc123",
                "profile": "analytics_forecast_app",
                "project_name": "Forecast Project",
                "current_phase": "development",
                "status": "running",
                "created_at": "2025-11-26T12:00:00Z",
                "updated_at": "2025-11-26T14:30:00Z"
            }
        ],
        "total": 25,
        "limit": 10,
        "offset": 0
    }
    ```
    """
    try:
        logger.info(f"Listing runs with filters: status={status}, profile={profile}, limit={limit}, offset={offset}")

        runs, total = await service.list_runs(
            status=status,
            profile=profile,
            limit=limit,
            offset=offset,
        )

        response = ListRunsResponse(
            runs=runs,
            total=total,
            limit=limit,
            offset=offset,
        )

        logger.info(f"Listed {len(runs)} runs (total: {total})")
        return response

    except Exception as e:
        logger.error(f"Failed to list runs: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to list runs: {str(e)}")


# -----------------------------------------------------------------------------
# Endpoint 2: POST /runs - Create orchestrator run
# -----------------------------------------------------------------------------

@router.post("", response_model=RunSummary, status_code=201)
async def create_run(
    request: CreateRunRequest,
    user: UserProfile = Depends(get_current_user),
    service: OrchestratorService = Depends(get_orchestrator_service),
) -> RunSummary:
    """
    Create a new orchestrator run.

    Creates a new run with the specified profile and optional intake requirements.

    **Request Body:**
    - profile: Profile name (e.g., 'analytics_forecast_app')
    - intake: Optional intake text or requirements
    - project_name: Optional project name
    - metadata: Additional metadata

    **Returns:**
    - RunSummary with basic run information

    **Example:**
    ```json
    {
        "profile": "analytics_forecast_app",
        "intake": "Build a demand forecasting app",
        "project_name": "Forecast Project Q4"
    }
    ```
    """
    try:
        logger.info(f"Creating run with profile {request.profile} for user {user.user_id}")

        run_summary = await service.create_run(
            profile=request.profile,
            user=user,
            intake=request.intake,
            project_name=request.project_name,
            metadata=request.metadata,
        )

        logger.info(f"Created run {run_summary.run_id}")
        return run_summary

    except Exception as e:
        logger.error(f"Failed to create run: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create run: {str(e)}")


# -----------------------------------------------------------------------------
# Endpoint 2: POST /runs/{run_id}/next - Advance to next phase
# -----------------------------------------------------------------------------

@router.post("/{run_id}/next", response_model=AdvanceRunResponse)
async def advance_run(
    run_id: str,
    request: AdvanceRunRequest | None = None,
    user: UserProfile = Depends(get_current_user),
    service: OrchestratorService = Depends(get_orchestrator_service),
) -> AdvanceRunResponse:
    """
    Advance a run to the next phase.

    Executes the current phase and advances to the next phase in the workflow.

    **Path Parameters:**
    - run_id: Run identifier

    **Request Body (optional):**
    - skip_validation: Skip governance validation (default: false)

    **Returns:**
    - AdvanceRunResponse with status and phase information

    **Example:**
    ```json
    {
        "skip_validation": false
    }
    ```
    """
    try:
        logger.info(f"Advancing run {run_id} for user {user.user_id}")

        if request is None:
            request = AdvanceRunRequest()

        # Get current state before advancing
        current_detail = await service.get_run(run_id)
        previous_phase = current_detail.current_phase

        # Advance the run
        updated_detail = await service.advance_run(
            run_id=run_id,
            user=user,
            skip_validation=request.skip_validation,
        )

        response = AdvanceRunResponse(
            run_id=run_id,
            previous_phase=previous_phase,
            current_phase=updated_detail.current_phase,
            status=updated_detail.status,
            message=f"Advanced from {previous_phase} to {updated_detail.current_phase}",
        )

        logger.info(f"Advanced run {run_id} to phase {updated_detail.current_phase}")
        return response

    except KeyError:
        raise HTTPException(status_code=404, detail=f"Run not found: {run_id}")
    except Exception as e:
        logger.error(f"Failed to advance run {run_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to advance run: {str(e)}")


# -----------------------------------------------------------------------------
# Endpoint 3: GET /runs/{run_id} - Get run status and phases
# -----------------------------------------------------------------------------

@router.get("/{run_id}", response_model=RunDetail)
async def get_run(
    run_id: str,
    service: OrchestratorService = Depends(get_orchestrator_service),
) -> RunDetail:
    """
    Get detailed information about a run.

    Returns comprehensive information including phases, status, and metadata.

    **Path Parameters:**
    - run_id: Run identifier

    **Returns:**
    - RunDetail with full run information including all phases

    **Example Response:**
    ```json
    {
        "run_id": "abc123",
        "profile": "analytics_forecast_app",
        "current_phase": "architecture",
        "status": "running",
        "phases": [
            {
                "phase": "planning",
                "status": "completed",
                "artifacts_count": 3
            }
        ]
    }
    ```
    """
    try:
        logger.info(f"Fetching run {run_id}")
        run_detail = await service.get_run(run_id)
        return run_detail

    except KeyError:
        raise HTTPException(status_code=404, detail=f"Run not found: {run_id}")
    except Exception as e:
        logger.error(f"Failed to get run {run_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get run: {str(e)}")


# -----------------------------------------------------------------------------
# Endpoint 4: GET /runs/{run_id}/artifacts - List artifacts by phase
# -----------------------------------------------------------------------------

@router.get("/{run_id}/artifacts", response_model=ArtifactsResponse)
async def get_run_artifacts(
    run_id: str,
    service: OrchestratorService = Depends(get_orchestrator_service),
) -> ArtifactsResponse:
    """
    List all artifacts for a run, grouped by phase.

    Returns artifacts generated during each phase of the workflow.

    **Path Parameters:**
    - run_id: Run identifier

    **Returns:**
    - ArtifactsResponse with artifacts grouped by phase

    **Example Response:**
    ```json
    {
        "run_id": "abc123",
        "total_count": 5,
        "artifacts_by_phase": {
            "planning": [
                {
                    "artifact_id": "planning_PRD.md",
                    "phase": "planning",
                    "name": "PRD.md",
                    "artifact_type": "prd"
                }
            ]
        }
    }
    ```
    """
    try:
        logger.info(f"Fetching artifacts for run {run_id}")
        artifacts = await service.list_artifacts(run_id)
        return artifacts

    except KeyError:
        raise HTTPException(status_code=404, detail=f"Run not found: {run_id}")
    except Exception as e:
        logger.error(f"Failed to get artifacts for run {run_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get artifacts: {str(e)}")


# -----------------------------------------------------------------------------
# Endpoint 5: GET /runs/{run_id}/metrics - Get governance, hygiene, and metrics
# -----------------------------------------------------------------------------

@router.get("/{run_id}/metrics", response_model=MetricsSummary)
async def get_run_metrics(
    run_id: str,
    service: OrchestratorService = Depends(get_orchestrator_service),
) -> MetricsSummary:
    """
    Get comprehensive metrics for a run.

    Returns performance, governance, token usage, and cost metrics.

    **Path Parameters:**
    - run_id: Run identifier

    **Returns:**
    - MetricsSummary with all metrics

    **Example Response:**
    ```json
    {
        "run_id": "abc123",
        "total_duration_seconds": 3600.0,
        "total_token_usage": {"input": 10000, "output": 5000},
        "total_cost_usd": 0.45,
        "governance_score": 1.0,
        "hygiene_score": 0.95,
        "artifacts_total": 12
    }
    ```
    """
    try:
        logger.info(f"Fetching metrics for run {run_id}")
        metrics = await service.get_metrics(run_id)
        return metrics

    except KeyError:
        raise HTTPException(status_code=404, detail=f"Run not found: {run_id}")
    except Exception as e:
        logger.error(f"Failed to get metrics for run {run_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get metrics: {str(e)}")
