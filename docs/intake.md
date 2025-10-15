# Project Intake Guide

## Overview

The Claude Code Orchestrator uses a structured intake process to initialize new projects with appropriate configuration, agent selection, and workflow settings.

## Quick Start

### Using Natural Language Triggers

The easiest way to start a new project is using natural language in Claude Code:

Simply type: **"New project"**

This will trigger the intake wizard, which will guide you through:
1. Selecting a project type (webapp, analytics, ml, etc.)
2. Creating an intake configuration file
3. Validating and rendering the configuration

**Supported trigger phrases:**
- "new project"
- "create new project"
- "start a new project"
- "begin project intake"

**Type-specific shortcuts:**
- "new web project" → Auto-selects webapp type
- "new analytics project" → Auto-selects analytics type
- "new ml project" → Auto-selects ml type

### Using CLI Directly

```bash
# Start interactive wizard
orchestrator intake new

# Create with specific type
orchestrator intake new --type webapp

# Non-interactive mode
orchestrator intake new --type analytics --output intake/my-project.intake.yaml --no-interactive
```

## Busy Protection

If the orchestrator is currently running a workflow, the "new project" trigger will be blocked:

```
⚠️  Orchestrator is currently running a workflow.
Please finish the current workflow or run: orchestrator run --abort
```

This prevents accidental interruption of in-progress work.

## Intake Process

### Step 1: Create Intake File

Choose a starter template based on your project type:

**Available Templates:**
- `webapp` - Web applications (React + FastAPI, etc.)
- `analytics` - Data analytics and reporting projects
- `ml` - Machine learning model development
- `service` - Microservices and APIs
- `library` - Reusable libraries and packages
- `cli` - Command-line tools

```bash
orchestrator intake new --type webapp
```

This creates an intake YAML file (e.g., `intake/my-webapp.intake.yaml`) based on the template.

### Step 2: Customize Intake Configuration

Edit the generated intake file to match your project needs:

```yaml
project:
  name: "my-webapp"
  type: "webapp"
  description: "A web application built with modern frameworks"

goals:
  primary:
    - "Build a responsive web application"
    - "Implement user authentication"
  success_criteria:
    - "Application loads in <2 seconds"
    - "Support 1000+ concurrent users"

orchestration:
  enabled_agents:
    - "architect"
    - "developer"
    - "qa"
    - "documentarian"
    - "consensus"
  checkpoint_cadence: "per-phase"
  approval_gates:
    - "planning"
    - "quality_assurance"
```

