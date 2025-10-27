#!/bin/bash

# GitHub Deployment Script for Orchestrator Methodology Framework
# This script completes the GitHub deployment steps for v1.0.0

set -e  # Exit on error

echo "🚀 Starting GitHub Deployment for Orchestrator v1.0.0"
echo "=================================================="
echo ""

# Step 1: Ensure we're on the feature branch
echo "📍 Step 1: Verifying branch..."
CURRENT_BRANCH=$(git branch --show-current)
if [ "$CURRENT_BRANCH" != "feature/orchestrator-methodology-framework" ]; then
    echo "❌ Error: Not on feature branch. Current branch: $CURRENT_BRANCH"
    echo "   Run: git checkout feature/orchestrator-methodology-framework"
    exit 1
fi
echo "✅ On correct branch: $CURRENT_BRANCH"
echo ""

# Step 2: Ensure branch is pushed
echo "📤 Step 2: Ensuring branch is pushed to GitHub..."
git push -u origin feature/orchestrator-methodology-framework
echo "✅ Branch pushed successfully"
echo ""

# Step 3: Authenticate with GitHub CLI (if not already)
echo "🔐 Step 3: Checking GitHub CLI authentication..."
if ! gh auth status &> /dev/null; then
    echo "⚠️  GitHub CLI not authenticated. Authenticating now..."
    echo "   Follow the prompts to authenticate with GitHub..."
    gh auth login
else
    echo "✅ Already authenticated with GitHub CLI"
fi
echo ""

# Step 4: Create Pull Request
echo "📝 Step 4: Creating Pull Request..."

PR_BODY=$(cat <<'EOF'
## Summary

This PR introduces the complete **Orchestrator Methodology Framework** for replicating complex projects using coordinated multi-agent workflows. This framework provides everything needed to bootstrap new projects with best practices, governance, and reusable knowledge baked in.

## What's Included

### 🎯 **Core Framework** (33 files, 16,811+ lines)

1. **Skills Framework** (`.claude/skills/`)
   - Reusable analytical methodologies (time series, survey analysis, optimization)
   - Domain-agnostic, template-driven approach
   - YAML-based skill definitions with validation criteria

2. **Knowledge Base** (`.claude/knowledge/`)
   - Three-tier hierarchy: Universal → Firm-wide → Project-specific
   - `analytics_best_practices.yaml` (20KB+) - Universal data science fundamentals
   - `kearney_standards.yaml` (12KB+) - Firm-wide RAISE framework compliance

3. **Architecture Decision Records** (`.claude/decisions/`)
   - Lightweight ADR system for documenting decisions
   - Template-based workflow
   - Searchable decision history

4. **Client Governance** (`clients/`)
   - YAML-based quality gates and compliance rules
   - JSON Schema validation
   - Client-specific brand constraints and approval workflows
   - Example: `kearney-default` with 80% test coverage, SOC2 compliance

5. **Bootstrap Command** (`src/orchestrator/commands/bootstrap.py`)
   - One-command project initialization
   - 4 templates: `analytics`, `ml-model`, `webapp`, `supply-chain`
   - Dry-run mode, client governance integration, git initialization

6. **C-Suite Presentation Templates** (`design_system/templates/c-suite/`)
   - Kearney-branded HTML/CSS templates
   - **Arial font** for presentations (corrected from Inter)
   - No gridlines, no emojis policy enforced

### 📚 **Documentation** (60KB+)

- **`docs/METHODOLOGY.md`** (20.6KB) - Complete methodology guide with 12 sections
- **`docs/QUICKSTART.md`** (11.2KB) - 5-minute hands-on tutorial (14 steps)
- **`docs/bootstrap.md`** (15KB) - Bootstrap command reference
- **`TEMPLATE_USAGE.md`** (18KB) - How to use this repo as a GitHub template
- **Updated**: `README.md`, `CLAUDE.md`, `docs/repo_hygiene.md`

### 🚀 **Project Templates** (`templates/project-types/`)

- **Analytics**: Data pipelines, Jupyter notebooks, statistical modeling
- **ML Model**: MLflow tracking, model cards, evaluation framework
- **Web Application**: React/FastAPI, auth, CI/CD
- **Supply Chain**: Optimization models, simulation, network analysis

## Technical Highlights

### Bootstrap Command Usage

```bash
# Create analytics project
orchestrator bootstrap analytics \
  --output ~/projects/customer-analysis \
  --name "Customer Segmentation"

# ML project with client governance
orchestrator bootstrap ml-model \
  --output ~/projects/forecast \
  --client acme-corp
```

### Quality Gates

All new projects include:
- ✅ Min 80% test coverage (configurable per client)
- ✅ Pre-commit hooks for code quality
- ✅ Repository hygiene validation
- ✅ ADR documentation requirements
- ✅ Data privacy compliance (PII handling)

## Testing

- ✅ All YAML files validated (fixed checkbox syntax issues)
- ✅ Bootstrap command tested with dry-run mode
- ✅ Template validation complete
- ✅ Font specifications corrected (Arial for presentations, Inter for apps)

## Breaking Changes

None. This is net-new functionality.

## Checklist

- [x] Code follows project style guidelines
- [x] Documentation updated (README, CLAUDE.md, METHODOLOGY, QUICKSTART)
- [x] All YAML syntax validated
- [x] Bootstrap command tested
- [x] Templates validated
- [x] Font specifications corrected per brand guidelines
- [x] Repository hygiene validation extended for framework files

## Next Steps (Post-Merge)

1. Tag release as `v1.0.0`
2. Enable "Template repository" checkbox in GitHub settings
3. Add topics: `orchestrator`, `claude-code`, `methodology`, `multi-agent`, `project-template`

---

**🎉 This completes Phase 3 of the orchestrator framework!**

Co-authored-by: Claude <noreply@anthropic.com>
EOF
)

