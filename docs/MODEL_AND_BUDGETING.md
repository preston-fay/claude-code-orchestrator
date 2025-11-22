# Model Selection & Token Budget Enforcement

This guide explains how the orchestrator selects LLM models and enforces token budgets for multi-user BYOK deployments.

---

## Overview

The orchestrator provides:

- **Parallel Agent Execution**: Run multiple agents concurrently within phases
- **Model Selection**: Choose models based on user entitlements
- **Token Budgets**: Enforce per-user and per-project token limits
- **Usage Tracking**: Track consumption for billing and limits

---

## Parallel Agent Execution

### How It Works

When a phase has multiple responsible agents (e.g., Developer + Steward), they execute in parallel using `asyncio.gather()`:

```python
# In WorkflowEngine._run_agents_for_phase()
tasks = []
for agent_id in phase_def.responsible_agents:
    tasks.append(self._execute_agent_with_budget(agent_id, phase, user))

results = await asyncio.gather(*tasks, return_exceptions=True)
```

### Benefits

- **Faster execution**: Agents don't wait for each other
- **Better resource utilization**: Multiple LLM calls run concurrently
- **Independent failures**: One agent failure doesn't block others

### Example Log Output

```
INFO - Running phase development with 2 agents: ['developer', 'steward']
INFO - Starting parallel execution of 2 agents
INFO - Selected model for developer: anthropic:claude-sonnet-4-20250514
INFO - Selected model for steward: anthropic:claude-3-5-haiku-20241022
INFO - Agent developer completed: model=claude-sonnet-4-20250514, tokens=700
INFO - Agent steward completed: model=claude-3-5-haiku-20241022, tokens=700
INFO - Parallel execution complete: 2 agents succeeded
```

---

## Model Selection

### Selection Precedence

Models are selected in this order:

1. **Project override**: `project.metadata.model_overrides[agent_role]`
2. **User entitlements**: `user.model_entitlements[agent_role][0]`
3. **User default**: `user.default_model`
4. **Global default**: `DEFAULT_ROLE_MODELS[agent_role]`

### Global Defaults

```python
DEFAULT_ROLE_MODELS = {
    "architect": "claude-sonnet-4-20250514",
    "developer": "claude-sonnet-4-20250514",
    "data": "claude-sonnet-4-20250514",
    "qa": "claude-3-5-haiku-20241022",
    "documentarian": "claude-3-5-haiku-20241022",
    "consensus": "claude-sonnet-4-20250514",
    "reviewer": "claude-sonnet-4-20250514",
    "steward": "claude-3-5-haiku-20241022",
}
```

### Configuring User Entitlements

Set via API:

```bash
curl -X POST http://localhost:8000/users/{user_id}/entitlements \
  -H "X-User-Id: admin" \
  -H "X-User-Email: admin@example.com" \
  -H "Content-Type: application/json" \
  -d '{
    "architect": ["claude-3-opus-20240229", "claude-sonnet-4-20250514"],
    "developer": ["claude-sonnet-4-20250514"],
    "qa": ["claude-3-5-haiku-20241022"]
  }'
```

The first model in each list is used by default.

### How Model Config is Injected

The `AgentContext` receives model information:

```python
context.provider = "anthropic"
context.model = "claude-sonnet-4-20250514"
context.llm_api_key = user.llm_api_key
```

Agents use these values when making LLM API calls.

---

## Token Budget Enforcement

### Budget Types

Users can have multiple budget limits:

| Type | Description | Example |
|------|-------------|---------|
| `daily` | Tokens per 24 hours | 100,000 |
| `project` | Tokens per project | 50,000 |
| `total` | Lifetime total | 1,000,000 |

### Setting Budgets

In the user profile:

```python
user.token_limits = {
    "daily": 100000,
    "project": 50000,
    "total": 1000000,
}
```

### How Enforcement Works

Before each agent execution:

1. **Estimate tokens** based on agent role
2. **Check budget** against all applicable limits
3. **Block if exceeded** with `BudgetExceededError`
4. **Execute if passed**
5. **Record actual usage** after completion

### Budget Check Flow

```python
# In WorkflowEngine._execute_agent_with_budget()
estimated_tokens = estimate_tokens_for_agent(agent_id)

await self._budget_enforcer.check_and_reserve(
    user=user,
    project_id=project_id,
    estimated_tokens=estimated_tokens,
)
```

### Token Estimates

Default estimates by agent role:

| Agent | Estimated Tokens |
|-------|-----------------|
| architect | 8,000 |
| developer | 10,000 |
| data | 6,000 |
| qa | 5,000 |
| documentarian | 4,000 |
| consensus | 3,000 |
| reviewer | 4,000 |
| steward | 2,000 |

### BudgetExceededError

When budget is exceeded:

```python
raise BudgetExceededError(
    "Project token limit exceeded. Current: 45000, Requested: 10000, Limit: 50000",
    limit_type="project",
    current=45000,
    limit=50000,
    requested=10000,
)
```

