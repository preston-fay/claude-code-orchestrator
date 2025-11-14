"""Tests for dependency graph and topological sorting."""

import pytest
from src.orchestrator.swarm.core import SwarmOrchestrator


def test_no_dependencies_all_parallel():
    """Test that agents with no dependencies can all run in parallel."""
    orchestrator = SwarmOrchestrator()

    agents = ["agent1", "agent2", "agent3", "agent4"]
    dependencies = None

    groups = orchestrator._topological_sort_groups(agents, dependencies)

    # All agents should be in one group since no dependencies
    assert len(groups) == 1
    assert set(groups[0]) == set(agents)


def test_linear_dependencies():
    """Test linear dependency chain (agent1 -> agent2 -> agent3)."""
    orchestrator = SwarmOrchestrator()

    agents = ["agent1", "agent2", "agent3"]
    dependencies = {
        "agent1": [],
        "agent2": ["agent1"],
        "agent3": ["agent2"],
    }

    groups = orchestrator._topological_sort_groups(agents, dependencies)

    # Should have 3 groups (one per level)
    assert len(groups) == 3
    assert groups[0] == ["agent1"]
    assert groups[1] == ["agent2"]
    assert groups[2] == ["agent3"]


def test_diamond_dependencies():
    """Test diamond dependency pattern (A -> B,C -> D)."""
    orchestrator = SwarmOrchestrator()

    agents = ["a", "b", "c", "d"]
    dependencies = {
        "a": [],
        "b": ["a"],
        "c": ["a"],
        "d": ["b", "c"],
    }

    groups = orchestrator._topological_sort_groups(agents, dependencies)

    # Should have 3 levels
    assert len(groups) == 3
    assert groups[0] == ["a"]
    assert set(groups[1]) == {"b", "c"}  # B and C can run in parallel
    assert groups[2] == ["d"]


def test_parallel_chains():
    """Test two independent chains running in parallel."""
    orchestrator = SwarmOrchestrator()

    agents = ["a1", "a2", "b1", "b2"]
    dependencies = {
        "a1": [],
        "a2": ["a1"],
        "b1": [],
        "b2": ["b1"],
    }

    groups = orchestrator._topological_sort_groups(agents, dependencies)

    # Should have 2 levels (a1 & b1, then a2 & b2)
    assert len(groups) == 2
    assert set(groups[0]) == {"a1", "b1"}
    assert set(groups[1]) == {"a2", "b2"}


def test_complex_dependencies():
    """Test complex dependency graph."""
    orchestrator = SwarmOrchestrator()

    # Graph:
    #     a
    #    / \
    #   b   c
    #   |\ /|
    #   | X |
    #   |/ \|
    #   d   e
    #    \ /
    #     f

    agents = ["a", "b", "c", "d", "e", "f"]
    dependencies = {
        "a": [],
        "b": ["a"],
        "c": ["a"],
        "d": ["b", "c"],
        "e": ["b", "c"],
        "f": ["d", "e"],
    }

    groups = orchestrator._topological_sort_groups(agents, dependencies)

    # Should have 4 levels
    assert len(groups) == 4
    assert groups[0] == ["a"]
    assert set(groups[1]) == {"b", "c"}
    assert set(groups[2]) == {"d", "e"}
    assert groups[3] == ["f"]


def test_cycle_detection():
    """Test that cycles are detected and raise an error."""
    orchestrator = SwarmOrchestrator()

    # Create a cycle: agent1 -> agent2 -> agent3 -> agent1
    agents = ["agent1", "agent2", "agent3"]
    dependencies = {
        "agent1": ["agent3"],
        "agent2": ["agent1"],
        "agent3": ["agent2"],
    }

    with pytest.raises(ValueError, match="Dependency cycle detected"):
        orchestrator._topological_sort_groups(agents, dependencies)


def test_self_dependency_cycle():
    """Test that self-dependencies are handled."""
    orchestrator = SwarmOrchestrator()

    agents = ["agent1", "agent2"]
    dependencies = {
        "agent1": ["agent1"],  # Self-dependency
        "agent2": [],
    }

    with pytest.raises(ValueError, match="Dependency cycle detected"):
        orchestrator._topological_sort_groups(agents, dependencies)


def test_partial_dependencies():
    """Test agents with missing dependency definitions."""
    orchestrator = SwarmOrchestrator()

    agents = ["agent1", "agent2", "agent3", "agent4"]
    dependencies = {
        "agent1": [],
        "agent3": ["agent1"],
        # agent2 and agent4 not in dependencies dict
    }

    groups = orchestrator._topological_sort_groups(agents, dependencies)

    # Agents without dependencies should be in first group
    assert "agent1" in groups[0]
    assert "agent2" in groups[0]
    assert "agent4" in groups[0]
    # agent3 depends on agent1
    assert "agent3" in groups[1]


def test_empty_agents_list():
    """Test handling of empty agents list."""
    orchestrator = SwarmOrchestrator()

    agents = []
    dependencies = {}

    groups = orchestrator._topological_sort_groups(agents, dependencies)

    assert groups == []


def test_single_agent():
    """Test single agent execution."""
    orchestrator = SwarmOrchestrator()

    agents = ["solo_agent"]
    dependencies = {"solo_agent": []}

    groups = orchestrator._topological_sort_groups(agents, dependencies)

    assert len(groups) == 1
    assert groups[0] == ["solo_agent"]


def test_deterministic_ordering():
    """Test that topological sort produces deterministic ordering."""
    orchestrator = SwarmOrchestrator()

    agents = ["z", "y", "x", "w", "v"]  # Reverse alphabetical
    dependencies = {
        "z": [],
        "y": ["z"],
        "x": ["z"],
        "w": ["y", "x"],
        "v": [],
    }

    # Run multiple times to verify determinism
    results = []
    for _ in range(5):
        groups = orchestrator._topological_sort_groups(agents, dependencies)
        results.append(groups)

    # All results should be identical
    for result in results[1:]:
        assert result == results[0]

    # Verify agents within groups are sorted alphabetically
    for group in results[0]:
        assert group == sorted(group)
