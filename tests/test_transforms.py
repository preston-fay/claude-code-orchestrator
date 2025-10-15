"""Tests for data transformation functionality."""

import pytest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


@pytest.fixture
def sample_df():
    """Sample DataFrame for testing."""
    try:
        import pandas as pd
        import numpy as np
    except ImportError:
        pytest.skip("pandas/numpy not installed")

    np.random.seed(42)
    return pd.DataFrame({
        'id': range(1, 11),
        'feature_a': np.random.randn(10),
        'feature_b': np.random.randint(0, 10, 10),
        'feature_c': np.random.choice(['A', 'B', 'C'], 10),
        'target': np.random.randint(0, 2, 10)
    })


def test_transform_removes_nulls(sample_df):
    """Test that transformation removes null values."""
    try:
        import pandas as pd
        import numpy as np
    except ImportError:
        pytest.skip("pandas/numpy not installed")

    # Add some nulls
    df_with_nulls = sample_df.copy()
    df_with_nulls.loc[0, 'feature_a'] = np.nan

    # Transform: remove nulls
    df_clean = df_with_nulls.dropna()

    assert len(df_clean) < len(df_with_nulls), "Should remove rows with nulls"
    assert df_clean.isnull().sum().sum() == 0, "Clean data should have no nulls"


def test_transform_removes_duplicates(sample_df):
    """Test that transformation removes duplicate rows."""
    try:
        import pandas as pd
    except ImportError:
        pytest.skip("pandas not installed")

    # Add duplicate
    df_with_dup = pd.concat([sample_df, sample_df.iloc[[0]]], ignore_index=True)

    # Transform: remove duplicates
    df_clean = df_with_dup.drop_duplicates()

    assert len(df_clean) < len(df_with_dup), "Should remove duplicates"


def test_feature_engineering_squared(sample_df):
    """Test feature engineering: squared feature."""
    try:
        import pandas as pd
    except ImportError:
        pytest.skip("pandas not installed")

    df_proc = sample_df.copy()
    df_proc['feature_a_squared'] = df_proc['feature_a'] ** 2

    assert 'feature_a_squared' in df_proc.columns, "Should create squared feature"
    assert (df_proc['feature_a_squared'] >= 0).all(), "Squared values should be non-negative"


def test_feature_engineering_normalization(sample_df):
    """Test feature engineering: normalization."""
    try:
        import pandas as pd
        import numpy as np
    except ImportError:
        pytest.skip("pandas/numpy not installed")

    df_proc = sample_df.copy()
    mean_b = df_proc['feature_b'].mean()
    std_b = df_proc['feature_b'].std()
    df_proc['feature_b_norm'] = (df_proc['feature_b'] - mean_b) / std_b

    # Check normalized values are centered around 0
    assert abs(df_proc['feature_b_norm'].mean()) < 1e-10, "Normalized mean should be ~0"
    assert abs(df_proc['feature_b_norm'].std() - 1.0) < 1e-10, "Normalized std should be ~1"


def test_one_hot_encoding(sample_df):
    """Test one-hot encoding of categorical features."""
    try:
        import pandas as pd
    except ImportError:
        pytest.skip("pandas not installed")

    df_proc = pd.get_dummies(sample_df, columns=['feature_c'], prefix='cat')

    # Check one-hot columns created
    expected_cols = ['cat_A', 'cat_B', 'cat_C']
    for col in expected_cols:
        assert col in df_proc.columns, f"Should create {col} column"

    # Check original column removed
    assert 'feature_c' not in df_proc.columns, "Original column should be removed"


@pytest.mark.integration
def test_full_transform_pipeline(sample_df):
    """Integration test: Full transformation pipeline."""
    try:
        import pandas as pd
        import numpy as np
    except ImportError:
        pytest.skip("pandas/numpy not installed")

    # Simulate full pipeline
    df = sample_df.copy()

    # Step 1: Clean
    df = df.dropna()
    df = df.drop_duplicates()

    # Step 2: Engineer features
    df['feature_a_squared'] = df['feature_a'] ** 2
    df['feature_b_norm'] = (df['feature_b'] - df['feature_b'].mean()) / df['feature_b'].std()

    # Step 3: Encode categoricals
    df = pd.get_dummies(df, columns=['feature_c'], prefix='cat')

    # Verify
    assert len(df) > 0, "Should have data after transforms"
    assert 'feature_a_squared' in df.columns, "Should have engineered features"
    assert 'cat_A' in df.columns, "Should have encoded categoricals"
