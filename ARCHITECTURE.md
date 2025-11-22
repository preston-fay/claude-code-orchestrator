# Claude Code Orchestrator - Core Architecture Overview

## Executive Summary

The Claude Code Orchestrator is a meta-framework that coordinates multiple specialized AI agents (subagents) to collaboratively build complex software projects through a structured, checkpoint-driven workflow. It uses a stateful run-loop architecture with consensus-based phase transitions and artifact validation.

**Key Components:**
- 8 Specialized subagents (Architect, Developer, QA, Data, Documentarian, Consensus, Reviewer, Steward)
- Phase-based workflow engine with checkpoint validation
- Dual execution modes: in-session guided (default) + API-based (automated)
- State persistence with JSON-based run tracking
- Parallel/sequential agent execution with retry logic
- Governance and quality gate enforcement

---

## Architecture Layers

```
┌─────────────────────────────────────────────────────────┐
│              CLI/Command Interface Layer                 │
│              (src/orchestrator/cli.py)                   │
└────────────────────┬────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────┐
│          Orchestrator Run-Loop Engine                    │
│          (src/orchestrator/runloop.py)                   │
│     - Phase execution & transitions                      │
│     - Agent invocation & coordination                    │
│     - Consensus request generation                       │
└────────────────────┬────────────────────────────────────┘
                     │
        ┌────────────┼────────────┐
        │            │            │
   ┌────▼─┐   ┌─────▼────┐   ┌──▼─────┐
   │State │   │Checkpoint│   │Executor│
   │Mgmt  │   │Validation│   │ Layer  │
   └──────┘   └──────────┘   └────────┘
        │            │            │
        └────────────┼────────────┘
                     │
     ┌───────────────┼───────────────┐
     │               │               │
┌────▼─┐    ┌────────▼─────┐   ┌───▼──────┐
│Agent │    │  Prompt      │   │ Executor │
│Config│    │  Loader      │   │ Selector │
└──────┘    └──────────────┘   └──────────┘
```

---

## 1. Main Entry Points & Invocation

### CLI Entry Point
**File:** `src/orchestrator/__main__.py` → `src/orchestrator/cli.py`

```python
# Entry point
from src.orchestrator.cli import app
app()  # Typer-based CLI application
```

### Main Commands

**Orchestrator Control:**
```bash
orchestrator run start [--intake <file>]     # Initialize workflow
orchestrator run next                        # Execute current phase
orchestrator run status                      # Show run status
orchestrator run approve/reject              # Consensus decisions
orchestrator run checkpoint [--force]        # In-session checkpoint
```

**Project Lifecycle:**
```bash
orchestrator quickstart --type webapp --name myapp  # Bootstrap project
orchestrator run repo-hygiene                       # Repository hygiene check
orchestrator release prepare/cut/verify             # Release management
```

**Data & Governance:**
```bash
orchestrator data ingest/transform/train/evaluate   # Data pipeline
orchestrator gov profile --all                      # Governance profiling
orchestrator registry model-publish                 # Model registry
```

### Execution Modes

1. **In-Session (Default)**
   - Orchestrator prints agent instructions and pauses (exit_code=2)
   - Claude Code executes work in current session
   - User runs `orchestrator run checkpoint` to validate and advance
   - Used for interactive development workflows

2. **API Mode** (When `ANTHROPIC_API_KEY` is available)
   - Real Claude API calls for agent execution
   - Fully automated, no human interaction required
   - Used in CI/CD pipelines and release automation

3. **Stub Mode** (Testing/Offline)
   - Simulated agent responses
   - Tests workflow logic without actual execution

---

## 2. Core Module Architecture

### 2.1 State Management (`src/orchestrator/state.py`)

**Purpose:** Persistent workflow state tracking

**Key Components:**
- `RunState` dataclass - Complete run state (JSON-serializable)
- `OrchestratorState` - Low-level state file management (legacy)
- State file: `.claude/orchestrator_state.json`

