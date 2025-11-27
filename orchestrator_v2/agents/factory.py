"""
Agent Factory for creating agent instances.

Provides centralized creation of agent instances with proper configuration.
"""

import logging
from typing import Type

from orchestrator_v2.agents.base_agent import BaseAgent
from orchestrator_v2.agents.architect import ArchitectAgent, create_architect_agent
from orchestrator_v2.agents.developer import DeveloperAgent, create_developer_agent
from orchestrator_v2.agents.qa import QAAgent, create_qa_agent
from orchestrator_v2.agents.documentarian import DocumentarianAgent, create_documentarian_agent
from orchestrator_v2.agents.consensus import ConsensusAgent, create_consensus_agent
from orchestrator_v2.agents.steward import StewardAgent, create_steward_agent
from orchestrator_v2.agents.reviewer import ReviewerAgent, create_reviewer_agent
from orchestrator_v2.agents.data_agent import DataAgent, create_data_agent

logger = logging.getLogger(__name__)


# Agent ID to factory function mapping
AGENT_FACTORIES: dict[str, callable] = {
    # Architect variations
    "architect": create_architect_agent,
    "architect_agent": create_architect_agent,
    "solutions_architect": create_architect_agent,
    
    # Developer variations
    "developer": create_developer_agent,
    "developer_agent": create_developer_agent,
    "dev": create_developer_agent,
    "developer.frontend": create_developer_agent,
    "developer.backend": create_developer_agent,
    
    # QA variations
    "qa": create_qa_agent,
    "qa_agent": create_qa_agent,
    "quality_assurance": create_qa_agent,
    "tester": create_qa_agent,
    
    # Documentarian variations
    "documentarian": create_documentarian_agent,
    "documentarian_agent": create_documentarian_agent,
    "docs": create_documentarian_agent,
    "documentation": create_documentarian_agent,
    
    # Consensus variations
    "consensus": create_consensus_agent,
    "consensus_agent": create_consensus_agent,
    
    # Steward variations
    "steward": create_steward_agent,
    "steward_agent": create_steward_agent,
    "code_steward": create_steward_agent,
    
    # Reviewer variations
    "reviewer": create_reviewer_agent,
    "reviewer_agent": create_reviewer_agent,
    "code_reviewer": create_reviewer_agent,
    
    # Data agent variations
    "data": create_data_agent,
    "data_agent": create_data_agent,
    "data.ingestion": create_data_agent,
    "data.transform": create_data_agent,
    "data.training": create_data_agent,
}


# Agent ID to class mapping (for type checking)
AGENT_CLASSES: dict[str, Type[BaseAgent]] = {
    "architect": ArchitectAgent,
    "developer": DeveloperAgent,
    "qa": QAAgent,
    "documentarian": DocumentarianAgent,
    "consensus": ConsensusAgent,
    "steward": StewardAgent,
    "reviewer": ReviewerAgent,
    "data": DataAgent,
}


def create_agent(agent_id: str) -> BaseAgent | None:
    """
    Create an agent instance by ID.
    
    Args:
        agent_id: Agent identifier (e.g., 'architect', 'developer', 'qa').
        
    Returns:
        Agent instance or None if agent ID is not recognized.
    """
    factory = AGENT_FACTORIES.get(agent_id.lower())
    
    if factory is None:
        logger.warning(f"Unknown agent ID: {agent_id}")
        return None
    
    try:
        agent = factory()
        logger.debug(f"Created agent instance: {agent_id} -> {type(agent).__name__}")
        return agent
    except Exception as e:
        logger.error(f"Failed to create agent {agent_id}: {e}")
        return None


def get_agent_class(agent_id: str) -> Type[BaseAgent] | None:
    """
    Get the agent class for an agent ID.
    
    Args:
        agent_id: Agent identifier.
        
    Returns:
        Agent class or None if not recognized.
    """
    # Normalize agent ID to base form
    base_id = agent_id.lower().split('.')[0].replace('_agent', '')
    return AGENT_CLASSES.get(base_id)


def list_available_agents() -> list[str]:
    """
    List all available agent IDs.
    
    Returns:
        List of agent IDs that can be created.
    """
    # Return unique base agent names
    return sorted(set(AGENT_CLASSES.keys()))


def create_agents_for_phase(phase_agents: list[str]) -> dict[str, BaseAgent]:
    """
    Create all agents needed for a phase.
    
    Args:
        phase_agents: List of agent IDs for the phase.
        
    Returns:
        Dictionary mapping agent_id to agent instance.
    """
    agents = {}
    
    for agent_id in phase_agents:
        agent = create_agent(agent_id)
        if agent is not None:
            agents[agent_id] = agent
        else:
            logger.warning(f"Could not create agent for phase: {agent_id}")
    
    return agents


class AgentPool:
    """
    Pool of reusable agent instances.
    
    Caches agent instances for reuse across phases to avoid
    repeated initialization overhead.
    """
    
    def __init__(self):
        self._agents: dict[str, BaseAgent] = {}
    
    def get(self, agent_id: str) -> BaseAgent | None:
        """
        Get or create an agent by ID.
        
        Args:
            agent_id: Agent identifier.
            
        Returns:
            Agent instance or None.
        """
        if agent_id not in self._agents:
            agent = create_agent(agent_id)
            if agent is not None:
                self._agents[agent_id] = agent
        
        return self._agents.get(agent_id)
    
    def get_all(self, agent_ids: list[str]) -> dict[str, BaseAgent]:
        """
        Get or create multiple agents.
        
        Args:
            agent_ids: List of agent IDs.
            
        Returns:
            Dictionary of agent_id to agent instance.
        """
        result = {}
        for agent_id in agent_ids:
            agent = self.get(agent_id)
            if agent is not None:
                result[agent_id] = agent
        return result
    
    def clear(self):
        """Clear all cached agents."""
        self._agents.clear()
    
    def remove(self, agent_id: str):
        """Remove a specific agent from the pool."""
        self._agents.pop(agent_id, None)


# Global agent pool instance
_agent_pool: AgentPool | None = None


def get_agent_pool() -> AgentPool:
    """Get the global agent pool instance."""
    global _agent_pool
    if _agent_pool is None:
        _agent_pool = AgentPool()
    return _agent_pool
