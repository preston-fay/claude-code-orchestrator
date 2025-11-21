"""
Centralized environment configuration for Orchestrator v2.

This module provides a single source of truth for all environment variables
and configuration settings used throughout the orchestrator.
"""

import os
from pathlib import Path
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings


class OrchestratorSettings(BaseSettings):
    """Orchestrator environment settings.

    All settings can be configured via environment variables or .env file.
    """

    # Workspace settings
    workspace_base: str = Field(
        default="~/.orchestrator/workspaces",
        description="Base directory for project workspaces"
    )

    # Logging settings
    logs_dir: str = Field(
        default="~/.orchestrator/logs",
        description="Directory for orchestrator logs"
    )

    # Environment
    env: str = Field(
        default="development",
        description="Environment name (development, staging, production)"
    )

    # LLM Provider settings
    default_llm_provider: str = Field(
        default="anthropic",
        description="Default LLM provider (anthropic, bedrock)"
    )

    default_model: str = Field(
        default="claude-3-5-sonnet-20241022",
        description="Default model to use for agents"
    )

    # API settings
    api_host: str = Field(
        default="0.0.0.0",
        description="API server host"
    )

    api_port: int = Field(
        default=8000,
        description="API server port"
    )

    # Token budget settings
    default_token_budget: int = Field(
        default=100000,
        description="Default token budget per project"
    )

    # Persistence settings
    data_dir: str = Field(
        default="~/.orchestrator/data",
        description="Directory for persistent data (projects, checkpoints)"
    )

    # Events settings
    events_dir: str = Field(
        default="runs",
        description="Directory for event logs"
    )

    # AWS settings (for Bedrock)
    aws_region: str = Field(
        default="us-east-1",
        description="AWS region for Bedrock"
    )

    class Config:
        env_file = ".env"
        env_prefix = "ORCHESTRATOR_"
        case_sensitive = False

    def get_workspace_base_path(self) -> Path:
        """Get the expanded workspace base path."""
        return Path(self.workspace_base).expanduser()

    def get_logs_dir_path(self) -> Path:
        """Get the expanded logs directory path."""
        return Path(self.logs_dir).expanduser()

    def get_data_dir_path(self) -> Path:
        """Get the expanded data directory path."""
        return Path(self.data_dir).expanduser()


# Global settings instance
settings = OrchestratorSettings()


def get_settings() -> OrchestratorSettings:
    """Get the global settings instance.

    Returns:
        OrchestratorSettings instance.
    """
    return settings
