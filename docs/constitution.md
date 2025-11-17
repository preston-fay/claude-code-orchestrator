# Project Constitution System

## Overview

The Constitution System provides a structured way to define and enforce fundamental principles, standards, and guardrails for your projects. Think of it as a "project charter" that all agents, code, and deliverables must adhere to throughout the development lifecycle.

**Key Benefits:**
- **Consistency**: All agents reference the same principles during execution
- **Quality**: Explicit standards reduce ambiguity and improve output quality
- **Onboarding**: New team members immediately understand project guardrails
- **Compliance**: Enforces client-specific requirements and Kearney standards
- **Audit Trail**: Constitution serves as a versioned record of project governance

## Quick Start

### 1. Generate Constitution from Intake

The easiest way to create a constitution is from your intake file:

```bash
# Auto-detects intake file in intake/ directory
orchestrator constitution generate

# Or specify intake file explicitly
orchestrator constitution generate --intake intake/my-project.yaml
```

This creates `.claude/constitution.md` with:
- **Code quality standards** based on project type (ML, analytics, webapp)
- **Security requirements** appropriate for data sensitivity
- **Kearney brand compliance** (RAISE framework, KDS colors/fonts)
- **Forbidden/required practices** from your intake configuration

### 2. Validate Constitution

Check that your constitution is well-formed:

```bash
orchestrator constitution validate
```

This verifies:
- Constitution file exists
- Required sections are present
- Document has sufficient content

### 3. Customize Constitution

Edit `.claude/constitution.md` to add project-specific requirements:

```markdown
## 📐 Code Quality Standards

### Mandatory Requirements
- All functions must have docstrings (Google style)
- Test coverage must be ≥80%
- No hardcoded credentials or API keys
- All SQL queries must use parameterized statements

### Testing Requirements
- Unit tests for all data transformations
- Integration tests for ETL pipeline end-to-end
- Model performance tests (accuracy, fairness, drift)
```

### 4. Use During Orchestration

The constitution is automatically enforced when you run the orchestrator:

```bash
orchestrator run start --intake intake/my-project.yaml
```

**How it's enforced:**
- **Planning Phase**: Architect reads constitution before proposing architecture
- **Development Phase**: Developer adheres to coding standards
- **QA Phase**: QA agent validates deliverables against constitution
- **Review Phase**: Reviewer checks compliance with principles

---

## Constitution Structure

### Core Sections

#### 1. Core Principles
Define the mission and values that guide all decisions:

```markdown
## 🎯 Core Principles

### Mission Statement
Build a production-grade ML model that predicts customer churn with 85%+ accuracy
while maintaining explainability for business stakeholders and regulatory compliance.

### Values
- **Reproducibility**: All experiments must be fully reproducible
- **Explainability**: Model decisions must be interpretable
- **Fairness**: Model tested for bias across customer segments
- **Privacy-First**: No PII in training data
```

#### 2. Code Quality Standards
Mandatory requirements for code:

```markdown
## 📐 Code Quality Standards

### Mandatory Requirements
- All Python functions must have docstrings (Google style)
- Test coverage must be ≥80%
- All code must pass `ruff` linting with zero errors
- Type hints required for all function signatures
- No hardcoded credentials or API keys
```

#### 3. User Experience Principles
Design and performance standards:

```markdown
## 🎨 User Experience (UX) Principles

### Design Consistency
- All dashboards use Kearney 6-color chart palette
- All visualizations have clear titles and axis labels
- All metrics include confidence intervals

### Performance Standards
- Inference API must respond in <100ms (P95)
- Dashboard queries must complete in <500ms
- Model retraining must complete in <4 hours
```

#### 4. Security & Privacy
Security requirements and data handling:

```markdown
## 🔒 Security & Privacy

### Security Standards
- All API endpoints require authentication (OAuth2 + JWT)
- All database connections use SSL/TLS
- Model artifacts must be signed and versioned

### Privacy Requirements
- No PII in training data (pseudonymize customer IDs)
- Data retention: Raw data deleted after 90 days
- GDPR compliance: Right to explanation for predictions
```

#### 5. Forbidden Practices
What NOT to do:

```markdown
## 🚫 Forbidden Practices

### Never Do This
- ❌ **Train/test split without time stratification**: Causes data leakage
- ❌ **Cherry-picking metrics**: Report all standard metrics (accuracy, precision, recall, F1)
- ❌ **Deploying models without explainability**: SHAP values required

### Technologies to Avoid
- ❌ pickle for model serialization (use joblib or ONNX)
- ❌ print() for logging (use proper logging library)
```

#### 6. Required Practices
What you MUST do:

```markdown
## ✅ Required Practices

### Always Do This
- ✅ **Version all experiments**: Use MLflow for tracking
- ✅ **Monitor drift**: Implement data drift and model drift detection
- ✅ **Test for bias**: Run fairness metrics across customer segments
```

#### 7. Kearney Standards
Firm-specific requirements:

```markdown
## 🎓 Kearney Standards

### RAISE Framework Compliance
- **R**igorous: Evidence-based decisions, validated assumptions
- **A**ctionable: Deliverables drive concrete business actions
- **I**nsightful: Deep understanding beyond surface observations
- **S**tructured: Clear methodology, reproducible analysis
- **E**ngaging: Compelling storytelling for C-suite audiences

### Brand Compliance
- All charts use Kearney color palette (primary: #7823DC)
- All fonts use Inter typeface
- All deliverables follow KDS (Kearney Design System)
```

#### 8. Phase-Specific Guidelines
Guidelines for each orchestrator phase:

```markdown
## 📋 Phase-Specific Guidelines

### Planning Phase
- Architect must document baseline model performance expectations
- Architect must specify train/validation/test split strategy
- Architect must identify potential bias risks and mitigation

### QA Phase
- QA must validate model performance on holdout test set
- QA must verify no data leakage (train/test contamination)
- QA must validate inference API meets latency requirements
```

---

## Creating Constitutions from Intake

### Intake Configuration

You can specify constitution principles directly in your `intake.yaml`:

```yaml
constitution:
  code_quality:
    - "All functions must have docstrings"
    - "Test coverage ≥ 90%"
    - "All database queries must use parameterized statements"

  ux_principles:
    - "All dashboards load in <2 seconds"
    - "All charts use Kearney brand colors"

  security:
    - "All API endpoints require authentication"
    - "No PII in application logs"

  data_quality:
    - "Missing value rate <5% per feature"
    - "All ETL pipelines have data validation checks"

  forbidden:
    - "No inline SQL in application code"
    - "No global variables"
    - "No hardcoded credentials"

  required:
    - "Use MLflow for experiment tracking"
    - "Use pytest for all tests"
```

### Project-Type Defaults

The generator adds sensible defaults based on project type:

**ML Projects:**
- Data quality standards (missing values, drift detection)
- Forbidden practices (data leakage, cherry-picking metrics)
- Required practices (experiment versioning, bias testing)

**Analytics Projects:**
- Data quality standards (>95% quality metrics)
- Performance standards (dashboard queries <500ms)
- ETL validation requirements

**Web App Projects:**
- UX performance standards (page load <2s, TTI <3s)
- Accessibility requirements (WCAG 2.1 AA)
- API response time standards (<200ms P95)

---

## Constitution Enforcement

### Automated Enforcement

The orchestrator enforces constitution through multiple mechanisms:

#### 1. Preflight Checks
Before starting a run, orchestrator validates:
- Constitution file exists
- Constitution is well-formed
- Required sections are present

```bash
# This will fail if no constitution exists:
orchestrator run start --intake intake/my-project.yaml
```

#### 2. Agent-Level Enforcement

**Architect Phase:**
- Reads constitution before proposing architecture
- Proposes designs that satisfy constitution requirements
- Documents compliance in Architecture Decision Records (ADRs)

**Developer Phase:**
- Implements code following coding standards
- Adheres to forbidden/required technology lists
- References constitution in code comments

**QA Phase:**
- Validates test coverage meets constitution threshold
- Checks code against forbidden practices
- Verifies performance standards are met

#### 3. CI/CD Enforcement

Add constitution checks to CI:

```yaml
# .github/workflows/ci.yml
- name: Validate constitution
  run: orchestrator constitution validate

- name: Check code against constitution
  run: |
    # This would be custom tooling
    python scripts/check_constitution_compliance.py
```

### Manual Enforcement

During code review, Reviewer agent checks:
- Code adheres to coding standards
- No forbidden practices are used
- Required practices are followed
- Documentation meets standards

---

## Best Practices

### 1. Start Simple, Iterate
Don't try to create a perfect constitution upfront:
- Generate baseline from intake
- Start workflow
- Add specific rules as issues arise
- Version and track changes

### 2. Be Specific, Not Vague
❌ **Vague**: "Code should be high quality"
✅ **Specific**: "Test coverage must be ≥80%, all functions must have docstrings"

❌ **Vague**: "Good performance"
✅ **Specific**: "API response time <200ms (P95), dashboard queries <500ms"

### 3. Document Rationale
Always explain WHY something is forbidden/required:

```markdown
- ❌ **Train/test split without time stratification**: Causes data leakage and overoptimistic metrics
- ✅ **Use MLflow for experiment tracking**: Ensures reproducibility and audit trail
```

### 4. Review and Update
Constitution should evolve with project:
- Review after each major phase
- Update based on lessons learned
- Version changes (use git)
- Communicate updates to team

### 5. Commit to Version Control
Your constitution is a critical project artifact:
```bash
git add .claude/constitution.md
git commit -m "chore: add project constitution"
git push
```

### 6. Use Constitution as Onboarding Doc
New team members should read:
1. README.md (what/why/how)
2. `.claude/constitution.md` (principles and standards)
3. `intake/project.intake.yaml` (requirements and goals)

---

## Constitution vs. Other Artifacts

| Artifact | Purpose | When to Use |
|----------|---------|-------------|
| **Constitution** | Fundamental principles and guardrails | Project-wide standards that rarely change |
| **Intake** | Requirements, goals, constraints | Initial project specification |
| **ADR** | Specific technical decisions | Document "why" for major tech choices |
| **Governance** | Client-specific compliance rules | Client mandates (test coverage, security scans) |
| **Skills** | Reusable methodologies | Analytical patterns (time-series, clustering) |

**Example Hierarchy:**
- Constitution says: "All models must be explainable"
- Intake says: "Build churn prediction model"
- ADR says: "Use SHAP for explainability (ADR-005)"
- Governance says: "Test coverage ≥ 90%" (client requirement)

---

## Troubleshooting

### "Constitution not found" Error

```
❌ Constitution not found at .claude/constitution.md
Run 'orchestrator constitution generate' to create one.
```

**Solution:**
```bash
orchestrator constitution generate --intake intake/my-project.yaml
```

### "Missing required sections" Error

```
❌ Constitution is missing required sections: ## 📐 Code Quality Standards
```

**Solution:** Your constitution is incomplete. Copy sections from:
- `.claude/templates/constitution.example.ml.md` (for ML projects)
- `.claude/templates/constitution.md` (template format)

### Constitution Feels Too Rigid

If constitution is blocking legitimate work:

1. **Review and revise**: Are rules too strict?
2. **Add exceptions**: Document when rules don't apply
3. **Use ADRs**: Document deviations with rationale

```markdown
## Exceptions

In the following cases, constitution rules may be relaxed:
- Prototypes and proof-of-concept code (mark with `# PROTOTYPE` comment)
- Generated code from external tools
- Third-party dependencies (cannot modify)
```

### Constitution Violations Not Detected

The automated checker has limited heuristics. For comprehensive checks:

1. Use dedicated linters (ruff, pylint, mypy)
2. Add custom checks in CI
3. Rely on code review by Reviewer agent
4. Update checker heuristics in `src/orchestrator/constitution/validator.py`

---

## Examples

### ML Project Constitution
See: `.claude/templates/constitution.example.ml.md`

Highlights:
- Data quality standards (missing values <5%)
- Forbidden: train/test leakage, cherry-picking metrics
- Required: MLflow tracking, bias testing

### Analytics Project Constitution

```markdown
## 📐 Code Quality Standards
- All SQL queries must be in `queries/` directory
- All dbt models must have data tests
- Data dictionary required for all datasets

