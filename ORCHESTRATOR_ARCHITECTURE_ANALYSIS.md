# Claude Code Orchestrator - Architecture Analysis

## Executive Summary

The Claude Code Orchestrator is a meta-framework that coordinates 8 specialized AI agents through a structured, checkpoint-driven workflow. It implements a stateful run-loop with consensus-based phase transitions, artifact validation, and comprehensive state persistence.

**Key Statistics:**
- 8 Agent Types
- 7 Workflow Phases (+ optional phases)
- 3 Execution Modes (in-session, API, stub)
- 2 Executor Types (LLM-based, subprocess-based)
- JSON-based State Persistence
- Glob-based Artifact Validation

---

## 1. AGENT TYPES & ARCHITECTURE

### Complete Agent Matrix

| Agent | Role | Executor Type | Execution Mode | Checkpoint Artifacts |
|-------|------|---------------|-----------------|---------------------|
| **Architect** | System design & technical specs | LLM | in-session / API / stub | architecture.md, technical_spec.md, data_models.md |
| **Developer** | Feature implementation | LLM | in-session / API / stub | src/**, implementation_notes.md |
| **QA** | Testing & validation | LLM | in-session / API / stub | test_plan.md, test_results.md, qa_report.md |
| **Data** | ETL, analytics, ML models | Subprocess | entrypoints | data/processed/**, models/**, docs/data_documentation.md |
| **Documentarian** | Documentation creation | LLM | in-session / API / stub | README.md, USER_GUIDE.md, API_REFERENCE.md, docs/** |
| **Consensus** | Conflict resolution, approvals | LLM | in-session / API / stub | consensus_decisions.md, conflict_resolution.md, checkpoint_approvals.md |
| **Reviewer** | Code review & feedback (optional) | LLM | in-session / API / stub | code_review.md, improvements.md, review_checklist.md |
| **Steward** | Repository hygiene, cleanup | Subprocess | entrypoints | reports/repo_hygiene_report.md, reports/PR_PLAN.md, reports/dead_code.md |

### Agent Definitions Location
- **Definition Files:** `.claude/agents/{agent_name}.md`
- **Configuration:** `.claude/config.yaml` (subagents section)
- **Prompt Templates:** `subagent_prompts/{agent_name}.md` (referenced in config)

### Agent Configuration Structure

```yaml
subagents:
  architect:
    enabled: true
    prompt_template: subagent_prompts/architect.md
    checkpoint_artifacts:
      - architecture.md
      - technical_spec.md
      - data_models.md
  
  data:
    enabled: true
    prompt_template: subagent_prompts/data.md
    checkpoint_artifacts:
      - data/processed/**/*.csv
      - models/**/*
      - docs/data_documentation.md
    entrypoints:
      ingest: "python -m src.cli ingest"
      transform: "python -m src.cli transform"
      train: "python -m src.cli train"
      evaluate: "python -m src.cli evaluate"
```

### Executor Selection Logic

**LLM Agents** (Architect, Developer, QA, Documentarian, Consensus, Reviewer):
- Triggered when agent has NO `entrypoints` in config
- Execution methods:
  - **in-session (default):** Print instructions, exit(2) → Claude Code executes in current session
  - **API mode:** Direct Claude API call (requires ANTHROPIC_API_KEY)
  - **stub mode:** Simulated response (testing)

**Subprocess Agents** (Data, Steward):
- Triggered when agent has `entrypoints` in config
- Execution:
  - Load entrypoints (python -m commands)
  - Execute subprocess with timeout (default: 30 minutes)
  - Retry logic for transient errors
  - Track stdout/stderr and exit codes

---

## 2. PHASE WORKFLOW & ORCHESTRATION

### Standard Workflow Phases

**Location:** `.claude/config.yaml` → `workflow.phases`

```yaml
workflow:
  phases:
    - name: planning
      agents: [architect]
      requires_consensus: true
      artifacts_required: []
      
    - name: data_engineering
      agents: [data]
      requires_consensus: false
      optional: true
      artifacts_required:
        - data/processed/**/*.csv
        - models/metrics.json
      handoff_to: developer
      
    - name: development
      agents: [developer]
      requires_consensus: false
      
    - name: quality_assurance
      agents: [qa]
      requires_consensus: true
      
    - name: documentation
      agents: [documentarian]
      requires_consensus: false
      
    - name: review
      agents: [reviewer]
      requires_consensus: true
      optional: true
      
    - name: repo_hygiene
      agents: [steward]
      requires_consensus: true
      optional: true
