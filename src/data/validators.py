"""Data validation utilities using Pydantic."""

from typing import List, Optional, Any
from pathlib import Path

try:
    from pydantic import BaseModel, Field, field_validator
    import pandas as pd
except ImportError:
    # Graceful degradation
    BaseModel = object
    Field = lambda *args, **kwargs: None


class DataFrameSchema(BaseModel):
    """Schema validation for pandas DataFrames."""

    required_columns: List[str] = Field(..., description="Required column names")
    min_rows: int = Field(1, description="Minimum number of rows")
    max_rows: Optional[int] = Field(None, description="Maximum number of rows")
    allow_nulls: bool = Field(False, description="Whether nulls are allowed")

    @field_validator('required_columns')
    @classmethod
    def validate_columns_not_empty(cls, v):
        """Ensure required_columns is not empty."""
        if not v:
            raise ValueError("required_columns cannot be empty")
        return v


class ValidationResult(BaseModel):
    """Result of data validation."""

    valid: bool = Field(..., description="Whether validation passed")
    errors: List[str] = Field(default_factory=list, description="List of validation errors")
    warnings: List[str] = Field(default_factory=list, description="List of validation warnings")
    row_count: Optional[int] = None
    column_count: Optional[int] = None


def validate_dataframe(df: "pd.DataFrame", schema: DataFrameSchema) -> ValidationResult:
    """
    Validate a DataFrame against a schema.

    Args:
        df: DataFrame to validate
        schema: Schema definition

    Returns:
        ValidationResult with validation outcome
    """
    errors = []
    warnings = []

    # Check required columns
    missing_cols = set(schema.required_columns) - set(df.columns)
    if missing_cols:
        errors.append(f"Missing required columns: {sorted(missing_cols)}")

    # Check row count
    if len(df) < schema.min_rows:
        errors.append(f"Row count {len(df)} is less than minimum {schema.min_rows}")

    if schema.max_rows and len(df) > schema.max_rows:
        errors.append(f"Row count {len(df)} exceeds maximum {schema.max_rows}")

    # Check for nulls if not allowed
    if not schema.allow_nulls:
        null_cols = df.columns[df.isnull().any()].tolist()
        if null_cols:
            errors.append(f"Null values found in columns: {null_cols}")

    # Warnings for potential issues
    if df.duplicated().any():
        dup_count = df.duplicated().sum()
        warnings.append(f"Found {dup_count} duplicate rows")

    return ValidationResult(
        valid=len(errors) == 0,
        errors=errors,
        warnings=warnings,
        row_count=len(df),
        column_count=len(df.columns)
    )


def validate_csv_file(
    file_path: Path,
    schema: DataFrameSchema,
    sample_rows: Optional[int] = None
) -> ValidationResult:
    """
    Validate a CSV file against a schema.

    Args:
        file_path: Path to CSV file
        schema: Schema definition
        sample_rows: If provided, only validate first N rows

    Returns:
        ValidationResult with validation outcome
    """
    try:
        import pandas as pd

        if not file_path.exists():
            return ValidationResult(
                valid=False,
                errors=[f"File not found: {file_path}"]
            )

        # Read file (sample if requested)
        if sample_rows:
            df = pd.read_csv(file_path, nrows=sample_rows)
        else:
            df = pd.read_csv(file_path)

        return validate_dataframe(df, schema)

    except Exception as e:
        return ValidationResult(
            valid=False,
            errors=[f"Failed to read file: {str(e)}"]
        )


def check_data_quality(df: "pd.DataFrame") -> dict:
    """
    Compute data quality metrics for a DataFrame.

    Args:
        df: DataFrame to analyze

    Returns:
        Dictionary of quality metrics
    """
    metrics = {
        "row_count": len(df),
        "column_count": len(df.columns),
        "duplicate_rows": int(df.duplicated().sum()),
        "duplicate_pct": float(df.duplicated().mean()),
        "columns": {}
    }

    for col in df.columns:
        col_metrics = {
            "dtype": str(df[col].dtype),
            "null_count": int(df[col].isnull().sum()),
            "null_pct": float(df[col].isnull().mean()),
            "unique_count": int(df[col].nunique()),
        }

        # Numeric column stats
        if pd.api.types.is_numeric_dtype(df[col]):
            col_metrics.update({
                "mean": float(df[col].mean()) if not df[col].isnull().all() else None,
                "std": float(df[col].std()) if not df[col].isnull().all() else None,
                "min": float(df[col].min()) if not df[col].isnull().all() else None,
                "max": float(df[col].max()) if not df[col].isnull().all() else None,
            })

        metrics["columns"][col] = col_metrics

    return metrics
