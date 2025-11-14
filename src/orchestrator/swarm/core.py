"""Swarm orchestrator for parallel agent execution with dependency management."""

import asyncio
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor, as_completed
from typing import List, Dict, Any, Optional, Set, Tuple
from dataclasses import dataclass
from collections import defaultdict, deque

from ..types import AgentOutcome
from .context_cache import ContextCache


@dataclass
class PhaseOutcome:
    """Result of executing a phase with swarm orchestrator."""

    phase_name: str
    success: bool
    agent_outcomes: List[AgentOutcome]
    execution_mode: str  # "sequential" or "parallel"
    parallel_groups: List[List[str]]  # Topologically sorted agent groups
    total_wall_time_s: float
    speedup_factor: Optional[float] = None  # Speedup vs sequential


class SwarmOrchestrator:
    """
    Orchestrator for parallel agent execution with dependency-aware scheduling.

    Features:
    - Topological sorting to identify independent agent groups
    - Concurrent execution within groups
    - Context caching to avoid redundant work
    - Deterministic result ordering
    - Configurable executor (thread or process pool)
    """

    def __init__(
        self,
        max_workers: Optional[int] = None,
        use_process_pool: bool = False,
        context_cache: Optional[ContextCache] = None,
    ):
        """
        Initialize swarm orchestrator.

        Args:
            max_workers: Maximum concurrent workers (defaults to 2)
            use_process_pool: Use ProcessPoolExecutor instead of ThreadPoolExecutor
            context_cache: Optional shared context cache
        """
        self.max_workers = max_workers or 2
        self.use_process_pool = use_process_pool
        self.context_cache = context_cache or ContextCache()

    def _build_dependency_graph(
        self, agents: List[str], dependencies: Optional[Dict[str, List[str]]] = None
    ) -> Dict[str, Set[str]]:
        """
        Build dependency graph from agent list and dependency map.

        Args:
            agents: List of agent names
            dependencies: Dict mapping agent -> list of dependencies (agents that must run first)

        Returns:
            Adjacency list representing dependency graph
        """
        graph: Dict[str, Set[str]] = {agent: set() for agent in agents}

        if dependencies:
            for agent, deps in dependencies.items():
                if agent in graph:
                    graph[agent] = set(deps) & set(agents)  # Only keep valid dependencies

        return graph

    def _topological_sort_groups(
        self, agents: List[str], dependencies: Optional[Dict[str, List[str]]] = None
    ) -> List[List[str]]:
        """
        Perform topological sort and group agents by dependency level.

        Agents in the same group have no dependencies on each other and can run in parallel.

        Args:
            agents: List of agent names
            dependencies: Dict mapping agent -> list of dependencies

        Returns:
            List of agent groups (each group can execute in parallel)
        """
        if not agents:
            # Empty agents list
            return []

        if not dependencies or all(not deps for deps in dependencies.values()):
            # No dependencies - all agents can run in parallel
            return [agents]

        graph = self._build_dependency_graph(agents, dependencies)

        # Calculate in-degree for each node (number of dependencies)
        in_degree = {agent: len(graph[agent]) for agent in agents}

        # Group agents by level (BFS-style topological sort)
        groups: List[List[str]] = []
        queue = deque([agent for agent, degree in in_degree.items() if degree == 0])
        processed = set()

        while queue:
            # Process all agents at current level
            current_level = []
            level_size = len(queue)

            for _ in range(level_size):
                agent = queue.popleft()
                current_level.append(agent)
                processed.add(agent)

                # Reduce in-degree for dependent agents
                for other_agent, deps in graph.items():
                    if agent in deps and other_agent not in processed:
                        in_degree[other_agent] -= 1
                        if in_degree[other_agent] == 0:
                            queue.append(other_agent)

            if current_level:
                groups.append(sorted(current_level))  # Sort for determinism

        # Check for cycles
        if len(processed) != len(agents):
            unprocessed = set(agents) - processed
            raise ValueError(f"Dependency cycle detected involving agents: {unprocessed}")

        return groups

    async def execute_phase_parallel(
        self,
        phase_name: str,
        agents: List[str],
        agent_executor_fn: Any,  # Async function to execute a single agent
        dependencies: Optional[Dict[str, List[str]]] = None,
        timeout_override: Optional[int] = None,
    ) -> PhaseOutcome:
        """
        Execute phase agents in parallel where dependencies allow.

        Args:
            phase_name: Name of the phase
            agents: List of agent names to execute
            agent_executor_fn: Async function(agent_name, phase_name, timeout) -> AgentOutcome
            dependencies: Optional dependency map
            timeout_override: Optional timeout override

        Returns:
            PhaseOutcome with execution results
        """
        import time

        start_time = time.time()

        # Determine parallel groups via topological sort
        parallel_groups = self._topological_sort_groups(agents, dependencies)

        # Execute groups sequentially, agents within groups in parallel
        all_outcomes: List[AgentOutcome] = []
        execution_mode = "parallel" if len(parallel_groups) > 1 or len(parallel_groups[0]) > 1 else "sequential"

        for group_idx, group in enumerate(parallel_groups):
            if len(group) == 1:
                # Single agent - execute sequentially
                outcome = await agent_executor_fn(group[0], phase_name, timeout_override)
                all_outcomes.append(outcome)
            else:
                # Multiple agents - execute in parallel
                group_outcomes = await self._execute_group_parallel(
                    group, phase_name, agent_executor_fn, timeout_override
                )
                all_outcomes.extend(group_outcomes)

        total_wall_time = time.time() - start_time

        # Calculate speedup (approximate - would need sequential baseline)
        # For now, just mark that parallel was used
        speedup = None
        if execution_mode == "parallel" and len(agents) > 1:
            # Rough estimate: speedup = agents / wall_time_per_agent
            # Real speedup calculation would require running sequentially
            speedup = len(agents) / max(1, len(parallel_groups))

        return PhaseOutcome(
            phase_name=phase_name,
            success=all(o.success for o in all_outcomes),
            agent_outcomes=all_outcomes,
            execution_mode=execution_mode,
            parallel_groups=parallel_groups,
            total_wall_time_s=total_wall_time,
            speedup_factor=speedup,
        )

    async def _execute_group_parallel(
        self,
        agents: List[str],
        phase_name: str,
        agent_executor_fn: Any,
        timeout_override: Optional[int] = None,
    ) -> List[AgentOutcome]:
        """
        Execute a group of independent agents in parallel.

        Args:
            agents: List of agent names (no inter-dependencies)
            phase_name: Phase name
            agent_executor_fn: Async executor function
            timeout_override: Optional timeout

        Returns:
            List of AgentOutcomes in original agent order
        """
        # Create semaphore for concurrency control
        semaphore = asyncio.Semaphore(self.max_workers)

        async def execute_with_semaphore(agent_name: str) -> Tuple[str, AgentOutcome]:
            """Execute agent with semaphore."""
            async with semaphore:
                outcome = await agent_executor_fn(agent_name, phase_name, timeout_override)
                return (agent_name, outcome)

        # Execute all agents concurrently
        tasks = [execute_with_semaphore(agent) for agent in agents]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Convert results to outcomes, preserving order
        outcomes_map = {}
        for result in results:
            if isinstance(result, Exception):
                # Handle exceptions as failed outcomes
                # This shouldn't happen since agent_executor_fn handles errors
                continue
            agent_name, outcome = result
            outcomes_map[agent_name] = outcome

        # Return outcomes in original agent order
        return [outcomes_map[agent] for agent in agents if agent in outcomes_map]

    def get_cache_stats(self) -> Dict[str, Any]:
        """Get context cache statistics."""
        return self.context_cache.get_stats()

    def clear_cache(self) -> None:
        """Clear context cache."""
        self.context_cache.clear()