```

### Phase Execution Flow

```
START_RUN(intake_path)
  ↓
INITIALIZE RunState:
  - run_id (timestamp-based)
  - status = RUNNING
  - current_phase = first_enabled_phase
  - Save to .claude/orchestrator_state.json
  ↓
NEXT_PHASE():
  ├─ RUN_PHASE(current_phase):
  │  ├─ For each agent in phase.agents:
  │  │  ├─ Build agent context (project_name, intake, last_artifacts)
  │  │  ├─ Load prompt template
  │  │  ├─ Interpolate variables ({{project_name}}, {{phase}}, etc.)
  │  │  ├─ Get executor (LLM or subprocess)
  │  │  └─ INVOKE_AGENT with retry logic
  │  │
  │  ├─ Validate artifacts (if artifacts_required defined):
  │  │  ├─ For each glob pattern, find matches
  │  │  ├─ Check file sizes > 0
  │  │  └─ Return ValidationResult (PASS|PARTIAL|FAIL)
  │  │
  │  └─ Generate PhaseOutcome
  │
  ├─ Check outcome:
  │  ├─ If requires_consensus = true:
  │  │  ├─ Generate .claude/consensus/REQUEST.md
  │  │  ├─ Set awaiting_consensus = true
  │  │  ├─ Return awaiting_consensus=true
  │  │  └─ PAUSE (awaiting approval)
  │  │
  │  ├─ If consensus approved OR requires_consensus = false:
  │  │  ├─ Add phase to completed_phases
  │  │  ├─ Store artifacts in phase_artifacts[phase_name]
  │  │  ├─ Move to next enabled phase
  │  │  └─ Continue or COMPLETE
  │  │
  │  └─ If phase failed:
  │     ├─ Set status = NEEDS_REVISION
  │     └─ Allow retry from current phase
  │
  └─ Save state after each transition
    
COMPLETE (when no next phase)
  ├─ Set status = COMPLETED
  └─ Save final state
```

### Phase State Transitions

```
[IDLE] 
  ↓ start_run()
[RUNNING] (Phase N)
  ├─ All agents succeed, no consensus → next phase
  ├─ Requires consensus, awaiting approval
  │  ├─ approve() → next phase
  │  └─ reject() → NEEDS_REVISION
  ├─ Agent/validation fails → NEEDS_REVISION
  └─ Optional phase → skip if not needed
  
[AWAITING_CONSENSUS]
  ├─ approve() → continue to next phase
  └─ reject(reason) → NEEDS_REVISION
  
[NEEDS_REVISION]
  └─ Retry current phase
  
[COMPLETED]
  └─ All phases finished (success or skipped)
```

### Phase Configuration Options

```yaml
phase:
  name: string                    # Phase identifier
  agents: [agent_name, ...]       # Agents in phase
  requires_consensus: bool        # Pause for approval?
  optional: bool                  # Can be skipped?
  enabled: bool                   # Is this phase active?
  parallel: bool                  # Run agents in parallel? (default: false)
  artifacts_required: [globs]     # Required checkpoint artifacts
  handoff_to: string              # Next phase (for optional routing)
