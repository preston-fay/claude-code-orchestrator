"""
FileSystem repository implementations for Orchestrator v2.

Implements repository interfaces using local filesystem storage
with JSON serialization for state objects.

See ADR-002 for persistence architecture.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from orchestrator_v2.core.state_models import (
    ArtifactInfo,
    CheckpointState,
    GovernanceResults,
    PhaseType,
    ProjectState,
)


class FileSystemProjectRepository:
    """FileSystem implementation of ProjectRepository."""

    def __init__(self, base_dir: Path | None = None):
        """Initialize the repository.

        Args:
            base_dir: Base directory for storage.
        """
        self.base_dir = base_dir or Path(".claude/orchestrator/projects")
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def _project_path(self, project_id: str) -> Path:
        """Get path for a project file."""
        return self.base_dir / f"{project_id}.json"

    async def save(self, project: ProjectState) -> None:
        """Save project state to filesystem."""
        path = self._project_path(project.project_id)
        data = project.model_dump(mode="json")
        path.write_text(json.dumps(data, indent=2, default=str))

    async def load(self, project_id: str) -> ProjectState:
        """Load project state from filesystem."""
        path = self._project_path(project_id)
        if not path.exists():
            raise KeyError(f"Project not found: {project_id}")

        data = json.loads(path.read_text())
        return ProjectState.model_validate(data)

    async def list_projects(self) -> list[str]:
        """List all project IDs."""
        return [
            p.stem for p in self.base_dir.glob("*.json")
        ]

    async def delete(self, project_id: str) -> None:
        """Delete a project."""
        path = self._project_path(project_id)
        if path.exists():
            path.unlink()

    async def exists(self, project_id: str) -> bool:
        """Check if project exists."""
        return self._project_path(project_id).exists()


class FileSystemCheckpointRepository:
    """FileSystem implementation of CheckpointRepository."""

    def __init__(self, base_dir: Path | None = None):
        """Initialize the repository.

        Args:
            base_dir: Base directory for storage.
        """
        self.base_dir = base_dir or Path(".claude/orchestrator/checkpoints")
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self._index: dict[str, dict[str, Any]] = {}
        self._load_index()

    def _load_index(self) -> None:
        """Load checkpoint index from disk."""
        index_path = self.base_dir / "index.json"
        if index_path.exists():
            self._index = json.loads(index_path.read_text())

    def _save_index(self) -> None:
        """Save checkpoint index to disk."""
        index_path = self.base_dir / "index.json"
        index_path.write_text(json.dumps(self._index, indent=2, default=str))

    def _checkpoint_path(self, checkpoint_id: str) -> Path:
        """Get path for a checkpoint file."""
        return self.base_dir / f"{checkpoint_id}.json"

    async def save(self, checkpoint: CheckpointState) -> None:
        """Save checkpoint state to filesystem."""
        path = self._checkpoint_path(checkpoint.id)
        data = checkpoint.model_dump(mode="json")
        path.write_text(json.dumps(data, indent=2, default=str))

        # Update index
        self._index[checkpoint.id] = {
            "project_id": checkpoint.run_id,
            "phase": checkpoint.phase.value,
            "checkpoint_type": checkpoint.checkpoint_type.value,
            "created_at": checkpoint.created_at.isoformat(),
        }
        self._save_index()

    async def load(self, checkpoint_id: str) -> CheckpointState:
        """Load checkpoint from filesystem."""
        path = self._checkpoint_path(checkpoint_id)
        if not path.exists():
            raise KeyError(f"Checkpoint not found: {checkpoint_id}")

        data = json.loads(path.read_text())
        return CheckpointState.model_validate(data)

    async def list_for_project(self, project_id: str) -> list[str]:
        """List checkpoint IDs for a project."""
        return [
            cid for cid, meta in self._index.items()
            if meta.get("project_id") == project_id
        ]

    async def list_for_phase(
        self,
        project_id: str,
        phase: PhaseType,
    ) -> list[str]:
        """List checkpoint IDs for a phase."""
        return [
            cid for cid, meta in self._index.items()
            if meta.get("project_id") == project_id
            and meta.get("phase") == phase.value
        ]

    async def get_latest(
        self,
        project_id: str,
        phase: PhaseType | None = None,
    ) -> CheckpointState | None:
        """Get the latest checkpoint."""
        candidates = []
        for cid, meta in self._index.items():
            if meta.get("project_id") != project_id:
                continue
            if phase and meta.get("phase") != phase.value:
                continue
            candidates.append((cid, meta.get("created_at", "")))

        if not candidates:
            return None

        # Sort by created_at descending
        candidates.sort(key=lambda x: x[1], reverse=True)
        return await self.load(candidates[0][0])

    async def delete(self, checkpoint_id: str) -> None:
        """Delete a checkpoint."""
        path = self._checkpoint_path(checkpoint_id)
        if path.exists():
            path.unlink()
        if checkpoint_id in self._index:
            del self._index[checkpoint_id]
            self._save_index()


class FileSystemArtifactRepository:
    """FileSystem implementation of ArtifactRepository."""

    def __init__(self, base_dir: Path | None = None):
        """Initialize the repository.

        Args:
            base_dir: Base directory for storage.
        """
        self.base_dir = base_dir or Path(".claude/orchestrator/artifacts")
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self._metadata: dict[str, list[dict[str, Any]]] = {}
        self._load_metadata()

    def _load_metadata(self) -> None:
        """Load artifact metadata from disk."""
        meta_path = self.base_dir / "metadata.json"
        if meta_path.exists():
            self._metadata = json.loads(meta_path.read_text())

    def _save_metadata(self) -> None:
        """Save artifact metadata to disk."""
        meta_path = self.base_dir / "metadata.json"
        meta_path.write_text(json.dumps(self._metadata, indent=2, default=str))

    def _artifact_dir(self, project_id: str) -> Path:
        """Get directory for project artifacts."""
        return self.base_dir / project_id

    async def save(
        self,
        project_id: str,
        artifact: ArtifactInfo,
        content: bytes,
    ) -> str:
        """Save artifact content to filesystem."""
        project_dir = self._artifact_dir(project_id)
        project_dir.mkdir(parents=True, exist_ok=True)

        # Create path based on artifact path
        artifact_file = project_dir / artifact.path.replace("/", "_")
        artifact_file.write_bytes(content)

        # Update metadata
        if project_id not in self._metadata:
            self._metadata[project_id] = []

        # Check if artifact already exists
        existing = [
            a for a in self._metadata[project_id]
            if a.get("path") == artifact.path
        ]
        if existing:
            # Update existing
            existing[0].update(artifact.model_dump(mode="json"))
        else:
            # Add new
            self._metadata[project_id].append(artifact.model_dump(mode="json"))

        self._save_metadata()
        return str(artifact_file)

    async def load(
        self,
        project_id: str,
        artifact_path: str,
    ) -> bytes:
        """Load artifact content from filesystem."""
        project_dir = self._artifact_dir(project_id)
        artifact_file = project_dir / artifact_path.replace("/", "_")

        if not artifact_file.exists():
            raise KeyError(f"Artifact not found: {artifact_path}")

        return artifact_file.read_bytes()

    async def list_for_project(self, project_id: str) -> list[ArtifactInfo]:
        """List artifacts for a project."""
        artifacts = self._metadata.get(project_id, [])
        return [ArtifactInfo.model_validate(a) for a in artifacts]

    async def list_for_phase(
        self,
        project_id: str,
        phase: PhaseType,
    ) -> list[ArtifactInfo]:
        """List artifacts for a phase."""
        artifacts = self._metadata.get(project_id, [])
        return [
            ArtifactInfo.model_validate(a)
            for a in artifacts
            if phase.value in a.get("path", "")
        ]

    async def delete(
        self,
        project_id: str,
        artifact_path: str,
    ) -> None:
        """Delete an artifact."""
        project_dir = self._artifact_dir(project_id)
        artifact_file = project_dir / artifact_path.replace("/", "_")

        if artifact_file.exists():
            artifact_file.unlink()

        # Update metadata
        if project_id in self._metadata:
            self._metadata[project_id] = [
                a for a in self._metadata[project_id]
                if a.get("path") != artifact_path
            ]
            self._save_metadata()

    async def exists(
        self,
        project_id: str,
        artifact_path: str,
    ) -> bool:
        """Check if artifact exists."""
        project_dir = self._artifact_dir(project_id)
        artifact_file = project_dir / artifact_path.replace("/", "_")
        return artifact_file.exists()


class FileSystemGovernanceLogRepository:
    """FileSystem implementation of GovernanceLogRepository."""

    def __init__(self, base_dir: Path | None = None):
        """Initialize the repository.

        Args:
            base_dir: Base directory for storage.
        """
        self.base_dir = base_dir or Path(".claude/orchestrator/governance")
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def _log_path(self, project_id: str) -> Path:
        """Get path for project governance log."""
        return self.base_dir / f"{project_id}_governance.json"

    async def log(
        self,
        project_id: str,
        phase: PhaseType,
        results: GovernanceResults,
    ) -> None:
        """Log governance evaluation results."""
        path = self._log_path(project_id)

        # Load existing logs
        logs = []
        if path.exists():
            logs = json.loads(path.read_text())

        # Add new entry
        entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "phase": phase.value,
            "passed": results.passed,
            "quality_gates": [g.model_dump(mode="json") for g in results.quality_gates],
            "compliance_checks": [c.model_dump(mode="json") for c in results.compliance_checks],
        }
        logs.append(entry)

        # Save
        path.write_text(json.dumps(logs, indent=2, default=str))

    async def get_logs(
        self,
        project_id: str,
        phase: PhaseType | None = None,
    ) -> list[dict]:
        """Get governance logs."""
        path = self._log_path(project_id)

        if not path.exists():
            return []

        logs = json.loads(path.read_text())

        if phase:
            logs = [l for l in logs if l.get("phase") == phase.value]

        return logs

    async def get_latest(
        self,
        project_id: str,
        phase: PhaseType,
    ) -> GovernanceResults | None:
        """Get latest governance results for phase."""
        logs = await self.get_logs(project_id, phase)

        if not logs:
            return None

        # Get latest by timestamp
        logs.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
        latest = logs[0]

        return GovernanceResults(
            quality_gates=[],  # Would need to reconstruct from log
            compliance_checks=[],
            passed=latest.get("passed", True),
        )
