"""
Ready/Set/Go service for Orchestrator v2.

Provides high-level RSG abstraction on top of the workflow engine.

RSG Phase Mapping:
- READY = PLANNING + ARCHITECTURE
- SET = DATA + early DEVELOPMENT
- GO = full DEVELOPMENT + QA + DOCUMENTATION

PHASE CONTROL:
Unlike previous versions, this service gives the USER control over when
phases execute. Each phase must be explicitly advanced by the user.
Phases do NOT auto-run in loops.
"""

from orchestrator_v2.engine.engine import WorkflowEngine
from orchestrator_v2.engine.state_models import PhaseType, RsgStage
from orchestrator_v2.persistence.interfaces import (
    ArtifactRepository,
    CheckpointRepository,
    ProjectRepository,
)
from orchestrator_v2.rsg.models import GoStatus, ReadyStatus, RsgOverview, SetStatus, PhaseAdvanceResult
from orchestrator_v2.workspace.manager import WorkspaceManager
from orchestrator_v2.user.models import UserProfile


# Phase boundaries for RSG stages
READY_PHASES = {PhaseType.PLANNING, PhaseType.ARCHITECTURE}
SET_PHASES = {PhaseType.DATA, PhaseType.DEVELOPMENT}
GO_PHASES = {PhaseType.DEVELOPMENT, PhaseType.QA, PhaseType.DOCUMENTATION}


class RsgServiceError(Exception):
    """Base exception for RSG service errors."""
    pass


