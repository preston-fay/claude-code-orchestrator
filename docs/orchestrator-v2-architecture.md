# Claude Code Orchestrator v2 Architecture

## Executive Summary

The Claude Code Orchestrator v2 is a comprehensive rewrite of the orchestration layer that coordinates multiple specialized Claude Code agents to deliver complex software projects. This document provides a high-level architectural overview and serves as the entry point for understanding the system design.

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                    ORCHESTRATOR v2 CORE                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐        │
│  │  Workflow   │    │   Phase     │    │    Agent    │        │
│  │  Engine     │───▶│  Manager    │───▶│   Runtime   │        │
│  └─────────────┘    └─────────────┘    └─────────────┘        │
│         │                  │                  │                │
│         ▼                  ▼                  ▼                │
│  ┌─────────────────────────────────────────────────────┐      │
│  │              CHECKPOINT SYSTEM                       │      │
│  │  (Artifact Validation, State Persistence, Rollback) │      │
│  └─────────────────────────────────────────────────────┘      │
│                           │                                    │
│         ┌─────────────────┼─────────────────┐                 │
│         ▼                 ▼                 ▼                 │
│  ┌───────────┐     ┌───────────┐     ┌───────────┐           │
│  │  Skills   │     │   Tools   │     │Governance │           │
│  │ Registry  │     │ Registry  │     │  Engine   │           │
│  └───────────┘     └───────────┘     └───────────┘           │
│         │                 │                 │                 │
│         └─────────────────┼─────────────────┘                 │
│                           ▼                                    │
│  ┌─────────────────────────────────────────────────────┐      │
│  │            TOKEN MANAGEMENT SYSTEM                   │      │
│  │    (Budgets, Tracking, Context Optimization)        │      │
│  └─────────────────────────────────────────────────────┘      │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

## Core Components

### 1. Workflow Engine

The Workflow Engine orchestrates the end-to-end execution of a project. It:

- Loads workflow configuration from intake files
- Manages workflow state and phase transitions
- Coordinates checkpoints and rollbacks
- Handles errors and recovery

```python
class WorkflowEngine:
    async def run(self, intake: IntakeConfig) -> WorkflowResult:
        workflow = await self.initialize(intake)

        for phase in workflow.phases:
            result = await self.phase_manager.execute(phase, workflow.context)

            if result.status == "blocked":
                await self.handle_blocked(phase, result)
            else:
                await self.checkpoint_manager.save(phase, result)

        return WorkflowResult(workflow)
```

### 2. Phase Manager

The Phase Manager executes individual phases according to the phase model defined in [ADR-002](adr/ADR-002-phase-model-and-checkpoints.md).

**Phases:**
1. **Planning** - Requirements analysis, scope definition
2. **Architecture** - System design, technology decisions
3. **Data** (Optional) - Data pipelines, models, analytics
4. **Development** - Feature implementation
5. **QA** - Testing and validation
6. **Documentation** - Technical and user documentation

Each phase produces checkpoint artifacts that are validated before proceeding.

### 3. Agent Runtime

The Agent Runtime manages agent lifecycle and execution as defined in [ADR-001](adr/ADR-001-agent-architecture-and-subagents.md).

**Agent Types:**
| Agent | Role | Subagents |
|-------|------|-----------|
| Architect | System design, ADRs | architect.data, architect.security |
| Data | ETL, ML pipelines | data.ingestion, data.transform |
| Developer | Code implementation | developer.frontend, developer.backend |
| QA | Testing, validation | qa.unit, qa.integration |
| Documentarian | Documentation | documentarian.api, documentarian.user |
| Consensus | Decision review | N/A |
| Steward | Repo hygiene | steward.security |
| Reviewer | Code review | N/A |

**Agent Lifecycle:**
```
INITIALIZE → PLAN → ACT (multi-step) → SUMMARIZE → COMPLETE
```

### 4. Checkpoint System

The Checkpoint System validates and persists phase outputs:

- **Artifact validation** using glob patterns
- **State snapshots** for recovery
- **Rollback support** for failed phases
- **Audit trail** for compliance

See [ADR-002](adr/ADR-002-phase-model-and-checkpoints.md) for details.

### 5. Skills Registry

Skills are executable methodology modules as defined in [ADR-003](adr/ADR-003-skills-and-tools-as-first-class-modules.md).

**Skill Structure:**
```yaml
skill:
  id: time_series_forecasting
  version: "1.0.0"
  triggers: ["forecast", "predict", "time series"]
  methodology:
    - step: data_preparation
    - step: exploration
    - step: model_selection
    - step: training
    - step: evaluation
```

Skills encode domain-agnostic methodologies that agents apply to tasks.

### 6. Tools Registry

Tools wrap environment interactions with consistent interfaces:

