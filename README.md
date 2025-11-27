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

---

## 🔧 API Endpoints

```bash
# Projects
POST   /projects                    # Create project
GET    /projects                    # List projects
GET    /projects/{id}               # Get project

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
│   ├── api/                  # FastAPI server
│   ├── agents/               # 8 specialized agents
│   ├── engine/               # Workflow engine
│   ├── llm/                  # LLM providers (Anthropic, Bedrock)
│   └── rsg/                  # Ready/Set/Go service
├── src/orchestrator/         # ⚠️ DEPRECATED - V1 (see docs/MIGRATION.md)
├── subagent_prompts/         # Agent prompt templates
├── docs/                     # Documentation
├── scripts/                  # Utility scripts
├── _archive/                 # Historical files
└── tests/                    # Test suite
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
