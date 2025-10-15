"""
Data and model profiling for governance.

Profiles datasets and models to track quality, drift, and health metrics.
"""

import hashlib
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import duckdb
import pandas as pd


def profile_dataset(path: Path) -> Dict[str, Any]:
    """
    Profile a dataset file to extract quality metrics.

    Args:
        path: Path to dataset file (CSV, Parquet, etc.)

    Returns:
        Dictionary with profiling statistics
    """
    # Read dataset
    if path.suffix == ".csv":
        df = pd.read_csv(path)
    elif path.suffix == ".parquet":
        df = pd.read_parquet(path)
    else:
        # Try DuckDB for other formats
        conn = duckdb.connect(":memory:")
        df = conn.execute(f"SELECT * FROM '{path}'").df()
        conn.close()

    # Basic stats
    stats = {
        "path": str(path),
        "rows": len(df),
        "columns": len(df.columns),
        "size_bytes": path.stat().st_size,
        "modified_at": datetime.fromtimestamp(path.stat().st_mtime).isoformat(),
    }

    # Column-level stats
    column_stats = {}
    for col in df.columns:
        col_type = str(df[col].dtype)
        null_count = df[col].isnull().sum()
        null_pct = (null_count / len(df)) * 100 if len(df) > 0 else 0

        col_stat = {
            "type": col_type,
            "null_count": int(null_count),
            "null_pct": round(null_pct, 2),
        }

        # Numeric columns
        if pd.api.types.is_numeric_dtype(df[col]):
            col_stat.update({
                "min": float(df[col].min()) if not df[col].isnull().all() else None,
                "max": float(df[col].max()) if not df[col].isnull().all() else None,
                "mean": float(df[col].mean()) if not df[col].isnull().all() else None,
                "std": float(df[col].std()) if not df[col].isnull().all() else None,
            })

        # Categorical columns
        elif pd.api.types.is_object_dtype(df[col]) or pd.api.types.is_categorical_dtype(df[col]):
            value_counts = df[col].value_counts()
            col_stat.update({
                "unique_count": int(df[col].nunique()),
                "top_values": value_counts.head(5).to_dict(),
            })

        column_stats[col] = col_stat

    stats["columns_detail"] = column_stats

    # Duplicates
    duplicate_count = df.duplicated().sum()
    stats["duplicate_rows"] = int(duplicate_count)
    stats["duplicate_pct"] = round((duplicate_count / len(df)) * 100 if len(df) > 0 else 0, 2)

    # Compute hash for change detection
    stats["content_hash"] = hashlib.sha256(df.to_csv(index=False).encode()).hexdigest()[:16]

    return stats


def detect_drift(prev_stats: Dict[str, Any], cur_stats: Dict[str, Any]) -> Dict[str, Any]:
    """
    Detect drift between two dataset profiles using simple PSI.

    Args:
        prev_stats: Previous profile statistics
        cur_stats: Current profile statistics

    Returns:
        Dictionary with drift metrics and flags
    """
    drift = {
        "row_delta_pct": 0.0,
        "column_delta": 0,
        "numeric_drift": {},
        "category_drift": {},
        "threshold_flags": [],
    }

    # Row count change
    prev_rows = prev_stats.get("rows", 0)
    cur_rows = cur_stats.get("rows", 0)
    if prev_rows > 0:
        drift["row_delta_pct"] = round(((cur_rows - prev_rows) / prev_rows) * 100, 2)

    # Column changes
    prev_cols = set(prev_stats.get("columns_detail", {}).keys())
    cur_cols = set(cur_stats.get("columns_detail", {}).keys())
    drift["column_delta"] = len(cur_cols.symmetric_difference(prev_cols))

    if drift["column_delta"] > 0:
        drift["threshold_flags"].append("SCHEMA_CHANGE")

    # Numeric drift (simple range comparison)
    prev_col_stats = prev_stats.get("columns_detail", {})
    cur_col_stats = cur_stats.get("columns_detail", {})

    for col in cur_cols.intersection(prev_cols):
        prev_col = prev_col_stats.get(col, {})
        cur_col = cur_col_stats.get(col, {})

        # Numeric columns - compare ranges
        if "mean" in prev_col and "mean" in cur_col:
            prev_mean = prev_col.get("mean")
            cur_mean = cur_col.get("mean")

            if prev_mean is not None and cur_mean is not None and prev_mean != 0:
                mean_delta_pct = abs((cur_mean - prev_mean) / prev_mean) * 100
                drift["numeric_drift"][col] = {
                    "mean_delta_pct": round(mean_delta_pct, 2),
                    "prev_mean": prev_mean,
                    "cur_mean": cur_mean,
                }

                # Flag if > 20% change
                if mean_delta_pct > 20:
                    drift["threshold_flags"].append(f"DRIFT_{col.upper()}")

        # Categorical columns - compare top values
        elif "top_values" in prev_col and "top_values" in cur_col:
            prev_top = set(prev_col.get("top_values", {}).keys())
            cur_top = set(cur_col.get("top_values", {}).keys())

            if prev_top:
                overlap = len(prev_top.intersection(cur_top))
                overlap_pct = (overlap / len(prev_top)) * 100
                drift["category_drift"][col] = {
                    "overlap_pct": round(overlap_pct, 2),
                    "new_categories": list(cur_top - prev_top),
                }

                # Flag if < 70% overlap
                if overlap_pct < 70:
                    drift["threshold_flags"].append(f"CAT_SHIFT_{col.upper()}")

    return drift


def profile_model(model_path: Path, metrics_path: Optional[Path] = None) -> Dict[str, Any]:
    """
    Profile a model file to extract metadata and performance metrics.

    Args:
        model_path: Path to model file
        metrics_path: Optional path to metrics.json

    Returns:
        Dictionary with model profile
    """
    stats = {
        "path": str(model_path),
        "size_bytes": model_path.stat().st_size,
        "modified_at": datetime.fromtimestamp(model_path.stat().st_mtime).isoformat(),
    }

    # Compute hash
    with open(model_path, "rb") as f:
        stats["sha256"] = hashlib.sha256(f.read()).hexdigest()

    # Load metrics if available
    if metrics_path and metrics_path.exists():
        with open(metrics_path) as f:
            metrics = json.load(f)

        stats["metrics"] = {
            "r2": metrics.get("r2"),
            "rmse": metrics.get("rmse"),
            "mae": metrics.get("mae"),
            "accuracy": metrics.get("accuracy"),
            "latency_ms": metrics.get("latency_ms"),
        }
    else:
        stats["metrics"] = {}

    return stats


def persist_profile(
    kind: str,
    name: str,
    version: str,
    stats: Dict[str, Any],
    profiles_dir: Path = Path("governance/profiles"),
) -> None:
    """
    Persist a profile as NDJSON.

    Args:
        kind: "dataset" or "model"
        name: Resource name
        version: Version string
        stats: Profile statistics
        profiles_dir: Directory for profile storage
    """
    profiles_dir.mkdir(parents=True, exist_ok=True)

    # Create NDJSON entry
    entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "kind": kind,
        "name": name,
        "version": version,
        "stats": stats,
    }

    # Append to NDJSON file
    output_file = profiles_dir / f"{kind}s.ndjson"
    with open(output_file, "a") as f:
        f.write(json.dumps(entry) + "\n")
