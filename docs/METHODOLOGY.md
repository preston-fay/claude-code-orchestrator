# Orchestrator Methodology

A comprehensive guide to the philosophy, architecture, and workflows of the Claude Code Orchestrator.

---

## Table of Contents

1. [Introduction](#introduction)
2. [Core Philosophy](#core-philosophy)
3. [Multi-Agent Architecture](#multi-agent-architecture)
4. [Checkpoint-Driven Workflow](#checkpoint-driven-workflow)
5. [The Skills System](#the-skills-system)
6. [Knowledge Architecture](#knowledge-architecture)
7. [Decision Records (ADRs)](#decision-records-adrs)
8. [Quality Gates & Governance](#quality-gates--governance)
9. [Brand Compliance](#brand-compliance)
10. [When to Use the Orchestrator](#when-to-use-the-orchestrator)
11. [Comparison to Other Approaches](#comparison-to-other-approaches)
12. [Real-World Workflows](#real-world-workflows)

---

## Introduction

The Claude Code Orchestrator is a **meta-framework** for building complex software projects using multiple specialized AI agents working collaboratively. Unlike single-agent approaches where one AI tries to do everything, the orchestrator coordinates specialized agents (Architect, Data, Developer, QA, Documentarian, Consensus) through a structured, checkpoint-driven workflow.

**Key Innovation:** Separating *orchestration logic* (workflow coordination, quality gates, consensus) from *execution logic* (agent-specific tasks) enables:

- **Scalability**: Add new agents without modifying orchestration
- **Quality**: Enforce quality gates and consensus before proceeding
- **Traceability**: Checkpoint artifacts create audit trail
- **Iteration**: Rollback and retry failed phases without starting over

**Target Audience:**

- Data scientists building analytics pipelines
- ML engineers training and deploying models
- Software developers building web applications
- Consultants delivering client projects with strict governance

---

## Core Philosophy

### 1. Separation of Concerns

Each agent has a **single, well-defined responsibility**:

- **Architect**: Design system architecture, propose technical approach
- **Data**: Handle data pipelines, ETL, feature engineering, model training
- **Developer**: Implement features, write application code
- **QA**: Test functionality, validate requirements, ensure quality
- **Documentarian**: Create documentation, user guides, README files
- **Consensus**: Review proposals, identify conflicts, build agreement
- **Steward**: Maintain repository health, identify technical debt

**Why this matters:** Agents with narrow scope produce higher-quality outputs than generalist agents trying to do everything.

**Example:**

```
❌ Single agent approach:
"Build a demand forecasting model and deploy it as a web app"
→ Agent tries to do architecture, data science, frontend, backend, testing
→ Produces mediocre results across all dimensions

✅ Orchestrator approach:
1. Architect designs system (API, database, model serving)
2. Data builds and validates model
3. Developer implements web UI and API
4. QA tests end-to-end functionality
5. Documentarian creates user guide
→ Each agent excels in their domain
```

### 2. Explicit Handoffs with Validation

Agents don't communicate directly. Instead, they produce **checkpoint artifacts** that:

1. **Document their work** (code, reports, decisions)
2. **Are validated** by the orchestrator (completeness, quality)
3. **Are reviewed** by Consensus agent at critical junctures
4. **Inform subsequent agents** (e.g., Developer reads Architect's design)

**Why this matters:** Explicit artifacts prevent miscommunication and create accountability.

**Example Handoff:**

```
Architect produces:
  ├── .claude/checkpoints/planning/architecture.md
  ├── .claude/checkpoints/planning/data_model.sql
  └── .claude/decisions/ADR-001-use-fastapi.md

↓ Orchestrator validates artifacts exist and are complete

↓ Consensus reviews and approves

Developer reads:
  ├── architecture.md → Understands system design
  ├── data_model.sql → Knows database schema
  └── ADR-001 → Understands why FastAPI was chosen

Developer implements based on approved architecture
```

### 3. Consensus-Driven Decision Making

For critical decisions (architecture, data model, deployment strategy), the **Consensus agent** reviews proposals before the workflow proceeds.

**Consensus Review Process:**

1. Agent (e.g., Architect) completes phase and produces artifacts
2. Orchestrator generates `.claude/consensus/REQUEST.md` with:
   - Summary of agent outputs
   - Required artifacts checklist
   - Validation results
   - Reviewer checklist
3. Consensus agent reviews REQUEST.md
4. Human approves (`orchestrator run approve`) or rejects
5. Workflow proceeds or agent retries with feedback

**Why this matters:** Prevents downstream rework from bad early decisions.

**Example:**

```
Architect proposes microservices architecture for 3-user internal tool

Consensus reviews:
❌ "Microservices add unnecessary complexity for this use case"
→ Requests simplification to monolith

Architect revises proposal:
✅ "Monolith with modular structure for future extraction"
→ Approved, workflow continues
```

### 4. Iterative Refinement with Quality Gates

Each phase has **quality gates** that must pass before proceeding:

- **Test Coverage**: Min 80% (configurable per client)
- **Security Scan**: No high/critical vulnerabilities
- **Documentation**: README, API docs, user guide present
- **Brand Compliance**: Colors, fonts, terminology match governance
- **Repository Hygiene**: No large files, secrets, or notebook outputs

**Why this matters:** Catches problems early when they're cheap to fix.

**Example Quality Gate Failure:**

```bash
orchestrator run next  # QA phase completes

Quality Gate Check:
❌ Test coverage: 65% (threshold: 80%)
❌ Security scan: 2 high vulnerabilities found
✅ Documentation: Complete
✅ Brand compliance: Passed

Phase cannot proceed. Fix issues and retry:
orchestrator run retry --phase qa
```

---

## Multi-Agent Architecture

### Agent Roles and Responsibilities

#### Architect

**Responsibilities:**
- Read intake YAML to understand requirements
- Design system architecture (components, data flows, APIs)
- Propose technology stack with rationale
- Create data models and schemas
- Document decisions in ADRs
- Produce architecture diagrams and specifications

**Inputs:**
- `intake.yaml` - Project requirements
- `.claude/knowledge/` - Best practices and standards
- `.claude/skills/` - Applicable methodologies
- `clients/<client>/governance.yaml` - Client constraints

**Outputs:**
- `.claude/checkpoints/planning/architecture.md`
- `.claude/checkpoints/planning/data_model.sql` (if applicable)
- `.claude/decisions/ADR-001-*.md` (architecture decisions)
- Diagrams, flowcharts, system design docs

**When to Invoke:** First phase of every project

---

#### Data

**Responsibilities:**
- Ingest raw data from sources
- Validate data quality (completeness, accuracy, consistency)
- Transform and engineer features
- Train models (for ML projects)
- Evaluate model performance
- Document data lineage and schemas

**Inputs:**
- Architecture from Architect (data model, pipeline design)
- `data/raw/` - Raw data files
- `.claude/knowledge/projects/` - Domain knowledge, business rules
- `.claude/skills/time_series_analytics.yaml` (example)

**Outputs:**
- `data/processed/` - Clean, analysis-ready data
- `models/` - Trained model artifacts (pkl, h5, pt)
- `models/metrics.json` - Model performance metrics
- `docs/data_documentation.md` - Data dictionary, lineage
- `.claude/checkpoints/data/validation_report.md`

**When to Invoke:** Analytics and ML projects

---

#### Developer

**Responsibilities:**
- Implement features based on architecture
- Write clean, maintainable, tested code
- Follow coding standards and best practices
- Create APIs, UIs, backend services
- Handle error cases and edge conditions

**Inputs:**
- Architecture from Architect
- Data/models from Data agent (if applicable)
- `.claude/knowledge/kearney_standards.yaml` - Code quality expectations
- `clients/<client>/governance.yaml` - Brand constraints

**Outputs:**
- `src/` - Application source code
- `tests/` - Unit and integration tests
- API documentation (OpenAPI/Swagger)
- Database migrations (if applicable)

**When to Invoke:** All projects after architecture phase

---

#### QA

**Responsibilities:**
- Validate functionality against requirements
- Write and execute test cases
- Run test suite and measure coverage
- Identify bugs and edge cases
- Verify non-functional requirements (performance, security)

**Inputs:**
- Requirements from `intake.yaml`
- Code from Developer
- `.claude/checkpoints/planning/architecture.md` - Expected behavior
- `clients/<client>/governance.yaml` - Quality thresholds

**Outputs:**
- `tests/` - Test suites (unit, integration, e2e)
- Test coverage report (`htmlcov/index.html`)
- `.claude/checkpoints/qa/test_report.md`
- Bug reports (if issues found)

**When to Invoke:** After development phase

---

#### Documentarian

**Responsibilities:**
- Create comprehensive README
- Write user guides and tutorials
- Document APIs and data schemas
- Create deployment guides
- Ensure documentation accuracy and completeness

**Inputs:**
- All previous phase outputs
- Codebase (`src/`, `tests/`)
- Architecture documentation
- `clients/<client>/governance.yaml` - Documentation requirements

**Outputs:**
- `README.md` - Project overview, setup, usage
- `docs/user_guide.md` - End-user documentation
- `docs/api_reference.md` - API documentation
- `docs/deployment_guide.md` - Deployment instructions
- `CONTRIBUTING.md` - Contribution guidelines

**When to Invoke:** After QA phase (near project completion)

---

#### Consensus

**Responsibilities:**
- Review proposals from other agents
- Identify conflicts and inconsistencies
- Validate decisions against requirements
- Request clarifications or revisions
- Approve or reject phase completion

**Inputs:**
- `.claude/consensus/REQUEST.md` - Generated by orchestrator
- All checkpoint artifacts from completed phase
- Validation results from orchestrator

**Outputs:**
- `.claude/consensus/DECISION.md` - Approval or rejection
- Feedback for revision (if rejected)

**When to Invoke:** After critical phases (planning, before deployment)

---

#### Steward

**Responsibilities:**
- Scan repository for hygiene issues
- Identify large files, secrets, notebook outputs
- Detect dead code and orphaned files
- Calculate cleanliness score
- Generate hygiene report

**Inputs:**
- Entire repository

**Outputs:**
- `reports/repo_hygiene_report.md`
- `docs/badges/cleanliness.svg` - Badge for README

**When to Invoke:** Before PRs, releases, or on-demand

---

## Checkpoint-Driven Workflow

### What is a Checkpoint?

A **checkpoint** is a validated milestone in the project lifecycle. Each phase produces checkpoint artifacts that must meet completeness and quality criteria before the workflow proceeds.

**Checkpoint Artifacts:**

```
.claude/checkpoints/
├── planning/
│   ├── architecture.md          ← System design
│   ├── data_model.sql           ← Database schema
│   └── technical_spec.md        ← Implementation details
├── data/
│   ├── validation_report.md     ← Data quality results
│   ├── feature_engineering.md   ← Feature descriptions
│   └── model_card.md            ← Model documentation
├── development/
│   ├── implementation_notes.md  ← Dev decisions
│   └── api_design.md            ← API contracts
├── qa/
│   ├── test_report.md           ← Test results
│   └── coverage_summary.txt     ← Coverage metrics
└── documentation/
    └── deliverables_checklist.md
```

### Checkpoint Validation

Before allowing workflow to proceed, orchestrator validates:

1. **Artifact Existence**: Required files present
2. **Artifact Completeness**: Files not empty, contain expected sections
3. **Quality Gates**: Coverage, security, hygiene thresholds met
4. **Consensus**: Critical checkpoints reviewed and approved

**Example Validation:**

```python
def validate_planning_checkpoint():
    required_artifacts = [
        '.claude/checkpoints/planning/architecture.md',
        '.claude/decisions/ADR-001-*.md',  # At least one ADR
    ]

    for artifact in required_artifacts:
        if not exists(artifact):
            raise CheckpointValidationError(f"Missing: {artifact}")

        if file_size(artifact) < 100:  # bytes
            raise CheckpointValidationError(f"Incomplete: {artifact}")

    # Validate architecture.md has required sections
    arch_doc = read_file('.claude/checkpoints/planning/architecture.md')
    required_sections = ['System Design', 'Data Model', 'Technology Stack']
    for section in required_sections:
        if section not in arch_doc:
            raise CheckpointValidationError(f"Missing section: {section}")
```

### Checkpoint Benefits

1. **Rollback**: Can return to any checkpoint without losing work
2. **Resume**: Abort workflow and resume from last checkpoint
3. **Audit Trail**: Checkpoints document decisions and progress
4. **Parallel Work**: Multiple agents can work concurrently if checkpoints are independent

---

## The Skills System

### What are Skills?

**Skills** are reusable analytical patterns stored as YAML files in `.claude/skills/`. Each skill encapsulates:

- **Methodology**: Step-by-step approach
- **When to Use**: Applicability criteria
- **Tools Required**: Dependencies
- **Validation Criteria**: Success metrics
- **Common Pitfalls**: What to avoid

### Skill Categories

1. **Analytics** (`category: analytics`)
   - Time series forecasting
   - A/B testing
   - Cohort analysis
   - Survey analysis

2. **Machine Learning** (`category: ml`)
   - Model selection
   - Hyperparameter tuning
   - Feature engineering
   - Model evaluation

3. **Optimization** (`category: optimization`)
   - Linear programming
   - Network optimization
   - Simulation
   - Heuristic algorithms

4. **Survey** (`category: survey`)
   - Questionnaire design
   - Response analysis
   - Sentiment analysis
   - Statistical testing

### How Agents Use Skills

**Discovery:**

```python
# Agent scans .claude/skills/ for relevant skills
skills = glob('.claude/skills/*.yaml')

# Filter by category and keywords from intake
relevant_skills = [
    s for s in skills
    if 'forecasting' in intake.requirements
    and s.category == 'analytics'
]
```

**Selection:**

```python
# Agent reads skill YAML
skill = yaml.load('.claude/skills/time_series_analytics.yaml')

# Checks applicability
if 'temporal' in data_characteristics and 'predict' in requirements:
    selected_skill = skill
```

**Adaptation:**

```python
# Agent adapts methodology to project context
methodology = skill['methodology']
for step in methodology:
    # Apply step with project-specific data/constraints
    adapted_step = customize_step(step, project_context)
    execute(adapted_step)
```

**Documentation:**

```python
# Agent documents skill usage in checkpoint
checkpoint.write(f"""
## Methodology

This analysis follows the {skill['name']} approach from
.claude/skills/{skill_file}. Key adaptations:

- Step 2 modified to use Prophet instead of ARIMA (better handles
  multiple seasonality in our data)
- Step 4 skipped (insufficient data for external regressor features)

See ADR-002 for rationale.
""")
```

### Creating New Skills

**When to create a skill:**

- You've solved a problem that will recur across projects
- You want to establish a firm-wide standard approach
- You're codifying lessons learned from past projects

**How to create a skill:**

```bash
# 1. Copy skill template
cp .claude/skills/template.yaml .claude/skills/my_new_skill.yaml

# 2. Fill in structure
vim .claude/skills/my_new_skill.yaml
```

**Skill YAML Structure:**

```yaml
name: "Time Series Forecasting"
category: "analytics"
description: "Forecast future values from temporal data"

when_to_use: |
  - Data has temporal ordering (timestamps)
  - Goal is to predict future values
  - Historical patterns are expected to continue

methodology:
  - step: "Visualize time series"
    rationale: "Identify trends, seasonality, anomalies"
    tools: ["matplotlib", "plotly"]

  - step: "Test for stationarity"
    rationale: "Determine if differencing needed"
    tools: ["statsmodels.tsa.stattools.adfuller"]

  - step: "Select model approach"
    rationale: "Choose ARIMA, Prophet, LSTM based on data characteristics"
    decision_criteria:
      - "Single seasonality → ARIMA"
      - "Multiple seasonality → Prophet"
      - "Complex non-linear → LSTM"

  - step: "Train and validate"
    rationale: "Fit model on training set, validate on holdout"
    validation: "MAPE < 10% on validation set"

  - step: "Generate forecasts"
    rationale: "Produce predictions with confidence intervals"

tools_required:
  - "python >= 3.9"
  - "pandas >= 1.3"
  - "statsmodels >= 0.13"
  - "prophet >= 1.1"  # optional
  - "tensorflow >= 2.10"  # optional for LSTM

validation_criteria: |
  - Model fits training data (R² > 0.7)
  - Validation MAPE < 15%
  - Forecast includes confidence intervals
  - Residuals are white noise (Ljung-Box p > 0.05)

common_pitfalls:
  - "Overfitting to noise in historical data"
  - "Not accounting for structural breaks (COVID, policy changes)"
  - "Using too short a training window"
  - "Ignoring external regressors (holidays, promotions)"

references:
  - "Forecasting: Principles and Practice (Hyndman & Athanasopoulos)"
  - "https://otexts.com/fpp3/"
```

---

## Knowledge Architecture

### Three-Tier Knowledge System

The orchestrator uses a **hierarchical knowledge base** with three levels of specificity:

```
┌─────────────────────────────────────────┐
│   Project-Specific Knowledge            │  ← Most specific
│   (.claude/knowledge/projects/)         │
├─────────────────────────────────────────┤
│   Firm-Wide Knowledge                   │  ← Kearney standards
│   (.claude/knowledge/kearney/)          │
├─────────────────────────────────────────┤
│   Universal Knowledge                   │  ← Data science fundamentals
│   (.claude/knowledge/universal/)        │
└─────────────────────────────────────────┘
```

### Knowledge Hierarchy (Most Specific Wins)

When agents need information, they check knowledge sources in order:

1. **Project-specific** first (e.g., "fiscal year = July-June")
2. **Firm-wide** second (e.g., "use RAISE framework for storytelling")
3. **Universal** last (e.g., "normalize features before modeling")

**Example Conflict Resolution:**

```yaml
# Universal knowledge: analytics_best_practices.yaml
best_practices:
  date_handling: "Use calendar year (Jan-Dec) unless specified"

# Firm-wide knowledge: kearney_standards.yaml
standards:
  # No override on date handling

# Project-specific knowledge: retail-client.yaml
domain_knowledge:
  fiscal_calendar: "Fiscal year is Feb-Jan"

# Agent reads all three, applies project-specific:
fiscal_year = "Feb-Jan"  # Project overrides universal
```

### Universal Knowledge

**Location:** `.claude/knowledge/universal/`

**Contents:**
- Data science fundamentals
- Statistical best practices
- Software engineering patterns
- Testing methodologies
- Security best practices

**Example:** `analytics_best_practices.yaml`

```yaml
data_quality:
  completeness: "Check for missing values, document imputation strategy"
  accuracy: "Validate against source systems, spot-check samples"
  consistency: "Cross-check related fields (revenue = price × quantity)"

exploratory_analysis:
  - "Visualize distributions (histograms, box plots)"
  - "Check correlations (heatmap)"
  - "Identify outliers (z-score, IQR)"
  - "Document assumptions and limitations"

modeling:
  train_test_split: "80/20 or 70/30, stratified if classification"
  cross_validation: "5-fold or 10-fold for small datasets"
  evaluation_metrics:
    regression: ["MAE", "RMSE", "R²"]
    classification: ["Accuracy", "Precision", "Recall", "F1", "AUC-ROC"]
```

### Firm-Wide Knowledge

**Location:** `.claude/knowledge/kearney/`

**Contents:**
- Kearney RAISE framework (storytelling)
- Brand compliance (fonts, colors, terminology)
- Quality standards (test coverage, documentation)
- Client engagement best practices

**Example:** `kearney_standards.yaml`

```yaml
raise_framework:
  situation: "Set context: What is the current state?"
  action: "What did we do? Methodology and approach"
  impact: "What changed? Quantifiable outcomes"
  story: "Connect the dots: Why does this matter?"
  example: "Illustrate with specific case or data point"

deliverable_standards:
  presentations:
    font: "Arial (NOT Inter for presentations)"
    colors: ["#7823DC (purple)", "#FFFFFF (white)", "#000000 (black)"]
    charts: "NO gridlines, label-first approach"

  code:
    test_coverage: "Minimum 80%"
    documentation: "README, API docs, deployment guide required"

quality_gates:
  before_client_review:
    - "Spell check all deliverables"
    - "Verify brand compliance"
    - "Run end-to-end demo"
    - "Peer review by senior consultant"
```

### Project-Specific Knowledge

**Location:** `.claude/knowledge/projects/<project-slug>.yaml`

**Contents:**
- Domain terminology (acronyms, jargon)
- Business rules (churn definition, segmentation logic)
- Data schemas (field names, types, constraints)
- Client-specific constraints (must use on-prem SQL Server)

**Example:** `retail-forecasting.yaml`

```yaml
project: "Retail Demand Forecasting"

domain_terminology:
  SKU: "Stock Keeping Unit (product identifier)"
  POS: "Point of Sale (transaction data)"
  DC: "Distribution Center (warehouse location)"

business_rules:
  stockout: "Zero inventory for 3+ consecutive days"
  promotion: "Price discount >= 15% from baseline"
  seasonality: "Back-to-school (Aug-Sep), Holiday (Nov-Dec)"

data_schemas:
  sales_table:
    - "sku_id (VARCHAR(20)): Unique product identifier"
    - "store_id (INT): Store number (1-500)"
    - "sale_date (DATE): Transaction date"
    - "quantity (INT): Units sold"
    - "revenue (DECIMAL(10,2)): Total sales dollars"

constraints:
  - "Must use client's on-premises SQL Server (no cloud)"
  - "Cannot use external data sources (GDPR restrictions)"
  - "Forecasts must be weekly granularity (not daily)"
```

### When to Add Knowledge

**During Project Intake:**

```bash
# Create project knowledge file
cp .claude/knowledge/projects/README.md \
   .claude/knowledge/projects/my-project.yaml

# Document domain knowledge from kickoff meetings
vim .claude/knowledge/projects/my-project.yaml
```

**During Architecture Phase:**

```bash
# Architect adds data schema documentation
# to project knowledge file
```

**During Data Phase:**

```bash
# Data agent adds discovered business rules
# (e.g., "Orders with status='CANCELLED' should be excluded")
```

---

## Decision Records (ADRs)

### What are ADRs?

**Architecture Decision Records (ADRs)** document significant technical decisions made during the project. They capture:

- **Context**: What problem are we solving?
- **Decision**: What did we decide?
- **Rationale**: Why this option over alternatives?
- **Alternatives**: What else was considered?
- **Consequences**: What are the tradeoffs?
- **Status**: Proposed / Accepted / Superseded

### When to Create ADRs

**Planning Phase:**
- Technology stack selection (FastAPI vs Flask vs Django)
- Database choice (PostgreSQL vs MongoDB vs DynamoDB)
- Architecture pattern (monolith vs microservices vs serverless)

**Data Phase:**
- Model selection (Prophet vs ARIMA vs LSTM)
- Feature engineering decisions (why feature X was created)
- Data pipeline design (batch vs streaming)

**Development Phase:**
- State management approach (Redux vs Context API vs Zustand)
- Authentication method (JWT vs session cookies vs OAuth)
- Deployment strategy (Docker vs serverless vs VMs)

### ADR Workflow

1. **Agent proposes decision** by creating ADR (status: Proposed)
2. **Consensus reviews** ADR during consensus phase
3. **Consensus approves** (status: Accepted) or requests revision
4. **Future agents reference** ADR when implementing

**Example:**

```markdown
# ADR-003: Use Prophet for Demand Forecasting

## Status
Accepted (2025-01-15)

## Context
We need to forecast weekly product demand for 500 SKUs across 50 stores.
Data shows strong weekly and yearly seasonality, plus promotional effects.

## Decision
Use Facebook Prophet for time-series forecasting.

## Rationale
- Handles multiple seasonality (weekly + yearly) out of the box
- Built-in support for holidays and promotions (external regressors)
- Robust to missing data and outliers
- Produces interpretable components (trend, seasonality, holidays)
- Fast training (critical for 25K forecasts: 500 SKUs × 50 stores)

## Alternatives Considered

### ARIMA
- ❌ Poor handling of multiple seasonality
- ❌ Requires manual differencing and parameter tuning
- ✅ Lightweight, well-understood

### LSTM (Deep Learning)
- ❌ Requires large amounts of data (we have 2 years, need 5+)
- ❌ Black box, hard to interpret for business stakeholders
- ❌ Slow training (not feasible for 25K forecasts)
- ✅ Can model complex non-linear patterns

## Consequences

### Positive
- Fast iteration (can retrain all forecasts in < 30 minutes)
- Interpretable results (can show business "back-to-school drives 20% lift")
- Handles promotions and holidays automatically

### Negative
- Less flexible than LSTM for capturing complex interactions
- Assumes multiplicative seasonality (may not fit all SKUs)
- Requires external library (fbprophet) which can be finicky to install

## Implementation Notes
- Use `Prophet(seasonality_mode='multiplicative')` for most SKUs
- For SKUs with zero sales periods, use `'additive'` mode
- Add promotion flag as external regressor: `model.add_regressor('promo')`

## References
- Prophet documentation: https://facebook.github.io/prophet/
- Comparison study: "Forecasting at Scale" (Taylor & Letham, 2018)
```

### ADR Numbering

- **Sequential**: ADR-001, ADR-002, ADR-003, ...
- **Number assigned when created** (not when accepted)
- **Gaps are OK** (deleted or abandoned ADRs)

### When NOT to Create ADRs

- Trivial decisions (variable naming, file organization)
- Easily reversible decisions (color of a button)
- Implementation details (document in code comments instead)

---

## Quality Gates & Governance

### What are Quality Gates?

**Quality gates** are automated checks that must pass before a phase can complete. They enforce minimum standards for code quality, security, documentation, and brand compliance.

### Default Quality Gates

1. **Test Coverage**: Minimum 70% (configurable)
2. **Security Scan**: No high or critical vulnerabilities
3. **Documentation**: README and user guide present
4. **Repository Hygiene**: No large files, secrets, or notebook outputs

### Client-Specific Governance

Clients can override defaults with custom governance in `clients/<client>/governance.yaml`.

**Example:** High-security client

```yaml
client_name: "high-security-bank"

quality_gates:
  min_test_coverage: 95  # Higher than default 70%
  security_scan_required: true
  require_documentation: true

compliance:
  frameworks:
    - "SOC2"
    - "PCI-DSS"
    - "GDPR"

  soc2:
    audit_trail: true  # Log all data access
    change_management: true  # Require approval for deployments

  pci_dss:
    encrypt_at_rest: true
    encrypt_in_transit: true
    key_rotation_days: 90

brand_constraints:
  colors:
    - "#003DA5"  # Bank blue
    - "#FFFFFF"
    - "#000000"
  fonts:
    - "Arial"
    - "Helvetica Neue"
  forbidden_terms:
    - "cheap"
    - "discount"
    - "bargain"  # Bank wants premium positioning

deployment:
  approval_required: true
  approvers:
    - "cto@bank.com"
    - "ciso@bank.com"
  deployment_windows:
    - "Sunday 02:00-06:00 UTC"  # Only deploy during maintenance window

notifications:
  slack_webhook: "https://hooks.slack.com/services/XXX"
  email:
    - "pm@bank.com"
    - "tech-lead@bank.com"
```

### Quality Gate Enforcement

**Before Phase Completion:**

```python
def validate_quality_gates(phase, governance):
    failures = []

    # Test coverage
    coverage = run_coverage_report()
    min_coverage = governance['quality_gates']['min_test_coverage']
    if coverage < min_coverage:
        failures.append(f"Coverage {coverage}% < threshold {min_coverage}%")

    # Security scan
    if governance['quality_gates']['security_scan_required']:
        vulns = run_security_scan()
        high_vulns = [v for v in vulns if v.severity in ['HIGH', 'CRITICAL']]
        if high_vulns:
            failures.append(f"{len(high_vulns)} high/critical vulnerabilities")

    # Documentation
    if governance['quality_gates']['require_documentation']:
        if not exists('README.md'):
            failures.append("Missing README.md")
        if not exists('docs/user_guide.md'):
            failures.append("Missing user guide")

    if failures:
        raise QualityGateFailure("\n".join(failures))
```

---

## Brand Compliance

### Why Brand Compliance Matters

For client-facing deliverables, brand consistency builds trust and professionalism. The orchestrator enforces brand compliance automatically.

### Brand Compliance Rules

**Fonts:**
- **Presentations (C-suite)**: Arial
- **Web Applications**: Inter
- **Documentation**: System fonts (browser default)

**Colors:**
- **Kearney Purple**: `#7823DC` (accent, CTAs)
- **Neutral**: Black, white, grays
- **Data Viz**: Colorblind-safe palettes (Tableau, Viridis)

**Charts:**
- **NO gridlines** (Kearney mandates clean charts)
- **Label-first** (direct labels, not legends when possible)
- **High contrast** (legible in print and projection)

**Terminology:**
- **Avoid**: "cheap", "discount", "bargain" (unless client requests)
- **Prefer**: "value", "investment", "strategic"

### Automated Compliance Checks

**In Repo Hygiene Scan:**

```python
def check_brand_compliance(governance):
    violations = []

    # Check CSS files for forbidden colors
    css_files = glob('**/*.css', recursive=True)
    for css_file in css_files:
        content = read_file(css_file)

        # Extract hex colors
        colors = re.findall(r'#[0-9A-Fa-f]{6}', content)

        allowed_colors = governance['brand_constraints']['colors']
        for color in colors:
            if color.upper() not in [c.upper() for c in allowed_colors]:
                violations.append(
                    f"{css_file}: Unapproved color {color}"
                )

    # Check HTML files for forbidden fonts
    html_files = glob('**/*.html', recursive=True)
    for html_file in html_files:
        content = read_file(html_file)

        # Extract font families
        fonts = re.findall(r'font-family:\s*([^;]+)', content)

        allowed_fonts = governance['brand_constraints']['fonts']
        for font in fonts:
            if not any(af in font for af in allowed_fonts):
                violations.append(
                    f"{html_file}: Unapproved font {font}"
                )

    return violations
```

---

## When to Use the Orchestrator

### Ideal Use Cases

✅ **Complex multi-phase projects** (design → data → dev → QA → deploy)
✅ **Client projects with strict governance** (compliance, brand, quality)
✅ **ML/analytics with deployment** (model training + productionization)
✅ **Projects requiring audit trail** (regulated industries, public sector)
✅ **Team collaboration** (multiple people working on same project)

### When NOT to Use Orchestrator

❌ **One-off scripts** (ETL script, data cleaning notebook)
❌ **Proof-of-concept / prototypes** (orchestrator overhead not worth it)
❌ **Trivial projects** (< 100 lines of code)
❌ **No quality requirements** (internal tools, experiments)

### Decision Framework

```
┌─────────────────────────────────────┐
│ Does project have multiple phases?  │
│ (architecture, data, dev, QA, docs) │
└───────────┬─────────────────────────┘
            │ YES
            ▼
┌─────────────────────────────────────┐
│ Client governance or compliance?    │
│ (SOC2, GDPR, brand requirements)    │
└───────────┬─────────────────────────┘
            │ YES
            ▼
┌─────────────────────────────────────┐
│ Need audit trail of decisions?      │
│ (ADRs, checkpoint artifacts)        │
└───────────┬─────────────────────────┘
            │ YES
            ▼
┌─────────────────────────────────────┐
│ ✅ USE ORCHESTRATOR                 │
└─────────────────────────────────────┘

            │ NO (any question)
            ▼
┌─────────────────────────────────────┐
│ ⚡ Single-agent or manual workflow  │
└─────────────────────────────────────┘
```

---

## Comparison to Other Approaches

### Orchestrator vs. Single-Agent AI

| Aspect | Orchestrator | Single Agent |
|--------|--------------|--------------|
| **Specialization** | Each agent excels in domain | Generalist tries everything |
| **Quality** | Quality gates enforced | No automated quality checks |
| **Traceability** | Checkpoint artifacts, ADRs | No audit trail |
| **Governance** | Client-specific rules enforced | Manual compliance |
| **Scalability** | Add agents without rework | Agent gets overwhelmed |

**Example:** Building a demand forecasting app

- **Single Agent**: Tries to do data science, frontend, backend, deployment in one go → mediocre results
- **Orchestrator**: Data agent builds excellent model, Developer creates polished UI, QA validates rigorously → production-quality

### Orchestrator vs. Manual Multi-Agent

| Aspect | Orchestrator | Manual Coordination |
|--------|--------------|---------------------|
| **Coordination** | Automated phase transitions | Manual handoffs |
| **Validation** | Automated quality gates | Manual reviews |
| **State Management** | Checkpoint persistence | Ad-hoc tracking |
| **Governance** | YAML configuration | Spreadsheets, email |
| **Consistency** | Repeatable workflow | Varies by project |

**Example:** Analytics project

- **Manual**: PM coordinates Architect, then Data Scientist, then Developer via Slack → miscommunication, missed requirements
- **Orchestrator**: Workflow executes phases automatically with validation → consistent handoffs

### Orchestrator vs. CI/CD Pipelines

| Aspect | Orchestrator | CI/CD (GitHub Actions) |
|--------|--------------|------------------------|
| **Purpose** | AI agent coordination | Code testing and deployment |
| **Workflow** | Multi-phase project lifecycle | Build → Test → Deploy |
| **Agents** | Specialized AI agents | Shell scripts, Docker |
| **Consensus** | Human-in-the-loop approval | Automated (or manual deploy gate) |

**They complement each other:**

- **Orchestrator**: Coordinates agents to build the project
- **CI/CD**: Tests and deploys what orchestrator built

**Example workflow:**

```
Orchestrator run completes → Pushes to GitHub → CI/CD runs tests → Deploys to staging
```

---

## Real-World Workflows

### Workflow 1: Analytics Project (Customer Segmentation)

**Project:** Identify high-value customer segments for targeted marketing

**Phases:**

1. **Planning** (Architect)
   - Defines segmentation approach (RFM analysis + clustering)
   - Proposes tech stack (Python, pandas, scikit-learn)
   - Creates data model (customer_id, purchase_history, demographics)
   - **Checkpoint:** architecture.md, ADR-001-use-kmeans.md

2. **Consensus** (Human + Consensus Agent)
   - Reviews architecture, approves approach
   - **Checkpoint:** DECISION.md (approved)

3. **Data Engineering** (Data Agent)
   - Ingests customer data from CRM (data/raw/)
   - Cleans and validates (missing values, duplicates)
   - Engineers RFM features (Recency, Frequency, Monetary)
   - Clusters customers (K-Means, k=5 segments)
   - **Checkpoint:** data/processed/customers_segmented.csv, models/metrics.json

4. **Development** (Developer)
   - Creates Jupyter notebook for analysis
   - Builds interactive dashboard (Streamlit)
   - Implements segment profiling reports
   - **Checkpoint:** src/segmentation_app.py, notebooks/analysis.ipynb

5. **QA** (QA Agent)
   - Validates segment definitions against business rules
   - Tests dashboard functionality (filters, exports)
   - Checks data quality (no NaN in output)
   - **Checkpoint:** tests/test_segmentation.py, test_report.md

6. **Documentation** (Documentarian)
   - Creates README with setup instructions
   - Documents segment definitions (Segment 1 = "VIP Customers")
   - Writes user guide for dashboard
   - **Checkpoint:** README.md, docs/user_guide.md

**Deliverables:**
- `data/processed/customers_segmented.csv` - Segmented customer list
- `reports/segment_profiles.html` - C-suite presentation
- `src/segmentation_app.py` - Interactive dashboard
- `docs/user_guide.md` - How to use and interpret results

---

### Workflow 2: ML Project (Demand Forecasting)

**Project:** Forecast weekly demand for retail products

**Phases:**

1. **Planning** (Architect)
   - Proposes time-series forecasting pipeline
   - Selects Prophet for multi-seasonality
   - Designs API for forecast serving
   - **Checkpoint:** architecture.md, ADR-002-use-prophet.md

2. **Data Engineering** (Data Agent)
   - Ingests POS data (2 years history)
   - Validates data quality (no future-dated sales)
   - Engineers features (promotions, holidays)
   - Trains Prophet models (500 SKUs × 50 stores)
   - Evaluates MAPE (12% average error)
   - **Checkpoint:** models/prophet_forecasts.pkl, models/metrics.json

3. **Development** (Developer)
   - Implements FastAPI endpoint for forecasts
   - Creates React dashboard for visualization
   - Adds export to CSV functionality
   - **Checkpoint:** backend/api/, frontend/src/

4. **QA** (QA Agent)
   - Validates forecast accuracy (MAPE < 15%)
   - Tests API endpoints (200 status, correct JSON)
   - Load tests (1000 req/sec → p95 < 500ms)
   - **Checkpoint:** tests/, test_report.md (95% coverage)

5. **Documentation** (Documentarian)
   - API reference (OpenAPI spec)
   - User guide (how to interpret forecasts)
   - Deployment guide (Docker, AWS)
   - **Checkpoint:** docs/api_reference.md, docs/deployment_guide.md

**Deliverables:**
- `models/prophet_forecasts.pkl` - Trained forecasting models
- `backend/` - FastAPI service
- `frontend/` - React dashboard
- `docs/deployment_guide.md` - How to deploy to production

---

### Workflow 3: Web Application (Executive Dashboard)

**Project:** Build KPI dashboard for C-suite

**Phases:**

1. **Planning** (Architect)
   - Designs system architecture (React frontend, Node.js backend, PostgreSQL)
   - Proposes authentication (OAuth2 with SSO)
   - Creates database schema (KPIs, user roles)
   - **Checkpoint:** architecture.md, data_model.sql

2. **Development** (Developer)
   - Implements frontend (React, Chart.js)
   - Implements backend API (Express.js)
   - Sets up database (PostgreSQL, migrations)
   - **Checkpoint:** frontend/, backend/, migrations/

3. **QA** (QA Agent)
   - Tests user flows (login, view KPIs, export)
   - Validates role-based access control
   - Checks mobile responsiveness
   - **Checkpoint:** tests/e2e/, test_report.md (88% coverage)

4. **Documentation** (Documentarian)
   - README with setup instructions
   - User guide with screenshots
   - Admin guide (how to add users, manage roles)
   - **Checkpoint:** README.md, docs/user_guide.md, docs/admin_guide.md

**Deliverables:**
- Deployed dashboard (https://kpi-dashboard.company.com)
- User guide with screenshots
- Admin documentation

---

**Last Updated:** 2025-10-26
**Version:** 1.0.0
**Maintainer:** Kearney Data & Analytics Team
