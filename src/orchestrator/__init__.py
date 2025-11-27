"""Claude Code Orchestrator - DEPRECATED.

This module (src/orchestrator) is deprecated and will be removed in a future version.
Please use orchestrator_v2 instead.

Migration guide:
- Import from orchestrator_v2 instead of src.orchestrator
- Use the V2 API server: uvicorn orchestrator_v2.api.server:app
- See docs/MIGRATION.md for full migration guide
"""

import warnings

__version__ = "0.1.0"
__deprecated__ = True

warnings.warn(
    "src.orchestrator is deprecated and will be removed in v3.0.0. "
    "Use orchestrator_v2 instead. See docs/MIGRATION.md for migration guide.",
    DeprecationWarning,
    stacklevel=2,
)
