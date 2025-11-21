# ADR-005: Token Efficiency and Cost Control

**Status:** Accepted
**Date:** 2025-11-21
**Deciders:** Platform Team
**Supersedes:** N/A

## Context

The current Orchestrator v1 has no systematic approach to token usage and cost management. This leads to:

1. **Unpredictable costs** - No visibility into token consumption until bill arrives
2. **Context bloat** - Agents receive full history, most of which is irrelevant
3. **No budgets** - Can't set limits per workflow, phase, or agent
4. **Wasteful patterns** - Repeated loading of same context across agents
5. **No optimization** - No incentive or mechanism to reduce token usage

For Orchestrator v2, we need:
- Real-time token tracking at granular levels
- Budget enforcement with configurable limits
- Context optimization to reduce unnecessary tokens
- Cost attribution for billing and analysis
- Automatic optimization strategies

## Decision

**We will implement a comprehensive token management system with real-time tracking, hierarchical budgets, intelligent context compression, and automatic optimization strategies.**

### Token Management Architecture

```
┌─────────────────────────────────────────────────────┐
│              TOKEN MANAGEMENT SYSTEM                │
├─────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐ │
│  │   Tracker   │  │   Budget    │  │  Optimizer  │ │
│  │   (Real-    │  │  Enforcer   │  │  (Context   │ │
│  │   time)     │  │             │  │   Mgmt)     │ │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘ │
│         │                │                │        │
│         v                v                v        │
│  ┌─────────────────────────────────────────────┐  │
│  │          Cost Attribution Engine            │  │
│  │   (Workflow → Phase → Agent → Tool)         │  │
│  └─────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────┘
```

### Budget Hierarchy

Budgets cascade from workflow to individual operations:

```yaml
# Budget configuration
budgets:
  # Workflow-level limit
  workflow:
    max_tokens: 2_000_000
    max_cost_usd: 50.00
    alert_threshold: 0.8  # Alert at 80%

  # Phase-level limits
  phases:
    planning:
      max_tokens: 200_000
      max_cost_usd: 5.00
    architecture:
      max_tokens: 300_000
      max_cost_usd: 8.00
    development:
      max_tokens: 800_000
      max_cost_usd: 20.00
    qa:
      max_tokens: 400_000
      max_cost_usd: 10.00
    documentation:
      max_tokens: 300_000
      max_cost_usd: 7.00

  # Agent-level limits (within phase)
  agents:
    architect:
      max_tokens_per_task: 50_000
    developer:
      max_tokens_per_task: 100_000
    qa:
      max_tokens_per_task: 75_000

  # Tool-level limits
  tools:
    file_read:
      max_tokens_per_call: 10_000
    code_generation:
      max_tokens_per_call: 20_000
```

### Real-Time Token Tracking

```python
class TokenTracker:
    def __init__(self):
        self.usage = defaultdict(lambda: {"input": 0, "output": 0})

    async def track_llm_call(
        self,
        workflow_id: str,
        phase: str,
        agent_id: str,
        request: LLMRequest,
        response: LLMResponse
    ) -> TokenUsage:
        """Track tokens for an LLM call."""

        usage = TokenUsage(
            input_tokens=response.usage.input_tokens,
            output_tokens=response.usage.output_tokens,
            cost=self._calculate_cost(response.usage)
        )

        # Attribute to hierarchy
        self._attribute(workflow_id, phase, agent_id, usage)

        # Check budgets
        await self._check_budgets(workflow_id, phase, agent_id, usage)

        return usage

    def _calculate_cost(self, usage: Usage) -> Decimal:
        """Calculate cost based on model pricing."""
        # Claude pricing (example)
        INPUT_COST_PER_1K = Decimal("0.003")
        OUTPUT_COST_PER_1K = Decimal("0.015")

        input_cost = (usage.input_tokens / 1000) * INPUT_COST_PER_1K
        output_cost = (usage.output_tokens / 1000) * OUTPUT_COST_PER_1K

        return input_cost + output_cost

    async def _check_budgets(
        self,
        workflow_id: str,
        phase: str,
        agent_id: str,
        usage: TokenUsage
    ) -> None:
        """Check if any budget thresholds exceeded."""

        # Check workflow budget
        workflow_total = self.get_workflow_total(workflow_id)
        if workflow_total.tokens > self.budgets.workflow.max_tokens:
            raise BudgetExceededError(
                f"Workflow budget exceeded: {workflow_total.tokens} tokens"
            )

        # Check phase budget
        phase_total = self.get_phase_total(workflow_id, phase)
        if phase_total.tokens > self.budgets.phases[phase].max_tokens:
            raise BudgetExceededError(
                f"Phase '{phase}' budget exceeded"
            )

        # Alert at threshold
        if workflow_total.cost / self.budgets.workflow.max_cost_usd > 0.8:
            await self._send_alert(workflow_id, "approaching_budget_limit")
```

