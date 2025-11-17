# Project Initiation Workflow

## Overview

This document provides a step-by-step workflow for initiating new projects using the Claude Code Orchestrator. Follow this process to ensure consistent, high-quality project kickoffs.

---

## Quick Reference

```
1. Intake Meeting (30-60 min) → Fill intake form
2. Review & Clarify (15 min) → Address gaps
3. Generate Constitution (5 min) → Define principles
4. Kickoff Orchestrator (1 min) → Start workflow
5. Monitor Progress → Review checkpoints
```

**Total Time to Start:** ~1-2 hours from idea to running orchestrator

---

## Detailed Workflow

### Phase 0: Pre-Requisites (One-Time Setup)

**For Your Workstation:**
```bash
# 1. Clone orchestrator repo
git clone https://github.com/your-org/claude-code-orchestrator.git
cd claude-code-orchestrator

# 2. Install dependencies
pip install -e .

# 3. Verify installation
orchestrator --help
```

**For Each New Project:**
```bash
# Create project directory
mkdir my-new-project
cd my-new-project

# Initialize git
git init

# Create orchestrator structure
mkdir -p intake .claude/checkpoints docs data/{raw,processed} models tests
```

---

### Phase 1: Intake Meeting (30-60 minutes)

**Participants:**
- Product Owner / Client Stakeholder
- Technical Lead
- (Optional) Data Scientist / Subject Matter Expert

**Agenda:**

#### A. Understand the Problem (15 min)
Use the **5 Whys** technique:
1. What business problem are we solving?
2. Why is this important to solve now?
3. What's the current state vs. desired state?
4. Why can't the existing solution work?
5. What does success look like?

**Capture:**
- Problem statement (1-2 sentences)
- Business impact (quantified if possible)
- Key stakeholders and their needs

#### B. Define Requirements (20 min)
Work through the **Project Intake Form** (see Question 2):
- Project type (webapp, ML, analytics, etc.)
- Primary goals (3-5 concrete objectives)
- Success criteria (MUST be measurable - use SMART framework)
- Data sources (for ML/analytics projects)
- Technical constraints
- Timeline and budget
- Compliance requirements

**Red Flags to Catch:**
- ❌ Vague success criteria ("good performance", "high accuracy")
- ❌ Missing data sources for ML/analytics projects
- ❌ Unrealistic timelines ("build Netflix in 2 weeks")
- ❌ Conflicting tech preferences
- ❌ No identified product owner

#### C. Identify Risks (10 min)
Document top 3-5 risks:
- Data availability/quality risks
- Technical complexity risks
- Timeline/resource risks
- Compliance/security risks

For each risk: severity (low/medium/high/critical) + mitigation plan

#### D. Define Boundaries (10 min)
Clarify what's **in scope** vs. **out of scope**:
- Phase 1 (MVP) vs. Phase 2 (future)
- Core features vs. nice-to-haves
- Tech stack mandates vs. preferences

**Output:** Completed intake form (Word/Excel/MD - see Question 2)

---

### Phase 2: Convert to intake.yaml (15 minutes)

**Option A: Manual Conversion**
```bash
# Start with template
orchestrator intake new --type ml
# Creates intake/ml-project.intake.yaml

# Fill in from meeting notes
vim intake/ml-project.intake.yaml
```

**Option B: AI-Assisted Conversion**
```bash
# Use ChatGPT/Claude to convert meeting notes → YAML
# Paste your intake form responses
# Ask: "Convert this to the orchestrator intake.yaml format"
# Review and paste into intake/ml-project.intake.yaml
```

**Option C: Spreadsheet Import (Future)**
```bash
# Future enhancement: Excel → YAML converter
# orchestrator intake import intake-form.xlsx
```

---

### Phase 3: Validate & Clarify (15 minutes)

**Step 1: Schema Validation**
```bash
orchestrator intake validate intake/my-project.intake.yaml
```
✅ Pass → Continue
❌ Fail → Fix schema errors (missing required fields, invalid enums)

**Step 2: Quality Clarification**
```bash
orchestrator intake clarify intake/my-project.intake.yaml
```

**If 0 questions:**
✅ You're ready to start!

**If 1-5 questions (medium/low severity):**
⚠️ Review questions, decide if acceptable to proceed or fix first

**If >5 questions OR any critical/high:**
🛑 **STOP - Fix these before proceeding:**
```bash
# Filter to critical only
orchestrator intake clarify intake/my-project.intake.yaml --severity critical

# Update intake.yaml to address each question
vim intake/my-project.intake.yaml

# Re-run until critical/high questions resolved
orchestrator intake clarify intake/my-project.intake.yaml
```

**Best Practice:**
- Address all **critical** questions before starting
- Address most **high** questions (acceptable to have 1-2 remaining)
- **Medium/low** questions can be addressed during Planning Phase

---

### Phase 4: Generate Constitution (5 minutes)

**Generate from intake:**
```bash
orchestrator constitution generate --intake intake/my-project.intake.yaml
# Creates .claude/constitution.md
```

**Review constitution:**
```bash
cat .claude/constitution.md
```