**State Fields:**
```python
@dataclass
class RunState:
    run_id: str                      # Unique run identifier (timestamp-based)
    status: RunStatus                # idle | running | awaiting_consensus | needs_revision | completed
    created_at: str                  # ISO timestamp
    current_phase: Optional[str]     # Currently executing phase
    completed_phases: List[str]      # Phases finished successfully
    phase_artifacts: Dict[str, List[str]]  # Artifacts per phase
    awaiting_consensus: bool         # True if phase requires approval
    consensus_phase: Optional[str]   # Phase awaiting consensus
    intake_path: Optional[str]       # Original intake YAML path
    intake_summary: Optional[Dict]   # Parsed intake data
    metadata: Dict[str, Any]         # Custom metadata
    errors: List[str]                # Accumulated errors
```

**Transitions:**
```
IDLE → RUNNING → [AWAITING_CONSENSUS ↔ RUNNING] → COMPLETED
           ↓
      NEEDS_REVISION (phase rejection)
           ↓
      RUNNING (resume)
```

### 2.2 Run-Loop Engine (`src/orchestrator/runloop.py`)

**Purpose:** Core orchestration logic - phase execution and coordination

**Key Classes:**
- `Orchestrator` - Main engine controlling the workflow

**Core Methods:**

```python
class Orchestrator:
    def __init__(project_root: Optional[Path] = None)
    
    # Workflow control
    def start_run(intake_path, from_phase)          # Initialize run
    def next_phase() -> PhaseOutcome                 # Execute current phase
    def run_phase(phase_name) -> PhaseOutcome        # Execute single phase
    def approve_consensus()                          # Approve phase consensus
    def reject_consensus(reason)                     # Reject phase with reason
    def abort_run()                                  # Stop workflow
    def resume_run()                                 # Resume aborted run
    def jump_to_phase(phase)                         # Admin: skip phases
    
    # Agent invocation (async)
    def invoke_agent(agent, phase) -> AgentOutcome   # Single agent
    async def _invoke_agent_async(...)               # Actual invocation
    async def _run_agents_parallel(...)              # Parallel execution
```

**Execution Flow:**

```
next_phase() called
    ↓
run_phase(current_phase)
    ↓
    ├─ For each agent in phase.agents:
    │   ├─ build_agent_context()
    │   ├─ load_and_interpolate_prompt()
    │   ├─ get_executor() → subprocess or LLM
    │   └─ invoke_agent() with retry logic
    │
    ├─ validate_artifacts() (if required)
    │
    └─ If requires_consensus:
       └─ _generate_consensus_request()
            ├─ Package artifacts
            └─ Write .claude/consensus/REQUEST.md

Check outcome:
    ├─ If awaiting_consensus:
    │   └─ status = AWAITING_CONSENSUS
    ├─ If success:
    │   ├─ Add to completed_phases
    │   └─ Move to next phase
    └─ If failure:
        └─ status = NEEDS_REVISION
```

### 2.3 Type System (`src/orchestrator/types.py`)

**Data Flow Types:**

```python
# Phase execution outcome
@dataclass
class PhaseOutcome:
    phase_name: str
    success: bool
    agent_outcomes: List[AgentOutcome]
    validation: Optional[ValidationResult]
    requires_consensus: bool
    awaiting_consensus: bool
    completed_at: Optional[str]
    notes: str

# Single agent execution
@dataclass
class AgentOutcome:
    agent_name: str
    success: bool
    artifacts: List[str]           # Files created/modified
    notes: str                      # Execution notes (first 500 chars)
    errors: List[str]
    exit_code: Optional[int]
    execution_time: Optional[float]

# Checkpoint validation result
@dataclass
class ValidationResult:
    status: ValidationStatus        # pass | partial | fail
    required: List[str]             # Required glob patterns
    found: List[str]                # Matched file paths
    missing: List[str]              # Unmatched patterns
    validation_report_path: Optional[str]
    notes: str
```

### 2.4 Checkpoint System (`src/orchestrator/checkpoints.py`)

**Purpose:** Artifact validation and workflow safety

**Validation Logic:**

```python
def validate_artifacts(
    artifacts_required: List[str],   # Glob patterns: "src/**/*.py"
    project_root: Path,
    phase_name: str
) -> ValidationResult:
    
    # For each pattern:
    #   1. Resolve glob matches
    #   2. Check files are non-empty
    #   3. Record found files
    
    # Status determination:
    #   - PASS: all patterns matched
    #   - PARTIAL: some patterns matched
    #   - FAIL: no patterns matched
```

