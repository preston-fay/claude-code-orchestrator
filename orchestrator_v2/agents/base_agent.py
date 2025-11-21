"""
Base agent implementation for Orchestrator v2.

Provides the concrete BaseAgent class that all role agents inherit from,
implementing the full agent lifecycle defined in ADR-001.
"""

import hashlib
from datetime import datetime
from pathlib import Path
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field

from orchestrator_v2.core.state_models import (
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


class BaseAgent:
    """Base agent class with full lifecycle implementation.

    All role agents inherit from this class and can override
    specific lifecycle methods to customize behavior.

    Lifecycle (ADR-001):
    1. initialize - Load context and prepare
    2. plan - Create execution plan
    3. act - Execute plan steps
    4. summarize - Produce output summary
    5. complete - Cleanup and report

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

    async def _run_subagent(
        self,
        subagent_config: BaseAgentConfig,
        phase: PhaseType,
        project_state: ProjectState,
    ) -> AgentSummary:
        """Run a subagent through its lifecycle.

        Args:
            subagent_config: Subagent configuration.
            phase: Current phase.
            project_state: Project state.

        Returns:
            Subagent summary.
        """
        # Create subagent instance
        subagent = BaseAgent(subagent_config)

        # Run full lifecycle
        await subagent.initialize(project_state)

        task = TaskDefinition(
            task_id=f"{phase.value}_{subagent.id}_{uuid4().hex[:8]}",
            description=f"Subagent task for {subagent.role}",
        )
        plan = await subagent.plan(task, phase, project_state)
        output = await subagent.act(plan, project_state)
        summary = await subagent.summarize(plan, output, project_state)
        await subagent.complete(project_state)

        # Merge artifacts and token usage
        self._artifacts.extend(subagent._artifacts)
        self._token_usage.input_tokens += subagent._token_usage.input_tokens
        self._token_usage.output_tokens += subagent._token_usage.output_tokens
        self._token_usage.total_tokens += subagent._token_usage.total_tokens

        return summary

    async def initialize(self, project_state: ProjectState) -> AgentEvent:
        """Initialize the agent with project context.

        Args:
            project_state: Current project state.

        Returns:
            Initialization event.
        """
        self._project_state = project_state

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
        )

        return event

    async def plan(
        self,
        task: TaskDefinition,
        phase: PhaseType,
        project_state: ProjectState,
    ) -> AgentPlan:
        """Create an execution plan for the task.

        Args:
            task: Task to plan for.
            phase: Current phase.
            project_state: Project state.

        Returns:
            Execution plan.
        """
        # Record token usage for planning
        self._record_tokens(input_tokens=200, output_tokens=100)

        # Create basic plan
        plan = AgentPlan(
            plan_id=f"{task.task_id}_plan",
            agent_id=self.id,
            task_id=task.task_id,
            steps=[
                AgentPlanStep(
                    step_id=f"{task.task_id}_step_1",
                    description=f"{self.role} execution step",
                ),
            ],
            estimated_tokens=500,
        )

        # Emit event
        self._record_event(
            "agent_planned",
            phase.value,
            plan_id=plan.plan_id,
            steps=len(plan.steps),
        )

        return plan

    async def act(
        self,
        plan: AgentPlan,
        project_state: ProjectState,
    ) -> AgentOutput:
        """Execute the plan steps.

        Args:
            plan: Execution plan.
            project_state: Project state.

        Returns:
            Execution output with artifacts.
        """
        phase = project_state.current_phase

        # Record token usage for acting
        self._record_tokens(input_tokens=300, output_tokens=200)

        # Create placeholder artifact
        content = f"""# {self.role.title()} Output

## Agent: {self.id}
## Phase: {phase.value}
## Task: {plan.task_id}

### Summary
This is a placeholder artifact from the {self.role} agent.

### Steps Executed
"""
        for step in plan.steps:
            content += f"- {step.description}\n"

        content += f"\n### Generated at: {datetime.utcnow().isoformat()}\n"

        artifact = self._create_artifact(
            f"{self.role}_output.md",
            content,
            phase,
            project_state.project_id,
        )

        # Run subagents if configured
        subagent_summaries = []
        for subagent_id, subagent_config in self.config.subagents.items():
            summary = await self._run_subagent(subagent_config, phase, project_state)
            subagent_summaries.append(summary)

        # Emit event
        self._record_event(
            "agent_acted",
            phase.value,
            artifacts=len(self._artifacts),
            subagents=len(subagent_summaries),
        )

        return AgentOutput(
            step_id=plan.steps[0].step_id if plan.steps else "no_step",
            success=True,
            artifacts=self._artifacts.copy(),
            token_usage=TokenUsage(
                input_tokens=self._token_usage.input_tokens,
                output_tokens=self._token_usage.output_tokens,
                total_tokens=self._token_usage.total_tokens,
            ),
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
