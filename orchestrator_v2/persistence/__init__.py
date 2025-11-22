"""
Persistence layer for Orchestrator v2.

Provides repository interfaces and implementations for
durable storage of projects, checkpoints, and artifacts.

See ADR-002 for checkpoint persistence details.
"""

from orchestrator_v2.persistence.interfaces import (
    ArtifactRepository,
    CheckpointRepository,
    GovernanceLogRepository,
    ProjectRepository,
)
from orchestrator_v2.persistence.fs_repository import (
    FileSystemArtifactRepository,
    FileSystemCheckpointRepository,
    FileSystemGovernanceLogRepository,
    FileSystemProjectRepository,
)

__all__ = [
    # Interfaces
    "ProjectRepository",
    "CheckpointRepository",
    "ArtifactRepository",
    "GovernanceLogRepository",
    # Implementations
    "FileSystemProjectRepository",
    "FileSystemCheckpointRepository",
    "FileSystemArtifactRepository",
    "FileSystemGovernanceLogRepository",
]
