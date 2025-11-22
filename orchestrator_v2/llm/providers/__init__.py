"""
LLM provider implementations for Orchestrator v2.

Available providers:
- AnthropicLlmProvider: Uses Anthropic API with BYOK
- BedrockLlmProvider: Uses AWS Bedrock with IAM credentials

See docs/LLM_PROVIDERS.md for provider details.
"""

from orchestrator_v2.llm.providers.anthropic_provider import AnthropicLlmProvider
from orchestrator_v2.llm.providers.base import (
    LlmAuthenticationError,
    LlmModelNotFoundError,
    LlmProvider,
    LlmProviderError,
    LlmRateLimitError,
    LlmResult,
)
from orchestrator_v2.llm.providers.bedrock_provider import BedrockLlmProvider
from orchestrator_v2.llm.providers.model_mapping import (
    map_model_to_anthropic,
    map_model_to_bedrock,
)

__all__ = [
    # Providers
    "AnthropicLlmProvider",
    "BedrockLlmProvider",
    # Base types
    "LlmProvider",
    "LlmResult",
    # Exceptions
    "LlmProviderError",
    "LlmAuthenticationError",
    "LlmRateLimitError",
    "LlmModelNotFoundError",
    # Mapping
    "map_model_to_bedrock",
    "map_model_to_anthropic",
]
