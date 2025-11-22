# LLM Provider Subsystem

The Claude Code Orchestrator supports multiple LLM providers through a pluggable provider architecture. This allows users to use their preferred provider (Anthropic API, AWS Bedrock) without changing agent code.

## Overview

The provider subsystem provides:
- **Unified interface** - All providers implement the same `LlmProvider` protocol
- **BYOK support** - Users can bring their own API keys for Anthropic
- **AWS Bedrock** - Use Claude via AWS IAM credentials
- **Dynamic selection** - Provider/model chosen per user, per agent, per task
- **Token tracking** - All calls track input/output tokens for budgeting

## Architecture

```
┌─────────────┐     ┌──────────────────┐     ┌───────────────────┐
│   Agent     │ ──> │ ProviderRegistry │ ──> │ AnthropicProvider │
│ (base_agent)│     └──────────────────┘     └───────────────────┘
└─────────────┘              │               ┌───────────────────┐
                             └────────────── │ BedrockProvider   │
                                             └───────────────────┘
```

## Supported Providers

### Anthropic API (BYOK)

Uses the official Anthropic Python SDK with user-supplied API keys.

**Requirements:**
- `anthropic` package (`pip install anthropic`)
- User API key stored in `UserProfile.anthropic_api_key`

**Supported Models:**
- `claude-sonnet-4-5-20250929` (Default) - Premium tier
- `claude-haiku-4-5-20251015` (Fallback) - Cost-efficient tier

**Model Aliases:**
- `sonnet-latest` → `claude-sonnet-4-5-20250929`
- `haiku-fallback` → `claude-haiku-4-5-20251015`

**Deprecated Models (auto-mapped):**
- `claude-sonnet-4-5` → `claude-sonnet-4-5-20250929`
- `claude-haiku-4-5` → `claude-haiku-4-5-20251015`
- `claude-3-5-sonnet-20241022` → `claude-sonnet-4-5-20250929`
- `claude-sonnet-4` → `claude-sonnet-4-5-20250929`

**Configuration:**
```yaml
# In user profile
default_provider: anthropic
anthropic_api_key: sk-ant-...
default_model: claude-sonnet-4-5-20250929
```

### AWS Bedrock

Uses `boto3` to call Claude models via AWS Bedrock. No API key required - uses AWS IAM credentials.

**Requirements:**
- `boto3` package (`pip install boto3`)
- AWS credentials configured (environment variables, IAM role, or AWS CLI)

**Supported Models:**
- `claude-sonnet-4-5-20250929` (Default) - Premium tier
- `claude-haiku-4-5-20251015` (Fallback) - Cost-efficient tier

**Model Aliases:**
- `sonnet-latest` → `claude-sonnet-4-5-20250929`
- `haiku-fallback` → `claude-haiku-4-5-20251015`

**Configuration:**
```bash
# Environment variables
export AWS_ACCESS_KEY_ID=...
export AWS_SECRET_ACCESS_KEY=...
export AWS_DEFAULT_REGION=us-east-1

# Or use IAM role (recommended for production)
```

```yaml
# In user profile
default_provider: bedrock
default_model: claude-sonnet-4-5-20250929
# No API key needed - uses AWS IAM
```

## Provider Selection

Provider selection follows this precedence:

1. **AgentContext.llm_provider** - Set by user profile or project settings
2. **ORCHESTRATOR_DEFAULT_LLM_PROVIDER** - Environment variable
3. **Default** - `anthropic`

### User Profile Settings

```yaml
# User profile with Anthropic
user_id: "dev-user"
default_provider: "anthropic"
anthropic_api_key: "sk-ant-..."

# User profile with Bedrock
user_id: "prod-user"
default_provider: "bedrock"
# No API key - uses AWS IAM
```

### Environment Override

```bash
# Force all users to use Bedrock
export ORCHESTRATOR_DEFAULT_LLM_PROVIDER=bedrock
```

## Model Selection

Model selection is handled by the `model_selection` module:

1. **Project override** - Project metadata can specify a model
2. **User entitlements** - User's allowed models from their profile
3. **User default** - User's preferred model
4. **Global default** - System default model

```python
from orchestrator_v2.core.model_selection import select_model_for_agent

# Returns ModelConfig with provider and model
model_config = select_model_for_agent(
    user=user_profile,
    agent_role="architect",
    project_metadata=project.metadata,
)
```

## Model Configuration

We recommend starting with **Claude Sonnet 4.5** (alias `sonnet-latest`). For cost-efficient mode, choose **Claude Haiku 4.5** (alias `haiku-fallback`).

### Current Models

| Model ID | Provider | Tier | Input Cost (per 1K) | Output Cost (per 1K) |
|----------|----------|------|---------------------|----------------------|
| `claude-sonnet-4-5-20250929` | Anthropic/Bedrock | Premium | $0.003 | $0.015 |
| `claude-haiku-4-5-20251015` | Anthropic/Bedrock | Cost-efficient | $0.001 | $0.005 |

### Model Aliases

Aliases allow using friendly names that resolve to specific model versions:

| Alias | Resolves To | Description |
|-------|-------------|-------------|
| `sonnet-latest` | `claude-sonnet-4-5-20250929` | Latest Sonnet model (recommended) |
| `haiku-fallback` | `claude-haiku-4-5-20251015` | Cost-efficient fallback |

### Model Tiers

