# ADR-002: DuckDB for Analytical Workloads

**Status**: Accepted

**Date**: 2025-01-26

**Decision Makers**: Data Agent, Developer Agent, Consensus Agent

**Tags**: technology, database, analytics

---

## Context

### Problem Statement
Analytics projects require querying and transforming datasets ranging from 100MB to 100GB with complex SQL operations (joins, aggregations, window functions). Current approach of loading CSV files into pandas DataFrames has performance limitations:
- 30+ second query times for 10GB datasets
- Memory constraints (entire dataset must fit in RAM)
- No SQL interface (forces Python-only transformations)
- Difficult to optimize complex analytical queries

### Business/Technical Context
The orchestrator supports analytics projects across domains (customer analytics, supply chain optimization, financial modeling). Requirements:
- **Performance**: Sub-second queries for exploratory analysis
- **SQL Support**: Standard SQL for compatibility with existing skills and workflows
- **Python Integration**: Native integration with pandas, numpy, scikit-learn
- **Simplicity**: Zero or minimal operational overhead (no database server administration)
- **Team Expertise**: Python-first team with limited database administration experience
- **Budget**: Moderate cloud spend acceptable, but not enterprise licensing costs

### Forces and Constraints
- **Performance vs. Simplicity**: Traditional databases (PostgreSQL) require server management
- **Cost vs. Features**: Cloud data warehouses (Snowflake, BigQuery) offer great performance but high cost for our data volumes
- **Flexibility vs. Standards**: NoSQL offers flexibility but lacks SQL standard compliance
- **Single-user vs. Multi-user**: Current projects are single-analyst workflows, not multi-user production databases

---

## Decision

**We will** use **DuckDB** as the primary analytical database for orchestrator projects requiring SQL query capabilities on medium to large datasets (100MB - 100GB).

**Rationale**: DuckDB provides SQL query performance comparable to traditional databases while running in-process with zero operational overhead. It integrates natively with Python and pandas, aligns with our team's Python expertise, and avoids the complexity and cost of client-server databases or cloud data warehouses.

---

## Alternatives Considered

### Option 1: PostgreSQL
**Description**: Industry-standard relational database with excellent SQL support and mature ecosystem.

**Pros**:
- Battle-tested, extremely mature (25+ years)
- Rich ecosystem (extensions, tools, documentation)
- ACID compliance, full transaction support
- Can scale to multi-user production workloads

**Cons**:
- **Operational overhead**: Requires server installation, configuration, backups, connection pooling
- **Overkill for use case**: Designed for multi-user transactional workloads, not single-user analytical queries
- **Network latency**: Client-server architecture adds overhead vs. in-process queries
- **Slower for analytics**: Optimized for OLTP (transactions), not OLAP (analytics)
- **Complexity**: Team lacks database administration expertise

**Why Rejected**: While PostgreSQL is excellent for production multi-user databases, it's overkill for single-analyst analytical workloads. The operational overhead (server management, backups, connection management) doesn't justify the benefits for our use case. DuckDB provides comparable analytical performance without the complexity.

---

### Option 2: SQLite
**Description**: Embedded SQL database, widely used, zero configuration.

**Pros**:
- Ubiquitous (ships with Python standard library)
- Zero configuration (file-based, no server)
- Stable and reliable (battle-tested)
- Lightweight

**Cons**:
- **Poor analytical performance**: Single-threaded, no parallel query execution
- **Limited analytical features**: Lacks window functions, CTEs (in older versions)
- **No columnar storage**: Row-based storage inefficient for analytical queries (wide tables with few columns accessed)
- **Large dataset limitations**: Performance degrades with multi-gigabyte datasets

**Why Rejected**: While SQLite is perfect for embedded transactional databases (mobile apps, lightweight applications), it's fundamentally designed for OLTP, not OLAP. For 10GB datasets with complex aggregations, SQLite is 10-100x slower than DuckDB. DuckDB is essentially "SQLite for analytics."

---

### Option 3: Cloud Data Warehouses (Snowflake, BigQuery, Redshift)
**Description**: Managed cloud-native data warehouses optimized for large-scale analytics.

**Pros**:
- Excellent performance at petabyte scale
- Separation of compute and storage
- Managed service (no operational overhead)
- Advanced features (time travel, clustering, materialized views)

**Cons**:
- **Cost**: Expensive for small to medium datasets (<1TB). Snowflake/BigQuery charge per query; costs add up quickly for exploratory analysis
- **Complexity**: Requires cloud account setup, IAM configuration, network rules
- **Data transfer costs**: Uploading/downloading data to/from cloud incurs egress fees
- **Latency**: Network round-trip for every query (vs. local in-process)
- **Overkill**: Designed for organizational data warehouses (100+ users, multi-TB datasets), not single-analyst projects

