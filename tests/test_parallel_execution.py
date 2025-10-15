"""Tests for parallel agent execution."""

import pytest
import asyncio
from pathlib import Path
from src.orchestrator.runloop import Orchestrator
from src.orchestrator.types import AgentOutcome


class TestParallelExecution:
    """Test parallel agent execution with concurrency control."""

    @pytest.fixture
    def mock_config(self, tmp_path):
        """Create mock config with parallel phase."""
        return {
            "workflow": {
                "phases": {
                    "test-parallel": {
                        "enabled": True,
                        "parallel": True,
                        "agents": ["agent1", "agent2", "agent3"],
                        "requires_consensus": False,
                        "artifacts_required": [],
                    }
                }
            },
            "orchestrator": {
                "max_parallel_agents": 2,
                "timeout_minutes": 1,
            },
            "subagents": {
                "agent1": {"description": "Test agent 1"},
                "agent2": {"description": "Test agent 2"},
                "agent3": {"description": "Test agent 3"},
            },
        }

    @pytest.mark.asyncio
    async def test_parallel_with_semaphore(self, tmp_path, mock_config, monkeypatch):
        """Test that parallel execution respects concurrency limit."""
        # Track concurrent executions
        concurrent_count = 0
        max_concurrent = 0

        async def mock_invoke_agent_async(self, agent_name, phase_name, timeout_override=None):
            nonlocal concurrent_count, max_concurrent
            concurrent_count += 1
            max_concurrent = max(max_concurrent, concurrent_count)

            # Simulate work
            await asyncio.sleep(0.1)

            concurrent_count -= 1
            return AgentOutcome(
                agent_name=agent_name,
                success=True,
                artifacts=[],
                exit_code=0,
                execution_time=0.1,
            )

        # Patch the async method
        monkeypatch.setattr(Orchestrator, "_invoke_agent_async", mock_invoke_agent_async)

        orch = Orchestrator(project_root=tmp_path)
        orch.config = mock_config

        # Run parallel agents
        outcomes = await orch._run_agents_parallel(
            ["agent1", "agent2", "agent3"], "test-parallel", max_workers=2
        )

        # Verify all succeeded
        assert len(outcomes) == 3
        assert all(o.success for o in outcomes)

        # Verify concurrency limit was respected
        assert max_concurrent <= 2

    @pytest.mark.asyncio
    async def test_parallel_exception_handling(self, tmp_path, mock_config, monkeypatch):
        """Test that exceptions in parallel execution are handled gracefully."""

        async def mock_invoke_agent_async(self, agent_name, phase_name, timeout_override=None):
            if agent_name == "agent2":
                raise RuntimeError("Agent failed")
            return AgentOutcome(
                agent_name=agent_name, success=True, artifacts=[], exit_code=0, execution_time=0.1
            )

        monkeypatch.setattr(Orchestrator, "_invoke_agent_async", mock_invoke_agent_async)

        orch = Orchestrator(project_root=tmp_path)
        orch.config = mock_config

        # Run parallel agents
        outcomes = await orch._run_agents_parallel(
            ["agent1", "agent2", "agent3"], "test-parallel"
        )

        # Verify we got all outcomes (including the failed one)
        assert len(outcomes) == 3

        # agent1 and agent3 should succeed, agent2 should fail
        success_count = sum(1 for o in outcomes if o.success)
        assert success_count == 2

    def test_run_phase_sequential_vs_parallel(self, tmp_path, mock_config, monkeypatch):
        """Test that phase execution switches between sequential and parallel correctly."""
        execution_modes = []

        async def track_parallel(agent_names, phase_name, max_workers=None, timeout_override=None):
            execution_modes.append("parallel")
            return [
                AgentOutcome(agent_name=name, success=True, artifacts=[], exit_code=0)
                for name in agent_names
            ]

        def track_sequential(agent_name, phase_name, timeout_override=None):
            execution_modes.append("sequential")
            return AgentOutcome(agent_name=agent_name, success=True, artifacts=[], exit_code=0)

        monkeypatch.setattr(Orchestrator, "_run_agents_parallel", track_parallel)
        monkeypatch.setattr(Orchestrator, "invoke_agent", track_sequential)

        orch = Orchestrator(project_root=tmp_path)
        orch.config = mock_config

        # Run with parallel=True
        outcome = orch.run_phase("test-parallel")
        assert "parallel" in execution_modes

        # Test with force_parallel
        execution_modes.clear()
        mock_config["workflow"]["phases"]["test-parallel"]["parallel"] = False

        outcome = orch.run_phase("test-parallel", force_parallel=True)
        assert "parallel" in execution_modes
