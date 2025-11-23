"""
Planning module for RSC.

Provides the planning pipeline service for multi-agent consensus
and artifact generation.
"""

from orchestrator_v2.planning.pipeline import (
    PlanningPipelineService,
    get_planning_service,
)

__all__ = [
    "PlanningPipelineService",
    "get_planning_service",
]
