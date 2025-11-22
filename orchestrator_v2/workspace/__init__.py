"""
Workspace module for Orchestrator v2.

Provides workspace management and path resolution
for project isolation.
"""

from orchestrator_v2.workspace.models import WorkspaceConfig, WorkspaceMetadata
from orchestrator_v2.workspace.manager import (
    WorkspaceError,
    WorkspaceManager,
    WorkspaceNotFoundError,
)

__all__ = [
    "WorkspaceConfig",
    "WorkspaceMetadata",
    "WorkspaceError",
    "WorkspaceManager",
    "WorkspaceNotFoundError",
]
