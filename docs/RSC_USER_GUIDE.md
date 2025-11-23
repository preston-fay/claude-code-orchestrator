# RSC (Ready-Set-Code) User Guide

## Overview

RSC is a generic orchestrator UI and engine for coordinating AI agents through structured workflows. It supports any project type through capability-driven phase derivation.

## Creating a Project

### From the UI

1. Navigate to the Projects list (`/projects`)
2. Click "New Project"
3. Enter:
   - **Project Name**: A descriptive name
   - **Template**: Choose a template (or Blank Project)
   - **Brief** (optional): Describe what you want to build
   - **Client**: Client identifier for governance (default: kearney-default)
4. Click "Create Project"

### Setting Brief & Capabilities

The project **brief** is a free-text description of what you want to build. When the planning phase runs, agents use this brief to generate:
- PRD.md
- architecture.md
- backlog.json

**Capabilities** determine which phases your project needs. Common capabilities:
- `data_pipeline` - Data ingestion and ETL
- `analytics_forecasting` - Time-series forecasting
- `ml_classification` - Machine learning classification
- `optimization` - Operations research
- `app_build` - Application development
- `backend_api` - API development

## Understanding Phases

Phases are derived from capabilities:

| Capability | Phases |
|------------|--------|
| generic | PLANNING → ARCHITECTURE → DEVELOPMENT → QA → DOCUMENTATION |
| data_pipeline | PLANNING → ARCHITECTURE → DATA → QA → DOCUMENTATION |
| analytics_forecasting | PLANNING → ARCHITECTURE → DATA → DEVELOPMENT → QA → DOCUMENTATION |
| app_build | PLANNING → ARCHITECTURE → DEVELOPMENT → QA → DOCUMENTATION |

## Running Phases

### From the UI

1. Open your project detail page
2. In the "Phases" section, click "Run" on the current phase
3. Wait for completion
4. View results in the "Run Activity" panel

### Using the Console

The project console supports slash commands:

```
/run-phase planning      # Run the planning phase
/run-phase architecture  # Run the architecture phase
/plan-phase planning     # Generate planning artifacts
```

## Viewing Artifacts

After running phases, artifacts appear in the "Planning & Architecture Artifacts" section:

- **planning/PRD.md** - Product Requirements Document
- **planning/architecture.md** - Technical architecture
- **planning/backlog.json** - Prioritized backlog

Artifacts are stored in the project workspace at:
```
<workspace_path>/artifacts/<phase>/<artifact>
```

## RSG (Ready/Set/Go) Status

The RSG macro status shows high-level progress:

- **READY** = PLANNING + ARCHITECTURE complete
- **SET** = DATA + early DEVELOPMENT complete
- **GO** = full DEVELOPMENT + QA + DOCUMENTATION complete

## External Links

Projects can track external deliverables:

- **app_repo_url**: Link to the repository for the built application
- **app_url**: Link to the deployed application

These are shown in the project detail page under "External Links".

## API Endpoints

### Projects
- `GET /projects` - List all projects
- `POST /projects` - Create project
- `GET /projects/{id}` - Get project
- `POST /projects/{id}/advance` - Run current phase
- `GET /projects/{id}/artifacts` - Get artifacts
- `POST /projects/{id}/chat` - Console chat

### RSG Status
- `GET /rsg/{id}/overview` - RSG status
- `POST /rsg/{id}/ready/start` - Start Ready stage
- `POST /rsg/{id}/set/start` - Start Set stage
- `POST /rsg/{id}/go/start` - Start Go stage

## Running Locally

### Start the API Server

```bash
cd /home/user/claude-code-orchestrator
python scripts/dev/run_api_server.py
# API runs at http://localhost:8000
```

### Start the UI

```bash
cd rsg-ui
npm install
npm run dev
# UI runs at http://localhost:5173
```

### Create a Test Project

1. Open http://localhost:5173
2. Click "New Project"
3. Select "Analytics - Time Series Forecasting" template
4. Enter a brief: "Build a demand forecasting model for retail sales"
5. Create the project
6. Run the PLANNING phase

## Model Configuration

RSC uses centralized model configuration:

- **Claude Sonnet 4.5** (premium): Default for most tasks
- **Claude Haiku 4.5** (cost-efficient): Fallback for simpler tasks

Configure your API key in Settings.

## Governance

Client governance rules are enforced during phase transitions:
- Test coverage thresholds
- Security scan requirements
- Documentation requirements
- Compliance checks (GDPR, HIPAA, SOC2)

See `clients/<client>/governance.yaml` for client-specific rules.
