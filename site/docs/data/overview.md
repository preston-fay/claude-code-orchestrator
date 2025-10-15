# Data Documentation

## Overview
This document describes the data architecture, policies, and conventions for the Claude Code Orchestrator project's data and analytics capabilities.

## Folder Structure & Purpose

### `data/`
Central data repository organized by processing stage.

- **`data/raw/`** - Immutable raw data as ingested from source systems
  - Never modify files in this directory
  - Timestamp all ingests (YYYYMMDD format)
  - Not version controlled (`.gitignore`d)

- **`data/interim/`** - Intermediate transformed data
  - Cleaned, validated, but not yet feature-engineered
  - May contain multiple transformation stages
  - Not version controlled

- **`data/processed/`** - Final processed datasets ready for modeling/analysis
  - Feature-engineered, split (train/test/val), ready for consumption
  - Not version controlled (regenerate from pipelines)

- **`data/external/`** - External reference data, lookup tables, sample datasets
  - **`data/external/sample/`** - Small sample datasets for testing
  - Version controlled (non-sensitive data only)

### `notebooks/`
Jupyter notebooks for exploration and analysis.

- Naming convention: `##_descriptive_name.ipynb` (e.g., `01_initial_exploration.ipynb`)
- Use notebooks for exploration, not production pipelines
- Document findings and migrate production code to `src/`

### `analytics/`
SQL queries, dashboard definitions, and analytics artifacts.

- **`analytics/queries/`** - Reusable SQL query templates
- **`analytics/dashboards/`** - Dashboard configurations (JSON/YAML)

### `models/`
Trained model artifacts, metrics, and metadata.

- **`models/registry/`** - Model versioning and registry metadata
- Store serialized models (pickle, joblib, ONNX, etc.)
- Include `metrics.json` with performance metrics
- Not version controlled (use MLflow or DVC for versioning)

### `src/data/`
Data loading, validation, and transformation code.

- `loaders.py` - Data ingestion from various sources
- `transforms.py` - Data transformation functions
- `validators.py` - Data quality and validation logic

### `src/features/`
Feature engineering and feature store code.

- Feature generation functions
- Feature selection logic
- Feature documentation

### `src/models/`
Model training, evaluation, and inference code.

- `train.py` - Training scripts
- `evaluate.py` - Evaluation and metrics
- `predict.py` - Inference/prediction logic

### `src/pipelines/`
End-to-end orchestrated pipelines.

- Pipeline definitions (data → features → train → evaluate)
- Orchestration code (Airflow DAGs, Prefect flows, or custom)
- `registry.py` - Available pipeline catalog

## Update Policy

### Data Refresh Schedule
- **Raw data**: Ingested on-demand or via scheduled jobs
- **Interim/Processed**: Regenerated when raw data updates or transformations change
- **Models**: Retrained on schedule (weekly/monthly) or when performance degrades

### Versioning Strategy
- **Code**: Git version control (all `src/` code)
- **Data**: Not in Git; use DVC (optional) or timestamped directories
- **Models**: MLflow tracking (optional) or manual versioning with timestamps

## Data Retention

- **Raw data**: Retain for audit/reproducibility (30-90 days)
- **Interim data**: Can be deleted after processing (ephemeral)
- **Processed data**: Retain current + 2 previous versions
- **Models**: Retain production model + last 3 versions

## PII & Data Privacy Rules

### Prohibited
- ❌ **Never commit raw PII** to Git (names, emails, SSNs, addresses, etc.)
- ❌ **Never commit credentials** (API keys, passwords, connection strings)
- ❌ **Never store sensitive data unencrypted** in `data/` folders

### Required
- ✅ **Anonymize or pseudonymize PII** before `data/processed/`
- ✅ **Use `.env` for secrets**, never hardcode
- ✅ **Encrypt sensitive data at rest** (if applicable)
- ✅ **Document data sources** and sensitivity classification
- ✅ **Review data samples** before sharing or committing

### Data Sensitivity Classification
- **Public**: Can be shared openly (sample datasets)
- **Internal**: Company/project use only (aggregated metrics)
- **Confidential**: Restricted access (customer data, PII)
- **Restricted**: Requires special approval (compliance-regulated data)

## Naming Conventions

### Files
- Use lowercase with underscores: `feature_engineering.py`
- Date-prefix data files: `YYYYMMDD_dataset_name.csv`
- Version models: `model_v1.0.0.pkl` or `model_20251014.pkl`

### Variables
- Descriptive names: `customer_churn_rate` not `ccr`
- DataFrame suffix: `df` (e.g., `sales_df`, `customers_df`)
- Boolean prefix: `is_`, `has_`, `can_` (e.g., `is_valid`, `has_nulls`)

### Functions
- Verb-first: `load_data()`, `transform_features()`, `validate_schema()`
- Return type hints: `def load_data(path: str) -> pd.DataFrame:`

## Data Quality Standards

### Required Validations
1. **Schema validation**: Column names, types, nullability
2. **Range checks**: Min/max values, outlier detection
3. **Referential integrity**: Foreign key consistency
4. **Completeness**: No unexpected nulls or missing values
5. **Uniqueness**: Primary keys, deduplication

### Quality Metrics to Track
- **Completeness**: % non-null values
- **Validity**: % values passing validation rules
- **Consistency**: % matching cross-field rules
- **Timeliness**: Data freshness (time since last update)
- **Accuracy**: % matching source of truth (when available)

## Pipeline Checkpoints

Data pipelines include checkpoints at key stages:

1. **Post-Ingestion**: Raw data loaded successfully
2. **Post-Validation**: Data quality checks pass
3. **Post-Transform**: Interim data created
4. **Post-Feature Engineering**: Processed data ready
5. **Post-Training**: Model trained and evaluated
6. **Post-Evaluation**: Metrics meet thresholds

Each checkpoint produces:
- Artifact (data file, model file, etc.)
- Metadata (row counts, column stats, execution time)
- Validation results (pass/fail, quality metrics)

See `.claude/checkpoints/DATA-CHECKLIST.md` for checkpoint artifact requirements.

## Getting Started

### Initial Setup
```bash
# Install dependencies
pip install -e .

# Copy environment template
cp .env.example .env

# Run sample pipeline
python -m src.cli ingest
python -m src.cli transform
python -m src.cli train
python -m src.cli evaluate
```

### Running Tests
```bash
# Run all tests
pytest

# Run data tests only
pytest tests/test_data_ingest.py tests/test_transforms.py

# Run with coverage
pytest --cov=src --cov-report=html
```

### Creating a New Pipeline
1. Define pipeline in `src/pipelines/`
2. Register in `src/pipelines/registry.py`
3. Add tests in `tests/`
4. Document in this file
5. Add to orchestrator config (`.claude/config.yaml`)

## Contact & Support

For questions about data architecture, pipelines, or this documentation:
- Review this document and `CLAUDE.md`
- Check `src/` code for implementation details
- Consult the Data Agent (`subagent_prompts/data.md`)

## Changelog

| Date | Change | Author |
|------|--------|--------|
| 2025-10-14 | Initial data documentation created | Orchestrator |
