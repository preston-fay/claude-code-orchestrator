"""
Consensus Agent for Orchestrator v2.

The Consensus agent reviews proposals from other agents,
identifies conflicts, and builds agreement. It serves as
a quality gate between major phases.

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

    LLM Integration:
    - Uses consensus.md template from subagent_prompts/
    - Produces review and approval decisions
    - Identifies conflicts between proposals
    - Generates resolution recommendations

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
        context: AgentContext | None = None,
    ) -> AgentPlan:
        """Plan review approach."""
        plan = await super().plan(task, phase, project_state, context)

        if not context and not self._agent_context:
            plan.steps = [
                AgentPlanStep(
                    step_id=f"{task.task_id}_analyze",
                    description="Analyze proposals and artifacts",
                    estimated_tokens=300,
                ),
                AgentPlanStep(
                    step_id=f"{task.task_id}_conflicts",
                    description="Identify conflicts and inconsistencies",
                    estimated_tokens=250,
                ),
                AgentPlanStep(
                    step_id=f"{task.task_id}_resolve",
                    description="Recommend conflict resolution",
                    estimated_tokens=200,
                ),
                AgentPlanStep(
                    step_id=f"{task.task_id}_approve",
                    description="Make approval decision",
                    estimated_tokens=150,
                ),
            ]
            plan.estimated_tokens = sum(s.estimated_tokens for s in plan.steps)
            plan.expected_outputs = ["consensus_report.md"]

        logger.info(
            f"Consensus created plan with {len(plan.steps)} steps for {task.task_id}"
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
            logger.info(f"Consensus executing with LLM for project {project_state.project_name}")
            return await super().act(plan, project_state, context)

        logger.info(f"Consensus executing with templates for project {project_state.project_name}")
        self._record_tokens(input_tokens=500, output_tokens=400)

        # Create consensus report
        consensus_content = f"""# Consensus Review Report

## Project: {project_state.project_name}
## Client: {project_state.client}
## Phase: {phase.value}

### Executive Summary

This report documents the consensus review process for the current phase.
All proposals have been reviewed for consistency, completeness, and alignment.

### Proposals Reviewed

| Proposal | Source | Status | Notes |
|----------|--------|--------|-------|
| Architecture Proposal | Architect Agent | ✅ Approved | Well-structured |
| Data Model | Architect Agent | ✅ Approved | Normalized design |
| Technology Stack | Architect Agent | ✅ Approved | Appropriate choices |

### Conflicts Identified

**No major conflicts found.**

Minor observations:
1. Consider adding caching layer discussion
2. Security requirements could be more detailed
3. Consider scalability projections

### Alignment Check

| Requirement | Addressed | Confidence |
|-------------|-----------|------------|
| Functional requirements | Yes | High |
| Non-functional requirements | Partial | Medium |
| Business constraints | Yes | High |
| Technical constraints | Yes | High |

### Resolution Recommendations

1. **Caching Strategy**: Add Redis caching layer documentation
2. **Security Details**: Expand security section with specific controls
3. **Load Testing**: Include performance benchmarks

### Approval Decision

**APPROVED** ✅

The current phase artifacts are approved for progression to the next phase.
Minor recommendations should be addressed during implementation.

### Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Scope creep | Medium | Medium | Clear requirements |
| Technical debt | Low | Medium | Code reviews |
| Timeline slip | Low | Low | Agile methodology |

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

        self._record_event(
            "consensus_acted",
            phase.value,
            artifacts=len(self._artifacts),
            decision="APPROVED",
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
            execution_summary="Phase approved with minor recommendations",
            recommendations=[
                "Address caching strategy in implementation",
                "Expand security documentation",
                "Plan for load testing",
            ],
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
            f"Consensus completed {len(plan.steps)} review steps: "
            f"proposal analysis, conflict identification, resolution recommendation, "
            f"and approval decision. Decision: APPROVED."
        )
        summary.recommendations = output.recommendations + [
            "Schedule follow-up review after implementation",
        ]
        return summary
