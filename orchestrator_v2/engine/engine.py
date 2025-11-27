"""
Workflow Engine for Orchestrator v2.

The WorkflowEngine is the central orchestration component that coordinates
the execution of a complete project workflow through phases, agents,
checkpoints, and governance gates.

See docs/orchestrator-v2-architecture.md for architecture overview.
"""

import asyncio
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Mapping
from uuid import uuid4

from orchestrator_v2.agents.base_agent import BaseAgent
from orchestrator_v2.agents.factory import create_agent, get_agent_pool
from orchestrator_v2.engine.model_selection import (
    select_model_for_agent,
    estimate_tokens_for_agent,
)
from orchestrator_v2.llm.retry import retry_async, RetryConfig, LLMRetryError
from orchestrator_v2.phases.execution_service import PhaseExecutionService
from orchestrator_v2.telemetry.budget_enforcer import (
    BudgetEnforcer,
    BudgetExceededError as BudgetError,
)
from orchestrator_v2.telemetry.events import EventType
from orchestrator_v2.telemetry.events_repository import emit_event
from orchestrator_v2.user.models import UserProfile
from orchestrator_v2.user.repository import FileSystemUserRepository

logger = logging.getLogger(__name__)
from orchestrator_v2.checkpoints.checkpoint_manager import CheckpointManager
from orchestrator_v2.engine.exceptions import (
    BudgetExceededError,
    CheckpointError,
    GovernanceError,
    OrchestratorError,
    PhaseError,
)
from orchestrator_v2.engine.phase_manager import PhaseManager
from orchestrator_v2.engine.state_models import (
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
from orchestrator_v2.workspace.repo_adapter import RepoAdapter
from orchestrator_v2.telemetry.token_tracking import TokenTracker
from orchestrator_v2.workspace.models import WorkspaceConfig


# LLM retry configuration for agent execution
AGENT_RETRY_CONFIG = RetryConfig(
    max_attempts=3,
    initial_delay=2.0,
    max_delay=30.0,
    exponential_base=2.0,
    jitter=True,
)


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
        user_repository: FileSystemUserRepository | None = None,
        use_real_agents: bool = True,
    ):
        """Initialize the WorkflowEngine.

        Args:
            phase_manager: Phase manager instance.
            checkpoint_manager: Checkpoint manager instance.
            governance_engine: Governance engine instance.
            token_tracker: Token tracker instance.
            agents: Mapping of agent_id to agent instances.
            workspace: Workspace configuration for file isolation.
            user_repository: User repository for BYOK and entitlements.
            use_real_agents: Whether to create real agent instances (default True).
        """
        self._phase_manager = phase_manager or PhaseManager()
        self._checkpoint_manager = checkpoint_manager or CheckpointManager()
        self._governance_engine = governance_engine or GovernanceEngine()
        self._token_tracker = token_tracker or TokenTracker()
        self._agents = dict(agents) if agents else {}
        self._phase_execution_service = PhaseExecutionService()
        self._state: ProjectState | None = None
        self._workspace: WorkspaceConfig | None = workspace
        self._repo_adapter: RepoAdapter | None = None
        self._user_repository = user_repository or FileSystemUserRepository()
        self._budget_enforcer = BudgetEnforcer(self._user_repository, self._token_tracker)
        self._use_real_agents = use_real_agents

        # Initialize repo adapter if workspace provided
        if workspace:
            self._repo_adapter = RepoAdapter(workspace)

    def _emit_event(
        self,
        event_type: EventType,
        message: str,
        phase: str | None = None,
        agent_id: str | None = None,
        **data,
    ) -> None:
        """Emit an event for the current project.

        Args:
            event_type: Type of event.
            message: Human-readable message.
            phase: Current phase (optional).
            agent_id: Agent identifier (optional).
            **data: Additional event data.
        """
        if self._state is None:
            return

        emit_event(
            event_type=event_type,
            project_id=self._state.project_id,
            message=message,
            phase=phase,
            agent_id=agent_id,
            **data,
        )

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

    def _get_or_create_agent(self, agent_id: str) -> BaseAgent | None:
        """Get an agent instance, creating it if needed.
        
        Args:
            agent_id: Agent identifier.
            
        Returns:
            Agent instance or None if not available.
        """
        # First check pre-registered agents
        if agent_id in self._agents:
            return self._agents[agent_id]
        
        # Try to create a real agent if enabled
        if self._use_real_agents:
            agent = create_agent(agent_id)
            if agent is not None:
                self._agents[agent_id] = agent
                logger.info(f"Created real agent instance for {agent_id}")
                return agent
        
        return None

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

        # Emit workflow started event
        self._emit_event(
            EventType.WORKFLOW_STARTED,
            f"Project '{project_name}' workflow started",
            phase=PhaseType.PLANNING.value,
            client=client,
        )

        return self._state

    async def run_phase(
        self,
        phase: PhaseType | None = None,
        user: UserProfile | None = None,
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

        # Emit phase started event
        self._emit_event(
            EventType.PHASE_STARTED,
            f"Phase {phase.value} started with {len(phase_def.responsible_agents)} agents",
            phase=phase.value,
            agents=phase_def.responsible_agents,
        )

        try:
            # Execute agents in parallel
            logger.info(
                f"Running phase {phase.value} with {len(phase_def.responsible_agents)} agents: "
                f"{phase_def.responsible_agents}"
            )

            agent_states = await self._run_agents_for_phase(phase_def, user)

            # Store results and track usage
            for agent_id, agent_state in agent_states.items():
                self.state.agent_states[agent_id] = agent_state

                # Track token usage
                self._token_tracker.track_llm_call(
                    workflow_id=self.state.project_id,
                    phase=phase.value,
                    agent_id=agent_id,
                    input_tokens=agent_state.token_usage.input_tokens,
                    output_tokens=agent_state.token_usage.output_tokens,
                )

                # Record usage for budget tracking
                if user and agent_state.token_usage:
                    await self._budget_enforcer.record_usage(
                        user=user,
                        project_id=self.state.project_id,
                        agent_role=agent_id,
                        model=agent_state.model_used or "unknown",
                        input_tokens=agent_state.token_usage.input_tokens,
                        output_tokens=agent_state.token_usage.output_tokens,
                    )

            logger.info(f"Phase {phase.value} agents completed successfully")

            # Generate artifacts using PhaseExecutionService
            if user:
                try:
                    logger.info(f"Generating artifacts for phase {phase.value}")
                    artifact_result = await self._phase_execution_service.execute_phase(
                        phase=phase,
                        project_state=self.state,
                        user=user,
                    )

                    # Store artifacts in phase state
                    if artifact_result.get("artifacts"):
                        for artifact_path in artifact_result["artifacts"]:
                            phase_state.artifacts[artifact_path] = ArtifactInfo(
                                path=artifact_path,
                                agent_id="phase_executor",
                                created_at=datetime.utcnow(),
                            )

                    logger.info(f"Generated {len(artifact_result.get('artifacts', []))} artifacts")
                except Exception as e:
                    logger.warning(f"Artifact generation failed for {phase.value}: {e}")

            # Evaluate governance gates
            governance_results = await self.evaluate_governance(phase)

            if not governance_results.passed:
                blocked_gates = [
                    g.gate_id for g in governance_results.quality_gates
                    if g.status == GateStatus.BLOCKED
                ]
                phase_state.status = "failed"
                phase_state.error_message = f"Blocked by gates: {blocked_gates}"

                # Emit phase failed event
                self._emit_event(
                    EventType.PHASE_FAILED,
                    f"Phase {phase.value} blocked by governance gates",
                    phase=phase.value,
                    blocked_gates=blocked_gates,
                )

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

            # Emit phase completed event
            self._emit_event(
                EventType.PHASE_COMPLETED,
                f"Phase {phase.value} completed successfully",
                phase=phase.value,
            )

        except Exception as e:
            phase_state.status = "failed"
            phase_state.error_message = str(e)

            # Emit phase failed event (if not already emitted)
            if not isinstance(e, GovernanceError):
                self._emit_event(
                    EventType.PHASE_FAILED,
                    f"Phase {phase.value} failed: {str(e)}",
                    phase=phase.value,
                    error=str(e),
                )
            raise

        return phase_state

    def _build_agent_context(
        self,
        task: TaskDefinition,
        user: UserProfile | None = None,
        model_config: Any | None = None,
    ) -> AgentContext:
        """Build an AgentContext with all necessary information.
        
        Args:
            task: Task definition for the agent.
            user: User profile for BYOK and entitlements.
            model_config: Selected model configuration.
            
        Returns:
            Configured AgentContext.
        """
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

        # Set LLM provider info from user and model config
        if user:
            context.user_id = user.user_id
            context.llm_api_key = user.anthropic_api_key
            context.llm_provider = user.default_provider or "anthropic"
            context.model_preferences = user.entitlements.model_access if user.entitlements else []

        if model_config:
            context.provider = model_config.provider
            context.model = model_config.model
        elif user and user.default_model:
            context.model = user.default_model
        else:
            # Default model
            context.model = "claude-sonnet-4-5-20250929"
        
        return context

    async def _execute_agent(
        self,
        agent_id: str,
        phase: PhaseType,
        user: UserProfile | None = None,
        model_config: Any | None = None,
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
            user: User profile for BYOK and entitlements.
            model_config: Selected model configuration.

        Returns:
            Agent execution state.
        """
        # Create agent state
        agent_state = AgentState(
            agent_id=agent_id,
            status=AgentStatus.INITIALIZING,
            started_at=datetime.utcnow(),
        )

        # Get agent instance (creates real agent if available)
        agent = self._get_or_create_agent(agent_id)

        # Emit agent started event
        self._emit_event(
            EventType.AGENT_STARTED,
            f"Agent {agent_id} started",
            phase=phase.value,
            agent_id=agent_id,
        )

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

            # Emit agent completed event
            self._emit_event(
                EventType.AGENT_COMPLETED,
                f"Agent {agent_id} completed (stub)",
                phase=phase.value,
                agent_id=agent_id,
                tokens_used=700,
            )

            return agent_state

        try:
            # Create task definition
            task = TaskDefinition(
                task_id=f"{phase.value}_{agent_id}_{uuid4().hex[:8]}",
                description=f"Execute {phase.value} phase tasks",
                requirements=self.state.metadata.get("requirements", []),
            )
            
            # Build agent context with LLM credentials
            context = self._build_agent_context(task, user, model_config)

            # Initialize
            agent_state.status = AgentStatus.INITIALIZING
            logger.debug(f"Initializing agent {agent_id}")
            
            # Check if agent methods are async
            if asyncio.iscoroutinefunction(agent.initialize):
                await agent.initialize(self.state, context)
            else:
                agent.initialize(self.state, context)

            # Plan - PASS CONTEXT for real LLM calls
            agent_state.status = AgentStatus.PLANNING
            logger.debug(f"Agent {agent_id} planning with context (has API key: {bool(context.llm_api_key)})")
            
            if asyncio.iscoroutinefunction(agent.plan):
                plan = await agent.plan(task, phase, self.state, context)
            else:
                plan = agent.plan(task, phase, self.state, context)

            # Act - PASS CONTEXT for real LLM calls
            agent_state.status = AgentStatus.ACTING
            logger.debug(f"Agent {agent_id} executing {len(plan.steps)} steps")
            
            for step in plan.steps:
                if asyncio.iscoroutinefunction(agent.act):
                    output = await agent.act(plan, self.state, context)
                else:
                    output = agent.act(plan, self.state, context)
                context.previous_outputs.append(output)

            # Summarize
            agent_state.status = AgentStatus.SUMMARIZING
            if asyncio.iscoroutinefunction(agent.summarize):
                summary = await agent.summarize(self.state.run_id)
            else:
                summary = agent.summarize(self.state.run_id)

            # Complete
            if asyncio.iscoroutinefunction(agent.complete):
                await agent.complete(self.state)
            else:
                agent.complete(self.state)
                
            agent_state.status = AgentStatus.COMPLETE
            agent_state.completed_at = datetime.utcnow()
            agent_state.summary = summary.summary
            agent_state.token_usage = summary.total_token_usage or TokenUsage(
                input_tokens=0,
                output_tokens=0,
                total_tokens=0,
            )

            # Emit agent completed event
            self._emit_event(
                EventType.AGENT_COMPLETED,
                f"Agent {agent_id} completed successfully",
                phase=phase.value,
                agent_id=agent_id,
                tokens_used=agent_state.token_usage.total_tokens if agent_state.token_usage else 0,
            )

        except LLMRetryError as e:
            # LLM call failed after all retries
            agent_state.status = AgentStatus.FAILED
            agent_state.error_message = f"LLM call failed after {e.attempts} attempts: {e.last_error}"
            agent_state.completed_at = datetime.utcnow()

            # Emit agent failed event
            self._emit_event(
                EventType.AGENT_FAILED,
                f"Agent {agent_id} failed: LLM retry exhausted",
                phase=phase.value,
                agent_id=agent_id,
                error=str(e),
                attempts=e.attempts,
            )

        except Exception as e:
            agent_state.status = AgentStatus.FAILED
            agent_state.error_message = str(e)
            agent_state.completed_at = datetime.utcnow()

            # Emit agent failed event
            self._emit_event(
                EventType.AGENT_FAILED,
                f"Agent {agent_id} failed: {str(e)}",
                phase=phase.value,
                agent_id=agent_id,
                error=str(e),
            )

        return agent_state

    async def _run_agents_for_phase(
        self,
        phase_def: Any,  # PhaseDefinition
        user: UserProfile | None = None,
    ) -> dict[str, AgentState]:
        """
        Execute all responsible agents for a phase, possibly in parallel.

        Uses asyncio.gather to run agents concurrently when they have no
        dependencies on each other within the phase.

        Args:
            phase_def: Phase definition with responsible agents.
            user: User profile for BYOK and entitlements.

        Returns:
            Mapping of agent_id to AgentState results.
        """
        from orchestrator_v2.engine.state_models import PhaseDefinition

        agent_ids = phase_def.responsible_agents
        if not agent_ids:
            return {}

        logger.info(f"Starting parallel execution of {len(agent_ids)} agents")

        # Create tasks for all agents
        tasks = []
        for agent_id in agent_ids:
            tasks.append(self._execute_agent_with_budget(agent_id, phase_def.name, user))

        # Execute all agents in parallel
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Process results
        agent_states: dict[str, AgentState] = {}
        errors = []

        for agent_id, result in zip(agent_ids, results):
            if isinstance(result, Exception):
                logger.error(f"Agent {agent_id} failed: {result}")
                errors.append((agent_id, result))
                # Create failed state
                agent_states[agent_id] = AgentState(
                    agent_id=agent_id,
                    status=AgentStatus.FAILED,
                    error_message=str(result),
                    completed_at=datetime.utcnow(),
                )
            else:
                agent_states[agent_id] = result
                logger.info(
                    f"Agent {agent_id} completed: model={result.model_used}, "
                    f"tokens={result.token_usage.total_tokens}"
                )

        # If any agent failed, raise the first error
        if errors:
            agent_id, error = errors[0]
            raise PhaseError(f"Agent {agent_id} failed: {error}")

        logger.info(f"Parallel execution complete: {len(agent_states)} agents succeeded")
        return agent_states

    async def _execute_agent_with_budget(
        self,
        agent_id: str,
        phase: PhaseType,
        user: UserProfile | None = None,
    ) -> AgentState:
        """
        Execute an agent with budget checking and model selection.

        Args:
            agent_id: Agent to execute.
            phase: Current phase.
            user: User profile for BYOK and entitlements.

        Returns:
            Agent execution state.
        """
        # Select model for this agent
        model_config = select_model_for_agent(
            user=user,
            agent_role=agent_id,
            project_metadata=self.state.metadata if self._state else None,
        )

        logger.info(
            f"Selected model for {agent_id}: {model_config.provider}:{model_config.model}"
        )

        # Check budget before execution
        if user:
            estimated_tokens = estimate_tokens_for_agent(agent_id)
            try:
                await self._budget_enforcer.check_and_reserve(
                    user=user,
                    project_id=self.state.project_id,
                    estimated_tokens=estimated_tokens,
                )
            except BudgetError as e:
                logger.error(f"Budget exceeded for {agent_id}: {e}")
                raise BudgetExceededError(str(e))

        # Execute the agent with user and model config (with retry for LLM errors)
        try:
            agent_state = await retry_async(
                self._execute_agent,
                agent_id,
                phase,
                user,
                model_config,
                config=AGENT_RETRY_CONFIG,
            )
        except LLMRetryError:
            # Re-raise as-is for specific handling
            raise
        except Exception as e:
            # Other errors don't get retried
            raise

        # Update state with model info
        agent_state.model_used = model_config.model
        agent_state.provider_used = model_config.provider

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
        # Emit governance check started event
        self._emit_event(
            EventType.GOVERNANCE_CHECK_STARTED,
            f"Evaluating governance gates for phase {phase.value}",
            phase=phase.value,
        )

        results = await self._governance_engine.evaluate_phase_transition(
            project_state=self.state,
            phase=phase,
        )

        # Emit governance check result event
        if results.passed:
            self._emit_event(
                EventType.GOVERNANCE_CHECK_PASSED,
                f"Governance gates passed for phase {phase.value}",
                phase=phase.value,
            )
        else:
            self._emit_event(
                EventType.GOVERNANCE_CHECK_FAILED,
                f"Governance gates failed for phase {phase.value}",
                phase=phase.value,
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

        # Emit workflow completed event
        self._emit_event(
            EventType.WORKFLOW_COMPLETED,
            f"Project '{self.state.project_name}' workflow completed",
            completed_phases=[p.value for p in self.state.completed_phases],
        )

        return self.state
