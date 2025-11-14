"""
Backward compatibility shim for CLI module.

This module has been refactored into a package at orchestrator/cli/.
This shim maintains backward compatibility for existing imports.

Original module location: src/orchestrator/cli.py
New package location: src/orchestrator/cli/

Migration complete: Phase 4.1 - Module Splitting
"""

# Import from new location
from .cli import app

# Re-export for backward compatibility
__all__ = ["app"]

if __name__ == "__main__":
    app()
