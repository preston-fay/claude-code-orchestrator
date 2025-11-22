"""
Provider registry for Orchestrator v2.

Manages available LLM providers and routes requests to the appropriate one.

See docs/LLM_PROVIDERS.md for provider configuration.
"""

import logging
import os
from typing import TYPE_CHECKING

from orchestrator_v2.llm.providers.anthropic_provider import AnthropicLlmProvider
from orchestrator_v2.llm.providers.base import LlmProvider, LlmProviderError, LlmResult
from orchestrator_v2.llm.providers.bedrock_provider import BedrockLlmProvider

if TYPE_CHECKING:
    from orchestrator_v2.engine.state_models import AgentContext

logger = logging.getLogger(__name__)

# Model configuration with tiers and pricing
MODEL_CONFIG = {
    "anthropic": {
        "default_model": "claude-sonnet-4-5-20250929",
        "aliases": {
            "sonnet-latest": "claude-sonnet-4-5-20250929",
            "haiku-fallback": "claude-haiku-4-5-20251015",
        },
        "models": {
            "claude-sonnet-4-5-20250929": {
                "tier": "premium",
                "display_name": "Claude Sonnet 4.5",
                "input_cost_per_1k": 0.003,
                "output_cost_per_1k": 0.015,
            },
            "claude-haiku-4-5-20251015": {
                "tier": "cost-efficient",
                "display_name": "Claude Haiku 4.5",
                "input_cost_per_1k": 0.001,
                "output_cost_per_1k": 0.005,
            },
            # Deprecated models - map to new versions
            "claude-sonnet-4-5": {
                "tier": "deprecated",
                "maps_to": "claude-sonnet-4-5-20250929",
            },
            "claude-haiku-4-5": {
                "tier": "deprecated",
                "maps_to": "claude-haiku-4-5-20251015",
            },
            "claude-sonnet-4": {
                "tier": "deprecated",
                "maps_to": "claude-sonnet-4-5-20250929",
            },
            "claude-3-5-sonnet-20241022": {
                "tier": "deprecated",
                "maps_to": "claude-sonnet-4-5-20250929",
            },
        },
    },
    "bedrock": {
        "default_model": "claude-sonnet-4-5-20250929",
        "aliases": {
            "sonnet-latest": "claude-sonnet-4-5-20250929",
            "haiku-fallback": "claude-haiku-4-5-20251015",
        },
        "models": {
            "claude-sonnet-4-5-20250929": {
                "tier": "premium",
                "display_name": "Claude Sonnet 4.5",
                "input_cost_per_1k": 0.003,
                "output_cost_per_1k": 0.015,
            },
            "claude-haiku-4-5-20251015": {
                "tier": "cost-efficient",
                "display_name": "Claude Haiku 4.5",
                "input_cost_per_1k": 0.001,
                "output_cost_per_1k": 0.005,
            },
        },
    },
}


def resolve_model_alias(provider: str, model: str) -> str:
    """Resolve model alias to actual model ID.

    Args:
        provider: Provider name.
        model: Model name or alias.

    Returns:
        Resolved model ID.
    """
    if provider not in MODEL_CONFIG:
        return model

    config = MODEL_CONFIG[provider]

    # Check if it's an alias
    if model in config.get("aliases", {}):
        resolved = config["aliases"][model]
        logger.info(f"Resolved alias '{model}' to '{resolved}'")
        return resolved

    # Check if it's a deprecated model
    models = config.get("models", {})
    if model in models and models[model].get("tier") == "deprecated":
        new_model = models[model].get("maps_to", config["default_model"])
        logger.warning(
            f"Model '{model}' is deprecated. Mapping to '{new_model}'. "
            "Please update your configuration."
        )
        return new_model

    return model


def get_model_tier(provider: str, model: str) -> str:
    """Get the tier for a model.

    Args:
        provider: Provider name.
        model: Model name.

    Returns:
        Model tier (premium, fallback, deprecated).
    """
    if provider not in MODEL_CONFIG:
        return "unknown"

    models = MODEL_CONFIG[provider].get("models", {})
    if model in models:
        return models[model].get("tier", "unknown")

    return "unknown"


