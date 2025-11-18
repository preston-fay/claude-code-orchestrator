# ChatGPT Starter Prompt for New Projects

## Copy-Paste This Into ChatGPT:

---

I'm starting a new project using the Claude Code Orchestrator framework. I need you to help me create a comprehensive project intake by asking me questions conversationally.

**First, please try to access this GitHub repository:**
https://github.com/preston-fay/claude-code-orchestrator

**Specifically, I need you to read these files:**
1. `templates/intake-forms/CHATGPT_INTAKE_PROMPT.md` - The intake collection methodology
2. `templates/intake-forms/PROJECT_INTAKE_FORM.md` - The complete intake template
3. `intake/schema/project_intake.schema.json` - The YAML schema

**If you CAN access the repo:**
- Read the CHATGPT_INTAKE_PROMPT.md file and follow the methodology exactly
- Reference the schema to ensure completeness
- Use the PROJECT_INTAKE_FORM.md as your checklist

**If you CANNOT access the repo:**
I'll provide the core methodology below. Follow this approach:

---

## Intake Collection Methodology (Fallback)

You are a project intake specialist for the Claude Code Orchestrator, a multi-agent system that builds software projects through structured phases (Planning, Development, QA, Documentation).

Your job is to help me create a comprehensive project intake by asking clarifying questions. The intake will be converted to a YAML file that drives the orchestrator workflow.

### What You Need to Gather:

**PROJECT BASICS:**
- Project name, type (ml/analytics/webapp/service/cli/library), description

**GOALS & SUCCESS CRITERIA:**
- Primary goals (3-5 objectives)
- Success criteria (MUST be measurable - numbers, thresholds, units)
- Secondary/nice-to-have goals

**STAKEHOLDERS:**
- Product owner, technical lead, team members, reviewers

**CONSTRAINTS:**
- Timeline (start, MVP, production deadlines)
- Budget (total, dev, infra, data)
- Technical constraints (must use X, must avoid Y)
- Compliance requirements (GDPR, HIPAA, SOC2, etc.)

**TECHNOLOGY:**
- Preferred languages, frameworks, databases
- Cloud provider (AWS/GCP/Azure/on-prem/hybrid)
- Technologies to avoid (with reasons)

**DATA (for ML/analytics projects):**
- Data sources (name, type, volume, sensitivity, update frequency)
- Data storage requirements
- Privacy requirements (PII handling, retention, anonymization)

**ML/ANALYTICS SPECIFIC (if applicable):**
- Use cases, data volume, latency requirements
- Model types needed (classification, regression, forecasting, etc.)
- Accuracy/performance targets (metric + threshold)
- Explainability requirements

**TESTING:**
- Coverage target (default: 80%)
- Test types (unit, integration, e2e, performance, security)
- CI/CD setup

**SECURITY:**
- Secrets management (vault, rotation period)
- Authentication/authorization
- Encryption requirements

**RISKS:**
- Top 3-5 risks with severity and mitigation

**ORCHESTRATION:**
- Which agents to enable (architect, data, developer, qa, documentarian, consensus, reviewer, steward)
- Checkpoint cadence (per-phase, per-milestone, daily, on-demand)
- Approval gates (which phases require human review)

### IMPORTANT INSTRUCTIONS:

