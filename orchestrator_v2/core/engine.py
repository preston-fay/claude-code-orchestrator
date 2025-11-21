"""
Workflow Engine for Orchestrator v2.

The WorkflowEngine is the central orchestration component that coordinates
the execution of a complete project workflow through phases, agents,
checkpoints, and governance gates.

See docs/orchestrator-v2-architecture.md for architecture overview.
"""

from datetime import datetime
from pathlib import Path
from typing import Any, Mapping
from uuid import uuid4

from orchestrator_v2.agents.base_agent import BaseAgent
from orchestrator_v2.checkpoints.checkpoint_manager import CheckpointManager
from orchestrator_v2.core.exceptions import (
    BudgetExceededError,
    CheckpointError,
    GovernanceError,
    OrchestratorError,
    PhaseError,
)
from orchestrator_v2.core.phase_manager import PhaseManager
from orchestrator_v2.core.state_models import (
    AgentContext,
    AgentState,
    AgentStatus,
    AgentSummary,
    ArtifactInfo,
    CheckpointState,
    CheckpointType,
    GateResult,
    GateStatus,
    GovernanceResults,
    PhaseState,
    PhaseType,
    ProjectState,
    TaskDefinition,
    TokenUsage,
)
from orchestrator_v2.governance.governance_engine import GovernanceEngine
from orchestrator_v2.repo.adapter import RepoAdapter
from orchestrator_v2.telemetry.token_tracking import TokenTracker
from orchestrator_v2.workspace.models import WorkspaceConfig


