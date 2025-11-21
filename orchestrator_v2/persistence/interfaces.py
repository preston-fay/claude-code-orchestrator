"""
Repository interfaces for Orchestrator v2 persistence.

Defines Protocol classes for repository abstractions that can be
implemented by different storage backends (FileSystem, S3, Database, etc.).

See ADR-002 for persistence architecture.
"""

from typing import Protocol

from orchestrator_v2.core.state_models import (
    ArtifactInfo,
    CheckpointState,
    GovernanceResults,
    PhaseType,
    ProjectState,
)


class ProjectRepository(Protocol):
    """Repository interface for project state persistence."""

    async def save(self, project: ProjectState) -> None:
        """Save project state.

        Args:
            project: Project state to save.
        """
        ...

    async def load(self, project_id: str) -> ProjectState:
        """Load project state by ID.

        Args:
            project_id: Project identifier.

        Returns:
            Loaded ProjectState.

        Raises:
            KeyError: If project not found.
        """
        ...

    async def list_projects(self) -> list[str]:
        """List all project IDs.

        Returns:
            List of project identifiers.
        """
        ...

    async def delete(self, project_id: str) -> None:
        """Delete a project.

        Args:
            project_id: Project identifier.
        """
        ...

    async def exists(self, project_id: str) -> bool:
        """Check if project exists.

        Args:
            project_id: Project identifier.

        Returns:
            True if project exists.
        """
        ...


class CheckpointRepository(Protocol):
    """Repository interface for checkpoint persistence."""

    async def save(self, checkpoint: CheckpointState) -> None:
        """Save checkpoint state.

        Args:
            checkpoint: Checkpoint state to save.
        """
        ...

    async def load(self, checkpoint_id: str) -> CheckpointState:
        """Load checkpoint by ID.

        Args:
            checkpoint_id: Checkpoint identifier.

        Returns:
            Loaded CheckpointState.

        Raises:
            KeyError: If checkpoint not found.
        """
        ...

    async def list_for_project(self, project_id: str) -> list[str]:
        """List checkpoint IDs for a project.

        Args:
            project_id: Project identifier.

        Returns:
            List of checkpoint identifiers.
        """
        ...

    async def list_for_phase(
        self,
        project_id: str,
        phase: PhaseType,
    ) -> list[str]:
        """List checkpoint IDs for a phase.

        Args:
            project_id: Project identifier.
            phase: Phase type.

        Returns:
            List of checkpoint identifiers.
        """
        ...

    async def get_latest(
        self,
        project_id: str,
        phase: PhaseType | None = None,
    ) -> CheckpointState | None:
        """Get the latest checkpoint.

        Args:
            project_id: Project identifier.
            phase: Optional phase filter.

        Returns:
            Latest checkpoint or None.
        """
        ...

    async def delete(self, checkpoint_id: str) -> None:
        """Delete a checkpoint.

        Args:
            checkpoint_id: Checkpoint identifier.
        """
        ...


class ArtifactRepository(Protocol):
    """Repository interface for artifact storage."""

    async def save(
        self,
        project_id: str,
        artifact: ArtifactInfo,
        content: bytes,
    ) -> str:
        """Save artifact content.

        Args:
            project_id: Project identifier.
            artifact: Artifact metadata.
            content: Artifact content bytes.

        Returns:
            Storage path or identifier.
        """
        ...

    async def load(
        self,
        project_id: str,
        artifact_path: str,
    ) -> bytes:
        """Load artifact content.

        Args:
            project_id: Project identifier.
            artifact_path: Artifact path.

        Returns:
            Artifact content bytes.

        Raises:
            KeyError: If artifact not found.
        """
        ...

    async def list_for_project(self, project_id: str) -> list[ArtifactInfo]:
        """List artifacts for a project.

        Args:
            project_id: Project identifier.

        Returns:
            List of artifact metadata.
        """
        ...

    async def list_for_phase(
        self,
        project_id: str,
        phase: PhaseType,
    ) -> list[ArtifactInfo]:
        """List artifacts for a phase.

        Args:
            project_id: Project identifier.
            phase: Phase type.

        Returns:
            List of artifact metadata.
        """
        ...

    async def delete(
        self,
        project_id: str,
        artifact_path: str,
    ) -> None:
        """Delete an artifact.

        Args:
            project_id: Project identifier.
            artifact_path: Artifact path.
        """
        ...

    async def exists(
        self,
        project_id: str,
        artifact_path: str,
    ) -> bool:
        """Check if artifact exists.

        Args:
            project_id: Project identifier.
            artifact_path: Artifact path.

        Returns:
            True if artifact exists.
        """
        ...


class GovernanceLogRepository(Protocol):
    """Repository interface for governance audit logs."""

    async def log(
        self,
        project_id: str,
        phase: PhaseType,
        results: GovernanceResults,
    ) -> None:
        """Log governance evaluation results.

        Args:
            project_id: Project identifier.
            phase: Phase evaluated.
            results: Governance results.
        """
        ...

    async def get_logs(
        self,
        project_id: str,
        phase: PhaseType | None = None,
    ) -> list[dict]:
        """Get governance logs.

        Args:
            project_id: Project identifier.
            phase: Optional phase filter.

        Returns:
            List of governance log entries.
        """
        ...

    async def get_latest(
        self,
        project_id: str,
        phase: PhaseType,
    ) -> GovernanceResults | None:
        """Get latest governance results for phase.

        Args:
            project_id: Project identifier.
            phase: Phase type.

        Returns:
            Latest governance results or None.
        """
        ...
