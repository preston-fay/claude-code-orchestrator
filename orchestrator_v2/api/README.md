# API

REST API surface for Orchestrator v2.

## Purpose

Provides HTTP endpoints for:
- Project management (create, read, delete)
- Workflow execution (advance phases)
- RSG stage control
- User management and provider settings
- Events and checkpoints

## Key Components

- **server.py**: FastAPI application and route handlers
- **dto.py**: Data Transfer Objects for API communication

## Main Endpoints

### Health
- `GET /health` - Health check

### Projects
- `GET /projects` - List all projects
- `POST /projects` - Create new project
- `GET /projects/{id}` - Get project details
- `GET /projects/{id}/status` - Get workflow status
- `POST /projects/{id}/advance` - Advance to next phase
- `GET /projects/{id}/events` - Get execution events
- `GET /projects/{id}/checkpoints` - Get checkpoints
- `DELETE /projects/{id}` - Delete project

### Users
- `GET /users/me` - Get current user profile
- `POST /users/me/provider-settings` - Update LLM provider
- `POST /users/me/provider-test` - Test provider connection

### RSG
- `POST /rsg/{id}/ready/start` - Start Ready stage
- `GET /rsg/{id}/ready/status` - Get Ready status
- (Similar for Set and Go stages)
- `GET /rsg/{id}/overview` - Get RSG overview

## Running the Server

```bash
python scripts/dev/run_api_server.py
# or
uvicorn orchestrator_v2.api.server:app --reload
```

## Related Documentation

- ORCHESTRATOR_QUICK_REFERENCE.md
- DEPLOYMENT_APP_RUNNER.md
