# Model Registry & Dataset Catalog

**Version:** 1.0.0
**Last Updated:** 2025-10-15

Production-ready registry for ML models and datasets with versioning, integrity verification, and release integration.

---

## Overview

The Model Registry and Dataset Catalog provide centralized artifact management for the Kearney Data Platform:

- **Version control** for models and datasets
- **SHA256 integrity** verification
- **Metrics and metadata** linkage
- **Release tagging** for audit trails
- **Client scoping** for multi-tenant deployments
- **CLI and API** interfaces

All entries are versioned using semantic versioning (e.g., `1.0.0`) and linked to orchestrator runs via release tags.

---

## Quick Start

### Publishing a Model

```bash
# Publish model with metrics
orchestrator registry model-publish \
  --path models/forecast_v1.pkl \
  --version 1.0.0 \
  --metrics models/forecast_v1_metrics.json \
  --client acme-corp \
  --cleanliness 93 \
  --release v1.0.0 \
  --notes "Initial production model"
```

### Registering a Dataset

```bash
# Register dataset with row count
orchestrator registry dataset-register \
  --path data/processed/sales.parquet \
  --version 1.0.0 \
  --rows 3200000 \
  --client acme-corp \
  --cleanliness 95 \
  --notes "Q4 2024 sales data"
```

### Listing Entries

```bash
# List all models
orchestrator registry list --type model

# List models for specific client
orchestrator registry list --type model --client acme-corp

# List datasets
orchestrator registry list --type dataset
```

### Fetching Metadata

```bash
# Get latest version
orchestrator registry fetch --name forecast_v1 --type model

# Get specific version
orchestrator registry fetch --name forecast_v1 --version 1.0.0 --type model
```

### Verifying Integrity

```bash
# Verify all artifacts and hashes
orchestrator registry verify
```

---

## CLI Reference

### `orchestrator registry model-publish`

Publish a model to the registry.

**Options:**
- `--path` (required): Path to model artifact
- `--version` (required): Semantic version (e.g., 1.0.0)
- `--name` (optional): Model name (defaults to filename)
- `--metrics` (optional): Path to metrics JSON file
- `--client` (optional): Client slug
- `--cleanliness` (optional): Cleanliness score (0-100)
- `--release` (optional): Release tag (e.g., v1.0.0)
- `--notes` (optional): Release notes

**Example:**
```bash
orchestrator registry model-publish \
  --path models/forecast_v1.pkl \
  --version 1.0.0 \
  --metrics models/metrics.json \
  --client acme-corp
```

**Output:**
```
Publishing model: forecast_v1 v1.0.0
Artifact: models/forecast_v1.pkl
✓ Model published successfully
ID: 550e8400-e29b-41d4-a716-446655440000
SHA256: a1b2c3d4e5f6...

Metrics:
  rmse: 0.12
  r2: 0.89
```

### `orchestrator registry dataset-register`

Register a dataset in the catalog.

**Options:**
- `--path` (required): Path to dataset file
- `--version` (required): Semantic version
- `--rows` (required): Number of rows
- `--name` (optional): Dataset name
- `--client` (optional): Client slug
- `--cleanliness` (optional): Cleanliness score
- `--release` (optional): Release tag
- `--notes` (optional): Description

**Example:**
```bash
orchestrator registry dataset-register \
  --path data/processed/sales.parquet \
  --version 1.0.0 \
  --rows 3200000 \
  --client acme-corp
```

### `orchestrator registry fetch`

Fetch model or dataset metadata.

**Options:**
- `--name` (required): Entry name
- `--type` (required): `model` or `dataset`
- `--version` (optional): Version (latest if omitted)

**Example:**
```bash
orchestrator registry fetch --name forecast_v1 --type model
```

**Output:**
```
Model: forecast_v1 v1.0.0
ID: 550e8400-e29b-41d4-a716-446655440000
Created: 2025-10-15T14:30:00Z
SHA256: a1b2c3d4e5f6789...

Artifacts:
  models/forecast_v1.pkl (exists)

Metrics:
  rmse: 0.12
  r2: 0.89

Cleanliness Score: 93/100
Release: v1.0.0
Client: acme-corp
```

