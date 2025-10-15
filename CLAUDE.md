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
