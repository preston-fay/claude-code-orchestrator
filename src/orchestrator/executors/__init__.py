"""Agent execution adapters."""

from pathlib import Path
from typing import Dict, Any, Callable, Awaitable

from .types import AgentExecResult
from .subprocess_exec import execute_subprocess
from .llm_exec import execute_llm


def get_executor(
    agent_name: str, agent_config: Dict[str, Any]
) -> Callable[..., Awaitable[AgentExecResult]]:
    """
    Get appropriate executor for an agent based on configuration.

    Args:
        agent_name: Name of the agent
        agent_config: Agent configuration from .claude/config.yaml

    Returns:
        Executor function (async callable)

    Selection logic:
    - If agent has entrypoints defined → use subprocess executor
    - Otherwise → use LLM executor
    """
    # Check for entrypoints in config
    entrypoints = agent_config.get("entrypoints", {})

    if entrypoints:
        # Has entrypoints → use subprocess
        return _make_subprocess_executor(entrypoints)
    else:
        # No entrypoints → use LLM
        return _make_llm_executor(agent_name)


def _make_subprocess_executor(
    entrypoints: Dict[str, str]
) -> Callable[..., Awaitable[AgentExecResult]]:
    """Create subprocess executor with entrypoints."""

    async def executor(
        project_root: Path,
        timeout_seconds: float = 1800,
        **kwargs,
    ) -> AgentExecResult:
        # Use first entrypoint (or a default one)
        command = entrypoints.get("default") or list(entrypoints.values())[0]

        return await execute_subprocess(
            command=command,
            working_dir=project_root,
            timeout_seconds=timeout_seconds,
        )

    return executor


def _make_llm_executor(agent_name: str) -> Callable[..., Awaitable[AgentExecResult]]:
    """Create LLM executor for agent."""

    async def executor(
        prompt: str,
        phase_name: str,
        project_root: Path,
        timeout_seconds: float = 1800,
        **kwargs,
    ) -> AgentExecResult:
        return await execute_llm(
            prompt=prompt,
            agent_name=agent_name,
            phase_name=phase_name,
            project_root=project_root,
            timeout_seconds=timeout_seconds,
        )

    return executor


__all__ = [
    "AgentExecResult",
    "get_executor",
    "execute_subprocess",
    "execute_llm",
]
