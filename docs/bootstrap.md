# Bootstrap Command - Quick Start Guide

The `orchestrator bootstrap` command initializes new projects with the complete orchestrator framework, following best practices and Kearney standards.

## Quick Start

```bash
# Create analytics project
orchestrator bootstrap analytics --output ~/projects/customer-segmentation

# Create ML model project with client governance
orchestrator bootstrap ml-model --output ~/projects/demand-forecast --client acme-corp

# Create webapp
orchestrator bootstrap webapp --output ~/projects/dashboard --name "Executive Dashboard"

# Preview without creating files
orchestrator bootstrap supply-chain --output ~/projects/network-optimization --dry-run
```

## Available Templates

### 1. Analytics (`analytics`)
**Use for:** Data analysis, insights generation, exploratory analysis, statistical modeling

**Creates:**
- Data pipeline structure (raw → interim → processed)
- Jupyter notebooks for exploration
- Analysis and visualization scripts
- Data quality reporting
- Executive deliverable templates

**Agents:** Architect, Data, Developer, QA, Documentarian

**Example Use Cases:**
- Customer segmentation analysis
- Market research insights
- A/B test analysis
- Descriptive analytics projects

### 2. ML Model (`ml-model`)
**Use for:** Predictive modeling, classification, regression, deep learning

**Creates:**
- ML pipeline structure (data, features, models, evaluation, deployment)
- Model training and evaluation framework
- MLflow experiment tracking setup
- Model card template
- Deployment API structure

**Agents:** Architect, Data, ML Engineer, Evaluator, Developer, Documentarian

**Example Use Cases:**
- Demand forecasting
- Customer churn prediction
- Recommender systems
- Time series forecasting

### 3. Web Application (`webapp`)
**Use for:** Full-stack web applications, dashboards, internal tools

**Creates:**
- Frontend structure (React/Vue/Angular)
- Backend API structure (FastAPI/Flask)
- Authentication and authorization setup
- Database models
- CI/CD configuration

**Agents:** Architect, Frontend Dev, Backend Dev, QA, Documentarian

**Example Use Cases:**
- Executive dashboards
- Client-facing portals
- Internal workflow tools
- Data visualization applications

### 4. Supply Chain (`supply-chain`)
**Use for:** Operations research, network optimization, logistics, inventory planning

**Creates:**
- Optimization model structure (LP, MILP)
- Simulation framework
- Network analysis tools
- Scenario analysis setup
- Decision support dashboards

**Agents:** Architect, Data, Optimization Engineer, Developer, QA, Documentarian

**Example Use Cases:**
- Network optimization
- Inventory planning
- Production scheduling
- Logistics routing

## Command Reference

### Basic Usage
```bash
orchestrator bootstrap <template> --output <directory> [OPTIONS]
```

### Parameters

#### Required
- `<template>` - Template name: `analytics`, `ml-model`, `webapp`, `supply-chain`
- `--output, -o <path>` - Target directory for new project

#### Optional
- `--client, -c <name>` - Client name for governance customization (e.g., `acme-corp`)
- `--name, -n <name>` - Project name (defaults to output directory name)
- `--description, -d <text>` - Project description
- `--dry-run` - Preview actions without creating files

### Examples

**Analytics project:**
```bash
orchestrator bootstrap analytics \
  --output ~/projects/customer-analysis \
  --name "Customer Segmentation Analysis" \
  --description "Identify high-value customer segments"
```

**ML project with client governance:**
```bash
orchestrator bootstrap ml-model \
  --output ~/projects/forecast \
  --client high-security-client \
  --name "Demand Forecasting Model"
```

**Preview webapp structure:**
```bash
orchestrator bootstrap webapp \
  --output ~/projects/dashboard \
  --dry-run
```

## What Gets Created

### Directory Structure
```
my-project/
├── .claude/                    # Orchestrator framework
│   ├── knowledge/              # Domain knowledge, best practices
│   ├── skills/                 # Reusable analytical skills
│   ├── decisions/              # Architecture Decision Records
│   ├── checkpoints/            # Phase validation artifacts
│   └── consensus/              # Consensus review documents
├── .github/workflows/          # CI/CD configuration
├── design_system/              # Kearney brand templates
├── data/                       # Data directories (analytics/ML)
├── src/                        # Source code
├── tests/                      # Automated tests
├── docs/                       # Documentation
├── reports/                    # Analysis outputs
├── scripts/                    # Utility scripts
├── configs/                    # Configuration files
├── .gitignore                  # Git ignore rules
├── .pre-commit-config.yaml     # Pre-commit hooks
├── .tidyignore                 # Repository hygiene exceptions
├── requirements.txt            # Python dependencies
├── intake.yaml                 # Project requirements (orchestrator)
└── README.md                   # Project documentation
```

