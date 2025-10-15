"""Tests for dataset profiling functionality."""

import json
from pathlib import Path
import pytest
import pandas as pd

from src.governance.profiling import profile_dataset, detect_drift, persist_profile


@pytest.fixture
def sample_csv(tmp_path):
    """Create a sample CSV dataset for testing."""
    data = {
        "id": [1, 2, 3, 4, 5],
        "name": ["A", "B", "C", "D", "E"],
        "value": [10.5, 20.3, 15.7, None, 25.1],
        "category": ["X", "Y", "X", "Y", "X"],
    }
    df = pd.DataFrame(data)

    csv_path = tmp_path / "test_dataset.csv"
    df.to_csv(csv_path, index=False)

    return csv_path


def test_profile_dataset_basic_stats(sample_csv):
    """Test that dataset profiling returns basic statistics."""
    stats = profile_dataset(sample_csv)

    assert stats["rows"] == 5
    assert stats["columns"] == 4
    assert "size_bytes" in stats
    assert "modified_at" in stats
    assert "content_hash" in stats


def test_profile_dataset_column_details(sample_csv):
    """Test that column-level statistics are computed."""
    stats = profile_dataset(sample_csv)

    columns_detail = stats["columns_detail"]

    # Check numeric column
    assert "value" in columns_detail
    assert columns_detail["value"]["null_pct"] == 20.0  # 1 out of 5
    assert "min" in columns_detail["value"]
    assert "max" in columns_detail["value"]
    assert "mean" in columns_detail["value"]

    # Check categorical column
    assert "category" in columns_detail
    assert "unique_count" in columns_detail["category"]
    assert "top_values" in columns_detail["category"]


def test_profile_dataset_duplicates(tmp_path):
    """Test duplicate detection."""
    data = {
        "col1": [1, 2, 3, 1, 2],
        "col2": ["a", "b", "c", "a", "b"],
    }
    df = pd.DataFrame(data)

    csv_path = tmp_path / "duplicates.csv"
    df.to_csv(csv_path, index=False)

    stats = profile_dataset(csv_path)

    assert stats["duplicate_rows"] == 2  # Rows 3,4 are duplicates of 0,1
    assert stats["duplicate_pct"] == 40.0


def test_detect_drift_no_change():
    """Test drift detection with identical datasets."""
    prev_stats = {
        "rows": 100,
        "columns_detail": {
            "value": {"mean": 50.0, "type": "float64"},
        },
    }

    cur_stats = {
        "rows": 100,
        "columns_detail": {
            "value": {"mean": 50.0, "type": "float64"},
        },
    }

    drift = detect_drift(prev_stats, cur_stats)

    assert drift["row_delta_pct"] == 0.0
    assert drift["column_delta"] == 0
    assert len(drift["threshold_flags"]) == 0


def test_detect_drift_numeric_change():
    """Test drift detection with numeric column changes."""
    prev_stats = {
        "rows": 100,
        "columns_detail": {
            "value": {"mean": 50.0, "type": "float64"},
        },
    }

    cur_stats = {
        "rows": 100,
        "columns_detail": {
            "value": {"mean": 70.0, "type": "float64"},  # 40% change
        },
    }

    drift = detect_drift(prev_stats, cur_stats)

    assert "value" in drift["numeric_drift"]
    assert drift["numeric_drift"]["value"]["mean_delta_pct"] == 40.0
    assert "DRIFT_VALUE" in drift["threshold_flags"]


def test_detect_drift_schema_change():
    """Test drift detection with schema changes."""
    prev_stats = {
        "rows": 100,
        "columns_detail": {
            "col1": {},
            "col2": {},
        },
    }

    cur_stats = {
        "rows": 100,
        "columns_detail": {
            "col1": {},
            "col3": {},  # col2 removed, col3 added
        },
    }

    drift = detect_drift(prev_stats, cur_stats)

    assert drift["column_delta"] == 2  # 2 columns changed
    assert "SCHEMA_CHANGE" in drift["threshold_flags"]


def test_persist_profile(tmp_path):
    """Test profile persistence to NDJSON."""
    profiles_dir = tmp_path / "profiles"

    stats = {
        "rows": 100,
        "columns": 5,
    }

    persist_profile("dataset", "test_ds", "v1.0", stats, profiles_dir)

    # Check file exists
    ndjson_file = profiles_dir / "datasets.ndjson"
    assert ndjson_file.exists()

    # Check content
    with open(ndjson_file) as f:
        line = f.readline()
        entry = json.loads(line)

    assert entry["kind"] == "dataset"
    assert entry["name"] == "test_ds"
    assert entry["version"] == "v1.0"
    assert entry["stats"] == stats


def test_profile_dataset_nulls(tmp_path):
    """Test null percentage calculation."""
    data = {
        "col1": [1, None, 3, None, 5],
        "col2": [None, None, None, None, None],
    }
    df = pd.DataFrame(data)

    csv_path = tmp_path / "nulls.csv"
    df.to_csv(csv_path, index=False)

    stats = profile_dataset(csv_path)

    assert stats["columns_detail"]["col1"]["null_pct"] == 40.0
    assert stats["columns_detail"]["col2"]["null_pct"] == 100.0
