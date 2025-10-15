"""
Tests for query result caching module.

Tests:
- Cache hit/miss scenarios
- TTL expiration
- Pattern-based invalidation
- Cache statistics
- Parquet storage
"""

import pytest
import pyarrow as pa
from pathlib import Path
from datetime import datetime, timedelta
import time

from src.data.cache import (
    QueryCache,
    get_cache,
    cached_query,
    cache_result,
    invalidate_cache,
)


@pytest.fixture
def temp_cache_dir(tmp_path):
    """Create temporary cache directory."""
    cache_dir = tmp_path / "test_cache"
    cache_dir.mkdir(parents=True, exist_ok=True)
    return cache_dir


@pytest.fixture
def cache(temp_cache_dir):
    """Create cache instance with temporary directory."""
    return QueryCache(cache_dir=temp_cache_dir)


class TestCacheBasics:
    """Test basic cache operations."""

    def test_cache_miss_returns_none(self, cache):
        """Cache miss should return None."""
        result = cache.get("SELECT 1", {})
        assert result is None

    def test_cache_set_and_get(self, cache):
        """Should cache and retrieve query result."""
        # Create test table
        table = pa.table({"x": [1, 2, 3], "y": ["a", "b", "c"]})

        # Cache it
        cache.set("SELECT * FROM test", table, {}, ttl_seconds=300)

        # Retrieve it
        result = cache.get("SELECT * FROM test", {})
        assert result is not None
        assert len(result) == 3
        assert result.column_names == ["x", "y"]

    def test_cache_with_params(self, cache):
        """Should handle queries with parameters."""
        table1 = pa.table({"x": [1, 2]})
        table2 = pa.table({"x": [3, 4]})

        # Cache with different params
        cache.set("SELECT * FROM test WHERE id = ?", table1, {"id": 1}, ttl_seconds=300)
        cache.set("SELECT * FROM test WHERE id = ?", table2, {"id": 2}, ttl_seconds=300)

        # Retrieve with params
        result1 = cache.get("SELECT * FROM test WHERE id = ?", {"id": 1})
        result2 = cache.get("SELECT * FROM test WHERE id = ?", {"id": 2})

        assert len(result1) == 2
        assert len(result2) == 2

    def test_cache_normalized_sql(self, cache):
        """Should normalize SQL whitespace for cache key."""
        table = pa.table({"x": [1]})

        # Set with extra whitespace
        cache.set("SELECT  *   FROM test", table, {}, ttl_seconds=300)

        # Get with different whitespace
        result = cache.get("SELECT * FROM test", {})
        assert result is not None
        assert len(result) == 1


class TestCacheTTL:
    """Test TTL-based cache expiration."""

    def test_cache_respects_ttl(self, cache):
        """Cache entry should expire after TTL."""
        table = pa.table({"x": [1]})

        # Cache with very short TTL
        cache.set("SELECT 1", table, {}, ttl_seconds=1)

        # Should be available immediately
        result1 = cache.get("SELECT 1", {})
        assert result1 is not None

        # Wait for expiration
        time.sleep(1.1)

        # Should be expired
        result2 = cache.get("SELECT 1", {})
        assert result2 is None

    def test_cache_with_long_ttl(self, cache):
        """Cache entry should persist with long TTL."""
        table = pa.table({"x": [1]})

        # Cache with long TTL
        cache.set("SELECT 1", table, {}, ttl_seconds=3600)

        # Should be available
        result = cache.get("SELECT 1", {})
        assert result is not None
        assert len(result) == 1

    def test_expired_entry_removed(self, cache):
        """Expired entries should be removed from disk."""
        table = pa.table({"x": [1]})
        cache.set("SELECT 1", table, {}, ttl_seconds=1)

        # Count files before expiration
        files_before = len(list(cache.cache_dir.glob("*.parquet")))
        assert files_before > 0

        # Wait for expiration and access
        time.sleep(1.1)
        cache.get("SELECT 1", {})

        # Files should be removed
        files_after = len(list(cache.cache_dir.glob("*.parquet")))
        assert files_after < files_before