### Configuration Files

**`.gitignore`**: Excludes data files, model artifacts, credentials, IDE files

**`requirements.txt`**: Python dependencies specific to template type

**`intake.yaml`**: Orchestrator intake configuration with:
- Project metadata
- Functional and technical requirements
- Data requirements
- Constraints and success criteria

**`README.md`**: Project documentation with:
- Getting started instructions
- Directory structure explanation
- Development workflow
- Testing and deployment guides

### Orchestrator Framework Files

**`.claude/knowledge/`**:
- `analytics_best_practices.yaml` - Universal data science patterns
- `kearney_standards.yaml` - Kearney firm-wide standards (RAISE framework)
- `projects/` - Project-specific knowledge templates

**`.claude/skills/`**:
- `time_series_analytics.yaml` - Forecasting methodologies
- `survey_data_processing.yaml` - Survey analysis patterns
- `optimization_modeling.yaml` - Operations research patterns

**`.claude/decisions/`**:
- `template.md` - ADR template for documenting decisions
- `README.md` - ADR system documentation

**`design_system/`**:
- C-suite presentation templates (HTML/CSS)
- Kearney design tokens (colors, fonts, spacing)
- Brand compliance guidelines

## Client Governance Integration

When you specify `--client <name>`, the bootstrap command:

1. **Loads client governance** from `clients/<name>/governance.yaml`
2. **Applies client-specific requirements**:
   - Quality gates (test coverage, security scanning)
   - Compliance frameworks (SOC2, GDPR, HIPAA)
   - Brand constraints (colors, fonts, forbidden terms)
   - Deployment requirements (approval workflows, windows)
3. **Customizes deliverables** with client theme if available

**Example:**
```bash
orchestrator bootstrap analytics \
  --output ~/projects/acme-analysis \
  --client acme-corp

# Applies acme-corp governance:
# - Custom quality gates (min_test_coverage: 90)
# - Compliance: GDPR + SOC2
# - Brand: Acme colors and logo
# - Notifications: Sends updates to Acme stakeholders
```

## Post-Bootstrap Workflow

After running bootstrap, follow these steps:

### 1. Install Dependencies
```bash
cd <project-directory>
pip install -r requirements.txt
```

### 2. Configure Project
Edit `intake.yaml` with project-specific details:
- Update requirements based on actual needs
- Specify data sources
- Define success metrics
- Add constraints

### 3. Add Data (Analytics/ML projects)
```bash
# Place raw data files
cp /path/to/data.csv data/raw/

# Create project-specific knowledge
cp .claude/knowledge/projects/README.md .claude/knowledge/projects/my-project.yaml
# Edit my-project.yaml with domain knowledge
```

### 4. Start Orchestrator Workflow
```bash
# Initialize orchestrator run
orchestrator run start --intake intake.yaml

# Execute first phase (planning)
orchestrator run next

# Review planning artifacts
ls .claude/checkpoints/planning/

# If consensus required, approve
orchestrator run approve

# Continue workflow
orchestrator run next
```

### 5. Development Iteration
```bash
# Run repository hygiene scan
orchestrator run repo-hygiene

# Run tests
pytest tests/

# Format code
black src/ tests/

# Commit changes
git add .
git commit -m "feat: implement feature X"
```

## Customization

### Modify Template
Templates are in `templates/project-types/*.yaml`. You can:

1. **Add directories** to `directory_structure`
2. **Copy additional files** in `copy_files`
3. **Generate custom config files** in `config_files`
4. **Modify intake template** with project-specific placeholders
5. **Add dependencies** to `dependencies`

**Example: Add custom directory**
```yaml
# templates/project-types/analytics.yaml
directory_structure:
  - ".claude/"
  - "data/raw/"
  - "my_custom_dir/"  # <-- Add this
```

### Create New Template
```bash
# Copy existing template
cp templates/project-types/analytics.yaml templates/project-types/my-template.yaml

# Edit my-template.yaml:
# - Change name, description
# - Modify directory_structure
# - Update agents and phases
# - Customize intake_template

# Use your template
orchestrator bootstrap my-template --output ~/projects/test
```

## Troubleshooting

### Template Not Found
```
Error: Template 'xyz' not found.
Available templates: analytics, ml-model, webapp, supply-chain
```
**Fix**: Use one of the available template names

### Source File Not Found
```
Error: Source file not found: /path/to/file
```
**Fix**: Ensure orchestrator framework files exist. Run `git pull` to update.

