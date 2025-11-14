"""Tests for context cache functionality."""

import pytest
from src.orchestrator.swarm.context_cache import ContextCache, CacheEntry


def test_cache_basic_operations():
    """Test basic cache get/set operations."""
    cache = ContextCache()

    # Set and get
    cache.set("key1", "value1")
    assert cache.get("key1") == "value1"

    # Get non-existent key
    assert cache.get("nonexistent") == None

    # Check contains
    assert "key1" in cache
    assert "nonexistent" not in cache


def test_cache_get_or_compute():
    """Test get_or_compute method."""
    cache = ContextCache()
    call_count = 0

    def expensive_fn():
        nonlocal call_count
        call_count += 1
        return f"result_{call_count}"

    # First call should compute
    result1 = cache.get_or_compute("compute_key", expensive_fn)
    assert result1 == "result_1"
    assert call_count == 1

    # Second call should use cache
    result2 = cache.get_or_compute("compute_key", expensive_fn)
    assert result2 == "result_1"  # Same result
    assert call_count == 1  # Not called again

    # Different key should compute again
    result3 = cache.get_or_compute("different_key", expensive_fn)
    assert result3 == "result_2"
    assert call_count == 2


def test_cache_stats():
    """Test cache statistics tracking."""
    cache = ContextCache()

    # Initial stats
    stats = cache.get_stats()
    assert stats["size"] == 0
    assert stats["hits"] == 0
    assert stats["misses"] == 0
    assert stats["hit_rate"] == 0.0

    # Add some entries
    cache.set("key1", "value1")
    cache.set("key2", "value2")

    # Trigger hits
    cache.get("key1")
    cache.get("key1")
    cache.get("key2")

    # Trigger misses
    cache.get("nonexistent1")
    cache.get("nonexistent2")

    stats = cache.get_stats()
    assert stats["size"] == 2
    assert stats["hits"] == 3
    assert stats["misses"] == 2
    assert stats["hit_rate"] == 3 / 5  # 3 hits out of 5 total requests


def test_cache_clear():
    """Test cache clearing."""
    cache = ContextCache()

    cache.set("key1", "value1")
    cache.set("key2", "value2")
    cache.get("key1")

    assert len(cache) == 2
    assert cache.get_stats()["hits"] == 1

    cache.clear()

    assert len(cache) == 0
    assert cache.get_stats()["hits"] == 0
    assert cache.get("key1") == None


def test_cache_hash_consistency():
    """Test that hashing is consistent for same inputs."""
    cache = ContextCache()

    # String keys
    cache.set("test", "value1")
    assert cache.get("test") == "value1"

    # Dict keys (should hash consistently)
    cache.set({"a": 1, "b": 2}, "dict_value")
    assert cache.get({"a": 1, "b": 2}) == "dict_value"
    assert cache.get({"b": 2, "a": 1}) == "dict_value"  # Order shouldn't matter

    # List keys
    cache.set([1, 2, 3], "list_value")
    assert cache.get([1, 2, 3]) == "list_value"


def test_cache_complex_values():
    """Test caching complex value types."""
    cache = ContextCache()

    # Dict value
    cache.set("dict_key", {"nested": {"data": [1, 2, 3]}})
    result = cache.get("dict_key")
    assert result == {"nested": {"data": [1, 2, 3]}}

    # List value
    cache.set("list_key", [{"a": 1}, {"b": 2}])
    result = cache.get("list_key")
    assert result == [{"a": 1}, {"b": 2}]

    # Object value
    class CustomObj:
        def __init__(self, x):
            self.x = x

    obj = CustomObj(42)
    cache.set("obj_key", obj)
    result = cache.get("obj_key")
    assert result.x == 42


def test_cache_hit_count():
    """Test that hit count is tracked correctly."""
    cache = ContextCache()

    cache.set("key1", "value1")

    # Multiple hits
    for _ in range(5):
        cache.get("key1")

    stats = cache.get_stats()
    assert stats["hits"] == 5


def test_cache_prevents_duplicate_computation():
    """Test that cache prevents duplicate expensive computations."""
    cache = ContextCache()
    computations = []

    def expensive_computation():
        result = sum(range(1000))
        computations.append(result)
        return result

    # First call computes
    result1 = cache.get_or_compute("expensive", expensive_computation)
    assert len(computations) == 1

    # Subsequent calls use cache
    for _ in range(10):
        result = cache.get_or_compute("expensive", expensive_computation)
        assert result == result1

    # Should still only have one computation
    assert len(computations) == 1