```

---

## 3. CHECKPOINT SYSTEM

### Checkpoint Purpose & Design

**What:** Artifact validation at phase completion
- Validates that required outputs were produced
- Uses glob patterns to match files
- Generates validation reports
- Prevents advancing with incomplete work

**How:** Three validation statuses

| Status | Meaning | Behavior |
|--------|---------|----------|
| **PASS** | All patterns matched, files non-empty | Phase complete, may advance |
| **PARTIAL** | Some patterns matched | Phase incomplete, needs revision |
| **FAIL** | No patterns matched | Critical failure, must redo phase |

### Artifact Validation Process

**Location:** `src/orchestrator/checkpoints.py`

```python
def validate_artifacts(
    artifacts_required: List[str],      # ["src/**/*.py", "docs/**/*.md"]
    project_root: Path,
    phase_name: str
) -> ValidationResult:
    """
    For each glob pattern:
      1. Resolve glob (e.g., "src/**/*.py" → [src/main.py, src/utils.py])
      2. Check if files exist and are non-empty (size > 0)
      3. Record matching files in found_files list
    
    Determine status:
      - PASS: all patterns have at least one match
      - PARTIAL: some patterns matched, some didn't
      - FAIL: no patterns matched at all
    
    Generate validation report:
      - Location: reports/checkpoint_validation_{phase}.md
      - Contents: Status, required patterns, found files, missing patterns
    """
```

### Checkpoint Configuration

**From .claude/config.yaml:**

```yaml
checkpointPolicy:
  enabled: true
  storage_path: .claude/checkpoints/
  versioning: true
  retention_policy:
    keep_all_approved: true
    keep_last_n_rejected: 5
  
  validation:
    require_consensus_approval: true
    require_all_artifacts: true
    allow_partial_checkpoints: false
```

### Data Checkpoint Artifacts (Special Case)

**For data_engineering phase:** `.claude/checkpoints/DATA-CHECKLIST.md`

| Checkpoint | Artifacts | Validation |
|------------|-----------|-----------|
| **Post-Ingestion** | data/raw/\*.csv, ingestion log | row count > 0, columns present |
| **Post-Validation** | docs/data_documentation.md, quality report | validation rules pass |
| **Post-Transform** | data/interim/\*_cleaned.csv, data/processed/\*_features.csv | no nulls (expected), feature count matches |
| **Post-Training** | models/\*.pkl, models/\*_metadata.json | model loadable, can predict |
| **Post-Evaluation** | models/metrics.json | metrics exist, valid JSON, above threshold |
| **Full Pipeline** | All above + docs/data_documentation.md | Complete pipeline state captured |

### Artifact Tracking & Handoff

**State tracking in .claude/orchestrator_state.json:**

```json
{
  "phase_artifacts": {
    "planning": ["architecture.md", "technical_spec.md", "data_models.md"],
    "data_engineering": ["data/processed/train.csv", "models/model.pkl", "models/metrics.json"],
    "development": ["src/main.py", "src/utils.py", "implementation_notes.md"]
  }
}
```

**Handoff mechanism:**

```
Phase N completes
  ↓
Artifacts validated
  ↓
Matched files stored in state.phase_artifacts[phase_name]
  ↓
Phase N+1 executes
  ↓
build_agent_context() includes:
  - last_artifacts: {...all previous phases...}
  ↓
Agent prompt contains:
  "Previous artifacts from planning: architecture.md, technical_spec.md, ..."
  ↓
Agent reads context and uses previous outputs
```

---

## 4. STATE MANAGEMENT & PERSISTENCE

### State File Structure

**Location:** `.claude/orchestrator_state.json`

```json
{
  "run_id": "20251120_103000",
  "status": "running",
  "created_at": "2025-11-20T10:30:00Z",
  "updated_at": "2025-11-20T11:45:30Z",
  "current_phase": "development",
  "completed_phases": ["planning"],
  "phase_artifacts": {
    "planning": ["architecture.md", "technical_spec.md"]
  },
  "awaiting_consensus": false,
  "consensus_phase": null,
  "intake_path": "intake/myproject.yaml",
  "intake_summary": {
    "project_name": "MyApp",
    "project_type": "webapp",
    "description": "..."
  },
  "metadata": {},
  "errors": []
}
```

### RunState Data Class

**Location:** `src/orchestrator/types.py`

```python
@dataclass
class RunState:
    run_id: str                           # Unique identifier
    status: RunStatus                     # idle|running|awaiting_consensus|needs_revision|completed
    created_at: str                       # ISO timestamp
    updated_at: str                       # ISO timestamp
    current_phase: Optional[str]          # Currently executing phase
    completed_phases: List[str]           # Phases finished successfully
    phase_artifacts: Dict[str, List[str]]# {phase: [artifact_paths]}
    awaiting_consensus: bool              # Paused for approval?
    consensus_phase: Optional[str]        # Which phase awaiting consensus?
    intake_path: Optional[str]            # Path to intake YAML
    intake_summary: Optional[Dict]        # Parsed intake data
    metadata: Dict[str, Any]              # Custom metadata
    errors: List[str]                     # Accumulated errors
