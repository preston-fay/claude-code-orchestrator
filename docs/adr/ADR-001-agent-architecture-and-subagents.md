# ADR-001: Agent Architecture and Subagents

**Status:** Accepted
**Date:** 2025-11-21
**Deciders:** Platform Team
**Supersedes:** N/A

## Context

The current Orchestrator v1 uses a hybrid approach where some agents (Architect, Developer, QA, Documentarian, Consensus, Reviewer) are LLM-based with prompt templates, while others (Data, Steward) are subprocess-based with Python entrypoints. This works but has limitations:

1. **Inconsistent agent interfaces** - LLM agents use prompt interpolation while subprocess agents use command execution
2. **Limited composability** - No clean way to have sub-agents (e.g., FrontendDeveloper, BackendDeveloper under Developer)
3. **No standardized lifecycle** - Each agent type has different initialization, execution, and cleanup patterns
4. **Poor traceability** - Agent decisions and tool usage are not uniformly tracked

As we move to Orchestrator v2, we need a consistent agent model that:
- Leverages Claude Agent SDK patterns for all agents
- Supports hierarchical agent structures (agents with subagents)
- Provides uniform lifecycle management
- Enables better observability and debugging

## Decision

**We will implement all role agents as first-class agents using a Claude Agent SDK-compatible pattern, with support for optional subagents.**

### Agent Model

Each agent will have:

1. **Identity & Mission**
   - Unique agent ID (e.g., `architect`, `developer.frontend`)
   - System prompt encoding role, constraints, and capabilities
   - Allowed skills and tools (explicit whitelist)

2. **Standardized Lifecycle**
   ```
   INITIALIZE → PLAN → ACT (multi-step) → SUMMARIZE → COMPLETE
   ```
   - **Initialize**: Load context, previous artifacts, governance constraints
   - **Plan**: Analyze task and create execution plan
   - **Act**: Execute plan steps, may invoke tools/skills
   - **Summarize**: Produce structured output and artifacts
   - **Complete**: Clean up, report metrics

3. **Configuration Structure**
   ```yaml
   agent:
     id: developer
     type: llm  # or subprocess
     system_prompt: prompts/developer.md
     skills:
       - code_generation
       - test_writing
     tools:
       - git
       - file_system
       - linter
     subagents:
       - id: developer.frontend
         system_prompt: prompts/developer_frontend.md
         skills: [react, css]
       - id: developer.backend
         system_prompt: prompts/developer_backend.md
         skills: [fastapi, database]
   ```

### Role Agent Mapping

| Agent | Type | Subagents (Optional) |
|-------|------|----------------------|
| Architect | LLM | architect.data, architect.security |
| Data | LLM/Subprocess | data.ingestion, data.transform, data.training |
| Developer | LLM | developer.frontend, developer.backend, developer.infra |
| QA | LLM | qa.unit, qa.integration, qa.security |
| Documentarian | LLM | documentarian.api, documentarian.user |
| Consensus | LLM | N/A |
| Steward | Subprocess | steward.hygiene, steward.security |
| Reviewer | LLM | N/A |

### Execution Model

1. **Parent agents** receive the full task and decide whether to:
   - Handle it directly
   - Delegate to one or more subagents
   - Split work across subagents and aggregate results

2. **Subagents** are scoped versions of parent agents:
   - Inherit parent's base capabilities
   - Have specialized skills/tools
   - Report back to parent agent

3. **Parallel execution** is supported:
   - Multiple subagents can run concurrently
   - Parent agent aggregates results
   - Controlled by concurrency limits in config

## Consequences

### Benefits

1. **Modularity** - Each agent is a self-contained unit with clear interfaces
2. **Composability** - Subagents allow specialization without explosion of top-level agents
3. **Parallelism** - Subagents can execute concurrently (e.g., frontend + backend dev)
4. **Traceability** - Uniform lifecycle means consistent logging and metrics
5. **Testability** - Agents can be tested in isolation with mock tools/skills
6. **Extensibility** - New agents/subagents can be added without modifying core orchestration

### Trade-offs

1. **Increased complexity** - More configuration and lifecycle management
2. **Migration effort** - Existing agents need refactoring to new model
3. **Potential overhead** - Subagent coordination adds latency
4. **Learning curve** - Team needs to understand agent patterns

### Risks & Mitigations

| Risk | Mitigation |
|------|------------|
| Subagent explosion | Limit depth to 2 levels (agent → subagent only) |
| Context fragmentation | Parent agent provides unified context to subagents |
| Coordination failures | Implement timeout and fallback to parent handling |

## Alternatives Considered

### 1. Keep Current Hybrid Model
- **Pros:** No migration effort, working today
- **Cons:** Inconsistent interfaces, limited composability, poor observability
- **Why rejected:** Doesn't scale for v2 requirements

### 2. Pure Function Model (No Agents)
- **Pros:** Simpler, no agent lifecycle
- **Cons:** Loses statefulness, harder to implement multi-step reasoning
- **Why rejected:** Agents provide better abstraction for complex tasks

### 3. External Agent Framework (LangGraph, CrewAI)
- **Pros:** Battle-tested, community support
- **Cons:** External dependency, may not align with Claude-specific patterns
- **Why rejected:** Prefer Claude-native patterns for better integration

## Implementation Notes

### Phase 1: Agent Interface
```python
class Agent(Protocol):
    id: str
    config: AgentConfig

    async def initialize(self, context: AgentContext) -> None: ...
    async def plan(self, task: Task) -> ExecutionPlan: ...
    async def act(self, plan: ExecutionPlan) -> List[ActionResult]: ...
    async def summarize(self, results: List[ActionResult]) -> AgentOutput: ...
```

### Phase 2: Subagent Support
```python
class ParentAgent(Agent):
    subagents: Dict[str, Agent]

    async def delegate(self, task: Task, subagent_ids: List[str]) -> List[AgentOutput]:
        results = await asyncio.gather(*[
            self.subagents[id].run(task) for id in subagent_ids
        ])
        return results
```

### Phase 3: Migration
1. Wrap existing LLM agents in new interface
2. Convert subprocess agents to new lifecycle
3. Add subagent support to Developer, QA, Data agents
4. Update orchestrator to use new agent registry

## Related Decisions

- ADR-002: Phase Model and Checkpoints (agent outputs feed checkpoints)
- ADR-003: Skills and Tools (agents declare skill/tool dependencies)
- ADR-005: Token Efficiency (agent-level token budgets)