### `orchestrator registry list`

List models or datasets with filters.

**Options:**
- `--type` (required): `model` or `dataset`
- `--client` (optional): Filter by client
- `--release` (optional): Filter by release tag

**Example:**
```bash
orchestrator registry list --type model --client acme-corp
```

**Output:**
```
┏━━━━━━━━━━━━━━┳━━━━━━━━━┳━━━━━━━━━━━┳━━━━━━━━━━━━┳━━━━━━━━━━┳━━━━━━━━━━┓
┃ Name         ┃ Version ┃ Client    ┃ Cleanliness┃ Release  ┃ Created  ┃
┡━━━━━━━━━━━━━━╇━━━━━━━━━╇━━━━━━━━━━━╇━━━━━━━━━━━━╇━━━━━━━━━━╇━━━━━━━━━━┩
│ forecast_v1  │ 1.0.0   │ acme-corp │      93/100│ v1.0.0   │2025-10-15│
│ forecast_v1  │ 2.0.0   │ acme-corp │      95/100│ v1.1.0   │2025-10-20│
└──────────────┴─────────┴───────────┴────────────┴──────────┴──────────┘
```

### `orchestrator registry verify`

Verify integrity of registry and catalog.

**Checks:**
- All artifact files exist
- SHA256 hashes match
- Manifest file sizes < 10 MB

**Example:**
```bash
orchestrator registry verify
```

**Output:**
```
Verifying registry integrity...
Models checked: 5
Datasets checked: 3

✓ All integrity checks passed
```

### `orchestrator registry stats`

Show aggregate statistics.

**Example:**
```bash
orchestrator registry stats
```

**Output:**
```
Registry Statistics

Total Models: 5
Total Datasets: 3
Avg Model Cleanliness: 93.4/100
Avg Dataset Cleanliness: 95.0/100

Models by Client:
  acme-corp: 3
  other-corp: 2

Datasets by Client:
  acme-corp: 2
  other-corp: 1
```

---

## API Reference

All endpoints are prefixed with `/api/registry`.

### GET `/api/registry/models`

List all models with optional filters.

**Query Parameters:**
- `client` (optional): Filter by client slug
- `release` (optional): Filter by release tag

**Response:**
```json
{
  "count": 2,
  "models": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "name": "forecast_v1",
      "version": "1.0.0",
      "type": "model",
      "created_at": "2025-10-15T14:30:00Z",
      "sha256": "a1b2c3d4e5f6...",
      "metrics": {"rmse": 0.12, "r2": 0.89},
      "artifacts": ["models/forecast_v1.pkl"],
      "cleanliness_score": 93,
      "release_tag": "v1.0.0",
      "client": "acme-corp",
      "notes": "Initial production model"
    }
  ]
}
```

### GET `/api/registry/models/{name}`

Get model metadata by name.

**Query Parameters:**
- `version` (optional): Version (latest if omitted)

**Response:** Single model object (see above)

### POST `/api/registry/models`

Publish a new model.

**Headers:**
- `X-API-Key`: Registry API key (required)

**Body:**
```json
{
  "name": "forecast_v1",
  "version": "1.0.0",
  "artifacts": ["models/forecast_v1.pkl"],
  "metrics": {"rmse": 0.12, "r2": 0.89},
  "client": "acme-corp",
  "notes": "Initial model"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Model published: forecast_v1 v1.0.0",
  "model": { ... }
}
```

### GET `/api/registry/datasets`

List all datasets (similar to models).

### POST `/api/registry/datasets`

Register a new dataset.

**Body:**
```json
{
  "name": "sales_data",
  "version": "1.0.0",
  "artifacts": ["data/processed/sales.parquet"],
  "row_count": 3200000,
  "client": "acme-corp",
  "notes": "Q4 2024 sales"
}
```

### GET `/api/registry/metrics`

