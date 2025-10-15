"""
Registry API endpoints for model and dataset management.

Provides REST API for:
- Listing models/datasets with filters
- Getting metadata by name/version
- Publishing models
- Registering datasets
- Aggregate statistics
"""

from fastapi import APIRouter, HTTPException, Header
from fastapi.responses import JSONResponse
from typing import Optional, Dict, Any, List
from pathlib import Path
import json

from src.registry.manager import RegistryManager
from src.registry.schemas import (
    ModelEntry,
    DatasetEntry,
    PublishModelRequest,
    RegisterDatasetRequest,
)

router = APIRouter(prefix="/api/registry", tags=["registry"])

# Paths
PROJECT_ROOT = Path(__file__).parent.parent.parent

# API Key for write operations (simple header-based auth)
# TODO: Move to proper secrets management in Phase 10
REGISTRY_API_KEY = "kearney-registry-key"  # Placeholder


def verify_api_key(api_key: Optional[str]):
    """Verify API key for write operations."""
    if api_key != REGISTRY_API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API key")


@router.get("/models")
async def list_models(
    client: Optional[str] = None,
    release: Optional[str] = None,
):
    """
    List all models with optional filters.

    Args:
        client: Filter by client slug
        release: Filter by release tag

    Returns:
        JSON with list of models
    """
    try:
        manager = RegistryManager(PROJECT_ROOT)
        models = manager.list_models(client=client, release_tag=release)

        return {
            "count": len(models),
            "models": [model.model_dump() for model in models],
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list models: {str(e)}")


@router.get("/models/{name}")
async def get_model(
    name: str,
    version: Optional[str] = None,
):
    """
    Get model metadata by name and optional version.

    Args:
        name: Model name
        version: Version (latest if not specified)

    Returns:
        Model metadata
    """
    try:
        manager = RegistryManager(PROJECT_ROOT)
        model = manager.get_model(name, version)

        if not model:
            raise HTTPException(
                status_code=404,
                detail=f"Model not found: {name} v{version or 'latest'}",
            )

        return model.model_dump()
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get model: {str(e)}")


@router.post("/models")
async def publish_model(
    request: PublishModelRequest,
    x_api_key: Optional[str] = Header(None),
):
    """
    Publish a new model to the registry.

    Requires API key in X-API-Key header.

    Args:
        request: Model publish request
        x_api_key: API key header

    Returns:
        Created model entry
    """
    verify_api_key(x_api_key)

    try:
        manager = RegistryManager(PROJECT_ROOT)

        # Check if artifacts exist
        for artifact_path in request.artifacts:
            full_path = PROJECT_ROOT / artifact_path
            if not full_path.exists():
                raise HTTPException(
                    status_code=400,
                    detail=f"Artifact not found: {artifact_path}",
                )

        # Publish
        entry = manager.publish_model(
            name=request.name,
            version=request.version,
            artifacts=request.artifacts,
            metrics=request.metrics,
            client=request.client,
            notes=request.notes,
        )

        return {
            "success": True,
            "message": f"Model published: {entry.name} v{entry.version}",
            "model": entry.model_dump(),
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to publish model: {str(e)}")


@router.get("/datasets")
async def list_datasets(
    client: Optional[str] = None,
    release: Optional[str] = None,
):
    """
    List all datasets with optional filters.

    Args:
        client: Filter by client slug
        release: Filter by release tag

    Returns:
        JSON with list of datasets
    """
    try:
        manager = RegistryManager(PROJECT_ROOT)
        datasets = manager.list_datasets(client=client, release_tag=release)

        return {
            "count": len(datasets),
            "datasets": [dataset.model_dump() for dataset in datasets],
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list datasets: {str(e)}")


@router.get("/datasets/{name}")
async def get_dataset(
    name: str,
    version: Optional[str] = None,
):
    """
    Get dataset metadata by name and optional version.

    Args:
        name: Dataset name
        version: Version (latest if not specified)

    Returns:
        Dataset metadata
    """
    try:
        manager = RegistryManager(PROJECT_ROOT)
        dataset = manager.get_dataset(name, version)

        if not dataset:
            raise HTTPException(
                status_code=404,
                detail=f"Dataset not found: {name} v{version or 'latest'}",
            )

        return dataset.model_dump()
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get dataset: {str(e)}")


@router.post("/datasets")
async def register_dataset(
    request: RegisterDatasetRequest,
    x_api_key: Optional[str] = Header(None),
):
    """
    Register a new dataset in the catalog.

    Requires API key in X-API-Key header.

    Args:
        request: Dataset register request
        x_api_key: API key header

    Returns:
        Created dataset entry
    """
    verify_api_key(x_api_key)

    try:
        manager = RegistryManager(PROJECT_ROOT)

        # Check if artifacts exist
        for artifact_path in request.artifacts:
            full_path = PROJECT_ROOT / artifact_path
            if not full_path.exists():
                raise HTTPException(
                    status_code=400,
                    detail=f"Artifact not found: {artifact_path}",
                )

        # Register
        entry = manager.register_dataset(
            name=request.name,
            version=request.version,
            artifacts=request.artifacts,
            row_count=request.row_count,
            client=request.client,
            notes=request.notes,
        )

        return {
            "success": True,
            "message": f"Dataset registered: {entry.name} v{entry.version}",
            "dataset": entry.model_dump(),
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to register dataset: {str(e)}")


@router.get("/metrics")
async def get_metrics():
    """
    Get aggregate registry statistics.

    Returns:
        Stats including count by client, avg cleanliness, etc.
    """
    try:
        manager = RegistryManager(PROJECT_ROOT)
        stats = manager.get_stats()

        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get metrics: {str(e)}")


@router.post("/verify")
async def verify_integrity(
    x_api_key: Optional[str] = Header(None),
):
    """
    Verify integrity of registry and catalog.

    Requires API key in X-API-Key header.

    Checks:
    - All artifact files exist
    - SHA256 hashes match
    - Manifest file sizes

    Returns:
        Verification results
    """
    verify_api_key(x_api_key)

    try:
        manager = RegistryManager(PROJECT_ROOT)
        results = manager.verify_integrity()

        status_code = 200 if results["valid"] else 500

        return JSONResponse(
            status_code=status_code,
            content=results,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to verify integrity: {str(e)}")