**Why Rejected**: Cloud data warehouses excel at enterprise-scale analytics with many concurrent users and massive datasets. For orchestrator projects (single analyst, <100GB data), the cost and complexity outweigh the benefits. DuckDB provides 80% of the performance at 0% of the operational overhead and cost.

---

### Option 4: Pandas Only (No Database)
**Description**: Continue using pandas DataFrames for all data manipulation, no SQL layer.

**Pros**:
- Already using pandas (no new dependencies)
- Pythonic API (familiar to data scientists)
- Integrates seamlessly with scikit-learn, matplotlib

**Cons**:
- **Memory constraints**: Entire dataset must fit in RAM (DataFrame holds full data)
- **Performance**: Slower than SQL for complex joins and aggregations
- **No query optimization**: Pandas executes operations sequentially, no query planner
- **Harder to optimize**: Complex operations require manual optimization (vs. SQL query optimizer)
- **Limited concurrency**: Single-threaded for most operations

**Why Rejected**: Pandas is excellent for small to medium datasets (<5GB) but struggles with larger analytical workloads. DuckDB allows us to keep the pandas workflow for small data while providing SQL performance for large datasets. DuckDB's `df()` method converts query results to pandas DataFrames, giving best of both worlds.

---

## Consequences

### Benefits
- **Zero Operational Overhead**: No database server to install, configure, backup, or maintain. DuckDB runs in-process (embedded database)
- **Fast Analytical Queries**: Columnar storage and vectorized execution provide 10-100x speedup vs. pandas for large datasets
- **SQL Standard Compliance**: Full support for window functions, CTEs, complex joins—all standard SQL
- **Native Python Integration**: Direct integration with pandas (read DataFrames, write to DataFrames), numpy arrays
- **Low Memory Footprint**: Doesn't load entire dataset into memory; streams results as needed
- **Portable**: Single-file database (or in-memory for temporary analysis)
- **Open Source**: No licensing costs, active community, regular updates

### Trade-offs and Costs
- **Single-Process Limitation**: DuckDB doesn't support concurrent writes from multiple processes. Fine for single-analyst workflows, but not suitable for multi-user production databases.
- **Less Mature Ecosystem**: Younger project than PostgreSQL/MySQL; fewer third-party tools, extensions, and integrations.
- **No Built-in Replication**: No native replication or high-availability features (not needed for analytical workloads but worth noting).
- **Learning Curve**: Team familiar with pandas must learn SQL (though SQL is widely known among data professionals).

### Risks
- **Risk**: DuckDB is relatively new (first release 2019); potential for bugs, API changes, or lack of long-term support.
  - **Mitigation**: DuckDB has active development, strong community, and is backed by DuckDB Labs. Used in production by major companies (Observable, Hex, Mode Analytics). For our non-critical analytical workloads, moderate risk is acceptable.

- **Risk**: If requirements evolve to need multi-user concurrent access, DuckDB's single-process limitation becomes a blocker.
  - **Mitigation**: For now, single-analyst access pattern is sufficient. If multi-user needs arise, we can migrate to PostgreSQL (SQL compatibility makes migration straightforward) or use DuckDB in read-only mode with separate write process. Document this as a known limitation.

- **Risk**: DuckDB's Python API may change between versions (it's pre-1.0 as of decision date).
  - **Mitigation**: Pin DuckDB version in requirements.txt. Test upgrades thoroughly. DuckDB has commitment to stability, and API is stabilizing.

### Implementation Effort
**Estimated Effort**: Small

- Install DuckDB: `pip install duckdb` (single dependency)
- Minimal code changes: Replace pandas operations with SQL queries where performance matters
- No infrastructure setup (no servers, no cloud accounts)
- Training: Team already knows SQL; just need to learn DuckDB-specific functions (well-documented)

**Migration from Pandas**: Incremental adoption possible. Can use pandas for small data, DuckDB for large datasets, with seamless interop.

---

## Implementation Notes

### Getting Started

**Installation**:
```bash
pip install duckdb>=0.10
```

**Basic Usage**:
```python
import duckdb
import pandas as pd

# Option 1: Query CSV directly (no loading to memory)
result = duckdb.query("SELECT * FROM 'data/large_file.csv' WHERE amount > 1000").df()

# Option 2: Query pandas DataFrame
df = pd.read_csv('data/small_file.csv')
result = duckdb.query("SELECT category, SUM(amount) FROM df GROUP BY category").df()

# Option 3: Persistent database file
con = duckdb.connect('analytics.duckdb')
con.execute("CREATE TABLE sales AS SELECT * FROM 'data/sales.csv'")
result = con.execute("SELECT * FROM sales WHERE year = 2024").df()
con.close()
```