```

### State Persistence Hooks

**Save state after:**
1. `start_run()` - Initialize new run
2. Each phase completion/transition
3. Consensus approval/rejection
4. Phase failure (error state)

**Implementation in runloop.py:**

```python
def _save_state(self) -> None:
    """Save orchestrator state to .claude/orchestrator_state.json."""
    state_path = self._get_state_path()
    state_path.parent.mkdir(parents=True, exist_ok=True)
    
    self.state.updated_at = datetime.now().isoformat()
    
    with open(state_path, "w") as f:
        json.dump(self.state.to_dict(), f, indent=2)
```

### Consensus & Approval Mechanism

**Consensus Request Generation:**

**Location:** `src/orchestrator/runloop.py` → `_generate_consensus_request()`

When `phase.requires_consensus = true`:

1. Phase completes (all agents successful, artifacts validated)
2. Orchestrator generates `.claude/consensus/REQUEST.md`
3. Includes:
   - Status ribbon (🟢 READY FOR REVIEW or 🔴 NEEDS ATTENTION)
   - Agent execution results
   - Validation status
   - Metrics digest
   - Recommended actions
4. State: `awaiting_consensus = true`, `consensus_phase = phase_name`
5. Workflow pauses until approval

**Approval Options:**

```bash
orchestrator run approve          # Accept phase, proceed to next
orchestrator run reject --reason "Comments"  # Reject phase, go to NEEDS_REVISION
```

---

## 5. EXECUTION PATTERNS & ARCHITECTURE

### Executor Pattern (Strategy)

**File:** `src/orchestrator/executors/`

**Selection Logic:**

```python
def get_executor(agent_name, agent_config):
    if agent_config.get("entrypoints"):
        # Has entrypoints → subprocess executor
        return subprocess_executor(entrypoints)
    else:
        # No entrypoints → LLM executor
        return llm_executor(agent_name)
```

### LLM Agent Execution Flow

```
1. Load agent prompt template
   └─ Location: subagent_prompts/{agent_name}.md

2. Build context
   ├─ project_name (from intake)
   ├─ phase (current phase name)
   ├─ last_artifacts (previous phase outputs)
   ├─ intake_summary (project requirements)
   └─ entrypoints (subprocess commands if any)

3. Interpolate prompt
   └─ Replace {{variable}} with context values

4. Get executor
   └─ Check execution_mode: in_session|api|stub

5. In-session mode:
   ├─ Print agent instructions to console
   ├─ Exit with code 2 (awaiting work)
   └─ Orchestrator pauses

6. API mode (requires ANTHROPIC_API_KEY):
   ├─ Call Claude API directly
   ├─ Get response
   └─ Parse artifacts from response

7. Stub mode (testing):
   └─ Return simulated response

8. Record outcome
   ├─ artifacts: [files created/modified]
   ├─ notes: execution summary
   └─ errors: any failures
```

### Subprocess Agent Execution Flow

```
1. Get entrypoints from config
   └─ Example: "python -m src.cli ingest"

2. Execute subprocess
   ├─ Set timeout (default: 30 minutes)
   ├─ Capture stdout/stderr
   ├─ Track exit code
   └─ Apply retry logic

3. Retry logic (if enabled):
   ├─ Retryable codes: 75, 101, 111, 125
   ├─ Retryable messages: "rate limit", "transient network"
   ├─ Exponential backoff: 0.7s → 1.4s → 2.8s
   ├─ Jitter: ±25% random variance
   └─ Max retries: 2 (configurable)

