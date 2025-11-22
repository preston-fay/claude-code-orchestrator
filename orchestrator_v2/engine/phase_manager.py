"""
Phase Manager for Orchestrator v2.

The PhaseManager handles workflow phase definitions, transitions,
and phase execution coordination.

See ADR-002 for phase model details.
"""

from typing import Any

from orchestrator_v2.engine.exceptions import AgentError, PhaseError
from orchestrator_v2.engine.state_models import (
    AgentContext,
    AgentOutput,
    AgentPlan,
    AgentState,
    AgentStatus,
    AgentSummary,
    ArtifactInfo,
    PhaseDefinition,
    PhaseState,
    PhaseType,
    ProjectState,
    TaskDefinition,
    TokenUsage,
    WorkflowDefinition,
)


def get_default_workflow() -> WorkflowDefinition:
    """Get the default analytics workflow definition.

    This defines the canonical phase sequence for analytics projects.
    See ADR-002 for phase graph details.

    Returns:
        Default WorkflowDefinition.
    """
    return WorkflowDefinition(
        name="analytics_workflow",
        description="Standard analytics project workflow",
        project_type="analytics",
        phases=[
            PhaseDefinition(
                name=PhaseType.PLANNING,
                order=0,
                responsible_agents=["architect"],
                inputs=["intake.yaml"],
                outputs=["project_plan.md", "requirements.md"],
                quality_gates=["plan_completeness"],
                description="Analyze requirements and plan project approach",
            ),
            PhaseDefinition(
                name=PhaseType.ARCHITECTURE,
                order=1,
                responsible_agents=["architect"],
                inputs=["project_plan.md", "requirements.md"],
                outputs=["architecture.md", "data_model.md"],
                quality_gates=["architecture_review"],
                description="Design system architecture and data models",
            ),
            PhaseDefinition(
                name=PhaseType.DATA,
                order=2,
                responsible_agents=["data"],
                inputs=["architecture.md", "data_model.md"],
                outputs=["data/processed/", "models/", "metrics.json"],
                quality_gates=["data_quality", "model_performance"],
                description="Build data pipelines and train models",
                optional=True,
            ),
            PhaseDefinition(
                name=PhaseType.DEVELOPMENT,
                order=3,
                responsible_agents=["developer"],
                inputs=["architecture.md"],
                outputs=["src/", "tests/"],
                quality_gates=["test_coverage", "code_quality"],
                description="Implement features and write tests",
            ),
            PhaseDefinition(
                name=PhaseType.QA,
                order=4,
                responsible_agents=["qa"],
                inputs=["src/", "tests/"],
                outputs=["test_report.md", "coverage.json"],
                quality_gates=["test_pass_rate", "security_scan"],
                description="Execute tests and validate quality",
            ),
            PhaseDefinition(
                name=PhaseType.DOCUMENTATION,
                order=5,
                responsible_agents=["documentarian"],
                inputs=["src/", "architecture.md"],
                outputs=["docs/", "README.md"],
                quality_gates=["doc_completeness"],
                description="Create technical and user documentation",
            ),
        ],
    )


class PhaseManager:
    """Manages workflow phases and transitions.

    The PhaseManager:
    - Holds the workflow definition
    - Determines current and next phases
    - Validates phase transitions
    - Provides phase metadata

    See ADR-002 for phase model details.
    """

    def __init__(self, workflow_definition: WorkflowDefinition | None = None):
        """Initialize the PhaseManager.

        Args:
            workflow_definition: Workflow definition to use.
                Defaults to the standard analytics workflow.
        """
        self._workflow_definition = workflow_definition or get_default_workflow()

    @property
    def workflow_definition(self) -> WorkflowDefinition:
        """Get the workflow definition."""
        return self._workflow_definition

    def get_current_phase(self, project_state: ProjectState) -> PhaseDefinition:
        """Get the current phase definition.

        Args:
            project_state: Current project state.

        Returns:
            Current phase definition.

        Raises:
            ValueError: If current phase not found in workflow.
        """
        phase_def = self._workflow_definition.get_phase_by_type(
            project_state.current_phase
        )
        if phase_def is None:
            raise ValueError(
                f"Phase {project_state.current_phase} not found in workflow"
            )
        return phase_def

    def get_next_phase(self, project_state: ProjectState) -> PhaseDefinition | None:
        """Get the next phase definition.

        Args:
            project_state: Current project state.

        Returns:
            Next phase definition, or None if workflow is complete.
        """
        current_order = self._workflow_definition.get_phase_order(
            project_state.current_phase
        )

        for phase in sorted(self._workflow_definition.phases, key=lambda p: p.order):
            if phase.order > current_order:
                return phase

        return None

    def get_phase_definition(self, phase_type: PhaseType) -> PhaseDefinition:
        """Get phase definition by type.

        Args:
            phase_type: Phase type to look up.

        Returns:
            Phase definition.

        Raises:
            ValueError: If phase not found.
        """
        phase_def = self._workflow_definition.get_phase_by_type(phase_type)
        if phase_def is None:
            raise ValueError(f"Phase {phase_type} not found in workflow")
        return phase_def

    def is_last_phase(self, phase: PhaseDefinition) -> bool:
        """Check if this is the last phase in the workflow.

        Args:
            phase: Phase to check.

        Returns:
            True if this is the last phase.
        """
        max_order = max(p.order for p in self._workflow_definition.phases)
        return phase.order >= max_order

    def get_agents_for_phase(self, phase_type: PhaseType) -> list[str]:
        """Get responsible agent IDs for a phase.

        Args:
            phase_type: Phase to get agents for.

        Returns:
            List of agent IDs.
        """
        phase_def = self.get_phase_definition(phase_type)
        return phase_def.responsible_agents

    def validate_phase_transition(
        self,
        from_phase: PhaseType,
        to_phase: PhaseType,
        completed_phases: list[PhaseType],
    ) -> tuple[bool, str]:
        """Validate a phase transition.

        Args:
            from_phase: Current phase.
            to_phase: Target phase.
            completed_phases: List of completed phases.

        Returns:
            Tuple of (is_valid, error_message).
        """
        from_order = self._workflow_definition.get_phase_order(from_phase)
        to_order = self._workflow_definition.get_phase_order(to_phase)

        if to_order <= from_order:
            return False, f"Cannot transition backward from {from_phase} to {to_phase}"

        if from_phase not in completed_phases:
            return False, f"Phase {from_phase} must be completed before transitioning"

        return True, ""

    def list_phases(self) -> list[PhaseDefinition]:
        """List all phases in order.

        Returns:
            Ordered list of phase definitions.
        """
        return sorted(self._workflow_definition.phases, key=lambda p: p.order)

    def get_phase_progress(self, project_state: ProjectState) -> dict[str, Any]:
        """Get workflow progress information.

        Args:
            project_state: Current project state.

        Returns:
            Progress dict with completion stats.
        """
        total_phases = len(self._workflow_definition.phases)
        completed = len(project_state.completed_phases)

        return {
            "total_phases": total_phases,
            "completed_phases": completed,
            "current_phase": project_state.current_phase.value,
            "progress_percent": (completed / total_phases * 100) if total_phases > 0 else 0,
        }