**Checkpoint Artifacts Configuration** (`.claude/config.yaml`):

```yaml
subagents:
  architect:
    checkpoint_artifacts:
      - architecture.md
      - technical_spec.md
      - data_models.md
  developer:
    checkpoint_artifacts:
      - src/**/*
      - implementation_notes.md
```

**Report Generation:**
- Location: `reports/checkpoint_validation_{phase}.md`
- Contains: Status, required patterns, found files, missing patterns

---

## 3. Subagent Coordination

### 3.1 Subagent Architecture

**8 Specialized Agents:**

| Agent | Role | Mode | Artifacts |
|-------|------|------|-----------|
| **Architect** | System design, tech spec | LLM | architecture.md, technical_spec.md |
| **Developer** | Implementation | LLM | src/**, implementation_notes.md |
| **QA** | Testing, validation | LLM | test_plan.md, test_results.md, qa_report.md |
| **Data** | ETL, analytics, ML | Subprocess | data/processed/**, models/**, docs/data_documentation.md |
| **Documentarian** | Docs, guides, API refs | LLM | README.md, USER_GUIDE.md, docs/** |
| **Consensus** | Conflict resolution | LLM | consensus_decisions.md |
| **Reviewer** | Code review | LLM | code_review.md, improvements.md |
| **Steward** | Repo hygiene, cleanup | Subprocess | reports/repo_hygiene_report.md, reports/PR_PLAN.md |

### 3.2 Agent Invocation Model

**Executor Selection (Smart Dispatch):**

```python
def get_executor(agent_name, agent_config):
    """Choose executor based on agent type"""
    if agent_config.get("entrypoints"):
        # Has entrypoints → subprocess (Data, Steward)
        return subprocess_executor(entrypoints)
    else:
        # No entrypoints → LLM (Architect, Developer, QA, etc.)
        return llm_executor(agent_name)
```

**LLM Agent Execution Flow:**

```
1. Load prompt template: subagent_prompts/{agent}.md
2. Build context (intake, artifacts, entrypoints)
3. Interpolate: {{project_name}}, {{last_artifacts}}, etc.
4. Execute via LLM executor:
   - In-session: Print instructions, exit(2)
   - API mode: Call Claude API
   - Stub mode: Simulate response
5. Parse artifacts from response
6. Write transcripts: .claude/logs/agents/{run_id}_{phase}_{agent}.log
```

**Subprocess Agent Execution Flow:**

```
1. Get entrypoints: python -m src.cli ingest, etc.
2. Execute subprocess:
   - Capture stdout/stderr
   - Track exit code
   - Apply timeout (30 min default)
3. Retry logic:
   - Retryable codes: 75, 101 (rate limit, transient)
   - Exponential backoff with jitter
4. Return AgentExecResult
```

### 3.3 Parallel vs Sequential Execution

**Configuration:**
```yaml
workflow:
  phases:
    - name: planning
      agents: [architect]
      parallel: false           # Sequential (default)
    
    - name: development
      agents: [developer]       # Single agent
      
    - name: quality_assurance
      agents: [qa]
      parallel: false
```

**Parallel Execution (if enabled):**

```python
async def _run_agents_parallel(agent_names, phase_name, max_workers=2):
    """Execute agents concurrently with semaphore limit"""
    semaphore = asyncio.Semaphore(max_workers)  # Concurrency cap
    tasks = [
        semaphore_wrapped_invoke(agent)
        for agent in agent_names
    ]
    outcomes = await asyncio.gather(*tasks, return_exceptions=True)
    return outcomes
```

**Sequential Execution (default):**
```python
agent_outcomes = []
for agent_name in agent_names:
    outcome = invoke_agent(agent_name, phase_name)
    agent_outcomes.append(outcome)
    if not outcome.success:
        # Can stop early on failure
        break
```

---

## 4. Workflow & Phase Management System

### 4.1 Phase Definition

**Structure** (`.claude/config.yaml`):

```yaml
workflow:
  phases:
    - name: planning
      agents: [architect]
      requires_consensus: true        # Needs manual approval
      artifacts_required: []
      handoff_to: development
      optional: false
      enabled: true
    
    - name: development
      agents: [developer]
      requires_consensus: false
      artifacts_required:
        - src/**/*.py
        - implementation_notes.md
      enabled: true
    
    - name: data_engineering
      agents: [data]
      optional: true                  # Can be skipped
      artifacts_required:
        - data/processed/**/*.csv
        - models/metrics.json
