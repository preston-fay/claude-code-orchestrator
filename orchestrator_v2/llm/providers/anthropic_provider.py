"""
Anthropic API provider for Orchestrator v2.

Uses the official Anthropic Python SDK with user-supplied API keys (BYOK).

See docs/LLM_PROVIDERS.md for usage details.
"""

import logging

from orchestrator_v2.core.state_models import AgentContext
from orchestrator_v2.llm.providers.base import (
    LlmAuthenticationError,
    LlmProviderError,
    LlmRateLimitError,
    LlmResult,
)

logger = logging.getLogger(__name__)


class AnthropicLlmProvider:
    """LLM provider using the Anthropic API.

    Requires a user-supplied API key (BYOK model).
    The API key is read from AgentContext.llm_api_key.

    Supported models:
    - claude-3-5-sonnet-20241022
    - claude-3-sonnet-20240229
    - claude-3-haiku-20240307
    - claude-3-opus-20240229
    """

    def __init__(self):
        """Initialize the Anthropic provider."""
        self._name = "anthropic"

    async def generate(
        self,
        prompt: str,
        model: str,
        context: AgentContext,
    ) -> LlmResult:
        """Generate a response using the Anthropic API.

        Args:
            prompt: The formatted prompt to send.
            model: Anthropic model identifier.
            context: Agent context with API key.

        Returns:
            LlmResult with generated text and token usage.

        Raises:
            LlmAuthenticationError: If API key is missing or invalid.
            LlmRateLimitError: If rate limits are exceeded.
            LlmProviderError: For other API errors.
        """
        # Check for API key
        if not context.llm_api_key:
            raise LlmAuthenticationError(
                "No Anthropic API key provided. Set llm_api_key in user profile.",
                provider=self._name,
                model=model,
            )

        try:
            # Import here to allow graceful degradation if not installed
            from anthropic import AsyncAnthropic, APIError, AuthenticationError, RateLimitError
        except ImportError as e:
            raise LlmProviderError(
                "anthropic package not installed. Run: pip install anthropic",
                provider=self._name,
                model=model,
            ) from e

        # Create client with user's API key
        client = AsyncAnthropic(api_key=context.llm_api_key)

        try:
            logger.info(
                f"Calling Anthropic API: model={model}, "
                f"user={context.user_id}, prompt_length={len(prompt)}"
            )

            response = await client.messages.create(
                model=model,
                max_tokens=4096,
                messages=[{"role": "user", "content": prompt}],
            )

            # Extract text from response
            text = ""
            for block in response.content:
                if hasattr(block, "text"):
                    text += block.text

            result = LlmResult(
                text=text,
                input_tokens=response.usage.input_tokens,
                output_tokens=response.usage.output_tokens,
                provider=self._name,
                model=model,
            )

            logger.info(
                f"Anthropic API response: input_tokens={result.input_tokens}, "
                f"output_tokens={result.output_tokens}"
            )

            return result

        except AuthenticationError as e:
            raise LlmAuthenticationError(
                f"Invalid API key: {e}",
                provider=self._name,
                model=model,
            ) from e

        except RateLimitError as e:
            raise LlmRateLimitError(
                f"Rate limit exceeded: {e}",
                provider=self._name,
                model=model,
            ) from e

        except APIError as e:
            raise LlmProviderError(
                f"API error: {e}",
                provider=self._name,
                model=model,
            ) from e

        except Exception as e:
            raise LlmProviderError(
                f"Unexpected error: {e}",
                provider=self._name,
                model=model,
            ) from e
