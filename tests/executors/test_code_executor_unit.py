"""Unit tests for CodeExecutor."""

import pytest
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))


def test_code_executor_import():
    """Test that CodeExecutor can be imported."""
    from orchestrator.executors import CodeExecutor, ExecutionResult

    assert CodeExecutor is not None
    assert ExecutionResult is not None


def test_code_executor_initialization(tmp_path):
    """Test CodeExecutor initialization."""
    from orchestrator.executors import CodeExecutor

    workdir = tmp_path / ".work"
    executor = CodeExecutor(workdir=str(workdir))

    assert executor.workdir == workdir
    assert workdir.exists()
    assert (workdir / "logs").exists()
    assert (workdir / "results").exists()
    assert (workdir / "generated").exists()


def test_import_guard_allows_safe_imports():
    """Test that import guard allows safe imports."""
    from orchestrator.executors.sandbox import static_import_guard

    safe_code = """
import json
import pandas as pd
from orchestrator.mcp.data import load_csv
"""

    is_safe, violations = static_import_guard(safe_code)
    assert is_safe is True
    assert len(violations) == 0


def test_import_guard_blocks_dangerous_imports():
    """Test that import guard blocks dangerous imports."""
    from orchestrator.executors.sandbox import static_import_guard

    dangerous_code = """
import os
import subprocess
import socket
"""

    is_safe, violations = static_import_guard(dangerous_code)
    assert is_safe is False
    assert len(violations) > 0
    assert any("os" in v for v in violations)


def test_import_guard_blocks_eval():
    """Test that safety validation catches eval/exec."""
    from orchestrator.executors.sandbox import validate_code_safety

    dangerous_code = """
result = eval("1 + 1")
"""

    is_safe, violations = validate_code_safety(dangerous_code)
    assert is_safe is False
    assert any("eval" in v.lower() for v in violations)


def test_execution_result_to_agent_result(tmp_path):
    """Test ExecutionResult conversion to AgentExecResult."""
    from orchestrator.executors import ExecutionResult

    # Create log files
    logs_dir = tmp_path / "logs"
    logs_dir.mkdir()

    stdout_file = logs_dir / "test.out"
    stderr_file = logs_dir / "test.err"

    stdout_file.write_text("stdout content")
    stderr_file.write_text("stderr content")

    result = ExecutionResult(
        code_path=str(tmp_path / "code.py"),
        logs={"stdout": str(stdout_file), "stderr": str(stderr_file)},
        artifacts=["artifact1.txt"],
        success=True,
        duration_s=1.5,
    )

    agent_result = result.to_agent_result()

    assert agent_result.exit_code == 0
    assert agent_result.stdout == "stdout content"
    assert agent_result.stderr == "stderr content"
    assert agent_result.artifacts == ["artifact1.txt"]
    assert agent_result.duration_s == 1.5


def test_code_executor_execute_generates_files(tmp_path):
    """Test that execute generates code, logs, and results."""
    from orchestrator.executors import CodeExecutor

    workdir = tmp_path / ".work"
    executor = CodeExecutor(workdir=str(workdir))

    result = executor.execute(
        agent="test_agent",
        task="Print hello world",
        context="Simple test",
        max_seconds=10,
    )

    # Check that files were created
    assert Path(result.code_path).exists()
    assert Path(result.logs["stdout"]).exists()
    assert Path(result.logs["stderr"]).exists()


def test_code_executor_timeout_handling(tmp_path):
    """Test that timeout is handled gracefully."""
    from orchestrator.executors import CodeExecutor

    workdir = tmp_path / ".work"
    executor = CodeExecutor(workdir=str(workdir))

    # Manually create a long-running code file
    code_file = workdir / "generated" / "timeout_test.py"
    code_file.parent.mkdir(parents=True, exist_ok=True)
    code_file.write_text("import time\ntime.sleep(100)\n")

    result = executor._run_in_sandbox(
        code_path=code_file,
        stdout_path=workdir / "logs" / "timeout.out",
        stderr_path=workdir / "logs" / "timeout.err",
        max_seconds=1,  # Very short timeout
    )

    success, error = result
    assert success is False
    assert error is not None
    assert "timeout" in error.lower() or "timed out" in error.lower()


def test_sandbox_patch_socket():
    """Test that socket patching code is generated."""
    from orchestrator.executors.sandbox import patch_socket_if_no_network

    patch_code = patch_socket_if_no_network()

    assert patch_code is not None
    assert "socket" in patch_code
    assert "Network access is disabled" in patch_code


def test_is_module_allowed():
    """Test module allowlist logic."""
    from orchestrator.executors.sandbox import _is_module_allowed

    # Safe modules
    assert _is_module_allowed("json") is True
    assert _is_module_allowed("pandas") is True
    assert _is_module_allowed("orchestrator.mcp.data") is True

    # Dangerous modules
    assert _is_module_allowed("os") is False
    assert _is_module_allowed("subprocess") is False
    assert _is_module_allowed("socket") is False


def test_code_executor_collects_artifacts(tmp_path, monkeypatch):
    """Test artifact collection from recent files."""
    from orchestrator.executors import CodeExecutor
    import time

    # Change to tmp_path directory
    monkeypatch.chdir(tmp_path)

    # Create artifact directories
    reports_dir = tmp_path / "reports"
    reports_dir.mkdir()

    # Create a recent file
    artifact_file = reports_dir / "test_artifact.txt"
    artifact_file.write_text("test artifact")

    workdir = tmp_path / ".work"
    executor = CodeExecutor(workdir=str(workdir))

    # Sleep briefly to ensure file is recent
    time.sleep(0.1)

    artifacts = executor._collect_artifacts()

    # The artifact should be collected (created within last minute)
    assert any("test_artifact.txt" in str(a) for a in artifacts)
