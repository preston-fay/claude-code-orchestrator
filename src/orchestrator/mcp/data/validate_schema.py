"""Validate data schema and quality."""

from typing import Any, Dict, List, Optional


def validate_schema(
    data: Any,
    expected_columns: List[str],
    *,
    required_types: Optional[Dict[str, str]] = None,
    allow_extra_columns: bool = True,
) -> Dict[str, Any]:
    """Validate that a DataFrame matches expected schema.

    Args:
        data: pandas DataFrame to validate
        expected_columns: List of column names that must be present
        required_types: Optional dict mapping column names to expected pandas dtype strings
        allow_extra_columns: If False, raise error if DataFrame has columns not in expected_columns

    Returns:
        Dict with validation results:
            - valid: bool
            - missing_columns: list of missing column names
            - extra_columns: list of unexpected column names
            - type_mismatches: dict of {column: {expected: str, actual: str}}
            - row_count: int

    Raises:
        ImportError: If pandas is not installed
        TypeError: If data is not a pandas DataFrame

    Example:
        >>> import pandas as pd
        >>> df = pd.DataFrame({"id": [1, 2], "name": ["A", "B"]})
        >>> result = validate_schema(df, ["id", "name"], required_types={"id": "int64"})
        >>> assert result["valid"] is True
    """
    try:
        import pandas as pd
    except ImportError as e:
        raise ImportError(
            "pandas is required for validate_schema. Install with: pip install pandas"
        ) from e

    if not isinstance(data, pd.DataFrame):
        raise TypeError(f"Expected pandas DataFrame, got {type(data).__name__}")

    result: Dict[str, Any] = {
        "valid": True,
        "missing_columns": [],
        "extra_columns": [],
        "type_mismatches": {},
        "row_count": len(data),
    }

    # Check for missing columns
    actual_columns = set(data.columns)
    expected_set = set(expected_columns)
    missing = expected_set - actual_columns
    if missing:
        result["missing_columns"] = sorted(missing)
        result["valid"] = False

    # Check for extra columns
    if not allow_extra_columns:
        extra = actual_columns - expected_set
        if extra:
            result["extra_columns"] = sorted(extra)
            result["valid"] = False

    # Check types
    if required_types:
        for col, expected_type in required_types.items():
            if col in data.columns:
                actual_type = str(data[col].dtype)
                if actual_type != expected_type:
                    result["type_mismatches"][col] = {
                        "expected": expected_type,
                        "actual": actual_type,
                    }
                    result["valid"] = False

    return result
