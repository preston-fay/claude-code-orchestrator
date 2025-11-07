"""
Metrics collection and tracking for Claude Code Orchestrator.

This package provides:
- Runtime metrics tracking (metrics.py - existing)
- DORA metrics calculation (dora_metrics.py)
- GitHub collaboration metrics (github_metrics.py)
- AI review impact metrics (ai_review_impact.py)
- Contribution analysis (contribution_analyzer.py)
- Metrics aggregation and trending (aggregator.py)
"""

from pathlib import Path

# Import existing metrics classes for backward compatibility
try:
    from .metrics import MetricsTracker, PhaseMetrics, RunMetrics
except ImportError:
    # Gracefully handle if metrics.py doesn't exist yet
    pass

__all__ = [
    "MetricsTracker",
    "PhaseMetrics",
    "RunMetrics",
]

__version__ = "1.0.0"
