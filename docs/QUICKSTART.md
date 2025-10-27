# Orchestrator Quick Start Guide

Get started with the Claude Code Orchestrator in 5 minutes.

---

## What You'll Build

In this quick start, you'll create a complete analytics project using the orchestrator:

1. **Bootstrap** a new project from a template
2. **Configure** project requirements
3. **Execute** the orchestrator workflow
4. **Review** checkpoint artifacts
5. **Approve** consensus and continue

**Time:** 5-10 minutes
**Prerequisites:** Python 3.9+, Claude Code installed

---

## Step 1: Bootstrap a Project (30 seconds)

Create a new analytics project with one command:

```bash
# Create project from analytics template
orchestrator bootstrap analytics \
  --output ~/projects/quickstart-demo \
  --name "Customer Analysis Demo" \
  --description "Quick start tutorial project"

# Navigate to project
cd ~/projects/quickstart-demo
```

**What just happened:**

The bootstrap command created a complete project structure:

```
quickstart-demo/
├── .claude/                 # Orchestrator framework
│   ├── knowledge/           # Best practices, standards
│   ├── skills/              # Reusable methodologies
│   ├── decisions/           # ADR templates
│   └── checkpoints/         # Phase artifacts (empty for now)
├── data/                    # Data directories
│   ├── raw/
│   ├── interim/
│   └── processed/
├── docs/                    # Documentation
├── scripts/                 # Utility scripts
├── intake.yaml              # Project requirements
├── README.md                # Project documentation
└── requirements.txt         # Python dependencies
```

---

## Step 2: Install Dependencies (1 minute)

```bash
# Install Python dependencies
pip install -r requirements.txt

# Verify installation
python3 -c "import pandas; print('Dependencies installed!')"
```

**Expected output:**

```
Dependencies installed!
```

---

## Step 3: Review Project Configuration (1 minute)

Open `intake.yaml` to see the project requirements:

```yaml
project:
  name: "Customer Analysis Demo"
  type: "analytics"
  description: "Quick start tutorial project"

requirements:
  functional:
    - "Analyze customer purchase patterns"
    - "Identify high-value customer segments"
    - "Generate executive summary report"

  technical:
    - "Python-based analysis pipeline"
    - "Reproducible Jupyter notebooks"
    - "Automated data validation"

  data:
    - "Customer transaction data (CSV)"
    - "Expected volume: 10K-100K records"

success_criteria:
  - "Clear segmentation with business interpretation"
  - "Actionable recommendations for marketing team"
  - "< 10% missing data in analysis"
```

**For this quick start, we'll use the defaults.** In real projects, you'd customize requirements to match your needs.

---

## Step 4: Add Sample Data (Optional, 2 minutes)

For a complete demo, add sample data to `data/raw/`:

```bash
# Create sample customer data
cat > data/raw/customers.csv << 'EOF'
customer_id,signup_date,total_purchases,total_revenue,last_purchase_date
1001,2024-01-15,12,1200.00,2024-10-01
1002,2024-02-20,5,450.00,2024-09-15
1003,2024-03-10,25,3500.00,2024-10-20
1004,2024-04-05,3,180.00,2024-07-10
1005,2024-05-12,18,2100.00,2024-10-22
EOF

# Verify data
head data/raw/customers.csv
```

**If you skip this step**, the orchestrator will still work, but the Data agent will note missing data in checkpoints.

---

## Step 5: Start Orchestrator Workflow (30 seconds)

Initialize the orchestrator run:

```bash
orchestrator run start --intake intake.yaml
```

**Expected output:**

```
✓ Loaded intake configuration
✓ Validated requirements
✓ Initialized workflow state
✓ Run started: run_20251026_1234

Current phase: planning
Next: orchestrator run next
```

**What just happened:**

The orchestrator:
1. Loaded your `intake.yaml` requirements
2. Validated the configuration
3. Created `.claude/orchestrator_state.json` to track progress
4. Set the workflow to start at the **planning** phase

---

## Step 6: Execute Planning Phase (1 minute)

Run the first phase:

```bash
orchestrator run next
```

**What happens during planning:**

The **Architect agent** will:
1. Read `intake.yaml` requirements
2. Review `.claude/knowledge/` for best practices
3. Check `.claude/skills/` for applicable methodologies
4. Propose system architecture and technical approach
5. Create checkpoint artifacts

**Checkpoint artifacts created:**

