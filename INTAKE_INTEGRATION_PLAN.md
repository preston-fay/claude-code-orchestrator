# Intake Template System Integration Plan

## Using Orchestrator's Own Agents to Build the Integration

### Phase 1: Architecture & Design (Architect Agent)

**Agent: Architect**
**Checkpoint: intake_architecture.md**

The Architect agent will:
1. Design the intake API endpoints structure
2. Create data models for intake responses
3. Define the integration points with existing workflow
4. Produce ADR-004: Intake Template System Architecture

**Deliverables:**
- `docs/architecture/intake_system_design.md`
- `.claude/decisions/ADR-004-intake-template-architecture.md`
- API specification for intake endpoints
- Data flow diagrams

### Phase 2: Backend Development (Developer Agent)

**Agent: Developer**
**Checkpoint: intake_backend_complete**

The Developer agent will implement:

1. **Intake API Module** (`orchestrator_v2/api/routes/intake.py`):
   ```python
   GET  /api/intake/templates - List available templates
   GET  /api/intake/templates/{template_id} - Get template definition
   POST /api/intake/sessions - Start intake session
   GET  /api/intake/sessions/{session_id} - Get session state
   POST /api/intake/sessions/{session_id}/answers - Submit answer
   POST /api/intake/sessions/{session_id}/complete - Complete intake
   ```

2. **Intake Service** (`orchestrator_v2/services/intake_service.py`):
   - Template loader (reads from `/intake/templates/`)
   - Session manager (tracks interview progress)
   - Response validator (against schema)
   - Conditional logic engine
   - Client governance integration

3. **Intake Models** (`orchestrator_v2/models/intake.py`):
   - IntakeTemplate
   - IntakeSession
   - IntakeResponse
   - ValidationResult

### Phase 3: Frontend Development (Developer Agent)

**Agent: Developer**
**Checkpoint: intake_frontend_complete**

The Developer will create:

1. **IntakeWizard Component** (`rsg-ui/src/components/IntakeWizard.tsx`):
   - Template selector
   - Question renderer (supports all question types)
   - Conditional logic handler
   - Progress tracker
   - Response validator
   - Ad-hoc context collector

2. **Intake API Client** (`rsg-ui/src/api/intake.ts`):
   - Template fetching
   - Session management
   - Answer submission
   - Validation handling

3. **Integration with Run Creation**:
   - Replace simple textarea with IntakeWizard
   - Pass completed intake to run creation

### Phase 4: Data & Analytics Integration (Data Agent)

**Agent: Data**
**Checkpoint: intake_analytics_ready**

The Data agent will:
1. Create intake analytics schema
2. Build response aggregation pipeline
3. Generate usage metrics dashboard
4. Implement template effectiveness tracking

**Deliverables:**
- `data/processed/intake_metrics.json`
- Analytics dashboard specification
- Template usage reports

### Phase 5: Quality Assurance (QA Agent)

**Agent: QA**
**Checkpoint: intake_tests_passed**

The QA agent will:

1. **Test Coverage:**
   - Unit tests for intake service
   - Integration tests for API endpoints
   - E2E tests for wizard flow
   - Validation tests for all templates

2. **Test Scenarios:**
   - Complete interview for each template
   - Conditional logic branching
   - Validation failures
   - Session persistence
   - Client governance application

3. **Test Files:**
   - `tests/test_intake_service.py`
   - `tests/test_intake_api.py`
   - `rsg-ui/src/components/__tests__/IntakeWizard.test.tsx`

### Phase 6: Documentation (Documentarian Agent)

**Agent: Documentarian**
**Checkpoint: intake_docs_complete**

The Documentarian will create:

1. **User Documentation:**
   - How to use the intake wizard
   - Template selection guide
   - FAQ for common questions

2. **Developer Documentation:**
   - API reference
   - Template authoring guide
   - Extending the system

3. **Files:**
   - `docs/user_guide/intake_wizard.md`
   - `docs/api/intake_endpoints.md`
   - `docs/developer/creating_intake_templates.md`

### Phase 7: Review & Consensus (Consensus + Reviewer Agents)

**Agents: Consensus, Reviewer**
**Checkpoint: intake_approved**

1. **Consensus Agent:**
   - Validates all checkpoints
   - Ensures integration coherence
   - Approves for deployment

2. **Reviewer Agent:**
   - Code review of implementation
   - Security assessment
   - Performance validation

### Phase 8: Repository Hygiene (Steward Agent)

**Agent: Steward**
**Checkpoint: intake_cleanup_complete**

The Steward will:
- Remove any dead code from old intake approach
- Organize intake-related files properly
- Update `.tidyignore` if needed
- Ensure no orphaned dependencies

## Implementation Commands

```bash
# Phase 1: Architecture
orchestrator run architect --task "Design intake template system integration"

# Phase 2-3: Development
orchestrator run developer --task "Implement intake backend API and service"
orchestrator run developer --task "Create IntakeWizard frontend component"

# Phase 4: Data Integration
orchestrator run data --task "Build intake analytics pipeline"

# Phase 5: QA
orchestrator run qa --task "Test intake system end-to-end"

# Phase 6: Documentation
orchestrator run documentarian --task "Document intake system"

# Phase 7: Review
orchestrator run consensus --task "Review intake integration"
orchestrator run reviewer --task "Code review intake implementation"

# Phase 8: Cleanup
orchestrator run steward --task "Clean up intake integration"
```

## Skills to Leverage

1. **Survey Data Processing** (`.claude/skills/survey_data_processing.yaml`)
   - Apply to intake response analysis
   - Use Likert scale methods for satisfaction questions
   - Apply response validation patterns

2. **Time Series Analytics** (`.claude/skills/time_series_analytics.yaml`)
   - For tracking intake completion rates over time
   - Forecasting template usage patterns

## Knowledge Base Integration

1. **Kearney Standards** (`.claude/knowledge/kearney_standards.yaml`)
   - Apply brand constraints automatically
   - Enforce governance rules in templates

2. **Analytics Best Practices** (`.claude/knowledge/analytics_best_practices.yaml`)
   - Guide data-related intake questions
   - Validate technical requirements

## Checkpoint Artifacts

Each phase produces checkpoint artifacts that feed into the next:

```
intake_architecture.md → intake_backend_complete → intake_frontend_complete
                     ↓
              intake_analytics_ready
                     ↓
              intake_tests_passed
                     ↓
              intake_docs_complete
                     ↓
              intake_approved
                     ↓
              intake_cleanup_complete
```

## Success Criteria

The intake system is complete when:
- ✅ Users can select from available templates
- ✅ Wizard guides through adaptive questions
- ✅ Responses are validated against schema
- ✅ Client governance is automatically applied
- ✅ Completed intake feeds into orchestrator workflow
- ✅ All tests pass with >80% coverage
- ✅ Documentation is comprehensive
- ✅ System is production-ready

## Next Steps

1. Run the architect agent to design the system
2. Let each agent handle their phase with checkpoints
3. Use consensus agent to validate progress
4. Deploy to production

This plan leverages the orchestrator's own capabilities to build the intake system properly, with each agent contributing their expertise and the checkpoint system ensuring quality at each stage.