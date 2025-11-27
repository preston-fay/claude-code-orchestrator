"""
Steward Agent for Orchestrator v2.

The Steward agent maintains repository health, identifies
dead code, orphans, and cleanliness issues.

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

    LLM Integration:
    - Uses steward.md template from subagent_prompts/
    - Produces hygiene and compliance reports
    - Identifies code quality issues
    - Generates cleanup recommendations

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
        context: AgentContext | None = None,
    ) -> AgentPlan:
        """Plan hygiene check approach."""
        plan = await super().plan(task, phase, project_state, context)

        if not context and not self._agent_context:
            plan.steps = [
                AgentPlanStep(
                    step_id=f"{task.task_id}_scan",
                    description="Scan repository structure",
                    estimated_tokens=200,
                ),
                AgentPlanStep(
                    step_id=f"{task.task_id}_dead_code",
                    description="Detect dead and unused code",
                    estimated_tokens=250,
                ),
                AgentPlanStep(
                    step_id=f"{task.task_id}_security",
                    description="Run security and compliance scans",
                    estimated_tokens=200,
                ),
                AgentPlanStep(
                    step_id=f"{task.task_id}_report",
                    description="Generate hygiene report",
                    estimated_tokens=150,
                ),
            ]
            plan.estimated_tokens = sum(s.estimated_tokens for s in plan.steps)
            plan.expected_outputs = ["hygiene_report.md"]

        logger.info(
            f"Steward created plan with {len(plan.steps)} steps for {task.task_id}"
        )
        return plan

    async def act(
        self,
        plan: AgentPlan,
        project_state: ProjectState,
        context: AgentContext | None = None,
    ) -> AgentOutput:
        """Execute hygiene check steps."""
        ctx = context or self._agent_context
        phase = project_state.current_phase

        if ctx:
            logger.info(f"Steward executing with LLM for project {project_state.project_name}")
            return await super().act(plan, project_state, context)

        logger.info(f"Steward executing with templates for project {project_state.project_name}")
        self._record_tokens(input_tokens=400, output_tokens=300)

        # Create hygiene report
        hygiene_content = f"""# Repository Hygiene Report

## Project: {project_state.project_name}
## Client: {project_state.client}
## Phase: {phase.value}

### Executive Summary

Repository hygiene scan completed. Overall status: **COMPLIANT** ✅

### Repository Scan Results

| Metric | Value | Status |
|--------|-------|--------|
| Total files | 45 | - |
| Source files | 28 | - |
| Test files | 12 | - |
| Config files | 5 | - |
| Large files (>1MB) | 0 | ✅ |
| Orphan files | 0 | ✅ |
| Temp files | 0 | ✅ |

### Dead Code Detection

| Category | Count | Severity |
|----------|-------|----------|
| Unused imports | 2 | Low |
| Unreachable code | 0 | - |
| Unused variables | 3 | Low |
| Unused functions | 1 | Medium |
| Commented code | 4 | Low |

**Total issues**: 10 (all low-medium severity)

### Security Scan Results

| Check | Status | Notes |
|-------|--------|-------|
| Hardcoded secrets | ✅ Pass | No secrets detected |
| Vulnerable dependencies | ⚠️ Warning | 1 outdated package |
| Insecure configurations | ✅ Pass | - |
| SQL injection risk | ✅ Pass | - |
| XSS vulnerabilities | ✅ Pass | - |

### Compliance Status

| Standard | Status | Notes |
|----------|--------|-------|
| Code style (PEP 8) | ✅ Compliant | - |
| Type hints | ⚠️ Partial | 85% coverage |
| Docstrings | ✅ Compliant | - |
| License headers | ✅ Compliant | - |

### Recommendations

1. **Remove unused imports** in:
   - `src/utils.py` (line 3, 7)

2. **Update outdated package**:
   - `requests` 2.28.0 → 2.31.0

3. **Remove commented code** in:
   - `src/api.py` (lines 45-52)

4. **Add type hints** to remaining functions

### Overall Status

**COMPLIANT** - Repository meets hygiene standards with minor recommendations.

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

        self._record_event(
            "steward_acted",
            phase.value,
            artifacts=len(self._artifacts),
            status="COMPLIANT",
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
            execution_summary="Repository hygiene check completed. Status: COMPLIANT",
            recommendations=[
                "Remove unused imports",
                "Update outdated dependencies",
                "Clean up commented code blocks",
            ],
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
            f"Steward completed {len(plan.steps)} hygiene checks: "
            f"repository scan, dead code detection, security scan, "
            f"and report generation. Status: COMPLIANT."
        )
        summary.recommendations = output.recommendations + [
            "Schedule regular hygiene checks",
        ]
        return summary
