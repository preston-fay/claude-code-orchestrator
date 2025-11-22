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


def create_developer_agent() -> "DeveloperAgent":
    """Factory function to create a DeveloperAgent with default config."""
    config = BaseAgentConfig(
        id="developer",
        role="developer",
        description="Code implementation and testing",
        skills=["code_generation", "test_writing", "refactoring"],
        tools=["file_system", "git", "python_executor", "linter"],
        subagents={
            "developer.frontend": BaseAgentConfig(
                id="developer.frontend",
                role="frontend_developer",
                description="Frontend specialization",
                skills=["frontend_development"],
                tools=["file_system", "git"],
            ),
            "developer.backend": BaseAgentConfig(
                id="developer.backend",
                role="backend_developer",
                description="Backend specialization",
                skills=["backend_development"],
                tools=["file_system", "git", "python_executor"],
            ),
        },
    )
    return DeveloperAgent(config)


class DeveloperAgent(BaseAgent):
    """Developer agent for code implementation.

    Responsibilities:
    - Feature implementation
    - Writing production code
    - Writing tests
    - Code refactoring
    - Integration with existing code

    Subagents:
    - developer.frontend: Frontend specialization
    - developer.backend: Backend specialization

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

    async def plan(
        self,
        task: TaskDefinition,
        phase: PhaseType,
        project_state: ProjectState,
    ) -> AgentPlan:
        """Plan development approach."""
        plan = await super().plan(task, phase, project_state)

        plan.steps = [
            AgentPlanStep(
                step_id=f"{task.task_id}_setup",
                description="Set up code structure",
            ),
            AgentPlanStep(
                step_id=f"{task.task_id}_implement",
                description="Implement features",
            ),
            AgentPlanStep(
                step_id=f"{task.task_id}_test",
                description="Write tests",
            ),
            AgentPlanStep(
                step_id=f"{task.task_id}_lint",
                description="Lint and format code",
            ),
        ]

        plan.estimated_tokens = 2500
        return plan

    async def act(
        self,
        plan: AgentPlan,
        project_state: ProjectState,
    ) -> AgentOutput:
        """Execute development steps."""
        phase = project_state.current_phase
        self._record_tokens(input_tokens=1200, output_tokens=1000)

        # Create development report
        dev_content = f"""# Development Report

## Project: {project_state.project_name}
## Agent: {self.id}
## Phase: {phase.value}

### Implementation Summary
Code implementation completed.

### Files Created/Modified
- src/main.py
- src/models.py
- tests/test_main.py

### Code Metrics
- Lines of code: [count]
- Test coverage: [percentage]

### Steps Executed
"""
        for step in plan.steps:
            dev_content += f"- {step.description}\n"

        self._create_artifact(
            "development_report.md",
            dev_content,
            phase,
            project_state.project_id,
        )

        # Run subagents
        for subagent_id, subagent_config in self.config.subagents.items():
            await self._run_subagent(subagent_config, phase, project_state)

        self._record_event("developer_acted", phase.value, artifacts=len(self._artifacts))

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
        """Summarize development work."""
        summary = await super().summarize(plan, output, project_state)
        summary.summary = (
            f"Developer completed {len(plan.steps)} implementation steps. "
            f"Produced {len(self._artifacts)} artifacts."
        )
        return summary
