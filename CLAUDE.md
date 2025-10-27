# Claude Code Orchestrator - Manifest

## Mission
The Claude Code Orchestrator is a meta-framework that coordinates multiple specialized Claude Code subagents to collaboratively build, refine, and deliver complex software projects through a structured, checkpoint-driven workflow.

## Intended Subagents
- **Architect**: Designs system architecture, data models, and technical specifications
- **Data**: Handles data engineering, ETL pipelines, analytics, and model training
- **Developer**: Implements features, writes code, and handles technical implementation
- **QA**: Tests functionality, validates requirements, runs test suites, and ensures quality
- **Documentarian**: Creates and maintains documentation, README files, and user guides
- **Consensus**: Reviews proposals from other agents, identifies conflicts, and builds agreement
- **Reviewer**: (Optional) Conducts code reviews and provides feedback on implementation
- **Steward**: Maintains repository health, identifies dead code, orphans, and cleanliness issues

## Workflow Overview
1. **Planning Phase**: Architect proposes system design and technical approach
2. **Consensus Phase**: Consensus agent reviews and validates architectural decisions
3. **Data Engineering Phase** (Optional): Data agent builds pipelines, models, and analytics
4. **Development Phase**: Developer implements features based on approved architecture
5. **Quality Assurance Phase**: QA agent validates implementation against requirements
6. **Documentation Phase**: Documentarian creates comprehensive documentation
7. **Review & Iteration**: Reviewer provides feedback; iterate as needed

## Checkpoint Approach
- Each phase concludes with a checkpoint artifact (design doc, code deliverable, test report, etc.)
- Checkpoints are validated by Consensus agent before proceeding to next phase
- Director/Orchestrator maintains state and coordinates phase transitions
- Checkpoints enable rollback, review, and iterative refinement
- All checkpoint artifacts are versioned and stored in project state

## Orchestration Principles
- Clear separation of concerns between subagents
- Explicit handoffs with checkpoint validation
- Consensus-driven decision making for critical junctures
- Iterative refinement with quality gates
- Transparent state management and audit trail

## Data Lifecycle & Checkpoints

The Data Engineering phase (when invoked) follows a structured pipeline with checkpoints:

### Data Pipeline Stages
1. **Ingestion**: Load raw data from source systems → `data/raw/`
   - **Checkpoint**: Raw data file, ingestion log, row count validation
2. **Validation**: Apply data quality checks and validation rules
   - **Checkpoint**: Validation report, quality metrics, pass/fail status
3. **Transformation**: Clean, normalize, and engineer features → `data/interim/`, `data/processed/`
   - **Checkpoint**: Interim data, processed features, transformation log
4. **Training**: Train models on processed data → `models/`
   - **Checkpoint**: Model artifacts, metadata, training logs
5. **Evaluation**: Assess model performance and generate metrics
   - **Checkpoint**: `models/metrics.json`, evaluation report, performance summary

### Data Checkpoint Artifacts
See `.claude/checkpoints/DATA-CHECKLIST.md` for complete list of required artifacts at each checkpoint.

**Key Artifacts for Handoff:**
- `models/[model].pkl` - Trained model for integration
- `models/metrics.json` - Performance metrics and evaluation results
- `data/processed/` - Feature-engineered data ready for use
- `docs/data_documentation.md` - Data dictionary, lineage, and documentation

### Data Privacy & Security

**PII Handling:**
- All personally identifiable information (PII) must be anonymized or pseudonymized before `data/processed/`
- Raw data containing PII is never committed to version control
- Use `.env` for database credentials and API keys (never hardcode secrets)

**Data Classification:**
- **Public**: Sample datasets, aggregated metrics (can be committed)
- **Internal**: Project-specific data, interim results (local only)
- **Confidential**: Customer data, PII (encrypted at rest, access-controlled)
- **Restricted**: Compliance-regulated data (special approval required)

**Security Requirements:**
- Encrypt sensitive data at rest and in transit
- Use secure connections for data source access (SSL/TLS)
- Apply principle of least privilege for data access
- Document data sources and sensitivity classification
- Review data samples before sharing or committing

See `docs/data_documentation.md` for detailed data privacy and retention policies.

## Using Skills

**What are Skills?**

Skills are reusable analytical patterns and methodologies stored in `.claude/skills/`. Each skill encapsulates a proven approach for a specific type of task (e.g., time-series forecasting, survey analysis, optimization modeling).

**How Agents Use Skills:**