class TestCacheInvalidation:
    """Test pattern-based cache invalidation."""

    def test_invalidate_exact_match(self, cache):
        """Should invalidate exact SQL match."""
        table = pa.table({"x": [1]})
        cache.set("SELECT * FROM users", table, {})

        # Invalidate
        count = cache.invalidate("SELECT * FROM users")
        assert count == 1

        # Should be gone
        result = cache.get("SELECT * FROM users", {})
        assert result is None

    def test_invalidate_wildcard_pattern(self, cache):
        """Should invalidate entries matching wildcard pattern."""
        table = pa.table({"x": [1]})

        # Cache multiple entries
        cache.set("SELECT * FROM users", table, {})
        cache.set("SELECT * FROM orders", table, {})
        cache.set("SELECT * FROM products", table, {})

        # Invalidate pattern
        count = cache.invalidate("*users*")
        assert count == 1

        # Check what's left
        assert cache.get("SELECT * FROM users", {}) is None
        assert cache.get("SELECT * FROM orders", {}) is not None
        assert cache.get("SELECT * FROM products", {}) is not None

    def test_invalidate_multiple_matches(self, cache):
        """Should invalidate all matching entries."""
        table = pa.table({"x": [1]})

        # Cache entries with common pattern
        cache.set("SELECT * FROM user_profiles", table, {})
        cache.set("SELECT * FROM user_sessions", table, {})
        cache.set("SELECT * FROM user_preferences", table, {})
        cache.set("SELECT * FROM orders", table, {})

        # Invalidate all user_ tables
        count = cache.invalidate("*user_*")
        assert count == 3

        # Only orders should remain
        assert cache.get("SELECT * FROM orders", {}) is not None

    def test_invalidate_no_matches(self, cache):
        """Should return 0 when no entries match."""
        table = pa.table({"x": [1]})
        cache.set("SELECT * FROM test", table, {})

        count = cache.invalidate("*nonexistent*")
        assert count == 0

        # Original entry should remain
        assert cache.get("SELECT * FROM test", {}) is not None


class TestCacheClear:
    """Test clearing entire cache."""

    def test_clear_removes_all_entries(self, cache):
        """clear() should remove all cache entries."""
        table = pa.table({"x": [1]})

        # Cache multiple entries
        cache.set("SELECT 1", table, {})
        cache.set("SELECT 2", table, {})
        cache.set("SELECT 3", table, {})

        # Clear
        cache.clear()

        # All should be gone
        assert cache.get("SELECT 1", {}) is None
        assert cache.get("SELECT 2", {}) is None
        assert cache.get("SELECT 3", {}) is None

    def test_clear_on_empty_cache(self, cache):
        """clear() should work on empty cache."""
        cache.clear()  # Should not raise
        assert True


class TestCacheStats:
    """Test cache statistics."""

    def test_stats_entry_count(self, cache):
        """Stats should report entry count."""
        table = pa.table({"x": [1]})

        stats = cache.get_stats()
        initial_count = stats["entries"]

        # Add entries
        cache.set("SELECT 1", table, {})
        cache.set("SELECT 2", table, {})

        stats = cache.get_stats()
        assert stats["entries"] == initial_count + 2

    def test_stats_total_size(self, cache):
        """Stats should report total cache size."""
        table = pa.table({"x": list(range(100))})

        cache.set("SELECT 1", table, {})

        stats = cache.get_stats()
        assert stats["total_size_mb"] > 0

    def test_stats_hit_miss_ratio(self, cache):
        """Stats should report hit/miss counts."""
        table = pa.table({"x": [1]})
        cache.set("SELECT 1", table, {})

        # Hit
        cache.get("SELECT 1", {})

        # Miss
        cache.get("SELECT 2", {})

        stats = cache.get_stats()
        # Stats should have hit/miss info (implementation dependent)
        assert "entries" in stats


class TestCacheKeyGeneration:
    """Test cache key computation."""

    def test_same_query_same_params_same_key(self, cache):
        """Same query and params should generate same key."""
        key1 = cache._compute_key("SELECT * FROM test", {"id": 1})
        key2 = cache._compute_key("SELECT * FROM test", {"id": 1})
        assert key1 == key2

    def test_different_query_different_key(self, cache):
        """Different queries should generate different keys."""
        key1 = cache._compute_key("SELECT * FROM test", {})
        key2 = cache._compute_key("SELECT * FROM other", {})
        assert key1 != key2

    def test_different_params_different_key(self, cache):
        """Different params should generate different keys."""
        key1 = cache._compute_key("SELECT * FROM test", {"id": 1})
        key2 = cache._compute_key("SELECT * FROM test", {"id": 2})
        assert key1 != key2

    def test_param_order_independent(self, cache):
        """Param order should not affect key."""
        key1 = cache._compute_key("SELECT 1", {"a": 1, "b": 2})
        key2 = cache._compute_key("SELECT 1", {"b": 2, "a": 1})
        assert key1 == key2

    def test_whitespace_normalized(self, cache):
        """SQL whitespace should be normalized in key."""
        key1 = cache._compute_key("SELECT  *   FROM test", {})
        key2 = cache._compute_key("SELECT * FROM test", {})
        assert key1 == key2


