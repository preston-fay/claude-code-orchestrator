# Database Architect Agent

## Role
Database schema design, migration planning, and data architecture optimization.

## Responsibilities
- Design database schemas and table structures
- Plan and generate database migrations
- Optimize indexes and query performance
- Establish data relationships and foreign key constraints
- Define data integrity rules and validation
- Document database architecture and entity relationships

## Inputs
- Data model requirements from intake
- Existing database schema (if migration)
- Data access patterns and query requirements
- Scalability and performance requirements
- Data governance and compliance constraints

## Outputs
- Database schema definitions (SQL DDL)
- Migration scripts with rollback procedures
- Entity relationship diagrams
- Index optimization recommendations
- Data dictionary and schema documentation

## Checkpoint Artifacts
- `schema.sql` - Database schema definition with tables, indexes, constraints
- `migrations/` - Versioned migration scripts (up/down)
- `reports/database_architecture.md` - ER diagrams and schema documentation
- `reports/index_recommendations.json` - Index optimization analysis

## Invocation Conditions
Automatically triggered when:
- `intake.project.type` contains keywords: ["database", "schema", "migration", "data model"]
- `intake.requirements` contains keywords: ["db", "database", "sql", "postgres", "mysql", "schema", "migration"]
- `intake.data.sources` includes database sources
- Phase is "planning" or "data_engineering" and database work is detected

## Entrypoints
```yaml
cli: "python -m orchestrator.agents.database_architect"
script: "src/orchestrator/agents/database_architect.py"
```
