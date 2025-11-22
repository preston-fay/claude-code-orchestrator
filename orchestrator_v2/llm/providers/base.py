"""
Base LLM provider interface for Orchestrator v2.

Defines the protocol that all LLM providers must implement,
enabling pluggable LLM backends (Anthropic API, AWS Bedrock, etc.).

See docs/LLM_PROVIDERS.md for provider architecture details.
"""

from typing import TYPE_CHECKING, Protocol, runtime_checkable

from pydantic import BaseModel

if TYPE_CHECKING:
    from orchestrator_v2.engine.state_models import AgentContext


class LlmResult(BaseModel):
    """Result from an LLM provider call.

    Contains the generated text and token usage metrics
    for cost tracking and budget enforcement.
    """
    text: str
    input_tokens: int
    output_tokens: int
    provider: str
    model: str


@runtime_checkable
class LlmProvider(Protocol):
    """Protocol for LLM providers.

    All LLM providers must implement this interface to be
    compatible with the orchestrator's agent runtime.

    Providers handle:
    - Authentication (API keys, IAM roles, etc.)
    - Model invocation
    - Response parsing
    - Token counting
    """

    async def generate(
        self,
        prompt: str,
        model: str,
        context: "AgentContext",
    ) -> LlmResult:
        """Generate a response from the LLM.

        Args:
            prompt: The formatted prompt to send to the LLM.
            model: Model identifier (provider-specific mapping may apply).
            context: Agent context with user credentials and settings.

        Returns:
            LlmResult with generated text and token usage.

        Raises:
            ValueError: If required credentials are missing.
            LlmProviderError: If the LLM call fails.
        """
        ...


class LlmProviderError(Exception):
    """Base exception for LLM provider errors."""

    def __init__(self, message: str, provider: str, model: str | None = None):
        self.provider = provider
        self.model = model
        super().__init__(f"[{provider}] {message}")


class LlmAuthenticationError(LlmProviderError):
    """Raised when LLM authentication fails."""
    pass


class LlmRateLimitError(LlmProviderError):
    """Raised when rate limits are exceeded."""
    pass


class LlmModelNotFoundError(LlmProviderError):
    """Raised when the requested model is not available."""
    pass
