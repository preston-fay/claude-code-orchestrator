"""
Base agent protocol for Orchestrator v2.

Defines the standard interface that all agents must implement,
following the agent lifecycle defined in ADR-001.
"""

from typing import Protocol, runtime_checkable

from orchestrator_v2.core.state_models import (
    AgentContext,
    AgentOutput,
    AgentPlan,
    AgentPlanStep,
    AgentSummary,
    ProjectState,
    TaskDefinition,
)


@runtime_checkable
class BaseAgent(Protocol):
    """Base protocol for all Orchestrator v2 agents.

    All agents follow a standardized lifecycle:
    1. Initialize - Load context and prepare for execution
    2. Plan - Analyze task and create execution plan
    3. Act - Execute plan steps with tools/skills
    4. Summarize - Produce structured output
    5. Complete - Cleanup and report metrics

    See ADR-001 for complete agent architecture.
    """

    id: str
    role: str

    def initialize(self, project_state: ProjectState) -> None:
        """Initialize the agent with project context.

        This loads:
        - Previous artifacts and decisions
        - Governance constraints
        - Available skills and tools
        - Budget limits

        Args:
            project_state: Current project state.

        TODO: Load agent-specific context
        TODO: Initialize skill/tool references
        TODO: Set up token tracking
        """
        ...

    def plan(self, task: TaskDefinition) -> AgentPlan:
        """Create an execution plan for the task.

        The agent analyzes the task and creates a sequence
        of steps to accomplish it.

        Args:
            task: Task to plan for.

        Returns:
            Execution plan with steps.

        TODO: Implement planning logic
        TODO: Select appropriate skills
        TODO: Estimate token usage
        """
        ...

    def act(self, step: AgentPlanStep, context: AgentContext) -> AgentOutput:
        """Execute a single plan step.

        This may involve:
        - Invoking tools
        - Executing skills
        - Generating outputs

        Args:
            step: Plan step to execute.
            context: Current agent context.

        Returns:
            Output from step execution.

        TODO: Implement step execution
        TODO: Track tool invocations
        TODO: Validate outputs
        """
        ...

    def summarize(self, run_id: str) -> AgentSummary:
        """Summarize the agent's execution.

        Creates a structured summary including:
        - Success/failure status
        - Artifacts produced
        - Token usage
        - Recommendations

        Args:
            run_id: Current run identifier.

        Returns:
            Execution summary.

        TODO: Implement summarization
        TODO: Collect all artifacts
        TODO: Calculate total token usage
        """
        ...

    def complete(self, project_state: ProjectState) -> None:
        """Complete agent execution and cleanup.

        This:
        - Finalizes any pending operations
        - Reports metrics
        - Releases resources

        Args:
            project_state: Final project state.

        TODO: Implement cleanup
        TODO: Report final metrics
        """
        ...


class AgentMixin:
    """Mixin providing common agent functionality.

    Role agents can inherit from this to get default
    implementations of common operations.
    """

    id: str
    role: str
    _skills: list[str]
    _tools: list[str]

    def get_available_skills(self) -> list[str]:
        """Get skills available to this agent.

        Returns:
            List of skill IDs.
        """
        return getattr(self, '_skills', [])

    def get_available_tools(self) -> list[str]:
        """Get tools available to this agent.

        Returns:
            List of tool IDs.
        """
        return getattr(self, '_tools', [])

    def can_delegate_to(self, subagent_id: str) -> bool:
        """Check if this agent can delegate to a subagent.

        Args:
            subagent_id: Subagent to check.

        Returns:
            True if delegation is allowed.

        TODO: Implement delegation checking
        TODO: Check subagent registry
        """
        return subagent_id.startswith(f"{self.id}.")
