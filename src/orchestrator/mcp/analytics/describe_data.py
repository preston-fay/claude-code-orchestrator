"""Generate descriptive statistics for data."""

from typing import Any, Dict, List, Optional


def describe_data(
    data: Any,
    *,
    columns: Optional[List[str]] = None,
    include_percentiles: bool = True,
) -> Dict[str, Any]:
    """Generate comprehensive descriptive statistics for a DataFrame.

    Args:
        data: pandas DataFrame to analyze
        columns: Optional list of columns to analyze (default: all numeric columns)
        include_percentiles: Include 25th, 50th, 75th percentiles (default: True)

    Returns:
        Dict with descriptive statistics:
            - row_count: int
            - column_count: int
            - numeric_columns: list of column names
            - categorical_columns: list of column names
            - missing_values: dict of {column: missing_count}
            - statistics: dict of {column: {mean, std, min, max, ...}}

    Raises:
        ImportError: If pandas is not installed
        TypeError: If data is not a pandas DataFrame

    Example:
        >>> import pandas as pd
        >>> df = pd.DataFrame({"x": [1, 2, 3, 4, 5], "y": ["a", "b", "c", "d", "e"]})
        >>> stats = describe_data(df)
        >>> print(stats["row_count"])
        5
    """
    try:
        import pandas as pd
        import numpy as np
    except ImportError as e:
        raise ImportError(
            "pandas and numpy are required for describe_data. "
            "Install with: pip install pandas numpy"
        ) from e

    if not isinstance(data, pd.DataFrame):
        raise TypeError(f"Expected pandas DataFrame, got {type(data).__name__}")

    result: Dict[str, Any] = {
        "row_count": len(data),
        "column_count": len(data.columns),
        "numeric_columns": [],
        "categorical_columns": [],
        "missing_values": {},
        "statistics": {},
    }

    # Identify column types
    numeric_cols = data.select_dtypes(include=[np.number]).columns.tolist()
    categorical_cols = data.select_dtypes(include=["object", "category"]).columns.tolist()

    result["numeric_columns"] = numeric_cols
    result["categorical_columns"] = categorical_cols

    # Missing values
    missing = data.isnull().sum()
    result["missing_values"] = {col: int(count) for col, count in missing.items() if count > 0}

    # Statistics for selected columns
    cols_to_analyze = columns if columns is not None else numeric_cols

    for col in cols_to_analyze:
        if col not in data.columns:
            continue

        if col in numeric_cols:
            series = data[col].dropna()
            stats = {
                "count": int(len(series)),
                "mean": float(series.mean()) if len(series) > 0 else None,
                "std": float(series.std()) if len(series) > 1 else None,
                "min": float(series.min()) if len(series) > 0 else None,
                "max": float(series.max()) if len(series) > 0 else None,
            }
            if include_percentiles and len(series) > 0:
                stats["25%"] = float(series.quantile(0.25))
                stats["50%"] = float(series.quantile(0.50))
                stats["75%"] = float(series.quantile(0.75))

            result["statistics"][col] = stats

        elif col in categorical_cols:
            value_counts = data[col].value_counts()
            result["statistics"][col] = {
                "count": int(len(data[col].dropna())),
                "unique": int(data[col].nunique()),
                "top": str(value_counts.index[0]) if len(value_counts) > 0 else None,
                "freq": int(value_counts.iloc[0]) if len(value_counts) > 0 else None,
            }

    return result