```
.claude/checkpoints/planning/
├── architecture.md          # System design
├── technical_spec.md        # Implementation details
└── data_pipeline.md         # Data flow diagram

.claude/decisions/
└── ADR-001-use-pandas-for-analysis.md
```

---

## Step 7: Review Checkpoint Artifacts (2 minutes)

Before proceeding, review what the Architect proposed:

```bash
# View architecture
cat .claude/checkpoints/planning/architecture.md

# View technical decisions
cat .claude/decisions/ADR-001-*.md
```

**Example architecture.md:**

```markdown
# System Architecture: Customer Analysis Demo

## Overview
Python-based analytics pipeline for customer segmentation and insights.

## Components

1. **Data Ingestion**: Load CSV from data/raw/
2. **Data Validation**: Check completeness, types, ranges
3. **Analysis**: RFM (Recency, Frequency, Monetary) segmentation
4. **Visualization**: Charts and executive summary
5. **Reporting**: Jupyter notebook + HTML export

## Technology Stack
- **Data Processing**: pandas, numpy
- **Visualization**: matplotlib, seaborn
- **Reporting**: Jupyter Notebook
- **Testing**: pytest

## Data Flow
```
data/raw/customers.csv
  → Validation (data quality checks)
  → Feature Engineering (RFM calculation)
  → Clustering (K-Means, k=4 segments)
  → Visualization (segment profiles)
  → Report (reports/customer_segments.html)
```

## Quality Gates
- Min 80% test coverage
- No missing critical fields (customer_id, revenue)
- RFM values calculated correctly
```

---

## Step 8: Check Workflow Status (30 seconds)

```bash
orchestrator run status
```

**Expected output:**

```
Run ID: run_20251026_1234
Current Phase: planning (completed)
Status: waiting_for_consensus

Completed Phases:
  ✓ planning (2025-10-26 12:34:56)

Pending Phases:
  • data_engineering
  • development
  • qa
  • documentation

Next: Review .claude/consensus/REQUEST.md
Then: orchestrator run approve
```

---

## Step 9: Review Consensus Request (2 minutes)

The orchestrator pauses for human review at critical checkpoints. Review the request:

```bash
cat .claude/consensus/REQUEST.md
```

**Example REQUEST.md:**

```markdown
🟢 **STATUS: READY FOR REVIEW**

---

# Consensus Request: planning

## Summary
The Architect has completed the planning phase and proposed a system architecture
for customer segmentation analysis using RFM methodology.

## Agent Outcomes

### Architect
- **Status**: ✓ Completed
- **Artifacts**: 3 files created
- **Decisions**: 1 ADR documented

## Artifact Validation

✓ `.claude/checkpoints/planning/architecture.md` (2.1 KB)
✓ `.claude/checkpoints/planning/technical_spec.md` (1.8 KB)
✓ `.claude/decisions/ADR-001-use-pandas-for-analysis.md` (1.2 KB)

## Key Decisions

### ADR-001: Use pandas for Data Analysis
- **Decision**: Use pandas/numpy for data manipulation
- **Rationale**: Industry standard, excellent documentation, team expertise
- **Alternatives**: Polars (faster but newer), SQL (less flexible)

## Reviewer Checklist

- [ ] Architecture aligns with project requirements
- [ ] Technology choices are appropriate for team skillset
- [ ] Data pipeline addresses data quality concerns
- [ ] ADRs document key decisions with rationale
- [ ] No obvious security or scalability issues

## Recommendation

✅ **APPROVE** - Architecture is sound and well-documented.
```

---

## Step 10: Approve and Continue (30 seconds)

If the architecture looks good, approve:

```bash
orchestrator run approve
```

**Expected output:**

```
✓ Consensus approved
✓ Phase 'planning' marked as approved
✓ Workflow can proceed

Next: orchestrator run next
```

**What if you want to reject?**

```bash
# Reject with feedback
orchestrator run reject

# Architect will retry planning phase with your feedback
```

---

## Step 11: Continue Workflow (2 minutes)

Execute the next phase (data engineering):

```bash
orchestrator run next
```

**What happens during data engineering:**

The **Data agent** will:
1. Load data from `data/raw/customers.csv`
2. Validate data quality (missing values, types)
3. Engineer RFM features (Recency, Frequency, Monetary)
4. Perform customer segmentation (K-Means clustering)
5. Generate metrics and validation report

