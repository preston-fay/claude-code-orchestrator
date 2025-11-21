"""
Configuration management for Orchestrator v2.

Handles loading and validation of workflow configurations,
governance policies, and budget settings.
"""

from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel

from orchestrator_v2.core.state_models import (
    BudgetConfig,
    PhaseType,
    WorkflowConfig,
)


class IntakeConfig(BaseModel):
    """Configuration loaded from intake.yaml."""
    project: dict[str, Any]
    requirements: list[str] = []
    constraints: dict[str, Any] = {}
    data: dict[str, Any] = {}
    orchestration: dict[str, Any] = {}


class ConfigLoader:
    """Load and validate orchestrator configurations.

    This class handles loading intake files, governance policies,
    and other configuration sources.
    """

    def __init__(self, base_path: Path | None = None):
        """Initialize the config loader.

        Args:
            base_path: Base path for resolving relative config paths.
        """
        self.base_path = base_path or Path.cwd()

    def load_intake(self, intake_path: Path) -> WorkflowConfig:
        """Load workflow configuration from intake.yaml.

        Args:
            intake_path: Path to the intake.yaml file.

        Returns:
            WorkflowConfig with validated settings.

        TODO: Implement YAML loading and validation
        TODO: Merge with default configurations
        TODO: Validate required fields per ADR-002
        """
        ...

    def load_governance_policy(self, client: str) -> dict[str, Any]:
        """Load governance policy for a client.

        Policy hierarchy (most specific wins):
        1. Client-specific: clients/{client}/governance.yaml
        2. Kearney default: governance/kearney-default.yaml
        3. Universal: governance/universal.yaml

        See ADR-004 for governance policy details.

        Args:
            client: Client identifier.

        Returns:
            Composed governance policy dict.

        TODO: Implement policy loading
        TODO: Implement policy composition/merging
        TODO: Validate policy schema
        """
        ...

    def load_budget_config(
        self,
        workflow_config: WorkflowConfig,
        governance_policy: dict[str, Any],
    ) -> BudgetConfig:
        """Load budget configuration from workflow and governance.

        Budget limits cascade: Workflow > Governance > Defaults

        See ADR-005 for budget hierarchy details.

        Args:
            workflow_config: Workflow configuration.
            governance_policy: Governance policy dict.

        Returns:
            BudgetConfig with resolved limits.

        TODO: Implement budget resolution
        TODO: Apply governance overrides
        """
        ...

    def get_phase_graph(self, project_type: str) -> list[PhaseType]:
        """Get the phase graph for a project type.

        Different project types have different phase sequences.
        See ADR-002 for project-type phase variants.

        Args:
            project_type: Type of project (analytics, ml, webapp, etc.)

        Returns:
            Ordered list of phases for this project type.

        TODO: Implement phase graph resolution
        TODO: Support custom phase graphs
        """
        # Default phase graph
        default_graph = [
            PhaseType.INTAKE,
            PhaseType.PLANNING,
            PhaseType.ARCHITECTURE,
            PhaseType.CONSENSUS,
            PhaseType.DEVELOPMENT,
            PhaseType.QA,
            PhaseType.CONSENSUS,
            PhaseType.DOCUMENTATION,
            PhaseType.REVIEW,
            PhaseType.HYGIENE,
            PhaseType.COMPLETE,
        ]
        return default_graph

    def validate_config(self, config: WorkflowConfig) -> list[str]:
        """Validate workflow configuration.

        Args:
            config: Workflow configuration to validate.

        Returns:
            List of validation errors (empty if valid).

        TODO: Implement comprehensive validation
        TODO: Check required fields
        TODO: Validate phase/agent references
        """
        errors: list[str] = []
        # TODO: Add validation logic
        return errors


def load_yaml_file(path: Path) -> dict[str, Any]:
    """Load a YAML file safely.

    Args:
        path: Path to YAML file.

    Returns:
        Parsed YAML as dict.

    TODO: Implement safe YAML loading
    TODO: Handle file not found
    TODO: Handle parse errors
    """
    ...