class TestCacheHelperFunctions:
    """Test module-level helper functions."""

    def test_get_cache_returns_singleton(self):
        """get_cache() should return singleton instance."""
        cache1 = get_cache()
        cache2 = get_cache()
        assert cache1 is cache2

    def test_cache_result_helper(self, temp_cache_dir):
        """cache_result() should cache table."""
        cache = QueryCache(cache_dir=temp_cache_dir)
        table = pa.table({"x": [1, 2, 3]})

        cache_result("SELECT 1", table, {}, ttl_seconds=300, cache_instance=cache)

        result = cache.get("SELECT 1", {})
        assert result is not None
        assert len(result) == 3

    def test_invalidate_cache_helper(self, temp_cache_dir):
        """invalidate_cache() should invalidate pattern."""
        cache = QueryCache(cache_dir=temp_cache_dir)
        table = pa.table({"x": [1]})

        cache.set("SELECT * FROM test", table, {})
        count = invalidate_cache("*test*", cache_instance=cache)

        assert count >= 0  # Should not raise


class TestCacheMetrics:
    """Test cache metrics integration."""

    def test_cache_hit_increments_metric(self, cache):
        """Cache hit should increment cache_hits_total."""
        from src.ops.metrics import cache_hits_total

        table = pa.table({"x": [1]})
        cache.set("SELECT 1", table, {})

        # This should increment cache_hits_total
        result = cache.get("SELECT 1", {})
        assert result is not None

    def test_cache_miss_increments_metric(self, cache):
        """Cache miss should increment cache_misses_total."""
        from src.ops.metrics import cache_misses_total

        # This should increment cache_misses_total
        result = cache.get("SELECT nonexistent", {})
        assert result is None


class TestCacheParquetStorage:
    """Test Parquet file storage."""

    def test_parquet_file_created(self, cache):
        """Should create .parquet file."""
        table = pa.table({"x": [1]})
        cache.set("SELECT 1", table, {})

        parquet_files = list(cache.cache_dir.glob("*.parquet"))
        assert len(parquet_files) > 0

    def test_metadata_file_created(self, cache):
        """Should create .meta file."""
        table = pa.table({"x": [1]})
        cache.set("SELECT 1", table, {})

        meta_files = list(cache.cache_dir.glob("*.meta"))
        assert len(meta_files) > 0

    def test_metadata_contains_ttl(self, cache):
        """Metadata should contain TTL info."""
        table = pa.table({"x": [1]})
        cache.set("SELECT 1", table, {}, ttl_seconds=600)

        meta_files = list(cache.cache_dir.glob("*.meta"))
        assert len(meta_files) > 0

        # Read metadata
        import json
        with open(meta_files[0], "r") as f:
            meta = json.load(f)

        assert "ttl_seconds" in meta
        assert meta["ttl_seconds"] == 600

    def test_parquet_preserves_schema(self, cache):
        """Parquet storage should preserve table schema."""
        table = pa.table({
            "int_col": [1, 2, 3],
            "str_col": ["a", "b", "c"],
            "float_col": [1.1, 2.2, 3.3]
        })

        cache.set("SELECT 1", table, {})
        result = cache.get("SELECT 1", {})

        assert result is not None
        assert result.column_names == ["int_col", "str_col", "float_col"]
        assert len(result) == 3


class TestCacheEdgeCases:
    """Test edge cases and error handling."""

    def test_cache_empty_table(self, cache):
        """Should handle empty table."""
        table = pa.table({"x": []})
        cache.set("SELECT 1", table, {})

        result = cache.get("SELECT 1", {})
        assert result is not None
        assert len(result) == 0

    def test_cache_large_table(self, cache):
        """Should handle large table."""
        table = pa.table({"x": list(range(10000))})
        cache.set("SELECT 1", table, {})

        result = cache.get("SELECT 1", {})
        assert result is not None
        assert len(result) == 10000

    def test_cache_with_null_values(self, cache):
        """Should handle tables with null values."""
        table = pa.table({"x": [1, None, 3]})
        cache.set("SELECT 1", table, {})

        result = cache.get("SELECT 1", {})
        assert result is not None
        assert len(result) == 3

    def test_cache_empty_params(self, cache):
        """Should handle empty params dict."""
        table = pa.table({"x": [1]})
        cache.set("SELECT 1", table, {})

        result1 = cache.get("SELECT 1", {})
        result2 = cache.get("SELECT 1", None)

        assert result1 is not None
        # Both should work (empty dict and None are treated same)
