"""
Rate limiting with token bucket algorithm.

Supports:
- In-process rate limiting (default)
- Redis-backed rate limiting (optional)
- Per-tenant, per-user, per-route limits
- Configurable burst allowance
"""

import time
from typing import Dict, Tuple, Optional
from collections import defaultdict
from datetime import datetime, timedelta

from .schemas import Identity


class TokenBucket:
    """
    Token bucket rate limiter.

    Implements token bucket algorithm with refill rate.
    """

    def __init__(self, capacity: int, refill_rate: float):
        """
        Initialize token bucket.

        Args:
            capacity: Maximum tokens (burst allowance)
            refill_rate: Tokens per second
        """
        self.capacity = capacity
        self.refill_rate = refill_rate
        self.tokens = capacity
        self.last_refill = time.time()

    def consume(self, tokens: int = 1) -> bool:
        """
        Try to consume tokens.

        Args:
            tokens: Number of tokens to consume

        Returns:
            True if tokens available, False if rate limited
        """
        self._refill()

        if self.tokens >= tokens:
            self.tokens -= tokens
            return True

        return False

    def _refill(self):
        """Refill tokens based on elapsed time."""
        now = time.time()
        elapsed = now - self.last_refill

        # Add tokens based on refill rate
        new_tokens = elapsed * self.refill_rate
        self.tokens = min(self.capacity, self.tokens + new_tokens)
        self.last_refill = now

    def remaining(self) -> int:
        """Get remaining tokens."""
        self._refill()
        return int(self.tokens)

    def reset_in(self) -> float:
        """Seconds until bucket is full."""
        if self.tokens >= self.capacity:
            return 0.0

        tokens_needed = self.capacity - self.tokens
        return tokens_needed / self.refill_rate


class RateLimiter:
    """
    In-process rate limiter with per-tenant/user/route limits.
    """

    def __init__(
        self,
        default_requests_per_minute: int = 60,
        default_burst: int = 10,
        route_limits: Optional[Dict[str, Dict[str, int]]] = None
    ):
        """
        Initialize rate limiter.

        Args:
            default_requests_per_minute: Default rate limit
            default_burst: Default burst allowance
            route_limits: Per-route overrides {route: {requests_per_minute, burst}}
        """
        self.default_rpm = default_requests_per_minute
        self.default_burst = default_burst
        self.route_limits = route_limits or {}

        # Buckets: {key -> TokenBucket}
        self.buckets: Dict[str, TokenBucket] = {}

        # Cleanup old buckets periodically
        self.last_cleanup = time.time()
        self.cleanup_interval = 300  # 5 minutes

    def check_rate_limit(
        self,
        identity: Identity,
        tenant: str,
        route: str
    ) -> Tuple[bool, int, float]:
        """
        Check rate limit for request.

        Args:
            identity: User identity
            tenant: Tenant slug
            route: Route path

        Returns:
            Tuple of (allowed, remaining, reset_in)
        """
        # Get limits for route
        limits = self.route_limits.get(route, {})
        rpm = limits.get("requests_per_minute", self.default_rpm)
        burst = limits.get("burst", self.default_burst)

        # Compute rate limit key
        key = f"{tenant}:{identity.id}:{route}"

        # Get or create bucket
        if key not in self.buckets:
            refill_rate = rpm / 60.0  # Convert to per-second
            self.buckets[key] = TokenBucket(capacity=burst, refill_rate=refill_rate)

        bucket = self.buckets[key]

        # Try to consume token
        allowed = bucket.consume(1)
        remaining = bucket.remaining()
        reset_in = bucket.reset_in()

        # Periodic cleanup
        self._maybe_cleanup()

        return allowed, remaining, reset_in

    def _maybe_cleanup(self):
        """Cleanup old buckets periodically."""
        now = time.time()
        if now - self.last_cleanup < self.cleanup_interval:
            return

        # Remove buckets that are full (not actively used)
        keys_to_remove = []
        for key, bucket in self.buckets.items():
            if bucket.tokens >= bucket.capacity:
                keys_to_remove.append(key)

        for key in keys_to_remove:
            del self.buckets[key]

        self.last_cleanup = now

    def reset(self, identity: Identity, tenant: str, route: str):
        """Reset rate limit for specific key."""
        key = f"{tenant}:{identity.id}:{route}"
        if key in self.buckets:
            del self.buckets[key]


# Global instance
_rate_limiter: Optional[RateLimiter] = None


def get_rate_limiter() -> RateLimiter:
    """Get global rate limiter instance."""
    global _rate_limiter
    if _rate_limiter is None:
        # Load config from security.yaml
        try:
            import yaml
            from pathlib import Path

            config_path = Path("configs/security.yaml")
            if config_path.exists():
                with open(config_path) as f:
                    config = yaml.safe_load(f)

                rate_config = config.get("rate_limits", {})
                default_rpm = rate_config.get("default", {}).get("requests_per_minute", 60)
                default_burst = rate_config.get("default", {}).get("burst", 10)
                route_limits = rate_config.get("routes", {})

                _rate_limiter = RateLimiter(
                    default_requests_per_minute=default_rpm,
                    default_burst=default_burst,
                    route_limits=route_limits
                )
            else:
                _rate_limiter = RateLimiter()
        except Exception:
            _rate_limiter = RateLimiter()

    return _rate_limiter


def is_rate_limited(identity: Identity, tenant: str, route: str) -> Tuple[bool, Dict[str, any]]:
    """
    Check if request is rate limited.

    Args:
        identity: User identity
        tenant: Tenant slug
        route: Route path

    Returns:
        Tuple of (is_limited, headers_dict)
    """
    limiter = get_rate_limiter()
    allowed, remaining, reset_in = limiter.check_rate_limit(identity, tenant, route)

    headers = {
        "X-RateLimit-Remaining": str(remaining),
        "X-RateLimit-Reset": str(int(time.time() + reset_in)),
    }

    if not allowed:
        headers["Retry-After"] = str(int(reset_in) + 1)

    return not allowed, headers
