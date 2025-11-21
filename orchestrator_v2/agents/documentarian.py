"""
Documentarian Agent for Orchestrator v2.

The Documentarian agent creates and maintains documentation,
README files, and user guides. It is responsible for:
- Technical documentation
- API documentation
- User guides
- README files

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


class DocumentarianAgent(AgentMixin):
    """Documentarian agent for documentation creation.

    Responsibilities:
    - Technical documentation
    - API documentation
    - User guides
    - README files
    - Code comments

    Subagents:
    - documentarian.api: API documentation
    - documentarian.user: User documentation

    Skills:
    - technical_writing
    - api_documentation
    - user_guide_creation

    Tools:
    - file_system
    - git
    """

    id = "documentarian"
    role = "technical_writer"
    _skills = ["technical_writing", "api_documentation", "user_guide_creation"]
    _tools = ["file_system", "git"]

    def initialize(self, project_state: ProjectState) -> None:
        """Initialize documentarian with project context.

        Loads:
        - Code artifacts to document
        - Existing documentation
        - Brand guidelines
        - Documentation standards

        TODO: Load code artifacts
        TODO: Load brand guidelines
        TODO: Check documentation standards
        """
        ...

    def plan(self, task: TaskDefinition) -> AgentPlan:
        """Plan documentation approach.

        Creates plan for:
        1. Content analysis
        2. Structure planning
        3. Documentation writing
        4. Review and formatting

        TODO: Implement documentation planning
        TODO: Identify documentation needs
        TODO: Plan content structure
        """
        ...

    def act(self, step: AgentPlanStep, context: AgentContext) -> AgentOutput:
        """Execute documentation step.

        May involve:
        - Writing markdown files
        - Generating API docs
        - Creating diagrams
        - Formatting content

        TODO: Implement documentation actions
        TODO: Generate documentation artifacts
        TODO: Apply brand guidelines
        """
        ...

    def summarize(self, run_id: str) -> AgentSummary:
        """Summarize documentation work.

        Summary includes:
        - Documents created
        - Coverage of code
        - Completeness assessment

        TODO: Collect documentation artifacts
        TODO: Report coverage
        TODO: Provide review notes
        """
        ...

    def complete(self, project_state: ProjectState) -> None:
        """Complete documentarian execution.

        TODO: Finalize documentation
        TODO: Report metrics
        """
        ...