### Configuration

**Recommended Settings**:
```python
# Increase memory limit for large queries (default is conservative)
duckdb.execute("SET memory_limit='4GB'")

# Enable progress bar for long-running queries
duckdb.execute("SET enable_progress_bar=true")

# Set threads for parallel execution (default: all cores)
duckdb.execute("SET threads TO 4")
```

### Integration Patterns

**Pattern 1: Ephemeral Analysis (In-Memory)**
```python
# No persistent database; query CSV/Parquet files directly
result = duckdb.query("""
    SELECT
        customer_id,
        SUM(amount) as total_spend,
        COUNT(*) as num_orders
    FROM 'data/orders.parquet'
    WHERE order_date >= '2024-01-01'
    GROUP BY customer_id
    ORDER BY total_spend DESC
    LIMIT 100
""").df()
```

**Pattern 2: Persistent Analytical Database**
```python
# Create database file for repeated analysis
con = duckdb.connect('project_analytics.duckdb')

# Load data once (from CSV/Parquet)
con.execute("CREATE TABLE customers AS SELECT * FROM 'data/customers.csv'")
con.execute("CREATE TABLE orders AS SELECT * FROM 'data/orders.csv'")

# Run multiple queries
high_value_customers = con.execute("""
    SELECT c.*, SUM(o.amount) as lifetime_value
    FROM customers c
    JOIN orders o ON c.customer_id = o.customer_id
    GROUP BY c.customer_id
    HAVING lifetime_value > 10000
""").df()

con.close()
```

**Pattern 3: Hybrid Pandas + DuckDB**
```python
# Use pandas for small data manipulation, DuckDB for heavy lifting
import pandas as pd
import duckdb

# Load small reference data with pandas
categories = pd.read_csv('data/categories.csv')  # 100 rows

# Query large transactional data with DuckDB, join with pandas DataFrame
transactions = duckdb.query("""
    SELECT
        t.transaction_id,
        t.amount,
        c.category_name
    FROM 'data/transactions.parquet' t
    JOIN categories c ON t.category_id = c.category_id
    WHERE t.amount > 100
""").df()

# Continue analysis in pandas
summary = transactions.groupby('category_name')['amount'].agg(['sum', 'mean', 'count'])
```

### Migration Strategy

**From Pandas to DuckDB** (gradual adoption):
1. Identify slow pandas operations (>10 seconds)
2. Replace with equivalent DuckDB SQL query
3. Benchmark performance improvement
4. Expand DuckDB usage for other large-dataset operations

**From DuckDB to PostgreSQL** (if multi-user needs arise):
1. DuckDB's SQL is PostgreSQL-compatible (subset)
2. Export tables: `COPY table TO 'table.csv'`
3. Import to PostgreSQL: `COPY table FROM 'table.csv'`
4. Minor query adjustments may be needed (DuckDB extensions)

---

## Related Decisions

- **Depends on**: [ADR-001: Multi-Agent Orchestration](./ADR-001-multi-agent-orchestration.md) - Data Agent uses DuckDB for analytical tasks
- **Related**: Future ADR on data pipeline architecture (DuckDB as transformation layer)

---

## References

- [DuckDB Official Documentation](https://duckdb.org/docs/)
- [DuckDB Python API](https://duckdb.org/docs/api/python/overview)
- [DuckDB vs. PostgreSQL Benchmark](https://duckdb.org/2021/05/14/sql-on-pandas.html)
- [Why DuckDB? (Blog Post)](https://duckdb.org/why_duckdb)
- [DuckDB: An Embeddable Analytical Database (Paper)](https://15721.courses.cs.cmu.edu/spring2023/papers/02-modern/p2168-raasveldt.pdf)

---

## Notes and Discussion

- **2025-01-26 Data Agent**: Proposed DuckDB after benchmarking on 10GB dataset showed 50x speedup vs. pandas for aggregation queries
- **2025-01-26 Developer Agent**: Validated Python integration; DuckDB's `df()` method makes pandas interop seamless
- **2025-01-26 Consensus Agent**: Approved with note that single-process limitation should be revisited if multi-user requirements emerge

---

## Revision History

| Date | Author | Change |
|------|--------|--------|
| 2025-01-26 | Data Agent | Initial draft (Status: Proposed) |
| 2025-01-26 | Developer Agent | Added implementation patterns and code examples |
| 2025-01-26 | Consensus Agent | Accepted with documentation of known limitations |

---

**Template Version**: 1.0.0
**Last Updated**: 2025-01-26