def get_default_model(provider: str) -> str:
    """Get default model for a provider.

    Args:
        provider: Provider name.

    Returns:
        Default model ID.
    """
    if provider in MODEL_CONFIG:
        return MODEL_CONFIG[provider]["default_model"]
    return "claude-sonnet-4-5-20250929"  # Global default


class ProviderRegistry:
    """Registry for LLM providers.

    Manages provider instances and routes generate() calls
    to the appropriate provider based on context.

    Provider selection precedence:
    1. AgentContext.llm_provider (user/project setting)
    2. ORCHESTRATOR_DEFAULT_LLM_PROVIDER environment variable
    3. Default: "anthropic"
    """

    def __init__(self):
        """Initialize the provider registry with available providers."""
        self._providers: dict[str, LlmProvider] = {}
        self._default_provider = os.environ.get(
            "ORCHESTRATOR_DEFAULT_LLM_PROVIDER", "anthropic"
        )

        # Register built-in providers
        self._register_builtin_providers()

    def _register_builtin_providers(self) -> None:
        """Register the built-in LLM providers."""
        # Anthropic API provider (requires BYOK)
        self._providers["anthropic"] = AnthropicLlmProvider()

        # AWS Bedrock provider (uses IAM credentials)
        bedrock_region = os.environ.get("AWS_DEFAULT_REGION", "us-east-1")
        self._providers["bedrock"] = BedrockLlmProvider(region=bedrock_region)

        logger.info(
            f"Registered {len(self._providers)} LLM providers: "
            f"{list(self._providers.keys())}"
        )

    def register(self, name: str, provider: LlmProvider) -> None:
        """Register a custom LLM provider.

        Args:
            name: Provider name (e.g., "openai", "azure").
            provider: Provider instance implementing LlmProvider protocol.
        """
        self._providers[name] = provider
        logger.info(f"Registered custom LLM provider: {name}")

    def get(self, name: str) -> LlmProvider:
        """Get a provider by name.

        Args:
            name: Provider name.

        Returns:
            Provider instance.

        Raises:
            ValueError: If provider is not registered.
        """
        if name not in self._providers:
            available = list(self._providers.keys())
            raise ValueError(
                f"Unknown LLM provider: '{name}'. "
                f"Available providers: {available}"
            )
        return self._providers[name]

    def get_for_context(self, context: "AgentContext") -> LlmProvider:
        """Get the appropriate provider for an agent context.

        Args:
            context: Agent context with provider preference.

        Returns:
            Provider instance.
        """
        provider_name = context.llm_provider or self._default_provider
        return self.get(provider_name)

    async def generate(
        self,
        prompt: str,
        model: str,
        context: "AgentContext",
    ) -> LlmResult:
        """Generate a response using the appropriate provider.

        This is a convenience method that selects the provider
        based on context and delegates to it.

        Args:
            prompt: The formatted prompt.
            model: Model identifier or alias.
            context: Agent context with provider and credentials.

        Returns:
            LlmResult with generated text and token usage.
        """
        provider = self.get_for_context(context)
        provider_name = context.llm_provider or self._default_provider

        # Resolve model alias and get default if not specified
        if not model:
            model = get_default_model(provider_name)
        else:
            model = resolve_model_alias(provider_name, model)

        # Get model tier for logging
        tier = get_model_tier(provider_name, model)

        logger.info(
            f"Generating with provider={provider_name}, model={model}, "
            f"tier={tier}, user={context.user_id}"
        )

        try:
            result = await provider.generate(prompt, model, context)
            return result
        except LlmProviderError:
            # Re-raise provider errors as-is
            raise
        except Exception as e:
            # Wrap unexpected errors
            raise LlmProviderError(
                f"Unexpected error: {e}",
                provider=provider_name,
                model=model,
            ) from e

    @property
    def available_providers(self) -> list[str]:
        """Get list of available provider names."""
        return list(self._providers.keys())

    @property
    def default_provider(self) -> str:
        """Get the default provider name."""
        return self._default_provider


# Global singleton instance
_registry: ProviderRegistry | None = None


def get_provider_registry() -> ProviderRegistry:
    """Get the global provider registry instance.

    Returns:
        Singleton ProviderRegistry instance.
    """
    global _registry
    if _registry is None:
        _registry = ProviderRegistry()
    return _registry


def reset_provider_registry() -> None:
    """Reset the global provider registry.

    Useful for testing.
    """
    global _registry
    _registry = None
