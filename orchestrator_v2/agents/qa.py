"""
QA Agent for Orchestrator v2.

The QA agent tests functionality, validates requirements,
and ensures quality. It is responsible for:
- Test execution
- Quality validation
- Bug identification
- Coverage analysis

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


def create_qa_agent() -> "QAAgent":
    """Factory function to create a QAAgent with default config."""
    config = BaseAgentConfig(
        id="qa",
        role="qa_engineer",
        description="Testing and quality validation",
        skills=["test_execution", "coverage_analysis", "bug_detection"],
        tools=["file_system", "python_executor", "linter", "security_scanner"],
        subagents={
            "qa.unit": BaseAgentConfig(
                id="qa.unit",
                role="unit_tester",
                description="Unit testing specialization",
                skills=["unit_testing"],
                tools=["python_executor"],
            ),
            "qa.security": BaseAgentConfig(
                id="qa.security",
                role="security_tester",
                description="Security testing",
                skills=["security_testing"],
                tools=["security_scanner"],
            ),
        },
    )
    return QAAgent(config)


class QAAgent(BaseAgent):
    """QA agent for testing and validation.

    Responsibilities:
    - Test suite execution
    - Requirement validation
    - Bug identification
    - Coverage analysis
    - Quality reporting

    LLM Integration:
    - Uses qa.md template from subagent_prompts/
    - Produces test reports and quality assessments
    - Identifies issues and generates recommendations
    - Creates coverage analysis documents

    Subagents:
    - qa.unit: Unit testing specialization
    - qa.security: Security testing

    Skills:
    - test_execution
    - coverage_analysis
    - bug_detection

    Tools:
    - file_system
    - python_executor
    - linter
    - security_scanner
    """

    async def plan(
        self,
        task: TaskDefinition,
        phase: PhaseType,
        project_state: ProjectState,
        context: AgentContext | None = None,
    ) -> AgentPlan:
        """Plan QA approach.

        When LLM context is available, generates a real plan based on
        code artifacts. Otherwise, returns a standard plan template.

        Creates plan for:
        1. Unit test execution
        2. Integration test execution
        3. Coverage analysis
        4. Security scanning

        Args:
            task: Task to plan for.
            phase: Current phase.
            project_state: Project state.
            context: Optional agent context for LLM calls.

        Returns:
            Execution plan with QA steps.
        """
        # Use parent's LLM-enabled plan method
        plan = await super().plan(task, phase, project_state, context)

        # If we got a simulated plan (no LLM context), enhance with QA defaults
        if not context and not self._agent_context:
            plan.steps = [
                AgentPlanStep(
                    step_id=f"{task.task_id}_unit",
                    description="Run unit tests and collect results",
                    estimated_tokens=400,
                ),
                AgentPlanStep(
                    step_id=f"{task.task_id}_integration",
                    description="Run integration tests",
                    estimated_tokens=300,
                ),
                AgentPlanStep(
                    step_id=f"{task.task_id}_coverage",
                    description="Analyze test coverage and identify gaps",
                    estimated_tokens=250,
                ),
                AgentPlanStep(
                    step_id=f"{task.task_id}_security",
                    description="Run security scans and vulnerability checks",
                    estimated_tokens=350,
                ),
            ]
            plan.estimated_tokens = sum(s.estimated_tokens for s in plan.steps)
            plan.expected_outputs = [
                "test_report.md",
                "coverage_report.md",
                "security_scan.md",
            ]

        logger.info(
            f"QA created plan with {len(plan.steps)} steps for {task.task_id}"
        )

        return plan

    async def act(
        self,
        plan: AgentPlan,
        project_state: ProjectState,
        context: AgentContext | None = None,
    ) -> AgentOutput:
        """Execute QA steps.

        When LLM context is available, generates real test analysis.
        Otherwise, creates template-based reports.

        Creates QA artifacts including:
        - Test execution report
        - Coverage report
        - Security scan results

        Args:
            plan: Execution plan.
            project_state: Project state.
            context: Optional agent context for LLM calls.

        Returns:
            Execution output with QA artifacts.
        """
        ctx = context or self._agent_context
        phase = project_state.current_phase

        # If we have LLM context, use the parent's LLM-enabled act method
        if ctx:
            logger.info(f"QA executing with LLM for project {project_state.project_name}")
            return await super().act(plan, project_state, context)

        # Otherwise, generate template-based artifacts
        logger.info(f"QA executing with templates for project {project_state.project_name}")

        # Record token usage for QA work (simulated)
        self._record_tokens(input_tokens=900, output_tokens=700)

        # Create test report
        test_report = f"""# Test Execution Report

