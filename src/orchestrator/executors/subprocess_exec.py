"""Subprocess executor for agents with shell/CLI entrypoints."""

import subprocess
import time
from pathlib import Path
from typing import Dict, Any, Optional
import os

from .types import AgentExecResult


async def execute_subprocess(
    command: str,
    working_dir: Path,
    timeout_seconds: float = 1800,  # 30 minutes default
    env: Optional[Dict[str, str]] = None,
) -> AgentExecResult:
    """
    Execute a subprocess command and capture results.

    Args:
        command: Shell command to execute
        working_dir: Working directory for execution
        timeout_seconds: Maximum execution time
        env: Environment variables (None = inherit from parent)

    Returns:
        AgentExecResult with captured output and metadata
    """
    start_time = time.time()

    # Prepare environment
    exec_env = os.environ.copy()
    if env:
        exec_env.update(env)

    try:
        # Execute command
        result = subprocess.run(
            command,
            shell=True,
            cwd=working_dir,
            env=exec_env,
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
        )

        duration = time.time() - start_time

        # Parse artifacts from stdout (look for artifact declarations)
        artifacts = _parse_artifacts_from_output(result.stdout)

        return AgentExecResult(
            stdout=result.stdout,
            stderr=result.stderr,
            exit_code=result.returncode,
            artifacts=artifacts,
            duration_s=duration,
            metadata={
                "command": command,
                "working_dir": str(working_dir),
                "timeout": timeout_seconds,
            },
        )

    except subprocess.TimeoutExpired as e:
        duration = time.time() - start_time

        return AgentExecResult(
            stdout=e.stdout.decode("utf-8") if e.stdout else "",
            stderr=e.stderr.decode("utf-8") if e.stderr else "Command timed out",
            exit_code=124,  # Standard timeout exit code
            duration_s=duration,
            metadata={
                "command": command,
                "timeout": timeout_seconds,
                "error": "timeout",
            },
        )

    except Exception as e:
        duration = time.time() - start_time

        return AgentExecResult(
            stdout="",
            stderr=f"Execution error: {str(e)}",
            exit_code=1,
            duration_s=duration,
            metadata={
                "command": command,
                "error": str(e),
            },
        )


def _parse_artifacts_from_output(stdout: str) -> list:
    """
    Parse artifact declarations from stdout.

    Looks for lines like:
    ARTIFACT: path/to/file.txt
    ARTIFACTS: file1.py,file2.py
    """
    artifacts = []

    for line in stdout.split("\n"):
        line = line.strip()

        if line.startswith("ARTIFACT:"):
            artifact = line.replace("ARTIFACT:", "").strip()
            artifacts.append(artifact)

        elif line.startswith("ARTIFACTS:"):
            artifact_list = line.replace("ARTIFACTS:", "").strip()
            artifacts.extend([a.strip() for a in artifact_list.split(",")])

    return artifacts
