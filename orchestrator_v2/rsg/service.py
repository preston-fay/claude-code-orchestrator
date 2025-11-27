"""
Ready/Set/Code service for Orchestrator v2.

Provides high-level RSC abstraction on top of the workflow engine.

RSC Phase Mapping:
- READY = PLANNING + ARCHITECTURE
- SET = DATA + early DEVELOPMENT
- CODE = full DEVELOPMENT + QA + DOCUMENTATION
"""

from orchestrator_v2.engine.engine import WorkflowEngine
from orchestrator_v2.engine.state_models import PhaseType, RscStage
from orchestrator_v2.persistence.interfaces import (
    ArtifactRepository,
    CheckpointRepository,
    ProjectRepository,
)
from orchestrator_v2.rsg.models import CodeStatus, ReadyStatus, RscOverview, SetStatus, PhaseAdvanceResult
from orchestrator_v2.workspace.manager import WorkspaceManager
from orchestrator_v2.user.models import UserProfile


# Phase boundaries for RSC stages
READY_PHASES = {PhaseType.PLANNING, PhaseType.ARCHITECTURE}
SET_PHASES = {PhaseType.DATA, PhaseType.DEVELOPMENT}
CODE_PHASES = {PhaseType.DEVELOPMENT, PhaseType.QA, PhaseType.DOCUMENTATION}


class RscServiceError(Exception):
    """Base exception for RSC service errors."""
    pass


# Backward compatibility alias
RsgServiceError = RscServiceError