**Checkpoint artifacts created:**

```
data/processed/
└── customers_segmented.csv    # Customers with segment labels

.claude/checkpoints/data/
├── validation_report.md       # Data quality results
├── feature_engineering.md     # RFM calculation details
└── segmentation_summary.md    # Cluster profiles

models/
└── metrics.json               # Segmentation quality metrics
```

---

## Step 12: View Results (1 minute)

Check the segmentation results:

```bash
# View processed data
head data/processed/customers_segmented.csv

# View metrics
cat models/metrics.json

# View validation report
cat .claude/checkpoints/data/validation_report.md
```

**Example customers_segmented.csv:**

```csv
customer_id,signup_date,total_purchases,total_revenue,last_purchase_date,recency_days,frequency,monetary,segment
1001,2024-01-15,12,1200.00,2024-10-01,25,12,1200.00,2
1002,2024-02-20,5,450.00,2024-09-15,41,5,450.00,3
1003,2024-03-10,25,3500.00,2024-10-20,6,25,3500.00,1
1004,2024-04-05,3,180.00,2024-07-10,107,3,180.00,4
1005,2024-05-12,18,2100.00,2024-10-22,4,18,2100.00,1
```

**Segments:**
- **Segment 1**: VIP customers (high recency, frequency, monetary)
- **Segment 2**: Regular customers (moderate on all dimensions)
- **Segment 3**: Infrequent buyers (low frequency, moderate monetary)
- **Segment 4**: At-risk customers (low recency, low frequency)

---

## Step 13: Complete Remaining Phases (3 minutes)

Continue executing phases:

```bash
# Development phase (create notebooks, reports)
orchestrator run next

# QA phase (validate analysis, test code)
orchestrator run next

# Documentation phase (create user guide)
orchestrator run next
```

**After all phases complete:**

```bash
orchestrator run status
```

**Expected output:**

```
Run ID: run_20251026_1234
Current Phase: documentation (completed)
Status: ✓ completed

Completed Phases:
  ✓ planning (2025-10-26 12:35:00)
  ✓ data_engineering (2025-10-26 12:37:15)
  ✓ development (2025-10-26 12:39:30)
  ✓ qa (2025-10-26 12:41:45)
  ✓ documentation (2025-10-26 12:43:00)

All phases complete! 🎉
```

---

## Step 14: Review Final Deliverables (2 minutes)

Check what the orchestrator created:

```bash
# Project structure
tree -L 2 -I '__pycache__|*.pyc|.ipynb_checkpoints'

# View README
cat README.md

# View user guide
cat docs/user_guide.md

# Open analysis notebook (if Jupyter installed)
jupyter notebook notebooks/customer_segmentation.ipynb
```

**Final deliverables:**

```
✓ data/processed/customers_segmented.csv  # Segmented customer data
✓ notebooks/customer_segmentation.ipynb   # Interactive analysis
✓ reports/segment_profiles.html           # Executive summary
✓ docs/user_guide.md                      # How to use results
✓ README.md                                # Project documentation
✓ tests/test_segmentation.py              # Automated tests
```

---

## Next Steps

### Explore Advanced Features

**1. Run Repository Hygiene Scan:**

```bash
orchestrator run repo-hygiene

# Review report
cat reports/repo_hygiene_report.md
```

**2. View Metrics Dashboard:**

```bash
orchestrator run metrics
```

**3. Review Architecture Decision Records:**

```bash
ls .claude/decisions/
cat .claude/decisions/ADR-*.md
```

### Try Other Templates

**ML Model Project:**

```bash
orchestrator bootstrap ml-model \
  --output ~/projects/forecasting-demo \
  --name "Demand Forecasting"
```

**Web Application:**

```bash
orchestrator bootstrap webapp \
  --output ~/projects/dashboard-demo \
  --name "KPI Dashboard"
```

**Supply Chain Optimization:**

```bash
orchestrator bootstrap supply-chain \
  --output ~/projects/network-optimization \
  --name "Distribution Network Optimization"
```

### Learn More

- **[METHODOLOGY.md](METHODOLOGY.md)** - Deep dive into orchestrator philosophy
- **[Bootstrap Guide](bootstrap.md)** - Complete bootstrap command reference
- **[Intake Documentation](intake.md)** - How to configure project requirements
- **[Repository Hygiene](repo_hygiene.md)** - Cleanliness standards and scoring

