"""
Developer Agent for Orchestrator v2.

The Developer agent implements features, writes code, and handles
technical implementation. It is responsible for:
- Code implementation
- Test writing
- Code refactoring
- Technical integration

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


class DeveloperAgent(AgentMixin):
    """Developer agent for code implementation.

    Responsibilities:
    - Feature implementation
    - Writing production code
    - Writing tests
    - Code refactoring
    - Integration with existing code

    Subagents:
    - developer.frontend: Frontend specialization (React, CSS)
    - developer.backend: Backend specialization (FastAPI, database)
    - developer.infra: Infrastructure specialization

    Skills:
    - code_generation
    - test_writing
    - refactoring

    Tools:
    - file_system
    - git
    - python_executor
    - linter
    """

    id = "developer"
    role = "developer"
    _skills = ["code_generation", "test_writing", "refactoring"]
    _tools = ["file_system", "git", "python_executor", "linter"]

    def initialize(self, project_state: ProjectState) -> None:
        """Initialize developer with project context.

        Loads:
        - Architecture decisions
        - Code standards
        - Existing codebase structure
        - Test requirements

        TODO: Load architecture from ADRs
        TODO: Load code standards
        TODO: Analyze existing code
        """
        ...

    def plan(self, task: TaskDefinition) -> AgentPlan:
        """Plan development approach.

        Creates plan for:
        1. Code structure setup
        2. Feature implementation
        3. Test writing
        4. Integration
        5. Linting/formatting

        TODO: Implement development planning
        TODO: Break down into implementable steps
        TODO: Plan test coverage
        """
        ...

    def act(self, step: AgentPlanStep, context: AgentContext) -> AgentOutput:
        """Execute development step.

        May involve:
        - Writing code files
        - Running tests
        - Executing linters
        - Git operations

        TODO: Implement development actions
        TODO: Generate code artifacts
        TODO: Track code changes
        """
        ...

    def summarize(self, run_id: str) -> AgentSummary:
        """Summarize development work.

        Summary includes:
        - Code implemented
        - Tests written
        - Coverage metrics
        - Integration notes

        TODO: Collect code artifacts
        TODO: Report test coverage
        TODO: Provide QA handoff notes
        """
        ...

    def complete(self, project_state: ProjectState) -> None:
        """Complete developer execution.

        TODO: Finalize code changes
        TODO: Report metrics
        """
        ...
