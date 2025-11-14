"""Database Architect agent implementation."""

import json
import time
from pathlib import Path
from typing import Dict, List, Optional, Any


class DatabaseArchitect:
    """Database schema design and migration planning agent.

    Designs database schemas, generates migrations, and provides
    optimization recommendations.
    """

    def __init__(self, project_root: Optional[Path] = None):
        """Initialize database architect.

        Args:
            project_root: Project root directory (defaults to cwd)
        """
        self.project_root = project_root or Path.cwd()
        self.reports_dir = self.project_root / "reports"
        self.migrations_dir = self.project_root / "migrations"
        self.reports_dir.mkdir(exist_ok=True)
        self.migrations_dir.mkdir(exist_ok=True)

    def run(
        self,
        *,
        database_type: str = "postgresql",
        entities: Optional[List[str]] = None,
        existing_schema: bool = False,
        **kwargs
    ) -> Dict[str, Any]:
        """Run database architecture and generate schema.

        Args:
            database_type: Database type (postgresql, mysql, sqlite)
            entities: List of entity names to create tables for
            existing_schema: Whether to generate migrations for existing schema
            **kwargs: Additional configuration

        Returns:
            Dict with artifact paths and summary
        """
        print("🗄️  Database Architect: Designing database schema...")

        start_time = time.time()

        entities = entities or ["users", "projects", "tasks"]

        # Design schema
        schema = self._design_schema(entities, database_type)

        # Generate migrations
        migrations = self._generate_migrations(schema, existing_schema)

        # Generate index recommendations
        index_recommendations = self._recommend_indexes(schema)

        # Write artifacts
        artifacts = self._write_artifacts(schema, migrations, index_recommendations, database_type)

        duration = time.time() - start_time

        print(f"✓ Database schema design complete ({duration:.2f}s)")
        print(f"  Tables: {len(schema['tables'])}")
        print(f"  Migrations: {len(migrations)}")
        print(f"  Artifacts: {', '.join(artifacts)}")

        return {
            "success": True,
            "artifacts": artifacts,
            "summary": {
                "tables_count": len(schema["tables"]),
                "migrations_count": len(migrations),
                "indexes_recommended": len(index_recommendations),
                "database_type": database_type,
            },
            "duration_s": duration,
        }

    def _design_schema(self, entities: List[str], db_type: str) -> Dict[str, Any]:
        """Design database schema for entities."""
        tables = []

        # Create a table for each entity
        for entity in entities:
            table_name = entity.lower()
            columns = self._generate_columns_for_entity(entity)
            indexes = self._generate_indexes_for_table(table_name, columns)
            constraints = self._generate_constraints_for_table(table_name, entities)

            tables.append({
                "name": table_name,
                "columns": columns,
                "indexes": indexes,
                "constraints": constraints,
            })

        # Add junction tables for many-to-many relationships
        if "projects" in entities and "users" in entities:
            tables.append({
                "name": "project_members",
                "columns": [
                    {"name": "project_id", "type": "INTEGER", "nullable": False},
                    {"name": "user_id", "type": "INTEGER", "nullable": False},
                    {"name": "role", "type": "VARCHAR(50)", "nullable": False, "default": "'member'"},
                    {"name": "joined_at", "type": "TIMESTAMP", "nullable": False, "default": "CURRENT_TIMESTAMP"},
                ],
                "indexes": [
                    {"name": "idx_project_members_project_id", "columns": ["project_id"]},
                    {"name": "idx_project_members_user_id", "columns": ["user_id"]},
                ],
                "constraints": [
                    {"type": "PRIMARY KEY", "columns": ["project_id", "user_id"]},
                    {"type": "FOREIGN KEY", "columns": ["project_id"], "references": "projects(id)"},
                    {"type": "FOREIGN KEY", "columns": ["user_id"], "references": "users(id)"},
                ],
            })

        return {
            "database_type": db_type,
            "tables": tables,
            "version": "1.0.0",
        }

    def _generate_columns_for_entity(self, entity: str) -> List[Dict[str, Any]]:
        """Generate standard columns for an entity."""
        entity_lower = entity.lower()

        # Standard columns for all tables
        columns = [
            {"name": "id", "type": "SERIAL", "nullable": False},
            {"name": "created_at", "type": "TIMESTAMP", "nullable": False, "default": "CURRENT_TIMESTAMP"},
            {"name": "updated_at", "type": "TIMESTAMP", "nullable": False, "default": "CURRENT_TIMESTAMP"},
        ]

        # Entity-specific columns
        if entity_lower == "users":
            columns.extend([
                {"name": "email", "type": "VARCHAR(255)", "nullable": False, "unique": True},
                {"name": "username", "type": "VARCHAR(50)", "nullable": False, "unique": True},
                {"name": "password_hash", "type": "VARCHAR(255)", "nullable": False},
                {"name": "first_name", "type": "VARCHAR(100)", "nullable": True},
                {"name": "last_name", "type": "VARCHAR(100)", "nullable": True},
                {"name": "is_active", "type": "BOOLEAN", "nullable": False, "default": "TRUE"},
            ])
        elif entity_lower == "projects":
            columns.extend([
                {"name": "name", "type": "VARCHAR(200)", "nullable": False},
                {"name": "description", "type": "TEXT", "nullable": True},
                {"name": "owner_id", "type": "INTEGER", "nullable": False},
                {"name": "status", "type": "VARCHAR(50)", "nullable": False, "default": "'active'"},
                {"name": "deadline", "type": "DATE", "nullable": True},
            ])
        elif entity_lower == "tasks":
            columns.extend([
                {"name": "title", "type": "VARCHAR(200)", "nullable": False},
                {"name": "description", "type": "TEXT", "nullable": True},
                {"name": "project_id", "type": "INTEGER", "nullable": False},
                {"name": "assignee_id", "type": "INTEGER", "nullable": True},
                {"name": "status", "type": "VARCHAR(50)", "nullable": False, "default": "'todo'"},
                {"name": "priority", "type": "VARCHAR(20)", "nullable": False, "default": "'medium'"},
                {"name": "due_date", "type": "TIMESTAMP", "nullable": True},
            ])

        return columns

    def _generate_indexes_for_table(self, table_name: str, columns: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Generate recommended indexes for table."""
        indexes = []

        # Primary key index (auto-created)
        # indexes.append({"name": f"idx_{table_name}_id", "columns": ["id"], "type": "PRIMARY KEY"})

        # Foreign key indexes
        fk_columns = [c["name"] for c in columns if c["name"].endswith("_id")]
        for fk_col in fk_columns:
            indexes.append({"name": f"idx_{table_name}_{fk_col}", "columns": [fk_col]})

        # Unique columns
        unique_columns = [c["name"] for c in columns if c.get("unique", False)]
        for unique_col in unique_columns:
            indexes.append({"name": f"idx_{table_name}_{unique_col}", "columns": [unique_col], "unique": True})

        # Status column (common query filter)
        if any(c["name"] == "status" for c in columns):
            indexes.append({"name": f"idx_{table_name}_status", "columns": ["status"]})

        return indexes

    def _generate_constraints_for_table(self, table_name: str, all_entities: List[str]) -> List[Dict[str, Any]]:
        """Generate constraints for table."""
        constraints = [
            {"type": "PRIMARY KEY", "columns": ["id"]}
        ]

        # Foreign key constraints
        if table_name == "projects":
            constraints.append({
                "type": "FOREIGN KEY",
                "columns": ["owner_id"],
                "references": "users(id)",
                "on_delete": "CASCADE"
            })
        elif table_name == "tasks":
            constraints.append({
                "type": "FOREIGN KEY",
                "columns": ["project_id"],
                "references": "projects(id)",
                "on_delete": "CASCADE"
            })
            constraints.append({
                "type": "FOREIGN KEY",
                "columns": ["assignee_id"],
                "references": "users(id)",
                "on_delete": "SET NULL"
            })

        return constraints

    def _generate_migrations(self, schema: Dict[str, Any], existing_schema: bool) -> List[Dict[str, Any]]:
        """Generate migration scripts."""
        migrations = []

        if existing_schema:
            # Migration to add new tables
            migrations.append({
                "version": "001_add_initial_tables",
                "description": "Add initial database tables",
                "up": "-- Migration up script (see schema.sql)",
                "down": "-- Rollback script"
            })
        else:
            # Initial schema creation
            migrations.append({
                "version": "000_initial_schema",
                "description": "Create initial database schema",
                "up": "-- See schema.sql for full schema",
                "down": "DROP TABLE IF EXISTS tasks, projects, users CASCADE;"
            })

        return migrations

    def _recommend_indexes(self, schema: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate index optimization recommendations."""
        recommendations = []

        for table in schema["tables"]:
            # Recommend composite indexes for common query patterns
            if table["name"] == "tasks":
                recommendations.append({
                    "table": "tasks",
                    "index": "idx_tasks_project_status",
                    "columns": ["project_id", "status"],
                    "rationale": "Optimize queries filtering by project and status together",
                    "impact": "High - Common query pattern"
                })
                recommendations.append({
                    "table": "tasks",
                    "index": "idx_tasks_assignee_status",
                    "columns": ["assignee_id", "status"],
                    "rationale": "Optimize user task list queries",
                    "impact": "Medium"
                })

        return recommendations

    def _write_artifacts(
        self,
        schema: Dict[str, Any],
        migrations: List[Dict[str, Any]],
        index_recommendations: List[Dict[str, Any]],
        db_type: str
    ) -> List[str]:
        """Write database architecture artifacts."""
        artifacts = []

        # Write schema.sql
        schema_sql = self._generate_sql(schema, db_type)
        schema_path = self.project_root / "schema.sql"
        schema_path.write_text(schema_sql)
        artifacts.append(str(schema_path))

        # Write migrations
        for migration in migrations:
            migration_file = self.migrations_dir / f"{migration['version']}.sql"
            migration_file.write_text(f"-- {migration['description']}\n\n{migration['up']}\n")
            artifacts.append(str(migration_file))

        # Write architecture documentation
        arch_md = self._format_architecture_markdown(schema, index_recommendations)
        arch_path = self.reports_dir / "database_architecture.md"
        arch_path.write_text(arch_md)
        artifacts.append(str(arch_path))

        # Write index recommendations JSON
        index_rec_path = self.reports_dir / "index_recommendations.json"
        index_rec_path.write_text(json.dumps({
            "recommendations": index_recommendations,
            "database_type": db_type,
        }, indent=2))
        artifacts.append(str(index_rec_path))

        return artifacts

    def _generate_sql(self, schema: Dict[str, Any], db_type: str) -> str:
        """Generate SQL DDL from schema."""
        sql = f"-- Database Schema for {schema['database_type'].upper()}\n"
        sql += f"-- Generated by Database Architect\n"
        sql += f"-- Version: {schema['version']}\n\n"

        for table in schema["tables"]:
            sql += f"CREATE TABLE {table['name']} (\n"

            # Columns
            column_defs = []
            for col in table["columns"]:
                col_def = f"  {col['name']} {col['type']}"
                if not col.get("nullable", True):
                    col_def += " NOT NULL"
                if "default" in col:
                    col_def += f" DEFAULT {col['default']}"
                if col.get("unique", False):
                    col_def += " UNIQUE"
                column_defs.append(col_def)

            # Constraints
            for constraint in table.get("constraints", []):
                if constraint["type"] == "PRIMARY KEY":
                    column_defs.append(f"  PRIMARY KEY ({', '.join(constraint['columns'])})")
                elif constraint["type"] == "FOREIGN KEY":
                    fk_def = f"  FOREIGN KEY ({', '.join(constraint['columns'])}) REFERENCES {constraint['references']}"
                    if "on_delete" in constraint:
                        fk_def += f" ON DELETE {constraint['on_delete']}"
                    column_defs.append(fk_def)

            sql += ",\n".join(column_defs)
            sql += "\n);\n\n"

            # Indexes
            for index in table.get("indexes", []):
                unique = "UNIQUE " if index.get("unique", False) else ""
                sql += f"CREATE {unique}INDEX {index['name']} ON {table['name']} ({', '.join(index['columns'])});\n"

            sql += "\n"

        return sql

    def _format_architecture_markdown(
        self, schema: Dict[str, Any], index_recommendations: List[Dict[str, Any]]
    ) -> str:
        """Format database architecture as markdown."""
        md = f"""# Database Architecture

**Database Type**: {schema['database_type'].upper()}
**Schema Version**: {schema['version']}

## Tables

"""

        for table in schema["tables"]:
            md += f"### {table['name']}\n\n"
            md += "| Column | Type | Nullable | Default |\n"
            md += "|--------|------|----------|----------|\n"

            for col in table["columns"]:
                nullable = "No" if not col.get("nullable", True) else "Yes"
                default = col.get("default", "-")
                md += f"| {col['name']} | {col['type']} | {nullable} | {default} |\n"

            md += "\n"

            if table.get("indexes"):
                md += "**Indexes:**\n"
                for idx in table["indexes"]:
                    md += f"- `{idx['name']}` on ({', '.join(idx['columns'])})\n"
                md += "\n"

        if index_recommendations:
            md += "## Index Optimization Recommendations\n\n"
            for rec in index_recommendations:
                md += f"### {rec['table']}.{rec['index']}\n"
                md += f"- **Columns**: {', '.join(rec['columns'])}\n"
                md += f"- **Rationale**: {rec['rationale']}\n"
                md += f"- **Impact**: {rec['impact']}\n\n"

        return md


def main():
    """CLI entrypoint for database architect."""
    import sys

    architect = DatabaseArchitect()
    result = architect.run(entities=["users", "projects", "tasks"])

    if result["success"]:
        print("\n✓ Database schema design complete")
        sys.exit(0)
    else:
        print("\n✗ Database schema design failed")
        sys.exit(1)


if __name__ == "__main__":
    main()
