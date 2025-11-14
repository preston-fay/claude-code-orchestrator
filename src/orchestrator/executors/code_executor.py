"""Code executor that generates and runs Python code in a sandbox.

This executor uses an LLM to generate Python code that imports
MCP APIs, then executes the code in a sandboxed environment with
resource limits and security controls.
"""

import json
import subprocess
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

from .sandbox import (
    patch_socket_if_no_network,
    set_rlimits_if_available,
    validate_code_safety,
)
from .types import AgentExecResult


@dataclass
class ExecutionResult:
    """Result from code execution."""

    code_path: str
    logs: Dict[str, str]  # {stdout: path, stderr: path}
    artifacts: List[str] = field(default_factory=list)
    success: bool = True
    error: Optional[str] = None
    duration_s: float = 0.0
    metadata: Dict[str, str] = field(default_factory=dict)

    def to_agent_result(self) -> AgentExecResult:
        """Convert to AgentExecResult for compatibility."""
        # Read stdout and stderr
        stdout_content = ""
        stderr_content = ""

        if "stdout" in self.logs and Path(self.logs["stdout"]).exists():
            stdout_content = Path(self.logs["stdout"]).read_text()

        if "stderr" in self.logs and Path(self.logs["stderr"]).exists():
            stderr_content = Path(self.logs["stderr"]).read_text()

        return AgentExecResult(
            stdout=stdout_content,
            stderr=stderr_content,
            exit_code=0 if self.success else 1,
            artifacts=self.artifacts,
            duration_s=self.duration_s,
            metadata={**self.metadata, "code_path": self.code_path},
        )


