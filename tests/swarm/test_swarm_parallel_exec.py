"""Tests for swarm parallel execution."""

import pytest
import asyncio
import time
from src.orchestrator.swarm.core import SwarmOrchestrator
from src.orchestrator.types import AgentOutcome


# Mock agent executor
async def mock_agent_executor(agent_name: str, phase_name: str, timeout: int = None) -> AgentOutcome:
    """Mock agent executor for testing."""
    # Simulate some work
    await asyncio.sleep(0.1)

    return AgentOutcome(
        agent_name=agent_name,
        success=True,
        artifacts=[],
        notes=f"Executed {agent_name} in {phase_name}",
        errors=[],
        exit_code=0,
        execution_time=0.1,
    )


@pytest.mark.asyncio
async def test_execute_single_agent():
    """Test executing a single agent."""
    orchestrator = SwarmOrchestrator(max_workers=2)

    outcome = await orchestrator.execute_phase_parallel(
        phase_name="test_phase",
        agents=["agent1"],
        agent_executor_fn=mock_agent_executor,
        dependencies=None,
    )

    assert outcome.success
    assert len(outcome.agent_outcomes) == 1
    assert outcome.agent_outcomes[0].agent_name == "agent1"
    assert outcome.execution_mode == "sequential"  # Single agent
    assert len(outcome.parallel_groups) == 1


@pytest.mark.asyncio
async def test_execute_parallel_agents():
    """Test executing independent agents in parallel."""
    orchestrator = SwarmOrchestrator(max_workers=3)

    agents = ["agent1", "agent2", "agent3"]

    start_time = time.time()
    outcome = await orchestrator.execute_phase_parallel(
        phase_name="test_phase",
        agents=agents,
        agent_executor_fn=mock_agent_executor,
        dependencies=None,  # No dependencies - all parallel
    )
    wall_time = time.time() - start_time

    assert outcome.success
    assert len(outcome.agent_outcomes) == 3
    assert outcome.execution_mode == "parallel"

    # All agents should be in one group
    assert len(outcome.parallel_groups) == 1
    assert set(outcome.parallel_groups[0]) == set(agents)

    # Wall time should be less than sequential time (3 * 0.1 = 0.3s)
    # Due to parallel execution, should be ~0.1s (plus overhead)
    assert wall_time < 0.25  # Allow some overhead


@pytest.mark.asyncio
async def test_execute_with_dependencies():
    """Test executing agents with dependencies."""
    orchestrator = SwarmOrchestrator(max_workers=3)

    agents = ["agent1", "agent2", "agent3"]
    dependencies = {
        "agent1": [],
        "agent2": ["agent1"],
        "agent3": ["agent1"],
    }

    outcome = await orchestrator.execute_phase_parallel(
        phase_name="test_phase",
        agents=agents,
        agent_executor_fn=mock_agent_executor,
        dependencies=dependencies,
    )

    assert outcome.success
    assert len(outcome.agent_outcomes) == 3
    assert outcome.execution_mode == "parallel"

    # Should have 2 groups: [agent1], [agent2, agent3]
    assert len(outcome.parallel_groups) == 2
    assert outcome.parallel_groups[0] == ["agent1"]
    assert set(outcome.parallel_groups[1]) == {"agent2", "agent3"}


@pytest.mark.asyncio
async def test_execute_preserves_order():
    """Test that results preserve original agent order."""
    orchestrator = SwarmOrchestrator(max_workers=5)

    agents = ["z", "y", "x", "w", "v"]  # Reverse alphabetical order

    outcome = await orchestrator.execute_phase_parallel(
        phase_name="test_phase",
        agents=agents,
        agent_executor_fn=mock_agent_executor,
        dependencies=None,
    )

    # Results should preserve original agent order
    result_names = [o.agent_name for o in outcome.agent_outcomes]
    assert result_names == agents


@pytest.mark.asyncio
async def test_concurrency_limit():
    """Test that max_workers limits concurrency."""
    call_times = []

    async def tracking_executor(agent_name: str, phase_name: str, timeout: int = None):
        call_times.append((agent_name, time.time()))
        await asyncio.sleep(0.1)
        return AgentOutcome(
            agent_name=agent_name,
            success=True,
            artifacts=[],
            notes="",
            errors=[],
            exit_code=0,
            execution_time=0.1,
        )

    # 5 agents but only 2 workers
    orchestrator = SwarmOrchestrator(max_workers=2)
    agents = ["a1", "a2", "a3", "a4", "a5"]

    await orchestrator.execute_phase_parallel(
        phase_name="test_phase",
        agents=agents,
        agent_executor_fn=tracking_executor,
        dependencies=None,
    )

    # Should have 5 calls
    assert len(call_times) == 5

    # Check that not all started at the same time (due to concurrency limit)
    start_times = [t for _, t in call_times]
    time_spread = max(start_times) - min(start_times)
    # With max_workers=2, some agents must wait
    assert time_spread > 0.05  # At least some delay due to queueing


@pytest.mark.asyncio
async def test_failed_agent():
    """Test handling of failed agent."""
    async def failing_executor(agent_name: str, phase_name: str, timeout: int = None):
        if agent_name == "failing_agent":
            return AgentOutcome(
                agent_name=agent_name,
                success=False,
                artifacts=[],
                notes="",
                errors=["Agent failed"],
                exit_code=1,
                execution_time=0.1,
            )
        return await mock_agent_executor(agent_name, phase_name, timeout)

    orchestrator = SwarmOrchestrator(max_workers=2)

    outcome = await orchestrator.execute_phase_parallel(
        phase_name="test_phase",
        agents=["agent1", "failing_agent", "agent2"],
        agent_executor_fn=failing_executor,
        dependencies=None,
    )

    # Phase should fail
    assert not outcome.success
    assert len(outcome.agent_outcomes) == 3

    # Find the failed agent
    failing_outcome = next(o for o in outcome.agent_outcomes if o.agent_name == "failing_agent")
    assert not failing_outcome.success
    assert failing_outcome.exit_code == 1


@pytest.mark.asyncio
async def test_speedup_calculation():
    """Test that speedup factor is calculated."""
    orchestrator = SwarmOrchestrator(max_workers=3)

    agents = ["agent1", "agent2", "agent3"]

    outcome = await orchestrator.execute_phase_parallel(
        phase_name="test_phase",
        agents=agents,
        agent_executor_fn=mock_agent_executor,
        dependencies=None,
    )

    # Speedup should be calculated for parallel execution
    assert outcome.speedup_factor is not None
    assert outcome.speedup_factor > 1.0  # Should show some speedup


@pytest.mark.asyncio
async def test_context_cache_stats():
    """Test context cache statistics."""
    orchestrator = SwarmOrchestrator(max_workers=2)

    # Initially empty
    stats = orchestrator.get_cache_stats()
    assert stats["size"] == 0

    # Can clear cache
    orchestrator.clear_cache()
    stats = orchestrator.get_cache_stats()
    assert stats["size"] == 0
