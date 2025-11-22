"""
Event emission for Orchestrator v2.

Handles structured event logging.

See ADR-005 for observability.
"""

from datetime import datetime
from enum import Enum
from typing import Any
import uuid

from pydantic import BaseModel, Field


class EventType(str, Enum):
    """Types of orchestrator events."""
    # Phase lifecycle
    PHASE_STARTED = "phase_started"
    PHASE_COMPLETED = "phase_completed"
    PHASE_FAILED = "phase_failed"

    # Agent lifecycle
    AGENT_STARTED = "agent_started"
    AGENT_COMPLETED = "agent_completed"
    AGENT_FAILED = "agent_failed"

    # Checkpoint events
    CHECKPOINT_CREATED = "checkpoint_created"
    CHECKPOINT_PASSED = "checkpoint_passed"
    CHECKPOINT_FAILED = "checkpoint_failed"

    # Governance events
    GOVERNANCE_CHECK_STARTED = "governance_check_started"
    GOVERNANCE_CHECK_PASSED = "governance_check_passed"
    GOVERNANCE_CHECK_FAILED = "governance_check_failed"

    # LLM events
    LLM_REQUEST_STARTED = "llm_request_started"
    LLM_REQUEST_COMPLETED = "llm_request_completed"
    LLM_REQUEST_FAILED = "llm_request_failed"

    # Workflow events
    WORKFLOW_STARTED = "workflow_started"
    WORKFLOW_COMPLETED = "workflow_completed"
    WORKFLOW_FAILED = "workflow_failed"

    # Generic info
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"


class OrchestratorEvent(BaseModel):
    """Event emitted during orchestrator execution."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    event_type: EventType
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    project_id: str
    phase: str | None = None
    agent_id: str | None = None
    message: str
    data: dict[str, Any] = Field(default_factory=dict)


class Event(BaseModel):
    """Structured event (legacy compatibility)."""
    event_type: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    workflow_id: str
    phase: str | None = None
    agent_id: str | None = None
    data: dict[str, Any] = Field(default_factory=dict)


class EventEmitter:
    """Emit structured events for observability.

    TODO: Implement event emission
    TODO: Support multiple sinks (file, stdout, remote)
    """

    def __init__(self):
        """Initialize the event emitter."""
        self._events: list[Event] = []

    def emit(
        self,
        event_type: str,
        workflow_id: str,
        phase: str | None = None,
        agent_id: str | None = None,
        **data: Any,
    ) -> None:
        """Emit an event.

        Args:
            event_type: Type of event.
            workflow_id: Workflow identifier.
            phase: Current phase.
            agent_id: Agent identifier.
            **data: Additional event data.

        TODO: Implement event emission
        TODO: Write to configured sinks
        """
        event = Event(
            event_type=event_type,
            workflow_id=workflow_id,
            phase=phase,
            agent_id=agent_id,
            data=data,
        )
        self._events.append(event)

    def get_events(
        self,
        workflow_id: str,
        event_type: str | None = None,
    ) -> list[Event]:
        """Get events for a workflow.

        Args:
            workflow_id: Workflow identifier.
            event_type: Optional type filter.

        Returns:
            List of events.

        TODO: Implement event retrieval
        """
        events = [e for e in self._events if e.workflow_id == workflow_id]
        if event_type:
            events = [e for e in events if e.event_type == event_type]
        return events
