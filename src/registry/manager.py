"""
Registry Manager for Model Registry and Dataset Catalog.

Handles CRUD operations, manifest persistence, and integrity validation.
"""

import json
import hashlib
import uuid
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Dict, Any
from .schemas import (
    ModelEntry,
    DatasetEntry,
    ModelRegistry,
    DatasetCatalog,
)


class RegistryManager:
    """
    Manager for model registry and dataset catalog.

    Handles:
    - Publishing models with metrics
    - Registering datasets with schema info
    - Fetching entries by name/version
    - Listing with filters
    - Integrity verification
    """

    def __init__(self, project_root: Path):
        """
        Initialize registry manager.

        Args:
            project_root: Root directory of project
        """
        self.project_root = project_root
        self.models_path = project_root / "models" / "registry" / "releases.json"
        self.datasets_path = project_root / "datasets" / "catalog.json"

        # Ensure directories exist
        self.models_path.parent.mkdir(parents=True, exist_ok=True)
        self.datasets_path.parent.mkdir(parents=True, exist_ok=True)

        # Initialize manifests if they don't exist
        self._initialize_manifests()

    def _initialize_manifests(self):
        """Initialize manifest files if they don't exist."""
        if not self.models_path.exists():
            registry = ModelRegistry(updated_at=datetime.utcnow().isoformat() + "Z", models=[])
            self._write_models_manifest(registry)

        if not self.datasets_path.exists():
            catalog = DatasetCatalog(updated_at=datetime.utcnow().isoformat() + "Z", datasets=[])
            self._write_datasets_manifest(catalog)

    def _read_models_manifest(self) -> ModelRegistry:
        """Read models manifest from disk."""
        with open(self.models_path, "r") as f:
            data = json.load(f)
        return ModelRegistry(**data)

    def _write_models_manifest(self, registry: ModelRegistry):
        """Write models manifest to disk (atomic)."""
        registry.updated_at = datetime.utcnow().isoformat() + "Z"

        # Write to temp file first
        temp_path = self.models_path.with_suffix(".tmp")
        with open(temp_path, "w") as f:
            json.dump(registry.model_dump(by_alias=True), f, indent=2)

        # Atomic rename
        temp_path.replace(self.models_path)

    def _read_datasets_manifest(self) -> DatasetCatalog:
        """Read datasets manifest from disk."""
        with open(self.datasets_path, "r") as f:
            data = json.load(f)
        return DatasetCatalog(**data)

    def _write_datasets_manifest(self, catalog: DatasetCatalog):
        """Write datasets manifest to disk (atomic)."""
        catalog.updated_at = datetime.utcnow().isoformat() + "Z"

        # Write to temp file first
        temp_path = self.datasets_path.with_suffix(".tmp")
        with open(temp_path, "w") as f:
            json.dump(catalog.model_dump(by_alias=True), f, indent=2)

        # Atomic rename
        temp_path.replace(self.datasets_path)

    def _compute_file_hash(self, file_path: Path) -> str:
        """Compute SHA256 hash of file."""
        sha256 = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                sha256.update(chunk)
        return sha256.hexdigest()

    def _compute_schema_hash(self, file_path: Path) -> str:
        """
        Compute schema hash for dataset.

        For parquet: hash of schema
        For CSV: hash of header row
        """
        if file_path.suffix == ".parquet":
            try:
                import pyarrow.parquet as pq

                table = pq.read_table(file_path)
                schema_str = str(table.schema)
                return hashlib.sha256(schema_str.encode()).hexdigest()
            except ImportError:
                # Fallback: hash first 8KB
                pass

        # Fallback: hash first chunk
        sha256 = hashlib.sha256()
        with open(file_path, "rb") as f:
            sha256.update(f.read(8192))
        return sha256.hexdigest()

    def publish_model(
        self,
        name: str,
        version: str,
        artifacts: List[str],
        metrics: Optional[Dict[str, float]] = None,
        cleanliness_score: Optional[int] = None,
        release_tag: Optional[str] = None,
        client: Optional[str] = None,
        notes: Optional[str] = None,
    ) -> ModelEntry:
        """
        Publish a model to the registry.

        Args:
            name: Model name (lowercase, hyphens/underscores)
            version: Semantic version (e.g., 1.0.0)
            artifacts: List of artifact paths relative to project root
            metrics: Model metrics (e.g., {"rmse": 0.12, "r2": 0.89})
            cleanliness_score: Data cleanliness score (0-100)
            release_tag: Release tag (e.g., v1.0.0)
            client: Client slug
            notes: Release notes

        Returns:
            Created model entry

        Raises:
            FileNotFoundError: If primary artifact doesn't exist
            ValueError: If model+version already exists
        """
        # Validate primary artifact exists
        primary_artifact = self.project_root / artifacts[0]
        if not primary_artifact.exists():
            raise FileNotFoundError(f"Primary artifact not found: {artifacts[0]}")

        # Compute hash
        sha256 = self._compute_file_hash(primary_artifact)

        # Check for duplicates
        registry = self._read_models_manifest()
        for model in registry.models:
            if model.name == name and model.version == version:
                raise ValueError(f"Model {name} v{version} already exists")

        # Create entry
        entry = ModelEntry(
            id=str(uuid.uuid4()),
            name=name,
            version=version,
            created_at=datetime.utcnow().isoformat() + "Z",
            sha256=sha256,
            metrics=metrics or {},
            artifacts=artifacts,
            cleanliness_score=cleanliness_score,
            release_tag=release_tag,
            client=client,
            notes=notes,
        )

        # Add to registry
        registry.models.append(entry)
        self._write_models_manifest(registry)

        return entry

    def register_dataset(
        self,
        name: str,
        version: str,
        artifacts: List[str],
        row_count: int,
        cleanliness_score: Optional[int] = None,
        release_tag: Optional[str] = None,
        client: Optional[str] = None,
        notes: Optional[str] = None,
    ) -> DatasetEntry:
        """
        Register a dataset in the catalog.

        Args:
            name: Dataset name (lowercase, hyphens/underscores)
            version: Semantic version (e.g., 1.0.0)
            artifacts: List of artifact paths relative to project root
            row_count: Number of rows in dataset
            cleanliness_score: Data cleanliness score (0-100)
            release_tag: Release tag (e.g., v1.0.0)
            client: Client slug
            notes: Dataset description

        Returns:
            Created dataset entry

        Raises:
            FileNotFoundError: If primary artifact doesn't exist
            ValueError: If dataset+version already exists
        """
        # Validate primary artifact exists
        primary_artifact = self.project_root / artifacts[0]
        if not primary_artifact.exists():
            raise FileNotFoundError(f"Primary artifact not found: {artifacts[0]}")

        # Compute hashes
        sha256 = self._compute_file_hash(primary_artifact)
        schema_hash = self._compute_schema_hash(primary_artifact)

        # Check for duplicates
        catalog = self._read_datasets_manifest()
        for dataset in catalog.datasets:
            if dataset.name == name and dataset.version == version:
                raise ValueError(f"Dataset {name} v{version} already exists")

        # Create entry
        entry = DatasetEntry(
            id=str(uuid.uuid4()),
            name=name,
            version=version,
            created_at=datetime.utcnow().isoformat() + "Z",
            sha256=sha256,
            row_count=row_count,
            schema_hash=schema_hash,
            artifacts=artifacts,
            cleanliness_score=cleanliness_score,
            release_tag=release_tag,
            client=client,
            notes=notes,
        )

        # Add to catalog
        catalog.datasets.append(entry)
        self._write_datasets_manifest(catalog)

        return entry

    def get_model(self, name: str, version: Optional[str] = None) -> Optional[ModelEntry]:
        """
        Get model by name and optional version.

        Args:
            name: Model name
            version: Version (latest if not specified)

        Returns:
            Model entry or None if not found
        """
        registry = self._read_models_manifest()

        # Filter by name
        matches = [m for m in registry.models if m.name == name]
        if not matches:
            return None

        # Filter by version or get latest
        if version:
            for model in matches:
                if model.version == version:
                    return model
            return None
        else:
            # Return latest version (sort by semver)
            return max(matches, key=lambda m: tuple(map(int, m.version.split("."))))

    def get_dataset(self, name: str, version: Optional[str] = None) -> Optional[DatasetEntry]:
        """
        Get dataset by name and optional version.

        Args:
            name: Dataset name
            version: Version (latest if not specified)

        Returns:
            Dataset entry or None if not found
        """
        catalog = self._read_datasets_manifest()

        # Filter by name
        matches = [d for d in catalog.datasets if d.name == name]
        if not matches:
            return None

        # Filter by version or get latest
        if version:
            for dataset in matches:
                if dataset.version == version:
                    return dataset
            return None
        else:
            # Return latest version (sort by semver)
            return max(matches, key=lambda d: tuple(map(int, d.version.split("."))))

    def list_models(
        self, client: Optional[str] = None, release_tag: Optional[str] = None
    ) -> List[ModelEntry]:
        """
        List models with optional filters.

        Args:
            client: Filter by client slug
            release_tag: Filter by release tag

        Returns:
            List of matching models
        """
        registry = self._read_models_manifest()
        models = registry.models

        if client:
            models = [m for m in models if m.client == client]

        if release_tag:
            models = [m for m in models if m.release_tag == release_tag]

        return models

    def list_datasets(
        self, client: Optional[str] = None, release_tag: Optional[str] = None
    ) -> List[DatasetEntry]:
        """
        List datasets with optional filters.

        Args:
            client: Filter by client slug
            release_tag: Filter by release tag

        Returns:
            List of matching datasets
        """
        catalog = self._read_datasets_manifest()
        datasets = catalog.datasets

        if client:
            datasets = [d for d in datasets if d.client == client]

        if release_tag:
            datasets = [d for d in datasets if d.release_tag == release_tag]

        return datasets

    def verify_integrity(self) -> Dict[str, Any]:
        """
        Verify integrity of registry and catalog.

        Checks:
        - All artifact files exist
        - SHA256 hashes match
        - Manifest file sizes

        Returns:
            Dict with verification results
        """
        results = {
            "valid": True,
            "errors": [],
            "warnings": [],
            "models_checked": 0,
            "datasets_checked": 0,
        }

        # Check models
        registry = self._read_models_manifest()
        for model in registry.models:
            results["models_checked"] += 1

            # Check primary artifact
            primary_artifact = self.project_root / model.artifacts[0]
            if not primary_artifact.exists():
                results["valid"] = False
                results["errors"].append(f"Model {model.name} v{model.version}: Artifact not found: {model.artifacts[0]}")
                continue

            # Verify hash
            actual_hash = self._compute_file_hash(primary_artifact)
            if actual_hash != model.sha256:
                results["valid"] = False
                results["errors"].append(
                    f"Model {model.name} v{model.version}: Hash mismatch (expected {model.sha256[:8]}..., got {actual_hash[:8]}...)"
                )

        # Check datasets
        catalog = self._read_datasets_manifest()
        for dataset in catalog.datasets:
            results["datasets_checked"] += 1

            # Check primary artifact
            primary_artifact = self.project_root / dataset.artifacts[0]
            if not primary_artifact.exists():
                results["valid"] = False
                results["errors"].append(
                    f"Dataset {dataset.name} v{dataset.version}: Artifact not found: {dataset.artifacts[0]}"
                )
                continue

            # Verify hash
            actual_hash = self._compute_file_hash(primary_artifact)
            if actual_hash != dataset.sha256:
                results["valid"] = False
                results["errors"].append(
                    f"Dataset {dataset.name} v{dataset.version}: Hash mismatch (expected {dataset.sha256[:8]}..., got {actual_hash[:8]}...)"
                )

        # Check manifest sizes
        if self.models_path.stat().st_size > 10 * 1024 * 1024:  # 10 MB
            results["warnings"].append(f"Models manifest exceeds 10 MB ({self.models_path.stat().st_size / 1024 / 1024:.1f} MB)")

        if self.datasets_path.stat().st_size > 10 * 1024 * 1024:  # 10 MB
            results["warnings"].append(
                f"Datasets manifest exceeds 10 MB ({self.datasets_path.stat().st_size / 1024 / 1024:.1f} MB)"
            )

        return results

    def get_stats(self) -> Dict[str, Any]:
        """
        Get aggregate statistics.

        Returns:
            Dict with stats (count by client, avg cleanliness, etc.)
        """
        registry = self._read_models_manifest()
        catalog = self._read_datasets_manifest()

        # Models stats
        models_by_client: Dict[str, int] = {}
        model_cleanliness_scores = []

        for model in registry.models:
            if model.client:
                models_by_client[model.client] = models_by_client.get(model.client, 0) + 1
            if model.cleanliness_score is not None:
                model_cleanliness_scores.append(model.cleanliness_score)

        # Datasets stats
        datasets_by_client: Dict[str, int] = {}
        dataset_cleanliness_scores = []

        for dataset in catalog.datasets:
            if dataset.client:
                datasets_by_client[dataset.client] = datasets_by_client.get(dataset.client, 0) + 1
            if dataset.cleanliness_score is not None:
                dataset_cleanliness_scores.append(dataset.cleanliness_score)

        return {
            "models_total": len(registry.models),
            "datasets_total": len(catalog.datasets),
            "models_by_client": models_by_client,
            "datasets_by_client": datasets_by_client,
            "avg_model_cleanliness": sum(model_cleanliness_scores) / len(model_cleanliness_scores)
            if model_cleanliness_scores
            else None,
            "avg_dataset_cleanliness": sum(dataset_cleanliness_scores) / len(dataset_cleanliness_scores)
            if dataset_cleanliness_scores
            else None,
        }