Get aggregate statistics.

**Response:**
```json
{
  "models_total": 5,
  "datasets_total": 3,
  "models_by_client": {
    "acme-corp": 3
  },
  "datasets_by_client": {
    "acme-corp": 2
  },
  "avg_model_cleanliness": 93.4,
  "avg_dataset_cleanliness": 95.0
}
```

### POST `/api/registry/verify`

Verify integrity (requires API key).

**Response:**
```json
{
  "valid": true,
  "errors": [],
  "warnings": [],
  "models_checked": 5,
  "datasets_checked": 3
}
```

---

## Manifest Structure

### Model Registry (`models/registry/releases.json`)

```json
{
  "$schema": "https://json-schema.org/draft-07/schema#",
  "version": "1.0.0",
  "updated_at": "2025-10-15T14:30:00Z",
  "models": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "name": "forecast_v1",
      "version": "1.0.0",
      "type": "model",
      "created_at": "2025-10-15T14:30:00Z",
      "sha256": "a1b2c3d4e5f6789...",
      "metrics": {"rmse": 0.12, "r2": 0.89},
      "artifacts": ["models/forecast_v1.pkl"],
      "cleanliness_score": 93,
      "release_tag": "v1.0.0",
      "client": "acme-corp",
      "notes": "Initial production model"
    }
  ]
}
```

### Dataset Catalog (`datasets/catalog.json`)

```json
{
  "$schema": "https://json-schema.org/draft-07/schema#",
  "version": "1.0.0",
  "updated_at": "2025-10-15T14:30:00Z",
  "datasets": [
    {
      "id": "660e9500-f39c-51e5-b827-557766551111",
      "name": "sales_data",
      "version": "1.0.0",
      "type": "dataset",
      "created_at": "2025-10-15T15:00:00Z",
      "sha256": "b2c3d4e5f6g7...",
      "row_count": 3200000,
      "schema_hash": "c3d4e5f6g7h8...",
      "artifacts": ["data/processed/sales.parquet"],
      "cleanliness_score": 95,
      "release_tag": "v1.0.0",
      "client": "acme-corp",
      "notes": "Q4 2024 sales dataset"
    }
  ]
}
```

---

## Integration with Releases

The registry is integrated with GitHub releases via `.github/workflows/release.yml`.

### On Release Creation

When a version tag (e.g., `v1.0.0`) is pushed:

1. **Verify Integrity**: Runs `orchestrator registry verify`
2. **Run Tests**: Executes all registry tests
3. **Count Entries**: Adds model/dataset counts to release notes
4. **Upload Manifests**: Attaches `releases.json` and `catalog.json` as release assets
5. **Steward Hygiene**: Verifies manifest sizes < 10 MB and no dangling paths

### Release Notes Format

```markdown
## Release Summary

**Models:** 5
**Datasets:** 3

### Artifacts
- Model Registry: `models/registry/releases.json`
- Dataset Catalog: `datasets/catalog.json`

Generated with Claude Code
```

---

## Governance

### Audit Trail

Every model and dataset entry includes:
- **Unique ID**: UUID for tracking
- **Creation timestamp**: ISO8601 format
- **SHA256 hash**: Immutable artifact fingerprint
- **Release tag**: Links to specific release (e.g., v1.0.0)
- **Client**: Multi-tenant scoping
- **Cleanliness score**: Data quality metric (0-100)

### Integrity Verification

Run `orchestrator registry verify` to ensure:
- All artifacts exist on disk
- SHA256 hashes match current file contents
- Manifest files are under size limits
- No orphaned or missing references

**Best Practice:** Run verification:
- Before each release
- Weekly via CI schedule
- After bulk model/dataset updates

### Multi-Tenant Isolation

Filter by client for isolated views:

```bash
# View only acme-corp models
orchestrator registry list --type model --client acme-corp

# Fetch acme-corp dataset
GET /api/registry/datasets/sales_data?client=acme-corp
```

---

## Examples

### Example 1: Full Model Lifecycle

