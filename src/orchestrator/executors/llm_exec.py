"""LLM executor for Claude/GPT-based agents."""

import time
import json
from pathlib import Path
from typing import Dict, Any

from .types import AgentExecResult


async def execute_llm(
    prompt: str,
    agent_name: str,
    phase_name: str,
    project_root: Path,
    timeout_seconds: float = 1800,
) -> AgentExecResult:
    """
    Execute an LLM-based agent.

    For now, this is a stub that writes the prompt to an output file
    and returns a simulated success. In production, this would:
    - Send prompt to Claude API or local Claude Code session
    - Parse structured output for artifacts
    - Handle streaming responses
    - Manage token limits

    Args:
        prompt: Interpolated agent prompt
        agent_name: Name of the agent
        phase_name: Current phase
        project_root: Project root directory
        timeout_seconds: Maximum execution time

    Returns:
        AgentExecResult with agent output
    """
    start_time = time.time()

    # Create output directory
    output_dir = project_root / ".claude" / "agent_outputs" / agent_name / phase_name
    output_dir.mkdir(parents=True, exist_ok=True)

    # Write prompt to file (for debugging/review)
    prompt_file = output_dir / "prompt.md"
    with open(prompt_file, "w") as f:
        f.write(prompt)

    # Simulate LLM execution
    # In production, this would call Claude API or subprocess to Claude Code
    response = _simulate_llm_response(agent_name, phase_name)

    # Write response
    response_file = output_dir / "response.md"
    with open(response_file, "w") as f:
        f.write(response)

    # Parse artifacts from response
    artifacts = _parse_llm_artifacts(response, project_root)

    duration = time.time() - start_time

    return AgentExecResult(
        stdout=response,
        stderr="",
        exit_code=0,
        artifacts=artifacts,
        duration_s=duration,
        metadata={
            "agent": agent_name,
            "phase": phase_name,
            "prompt_file": str(prompt_file),
            "response_file": str(response_file),
            "executor": "llm_stub",
        },
    )


def _simulate_llm_response(agent_name: str, phase_name: str) -> str:
    """
    Simulate an LLM response.

    In production, replace with actual API call.
    """
    return f"""# {agent_name.capitalize()} Agent Response

Phase: {phase_name}

## Summary

I have completed the {phase_name} phase tasks for the {agent_name} agent.

## Artifacts Produced

ARTIFACT: docs/architecture.md
ARTIFACT: docs/technical_spec.md

## Next Steps

The phase is complete and ready for review.
"""


def _parse_llm_artifacts(response: str, project_root: Path) -> list:
    """
    Parse artifact declarations from LLM response.

    Looks for:
    - ARTIFACT: path/to/file
    - JSON blocks with artifact lists
    """
    artifacts = []

    # Parse ARTIFACT: lines
    for line in response.split("\n"):
        line = line.strip()

        if line.startswith("ARTIFACT:"):
            artifact = line.replace("ARTIFACT:", "").strip()
            # Normalize to relative path
            if artifact.startswith(str(project_root)):
                artifact = Path(artifact).relative_to(project_root)
            artifacts.append(str(artifact))

    # Could also parse JSON blocks with schema like:
    # ```json
    # {"artifacts": ["file1.py", "file2.py"]}
    # ```

    return artifacts
