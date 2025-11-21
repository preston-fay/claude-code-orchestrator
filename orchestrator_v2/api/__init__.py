"""
API module for Orchestrator v2.

Provides interfaces and DTOs for external integration,
including the Ready/Set/Go UI.
"""

from orchestrator_v2.api.interfaces import OrchestratorAPI
from orchestrator_v2.api.dto import (
    ProjectDTO,
    PhaseDTO,
    CheckpointDTO,
    StatusDTO,
)

__all__ = [
    "OrchestratorAPI",
    "ProjectDTO",
    "PhaseDTO",
    "CheckpointDTO",
    "StatusDTO",
]
