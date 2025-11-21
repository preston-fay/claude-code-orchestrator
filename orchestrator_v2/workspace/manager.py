"""
Workspace manager for Orchestrator v2.

Manages workspace creation, loading, and path resolution
for project isolation.

See ADR-002 for workspace architecture.
"""

import json
import subprocess
from datetime import datetime
from pathlib import Path

from orchestrator_v2.workspace.models import WorkspaceConfig, WorkspaceMetadata


class WorkspaceError(Exception):
    """Base exception for workspace operations."""
    pass


class WorkspaceNotFoundError(WorkspaceError):
    """Workspace not found."""
    pass


class WorkspaceManager:
    """Manage project workspaces.

    The WorkspaceManager handles:
    - Workspace creation with proper directory structure
    - Repository cloning or initialization
    - Workspace loading and metadata management
    - Git ignore configuration

    See ADR-002 for workspace design.
    """

    def __init__(self, base_dir: Path | None = None):
        """Initialize workspace manager.

        Args:
            base_dir: Base directory for all workspaces.
                     Defaults to ~/.orchestrator/workspaces
        """
        if base_dir is None:
            base_dir = Path.home() / ".orchestrator" / "workspaces"
        self.base_dir = base_dir
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def create_workspace(
        self,
        project_id: str,
        git_url: str | None = None,
        template_repo: str | None = None,
        workspace_root: Path | None = None,
        metadata: dict | None = None,
    ) -> WorkspaceConfig:
        """Create a new workspace for a project.

        Args:
            project_id: Unique project identifier.
            git_url: Optional Git URL to clone.
            template_repo: Optional template repository path.
            workspace_root: Optional custom workspace root.
            metadata: Optional additional metadata.

        Returns:
            Created WorkspaceConfig.

        Raises:
            WorkspaceError: If workspace creation fails.
        """
        # Determine workspace root
        if workspace_root is None:
            workspace_root = self.base_dir / project_id

        # Check if already exists
        if workspace_root.exists():
            raise WorkspaceError(f"Workspace already exists: {workspace_root}")

        # Create directory structure
        repo_path = workspace_root / "repo"
        state_path = workspace_root / ".orchestrator"
        artifacts_path = workspace_root / "artifacts"
        logs_path = workspace_root / "logs"
        tmp_path = workspace_root / "tmp"

        for path in [workspace_root, repo_path, state_path, artifacts_path, logs_path, tmp_path]:
            path.mkdir(parents=True, exist_ok=True)

        # Create subdirectories in state
        (state_path / "checkpoints").mkdir(exist_ok=True)
        (state_path / "governance").mkdir(exist_ok=True)

        # Clone or initialize repository
        if git_url:
            self._clone_repo(git_url, repo_path)
        elif template_repo:
            self._copy_template(template_repo, repo_path)
        else:
            self._init_repo(repo_path)

        # Ensure .orchestrator is gitignored
        self._sanitize_repo_directory(repo_path, workspace_root)

        # Create workspace config
        config = WorkspaceConfig(
            project_id=project_id,
            workspace_root=workspace_root,
            repo_path=repo_path,
            state_path=state_path,
            artifacts_path=artifacts_path,
            logs_path=logs_path,
            tmp_path=tmp_path,
            git_url=git_url,
            metadata=metadata or {},
        )

        # Save workspace metadata
        self._save_workspace_metadata(config)

        return config

    def load_workspace(self, project_id: str) -> WorkspaceConfig:
        """Load an existing workspace.

        Args:
            project_id: Project identifier.

        Returns:
            Loaded WorkspaceConfig.

        Raises:
            WorkspaceNotFoundError: If workspace not found.
        """
        workspace_root = self.base_dir / project_id
        metadata_path = workspace_root / ".orchestrator" / "workspace.json"

        if not metadata_path.exists():
            raise WorkspaceNotFoundError(f"Workspace not found: {project_id}")

        # Load metadata
        metadata = WorkspaceMetadata.model_validate_json(metadata_path.read_text())

        # Create config
        config = WorkspaceConfig(
            project_id=metadata.project_id,
            workspace_root=workspace_root,
            repo_path=workspace_root / "repo",
            state_path=workspace_root / ".orchestrator",
            artifacts_path=workspace_root / "artifacts",
            logs_path=workspace_root / "logs",
            tmp_path=workspace_root / "tmp",
            git_url=metadata.git_url,
            metadata=metadata.metadata,
            created_at=metadata.created_at,
        )

        # Update last accessed
        metadata.last_accessed = datetime.utcnow()
        metadata_path.write_text(metadata.model_dump_json(indent=2))

        return config

    def list_workspaces(self) -> list[str]:
        """List all workspace project IDs.

        Returns:
            List of project IDs.
        """
        workspaces = []
        for path in self.base_dir.iterdir():
            if path.is_dir():
                metadata_path = path / ".orchestrator" / "workspace.json"
                if metadata_path.exists():
                    workspaces.append(path.name)
        return workspaces

    def delete_workspace(self, project_id: str) -> None:
        """Delete a workspace.

        Args:
            project_id: Project identifier.

        Raises:
            WorkspaceNotFoundError: If workspace not found.
        """
        import shutil

        workspace_root = self.base_dir / project_id

        if not workspace_root.exists():
            raise WorkspaceNotFoundError(f"Workspace not found: {project_id}")

        shutil.rmtree(workspace_root)

    def _clone_repo(self, git_url: str, destination: Path) -> None:
        """Clone a Git repository.

        Args:
            git_url: Repository URL.
            destination: Clone destination.
        """
        try:
            subprocess.run(
                ["git", "clone", git_url, str(destination)],
                check=True,
                capture_output=True,
                text=True,
            )
        except subprocess.CalledProcessError as e:
            raise WorkspaceError(f"Failed to clone repository: {e.stderr}")

    def _init_repo(self, destination: Path) -> None:
        """Initialize a new Git repository.

        Args:
            destination: Repository path.
        """
        try:
            subprocess.run(
                ["git", "init"],
                cwd=destination,
                check=True,
                capture_output=True,
                text=True,
            )
        except subprocess.CalledProcessError as e:
            raise WorkspaceError(f"Failed to initialize repository: {e.stderr}")

    def _copy_template(self, template_repo: str, destination: Path) -> None:
        """Copy a template repository.

        Args:
            template_repo: Template repository path.
            destination: Destination path.
        """
        import shutil

        template_path = Path(template_repo)
        if not template_path.exists():
            raise WorkspaceError(f"Template not found: {template_repo}")

        shutil.copytree(template_path, destination, dirs_exist_ok=True)

        # Initialize as new repo (remove old .git)
        old_git = destination / ".git"
        if old_git.exists():
            shutil.rmtree(old_git)
        self._init_repo(destination)

    def _sanitize_repo_directory(self, repo_path: Path, workspace_root: Path) -> None:
        """Ensure orchestrator directories are gitignored.

        Args:
            repo_path: Repository path.
            workspace_root: Workspace root path.
        """
        gitignore_path = repo_path / ".gitignore"

        # Items to ignore (relative to repo)
        ignore_items = [
            "# Orchestrator workspace (auto-generated)",
            "../.orchestrator/",
            "../artifacts/",
            "../logs/",
            "../tmp/",
        ]

        # Read existing gitignore
        existing_content = ""
        if gitignore_path.exists():
            existing_content = gitignore_path.read_text()

        # Check if already configured
        if "# Orchestrator workspace" in existing_content:
            return

        # Append ignore items
        new_content = existing_content
        if not new_content.endswith("\n"):
            new_content += "\n"
        new_content += "\n".join(ignore_items) + "\n"

        gitignore_path.write_text(new_content)

    def _save_workspace_metadata(self, config: WorkspaceConfig) -> None:
        """Save workspace metadata to file.

        Args:
            config: Workspace configuration.
        """
        metadata = WorkspaceMetadata(
            project_id=config.project_id,
            workspace_root=str(config.workspace_root),
            git_url=config.git_url,
            created_at=config.created_at,
            metadata=config.metadata,
        )

        metadata_path = config.state_path / "workspace.json"
        metadata_path.write_text(metadata.model_dump_json(indent=2))
