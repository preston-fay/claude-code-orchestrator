"""MCP (Model Context Protocol) - Filesystem Registry for Code Execution.

This package provides importable APIs for data loading, analytics, modeling, and visualization.
These APIs are designed to be used by generated code in the sandboxed code executor.

Architecture:
- Each module is a pure, side-effect-free function (where possible)
- All APIs use clear typing and docstrings
- Outputs are written to well-known paths (data/processed/, reports/)
- Optional dependencies are soft-imported with helpful error messages

Usage:
    from orchestrator.mcp.data import load_csv
    from orchestrator.mcp.analytics import describe_data
    from orchestrator.mcp.viz import plot_distribution
"""

__version__ = "0.1.0"

# Subpackages are imported on-demand to avoid loading heavy dependencies
__all__ = ["data", "analytics", "models", "viz"]