class CodeExecutor:
    """Executor that generates and runs Python code using MCP APIs.

    This executor:
    1. Prompts an LLM to generate Python code using MCP APIs
    2. Validates the generated code for security
    3. Runs the code in a sandboxed environment
    4. Collects artifacts and logs

    Example:
        >>> executor = CodeExecutor()
        >>> result = executor.execute(
        ...     agent="data_analyst",
        ...     task="Load sales.csv and plot distribution of revenue column",
        ...     context="CSV is in data/raw/sales.csv",
        ... )
        >>> print(result.success)
        True
        >>> print(result.artifacts)
        ['reports/distribution_revenue.png']
    """

    def __init__(
        self,
        mcp_root: str = "src/orchestrator/mcp",
        workdir: str = ".work",
    ):
        """Initialize code executor.

        Args:
            mcp_root: Path to MCP registry root (for documentation purposes)
            workdir: Working directory for generated code and logs
        """
        self.mcp_root = Path(mcp_root)
        self.workdir = Path(workdir)

        # Create directories
        self.workdir.mkdir(exist_ok=True)
        (self.workdir / "logs").mkdir(exist_ok=True)
        (self.workdir / "results").mkdir(exist_ok=True)
        (self.workdir / "generated").mkdir(exist_ok=True)

    def execute(
        self,
        agent: str,
        task: str,
        context: Optional[str] = None,
        max_seconds: int = 120,
    ) -> ExecutionResult:
        """Execute a task by generating and running code.

        Args:
            agent: Agent name (used for file naming)
            task: Task description for the LLM
            context: Optional context/background information
            max_seconds: Maximum execution time in seconds

        Returns:
            ExecutionResult with paths to code, logs, artifacts, and status
        """
        timestamp = int(time.time())
        agent_slug = agent.replace(" ", "_").lower()

        # Generate code using LLM (placeholder - will use real LLM in integration)
        code = self._generate_code_with_llm(task, context)

        # Validate code safety
        is_safe, violations = validate_code_safety(code)
        if not is_safe:
            return ExecutionResult(
                code_path="",
                logs={},
                success=False,
                error=f"Code safety validation failed: {', '.join(violations)}",
            )

        # Prepare code file
        code_path = self.workdir / "generated" / f"{agent_slug}_{timestamp}.py"
        code_path.write_text(code, encoding="utf-8")

        # Prepare log paths
        stdout_path = self.workdir / "logs" / f"{agent_slug}_{timestamp}.out"
        stderr_path = self.workdir / "logs" / f"{agent_slug}_{timestamp}.err"
        result_json_path = self.workdir / "results" / f"{agent_slug}_{timestamp}.json"

        # Execute in sandbox
        start_time = time.time()
        success, error = self._run_in_sandbox(
            code_path=code_path,
            stdout_path=stdout_path,
            stderr_path=stderr_path,
            max_seconds=max_seconds,
        )
        duration = time.time() - start_time

        # Collect artifacts
        artifacts = self._collect_artifacts()

        # Create result
        result = ExecutionResult(
            code_path=str(code_path),
            logs={
                "stdout": str(stdout_path),
                "stderr": str(stderr_path),
            },
            artifacts=artifacts,
            success=success,
            error=error,
            duration_s=duration,
            metadata={
                "agent": agent,
                "task": task,
                "timestamp": str(timestamp),
            },
        )

        # Save result JSON
        result_json_path.write_text(
            json.dumps(
                {
                    "success": result.success,
                    "error": result.error,
                    "code_path": result.code_path,
                    "logs": result.logs,
                    "artifacts": result.artifacts,
                    "duration_s": result.duration_s,
                    "metadata": result.metadata,
                },
                indent=2,
            ),
            encoding="utf-8",
        )

        return result

    def _generate_code_with_llm(self, task: str, context: Optional[str]) -> str:
        """Generate Python code using LLM.

        This is a placeholder implementation. In production, this would:
        1. Load prompt templates from .claude/prompts/
        2. Call an LLM API (Anthropic Claude, OpenAI, etc.)
        3. Parse and validate the generated code

        Args:
            task: Task description
            context: Optional context

        Returns:
            Generated Python code as string
        """
        # Placeholder: Generate a simple example
        # In production, this would call an actual LLM
        code_template = '''"""
Task: {task}
Context: {context}
"""

import json
from pathlib import Path

# Import MCP APIs as needed
# from orchestrator.mcp.data import load_csv
# from orchestrator.mcp.analytics import describe_data
# from orchestrator.mcp.viz import plot_distribution

def main():
    """Execute the task."""
    print("Code execution started")

    # TODO: Implement task logic here
    # Example:
    # df = load_csv("data/raw/example.csv")
    # stats = describe_data(df)
    # plot_path = plot_distribution(df, "column_name")

    # Output summary
    result = {{
        "status": "success",
        "message": "Placeholder code executed",
        "artifacts": []
    }}

    print(json.dumps(result))
    return result

if __name__ == "__main__":
    main()
'''

        code = code_template.format(
            task=task,
            context=context or "No additional context provided"
        )

        return code

    def _run_in_sandbox(
        self,
        code_path: Path,
        stdout_path: Path,
        stderr_path: Path,
        max_seconds: int = 120,
    ) -> tuple[bool, Optional[str]]:
        """Run code in a sandboxed subprocess.

        Args:
            code_path: Path to Python script
            stdout_path: Path to write stdout
            stderr_path: Path to write stderr
            max_seconds: Timeout in seconds

        Returns:
            Tuple of (success: bool, error: Optional[str])
        """
        # Prepare environment
        env = {
            "PYTHONPATH": "src",
            "NO_NETWORK": "1",
            "PYTHONUNBUFFERED": "1",
        }

        # Add network blocking patch to code
        original_code = code_path.read_text()
        patch = patch_socket_if_no_network()
        if patch:
            patched_code = patch + "\n\n" + original_code
            code_path.write_text(patched_code)

        try:
            with open(stdout_path, "w") as stdout_file, open(stderr_path, "w") as stderr_file:
                # Run subprocess with timeout
                process = subprocess.run(
                    [sys.executable, str(code_path)],
                    stdout=stdout_file,
                    stderr=stderr_file,
                    timeout=max_seconds,
                    env=env,
                    cwd=str(Path.cwd()),  # Run from repo root
                )

                if process.returncode == 0:
                    return True, None
                else:
                    stderr_content = stderr_path.read_text() if stderr_path.exists() else ""
                    return False, f"Process exited with code {process.returncode}: {stderr_content[:200]}"

        except subprocess.TimeoutExpired:
            return False, f"Execution timed out after {max_seconds} seconds"
        except Exception as e:
            return False, f"Execution failed: {str(e)}"

    def _collect_artifacts(self) -> List[str]:
        """Collect artifacts generated by the code.

        Looks for files created in:
        - data/processed/
        - reports/
        - artifacts/

        Returns:
            List of artifact file paths
        """
        artifacts = []

        artifact_dirs = [
            Path("data/processed"),
            Path("reports"),
            Path("artifacts"),
        ]

        for dir_path in artifact_dirs:
            if not dir_path.exists():
                continue

            # Find files modified in the last minute (recently created)
            cutoff_time = time.time() - 60

            for file_path in dir_path.rglob("*"):
                if file_path.is_file():
                    mtime = file_path.stat().st_mtime
                    if mtime >= cutoff_time:
                        artifacts.append(str(file_path))

        return sorted(artifacts)
