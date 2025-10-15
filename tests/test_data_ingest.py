"""Tests for data ingestion functionality."""

import pytest
from pathlib import Path
import sys

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


@pytest.fixture
def sample_data_path():
    """Path to sample data file."""
    return Path(__file__).parent.parent / "data" / "external" / "sample" / "sample_data.csv"


@pytest.fixture
def temp_raw_dir(tmp_path):
    """Temporary directory for raw data."""
    raw_dir = tmp_path / "raw"
    raw_dir.mkdir()
    return raw_dir


def test_sample_data_exists(sample_data_path):
    """Test that sample data file exists."""
    assert sample_data_path.exists(), "Sample data file should exist"


def test_sample_data_format(sample_data_path):
    """Test that sample data has correct format."""
    try:
        import pandas as pd
    except ImportError:
        pytest.skip("pandas not installed")

    df = pd.read_csv(sample_data_path)

    # Check expected columns
    expected_cols = ['id', 'feature_a', 'feature_b', 'feature_c', 'target']
    assert list(df.columns) == expected_cols, "Sample data should have expected columns"

    # Check has data
    assert len(df) > 0, "Sample data should not be empty"

    # Check no nulls in sample
    assert df.isnull().sum().sum() == 0, "Sample data should have no nulls"


def test_ingest_creates_output():
    """Test that ingest command creates output file."""
    # This is a placeholder for actual CLI testing
    # In a real implementation, you'd use typer.testing.CliRunner
    assert True  # Placeholder


@pytest.mark.integration
def test_ingest_sample_data_integration(sample_data_path, temp_raw_dir):
    """Integration test: Ingest sample data to raw directory."""
    try:
        import pandas as pd
    except ImportError:
        pytest.skip("pandas not installed")

    # Simulate ingest: read from sample, write to raw
    df = pd.read_csv(sample_data_path)
    output_path = temp_raw_dir / "ingested.csv"
    df.to_csv(output_path, index=False)

    # Verify output
    assert output_path.exists(), "Ingested file should exist"

    df_loaded = pd.read_csv(output_path)
    assert len(df_loaded) == len(df), "Ingested data should have same row count"


def test_ingest_handles_missing_source():
    """Test that ingest handles missing source file gracefully."""
    # Placeholder for error handling test
    assert True