1. **Discovery**: Agents scan `.claude/skills/` at the start of relevant phases to identify applicable skills
2. **Selection**: Agents choose skills that match project requirements (e.g., if intake mentions "forecasting", load `time_series_analytics.yaml`)
3. **Adaptation**: Agents read skill YAML for methodology steps, then adapt to project-specific context
4. **Application**: Agents apply the skill's approach while documenting deviations in checkpoint artifacts

**Example Workflow:**

```
Architect reads intake.yaml → Identifies "demand forecasting" requirement
→ Loads .claude/skills/time_series_analytics.yaml
→ Reviews ARIMA/Prophet/LSTM approaches
→ Proposes time-series pipeline in architecture checkpoint
→ Documents decision to use Prophet in ADR
```

**When to Create New Skills:**

- After solving a problem that could recur across projects
- When establishing a new firm-wide analytical standard
- To codify lessons learned from past projects

**Skill YAML Structure:**

```yaml
name: "Skill Name"
category: "analytics|ml|optimization|survey"
description: "What this skill helps with"
when_to_use: "Criteria for applicability"
methodology:
  - step: "Step description"
    rationale: "Why this step matters"
tools_required: ["python", "pandas", "scikit-learn"]
validation_criteria: "How to verify success"
common_pitfalls: ["Pitfall 1", "Pitfall 2"]
```

See [.claude/skills/README.md](.claude/skills/README.md) for complete skill authoring guide.

## Accessing Knowledge

**What is the Knowledge Base?**

The knowledge base provides agents with contextual information at three levels of specificity:

1. **Universal** (`.claude/knowledge/universal/`) - Data science fundamentals applicable to all projects
2. **Firm-wide** (`.claude/knowledge/kearney/`) - Kearney standards like RAISE framework, brand compliance
3. **Project-specific** (`.claude/knowledge/projects/`) - Domain terminology, business rules, data schemas

**How Agents Access Knowledge:**

**During Planning Phase:**
- Architect reads `kearney_standards.yaml` to ensure RAISE compliance
- Architect reads project-specific knowledge (if exists) for domain context
- Architecture proposal explicitly references knowledge sources used

**During Data Phase:**
- Data agent reads `analytics_best_practices.yaml` for data quality standards
- Data agent reads project knowledge for data dictionary and business rules
- ETL code includes comments linking to knowledge sources

**During Development Phase:**
- Developer reads universal patterns for implementation best practices
- Developer reads firm-wide standards for code quality expectations
- Code adheres to standards documented in knowledge base

**During QA Phase:**
- QA agent reads project knowledge for acceptance criteria
- Test cases validate business rules documented in knowledge base

**Knowledge Hierarchy (Most Specific Wins):**

```
Project Knowledge > Firm-wide Knowledge > Universal Knowledge
```

If project knowledge says "use fiscal year", that overrides universal "use calendar year" guidance.

**When to Add Project Knowledge:**

```bash
# At project start, create project-specific knowledge
cp .claude/knowledge/projects/README.md .claude/knowledge/projects/my-project.yaml

# Document:
# - Domain terminology (e.g., "ACV" = Annual Contract Value)
# - Business rules (e.g., "Churn = no activity in 90 days")
# - Data schemas (e.g., "customer_id is UUID v4")
# - Constraints (e.g., "Must use on-premises SQL Server")
```

See [.claude/knowledge/README.md](.claude/knowledge/README.md) for knowledge base architecture.

## Creating ADRs

**What are Architecture Decision Records (ADRs)?**

ADRs document significant technical decisions made during the project. They capture *why* a decision was made, not just *what* was decided.

**When Agents Create ADRs:**

Agents are prompted to create ADRs at key decision points:

1. **Planning Phase**: Architecture design decisions
   - "Why FastAPI instead of Flask?"
   - "Why PostgreSQL instead of MongoDB?"
   - "Why microservices instead of monolith?"

2. **Data Phase**: Data pipeline and modeling decisions
   - "Why Prophet instead of ARIMA for forecasting?"
   - "Why feature X was engineered?"
   - "Why 80/20 train-test split?"

3. **Development Phase**: Implementation decisions
   - "Why Redux instead of Context API?"
   - "Why server-side rendering?"
   - "Why WebSockets instead of polling?"

**How Agents Create ADRs:**

```bash
# Agent copies template
cp .claude/decisions/template.md .claude/decisions/ADR-003-use-prophet-for-forecasting.md

# Agent fills in:
# - Context: What problem are we solving?
# - Decision: What did we decide?
# - Rationale: Why this option?
# - Alternatives: What else was considered?
# - Consequences: What are the tradeoffs?
# - Status: Proposed/Accepted/Superseded
```

**ADR Workflow:**