class RscService:
    """Service layer for Ready/Set/Code operations.

    Wraps the workflow engine to provide high-level RSC abstractions
    that map to the underlying phase-based execution model.
    """

    def __init__(
        self,
        project_repository: ProjectRepository,
        checkpoint_repository: CheckpointRepository,
        artifact_repository: ArtifactRepository,
        workspace_manager: WorkspaceManager,
    ):
        """Initialize the RSC service.

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
        """Advance exactly ONE phase, then return control to user.
        
        This is the primary method for user-controlled phase execution.
        Each call runs only one phase, giving the user explicit control
        over when the next phase runs.
        
        Args:
            project_id: Project identifier.
            user: User profile with API key for real LLM calls.
            
        Returns:
            PhaseAdvanceResult with execution details.
            
        Raises:
            RscServiceError: If phase cannot be executed.
        """
        # Load project state
        state = await self._project_repo.load(project_id)
        
        # Check if workflow is complete
        if state.current_phase == PhaseType.COMPLETE:
            return PhaseAdvanceResult(
                phase_executed=PhaseType.COMPLETE,
                success=True,
                message="Workflow already complete",
                current_phase=state.current_phase,
                completed_phases=list(state.completed_phases),
                rsc_stage=state.rsc_stage,
                has_more_phases=False,
            )
        
        # Get or create workspace
        try:
            workspace = self._workspace_manager.load_workspace(project_id)
        except Exception:
            workspace = self._workspace_manager.create_workspace(project_id)
        
        # Create engine with workspace
        engine = WorkflowEngine(workspace=workspace)
        engine._state = state
        
        # Record which phase we're about to execute
        phase_to_execute = state.current_phase
        
        # Run EXACTLY ONE phase
        try:
            await engine.run_phase(user=user)
            success = True
            message = f"Completed {phase_to_execute.value} phase"
            error = None
        except Exception as e:
            success = False
            message = f"Error in {phase_to_execute.value} phase"
            error = str(e)
        
        # Update RSC stage based on completed phases
        await self._update_rsc_stage(state)
        
        # Save state
        await self._project_repo.save(state)
        
        return PhaseAdvanceResult(
            phase_executed=phase_to_execute,
            success=success,
            message=message,
            error=error,
            current_phase=state.current_phase,
            completed_phases=list(state.completed_phases),
            rsc_stage=state.rsc_stage,
            has_more_phases=state.current_phase != PhaseType.COMPLETE,
        )

    async def _update_rsc_stage(self, state) -> None:
        """Update RSC stage based on completed phases.
        
        Args:
            state: ProjectState to update.
        """
        completed = set(state.completed_phases)
        
        # Check CODE completion (all CODE phases done)
        if all(p in completed for p in [PhaseType.DEVELOPMENT, PhaseType.QA, PhaseType.DOCUMENTATION]):
            state.rsc_stage = RscStage.COMPLETE
            state.rsc_progress.code_completed = True
            state.rsc_progress.last_code_phase = state.completed_phases[-1] if state.completed_phases else None
        # Check SET completion (DATA phase done)
        elif PhaseType.DATA in completed:
            state.rsc_stage = RscStage.CODE if state.current_phase in CODE_PHASES else RscStage.SET
            state.rsc_progress.set_completed = True
            state.rsc_progress.last_set_phase = PhaseType.DATA
        # Check READY completion (PLANNING + ARCHITECTURE done)
        elif all(p in completed for p in [PhaseType.PLANNING, PhaseType.ARCHITECTURE]):
            state.rsc_stage = RscStage.SET
            state.rsc_progress.ready_completed = True
            state.rsc_progress.last_ready_phase = PhaseType.ARCHITECTURE
        # Partial READY (only PLANNING done)
        elif PhaseType.PLANNING in completed:
            state.rsc_stage = RscStage.READY
            state.rsc_progress.last_ready_phase = PhaseType.PLANNING

    async def start_ready(
        self,
        project_id: str,
        user: UserProfile | None = None,
    ) -> ReadyStatus:
        """Start the Ready stage (PLANNING + ARCHITECTURE).

        Executes ONE phase and returns. User must call again to continue.

        Args:
            project_id: Project identifier.
            user: User profile with API key for real LLM calls.

        Returns:
            ReadyStatus with completion info.

        Raises:
            RscServiceError: If stage cannot be started.
        """
        # Load project state
        state = await self._project_repo.load(project_id)

        # Validate stage
        if state.rsc_stage not in [RscStage.NOT_STARTED, RscStage.READY]:
            raise RscServiceError(
                f"Cannot start Ready: project is in {state.rsc_stage.value} stage"
            )

        # Run one phase using advance_phase
        result = await self.advance_phase(project_id, user)
        
        # Reload state after advance
        state = await self._project_repo.load(project_id)

        return ReadyStatus(
            stage=state.rsc_stage,
            completed=state.rsc_progress.ready_completed,
            current_phase=state.current_phase,
            completed_phases=list(state.completed_phases),
            governance_passed=result.success,
            messages=[result.message] if result.message else [],
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
            stage=state.rsc_stage,
            completed=ready_complete or state.rsc_progress.ready_completed,
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
        """Start the Set stage (DATA + early DEVELOPMENT).

        Executes ONE phase and returns. User must call again to continue.

        Args:
            project_id: Project identifier.
            user: User profile with API key for real LLM calls.

        Returns:
            SetStatus with completion info.

        Raises:
            RscServiceError: If stage cannot be started.
        """
        # Load project state
        state = await self._project_repo.load(project_id)

        # Validate stage
        if state.rsc_stage not in [RscStage.READY, RscStage.SET]:
            if state.rsc_stage == RscStage.NOT_STARTED:
                raise RscServiceError(
                    "Cannot start Set: Ready stage not completed"
                )
            raise RscServiceError(
                f"Cannot start Set: project is in {state.rsc_stage.value} stage"
            )

        # Run one phase using advance_phase
        result = await self.advance_phase(project_id, user)
        
        # Reload state after advance
        state = await self._project_repo.load(project_id)

        # Count artifacts
        artifacts = await self._artifact_repo.list_for_project(project_id)

        return SetStatus(
            stage=state.rsc_stage,
            completed=state.rsc_progress.set_completed,
            current_phase=state.current_phase,
            completed_phases=[
                p for p in state.completed_phases if p in SET_PHASES
            ],
            artifacts_count=len(artifacts),
            data_ready=PhaseType.DATA in state.completed_phases,
            messages=[result.message] if result.message else [],
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
            stage=state.rsc_stage,
            completed=state.rsc_progress.set_completed,
            current_phase=state.current_phase,
            completed_phases=[
                p for p in state.completed_phases if p in SET_PHASES
            ],
            artifacts_count=len(artifacts),
            data_ready=data_ready,
            messages=[],
        )

    async def start_code(
        self,
        project_id: str,
        user: UserProfile | None = None,
    ) -> CodeStatus:
        """Start the Code stage (DEVELOPMENT + QA + DOCUMENTATION).

        Executes ONE phase and returns. User must call again to continue.

        Args:
            project_id: Project identifier.
            user: User profile with API key for real LLM calls.

        Returns:
            CodeStatus with completion info.

        Raises:
            RscServiceError: If stage cannot be started.
        """
        # Load project state
        state = await self._project_repo.load(project_id)

        # Validate stage
        if state.rsc_stage not in [RscStage.SET, RscStage.CODE]:
            if state.rsc_stage in [RscStage.NOT_STARTED, RscStage.READY]:
                raise RscServiceError(
                    "Cannot start Code: Set stage not completed"
                )
            raise RscServiceError(
                f"Cannot start Code: project is in {state.rsc_stage.value} stage"
            )

        # Run one phase using advance_phase
        result = await self.advance_phase(project_id, user)
        
        # Reload state after advance
        state = await self._project_repo.load(project_id)

        # Count checkpoints
        checkpoints = await self._checkpoint_repo.list_for_project(project_id)

        governance_blocked = False
        if result.error and ("governance" in result.error.lower() or "blocked" in result.error.lower()):
            governance_blocked = True

        return CodeStatus(
            stage=state.rsc_stage,
            completed=state.rsc_progress.code_completed,
            current_phase=state.current_phase,
            completed_phases=[
                p for p in state.completed_phases if p in CODE_PHASES
            ],
            checkpoints_count=len(checkpoints),
            governance_blocked=governance_blocked,
            messages=[result.message] if result.message else [],
        )

    # Backward compatibility alias
    async def start_go(
        self,
        project_id: str,
        user: UserProfile | None = None,
    ) -> CodeStatus:
        """Deprecated: Use start_code() instead."""
        return await self.start_code(project_id, user)

    async def get_code_status(self, project_id: str) -> CodeStatus:
        """Get the current Code stage status.

        Args:
            project_id: Project identifier.

        Returns:
            CodeStatus with current info.
        """
        state = await self._project_repo.load(project_id)

        # Count checkpoints
        checkpoints = await self._checkpoint_repo.list_for_project(project_id)

        return CodeStatus(
            stage=state.rsc_stage,
            completed=state.rsc_progress.code_completed,
            current_phase=state.current_phase,
            completed_phases=[
                p for p in state.completed_phases if p in CODE_PHASES
            ],
            checkpoints_count=len(checkpoints),
            governance_blocked=False,
            messages=[],
        )

    # Backward compatibility alias
    async def get_go_status(self, project_id: str) -> CodeStatus:
        """Deprecated: Use get_code_status() instead."""
        return await self.get_code_status(project_id)

    async def get_overview(self, project_id: str) -> RscOverview:
        """Get combined overview of all RSC stages.

        Args:
            project_id: Project identifier.

        Returns:
            RscOverview with all stage statuses.
        """
        state = await self._project_repo.load(project_id)

        ready_status = await self.get_ready_status(project_id)
        set_status = await self.get_set_status(project_id)
        code_status = await self.get_code_status(project_id)

        return RscOverview(
            project_id=project_id,
            project_name=state.project_name,
            stage=state.rsc_stage,
            ready=ready_status,
            set=set_status,
            code=code_status,
        )


# Backward compatibility alias
RsgService = RscService
