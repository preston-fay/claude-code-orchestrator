"""
File system repository for Feature Orchestration Engine.

Stores feature requests, plans, and results in the project workspace.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from .models import (
    FeatureRequest,
    FeaturePlan,
    FeatureBuildPlan,
    FeatureBuildResult,
    FeatureDetail,
    FeatureStatus,
)


class FileSystemFeatureRepository:
    """Repository for storing feature data in the file system."""

    def __init__(self, base_dir: str | None = None):
        if base_dir:
            self.base_dir = Path(base_dir)
        else:
            self.base_dir = Path.home() / ".orchestrator" / "projects"

    def _get_features_dir(self, project_id: str) -> Path:
        """Get the features directory for a project."""
        return self.base_dir / project_id / "features"

    def _get_feature_dir(self, project_id: str, feature_id: str) -> Path:
        """Get the directory for a specific feature."""
        return self._get_features_dir(project_id) / feature_id

    def _ensure_dir(self, path: Path) -> None:
        """Ensure a directory exists."""
        path.mkdir(parents=True, exist_ok=True)

    def _serialize(self, obj: Any) -> str:
        """Serialize an object to JSON."""
        if hasattr(obj, 'model_dump'):
            data = obj.model_dump()
        else:
            data = obj

        def convert(o):
            if isinstance(o, datetime):
                return o.isoformat()
            if hasattr(o, 'value'):  # Enum
                return o.value
            return o

        return json.dumps(data, default=convert, indent=2)

    def _deserialize(self, content: str, model_class: type) -> Any:
        """Deserialize JSON to a model object."""
        data = json.loads(content)
        return model_class(**data)

    # Feature Request operations

    def save_request(self, request: FeatureRequest) -> None:
        """Save a feature request."""
        feature_dir = self._get_feature_dir(request.project_id, request.id)
        self._ensure_dir(feature_dir)

        request_path = feature_dir / "request.json"
        request_path.write_text(self._serialize(request))

    def get_request(self, project_id: str, feature_id: str) -> FeatureRequest | None:
        """Get a feature request by ID."""
        request_path = self._get_feature_dir(project_id, feature_id) / "request.json"
        if not request_path.exists():
            return None

        return self._deserialize(request_path.read_text(), FeatureRequest)

    def list_requests(self, project_id: str) -> list[FeatureRequest]:
        """List all feature requests for a project."""
        features_dir = self._get_features_dir(project_id)
        if not features_dir.exists():
            return []

        requests = []
        for feature_dir in features_dir.iterdir():
            if feature_dir.is_dir():
                request_path = feature_dir / "request.json"
                if request_path.exists():
                    request = self._deserialize(request_path.read_text(), FeatureRequest)
                    requests.append(request)

        # Sort by created_at descending
        requests.sort(key=lambda r: r.created_at, reverse=True)
        return requests

    def update_request_status(
        self,
        project_id: str,
        feature_id: str,
        status: FeatureStatus
    ) -> FeatureRequest | None:
        """Update the status of a feature request."""
        request = self.get_request(project_id, feature_id)
        if not request:
            return None

        request.status = status
        request.updated_at = datetime.utcnow()
        self.save_request(request)
        return request

    # Feature Plan operations

    def save_plan(self, plan: FeaturePlan) -> None:
        """Save a feature plan."""
        feature_dir = self._get_feature_dir(plan.project_id, plan.feature_id)
        self._ensure_dir(feature_dir)

        plan_path = feature_dir / "plan.json"
        plan_path.write_text(self._serialize(plan))

    def get_plan(self, project_id: str, feature_id: str) -> FeaturePlan | None:
        """Get a feature plan by feature ID."""
        plan_path = self._get_feature_dir(project_id, feature_id) / "plan.json"
        if not plan_path.exists():
            return None

        return self._deserialize(plan_path.read_text(), FeaturePlan)

    # Feature Build Plan operations

    def save_build_plan(self, build_plan: FeatureBuildPlan) -> None:
        """Save a feature build plan."""
        feature_dir = self._get_feature_dir(build_plan.project_id, build_plan.feature_id)
        self._ensure_dir(feature_dir)

        build_plan_path = feature_dir / "build_plan.json"
        build_plan_path.write_text(self._serialize(build_plan))

    def get_build_plan(self, project_id: str, feature_id: str) -> FeatureBuildPlan | None:
        """Get a feature build plan by feature ID."""
        build_plan_path = self._get_feature_dir(project_id, feature_id) / "build_plan.json"
        if not build_plan_path.exists():
            return None

        return self._deserialize(build_plan_path.read_text(), FeatureBuildPlan)

    # Feature Build Result operations

    def save_result(self, result: FeatureBuildResult) -> None:
        """Save a feature build result."""
        feature_dir = self._get_feature_dir(result.project_id, result.feature_id)
        self._ensure_dir(feature_dir)

        result_path = feature_dir / "result.json"
        result_path.write_text(self._serialize(result))

    def get_result(self, project_id: str, feature_id: str) -> FeatureBuildResult | None:
        """Get a feature build result by feature ID."""
        result_path = self._get_feature_dir(project_id, feature_id) / "result.json"
        if not result_path.exists():
            return None

        return self._deserialize(result_path.read_text(), FeatureBuildResult)

    # Logs operations

    def append_log(self, project_id: str, feature_id: str, log_entry: str) -> None:
        """Append a log entry for a feature build."""
        logs_dir = self._get_feature_dir(project_id, feature_id) / "logs"
        self._ensure_dir(logs_dir)

        log_file = logs_dir / "build.log"
        with open(log_file, "a") as f:
            timestamp = datetime.utcnow().isoformat()
            f.write(f"[{timestamp}] {log_entry}\n")

    def get_logs(self, project_id: str, feature_id: str) -> list[str]:
        """Get all logs for a feature build."""
        log_file = self._get_feature_dir(project_id, feature_id) / "logs" / "build.log"
        if not log_file.exists():
            return []

        return log_file.read_text().strip().split("\n")

    # Combined operations

    def get_feature_detail(self, project_id: str, feature_id: str) -> FeatureDetail | None:
        """Get complete feature detail including request, plan, and result."""
        request = self.get_request(project_id, feature_id)
        if not request:
            return None

        return FeatureDetail(
            request=request,
            plan=self.get_plan(project_id, feature_id),
            build_plan=self.get_build_plan(project_id, feature_id),
            result=self.get_result(project_id, feature_id),
        )

    def delete_feature(self, project_id: str, feature_id: str) -> bool:
        """Delete a feature and all its data."""
        import shutil

        feature_dir = self._get_feature_dir(project_id, feature_id)
        if feature_dir.exists():
            shutil.rmtree(feature_dir)
            return True
        return False
