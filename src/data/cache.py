"""
Query result caching for DuckDB.

Caches parameterized SQL query results to Parquet files with:
- SQL hash + params → cache key
- TTL-based expiration
- Pattern-based invalidation
"""

import hashlib
import json
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
import os

try:
    import pyarrow.parquet as pq
    import pyarrow as pa
    PYARROW_AVAILABLE = True
except ImportError:
    PYARROW_AVAILABLE = False

from src.ops.metrics import cache_hits_total, cache_misses_total, cache_size_bytes


class QueryCache:
    """
    Query result cache with TTL and pattern invalidation.

    Cache structure:
        cache/queries/{hash}.parquet  - Result data
        cache/queries/{hash}.meta     - Metadata (SQL, params, created_at, ttl)
    """

    def __init__(self, cache_dir: Path):
        """
        Initialize query cache.

        Args:
            cache_dir: Directory for cache files
        """
        self.cache_dir = cache_dir
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def _compute_key(self, sql: str, params: Optional[Dict[str, Any]] = None) -> str:
        """
        Compute cache key from SQL and params.

        Args:
            sql: SQL query
            params: Query parameters

        Returns:
            Cache key (hex hash)
        """
        # Normalize SQL (remove extra whitespace)
        normalized_sql = " ".join(sql.split())

        # Include params in hash
        params_str = json.dumps(params or {}, sort_keys=True)

        # Compute hash
        key_str = f"{normalized_sql}|{params_str}"
        return hashlib.sha256(key_str.encode()).hexdigest()

    def get(
        self, sql: str, params: Optional[Dict[str, Any]] = None
    ) -> Optional["pa.Table"]:
        """
        Get cached query result.

        Args:
            sql: SQL query
            params: Query parameters

        Returns:
            PyArrow table or None if not cached/expired
        """
        if not PYARROW_AVAILABLE:
            return None

        key = self._compute_key(sql, params)
        data_path = self.cache_dir / f"{key}.parquet"
        meta_path = self.cache_dir / f"{key}.meta"

        # Check if cached
        if not data_path.exists() or not meta_path.exists():
            cache_misses_total.labels(cache_type="query").inc()
            return None

        # Load metadata
        with open(meta_path, "r") as f:
            meta = json.load(f)

        # Check TTL
        created_at = datetime.fromisoformat(meta["created_at"])
        ttl = timedelta(seconds=meta["ttl_seconds"])

        if datetime.now() > created_at + ttl:
            # Expired - remove
            data_path.unlink()
            meta_path.unlink()
            cache_misses_total.labels(cache_type="query").inc()
            return None

        # Load data
        try:
            table = pq.read_table(data_path)
            cache_hits_total.labels(cache_type="query").inc()
            return table
        except Exception:
            # Corrupted cache - remove
            data_path.unlink()
            meta_path.unlink()
            cache_misses_total.labels(cache_type="query").inc()
            return None

    def set(
        self,
        sql: str,
        table: "pa.Table",
        params: Optional[Dict[str, Any]] = None,
        ttl_seconds: int = 3600,
    ) -> None:
        """
        Cache query result.

        Args:
            sql: SQL query
            table: PyArrow table result
            params: Query parameters
            ttl_seconds: Time to live in seconds
        """
        if not PYARROW_AVAILABLE:
            return

        key = self._compute_key(sql, params)
        data_path = self.cache_dir / f"{key}.parquet"
        meta_path = self.cache_dir / f"{key}.meta"

        # Write data
        pq.write_table(table, data_path, compression="snappy")

        # Write metadata
        meta = {
            "sql": sql,
            "params": params or {},
            "created_at": datetime.now().isoformat(),
            "ttl_seconds": ttl_seconds,
            "row_count": len(table),
        }

        with open(meta_path, "w") as f:
            json.dump(meta, f)

        # Update size metric
        self._update_size_metric()

    def invalidate(self, pattern: str = "*") -> int:
        """
        Invalidate cache entries matching pattern.

        Args:
            pattern: SQL pattern to match (supports * wildcard)

        Returns:
            Number of entries invalidated
        """
        count = 0

        # Get all meta files
        for meta_path in self.cache_dir.glob("*.meta"):
            with open(meta_path, "r") as f:
                meta = json.load(f)

            sql = meta["sql"]

            # Check if matches pattern
            if self._matches_pattern(sql, pattern):
                # Remove data and meta
                data_path = meta_path.with_suffix(".parquet")
                if data_path.exists():
                    data_path.unlink()
                meta_path.unlink()
                count += 1

        # Update size metric
        self._update_size_metric()

        return count

    def clear(self) -> int:
        """
        Clear entire cache.

        Returns:
            Number of entries cleared
        """
        return self.invalidate("*")

    def _matches_pattern(self, sql: str, pattern: str) -> bool:
        """
        Check if SQL matches pattern.

        Args:
            sql: SQL query
            pattern: Pattern with * wildcard

        Returns:
            True if matches
        """
        if pattern == "*":
            return True

        # Simple wildcard matching
        pattern_parts = pattern.split("*")
        pos = 0

        for part in pattern_parts:
            if not part:
                continue

            idx = sql.find(part, pos)
            if idx == -1:
                return False

            pos = idx + len(part)

        return True

    def _update_size_metric(self) -> None:
        """Update cache size metric."""
        total_size = sum(
            f.stat().st_size
            for f in self.cache_dir.glob("*")
            if f.is_file()
        )
        cache_size_bytes.labels(cache_type="query").set(total_size)

    def get_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.

        Returns:
            Dict with stats (entries, size, oldest, newest)
        """
        meta_files = list(self.cache_dir.glob("*.meta"))

        if not meta_files:
            return {
                "entries": 0,
                "size_bytes": 0,
                "size_mb": 0,
            }

        # Get sizes
        total_size = sum(f.stat().st_size for f in self.cache_dir.glob("*"))

        # Get timestamps
        timestamps = []
        for meta_path in meta_files:
            with open(meta_path, "r") as f:
                meta = json.load(f)
            timestamps.append(datetime.fromisoformat(meta["created_at"]))

        return {
            "entries": len(meta_files),
            "size_bytes": total_size,
            "size_mb": round(total_size / 1024 / 1024, 2),
            "oldest": min(timestamps).isoformat() if timestamps else None,
            "newest": max(timestamps).isoformat() if timestamps else None,
        }


# Global cache instance
_cache: Optional[QueryCache] = None


def get_cache() -> QueryCache:
    """
    Get global cache instance.

    Returns:
        QueryCache instance
    """
    global _cache

    if _cache is None:
        project_root = Path(__file__).parent.parent.parent
        cache_dir = project_root / "cache" / "queries"
        _cache = QueryCache(cache_dir)

    return _cache


def cached_query(
    sql: str, params: Optional[Dict[str, Any]] = None, ttl_seconds: int = 3600
) -> Optional["pa.Table"]:
    """
    Execute query with caching.

    Args:
        sql: SQL query
        params: Query parameters
        ttl_seconds: Cache TTL

    Returns:
        Cached result or None (caller should execute query)
    """
    cache = get_cache()
    return cache.get(sql, params)


def cache_result(
    sql: str,
    table: "pa.Table",
    params: Optional[Dict[str, Any]] = None,
    ttl_seconds: int = 3600,
) -> None:
    """
    Cache query result.

    Args:
        sql: SQL query
        table: Result table
        params: Query parameters
        ttl_seconds: Cache TTL
    """
    cache = get_cache()
    cache.set(sql, table, params, ttl_seconds)


def invalidate_cache(pattern: str = "*") -> int:
    """
    Invalidate cache entries.

    Args:
        pattern: SQL pattern

    Returns:
        Number invalidated
    """
    cache = get_cache()
    return cache.invalidate(pattern)
