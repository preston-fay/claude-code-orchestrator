"""
Repository adapter for Orchestrator v2.

Provides safe repository operations with path validation
to prevent unauthorized writes outside the workspace.

See ADR-002 for repository isolation architecture.
"""

import subprocess
from pathlib import Path
from typing import Any

from orchestrator_v2.workspace.models import WorkspaceConfig


class UnsafeRepoWrite(Exception):
    """Exception raised when attempting to write outside allowed paths."""
    pass


class RepoError(Exception):
    """Base exception for repository operations."""
    pass


class RepoAdapter:
    """Safe adapter for repository operations.

    The RepoAdapter ensures:
    - All writes are within allowed paths
    - Orchestrator files are never modified
    - Repository operations are properly isolated
    - Path validation prevents escapes

    See ADR-002 for security architecture.
    """

    def __init__(self, workspace: WorkspaceConfig):
        """Initialize the repo adapter.

        Args:
            workspace: Workspace configuration.
        """
        self.workspace = workspace
        self.repo_path = workspace.repo_path

    def _validate_path(self, path: Path, allowed_root: Path | None = None) -> Path:
        """Validate that a path is within allowed boundaries.

        Args:
            path: Path to validate.
            allowed_root: Root directory path must be under.

        Returns:
            Resolved absolute path.

        Raises:
            UnsafeRepoWrite: If path is outside allowed boundaries.
        """
        if allowed_root is None:
            allowed_root = self.repo_path

        # Resolve to absolute path
        if not path.is_absolute():
            path = allowed_root / path
        path = path.resolve()

        # Check path is within allowed root
        try:
            path.relative_to(allowed_root.resolve())
        except ValueError:
            raise UnsafeRepoWrite(
                f"Path {path} is outside allowed root {allowed_root}"
            )

        # Prevent writing to sensitive locations
        forbidden_patterns = [
            ".orchestrator",
            "../.orchestrator",
            "../artifacts",
            "../logs",
            "../tmp",
        ]
        path_str = str(path)
        for pattern in forbidden_patterns:
            if pattern in path_str:
                raise UnsafeRepoWrite(
                    f"Path {path} contains forbidden pattern: {pattern}"
                )

        return path

    def clone(self, git_url: str, destination: Path | None = None) -> None:
        """Clone a repository.

        Args:
            git_url: Repository URL.
            destination: Optional destination (defaults to repo_path).

        Raises:
            RepoError: If clone fails.
        """
        if destination is None:
            destination = self.repo_path

        try:
            subprocess.run(
                ["git", "clone", git_url, str(destination)],
                check=True,
                capture_output=True,
                text=True,
            )
        except subprocess.CalledProcessError as e:
            raise RepoError(f"Failed to clone: {e.stderr}")

    def init_repo(self, destination: Path | None = None) -> None:
        """Initialize a new repository.

        Args:
            destination: Optional destination (defaults to repo_path).

        Raises:
            RepoError: If init fails.
        """
        if destination is None:
            destination = self.repo_path

        try:
            subprocess.run(
                ["git", "init"],
                cwd=destination,
                check=True,
                capture_output=True,
                text=True,
            )
        except subprocess.CalledProcessError as e:
            raise RepoError(f"Failed to init: {e.stderr}")

    def apply_patch(self, patch_text: str) -> None:
        """Apply a patch to the repository.

        Args:
            patch_text: Patch content.

        Raises:
            RepoError: If patch application fails.
        """
        try:
            process = subprocess.run(
                ["git", "apply", "--check", "-"],
                cwd=self.repo_path,
                input=patch_text,
                capture_output=True,
                text=True,
            )
            if process.returncode != 0:
                raise RepoError(f"Patch check failed: {process.stderr}")

            subprocess.run(
                ["git", "apply", "-"],
                cwd=self.repo_path,
                input=patch_text,
                check=True,
                capture_output=True,
                text=True,
            )
        except subprocess.CalledProcessError as e:
            raise RepoError(f"Failed to apply patch: {e.stderr}")

    def commit(self, message: str, add_all: bool = True) -> str:
        """Create a commit.

        Args:
            message: Commit message.
            add_all: Whether to add all changes first.

        Returns:
            Commit hash.

        Raises:
            RepoError: If commit fails.
        """
        try:
            if add_all:
                subprocess.run(
                    ["git", "add", "-A"],
                    cwd=self.repo_path,
                    check=True,
                    capture_output=True,
                    text=True,
                )

            subprocess.run(
                ["git", "commit", "-m", message],
                cwd=self.repo_path,
                check=True,
                capture_output=True,
                text=True,
            )

            # Get commit hash
            result = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                cwd=self.repo_path,
                check=True,
                capture_output=True,
                text=True,
            )
            return result.stdout.strip()

        except subprocess.CalledProcessError as e:
            raise RepoError(f"Failed to commit: {e.stderr}")

    def get_status(self) -> dict[str, Any]:
        """Get repository status.

        Returns:
            Status information dict.

        Raises:
            RepoError: If status check fails.
        """
        try:
            # Get status
            status_result = subprocess.run(
                ["git", "status", "--porcelain"],
                cwd=self.repo_path,
                check=True,
                capture_output=True,
                text=True,
            )

            # Get branch
            branch_result = subprocess.run(
                ["git", "branch", "--show-current"],
                cwd=self.repo_path,
                check=True,
                capture_output=True,
                text=True,
            )

            # Parse status
            changes = []
            for line in status_result.stdout.strip().split("\n"):
                if line:
                    status = line[:2]
                    filepath = line[3:]
                    changes.append({"status": status, "path": filepath})

            return {
                "branch": branch_result.stdout.strip(),
                "changes": changes,
                "clean": len(changes) == 0,
            }

        except subprocess.CalledProcessError as e:
            raise RepoError(f"Failed to get status: {e.stderr}")

    def get_diff(self, staged: bool = False) -> str:
        """Get repository diff.

        Args:
            staged: Whether to show staged changes.

        Returns:
            Diff output.

        Raises:
            RepoError: If diff fails.
        """
        try:
            cmd = ["git", "diff"]
            if staged:
                cmd.append("--staged")

            result = subprocess.run(
                cmd,
                cwd=self.repo_path,
                check=True,
                capture_output=True,
                text=True,
            )
            return result.stdout

        except subprocess.CalledProcessError as e:
            raise RepoError(f"Failed to get diff: {e.stderr}")

    def create_or_update_file(
        self,
        relative_path: str,
        content: str,
        create_dirs: bool = True,
    ) -> Path:
        """Create or update a file in the repository.

        Args:
            relative_path: Path relative to repo root.
            content: File content.
            create_dirs: Whether to create parent directories.

        Returns:
            Absolute path to file.

        Raises:
            UnsafeRepoWrite: If path is outside repo.
        """
        file_path = self._validate_path(Path(relative_path))

        if create_dirs:
            file_path.parent.mkdir(parents=True, exist_ok=True)

        file_path.write_text(content)
        return file_path

    def safe_write_file(
        self,
        path: str | Path,
        content: str | bytes,
        allowed_root: Path | None = None,
    ) -> Path:
        """Safely write a file with path validation.

        Args:
            path: File path (relative or absolute).
            content: File content.
            allowed_root: Optional override for allowed root.

        Returns:
            Absolute path to written file.

        Raises:
            UnsafeRepoWrite: If path is outside allowed boundaries.
        """
        if allowed_root is None:
            allowed_root = self.repo_path

        file_path = self._validate_path(Path(path), allowed_root)
        file_path.parent.mkdir(parents=True, exist_ok=True)

        if isinstance(content, bytes):
            file_path.write_bytes(content)
        else:
            file_path.write_text(content)

        return file_path

    def read_file(self, relative_path: str) -> str:
        """Read a file from the repository.

        Args:
            relative_path: Path relative to repo root.

        Returns:
            File content.

        Raises:
            FileNotFoundError: If file doesn't exist.
        """
        file_path = self.repo_path / relative_path
        return file_path.read_text()

    def delete_file(self, relative_path: str) -> None:
        """Delete a file from the repository.

        Args:
            relative_path: Path relative to repo root.

        Raises:
            UnsafeRepoWrite: If path is outside repo.
        """
        file_path = self._validate_path(Path(relative_path))
        if file_path.exists():
            file_path.unlink()

    def list_files(self, pattern: str = "*") -> list[Path]:
        """List files in repository matching pattern.

        Args:
            pattern: Glob pattern.

        Returns:
            List of matching paths.
        """
        return list(self.repo_path.glob(pattern))
