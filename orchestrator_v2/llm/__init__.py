"""
LLM provider subsystem for Orchestrator v2.

This module provides a pluggable LLM backend system supporting
multiple providers (Anthropic API, AWS Bedrock, etc.).

Usage:
    from orchestrator_v2.llm import get_provider_registry

    registry = get_provider_registry()
    result = await registry.generate(prompt, model, context)

See docs/LLM_PROVIDERS.md for architecture details.
"""

from orchestrator_v2.llm.provider_registry import (
    ProviderRegistry,
    get_provider_registry,
    reset_provider_registry,
)
from orchestrator_v2.llm.providers.base import (
    LlmAuthenticationError,
    LlmModelNotFoundError,
    LlmProvider,
    LlmProviderError,
    LlmRateLimitError,
    LlmResult,
)

__all__ = [
    # Registry
    "ProviderRegistry",
    "get_provider_registry",
    "reset_provider_registry",
    # Base types
    "LlmProvider",
    "LlmResult",
    # Exceptions
    "LlmProviderError",
    "LlmAuthenticationError",
    "LlmRateLimitError",
    "LlmModelNotFoundError",
]
