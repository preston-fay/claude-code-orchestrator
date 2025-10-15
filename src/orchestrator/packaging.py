"""Artifact packaging for phase handoffs."""

import json
import zipfile
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime


def package_phase_artifacts(
    phase_name: str,
    artifact_paths: List[str],
    project_root: Path,
    run_id: str,
    metrics_digest: Optional[Dict[str, Any]] = None,
) -> Path:
    """
    Package phase artifacts into a zip bundle with manifest.

    Args:
        phase_name: Name of the phase
        artifact_paths: List of artifact file paths (relative to project_root)
        project_root: Project root directory
        run_id: Run identifier
        metrics_digest: Optional metrics summary to include in manifest

    Returns:
        Path to created zip file

    Creates:
        artifacts/{run_id}/{phase}.zip containing:
        - All artifact files
        - MANIFEST.json with metadata
    """
    # Create artifacts directory
    artifacts_dir = project_root / "artifacts" / run_id
    artifacts_dir.mkdir(parents=True, exist_ok=True)

    zip_path = artifacts_dir / f"{phase_name}.zip"

    # Prepare manifest
    manifest = {
        "phase": phase_name,
        "run_id": run_id,
        "created_at": datetime.now().isoformat(),
        "artifact_count": len(artifact_paths),
        "artifacts": artifact_paths,
        "metrics_digest": metrics_digest or {},
    }

    # Create zip file
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
        # Add manifest
        zipf.writestr("MANIFEST.json", json.dumps(manifest, indent=2))

        # Add artifacts
        for artifact_path in artifact_paths:
            full_path = project_root / artifact_path

            if not full_path.exists():
                # Log warning but continue
                print(f"Warning: Artifact not found: {artifact_path}")
                continue

            if full_path.is_file():
                # Add file with its relative path
                zipf.write(full_path, arcname=artifact_path)
            elif full_path.is_dir():
                # Add directory recursively
                for file_path in full_path.rglob("*"):
                    if file_path.is_file():
                        arcname = file_path.relative_to(project_root)
                        zipf.write(file_path, arcname=arcname)

    return zip_path


def extract_manifest(zip_path: Path) -> Dict[str, Any]:
    """
    Extract manifest from artifact bundle.

    Args:
        zip_path: Path to zip file

    Returns:
        Manifest dictionary
    """
    with zipfile.ZipFile(zip_path, "r") as zipf:
        manifest_data = zipf.read("MANIFEST.json")
        return json.loads(manifest_data)


def list_phase_bundles(project_root: Path, run_id: Optional[str] = None) -> List[Path]:
    """
    List all phase artifact bundles.

    Args:
        project_root: Project root directory
        run_id: Optional run ID to filter by

    Returns:
        List of zip file paths
    """
    artifacts_dir = project_root / "artifacts"

    if not artifacts_dir.exists():
        return []

    if run_id:
        # List bundles for specific run
        run_dir = artifacts_dir / run_id
        if run_dir.exists():
            return list(run_dir.glob("*.zip"))
        return []
    else:
        # List all bundles
        return list(artifacts_dir.glob("*/*.zip"))


def get_metrics_digest(
    phase_name: str, agent_outcomes: List[Any], validation: Optional[Any] = None
) -> Dict[str, Any]:
    """
    Create metrics digest for manifest.

    Args:
        phase_name: Phase name
        agent_outcomes: List of AgentOutcome objects
        validation: Optional ValidationResult

    Returns:
        Metrics digest dictionary
    """
    digest = {
        "phase": phase_name,
        "agents_executed": len(agent_outcomes),
        "agents_succeeded": sum(1 for o in agent_outcomes if o.success),
        "total_duration_s": sum(o.execution_time or 0 for o in agent_outcomes),
        "total_retries": sum(
            getattr(o, "retry_count", 0) for o in agent_outcomes
        ),
    }

    if validation:
        digest["validation"] = {
            "status": validation.status.value if hasattr(validation.status, "value") else str(validation.status),
            "artifacts_found": len(validation.found),
            "artifacts_missing": len(validation.missing),
        }

    # Add agent details
    digest["agents"] = []
    for outcome in agent_outcomes:
        digest["agents"].append(
            {
                "name": outcome.agent_name,
                "success": outcome.success,
                "duration_s": outcome.execution_time,
                "exit_code": outcome.exit_code,
            }
        )

    return digest
