"""
Phases module for RSC.

Provides phase execution services for all orchestration phases.
"""

from orchestrator_v2.phases.execution_service import (
    PhaseExecutionService,
    get_execution_service,
)

__all__ = [
    "PhaseExecutionService",
    "get_execution_service",
]
