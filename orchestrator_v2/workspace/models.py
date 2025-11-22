"""
Workspace models for Orchestrator v2.

Defines the data structures for workspace configuration
and path management.

See ADR-002 for workspace architecture.
"""

from datetime import datetime
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field


class WorkspaceConfig(BaseModel):
    """Configuration for a project workspace.

    Defines all paths for a workspace that isolates:
    - Project repository
    - Orchestrator state
    - Artifacts
    - Logs
    - Temporary files

    Directory structure:
    workspace_root/
        repo/           - Project Git repository
        .orchestrator/  - Orchestrator state and checkpoints
        artifacts/      - Generated artifacts
        logs/           - Execution logs
        tmp/            - Temporary files
    """
    project_id: str
    workspace_root: Path
    repo_path: Path
    state_path: Path
    artifacts_path: Path
    logs_path: Path
    tmp_path: Path

    # Metadata
    git_url: str | None = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    metadata: dict[str, Any] = Field(default_factory=dict)

    class Config:
        """Pydantic config."""
        arbitrary_types_allowed = True

    def resolve_repo_path(self, relative_path: str) -> Path:
        """Resolve a path relative to the repository root.

        Args:
            relative_path: Path relative to repo root.

        Returns:
            Absolute path within repo.
        """
        return self.repo_path / relative_path

    def resolve_artifact_path(self, artifact_id: str) -> Path:
        """Resolve path for an artifact.

        Args:
            artifact_id: Artifact identifier or relative path.

        Returns:
            Absolute path for artifact.
        """
        return self.artifacts_path / artifact_id

    def resolve_state_path(self, relative_path: str = "") -> Path:
        """Resolve a path within orchestrator state directory.

        Args:
            relative_path: Optional relative path.

        Returns:
            Absolute path within state directory.
        """
        if relative_path:
            return self.state_path / relative_path
        return self.state_path

    def resolve_log_path(self, log_name: str = "") -> Path:
        """Resolve path for a log file.

        Args:
            log_name: Optional log file name.

        Returns:
            Absolute path for log.
        """
        if log_name:
            return self.logs_path / log_name
        return self.logs_path

    def resolve_tmp_path(self, filename: str = "") -> Path:
        """Resolve path for a temporary file.

        Args:
            filename: Optional filename.

        Returns:
            Absolute path for temp file.
        """
        if filename:
            return self.tmp_path / filename
        return self.tmp_path


class WorkspaceMetadata(BaseModel):
    """Metadata stored in workspace.json."""
    project_id: str
    workspace_root: str
    git_url: str | None = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_accessed: datetime = Field(default_factory=datetime.utcnow)
    metadata: dict[str, Any] = Field(default_factory=dict)
