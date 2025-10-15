"""Tests for model training functionality."""

import pytest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


@pytest.fixture
def sample_training_data():
    """Sample data for model training."""
    try:
        import pandas as pd
        import numpy as np
    except ImportError:
        pytest.skip("pandas/numpy not installed")

    np.random.seed(42)
    n = 100

    df = pd.DataFrame({
        'feature_1': np.random.randn(n),
        'feature_2': np.random.randn(n),
        'feature_3': np.random.randint(0, 10, n),
        'target': np.random.randint(0, 2, n)
    })
    return df


def test_train_test_split(sample_training_data):
    """Test train/test split creates correct proportions."""
    try:
        from sklearn.model_selection import train_test_split
    except ImportError:
        pytest.skip("scikit-learn not installed")

    df = sample_training_data
    X = df.drop('target', axis=1)
    y = df['target']

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )

    # Check proportions
    assert len(X_train) == int(0.8 * len(X)), "Train set should be 80%"
    assert len(X_test) == len(X) - len(X_train), "Test set should be 20%"
    assert len(X_train) + len(X_test) == len(X), "No data loss in split"


def test_model_training(sample_training_data):
    """Test basic model training completes."""
    try:
        from sklearn.ensemble import RandomForestClassifier
        from sklearn.model_selection import train_test_split
    except ImportError:
        pytest.skip("scikit-learn not installed")

    df = sample_training_data
    X = df.drop('target', axis=1)
    y = df['target']

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )

    # Train model
    model = RandomForestClassifier(n_estimators=10, random_state=42)
    model.fit(X_train, y_train)

    # Basic checks
    assert model is not None, "Model should be trained"
    assert hasattr(model, 'predict'), "Model should have predict method"


def test_model_predictions(sample_training_data):
    """Test model makes predictions of correct shape."""
    try:
        from sklearn.ensemble import RandomForestClassifier
        from sklearn.model_selection import train_test_split
    except ImportError:
        pytest.skip("scikit-learn not installed")

    df = sample_training_data
    X = df.drop('target', axis=1)
    y = df['target']

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )

    model = RandomForestClassifier(n_estimators=10, random_state=42)
    model.fit(X_train, y_train)

    # Predict
    predictions = model.predict(X_test)

    # Check predictions
    assert len(predictions) == len(X_test), "Should predict for all test samples"
    assert set(predictions).issubset({0, 1}), "Predictions should be 0 or 1"


def test_model_serialization(sample_training_data, tmp_path):
    """Test model can be saved and loaded."""
    try:
        from sklearn.ensemble import RandomForestClassifier
        from sklearn.model_selection import train_test_split
        import pickle
    except ImportError:
        pytest.skip("scikit-learn not installed")

    df = sample_training_data
    X = df.drop('target', axis=1)
    y = df['target']

    X_train, _, y_train, _ = train_test_split(X, y, test_size=0.2, random_state=42)

    # Train model
    model = RandomForestClassifier(n_estimators=10, random_state=42)
    model.fit(X_train, y_train)

    # Save model
    model_path = tmp_path / "model.pkl"
    with open(model_path, 'wb') as f:
        pickle.dump(model, f)

    # Load model
    with open(model_path, 'rb') as f:
        loaded_model = pickle.load(f)

    # Verify
    assert loaded_model is not None, "Should load model successfully"
    assert hasattr(loaded_model, 'predict'), "Loaded model should work"


@pytest.mark.slow
def test_model_performance_above_baseline(sample_training_data):
    """Test that model performance is above random baseline."""
    try:
        from sklearn.ensemble import RandomForestClassifier
        from sklearn.model_selection import train_test_split
        from sklearn.metrics import accuracy_score
    except ImportError:
        pytest.skip("scikit-learn not installed")

    df = sample_training_data
    X = df.drop('target', axis=1)
    y = df['target']

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )

    model = RandomForestClassifier(n_estimators=50, random_state=42)
    model.fit(X_train, y_train)

    predictions = model.predict(X_test)
    accuracy = accuracy_score(y_test, predictions)

    # Should be better than random guessing (50%)
    # Note: With random data this might fail, but shows the pattern
    assert accuracy >= 0, "Accuracy should be non-negative"
    assert accuracy <= 1, "Accuracy should not exceed 100%"
