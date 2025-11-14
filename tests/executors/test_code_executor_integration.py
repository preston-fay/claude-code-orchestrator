"""Integration tests for CodeExecutor."""

import pytest
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))


@pytest.mark.skipif(
    sys.platform == "win32",
    reason="Sandbox features may not work on Windows"
)
def test_code_executor_end_to_end_simple(tmp_path, monkeypatch):
    """Test end-to-end code execution with a simple script."""
    from orchestrator.executors import CodeExecutor

    # Change to tmp_path for artifact collection
    monkeypatch.chdir(tmp_path)

    workdir = tmp_path / ".work"
    executor = CodeExecutor(workdir=str(workdir))

    # Manually override the code generation to use a simple test script
    def mock_generate_code(task, context):
        return '''
"""Simple test script."""
import json

def main():
    print("Test execution successful")
    result = {"status": "success", "message": "Test completed"}
    print(json.dumps(result))

if __name__ == "__main__":
    main()
'''

    # Monkey-patch the code generator
    executor._generate_code_with_llm = mock_generate_code

    # Execute
    result = executor.execute(
        agent="test_agent",
        task="Run a simple test",
        context="Integration test",
        max_seconds=30,
    )

    # Verify results
    assert result.success is True
    assert Path(result.code_path).exists()
    assert Path(result.logs["stdout"]).exists()

    # Check stdout contains expected output
    stdout_content = Path(result.logs["stdout"]).read_text()
    assert "Test execution successful" in stdout_content


@pytest.mark.skipif(
    sys.platform == "win32",
    reason="Sandbox features may not work on Windows"
)
def test_code_executor_with_mcp_apis(tmp_path, monkeypatch):
    """Test code execution with MCP API imports."""
    pytest.importorskip("pandas", reason="pandas not installed")

    from orchestrator.executors import CodeExecutor

    # Change to tmp_path
    monkeypatch.chdir(tmp_path)

    # Create a test CSV
    data_dir = tmp_path / "data" / "raw"
    data_dir.mkdir(parents=True)
    csv_file = data_dir / "test.csv"
    csv_file.write_text("x,y,z\n1,2,3\n4,5,6\n7,8,9\n")

    workdir = tmp_path / ".work"
    executor = CodeExecutor(workdir=str(workdir))

    # Create a test script that uses MCP APIs
    def mock_generate_code(task, context):
        return '''
"""Test script using MCP APIs."""
import json
from orchestrator.mcp.data import load_csv
from orchestrator.mcp.analytics import describe_data

def main():
    # Load CSV
    df = load_csv("data/raw/test.csv")
    print(f"Loaded {len(df)} rows")

    # Describe data
    stats = describe_data(df)
    print(f"Columns: {stats['column_count']}")

    result = {
        "status": "success",
        "rows": stats["row_count"],
        "columns": stats["column_count"]
    }
    print(json.dumps(result))

if __name__ == "__main__":
    main()
'''

    executor._generate_code_with_llm = mock_generate_code

    result = executor.execute(
        agent="data_analyst",
        task="Load and describe CSV",
        context="Test MCP integration",
        max_seconds=30,
    )

    # Verify results
    assert result.success is True

    stdout_content = Path(result.logs["stdout"]).read_text()
    assert "Loaded 3 rows" in stdout_content
    assert "Columns: 3" in stdout_content


@pytest.mark.skipif(
    sys.platform == "win32",
    reason="Sandbox features may not work on Windows"
)
def test_code_executor_blocks_dangerous_code(tmp_path, monkeypatch):
    """Test that dangerous code is blocked by safety checks."""
    from orchestrator.executors import CodeExecutor

    monkeypatch.chdir(tmp_path)

    workdir = tmp_path / ".work"
    executor = CodeExecutor(workdir=str(workdir))

    # Try to generate dangerous code
    def mock_generate_dangerous_code(task, context):
        return '''
import os
import subprocess

def main():
    # This should be blocked
    os.system("ls")
    subprocess.run(["echo", "dangerous"])

if __name__ == "__main__":
    main()
'''

    executor._generate_code_with_llm = mock_generate_dangerous_code

    result = executor.execute(
        agent="bad_actor",
        task="Try something dangerous",
        context="Should fail safety check",
        max_seconds=10,
    )

    # Should fail due to safety validation
    assert result.success is False
    assert result.error is not None
    assert "safety" in result.error.lower() or "import" in result.error.lower()


def test_code_executor_agent_result_conversion(tmp_path, monkeypatch):
    """Test conversion from ExecutionResult to AgentExecResult."""
    from orchestrator.executors import CodeExecutor

    monkeypatch.chdir(tmp_path)

    workdir = tmp_path / ".work"
    executor = CodeExecutor(workdir=str(workdir))

    def mock_generate_code(task, context):
        return '''
print("Hello from agent")
'''

    executor._generate_code_with_llm = mock_generate_code

    exec_result = executor.execute(
        agent="test_agent",
        task="Simple task",
        max_seconds=10,
    )

    # Convert to AgentExecResult
    agent_result = exec_result.to_agent_result()

    assert agent_result.exit_code == 0 if exec_result.success else 1
    assert agent_result.stdout is not None
    assert "code_path" in agent_result.metadata
