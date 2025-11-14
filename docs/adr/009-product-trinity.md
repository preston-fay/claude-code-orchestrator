# ADR-009: Product Trinity Workflow

**Status:** Accepted  
**Date:** 2025-11-14  
**Context:** Phase 5.B - Structured PM → UX → Dev → QA Workflow

## Context

Many projects follow a product development lifecycle: requirements → design → implementation → validation. Current orchestrator lacks a structured workflow for this common pattern.

**Goal:** Provide opinionated PM → UX → Dev → QA workflow with:
- Clear artifact handoffs between phases
- Testable acceptance criteria from PM → QA
- Design system and accessibility baked in
- QA validation with pass/fail metrics

## Decision

Implement **Product Trinity Workflow** as opt-in workflow configuration.

### Workflow Phases

```yaml
product_requirements:
  agents: [product-manager]
  artifacts: [PRD.md, user_stories.md, acceptance_criteria.md]
  
ux_design:
  agents: [ux-designer]
  artifacts: [wireframes/, design_system.md, accessibility_checklist.md]
  
development:
  agents: [developer]
  artifacts: [src/**/*.py]
  
quality_assurance:
  agents: [qa]
  artifacts: [qa_validation_report.md]
```

### Agent Responsibilities

**Product Manager:**
- Inputs: intake.yaml
- Outputs: PRD, user stories (As a/I want/So that), acceptance criteria (Given/When/Then)

**UX Designer:**
- Inputs: PRD, user stories
- Outputs: Wireframes (ASCII diagrams), design system (colors/typography/components), WCAG checklist

**QA:**
- Inputs: Acceptance criteria, implementation, component specs
- Outputs: QA validation report (pass/fail per criterion, pass rate %, severity classification)

### Activation

```bash
# Use Product Trinity workflow
orchestrator run --workflow product_trinity --intake starter.product.yaml

# Or use dedicated config
orchestrator run --config .claude/config.product_trinity.yaml
```

## Consequences

### Positive
- **Structured:** Clear phases with defined inputs/outputs
- **Testable:** Acceptance criteria → QA validation mapping
- **Accessibility First:** WCAG checklist in UX phase
- **Observable:** Pass rate metrics tracked
- **Reusable:** Starter template for common product projects

### Negative
- **Opinionated:** Assumes PM → UX → Dev → QA flow (may not fit all teams)
- **Lightweight:** Current agents are stubs (can be enhanced with real LLM calls)

### Neutral
- **Opt-In:** Doesn't affect existing workflows
- **Extensible:** Can add more agents (e.g., data scientist, devops)

## Alternatives Considered

### 1. Generic Workflow Builder
- Rejected: Too abstract, loses opinionated value
- Product Trinity is common enough to warrant dedicated support

### 2. Full Implementations vs Stubs
- Decision: Ship stubs first, can enhance later
- Stubs prove the workflow structure works

### 3. Different Phase Names
- Considered: "product" vs "product_requirements", "qa" vs "quality_assurance"
- Decision: Be explicit and verbose

## Implementation

**Files:**
- `.claude/agents/product-manager.md` - PM definition
- `.claude/agents/ux-designer.md` - UX definition
- `.claude/agents/qa.md` - QA definition
- `src/orchestrator/agents/product_manager.py` - Stub implementation
- `src/orchestrator/agents/ux_designer.py` - Stub implementation
- `src/orchestrator/agents/qa.py` - Stub implementation
- `.claude/config.product_trinity.yaml` - Workflow config
- `intake/templates/starter.product.yaml` - Starter template

**Tests:** 6 smoke tests, 100% passing

**Test Coverage:**
- test_product_trinity_end_to_end: Full PM → UX → QA flow
- test_qa_pass_fail_tracking: Metrics validation
- test_artifacts_have_meaningful_content: Not just templates

## Future Enhancements

1. **Real LLM Integration:** Replace stubs with actual LLM calls for dynamic artifact generation
2. **Visual Wireframes:** Generate actual PNG/SVG from specs
3. **Automated E2E Tests:** QA agent runs Playwright/Selenium
4. **Design System Generator:** Auto-generate CSS from design system spec
5. **Sprint Planning:** PM agent estimates stories, creates burndown charts

## Related
- ADR-005: Specialized Agents (similar auto-detection pattern)
- ADR-008: Skills Engine (UX phase uses wcag_accessibility skill)
