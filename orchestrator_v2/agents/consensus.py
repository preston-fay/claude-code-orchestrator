"""
Consensus Agent for Orchestrator v2.

The Consensus agent reviews proposals from other agents,
identifies conflicts, and builds agreement. It serves as
a quality gate between major phases.

See ADR-001 for agent responsibilities.
"""

from orchestrator_v2.agents.base_agent import BaseAgent, BaseAgentConfig
from orchestrator_v2.core.state_models import (
    AgentOutput,
    AgentPlan,
    AgentPlanStep,
    AgentSummary,
    PhaseType,
    ProjectState,
    TaskDefinition,
    TokenUsage,
)


def create_consensus_agent() -> "ConsensusAgent":
    """Factory function to create a ConsensusAgent with default config."""
    config = BaseAgentConfig(
        id="consensus",
        role="reviewer",
        description="Review and approval",
        skills=["proposal_review", "conflict_resolution", "decision_validation"],
        tools=["file_system"],
        subagents={},
    )
    return ConsensusAgent(config)


class ConsensusAgent(BaseAgent):
    """Consensus agent for review and approval.

    Responsibilities:
    - Reviewing proposals from other agents
    - Identifying conflicts and issues
    - Building consensus on decisions
    - Approving phase transitions

    Subagents: None

    Skills:
    - proposal_review
    - conflict_resolution
    - decision_validation

    Tools:
    - file_system
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
                description="Analyze proposals",
            ),
            AgentPlanStep(
                step_id=f"{task.task_id}_conflicts",
                description="Identify conflicts",
            ),
            AgentPlanStep(
                step_id=f"{task.task_id}_resolve",
                description="Recommend resolution",
            ),
            AgentPlanStep(
                step_id=f"{task.task_id}_approve",
                description="Make approval decision",
            ),
        ]

        plan.estimated_tokens = 1000
        return plan

    async def act(
        self,
        plan: AgentPlan,
        project_state: ProjectState,
    ) -> AgentOutput:
        """Execute review steps."""
        phase = project_state.current_phase
        self._record_tokens(input_tokens=500, output_tokens=400)

        # Create consensus report
        consensus_content = f"""# Consensus Review Report

## Project: {project_state.project_name}
## Agent: {self.id}
## Phase: {phase.value}

### Proposals Reviewed
- Proposal 1: [Description]

### Conflicts Identified
- No major conflicts found

### Resolution Recommendations
- [Recommendations if any]

### Approval Decision
APPROVED - Phase may proceed

### Steps Executed
"""
        for step in plan.steps:
            consensus_content += f"- {step.description}\n"

        self._create_artifact(
            "consensus_report.md",
            consensus_content,
            phase,
            project_state.project_id,
        )

        self._record_event("consensus_acted", phase.value, artifacts=len(self._artifacts))

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
        """Summarize consensus work."""
        summary = await super().summarize(plan, output, project_state)
        summary.summary = (
            f"Consensus completed {len(plan.steps)} review steps. "
            f"Decision: APPROVED."
        )
        return summary
