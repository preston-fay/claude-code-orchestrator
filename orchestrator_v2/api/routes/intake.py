"""
Intake Template System API Routes.

Provides REST API endpoints for the intake template system,
enabling structured requirement gathering through adaptive interviews.
"""

import logging
from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import JSONResponse

from orchestrator_v2.auth.dependencies import get_current_user
from orchestrator_v2.models.intake import (
    CompleteSessionRequest,
    CreateSessionRequest,
    NavigationRequest,
    ProjectCreationResult,
    ResponseSubmissionResult,
    SessionResponse,
    SessionStatusResponse,
    SubmitResponsesRequest,
    TemplateDefinition,
    TemplateListItem,
    ValidateRequest,
    ValidationResult,
)
from orchestrator_v2.services.intake_service import (
    IntakeSessionService,
    IntakeServiceError,
    SessionNotFoundError,
    TemplateNotFoundError,
)
from orchestrator_v2.user.models import UserProfile

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/api/intake", tags=["intake"])

# Initialize service (will be dependency injected in production)
intake_service = IntakeSessionService()


def get_intake_service() -> IntakeSessionService:
    """Get intake service instance."""
    return intake_service


# -----------------------------------------------------------------------------
# Session Management Endpoints
# -----------------------------------------------------------------------------

@router.post("/sessions", response_model=SessionResponse, status_code=201)
async def create_session(
    request: CreateSessionRequest,
    service: IntakeSessionService = Depends(get_intake_service),
    user: UserProfile | None = Depends(get_current_user)
) -> SessionResponse:
    """
    Create a new intake session.
    
    Starts a structured interview process based on the specified template.
    The session tracks user progress through adaptive questionnaires.
    
    Args:
        request: Session creation parameters
        service: Intake service instance
        user: Current authenticated user
        
    Returns:
        Created session information with initial state
        
    Raises:
        HTTPException: 404 if template not found, 400 for validation errors
    """
    try:
        # Add user ID to request if user is authenticated
        if user and not request.user_id:
            request.user_id = user.user_id
            
        session_response = await service.create_session(request)
        
        logger.info(f"Created intake session {session_response.session_id} for template {request.template_id}")
        return session_response
        
    except TemplateNotFoundError as e:
        logger.error(f"Template not found: {e}")
        raise HTTPException(status_code=404, detail=str(e))
    except IntakeServiceError as e:
        logger.error(f"Error creating session: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error creating session: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/sessions/{session_id}", response_model=SessionStatusResponse)
async def get_session_status(
    session_id: str,
    service: IntakeSessionService = Depends(get_intake_service)
) -> SessionStatusResponse:
    """
    Get current session state.
    
    Returns comprehensive session status including current phase,
    visible questions, progress, and validation state.
    
    Args:
        session_id: Session identifier
        service: Intake service instance
        
    Returns:
        Complete session status information
        
    Raises:
        HTTPException: 404 if session not found
    """
    try:
        return await service.get_session_status(session_id)
    except SessionNotFoundError as e:
        logger.error(f"Session not found: {e}")
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error getting session status: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.put("/sessions/{session_id}/responses", response_model=ResponseSubmissionResult)
async def submit_responses(
    session_id: str,
    request: SubmitResponsesRequest,
    service: IntakeSessionService = Depends(get_intake_service)
) -> ResponseSubmissionResult:
    """
    Submit responses for current phase.
    
    Validates and saves user responses, potentially advancing to the next phase
    based on conditional logic and auto-advance settings.
    
    Args:
        session_id: Session identifier
        request: Response submission data
        service: Intake service instance
        
    Returns:
        Submission result with validation status and navigation info
        
    Raises:
        HTTPException: 404 if session not found, 400 for validation errors
    """
    try:
        result = await service.submit_responses(session_id, request)
        
        logger.info(f"Submitted responses for session {session_id}, phase {request.phase_id}")
        if result.advanced:
            logger.info(f"Advanced session {session_id} to phase {result.next_phase_id}")
            
        return result
        
    except SessionNotFoundError as e:
        logger.error(f"Session not found: {e}")
        raise HTTPException(status_code=404, detail=str(e))
    except IntakeServiceError as e:
        logger.error(f"Error submitting responses: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error submitting responses: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/sessions/{session_id}/navigate")
