"""
Token budget enforcement for per-user and per-project limits.

Ensures users don't exceed their allocated token budgets during
agent execution.
"""

import logging
from datetime import datetime, timedelta
from typing import Protocol

from orchestrator_v2.user.models import UserProfile
from orchestrator_v2.user.repository import FileSystemUserRepository


logger = logging.getLogger(__name__)


class BudgetExceededError(Exception):
    """Raised when a token budget limit would be exceeded."""

    def __init__(self, message: str, limit_type: str, current: int, limit: int, requested: int):
        super().__init__(message)
        self.limit_type = limit_type
        self.current = current
        self.limit = limit
        self.requested = requested


class TokenTracker(Protocol):
    """Protocol for token tracking."""

    async def get_usage_for_period(
        self,
        user_id: str,
        project_id: str | None,
        period_start: datetime,
    ) -> int:
        """Get total tokens used since period_start."""
        ...

    async def record_usage(
        self,
        user_id: str,
        project_id: str,
        agent_role: str,
        model: str,
        input_tokens: int,
        output_tokens: int,
    ) -> None:
        """Record token usage."""
        ...


class BudgetEnforcer:
    """
    Enforces token budget limits for users and projects.

    Checks budgets before agent execution and records usage after.
    """

    def __init__(
        self,
        user_repo: FileSystemUserRepository,
        token_tracker: TokenTracker | None = None,
    ):
        """
        Initialize budget enforcer.

        Args:
            user_repo: Repository for user profiles
            token_tracker: Optional tracker for detailed usage
        """
        self._user_repo = user_repo
        self._token_tracker = token_tracker

    async def check_and_reserve(
        self,
        user: UserProfile,
        project_id: str,
        estimated_tokens: int,
    ) -> None:
        """
        Check if user has sufficient budget and reserve tokens.

        Raises BudgetExceededError if budget would be exceeded.

        Args:
            user: User profile with limits and usage
            project_id: Project ID for project-level limits
            estimated_tokens: Estimated tokens for this operation
        """
        # Check daily limit
        if "daily" in user.token_limits:
            daily_limit = user.token_limits["daily"]
            daily_usage = await self._get_daily_usage(user)

            if daily_usage + estimated_tokens > daily_limit:
                logger.warning(
                    f"Budget check FAILED: user={user.user_id}, "
                    f"daily_usage={daily_usage}, estimated={estimated_tokens}, "
                    f"limit={daily_limit}"
                )
                raise BudgetExceededError(
                    f"Daily token limit exceeded. Current: {daily_usage}, "
                    f"Requested: {estimated_tokens}, Limit: {daily_limit}",
                    limit_type="daily",
                    current=daily_usage,
                    limit=daily_limit,
                    requested=estimated_tokens,
                )

        # Check project limit
        if "project" in user.token_limits:
            project_limit = user.token_limits["project"]
            project_usage = await self._get_project_usage(user, project_id)

            if project_usage + estimated_tokens > project_limit:
                logger.warning(
                    f"Budget check FAILED: user={user.user_id}, "
                    f"project={project_id}, usage={project_usage}, "
                    f"estimated={estimated_tokens}, limit={project_limit}"
                )
                raise BudgetExceededError(
                    f"Project token limit exceeded. Current: {project_usage}, "
                    f"Requested: {estimated_tokens}, Limit: {project_limit}",
                    limit_type="project",
                    current=project_usage,
                    limit=project_limit,
                    requested=estimated_tokens,
                )

        # Check total limit
        if "total" in user.token_limits:
            total_limit = user.token_limits["total"]
            total_usage = user.token_usage.total_input_tokens + user.token_usage.total_output_tokens

            if total_usage + estimated_tokens > total_limit:
                logger.warning(
                    f"Budget check FAILED: user={user.user_id}, "
                    f"total_usage={total_usage}, estimated={estimated_tokens}, "
                    f"limit={total_limit}"
                )
                raise BudgetExceededError(
                    f"Total token limit exceeded. Current: {total_usage}, "
                    f"Requested: {estimated_tokens}, Limit: {total_limit}",
                    limit_type="total",
                    current=total_usage,
                    limit=total_limit,
                    requested=estimated_tokens,
                )

        logger.info(
            f"Budget check PASSED: user={user.user_id}, "
            f"project={project_id}, estimated={estimated_tokens}"
        )

    async def record_usage(
        self,
        user: UserProfile,
        project_id: str,
        agent_role: str,
        model: str,
        input_tokens: int,
        output_tokens: int,
    ) -> None:
        """
        Record actual token usage after agent execution.

        Updates user profile and persists to repository.

        Args:
            user: User profile to update
            project_id: Project ID
            agent_role: Agent that used the tokens
            model: Model that was used
            input_tokens: Input tokens consumed
            output_tokens: Output tokens generated
        """
        total_tokens = input_tokens + output_tokens

        # Update user profile
        user.token_usage.total_input_tokens += input_tokens
        user.token_usage.total_output_tokens += output_tokens
        user.token_usage.total_requests += 1

        # Save updated profile
        await self._user_repo.save(user)

        # TODO: Record in token tracker when protocol is fully implemented
        # if self._token_tracker:
        #     await self._token_tracker.record_usage(...)

        logger.info(
            f"Token usage recorded: user={user.user_id}, "
            f"project={project_id}, agent={agent_role}, "
            f"model={model}, tokens={total_tokens}"
        )

    async def _get_daily_usage(self, user: UserProfile) -> int:
        """Get token usage for today."""
        # Simple implementation: use total usage
        # In production, track per-day usage
        if self._token_tracker:
            today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
            return await self._token_tracker.get_usage_for_period(
                user_id=user.user_id,
                project_id=None,
                period_start=today,
            )

        # Fallback: check if usage was reset today
        last_reset = user.token_usage.last_reset
        today = datetime.utcnow().date()

        if last_reset.date() < today:
            # Reset daily counters
            return 0

        return user.token_usage.total_input_tokens + user.token_usage.total_output_tokens

    async def _get_project_usage(self, user: UserProfile, project_id: str) -> int:
        """Get token usage for a specific project."""
        if self._token_tracker:
            # Use tracker for accurate per-project usage
            return await self._token_tracker.get_usage_for_period(
                user_id=user.user_id,
                project_id=project_id,
                period_start=datetime.min,
            )

        # Fallback: can't track per-project without tracker
        # Return total usage as conservative estimate
        return user.token_usage.total_input_tokens + user.token_usage.total_output_tokens

    async def get_remaining_budget(
        self,
        user: UserProfile,
        project_id: str | None = None,
    ) -> dict[str, int]:
        """
        Get remaining budget for each limit type.

        Returns:
            Dict mapping limit_type to remaining tokens
        """
        remaining = {}

        if "daily" in user.token_limits:
            daily_usage = await self._get_daily_usage(user)
            remaining["daily"] = max(0, user.token_limits["daily"] - daily_usage)

        if "project" in user.token_limits and project_id:
            project_usage = await self._get_project_usage(user, project_id)
            remaining["project"] = max(0, user.token_limits["project"] - project_usage)

        if "total" in user.token_limits:
            total_usage = user.token_usage.total_input_tokens + user.token_usage.total_output_tokens
            remaining["total"] = max(0, user.token_limits["total"] - total_usage)

        return remaining