4. Return result
   ├─ stdout/stderr (full output)
   ├─ exit_code (0 = success)
   ├─ artifacts: [files created]
   └─ duration_s: execution time
```

### Parallel vs Sequential Execution

**Configuration:**

```yaml
orchestrator:
  max_parallel_agents: 2  # Concurrency limit (1 = sequential)

workflow:
  phases:
    - name: planning
      agents: [architect]
      parallel: false  # Force sequential
    
    - name: development
      agents: [developer]
      # parallel defaults to false (sequential)
```

**Sequential (Default):**

```python
agent_outcomes = []
for agent_name in agent_names:
    outcome = invoke_agent(agent_name, phase_name)
    agent_outcomes.append(outcome)
    if not outcome.success:
        break  # Stop early on failure
```

**Parallel (When enabled):**

```python
async def _run_agents_parallel(agent_names, max_workers=2):
    semaphore = asyncio.Semaphore(max_workers)
    
    async def run_with_limit(agent):
        async with semaphore:
            return await invoke_agent(agent, phase_name)
    
    tasks = [run_with_limit(a) for a in agent_names]
    outcomes = await asyncio.gather(*tasks, return_exceptions=True)
    return outcomes
```

### Retry & Timeout Configuration

**From .claude/config.yaml:**

```yaml
orchestrator:
  timeout_minutes: 30
  retry:
    retries: 2
    backoff: 2.0  # Exponential multiplier
    jitter: 0.25  # ±25% random variance
    retryable_exit_codes: [75, 101]
    retryable_messages:
      - "rate limit"
      - "transient network"
```

---

## 6. KEY CONFIGURATION FILES

### .claude/config.yaml

**Main orchestrator configuration**

Key sections:
- `orchestrator`: Run-loop settings, execution mode, timeouts
- `subagents`: Agent definitions and checkpoint artifacts
- `workflow.phases`: Phase definitions and transitions
- `checkpointPolicy`: Validation rules and artifact retention
- `integrations`: Git, notifications, handoff settings

### .claude/agents/*.md

**Individual agent role definitions** (reference documents)

- architect.md
- developer.md
- qa.md
- documentarian.md
- consensus.md
- reviewer.md
- steward.md

### subagent_prompts/*.md

**Prompt templates for LLM agents**

Each template:
- Defines agent role and responsibilities
- Lists inputs and outputs
- Specifies checkpoint artifacts
- Includes success criteria
- Has interpolation variables: {{project_name}}, {{phase}}, {{last_artifacts}}, etc.

### .claude/orchestrator_state.json

**Persistent run state** (auto-generated)

Updated after each phase transition, contains:
- Run ID and status
- Current/completed phases
- Phase artifacts
- Consensus state
- Intake data
- Errors

---

## 7. ARTIFACT FLOW & HANDOFF MECHANISM

### Context Building for Handoff

**Function:** `src/orchestrator/prompt_loader.py::build_agent_context()`

```python
def build_agent_context(
    project_root: Path,
    phase: str,
    agent: str,
    intake_summary: Dict,
    last_artifacts: Dict,  # phase_artifacts from state
    entrypoints: Dict,
) -> Dict[str, Any]:
    return {
        "project_name": intake_summary["project_name"],
        "phase": phase,
        "agent": agent,
        "last_artifacts": _format_artifacts(last_artifacts),
        "intake_summary": _format_intake(intake_summary),
        "entrypoints": _format_entrypoints(entrypoints),
    }
```

### Prompt Interpolation

**Template variables (simple {{}} syntax):**

```markdown
# {{agent}} Agent Instructions

## Project Context
- Project: {{project_name}}
- Phase: {{phase}}

## Previous Artifacts
{{last_artifacts}}

## Requirements
{{intake_summary}}

## Available Entrypoints
{{entrypoints}}

