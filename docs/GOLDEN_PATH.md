# Golden Path Guide

This guide walks you through running your first project end-to-end using Ready-Set-Code.

## What is the Golden Path?

The Golden Path is a canonical example project that demonstrates the full orchestration flow:

- **Project**: Customer Demand Forecasting
- **Domain**: Retail analytics
- **Flow**: Ready → Set → Go stages
- **Output**: Forecasting pipeline + KPI dashboard spec

It's designed to be:
- Run immediately without configuration
- Adapted as a template for real projects
- A reference for how phases and agents work together

## Prerequisites

Before running the Golden Path demo, ensure you have:

### 1. LLM Provider Configured

You need either:
- **Anthropic API key** (BYOK) - Set via UI Settings
- **AWS Bedrock** configured with IAM credentials

### 2. API Server Running

```bash
python scripts/dev/run_api_server.py
```

The API should be running at http://localhost:8000

### 3. UI Running (Optional but Recommended)

```bash
cd rsg-ui
npm install
npm run dev
```

The UI should be running at http://localhost:5173

## Running the Golden Path Demo

### Step 1: Start the Demo Script

```bash
python scripts/dev/run_golden_path_demo.py
```

This script will:
1. Check API health
2. Create a new project named "Golden Path - Customer Demand Forecast"
3. Run Ready stage (Planning + Architecture phases)
4. Run Set stage (Data phase)
5. Run Go stage (Development + QA + Documentation phases)
6. Display the final RSG overview and recent events

### Step 2: View in UI

1. Open http://localhost:5173
2. Find "Golden Path - Customer Demand Forecast" in the project list
3. Click to view project details

### Step 3: Explore the Results

In the project detail view, you'll see:
- **RSG Status Cards**: Visual status of Ready/Set/Go
- **Phase List**: Status of each individual phase
- **Run Activity**: Real-time event log showing execution flow
- **Checkpoints**: Saved state at each phase transition

## What Happens During Each Stage

### Ready Stage

**Phases**: Planning, Architecture

The orchestrator:
1. Analyzes the intake YAML
2. Generates a project plan
3. Creates architecture documentation
4. Produces ADRs for key decisions

### Set Stage

**Phases**: Data

The orchestrator:
1. Designs the data pipeline
2. Creates ETL scripts (stubbed)
3. Defines model training approach
4. Saves checkpoint with data artifacts

### Go Stage

**Phases**: Development, QA, Documentation

The orchestrator:
1. Implements remaining code
2. Runs tests and validation
3. Generates project documentation
4. Produces final deliverables

## Adapting for Your Project

The Golden Path is designed to be copied and customized.

### Step 1: Copy the Template

```bash
cp -r examples/golden_path examples/my_project
```

### Step 2: Edit the Intake YAML

Open `examples/my_project/intake_analytics_forecasting.yaml` and update:

```yaml
project:
  id: "my-client-project"
  name: "Client Name - Project Type"
  type: "analytics_forecasting"
  domain: "your_domain"

goals:
  primary:
    - "Your specific goal 1"
    - "Your specific goal 2"

data:
  sources:
    - name: "your_data"
      path: "data/raw/your_data.csv"
```

### Step 3: Add Your Data

Replace the sample CSV with your actual data:

```bash
cp /path/to/your/data.csv examples/my_project/data/raw/
```

### Step 4: Modify the Demo Script

Edit `scripts/dev/run_golden_path_demo.py`:

```python
PROJECT_NAME = "Client Name - Project Type"
# Optionally update metadata to point to your intake file
```

### Step 5: Run Your Project

```bash
python scripts/dev/run_golden_path_demo.py
```

## Intake YAML Reference

Key sections in the intake YAML:

### Project Metadata

```yaml
project:
  id: "unique-project-id"
  name: "Human-Readable Name"
  type: "analytics_forecasting"
  domain: "retail"
```

### Goals

```yaml
goals:
  primary:
    - "Main objective 1"
    - "Main objective 2"
  secondary:
    - "Nice-to-have objective"
```

### Data Sources

```yaml
data:
  sources:
    - name: "data_name"
      path: "data/raw/file.csv"
      format: "csv"
```

### Orchestration Config

```yaml
orchestration:
  enabled_agents:
    - "architect"
    - "data"
    - "developer"
    - "qa"
    - "documentarian"
```

### Governance

```yaml
governance:
  client_profile: "kearney-default"
  quality_gates:
    min_test_coverage: 0.70
```

## Troubleshooting

### "Cannot connect to API"

**Problem**: The demo script can't reach the API server.

**Solution**:
1. Ensure the API is running: `python scripts/dev/run_api_server.py`
2. Check the port: default is 8000
3. Set custom URL: `export ORCHESTRATOR_API_URL=http://localhost:8000`

### "LLM provider error"

**Problem**: Phases fail with LLM-related errors.

**Solution**:
1. Open UI Settings
2. Configure LLM provider (Anthropic or Bedrock)
3. Test connection
4. Re-run the demo

### "Phase failed"

**Problem**: A phase shows as failed in the UI.

**Solution**:
1. Check Run Activity panel for error details
2. Review governance settings in intake YAML
3. Ensure data files exist at specified paths

### "No events showing"

**Problem**: Run Activity panel is empty.

**Solution**:
1. Refresh the page
2. Check that events endpoint is working: `curl http://localhost:8000/projects/{id}/events`
3. Run a phase to generate events

## Best Practices

1. **Start with Golden Path**: Run it first to understand the flow
2. **Iterate on intake**: Update goals and config, re-run
3. **Check events**: The Run Activity panel shows what's happening
4. **Save checkpoints**: Use them to rollback if needed
5. **Customize governance**: Adjust quality gates for your needs

## Related Documentation

- [Orchestrator Quick Reference](../ORCHESTRATOR_QUICK_REFERENCE.md)
- [LLM Providers](LLM_PROVIDERS.md)
- [User Authentication](USER_AUTHENTICATION.md)

## Files Reference

```
examples/golden_path/
├── README.md                              # Template documentation
├── intake_analytics_forecasting.yaml      # Intake configuration
└── data/raw/demand_history.csv            # Sample data

scripts/dev/
└── run_golden_path_demo.py                # Demo runner script
```
