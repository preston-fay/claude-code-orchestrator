"""
Ready/Set/Go service for Orchestrator v2.

Provides high-level RSG abstraction on top of the workflow engine.

RSG Phase Mapping:
- READY = PLANNING + ARCHITECTURE
- SET = DATA + early DEVELOPMENT
- GO = full DEVELOPMENT + QA + DOCUMENTATION
"""

from orchestrator_v2.engine.engine import WorkflowEngine
from orchestrator_v2.engine.state_models import PhaseType, RsgStage
from orchestrator_v2.persistence.interfaces import (
    ArtifactRepository,
    CheckpointRepository,
    ProjectRepository,
)
from orchestrator_v2.rsg.models import GoStatus, ReadyStatus, RsgOverview, SetStatus
from orchestrator_v2.workspace.manager import WorkspaceManager


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

    async def start_ready(self, project_id: str) -> ReadyStatus:
        """Start the Ready stage (PLANNING + ARCHITECTURE).

        Executes phases until ARCHITECTURE is complete or DATA begins.

        Args:
            project_id: Project identifier.

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

        # Get or create workspace
        try:
            workspace = self._workspace_manager.load_workspace(project_id)
        except Exception:
            workspace = self._workspace_manager.create_workspace(project_id)

        # Create engine with workspace
        engine = WorkflowEngine(workspace=workspace)
        engine._state = state

        # Run phases until end of Ready scope
        messages = []
        governance_passed = True

        while state.current_phase in [PhaseType.PLANNING, PhaseType.ARCHITECTURE]:
            if state.current_phase == PhaseType.COMPLETE:
                break

            try:
                await engine.run_phase()
                messages.append(f"Completed {state.current_phase.value} phase")
            except Exception as e:
                messages.append(f"Error in {state.current_phase.value}: {str(e)}")
                governance_passed = False
                break

            # Check if we've moved past Ready phases
            if state.current_phase not in READY_PHASES:
                break

        # Update RSG state
        state.rsg_stage = RsgStage.READY
        state.rsg_progress.ready_completed = True
        state.rsg_progress.last_ready_phase = (
            state.completed_phases[-1] if state.completed_phases else None
        )

        # Save state
        await self._project_repo.save(state)

        return ReadyStatus(
            stage=state.rsg_stage,
            completed=state.rsg_progress.ready_completed,
            current_phase=state.current_phase,
            completed_phases=list(state.completed_phases),
            governance_passed=governance_passed,
            messages=messages,
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

    async def start_set(self, project_id: str) -> SetStatus:
        """Start the Set stage (DATA + early DEVELOPMENT).

        Executes phases until QA begins.

        Args:
            project_id: Project identifier.

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

        # Get workspace
        workspace = self._workspace_manager.load_workspace(project_id)

        # Create engine
        engine = WorkflowEngine(workspace=workspace)
        engine._state = state

        # Run phases until end of Set scope
        messages = []
        data_ready = False

        while state.current_phase in [PhaseType.DATA, PhaseType.DEVELOPMENT]:
            if state.current_phase == PhaseType.COMPLETE:
                break

            try:
                await engine.run_phase()
                messages.append(f"Completed {state.current_phase.value} phase")

                if PhaseType.DATA in state.completed_phases:
                    data_ready = True

            except Exception as e:
                messages.append(f"Error in {state.current_phase.value}: {str(e)}")
                break

            # Check if we've moved to QA (end of Set)
            if state.current_phase == PhaseType.QA:
                break

        # Count artifacts
        artifacts = await self._artifact_repo.list_for_project(project_id)

        # Update RSG state
        state.rsg_stage = RsgStage.SET
        state.rsg_progress.set_completed = data_ready
        state.rsg_progress.last_set_phase = (
            state.completed_phases[-1] if state.completed_phases else None
        )

        # Save state
        await self._project_repo.save(state)

        return SetStatus(
            stage=state.rsg_stage,
            completed=state.rsg_progress.set_completed,
            current_phase=state.current_phase,
            completed_phases=[
                p for p in state.completed_phases if p in SET_PHASES
            ],
            artifacts_count=len(artifacts),
            data_ready=data_ready,
            messages=messages,
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

    async def start_go(self, project_id: str) -> GoStatus:
        """Start the Go stage (DEVELOPMENT + QA + DOCUMENTATION).

        Executes remaining phases until complete or blocked.

        Args:
            project_id: Project identifier.

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

        # Get workspace
        workspace = self._workspace_manager.load_workspace(project_id)

        # Create engine
        engine = WorkflowEngine(workspace=workspace)
        engine._state = state

        # Run phases until complete or blocked
        messages = []
        governance_blocked = False

        while state.current_phase != PhaseType.COMPLETE:
            try:
                await engine.run_phase()
                messages.append(f"Completed {state.current_phase.value} phase")
            except Exception as e:
                error_msg = str(e)
                messages.append(f"Error in {state.current_phase.value}: {error_msg}")
                if "governance" in error_msg.lower() or "blocked" in error_msg.lower():
                    governance_blocked = True
                break

        # Count checkpoints
        checkpoints = await self._checkpoint_repo.list_for_project(project_id)

        # Update RSG state
        if state.current_phase == PhaseType.COMPLETE:
            state.rsg_stage = RsgStage.COMPLETE
            state.rsg_progress.go_completed = True
        else:
            state.rsg_stage = RsgStage.GO

        state.rsg_progress.last_go_phase = (
            state.completed_phases[-1] if state.completed_phases else None
        )

        # Save state
        await self._project_repo.save(state)

        return GoStatus(
            stage=state.rsg_stage,
            completed=state.rsg_progress.go_completed,
            current_phase=state.current_phase,
            completed_phases=[
                p for p in state.completed_phases if p in GO_PHASES
            ],
            checkpoints_count=len(checkpoints),
            governance_blocked=governance_blocked,
            messages=messages,
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