## Checkpoint Artifacts
{{checkpoint_artifacts}}
```

### Artifact Tracking Across Phases

```
Phase 1: Planning
  Artifacts produced: architecture.md, technical_spec.md
  ↓
  state.phase_artifacts["planning"] = [
    "architecture.md",
    "technical_spec.md"
  ]
  ↓
Phase 2: Development
  Context includes: "Previous artifacts from planning: architecture.md, ..."
  Developer reads architecture docs from Phase 1
  Creates implementation code
  ↓
  state.phase_artifacts["development"] = [
    "src/main.py",
    "src/utils.py",
    "implementation_notes.md"
  ]
  ↓
Phase 3: QA
  Context includes: "Artifacts from planning: architecture.md, ..."
  Context includes: "Artifacts from development: src/main.py, ..."
  QA writes tests and validates implementations
```

---

## 8. TECHNICAL STACK & FILE STRUCTURE

### Core Dependencies

- **Python 3.9+**
- **Typer**: CLI framework
- **Rich**: Terminal formatting
- **PyYAML**: Configuration loading
- **Anthropic SDK**: Claude API (optional, for API mode)
- **asyncio**: Async agent execution
- **jsonschema**: Configuration validation

### Project Structure

```
src/
├── orchestrator/
│   ├── __main__.py           # Entry point
│   ├── cli.py                # Typer CLI app
│   ├── runloop.py            # Core Orchestrator class
│   ├── state.py              # State persistence
│   ├── types.py              # Data classes (RunState, PhaseOutcome, etc.)
│   ├── checkpoints.py        # Artifact validation
│   ├── prompt_loader.py      # Template loading & interpolation
│   ├── executors/
│   │   ├── types.py          # AgentExecResult dataclass
│   │   ├── llm_exec.py       # LLM executor (Claude API)
│   │   └── subprocess_exec.py # Subprocess executor
│   ├── commands/
│   │   ├── bootstrap.py      # Quickstart command
│   │   └── checkpoint.py     # Checkpoint validation
│   ├── reliability.py        # Retry & timeout logic
│   └── ...
│
.claude/
├── config.yaml               # Main configuration
├── orchestrator_state.json   # Current run state
├── agents/                   # Agent definitions
│   ├── architect.md
│   ├── developer.md
│   ├── qa.md
│   ├── documentarian.md
│   ├── consensus.md
│   ├── reviewer.md
│   └── steward.md
├── checkpoints/
│   ├── DATA-CHECKLIST.md
│   └── [phase_name]_[timestamp].zip  # Checkpoint archives
├── consensus/
│   └── REQUEST.md            # Consensus approval request
├── logs/
│   └── run_[run_id].log      # Run execution log
└── ...
```

---

## 9. SKILLS & KNOWLEDGE SYSTEMS

### Skills Framework

**Location:** `.claude/skills/`

**Philosophy:** Reusable analytical patterns, not domain-specific solutions

**Available Skills:**

1. **time_series_analytics.yaml**
   - Forecasting: ARIMA, Prophet, LSTM
   - Anomaly detection, seasonal decomposition
   - Multi-horizon forecasting with uncertainty

2. **survey_data_processing.yaml**
   - Data cleaning & entity resolution
   - Fuzzy matching, sentiment analysis
   - Categorical analysis, survey weighting

3. **optimization_modeling.yaml**
   - Linear/integer programming
   - Network optimization, routing
   - Assignment, scheduling, portfolio optimization

**How agents use skills:**
1. Identify applicable skills for phase
2. Load skill YAML for methodology
3. Adapt to project-specific context
4. Document decisions in ADRs

### Knowledge Base

**Location:** `.claude/knowledge/`

**Hierarchy:**
1. **Project-specific** (most relevant)
2. **Firm-wide** (Kearney standards, RAISE framework)
3. **Universal** (data science fundamentals)

**Structure:**
- `analytics_best_practices.yaml` - Data quality standards
- `kearney_standards.yaml` - Firm conventions
- `projects/[project].yaml` - Domain-specific rules

---

## 10. GOVERNANCE & COMPLIANCE

### Client Governance (Optional)

**Location:** `clients/{client_name}/governance.yaml`

**Enforces:**
- Quality gates (test coverage, security scans)
- Compliance rules (GDPR, HIPAA, SOC2)
- Brand constraints (colors, fonts, terminology)
- Deployment policies

**Hierarchy:**
```
Client Governance > Kearney Default > Hardcoded Minimums
```

### Repository Hygiene

**Steward Agent** maintains:
- No large binary files (> 1MB) in version control
- No notebook outputs
- No raw data files (data/raw/)
- No model artifacts unless whitelisted
- No secrets (.env, credentials.json)

**Tools:**
- `src/steward/scanner.py` - Orphan/large file detection
- `src/steward/dead_code.py` - Unused code analysis
- `src/steward/notebooks.py` - Notebook output detection
- `.tidyignore` - Whitelist exemptions

---

## 11. EXECUTION MODES SUMMARY

| Mode | Execution | Use Case | Requirements |
|------|-----------|----------|--------------|
| **in-session** | Print instructions, pause | Interactive development | None |
| **API** | Direct Claude API calls | Automated CI/CD pipelines | ANTHROPIC_API_KEY env var |
| **stub** | Simulated responses | Testing workflow logic | None |

**Set via:**
- `.claude/config.yaml` → `orchestrator.execution_mode`
- Environment: `ORCHESTRATOR_EXECUTION_MODE=api`

---

## 12. ERROR HANDLING & RECOVERY

### Phase Failure Handling

```
Phase execution fails
  ↓