---

## Troubleshooting

### Issue: Bootstrap Command Not Found

**Error:**

```
bash: orchestrator: command not found
```

**Fix:**

```bash
# Install orchestrator CLI
cd /path/to/claude-code-orchestrator
pip install -e .

# Verify installation
orchestrator --version
```

---

### Issue: Dependencies Won't Install

**Error:**

```
ERROR: Could not find a version that satisfies the requirement pandas>=2.0
```

**Fix:**

```bash
# Update pip first
pip install --upgrade pip

# Install with verbose output
pip install -r requirements.txt -v

# If specific package fails, install individually
pip install pandas
pip install numpy
pip install matplotlib
```

---

### Issue: Workflow Won't Start

**Error:**

```
Error: No active workflow configuration
```

**Fix:**

```bash
# Ensure intake.yaml exists
ls intake.yaml

# Start with explicit path
orchestrator run start --intake ./intake.yaml

# Check workflow state
cat .claude/orchestrator_state.json
```

---

### Issue: Agent Phase Fails

**Error:**

```
Phase 'data_engineering' failed: FileNotFoundError: data/raw/customers.csv
```

**Fix:**

```bash
# Check if data exists
ls data/raw/

# Add sample data or adjust intake.yaml
# Then retry the phase
orchestrator run retry --phase data_engineering
```

---

### Issue: Quality Gate Fails

**Error:**

```
QualityGateFailure: Test coverage 65% < threshold 80%
```

**Fix:**

```bash
# Add more tests to increase coverage
# Then retry QA phase
orchestrator run retry --phase qa

# OR lower threshold (not recommended)
# Edit clients/kearney-default/governance.yaml:
# quality_gates:
#   min_test_coverage: 65
```

---

## What to Do If Things Go Wrong

### 1. Check Workflow Status

```bash
orchestrator run status
```

This shows which phase failed and why.

### 2. Review Agent Logs

```bash
orchestrator run log
```

This shows detailed output from agent execution.

### 3. Retry Failed Phase

```bash
orchestrator run retry --phase <phase_name>
```

This re-executes the failed phase without losing previous progress.

### 4. Rollback to Previous Checkpoint

```bash
orchestrator run rollback --phase <phase_name>
```

This non-destructively resets the workflow cursor to an earlier phase.

### 5. Abort and Start Over

```bash
orchestrator run abort
rm -rf .claude/checkpoints/*
orchestrator run start --intake intake.yaml
```

---

## Quick Reference Commands

```bash
# Project Creation
orchestrator bootstrap <template> --output <dir>  # Create new project

# Workflow Execution
orchestrator run start --intake intake.yaml       # Initialize workflow
orchestrator run next                              # Execute next phase
orchestrator run status                            # Check progress

# Consensus
orchestrator run approve                           # Approve consensus
orchestrator run reject                            # Reject and request revision

# Error Handling
orchestrator run retry --phase <phase>             # Retry failed phase
orchestrator run rollback --phase <phase>          # Rollback to checkpoint
orchestrator run abort                             # Abort current run

# Quality & Metrics
orchestrator run repo-hygiene                      # Run hygiene scan
orchestrator run metrics                           # View metrics dashboard

# Intake Management
orchestrator intake new                            # Create new intake
orchestrator intake validate <file>                # Validate intake YAML
orchestrator intake templates                      # List available templates
```

---

## Summary

Congratulations! You've:

✅ Created a complete analytics project with `orchestrator bootstrap`
✅ Executed a multi-phase workflow with specialized agents
✅ Reviewed checkpoint artifacts and approved consensus
✅ Generated production-ready deliverables (data, notebooks, reports)
✅ Learned orchestrator commands and troubleshooting

**Total time:** ~10 minutes
**What you got:** A complete, documented, tested analytics project

---

## What's Next?

1. **Customize `intake.yaml`** for your real project requirements
2. **Add your own data** to `data/raw/`
3. **Create project-specific knowledge** in `.claude/knowledge/projects/`
4. **Define client governance** in `clients/<client>/governance.yaml` (if needed)
5. **Run orchestrator workflow** and review/approve checkpoints
6. **Deliver production-ready project** with confidence

**Happy orchestrating!** 🚀

---

**Last Updated:** 2025-10-26
**Version:** 1.0.0
**Questions?** See [METHODOLOGY.md](METHODOLOGY.md) or open an issue