1. **Architect proposes** decision in ADR (status: Proposed)
2. **Consensus agent reviews** ADR during consensus phase
3. **Consensus updates** ADR (status: Accepted) or requests revision
4. **Future agents reference** ADR when implementing or extending

**ADR Numbering:**

- ADR-001, ADR-002, ADR-003 (sequential)
- Number assigned when ADR is created (not when accepted)
- Gaps in sequence are OK (deleted/abandoned ADRs)

**When NOT to Create ADRs:**

- Trivial decisions (e.g., variable naming)
- Decisions that can be easily reversed
- Implementation details (document in code comments instead)

See [.claude/decisions/README.md](.claude/decisions/README.md) for ADR system guide.

## Client Governance

**What is Client Governance?**

Client governance defines client-specific quality gates, compliance requirements, brand constraints, and deployment policies. Rules are stored in `clients/<client-name>/governance.yaml` and automatically enforced during workflow execution.

**How the Orchestrator Applies Governance:**

**At Workflow Start:**
```bash
# Orchestrator reads intake.yaml for client name
orchestrator run start --intake intake.yaml

# If client specified, loads clients/<client>/governance.yaml
# Falls back to clients/kearney-default/governance.yaml if not found
```

**During Each Phase:**

1. **Quality Gates Check**: Before phase completion, orchestrator validates:
   - Test coverage meets `min_test_coverage` threshold
   - Security scan passes (if `security_scan_required: true`)
   - Documentation completeness (if `require_documentation: true`)

2. **Compliance Validation**: Orchestrator checks for compliance flags:
   - GDPR: No PII in version control, data retention limits
   - HIPAA: PHI encryption, access logs
   - SOC2: Audit trails, change management

3. **Brand Enforcement**: Orchestrator validates deliverables against:
   - `brand_constraints.colors` - Allowed color palette
   - `brand_constraints.fonts` - Required font families
   - `brand_constraints.forbidden_terms` - Words to avoid

4. **Deployment Approval**: For production deployments:
   - Checks `deployment.approval_required` and pauses for stakeholder approval
   - Validates deployment is within `deployment_windows` (e.g., no Friday deploys)

**How Agents Use Governance:**

**Architect Phase:**
- Reads governance to understand constraints before design
- Proposes architecture that satisfies `compliance` requirements
- Documents compliance approach in ADR

**Data Phase:**
- Applies `quality_gates.min_test_coverage` to data validation tests
- Implements data retention per `compliance.gdpr.data_retention_days`
- Logs data access per `compliance.hipaa.audit_trail`

**Developer Phase:**
- Uses colors from `brand_constraints.colors` in UI
- Uses fonts from `brand_constraints.fonts` in stylesheets
- Avoids `brand_constraints.forbidden_terms` in user-facing text

**QA Phase:**
- Validates test coverage meets threshold
- Runs security scans if required
- Checks brand compliance in deliverables

**Deployment Phase:**
- Requests approval if `deployment.approval_required: true`
- Sends notifications to `notifications.slack_webhook` and `notifications.email`

**Governance Inheritance:**

```
Client Governance > Kearney Default > Hardcoded Minimums
```

If client governance doesn't specify `min_test_coverage`, uses Kearney default (80%). If neither specified, uses hardcoded minimum (70%).

**Example Governance Check:**

```python
# Orchestrator validates before phase completion
if test_coverage < governance['quality_gates']['min_test_coverage']:
    raise QualityGateFailure("Test coverage below threshold")

if 'gdpr' in governance['compliance'] and pii_detected_in_repo():
    raise ComplianceViolation("PII found in version control")
```

See [clients/README.md](clients/README.md) for governance schema and examples.

## House Rules

### Repository Hygiene

The Steward agent enforces repository cleanliness and hygiene. All contributors must follow these rules:

**What belongs in version control:**
- Source code, tests, documentation
- Configuration files (with secrets in `.env`, not committed)
- Small reference datasets (< 100KB)
- Infrastructure code (.github/workflows/, Dockerfiles)

**What does NOT belong:**
- Large binary files (> 1MB) → use S3, MLflow, DVC
- Raw datasets (data/raw/) → use data versioning tools
- Model artifacts (*.pkl, *.h5) → use MLflow or S3
- Secrets (.env, *.pem, credentials.json)
- Jupyter notebook outputs
- Generated files (build/, dist/, __pycache__/)

**Hygiene enforcement:**
- Run `orchestrator run repo-hygiene` before creating PRs
- Reviewreports/repo_hygiene_report.md for violations
- Add intentional exemptions to `.tidyignore` with comments
- CI will fail PRs with non-whitelisted large files or notebook outputs

See [docs/repo_hygiene.md](docs/repo_hygiene.md) for complete hygiene guide.