**Available Tools:**
- `git` - Version control operations
- `file_system` - File read/write
- `duckdb` - SQL analytics
- `python_executor` - Python code execution
- `linter` - Code quality checks
- `visualization` - Chart generation

Each tool has:
- Defined actions with parameters
- Input/output schemas
- Safety constraints
- Timeout limits

### 7. Governance Engine

The Governance Engine enforces quality gates and compliance as defined in [ADR-004](adr/ADR-004-governance-and-quality-gates-engine.md).

**Policy Hierarchy:**
```
Client Governance > Kearney Default > Universal
```

**Gate Types:**
- **Metric gates** - Test coverage, complexity
- **Tool gates** - Security scans, linting
- **Validator gates** - Brand compliance, license headers

Gates are evaluated at every phase boundary with full audit logging.

### 8. Token Management

Token management provides cost control as defined in [ADR-005](adr/ADR-005-token-efficiency-and-cost-control.md).

**Features:**
- Real-time token tracking
- Hierarchical budgets (workflow → phase → agent)
- Context optimization strategies
- Cost attribution and reporting

**Optimization Strategies:**
- Selective context loading
- Progressive context expansion
- Context summarization for handoffs
- Caching and reuse

## Data Flow

### Workflow Execution Flow

```
┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐
│  Intake  │───▶│ Planning │───▶│  Arch    │───▶│  Data    │
│  Config  │    │  Phase   │    │  Phase   │    │  Phase   │
└──────────┘    └────┬─────┘    └────┬─────┘    └────┬─────┘
                     │               │               │
                     ▼               ▼               ▼
                ┌─────────┐    ┌─────────┐    ┌─────────┐
                │Checkpoint│   │Checkpoint│   │Checkpoint│
                │   CP1   │    │   CP2   │    │   CP3   │
                └─────────┘    └─────────┘    └─────────┘
                                                     │
     ┌───────────────────────────────────────────────┘
     │
     ▼
┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐
│   Dev    │───▶│    QA    │───▶│   Docs   │───▶│ Complete │
│  Phase   │    │  Phase   │    │  Phase   │    │          │
└────┬─────┘    └────┬─────┘    └────┬─────┘    └──────────┘
     │               │               │
     ▼               ▼               ▼
┌─────────┐    ┌─────────┐    ┌─────────┐
│Checkpoint│   │Checkpoint│   │Checkpoint│
│   CP4   │    │   CP5   │    │   CP6   │
└─────────┘    └─────────┘    └─────────┘
```

### Agent Execution Flow

```
┌────────────┐
│   Task     │
└─────┬──────┘
      │
      ▼
┌────────────┐    ┌────────────┐
│  Discover  │───▶│   Load     │
│   Skills   │    │   Tools    │
└─────┬──────┘    └─────┬──────┘
      │                 │
      └────────┬────────┘
               │
               ▼
┌────────────────────────────┐
│     Agent Execution        │
│  ┌─────────────────────┐  │
│  │ Initialize Context  │  │
│  └──────────┬──────────┘  │
│             │              │
│  ┌──────────▼──────────┐  │
│  │   Plan Approach     │  │
│  └──────────┬──────────┘  │
│             │              │
│  ┌──────────▼──────────┐  │
│  │  Execute Actions    │◀─┼──┐
│  └──────────┬──────────┘  │  │
│             │              │  │ Loop
│  ┌──────────▼──────────┐  │  │
│  │  Evaluate Result    │──┼──┘
│  └──────────┬──────────┘  │
│             │              │
│  ┌──────────▼──────────┐  │
│  │ Summarize Output    │  │
│  └─────────────────────┘  │
└────────────┬───────────────┘
             │
             ▼
┌────────────────────────────┐
│     Checkpoint Save        │
└────────────────────────────┘
```

## Key Design Decisions

| Area | Decision | ADR |
|------|----------|-----|
| Agent Model | All agents use Claude Agent SDK patterns with optional subagents | [ADR-001](adr/ADR-001-agent-architecture-and-subagents.md) |
| Workflow Model | Six-phase model with explicit checkpoints and rollback | [ADR-002](adr/ADR-002-phase-model-and-checkpoints.md) |
| Skills | Executable methodology modules with schemas and triggers | [ADR-003](adr/ADR-003-skills-and-tools-as-first-class-modules.md) |
| Tools | Standardized wrappers with consistent interfaces | [ADR-003](adr/ADR-003-skills-and-tools-as-first-class-modules.md) |
| Governance | Centralized engine with composable policies and audit trail | [ADR-004](adr/ADR-004-governance-and-quality-gates-engine.md) |
| Cost Control | Hierarchical budgets with context optimization | [ADR-005](adr/ADR-005-token-efficiency-and-cost-control.md) |

## Technology Stack

