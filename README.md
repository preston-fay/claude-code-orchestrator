# Claude Code Orchestrator

![Cleanliness](docs/badges/cleanliness.svg)

A multi-agent AI orchestration framework for building complex software projects through structured, checkpoint-driven workflows.

---

## 🚀 Quick Start (V2)

```bash
# Clone the repository
git clone https://github.com/preston-fay/claude-code-orchestrator.git
cd claude-code-orchestrator

# Install dependencies
pip install -r requirements-railway.txt

# Set your Anthropic API key
export ANTHROPIC_API_KEY=sk-ant-...

# Start the API server
uvicorn orchestrator_v2.api.server:app --reload

# Server running at http://localhost:8000
# API docs at http://localhost:8000/docs
```

### Test It Works

```bash
# Verify your API key
python scripts/verify_api_key.py

# Run workflow test
python scripts/run_workflow_test.py --real-llm
```

---

## 📦 Deployment

### Railway (Recommended for Testing)

[![Deploy on Railway](https://railway.app/button.svg)](https://railway.app/template/...)

1. Connect your GitHub repo to Railway
2. Set environment variable: `ANTHROPIC_API_KEY`
3. Deploy automatically

### AWS (Production)

See `DEPLOYMENT_APP_RUNNER.md` for AWS App Runner deployment.

---

## 🏗️ Architecture

The orchestrator uses specialized AI agents working in phases:

```
Ready Stage    →    Set Stage      →    Go Stage
─────────────       ─────────────       ─────────────
PLANNING            DATA                DEVELOPMENT
ARCHITECTURE        (early dev)         QA
                                        DOCUMENTATION
```

### Agents

| Agent | Role |
|-------|------|
| **Architect** | System design, tech stack selection |
| **Developer** | Code implementation |
| **QA** | Testing, quality assurance |
| **Documentarian** | Documentation generation |
| **Data** | Data pipelines, ML workflows |
| **Consensus** | Decision review, approval gates |
| **Reviewer** | Code review, quality scoring |
| **Steward** | Compliance, code hygiene |

---

## 📚 Documentation

| Doc | Description |
|-----|-------------|
| [LLM Integration](docs/LLM_INTEGRATION.md) | How to set up real LLM calls |
| [Migration Guide](docs/MIGRATION.md) | Migrating from V1 to V2 |
| [QUICKSTART](docs/QUICKSTART.md) | 5-minute tutorial |
| [METHODOLOGY](docs/METHODOLOGY.md) | Deep dive into orchestrator design |
| [API Reference](docs/API_MINIMUM.md) | REST API documentation |

### Intake System Documentation

| Doc | Description |
|-----|-------------|
| [Intake Wizard Guide](docs/user_guide/intake_wizard_guide.md) | How to use the intake wizard interface |
| [Intake API Reference](docs/api/intake_api_reference.md) | Complete API documentation for intake endpoints |
| [Creating Templates](docs/developer/creating_intake_templates.md) | Developer guide for building custom templates |
| [System Architecture](docs/architecture/intake_system_design.md) | Technical architecture and design decisions |
| [QA Report](docs/qa/intake_system_qa_report.md) | Quality assurance testing results |

---

## 🧭 Intake Template System

**Smart requirement gathering for perfect project starts**

The Intake Template System provides structured, adaptive interviews that ensure comprehensive project requirements before workflow execution. No more blank-page syndrome or missing context.

### Key Benefits
- **Guided interviews** tailored to your project type
- **Adaptive questions** that respond to your answers
- **Automatic validation** ensures completeness
- **Client governance** applies brand and compliance rules
- **Perfect prompts for perfect prompts** - orchestrator gets complete context

### Quick Example

```bash
# Start an intake session
curl -X POST "http://localhost:8000/api/intake/sessions" \
  -H "Content-Type: application/json" \
  -d '{"template_id": "presentation", "client_slug": "kearney-default"}'

# The wizard guides users through structured questions
# Outputs a complete project profile ready for orchestration
```

### Available Templates

| Template | Use Case | Duration | Questions |
|----------|----------|----------|-----------|
| **Presentation** | Slide decks, client reports | 15-20 min | 12-18 |
| **Analytics** | Data analysis, insights | 25-35 min | 18-25 |
| **ML Model** | Machine learning projects | 30-45 min | 20-30 |
| **Web Application** | Web tools, dashboards | 20-30 min | 15-22 |
| **Supply Chain** | Operations optimization | 35-50 min | 25-35 |

### Documentation
- **📘 [User Guide](docs/user_guide/intake_wizard_guide.md)** - How to use the intake wizard
- **🔧 [API Reference](docs/api/intake_api_reference.md)** - Complete API documentation
- **👨‍💻 [Developer Guide](docs/developer/creating_intake_templates.md)** - Create custom templates

---

## 🔧 API Endpoints

```bash
# Projects
POST   /projects                    # Create project
GET    /projects                    # List projects
GET    /projects/{id}               # Get project

# Intake Template System
POST   /api/intake/sessions         # Create intake session
GET    /api/intake/sessions/{id}    # Get session status
PUT    /api/intake/sessions/{id}/responses  # Submit answers
POST   /api/intake/sessions/{id}/complete   # Complete & create project
GET    /api/intake/templates        # List available templates

# Ready/Set/Go Workflow
POST   /rsg/{id}/ready/start        # Start Ready stage
POST   /rsg/{id}/set/start          # Start Set stage  
POST   /rsg/{id}/go/start           # Start Go stage
GET    /rsg/{id}/overview           # Get full RSG status

# User Settings (BYOK)
POST   /users/me/provider-settings  # Set your API key
POST   /users/me/provider-test      # Test API key works
```

---

## 🗂️ Repository Structure

```
claude-code-orchestrator/
├── orchestrator_v2/          # ✅ PRIMARY - V2 Implementation
│   ├── api/                  # FastAPI server + intake routes
│   ├── agents/               # 8 specialized agents
│   ├── engine/               # Workflow engine
│   ├── llm/                  # LLM providers (Anthropic, Bedrock)
│   ├── models/               # Data models (includes intake.py)
│   ├── services/             # Business logic (includes intake_service.py)
│   └── rsg/                  # Ready/Set/Go service
├── intake/                   # 🧭 Intake Template System
│   ├── templates/            # YAML template definitions
│   └── schema/               # JSON schema validation
├── rsg-ui/                   # React frontend with intake wizard
├── src/orchestrator/         # ⚠️ DEPRECATED - V1 (see docs/MIGRATION.md)
├── subagent_prompts/         # Agent prompt templates
├── docs/                     # Documentation
│   ├── user_guide/           # End-user documentation
│   ├── api/                  # API reference docs
│   ├── developer/            # Developer guides
│   ├── architecture/         # System design docs
│   └── qa/                   # Quality assurance reports
├── scripts/                  # Utility scripts
├── _archive/                 # Historical files
└── tests/                    # Test suite (includes intake tests)
```

---

## ⚠️ V1 Deprecation Notice

The `src/orchestrator/` module is deprecated. Please use `orchestrator_v2/` instead.

See [Migration Guide](docs/MIGRATION.md) for upgrade instructions.

---

## 🚀 Using as a Template

**Create a new project:**

```bash
# Method 1: Bootstrap Command
orchestrator bootstrap analytics --output ~/projects/my-new-project

# Method 2: GitHub Template Button
# Click "Use this template" button above ↗️
```

**Available templates:** `analytics`, `ml-model`, `webapp`, `supply-chain`

**📖 Full guide:** [TEMPLATE_USAGE.md](TEMPLATE_USAGE.md)

---

## Features

### Intake Template System

Structured requirement gathering through adaptive interviews that ensure comprehensive project context before orchestrator workflows begin.

**Key capabilities:**
- Conditional logic and adaptive questioning
- Client-specific governance and validation
- Auto-save and session management
- Project template inheritance
- Multi-language and branding support

**📖 Learn more:** [docs/user_guide/intake_wizard_guide.md](docs/user_guide/intake_wizard_guide.md)

### Skills Framework

Reusable analytical patterns and methodologies that agents can apply across projects.

**📖 Learn more:** [.claude/skills/README.md](.claude/skills/README.md)

### Knowledge Base

Three-tier knowledge architecture: universal → firm-wide → project-specific.

**📖 Learn more:** [.claude/knowledge/README.md](.claude/knowledge/README.md)

### Client Governance

YAML-based configuration for quality gates, compliance, and brand constraints.

**📖 Learn more:** [clients/README.md](clients/README.md)

### AI Code Review

Automated PR review using Claude API for security, performance, and quality.

**📖 Learn more:** [docs/AI_CODE_REVIEW_SETUP.md](docs/AI_CODE_REVIEW_SETUP.md)

---

## Repository Health

![Hygiene Trend](docs/hygiene_trend.png)

See [Repository Hygiene Guide](docs/repo_hygiene.md) for cleanliness scoring.

---

## License

MIT
