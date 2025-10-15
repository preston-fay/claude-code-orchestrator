"""DuckDB warehouse helpers with safety features."""

import duckdb
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
import time
from contextlib import contextmanager


class WarehouseError(Exception):
    """Warehouse operation error."""

    pass


class QueryTimeout(WarehouseError):
    """Query exceeded timeout."""

    pass


class QueryNotAllowed(WarehouseError):
    """Query not in allowlist."""

    pass


# SQL allowlist patterns - only these operations permitted
ALLOWED_PATTERNS = [
    r"^SELECT\s",
    r"^WITH\s",
    r"^DESCRIBE\s",
    r"^SHOW\s",
    r"^EXPLAIN\s",
]

# Dangerous patterns - block immediately
BLOCKED_PATTERNS = [
    r"DROP\s",
    r"DELETE\s",
    r"TRUNCATE\s",
    r"ALTER\s",
    r"CREATE\s+USER",
    r"GRANT\s",
    r"REVOKE\s",
]


class DuckDBWarehouse:
    """
    DuckDB warehouse with safety features.

    Features:
    - SQL allowlist (SELECT, WITH, DESCRIBE only)
    - Query timeout protection
    - Parameterized queries
    - Arrow/Parquet registration
    - Materialization helpers
    """

    def __init__(
        self,
        db_path: Union[str, Path] = ":memory:",
        read_only: bool = False,
        timeout_seconds: int = 30,
    ):
        """
        Initialize warehouse.

        Args:
            db_path: Path to DuckDB file (":memory:" for in-memory)
            read_only: Open in read-only mode
            timeout_seconds: Default query timeout
        """
        self.db_path = str(db_path) if db_path != ":memory:" else ":memory:"
        self.read_only = read_only
        self.timeout_seconds = timeout_seconds
        self.conn: Optional[duckdb.DuckDBPyConnection] = None

    def connect(self) -> duckdb.DuckDBPyConnection:
        """Get or create connection."""
        if self.conn is None:
            self.conn = duckdb.connect(self.db_path, read_only=self.read_only)
            # Set timeout
            self.conn.execute(f"SET statement_timeout = '{self.timeout_seconds}s'")
        return self.conn

    def close(self) -> None:
        """Close connection."""
        if self.conn:
            self.conn.close()
            self.conn = None

    @contextmanager
    def transaction(self):
        """Context manager for transactions."""
        conn = self.connect()
        try:
            conn.begin()
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise

    def _check_sql_allowed(self, sql: str) -> None:
        """
        Check if SQL is allowed.

        Args:
            sql: SQL query

        Raises:
            QueryNotAllowed: If query not permitted
        """
        import re

        sql_upper = sql.upper().strip()

        # Check blocked patterns first
        for pattern in BLOCKED_PATTERNS:
            if re.search(pattern, sql_upper, re.IGNORECASE):
                raise QueryNotAllowed(f"Query contains blocked pattern: {pattern}")

        # Check allowed patterns
        allowed = any(re.match(pattern, sql_upper, re.IGNORECASE) for pattern in ALLOWED_PATTERNS)

        if not allowed:
            raise QueryNotAllowed(
                f"Query not in allowlist. Allowed: SELECT, WITH, DESCRIBE, SHOW, EXPLAIN"
            )

    def query(
        self,
        sql: str,
        params: Optional[Dict[str, Any]] = None,
        timeout: Optional[int] = None,
        check_allowlist: bool = True,
    ) -> duckdb.DuckDBPyRelation:
        """
        Execute safe query.

        Args:
            sql: SQL query
            params: Query parameters (dict for named params)
            timeout: Query timeout override
            check_allowlist: Check SQL against allowlist

        Returns:
            DuckDB relation object

        Raises:
            QueryNotAllowed: If query not permitted
            QueryTimeout: If query exceeds timeout
        """
        if check_allowlist:
            self._check_sql_allowed(sql)

        conn = self.connect()

        # Set timeout for this query
        if timeout:
            conn.execute(f"SET statement_timeout = '{timeout}s'")

        try:
            # Parameterized query
            if params:
                result = conn.execute(sql, params)
            else:
                result = conn.execute(sql)

            return result

        except duckdb.InterruptException:
            raise QueryTimeout(f"Query exceeded timeout ({timeout or self.timeout_seconds}s)")
        finally:
            # Reset timeout
            if timeout:
                conn.execute(f"SET statement_timeout = '{self.timeout_seconds}s'")

    def query_df(self, sql: str, **kwargs) -> Any:
        """
        Execute query and return pandas DataFrame.

        Args:
            sql: SQL query
            **kwargs: Passed to query()

        Returns:
            pandas DataFrame
        """
        result = self.query(sql, **kwargs)
        return result.df()

    def query_arrow(self, sql: str, **kwargs) -> Any:
        """
        Execute query and return Arrow table.

        Args:
            sql: SQL query
            **kwargs: Passed to query()

        Returns:
            PyArrow table
        """
        result = self.query(sql, **kwargs)
        return result.arrow()

    def register_parquet(self, name: str, path: Union[str, Path]) -> None:
        """
        Register Parquet file as table.

        Args:
            name: Table name
            path: Path to Parquet file or directory
        """
        conn = self.connect()
        path_str = str(path)

        # Check if path exists
        if not Path(path).exists():
            raise FileNotFoundError(f"Parquet file not found: {path}")

        conn.execute(f"CREATE OR REPLACE VIEW {name} AS SELECT * FROM read_parquet('{path_str}')")

    def register_arrow(self, name: str, arrow_table: Any) -> None:
        """
        Register Arrow table.

        Args:
            name: Table name
            arrow_table: PyArrow table
        """
        conn = self.connect()
        conn.register(name, arrow_table)

    def materialize(self, view_name: str, table_name: str) -> None:
        """
        Materialize view as table.

        Args:
            view_name: Source view name
            table_name: Target table name
        """
        conn = self.connect()
        conn.execute(f"CREATE OR REPLACE TABLE {table_name} AS SELECT * FROM {view_name}")

    def list_tables(self) -> List[str]:
        """List all tables and views."""
        result = self.query("SHOW TABLES")
        return [row[0] for row in result.fetchall()]

    def describe(self, table_name: str) -> Any:
        """
        Get table schema.

        Args:
            table_name: Table name

        Returns:
            DataFrame with column info
        """
        result = self.query(f"DESCRIBE {table_name}")
        return result.df()

    def get_row_count(self, table_name: str) -> int:
        """Get row count for table."""
        result = self.query(f"SELECT COUNT(*) as count FROM {table_name}")
        return result.fetchone()[0]


def create_warehouse(
    db_path: Union[str, Path] = ":memory:", **kwargs
) -> DuckDBWarehouse:
    """
    Create warehouse instance.

    Args:
        db_path: Database path
        **kwargs: Passed to DuckDBWarehouse

    Returns:
        DuckDBWarehouse instance
    """
    warehouse = DuckDBWarehouse(db_path, **kwargs)
    warehouse.connect()
    return warehouse
