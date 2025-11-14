"""Load CSV data with type inference and validation."""

from typing import Any, Dict, Optional


def load_csv(path: str, *, dtype: Optional[Dict[str, Any]] = None) -> Any:
    """Load CSV file into a pandas DataFrame.

    Args:
        path: Path to CSV file (relative to project root or absolute)
        dtype: Optional dict mapping column names to data types

    Returns:
        pandas.DataFrame with loaded data

    Raises:
        ImportError: If pandas is not installed
        FileNotFoundError: If CSV file does not exist
        ValueError: If CSV is malformed

    Example:
        >>> df = load_csv("data/raw/sales.csv")
        >>> df = load_csv("data/raw/sales.csv", dtype={"id": str, "amount": float})
    """
    try:
        import pandas as pd
    except ImportError as e:
        raise ImportError(
            "pandas is required for load_csv. Install with: pip install pandas"
        ) from e

    from pathlib import Path

    csv_path = Path(path)
    if not csv_path.exists():
        raise FileNotFoundError(
            f"CSV file not found: {path}\n"
            f"Working directory: {Path.cwd()}\n"
            f"Make sure the file exists and the path is correct."
        )

    try:
        df = pd.read_csv(csv_path, dtype=dtype)
        return df
    except Exception as e:
        raise ValueError(f"Failed to parse CSV file {path}: {e}") from e
