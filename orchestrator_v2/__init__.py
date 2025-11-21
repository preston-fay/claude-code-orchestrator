"""
Orchestrator v2 - AI-Driven Software Delivery Framework

A comprehensive orchestration system for coordinating multiple specialized
Claude Code agents through a structured, checkpoint-driven workflow.

See docs/orchestrator-v2-architecture.md for full architecture documentation.
"""

__version__ = "2.0.0-alpha"
__author__ = "Kearney Platform Team"

from orchestrator_v2.engine.engine import WorkflowEngine
from orchestrator_v2.engine.phase_manager import PhaseManager
from orchestrator_v2.engine.state_models import (
    ProjectState,
    PhaseState,
    AgentState,
    WorkflowConfig,
)

__all__ = [
    "WorkflowEngine",
    "PhaseManager",
    "ProjectState",
    "PhaseState",
    "AgentState",
    "WorkflowConfig",
]
