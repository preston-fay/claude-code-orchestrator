"""
Backward compatibility shim for runloop module.

This module has been refactored into a package at orchestrator/runloop/.
This shim maintains backward compatibility for existing imports.

Original module location: src/orchestrator/runloop.py
New package location: src/orchestrator/runloop/

Migration complete: Phase 4.1 - Module Splitting
"""

# Import from new location
from .runloop import Orchestrator

# Re-export for backward compatibility
__all__ = ["Orchestrator"]
