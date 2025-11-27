"""
Agent implementations for Orchestrator v2.

This module contains the base agent protocol and all specialized
role agents that execute workflow tasks.

LLM Integration:
- Agents support real LLM calls when AgentContext is provided
- Uses prompt templates from subagent_prompts/ directory
- Falls back to simulated responses without LLM context

See ADR-001 for agent architecture details.
"""

from orchestrator_v2.agents.base_agent import BaseAgent, BaseAgentConfig, AgentEvent
from orchestrator_v2.agents.architect import ArchitectAgent, create_architect_agent
from orchestrator_v2.agents.data_agent import DataAgent, create_data_agent
from orchestrator_v2.agents.developer import DeveloperAgent, create_developer_agent
from orchestrator_v2.agents.qa import QAAgent, create_qa_agent
from orchestrator_v2.agents.documentarian import DocumentarianAgent, create_documentarian_agent
from orchestrator_v2.agents.consensus import ConsensusAgent, create_consensus_agent
from orchestrator_v2.agents.steward import StewardAgent, create_steward_agent
from orchestrator_v2.agents.reviewer import ReviewerAgent, create_reviewer_agent

# LLM integration components
from orchestrator_v2.agents.prompt_builder import (
    PromptBuilder,
    PromptTemplate,
    BuiltPrompt,
    get_prompt_builder,
)
from orchestrator_v2.agents.response_parser import (
    ResponseParser,
    PlanResponse,
    ActResponse,
    ArtifactData,
    get_response_parser,
)
from orchestrator_v2.agents.llm_agent_mixin import LlmAgentMixin

__all__ = [
    # Base
    "BaseAgent",
    "BaseAgentConfig",
    "AgentEvent",
    # Role agents
    "ArchitectAgent",
    "DataAgent",
    "DeveloperAgent",
    "QAAgent",
    "DocumentarianAgent",
    "ConsensusAgent",
    "StewardAgent",
    "ReviewerAgent",
    # Factory functions
    "create_architect_agent",
    "create_data_agent",
    "create_developer_agent",
    "create_qa_agent",
    "create_documentarian_agent",
    "create_consensus_agent",
    "create_steward_agent",
    "create_reviewer_agent",
    # LLM integration
    "PromptBuilder",
    "PromptTemplate",
    "BuiltPrompt",
    "get_prompt_builder",
    "ResponseParser",
    "PlanResponse",
    "ActResponse",
    "ArtifactData",
    "get_response_parser",
    "LlmAgentMixin",
]