status = NEEDS_REVISION
  ↓
Agent outcome recorded with errors
  ↓
User reviews error logs
  ↓
User retries: orchestrator run next
  ↓
Same phase re-executes from beginning
```

### Transient Error Retry

```
Agent execution fails with error
  ↓
Check if retryable:
  - Exit code in [75, 101, 111, 125]?
  - Error message contains "rate limit" or "transient"?
  ↓
If retryable:
  - Wait: backoff_delay
  - Retry with exponential backoff
  - Jitter added for concurrency safety
  ↓
If max retries exceeded or not retryable:
  - Mark as failure
  - Return error to orchestrator
```

---

## 13. KEY CONCEPTS REFERENCE

| Concept | Purpose | Implementation |
|---------|---------|-----------------|
| **Run** | Single workflow execution | RunState + run_id (timestamp) |
| **Phase** | Sequential milestone | Named workflow stage with agents |
| **Agent** | Specialized executor | LLM or subprocess process |
| **Checkpoint** | Artifact validation | Glob matching + validation reports |
| **Consensus** | Human approval gate | REQUEST.md file + CLI approval |
| **Handoff** | Context passing | State artifacts + prompt interpolation |
| **State** | Persistent progress | JSON file + in-memory RunState |
| **Executor** | Runtime dispatch | Strategy pattern selection |

---

## 14. CURRENT LIMITATIONS & DESIGN DECISIONS

### As Implemented

✅ **Sequential phase execution** (no concurrent phases)
✅ **Stateful run tracking** (JSON-based persistence)
✅ **Glob-based artifact validation** (file pattern matching)
✅ **In-session mode** (human-guided orchestration default)
✅ **Consensus gates** (approval requests before advancing)
✅ **Subprocess & LLM agents** (dual execution modes)

### Notable Design Choices

1. **In-session execution by default** - Orchestrator prints instructions, waits for human action
2. **Sequential agents within phase** - No concurrent agent execution within a phase
3. **Simple glob matching** - No complex artifact dependencies
4. **JSON state files** - Human-readable, version control friendly
5. **Prompt interpolation** - {{}} template syntax, simple variable substitution
6. **Artifact tracking** - Phase-level granularity, not per-agent

---

## END OF ANALYSIS

**Total Lines of Code (Core):** ~2,500 (src/orchestrator/)
**Configuration Files:** 3 (config.yaml, agent definitions, state file)
**Agent Types:** 8 defined + extensible
**Phases Supported:** 7 standard + custom phases
**Execution Patterns:** 3 (in-session, API, stub)

