# RSC Phase Diagnostics

Phase diagnostics provide visibility into what happened during phase execution, including agents, skills, artifacts, and resource usage.

## Overview

When a phase runs, RSC captures:
- Which agents executed
- Which skills were invoked
- What artifacts were produced
- Token usage
- Governance results
- Timing information

## Storage

Diagnostics are stored per-phase in the workspace:

```
{workspace}/.diagnostics/
├── planning.json
├── architecture.json
├── data.json
├── development.json
├── qa.json
└── documentation.json
```

## Schema

```json
{
  "phase": "data",
  "agents": ["data_agent"],
  "skills": ["data_profiling", "schema_generation"],
  "artifacts": ["data_overview.md", "schema.json", "profile_report.md"],
  "governance": {
    "passed": true
  },
  "token_usage": {
    "input": 1500,
    "output": 2000,
    "total": 3500
  },
  "timestamp": "2025-11-23T10:30:00.000Z",
  "errors": []
}
```

## Accessing Diagnostics

### Via Console Command

```bash
/diagnose-phase data
```

Returns formatted diagnostics:

```
**Diagnostics for data phase:**

**Agents:** data_agent
**Skills:** data_profiling, schema_generation
**Artifacts:** data_overview.md, schema.json, profile_report.md

**Token Usage:**
- Input: 1500
- Output: 2000
- Total: 3500

**Governance:** Passed

**Timestamp:** 2025-11-23T10:30:00.000Z
```

### Via API

```bash
GET /projects/{project_id}/diagnostics/{phase}
```

Response:

```json
{
  "phase": "data",
  "agents": ["data_agent"],
  "skills": ["data_profiling", "schema_generation"],
  "artifacts": ["data_overview.md", "schema.json", "profile_report.md"],
  "governance": {"passed": true},
  "token_usage": {"input": 1500, "output": 2000, "total": 3500},
  "timestamp": "2025-11-23T10:30:00.000Z",
  "errors": []
}
```

### Via UI

The Project Detail page includes a Phase Diagnostics panel that displays:

1. **Agents** - List of agents that executed
2. **Skills** - Skills invoked during execution
3. **Artifacts** - Files created
4. **Token Usage** - Input/output token counts
5. **Governance** - Pass/fail status

## Fields

| Field | Description |
|-------|-------------|
| `phase` | Phase name |
| `agents` | List of agent IDs that ran |
| `skills` | List of skill IDs invoked |
| `artifacts` | List of artifact filenames created |
| `governance` | Object with `passed` boolean |
| `token_usage` | Object with `input`, `output`, `total` |
| `timestamp` | ISO 8601 timestamp of completion |
| `errors` | List of error messages (if any) |

## Use Cases

### Cost Tracking

Track token usage across phases to understand LLM costs:

```python
total_tokens = sum(
    diag['token_usage']['total']
    for phase in ['planning', 'data', 'development', 'qa', 'documentation']
    if (diag := get_diagnostics(project_id, phase))
)
```

### Debugging

When a phase fails or produces unexpected output:

1. Check `errors` list for error messages
2. Review `agents` to see what ran
3. Check `artifacts` to see what was created
4. Compare `token_usage` with expected values

### Audit Trail

Diagnostics provide an audit trail of:
- What agents participated
- What skills were used
- When phases completed
- Whether governance passed

## Empty Diagnostics

If a phase hasn't been run, the API returns empty diagnostics:

```json
{
  "phase": "development",
  "agents": [],
  "skills": [],
  "artifacts": [],
  "governance": {},
  "token_usage": {},
  "timestamp": null,
  "errors": []
}
```

## Integration with Artifacts

Diagnostics complement the artifacts system:

- **Artifacts**: The actual files produced (PRD.md, schema.json)
- **Diagnostics**: Metadata about how they were produced (which agent, which skills)

Use `/artifacts phase=X` to list files, then `/diagnose-phase X` to understand how they were created.

## Future Enhancements

Planned improvements to diagnostics:

- Per-agent token breakdown
- Skill execution timing
- Governance rule details
- Historical diagnostics (not just latest)
- Cost estimation in USD
