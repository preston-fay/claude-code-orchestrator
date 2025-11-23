# RSC Agent Execution

This document describes the phase execution system in Ready-Set-Code (RSC).

## Overview

RSC uses a `PhaseExecutionService` to run real agent logic for each phase of the orchestration pipeline. Each phase uses LLM-based agents to generate artifacts tailored to the project's brief and capabilities.

## Supported Phases

### DATA Phase
**Agent**: `data_agent`

Generates data engineering artifacts:
- `data_overview.md` - Data requirements and pipeline overview
- `schema.json` - Data schema with entities, relationships, validation rules
- `profile_report.md` - Data profiling methodology and recommendations

**Prompt Context**:
- Project name and brief
- Capabilities (determines data complexity)

### DEVELOPMENT Phase
**Agent**: `developer_agent`

Generates development artifacts based on capabilities:
- `dev_summary.md` - Components, architecture decisions, implementation approach
- `file_change_log.json` - File operations with timestamps

**Scaffold Detection**:
- React frontend: `app_build`, `frontend_ui`
- FastAPI backend: `app_build`, `backend_api`
- Analytics: `analytics_forecasting`, `analytics_dashboard`
- ML: `ml_classification`, `ml_regression`, `ml_clustering`

### QA Phase
**Agent**: `qa_agent`

Generates quality assurance artifacts:
- `qa_results.json` - Test plan, coverage targets, test types
- `quality_gate_report.md` - Quality criteria, assessment, recommendations

### DOCUMENTATION Phase
**Agent**: `documentarian_agent`

Generates final documentation:
- `system_overview.md` - Project purpose, components, architecture
- `how_to_run.md` - Prerequisites, installation, configuration
- `api_reference.md` - Endpoints, request/response formats
- `release_notes.md` - Version, features, known issues, roadmap

## Usage

### Via Console Commands

```bash
# Run a specific phase
/run-phase data
/run-phase development
/run-phase qa
/run-phase documentation
```

### Via API

```python
POST /projects/{project_id}/chat
{
  "message": "/run-phase data"
}
```

Response:
```json
{
  "reply": "Phase data completed successfully.\n\nSummary: Data phase completed. Generated 3 artifacts.\n\nAgents: data_agent\n\nArtifacts generated:\n- data_overview.md\n- schema.json\n- profile_report.md",
  "model": "claude-sonnet-4-5-20250929",
  "tokens": {"input": 0, "output": 0},
  "agent": "data_agent"
}
```

## Artifact Storage

Artifacts are saved to:
```
{workspace}/artifacts/{phase}/
```

Example:
```
/home/user/.orchestrator/workspaces/proj-123/
  artifacts/
    planning/
      PRD.md
      architecture.md
      feature_backlog.json
    data/
      data_overview.md
      schema.json
      profile_report.md
    development/
      dev_summary.md
      file_change_log.json
    qa/
      qa_results.json
      quality_gate_report.md
    documentation/
      system_overview.md
      how_to_run.md
      api_reference.md
      release_notes.md
```

## LLM Configuration

The execution service uses:
- **Primary Model**: Claude Sonnet 4.5 (`claude-sonnet-4-5-20250929`)
- **Provider Registry**: Supports Anthropic and AWS Bedrock

Model selection follows user preferences set in their profile.

## Error Handling

If a phase fails:
1. Error is logged to the console
2. Empty artifacts list returned
3. Summary includes error message
4. State is not advanced (phase can be retried)

## Integration with Planning

The execution service complements the planning pipeline:

1. **Planning Pipeline**: Generates PRD, architecture, backlog (multi-agent consensus)
2. **Execution Service**: Runs subsequent phases (single-agent per phase)

## Service Architecture

```python
from orchestrator_v2.phases import get_execution_service

# Get singleton instance
service = get_execution_service()

# Execute a phase
result = await service.execute_phase(
    phase=PhaseType.DATA,
    project_state=state,
    user=user_profile
)

# Result structure
{
    "artifacts": ["/path/to/artifact1.md", ...],
    "summary": "Phase completed description",
    "agents": ["agent_name"]
}
```

## Extending Agents

To add new phase logic:

1. Add handler method in `PhaseExecutionService`:
```python
async def _execute_new_phase(
    self,
    project_state: ProjectState,
    context: AgentContext,
) -> dict[str, Any]:
    # Implementation
```

2. Register in `execute_phase()`:
```python
elif phase == PhaseType.NEW_PHASE:
    return await self._execute_new_phase(project_state, context)
```

## Safety Rules

The execution service follows these safety rules:

1. **No Modification of Planning Artifacts**: Execution phases read but don't modify planning outputs
2. **Capability-Aware**: Artifacts are tailored to project capabilities
3. **Workspace Isolation**: Each project has its own artifact directory
4. **User Credentials**: LLM calls use user's BYOK API key

## Related Documentation

- [RSC User Guide](./RSC_USER_GUIDE.md)
- [RSC Planning Pipeline](./RSC_PLANNING_PIPELINE.md)
- [RSC Orchestration Status](./RSC_ORCHESTRATION_STATUS.md)
