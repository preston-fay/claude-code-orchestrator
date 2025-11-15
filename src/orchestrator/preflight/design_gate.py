"""Design system preflight gate - ensures KDS selection before orchestrator run."""

from dataclasses import dataclass
from typing import Optional, Dict, Any
import os
import logging

logger = logging.getLogger(__name__)


@dataclass
class DesignSelection:
    """Design system selection result."""

    system: str  # "kearney" or "client:<slug>"
    overrides: Optional[Dict[str, Any]] = None


PROMPT_JSON = """\
Select a design system for this deliverable.

1) "kearney" (recommended) — standard Kearney branding (accessible, default)
2) "client:<slug>" — provide overrides

Reply strictly in JSON, e.g.:
{
  "system": "kearney" | "client:<slug>",
  "overrides": {
    "client_name": "ACME",
    "logo_url": "https://...",
    "colors": {"primary":"#005EB8","secondary":"#FFC72C"},
    "fonts": {"headline":"Inter","body":"Inter"},
    "wcag_target": "AA"
  }
}
"""


def ensure_design_selection(config: Dict[str, Any], env: Optional[Dict[str, str]] = None) -> DesignSelection:
    """
    Ensure design system is selected before orchestrator run.

    This is a mandatory preflight check. The orchestrator will not proceed
    without a design system selection.

    Args:
        config: Orchestrator configuration dictionary
        env: Environment variables (defaults to os.environ)

    Returns:
        DesignSelection with system and optional overrides

    Raises:
        RuntimeError: If design system selection is invalid or missing
    """
    if env is None:
        env = dict(os.environ)

    # Check config first
    sel = (config.get("design_system") or "").strip().lower()

    # Fall back to environment variable
    if not sel:
        sel = (env.get("DESIGN_SYSTEM") or "").strip().lower()

    # If found in config/env, validate it
    if sel:
        if sel == "kearney":
            logger.info("Design system: kearney (from config/env)")
            return DesignSelection(system="kearney", overrides=None)

        if sel.startswith("client:"):
            logger.info(f"Design system: {sel} (from config/env)")
            overrides = config.get("design_overrides") or {}
            return DesignSelection(system=sel, overrides=overrides)

        raise RuntimeError(
            f"Invalid 'design_system' value: '{sel}'. "
            "Must be 'kearney' or 'client:<slug>'."
        )

    # If not found, this is a hard stop - design system is mandatory
    raise RuntimeError(
        "Design system selection is required before generation.\n\n"
        "Please set one of the following:\n"
        "  1. In .claude/config.yaml: design_system: 'kearney'\n"
        "  2. In environment: export DESIGN_SYSTEM='kearney'\n"
        "  3. Via CLI flag: --design-system kearney\n\n"
        f"{PROMPT_JSON}"
    )
