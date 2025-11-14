"""Train Prophet time-series forecasting model."""

from pathlib import Path
from typing import Any, Dict, Optional


def train_prophet(
    data: Any,
    *,
    date_column: str = "ds",
    value_column: str = "y",
    periods: int = 30,
    output_path: Optional[str] = None,
) -> Dict[str, Any]:
    """Train a Prophet time-series forecasting model.

    Args:
        data: pandas DataFrame with time series data
        date_column: Name of date/datetime column (default: "ds")
        value_column: Name of value column to forecast (default: "y")
        periods: Number of periods to forecast (default: 30)
        output_path: Optional path to save model pickle (default: models/prophet_model.pkl)

    Returns:
        Dict with training results:
            - model_path: str (path to saved model)
            - forecast_path: str (path to forecast CSV)
            - metrics: dict with MAE, RMSE if test data available
            - periods_forecasted: int

    Raises:
        ImportError: If prophet is not installed
        ValueError: If required columns are missing or data is invalid

    Example:
        >>> import pandas as pd
        >>> df = pd.DataFrame({
        ...     "ds": pd.date_range("2024-01-01", periods=100),
        ...     "y": range(100)
        ... })
        >>> result = train_prophet(df, periods=10)
        >>> print(result["model_path"])
        models/prophet_model.pkl

    Note:
        Prophet must be installed separately: pip install prophet
        If not installed, this function will raise ImportError with installation instructions.
    """
    try:
        from prophet import Prophet
    except ImportError as e:
        raise ImportError(
            "Prophet is required for train_prophet.\n"
            "Install with: pip install prophet\n"
            "Note: Prophet requires additional system dependencies.\n"
            "See: https://facebook.github.io/prophet/docs/installation.html"
        ) from e

    try:
        import pandas as pd
        import pickle
    except ImportError as e:
        raise ImportError("pandas is required for train_prophet. Install with: pip install pandas") from e

    if not isinstance(data, pd.DataFrame):
        raise ValueError(f"data must be a pandas DataFrame, got {type(data).__name__}")

    if date_column not in data.columns or value_column not in data.columns:
        raise ValueError(
            f"Required columns missing. Expected '{date_column}' and '{value_column}', "
            f"but DataFrame has: {list(data.columns)}"
        )

    # Prepare data (Prophet expects 'ds' and 'y' columns)
    df = data[[date_column, value_column]].copy()
    df.columns = ["ds", "y"]

    # Train model
    model = Prophet()
    model.fit(df)

    # Make forecast
    future = model.make_future_dataframe(periods=periods)
    forecast = model.predict(future)

    # Save model
    models_dir = Path("models")
    models_dir.mkdir(exist_ok=True)

    model_path = output_path or "models/prophet_model.pkl"
    with open(model_path, "wb") as f:
        pickle.dump(model, f)

    # Save forecast
    forecast_path = "data/processed/prophet_forecast.csv"
    Path(forecast_path).parent.mkdir(parents=True, exist_ok=True)
    forecast.to_csv(forecast_path, index=False)

    result = {
        "model_path": model_path,
        "forecast_path": forecast_path,
        "periods_forecasted": periods,
        "metrics": {},  # Would calculate if we had test data
    }

    return result
