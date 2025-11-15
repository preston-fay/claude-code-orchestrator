"""Orchestrator preflight checks and gates."""

from .design_gate import ensure_design_selection, DesignSelection

__all__ = ["ensure_design_selection", "DesignSelection"]