### Context Optimization Strategies

#### Strategy 1: Selective Context Loading

```python
class ContextOptimizer:
    async def prepare_agent_context(
        self,
        agent: Agent,
        task: Task,
        full_context: WorkflowContext
    ) -> OptimizedContext:
        """Prepare minimal context for agent task."""

        # Start with essential context
        context = OptimizedContext()

        # Add task-specific items only
        context.add(task.description)
        context.add(task.requirements)

        # Add relevant artifacts (not all)
        relevant_artifacts = self._find_relevant_artifacts(
            agent.id,
            task,
            full_context.artifacts
        )
        for artifact in relevant_artifacts:
            context.add_artifact(artifact)

        # Add skill methodology (if using skill)
        if task.skill_id:
            skill = self.skill_registry.get(task.skill_id)
            context.add_skill(skill.methodology)

        # Add relevant ADRs only
        relevant_adrs = self._find_relevant_adrs(task, full_context.adrs)
        for adr in relevant_adrs:
            context.add_adr_summary(adr)  # Summary, not full text

        return context

    def _find_relevant_artifacts(
        self,
        agent_id: str,
        task: Task,
        artifacts: List[Artifact]
    ) -> List[Artifact]:
        """Find artifacts relevant to this agent and task."""

        relevant = []
        for artifact in artifacts:
            # Check if artifact type matches agent needs
            if artifact.type in AGENT_ARTIFACT_MAP[agent_id]:
                relevant.append(artifact)
            # Check if artifact is referenced in task
            elif artifact.id in task.references:
                relevant.append(artifact)

        return relevant
```

#### Strategy 2: Progressive Context Expansion

```python
class ProgressiveContextLoader:
    async def load_context(
        self,
        agent: Agent,
        task: Task,
        budget_remaining: int
    ) -> Context:
        """Load context progressively until budget limit."""

        context = Context()
        token_count = 0

        # Priority 1: Critical context (always include)
        critical = await self._get_critical_context(task)
        token_count += critical.token_count
        context.merge(critical)

        # Priority 2: Relevant history (include if budget allows)
        if token_count < budget_remaining * 0.7:
            history = await self._get_relevant_history(task, agent)
            token_count += history.token_count
            context.merge(history)

        # Priority 3: Background knowledge (include if budget allows)
        if token_count < budget_remaining * 0.9:
            background = await self._get_background(task)
            # Truncate if needed
            available = budget_remaining - token_count
            background = background.truncate_to(available)
            context.merge(background)

        return context
```

#### Strategy 3: Context Summarization

```python
class ContextSummarizer:
    async def summarize_for_handoff(
        self,
        phase_output: PhaseOutput,
        next_phase: str
    ) -> Summary:
        """Create concise summary for next phase."""

        # Don't pass raw artifacts, summarize them
        summary = Summary()

        # Summarize decisions made
        summary.add_section(
            "Decisions",
            await self._summarize_decisions(phase_output.adrs)
        )

        # Summarize artifacts created
        summary.add_section(
            "Artifacts",
            await self._list_artifacts_with_descriptions(phase_output.artifacts)
        )

        # Key findings (not full analysis)
        summary.add_section(
            "Key Findings",
            await self._extract_key_findings(phase_output.analysis)
        )

        # What next phase needs to know
        summary.add_section(
            "Handoff Notes",
            phase_output.handoff_notes
        )

        return summary
```

#### Strategy 4: Caching and Reuse

```python
class ContextCache:
    def __init__(self, redis_client):
        self.cache = redis_client

    async def get_or_compute(
        self,
        key: str,
        compute_fn: Callable,
        ttl: int = 3600
    ) -> CachedContext:
        """Cache expensive context computations."""

        # Check cache
        cached = await self.cache.get(key)
        if cached:
            return CachedContext.deserialize(cached)

        # Compute and cache
        result = await compute_fn()
        await self.cache.set(key, result.serialize(), ex=ttl)

        return result

    # Common cached items
    async def get_project_structure(self, repo_path: str) -> str:
        return await self.get_or_compute(
            f"structure:{repo_path}",
            lambda: analyze_project_structure(repo_path)
        )

    async def get_dependency_graph(self, repo_path: str) -> str:
        return await self.get_or_compute(
            f"deps:{repo_path}",
            lambda: analyze_dependencies(repo_path)
        )
```

### Cost Attribution and Reporting