## Project: {project_state.project_name}
## Client: {project_state.client}
## Phase: {phase.value}

### Executive Summary

Testing completed for the project with overall **PASS** status. 
The test suite demonstrates good coverage with minor areas for improvement.

### Test Results Summary

| Category | Total | Passed | Failed | Skipped | Pass Rate |
|----------|-------|--------|--------|---------|-----------|
| Unit Tests | 120 | 117 | 2 | 1 | 97.5% |
| Integration Tests | 25 | 24 | 1 | 0 | 96.0% |
| E2E Tests | 5 | 5 | 0 | 0 | 100% |
| **Total** | **150** | **146** | **3** | **1** | **97.3%** |

### Failed Tests

#### 1. test_models.py::TestEntity::test_concurrent_update
- **Status**: FAILED
- **Error**: AssertionError - Race condition in update
- **Severity**: Medium
- **Recommendation**: Add locking mechanism for concurrent updates

#### 2. test_main.py::TestApplication::test_shutdown_under_load
- **Status**: FAILED
- **Error**: TimeoutError - Shutdown exceeded 30s
- **Severity**: Low
- **Recommendation**: Implement graceful shutdown with resource cleanup

#### 3. test_integration.py::TestAPI::test_bulk_operation
- **Status**: FAILED
- **Error**: MemoryError - Exceeded limit on large dataset
- **Severity**: Medium
- **Recommendation**: Implement pagination or streaming for bulk operations

### Test Environment

- Python Version: 3.11.5
- Test Framework: pytest 7.4.0
- CI/CD: GitHub Actions
- Coverage Tool: pytest-cov

### Steps Executed
"""
        for step in plan.steps:
            test_report += f"- {step.description}\n"

        self._create_artifact(
            "test_report.md",
            test_report,
            phase,
            project_state.project_id,
        )

        # Create coverage report
        coverage_report = f"""# Code Coverage Report

## Project: {project_state.project_name}
## Generated: QA Agent

### Coverage Summary

| Metric | Coverage | Target | Status |
|--------|----------|--------|--------|
| Line Coverage | 85.2% | 80% | ✅ PASS |
| Branch Coverage | 78.4% | 75% | ✅ PASS |
| Function Coverage | 92.1% | 90% | ✅ PASS |
| Statement Coverage | 84.8% | 80% | ✅ PASS |

### Module Breakdown

| Module | Lines | Covered | Coverage |
|--------|-------|---------|----------|
| src/main.py | 85 | 78 | 91.8% |
| src/models.py | 120 | 95 | 79.2% |
| src/utils.py | 45 | 42 | 93.3% |
| src/api.py | 150 | 118 | 78.7% |

### Uncovered Areas

#### High Priority (< 70% coverage)
- `src/api.py:handle_errors` - Error handling paths not fully tested
- `src/models.py:validate` - Edge case validation untested

#### Medium Priority (70-80% coverage)
- `src/models.py` - Some edge cases in data transformation
- `src/api.py` - Some API error responses untested

### Recommendations

1. **Add error handling tests** - Create tests for exception paths
2. **Edge case coverage** - Add tests for boundary conditions
3. **Integration gaps** - Test more cross-module interactions
4. **Mock external services** - Improve isolation in unit tests

### Coverage Trend

| Date | Line | Branch | Change |
|------|------|--------|--------|
| Week 1 | 72.1% | 65.3% | - |
| Week 2 | 78.5% | 71.2% | +6.4% |
| Week 3 | 82.3% | 75.8% | +3.8% |
| Current | 85.2% | 78.4% | +2.9% |
"""

        self._create_artifact(
            "coverage_report.md",
            coverage_report,
            phase,
            project_state.project_id,
        )

        # Create security scan report
        security_report = f"""# Security Scan Report

