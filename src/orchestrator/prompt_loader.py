"""Utilities for loading and interpolating subagent prompt templates."""

from pathlib import Path
from typing import Dict, Any, Optional
import re


def load_prompt_template(agent_name: str, project_root: Optional[Path] = None) -> str:
    """
    Load a subagent's prompt template from subagent_prompts/.

    Args:
        agent_name: Name of the agent (e.g., "architect", "data")
        project_root: Root directory of the project (defaults to current working directory)

    Returns:
        Raw template content

    Raises:
        FileNotFoundError: If template doesn't exist
    """
    if project_root is None:
        project_root = Path.cwd()

    template_path = project_root / "subagent_prompts" / f"{agent_name}.md"

    if not template_path.exists():
        raise FileNotFoundError(f"Prompt template not found: {template_path}")

    with open(template_path) as f:
        return f.read()


def interpolate_prompt(template: str, context: Dict[str, Any]) -> str:
    """
    Interpolate context variables into a prompt template.

    Supports simple {{variable}} syntax.

    Args:
        template: Raw template string with {{placeholders}}
        context: Dictionary of values to interpolate

    Returns:
        Interpolated prompt string

    Examples:
        >>> template = "Project: {{project_name}}"
        >>> interpolate_prompt(template, {"project_name": "MyApp"})
        'Project: MyApp'
    """
    result = template

    # Replace {{variable}} patterns
    for key, value in context.items():
        pattern = r'\{\{' + re.escape(key) + r'\}\}'
        # Convert value to string, handle None
        str_value = str(value) if value is not None else ""
        result = re.sub(pattern, str_value, result)

    return result


def build_agent_context(
    project_root: Path,
    phase: str,
    agent: str,
    intake_summary: Optional[Dict[str, Any]] = None,
    last_artifacts: Optional[Dict[str, Any]] = None,
    entrypoints: Optional[Dict[str, str]] = None,
    checkpoint_policy: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Build context dictionary for agent prompt interpolation.

    Args:
        project_root: Project root path
        phase: Current phase name
        agent: Agent name
        intake_summary: Optional intake configuration summary
        last_artifacts: Optional artifacts from previous phases
        entrypoints: Optional entrypoint commands for this agent
        checkpoint_policy: Optional checkpoint validation policy

    Returns:
        Context dictionary ready for interpolation
    """
    context = {
        "project_root": str(project_root),
        "phase": phase,
        "agent": agent,
        "intake_summary": _format_intake_summary(intake_summary) if intake_summary else "N/A",
        "last_artifacts": _format_artifacts(last_artifacts) if last_artifacts else "N/A",
        "entrypoints": _format_entrypoints(entrypoints) if entrypoints else "N/A",
        "checkpoint_policy": checkpoint_policy or "Standard validation",
    }

    # Add individual intake fields if available
    if intake_summary:
        context["project_name"] = intake_summary.get("project_name", "N/A")
        context["project_type"] = intake_summary.get("project_type", "N/A")
        context["description"] = intake_summary.get("description", "N/A")

    return context


def _format_intake_summary(intake: Dict[str, Any]) -> str:
    """Format intake summary for prompt context."""
    lines = ["Project Intake:"]

    if "project_name" in intake:
        lines.append(f"  - Name: {intake['project_name']}")
    if "project_type" in intake:
        lines.append(f"  - Type: {intake['project_type']}")
    if "description" in intake:
        lines.append(f"  - Description: {intake['description']}")
    if "requirements" in intake:
        lines.append(f"  - Requirements: {len(intake['requirements'])} items")

    return "\n".join(lines)


def _format_artifacts(artifacts: Dict[str, Any]) -> str:
    """Format artifacts dictionary for prompt context."""
    if not artifacts:
        return "No previous artifacts"

    lines = ["Previous Artifacts:"]
    for phase, items in artifacts.items():
        if items:
            lines.append(f"  - {phase}: {len(items)} file(s)")
            for item in items[:3]:  # Show first 3
                lines.append(f"    • {item}")
            if len(items) > 3:
                lines.append(f"    ... and {len(items) - 3} more")

    return "\n".join(lines)


def _format_entrypoints(entrypoints: Dict[str, str]) -> str:
    """Format entrypoints dictionary for prompt context."""
    if not entrypoints:
        return "No entrypoints defined"

    lines = ["Available Entrypoints:"]
    for name, command in entrypoints.items():
        lines.append(f"  - {name}: {command}")

    return "\n".join(lines)


def load_and_interpolate(
    agent_name: str,
    context: Dict[str, Any],
    project_root: Optional[Path] = None,
) -> str:
    """
    Convenience function to load template and interpolate in one call.

    Args:
        agent_name: Name of the agent
        context: Context dictionary for interpolation
        project_root: Optional project root (defaults to cwd)

    Returns:
        Fully interpolated prompt ready for agent execution
    """
    template = load_prompt_template(agent_name, project_root)
    return interpolate_prompt(template, context)
