# MCP Code Execution Mode - Playbook

This playbook explains how to use the MCP code execution mode in the orchestrator.

## Quick Start

```bash
# Start a run with code execution mode
orchestrator run start --mode code --intake myproject.yaml

# Execute the first phase
orchestrator run next

# Check logs and artifacts
ls .work/generated/    # Generated Python code
ls .work/logs/         # Execution stdout/stderr
ls .work/results/      # JSON execution results
ls reports/            # Generated reports and plots
```

## What is MCP Code Execution?

MCP (Model Context Protocol) code execution is a pattern where:
1. LLM generates Python code that imports filesystem-based APIs
2. Code runs in a sandboxed environment
3. Artifacts are written to well-known paths

**Benefits**:
- **98% token reduction**: From ~150k to ~2k tokens for typical data tasks
- **Faster execution**: Less LLM processing, more local compute
- **Reproducible**: Generated code can be reviewed and re-run

## Execution Modes

| Mode | Description | Default | Use When |
|------|-------------|---------|----------|
| `legacy` | Existing LLM/subprocess executors | ✅ Yes | Production workflows, proven patterns |
| `code` | MCP code generation + sandbox | ❌ No | Data analysis, model training, report generation |

## Usage

### 1. Starting a Code Execution Run

```bash
orchestrator run start \
  --mode code \
  --intake intake.yaml \
  --from data_engineering
```

**Options**:
- `--mode code`: Enable code execution mode (defaults to `legacy`)
- `--intake`: Path to intake YAML (project configuration)
- `--from`: Start from specific phase (optional)

### 2. Monitoring Execution

During execution, check progress:

```bash
# View run status
orchestrator run status

# Tail run log
orchestrator run log --lines 50

# Check generated code
cat .work/generated/data_analyst_*.py

# Check execution logs
cat .work/logs/data_analyst_*.out
cat .work/logs/data_analyst_*.err
```

### 3. Reviewing Artifacts

Generated artifacts are written to:
- `data/processed/` - Processed datasets, model predictions
- `reports/` - HTML reports, plots (PNG), summary tables
- `artifacts/` - Additional outputs

```bash
# List all artifacts
ls -lhR reports/ data/processed/ artifacts/

# View HTML reports
open reports/report.html

# View plots
open reports/distribution_revenue.png
```

## Artifact Paths

The code executor expects artifacts at specific paths:

| Type | Path | Example |
|------|------|---------|
| Processed data | `data/processed/` | `data/processed/clean_sales.csv` |
| Reports | `reports/` | `reports/analysis_report.html` |
| Plots | `reports/` | `reports/distribution_age.png` |
| Models | `models/` | `models/prophet_model.pkl` |
| Predictions | `data/processed/` | `data/processed/predictions.csv` |

## Available MCP APIs

### Data Loading (`orchestrator.mcp.data`)

```python
from orchestrator.mcp.data import load_csv, load_sql, validate_schema

# Load CSV with optional dtype specification
df = load_csv("data/raw/sales.csv", dtype={"id": str, "amount": float})

# Load from SQL database (requires connection string in env)
df = load_sql("SELECT * FROM customers LIMIT 1000")

# Validate DataFrame schema
result = validate_schema(df, expected_columns=["id", "name", "email"])
```

### Analytics (`orchestrator.mcp.analytics`)

```python
from orchestrator.mcp.analytics import describe_data, detect_drift

# Generate descriptive statistics
stats = describe_data(df, columns=["revenue", "quantity"])

# Detect data drift between reference and current
drift = detect_drift(ref_df, current_df, threshold=0.1)
```

### Modeling (`orchestrator.mcp.models`)

```python
from orchestrator.mcp.models import train_prophet, evaluate_model

# Train Prophet time-series model
result = train_prophet(df, date_column="date", value_column="sales")

# Evaluate model performance
metrics = evaluate_model(y_true, y_pred, task_type="regression")
```

### Visualization (`orchestrator.mcp.viz`)

```python
from orchestrator.mcp.viz import plot_distribution, generate_report

# Plot distribution histogram
plot_path = plot_distribution(df, "revenue", bins=30)

# Generate HTML report from markdown
report_path = generate_report(
    content=markdown_text,
    title="Q4 Analysis",
    metadata={"author": "Data Agent", "date": "2025-11-14"}
)
```

## Debugging Tips

### Check Generated Code

