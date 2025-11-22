# Claude Code Orchestrator - Quick Reference Summary

## Agent Types at a Glance

### 1. **Architect** (LLM)
- **Role:** System design, technical specifications
- **Artifacts:** architecture.md, technical_spec.md, data_models.md
- **Executor Type:** LLM (in-session/API/stub)
- **Location:** `.claude/agents/architect.md`

### 2. **Developer** (LLM)
- **Role:** Feature implementation
- **Artifacts:** src/**, implementation_notes.md
- **Executor Type:** LLM
- **Location:** `.claude/agents/developer.md`

### 3. **QA** (LLM)
- **Role:** Testing, validation, quality assurance
- **Artifacts:** test_plan.md, test_results.md, qa_report.md
- **Executor Type:** LLM
- **Location:** `.claude/agents/qa.md`

### 4. **Data** (Subprocess)
- **Role:** ETL, analytics, ML model training
- **Artifacts:** data/processed/**, models/**, docs/data_documentation.md
- **Executor Type:** Subprocess (entrypoints)
- **Entrypoints:** ingest, transform, train, evaluate, pipeline, status
- **Location:** `.claude/agents/` (no dedicated file, config-based)

### 5. **Documentarian** (LLM)
- **Role:** Documentation creation and maintenance
- **Artifacts:** README.md, USER_GUIDE.md, API_REFERENCE.md, docs/**
- **Executor Type:** LLM
- **Location:** `.claude/agents/documentarian.md`

### 6. **Consensus** (LLM)
- **Role:** Conflict resolution, checkpoint approvals
- **Artifacts:** consensus_decisions.md, conflict_resolution.md, checkpoint_approvals.md
- **Executor Type:** LLM
- **Location:** `.claude/agents/consensus.md`

### 7. **Reviewer** (LLM, Optional)
- **Role:** Code review, best practices validation
- **Artifacts:** code_review.md, improvements.md, review_checklist.md
- **Executor Type:** LLM
- **Location:** `.claude/agents/reviewer.md`

### 8. **Steward** (Subprocess)
- **Role:** Repository hygiene, dead code detection
- **Artifacts:** reports/repo_hygiene_report.md, reports/PR_PLAN.md, reports/dead_code.md
- **Executor Type:** Subprocess (entrypoints)
- **Entrypoints:** scan, dead_code, notebooks, aggregate
- **Location:** `.claude/agents/steward.md`

---

## Workflow Phases

**Standard Workflow Order:**
1. **planning** (Architect) - requires_consensus=true
2. **data_engineering** (Data) - optional, requires_consensus=false
3. **development** (Developer) - requires_consensus=false
4. **quality_assurance** (QA) - requires_consensus=true
5. **documentation** (Documentarian) - requires_consensus=false
6. **review** (Reviewer) - optional, requires_consensus=true
7. **repo_hygiene** (Steward) - optional, requires_consensus=true

**State Progression:**
```
IDLE → RUNNING → [AWAITING_CONSENSUS] → COMPLETED
           ↓
    NEEDS_REVISION (on failure/rejection)
```

---

## Checkpoint System

### Three Validation Statuses
- **PASS:** All artifact patterns matched, files non-empty
- **PARTIAL:** Some patterns matched, others missing
- **FAIL:** No patterns matched

### Validation Process
1. Phase completes (all agents successful)
2. Glob patterns matched against project files
3. Report generated: `reports/checkpoint_validation_{phase}.md`
4. If requires_consensus=true: approval request generated
5. Artifacts tracked in state: `phase_artifacts[phase_name]`

### Special: Data Checkpoints
Located in `.claude/checkpoints/DATA-CHECKLIST.md`
- Post-Ingestion (raw data loaded)
- Post-Validation (quality checks complete)
- Post-Transform (features engineered)
- Post-Training (models trained)
- Post-Evaluation (metrics calculated)
- Full Pipeline (complete state)

---

## State Management

### State File Location
`.claude/orchestrator_state.json`

### Key State Fields
```json
{
  "run_id": "timestamp-based ID",
  "status": "idle|running|awaiting_consensus|needs_revision|completed",
  "current_phase": "phase name",
  "completed_phases": ["planning", "development"],
  "phase_artifacts": {
    "planning": ["architecture.md", "technical_spec.md"],
    "development": ["src/main.py", "implementation_notes.md"]
  },
  "awaiting_consensus": false|true,
  "intake_path": "path/to/intake.yaml",
  "intake_summary": {
    "project_name": "string",
    "project_type": "webapp|ml|analytics",
    "description": "string"
  }
}
```

### State Persistence
State saved after:
- `start_run()` (initialization)
- Each phase completion
- Consensus approval/rejection
- Phase failure

---

## Execution Modes

| Mode | Behavior | Use Case | Requirements |
|------|----------|----------|--------------|
| **in-session** | Print instructions, exit(2) | Interactive development | None |
| **API** | Call Claude API directly | Automated CI/CD | ANTHROPIC_API_KEY |
| **stub** | Return simulated responses | Testing | None |

**Set via:** `.claude/config.yaml` → `orchestrator.execution_mode`
**Or:** Environment variable `ORCHESTRATOR_EXECUTION_MODE=api`

---

## Executor Types

### LLM Agents (Architect, Developer, QA, Documentarian, Consensus, Reviewer)
- Triggered when agent has NO `entrypoints` in config
- Load prompt template from `subagent_prompts/{agent}.md`
- Build context (project_name, phase, last_artifacts, etc.)
- Interpolate {{variables}} in template
- Execute via selected mode (in-session/API/stub)

### Subprocess Agents (Data, Steward)
- Triggered when agent has `entrypoints` in config
- Execute Python subprocess commands
- Timeout: 30 minutes (configurable)
- Retry on transient errors (exit codes 75, 101, 111, 125)
- Exponential backoff: 0.7s → 1.4s → 2.8s
- Track stdout, stderr, exit code

---

## Phase Execution Flow

```
START_RUN(intake_path)
  ├─ Initialize RunState
  └─ Save to orchestrator_state.json

NEXT_PHASE()
  ├─ RUN_PHASE(current_phase)
  │  ├─ Build agent context
  │  ├─ For each agent:
  │  │  ├─ Load prompt template
  │  │  ├─ Interpolate variables
  │  │  ├─ Get executor (LLM or subprocess)
  │  │  └─ Invoke with retry logic
  │  ├─ Validate artifacts (if required)
  │  └─ Generate PhaseOutcome
  │
  ├─ Check requires_consensus
  │  ├─ If true: Generate REQUEST.md, pause
  │  └─ If false: Advance to next phase
  │
  ├─ Update state
  ├─ Store artifacts in phase_artifacts
  └─ Save state

COMPLETE (when no next phase)
```

---

## Consensus & Approval

**When Phase Requires Consensus:**
1. Phase completes successfully
2. `.claude/consensus/REQUEST.md` generated
3. State: `awaiting_consensus = true`
4. Workflow pauses

**User Actions:**
```bash
orchestrator run approve              # Accept, advance
orchestrator run reject --reason "..."  # Reject, retry
```

**Request Contents:**
- Status ribbon (green/red)
- Agent execution results
- Artifact validation status
- Metrics digest
- Recommended actions

---

## Artifact Flow & Handoff

### How Artifacts Pass Between Phases

```
Phase N completes
  ├─ Artifacts validated via globs
  ├─ Matched files stored in state.phase_artifacts["phase_n"]
  └─ Save state to JSON

Phase N+1 starts
  ├─ build_agent_context() called
  ├─ last_artifacts = all previous phase_artifacts
  ├─ Interpolate into prompt template
  └─ Agent sees: "Previous artifacts from planning: architecture.md, ..."
```

### Interpolation Variables
- `{{project_name}}` - From intake
- `{{phase}}` - Current phase
- `{{last_artifacts}}` - All previous artifacts
- `{{intake_summary}}` - Project requirements
- `{{entrypoints}}` - Subprocess commands
- `{{checkpoint_artifacts}}` - Expected outputs

---

## Configuration Locations

| File | Purpose | Location |
|------|---------|----------|
| Main config | Orchestrator settings, phases, agents | `.claude/config.yaml` |
| Agent defs | Role descriptions | `.claude/agents/{agent}.md` |
| Prompts | LLM prompt templates | `subagent_prompts/{agent}.md` |
| State | Current run state | `.claude/orchestrator_state.json` |
| Checkpoints | Validation rules | `.claude/checkpoints/DATA-CHECKLIST.md` |
| Consensus | Approval requests | `.claude/consensus/REQUEST.md` |
| Decisions | Architecture decisions | `.claude/decisions/ADR-*.md` |
| Skills | Reusable methodologies | `.claude/skills/*.yaml` |
| Knowledge | Domain information | `.claude/knowledge/*.yaml` |

---

## Key Design Decisions

✅ **Sequential by default** - Phases execute one at a time, agents execute sequentially within phases
✅ **In-session mode** - Orchestrator prints instructions, waits for human work by default
✅ **JSON state files** - Human-readable, version control friendly
✅ **Glob-based validation** - Simple pattern matching for artifact existence
✅ **Prompt interpolation** - {{}} template syntax for context injection
✅ **Phase-level artifacts** - Track outputs at phase granularity
✅ **Consensus gates** - Human approval required for critical phases
✅ **Retry on transient errors** - Exponential backoff for flaky operations

---

## Files to Understand the Architecture

**Core Logic:**
- `src/orchestrator/runloop.py` - Main orchestration engine
- `src/orchestrator/state.py` - State persistence
- `src/orchestrator/types.py` - Data classes
- `src/orchestrator/checkpoints.py` - Artifact validation

**Configuration:**
- `.claude/config.yaml` - Main configuration
- `.claude/agents/*.md` - Agent definitions
- `subagent_prompts/*.md` - LLM prompt templates

**State & Artifacts:**
- `.claude/orchestrator_state.json` - Current run state
- `.claude/checkpoints/` - Checkpoint artifacts
- `.claude/consensus/REQUEST.md` - Approval requests
- `reports/checkpoint_validation_*.md` - Validation reports

**Execution:**
- `src/orchestrator/executors/llm_exec.py` - LLM executor
- `src/orchestrator/executors/subprocess_exec.py` - Subprocess executor
- `src/orchestrator/reliability.py` - Retry & timeout logic

---

## Total Architecture Stats

- **8 Agent Types** (6 LLM-based, 2 subprocess-based)
- **7 Standard Phases** (+ 2 optional phases)
- **3 Execution Modes** (in-session, API, stub)
- **2 Executor Patterns** (LLM, subprocess)
- **3 Validation Statuses** (PASS, PARTIAL, FAIL)
- **~2,500 Lines** Core orchestrator code

---

## Running the Orchestrator API in Docker

### Build locally
```bash
docker build -t orchestrator-api:local .
```

### Run locally
```bash
docker run -p 8000:8000 orchestrator-api:local
```

### Test health endpoint
```bash
curl http://localhost:8000/health
```

### Production Entrypoint

The production ASGI entrypoint is:
```
orchestrator_v2.main:app
```

**Usage with uvicorn:**
```bash
uvicorn orchestrator_v2.main:app --host 0.0.0.0 --port 8000
```

**Usage with gunicorn (multiple workers):**
```bash
gunicorn orchestrator_v2.main:app -w 4 -k uvicorn.workers.UvicornWorker
```

### Docker Image Details

| Property | Value |
|----------|-------|
| Base Image | python:3.11-slim |
| Exposed Port | 8000 |
| Entrypoint | uvicorn orchestrator_v2.main:app |
| Build Type | Multi-stage (builder + runtime) |

### CI/CD

GitHub Actions workflow: `.github/workflows/build-and-publish-image.yml`

- Triggers on push to main branch
- Builds and tests container image
- Pushes to Amazon ECR with `latest` and `GITHUB_SHA` tags

---

## Setting Up Amazon ECR and GitHub Secrets

### 1. Create the ECR repository (one-time)

Make sure you have AWS CLI configured locally with the right account.

```bash
aws ecr create-repository \
  --repository-name orchestrator-api \
  --image-scanning-configuration scanOnPush=true \
  --region us-east-1
```

### 2. Add GitHub Secrets

In your GitHub repo settings, add:
- `AWS_ACCESS_KEY_ID`
- `AWS_SECRET_ACCESS_KEY`

These should correspond to an IAM user/role with permissions to:
- `ecr:GetAuthorizationToken`
- `ecr:BatchCheckLayerAvailability`
- `ecr:PutImage`
- `ecr:InitiateLayerUpload`
- `ecr:UploadLayerPart`
- `ecr:CompleteLayerUpload`
- `ecr:DescribeRepositories`
- `sts:GetCallerIdentity`

### 3. Run the workflow

Push to main or trigger the workflow manually from GitHub Actions.

On success, you should see the image in ECR with tags:
- `latest`
- `<GITHUB_SHA>`

### 4. Get ECR Image URI

```bash
python scripts/print_ecr_uri.py
# Example output:
# 123456789012.dkr.ecr.us-east-1.amazonaws.com/orchestrator-api
```

This URI will be used in App Runner deployment.

---

## Quick Validation After Deployment

### 1. Get the App Runner URL

From AWS Console → App Runner → Your Service → Default domain

### 2. Run the Verification Script

```bash
python scripts/verify_deployment.py --url https://xxxxx.awsapprunner.com
```

Expected output:
```
Orchestrator Deployment Verification
=====================================
Target: https://xxxxx.awsapprunner.com

[1/4] Health Check................ OK
[2/4] Create Project.............. OK
      Project ID: abc12345...
[3/4] Start Ready Stage........... OK
[4/4] Get RSG Overview............ OK

=====================================
VERIFICATION PASSED
All endpoints responding correctly
=====================================
```

### 3. Or Use Raw curl

```bash
# Health check
curl https://<url>/health

# List projects
curl https://<url>/projects

# RSG overview
curl https://<url>/rsg/<project_id>/overview
```

See [DEPLOYMENT_VALIDATION.md](DEPLOYMENT_VALIDATION.md) for complete validation guide.

