# Territory POC - IA/IL/IN Retail Realignment

A proof-of-concept demonstrating territory realignment using RVS/ROS/RWS scoring for retailers in Iowa, Illinois, and Indiana.

## Important: Workspace Separation

**No client data should be placed in this repo.**

This directory contains only:
- `intake_territory_poc.yaml` - Configuration metadata
- `README.md` - Documentation

All actual data must live in the **workspace**:
```
/home/user/workspaces/territory_poc/
├── data/
│   └── Retailer_Segmentation_CROP.xlsx  ← Place your data here
├── artifacts/
│   ├── retailers_midwest_scored.csv     ← Generated outputs
│   ├── territory_assignments.csv
│   └── territory_kpis.csv
├── logs/
└── tmp/
```

## Setup

### 1. Create Workspace Structure

```bash
mkdir -p /home/user/workspaces/territory_poc/data
mkdir -p /home/user/workspaces/territory_poc/artifacts
mkdir -p /home/user/workspaces/territory_poc/logs
```

### 2. Place Your Data File

Copy the retailer segmentation Excel file to:
```
/home/user/workspaces/territory_poc/data/Retailer_Segmentation_CROP.xlsx
```

### 3. Start the API and UI

```bash
# Terminal 1: Start API
python scripts/dev/run_api_server.py

# Terminal 2: Start UI
cd rsg-ui
npm run dev
```

### 4. Run the POC

**Option A: Via UI**
1. Open http://localhost:5173
2. Click "New Territory Scenario (POC)"
3. Adjust territory count and weights
4. Click "Run Scenario"

**Option B: Via Script**
```bash
# Generate sample data and run pipeline
python scripts/dev/run_territory_poc_demo.py --generate-sample

# Use your own data
python scripts/dev/run_territory_poc_demo.py

# Customize parameters
python scripts/dev/run_territory_poc_demo.py --generate-sample --num-retailers 500
```

## API Endpoints

The Territory POC provides dedicated API endpoints:

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/territory/score` | Run scoring skill (computes RVS/ROS/RWS) |
| POST | `/territory/cluster` | Run clustering skill (assigns territories) |
| GET | `/territory/assignments?workspace_path=...` | Get retailer assignments |
| GET | `/territory/kpis?workspace_path=...` | Get territory KPIs |

### Example API Usage

```bash
# Run scoring
curl -X POST http://localhost:8000/territory/score \
  -H "Content-Type: application/json" \
  -d '{
    "workspace_path": "/home/user/workspaces/territory_poc",
    "intake_config": {
      "territory": {"target_territories": 12, "states": ["IA", "IL", "IN"]},
      "scoring": {"weights": {"value_weight": 0.5, "opportunity_weight": 0.3, "workload_weight": 0.2}}
    }
  }'

# Run clustering (after scoring)
curl -X POST http://localhost:8000/territory/cluster \
  -H "Content-Type: application/json" \
  -d '{
    "workspace_path": "/home/user/workspaces/territory_poc",
    "intake_config": {
      "territory": {"target_territories": 12}
    }
  }'

# Get KPIs
curl "http://localhost:8000/territory/kpis?workspace_path=/home/user/workspaces/territory_poc"
```

## Scoring Methodology

### RVS - Retail Value Score
Current economic contribution based on:
- 3-year average revenue (CY, PY, PPY)
- Normalized to 0-1 scale

### ROS - Retail Opportunity Score
Future growth potential based on:
- Segment classification (Elite > Core > Explorer)
- Normalized to 0-1 scale

### RWS - Retail Workload Score
Rep effort required based on:
- Segment complexity
- Value quantile
- Normalized to 0-1 scale

## Territory Assignment

Retailers are assigned to territories using k-means clustering on:
- Geographic location (ZIP centroid lat/lon)
- Weighted composite score (RVS × w1 + ROS × w2 + RWS × w3)

## Outputs

After running the POC, check the workspace artifacts:

| File | Description |
|------|-------------|
| `retailers_midwest_scored.csv` | All retailers with RVS/ROS/RWS scores |
| `territory_assignments.csv` | Retailer → territory mapping |
| `territory_kpis.csv` | Per-territory KPIs and summary |

## Expected Data Columns

The Excel file should contain these columns (or similar):
- Retailer identifier (GLN, Ship-To ID)
- Name, City, State, ZIP
- Segment classification
- Revenue columns (CY Rev, PY Rev, PPY Rev)

## Troubleshooting

**"File not found" error**
- Verify the Excel file is at `/home/user/workspaces/territory_poc/data/`
- Check file name matches exactly

**No retailers after filtering**
- Confirm your data contains IA, IL, IN states
- Check the state column name in intake YAML

**Clustering fails**
- Ensure there are enough retailers for the target territory count
- Reduce target_territories if needed
