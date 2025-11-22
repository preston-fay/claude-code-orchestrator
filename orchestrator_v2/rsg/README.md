# RSG (Ready-Set-Go)

Ready-Set-Go abstraction layer for Orchestrator v2.

## Purpose

Provides a simplified three-stage view of the workflow:
- **Ready**: Planning and architecture (PLANNING + ARCHITECTURE phases)
- **Set**: Data preparation and early development (DATA + early DEVELOPMENT)
- **Go**: Full development, QA, and documentation (DEVELOPMENT + QA + DOCUMENTATION)

## Key Components

- **models.py**: RSG stage status models
- **service.py**: `RsgService` for stage management

## Stage Mapping

```
Ready Stage:
  └── PLANNING phase
  └── ARCHITECTURE phase

Set Stage:
  └── DATA phase
  └── DEVELOPMENT phase (partial)

Go Stage:
  └── DEVELOPMENT phase (remaining)
  └── QA phase
  └── DOCUMENTATION phase
```

## Usage

```python
from orchestrator_v2.rsg.service import RsgService

service = RsgService(
    project_repository=project_repo,
    checkpoint_repository=checkpoint_repo,
    artifact_repository=artifact_repo,
    workspace_manager=workspace_manager
)

# Start Ready stage
status = await service.start_ready(project_id)

# Get overview
overview = await service.get_overview(project_id)
```

## API Endpoints

- `POST /rsg/{project_id}/ready/start`
- `GET /rsg/{project_id}/ready/status`
- `POST /rsg/{project_id}/set/start`
- `GET /rsg/{project_id}/set/status`
- `POST /rsg/{project_id}/go/start`
- `GET /rsg/{project_id}/go/status`
- `GET /rsg/{project_id}/overview`

## Related Documentation

- docs/orchestrator-v2-architecture.md
