# Engine

Core workflow orchestration engine for Orchestrator v2.

## Purpose

The engine module contains the central orchestration logic that coordinates:
- Workflow initialization and state management
- Phase transitions and checkpoint creation
- Agent execution and lifecycle management
- Governance gate evaluation
- Token budget enforcement

## Key Components

- **engine.py**: `WorkflowEngine` - Central orchestrator that runs phases and agents
- **phase_manager.py**: `PhaseManager` - Manages phase definitions and transitions
- **state_models.py**: Data models for project state, phases, agents, checkpoints
- **config.py**: Workflow configuration
- **exceptions.py**: Custom exceptions for orchestrator errors
- **model_selection.py**: LLM model selection based on agent role and user entitlements

## Usage

```python
from orchestrator_v2.engine import WorkflowEngine

engine = WorkflowEngine()
state = await engine.start_project(
    project_name="My Project",
    client="kearney-default"
)
await engine.run_phase()
```

## Related Documentation

- ADR-001: Agent Coordination Patterns
- ADR-002: Phase and Checkpoint Model
- docs/orchestrator-v2-architecture.md
