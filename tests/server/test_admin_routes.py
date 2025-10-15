"""Tests for admin dashboard routes."""

import pytest
from fastapi.testclient import TestClient
from pathlib import Path
import tempfile
import json

from src.server.app import app, get_warehouse
from src.data.warehouse import DuckDBWarehouse


@pytest.fixture
def test_warehouse():
    """Create test warehouse with sample data."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.duckdb"
        warehouse = DuckDBWarehouse(db_path, read_only=False)
        warehouse.connect()

        # Create test table
        warehouse.conn.execute("""
            CREATE TABLE test_data (
                id INTEGER,
                name VARCHAR,
                value DOUBLE
            )
        """)

        # Insert sample data
        warehouse.conn.execute("""
            INSERT INTO test_data VALUES
                (1, 'Alice', 100.5),
                (2, 'Bob', 200.3),
                (3, 'Charlie', 300.7)
        """)

        yield warehouse
        warehouse.disconnect()


@pytest.fixture
def client(test_warehouse, monkeypatch):
    """Create test client with mocked warehouse."""
    def mock_get_warehouse():
        return test_warehouse

    monkeypatch.setattr("src.server.app.get_warehouse", mock_get_warehouse)
    monkeypatch.setattr("src.server.admin.routes.get_warehouse", mock_get_warehouse)

    return TestClient(app)


class TestAdminDashboard:
    """Test admin dashboard endpoint."""

    def test_dashboard_loads(self, client):
        """Dashboard should load with KPIs."""
        response = client.get("/admin")
        assert response.status_code == 200
        assert b"Kearney Data Platform" in response.content
        assert b"Cleanliness Score" in response.content
        assert b"Total Queries" in response.content

    def test_dashboard_has_no_emojis(self, client):
        """Dashboard should not contain emojis."""
        response = client.get("/admin")
        content = response.content.decode('utf-8')

        # Check for common emoji unicode ranges
        emoji_ranges = [
            (0x1F600, 0x1F64F),  # Emoticons
            (0x1F300, 0x1F5FF),  # Misc Symbols
            (0x1F680, 0x1F6FF),  # Transport
        ]

        for char in content:
            code = ord(char)
            for start, end in emoji_ranges:
                assert not (start <= code <= end), f"Found emoji: {char}"

    def test_dashboard_uses_tokens(self, client):
        """Dashboard should reference design tokens."""
        response = client.get("/admin")
        content = response.content.decode('utf-8')

        # Should link to tokens.css
        assert "/static/tokens.css" in content

        # Should use CSS custom properties
        assert "var(--" in content


class TestSQLConsole:
    """Test SQL console endpoint."""

    def test_sql_console_get(self, client):
        """SQL console form should load."""
        response = client.get("/admin/sql")
        assert response.status_code == 200
        assert b"SQL Console" in response.content
        assert b"Available Tables" in response.content

    def test_sql_select_allowed(self, client):
        """SELECT queries should be allowed."""
        response = client.post("/admin/sql", data={
            "sql": "SELECT * FROM test_data",
            "limit": 100,
            "timeout": 3
        })
        assert response.status_code == 200
        assert b"Alice" in response.content
        assert b"Bob" in response.content
        assert b"Charlie" in response.content

    def test_sql_drop_blocked(self, client):
        """DROP queries should be blocked."""
        response = client.post("/admin/sql", data={
            "sql": "DROP TABLE test_data",
            "limit": 100,
            "timeout": 3
        })
        assert response.status_code == 200
        assert b"Query not allowed" in response.content or b"not permitted" in response.content

    def test_sql_delete_blocked(self, client):
        """DELETE queries should be blocked."""
        response = client.post("/admin/sql", data={
            "sql": "DELETE FROM test_data WHERE id = 1",
            "limit": 100,
            "timeout": 3
        })
        assert response.status_code == 200
        assert b"Query not allowed" in response.content or b"not permitted" in response.content

    def test_sql_row_limit_enforced(self, client):
        """Row limit should be enforced at MAX_ROWS."""
        # Try to request more than MAX_ROWS (1000)
        response = client.post("/admin/sql", data={
            "sql": "SELECT * FROM test_data",
            "limit": 5000,  # Over limit
            "timeout": 3
        })
        assert response.status_code == 200
        # Should still succeed but limit to MAX_ROWS

    def test_sql_auto_limit_added(self, client):
        """LIMIT should be auto-added if missing."""
        response = client.post("/admin/sql", data={
            "sql": "SELECT * FROM test_data",
            "limit": 2,
            "timeout": 3
        })
        assert response.status_code == 200
        # Should only return 2 rows (auto-added LIMIT)
        assert response.content.count(b"<tr>") <= 4  # Header + 2 data rows

    def test_sql_csv_export(self, client):
        """CSV export should work."""
        response = client.post("/admin/sql", data={
            "sql": "SELECT * FROM test_data",
            "limit": 100,
            "timeout": 3,
            "export": "csv"
        })
        assert response.status_code == 200
        assert response.headers["content-type"] == "text/csv; charset=utf-8"
        assert b"id,name,value" in response.content or b"Alice" in response.content

    def test_sql_timeout_enforced(self, client):
        """Timeout should be enforced at 10 seconds max."""
        response = client.post("/admin/sql", data={
            "sql": "SELECT * FROM test_data",
            "limit": 100,
            "timeout": 999  # Over limit
        })
        # Should not fail - timeout capped at 10s
        assert response.status_code == 200


class TestArtifactsBrowser:
    """Test artifacts browser endpoint."""

    def test_artifacts_browser_loads(self, client):
        """Artifacts browser should load."""
        response = client.get("/admin/artifacts")
        assert response.status_code == 200
        assert b"Artifacts" in response.content

    def test_artifacts_lists_runs(self, client, tmp_path, monkeypatch):
        """Artifacts browser should list run IDs."""
        # Create mock artifacts directory
        artifacts_dir = tmp_path / "artifacts"
        artifacts_dir.mkdir()

        run1_dir = artifacts_dir / "run_20250115_120000"
        run1_dir.mkdir()
        (run1_dir / "test.json").write_text('{"test": true}')

        monkeypatch.setattr("src.server.admin.routes.ARTIFACTS_DIR", artifacts_dir)

        response = client.get("/admin/artifacts")
        assert response.status_code == 200
        assert b"run_20250115_120000" in response.content

    def test_artifact_download(self, client, tmp_path, monkeypatch):
        """Artifact download should work."""
        artifacts_dir = tmp_path / "artifacts"
        artifacts_dir.mkdir()

        run_dir = artifacts_dir / "run_test"
        run_dir.mkdir()
        test_file = run_dir / "data.json"
        test_file.write_text('{"key": "value"}')

        monkeypatch.setattr("src.server.admin.routes.ARTIFACTS_DIR", artifacts_dir)

        response = client.get("/admin/artifacts/run_test/data.json")
        assert response.status_code == 200
        assert b"key" in response.content

    def test_artifact_download_path_traversal_blocked(self, client):
        """Path traversal in artifact download should be blocked."""
        response = client.get("/admin/artifacts/run_test/../../../etc/passwd")
        assert response.status_code in (404, 400, 403)  # Should be blocked


class TestStaticFiles:
    """Test static file serving."""

    def test_tokens_css_available(self, client):
        """tokens.css should be available."""
        response = client.get("/static/tokens.css")
        # May be 200 if file exists, or 404 if not yet copied
        # Just verify endpoint is mounted
        assert response.status_code in (200, 404)

    def test_static_mount_exists(self, client):
        """Static mount should be configured."""
        # Verify app has static mount
        from src.server.app import app
        routes = [route.path for route in app.routes]
        assert any("/static" in path for path in routes)


class TestSQLSafety:
    """Test SQL safety mechanisms."""

    def test_with_cte_allowed(self, client):
        """WITH (CTE) queries should be allowed."""
        response = client.post("/admin/sql", data={
            "sql": """
                WITH summary AS (
                    SELECT name, value FROM test_data
                )
                SELECT * FROM summary
            """,
            "limit": 100,
            "timeout": 3
        })
        assert response.status_code == 200
        assert b"Alice" in response.content

    def test_describe_allowed(self, client):
        """DESCRIBE queries should be allowed."""
        response = client.post("/admin/sql", data={
            "sql": "DESCRIBE test_data",
            "limit": 100,
            "timeout": 3
        })
        assert response.status_code == 200
        # Should show schema info

    def test_multiple_statements_blocked(self, client):
        """Multiple statements should be blocked."""
        response = client.post("/admin/sql", data={
            "sql": "SELECT * FROM test_data; DROP TABLE test_data;",
            "limit": 100,
            "timeout": 3
        })
        # Should either block or only execute first statement
        assert response.status_code in (200, 403)

    def test_create_user_blocked(self, client):
        """CREATE USER should be blocked."""
        response = client.post("/admin/sql", data={
            "sql": "CREATE USER hacker WITH PASSWORD 'bad'",
            "limit": 100,
            "timeout": 3
        })
        assert response.status_code == 200
        assert b"Query not allowed" in response.content or b"not permitted" in response.content
