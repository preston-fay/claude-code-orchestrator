"""
Base agent implementation for Orchestrator v2.

Provides the concrete BaseAgent class that all role agents inherit from,
implementing the full agent lifecycle defined in ADR-001.

LLM Integration:
- Uses LlmAgentMixin for prompt building and LLM calls
- Falls back to simulated responses when no AgentContext provided
- Parses LLM responses into structured AgentPlan and AgentOutput
"""

import hashlib
import logging
from datetime import datetime
from pathlib import Path
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field

from orchestrator_v2.engine.state_models import (
    AgentContext,
    AgentOutput,
    AgentPlan,
    AgentPlanStep,
    AgentState,
    AgentStatus,
    AgentSummary,
    ArtifactInfo,
    PhaseType,
    ProjectState,
    TaskDefinition,
    TokenUsage,
)
from orchestrator_v2.llm import get_provider_registry, LlmResult
from orchestrator_v2.agents.llm_agent_mixin import LlmAgentMixin
from orchestrator_v2.agents.response_parser import ActResponse


logger = logging.getLogger(__name__)


class BaseAgentConfig(BaseModel):
    """Configuration for an agent.

    See ADR-001 for agent configuration details.
    """
    id: str
    role: str
    description: str = ""
    skills: list[str] = Field(default_factory=list)
    tools: list[str] = Field(default_factory=list)
    subagents: dict[str, "BaseAgentConfig"] = Field(default_factory=dict)


class AgentEvent(BaseModel):
    """Event emitted during agent execution."""
    event_type: str
    agent_id: str
    phase: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    data: dict[str, Any] = Field(default_factory=dict)


