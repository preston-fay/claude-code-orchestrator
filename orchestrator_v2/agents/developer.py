"""
Developer Agent for Orchestrator v2.

The Developer agent implements features, writes code, and handles
technical implementation. It is responsible for:
- Code implementation
- Test writing
- Code refactoring
- Technical integration

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

    LLM Integration:
    - Uses developer.md template from subagent_prompts/
    - Produces code files and implementation reports
    - Creates test files with proper coverage
    - Generates documentation for implemented features

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
        context: AgentContext | None = None,
    ) -> AgentPlan:
        """Plan development approach.

        When LLM context is available, generates a real plan based on
        architecture specs and requirements. Otherwise, returns a standard plan.

        Creates plan for:
        1. Code structure setup
        2. Feature implementation
        3. Test writing
        4. Linting and formatting

        Args:
            task: Task to plan for.
            phase: Current phase.
            project_state: Project state.
            context: Optional agent context for LLM calls.

        Returns:
            Execution plan with development steps.
        """
        # Use parent's LLM-enabled plan method
        plan = await super().plan(task, phase, project_state, context)

        # If we got a simulated plan (no LLM context), enhance with dev defaults
        if not context and not self._agent_context:
            plan.steps = [
                AgentPlanStep(
                    step_id=f"{task.task_id}_setup",
                    description="Set up code structure and project scaffold",
                    estimated_tokens=400,
                ),
                AgentPlanStep(
                    step_id=f"{task.task_id}_implement",
                    description="Implement core features and business logic",
                    estimated_tokens=800,
                ),
                AgentPlanStep(
                    step_id=f"{task.task_id}_test",
                    description="Write unit and integration tests",
                    estimated_tokens=600,
                ),
                AgentPlanStep(
                    step_id=f"{task.task_id}_lint",
                    description="Lint and format code",
                    estimated_tokens=200,
                ),
            ]
            plan.estimated_tokens = sum(s.estimated_tokens for s in plan.steps)
            plan.expected_outputs = [
                "src/main.py",
                "src/models.py",
                "tests/test_main.py",
                "development_report.md",
            ]

        logger.info(
            f"Developer created plan with {len(plan.steps)} steps for {task.task_id}"
        )

        return plan

    async def act(
        self,
        plan: AgentPlan,
        project_state: ProjectState,
        context: AgentContext | None = None,
    ) -> AgentOutput:
        """Execute development steps.

        When LLM context is available, generates real code artifacts.
        Otherwise, creates template-based placeholder code.

        Creates code artifacts including:
        - Source files
        - Test files
        - Development report

        Args:
            plan: Execution plan.
            project_state: Project state.
            context: Optional agent context for LLM calls.

        Returns:
            Execution output with code artifacts.
        """
        ctx = context or self._agent_context
        phase = project_state.current_phase

        # If we have LLM context, use the parent's LLM-enabled act method
        if ctx:
            logger.info(f"Developer executing with LLM for project {project_state.project_name}")
            return await super().act(plan, project_state, context)

        # Otherwise, generate template-based artifacts
        logger.info(f"Developer executing with templates for project {project_state.project_name}")

        # Record token usage for development work (simulated)
        self._record_tokens(input_tokens=1200, output_tokens=1000)

        # Create main source file
        main_content = f'''"""
Main module for {project_state.project_name}.

This module provides the core functionality for the application.
Generated by Developer Agent.
"""

import logging
from typing import Any

logger = logging.getLogger(__name__)


class Application:
    """Main application class.

    Handles initialization, configuration, and core business logic.
    """

    def __init__(self, config: dict[str, Any] | None = None):
        """Initialize the application.

        Args:
            config: Optional configuration dictionary.
        """
        self.config = config or {{}}
        self._initialized = False
        logger.info("Application instance created")

    def initialize(self) -> None:
        """Initialize application resources."""
        if self._initialized:
            logger.warning("Application already initialized")
            return
        
        # Setup code here
        self._initialized = True
        logger.info("Application initialized successfully")

    def run(self) -> None:
        """Run the main application logic."""
        if not self._initialized:
            self.initialize()
        
        logger.info("Application running...")
        # Main logic here

    def shutdown(self) -> None:
        """Clean up application resources."""
        if self._initialized:
            # Cleanup code here
            self._initialized = False
            logger.info("Application shut down")


def main() -> None:
    """Entry point for the application."""
    logging.basicConfig(level=logging.INFO)
    
    app = Application()
    try:
        app.run()
    finally:
        app.shutdown()


if __name__ == "__main__":
    main()
'''

        self._create_artifact(
            "src/main.py",
            main_content,
            phase,
            project_state.project_id,
        )

        # Create models file
        models_content = f'''"""
Data models for {project_state.project_name}.

This module defines the core data structures used throughout the application.
Generated by Developer Agent.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID, uuid4


class Status(Enum):
    """Status enumeration for entities."""
    PENDING = "pending"
    ACTIVE = "active"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


