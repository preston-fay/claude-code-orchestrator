"""
Orchestrator Service Layer.

Provides high-level business logic for managing orchestrator runs,
coordinating between the engine, persistence, and API layers.
"""

import logging
from datetime import datetime
from pathlib import Path
from typing import Any
from uuid import uuid4

from orchestrator_v2.api.dto.runs import (
    RunSummary,
    RunDetail,
    PhaseInfo,
    ArtifactSummary,
    ArtifactsResponse,
    PhaseMetrics,
    MetricsSummary,
)
from orchestrator_v2.engine.engine import WorkflowEngine
from orchestrator_v2.engine.state_models import ProjectState, PhaseType, PhaseState
from orchestrator_v2.persistence.fs_repository import FileSystemProjectRepository
from orchestrator_v2.user.models import UserProfile
from orchestrator_v2.workspace.manager import WorkspaceManager

logger = logging.getLogger(__name__)


class OrchestratorService:
    """
    Service layer for orchestrator operations.

    Manages run lifecycle, state persistence, and artifact tracking.
    """

    def __init__(
        self,
        project_repo: FileSystemProjectRepository | None = None,
        workspace_manager: WorkspaceManager | None = None,
    ):
        """Initialize the orchestrator service."""
        self._project_repo = project_repo or FileSystemProjectRepository()
        self._workspace_manager = workspace_manager or WorkspaceManager()
        self._engines: dict[str, WorkflowEngine] = {}
        logger.info("OrchestratorService initialized")

    async def create_run(
        self,
        profile: str,
        user: UserProfile,
        intake: str | None = None,
        project_name: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> RunSummary:
        """
        Create a new orchestrator run.

        Args:
            profile: Profile name (e.g., 'analytics_forecast_app')
            user: User profile for BYOK and auth
            intake: Optional intake text/requirements
            project_name: Optional project name
            metadata: Additional metadata

        Returns:
            RunSummary with basic run information
        """
        run_id = str(uuid4())
        project_name = project_name or f"run_{run_id[:8]}"

        # Create project state
        state = ProjectState(
            project_id=run_id,
            project_name=project_name,
            client="default",
            user_id=user.user_id,
            project_type=profile,
            template_id=profile,
            current_phase=PhaseType.PLANNING,
            metadata=metadata or {},
        )

        if intake:
            state.metadata["intake"] = intake

        # Create workspace
        workspace_config = await self._workspace_manager.create_workspace(
            project_id=run_id,
            project_name=project_name,
            metadata={"profile": profile, "intake": intake},
        )
        state.workspace_path = str(workspace_config.workspace_root)

        # Persist state
        await self._project_repo.save(state)

        logger.info(f"Created run {run_id} with profile {profile}")

        return RunSummary(
            run_id=run_id,
            profile=profile,
            project_name=project_name,
            current_phase=state.current_phase.value,
            status="running",
            created_at=state.created_at,
            updated_at=datetime.utcnow(),
        )

    async def get_run(self, run_id: str) -> RunDetail:
        """
        Get detailed information about a run.

        Args:
            run_id: Run identifier

        Returns:
            RunDetail with full run information
        """
        state = await self._project_repo.load(run_id)

        # Build phase information
        phases = []
        for phase_name, phase_state in state.phases.items():
            phase_info = PhaseInfo(
                phase=phase_name,
                status=phase_state.status.value if phase_state.status else "pending",
                started_at=phase_state.started_at,
                completed_at=phase_state.completed_at,
                duration_seconds=self._calculate_duration(
                    phase_state.started_at,
                    phase_state.completed_at,
                ),
                agent_ids=list(phase_state.agent_states.keys()),
                artifacts_count=len(phase_state.artifacts),
            )
            phases.append(phase_info)

        # Calculate status
        status = "running"
        if state.current_phase == PhaseType.DOCUMENTATION and \
           state.phases.get("documentation", PhaseState()).status.value == "completed":
            status = "completed"

        completed_at = None
        if status == "completed":
            last_phase = state.phases.get("documentation")
            if last_phase:
                completed_at = last_phase.completed_at

        return RunDetail(
            run_id=run_id,
            profile=state.template_id or state.project_type,
            intake=state.metadata.get("intake"),
            project_name=state.project_name,
            current_phase=state.current_phase.value,
            status=status,
            phases=phases,
            created_at=state.created_at,
            updated_at=datetime.utcnow(),
            completed_at=completed_at,
            total_duration_seconds=self._calculate_total_duration(state),
            metadata=state.metadata,
        )

    async def advance_run(
        self,
        run_id: str,
        user: UserProfile,
        skip_validation: bool = False,
    ) -> RunDetail:
        """
        Advance a run to the next phase.

        Args:
            run_id: Run identifier
            user: User profile for execution
            skip_validation: Skip governance validation

        Returns:
            Updated RunDetail
        """
        state = await self._project_repo.load(run_id)

        # Get or create engine for this run
        if run_id not in self._engines:
            engine = WorkflowEngine()
            engine.load_state(state)
            self._engines[run_id] = engine
        else:
            engine = self._engines[run_id]

        # Execute current phase
        try:
            await engine.run_phase(state.current_phase, user=user)

            # Advance to next phase
            next_phase = self._get_next_phase(state.current_phase)
            if next_phase:
                state.current_phase = next_phase
                await self._project_repo.save(state)

            logger.info(f"Advanced run {run_id} to phase {next_phase}")
        except Exception as e:
            logger.error(f"Failed to advance run {run_id}: {e}")
            raise

        return await self.get_run(run_id)

    async def list_artifacts(self, run_id: str) -> ArtifactsResponse:
        """
        List all artifacts for a run, grouped by phase.

        Args:
            run_id: Run identifier

        Returns:
            ArtifactsResponse with artifacts grouped by phase
        """
        state = await self._project_repo.load(run_id)

        artifacts_by_phase: dict[str, list[ArtifactSummary]] = {}
        total_count = 0

        # Scan workspace for artifacts
        if state.workspace_path:
            workspace_path = Path(state.workspace_path)
            artifacts_dir = workspace_path / "artifacts"

            if artifacts_dir.exists():
                for phase_dir in artifacts_dir.iterdir():
                    if not phase_dir.is_dir():
                        continue

                    phase_name = phase_dir.name
                    phase_artifacts = []

                    for artifact_file in phase_dir.iterdir():
                        if not artifact_file.is_file() or artifact_file.name.startswith("_"):
                            continue

                        stat = artifact_file.stat()
                        artifact_type = self._determine_artifact_type(artifact_file)

                        artifact = ArtifactSummary(
                            artifact_id=f"{phase_name}_{artifact_file.name}",
                            phase=phase_name,
                            path=str(artifact_file),
                            name=artifact_file.name,
                            description=f"{artifact_type.upper()} artifact for {phase_name}",
                            artifact_type=artifact_type,
                            size_bytes=stat.st_size,
                            created_at=datetime.fromtimestamp(stat.st_ctime),
                        )
                        phase_artifacts.append(artifact)
                        total_count += 1

                    if phase_artifacts:
                        artifacts_by_phase[phase_name] = phase_artifacts

        return ArtifactsResponse(
            run_id=run_id,
            artifacts_by_phase=artifacts_by_phase,
            total_count=total_count,
        )

    async def get_metrics(self, run_id: str) -> MetricsSummary:
        """
        Get comprehensive metrics for a run.

        Args:
            run_id: Run identifier

        Returns:
            MetricsSummary with performance and governance metrics
        """
        state = await self._project_repo.load(run_id)

        phases_metrics = []
        total_tokens = {"input": 0, "output": 0}
        total_cost = 0.0
        artifacts_total = 0
        errors_count = 0

        for phase_name, phase_state in state.phases.items():
            # Calculate phase token usage
            phase_tokens = {"input": 0, "output": 0}
            agents_executed = []

            for agent_id, agent_state in phase_state.agent_states.items():
                agents_executed.append(agent_id)
                if agent_state.token_usage:
                    phase_tokens["input"] += agent_state.token_usage.input_tokens
                    phase_tokens["output"] += agent_state.token_usage.output_tokens

            total_tokens["input"] += phase_tokens["input"]
            total_tokens["output"] += phase_tokens["output"]

            # Calculate cost (rough estimate: $0.003/1K input, $0.015/1K output)
            phase_cost = (
                (phase_tokens["input"] / 1000) * 0.003 +
                (phase_tokens["output"] / 1000) * 0.015
            )
            total_cost += phase_cost

            artifacts_count = len(phase_state.artifacts)
            artifacts_total += artifacts_count

            if phase_state.error:
                errors_count += 1

            phase_metrics = PhaseMetrics(
                phase=phase_name,
                duration_seconds=self._calculate_duration(
                    phase_state.started_at,
                    phase_state.completed_at,
                ) or 0.0,
                token_usage=phase_tokens,
                cost_usd=phase_cost,
                agents_executed=agents_executed,
                artifacts_generated=artifacts_count,
                governance_passed=True,  # TODO: Get from governance results
                governance_warnings=[],
            )
            phases_metrics.append(phase_metrics)

        return MetricsSummary(
            run_id=run_id,
            total_duration_seconds=self._calculate_total_duration(state) or 0.0,
            total_token_usage=total_tokens,
            total_cost_usd=total_cost,
            phases_metrics=phases_metrics,
            governance_score=1.0 if errors_count == 0 else 0.8,
            hygiene_score=1.0,  # TODO: Calculate from workspace analysis
            artifacts_total=artifacts_total,
            errors_count=errors_count,
        )

    # Helper methods

    def _calculate_duration(
        self,
        started_at: datetime | None,
        completed_at: datetime | None,
    ) -> float | None:
        """Calculate duration in seconds between two timestamps."""
        if not started_at or not completed_at:
            return None
        return (completed_at - started_at).total_seconds()

    def _calculate_total_duration(self, state: ProjectState) -> float | None:
        """Calculate total run duration."""
        if not state.phases:
            return None

        # Find earliest start and latest completion
        earliest_start = None
        latest_completion = None

        for phase_state in state.phases.values():
            if phase_state.started_at:
                if not earliest_start or phase_state.started_at < earliest_start:
                    earliest_start = phase_state.started_at
            if phase_state.completed_at:
                if not latest_completion or phase_state.completed_at > latest_completion:
                    latest_completion = phase_state.completed_at

        if earliest_start and latest_completion:
            return (latest_completion - earliest_start).total_seconds()
        return None

    def _get_next_phase(self, current_phase: PhaseType) -> PhaseType | None:
        """Get the next phase in the workflow."""
        phase_order = [
            PhaseType.PLANNING,
            PhaseType.ARCHITECTURE,
            PhaseType.DATA,
            PhaseType.DEVELOPMENT,
            PhaseType.QA,
            PhaseType.DOCUMENTATION,
        ]

        try:
            current_index = phase_order.index(current_phase)
            if current_index < len(phase_order) - 1:
                return phase_order[current_index + 1]
        except ValueError:
            pass

        return None

    def _determine_artifact_type(self, file_path: Path) -> str:
        """Determine artifact type from file extension and name."""
        suffix = file_path.suffix.lower()
        name = file_path.stem.lower()

        if "prd" in name:
            return "prd"
        elif "architecture" in name or "arch" in name:
            return "architecture"
        elif "requirements" in name or "req" in name:
            return "requirements"
        elif "test" in name:
            return "test"
        elif suffix in [".py", ".js", ".ts", ".java"]:
            return "code"
        elif suffix in [".md", ".txt"]:
            return "documentation"
        elif suffix == ".json":
            return "data"
        else:
            return "artifact"
