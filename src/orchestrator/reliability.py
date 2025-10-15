"""Reliability utilities: timeouts, retries, backoff, rollback."""

import asyncio
import random
import time
from typing import TypeVar, Callable, Awaitable, List, Optional, Any
from dataclasses import dataclass

T = TypeVar("T")


@dataclass
class RetryConfig:
    """Configuration for retry behavior."""

    retries: int = 2
    base_delay: float = 0.7
    jitter: float = 0.25
    backoff: float = 2.0
    retryable_exit_codes: List[int] = None
    retryable_messages: List[str] = None

    def __post_init__(self):
        if self.retryable_exit_codes is None:
            self.retryable_exit_codes = [75, 101, 111, 125]
        if self.retryable_messages is None:
            self.retryable_messages = ["rate limit", "transient network", "timeout"]


async def with_timeout(
    coro: Awaitable[T], seconds: float, timeout_message: str = "Operation timed out"
) -> T:
    """
    Execute a coroutine with a timeout.

    Args:
        coro: Coroutine to execute
        seconds: Timeout in seconds
        timeout_message: Custom timeout error message

    Returns:
        Result from coroutine

    Raises:
        asyncio.TimeoutError: If operation exceeds timeout
    """
    try:
        return await asyncio.wait_for(coro, timeout=seconds)
    except asyncio.TimeoutError:
        raise asyncio.TimeoutError(timeout_message)


async def retry_async(
    fn: Callable[[], Awaitable[T]],
    config: Optional[RetryConfig] = None,
    is_retryable: Optional[Callable[[Exception, Any], bool]] = None,
) -> T:
    """
    Retry an async function with exponential backoff and jitter.

    Args:
        fn: Async function to retry
        config: Retry configuration (uses defaults if None)
        is_retryable: Optional function to determine if error is retryable

    Returns:
        Result from successful execution

    Raises:
        Last exception if all retries exhausted
    """
    if config is None:
        config = RetryConfig()

    last_exception = None
    attempt = 0

    while attempt <= config.retries:
        try:
            result = await fn()
            return result

        except Exception as e:
            last_exception = e
            attempt += 1

            # Check if retryable
            if is_retryable:
                retryable = is_retryable(e, None)
            else:
                retryable = _is_default_retryable(e, config)

            if not retryable or attempt > config.retries:
                # Not retryable or exhausted retries
                raise

            # Calculate delay with exponential backoff and jitter
            delay = config.base_delay * (config.backoff ** (attempt - 1))
            jitter_amount = delay * config.jitter * (2 * random.random() - 1)
            delay_with_jitter = max(0, delay + jitter_amount)

            # Log retry (would use logger in production)
            print(
                f"Retry attempt {attempt}/{config.retries} after {delay_with_jitter:.2f}s: {str(e)[:100]}"
            )

            await asyncio.sleep(delay_with_jitter)

    # Should not reach here, but raise last exception if we do
    if last_exception:
        raise last_exception


def _is_default_retryable(exception: Exception, config: RetryConfig) -> bool:
    """
    Default retry classification logic.

    Checks:
    - Exception type (asyncio.TimeoutError, ConnectionError, etc)
    - Exit codes (if exception has exit_code attribute)
    - Error messages
    """
    # Check exception type
    if isinstance(exception, (asyncio.TimeoutError, ConnectionError, TimeoutError)):
        return True

    # Check exit code (if present)
    if hasattr(exception, "exit_code"):
        if exception.exit_code in config.retryable_exit_codes:
            return True

    # Check error message
    error_msg = str(exception).lower()
    for msg in config.retryable_messages:
        if msg.lower() in error_msg:
            return True

    return False


def retry_with_result_check(
    fn: Callable[[], Awaitable[T]],
    config: Optional[RetryConfig] = None,
    check_result: Optional[Callable[[T], bool]] = None,
) -> Awaitable[T]:
    """
    Retry function based on result checking (not just exceptions).

    Args:
        fn: Async function to retry
        config: Retry configuration
        check_result: Function to check if result is acceptable (True = success)

    Returns:
        Successful result
    """

    async def retry_wrapper():
        if config is None:
            cfg = RetryConfig()
        else:
            cfg = config

        last_result = None
        attempt = 0

        while attempt <= cfg.retries:
            result = await fn()
            last_result = result

            # Check if result is acceptable
            if check_result is None or check_result(result):
                return result

            attempt += 1

            if attempt <= cfg.retries:
                # Calculate delay
                delay = cfg.base_delay * (cfg.backoff ** (attempt - 1))
                jitter_amount = delay * cfg.jitter * (2 * random.random() - 1)
                delay_with_jitter = max(0, delay + jitter_amount)

                await asyncio.sleep(delay_with_jitter)

        # Return last result even if not acceptable
        return last_result

    return retry_wrapper()


class RollbackInfo:
    """Information for rolling back a phase."""

    def __init__(self, phase_name: str, reason: str, artifacts: List[str]):
        self.phase_name = phase_name
        self.reason = reason
        self.artifacts = artifacts
        self.timestamp = time.strftime("%Y-%m-%d %H:%M:%S")

    def to_markdown(self) -> str:
        """Generate rollback advisory markdown."""
        lines = [
            f"# Rollback Advisory: {self.phase_name}",
            "",
            f"**Timestamp:** {self.timestamp}",
            f"**Reason:** {self.reason}",
            "",
            "## Manual Rollback Steps",
            "",
            "This is a non-destructive advisory. The orchestrator has:",
            "- Reset the workflow cursor to the previous phase",
            "- Preserved all artifacts and logs",
            "",
            "### Artifacts to Review/Revert",
            "",
        ]

        if self.artifacts:
            for artifact in self.artifacts:
                lines.append(f"- `{artifact}`")
        else:
            lines.append("No artifacts were recorded for this phase.")

        lines.extend(
            [
                "",
                "### Recommended Actions",
                "",
                "1. Review the artifacts listed above",
                "2. Manually revert any unwanted changes using git or file operations",
                "3. Run `orchestrator run resume` to continue from the previous phase",
                "4. Or run `orchestrator run next` to re-execute this phase",
                "",
                "### Notes",
                "",
                "- No automatic git operations were performed",
                "- All phase logs are preserved in `.claude/logs/`",
                "- Consensus decisions are preserved in `.claude/consensus/`",
                "",
                "---",
                "*Generated by Orchestrator Rollback System*",
            ]
        )

        return "\n".join(lines)
