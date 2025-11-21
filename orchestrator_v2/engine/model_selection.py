"""
Model selection logic for agent execution.

Determines which LLM provider and model to use based on:
- User entitlements
- Agent role
- Default configurations
"""

from dataclasses import dataclass
from typing import Any

from orchestrator_v2.user.models import UserProfile


# Default models per agent role
DEFAULT_ROLE_MODELS: dict[str, str] = {
    "architect": "claude-sonnet-4-20250514",
    "developer": "claude-sonnet-4-20250514",
    "data": "claude-sonnet-4-20250514",
    "qa": "claude-3-5-haiku-20241022",
    "documentarian": "claude-3-5-haiku-20241022",
    "consensus": "claude-sonnet-4-20250514",
    "reviewer": "claude-sonnet-4-20250514",
    "steward": "claude-3-5-haiku-20241022",
}

# Default provider
DEFAULT_PROVIDER = "anthropic"


@dataclass
class ModelConfig:
    """Configuration for an LLM model."""
    provider: str
    model: str

    def __str__(self) -> str:
        return f"{self.provider}:{self.model}"


def select_model_for_agent(
    user: UserProfile | None,
    agent_role: str,
    project_metadata: dict[str, Any] | None = None,
) -> ModelConfig:
    """
    Select the appropriate model for an agent based on user entitlements.

    Precedence:
    1. Project-specific override (from project_metadata)
    2. User's model_entitlements for this agent role
    3. User's default_model
    4. Global default model for this role

    Args:
        user: User profile with entitlements and preferences
        agent_role: Role of the agent (architect, developer, etc.)
        project_metadata: Optional project-specific configuration

    Returns:
        ModelConfig with provider and model name
    """
    provider = DEFAULT_PROVIDER
    model = None

    # 1. Check project-specific override
    if project_metadata:
        project_models = project_metadata.get("model_overrides", {})
        if agent_role in project_models:
            model = project_models[agent_role]
            provider = project_metadata.get("provider", DEFAULT_PROVIDER)

    # 2. Check user entitlements for this role
    if not model and user:
        role_entitlements = user.model_entitlements.get(agent_role, [])
        if role_entitlements:
            # Use first allowed model
            model = role_entitlements[0]
            provider = user.llm_provider

    # 3. Check user's default model
    if not model and user:
        if user.default_model:
            model = user.default_model
            provider = user.llm_provider

    # 4. Fall back to global defaults
    if not model:
        model = DEFAULT_ROLE_MODELS.get(agent_role, "claude-sonnet-4-20250514")

    # Set provider from user if available
    if user and user.llm_provider:
        provider = user.llm_provider

    return ModelConfig(provider=provider, model=model)


def get_model_cost_per_token(model: str) -> tuple[float, float]:
    """
    Get cost per token for a model (input, output).

    Returns:
        Tuple of (input_cost_per_1k, output_cost_per_1k) in USD
    """
    # Approximate costs as of 2024
    costs = {
        # Claude 3.5 Sonnet
        "claude-sonnet-4-20250514": (0.003, 0.015),
        "claude-3-5-sonnet-20241022": (0.003, 0.015),
        "claude-3-5-sonnet-latest": (0.003, 0.015),
        # Claude 3.5 Haiku
        "claude-3-5-haiku-20241022": (0.0008, 0.004),
        "claude-3-5-haiku-latest": (0.0008, 0.004),
        # Claude 3 Opus
        "claude-3-opus-20240229": (0.015, 0.075),
        "claude-3-opus-latest": (0.015, 0.075),
        # Default fallback
        "default": (0.003, 0.015),
    }

    return costs.get(model, costs["default"])


def estimate_tokens_for_agent(agent_role: str) -> int:
    """
    Estimate token usage for an agent based on historical patterns.

    This is a simple heuristic - in production, use actual historical data.

    Args:
        agent_role: Role of the agent

    Returns:
        Estimated total tokens (input + output)
    """
    estimates = {
        "architect": 8000,      # Detailed planning
        "developer": 10000,     # Code generation
        "data": 6000,           # Pipeline work
        "qa": 5000,             # Test generation
        "documentarian": 4000,  # Documentation
        "consensus": 3000,      # Review/approval
        "reviewer": 4000,       # Code review
        "steward": 2000,        # Hygiene checks
    }

    return estimates.get(agent_role, 5000)
