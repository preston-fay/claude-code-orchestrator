"""Orchestrator CLI module.

Split into logical submodules for maintainability:
- main: Main app setup and top-level commands (status, triggers, version, quickstart)
- commands_run: Run workflow commands (start, next, approve, reject, etc.)
- commands_release: Release management commands (prepare, cut, verify, rollback)
"""

from .main import app

__all__ = ["app"]