See the [Intake Schema](#intake-schema) section for all available options.

### Step 3: Validate Configuration

```bash
orchestrator intake validate intake/my-webapp.intake.yaml
```

This checks that your intake file conforms to the schema and has all required fields.

### Step 4: Render to Project Files

```bash
orchestrator intake render intake/my-webapp.intake.yaml
```

This command safely merges your intake configuration into:
- `.claude/config.yaml` - Orchestration settings
- `CLAUDE.md` - Project mission and phases
- `docs/requirements.md` - Project requirements

**Safety Features:**
- Creates timestamped backups before any modifications
- Prompts for confirmation before overwriting files
- Supports `--dry-run` to preview changes
- Never overwrites without `--overwrite` flag in non-interactive mode

## Intake Schema

### Project Section

```yaml
project:
  name: string          # Project name (kebab-case)
  type: enum            # webapp | service | library | analytics | ml | cli | other
  description: string   # Brief description
  version: string       # Initial version (default: "0.1.0")
```

### Goals Section

```yaml
goals:
  primary: [string]              # Primary goals (required)
  secondary: [string]            # Secondary/nice-to-have goals
  success_criteria: [string]     # Measurable success criteria
```

### Orchestration Section

```yaml
orchestration:
  enabled_agents: [string]       # Which agents to enable
  checkpoint_cadence: enum       # per-phase | per-milestone | daily | on-demand
  approval_gates: [string]       # Phases requiring explicit approval
  consensus_required: [string]   # Phases requiring consensus agent
```

### Data Section (for analytics/ml projects)

```yaml
data:
  sources:
    - name: string
      type: string
      description: string
      sensitivity: enum  # public | internal | confidential | restricted
  storage: [string]
  privacy_requirements: [string]

analytics_ml:
  required: boolean
  use_cases: [string]
  data_volume: string
  latency_requirements: string
  model_types: [string]
```

### Testing Section

```yaml
testing:
  coverage_target: number       # 0-100 (default: 80)
  test_types: [enum]            # unit | integration | e2e | performance | security
  ci_cd: boolean                # Enable CI/CD (default: true)
```

### Security Section

```yaml
secrets_policy:
  vault_required: boolean
  rotation_period: string
  encryption_at_rest: boolean

risk_register:
  - risk: string
    severity: enum              # low | medium | high | critical
    mitigation: string
```

See [`intake/schema/project_intake.schema.json`](../intake/schema/project_intake.schema.json) for the complete schema with all fields and validation rules.

## Starter Templates

### Webapp Template

Best for:
- Single-page applications (SPAs)
- Full-stack web applications
- Admin dashboards
- SaaS products

Default stack: TypeScript + React + FastAPI + PostgreSQL

### Analytics Template

Best for:
- Business intelligence dashboards
- Data warehousing
- ETL pipelines
- Reporting systems

Default stack: Python + dbt + Airflow + PostgreSQL/Snowflake

Includes:
- Data pipeline configuration
- Analytics query templates
- Dashboard specifications

### ML Template

Best for:
- Machine learning model development
- Inference API services
- Model monitoring and retraining
- MLOps infrastructure

Default stack: Python + scikit-learn/PyTorch + MLflow

Includes:
- Model training pipeline
- Feature store configuration
- Model versioning
- Drift detection

## CLI Reference

### `orchestrator intake new`

Create a new intake configuration file.

```bash
orchestrator intake new [OPTIONS]
```

**Options:**
- `--type, -t TEXT` - Project type (webapp, analytics, ml, etc.)
- `--output, -o PATH` - Output path for intake file
- `--interactive / --no-interactive` - Enable/disable wizard (default: interactive)

**Examples:**
```bash
# Interactive wizard
orchestrator intake new

# Specific type
orchestrator intake new --type ml

# Custom output path
orchestrator intake new --type webapp --output custom/path/project.yaml

# Non-interactive
orchestrator intake new --type analytics --no-interactive
```

### `orchestrator intake validate`

Validate an intake configuration file against the schema.

```bash
orchestrator intake validate <intake-file>
```

**Examples:**
```bash
orchestrator intake validate intake/my-project.intake.yaml
```

### `orchestrator intake render`

Render intake configuration to project files.

```bash
orchestrator intake render [OPTIONS] <intake-file>
```

**Options:**
- `--overwrite` - Overwrite existing files without confirmation
- `--dry-run` - Show what would be done without making changes

**Examples:**
```bash
# Interactive (prompts for confirmation)
orchestrator intake render intake/my-project.intake.yaml

# Dry run (preview changes)
orchestrator intake render --dry-run intake/my-project.intake.yaml

# Force overwrite
orchestrator intake render --overwrite intake/my-project.intake.yaml
```

### `orchestrator intake templates`

List available starter templates.

```bash
orchestrator intake templates
```

## Workflow Integration

Once you've created and rendered your intake file, you can start the orchestration workflow:

```bash
# (Future command - not yet implemented)
orchestrator run --intake intake/my-project.intake.yaml
```

This will:
1. Initialize the orchestrator with your configuration
2. Start the workflow at the planning phase
3. Execute each phase according to your settings
4. Create checkpoints at each phase boundary
5. Route to consensus agent at approval gates

## Best Practices

1. **Start with a Template**: Use the closest matching starter template and customize it rather than starting from scratch.

2. **Be Specific**: Define clear, measurable success criteria in the `goals` section.

3. **Enable Appropriate Agents**: Only enable agents you need. For simple projects, you might not need the reviewer or data agents.

4. **Set Approval Gates**: Identify critical phases that require human review (typically planning and QA).

5. **Document Constraints**: Capture technical, budget, and timeline constraints upfront in the intake file.

6. **Privacy First**: Classify data sensitivity and document PII handling requirements.

7. **Version Your Intake**: Commit intake files to version control alongside your project.

8. **Validate Often**: Run `orchestrator intake validate` after making changes to catch errors early.

## Troubleshooting

### "Validation failed: Missing required field"

Ensure all required fields are present in your intake file:
- `project.name`
- `project.type`
- `goals.primary` (must be non-empty array)

### "Unknown template type"

Check available templates with:
```bash
orchestrator intake templates
```

### "Orchestrator is currently running"

If you try to start a new project while another is in progress:
1. Complete the current workflow, OR
2. Abort it with `orchestrator run --abort`

### "Schema validation error"

The intake file doesn't conform to the schema. Common issues:
- Invalid enum values (e.g., wrong project type)
- Missing required nested fields
- Invalid data types (e.g., string instead of array)

Run `orchestrator intake validate` for detailed error messages.

## Next Steps

After creating and rendering your intake configuration:

1. Review the generated/updated files:
   - `.claude/config.yaml`
   - `CLAUDE.md`
   - `docs/requirements.md`

2. Start the orchestration workflow (coming soon):
   ```bash
   orchestrator run
   ```

3. Monitor progress:
   ```bash
   orchestrator status
   ```

For more information, see:
- [Orchestrator Documentation](../README.md)
- [Data Engineering Guide](./data_documentation.md)
- [Security Policy](../SECURITY.md)
