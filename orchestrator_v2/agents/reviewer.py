"""
Reviewer Agent for Orchestrator v2.

The Reviewer agent conducts code reviews and provides
feedback on implementation quality.

See ADR-001 for agent responsibilities.
"""

from orchestrator_v2.agents.base_agent import AgentMixin
from orchestrator_v2.core.state_models import (
    AgentContext,
    AgentOutput,
    AgentPlan,
    AgentPlanStep,
    AgentSummary,
    ProjectState,
    TaskDefinition,
)


class ReviewerAgent(AgentMixin):
    """Reviewer agent for code review.

    Responsibilities:
    - Code review
    - Implementation feedback
    - Best practices validation
    - Style consistency checks

    Subagents: None

    Skills:
    - code_review
    - best_practices
    - style_analysis

    Tools:
    - file_system
    - git
    - linter
    """

    id = "reviewer"
    role = "code_reviewer"
    _skills = ["code_review", "best_practices", "style_analysis"]
    _tools = ["file_system", "git", "linter"]

    def initialize(self, project_state: ProjectState) -> None:
        """Initialize reviewer with project context.

        Loads:
        - Code to review
        - Review standards
        - Previous feedback
        - Style guides

        TODO: Load code changes for review
        TODO: Load review standards
        TODO: Load style guides
        """
        ...

    def plan(self, task: TaskDefinition) -> AgentPlan:
        """Plan review approach.

        Creates plan for:
        1. Code analysis
        2. Standards validation
        3. Feedback generation
        4. Recommendations

        TODO: Implement review planning
        TODO: Identify review focus areas
        TODO: Plan feedback format
        """
        ...

    def act(self, step: AgentPlanStep, context: AgentContext) -> AgentOutput:
        """Execute review step.

        May involve:
        - Analyzing code quality
        - Checking standards
        - Generating feedback
        - Suggesting improvements

        TODO: Implement review actions
        TODO: Generate review feedback
        TODO: Track review comments
        """
        ...

    def summarize(self, run_id: str) -> AgentSummary:
        """Summarize review work.

        Summary includes:
        - Code reviewed
        - Issues found
        - Recommendations
        - Approval status

        TODO: Collect review artifacts
        TODO: Report issues found
        TODO: Provide approval recommendation
        """
        ...

    def complete(self, project_state: ProjectState) -> None:
        """Complete reviewer execution.

        TODO: Finalize review
        TODO: Report metrics
        """
        ...