**Customize (optional but recommended):**
```bash
vim .claude/constitution.md

# Add project-specific rules:
# - Forbidden practices for your domain
# - Required tools/frameworks
# - Phase-specific guidelines
# - Client-specific compliance requirements
```

**Examples of customizations:**
- **Healthcare ML:** Add HIPAA compliance rules, PHI handling
- **Finance Analytics:** Add SOC2 requirements, data retention policies
- **E-commerce Web App:** Add PCI-DSS for payment handling

**Validate:**
```bash
orchestrator constitution validate
```

---

### Phase 5: Commit Initial Artifacts (2 minutes)

**Create baseline commit:**
```bash
git add intake/my-project.intake.yaml .claude/constitution.md
git commit -m "feat: add project intake and constitution

- Project: [Name]
- Type: [ML/Analytics/WebApp]
- Primary Goals: [List]
- Success Criteria: [List]
"
git push
```

**Why commit before starting orchestrator?**
- Establishes project baseline
- Enables rollback if needed
- Creates audit trail of initial requirements
- Allows team review before execution

---

### Phase 6: Start Orchestrator (1 minute)

**Launch the workflow:**
```bash
orchestrator run start --intake intake/my-project.intake.yaml
```

**What happens next:**
1. **Preflight Checks** (automatic)
   - Constitution exists? ✅
   - Design system selected? ✅
   - All required fields present? ✅

2. **Planning Phase** (Architect agent)
   - Reads intake, constitution, Kearney standards
   - Proposes architecture
   - Creates Architecture Decision Records (ADRs)
   - **Checkpoint:** Architecture document

3. **Consensus Review** (Consensus agent)
   - Reviews architecture for conflicts
   - Validates against client governance
   - Approves or requests revisions
   - **Checkpoint:** Approved architecture

4. **Development Phase** (Developer agent)
   - Implements features
   - Adheres to constitution standards
   - **Checkpoint:** Working code

5. **QA Phase** (QA agent)
   - Tests functionality
   - Validates against success criteria
   - Checks constitution compliance
   - **Checkpoint:** Test report

6. **Documentation Phase** (Documentarian agent)
   - Creates README, API docs, user guides
   - **Checkpoint:** Documentation

---

### Phase 7: Monitor Progress (Ongoing)

**Check status:**
```bash
orchestrator status
```

**Review checkpoints:**
```bash
ls .claude/checkpoints/
cat .claude/checkpoints/architecture.md
cat .claude/checkpoints/test_report.md
```

**Intervene if needed:**
```bash
# Pause workflow
orchestrator run pause

# Review current state
cat .claude/state.json

# Resume or restart
orchestrator run resume
orchestrator run restart --from-phase development
```

---

### Phase 8: Approval Gates (Human Review)

At defined approval gates (from intake.yaml), orchestrator pauses for human review:

**Example:**
```yaml
orchestration:
  approval_gates:
    - "planning"        # Review architecture before development
    - "quality_assurance"  # Review tests before deployment
```

**When orchestrator pauses:**
```
⏸️  Approval gate: Planning Phase
📄 Review: .claude/checkpoints/architecture.md
❓ Approve to continue? (y/n)
```

**Your options:**
- ✅ **Approve** → Orchestrator continues to next phase
- ❌ **Reject** → Provide feedback, agent revises
- 🔄 **Request Changes** → Specific edits needed

---

### Phase 9: Iteration & Refinement (As Needed)

**Common iteration scenarios:**

#### A. Requirements Change Mid-Flight
```bash
# Pause orchestrator
orchestrator run pause

# Update intake
vim intake/my-project.intake.yaml

# Update constitution if needed
vim .claude/constitution.md

# Restart from appropriate phase
orchestrator run restart --from-phase planning
```

#### B. Architect Proposal Rejected
```
# Consensus agent rejects architecture
# Provide feedback in .claude/checkpoints/consensus_feedback.md
# Architect agent revises based on feedback
# Re-submit for consensus review
```

#### C. QA Finds Issues
```
# QA agent documents failures in test report
# Developer agent reads failures and fixes
# QA agent re-runs tests
# Iterates until all tests pass
```

---

### Phase 10: Completion & Handoff (Final)

**When all phases complete:**
```
✅ All phases completed successfully
📊 Project Summary:
   - Architecture: Approved
   - Development: 15 features implemented
   - QA: 127 tests passing (coverage: 87%)
   - Documentation: README, API docs, user guide created

📁 Deliverables:
   - Code: src/
   - Tests: tests/
   - Docs: docs/
   - Models: models/ (for ML projects)
   - Checkpoints: .claude/checkpoints/
```