```bash
# 1. Publish model after training
orchestrator registry model-publish \
  --path models/churn_predictor.pkl \
  --version 1.0.0 \
  --metrics models/churn_metrics.json \
  --client acme-corp \
  --cleanliness 92 \
  --release v1.0.0 \
  --notes "Initial churn prediction model"

# 2. Verify it was added
orchestrator registry fetch --name churn_predictor --type model

# 3. List all models for client
orchestrator registry list --type model --client acme-corp

# 4. Publish new version
orchestrator registry model-publish \
  --path models/churn_predictor_v2.pkl \
  --name churn_predictor \
  --version 2.0.0 \
  --metrics models/churn_metrics_v2.json \
  --client acme-corp \
  --cleanliness 94 \
  --release v1.1.0 \
  --notes "Improved feature engineering"

# 5. Fetch latest (gets v2.0.0)
orchestrator registry fetch --name churn_predictor --type model
```

### Example 2: Dataset Registration

```bash
# Register raw dataset
orchestrator registry dataset-register \
  --path data/raw/transactions_2024.parquet \
  --version 1.0.0 \
  --rows 5000000 \
  --client acme-corp \
  --cleanliness 87 \
  --notes "Raw transaction data Q1-Q4 2024"

# Register processed dataset
orchestrator registry dataset-register \
  --path data/processed/transactions_clean.parquet \
  --version 1.0.0 \
  --rows 4950000 \
  --client acme-corp \
  --cleanliness 98 \
  --notes "Cleaned and validated transactions"
```

### Example 3: API Usage (Python)

```python
import requests

API_BASE = "http://localhost:8000/api/registry"
API_KEY = "kearney-registry-key"

# List models for client
response = requests.get(
    f"{API_BASE}/models",
    params={"client": "acme-corp"}
)
models = response.json()["models"]

# Get latest model
response = requests.get(f"{API_BASE}/models/forecast_v1")
model = response.json()

# Publish new model
payload = {
    "name": "new_model",
    "version": "1.0.0",
    "artifacts": ["models/new_model.pkl"],
    "metrics": {"accuracy": 0.95},
    "client": "acme-corp"
}

response = requests.post(
    f"{API_BASE}/models",
    json=payload,
    headers={"X-API-Key": API_KEY}
)
```

---

## Troubleshooting

### Issue: "Model already exists"

**Cause:** Trying to publish duplicate name+version.

**Solution:** Increment version number:
```bash
# Instead of 1.0.0, use 1.0.1 or 2.0.0
orchestrator registry model-publish \
  --path models/forecast.pkl \
  --version 1.0.1
```

### Issue: "Artifact not found"

**Cause:** File path doesn't exist relative to project root.

**Solution:** Verify path is correct:
```bash
ls models/forecast_v1.pkl

# Or use absolute path
orchestrator registry model-publish \
  --path /full/path/to/model.pkl \
  --version 1.0.0
```

### Issue: "Hash mismatch detected"

**Cause:** Artifact file was modified after publishing.

**Solution:** Re-publish with new version:
```bash
orchestrator registry model-publish \
  --path models/forecast_v1.pkl \
  --version 1.0.1 \
  --notes "Updated model file"
```

### Issue: "Manifest exceeds 10 MB"

**Cause:** Too many entries in registry/catalog.

**Solution:** Archive old entries or split by client:
```bash
# Move old entries to archive
mv models/registry/releases.json models/registry/releases_archive_2024.json

# Start fresh manifest
orchestrator registry list --type model  # Creates new manifest
```

---

## Resources

- [Design System](design_system.md)
- [CI Workflow](../.github/workflows/ci.yml)
- [Release Workflow](../.github/workflows/release.yml)
- [Python Registry Manager](../src/registry/manager.py)
- [Pydantic Schemas](../src/registry/schemas.py)
- [FastAPI Routes](../src/server/registry_routes.py)

---

**Version:** 1.0.0
**Last Updated:** 2025-10-15
**Maintained by:** Kearney Data Platform Team
