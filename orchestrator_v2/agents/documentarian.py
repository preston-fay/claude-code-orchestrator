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


def create_documentarian_agent() -> "DocumentarianAgent":
    """Factory function to create a DocumentarianAgent with default config."""
    config = BaseAgentConfig(
        id="documentarian",
        role="technical_writer",
        description="Documentation creation",
        skills=["technical_writing", "api_documentation", "user_guide_creation"],
        tools=["file_system", "git"],
        subagents={},
    )
    return DocumentarianAgent(config)


class DocumentarianAgent(BaseAgent):
    """Documentarian agent for documentation creation.

    Responsibilities:
    - Technical documentation
    - API documentation
    - User guides
    - README files
    - Code comments

    Skills:
    - technical_writing
    - api_documentation
    - user_guide_creation

    Tools:
    - file_system
    - git
    """

    async def plan(
        self,
        task: TaskDefinition,
        phase: PhaseType,
        project_state: ProjectState,
    ) -> AgentPlan:
        """Plan documentation approach."""
        plan = await super().plan(task, phase, project_state)

        plan.steps = [
            AgentPlanStep(
                step_id=f"{task.task_id}_analyze",
                description="Analyze code artifacts",
            ),
            AgentPlanStep(
                step_id=f"{task.task_id}_structure",
                description="Plan documentation structure",
            ),
            AgentPlanStep(
                step_id=f"{task.task_id}_write",
                description="Write documentation",
            ),
            AgentPlanStep(
                step_id=f"{task.task_id}_format",
                description="Format and review",
            ),
        ]

        plan.estimated_tokens = 1200
        return plan

    async def act(
        self,
        plan: AgentPlan,
        project_state: ProjectState,
    ) -> AgentOutput:
        """Execute documentation steps."""
        phase = project_state.current_phase
        self._record_tokens(input_tokens=600, output_tokens=500)

        # Create documentation artifact
        doc_content = f"""# Project Documentation

## Project: {project_state.project_name}
## Agent: {self.id}
## Phase: {phase.value}

### Overview
[Project overview and purpose]

### Architecture
[System architecture description]

### API Reference
[API endpoint documentation]

### User Guide
[Step-by-step usage instructions]

### Steps Executed
"""
        for step in plan.steps:
            doc_content += f"- {step.description}\n"

        self._create_artifact(
            "documentation.md",
            doc_content,
            phase,
            project_state.project_id,
        )

        self._record_event("documentarian_acted", phase.value, artifacts=len(self._artifacts))

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
        """Summarize documentation work."""
        summary = await super().summarize(plan, output, project_state)
        summary.summary = (
            f"Documentarian completed {len(plan.steps)} documentation steps. "
            f"Produced {len(self._artifacts)} artifacts."
        )
        return summary
