"""Test MCP module imports and basic functionality."""

import pytest
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))


def test_mcp_main_import():
    """Test that main MCP package can be imported."""
    import orchestrator.mcp
    assert orchestrator.mcp.__version__ == "0.1.0"


def test_mcp_data_imports():
    """Test that data module functions can be imported."""
    from orchestrator.mcp.data import load_csv, load_sql, validate_schema

    assert callable(load_csv)
    assert callable(load_sql)
    assert callable(validate_schema)


def test_mcp_analytics_imports():
    """Test that analytics module functions can be imported."""
    from orchestrator.mcp.analytics import describe_data, detect_drift

    assert callable(describe_data)
    assert callable(detect_drift)


def test_mcp_models_imports():
    """Test that models module functions can be imported."""
    from orchestrator.mcp.models import train_prophet, evaluate_model

    assert callable(train_prophet)
    assert callable(evaluate_model)


def test_mcp_viz_imports():
    """Test that viz module functions can be imported."""
    from orchestrator.mcp.viz import plot_distribution, generate_report

    assert callable(plot_distribution)
    assert callable(generate_report)


def test_load_csv_with_temp_file(tmp_path):
    """Test load_csv with a temporary CSV file."""
    pytest.importorskip("pandas", reason="pandas not installed")

    from orchestrator.mcp.data import load_csv
    import pandas as pd

    # Create a temporary CSV
    csv_file = tmp_path / "test.csv"
    csv_file.write_text("a,b,c\n1,2,3\n4,5,6\n")

    # Load it
    df = load_csv(str(csv_file))

    assert isinstance(df, pd.DataFrame)
    assert len(df) == 2
    assert list(df.columns) == ["a", "b", "c"]


def test_validate_schema_basic(tmp_path):
    """Test validate_schema with basic DataFrame."""
    pytest.importorskip("pandas", reason="pandas not installed")

    from orchestrator.mcp.data import validate_schema
    import pandas as pd

    df = pd.DataFrame({"x": [1, 2, 3], "y": [4, 5, 6]})

    result = validate_schema(df, ["x", "y"])

    assert result["valid"] is True
    assert result["missing_columns"] == []
    assert result["row_count"] == 3


def test_describe_data_basic():
    """Test describe_data with basic DataFrame."""
    pytest.importorskip("pandas", reason="pandas not installed")

    from orchestrator.mcp.analytics import describe_data
    import pandas as pd

    df = pd.DataFrame({"x": [1, 2, 3, 4, 5], "y": ["a", "b", "c", "d", "e"]})

    stats = describe_data(df)

    assert stats["row_count"] == 5
    assert stats["column_count"] == 2
    assert "x" in stats["numeric_columns"]
    assert "y" in stats["categorical_columns"]


def test_evaluate_model_regression():
    """Test evaluate_model for regression task."""
    pytest.importorskip("numpy", reason="numpy not installed")

    from orchestrator.mcp.models import evaluate_model
    import numpy as np

    y_true = np.array([1, 2, 3, 4, 5])
    y_pred = np.array([1.1, 2.1, 2.9, 4.2, 4.8])

    metrics = evaluate_model(y_true, y_pred, task_type="regression")

    assert "mae" in metrics
    assert "rmse" in metrics
    assert "r2" in metrics
    assert metrics["mae"] > 0
    assert metrics["rmse"] > 0


def test_generate_report_basic(tmp_path):
    """Test generate_report with basic markdown."""
    from orchestrator.mcp.viz import generate_report

    markdown = """
# Test Report

## Summary
- Item 1
- Item 2

## Details
Some text here.
"""

    output_path = str(tmp_path / "report.html")
    result_path = generate_report(markdown, output_path=output_path, title="Test")

    assert Path(result_path).exists()
    content = Path(result_path).read_text()
    assert "<h1>Test Report</h1>" in content or "Test Report" in content
    assert "Test" in content
