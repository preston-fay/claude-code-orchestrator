# Claude Code Orchestrator

![Cleanliness](docs/badges/cleanliness.svg)

A meta-framework for coordinating multiple specialized Claude Code subagents to collaboratively build complex software projects through structured, checkpoint-driven workflows.

## Repository Health

![Hygiene Trend](docs/hygiene_trend.png)

See [Repository Hygiene Guide](docs/repo_hygiene.md) for cleanliness scoring and quality gates.

## Natural Language Triggers

The orchestrator responds to natural language commands in Claude Code:

**"New project"** → Starts the project intake wizard

Simply type "new project" and the orchestrator will guide you through:
- Selecting a project type (webapp, analytics, ml, etc.)
- Creating an intake configuration
- Rendering project files

**Supported trigger phrases:**
- "new project", "create new project", "start a new project"
- "new web project" (auto-selects webapp type)
- "new analytics project" (auto-selects analytics type)
- "new ml project" (auto-selects ml type)

**Busy Protection:** Triggers are blocked while a workflow is running. Finish the current workflow or run `orchestrator run --abort`.

## Unified CLI

The orchestrator provides a unified command-line interface that composes multiple command groups:

```bash
# Intake commands (project initialization)
orchestrator intake new          # Create new project intake
orchestrator intake validate <file>  # Validate intake config
orchestrator intake render <file>    # Render config to project files
orchestrator intake templates    # List available templates

# Data commands (from data foundation)
orchestrator data ingest         # Ingest data to raw/
orchestrator data transform      # Transform data → processed/
orchestrator data train          # Train model
orchestrator data evaluate       # Evaluate model
orchestrator data status         # Show pipeline status

# Run commands (orchestration workflow)
orchestrator run start           # Start new workflow run
orchestrator run next            # Execute next phase
orchestrator run next --parallel --max-workers N --timeout SEC  # Parallel execution
orchestrator run status          # Show run status
orchestrator run metrics         # View metrics dashboard
orchestrator run approve         # Approve consensus gate
orchestrator run reject          # Reject and mark for revision
orchestrator run retry --phase PHASE [--agent NAME]  # Retry failed execution
orchestrator run rollback --phase PHASE  # Non-destructive rollback
orchestrator run abort           # Abort current run
orchestrator run resume          # Resume aborted run
orchestrator run log             # View run log
orchestrator run repo-hygiene    # Repository hygiene scan

# Release commands (versioning, changelog, gates, GitHub releases)
orchestrator release prepare     # Prepare release with quality gates
orchestrator release cut         # Execute release (tag, push, GitHub)
orchestrator release verify      # Verify release success
orchestrator release rollback VERSION  # Rollback release

# Orchestrator commands
orchestrator quickstart --type TYPE --name NAME  # One-command project start
orchestrator status              # Show orchestrator status
orchestrator triggers            # List NL triggers
```

## Run-Loop Quickstart

The orchestrator executes multi-phase workflows with checkpoint validation and consensus gates:

```bash
# 1. Start a new run with an intake file
orchestrator run start --intake intake/examples/web_todo_app.yaml

# 2. Execute the next phase (e.g., planning)
orchestrator run next

# 3. Check status
orchestrator run status

# 4. If consensus required, review and approve
orchestrator run approve

# 5. Continue executing phases
orchestrator run next

# Abort if needed
orchestrator run abort
```

**Key Features:**
- **Stateful execution:** Run state persisted to `.claude/orchestrator_state.json`
- **Checkpoint validation:** Artifacts validated after each phase
- **Consensus gates:** Critical phases pause for human approval with enhanced UX
- **Resume capability:** Abort and resume runs without losing progress
- **Phase artifacts:** Track outputs from each completed phase
- **Parallel execution:** Run agents concurrently with configurable limits
- **Artifact packaging:** Automatic zip bundles per phase with metadata
- **Metrics tracking:** Runtime metrics in JSON and Prometheus formats

### Quickstart Macro (One Command!)

The fastest way to start a new project:

```bash
# All-in-one: Generate intake → start run → execute planning → pause at consensus
orchestrator quickstart --type webapp --name my-todo-app

# Or try other types:
orchestrator quickstart --type analytics --name data-pipeline
orchestrator quickstart --type ml --name sentiment-model
orchestrator quickstart --type library --name my-utils
orchestrator quickstart --type service --name api-gateway
```

This will:
1. Generate intake YAML
2. Start orchestrator run
3. Execute planning phase
4. Pause at consensus gate for review

Then continue with:
```bash
orchestrator run approve
orchestrator run next
```

### Parallel Execution

Speed up workflows by running agents concurrently:

```bash
# Force parallel execution for current phase (if supported)
orchestrator run next --parallel

# Control concurrency (capped by config limit)
orchestrator run next --parallel --max-workers 4

# Override timeout (in seconds)
orchestrator run next --timeout 300
```

Configuration in `.claude/config.yaml`:
```yaml
orchestrator:
  max_parallel_agents: 2  # Concurrency limit
  timeout_minutes: 30     # Default timeout
```

### Metrics & Monitoring

Track runtime metrics and performance:

```bash
# View metrics dashboard
orchestrator run metrics

# Output:
# - Phase durations table
# - Agent runtimes and retry counts
# - Latest cleanliness score
# - Paths to JSON and Prometheus files
```

Metrics are saved to:
- `.claude/metrics/run_<id>.json` (structured data)
- `.claude/metrics/metrics.prom` (Prometheus format)

### Retry & Rollback

Handle failures gracefully:

