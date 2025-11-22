# Telemetry

Observability and tracking for Orchestrator v2.

## Purpose

Provides monitoring and tracking capabilities:
- Event logging for execution activity
- Token usage tracking and budgets
- OpenTelemetry tracing integration

## Key Components

- **events.py**: `EventType` enum and `OrchestratorEvent` model
- **events_repository.py**: Event persistence and retrieval
- **token_tracking.py**: `TokenTracker` for usage monitoring
- **budget_enforcer.py**: Token budget enforcement
- **otel_tracing.py**: OpenTelemetry integration

## Events System

Events capture execution lifecycle:
- Workflow started/completed/failed
- Phase started/completed/failed
- Agent started/completed/failed
- Governance checks
- LLM requests

```python
from orchestrator_v2.telemetry import emit_event, EventType

emit_event(
    EventType.PHASE_STARTED,
    project_id="...",
    message="Phase planning started",
    phase="planning"
)
```

## Token Tracking

```python
from orchestrator_v2.telemetry import TokenTracker

tracker = TokenTracker()
tracker.track_llm_call(
    workflow_id="...",
    phase="planning",
    agent_id="architect",
    input_tokens=500,
    output_tokens=200
)

usage = tracker.get_usage(workflow_id)
```

## Related Documentation

- ADR-005: Token Efficiency Architecture
