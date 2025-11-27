# Migration Guide: V1 to V2

This guide helps you migrate from the deprecated `src/orchestrator` (V1) to the new `orchestrator_v2`.

## Why Migrate?

| Feature | V1 | V2 |
|---------|----|----|  
| Real LLM Calls | ❌ Simulated | ✅ Calls Claude API |
| Agent Architecture | Monolithic | 8 Specialized Agents |
| Async Support | ❌ | ✅ Full async/await |
| API Server | CLI only | FastAPI REST API |
| Token Budgets | ❌ | ✅ Per-agent limits |
| Retry Logic | ❌ | ✅ Exponential backoff |

## Quick Migration

### Before (V1)
```python
from src.orchestrator import cli
from src.orchestrator.runloop import RunLoop
```

### After (V2)
```python
from orchestrator_v2.engine.engine import WorkflowEngine
from orchestrator_v2.agents import create_agent
```

## Running the API Server

### V1 (Deprecated)
```bash
python -m orchestrator  # CLI only, no real LLM
```

### V2 (Recommended)
```bash
# Set your API key
export ANTHROPIC_API_KEY=sk-ant-...

# Start server
uvicorn orchestrator_v2.api.server:app --reload

# Or use the script
python scripts/run_api_server.py
```

## Key API Endpoints (V2)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check |
| `/projects` | GET | List all projects |
| `/projects` | POST | Create new project |
| `/projects/{id}` | GET | Get project details |
| `/rsg/{id}/ready/start` | POST | Start Ready stage |
| `/rsg/{id}/set/start` | POST | Start Set stage |
| `/rsg/{id}/go/start` | POST | Start Go stage |
| `/users/me/provider-settings` | POST | Set your API key |

## Setting Your API Key

```bash
curl -X POST http://localhost:8000/users/me/provider-settings \
  -H "Content-Type: application/json" \
  -d '{"llm_provider": "anthropic", "api_key": "sk-ant-..."}'
```

## Agent Mapping

| V1 Concept | V2 Agent |
|------------|----------|
| Planning phase | `ArchitectAgent` |
| Implementation | `DeveloperAgent` |
| Testing | `QAAgent` |
| Documentation | `DocumentarianAgent` |
| Review | `ConsensusAgent`, `ReviewerAgent` |
| Data work | `DataAgent` |
| Compliance | `StewardAgent` |

## Need Help?

See `docs/LLM_INTEGRATION.md` for full LLM setup instructions.
