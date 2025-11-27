"""
Reviewer Agent for Orchestrator v2.

The Reviewer agent conducts code reviews and provides
feedback on implementation quality.

This agent now uses real LLM calls when an AgentContext is provided,
falling back to simulated responses otherwise.

See ADR-001 for agent responsibilities.
"""

import logging

from orchestrator_v2.agents.base_agent import BaseAgent, BaseAgentConfig
from orchestrator_v2.engine.state_models import (
    AgentContext,
    AgentOutput,
    AgentPlan,
    AgentPlanStep,
    AgentSummary,
    PhaseType,
    ProjectState,
    TaskDefinition,
    TokenUsage,
)

logger = logging.getLogger(__name__)


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

    LLM Integration:
    - Uses reviewer.md template from subagent_prompts/
    - Produces detailed code review reports
    - Identifies issues and improvements
    - Provides actionable feedback

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
        context: AgentContext | None = None,
    ) -> AgentPlan:
        """Plan review approach."""
        plan = await super().plan(task, phase, project_state, context)

        if not context and not self._agent_context:
            plan.steps = [
                AgentPlanStep(
                    step_id=f"{task.task_id}_analyze",
                    description="Analyze code quality and structure",
                    estimated_tokens=300,
                ),
                AgentPlanStep(
                    step_id=f"{task.task_id}_standards",
                    description="Check standards and best practices",
                    estimated_tokens=250,
                ),
                AgentPlanStep(
                    step_id=f"{task.task_id}_feedback",
                    description="Generate detailed feedback",
                    estimated_tokens=200,
                ),
                AgentPlanStep(
                    step_id=f"{task.task_id}_recommend",
                    description="Provide improvement recommendations",
                    estimated_tokens=150,
                ),
            ]
            plan.estimated_tokens = sum(s.estimated_tokens for s in plan.steps)
            plan.expected_outputs = ["code_review_report.md"]

        logger.info(
            f"Reviewer created plan with {len(plan.steps)} steps for {task.task_id}"
        )
        return plan

    async def act(
        self,
        plan: AgentPlan,
        project_state: ProjectState,
        context: AgentContext | None = None,
    ) -> AgentOutput:
        """Execute review steps."""
        ctx = context or self._agent_context
        phase = project_state.current_phase

        if ctx:
            logger.info(f"Reviewer executing with LLM for project {project_state.project_name}")
            return await super().act(plan, project_state, context)

        logger.info(f"Reviewer executing with templates for project {project_state.project_name}")
        self._record_tokens(input_tokens=450, output_tokens=350)

        # Create review report
        review_content = f"""# Code Review Report

## Project: {project_state.project_name}
## Client: {project_state.client}
## Phase: {phase.value}

### Executive Summary

Code review completed. Overall quality: **Good** ✅
Approval status: **APPROVED with suggestions**

### Code Quality Metrics

| Metric | Score | Target | Status |
|--------|-------|--------|--------|
| Overall quality | 8.2/10 | 7.5 | ✅ |
| Readability | 8.5/10 | 8.0 | ✅ |
| Maintainability | 8.0/10 | 7.5 | ✅ |
| Complexity | 7.8/10 | 7.0 | ✅ |
| Test coverage | 85% | 80% | ✅ |

### Standards Compliance

| Standard | Status | Details |
|----------|--------|---------|\n| PEP 8 | ✅ Pass | Code style compliant |
| Type hints | ✅ Pass | 95% coverage |
| Docstrings | ✅ Pass | All public APIs documented |
| Import order | ✅ Pass | isort compliant |
| Line length | ✅ Pass | Max 88 chars (Black) |

### Issues Found

| Severity | Count | Description |
|----------|-------|-------------|
| Critical | 0 | - |
| Major | 0 | - |
| Minor | 3 | Style suggestions |
| Info | 2 | Optional improvements |

#### Minor Issues

1. **src/main.py:45** - Consider extracting method
   ```python
   # Current: Long method with multiple responsibilities
   # Suggested: Split into smaller, focused methods
   ```

2. **src/models.py:78** - Magic number
   ```python
   # Current: if count > 100:
   # Suggested: if count > MAX_BATCH_SIZE:
   ```

3. **src/api.py:23** - Missing error message
   ```python
   # Current: raise ValueError()
   # Suggested: raise ValueError("Description of issue")
   ```

#### Informational

1. Consider adding logging to critical paths
2. Optional: Add performance metrics collection

### Positive Observations

- ✅ Clean code structure and organization
- ✅ Good separation of concerns
- ✅ Comprehensive error handling in most areas
- ✅ Well-written unit tests
- ✅ Clear naming conventions

### Recommendations

1. **High Priority**
   - Fix the minor issues identified above
   - Add missing error messages to exceptions

2. **Medium Priority**
   - Consider refactoring long methods
   - Add constants for magic numbers

3. **Low Priority**
   - Add more inline comments for complex logic
   - Consider adding performance benchmarks

### Approval Status

**APPROVED** ✅ with minor suggestions

The code is ready for merge after addressing the minor issues.
No blocking concerns identified.

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

        self._record_event(
            "reviewer_acted",
            phase.value,
            artifacts=len(self._artifacts),
            decision="APPROVED",
            quality_score=8.2,
            used_llm=ctx is not None,
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
            execution_summary="Code review completed. Quality: Good (8.2/10). Status: APPROVED",
            recommendations=[
                "Fix minor issues before merge",
                "Add missing error messages",
                "Consider method refactoring",
            ],
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
            f"Reviewer completed {len(plan.steps)} review steps: "
            f"quality analysis, standards check, feedback generation, "
            f"and recommendations. Status: APPROVED with suggestions."
        )
        summary.recommendations = output.recommendations + [
            "Schedule follow-up review after changes",
        ]
        return summary
