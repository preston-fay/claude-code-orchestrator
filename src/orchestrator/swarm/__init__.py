"""Swarm orchestration for parallel agent execution.

This module provides dependency-aware parallel execution of agents with:
- Topological sorting to identify independent execution groups
- Concurrent execution within groups
- Context caching to avoid redundant computation
- Deterministic result ordering
"""

from .core import SwarmOrchestrator, PhaseOutcome
from .context_cache import ContextCache, CacheEntry

__all__ = ["SwarmOrchestrator", "PhaseOutcome", "ContextCache", "CacheEntry"]
