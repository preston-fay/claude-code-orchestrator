"""
AWS Bedrock provider for Orchestrator v2.

Uses boto3 to call Claude models via AWS Bedrock.
Authentication uses AWS IAM credentials (no API key required).

See docs/LLM_PROVIDERS.md for usage details.
"""

import json
import logging
import os

from orchestrator_v2.engine.state_models import AgentContext
from orchestrator_v2.llm.providers.base import (
    LlmAuthenticationError,
    LlmModelNotFoundError,
    LlmProviderError,
    LlmRateLimitError,
    LlmResult,
)
from orchestrator_v2.llm.providers.model_mapping import map_model_to_bedrock

logger = logging.getLogger(__name__)


class BedrockLlmProvider:
    """LLM provider using AWS Bedrock.

    Uses AWS IAM credentials for authentication.
    No user API key required - uses environment credentials or IAM role.

    Supported models (via Bedrock):
    - anthropic.claude-3-5-sonnet-20241022-v2:0
    - anthropic.claude-3-sonnet-20240229-v1:0
    - anthropic.claude-3-haiku-20240307-v1:0
    - anthropic.claude-3-opus-20240229-v1:0
    """

    def __init__(self, region: str | None = None):
        """Initialize the Bedrock provider.

        Args:
            region: AWS region for Bedrock. Defaults to AWS_DEFAULT_REGION
                    environment variable or us-east-1.
        """
        self._name = "bedrock"
        self._region = region or os.environ.get("AWS_DEFAULT_REGION", "us-east-1")
        self._client = None

    def _get_client(self):
        """Get or create the Bedrock runtime client.

        Returns:
            boto3 Bedrock runtime client.

        Raises:
            LlmProviderError: If boto3 is not installed.
            LlmAuthenticationError: If AWS credentials are not configured.
        """
        if self._client is None:
            try:
                import boto3
                from botocore.exceptions import NoCredentialsError
            except ImportError as e:
                raise LlmProviderError(
                    "boto3 package not installed. Run: pip install boto3",
                    provider=self._name,
                ) from e

            try:
                self._client = boto3.client(
                    "bedrock-runtime",
                    region_name=self._region,
                )
            except NoCredentialsError as e:
                raise LlmAuthenticationError(
                    "AWS credentials not configured. Set AWS_ACCESS_KEY_ID and "
                    "AWS_SECRET_ACCESS_KEY or use an IAM role.",
                    provider=self._name,
                ) from e

        return self._client

    async def generate(
        self,
        prompt: str,
        model: str,
        context: AgentContext,
    ) -> LlmResult:
        """Generate a response using AWS Bedrock.

        Args:
            prompt: The formatted prompt to send.
            model: Model identifier (will be mapped to Bedrock model ID).
            context: Agent context (API key not required for Bedrock).

        Returns:
            LlmResult with generated text and token usage.

        Raises:
            LlmAuthenticationError: If AWS credentials are invalid.
            LlmModelNotFoundError: If the model is not available.
            LlmRateLimitError: If rate limits are exceeded.
            LlmProviderError: For other API errors.
        """
        try:
            from botocore.exceptions import ClientError
        except ImportError as e:
            raise LlmProviderError(
                "boto3 package not installed. Run: pip install boto3",
                provider=self._name,
                model=model,
            ) from e

        # Map model name to Bedrock model ID
        bedrock_model = map_model_to_bedrock(model)

        client = self._get_client()

        # Build request body for Claude on Bedrock
        # Using the Messages API format
        request_body = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 4096,
            "messages": [
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
        }

        try:
            logger.info(
                f"Calling Bedrock API: model={bedrock_model}, "
                f"region={self._region}, user={context.user_id}, "
                f"prompt_length={len(prompt)}"
            )

            response = client.invoke_model(
                modelId=bedrock_model,
                contentType="application/json",
                accept="application/json",
                body=json.dumps(request_body),
            )

            # Parse response
            response_body = json.loads(response["body"].read())

            # Extract text from response
            text = ""
            for block in response_body.get("content", []):
                if block.get("type") == "text":
                    text += block.get("text", "")

            # Get token usage
            usage = response_body.get("usage", {})
            input_tokens = usage.get("input_tokens", 0)
            output_tokens = usage.get("output_tokens", 0)

            result = LlmResult(
                text=text,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                provider=self._name,
                model=bedrock_model,
            )

            logger.info(
                f"Bedrock API response: input_tokens={result.input_tokens}, "
                f"output_tokens={result.output_tokens}"
            )

            return result

        except ClientError as e:
            error_code = e.response.get("Error", {}).get("Code", "")
            error_message = e.response.get("Error", {}).get("Message", str(e))

            if error_code == "AccessDeniedException":
                raise LlmAuthenticationError(
                    f"Access denied: {error_message}",
                    provider=self._name,
                    model=bedrock_model,
                ) from e

            if error_code == "ValidationException" and "model" in error_message.lower():
                raise LlmModelNotFoundError(
                    f"Model not found: {bedrock_model}. {error_message}",
                    provider=self._name,
                    model=bedrock_model,
                ) from e

            if error_code == "ThrottlingException":
                raise LlmRateLimitError(
                    f"Rate limit exceeded: {error_message}",
                    provider=self._name,
                    model=bedrock_model,
                ) from e

            raise LlmProviderError(
                f"Bedrock error ({error_code}): {error_message}",
                provider=self._name,
                model=bedrock_model,
            ) from e

        except Exception as e:
            raise LlmProviderError(
                f"Unexpected error: {e}",
                provider=self._name,
                model=bedrock_model,
            ) from e
