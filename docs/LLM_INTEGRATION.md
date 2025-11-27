# LLM Integration Guide

This document explains how to set up and use real LLM (Claude) calls in the Orchestrator v2.

## Overview

Orchestrator v2 supports two modes:

1. **Simulated Mode** (default, no API key needed)
   - Agents generate template-based artifacts
   - Useful for development and testing
   - No API costs

2. **Real LLM Mode** (requires Anthropic API key)
   - Agents call Claude API for intelligent responses
   - Generates context-aware artifacts
   - Uses claude-sonnet-4-5-20250929 by default

## Setup

### 1. Get an API Key

Get your Anthropic API key from: https://console.anthropic.com/settings/keys

### 2. Set Environment Variable

```bash
export ANTHROPIC_API_KEY=sk-ant-api03-your-key-here
```

Or create a `.env` file:

```bash
cp .env.example .env
# Edit .env and add your API key
```

### 3. Test the Integration

```bash
# Quick test
python scripts/run_workflow_test.py --real-llm

# Run integration tests
pytest tests/integration/test_end_to_end_workflow.py -v
```

## Architecture

### Data Flow

```
User Request
     │
     ▼
┌─────────────────┐
│   API Server    │ ◄── Sets LLM credentials from user profile
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ WorkflowEngine  │ ◄── Creates AgentContext with LLM creds
└────────┬────────┘
         │
         ├──► _get_or_create_agent() ──► Agent Factory
         │
         └──► _build_agent_context() 
                    │
                    ▼
         ┌──────────────────┐
         │  AgentContext    │
         │  - llm_api_key   │
         │  - llm_provider  │
         │  - model         │
         └────────┬─────────┘
                  │
                  ▼
         ┌──────────────────┐
         │  Agent.plan()   │ ◄── Receives context
         │  Agent.act()    │ ◄── Receives context
         └────────┬─────────┘
                  │
                  ▼ (if context has API key)
         ┌──────────────────┐
         │  LlmAgentMixin   │
         │  _llm_plan()     │
         │  _llm_act()      │
         └────────┬─────────┘
                  │
                  ▼
         ┌──────────────────┐
         │ PromptBuilder    │ ◄── Loads templates from subagent_prompts/
         │ ResponseParser   │
         └────────┬─────────┘
                  │
                  ▼
         ┌──────────────────┐
         │ Claude API       │ ◄── Real LLM call
         └──────────────────┘
```

### Key Components

| Component | File | Purpose |
|-----------|------|--------|
| AgentContext | `engine/state_models.py` | Carries LLM credentials through the system |
| LlmAgentMixin | `agents/llm_agent_mixin.py` | Provides `_llm_plan()` and `_llm_act()` methods |
| PromptBuilder | `agents/prompt_builder.py` | Loads and builds prompts from templates |
| ResponseParser | `agents/response_parser.py` | Parses LLM responses into structured data |
| Agent Factory | `agents/factory.py` | Creates agent instances dynamically |
| Retry Logic | `llm/retry.py` | Handles rate limits and transient errors |

## Usage

### Programmatic Usage

```python
from orchestrator_v2.engine.engine import WorkflowEngine
from orchestrator_v2.engine.state_models import AgentContext, TaskDefinition
from orchestrator_v2.agents import create_agent

# Create agent
agent = create_agent("architect")

# Create context with LLM credentials
context = AgentContext(
    project_state=project_state,
    task=task,
    user_id="user-001",
    llm_api_key="sk-ant-api03-...",
    llm_provider="anthropic",
    model="claude-sonnet-4-5-20250929",
)

# Initialize and run agent
agent.initialize(project_state, context)
plan = agent.plan(task, phase, project_state, context)  # Real LLM call!
output = agent.act(plan, project_state, context)  # Real LLM call!
```

### Via API Server

```bash
# Start server
python scripts/run_api_server.py

# Set your API key in user profile
curl -X POST http://localhost:8000/users/me/provider-settings \
  -H "Content-Type: application/json" \
  -d '{"llm_provider": "anthropic", "api_key": "sk-ant-api03-..."}'

# Create and run project
curl -X POST http://localhost:8000/projects \
  -H "Content-Type: application/json" \
  -d '{"project_name": "My Project"}'
```

## Retry Logic

The system includes automatic retry for transient LLM failures:

- **Rate limits (429)**: Retried with exponential backoff
- **Server errors (500, 502, 503, 504)**: Retried
- **Timeouts**: Retried
- **Max attempts**: 3 (configurable)
- **Backoff**: 2s, 4s, 8s (with jitter)

```python
from orchestrator_v2.llm import RetryConfig, retry_async

# Custom retry config
config = RetryConfig(
    max_attempts=5,
    initial_delay=1.0,
    max_delay=30.0,
    exponential_base=2.0,
    jitter=True,
)

result = await retry_async(my_llm_function, config=config)
```

## Supported Agents

| Agent | ID | Description |
|-------|-----|-------------|
| Architect | `architect` | System design and architecture |
| Developer | `developer` | Code implementation |
| QA | `qa` | Testing and quality assurance |
| Documentarian | `documentarian` | Documentation generation |
| Consensus | `consensus` | Decision review and approval |
| Steward | `steward` | Code hygiene and compliance |
| Reviewer | `reviewer` | Code review and quality scoring |
| Data | `data` | Data pipeline and ML |

## Cost Estimation

Approximate costs per agent execution (claude-sonnet-4-5):

| Agent | Input Tokens | Output Tokens | Est. Cost |
|-------|--------------|---------------|-----------|
| Architect | ~2,000 | ~1,500 | $0.02-0.05 |
| Developer | ~3,000 | ~2,000 | $0.03-0.08 |
| QA | ~2,500 | ~1,500 | $0.02-0.06 |
| Documentarian | ~2,000 | ~2,000 | $0.02-0.06 |

Full project workflow: ~$0.10-0.50 depending on complexity.

## Troubleshooting

### API Key Not Working

1. Verify key format: `sk-ant-api03-...`
2. Check key is active at console.anthropic.com
3. Ensure sufficient credits

### Rate Limits

The retry logic handles rate limits automatically. If you see persistent 429 errors:

1. Wait a few minutes
2. Reduce concurrent agent execution
3. Use a higher-tier API plan

### Network Errors

Ensure your network allows connections to:
- `api.anthropic.com` (port 443)

### Simulated Mode Fallback

If no API key is provided, agents automatically fall back to simulated mode with template-based responses. This is intentional for:
- Development without API costs
- CI/CD testing
- Offline development
