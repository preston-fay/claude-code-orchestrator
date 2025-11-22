"""
Model mapping utilities for LLM providers.

Maps orchestrator model names to provider-specific model identifiers.

See docs/LLM_PROVIDERS.md for supported models.
"""

# Mapping from orchestrator model names to AWS Bedrock model IDs
BEDROCK_MODEL_MAP: dict[str, str] = {
    # Claude 3.5 models
    "claude-3-5-sonnet-20241022": "anthropic.claude-3-5-sonnet-20241022-v2:0",
    "claude-3-5-haiku-20241022": "anthropic.claude-3-5-haiku-20241022-v1:0",

    # Claude 3 models
    "claude-3-sonnet-20240229": "anthropic.claude-3-sonnet-20240229-v1:0",
    "claude-3-haiku-20240307": "anthropic.claude-3-haiku-20240307-v1:0",
    "claude-3-opus-20240229": "anthropic.claude-3-opus-20240229-v1:0",

    # Short aliases
    "claude-3-sonnet": "anthropic.claude-3-sonnet-20240229-v1:0",
    "claude-3-haiku": "anthropic.claude-3-haiku-20240307-v1:0",
    "claude-3-opus": "anthropic.claude-3-opus-20240229-v1:0",
    "claude-3-5-sonnet": "anthropic.claude-3-5-sonnet-20241022-v2:0",
    "claude-3-5-haiku": "anthropic.claude-3-5-haiku-20241022-v1:0",
}

# Mapping from orchestrator model names to Anthropic API model IDs
ANTHROPIC_MODEL_MAP: dict[str, str] = {
    # Short aliases map to full model names
    "claude-3-sonnet": "claude-3-sonnet-20240229",
    "claude-3-haiku": "claude-3-haiku-20240307",
    "claude-3-opus": "claude-3-opus-20240229",
    "claude-3-5-sonnet": "claude-3-5-sonnet-20241022",
    "claude-3-5-haiku": "claude-3-5-haiku-20241022",
}


def map_model_to_bedrock(model: str) -> str:
    """Map an orchestrator model name to a Bedrock model ID.

    Args:
        model: Orchestrator model name (e.g., "claude-3-sonnet").

    Returns:
        Bedrock model ID (e.g., "anthropic.claude-3-sonnet-20240229-v1:0").
        Returns the input unchanged if not found in mapping.
    """
    return BEDROCK_MODEL_MAP.get(model, model)


def map_model_to_anthropic(model: str) -> str:
    """Map an orchestrator model name to an Anthropic API model ID.

    Args:
        model: Orchestrator model name (e.g., "claude-3-sonnet").

    Returns:
        Anthropic model ID (e.g., "claude-3-sonnet-20240229").
        Returns the input unchanged if not found in mapping.
    """
    return ANTHROPIC_MODEL_MAP.get(model, model)


def get_model_capabilities(model: str) -> dict[str, any]:
    """Get capabilities for a model.

    Args:
        model: Model identifier.

    Returns:
        Dictionary of model capabilities.
    """
    # Normalize model name
    normalized = model.lower()

    capabilities = {
        "max_tokens": 4096,
        "supports_vision": False,
        "supports_tools": True,
        "cost_tier": "standard",
    }

    if "opus" in normalized:
        capabilities["max_tokens"] = 4096
        capabilities["supports_vision"] = True
        capabilities["cost_tier"] = "high"
    elif "sonnet" in normalized:
        capabilities["max_tokens"] = 4096
        capabilities["supports_vision"] = True
        capabilities["cost_tier"] = "standard"
    elif "haiku" in normalized:
        capabilities["max_tokens"] = 4096
        capabilities["supports_vision"] = True
        capabilities["cost_tier"] = "low"

    return capabilities