class RsgService:
    """Service layer for Ready/Set/Go operations.

    Wraps the workflow engine to provide high-level RSG abstractions
    that map to the underlying phase-based execution model.
    
    IMPORTANT: This service gives users explicit control over phase execution.
    Phases do NOT auto-run. Users must call advance_phase() to run each phase.
    """

    def __init__(
        self,
        project_repository: ProjectRepository,
        checkpoint_repository: CheckpointRepository,
        artifact_repository: ArtifactRepository,
        workspace_manager: WorkspaceManager,
    ):
        """Initialize the RSG service.

        Args:
            project_repository: Repository for project state.
            checkpoint_repository: Repository for checkpoints.
            artifact_repository: Repository for artifacts.
            workspace_manager: Workspace manager.
        """
        self._project_repo = project_repository
        self._checkpoint_repo = checkpoint_repository
        self._artifact_repo = artifact_repository
        self._workspace_manager = workspace_manager

    async def advance_phase(
        self,
        project_id: str,
        user: UserProfile | None = None,
    ) -> PhaseAdvanceResult:
        """Advance the project by running ONE phase.
        
        This is the primary method for phase execution. It runs exactly ONE
        phase and then returns control to the user. The user must call this
        method again to run the next phase.
        
        Args:
            project_id: Project identifier.
            user: User profile with API key for real LLM calls.
            
        Returns:
            PhaseAdvanceResult with details of the executed phase.
            
        Raises:
            RsgServiceError: If phase cannot be advanced.
        """
        # Load project state
        state = await self._project_repo.load(project_id)
        
        # Check if already complete
        if state.current_phase == PhaseType.COMPLETE:
            raise RsgServiceError("Project is already complete - no more phases to run")
        
        # Get or create workspace
        try:
            workspace = self._workspace_manager.load_workspace(project_id)
        except Exception:
            workspace = self._workspace_manager.create_workspace(project_id)
        
        # Create engine with workspace
        engine = WorkflowEngine(workspace=workspace)
        engine._state = state
        
        # Record which phase we're about to run
        phase_to_run = state.current_phase
        
        # Run EXACTLY ONE phase
        try:
            phase_state = await engine.run_phase(user=user)
            message = f"Completed {phase_to_run.value} phase"
            success = True
            error = None
        except Exception as e:
            message = f"Error in {phase_to_run.value}: {str(e)}"
            success = False
            error = str(e)
        
        # Update RSG stage based on progress
        self._update_rsg_stage(state)
        
        # Save state
        await self._project_repo.save(state)
        
        # Determine if more phases are available
        has_more_phases = state.current_phase != PhaseType.COMPLETE
        
        return PhaseAdvanceResult(
            phase_executed=phase_to_run,
            success=success,
            message=message,
            error=error,
            current_phase=state.current_phase,
            completed_phases=list(state.completed_phases),
            rsg_stage=state.rsg_stage,
            has_more_phases=has_more_phases,
        )
    
    def _update_rsg_stage(self, state) -> None:
        """Update the RSG stage based on completed phases.
        
        Args:
            state: ProjectState to update.
        """
        completed = set(state.completed_phases)
        
        # Check GO completion (all phases done)
        if state.current_phase == PhaseType.COMPLETE:
            state.rsg_stage = RsgStage.COMPLETE
            state.rsg_progress.go_completed = True
            return
        
        # Check GO stage (past SET)
        if PhaseType.QA in completed or PhaseType.DOCUMENTATION in completed:
            state.rsg_stage = RsgStage.GO
            return
            
        # Check SET completion
        if PhaseType.DATA in completed or PhaseType.DEVELOPMENT in completed:
            state.rsg_stage = RsgStage.SET
            state.rsg_progress.set_completed = PhaseType.DATA in completed
            return
        
        # Check READY completion
        if PhaseType.ARCHITECTURE in completed:
            state.rsg_stage = RsgStage.READY
            state.rsg_progress.ready_completed = True
            return
        
        # Still in READY (PLANNING done or in progress)
        if PhaseType.PLANNING in completed or state.current_phase == PhaseType.PLANNING:
            state.rsg_stage = RsgStage.READY
            return
        
        # Not started
        state.rsg_stage = RsgStage.NOT_STARTED

    async def start_ready(
        self,
        project_id: str,
        user: UserProfile | None = None,
    ) -> ReadyStatus:
        """Start the Ready stage by running the PLANNING phase.

        NOTE: This runs only ONE phase (PLANNING). User must call
        advance_phase() to run ARCHITECTURE phase.

        Args:
            project_id: Project identifier.
            user: User profile with API key for real LLM calls.

        Returns:
            ReadyStatus with completion info.

        Raises:
            RsgServiceError: If stage cannot be started.
        """
        # Load project state
        state = await self._project_repo.load(project_id)

        # Validate stage
        if state.rsg_stage not in [RsgStage.NOT_STARTED, RsgStage.READY]:
            raise RsgServiceError(
                f"Cannot start Ready: project is in {state.rsg_stage.value} stage"
            )

        # Validate we're at the right phase
        if state.current_phase not in [PhaseType.PLANNING, PhaseType.ARCHITECTURE, PhaseType.INTAKE]:
            raise RsgServiceError(
                f"Cannot start Ready: project is at {state.current_phase.value} phase"
            )

        # Run ONE phase using advance_phase
        result = await self.advance_phase(project_id, user)
        
        # Reload state
        state = await self._project_repo.load(project_id)

        return ReadyStatus(
            stage=state.rsg_stage,
            completed=state.rsg_progress.ready_completed,
            current_phase=state.current_phase,
            completed_phases=list(state.completed_phases),
            governance_passed=result.success,
            messages=[result.message],
        )

    async def get_ready_status(self, project_id: str) -> ReadyStatus:
        """Get the current Ready stage status.

        Args:
            project_id: Project identifier.

        Returns:
            ReadyStatus with current info.
        """
        state = await self._project_repo.load(project_id)

        # Determine if Ready phases are complete
        ready_complete = all(
            phase in state.completed_phases
            for phase in [PhaseType.PLANNING, PhaseType.ARCHITECTURE]
        )

        return ReadyStatus(
            stage=state.rsg_stage,
            completed=ready_complete or state.rsg_progress.ready_completed,
            current_phase=state.current_phase,
            completed_phases=[
                p for p in state.completed_phases if p in READY_PHASES
            ],
            governance_passed=True,  # Would check actual governance logs
            messages=[],
        )

    async def start_set(
        self,
        project_id: str,
        user: UserProfile | None = None,
    ) -> SetStatus:
        """Start the Set stage by running the next phase (DATA).

        NOTE: This runs only ONE phase. User must call advance_phase()
        to run additional phases.

        Args:
            project_id: Project identifier.
            user: User profile with API key for real LLM calls.

        Returns:
            SetStatus with completion info.

        Raises:
            RsgServiceError: If stage cannot be started.
        """
        # Load project state
        state = await self._project_repo.load(project_id)

        # Validate stage
        if state.rsg_stage not in [RsgStage.READY, RsgStage.SET]:
            if state.rsg_stage == RsgStage.NOT_STARTED:
                raise RsgServiceError(
                    "Cannot start Set: Ready stage not completed"
                )
            raise RsgServiceError(
                f"Cannot start Set: project is in {state.rsg_stage.value} stage"
            )

        # Run ONE phase using advance_phase
        result = await self.advance_phase(project_id, user)
        
        # Reload state
        state = await self._project_repo.load(project_id)

        # Count artifacts
        artifacts = await self._artifact_repo.list_for_project(project_id)

        return SetStatus(
            stage=state.rsg_stage,
            completed=state.rsg_progress.set_completed,
            current_phase=state.current_phase,
            completed_phases=[
                p for p in state.completed_phases if p in SET_PHASES
            ],
            artifacts_count=len(artifacts),
            data_ready=PhaseType.DATA in state.completed_phases,
            messages=[result.message],
        )

    async def get_set_status(self, project_id: str) -> SetStatus:
        """Get the current Set stage status.

        Args:
            project_id: Project identifier.

        Returns:
            SetStatus with current info.
        """
        state = await self._project_repo.load(project_id)

        # Check data readiness
        data_ready = PhaseType.DATA in state.completed_phases

        # Count artifacts
        artifacts = await self._artifact_repo.list_for_project(project_id)

        return SetStatus(
            stage=state.rsg_stage,
            completed=state.rsg_progress.set_completed,
            current_phase=state.current_phase,
            completed_phases=[
                p for p in state.completed_phases if p in SET_PHASES
            ],
            artifacts_count=len(artifacts),
            data_ready=data_ready,
            messages=[],
        )

    async def start_go(
        self,
        project_id: str,
        user: UserProfile | None = None,
    ) -> GoStatus:
        """Start the Go stage by running the next phase.

        NOTE: This runs only ONE phase. User must call advance_phase()
        to run additional phases until completion.

        Args:
            project_id: Project identifier.
            user: User profile with API key for real LLM calls.

        Returns:
            GoStatus with completion info.

        Raises:
            RsgServiceError: If stage cannot be started.
        """
        # Load project state
        state = await self._project_repo.load(project_id)

        # Validate stage
        if state.rsg_stage not in [RsgStage.SET, RsgStage.GO]:
            if state.rsg_stage in [RsgStage.NOT_STARTED, RsgStage.READY]:
                raise RsgServiceError(
                    "Cannot start Go: Set stage not completed"
                )
            raise RsgServiceError(
                f"Cannot start Go: project is in {state.rsg_stage.value} stage"
            )

        # Run ONE phase using advance_phase
        result = await self.advance_phase(project_id, user)
        
        # Reload state
        state = await self._project_repo.load(project_id)

        # Count checkpoints
        checkpoints = await self._checkpoint_repo.list_for_project(project_id)

        return GoStatus(
            stage=state.rsg_stage,
            completed=state.rsg_progress.go_completed,
            current_phase=state.current_phase,
            completed_phases=[
                p for p in state.completed_phases if p in GO_PHASES
            ],
            checkpoints_count=len(checkpoints),
            governance_blocked=not result.success and "governance" in (result.error or "").lower(),
            messages=[result.message],
        )

    async def get_go_status(self, project_id: str) -> GoStatus:
        """Get the current Go stage status.

        Args:
            project_id: Project identifier.

        Returns:
            GoStatus with current info.
        """
        state = await self._project_repo.load(project_id)

        # Count checkpoints
        checkpoints = await self._checkpoint_repo.list_for_project(project_id)

        return GoStatus(
            stage=state.rsg_stage,
            completed=state.rsg_progress.go_completed,
            current_phase=state.current_phase,
            completed_phases=[
                p for p in state.completed_phases if p in GO_PHASES
            ],
            checkpoints_count=len(checkpoints),
            governance_blocked=False,
            messages=[],
        )

    async def get_overview(self, project_id: str) -> RsgOverview:
        """Get combined overview of all RSG stages.

        Args:
            project_id: Project identifier.

        Returns:
            RsgOverview with all stage statuses.
        """
        state = await self._project_repo.load(project_id)

        ready_status = await self.get_ready_status(project_id)
        set_status = await self.get_set_status(project_id)
        go_status = await self.get_go_status(project_id)

        return RsgOverview(
            project_id=project_id,
            project_name=state.project_name,
            stage=state.rsg_stage,
            ready=ready_status,
            set=set_status,
            go=go_status,
        )
