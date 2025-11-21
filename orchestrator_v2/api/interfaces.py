"""
API interfaces for Orchestrator v2.

Defines the interface for external integration.
"""

from pathlib import Path
from typing import Protocol

from orchestrator_v2.api.dto import (
    CheckpointDTO,
    GovernanceResultDTO,
    PhaseDTO,
    ProjectDTO,
    StatusDTO,
)


class OrchestratorAPI(Protocol):
    """API interface for Orchestrator v2.

    This interface defines the contract for external
    integration with the orchestrator, including UIs
    like Ready/Set/Go.
    """

    async def create_project(
        self,
        intake_path: Path,
    ) -> ProjectDTO:
        """Create a new project from intake.

        Args:
            intake_path: Path to intake.yaml.

        Returns:
            Created project DTO.

        TODO: Implement project creation
        """
        ...

    async def get_project(self, project_id: str) -> ProjectDTO:
        """Get project by ID.

        Args:
            project_id: Project identifier.

        Returns:
            Project DTO.

        TODO: Implement project retrieval
        """
        ...

    async def get_status(self, project_id: str) -> StatusDTO:
        """Get workflow status.

        Args:
            project_id: Project identifier.

        Returns:
            Status DTO.

        TODO: Implement status retrieval
        """
        ...

    async def run_next_phase(self, project_id: str) -> PhaseDTO:
        """Run the next workflow phase.

        Args:
            project_id: Project identifier.

        Returns:
            Executed phase DTO.

        TODO: Implement phase execution
        """
        ...

    async def approve_phase(
        self,
        project_id: str,
        phase: str,
        approver: str,
    ) -> None:
        """Approve a phase for transition.

        Args:
            project_id: Project identifier.
            phase: Phase to approve.
            approver: Approver identifier.

        TODO: Implement phase approval
        """
        ...

    async def get_checkpoints(
        self,
        project_id: str,
    ) -> list[CheckpointDTO]:
        """Get checkpoints for a project.

        Args:
            project_id: Project identifier.

        Returns:
            List of checkpoint DTOs.

        TODO: Implement checkpoint listing
        """
        ...

    async def rollback(
        self,
        project_id: str,
        checkpoint_id: str,
    ) -> None:
        """Rollback to a checkpoint.

        Args:
            project_id: Project identifier.
            checkpoint_id: Checkpoint to rollback to.

        TODO: Implement rollback
        """
        ...

    async def get_governance_results(
        self,
        project_id: str,
        phase: str,
    ) -> GovernanceResultDTO:
        """Get governance results for a phase.

        Args:
            project_id: Project identifier.
            phase: Phase to get results for.

        Returns:
            Governance result DTO.

        TODO: Implement governance retrieval
        """
        ...
