# RSC Orchestration Status

## Current Implementation State

### Fully Implemented

- **Engine Core**
  - WorkflowEngine with phase management
  - Governance gate evaluation
  - Token budget enforcement
  - Telemetry events

- **Capability-Driven Phases**
  - CAPABILITY_PHASE_MAP with 12+ capabilities
  - get_phases_for_capabilities() function
  - Dynamic phase derivation

- **API Endpoints**
  - Project CRUD
  - Phase execution (POST /projects/{id}/advance)
  - Artifacts listing (GET /projects/{id}/artifacts)
  - Project chat (POST /projects/{id}/chat)
  - RSG status endpoints

- **UI Components**
  - Project list with templates
  - Project detail with brief/capabilities
  - Phase status and run buttons
  - Artifacts panel
  - Run activity panel

- **Model Configuration**
  - Centralized MODEL_CONFIG
  - Aliases: sonnet-latest, haiku-fallback
  - Claude Sonnet 4.5 (premium)
  - Claude Haiku 4.5 (cost-efficient)

### Stubbed / Partial Implementation

- **Agent Execution**
  - Agents execute as stubs when not implemented
  - Token usage is simulated (500 input, 200 output)
  - Real LLM agents would need full implementation

- **Planning Artifacts**
  - The `/plan-phase` command returns a placeholder
  - Real PRD/architecture/backlog generation requires:
    - ArchitectAgent with LLM integration
    - Template-based artifact generation
    - Brief parsing and domain knowledge loading

- **Console Chat**
  - `/run-phase` command works
  - `/plan-phase` returns placeholder
  - `/feature` not implemented
  - Free-form chat calls LLM but needs context tuning

### Not Yet Implemented

- **Real Planning Artifacts**
  - LLM-generated PRD.md
  - LLM-generated architecture.md
  - Structured backlog.json

- **Full Agent Integration**
  - Architect agent with planning prompts
  - Data agent with pipeline execution
  - Developer agent with code generation
  - QA agent with test execution
  - Documentarian agent

## Known Limitations

1. **Phase Execution is Stubbed**
   - Phases run without errors but don't produce real artifacts
   - Token usage is simulated

2. **Planning Artifacts Placeholder**
   - `/plan-phase` doesn't call LLM yet
   - Need to implement ArchitectAgent.generate_planning_artifacts()

3. **Workspace Artifacts**
   - Artifacts panel shows files from workspace/artifacts/
   - If no files exist, panel shows nothing
   - Files must be created by agent execution or manually

4. **Console Commands**
   - Only `/run-phase` fully functional
   - `/plan-phase` needs LLM integration
   - `/feature` not implemented

## Next Steps for Full Implementation

1. **Implement ArchitectAgent Planning**
   - Load project brief and capabilities
   - Call LLM with structured prompts
   - Generate PRD.md, architecture.md, backlog.json
   - Write to workspace/artifacts/planning/

2. **Add Territory Blueprint Support**
   - Load docs/territory_system_blueprint.md if brief mentions territory
   - Include as domain context in planning prompts

3. **Implement Real Agents**
   - Each agent type needs:
     - Initialization logic
     - LLM prompt templates
     - Artifact generation
     - Quality validation

4. **Console Improvements**
   - Implement `/feature` command
   - Add message history
   - Stream responses

## Testing the Current State

```bash
# Start API
python scripts/dev/run_api_server.py

# Start UI
cd rsg-ui && npm run dev

# Create project and run phases
# - Phases complete without errors
# - Events emitted correctly
# - No real artifacts generated (stubbed)
```

## Architecture Notes

- Engine at `orchestrator_v2/engine/engine.py`
- Governance at `orchestrator_v2/governance/governance_engine.py`
- API at `orchestrator_v2/api/server.py`
- LLM providers at `orchestrator_v2/llm/provider_registry.py`
- UI at `rsg-ui/src/`