- **Premium**: Full-featured models for complex tasks (Claude Sonnet 4.5)
- **Cost-efficient**: Faster, cheaper models for simpler tasks (Claude Haiku 4.5)
- **Deprecated**: Old models that auto-map to current versions

**Note:** For production deployments, use the full version-specific IDs (e.g., `claude-sonnet-4-5-20250929`) to ensure consistent behavior.

## Usage in Agents

Agents use the `_call_llm` method from `BaseAgent`:

```python
class MyAgent(BaseAgent):
    async def act(self, plan, project_state):
        # Build prompt
        prompt = f"Analyze the following requirements:\n{requirements}"

        # Call LLM using configured provider
        result = await self._call_llm(prompt, context)

        # Use the result
        analysis = result.text

        # Token usage is automatically tracked
        return AgentOutput(output=analysis)
```

## Token Tracking

All LLM calls automatically track:
- Input tokens
- Output tokens
- Provider used
- Model used
- Cost (calculated from model-specific pricing)

This feeds into the budget enforcement system:

```python
# Token usage is recorded per call
self._token_tracker.track_llm_call(
    workflow_id=project_id,
    phase=phase,
    agent_id=agent_id,
    input_tokens=result.input_tokens,
    output_tokens=result.output_tokens,
    model_name="claude-sonnet-4-5-20250929",
    provider="anthropic",
)
```

Cost calculation uses model-specific pricing:
- Claude Sonnet 4.5: $0.003/1K input, $0.015/1K output (premium tier)
- Claude Haiku 4.5: $0.001/1K input, $0.005/1K output (cost-efficient tier)

Token reports differentiate model tier usage, showing "Model in use: Claude Sonnet 4.5" or "Model in use: Claude Haiku 4.5".

## Error Handling

The provider system defines specific exceptions:

```python
from orchestrator_v2.llm import (
    LlmProviderError,      # Base exception
    LlmAuthenticationError, # Invalid/missing credentials
    LlmRateLimitError,      # Rate limits exceeded
    LlmModelNotFoundError,  # Model not available
)
```

### Authentication Errors

**Anthropic:**
```python
# Missing API key
LlmAuthenticationError: No Anthropic API key provided.

# Invalid API key
LlmAuthenticationError: Invalid API key: Authentication failed.
```

**Bedrock:**
```python
# Missing AWS credentials
LlmAuthenticationError: AWS credentials not configured.

# Access denied
LlmAuthenticationError: Access denied: User not authorized for model.
```

## Adding New Providers

To add a new provider (e.g., OpenAI, Azure):

1. **Create provider class** implementing `LlmProvider` protocol:

```python
# orchestrator_v2/llm/providers/openai_provider.py
from orchestrator_v2.llm.providers.base import LlmProvider, LlmResult

class OpenAILlmProvider:
    async def generate(
        self,
        prompt: str,
        model: str,
        context: AgentContext,
    ) -> LlmResult:
        # Implementation
        ...
```

2. **Register in provider_registry.py**:

```python
def _register_builtin_providers(self) -> None:
    self._providers["anthropic"] = AnthropicLlmProvider()
    self._providers["bedrock"] = BedrockLlmProvider()
    self._providers["openai"] = OpenAILlmProvider()  # New
```

3. **Add model mapping** (if needed):

```python
OPENAI_MODEL_MAP = {
    "gpt-4": "gpt-4-turbo-preview",
    ...
}
```

4. **Update user model** to include credentials:

```python
class UserProfile(BaseModel):
    openai_api_key: str | None = None
```

## Configuration Reference

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `ORCHESTRATOR_DEFAULT_LLM_PROVIDER` | Default provider name | `anthropic` |
| `AWS_DEFAULT_REGION` | AWS region for Bedrock | `us-east-1` |
| `AWS_ACCESS_KEY_ID` | AWS access key | (from AWS config) |
| `AWS_SECRET_ACCESS_KEY` | AWS secret key | (from AWS config) |

### AgentContext Fields

| Field | Description |
|-------|-------------|
| `user_id` | User identifier |
| `llm_api_key` | API key for Anthropic |
| `llm_provider` | Provider name (`anthropic`, `bedrock`) |
| `provider` | Selected provider for this execution |
| `model` | Selected model for this execution |

## Switching Providers

To switch a project from Anthropic to Bedrock:

1. **Update user profiles** to use `default_provider: bedrock`
2. **Configure AWS credentials** for the execution environment
3. **No code changes required** - agents automatically use the new provider

This enables seamless migration from personal API keys (development) to enterprise Bedrock (production).

## Security Considerations

- **API keys** should be stored securely (never in version control)
- **AWS credentials** should use IAM roles in production
- **User profiles** should use encrypted storage for sensitive data
- **Audit logging** tracks all LLM calls for compliance

## Troubleshooting

### "No Anthropic API key provided"

User profile is missing `anthropic_api_key`. Set it:

```python
user = user_repository.get_user(user_id)
user.anthropic_api_key = "sk-ant-..."
user_repository.save_user(user)
```

### "AWS credentials not configured"

Bedrock provider cannot find AWS credentials. Configure:

```bash
# Option 1: Environment variables
export AWS_ACCESS_KEY_ID=...
export AWS_SECRET_ACCESS_KEY=...

# Option 2: AWS CLI
aws configure

# Option 3: IAM role (on EC2/ECS)
# Automatically uses instance role
```

### "Model not found"

The requested model is not available in the provider. Check:
- Model name spelling
- Model availability in your region (Bedrock)
- Model access permissions (Bedrock requires model access to be enabled)
