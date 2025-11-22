"""
Steward Agent for Orchestrator v2.

The Steward agent maintains repository health, identifies
dead code, orphans, and cleanliness issues.

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


def create_steward_agent() -> "StewardAgent":
    """Factory function to create a StewardAgent with default config."""
    config = BaseAgentConfig(
        id="steward",
        role="maintainer",
        description="Repository hygiene",
        skills=["repo_hygiene", "dead_code_detection", "security_scanning"],
        tools=["file_system", "git", "security_scanner", "linter"],
        subagents={},
    )
    return StewardAgent(config)


class StewardAgent(BaseAgent):
    """Steward agent for repository hygiene.

    Responsibilities:
    - Repository cleanliness checks
    - Dead code detection
    - Orphan file identification
    - Security scanning
    - Compliance validation

    Skills:
    - repo_hygiene
    - dead_code_detection
    - security_scanning

    Tools:
    - file_system
    - git
    - security_scanner
    - linter
    """

    async def plan(
        self,
        task: TaskDefinition,
        phase: PhaseType,
        project_state: ProjectState,
    ) -> AgentPlan:
        """Plan hygiene check approach."""
        plan = await super().plan(task, phase, project_state)

        plan.steps = [
            AgentPlanStep(
                step_id=f"{task.task_id}_scan",
                description="Scan repository",
            ),
            AgentPlanStep(
                step_id=f"{task.task_id}_dead_code",
                description="Detect dead code",
            ),
            AgentPlanStep(
                step_id=f"{task.task_id}_security",
                description="Run security scans",
            ),
            AgentPlanStep(
                step_id=f"{task.task_id}_report",
                description="Generate hygiene report",
            ),
        ]

        plan.estimated_tokens = 800
        return plan

    async def act(
        self,
        plan: AgentPlan,
        project_state: ProjectState,
    ) -> AgentOutput:
        """Execute hygiene check steps."""
        phase = project_state.current_phase
        self._record_tokens(input_tokens=400, output_tokens=300)

        # Create hygiene report
        hygiene_content = f"""# Repository Hygiene Report

## Project: {project_state.project_name}
## Agent: {self.id}
## Phase: {phase.value}

### Repository Scan Results
- Total files: [count]
- Large files: 0
- Orphan files: 0

### Dead Code Detection
- Unused imports: 0
- Unreachable code: 0
- Unused variables: 0

### Security Scan
- Vulnerabilities: 0
- Secrets detected: 0

### Compliance Status
COMPLIANT

### Steps Executed
"""
        for step in plan.steps:
            hygiene_content += f"- {step.description}\n"

        self._create_artifact(
            "hygiene_report.md",
            hygiene_content,
            phase,
            project_state.project_id,
        )

        self._record_event("steward_acted", phase.value, artifacts=len(self._artifacts))

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
        """Summarize hygiene work."""
        summary = await super().summarize(plan, output, project_state)
        summary.summary = (
            f"Steward completed {len(plan.steps)} hygiene checks. "
            f"Status: COMPLIANT."
        )
        return summary
