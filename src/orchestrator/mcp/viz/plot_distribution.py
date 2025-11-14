"""Create distribution plots for data visualization."""

from pathlib import Path
from typing import Any, Optional


def plot_distribution(
    data: Any,
    column: str,
    *,
    output_path: Optional[str] = None,
    bins: int = 30,
    title: Optional[str] = None,
) -> str:
    """Create a histogram/distribution plot for a column.

    Args:
        data: pandas DataFrame containing the data
        column: Name of column to plot
        output_path: Path to save PNG file (default: reports/distribution_{column}.png)
        bins: Number of bins for histogram (default: 30)
        title: Plot title (default: "Distribution of {column}")

    Returns:
        str: Path to saved PNG file

    Raises:
        ImportError: If matplotlib is not installed
        ValueError: If column does not exist or is not numeric

    Example:
        >>> import pandas as pd
        >>> df = pd.DataFrame({"values": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]})
        >>> path = plot_distribution(df, "values")
        >>> print(path)
        reports/distribution_values.png
    """
    try:
        import matplotlib
        matplotlib.use("Agg")  # Non-interactive backend
        import matplotlib.pyplot as plt
    except ImportError as e:
        raise ImportError(
            "matplotlib is required for plot_distribution. "
            "Install with: pip install matplotlib"
        ) from e

    try:
        import pandas as pd
        import numpy as np
    except ImportError as e:
        raise ImportError(
            "pandas and numpy are required for plot_distribution. "
            "Install with: pip install pandas numpy"
        ) from e

    if not isinstance(data, pd.DataFrame):
        raise ValueError(f"data must be a pandas DataFrame, got {type(data).__name__}")

    if column not in data.columns:
        raise ValueError(
            f"Column '{column}' not found in DataFrame. Available columns: {list(data.columns)}"
        )

    # Check if column is numeric
    if not pd.api.types.is_numeric_dtype(data[column]):
        raise ValueError(
            f"Column '{column}' is not numeric (dtype: {data[column].dtype}). "
            f"Distribution plots require numeric data."
        )

    # Prepare output path
    if output_path is None:
        reports_dir = Path("reports")
        reports_dir.mkdir(exist_ok=True)
        output_path = f"reports/distribution_{column}.png"

    # Ensure output directory exists
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)

    # Create plot
    fig, ax = plt.subplots(figsize=(10, 6))

    series = data[column].dropna()
    ax.hist(series, bins=bins, edgecolor="black", alpha=0.7)

    ax.set_xlabel(column)
    ax.set_ylabel("Frequency")
    ax.set_title(title or f"Distribution of {column}")
    ax.grid(True, alpha=0.3)

    # Add summary statistics as text
    stats_text = (
        f"n = {len(series)}\n"
        f"mean = {series.mean():.2f}\n"
        f"std = {series.std():.2f}\n"
        f"min = {series.min():.2f}\n"
        f"max = {series.max():.2f}"
    )
    ax.text(
        0.95,
        0.95,
        stats_text,
        transform=ax.transAxes,
        verticalalignment="top",
        horizontalalignment="right",
        bbox=dict(boxstyle="round", facecolor="wheat", alpha=0.5),
        fontsize=9,
    )

    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close(fig)

    return output_path
