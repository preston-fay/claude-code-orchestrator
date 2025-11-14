# Product Trinity Playbook

## Overview
Product Trinity workflow provides structured PM → UX → Dev → QA flow for product development projects.

## Quick Start

```bash
# Initialize product project
orchestrator init --workflow product_trinity

# Creates: intake/starter.product.yaml

# Run workflow
orchestrator run --workflow product_trinity --intake intake/starter.product.yaml
```

## Workflow Phases

```
1. Product Requirements (PM)
   ↓ Produces: PRD.md, user_stories.md, acceptance_criteria.md
   
2. UX Design (UX Designer)
   ↓ Produces: wireframes/, design_system.md, accessibility_checklist.md
   
3. Development (Developer)
   ↓ Produces: src/ implementation
   
4. Quality Assurance (QA)
   → Produces: qa_validation_report.md (with pass/fail per criterion)
```

## Expected Artifacts

After complete run, you'll have:

```
reports/
├── PRD.md                      # Product requirements
├── user_stories.md             # User stories (As a/I want/So that)
├── acceptance_criteria.md      # Testable criteria (Given/When/Then)
├── design_system.md            # Colors, typography, components
├── accessibility_checklist.md  # WCAG 2.1 AA compliance
└── qa_validation_report.md     # Pass/fail validation

wireframes/
├── login.md                    # Login screen wireframe
└── dashboard.md                # Dashboard wireframe
```

## QA Validation Report Format

```markdown
# QA Validation Report

## Summary
| Total Criteria | Passed | Failed | Pass Rate |
|----------------|--------|--------|-----------|
| 7              | 6      | 1      | 85.7%     |

## AC-001: Valid Credentials Redirect
**Status:** ✅ PASS  
**Evidence:** User successfully redirected to dashboard

## AC-005: Loading Time < 2s
**Status:** ❌ FAIL  
**Evidence:** Load time: 2.8s (exceeds 2s requirement)  
**Severity:** Major  
**Recommended Action:** Optimize database queries
```

## Customization

Edit `.claude/config.product_trinity.yaml` to:
- Add/remove phases
- Change consensus requirements
- Modify artifact patterns

## Integration with Skills

Product phases auto-inject relevant skills:
- PM: survey_data_processing (if personas/feedback mentioned)
- UX: wcag_accessibility (if accessibility in requirements)
- Dev: Normal skills engine flow
- QA: Evaluation snippets

## Troubleshooting

**Q: Can I skip a phase?**  
A: Yes, set `enabled: false` in config

**Q: Can I add custom agents?**  
A: Yes, add agent definition in `.claude/agents/` and reference in workflow

**Q: Why is QA failing?**  
A: Check `qa_validation_report.md` for specific criteria that failed
