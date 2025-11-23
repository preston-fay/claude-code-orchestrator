# RSC Planning Pipeline

## Overview

The RSC Planning Pipeline uses a multi-agent consensus architecture to generate comprehensive planning artifacts from a project brief and capabilities.

## Agents Involved

### 1. Architect Agent
- Receives project brief, capabilities, and domain context
- Generates initial drafts:
  - PRD draft
  - Architecture draft
  - Backlog draft
  - Skills plan draft

### 2. Reviewer Agent
- Critiques Architect's output
- Identifies gaps, risks, and improvements
- Provides constructive feedback

### 3. Consensus Agent
- Merges Architect and Reviewer outputs
- Resolves conflicts
- Creates unified draft set

### 4. Documentarian Agent
- Finalizes drafts into polished documents
- Generates Mermaid diagrams for architecture
- Creates story maps from backlog

### 5. Steward Agent
- Saves artifacts to workspace
- Updates artifact index
- Ensures proper file structure

## Artifacts Generated

### PRD.md (Hybrid Grade)
Executive + engineering focused Product Requirements Document:
- Executive Summary (C-suite friendly)
- Goals and Success Metrics (KPIs)
- Functional Requirements
- Non-Functional Requirements
- User Stories / Flows
- Data Requirements
- Constraints
- Risks and Mitigations
- Timeline Overview

### architecture.md (with D3 Diagrams)
Technical architecture document with Mermaid diagrams:
- System Overview diagram
- Component Architecture
- Data Flow diagram
- Technology Stack
- API Contracts
- Deployment Architecture
- Security Considerations

### feature_backlog.json
Structured JSON array of features:
```json
[
  {
    "id": "feat-1",
    "title": "Feature Title",
    "description": "Feature description",
    "priority": "high",
    "effort_points": 5,
    "dependencies": []
  }
]
```

### feature_story_map.md
Executive-friendly story map:
- High Priority (Must Have)
- Medium Priority (Should Have)
- Low Priority (Nice to Have)

### skills_plan.json
Mapping of capabilities to required skills:
```json
{
  "capabilities": ["data_pipeline", "analytics_forecasting"],
  "required_skills": ["time_series_analytics", "data_validation"]
}
```

## Running the Pipeline

### Via Console Command

```
/plan-phase planning
```

This runs the full multi-agent pipeline and generates all artifacts.

### Via API

```bash
POST /projects/{project_id}/chat
{
  "message": "/plan-phase planning"
}
```

### Viewing Artifacts

```
/artifacts phase=planning
```

Or via API:
```bash
GET /projects/{project_id}/artifacts
```

## Domain Context

The pipeline automatically loads domain-specific context based on project brief:

- **Territory Projects**: If brief mentions "territory", "territory optimizer", or "territory alignment", loads `docs/territory_system_blueprint.md` as context

## Artifact Location

Artifacts are saved to:
```
<workspace_path>/artifacts/planning/
├── PRD.md
├── architecture.md
├── feature_backlog.json
├── feature_story_map.md
└── skills_plan.json
```

## LLM Configuration

- **Primary Model**: Claude Sonnet 4.5 (`claude-sonnet-4-5-20250929`)
- **Fallback Model**: Claude Haiku 4.5 (`claude-haiku-4-5-20251015`)

User BYOK (Bring Your Own Key) is supported via user profile settings.

## Capabilities Influence

The capabilities list influences diagram generation:

| Capability | Architecture Diagrams Added |
|------------|----------------------------|
| `app_build`, `backend_api` | Sequence diagrams, API contracts |
| `data_pipeline`, `analytics_forecasting` | Data flow diagrams |
| `ml_classification`, `ml_regression` | Model architecture diagrams |
| `optimization` | Optimization flow diagrams |

## Error Handling

If any agent fails:
- Pipeline continues with fallback content
- Errors are logged
- User receives notification of partial completion

## Next Steps After Planning

Once planning completes:
1. Review generated artifacts
2. Run architecture phase for detailed design
3. Run development phase for implementation
4. Run QA phase for testing
5. Run documentation phase for final docs
