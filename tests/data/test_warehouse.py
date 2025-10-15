"""Tests for DuckDB warehouse with safety features."""

import pytest
from pathlib import Path
from src.data.warehouse import (
    DuckDBWarehouse,
    QueryNotAllowed,
    QueryTimeout,
    create_warehouse,
)


class TestWarehouseSafety:
    """Test warehouse safety features."""

    def test_create_in_memory_warehouse(self):
        """Test creating in-memory warehouse."""
        wh = create_warehouse()
        assert wh is not None
        assert wh.db_path == ":memory:"

    def test_select_query_allowed(self):
        """Test that SELECT queries are allowed."""
        wh = create_warehouse()

        # Create test table
        wh.query("CREATE TABLE test (id INTEGER, name VARCHAR)", check_allowlist=False)
        wh.query("INSERT INTO test VALUES (1, 'Alice'), (2, 'Bob')", check_allowlist=False)

        # SELECT should be allowed
        result = wh.query("SELECT * FROM test")
        rows = result.fetchall()
        assert len(rows) == 2

    def test_with_cte_allowed(self):
        """Test that WITH (CTE) queries are allowed."""
        wh = create_warehouse()
        wh.query("CREATE TABLE test (id INTEGER)", check_allowlist=False)
        wh.query("INSERT INTO test VALUES (1), (2), (3)", check_allowlist=False)

        # WITH should be allowed
        result = wh.query("WITH cte AS (SELECT * FROM test WHERE id > 1) SELECT * FROM cte")
        rows = result.fetchall()
        assert len(rows) == 2

    def test_drop_blocked(self):
        """Test that DROP is blocked."""
        wh = create_warehouse()
        wh.query("CREATE TABLE test (id INTEGER)", check_allowlist=False)

        # DROP should be blocked
        with pytest.raises(QueryNotAllowed, match="blocked pattern"):
            wh.query("DROP TABLE test")

    def test_delete_blocked(self):
        """Test that DELETE is blocked."""
        wh = create_warehouse()
        wh.query("CREATE TABLE test (id INTEGER)", check_allowlist=False)

        # DELETE should be blocked
        with pytest.raises(QueryNotAllowed, match="blocked pattern"):
            wh.query("DELETE FROM test")

    def test_alter_blocked(self):
        """Test that ALTER is blocked."""
        wh = create_warehouse()
        wh.query("CREATE TABLE test (id INTEGER)", check_allowlist=False)

        # ALTER should be blocked
        with pytest.raises(QueryNotAllowed, match="blocked pattern"):
            wh.query("ALTER TABLE test ADD COLUMN name VARCHAR")

    def test_truncate_blocked(self):
        """Test that TRUNCATE is blocked."""
        wh = create_warehouse()

        with pytest.raises(QueryNotAllowed, match="blocked pattern"):
            wh.query("TRUNCATE TABLE test")

    def test_parameterized_query(self):
        """Test parameterized queries."""
        wh = create_warehouse()
        wh.query("CREATE TABLE test (id INTEGER, name VARCHAR)", check_allowlist=False)
        wh.query("INSERT INTO test VALUES (1, 'Alice'), (2, 'Bob')", check_allowlist=False)

        # Parameterized query
        result = wh.query("SELECT * FROM test WHERE id = $id", params={"id": 1})
        rows = result.fetchall()
        assert len(rows) == 1
        assert rows[0][1] == "Alice"

    def test_query_timeout(self):
        """Test query timeout protection."""
        wh = create_warehouse(timeout_seconds=1)

        # This should timeout (very long-running query simulation)
        with pytest.raises(QueryTimeout):
            wh.query(
                "SELECT * FROM range(10000000) t1, range(10000000) t2",
                check_allowlist=False,
                timeout=1
            )

    def test_register_parquet(self, tmp_path):
        """Test registering Parquet files."""
        import pyarrow as pa
        import pyarrow.parquet as pq

        # Create test Parquet file
        table = pa.table({"id": [1, 2, 3], "name": ["Alice", "Bob", "Charlie"]})
        parquet_path = tmp_path / "test.parquet"
        pq.write_table(table, parquet_path)

        # Register and query
        wh = create_warehouse()
        wh.register_parquet("test_data", parquet_path)

        result = wh.query("SELECT * FROM test_data")
        rows = result.fetchall()
        assert len(rows) == 3

    def test_query_df(self):
        """Test returning pandas DataFrame."""
        wh = create_warehouse()
        wh.query("CREATE TABLE test (id INTEGER, value FLOAT)", check_allowlist=False)
        wh.query("INSERT INTO test VALUES (1, 10.5), (2, 20.5)", check_allowlist=False)

        df = wh.query_df("SELECT * FROM test")
        assert len(df) == 2
        assert "id" in df.columns
        assert "value" in df.columns

    def test_list_tables(self):
        """Test listing tables."""
        wh = create_warehouse()
        wh.query("CREATE TABLE table1 (id INTEGER)", check_allowlist=False)
        wh.query("CREATE TABLE table2 (id INTEGER)", check_allowlist=False)

        tables = wh.list_tables()
        assert "table1" in tables
        assert "table2" in tables

    def test_describe_table(self):
        """Test table schema description."""
        wh = create_warehouse()
        wh.query("CREATE TABLE test (id INTEGER, name VARCHAR, value FLOAT)", check_allowlist=False)

        schema = wh.describe("test")
        assert len(schema) == 3
        assert "column_name" in schema.columns

    def test_materialize_view(self):
        """Test materializing view as table."""
        wh = create_warehouse()
        wh.query("CREATE TABLE source (id INTEGER)", check_allowlist=False)
        wh.query("INSERT INTO source VALUES (1), (2), (3)", check_allowlist=False)
        wh.query("CREATE VIEW test_view AS SELECT * FROM source WHERE id > 1", check_allowlist=False)

        # Materialize
        wh.materialize("test_view", "materialized_table")

        result = wh.query("SELECT COUNT(*) FROM materialized_table")
        count = result.fetchone()[0]
        assert count == 2
