"""Utility functions for orchestrator run-loop."""

import asyncio
from ..reliability import RetryConfig


def is_agent_error_retryable(exception: Exception, retry_cfg: RetryConfig) -> bool:
    """
    Check if agent execution error is retryable.

    Args:
        exception: Exception raised during agent execution
        retry_cfg: Retry configuration

    Returns:
        True if the error should be retried
    """
    # Timeout errors are retryable
    if isinstance(exception, (asyncio.TimeoutError, TimeoutError)):
        return True

    # Check exit code if present
    if hasattr(exception, "exit_code"):
        if exception.exit_code in retry_cfg.retryable_exit_codes:
            return True

    # Check error message
    error_msg = str(exception).lower()
    for msg in retry_cfg.retryable_messages:
        if msg.lower() in error_msg:
            return True

    return False