If execution fails, inspect the generated code:

```bash
# Find most recent generated code
ls -lt .work/generated/ | head -5

# View code
cat .work/generated/data_analyst_1731617845.py
```

### Check Execution Logs

```bash
# View stdout
cat .work/logs/data_analyst_1731617845.out

# View stderr (errors)
cat .work/logs/data_analyst_1731617845.err
```

### Check Safety Violations

If code fails safety checks, you'll see:

```
Code safety validation failed: import os, Dangerous function call: eval(
```

**Fix**: Ensure generated code uses only allowed imports and safe functions.

### Check Timeout

If execution times out:

```
Execution timed out after 120 seconds
```

**Fix**: Increase timeout in code executor or optimize generated code.

## Security Model

### Allowed Imports

**Standard library (safe subset)**:
- `json`, `csv`, `pathlib`, `typing`, `math`, `statistics`
- `datetime`, `collections`, `itertools`, `functools`, `re`, `pickle`

**Third-party (data science)**:
- `pandas`, `numpy`, `matplotlib`, `sklearn`, `scipy`

**MCP APIs**:
- `orchestrator.mcp.*` (all modules)

### Blocked Imports

- `os`, `subprocess` - System command execution
- `socket`, `requests`, `urllib` - Network access
- `eval`, `exec`, `compile`, `__import__` - Code injection

### Resource Limits

- **Timeout**: 120 seconds (default, configurable)
- **CPU time**: 120 seconds (POSIX only)
- **Memory**: 1GB (POSIX only)
- **Network**: Blocked (socket module patched)

## Migration from Legacy Mode

**Step 1**: Run existing workflow in legacy mode (baseline)

```bash
orchestrator run start --mode legacy --intake myproject.yaml
orchestrator run next
```

**Step 2**: Run same workflow in code mode (test)

```bash
orchestrator run abort  # Stop legacy run
orchestrator run start --mode code --intake myproject.yaml
orchestrator run next
```

**Step 3**: Compare results

```bash
diff reports/legacy_report.html reports/code_report.html
```

**Step 4**: Adopt code mode for production

Update intake YAML or use `--mode code` by default.

## Troubleshooting

### Error: "pandas is required for load_csv"

**Solution**: Install dependencies

```bash
pip install pandas numpy matplotlib
```

### Error: "Code safety validation failed: import subprocess"

**Solution**: Remove disallowed imports from generated code. Use MCP APIs instead.

### Error: "Execution timed out after 120 seconds"

**Solution**: Increase timeout

```python
# In custom executor
executor.execute(agent, task, context, max_seconds=300)
```

### Warning: "resource module not available"

**Platform**: Windows

**Impact**: CPU and memory limits cannot be enforced

**Solution**: Acceptable for development. For production, use Linux/macOS or Docker.

## Examples

### Example 1: Load CSV and Generate Report

**Task**: "Load sales.csv, describe the data, and generate an HTML report"

**Generated Code**:
```python
from orchestrator.mcp.data import load_csv
from orchestrator.mcp.analytics import describe_data
from orchestrator.mcp.viz import generate_report
import json

df = load_csv("data/raw/sales.csv")
stats = describe_data(df)

markdown = f"""
# Sales Data Analysis

## Summary
- Rows: {stats['row_count']}
- Columns: {stats['column_count']}

## Numeric Columns
{', '.join(stats['numeric_columns'])}
"""

report_path = generate_report(markdown, title="Sales Analysis")
print(json.dumps({"report": report_path}))
```

### Example 2: Detect Data Drift

**Task**: "Compare current_sales.csv with reference_sales.csv for drift"

**Generated Code**:
```python
from orchestrator.mcp.data import load_csv
from orchestrator.mcp.analytics import detect_drift
import json

ref_df = load_csv("data/raw/reference_sales.csv")
cur_df = load_csv("data/raw/current_sales.csv")

drift = detect_drift(ref_df, cur_df, threshold=0.1)

print(json.dumps({
    "overall_drift": drift["overall_drift"],
    "drifted_columns": [k for k, v in drift["column_drift"].items() if v["drifted"]]
}))
```

## See Also

- [ADR-004: MCP Code Execution Pattern](../adr/004-mcp-code-execution.md)
- [Sandbox Self-Test](../../scripts/ops/sandbox_selftest.sh)
- [MCP API Reference](../../src/orchestrator/mcp/README.md) (TODO)
