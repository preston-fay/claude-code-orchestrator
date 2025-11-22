# RSC Orchestration Status

This document captures the current state of the RSC orchestration system and outlines what needs to be fixed for real functionality.

## Where RSC Was Lying

The RSC orchestration system was fundamentally a **facade with working UI but stubbed backend**. The hierarchy of issues:

### Level 1: Critical Runtime Issues (FIXED)

**Async/Await Mismatches** (`orchestrator_v2/engine/engine.py`)
- Lines 469, 478, 506, 511, 514 were missing `await` for agent lifecycle methods
- **Impact**: Agent coroutines were created but never executed
- **Status**: ✅ FIXED

**Governance Engine Crashes** (`orchestrator_v2/governance/governance_engine.py`)
- `GovernanceResults` was missing `failed_rules` field referenced in code
- Signature mismatch between caller and definition
- **Impact**: System would crash on any governance gate block
- **Status**: ✅ FIXED

### Level 2: Stub Agents (Still Present)

All agents in `orchestrator_v2/agents/*.py` create placeholder artifacts without real work:

| Agent | File | Issue |
|-------|------|-------|
| Architect | `architect.py:158-201` | Creates fake "Architecture Proposal" with `[placeholder]` content |
| Developer | `developer.py:122-150` | Creates fake "Development Report" with hardcoded file list |
| Data Agent | `data_agent.py:141-178` | Creates fake metrics: `Total records: [count]` |
| QA Agent | `qa.py:122-153` | Always reports `Pass rate: 96.7%` regardless of actual tests |
| Consensus | `consensus.py:98-126` | Always says `APPROVED - Phase may proceed` |
| Reviewer | `reviewer.py:99-137` | Always says `APPROVED with minor suggestions` |
| Steward | `steward.py:99-132` | Always shows `Status: COMPLIANT` |
| Documentarian | `documentarian.py:101-129` | Creates placeholder documentation |

**BaseAgent.act()** (lines 342-364) creates the same placeholder for every agent.

### Level 3: Disconnected Skills

Skills exist in `orchestrator_v2/capabilities/skills/` but are never invoked:

- `time_series_forecasting` - ARIMA/Prophet methodology
- `optimization_modeling` - Linear programming
- `survey_analysis` - Statistical analysis
- `territory_poc/territory_scoring_skill.py`
- `territory_poc/territory_alignment_skill.py`

**Where they should be called but aren't:**
- `BaseAgent.load_skills()` (line 87-95) says "Will integrate with SkillRegistry in future"
- No actual calls to `execute_skills()` or `find_matching_skills()` in agents or engine

### Level 4: UI Wiring Issues

**Phase execution** (`rsg-ui/src/api/client.ts:191-192`):
```typescript
export async function runPhase(projectId: string, phase?: string): Promise<void> {
  await axiosInstance.post(`/projects/${projectId}/advance`);  // phase param ignored!
}
```

The UI passes the phase name but the API function ignores it.

## What Works Now

After the critical fixes:

1. **Agent lifecycle executes** - Async methods are properly awaited
2. **Governance doesn't crash** - `failed_rules` field exists, signature is flexible
3. **Projects can be created** with multi-capability support
4. **Phases advance** through the workflow
5. **Events are emitted** properly

## What Still Needs Work

### High Priority

1. **Replace stub agents with real implementations**
   - Call LLM for planning and acting
   - Generate real artifacts
   - Track actual token usage

2. **Wire skills to agents**
   - Connect SkillRegistry to agent execution
   - Call `find_matching_skills()` based on phase/capabilities
   - Execute skills and collect results

3. **Make artifacts real**
   - Skills write actual files to workspace
   - Create proper ArtifactInfo entries
   - Expose via API endpoints

### Medium Priority

4. **Fix UI phase parameter passthrough**
   - Update `runPhase()` to use the phase parameter
   - Or clarify that `/advance` always runs current phase

5. **Add artifacts endpoint**
   - `GET /projects/{project_id}/artifacts`
   - Group by phase and agent

6. **Project console context**
   - Pass capabilities and phases to chat endpoint
   - Include artifact summary in system prompt

### Lower Priority

7. **Orchestration profiles**
   - Define phase→capability→skill mappings per template
   - Store in ProjectState

8. **Remove "Territory Demo" references from UI**
   - Keep demo templates internal only

## Testing

To verify the critical fixes work:

```bash
# Start API server
cd /home/user/claude-code-orchestrator
.venv/bin/python scripts/dev/run_api_server.py

# Create a project
curl -X POST http://localhost:8000/projects \
  -H "Content-Type: application/json" \
  -d '{"project_name":"Test","template_id":"blank"}'

# Advance phase (should not crash on governance)
curl -X POST http://localhost:8000/projects/{project_id}/advance
```

## Architecture Notes

The system is designed with:
- **Phases** as workflow stages (planning, architecture, data, development, qa, documentation)
- **Agents** as role-based executors (architect, developer, qa, etc.)
- **Skills** as reusable analytical patterns (forecasting, optimization, etc.)
- **Capabilities** as project features that map to phases and skills

The wiring should flow:
```
Template → Capabilities → Phases → Agents → Skills → Artifacts
```

Currently the flow breaks at Agents → Skills (skills are never called).