@dataclass
class BaseModel:
    """Base model with common fields."""
    id: UUID = field(default_factory=uuid4)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class Entity(BaseModel):
    """Generic entity model."""
    name: str = ""
    description: str = ""
    status: Status = Status.PENDING

    def activate(self) -> None:
        """Mark entity as active."""
        self.status = Status.ACTIVE
        self.updated_at = datetime.utcnow()

    def complete(self) -> None:
        """Mark entity as completed."""
        self.status = Status.COMPLETED
        self.updated_at = datetime.utcnow()


@dataclass
class Task(BaseModel):
    """Task model for work items."""
    title: str = ""
    description: str = ""
    status: Status = Status.PENDING
    assignee: str | None = None
    due_date: datetime | None = None
    
    def assign(self, assignee: str) -> None:
        """Assign task to a user."""
        self.assignee = assignee
        self.updated_at = datetime.utcnow()
'''

        self._create_artifact(
            "src/models.py",
            models_content,
            phase,
            project_state.project_id,
        )

        # Create test file
        test_content = f'''"""
Tests for {project_state.project_name}.

This module contains unit tests for the core functionality.
Generated by Developer Agent.
"""

import pytest
from unittest.mock import MagicMock, patch

# Import modules to test (adjust paths as needed)
# from src.main import Application
# from src.models import Entity, Task, Status


class TestApplication:
    """Tests for the Application class."""

    def test_initialization(self):
        """Test application initializes correctly."""
        # app = Application()
        # assert app._initialized is False
        pass

    def test_initialize_sets_flag(self):
        """Test initialize method sets initialized flag."""
        # app = Application()
        # app.initialize()
        # assert app._initialized is True
        pass

    def test_double_initialize_warns(self):
        """Test double initialization logs warning."""
        # app = Application()
        # app.initialize()
        # with patch('src.main.logger') as mock_logger:
        #     app.initialize()
        #     mock_logger.warning.assert_called_once()
        pass

    def test_run_auto_initializes(self):
        """Test run method auto-initializes if needed."""
        # app = Application()
        # app.run()
        # assert app._initialized is True
        pass

    def test_shutdown_cleans_up(self):
        """Test shutdown cleans up resources."""
        # app = Application()
        # app.initialize()
        # app.shutdown()
        # assert app._initialized is False
        pass


class TestModels:
    """Tests for data models."""

    def test_entity_default_status(self):
        """Test entity has pending status by default."""
        # entity = Entity(name="Test")
        # assert entity.status == Status.PENDING
        pass

    def test_entity_activate(self):
        """Test entity activation."""
        # entity = Entity(name="Test")
        # entity.activate()
        # assert entity.status == Status.ACTIVE
        pass

    def test_task_assignment(self):
        """Test task assignment."""
        # task = Task(title="Test Task")
        # task.assign("user@example.com")
        # assert task.assignee == "user@example.com"
        pass


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
'''

        self._create_artifact(
            "tests/test_main.py",
            test_content,
            phase,
            project_state.project_id,
        )

        # Create development report
        dev_content = f"""# Development Report

## Project: {project_state.project_name}
## Client: {project_state.client}
## Phase: {phase.value}

### Implementation Summary
Code implementation completed for core application structure.

### Files Created/Modified

| File | Description | Lines |
|------|-------------|-------|
| src/main.py | Main application module | ~70 |
| src/models.py | Data models | ~75 |
| tests/test_main.py | Unit tests | ~80 |

### Architecture Decisions

- Used dataclasses for clean, typed data models
- Implemented basic lifecycle management (init, run, shutdown)
- Status enum for consistent state management
- Logging integrated for debugging and monitoring

### Code Metrics

- Lines of code: ~225
- Test coverage: Scaffolded (tests need implementation)
- Type hints: Full coverage
- Documentation: Docstrings on all public APIs

### Next Steps

1. Implement actual business logic in Application.run()
2. Add database integration if required
3. Complete test implementations
4. Add configuration management

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

        # Run subagents if configured
        subagent_summaries = []
        for subagent_id, subagent_config in self.config.subagents.items():
            summary = await self._run_subagent(subagent_config, phase, project_state, ctx)
            subagent_summaries.append(summary)

        # Emit event
        self._record_event(
            "developer_acted",
            phase.value,
            artifacts=len(self._artifacts),
            subagents=len(subagent_summaries),
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
            execution_summary=f"Created code artifacts for {project_state.project_name}",
            recommendations=[
                "Complete test implementations with actual assertions",
                "Add error handling for edge cases",
                "Consider adding configuration file support",
            ],
        )

    async def summarize(
        self,
        plan: AgentPlan,
        output: AgentOutput,
        project_state: ProjectState,
    ) -> AgentSummary:
        """Summarize development work.

        Summary includes:
        - Files created/modified
        - Code metrics
        - Recommendations for QA

        Args:
            plan: Execution plan.
            output: Execution output.
            project_state: Project state.

        Returns:
            Execution summary.
        """
        summary = await super().summarize(plan, output, project_state)

        # Enhance summary with developer-specific details
        summary.summary = (
            f"Developer completed {len(plan.steps)} implementation steps: "
            f"code structure setup, feature implementation, test writing, "
            f"and linting. Produced {len(self._artifacts)} artifacts."
        )

        # Add developer-specific recommendations
        summary.recommendations = output.recommendations + [
            "Run full test suite before deployment",
            "Review code for security vulnerabilities",
        ]

        return summary
