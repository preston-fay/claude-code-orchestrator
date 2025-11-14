"""Detect data drift between reference and current datasets."""

from typing import Any, Dict, List, Optional


def detect_drift(
    reference_data: Any,
    current_data: Any,
    *,
    columns: Optional[List[str]] = None,
    threshold: float = 0.1,
) -> Dict[str, Any]:
    """Detect statistical drift between reference and current datasets.

    Uses Population Stability Index (PSI) for numeric columns and
    Kolmogorov-Smirnov test for distribution comparison.

    Args:
        reference_data: pandas DataFrame with reference/baseline data
        current_data: pandas DataFrame with current data to compare
        columns: Optional list of columns to check (default: all numeric columns)
        threshold: PSI threshold for flagging drift (default: 0.1)
                  < 0.1: no significant drift
                  0.1-0.25: moderate drift
                  > 0.25: significant drift

    Returns:
        Dict with drift detection results:
            - overall_drift: bool (True if any column exceeds threshold)
            - column_drift: dict of {column: {"psi": float, "drifted": bool, "ks_statistic": float}}
            - columns_checked: list of column names
            - threshold_used: float

    Raises:
        ImportError: If pandas or numpy is not installed
        TypeError: If inputs are not pandas DataFrames
        ValueError: If columns don't match between datasets

    Example:
        >>> import pandas as pd
        >>> ref = pd.DataFrame({"x": [1, 2, 3, 4, 5]})
        >>> cur = pd.DataFrame({"x": [10, 20, 30, 40, 50]})
        >>> drift = detect_drift(ref, cur)
        >>> print(drift["overall_drift"])
        True
    """
    try:
        import pandas as pd
        import numpy as np
    except ImportError as e:
        raise ImportError(
            "pandas and numpy are required for detect_drift. "
            "Install with: pip install pandas numpy"
        ) from e

    if not isinstance(reference_data, pd.DataFrame) or not isinstance(current_data, pd.DataFrame):
        raise TypeError("Both reference_data and current_data must be pandas DataFrames")

    # Determine columns to check
    if columns is None:
        numeric_cols = reference_data.select_dtypes(include=[np.number]).columns.tolist()
        columns = [col for col in numeric_cols if col in current_data.columns]
    else:
        # Validate columns exist in both datasets
        missing_in_ref = set(columns) - set(reference_data.columns)
        missing_in_cur = set(columns) - set(current_data.columns)
        if missing_in_ref or missing_in_cur:
            raise ValueError(
                f"Columns mismatch. Missing in reference: {missing_in_ref}, "
                f"missing in current: {missing_in_cur}"
            )

    result: Dict[str, Any] = {
        "overall_drift": False,
        "column_drift": {},
        "columns_checked": columns,
        "threshold_used": threshold,
    }

    for col in columns:
        ref_series = reference_data[col].dropna()
        cur_series = current_data[col].dropna()

        if len(ref_series) == 0 or len(cur_series) == 0:
            result["column_drift"][col] = {
                "psi": None,
                "drifted": False,
                "ks_statistic": None,
                "error": "Insufficient data",
            }
            continue

        # Calculate PSI (Population Stability Index)
        psi = _calculate_psi(ref_series.values, cur_series.values)

        # Calculate KS statistic (simple implementation)
        ks_stat = _calculate_ks_statistic(ref_series.values, cur_series.values)

        drifted = psi > threshold if psi is not None else False

        result["column_drift"][col] = {
            "psi": float(psi) if psi is not None else None,
            "drifted": drifted,
            "ks_statistic": float(ks_stat) if ks_stat is not None else None,
        }

        if drifted:
            result["overall_drift"] = True

    return result


def _calculate_psi(reference: Any, current: Any, bins: int = 10) -> Optional[float]:
    """Calculate Population Stability Index.

    PSI measures the shift in distribution between two datasets.
    """
    try:
        import numpy as np
    except ImportError:
        return None

    try:
        # Create bins based on reference distribution
        min_val = min(reference.min(), current.min())
        max_val = max(reference.max(), current.max())
        bin_edges = np.linspace(min_val, max_val, bins + 1)

        # Calculate histograms
        ref_hist, _ = np.histogram(reference, bins=bin_edges)
        cur_hist, _ = np.histogram(current, bins=bin_edges)

        # Normalize to get proportions
        ref_prop = ref_hist / len(reference)
        cur_prop = cur_hist / len(current)

        # Avoid division by zero
        ref_prop = np.where(ref_prop == 0, 0.0001, ref_prop)
        cur_prop = np.where(cur_prop == 0, 0.0001, cur_prop)

        # Calculate PSI
        psi = np.sum((cur_prop - ref_prop) * np.log(cur_prop / ref_prop))

        return psi
    except Exception:
        return None


def _calculate_ks_statistic(reference: Any, current: Any) -> Optional[float]:
    """Calculate Kolmogorov-Smirnov statistic (simple implementation)."""
    try:
        import numpy as np
    except ImportError:
        return None

    try:
        # Sort both arrays
        ref_sorted = np.sort(reference)
        cur_sorted = np.sort(current)

        # Create ECDFs
        n_ref = len(ref_sorted)
        n_cur = len(cur_sorted)

        # Combine and sort all values
        all_values = np.concatenate([ref_sorted, cur_sorted])
        all_values = np.sort(np.unique(all_values))

        # Calculate ECDFs at each unique value
        ref_ecdf = np.searchsorted(ref_sorted, all_values, side="right") / n_ref
        cur_ecdf = np.searchsorted(cur_sorted, all_values, side="right") / n_cur

        # KS statistic is the maximum difference
        ks_stat = np.max(np.abs(ref_ecdf - cur_ecdf))

        return ks_stat
    except Exception:
        return None
