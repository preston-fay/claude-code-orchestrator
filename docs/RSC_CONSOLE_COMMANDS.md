# RSC Console Commands

The RSC project console supports slash commands for interacting with your project's orchestration pipeline.

## Command Reference

### Phase Execution

#### `/plan-phase <phase>`
Generate planning artifacts for a phase.

```
/plan-phase planning
```

Runs the multi-agent planning pipeline (Architect → Reviewer → Consensus → Documentarian → Steward) and generates:
- PRD.md
- architecture.md
- feature_backlog.json
- feature_story_map.md
- skills_plan.json

#### `/run-phase <phase>`
Execute a specific phase with LLM-based agents.

```
/run-phase data
/run-phase development
/run-phase qa
/run-phase documentation
```

Each phase generates phase-specific artifacts and saves diagnostics.

**Valid phases:** planning, architecture, data, development, qa, documentation

### Artifacts

#### `/artifacts phase=<phase>`
List artifacts for a specific phase.

```
/artifacts phase=planning
```

Returns list of artifacts with names, sizes, and IDs for viewing.

#### `/open <artifact_id>`
View artifact content and metadata.

```
/open planning_PRD.md
```

Artifact IDs follow the format: `phase_filename`

### Analysis

#### `/next-actions`
Get AI-recommended next steps based on project state.

```
/next-actions
```

Analyzes completed phases, capabilities, and artifacts to suggest concrete next actions.

#### `/summarize-prd`
Get an executive summary of the project's PRD.

```
/summarize-prd
```

Extracts key points: purpose, features, technical approach, success criteria.

#### `/diagnose-phase <phase>`
View diagnostics for a specific phase.

```
/diagnose-phase data
```

Shows:
- Agents invoked
- Skills used
- Artifacts created
- Token usage
- Governance results
- Timestamp

### Other

#### `/help`
Show all available commands with descriptions.

```
/help
```

## API Usage

Commands are sent via the chat endpoint:

```bash
POST /projects/{project_id}/chat
Content-Type: application/json

{
  "message": "/help"
}
```

Response format:

```json
{
  "reply": "...",
  "model": "claude-sonnet-4-5-20250929",
  "tokens": {"input": 0, "output": 0},
  "agent": "console"
}
```

## Command Types

| Command | LLM Required | Artifacts Modified |
|---------|--------------|-------------------|
| /help | No | No |
| /artifacts | No | No |
| /open | No | No |
| /diagnose-phase | No | No |
| /run-phase | Yes | Yes |
| /plan-phase | Yes | Yes |
| /next-actions | Yes | No |
| /summarize-prd | Yes | No |

## Free-Form Chat

Messages that don't start with `/` are handled as free-form chat with project context:

```bash
POST /projects/{project_id}/chat
{
  "message": "What should I do next?"
}
```

The LLM receives context about the project (name, brief, capabilities, phases) and can provide guidance.

## Error Handling

Invalid commands return helpful usage information:

```
Unknown command: /invalid

Type `/help` for a list of available commands.
```

Invalid phases are rejected with valid options:

```
Invalid phase: foo
Valid phases: planning, architecture, data, development, qa, documentation
```

## Examples

### Complete Workflow

```bash
# 1. Generate planning artifacts
/plan-phase planning

# 2. View what was created
/artifacts phase=planning

# 3. Read the PRD
/open planning_PRD.md

# 4. Get summary
/summarize-prd

# 5. Run data phase
/run-phase data

# 6. Check diagnostics
/diagnose-phase data

# 7. Get recommendations
/next-actions
```

### Quick Status Check

```bash
# See what's in planning
/artifacts phase=planning

# Check diagnostics
/diagnose-phase planning

# Get next steps
/next-actions
```