class WorkflowEngine:
    """Central orchestration engine for Orchestrator v2.

    The WorkflowEngine coordinates:
    - Workflow initialization and state management
    - Phase transitions and checkpoint creation
    - Governance gate evaluation
    - Token budget enforcement
    - Error handling and recovery

    See ADR-001 for agent coordination patterns.
    See ADR-002 for phase and checkpoint model.
    """

    def __init__(
        self,
        phase_manager: PhaseManager | None = None,
        checkpoint_manager: CheckpointManager | None = None,
        governance_engine: GovernanceEngine | None = None,
        token_tracker: TokenTracker | None = None,
        agents: Mapping[str, BaseAgent] | None = None,
        workspace: WorkspaceConfig | None = None,
    ):
        """Initialize the WorkflowEngine.

        Args:
            phase_manager: Phase manager instance.
            checkpoint_manager: Checkpoint manager instance.
            governance_engine: Governance engine instance.
            token_tracker: Token tracker instance.
            agents: Mapping of agent_id to agent instances.
            workspace: Workspace configuration for file isolation.
        """
        self._phase_manager = phase_manager or PhaseManager()
        self._checkpoint_manager = checkpoint_manager or CheckpointManager()
        self._governance_engine = governance_engine or GovernanceEngine()
        self._token_tracker = token_tracker or TokenTracker()
        self._agents = agents or {}
        self._state: ProjectState | None = None
        self._workspace: WorkspaceConfig | None = workspace
        self._repo_adapter: RepoAdapter | None = None

        # Initialize repo adapter if workspace provided
        if workspace:
            self._repo_adapter = RepoAdapter(workspace)

    @property
    def workspace(self) -> WorkspaceConfig | None:
        """Get the workspace configuration."""
        return self._workspace

    @property
    def repo_adapter(self) -> RepoAdapter | None:
        """Get the repository adapter."""
        return self._repo_adapter

    def set_workspace(self, workspace: WorkspaceConfig) -> None:
        """Set the workspace configuration.

        Args:
            workspace: Workspace configuration.
        """
        self._workspace = workspace
        self._repo_adapter = RepoAdapter(workspace)

        # Update checkpoint manager to use workspace paths
        if workspace:
            self._checkpoint_manager = CheckpointManager(
                checkpoint_dir=workspace.state_path / "checkpoints"
            )

    @property
    def state(self) -> ProjectState:
        """Get current project state.

        Raises:
            OrchestratorError: If no project is initialized.
        """
        if self._state is None:
            raise OrchestratorError("No project initialized. Call start_project first.")
        return self._state

    @property
    def phase_manager(self) -> PhaseManager:
        """Get the phase manager."""
        return self._phase_manager

    async def start_project(
        self,
        intake_path: Path | None = None,
        project_name: str = "Untitled Project",
        client: str = "kearney-default",
        **kwargs: Any,
    ) -> ProjectState:
        """Start a new project workflow.

        This initializes the workflow by:
        1. Creating project state with initial phase
        2. Loading governance policies
        3. Setting up budget tracking
        4. Creating initial PRE checkpoint

        See ADR-002 for initialization flow.

        Args:
            intake_path: Optional path to intake.yaml file.
            project_name: Name of the project.
            client: Client identifier for governance.
            **kwargs: Additional configuration.

        Returns:
            Initialized ProjectState.
        """
        # Generate IDs
        project_id = str(uuid4())
        run_id = str(uuid4())

        # Create initial state - start at PLANNING phase
        self._state = ProjectState(
            project_id=project_id,
            run_id=run_id,
            project_name=project_name,
            client=client,
            current_phase=PhaseType.PLANNING,
            completed_phases=[],
            metadata=kwargs.get("metadata", {}),
        )

        # Load governance policy for client
        self._governance_engine.load_policy(client)

        # Set up budget tracking
        self._token_tracker.set_budget(project_id, self._state.budget_config)

        # Create initial PRE checkpoint
        await self.save_checkpoint(PhaseType.PLANNING, CheckpointType.PRE)

        return self._state

    async def run_phase(
        self,
        phase: PhaseType | None = None,
    ) -> PhaseState:
        """Execute a workflow phase.

        This runs a complete phase by:
        1. Creating PRE checkpoint
        2. Resolving phase definition and agents
        3. Executing each agent through its lifecycle
        4. Collecting artifacts and token usage
        5. Evaluating governance gates
        6. Creating POST checkpoint
        7. Advancing to next phase

        See ADR-001 for agent lifecycle.
        See ADR-002 for phase execution model.

        Args:
            phase: Phase to execute (defaults to current phase).

        Returns:
            Completed PhaseState.

        Raises:
            PhaseError: If phase execution fails.
            GovernanceError: If governance gates block.
        """
        if phase is None:
            phase = self.state.current_phase

        # Get phase definition
        phase_def = self._phase_manager.get_phase_definition(phase)

        # Create phase state
        phase_state = PhaseState(
            phase=phase,
            status="running",
            started_at=datetime.utcnow(),
            agent_ids=phase_def.responsible_agents,
        )

        # Store phase state
        self.state.phase_states[phase.value] = phase_state

        try:
            # Execute each responsible agent
            for agent_id in phase_def.responsible_agents:
                agent_state = await self._execute_agent(agent_id, phase)
                self.state.agent_states[agent_id] = agent_state

                # Track token usage
                self._token_tracker.track_llm_call(
                    workflow_id=self.state.project_id,
                    phase=phase.value,
                    agent_id=agent_id,
                    input_tokens=agent_state.token_usage.input_tokens,
                    output_tokens=agent_state.token_usage.output_tokens,
                )

            # Evaluate governance gates
            governance_results = await self.evaluate_governance(phase)

            if not governance_results.passed:
                blocked_gates = [
                    g.gate_id for g in governance_results.quality_gates
                    if g.status == GateStatus.BLOCKED
                ]
                phase_state.status = "failed"
                phase_state.error_message = f"Blocked by gates: {blocked_gates}"
                raise GovernanceError(
                    f"Phase {phase.value} blocked by governance gates: {blocked_gates}"
                )

            # Mark phase as completed
            phase_state.status = "completed"
            phase_state.completed_at = datetime.utcnow()

            # Create POST checkpoint
            await self.save_checkpoint(phase, CheckpointType.POST)

            # Add to completed phases
            if phase not in self.state.completed_phases:
                self.state.completed_phases.append(phase)

            # Advance to next phase
            next_phase_def = self._phase_manager.get_next_phase(self.state)
            if next_phase_def:
                self.state.current_phase = next_phase_def.name
            else:
                self.state.current_phase = PhaseType.COMPLETE

            self.state.updated_at = datetime.utcnow()

        except Exception as e:
            phase_state.status = "failed"
            phase_state.error_message = str(e)
            raise

        return phase_state

    async def _execute_agent(
        self,
        agent_id: str,
        phase: PhaseType,
    ) -> AgentState:
        """Execute an agent through its lifecycle.

        Agent lifecycle (ADR-001):
        1. Initialize - Load context
        2. Plan - Create execution plan
        3. Act - Execute plan steps
        4. Summarize - Produce output
        5. Complete - Cleanup

        Args:
            agent_id: Agent to execute.
            phase: Current phase.

        Returns:
            Agent execution state.
        """
        # Create agent state
        agent_state = AgentState(
            agent_id=agent_id,
            status=AgentStatus.INITIALIZING,
            started_at=datetime.utcnow(),
        )

        # Get agent instance (or use stub)
        agent = self._agents.get(agent_id)

        if agent is None:
            # Stub execution for agents not yet implemented
            agent_state.status = AgentStatus.COMPLETE
            agent_state.completed_at = datetime.utcnow()
            agent_state.summary = f"Stub execution for {agent_id} in {phase.value}"
            # Simulate token usage
            agent_state.token_usage = TokenUsage(
                input_tokens=500,
                output_tokens=200,
                total_tokens=700,
            )
            return agent_state

        try:
            # Initialize
            agent_state.status = AgentStatus.INITIALIZING
            agent.initialize(self.state)

            # Plan
            agent_state.status = AgentStatus.PLANNING
            task = TaskDefinition(
                task_id=f"{phase.value}_{agent_id}_{uuid4().hex[:8]}",
                description=f"Execute {phase.value} phase tasks",
                requirements=self.state.metadata.get("requirements", []),
            )
            plan = agent.plan(task)

            # Act
            agent_state.status = AgentStatus.ACTING
            context = AgentContext(
                project_state=self.state,
                task=task,
            )
            # Add workspace paths if available
            if self._workspace:
                context.workspace_root = str(self._workspace.workspace_root)
                context.repo_path = str(self._workspace.repo_path)
                context.artifacts_path = str(self._workspace.artifacts_path)
                context.logs_path = str(self._workspace.logs_path)
                context.tmp_path = str(self._workspace.tmp_path)

            for step in plan.steps:
                output = agent.act(step, context)
                context.previous_outputs.append(output)

            # Summarize
            agent_state.status = AgentStatus.SUMMARIZING
            summary = agent.summarize(self.state.run_id)

            # Complete
            agent.complete(self.state)
            agent_state.status = AgentStatus.COMPLETE
            agent_state.completed_at = datetime.utcnow()
            agent_state.summary = summary.summary
            agent_state.token_usage = summary.total_token_usage

        except Exception as e:
            agent_state.status = AgentStatus.FAILED
            agent_state.error_message = str(e)
            agent_state.completed_at = datetime.utcnow()

        return agent_state

    async def advance_phase(self) -> PhaseType | None:
        """Advance to and execute the next phase.

        This is the main entry point for stepping through the workflow.

        Returns:
            The new current phase, or None if workflow is complete.
        """
        # Check if workflow is complete
        if self.state.current_phase == PhaseType.COMPLETE:
            return None

        # Run the current phase
        await self.run_phase(self.state.current_phase)

        # Return new current phase
        if self.state.current_phase == PhaseType.COMPLETE:
            return None
        return self.state.current_phase

    async def load_checkpoint(
        self,
        checkpoint_id: str,
    ) -> CheckpointState:
        """Load a checkpoint by ID.

        Args:
            checkpoint_id: Checkpoint identifier.

        Returns:
            Loaded CheckpointState.
        """
        return await self._checkpoint_manager.load_checkpoint(checkpoint_id)

    async def save_checkpoint(
        self,
        phase: PhaseType,
        checkpoint_type: CheckpointType,
    ) -> CheckpointState:
        """Save a checkpoint for the current state.

        Args:
            phase: Phase this checkpoint is for.
            checkpoint_type: PRE or POST.

        Returns:
            Created CheckpointState.
        """
        checkpoint = await self._checkpoint_manager.save_checkpoint(
            phase=phase,
            checkpoint_type=checkpoint_type,
            state=self.state,
            agent_states=self.state.agent_states,
            artifacts={},  # Artifacts would be collected from phase
            governance=GovernanceResults(),
        )

        # Track checkpoint in state
        self.state.checkpoints.append(checkpoint.id)
        self.state.current_checkpoint_id = checkpoint.id

        return checkpoint

    async def rollback_to_checkpoint(
        self,
        checkpoint_id: str,
    ) -> None:
        """Rollback workflow to a previous checkpoint.

        Args:
            checkpoint_id: Checkpoint to rollback to.
        """
        await self._checkpoint_manager.rollback(checkpoint_id)

    async def evaluate_governance(
        self,
        phase: PhaseType,
    ) -> GovernanceResults:
        """Evaluate governance gates for a phase.

        Args:
            phase: Phase to evaluate gates for.

        Returns:
            GovernanceResults with gate outcomes.
        """
        results = await self._governance_engine.evaluate_phase_transition(
            from_phase=phase,
            to_phase=self._get_next_phase_type(phase),
            state=self.state,
        )

        # Log governance evaluation
        self._governance_engine.audit_log(
            gate_id="phase_transition",
            phase=phase.value,
            result=GateResult(
                gate_id="phase_transition",
                status=GateStatus.PASSED if results.passed else GateStatus.BLOCKED,
                message=f"Phase {phase.value} governance evaluation",
            ),
            context={"workflow_id": self.state.project_id},
        )

        return results

    def _get_next_phase_type(self, current: PhaseType) -> PhaseType:
        """Get next phase type for governance evaluation."""
        next_def = self._phase_manager.get_next_phase(self.state)
        return next_def.name if next_def else PhaseType.COMPLETE

    async def get_status(self) -> dict[str, Any]:
        """Get current workflow status.

        Returns:
            Status dict with phase, progress, and metrics.
        """
        progress = self._phase_manager.get_phase_progress(self.state)
        usage = self._token_tracker.get_usage(self.state.project_id)

        return {
            "project_id": self.state.project_id,
            "run_id": self.state.run_id,
            "project_name": self.state.project_name,
            "current_phase": self.state.current_phase.value,
            "completed_phases": [p.value for p in self.state.completed_phases],
            "progress": progress,
            "token_usage": {
                "input_tokens": usage.input_tokens,
                "output_tokens": usage.output_tokens,
                "total_tokens": usage.total_tokens,
                "cost_usd": float(usage.cost_usd),
            },
            "checkpoints": self.state.checkpoints,
        }

    async def complete(self) -> ProjectState:
        """Complete the workflow and finalize state.

        Returns:
            Final ProjectState.
        """
        self.state.current_phase = PhaseType.COMPLETE
        self.state.updated_at = datetime.utcnow()
        await self.save_checkpoint(PhaseType.COMPLETE, CheckpointType.POST)
        return self.state
