"""
API module for Orchestrator v2.

Provides interfaces and DTOs for external integration,
including the Ready/Set/Go UI.
"""

from orchestrator_v2.api.interfaces import OrchestratorAPI
from orchestrator_v2.api.dto import (
    AgentStatusDTO,
    CheckpointDTO,
    GovernanceResultDTO,
    PhaseDTO,
    ProjectDTO,
    StatusDTO,
)
from orchestrator_v2.api.server import app, create_app

__all__ = [
    # Interfaces
    "OrchestratorAPI",
    # DTOs
    "AgentStatusDTO",
    "CheckpointDTO",
    "GovernanceResultDTO",
    "PhaseDTO",
    "ProjectDTO",
    "StatusDTO",
    # Server
    "app",
    "create_app",
]