This stops the phase execution with a governance-like error.

---

## Usage Tracking

### What's Tracked

For every LLM call:

- `user_id` - Who made the request
- `project_id` - Which project
- `agent_role` - Which agent
- `model` - Which model was used
- `input_tokens` - Tokens in prompt
- `output_tokens` - Tokens in response

### Recording Usage

```python
await budget_enforcer.record_usage(
    user=user,
    project_id="proj-123",
    agent_role="developer",
    model="claude-sonnet-4-20250514",
    input_tokens=3000,
    output_tokens=2000,
)
```

### Viewing Usage

User profile includes:

```json
{
  "token_usage": {
    "total_input_tokens": 50000,
    "total_output_tokens": 25000,
    "total_requests": 100,
    "last_reset": "2024-01-01T00:00:00Z"
  }
}
```

### Getting Remaining Budget

```python
remaining = await enforcer.get_remaining_budget(user, project_id)
# Returns: {"daily": 50000, "project": 5000, "total": 950000}
```

---

## Cost Tracking

### Model Costs

Approximate costs per 1K tokens (as of 2024):

| Model | Input | Output |
|-------|-------|--------|
| claude-sonnet-4-20250514 | $0.003 | $0.015 |
| claude-3-5-haiku-20241022 | $0.0008 | $0.004 |
| claude-3-opus-20240229 | $0.015 | $0.075 |

### Cost Calculation

```python
from orchestrator_v2.core.model_selection import get_model_cost_per_token

input_cost, output_cost = get_model_cost_per_token("claude-sonnet-4-20250514")
total_cost = (input_tokens * input_cost + output_tokens * output_cost) / 1000
```

---

## Testing

### Run the Test Script

```bash
python scripts/test_parallel_model_budget.py
```

### Expected Output

```
============================================================
  Parallel Execution, Model Selection & Budget Enforcement
============================================================

============================================================
  Test 1: Model Selection
============================================================
  ✓ Model for architect: claude-3-opus-20240229
  ✓ Model for developer: claude-sonnet-4-20250514
  ✓ Model for qa: claude-3-5-haiku-20241022
  ✓ Model for documentarian: claude-sonnet-4-20250514

============================================================
  Test 2: Budget Enforcement
============================================================
  ✓ Budget check (5000 tokens): PASSED
  ✓ Budget exceeded check: Correctly blocked: project

============================================================
  Test 3: Parallel Agent Execution
============================================================
  ✓ Parallel execution: Completed in 0.02s
  ✓   Agent: developer: model=claude-sonnet-4-20250514, tokens=700
  ✓   Agent: steward: model=claude-3-5-haiku-20241022, tokens=700

============================================================
  All tests PASSED
============================================================
```

---

## Best Practices

### 1. Set Conservative Budgets

Start with lower limits and increase as needed:

```python
token_limits = {
    "daily": 50000,   # Start low
    "project": 25000,  # Per project
}
```

### 2. Use Appropriate Models

- **Architect/Developer**: Use capable models (Sonnet, Opus)
- **QA/Docs**: Use cost-effective models (Haiku)
- **Steward**: Use fast, cheap models (Haiku)

### 3. Monitor Usage

Check remaining budgets before large operations:

```python
remaining = await enforcer.get_remaining_budget(user, project_id)
if remaining["project"] < 10000:
    logger.warning("Low budget remaining")
```

### 4. Handle Budget Errors Gracefully

```python
try:
    await engine.run_phase(phase, user)
except BudgetExceededError as e:
    # Inform user, suggest upgrading limits
    return {"error": "budget_exceeded", "detail": str(e)}
```

---

## Configuration Reference

### UserProfile Fields

| Field | Type | Description |
|-------|------|-------------|
| `llm_api_key` | str | BYOK API key |
| `llm_provider` | str | Provider (anthropic, openai) |
| `default_model` | str | Default model for unspecified roles |
| `model_entitlements` | dict | Allowed models per role |
| `token_limits` | dict | Budget limits by type |
| `token_usage` | TokenUsage | Current usage counters |

### AgentState Fields

| Field | Type | Description |
|-------|------|-------------|
| `model_used` | str | Model that was used |
| `provider_used` | str | Provider that was used |
| `token_usage` | TokenUsage | Tokens consumed |

### AgentContext Fields

| Field | Type | Description |
|-------|------|-------------|
| `provider` | str | Selected provider |
| `model` | str | Selected model |
| `llm_api_key` | str | User's API key |
| `model_preferences` | list | Allowed models for role |

---

## Related Documentation

- [USER_AUTHENTICATION.md](USER_AUTHENTICATION.md) - Authentication and BYOK setup
- [ORCHESTRATOR_QUICK_REFERENCE.md](../ORCHESTRATOR_QUICK_REFERENCE.md) - Quick reference
- [orchestrator-v2-architecture.md](orchestrator-v2-architecture.md) - Architecture overview
