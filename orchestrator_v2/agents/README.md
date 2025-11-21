# Agents

Multi-role agent implementations for Orchestrator v2.

## Purpose

Agents are specialized AI workers that execute specific tasks within phases:
- Each agent has a defined role (Architect, Developer, QA, etc.)
- Agents follow a lifecycle: Initialize → Plan → Act → Summarize → Complete
- Agents produce artifacts and track token usage

## Agent Roles

- **Architect**: System design, data models, technical specifications
- **Data**: Data engineering, ETL pipelines, analytics, model training
- **Developer**: Feature implementation, code writing
- **QA**: Testing, validation, quality assurance
- **Documentarian**: Documentation, README files, user guides
- **Consensus**: Reviews proposals, identifies conflicts, builds agreement
- **Steward**: Repository hygiene, dead code identification
- **Reviewer**: Code reviews and feedback (optional)

## Adding a New Agent

1. Create a new file (e.g., `my_agent.py`)
2. Extend `BaseAgent` and implement required methods:

```python
from orchestrator_v2.agents.base_agent import BaseAgent

class MyAgent(BaseAgent):
    def initialize(self, state):
        # Load context
        pass

    def plan(self, task):
        # Create execution plan
        pass

    def act(self, step, context):
        # Execute plan step
        pass

    def summarize(self, run_id):
        # Produce summary
        pass

    def complete(self, state):
        # Cleanup
        pass
```

3. Register the agent with the engine

## Related Documentation

- ADR-001: Agent Coordination Patterns
- CLAUDE.md: Intended subagents section