```

### 4.2 Phase Transitions

**State Machine:**

```
[IDLE] → start_run() → [First Enabled Phase]
   ↓
[RUNNING Phase N]
   ↓
   ├─ Agent execution (parallel/sequential)
   ├─ Artifact validation
   ├─ Consensus generation (if required)
   └─ Outcome determination
   ↓
   ├─ Success → next_phase() → Phase N+1
   ├─ Needs Consensus → AWAITING_CONSENSUS
   │  └─ approve() → Phase N+1
   │  └─ reject() → NEEDS_REVISION
   └─ Failure → NEEDS_REVISION
   ↓
[COMPLETED] (when no next phase)
```

**Configuration:**
```yaml
workflow:
  transitions:
    auto_advance: false              # Explicit "run next" required
    rollback_enabled: true
    max_iterations: 3                # Max retries per phase
```

### 4.3 Consensus & Approval Mechanism

**Consensus Request Generation:**

```python
def _generate_consensus_request(phase_name, agent_outcomes, validation):
    """Create .claude/consensus/REQUEST.md for human review"""
    
    # Status ribbon
    if all_agents_success and validation_ok:
        ribbon = "🟢 STATUS: READY FOR REVIEW"
    else:
        ribbon = "🔴 STATUS: NEEDS ATTENTION"
    
    # Package artifacts
    zip_path = package_phase_artifacts(artifacts, run_id)
    
    # Write comprehensive request with:
    # - Agent outcomes
    # - Validation results
    # - Metrics digest
    # - Recommended actions
```

**Approval Flow:**

```
1. Phase completes with requires_consensus: true
2. Orchestrator generates .claude/consensus/REQUEST.md
3. User reviews the request
4. User runs: orchestrator run approve
   OR: orchestrator run reject --reason "..."
5. State transitions to next phase or NEEDS_REVISION
```

**Consensus Request Structure:**

```markdown
🟢 STATUS: READY FOR REVIEW

# Consensus Request: planning

**Requested:** 2025-11-20T10:30:00

| Metric | Value |
|--------|-------|
| Phase | planning |
| Agents | 1 |
| Status | ✅ All succeeded |

## Agent Results
- ✅ Architect (123.4s)
  - artifacts: 3 files
  
## Validation
- ✅ PASS (3/3 artifacts found)

## Checkpoint Package
- Archive: .claude/checkpoints/planning_20251120_103000.zip
```

---

## 5. State Management & Handoff Mechanisms

### 5.1 State Persistence

**State File Structure:**
```
.claude/orchestrator_state.json
```

```json
{
  "run_id": "20251120_103000",
  "status": "running",
  "created_at": "2025-11-20T10:30:00",
  "updated_at": "2025-11-20T11:45:30",
  "current_phase": "development",
  "completed_phases": ["planning"],
  "phase_artifacts": {
    "planning": [
      "architecture.md",
      "technical_spec.md"
    ]
  },
  "awaiting_consensus": false,
  "intake_path": "intake/myproject.yaml",
  "intake_summary": {
    "project_name": "MyApp",
    "project_type": "webapp",
    "description": "..."
  }
}
```

**Persistence Hooks:**
```python
def _save_state():
    """Write state to disk after each change"""
    state.updated_at = datetime.now()
    with open(state_path, 'w') as f:
        json.dump(state.to_dict(), f, indent=2)

def start_run(intake_path):
    self.state = RunState(...)
    self._save_state()

def next_phase():
    outcome = run_phase(...)
    self._save_state()  # After every phase
```

### 5.2 Agent Context & Handoff

**Context Building:**

```python
def build_agent_context(
    project_root: Path,
    phase: str,
    agent: str,
    intake_summary: Dict,
    last_artifacts: Dict,
    entrypoints: Dict,
) -> Dict[str, Any]:
    """Build interpolation context for agent prompt"""
    
    return {
        "project_name": intake_summary["project_name"],
        "phase": phase,
        "agent": agent,
        "last_artifacts": _format_artifacts(last_artifacts),
        "intake_summary": _format_intake(intake_summary),
        "entrypoints": _format_entrypoints(entrypoints),
    }
