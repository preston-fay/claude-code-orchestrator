# Data Checkpoint Artifacts Checklist

This checklist defines what artifacts must be captured at each data pipeline checkpoint.

## Checkpoint: Post-Ingestion

**Trigger:** After raw data is loaded from source

**Required Artifacts:**
- [ ] `data/raw/[dataset].csv` - Raw data file(s)
- [ ] Ingestion log with row count, source, timestamp
- [ ] Data quality summary (completeness, nulls, duplicates)

**Validation Criteria:**
- File exists and is readable
- Row count > 0
- Expected columns present
- No critical data quality failures

---

## Checkpoint: Post-Validation

**Trigger:** After data quality checks complete

**Required Artifacts:**
- [ ] `docs/data_documentation.md` - Updated data dictionary
- [ ] Data quality report (validation results, metrics)
- [ ] List of validation rules applied

**Validation Criteria:**
- All critical validation rules pass
- Quality metrics meet thresholds
- Data dictionary is current

---

## Checkpoint: Post-Transform

**Trigger:** After data transformation and feature engineering

**Required Artifacts:**
- [ ] `data/interim/[dataset]_cleaned.csv` - Cleaned data
- [ ] `data/processed/[dataset]_features.csv` - Feature-engineered data
- [ ] Transformation log (steps applied, parameters)
- [ ] Feature statistics (distributions, correlations)

**Validation Criteria:**
- Interim data has no nulls (unless expected)
- Processed data has expected feature count
- No data leakage (future data in training set)
- Transformations are deterministic and reproducible

---

## Checkpoint: Post-Training

**Trigger:** After model training completes

**Required Artifacts:**
- [ ] `models/[model_name].pkl` - Serialized model
- [ ] `models/[model_name]_metadata.json` - Model metadata
  - Model type and hyperparameters
  - Feature names and count
  - Training data size
  - Training timestamp
  - Random seed used

**Validation Criteria:**
- Model file exists and is loadable
- Model can make predictions
- Metadata is complete and valid
- Training converged (no errors)

---

## Checkpoint: Post-Evaluation

**Trigger:** After model evaluation completes

**Required Artifacts:**
- [ ] `models/metrics.json` - Performance metrics
  - Accuracy, precision, recall, F1 (if classification)
  - RMSE, MAE, R² (if regression)
  - Test set size
  - Confusion matrix (if classification)
- [ ] Evaluation report (optional, for detailed analysis)

**Validation Criteria:**
- Metrics file exists and is valid JSON
- Metrics meet minimum thresholds (if defined)
- No overfitting detected (train vs. test performance reasonable)
- Model performance is reproducible

---

## Full Pipeline Checkpoint

**Trigger:** When complete pipeline has executed successfully

**Required Artifacts:**
- [ ] All artifacts from above checkpoints
- [ ] `docs/data_documentation.md` - Complete data documentation
- [ ] Pipeline execution log
  - Steps executed
  - Execution time per step
  - Total runtime
  - Success/failure status
  - Errors encountered (if any)

**Optional Artifacts (for production):**
- [ ] Model card or model documentation
- [ ] Data provenance and lineage
- [ ] Experiment tracking metadata (MLflow, Weights & Biases, etc.)
- [ ] Model performance dashboard or report

**Handoff Package to Developer Agent:**
- `models/[model_name].pkl` - Trained model for integration
- `models/[model_name]_metadata.json` - Model metadata
- `models/metrics.json` - Performance metrics
- `docs/data_documentation.md` - Data and model documentation
- `data/processed/[dataset]_features.csv` - Sample processed data for testing

---

## Notes

- All checkpoints should be versioned (timestamp or version number)
- Sensitive data must never be in checkpoints committed to Git
- Large files (models, data) use `.gitignore` and external storage (S3, DVC, etc.)
- Metadata files should be small and can be committed to Git
- Failed checkpoints should log errors and allow for debugging/retry
