"""
Governance runner for nightly profiling and snapshot generation.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any

from .profiling import profile_dataset, profile_model, persist_profile, detect_drift


def load_latest_profile(kind: str, name: str, profiles_dir: Path = Path("governance/profiles")) -> Dict[str, Any] | None:
    """
    Load the latest profile for a given resource.

    Args:
        kind: "dataset" or "model"
        name: Resource name
        profiles_dir: Profiles directory

    Returns:
        Latest profile dictionary or None
    """
    profile_file = profiles_dir / f"{kind}s.ndjson"

    if not profile_file.exists():
        return None

    # Read all profiles for this resource
    profiles = []
    with open(profile_file) as f:
        for line in f:
            entry = json.loads(line)
            if entry.get("name") == name:
                profiles.append(entry)

    if not profiles:
        return None

    # Return most recent
    return sorted(profiles, key=lambda x: x["timestamp"], reverse=True)[0]


def run_nightly(
    datasets_dir: Path = Path("datasets"),
    models_dir: Path = Path("models"),
    profiles_dir: Path = Path("governance/profiles"),
    snapshots_dir: Path = Path("governance/snapshots"),
) -> Dict[str, Any]:
    """
    Run nightly governance profiling.

    Args:
        datasets_dir: Directory containing datasets
        models_dir: Directory containing models
        profiles_dir: Directory for profile storage
        snapshots_dir: Directory for snapshot storage

    Returns:
        Summary dictionary
    """
    summary = {
        "timestamp": datetime.utcnow().isoformat(),
        "datasets_profiled": 0,
        "models_profiled": 0,
        "drift_detected": [],
        "errors": [],
    }

    # Profile datasets
    if datasets_dir.exists():
        for dataset_path in datasets_dir.rglob("*.csv"):
            try:
                name = dataset_path.stem
                version = "latest"

                # Load previous profile for drift detection
                prev_profile = load_latest_profile("dataset", name, profiles_dir)

                # Compute new profile
                stats = profile_dataset(dataset_path)

                # Detect drift if previous exists
                if prev_profile:
                    drift = detect_drift(prev_profile["stats"], stats)
                    if drift.get("threshold_flags"):
                        summary["drift_detected"].append({
                            "kind": "dataset",
                            "name": name,
                            "flags": drift["threshold_flags"],
                        })

                # Persist
                persist_profile("dataset", name, version, stats, profiles_dir)
                summary["datasets_profiled"] += 1

            except Exception as e:
                summary["errors"].append({
                    "kind": "dataset",
                    "path": str(dataset_path),
                    "error": str(e),
                })

        # Also check for parquet files
        for dataset_path in datasets_dir.rglob("*.parquet"):
            try:
                name = dataset_path.stem
                version = "latest"

                prev_profile = load_latest_profile("dataset", name, profiles_dir)
                stats = profile_dataset(dataset_path)

                if prev_profile:
                    drift = detect_drift(prev_profile["stats"], stats)
                    if drift.get("threshold_flags"):
                        summary["drift_detected"].append({
                            "kind": "dataset",
                            "name": name,
                            "flags": drift["threshold_flags"],
                        })

                persist_profile("dataset", name, version, stats, profiles_dir)
                summary["datasets_profiled"] += 1

            except Exception as e:
                summary["errors"].append({
                    "kind": "dataset",
                    "path": str(dataset_path),
                    "error": str(e),
                })

    # Profile models
    if models_dir.exists():
        for model_path in models_dir.rglob("*.pkl"):
            try:
                name = model_path.stem
                version = "latest"

                # Look for accompanying metrics.json
                metrics_path = model_path.parent / f"{name}_metrics.json"
                if not metrics_path.exists():
                    metrics_path = model_path.parent / "metrics.json"
                if not metrics_path.exists():
                    metrics_path = None

                # Compute profile
                stats = profile_model(model_path, metrics_path)

                # Persist
                persist_profile("model", name, version, stats, profiles_dir)
                summary["models_profiled"] += 1

            except Exception as e:
                summary["errors"].append({
                    "kind": "model",
                    "path": str(model_path),
                    "error": str(e),
                })

    # Create daily snapshot
    snapshots_dir.mkdir(parents=True, exist_ok=True)
    snapshot_date = datetime.utcnow().strftime("%Y-%m-%d")
    snapshot_path = snapshots_dir / f"{snapshot_date}.json"

    snapshot = {
        "date": snapshot_date,
        "timestamp": summary["timestamp"],
        "summary": {
            "datasets": summary["datasets_profiled"],
            "models": summary["models_profiled"],
            "drift_alerts": len(summary["drift_detected"]),
            "errors": len(summary["errors"]),
        },
        "drift_detected": summary["drift_detected"],
        "errors": summary["errors"][:10],  # Limit to first 10 errors
    }

    with open(snapshot_path, "w") as f:
        json.dump(snapshot, f, indent=2)

    return summary


def rebuild_snapshot(
    date_str: str,
    profiles_dir: Path = Path("governance/profiles"),
    snapshots_dir: Path = Path("governance/snapshots"),
) -> Dict[str, Any]:
    """
    Rebuild a snapshot for a specific date.

    Args:
        date_str: Date in YYYY-MM-DD format
        profiles_dir: Profiles directory
        snapshots_dir: Snapshots directory

    Returns:
        Snapshot dictionary
    """
    # Parse date
    target_date = datetime.strptime(date_str, "%Y-%m-%d")

    # Collect profiles from that day
    datasets_count = 0
    models_count = 0
    drift_alerts = []

    # Read dataset profiles
    dataset_file = profiles_dir / "datasets.ndjson"
    if dataset_file.exists():
        with open(dataset_file) as f:
            for line in f:
                entry = json.loads(line)
                entry_date = datetime.fromisoformat(entry["timestamp"]).date()

                if entry_date == target_date.date():
                    datasets_count += 1

    # Read model profiles
    model_file = profiles_dir / "models.ndjson"
    if model_file.exists():
        with open(model_file) as f:
            for line in f:
                entry = json.loads(line)
                entry_date = datetime.fromisoformat(entry["timestamp"]).date()

                if entry_date == target_date.date():
                    models_count += 1

    # Create snapshot
    snapshot = {
        "date": date_str,
        "timestamp": target_date.isoformat(),
        "summary": {
            "datasets": datasets_count,
            "models": models_count,
            "drift_alerts": len(drift_alerts),
            "errors": 0,
        },
        "drift_detected": drift_alerts,
        "errors": [],
    }

    # Write snapshot
    snapshots_dir.mkdir(parents=True, exist_ok=True)
    snapshot_path = snapshots_dir / f"{date_str}.json"

    with open(snapshot_path, "w") as f:
        json.dump(snapshot, f, indent=2)

    return snapshot
