# Claude Code Orchestrator

![Cleanliness](docs/badges/cleanliness.svg)

A meta-framework for coordinating multiple specialized Claude Code subagents to collaboratively build complex software projects through structured, checkpoint-driven workflows.

---

## 🚀 Using as a Template

**Create a new project in seconds:**

```bash
# Method 1: Bootstrap Command (Recommended)
orchestrator bootstrap analytics --output ~/projects/my-new-project

# Method 2: GitHub Template Button
# Click "Use this template" button above ↗️
```

[![Use this template](https://img.shields.io/badge/Use%20this%20template-2ea44f?style=for-the-badge)](https://github.com/kearney/claude-code-orchestrator/generate)

**Available project templates:**
- **`analytics`** - Data analysis, insights, statistical modeling
- **`ml-model`** - Machine learning, predictive modeling, deep learning
- **`webapp`** - Full-stack web applications, dashboards
- **`supply-chain`** - Operations research, optimization, logistics

**📖 Full guide:** [TEMPLATE_USAGE.md](TEMPLATE_USAGE.md)

---

## Features

The orchestrator provides a comprehensive framework for building production-grade software with AI agents:

### Skills Framework

Reusable analytical patterns and methodologies that agents can apply across projects. Skills encapsulate proven approaches for common tasks like time-series forecasting, survey analysis, and optimization modeling. Agents load skills on-demand and adapt them to project-specific requirements.

**📖 Learn more:** [.claude/skills/README.md](.claude/skills/README.md)

### Knowledge Base

A three-tier knowledge architecture that provides agents with universal best practices, firm-wide standards, and project-specific domain expertise. Knowledge flows from universal (data science fundamentals) → firm-wide (Kearney RAISE framework) → project-specific (domain terminology, business rules).

**📖 Learn more:** [.claude/knowledge/README.md](.claude/knowledge/README.md)

### Architecture Decision Records (ADRs)

Lightweight documentation of significant technical decisions made during the project lifecycle. ADRs capture context, options considered, decision rationale, and consequences. The orchestrator prompts agents to create ADRs at key decision points.

**📖 Learn more:** [.claude/decisions/README.md](.claude/decisions/README.md)

### Client Governance

YAML-based configuration system for client-specific quality gates, compliance requirements, brand constraints, and deployment policies. Governance rules are validated via JSON Schema and automatically enforced during workflow execution.

**📖 Learn more:** [clients/README.md](clients/README.md)

### Code Execution Mode (MCP)

Opt-in code generation mode that reduces LLM token usage by 98% (from ~150k to ~2k tokens). The orchestrator generates Python code that imports filesystem-based APIs, executes it in a sandboxed environment, and collects artifacts.

**Key Features:**
- 🚀 **98% Token Reduction**: Generate code instead of passing large contexts
- 🔒 **Sandboxed Execution**: Import whitelist, network blocking, resource limits
- 📦 **MCP API Registry**: Data loading, analytics, modeling, visualization modules
- ⚙️ **Opt-In**: Use `--mode code` flag, defaults to legacy executors

**Usage:**
```bash
orchestrator run start --mode code --intake myproject.yaml
```

**📖 Learn more:** [docs/playbooks/mcp-code-exec.md](docs/playbooks/mcp-code-exec.md) | [docs/adr/004-mcp-code-execution.md](docs/adr/004-mcp-code-execution.md)

### Specialized Agents (Auto-Detected)

Three specialized agents automatically trigger based on project requirements and governance policies, extending lifecycle coverage without manual configuration.

**Available Agents:**
- 🔍 **Performance Engineer**: Profiles application, identifies bottlenecks, validates against SLAs
- 🔒 **Security Auditor**: Scans for vulnerabilities (OWASP Top 10), validates compliance (GDPR/HIPAA/SOC2)
- 🗄️ **Database Architect**: Designs schemas, generates migrations, optimizes indexes

**Auto-Detection Triggers:**
```yaml
# Performance Engineer triggers on:
performance_slas.latency_p95_ms > 0  # OR production environment OR performance keywords

# Security Auditor triggers on:
require_security_scan: true  # OR compliance requirements OR production environment

# Database Architect triggers on:
requirements: ["database", "schema", "SQL"]  # OR database keywords in project type
```

**Artifacts**: Performance profiles, security scan results, database schemas, compliance reports

**📖 Learn more:** [docs/playbooks/specialized-agents.md](docs/playbooks/specialized-agents.md) | [docs/adr/005-specialized-agents.md](docs/adr/005-specialized-agents.md)

### C-Suite Templates

Production-ready HTML/CSS/JS templates for executive presentations and one-pagers. Templates enforce Kearney brand compliance (Arial font, no gridlines, purple accent) and include D3.js chart patterns optimized for C-suite audiences.

**📖 Learn more:** [design_system/templates/README.md](design_system/templates/README.md)

### 🤖 AI-Powered Code Review

Automated code review using Claude API that analyzes pull requests for security vulnerabilities, performance issues, code quality, and best practices. Reviews are posted as PR comments with actionable recommendations.

**Key Features:**
- 🔒 **Security Analysis**: Input validation, injection prevention, authentication
- ⚡ **Performance Review**: Algorithm efficiency, database queries, memory usage
- 📝 **Code Quality**: Readability, maintainability, modularity, documentation
- ✅ **Best Practices**: Error handling, logging, testing coverage
- 🏗️ **Architecture**: Design patterns, separation of concerns, dependencies
- 📊 **Severity Classification**: Critical, Major, Minor, Suggestions
- 💡 **Before/After Samples**: Concrete code recommendations with examples

**Quick Setup:**
```bash
# 1. Get Anthropic API key from https://console.anthropic.com
# 2. Add to GitHub Secrets: ANTHROPIC_API_KEY
# 3. Create a PR → AI review runs automatically
```

**Cost:** ~$0.10-$0.50 per PR review (depending on size)

**📖 Full setup guide:** [docs/AI_CODE_REVIEW_SETUP.md](docs/AI_CODE_REVIEW_SETUP.md)

**Example Review Output:**
```markdown
### Critical Issues (Must Fix)
**Issue 1: SQL Injection Vulnerability**
- File: `src/auth.py:45`
- Category: Security
- Code: `query = f"SELECT * FROM users WHERE id='{user_id}'"`
- Recommendation: Use parameterized queries
- Effort: 15 minutes
```

**How It Works:**
1. PR opened/updated → GitHub Actions triggers
2. Changed files analyzed via Claude API
3. Comprehensive review posted as PR comment
4. Full report uploaded as workflow artifact
5. Security issues flagged for immediate attention

**Customization:**
- Customize reviewer prompt: `subagent_prompts/reviewer.md`
- Add project-specific rules and style guidelines
- Configure review depth (STANDARD, THOROUGH, SECURITY_FOCUSED)
- Set file size limits and review scope

---

## Getting Started

**New to the orchestrator?** Start here:

- **[QUICKSTART.md](docs/QUICKSTART.md)** - 5-minute setup guide with hands-on examples
- **[METHODOLOGY.md](docs/METHODOLOGY.md)** - Deep dive into orchestrator philosophy and architecture

**Want to create a new project?** Use the bootstrap command:

```bash
# Create a new analytics project in seconds
orchestrator bootstrap analytics --output ~/projects/my-analysis

# Or use the interactive wizard
orchestrator intake new
```

**Already have a project?** Jump to the [Run-Loop Quickstart](#run-loop-quickstart) below.

---

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

### Quick Start Options

**Option 1: Bootstrap Command (Fastest)**

```bash
# Create a complete project structure in seconds
orchestrator bootstrap analytics --output ~/projects/my-project
cd ~/projects/my-project

# Install dependencies
pip install -r requirements.txt

# Start orchestration
orchestrator run start --intake intake.yaml
orchestrator run next
```

**Option 2: Natural Language in Claude Code**

1. In Claude Code, type: **"new project"**
2. Follow the interactive wizard to select project type and configure
3. Edit the generated intake file: `intake/<project-name>.intake.yaml`
4. Validate: `orchestrator intake validate intake/<project>.intake.yaml`
5. Render to project files: `orchestrator intake render intake/<project>.intake.yaml`
6. Start orchestration: `orchestrator run start --intake intake/<project>.intake.yaml`
7. Execute workflow: `orchestrator run next` (repeat until complete)

**📖 See also:**
- [Bootstrap Command Guide](docs/bootstrap.md) - Complete bootstrap documentation
- [Intake Documentation](docs/intake.md) - Detailed intake configuration guide
- [QUICKSTART.md](docs/QUICKSTART.md) - 5-minute hands-on tutorial
- [METHODOLOGY.md](docs/METHODOLOGY.md) - Understanding the orchestrator approach