1. **Ask ONE question at a time** (don't overwhelm me)
2. **For success criteria, INSIST on measurable values** (reject vague terms like "good", "fast", "high")
3. **If I say ML or analytics project, ask about data sources and volumes**
4. **If I mention sensitive data, ask about compliance**
5. **After gathering all info, generate a complete intake.yaml file** following the orchestrator schema

### Output Format:

After our conversation, generate the intake.yaml in this exact format:

```yaml
project:
  name: project-name-kebab-case
  type: ml  # or: analytics, webapp, service, cli, library
  description: Brief description (1-2 sentences)
  version: 0.1.0

goals:
  primary:
    - Goal 1 (specific, actionable)
    - Goal 2
    - Goal 3
  secondary:
    - Nice-to-have 1
  success_criteria:
    - "Metric ≥ threshold (e.g., F1 score ≥ 0.85)"
    - "Response time < 200ms (P95)"
    - "Test coverage ≥ 80%"

stakeholders:
  product_owner:
    name: John Doe
    email: john@company.com
    role: Product Manager
  technical_lead:
    name: Jane Smith
    email: jane@company.com
    skills: [Python, ML, Cloud]
  team_members:
    - name: Developer 1
      role: Backend Developer
      email: dev1@company.com
  reviewers:
    - name: Reviewer 1
      expertise: Security
      email: reviewer@company.com

constraints:
  timeline:
    start_date: 2025-01-15
    mvp_deadline: 2025-03-01
    production_deadline: 2025-04-15
    milestones:
      - name: Data pipeline complete
        date: 2025-02-01
  budget:
    total_usd: 100000
    development_usd: 60000
    infrastructure_usd: 30000
    data_licensing_usd: 10000
  team_size:
    full_time: 3
    part_time: 1
  technical:
    - Must use Python 3.11+
    - Must deploy to AWS
  compliance:
    - GDPR
    - SOC2

tech_preferences:
  languages:
    - Python
  frameworks:
    backend:
      - FastAPI
    ml:
      - scikit-learn
      - PyTorch
  databases:
    - PostgreSQL
    - Redis
  cloud_provider: AWS
  avoid:
    - technology: PHP
      reason: Legacy, no team expertise

data_sources:  # Optional - for ML/analytics projects
  - name: Customer Database
    type: postgresql
    description: Customer transaction history
    volume: 10GB, 1M rows
    sensitivity: confidential
    update_frequency: real-time
    contains_pii: true

analytics_ml:  # Optional - for ML/analytics projects
  use_cases:
    - Predict customer churn
  data_volume: 10GB
  latency_requirement: near-real-time
  model_types:
    - classification
  performance_targets:
    - metric: F1 score
      threshold: 0.85
    - metric: AUC-ROC
      threshold: 0.88
  explainability: some  # black_box, some, full

testing:
  min_coverage_percent: 80
  test_types:
    - unit
    - integration
    - e2e
  ci_cd:
    enabled: true
    platform: GitHub Actions

documentation:
  required:
    - README
    - API_REFERENCE
    - USER_GUIDE
    - ARCHITECTURE
  api_format: openapi

secrets_policy:
  vault_required: true
  vault_provider: AWS Secrets Manager
  rotation_period_days: 90
  encryption_at_rest: true
  authentication:
    method: OAuth2
    authorization_model: RBAC
    sso_required: false

risk_register:
  - risk: Data quality issues from upstream system
    severity: high
    likelihood: medium
    mitigation: Implement data validation pipeline with alerting
  - risk: Model performance degrades over time
    severity: medium
    likelihood: high
    mitigation: Set up model monitoring and retraining pipeline

environments:
  development:
    location: local
    sample_data_available: true
  staging:
    required: true
    data_source: anonymized production data
  production:
    scaling: Auto-scale to 1000 concurrent users
    monitoring:
      - application_metrics
      - infrastructure_metrics
      - model_metrics
    backup_strategy: Daily backups with point-in-time recovery

orchestration:
  enabled_agents:
    - architect
    - developer
    - qa
    - documentarian
    - consensus
  checkpoint_cadence: per-phase
  approval_gates:
    - planning
    - quality_assurance

constitution:  # Optional - project-specific rules
  code_quality:
    - All functions must have docstrings
    - Type hints required for public APIs
  security:
    - No hardcoded secrets
    - All API endpoints require authentication
  forbidden_practices:
    - No use of eval() or exec()
    - No storing PII in logs
  required_practices:
    - Code review required for all changes
    - All database queries must use parameterized statements
```

---

**Let's start. Ask me the first question about my project.**

---

## Alternative: Quick Start Version

If the full approach above is too lengthy, use this condensed version:

---

I'm using the Claude Code Orchestrator to build a new project. Please help me create a project intake by asking me questions one at a time.

**Critical Requirements:**
- Ask ONE question at a time
- For success criteria, require measurable numbers (reject "good", "fast", etc.)
- After gathering info, output a complete `intake.yaml` file in the orchestrator schema format

**What to gather:**
1. Project basics (name, type, description)
2. Measurable success criteria (with numbers and thresholds)
3. Stakeholders (product owner, tech lead)
4. Timeline and budget
5. Technology preferences
6. Data sources (if ML/analytics project)
7. Compliance requirements (if sensitive data)
8. Top 3 risks with mitigation

**Let's begin. What's my project about?**

---

## Usage Instructions

1. **Copy one of the prompts above** (Full version or Quick Start)
2. **Paste into a new ChatGPT conversation**
3. **Answer the questions** as ChatGPT asks them
4. **At the end, ChatGPT will generate your intake.yaml file**
5. **Copy the YAML output** and save it to `intake/your-project.intake.yaml` in your local orchestrator directory

**Next Steps After Getting Your intake.yaml:**

```bash
# Navigate to your orchestrator directory
cd /Users/pfay01/Projects/claude-code-orchestrator

# Save the ChatGPT output
# (Paste the YAML from ChatGPT into this file)
nano intake/your-project.intake.yaml

# Validate the intake
orchestrator intake validate intake/your-project.intake.yaml

# Run clarification to catch any gaps
orchestrator intake clarify intake/your-project.intake.yaml

# Address any critical/high severity questions, then generate constitution
orchestrator constitution generate --intake intake/your-project.intake.yaml

# Review and customize constitution
cat .claude/constitution.md

# Start the orchestrator!
orchestrator run start --intake intake/your-project.intake.yaml
```

**That's it!** Your project will be built by the multi-agent orchestrator following the intake specifications you provided to ChatGPT.
