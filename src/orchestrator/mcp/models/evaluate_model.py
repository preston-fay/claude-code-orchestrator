"""Evaluate model performance with common metrics."""

from typing import Any, Dict, List, Optional


def evaluate_model(
    y_true: Any,
    y_pred: Any,
    *,
    task_type: str = "regression",
    labels: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """Evaluate model predictions with standard metrics.

    Args:
        y_true: True values (array-like or pandas Series)
        y_pred: Predicted values (array-like or pandas Series)
        task_type: Type of task - "regression" or "classification" (default: "regression")
        labels: Class labels for classification tasks (optional)

    Returns:
        Dict with evaluation metrics:
            For regression:
                - mae: Mean Absolute Error
                - rmse: Root Mean Squared Error
                - r2: R-squared score
                - mape: Mean Absolute Percentage Error
            For classification:
                - accuracy: Accuracy score
                - precision: Precision score
                - recall: Recall score
                - f1: F1 score

    Raises:
        ImportError: If numpy or sklearn is not installed
        ValueError: If task_type is invalid or inputs have mismatched lengths

    Example:
        >>> import numpy as np
        >>> y_true = np.array([1, 2, 3, 4, 5])
        >>> y_pred = np.array([1.1, 2.1, 2.9, 4.2, 4.8])
        >>> metrics = evaluate_model(y_true, y_pred, task_type="regression")
        >>> print(f"RMSE: {metrics['rmse']:.2f}")
        RMSE: 0.18
    """
    try:
        import numpy as np
    except ImportError as e:
        raise ImportError(
            "numpy is required for evaluate_model. Install with: pip install numpy"
        ) from e

    # Convert to numpy arrays
    y_true_arr = np.asarray(y_true)
    y_pred_arr = np.asarray(y_pred)

    if len(y_true_arr) != len(y_pred_arr):
        raise ValueError(
            f"Length mismatch: y_true has {len(y_true_arr)} samples, "
            f"y_pred has {len(y_pred_arr)} samples"
        )

    if task_type == "regression":
        return _evaluate_regression(y_true_arr, y_pred_arr)
    elif task_type == "classification":
        return _evaluate_classification(y_true_arr, y_pred_arr, labels)
    else:
        raise ValueError(f"Invalid task_type: {task_type}. Must be 'regression' or 'classification'")


def _evaluate_regression(y_true: Any, y_pred: Any) -> Dict[str, float]:
    """Calculate regression metrics."""
    try:
        import numpy as np
    except ImportError:
        return {}

    # Mean Absolute Error
    mae = float(np.mean(np.abs(y_true - y_pred)))

    # Root Mean Squared Error
    rmse = float(np.sqrt(np.mean((y_true - y_pred) ** 2)))

    # R-squared
    ss_res = np.sum((y_true - y_pred) ** 2)
    ss_tot = np.sum((y_true - np.mean(y_true)) ** 2)
    r2 = float(1 - (ss_res / ss_tot)) if ss_tot != 0 else 0.0

    # Mean Absolute Percentage Error (avoid division by zero)
    mask = y_true != 0
    mape = float(np.mean(np.abs((y_true[mask] - y_pred[mask]) / y_true[mask])) * 100) if mask.any() else 0.0

    return {
        "mae": mae,
        "rmse": rmse,
        "r2": r2,
        "mape": mape,
    }


def _evaluate_classification(
    y_true: Any, y_pred: Any, labels: Optional[List[str]] = None
) -> Dict[str, Any]:
    """Calculate classification metrics."""
    try:
        import numpy as np
    except ImportError:
        return {}

    # Accuracy
    accuracy = float(np.mean(y_true == y_pred))

    # For binary/multiclass, calculate precision, recall, F1
    # Simple implementation without sklearn
    unique_classes = np.unique(np.concatenate([y_true, y_pred]))

    if len(unique_classes) == 2:
        # Binary classification
        tp = np.sum((y_true == unique_classes[1]) & (y_pred == unique_classes[1]))
        fp = np.sum((y_true == unique_classes[0]) & (y_pred == unique_classes[1]))
        fn = np.sum((y_true == unique_classes[1]) & (y_pred == unique_classes[0]))

        precision = float(tp / (tp + fp)) if (tp + fp) > 0 else 0.0
        recall = float(tp / (tp + fn)) if (tp + fn) > 0 else 0.0
        f1 = float(2 * precision * recall / (precision + recall)) if (precision + recall) > 0 else 0.0

        return {
            "accuracy": accuracy,
            "precision": precision,
            "recall": recall,
            "f1": f1,
        }
    else:
        # Multiclass - macro averaged metrics
        precisions = []
        recalls = []

        for cls in unique_classes:
            tp = np.sum((y_true == cls) & (y_pred == cls))
            fp = np.sum((y_true != cls) & (y_pred == cls))
            fn = np.sum((y_true == cls) & (y_pred != cls))

            prec = tp / (tp + fp) if (tp + fp) > 0 else 0.0
            rec = tp / (tp + fn) if (tp + fn) > 0 else 0.0

            precisions.append(prec)
            recalls.append(rec)

        precision = float(np.mean(precisions))
        recall = float(np.mean(recalls))
        f1 = float(2 * precision * recall / (precision + recall)) if (precision + recall) > 0 else 0.0

        return {
            "accuracy": accuracy,
            "precision": precision,
            "recall": recall,
            "f1": f1,
        }