# Check if PR already exists
PR_URL=$(gh pr list --head feature/orchestrator-methodology-framework --json url --jq '.[0].url' 2>/dev/null || echo "")

if [ -n "$PR_URL" ]; then
    echo "✅ Pull Request already exists: $PR_URL"
else
    gh pr create \
        --title "feat: add complete methodology framework for project replication" \
        --body "$PR_BODY" \
        --base main \
        --head feature/orchestrator-methodology-framework

    echo "✅ Pull Request created successfully"
fi

# Get PR number
PR_NUMBER=$(gh pr list --head feature/orchestrator-methodology-framework --json number --jq '.[0].number')
echo "   PR #$PR_NUMBER"
echo ""

# Step 5: Merge Pull Request
echo "🔀 Step 5: Merging Pull Request..."
echo "   Waiting 2 seconds before merge..."
sleep 2

gh pr merge "$PR_NUMBER" --merge --delete-branch
echo "✅ Pull Request merged and branch deleted"
echo ""

# Step 6: Switch to main and pull
echo "📥 Step 6: Switching to main branch and pulling..."
git checkout main
git pull origin main
echo "✅ Main branch updated"
echo ""

# Step 7: Create GitHub Release
echo "🏷️  Step 7: Creating GitHub Release v1.0.0..."

RELEASE_NOTES=$(cat <<'EOF'
# Orchestrator Methodology Framework v1.0.0

**First stable release of the Claude Code Orchestrator methodology framework!** 🎉

## 🎯 What is this?

The Orchestrator Methodology Framework enables **project replication at scale** using coordinated multi-agent workflows. Bootstrap new analytics, ML, webapp, or supply chain projects in seconds with best practices, governance, and institutional knowledge baked in.

## ✨ Key Features

### 1. Bootstrap Command
One command to initialize complete projects:

```bash
orchestrator bootstrap analytics --output ~/projects/customer-analysis
orchestrator bootstrap ml-model --output ~/projects/forecast --client acme-corp
orchestrator bootstrap webapp --output ~/projects/dashboard
orchestrator bootstrap supply-chain --output ~/projects/network-optimization
```

### 2. Skills Framework
Reusable analytical methodologies (`.claude/skills/`):
- Time series forecasting (ARIMA, Prophet, LSTM)
- Survey data processing and analysis
- Optimization modeling (LP, MILP, network optimization)
- Geospatial analytics

### 3. Knowledge Base
Three-tier hierarchy (`.claude/knowledge/`):
- **Universal**: `analytics_best_practices.yaml` (20KB) - Data science fundamentals
- **Firm-wide**: `kearney_standards.yaml` (12KB) - RAISE framework, quality standards
- **Project-specific**: Custom domain knowledge per project

### 4. Client Governance
YAML-based quality gates (`clients/`):
- Test coverage thresholds (e.g., 80% minimum)
- Compliance frameworks (SOC2, GDPR, HIPAA)
- Brand constraints (colors, fonts, forbidden terms)
- Approval workflows and deployment windows

### 5. Architecture Decision Records
Lightweight decision documentation system (`.claude/decisions/`):
- Template-based ADR creation
- Searchable decision history
- Context, rationale, and alternatives documented

### 6. C-Suite Presentation Templates
Kearney-branded deliverables (`design_system/templates/c-suite/`):
- HTML/CSS templates for executive summaries
- Arial font for presentations (brand compliance)
- No gridlines, no emojis policy

## 📚 Documentation

- **[QUICKSTART.md](docs/QUICKSTART.md)** - 5-minute hands-on tutorial (14 steps)
- **[METHODOLOGY.md](docs/METHODOLOGY.md)** - Complete methodology guide (20KB, 12 sections)
- **[bootstrap.md](docs/bootstrap.md)** - Bootstrap command reference (15KB)
- **[TEMPLATE_USAGE.md](TEMPLATE_USAGE.md)** - How to use this repo as a GitHub template

## 🚀 Quick Start

```bash
# 1. Install orchestrator
pip install -e .

# 2. Bootstrap a project
orchestrator bootstrap analytics \
  --output ~/projects/my-analysis \
  --name "Customer Segmentation Analysis"

# 3. Navigate and configure
cd ~/projects/my-analysis
pip install -r requirements.txt

# 4. Start orchestrator workflow
orchestrator run start --intake intake.yaml
orchestrator run next  # Execute phases iteratively
```

## 📦 What's Included

- **33 files** created/modified
- **16,811+ lines** of code and documentation
- **4 project templates**: analytics, ml-model, webapp, supply-chain
- **60KB+ documentation**: METHODOLOGY, QUICKSTART, bootstrap guide
- **Validated YAML**: All knowledge, skills, and governance files tested

## 🔧 Technical Details

### System Requirements
- Python 3.9+
- Claude Code CLI installed
- Git

### Project Templates

| Template | Use Case | Key Features |
|----------|----------|--------------|
| `analytics` | Data analysis, insights | Jupyter notebooks, data pipelines, reporting |
| `ml-model` | Predictive modeling | MLflow tracking, model cards, evaluation framework |
| `webapp` | Full-stack web apps | React/FastAPI, auth, CI/CD |
| `supply-chain` | Operations research | Optimization models, simulation, network analysis |

### Quality Gates (Default)
- ✅ Min 80% test coverage
- ✅ No secrets committed (`.env` required)
- ✅ Repository hygiene validation
- ✅ ADR documentation for decisions
- ✅ Data privacy compliance (PII handling)

## 🐛 Bug Fixes

- Fixed YAML syntax errors in knowledge base (checkbox markers must be quoted)
- Corrected font specification (Arial for presentations, Inter for web apps)
- Validated all template YAML files

## 🎓 Use as Template Repository

This repository is now configured as a **GitHub Template**:

1. Click "Use this template" button on GitHub
2. Create new repository from template
3. Clone and start building immediately

## 📝 Breaking Changes

None. This is the first stable release.

## 🙏 Acknowledgments

Built with Claude Code and the multi-agent orchestrator pattern.

---

**Full Changelog**: Initial release (v1.0.0)

**Co-authored-by**: Claude <noreply@anthropic.com>
EOF
)

