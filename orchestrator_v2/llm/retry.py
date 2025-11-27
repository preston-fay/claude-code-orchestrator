"""
LLM retry utilities with exponential backoff.

Provides retry logic for transient LLM failures like:
- Rate limits (429)
- Server errors (500, 502, 503)
- Network timeouts
- API overload
"""

import asyncio
import logging
import random
from functools import wraps
from typing import Any, Callable, TypeVar, ParamSpec

logger = logging.getLogger(__name__)

P = ParamSpec('P')
T = TypeVar('T')


# Retryable exception types
RETRYABLE_EXCEPTIONS = (
    ConnectionError,
    TimeoutError,
    asyncio.TimeoutError,
)

# Retryable status codes in exception messages
RETRYABLE_STATUS_CODES = (429, 500, 502, 503, 504)


class LLMRetryError(Exception):
    """Raised when all retry attempts are exhausted."""
    
    def __init__(self, message: str, last_error: Exception | None = None, attempts: int = 0):
        super().__init__(message)
        self.last_error = last_error
        self.attempts = attempts


class RetryConfig:
    """Configuration for retry behavior."""
    
    def __init__(
        self,
        max_attempts: int = 3,
        initial_delay: float = 1.0,
        max_delay: float = 60.0,
        exponential_base: float = 2.0,
        jitter: bool = True,
    ):
        """
        Initialize retry configuration.
        
        Args:
            max_attempts: Maximum number of retry attempts.
            initial_delay: Initial delay in seconds before first retry.
            max_delay: Maximum delay in seconds between retries.
            exponential_base: Base for exponential backoff.
            jitter: Whether to add random jitter to delays.
        """
        self.max_attempts = max_attempts
        self.initial_delay = initial_delay
        self.max_delay = max_delay
        self.exponential_base = exponential_base
        self.jitter = jitter
    
    def get_delay(self, attempt: int) -> float:
        """Calculate delay for a given attempt number."""
        delay = self.initial_delay * (self.exponential_base ** attempt)
        delay = min(delay, self.max_delay)
        
        if self.jitter:
            # Add +/- 25% jitter
            jitter_range = delay * 0.25
            delay += random.uniform(-jitter_range, jitter_range)
        
        return max(0, delay)


# Default retry configuration
DEFAULT_RETRY_CONFIG = RetryConfig(
    max_attempts=3,
    initial_delay=1.0,
    max_delay=60.0,
    exponential_base=2.0,
    jitter=True,
)


def is_retryable_error(error: Exception) -> bool:
    """
    Check if an error is retryable.
    
    Args:
        error: The exception to check.
        
    Returns:
        True if the error is retryable.
    """
    # Check exception type
    if isinstance(error, RETRYABLE_EXCEPTIONS):
        return True
    
    # Check for retryable status codes in error message
    error_str = str(error).lower()
    for code in RETRYABLE_STATUS_CODES:
        if str(code) in error_str:
            return True
    
    # Check for common retryable error patterns
    retryable_patterns = [
        'rate limit',
        'rate_limit',
        'too many requests',
        'overloaded',
        'temporarily unavailable',
        'service unavailable',
        'gateway timeout',
        'connection reset',
        'connection refused',
        'network error',
    ]
    
    for pattern in retryable_patterns:
        if pattern in error_str:
            return True
    
    return False


async def retry_async(
    func: Callable[..., Any],
    *args: Any,
    config: RetryConfig | None = None,
    **kwargs: Any,
) -> Any:
    """
    Execute an async function with retry logic.
    
    Args:
        func: Async function to execute.
        *args: Positional arguments for the function.
        config: Retry configuration (uses default if not provided).
        **kwargs: Keyword arguments for the function.
        
    Returns:
        Result of the function.
        
    Raises:
        LLMRetryError: If all retry attempts are exhausted.
    """
    if config is None:
        config = DEFAULT_RETRY_CONFIG
    
    last_error: Exception | None = None
    
    for attempt in range(config.max_attempts):
        try:
            return await func(*args, **kwargs)
        except Exception as e:
            last_error = e
            
            if not is_retryable_error(e):
                # Non-retryable error, raise immediately
                raise
            
            if attempt < config.max_attempts - 1:
                delay = config.get_delay(attempt)
                logger.warning(
                    f"LLM call failed (attempt {attempt + 1}/{config.max_attempts}): {e}. "
                    f"Retrying in {delay:.2f}s..."
                )
                await asyncio.sleep(delay)
            else:
                logger.error(
                    f"LLM call failed after {config.max_attempts} attempts: {e}"
                )
    
    raise LLMRetryError(
        f"All {config.max_attempts} retry attempts exhausted",
        last_error=last_error,
        attempts=config.max_attempts,
    )


def with_retry(
    config: RetryConfig | None = None,
) -> Callable[[Callable[P, T]], Callable[P, T]]:
    """
    Decorator to add retry logic to async functions.
    
    Args:
        config: Retry configuration (uses default if not provided).
        
    Returns:
        Decorated function with retry logic.
    """
    if config is None:
        config = DEFAULT_RETRY_CONFIG
    
    def decorator(func: Callable[P, T]) -> Callable[P, T]:
        @wraps(func)
        async def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
            return await retry_async(func, *args, config=config, **kwargs)
        return wrapper  # type: ignore
    return decorator


class LLMCallContext:
    """
    Context manager for LLM calls with automatic retry.
    
    Usage:
        async with LLMCallContext(config) as ctx:
            result = await ctx.execute(provider.generate, prompt=prompt)
    """
    
    def __init__(self, config: RetryConfig | None = None):
        self.config = config or DEFAULT_RETRY_CONFIG
        self.attempts = 0
        self.last_error: Exception | None = None
    
    async def __aenter__(self) -> 'LLMCallContext':
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass
    
    async def execute(self, func: Callable[..., Any], *args: Any, **kwargs: Any) -> Any:
        """
        Execute a function with retry logic.
        
        Args:
            func: Function to execute.
            *args: Positional arguments.
            **kwargs: Keyword arguments.
            
        Returns:
            Function result.
        """
        result = await retry_async(func, *args, config=self.config, **kwargs)
        return result
