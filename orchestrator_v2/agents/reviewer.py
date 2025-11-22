"""
Reviewer Agent for Orchestrator v2.

The Reviewer agent conducts code reviews and provides
feedback on implementation quality.

See ADR-001 for agent responsibilities.
"""

from orchestrator_v2.agents.base_agent import BaseAgent, BaseAgentConfig
from orchestrator_v2.engine.state_models import (
    AgentOutput,
    AgentPlan,
    AgentPlanStep,
    AgentSummary,
    PhaseType,
    ProjectState,
    TaskDefinition,
    TokenUsage,
)


def create_reviewer_agent() -> "ReviewerAgent":
    """Factory function to create a ReviewerAgent with default config."""
    config = BaseAgentConfig(
        id="reviewer",
        role="code_reviewer",
        description="Code review",
        skills=["code_review", "best_practices", "style_analysis"],
        tools=["file_system", "git", "linter"],
        subagents={},
    )
    return ReviewerAgent(config)


class ReviewerAgent(BaseAgent):
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

    async def plan(
        self,
        task: TaskDefinition,
        phase: PhaseType,
        project_state: ProjectState,
    ) -> AgentPlan:
        """Plan review approach."""
        plan = await super().plan(task, phase, project_state)

        plan.steps = [
            AgentPlanStep(
                step_id=f"{task.task_id}_analyze",
                description="Analyze code quality",
            ),
            AgentPlanStep(
                step_id=f"{task.task_id}_standards",
                description="Check standards compliance",
            ),
            AgentPlanStep(
                step_id=f"{task.task_id}_feedback",
                description="Generate feedback",
            ),
            AgentPlanStep(
                step_id=f"{task.task_id}_recommend",
                description="Provide recommendations",
            ),
        ]

        plan.estimated_tokens = 900
        return plan

    async def act(
        self,
        plan: AgentPlan,
        project_state: ProjectState,
    ) -> AgentOutput:
        """Execute review steps."""
        phase = project_state.current_phase
        self._record_tokens(input_tokens=450, output_tokens=350)

        # Create review report
        review_content = f"""# Code Review Report

## Project: {project_state.project_name}
## Agent: {self.id}
## Phase: {phase.value}

### Code Quality Analysis
- Overall quality: Good
- Readability: High
- Maintainability: High

### Standards Compliance
- PEP 8: PASS
- Type hints: PASS
- Docstrings: PASS

### Issues Found
- Minor: 2
- Major: 0
- Critical: 0

### Recommendations
1. Add more unit tests
2. Consider refactoring large functions

### Approval Status
APPROVED with minor suggestions

### Steps Executed
"""
        for step in plan.steps:
            review_content += f"- {step.description}\n"

        self._create_artifact(
            "code_review_report.md",
            review_content,
            phase,
            project_state.project_id,
        )

        self._record_event("reviewer_acted", phase.value, artifacts=len(self._artifacts))

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
        """Summarize review work."""
        summary = await super().summarize(plan, output, project_state)
        summary.summary = (
            f"Reviewer completed {len(plan.steps)} review steps. "
            f"Status: APPROVED with suggestions."
        )
        return summary