```

**Prompt Interpolation:**

```python
def interpolate_prompt(template: str, context: Dict) -> str:
    """Replace {{variable}} placeholders in prompt"""
    
    # Template: "Previous artifacts:\n{{last_artifacts}}"
    # Context: {"last_artifacts": "planning: architecture.md, ..."}
    # Result:  "Previous artifacts:\nplanning: architecture.md, ..."
```

**Prompt Template Structure:**
```
subagent_prompts/{agent_name}.md

---

## Role
You are the {{agent}} agent...

## Context
Project: {{project_name}}
Phase: {{phase}}
Previous Artifacts: {{last_artifacts}}

## Entrypoints
{{entrypoints}}

## Task
[Specific instructions for this phase]

## Checkpoint
Required artifacts:
- {{checkpoint_artifacts}}

## Success Criteria
[Definition of done]
```

### 5.3 Artifact Tracking

**Artifact Recording:**
```python
if outcome.success:
    state.completed_phases.append(phase_name)
    
    # Store artifacts found during validation
    if outcome.validation and outcome.validation.found:
        state.phase_artifacts[phase_name] = outcome.validation.found
    
    state._save_state()
```

**Artifact Passing Between Phases:**

```
Phase N executes
    ↓
Artifacts created/modified
    ↓
validate_artifacts() scans for matches
    ↓
Matched files stored in state.phase_artifacts[phase_name]
    ↓
Phase N+1 executes
    ↓
build_agent_context() includes:
  last_artifacts: state.phase_artifacts  # All previous phases
    ↓
Agent prompt contains:
  "Previous artifacts from planning: architecture.md, ..."
```

---

## 6. Key Design Patterns

### 6.1 Executor Pattern (Strategy)

**Problem:** Different agents execute differently

**Solution:** Runtime selection of executor

```python
# Subprocess-based (Data, Steward)
executor = subprocess_executor(entrypoints)
result = await executor(command, timeout)

# LLM-based (Architect, Developer, QA, etc.)
executor = llm_executor(agent_name)
result = await executor(prompt, phase, project_root, timeout)
```

### 6.2 Consensus Gate Pattern

**Problem:** Workflow needs human validation at critical points

**Solution:** Pause at checkpoints, generate approval requests

```python
if phase_config.requires_consensus:
    _generate_consensus_request(phase, outcomes, validation)
    state.awaiting_consensus = True
    return PhaseOutcome(..., awaiting_consensus=True)
```

### 6.3 Checkpoint Validation Pattern

**Problem:** Need to verify work completed before advancing

**Solution:** Glob-based artifact matching with status levels

```python
validation = validate_artifacts(
    ["src/**/*.py", "README.md"],
    project_root,
    phase_name
)
# Returns: PASS | PARTIAL | FAIL
```

### 6.4 Retry with Backoff Pattern

**Problem:** Transient failures (API rate limits, network)

**Solution:** Exponential backoff with jitter

```python
retry_config = RetryConfig(
    retries=2,
    base_delay=0.7,
    backoff=2.0,  # 0.7s → 1.4s → 2.8s
    jitter=0.25,   # ±25% random variance
    retryable_exit_codes=[75, 101],
)

result = await retry_async(
    execute_agent,
    config=retry_config,
    is_retryable=lambda e, _: is_transient_error(e)
)
```

### 6.5 Async Semaphore Pattern (Concurrency Control)

**Problem:** Parallel execution needs bounded concurrency

**Solution:** Asyncio semaphore limits concurrent agents

```python
semaphore = asyncio.Semaphore(max_workers=2)

async def run_with_limit(agent):
    async with semaphore:
        return await invoke_agent(agent)