class BaseAgent(LlmAgentMixin):
    """Base agent class with full lifecycle implementation.

    All role agents inherit from this class and can override
    specific lifecycle methods to customize behavior.

    Lifecycle (ADR-001):
    1. initialize - Load context and prepare
    2. plan - Create execution plan (calls LLM when context provided)
    3. act - Execute plan steps (calls LLM when context provided)
    4. summarize - Produce output summary
    5. complete - Cleanup and report

    LLM Integration:
    - When AgentContext is provided, methods call the real LLM
    - When no context is provided, returns simulated responses
    - Uses prompt templates from subagent_prompts/ directory

    See ADR-001 for agent architecture details.
    """

    def __init__(self, config: BaseAgentConfig):
        """Initialize the agent with configuration.

        Args:
            config: Agent configuration.
        """
        self.config = config
        self.id = config.id
        self.role = config.role
        self._skills: list[str] = config.skills.copy()
        self._tools: list[str] = config.tools.copy()
        self._events: list[AgentEvent] = []
        self._artifacts: list[ArtifactInfo] = []
        self._token_usage = TokenUsage()
        self._project_state: ProjectState | None = None
        self._agent_context: AgentContext | None = None

    def load_skills(self) -> list[str]:
        """Load skills from registry based on agent config.

        Returns:
            List of loaded skill IDs.
        """
        # Skills are loaded from config for now
        # Will integrate with SkillRegistry in future
        return self._skills

    def load_tools(self) -> list[str]:
        """Load tools from registry based on agent config.

        Returns:
            List of loaded tool IDs.
        """
        # Tools are loaded from config for now
        # Will integrate with ToolRegistry in future
        return self._tools

    def _record_event(self, event_type: str, phase: str, **data: Any) -> AgentEvent:
        """Record an event during execution.

        Args:
            event_type: Type of event.
            phase: Current phase.
            **data: Additional event data.

        Returns:
            Created event.
        """
        event = AgentEvent(
            event_type=event_type,
            agent_id=self.id,
            phase=phase,
            data=data,
        )
        self._events.append(event)
        return event

    def _record_tokens(self, input_tokens: int, output_tokens: int) -> None:
        """Record token usage.

        Args:
            input_tokens: Input token count.
            output_tokens: Output token count.
        """
        self._token_usage.input_tokens += input_tokens
        self._token_usage.output_tokens += output_tokens
        self._token_usage.total_tokens += input_tokens + output_tokens

    async def _call_llm(
        self,
        prompt: str,
        context: AgentContext,
    ) -> LlmResult:
        """Call the LLM using the configured provider.

        This method uses the provider registry to route the call
        to the appropriate LLM provider based on context settings.

        Args:
            prompt: The formatted prompt to send.
            context: Agent context with provider and model settings.

        Returns:
            LlmResult with generated text and token usage.

        Raises:
            LlmProviderError: If the LLM call fails.
        """
        registry = get_provider_registry()

        # Get model from context or use default
        model = context.model or "claude-sonnet-4-5-20250929"

        # Call the provider
        result = await registry.generate(
            prompt=prompt,
            model=model,
            context=context,
        )

        # Record token usage
        self._record_tokens(result.input_tokens, result.output_tokens)

        return result

    def _create_artifact(
        self,
        filename: str,
        content: str,
        phase: PhaseType,
        project_id: str,
    ) -> ArtifactInfo:
        """Create an artifact file.

        Args:
            filename: Name of the artifact file.
            content: Content to write.
            phase: Current phase.
            project_id: Project identifier.

        Returns:
            Artifact information.
        """
        # Create artifact directory
        artifact_dir = Path(f"artifacts/{project_id}/{phase.value}/{self.id}")
        artifact_dir.mkdir(parents=True, exist_ok=True)

        # Write artifact
        file_path = artifact_dir / filename
        file_path.write_text(content)

        # Calculate hash
        sha256 = hashlib.sha256(content.encode()).hexdigest()

        artifact = ArtifactInfo(
            path=str(file_path),
            hash=sha256,
            size_bytes=len(content.encode()),
            artifact_type="file",
        )
        self._artifacts.append(artifact)
        return artifact

    def _create_artifact_from_response(
        self,
        artifact_data: Any,
        phase: PhaseType,
        project_id: str,
    ) -> ArtifactInfo:
        """Create an artifact from LLM response data.

        Args:
            artifact_data: Artifact data from parsed response.
            phase: Current phase.
            project_id: Project identifier.

        Returns:
            Artifact information.
        """
        filename = artifact_data.filename
        content = artifact_data.content
        return self._create_artifact(filename, content, phase, project_id)

    async def _run_subagent(
        self,
        subagent_config: BaseAgentConfig,
        phase: PhaseType,
        project_state: ProjectState,
        context: AgentContext | None = None,
    ) -> AgentSummary:
        """Run a subagent through its lifecycle.

        Args:
            subagent_config: Subagent configuration.
            phase: Current phase.
            project_state: Project state.
            context: Optional agent context for LLM calls.

        Returns:
            Subagent summary.
        """
        # Create subagent instance
        subagent = BaseAgent(subagent_config)

        # Run full lifecycle
        await subagent.initialize(project_state, context)

        task = TaskDefinition(
            task_id=f"{phase.value}_{subagent.id}_{uuid4().hex[:8]}",
            description=f"Subagent task for {subagent.role}",
        )
        plan = await subagent.plan(task, phase, project_state, context)
        output = await subagent.act(plan, project_state, context)
        summary = await subagent.summarize(plan, output, project_state)
        await subagent.complete(project_state)

        # Merge artifacts and token usage
        self._artifacts.extend(subagent._artifacts)
        self._token_usage.input_tokens += subagent._token_usage.input_tokens
        self._token_usage.output_tokens += subagent._token_usage.output_tokens
        self._token_usage.total_tokens += subagent._token_usage.total_tokens

        return summary

    async def initialize(
        self,
        project_state: ProjectState,
        context: AgentContext | None = None,
    ) -> AgentEvent:
        """Initialize the agent with project context.

        Args:
            project_state: Current project state.
            context: Optional agent context for LLM calls.

        Returns:
            Initialization event.
        """
        self._project_state = project_state
        self._agent_context = context

        # Load skills and tools
        self.load_skills()
        self.load_tools()

        # Record token usage for initialization
        self._record_tokens(input_tokens=100, output_tokens=50)

        # Emit event
        event = self._record_event(
            "agent_initialized",
            project_state.current_phase.value,
            skills=self._skills,
            tools=self._tools,
            has_llm_context=context is not None,
        )

        logger.info(
            f"Agent {self.id} initialized for project {project_state.project_id}, "
            f"LLM context: {'available' if context else 'not available'}"
        )

        return event

    async def plan(
        self,
        task: TaskDefinition,
        phase: PhaseType,
        project_state: ProjectState,
        context: AgentContext | None = None,
    ) -> AgentPlan:
        """Create an execution plan for the task.

        When an AgentContext is provided, this method calls the LLM
        to generate a plan. Otherwise, it returns a simulated plan.

        Args:
            task: Task to plan for.
            phase: Current phase.
            project_state: Project state.
            context: Optional agent context for LLM calls.

        Returns:
            Execution plan.
        """
        # Use stored context if not provided
        ctx = context or self._agent_context

        # Call LLM via mixin if context available
        plan_response = await self._llm_plan(task, phase, project_state, ctx)

        # Convert response to AgentPlan
        steps = []
        for i, step_data in enumerate(plan_response.steps):
            step_id = step_data.get("step_id", f"{task.task_id}_step_{i+1}")
            description = step_data.get("description", f"Step {i+1}")
            estimated_tokens = step_data.get("estimated_tokens", 500)

            steps.append(AgentPlanStep(
                step_id=step_id,
                description=description,
                estimated_tokens=estimated_tokens,
            ))

        # Ensure at least one step
        if not steps:
            steps = [AgentPlanStep(
                step_id=f"{task.task_id}_step_1",
                description=f"{self.role} execution step",
            )]

        plan = AgentPlan(
            plan_id=f"{task.task_id}_plan",
            agent_id=self.id,
            task_id=task.task_id,
            steps=steps,
            estimated_tokens=sum(s.estimated_tokens for s in steps),
            analysis=plan_response.analysis,
            expected_outputs=plan_response.outputs,
            dependencies=plan_response.dependencies,
            validation_criteria=plan_response.validation_criteria,
        )

        # Emit event
        self._record_event(
            "agent_planned",
            phase.value,
            plan_id=plan.plan_id,
            steps=len(plan.steps),
            used_llm=ctx is not None,
        )

        logger.info(
            f"Agent {self.id} created plan with {len(plan.steps)} steps "
            f"for task {task.task_id}"
        )

        return plan

    async def act(
        self,
        plan: AgentPlan,
        project_state: ProjectState,
        context: AgentContext | None = None,
    ) -> AgentOutput:
        """Execute the plan steps.

        When an AgentContext is provided, this method calls the LLM
        to execute each step. Otherwise, it returns simulated output.

        Args:
            plan: Execution plan.
            project_state: Project state.
            context: Optional agent context for LLM calls.

        Returns:
            Execution output with artifacts.
        """
        phase = project_state.current_phase

        # Use stored context if not provided
        ctx = context or self._agent_context

        # Execute via LLM mixin
        act_response = await self._llm_act(plan, project_state, ctx)

        # Create artifacts from response
        for artifact_data in act_response.artifacts:
            self._create_artifact_from_response(artifact_data, phase, project_state.project_id)

        # Run subagents if configured
        subagent_summaries = []
        for subagent_id, subagent_config in self.config.subagents.items():
            summary = await self._run_subagent(subagent_config, phase, project_state, ctx)
            subagent_summaries.append(summary)

        # Emit event
        self._record_event(
            "agent_acted",
            phase.value,
            artifacts=len(self._artifacts),
            subagents=len(subagent_summaries),
            used_llm=ctx is not None,
            success=act_response.success,
        )

        logger.info(
            f"Agent {self.id} completed execution: {len(self._artifacts)} artifacts, "
            f"success={act_response.success}"
        )

        return AgentOutput(
            step_id=plan.steps[0].step_id if plan.steps else "no_step",
            success=act_response.success,
            artifacts=self._artifacts.copy(),
            token_usage=TokenUsage(
                input_tokens=self._token_usage.input_tokens,
                output_tokens=self._token_usage.output_tokens,
                total_tokens=self._token_usage.total_tokens,
            ),
            execution_summary=act_response.execution_summary,
            recommendations=act_response.recommendations,
        )

    async def summarize(
        self,
        plan: AgentPlan,
        output: AgentOutput,
        project_state: ProjectState,
    ) -> AgentSummary:
        """Summarize the agent's execution.

        Args:
            plan: Execution plan.
            output: Execution output.
            project_state: Project state.

        Returns:
            Execution summary.
        """
        # Record token usage for summarization
        self._record_tokens(input_tokens=100, output_tokens=100)

        summary = AgentSummary(
            agent_id=self.id,
            task_id=plan.task_id,
            success=output.success,
            summary=f"{self.role.title()} completed {len(plan.steps)} steps, "
                    f"produced {len(self._artifacts)} artifacts",
            artifacts=self._artifacts.copy(),
            total_token_usage=TokenUsage(
                input_tokens=self._token_usage.input_tokens,
                output_tokens=self._token_usage.output_tokens,
                total_tokens=self._token_usage.total_tokens,
            ),
        )

        # Emit event
        self._record_event(
            "agent_summarized",
            project_state.current_phase.value,
            summary=summary.summary,
        )

        return summary

    async def complete(self, project_state: ProjectState) -> AgentEvent:
        """Complete agent execution and cleanup.

        Args:
            project_state: Final project state.

        Returns:
            Completion event.
        """
        event = self._record_event(
            "agent_completed",
            project_state.current_phase.value,
            total_tokens=self._token_usage.total_tokens,
            artifacts=len(self._artifacts),
        )

        logger.info(
            f"Agent {self.id} completed: {self._token_usage.total_tokens} tokens, "
            f"{len(self._artifacts)} artifacts"
        )

        return event

    def get_state(self) -> AgentState:
        """Get the current agent state.

        Returns:
            Agent state with all tracked information.
        """
        return AgentState(
            agent_id=self.id,
            status=AgentStatus.COMPLETE,
            token_usage=self._token_usage,
            summary=f"Completed with {len(self._artifacts)} artifacts",
        )
