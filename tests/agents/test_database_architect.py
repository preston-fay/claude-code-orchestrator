"""Tests for Database Architect agent."""

import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))


def test_database_architect_import():
    """Test that DatabaseArchitect can be imported."""
    from orchestrator.agents import DatabaseArchitect
    assert DatabaseArchitect is not None


def test_database_architect_run(tmp_path, monkeypatch):
    """Test basic database architect execution."""
    from orchestrator.agents import DatabaseArchitect

    monkeypatch.chdir(tmp_path)
    architect = DatabaseArchitect(project_root=tmp_path)

    result = architect.run(entities=["users", "projects"])

    assert result["success"] is True
    assert "artifacts" in result
    assert len(result["artifacts"]) >= 3  # schema.sql, migration, documentation
    assert "summary" in result

    # Check schema.sql was created
    assert (tmp_path / "schema.sql").exists()


def test_database_architect_schema_generation(tmp_path, monkeypatch):
    """Test schema SQL generation."""
    from orchestrator.agents import DatabaseArchitect

    monkeypatch.chdir(tmp_path)
    architect = DatabaseArchitect(project_root=tmp_path)

    result = architect.run(entities=["users"], database_type="postgresql")

    schema_path = tmp_path / "schema.sql"
    assert schema_path.exists()

    # Check SQL contains CREATE TABLE
    sql = schema_path.read_text()
    assert "CREATE TABLE users" in sql
    assert "id SERIAL" in sql or "id INTEGER" in sql


def test_database_architect_migrations(tmp_path, monkeypatch):
    """Test migration generation."""
    from orchestrator.agents import DatabaseArchitect

    monkeypatch.chdir(tmp_path)
    architect = DatabaseArchitect(project_root=tmp_path)

    result = architect.run(entities=["users"], existing_schema=False)

    # Check migrations directory was created
    migrations_dir = tmp_path / "migrations"
    assert migrations_dir.exists()

    # Check at least one migration file exists
    migration_files = list(migrations_dir.glob("*.sql"))
    assert len(migration_files) > 0


def test_database_architect_documentation(tmp_path, monkeypatch):
    """Test documentation generation."""
    from orchestrator.agents import DatabaseArchitect

    monkeypatch.chdir(tmp_path)
    architect = DatabaseArchitect(project_root=tmp_path)

    result = architect.run(entities=["users", "projects", "tasks"])

    # Check documentation was created
    doc_path = tmp_path / "reports" / "database_architecture.md"
    assert doc_path.exists()

    # Check content has table information
    content = doc_path.read_text()
    assert "Tables" in content
    assert "users" in content
