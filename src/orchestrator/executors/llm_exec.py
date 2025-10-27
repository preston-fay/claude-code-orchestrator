"""LLM executor for Claude/GPT-based agents."""

import time
import json
import os
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
    Execute an LLM-based agent using Claude API.

    Supports three modes:
    1. In-session mode: Prints instructions for Claude Code to execute in current session
    2. Real mode: If ANTHROPIC_API_KEY is set, calls Claude API
    3. Stub mode: Falls back to simulated response if no API key

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

    # Check execution mode (env var takes precedence over config)
    execution_mode = os.getenv("ORCHESTRATOR_EXECUTION_MODE")
    if not execution_mode:
        # Load from config if available
        config_path = project_root / ".claude" / "config.yaml"
        if config_path.exists():
            import yaml
            with open(config_path) as f:
                config = yaml.safe_load(f)
                execution_mode = config.get("orchestrator", {}).get("execution_mode", "in_session")
        else:
            execution_mode = "in_session"

    if execution_mode == "in_session":
        # In-session mode: Print instructions for Claude Code
        response = _print_in_session_instructions(
            prompt=prompt,
            agent_name=agent_name,
            phase_name=phase_name,
            prompt_file=prompt_file,
            project_root=project_root,
        )
        executor_type = "in_session"
        # Exit code 2 signals "awaiting human validation"
        exit_code = 2
    else:
        # Check for API key
        api_key = os.getenv("ANTHROPIC_API_KEY")

        if api_key:
            # Real mode: Call Claude API
            try:
                response = await _call_claude_api(
                    prompt=prompt,
                    agent_name=agent_name,
                    phase_name=phase_name,
                    api_key=api_key,
                    timeout_seconds=timeout_seconds,
                )
                executor_type = "llm_api"
            except Exception as e:
                # Fallback to stub if API call fails
                response = _simulate_llm_response(agent_name, phase_name, error=str(e))
                executor_type = "llm_stub_fallback"
        else:
            # Stub mode: Simulate response
            response = _simulate_llm_response(agent_name, phase_name)
            executor_type = "llm_stub"

        exit_code = 0

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
        exit_code=exit_code,
        artifacts=artifacts,
        duration_s=duration,
        metadata={
            "agent": agent_name,
            "phase": phase_name,
            "prompt_file": str(prompt_file),
            "response_file": str(response_file),
            "executor": executor_type,
        },
    )


def _print_in_session_instructions(
    prompt: str,
    agent_name: str,
    phase_name: str,
    prompt_file: Path,
    project_root: Path,
) -> str:
    """
    Print agent instructions to console for Claude Code to execute in current session.

    Returns the printed instructions as a string for logging.
    """
    # Load required artifacts from config
    config_path = project_root / ".claude" / "config.yaml"
    required_artifacts = []

    if config_path.exists():
        import yaml
        with open(config_path) as f:
            config = yaml.safe_load(f)
            subagents = config.get("subagents", {})
            agent_config = subagents.get(agent_name, {})
            required_artifacts = agent_config.get("checkpoint_artifacts", [])

    # Build output
    output = []
    output.append("\n" + "="*80)
    output.append(f"🎯 PHASE READY: {phase_name.upper()} - {agent_name.upper()} AGENT")
    output.append("="*80 + "\n")

    output.append("📋 AGENT INSTRUCTIONS:\n")
    output.append(prompt)
    output.append("\n" + "-"*80 + "\n")

    if required_artifacts:
        output.append("✅ REQUIRED ARTIFACTS:\n")
        for artifact in required_artifacts:
            output.append(f"  - {artifact}")
        output.append("\n" + "-"*80 + "\n")

    output.append("="*80)
    output.append("⏸️  ORCHESTRATOR PAUSED - AWAITING COMPLETION")
    output.append("="*80 + "\n")
    output.append("🤖 Claude Code: Execute the instructions above in this session.")
    output.append(f"📝 Full prompt saved to: {prompt_file}")
    output.append("\n👤 When work is complete, run: orchestrator run checkpoint\n")

    # Print to console
    message = "\n".join(output)
    print(message)

    return message


async def _call_claude_api(
    prompt: str,
    agent_name: str,
    phase_name: str,
    api_key: str,
    timeout_seconds: float,
) -> str:
    """
    Call Anthropic Claude API for agent execution.

    Args:
        prompt: Agent prompt
        agent_name: Name of agent
        phase_name: Current phase
        api_key: Anthropic API key
        timeout_seconds: Timeout in seconds

    Returns:
        Claude's response text
    """
    try:
        import anthropic
    except ImportError:
        raise ImportError(
            "anthropic package not installed. "
            "Install with: pip install anthropic>=0.40.0"
        )

    client = anthropic.Anthropic(api_key=api_key)

    # Call Claude API with timeout
    try:
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=8000,
            temperature=0.7,
            messages=[
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
            timeout=timeout_seconds,
        )

        # Extract text from response
        response_text = response.content[0].text

        # Add metadata footer
        metadata = f"\n\n---\n*Generated by {agent_name} agent via Claude API*\n"
        metadata += f"*Model: {response.model}*\n"
        metadata += f"*Tokens: {response.usage.input_tokens} in, {response.usage.output_tokens} out*\n"

        return response_text + metadata

    except anthropic.APITimeoutError:
        raise TimeoutError(f"Claude API call timed out after {timeout_seconds}s")
    except anthropic.APIError as e:
        raise RuntimeError(f"Claude API error: {str(e)}")


def _simulate_llm_response(agent_name: str, phase_name: str, error: str = None) -> str:
    """
    Simulate an LLM response (fallback when API key not available or API fails).

    Args:
        agent_name: Name of the agent
        phase_name: Current phase
        error: Optional error message if this is a fallback

    Returns:
        Simulated agent response
    """
    warning = ""
    if error:
        warning = f"\n⚠️  **FALLBACK MODE**: API call failed ({error}). Using simulated response.\n\n"
    else:
        warning = "\n⚠️  **STUB MODE**: No ANTHROPIC_API_KEY found. Using simulated response.\n"
        warning += "Set ANTHROPIC_API_KEY environment variable to enable real Claude API calls.\n\n"

    return f"""# {agent_name.capitalize()} Agent Response
{warning}
Phase: {phase_name}

## Summary

I have completed the {phase_name} phase tasks for the {agent_name} agent.

## Artifacts Produced

ARTIFACT: docs/architecture.md
ARTIFACT: docs/technical_spec.md

## Next Steps

The phase is complete and ready for review.

---
*This is a simulated response. To enable real AI agent execution:*
1. Get an API key from https://console.anthropic.com/settings/keys
2. Export it: `export ANTHROPIC_API_KEY="sk-ant-..."`
3. Restart the orchestrator run
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
