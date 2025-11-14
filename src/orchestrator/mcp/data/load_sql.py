"""Load data from SQL databases."""

import os
from typing import Any, Optional


def load_sql(
    query: str,
    connection_string: Optional[str] = None,
    *,
    env_var: str = "DATABASE_URL",
) -> Any:
    """Load data from SQL database using SQLAlchemy.

    Args:
        query: SQL query to execute
        connection_string: Database connection string (e.g., "postgresql://user:pass@host/db")
                          If None, will read from environment variable
        env_var: Environment variable name for connection string (default: DATABASE_URL)

    Returns:
        pandas.DataFrame with query results

    Raises:
        ImportError: If pandas or sqlalchemy is not installed
        ValueError: If connection string not provided and not found in environment
        Exception: If query execution fails

    Example:
        >>> # Using environment variable DATABASE_URL
        >>> df = load_sql("SELECT * FROM customers LIMIT 100")
        >>>
        >>> # Using explicit connection string
        >>> df = load_sql(
        ...     "SELECT * FROM orders WHERE date > '2024-01-01'",
        ...     connection_string="postgresql://localhost/mydb"
        ... )
    """
    try:
        import pandas as pd
    except ImportError as e:
        raise ImportError(
            "pandas is required for load_sql. Install with: pip install pandas"
        ) from e

    try:
        from sqlalchemy import create_engine
    except ImportError as e:
        raise ImportError(
            "sqlalchemy is required for load_sql. Install with: pip install sqlalchemy"
        ) from e

    # Get connection string
    conn_str = connection_string or os.getenv(env_var)
    if not conn_str:
        raise ValueError(
            f"Database connection string not provided.\n"
            f"Either pass connection_string argument or set {env_var} environment variable.\n"
            f"Example: export {env_var}='postgresql://user:password@localhost/database'"
        )

    try:
        engine = create_engine(conn_str)
        df = pd.read_sql(query, engine)
        return df
    except Exception as e:
        raise Exception(f"Failed to execute SQL query: {e}") from e
