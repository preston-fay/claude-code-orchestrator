"""
LLM Provider module for Orchestrator v2.

Provides unified interface to LLM providers (Anthropic, Bedrock, etc.)
with support for BYOK (Bring Your Own Key) and retry logic.
"""

from orchestrator_v2.llm.provider_registry import (
    ProviderRegistry,
    get_provider_registry,
    resolve_model_alias,
)
from orchestrator_v2.llm.providers.base import (
    LlmResult,
    LlmProvider,
    LlmProviderError,
    LlmAuthenticationError,
    LlmRateLimitError,
    LlmModelNotFoundError,
)
from orchestrator_v2.llm.retry import (
    LLMRetryError,
    RetryConfig,
    DEFAULT_RETRY_CONFIG,
    retry_async,
    with_retry,
    LLMCallContext,
    is_retryable_error,
)

__all__ = [
    # Provider registry
    "ProviderRegistry",
    "get_provider_registry",
    "resolve_model_alias",
    
    # LLM types
    "LlmResult",
    "LlmProvider",
    
    # Exceptions
    "LlmProviderError",
    "LlmAuthenticationError",
    "LlmRateLimitError",
    "LlmModelNotFoundError",
    
    # Retry utilities
    "LLMRetryError",
    "RetryConfig",
    "DEFAULT_RETRY_CONFIG",
    "retry_async",
    "with_retry",
    "LLMCallContext",
    "is_retryable_error",
]