gh release create v1.0.0 \
    --title "v1.0.0 - Orchestrator Methodology Framework" \
    --notes "$RELEASE_NOTES" \
    --target main

echo "✅ GitHub Release v1.0.0 created successfully"
echo ""

# Step 8: Add GitHub Topics
echo "🏷️  Step 8: Adding GitHub topics..."
gh repo edit preston-fay/claude-code-orchestrator \
    --add-topic orchestrator \
    --add-topic claude-code \
    --add-topic methodology \
    --add-topic multi-agent \
    --add-topic project-template \
    --add-topic bootstrap \
    --add-topic kearney \
    --add-topic analytics

echo "✅ GitHub topics added"
echo ""

# Step 9: Enable Template Repository (requires manual action via web UI)
echo "🎯 Step 9: Enable Template Repository..."
echo "   ⚠️  This step requires manual action via GitHub web UI:"
echo "   1. Go to https://github.com/preston-fay/claude-code-orchestrator/settings"
echo "   2. Scroll to 'Template repository' section"
echo "   3. Check the box: ☑️ Template repository"
echo "   4. Save changes"
echo ""
echo "   Alternatively, you can use gh API (experimental):"
echo "   gh api repos/preston-fay/claude-code-orchestrator --method PATCH -f is_template=true"
echo ""

# Try to enable via API
if gh api repos/preston-fay/claude-code-orchestrator --method PATCH -f is_template=true &> /dev/null; then
    echo "✅ Template repository setting enabled via API"
else
    echo "⚠️  Could not enable template repository via API. Please do this manually via web UI."
fi
echo ""

# Final summary
echo "=================================================="
echo "🎉 GitHub Deployment Complete!"
echo "=================================================="
echo ""
echo "✅ Pull Request created and merged"
echo "✅ Release v1.0.0 tagged and published"
echo "✅ GitHub topics added"
echo "⚠️  Template repository: Verify in settings"
echo ""
echo "🔗 Repository: https://github.com/preston-fay/claude-code-orchestrator"
echo "🔗 Release: https://github.com/preston-fay/claude-code-orchestrator/releases/tag/v1.0.0"
echo ""
echo "📚 Next steps:"
echo "   1. Verify template repository checkbox in GitHub settings"
echo "   2. Test 'Use this template' button functionality"
echo "   3. Share repository with team"
echo ""
echo "Happy orchestrating! 🚀"