## 🚫 Forbidden Practices
- ❌ **SELECT * in production queries**: Explicitly list columns
- ❌ **No CTEs in complex queries**: Use dbt models instead
- ❌ **Unparameterized dates**: Use config variables

## ✅ Required Practices
- ✅ **dbt for transformations**: All SQL transformations via dbt
- ✅ **Great Expectations for validation**: Data quality checks
- ✅ **Airflow for orchestration**: Schedule all ETL jobs
```

### Web App Constitution

```markdown
## 🎨 UX Principles
- Page load time <2 seconds (Lighthouse score ≥90)
- All interactive elements keyboard accessible
- Mobile-first responsive design

## 🚫 Forbidden Practices
- ❌ **Inline styles**: Use CSS modules or styled-components
- ❌ **Direct DOM manipulation**: Use React state/props
- ❌ **console.log in production**: Use proper logging

## ✅ Required Practices
- ✅ **TypeScript for all new code**: Catch errors at compile time
- ✅ **React Testing Library**: Test user behavior, not implementation
- ✅ **Storybook for components**: Visual regression testing
```

---

## CLI Reference

### `orchestrator constitution generate`

Generate a constitution from intake configuration.

**Options:**
- `--intake, -i PATH`: Path to intake.yaml (auto-detects if omitted)
- `--output, -o PATH`: Output path (default: .claude/constitution.md)
- `--force, -f`: Overwrite existing constitution without prompting

**Examples:**
```bash
# Auto-detect intake file
orchestrator constitution generate

# Specify intake explicitly
orchestrator constitution generate --intake intake/ml-project.yaml

# Force overwrite existing constitution
orchestrator constitution generate --force
```

### `orchestrator constitution validate`

Validate constitution file.

**Options:**
- `--constitution, -c PATH`: Path to constitution (default: .claude/constitution.md)

**Examples:**
```bash
# Validate default constitution
orchestrator constitution validate

# Validate custom path
orchestrator constitution validate --constitution docs/project-charter.md
```

### `orchestrator constitution check`

Check if constitution exists and show stats.

**Examples:**
```bash
orchestrator constitution check
# ✅ Constitution found: .claude/constitution.md
# 📊 Stats: 425 lines, 3,842 words
```

---

## For AI Coding Academy

### Teaching Constitution-Driven Development

**Module 1: Understanding Constitutions**
- What is a project constitution?
- Why are explicit principles important?
- Constitution vs. requirements vs. implementation

**Module 2: Creating Constitutions**
- Exercise: Generate constitution from intake
- Exercise: Customize for project domain
- Exercise: Identify vague vs. specific standards

**Module 3: Enforcing Constitutions**
- How agents use constitution during workflow
- Automated enforcement (preflight, QA)
- Manual enforcement (code review)

**Module 4: Real-World Application**
- Case study: ML project with bias requirements
- Case study: Client project with compliance mandates
- Exercise: Write constitution for capstone project

### Grading Rubric

Constitution quality assessment:
- **Specificity** (30%): Are standards measurable and actionable?
- **Completeness** (25%): Are all required sections present?
- **Rationale** (20%): Are forbidden/required practices justified?
- **Relevance** (15%): Do standards match project domain?
- **Enforceability** (10%): Can standards be automatically checked?

---

## Next Steps

1. **Generate your first constitution:**
   ```bash
   orchestrator constitution generate
   ```

2. **Review and customize** `.claude/constitution.md`

3. **Commit to version control:**
   ```bash
   git add .claude/constitution.md
   git commit -m "feat: add project constitution"
   ```

4. **Start orchestrator with constitution enforcement:**
   ```bash
   orchestrator run start --intake intake/my-project.yaml
   ```

5. **Iterate based on experience** - Update constitution as you learn what standards matter most

---

**Related Documentation:**
- [Intake System](./intake.md) - Project specification and requirements
- [Architecture Decision Records](../. claude/decisions/README.md) - Documenting technical choices
- [Client Governance](../clients/README.md) - Client-specific compliance
- [Kearney Standards](../.claude/knowledge/kearney/) - Firm-wide best practices
