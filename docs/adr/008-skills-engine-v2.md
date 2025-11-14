# ADR-008: Skills Activation Engine v2

**Status:** Accepted  
**Date:** 2025-11-14  
**Context:** Phase 5.A - Skills Auto-Matching and Snippet Injection

## Context

Agents benefit from reusable analytical patterns (skills) but manually loading and configuring them creates overhead. We need:
- Auto-detection of relevant skills based on task context
- Concise, agent-specific snippets (not full skill documentation)
- Prerequisite gating to fail-fast when MCP modules missing
- Telemetry to understand skill usage patterns

## Decision

Implement **Skills Activation Engine v2** with four core capabilities:

### 1. Auto-Matching
```python
engine = SkillsEngine()
matched = engine.match(task_text, intake, governance)
# Returns: [time_series_analytics, optimization_modeling]
```

**Matching Strategy:**
- Keyword-based matching against task text, intake requirements, governance policies
- Case-insensitive, sorted by relevance (match count), then alphabetically
- Deterministic ordering across runs

### 2. Prerequisite Validation
```python
available, missing = engine.validate_prereqs(matched)
# available: Skills with all MCP modules present
# missing: List of MissingPrereq with actionable hints
```

**Gating Policy:**
- Default (non-enforce): Warn about missing prereqs, continue
- Enforce mode (`--skills-enforce`): Fail-fast with installation instructions

### 3. Agent-Specific Snippet Injection
```python
snippet = engine.render_for_agent("developer", available, max_chars=2000)
# Returns concise code snippet for current agent only
```

**Benefits:**
- Concise (<2k chars) vs full skill documentation
- Agent-specific (data agent gets different snippet than developer)
- Respects token budgets

### 4. Telemetry
```python
summary = engine.summarize(matched, available, missing)
# {
#   "skills_matched": ["time_series_analytics"],
#   "skills_available": ["time_series_analytics"],
#   "skills_missing_prereqs": [],
#   "missing_modules": []
# }
```

## Consequences

### Positive
- **Zero Config:** Skills auto-activate based on task context
- **Fail-Fast:** Missing prereqs detected before execution
- **Token Efficient:** Concise snippets vs full docs
- **Observable:** Telemetry tracks skill usage

### Negative
- **Keyword Brittleness:** Relies on keyword matching (could use LLM in future)
- **Index Maintenance:** Skills index requires manual curation

### Neutral
- **Opt-In Enforcement:** `--skills-enforce` flag for strict mode

## Alternatives Considered

### 1. LLM-Based Matching
- Rejected: Adds latency, cost, non-determinism
- Could revisit for v3

### 2. Always Inject All Skills
- Rejected: Bloats context, wastes tokens
- Keyword matching provides good enough filtering

### 3. No Prerequisite Validation
- Rejected: Cryptic failures when MCP modules missing
- Fail-fast is better UX

## Implementation

**Files:**
- `src/orchestrator/skills/engine.py` - SkillsEngine class
- `src/orchestrator/skills/index.yaml` - Skills catalog
- `src/orchestrator/skills/types.py` - Pydantic models
- `tests/skills/` - 23 tests

**Skills Index Seeded With:**
- time_series_analytics (Prophet forecasting)
- optimization_modeling (LP/NLP)
- survey_data_processing (Likert scales)
- ml_classification (sklearn)
- wcag_accessibility (WCAG 2.1 AA)

**Test Coverage:** 100% on engine, 23 tests passing

## Related
- Phase 5.B: Product Trinity (uses wcag_accessibility skill)
- ADR-004: MCP Code Execution (skills reference MCP modules)
