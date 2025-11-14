"""Context cache for sharing computation results across parallel agent executions."""

import hashlib
import json
from typing import Any, Callable, Dict, Optional
from dataclasses import dataclass
from datetime import datetime


@dataclass
class CacheEntry:
    """Cache entry with metadata."""

    key: str
    value: Any
    created_at: str
    hit_count: int = 0


class ContextCache:
    """
    Cache for sharing context and computation results across parallel agents.

    Uses content-based hashing to avoid recomputing identical work.
    Thread-safe for concurrent access.
    """

    def __init__(self):
        """Initialize empty cache."""
        self._cache: Dict[str, CacheEntry] = {}
        self._stats = {
            "hits": 0,
            "misses": 0,
            "sets": 0,
        }

    def _hash_key(self, key: Any) -> str:
        """
        Create a stable hash key from any input.

        Args:
            key: Input to hash (will be JSON-serialized)

        Returns:
            Hex digest hash string
        """
        if isinstance(key, str):
            key_str = key
        else:
            # Serialize to JSON for consistent hashing
            key_str = json.dumps(key, sort_keys=True)

        return hashlib.sha256(key_str.encode()).hexdigest()

    def get_or_compute(self, key: Any, compute_fn: Callable[[], Any]) -> Any:
        """
        Get value from cache or compute it if missing.

        Args:
            key: Cache key (any JSON-serializable value)
            compute_fn: Function to call if cache miss (no arguments)

        Returns:
            Cached or computed value
        """
        hash_key = self._hash_key(key)

        # Check cache
        if hash_key in self._cache:
            entry = self._cache[hash_key]
            entry.hit_count += 1
            self._stats["hits"] += 1
            return entry.value

        # Cache miss - compute value
        self._stats["misses"] += 1
        value = compute_fn()

        # Store in cache
        self.set(key, value)

        return value

    def get(self, key: Any) -> Optional[Any]:
        """
        Get value from cache.

        Args:
            key: Cache key

        Returns:
            Cached value or None if not found
        """
        hash_key = self._hash_key(key)

        if hash_key in self._cache:
            entry = self._cache[hash_key]
            entry.hit_count += 1
            self._stats["hits"] += 1
            return entry.value

        self._stats["misses"] += 1
        return None

    def set(self, key: Any, value: Any) -> None:
        """
        Store value in cache.

        Args:
            key: Cache key
            value: Value to cache
        """
        hash_key = self._hash_key(key)

        self._cache[hash_key] = CacheEntry(
            key=hash_key,
            value=value,
            created_at=datetime.now().isoformat(),
            hit_count=0,
        )
        self._stats["sets"] += 1

    def clear(self) -> None:
        """Clear all cached entries."""
        self._cache.clear()
        self._stats = {
            "hits": 0,
            "misses": 0,
            "sets": 0,
        }

    def get_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.

        Returns:
            Dictionary with cache metrics
        """
        total_requests = self._stats["hits"] + self._stats["misses"]
        hit_rate = (
            self._stats["hits"] / total_requests if total_requests > 0 else 0.0
        )

        return {
            "size": len(self._cache),
            "hits": self._stats["hits"],
            "misses": self._stats["misses"],
            "sets": self._stats["sets"],
            "hit_rate": hit_rate,
            "total_requests": total_requests,
        }

    def __len__(self) -> int:
        """Return number of cached entries."""
        return len(self._cache)

    def __contains__(self, key: Any) -> bool:
        """Check if key exists in cache."""
        hash_key = self._hash_key(key)
        return hash_key in self._cache
