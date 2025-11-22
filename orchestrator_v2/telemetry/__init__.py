"""
Telemetry module for Orchestrator v2.

Provides token tracking, cost management, and observability.

See ADR-005 for token efficiency architecture.
"""

from orchestrator_v2.telemetry.token_tracking import TokenTracker
from orchestrator_v2.telemetry.events import EventEmitter, EventType, OrchestratorEvent
from orchestrator_v2.telemetry.events_repository import (
    EventRepository,
    get_event_repository,
    emit_event,
)
from orchestrator_v2.telemetry.otel_tracing import TracingManager
from orchestrator_v2.telemetry.budget_enforcer import (
    BudgetEnforcer,
    BudgetExceededError,
)

__all__ = [
    "TokenTracker",
    "EventEmitter",
    "EventType",
    "OrchestratorEvent",
    "EventRepository",
    "get_event_repository",
    "emit_event",
    "TracingManager",
    "BudgetEnforcer",
    "BudgetExceededError",
]