```bash
# Retry failed phase
orchestrator run retry --phase development

# Retry specific agent
orchestrator run retry --phase development --agent developer

# Non-destructive rollback
orchestrator run rollback --phase planning

# Creates ROLLBACK_<timestamp>.md advisory
# Resets workflow cursor without modifying git/files
```

### Enhanced Consensus UX

Improved human-review experience with:

- **Status ribbon** at top: 🟢 READY / 🟡 PARTIAL / 🔴 NEEDS ATTENTION
- **Collapsible sections** for agent outcomes, validation, metrics
- **Artifact bundles**: All phase outputs packaged in `artifacts/{run_id}/{phase}.zip`
- **Metrics links**: Direct links to runtime data and hygiene scores

Example REQUEST.md structure:
```
🟢 **STATUS: READY FOR REVIEW**
---
# Consensus Request: development

## 📦 Artifact Bundle
artifacts/run_20250114_1234/development.zip

<details>
<summary>📋 Agent Outcomes (click to expand)</summary>
...
</details>

<details>
<summary>✅ Artifact Validation (click to expand)</summary>
...
</details>

## Reviewer Checklist
- [ ] All agents completed successfully
- [ ] Required artifacts present
...
```

### Production-Grade Release Management

Ship with confidence using semantic versioning, conventional commits changelog, and quality gates:

```bash
# 1. Prepare release (analyze commits, run gates, preview changelog)
orchestrator release prepare

# Output:
# Version: 0.2.0 → 0.3.0 (minor bump)
# Commits: 47 since last release
# Quality Gates: ✅ All gates passed
#
# ┌──────────────┬────────┬─────────────────────────────┐
# │ Gate         │ Status │ Message                     │
# ├──────────────┼────────┼─────────────────────────────┤
# │ git_status   │ ✅ PASS│ Working tree is clean       │
# │ tests        │ ✅ PASS│ All tests passed (31 tests) │
# │ hygiene      │ ✅ PASS│ Cleanliness: 92/100 (A)     │
# │ security     │ ✅ PASS│ No security issues          │
# │ build        │ ✅ PASS│ Package built successfully  │
# └──────────────┴────────┴─────────────────────────────┘
#
# ✓ Ready to Release

# 2. Execute release (version bump, tag, push, GitHub release)
orchestrator release cut

# Confirms, then:
# - Updates __version__.py and CHANGELOG.md
# - Commits changes
# - Creates git tag
# - Pushes to remote
# - Creates GitHub release with artifacts

# 3. Verify everything worked
orchestrator release verify

# ✓ Release Verified Successfully
```

**Natural Language:** Just type **"prepare release"** or **"cut release"** in Claude Code!

#### Release Features

- **Semantic Versioning**: Automatic bump type detection from conventional commits
- **Conventional Commits**: Parses `feat:`, `fix:`, `BREAKING CHANGE:` for changelog
- **Quality Gates**:
  - `git_status`: Working tree must be clean
  - `tests`: Test suite must pass
  - `hygiene`: Cleanliness score above threshold
  - `security`: Bandit security scan (if installed)
  - `build`: Package must build successfully
- **Changelog Generation**: Auto-generated from commits with emoji sections
- **GitHub Releases**: Automatic with package artifacts and release notes
- **Rollback Support**: Undo releases safely

#### Release Workflow

```bash
# Standard release (auto-detect version bump)
orchestrator release prepare
orchestrator release cut

# Manual version bump
orchestrator release prepare --bump major  # Breaking changes
orchestrator release cut --bump minor      # New features
orchestrator release cut --bump patch      # Bug fixes only

# Prerelease versions
orchestrator release prepare --prerelease alpha.1
orchestrator release cut --prerelease beta.2

# Skip specific gates (use with caution!)
orchestrator release prepare --skip-gate security --skip-gate hygiene

# Local-only release (don't push or create GitHub release)
orchestrator release cut --no-push --no-github

# Draft GitHub release (for manual review before publishing)
orchestrator release cut --draft

# Force release despite gate failures (NOT RECOMMENDED)
orchestrator release cut --force

# Rollback if needed
orchestrator release rollback 1.2.3
git revert HEAD  # Revert version bump commit
```

#### Changelog Format

Generated CHANGELOG.md follows [Keep a Changelog](https://keepachangelog.com/):

```markdown
## [1.2.0] - 2025-01-14

### ⚠️ BREAKING CHANGES
- **api**: change authentication method (abc1234)

### ✨ Features
- **cli**: add release management commands (def5678)
- **gates**: implement quality gate system (ghi9012)

### 🐛 Bug Fixes
- **version**: fix semver parsing (jkl3456)

### 📚 Documentation
- add release workflow guide (mno7890)
```

#### GitHub Release Assets

Automatically includes:
- Python wheels (`.whl`)
- Source distributions (`.tar.gz`)
- Quality gates report (`quality_gates_report.json`)
- Full changelog (`CHANGELOG.md`)

### Quick Start with Natural Language

1. In Claude Code, type: **"new project"**
2. Follow the interactive wizard to select project type and configure
3. Edit the generated intake file: `intake/<project-name>.intake.yaml`
4. Validate: `orchestrator intake validate intake/<project>.intake.yaml`
5. Render to project files: `orchestrator intake render intake/<project>.intake.yaml`
6. Start orchestration: `orchestrator run start --intake intake/<project>.intake.yaml`
7. Execute workflow: `orchestrator run next` (repeat until complete)

See [docs/intake.md](docs/intake.md) for detailed intake documentation.