```python
class CostReporter:
    def generate_workflow_report(
        self,
        workflow_id: str
    ) -> CostReport:
        """Generate detailed cost report for workflow."""

        usage = self.tracker.get_workflow_usage(workflow_id)

        return CostReport(
            workflow_id=workflow_id,
            total_tokens=usage.total_tokens,
            total_cost=usage.total_cost,

            # Breakdown by phase
            by_phase={
                phase: PhaseUsage(
                    tokens=phase_usage.tokens,
                    cost=phase_usage.cost,
                    percentage=phase_usage.tokens / usage.total_tokens
                )
                for phase, phase_usage in usage.phases.items()
            },

            # Breakdown by agent
            by_agent={
                agent: AgentUsage(
                    tokens=agent_usage.tokens,
                    cost=agent_usage.cost
                )
                for agent, agent_usage in usage.agents.items()
            },

            # Efficiency metrics
            efficiency={
                "context_reuse_rate": self._calc_reuse_rate(workflow_id),
                "avg_tokens_per_task": usage.total_tokens / usage.task_count,
                "optimization_savings": self._calc_savings(workflow_id)
            }
        )
```

### Budget Enforcement Actions

```yaml
# When budget exceeded
on_budget_exceeded:
  workflow:
    action: pause
    notification:
      - slack: "#project-alerts"
      - email: "pm@client.com"
    require_approval_to_continue: true

  phase:
    action: complete_with_reduced_scope
    notification:
      - log: "Phase budget exceeded, completing with reduced scope"

  agent:
    action: retry_with_smaller_context
    max_retries: 2
    context_reduction: 0.5  # Halve context each retry
```

### Integration with Agents

Agents receive budget information and adapt accordingly:

```python
class Agent:
    async def execute_task(self, task: Task) -> TaskResult:
        # Get remaining budget
        budget = await self.budget_enforcer.get_remaining(
            workflow_id=self.context.workflow_id,
            phase=self.context.phase,
            agent_id=self.id
        )

        # Adapt strategy based on budget
        if budget.tokens < 10_000:
            # Low budget: be concise
            strategy = "minimal"
        elif budget.tokens < 50_000:
            # Medium budget: balanced
            strategy = "balanced"
        else:
            # High budget: thorough
            strategy = "thorough"

        # Execute with strategy
        result = await self._execute_with_strategy(task, strategy)

        return result
```

## Consequences

### Benefits

1. **Cost predictability** - Know costs before they occur
2. **Budget enforcement** - Automatic limits prevent runaway spending
3. **Efficient context** - Only relevant information passed to agents
4. **Cost attribution** - Clear breakdown for billing and analysis
5. **Optimization incentives** - Metrics drive continuous improvement
6. **Scalability** - Can run more workflows within same budget

### Trade-offs

1. **Complexity** - Token tracking adds system overhead
2. **Risk of under-context** - Aggressive optimization may miss needed context
3. **Budget tuning** - Requires experimentation to set right limits
4. **Caching invalidation** - Stale cached context could cause issues

### Risks & Mitigations

| Risk | Mitigation |
|------|------------|
| Too aggressive optimization | Start conservative, tune based on quality metrics |
| Budget too restrictive | Allow manual override with approval |
| Token counting accuracy | Use official API response counts, not estimates |
| Cache staleness | TTL-based expiration, invalidate on relevant changes |

## Alternatives Considered

### 1. No Token Management
- **Pros:** Simpler system
- **Cons:** Unpredictable costs, no optimization incentive
- **Why rejected:** Need cost control for production use

### 2. Simple Per-Request Limits
- **Pros:** Easy to implement
- **Cons:** No hierarchical control, no context optimization
- **Why rejected:** Need granular control and optimization

### 3. External Cost Management (AWS Budgets-style)
- **Pros:** Proven patterns
- **Cons:** Not token-aware, post-hoc only
- **Why rejected:** Need real-time, token-specific management

## Implementation Notes

### Token Counting Utilities

```python
def count_tokens(text: str, model: str = "claude-3") -> int:
    """Count tokens in text for given model."""
    # Use tiktoken or model-specific tokenizer
    encoding = tiktoken.encoding_for_model(model)
    return len(encoding.encode(text))

def estimate_request_tokens(request: LLMRequest) -> int:
    """Estimate tokens for a request before sending."""
    system_tokens = count_tokens(request.system_prompt)
    message_tokens = sum(count_tokens(m.content) for m in request.messages)
    return system_tokens + message_tokens
```

### Budget CLI

```bash
# View current usage
orchestrator budget status --workflow proj-123

# Set workflow budget
orchestrator budget set --workflow proj-123 --max-tokens 1000000

# View cost report
orchestrator budget report --workflow proj-123 --format json

# Alert configuration
orchestrator budget alert --threshold 0.8 --slack-webhook $WEBHOOK
```

### Metrics Dashboard

Key metrics to display:
- Real-time token consumption (workflow/phase/agent)
- Cost accumulation over time
- Context efficiency ratio
- Budget utilization percentage
- Optimization savings

## Related Decisions

- ADR-001: Agent Architecture (agents receive budget constraints)
- ADR-002: Phase Model (budgets per phase)
- ADR-003: Skills and Tools (tool calls tracked for cost)
- ADR-004: Governance (budget enforcement as quality gate)
