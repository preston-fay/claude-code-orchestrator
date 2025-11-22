# LLM

Multi-provider LLM integration for Orchestrator v2.

## Purpose

This module provides a pluggable LLM provider architecture supporting:
- Anthropic API (BYOK - Bring Your Own Key)
- AWS Bedrock (IAM credentials)

## Architecture

```
LlmProvider (Protocol)
├── AnthropicProvider - Direct API calls with user's API key
└── BedrockProvider - AWS Bedrock with IAM credentials
```

## Key Components

- **provider_registry.py**: Central registry for provider selection
- **providers/base.py**: `LlmProvider` protocol and `LlmResult` model
- **providers/anthropic_provider.py**: Anthropic API implementation
- **providers/bedrock_provider.py**: AWS Bedrock implementation
- **providers/model_mapping.py**: Model name to provider ID mapping

## Usage

```python
from orchestrator_v2.llm import get_provider_registry

registry = get_provider_registry()
result = await registry.generate(
    prompt="Your prompt here",
    model="claude-3-5-sonnet-20241022",
    context=agent_context
)

print(result.text)
print(f"Tokens: {result.input_tokens} in, {result.output_tokens} out")
```

## Configuration

Set user's LLM provider via the API:
- `POST /users/me/provider-settings`
- Test connection: `POST /users/me/provider-test`

## Related Documentation

- docs/LLM_PROVIDERS.md: Complete provider documentation
- docs/USER_AUTHENTICATION.md: BYOK setup