tasks = [run_with_limit(a) for a in agents]
results = await asyncio.gather(*tasks)
```

### 6.6 Prompt Interpolation Pattern

**Problem:** Agent prompts need dynamic context

**Solution:** Template variables with simple {{}} syntax

```python
template = "Project: {{project_name}}, Phase: {{phase}}"
context = {"project_name": "MyApp", "phase": "development"}
prompt = interpolate_prompt(template, context)
# Result: "Project: MyApp, Phase: development"
```

---

## 7. Configuration Hierarchy

### 7.1 Main Config File

**Location:** `.claude/config.yaml`

**Key Sections:**

```yaml
# Orchestrator settings
orchestrator:
  state_file: .claude/orchestrator_state.json
  max_parallel_agents: 2
  timeout_minutes: 30
  execution_mode: in_session | api | stub
  retry:
    retries: 2
    base_delay: 0.7
    backoff: 2.0
    retryable_exit_codes: [75, 101]

# Subagent definitions
subagents:
  architect:
    enabled: true
    prompt_template: subagent_prompts/architect.md
    checkpoint_artifacts: [architecture.md, ...]
  data:
    enabled: true
    entrypoints:
      ingest: "python -m src.cli ingest"
      transform: "python -m src.cli transform"

# Workflow phases
workflow:
  phases:
    - name: planning
      agents: [architect]
      requires_consensus: true
      artifacts_required: []
    - name: development
      agents: [developer]
      requires_consensus: false
      artifacts_required: [src/**/*]
  
  transitions:
    auto_advance: false
    rollback_enabled: true
```

### 7.2 Client Governance (Optional)

**Location:** `clients/{client-name}/governance.yaml`

Enforces client-specific:
- Quality gates (test coverage, security scans)
- Compliance rules (GDPR, HIPAA, SOC2)
- Brand constraints (colors, fonts, terminology)
- Deployment policies

---

## 8. Execution Flow - Complete Example

### Scenario: "New Project" Quickstart

```
1. User runs: orchestrator quickstart --type webapp --name myapp
   ↓
2. CLI generates intake YAML and calls Orchestrator.start_run(intake_path)
   ↓
3. Orchestrator initializes RunState:
   - run_id: 20251120_103000
   - current_phase: planning
   - status: RUNNING
   ↓
4. User runs: orchestrator run next
   ↓
5. Orchestrator.next_phase() → Orchestrator.run_phase("planning")
   ├─ Get agents: [architect]
   ├─ Build context (project_name, intake_summary)
   ├─ Load prompt: subagent_prompts/architect.md
   ├─ Interpolate: {{project_name}} → "myapp"
   ├─ Get executor: LLM (no entrypoints)
   ├─ Execute in in-session mode:
   │  └─ Print agent instructions to console
   │  └─ Exit with code 2 (awaiting work)
   │
   └─ Return PhaseOutcome:
      ├─ phase_name: "planning"
      ├─ success: false (agent awaiting work)
      ├─ agent_outcomes: [AgentOutcome(exit_code=2)]
      └─ awaiting_consensus: false
   ↓
6. Agent execution returns exit_code=2
   Orchestrator.next_phase() shows:
   "⏸️ IN-SESSION MODE"
   "Claude Code will execute the work"
   "Then run: orchestrator run checkpoint"
   ↓
7. Claude Code executes in current session:
   - Reads agent instructions
   - Creates architecture.md
   - Creates technical_spec.md
   - Commits to git
   ↓
8. User runs: orchestrator run checkpoint
   ↓
9. Checkpoint validation:
   - validate_artifacts(["architecture.md", "technical_spec.md"])
   - Scans project_root for files
   - Status: PASS (both found and non-empty)
   ↓
10. Orchestrator advances:
    - state.completed_phases.append("planning")
    - state.phase_artifacts["planning"] = ["architecture.md", "technical_spec.md"]
    - state.current_phase = "development"
    - state._save_state()
    ↓
11. Orchestrator checks requires_consensus for planning:
    - If true: _generate_consensus_request()
    - Sets state.awaiting_consensus = true
    - Pauses for user approval
    ↓
12. If consensus required, user runs: orchestrator run approve
    - state.awaiting_consensus = false
    - Continues to development
    ↓
13. User runs: orchestrator run next
    Orchestrator.run_phase("development")
    - Same cycle with Developer agent
    - Developer has context: "Previous artifacts from planning: architecture.md, ..."
