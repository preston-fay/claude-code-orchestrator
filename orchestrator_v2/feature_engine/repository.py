"""
Feature Engine Repository

File-system based storage for feature requests.
"""

import json
from datetime import datetime
from pathlib import Path

from orchestrator_v2.feature_engine.models import FeatureRequest, FeatureStatus


class FeatureRepository:
    """Repository for storing and retrieving features."""

    def __init__(self, projects_root: Path | None = None):
        self.projects_root = projects_root or Path.home() / ".orchestrator" / "projects"

    def _get_features_dir(self, project_id: str) -> Path:
        """Get the features directory for a project."""
        return self.projects_root / project_id / "features"

    def _get_feature_path(self, project_id: str, feature_id: str) -> Path:
        """Get the path to a feature's JSON file."""
        return self._get_features_dir(project_id) / f"{feature_id}.json"

    async def list_features(self, project_id: str) -> list[FeatureRequest]:
        """List all features for a project."""
        features_dir = self._get_features_dir(project_id)
        if not features_dir.exists():
            return []

        features = []
        for feature_file in sorted(features_dir.glob("*.json")):
            try:
                data = json.loads(feature_file.read_text())
                features.append(FeatureRequest(**data))
            except Exception:
                continue

        return sorted(features, key=lambda f: f.created_at, reverse=True)

    async def get_feature(self, project_id: str, feature_id: str) -> FeatureRequest | None:
        """Get a specific feature."""
        feature_path = self._get_feature_path(project_id, feature_id)
        if not feature_path.exists():
            return None

        data = json.loads(feature_path.read_text())
        return FeatureRequest(**data)

    async def save_feature(self, project_id: str, feature: FeatureRequest) -> None:
        """Save a feature to disk."""
        features_dir = self._get_features_dir(project_id)
        features_dir.mkdir(parents=True, exist_ok=True)

        feature_path = self._get_feature_path(project_id, feature.feature_id)
        feature.updated_at = datetime.utcnow()

        data = feature.model_dump(mode="json")
        feature_path.write_text(json.dumps(data, indent=2, default=str))

    async def delete_feature(self, project_id: str, feature_id: str) -> bool:
        """Delete a feature."""
        feature_path = self._get_feature_path(project_id, feature_id)
        if feature_path.exists():
            feature_path.unlink()
            return True
        return False

    async def get_next_feature_number(self, project_id: str) -> int:
        """Get the next feature number for a project."""
        features = await self.list_features(project_id)
        if not features:
            return 1

        # Extract numbers from feature IDs like "F-001", "F-002"
        max_num = 0
        for feature in features:
            if feature.feature_id.startswith("F-"):
                try:
                    num = int(feature.feature_id[2:])
                    max_num = max(max_num, num)
                except ValueError:
                    continue

        return max_num + 1


# Singleton repository instance
_feature_repository: FeatureRepository | None = None


def get_feature_repository() -> FeatureRepository:
    """Get the singleton feature repository instance."""
    global _feature_repository
    if _feature_repository is None:
        _feature_repository = FeatureRepository()
    return _feature_repository