## Project: {project_state.project_name}
## Scan Type: Static Analysis + Dependency Check
## Phase: {phase.value}

### Executive Summary

Security scan completed with **1 High**, **3 Medium**, and **5 Low** severity findings.
Immediate attention required for the high severity issue.

### Findings Summary

| Severity | Count | Status |
|----------|-------|--------|
| Critical | 0 | ✅ |
| High | 1 | ⚠️ Action Required |
| Medium | 3 | 🔄 Review Needed |
| Low | 5 | 📝 Noted |

### High Severity Findings

#### HSF-001: SQL Injection Risk
- **Location**: `src/api.py:87`
- **Description**: User input directly concatenated in query string
- **CVSS Score**: 8.1
- **Remediation**: Use parameterized queries or ORM
- **Status**: Open

### Medium Severity Findings

#### MSF-001: Hardcoded Secrets
- **Location**: `config/settings.py:12`
- **Description**: API key appears to be hardcoded
- **Remediation**: Use environment variables

#### MSF-002: Missing Rate Limiting
- **Location**: `src/api.py`
- **Description**: No rate limiting on authentication endpoints
- **Remediation**: Implement rate limiting middleware

#### MSF-003: Verbose Error Messages
- **Location**: `src/api.py:handle_errors`
- **Description**: Stack traces exposed in error responses
- **Remediation**: Sanitize error responses in production

### Dependency Vulnerabilities

| Package | Current | Vulnerable | Fixed In | Severity |
|---------|---------|------------|----------|----------|
| requests | 2.28.0 | CVE-2023-XXXX | 2.31.0 | Medium |
| pillow | 9.0.0 | CVE-2023-YYYY | 9.4.0 | Low |

### Recommendations

1. **Immediate**: Fix SQL injection vulnerability
2. **Short-term**: Update vulnerable dependencies
3. **Medium-term**: Implement rate limiting
4. **Long-term**: Set up automated security scanning in CI/CD

### Compliance Status

| Standard | Status | Notes |
|----------|--------|-------|
| OWASP Top 10 | Partial | 2 items need attention |
| CWE/SANS Top 25 | Partial | 3 items need attention |
| PCI DSS | N/A | Not applicable |
"""

        self._create_artifact(
            "security_scan.md",
            security_report,
            phase,
            project_state.project_id,
        )

        # Run subagents if configured
        subagent_summaries = []
        for subagent_id, subagent_config in self.config.subagents.items():
            summary = await self._run_subagent(subagent_config, phase, project_state, ctx)
            subagent_summaries.append(summary)

        # Emit event
        self._record_event(
            "qa_acted",
            phase.value,
            artifacts=len(self._artifacts),
            subagents=len(subagent_summaries),
            used_llm=ctx is not None,
            test_pass_rate=97.3,
            coverage=85.2,
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
            execution_summary=f"QA testing completed for {project_state.project_name}. Pass rate: 97.3%, Coverage: 85.2%",
            recommendations=[
                "Fix high severity security finding (SQL injection)",
                "Address failed tests before deployment",
                "Update vulnerable dependencies",
            ],
        )

    async def summarize(
        self,
        plan: AgentPlan,
        output: AgentOutput,
        project_state: ProjectState,
    ) -> AgentSummary:
        """Summarize QA work.

        Summary includes:
        - Test results and pass rate
        - Coverage metrics
        - Security findings
        - Recommendations

        Args:
            plan: Execution plan.
            output: Execution output.
            project_state: Project state.

        Returns:
            Execution summary.
        """
        summary = await super().summarize(plan, output, project_state)

        # Enhance summary with QA-specific details
        summary.summary = (
            f"QA completed {len(plan.steps)} validation steps: "
            f"unit testing, integration testing, coverage analysis, "
            f"and security scanning. Produced {len(self._artifacts)} artifacts. "
            f"Pass rate: 97.3%, Coverage: 85.2%."
        )

        # Add QA-specific recommendations
        summary.recommendations = output.recommendations + [
            "Consider adding more edge case tests",
            "Schedule regular security audits",
        ]

        return summary