```

---

## 9. Technical Stack & Dependencies

**Core Technologies:**
- **Python 3.9+** - Main implementation language
- **Typer** - CLI framework
- **Rich** - Terminal formatting
- **PyYAML** - Configuration loading
- **Anthropic Python SDK** - Claude API (optional, for API mode)
- **asyncio** - Async agent execution
- **jsonschema** - Configuration validation

**Project Structure:**
```
src/
├── orchestrator/
│   ├── __main__.py            # Entry point
│   ├── cli.py                 # Main CLI
│   ├── runloop.py             # Core engine
│   ├── state.py               # State management
│   ├── types.py               # Data structures
│   ├── checkpoints.py         # Validation
│   ├── prompt_loader.py       # Template loading
│   ├── executors/             # Execution adapters
│   │   ├── __init__.py
│   │   ├── types.py
│   │   ├── llm_exec.py       # LLM agent executor
│   │   └── subprocess_exec.py # Subprocess executor
│   ├── commands/              # Subcommands
│   │   ├── bootstrap.py
│   │   └── checkpoint.py
│   ├── reliability.py         # Retry, timeout logic
│   └── ...
├── intake/                    # Intake system
│   ├── cli.py
│   └── ...
└── ...

.claude/
├── config.yaml               # Main configuration
├── orchestrator_state.json   # Current run state
├── logs/                     # Run logs
├── agent_outputs/            # Agent prompts/responses
├── consensus/                # Consensus requests
└── checkpoints/              # Checkpoint artifacts
```

---

## 10. Key APIs & Integration Points

### Invoking the Orchestrator Programmatically

```python
from src.orchestrator.runloop import Orchestrator
from pathlib import Path

# Initialize
orch = Orchestrator(project_root=Path.cwd())

# Start a run
orch.start_run(intake_path="intake/myproject.yaml")

# Execute phases
outcome = orch.next_phase(
    force_parallel=False,
    max_workers=2,
    timeout_override=None
)

# Check status
print(orch.state.status)
print(orch.state.current_phase)
print(orch.state.completed_phases)

# Handle consensus
if orch.state.awaiting_consensus:
    orch.approve_consensus()
    # OR
    orch.reject_consensus("Needs architectural review")

# Get run info
status = orch.get_status()
log_tail = orch.get_log_tail(lines=50)
```

### Extending with Custom Agents

1. Create prompt template: `subagent_prompts/my_agent.md`
2. Add to config:
   ```yaml
   subagents:
     my_agent:
       enabled: true
       prompt_template: subagent_prompts/my_agent.md
       checkpoint_artifacts: [output/**/*]
   ```
3. Add to phase:
   ```yaml
   workflow:
     phases:
       - name: custom_phase
         agents: [my_agent]
   ```
4. Run: `orchestrator run start && orchestrator run next`

---

## Summary: Core Concepts

| Concept | Purpose | Implementation |
|---------|---------|-----------------|
| **Run** | Single workflow execution | RunState + run_id |
| **Phase** | Sequential milestone | Named workflow stages |
| **Agent** | Specialized executor | LLM or subprocess |
| **Checkpoint** | Artifact validation | Glob matching + validation reports |
| **Consensus** | Human approval gate | REQUEST.md file + CLI approval |
| **Handoff** | Context passing | State artifacts + prompt interpolation |
| **State** | Persistent progress | JSON file + in-memory RunState |
| **Executor** | Runtime dispatch | Strategy pattern (LLM vs subprocess) |

---

## Performance Characteristics

**Typical Workflow Timing:**

- **Planning phase (Architect):** 2-5 minutes (in-session work)
- **Development phase (Developer):** 10-30 minutes (in-session work)
- **QA phase (QA):** 5-10 minutes (in-session work)
- **Documentation phase:** 5-15 minutes (in-session work)
- **Consensus review:** < 5 minutes per phase

**Concurrency Limits:**

- Default: `max_parallel_agents: 1` (sequential)
- Can increase to 2-4 for true parallel execution
- Capped at config limit (safety mechanism)

**Timeout Defaults:**

- Per agent: 30 minutes
- Per phase: Sum of agents + consensus overhead
- Configurable via `--timeout` flag or `.claude/config.yaml`

**State I/O:**

- Write on every phase transition
- JSON serialization ~1-2ms
- Negligible performance impact