async def navigate_session(
    session_id: str,
    request: NavigationRequest,
    service: IntakeSessionService = Depends(get_intake_service)
) -> dict[str, Any]:
    """
    Navigate between phases.
    
    Supports forward, backward, and direct navigation between phases,
    respecting conditional visibility and completion requirements.
    
    Args:
        session_id: Session identifier
        request: Navigation parameters
        service: Intake service instance
        
    Returns:
        Navigation result with success status and new phase info
        
    Raises:
        HTTPException: 404 if session not found, 400 for invalid navigation
    """
    try:
        result = await service.navigate_session(session_id, request)
        
        if result.success:
            logger.info(f"Navigated session {session_id} to phase {result.current_phase_id}")
        else:
            logger.warning(f"Navigation failed for session {session_id}: {result.message}")
            
        return {
            "success": result.success,
            "current_phase_id": result.current_phase_id,
            "target_phase_id": result.target_phase_id,
            "message": result.message
        }
        
    except SessionNotFoundError as e:
        logger.error(f"Session not found: {e}")
        raise HTTPException(status_code=404, detail=str(e))
    except IntakeServiceError as e:
        logger.error(f"Error navigating session: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error navigating session: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/sessions/{session_id}/complete", response_model=ProjectCreationResult)
async def complete_session(
    session_id: str,
    request: CompleteSessionRequest,
    service: IntakeSessionService = Depends(get_intake_service),
    user: UserProfile | None = Depends(get_current_user)
) -> ProjectCreationResult:
    """
    Complete intake and create project.
    
    Performs final validation, creates a project with the intake data,
    and marks the session as complete. This triggers the handoff to
    the orchestrator workflow.
    
    Args:
        session_id: Session identifier
        request: Completion parameters
        service: Intake service instance
        user: Current authenticated user
        
    Returns:
        Project creation result with success status and next steps
        
    Raises:
        HTTPException: 404 if session not found, 400 for validation failures
    """
    try:
        result = await service.complete_session(session_id, request)
        
        if result.success:
            logger.info(f"Completed intake session {session_id}, created project {result.project_id}")
        else:
            logger.warning(f"Failed to complete session {session_id}: validation errors")
            
        return result
        
    except SessionNotFoundError as e:
        logger.error(f"Session not found: {e}")
        raise HTTPException(status_code=404, detail=str(e))
    except IntakeServiceError as e:
        logger.error(f"Error completing session: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error completing session: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.delete("/sessions/{session_id}")
async def delete_session(
    session_id: str,
    service: IntakeSessionService = Depends(get_intake_service)
) -> dict[str, str]:
    """
    Delete a session.
    
    Permanently removes session data. This action cannot be undone.
    
    Args:
        session_id: Session identifier
        service: Intake service instance
        
    Returns:
        Deletion confirmation
        
    Raises:
        HTTPException: 404 if session not found
    """
    try:
        deleted = await service.session_repo.delete(session_id)
        if not deleted:
            raise HTTPException(status_code=404, detail=f"Session not found: {session_id}")
            
        logger.info(f"Deleted intake session {session_id}")
        return {"status": "deleted", "session_id": session_id}
        
    except Exception as e:
        logger.error(f"Error deleting session {session_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


# -----------------------------------------------------------------------------
# Template Operations Endpoints
# -----------------------------------------------------------------------------

@router.get("/templates", response_model=list[TemplateListItem])
async def list_templates(
    client_slug: str | None = Query(None, description="Filter by client"),
    category: str | None = Query(None, description="Filter by category"),
    include_abstract: bool = Query(False, description="Include abstract templates"),
    service: IntakeSessionService = Depends(get_intake_service)
) -> list[TemplateListItem]:
    """
    List available templates.
    
    Returns all intake templates available to the system,
    optionally filtered by client or category.
    
    Args:
        client_slug: Optional client filter
        category: Optional category filter  
        include_abstract: Include abstract base templates
        service: Intake service instance
        
    Returns:
        List of available templates with metadata
    """
    try:
        templates = await service.list_templates(
            client_slug=client_slug,
            category=category,
            include_abstract=include_abstract
        )
        
        logger.debug(f"Listed {len(templates)} templates")
        return templates
        
    except Exception as e:
        logger.error(f"Error listing templates: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/templates/{template_id}", response_model=TemplateDefinition)
async def get_template(
    template_id: str,
    client_slug: str | None = Query(None, description="Apply client-specific governance"),
    service: IntakeSessionService = Depends(get_intake_service)
) -> TemplateDefinition:
    """
    Get template definition with governance applied.
    
    Returns complete template structure including phases, questions,
    and conditional logic, with optional client-specific customizations.
    
    Args:
        template_id: Template identifier
        client_slug: Optional client for governance application
        service: Intake service instance
        
    Returns:
        Complete template definition
        
    Raises:
        HTTPException: 404 if template not found
    """
    try:
        template = await service.get_template(template_id, client_slug)
        if not template:
            raise HTTPException(status_code=404, detail=f"Template not found: {template_id}")
            
        logger.debug(f"Retrieved template {template_id}")
        return template
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting template {template_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


# -----------------------------------------------------------------------------
# Utility Endpoints  
# -----------------------------------------------------------------------------

@router.post("/validate", response_model=ValidationResult)
async def validate_responses(
    request: ValidateRequest,
    service: IntakeSessionService = Depends(get_intake_service)
) -> ValidationResult:
    """
    Validate responses against template and governance.
    
    Performs comprehensive validation of intake responses without
    creating or modifying a session. Useful for real-time validation.
    
    Args:
        request: Validation parameters including template and responses
        service: Intake service instance
        
    Returns:
        Validation result with errors and warnings
        
    Raises:
        HTTPException: 404 if template not found, 400 for service errors
    """
    try:
        result = await service.validate_responses(request)
        
        logger.debug(f"Validated responses for template {request.template_id}")
        return result
        
    except TemplateNotFoundError as e:
        logger.error(f"Template not found: {e}")
        raise HTTPException(status_code=404, detail=str(e))
    except IntakeServiceError as e:
        logger.error(f"Error validating responses: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error validating responses: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/preview/{template_id}")
async def preview_template(
    template_id: str,
    service: IntakeSessionService = Depends(get_intake_service)
) -> dict[str, Any]:
    """
    Preview template structure for development/debugging.
    
    Returns detailed template information for development purposes,
    including computed metadata and phase/question counts.
    
    Args:
        template_id: Template identifier
        service: Intake service instance
        
    Returns:
        Template preview with structure information
        
    Raises:
        HTTPException: 404 if template not found
    """
    try:
        template = await service.get_template(template_id)
        if not template:
            raise HTTPException(status_code=404, detail=f"Template not found: {template_id}")
        
        # Build preview information
        phase_info = []
        total_questions = 0
        
        for phase in template.phases:
            visible_questions = len([q for q in phase.questions if not q.hidden])
            total_questions += visible_questions
            
            phase_info.append({
                "id": phase.id,
                "name": phase.name,
                "order": phase.order,
                "required": phase.required,
                "question_count": visible_questions,
                "has_conditions": phase.condition is not None
            })
        
        preview = {
            "template": {
                "id": template.template.id,
                "name": template.template.name,
                "description": template.template.description,
                "version": template.template.version,
                "category": template.template.category,
                "estimated_time_minutes": template.template.estimated_time_minutes
            },
            "structure": {
                "total_phases": len(template.phases),
                "total_questions": total_questions,
                "phases": phase_info
            },
            "features": {
                "has_brand_constraints": template.brand_constraints is not None,
                "has_governance": template.governance is not None,
                "has_conditional_logic": any(
                    phase.condition or any(q.condition for q in phase.questions) 
                    for phase in template.phases
                ),
                "supports_inheritance": template.template.extends is not None
            }
        }
        
        logger.debug(f"Generated preview for template {template_id}")
        return preview
        
    except Exception as e:
        logger.error(f"Error previewing template {template_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


# -----------------------------------------------------------------------------
# Health and Status Endpoints
# -----------------------------------------------------------------------------

@router.get("/health")
async def health_check() -> dict[str, str]:
    """
    Health check endpoint for intake system.
    
    Returns:
        Health status information
    """
    return {
        "status": "healthy",
        "service": "intake",
        "timestamp": str(datetime.utcnow())
    }


# -----------------------------------------------------------------------------
# Error Handlers
# -----------------------------------------------------------------------------

# Note: Exception handlers should be registered on the app, not router
# These are commented out but kept for documentation purposes

# @app.exception_handler(IntakeServiceError)
# async def intake_service_error_handler(request, exc: IntakeServiceError):
#     """Handle intake service errors."""
#     logger.error(f"Intake service error: {exc}")
#     return JSONResponse(
#         status_code=400,
#         content={"error": "Intake service error", "detail": str(exc)}
#     )


# @app.exception_handler(TemplateNotFoundError)
# async def template_not_found_error_handler(request, exc: TemplateNotFoundError):
#     """Handle template not found errors."""
#     logger.error(f"Template not found: {exc}")
#     return JSONResponse(
#         status_code=404,
#         content={"error": "Template not found", "detail": str(exc)}
#     )


# @app.exception_handler(SessionNotFoundError)
# async def session_not_found_error_handler(request, exc: SessionNotFoundError):
#     """Handle session not found errors."""
#     logger.error(f"Session not found: {exc}")
#     return JSONResponse(
#         status_code=404,
#         content={"error": "Session not found", "detail": str(exc)}
#     )