**Final steps:**
1. **Review deliverables** against success criteria
2. **Create deployment plan** (if not already done by Developer agent)
3. **Schedule deployment** (if approval required per governance)
4. **Archive project artifacts** (commit everything, tag release)
5. **Conduct retrospective** (what worked, what didn't)

**Create final commit:**
```bash
git add -A
git commit -m "feat: complete [Project Name] - all phases successful

- Architecture: [Summary]
- Features: [List]
- Tests: [Coverage]
- Docs: [Created]

Closes #[issue-number]
"
git tag v1.0.0
git push --tags
```

---

## Workflow Variations by Project Type

### ML Projects

**Additional steps:**
- **Data collection** before intake meeting (need data samples)
- **Baseline model** benchmarking (what's current accuracy?)
- **Model risk assessment** (bias, fairness, drift)
- **MLOps setup** (MLflow, DVC, feature store)

**Extended timeline:**
- Intake meeting: 60 min (data discussion)
- Data Engineering Phase: 1-3 days (before development)
- Model training: 1-7 days (depending on data volume)

### Analytics Projects

**Additional steps:**
- **Data source access** (database credentials, API keys)
- **Business rules documentation** (KPIs, metrics definitions)
- **Dashboard mockups** (stakeholder expectations)

**Extended timeline:**
- ETL pipeline development: 1-3 days
- Dashboard iteration: Multiple feedback cycles

### Web Applications

**Additional steps:**
- **UI/UX design** (wireframes, mockups)
- **User stories** (detailed acceptance criteria)
- **Accessibility requirements** (WCAG level)

**Extended timeline:**
- Frontend iteration: Multiple feedback cycles
- User acceptance testing: 1-2 weeks

---

## Anti-Patterns to Avoid

### ❌ Starting Without Clarification
**Problem:** Vague intake → architect guesses → rework
**Solution:** ALWAYS run `orchestrator intake clarify` before starting

### ❌ Skipping Constitution
**Problem:** No standards → inconsistent output
**Solution:** Generate constitution, even if minimal

### ❌ Ignoring Approval Gates
**Problem:** Orchestrator builds wrong thing
**Solution:** Review architecture at approval gates

### ❌ Not Committing Checkpoints
**Problem:** Can't rollback, no audit trail
**Solution:** Commit after each major checkpoint

### ❌ Changing Requirements Mid-Flight Without Pausing
**Problem:** Orchestrator out of sync with new requirements
**Solution:** Pause → Update intake → Restart from phase

---

## Success Metrics

Track these metrics to measure orchestrator effectiveness:

### Quality Metrics
- **Clarification questions on first run** (target: <5)
- **Consensus approval on first try** (target: >80%)
- **QA test pass rate** (target: >90%)
- **Constitution compliance** (target: 100% on critical rules)

### Efficiency Metrics
- **Time to first checkpoint** (Planning Phase completion)
- **Total phases completed** (should match intake)
- **Rework cycles** (target: <2 per phase)

### Learning Metrics (for Academy)
- **Intake quality improvement** (v1 → v2 → v3)
- **Constitution customization** (% students who customize)
- **Successful project completions** (target: >90%)

---

## Troubleshooting Common Issues

### Issue: "No intake file found"
```bash
# Solution: Create intake directory and file
mkdir -p intake
orchestrator intake new --type ml
```

### Issue: "Constitution not found"
```bash
# Solution: Generate constitution
orchestrator constitution generate
```

### Issue: "Design system not selected"
```bash
# Solution: Add to intake.yaml
design_system: "kearney"
```

### Issue: "Orchestrator stuck at approval gate"
```bash
# Solution: Review checkpoint, approve/reject
cat .claude/checkpoints/[phase].md
# Then respond to prompt
```

### Issue: "Agent produced low-quality output"
```bash
# Solution: Check constitution clarity
vim .claude/constitution.md
# Add more specific standards
# Restart from that phase
orchestrator run restart --from-phase planning
```

---

## Templates & Checklists

### Pre-Start Checklist
```
☐ Intake meeting completed
☐ Intake form filled out
☐ intake.yaml created and validated
☐ Clarification run (0 critical questions)
☐ Constitution generated and reviewed
☐ Initial commit made
☐ Team notified of orchestrator start
```

### Phase Completion Checklist
```
☐ Checkpoint artifact created
☐ Checkpoint reviewed against success criteria
☐ Checkpoint committed to git
☐ Approval gate passed (if applicable)
☐ Team notified of progress
```

### Project Completion Checklist
```
☐ All success criteria met
☐ All tests passing (coverage ≥ target)
☐ Documentation complete
☐ Constitution compliance verified
☐ Deployment plan created
☐ Retrospective scheduled
☐ Final commit and tag
```

---

## Getting Help

### For Orchestrator Issues
- Check logs: `cat .claude/logs/orchestrator.log`
- Review state: `cat .claude/state.json`
- Consult docs: `docs/` directory

### For Project Guidance
- Review examples: `.claude/templates/`
- Check similar projects: Search internal repos
- Ask in Academy Slack: `#orchestrator-help`

### For Technical Issues
- GitHub Issues: https://github.com/your-org/claude-code-orchestrator/issues
- Internal Support: orchestrator-support@company.com

---

## Next Steps

1. **Schedule intake meeting** for your next project
2. **Use the intake form** (Question 2) to capture requirements
3. **Follow this workflow** step-by-step
4. **Share feedback** to improve the process

**Ready to start? Run:**
```bash
orchestrator intake new --type [your-project-type]
```
