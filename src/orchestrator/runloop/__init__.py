"""Orchestrator run-loop module.

Split into logical submodules for maintainability:
- core: Main Orchestrator class with state machine
- detectors: Auto-detection logic for specialized agents
- transitions: Phase navigation and consensus logic
- utils: Shared helper functions
"""

from .core import Orchestrator

__all__ = ["Orchestrator"]