### Client Governance Not Found
```
Warning: Client governance not found: clients/acme/governance.yaml
```
**Fix**: Create client governance file or omit `--client` parameter

### Directory Already Exists
Bootstrap will create the directory if it doesn't exist. If it exists, files will be added/overwritten.

**Fix**: Use a different output directory or remove existing directory

### Git Initialization Failed
```
Warning: Git initialization failed
```
**Fix**: Ensure `git` is installed and available in PATH

## Best Practices

### 1. Use Dry Run First
```bash
orchestrator bootstrap analytics --output ~/projects/test --dry-run
# Review what would be created before committing
```

### 2. Version Control from Start
Bootstrap initializes git automatically with initial commit. Push to remote immediately:
```bash
cd <project-directory>
git remote add origin https://github.com/org/repo.git
git push -u origin main
```

### 3. Review Generated Files
- Check `.gitignore` matches your needs
- Review `intake.yaml` for completeness
- Validate `README.md` instructions
- Test `requirements.txt` installs correctly

### 4. Follow Workflow Phases
Don't skip phases. Each phase has quality gates:
```bash
orchestrator run next  # Execute each phase
# Review artifacts before proceeding
orchestrator run next  # Continue
```

### 5. Document Decisions
Create ADRs for significant decisions:
```bash
cp .claude/decisions/template.md .claude/decisions/ADR-003-my-decision.md
# Fill in decision rationale
```

## Integration with Other Commands

### With Intake Validate
```bash
# Bootstrap project
orchestrator bootstrap analytics --output ~/projects/test

# Validate intake configuration
cd ~/projects/test
orchestrator intake validate
```

### With Run Workflow
```bash
# Bootstrap and start workflow
orchestrator bootstrap ml-model --output ~/projects/forecast
cd ~/projects/forecast
orchestrator run start --intake intake.yaml
orchestrator run next
```

### With Repo Hygiene
```bash
# After development
orchestrator run repo-hygiene
# Review reports/repo_hygiene_report.md
```

## FAQ

**Q: Can I bootstrap into an existing directory?**
A: Yes, but bootstrap will create/overwrite files. Use `--dry-run` first to preview.

**Q: How do I update an existing project with new framework files?**
A: Bootstrap into a temporary directory, then manually copy updated files to your project.

**Q: Can I create my own custom template?**
A: Yes! Copy an existing template YAML and customize. See "Create New Template" section.

**Q: What if I don't specify a client?**
A: Project uses Kearney default governance standards (see `clients/kearney-default/governance.yaml`).

**Q: Can I modify generated files after bootstrap?**
A: Absolutely! Bootstrap creates starter files. Customize as needed for your project.

**Q: Does bootstrap install Python dependencies?**
A: No. Run `pip install -r requirements.txt` after bootstrap.

**Q: How do I use a different Python version?**
A: Create venv with your preferred version before installing:
```bash
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Examples Gallery

### Example 1: Customer Churn Analysis
```bash
orchestrator bootstrap analytics \
  --output ~/projects/churn-analysis \
  --name "Customer Churn Analysis" \
  --description "Identify at-risk customers and retention strategies"

cd ~/projects/churn-analysis
# Place customer data in data/raw/
pip install -r requirements.txt
orchestrator run start --intake intake.yaml
```

### Example 2: Demand Forecasting Model
```bash
orchestrator bootstrap ml-model \
  --output ~/projects/demand-forecast \
  --client retail-client \
  --name "Store Demand Forecasting"

cd ~/projects/demand-forecast
# Configure MLflow tracking
pip install -r requirements.txt
# Place historical sales data in data/raw/
orchestrator run start --intake intake.yaml
```

### Example 3: Executive Dashboard
```bash
orchestrator bootstrap webapp \
  --output ~/projects/executive-dashboard \
  --name "Executive KPI Dashboard"

cd ~/projects/executive-dashboard
pip install -r backend/requirements.txt
cd frontend && npm install
# Start development servers
uvicorn backend.main:app --reload &
cd frontend && npm run dev
```

### Example 4: Supply Chain Network Optimization
```bash
orchestrator bootstrap supply-chain \
  --output ~/projects/network-optimization \
  --name "Distribution Network Optimization"

cd ~/projects/network-optimization
pip install -r requirements.txt
# Place network data (nodes, edges, costs) in data/raw/
orchestrator run start --intake intake.yaml
```

---

**Last Updated:** 2025-01-26
**Version:** 1.0.0
**Maintainer:** Kearney Data & Analytics Team
