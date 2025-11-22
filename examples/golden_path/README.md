# Golden Path - Customer Demand Forecasting

This is the canonical example project for demonstrating Ready-Set-Code end-to-end orchestration.

## What's Included

```
golden_path/
├── README.md                              # This file
├── intake_analytics_forecasting.yaml      # Project intake configuration
└── data/
    └── raw/
        └── demand_history.csv             # Sample demand data
```

## Project Overview

**Scenario**: A retail analytics project that forecasts weekly product demand by region and produces an executive KPI dashboard specification.

**Phases**:
1. **Planning** - Define scope, success metrics, and approach
2. **Architecture** - Design data pipeline and model architecture
3. **Data** - Build ETL pipeline and train forecasting model
4. **Development** - Implement dashboard specification
5. **QA** - Validate model accuracy and test coverage
6. **Documentation** - Generate comprehensive handoff docs

## Quick Start

### Prerequisites

1. API server running: `python scripts/dev/run_api_server.py`
2. UI running: `cd rsg-ui && npm run dev`
3. LLM provider configured (Anthropic API key or Bedrock)

### Run the Demo

```bash
python scripts/dev/run_golden_path_demo.py
```

This will:
1. Create a new project via the API
2. Run Ready → Set → Go stages
3. Print the final RSG overview

### View in UI

1. Open http://localhost:5173
2. Find "Golden Path - Customer Demand Forecast" in the project list
3. Click to see phase details and Run Activity

## Adapting for Your Project

1. **Copy this folder**:
   ```bash
   cp -r examples/golden_path examples/my_client_project
   ```

2. **Edit intake YAML**:
   - Change `project.name` and `project.id`
   - Update `goals` and `success_metrics`
   - Replace `data.sources` with your data
   - Adjust `governance` settings for client

3. **Replace sample data**:
   - Add your data files to `data/raw/`
   - Update paths in intake YAML

4. **Run with modified script**:
   ```python
   # In run_golden_path_demo.py, change:
   INTAKE_PATH = "examples/my_client_project/intake_my_project.yaml"
   PROJECT_NAME = "My Client Project"
   ```

## Data Dictionary

### demand_history.csv

| Column | Type | Description |
|--------|------|-------------|
| week_date | date | Start of week (Monday) |
| product_category | string | Product category (Electronics, Apparel, Home) |
| region | string | Geographic region (Northeast, Southeast, Midwest, West) |
| units_sold | int | Number of units sold |
| revenue_usd | float | Revenue in USD |

## Expected Outputs

After a successful run, the project should produce:

- **Architecture**: ADR documenting pipeline design
- **Data**: Trained model in `models/demand_forecast.pkl`
- **Metrics**: Model evaluation in `models/metrics.json`
- **Dashboard**: Specification in `docs/dashboard_spec.md`
- **Documentation**: Complete project handoff docs

## Troubleshooting

**"API not reachable"**
- Ensure `python scripts/dev/run_api_server.py` is running

**"LLM provider error"**
- Check Settings in UI → LLM Access
- Verify API key is set and test connection works

**"Phase failed"**
- Check Run Activity panel for error details
- Review governance gates in intake YAML

## Related Documentation

- [Golden Path Guide](../../docs/GOLDEN_PATH.md) - Complete walkthrough
- [LLM Providers](../../docs/LLM_PROVIDERS.md) - Provider setup
- [Quick Reference](../../ORCHESTRATOR_QUICK_REFERENCE.md) - API endpoints