### Core Runtime
- **Python 3.11+** - Primary runtime
- **AsyncIO** - Concurrent agent execution
- **Pydantic** - Schema validation
- **YAML** - Configuration format

### Storage & State
- **SQLite/PostgreSQL** - Workflow state
- **Redis** - Context caching
- **File System** - Artifacts and checkpoints

### Integration
- **Claude API** - LLM backend for agents
- **Git** - Version control
- **DuckDB** - Analytics queries

### Observability
- **Structured logging** - JSON logs
- **OpenTelemetry** - Tracing
- **Prometheus** - Metrics

## Directory Structure

```
orchestrator/
├── core/
│   ├── workflow.py          # Workflow engine
│   ├── phase.py             # Phase manager
│   ├── agent.py             # Agent runtime
│   └── checkpoint.py        # Checkpoint system
├── skills/
│   ├── registry.py          # Skill discovery
│   ├── base.py              # BaseSkill class
│   └── [skill_name]/        # Individual skills
├── tools/
│   ├── registry.py          # Tool discovery
│   ├── base.py              # BaseTool class
│   └── [tool_name]/         # Individual tools
├── governance/
│   ├── engine.py            # Governance engine
│   ├── gates/               # Gate definitions
│   └── policies/            # Default policies
├── tokens/
│   ├── tracker.py           # Usage tracking
│   ├── budget.py            # Budget enforcement
│   └── optimizer.py         # Context optimization
├── agents/
│   ├── architect.yaml       # Agent configs
│   ├── developer.yaml
│   ├── qa.yaml
│   └── ...
└── cli/
    └── commands/            # CLI commands
```

## Configuration

### Workflow Configuration (intake.yaml)

```yaml
project:
  name: "Customer Analytics Platform"
  client: "acme-corp"

requirements:
  - "Build demand forecasting model"
  - "Create executive dashboard"
  - "Document API endpoints"

phases:
  - planning
  - architecture
  - data
  - development
  - qa
  - documentation

constraints:
  timeline: "2 weeks"
  budget_tokens: 2000000
```

### Agent Configuration

```yaml
agent:
  id: developer
  system_prompt: prompts/developer.md
  skills:
    - code_generation
    - test_writing
  tools:
    - git
    - file_system
    - python_executor
  subagents:
    - id: developer.frontend
      skills: [react, css]
    - id: developer.backend
      skills: [fastapi, database]
```

## Usage

### Running a Workflow

```bash
# Initialize new project
orchestrator init --template analytics

# Start workflow
orchestrator run start --intake intake.yaml

# Check status
orchestrator run status

# View checkpoint
orchestrator checkpoint show CP2

# Rollback to checkpoint
orchestrator checkpoint rollback CP1
```

### Managing Governance

```bash
# Validate governance config
orchestrator governance validate --client acme-corp

# Check gates manually
orchestrator governance check --phase qa

# View audit trail
orchestrator governance audit --workflow proj-123
```

### Budget Management

```bash
# View token usage
orchestrator budget status --workflow proj-123

# Set budget
orchestrator budget set --max-tokens 1000000

# Generate cost report
orchestrator budget report --format json
```

## Migration from v1

### Breaking Changes

1. **Agent configuration format** - New YAML schema with subagent support
2. **Checkpoint format** - New validation and rollback system
3. **Skills format** - From documentation to executable modules
4. **Governance location** - Centralized engine vs. manual checks

### Migration Steps

1. Convert agent prompts to new configuration format
2. Update skill YAML files with schemas and triggers
3. Migrate governance rules to new policy format
4. Update checkpoint handlers for new validation
5. Configure token budgets for workflows

See [docs/migration-guide.md](migration-guide.md) for detailed instructions.

## Roadmap

### Phase 1: Core Infrastructure (Current)
- Agent runtime with subagent support
- Checkpoint system with validation
- Basic governance gates

### Phase 2: Advanced Features
- Skill marketplace (internal)
- Advanced context optimization
- Real-time collaboration

### Phase 3: Enterprise Features
- Multi-tenant support
- SSO integration
- Advanced compliance (SOC2, FedRAMP)

## Contributing

See [CONTRIBUTING.md](../CONTRIBUTING.md) for development setup and contribution guidelines.

## Related Documents

- [ADR-001: Agent Architecture](adr/ADR-001-agent-architecture-and-subagents.md)
- [ADR-002: Phase Model](adr/ADR-002-phase-model-and-checkpoints.md)
- [ADR-003: Skills and Tools](adr/ADR-003-skills-and-tools-as-first-class-modules.md)
- [ADR-004: Governance Engine](adr/ADR-004-governance-and-quality-gates-engine.md)
- [ADR-005: Token Efficiency](adr/ADR-005-token-efficiency-and-cost-control.md)
