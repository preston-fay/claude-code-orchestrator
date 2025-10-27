# Using Claude Code Orchestrator as a Template

This repository is configured as a **GitHub template repository**, making it easy to create new projects with the complete orchestrator framework pre-configured.

## Quick Start

Choose one of two methods to create a new project:

### Method 1: Bootstrap Command (Recommended) ⭐
```bash
orchestrator bootstrap analytics --output ~/projects/my-new-project
cd ~/projects/my-new-project
pip install -r requirements.txt
orchestrator run start --intake intake.yaml
```

### Method 2: GitHub "Use this Template" Button
1. Click **"Use this template"** button on GitHub
2. Create new repository
3. Clone your new repository
4. Follow post-creation checklist

---

## Comparison: Which Method Should You Use?

| Feature | Bootstrap Command | GitHub Template Button |
|---------|-------------------|----------------------|
| **Speed** | ⚡ Instant (seconds) | 🐌 Slower (minutes, requires GitHub) |
| **Customization** | ✅ Choose template type | ⚠️ Full copy, manual cleanup needed |
| **Project Types** | ✅ 4 templates (analytics, ml-model, webapp, supply-chain) | ❌ One size fits all |
| **Client Governance** | ✅ Automatic (`--client acme-corp`) | ❌ Manual configuration |
| **Git Initialization** | ✅ Automatic with initial commit | ✅ Automatic (on GitHub) |
| **Intake YAML** | ✅ Pre-generated with placeholders | ❌ Must create manually |
| **Directory Structure** | ✅ Template-specific (lean) | ⚠️ Includes everything (bloated) |
| **Offline Use** | ✅ Works offline | ❌ Requires internet |
| **Best For** | New projects from scratch | Forking entire orchestrator framework |

**Recommendation:** Use **bootstrap command** for 95% of use cases. Only use GitHub template button if you need to fork the entire orchestrator codebase for modification.

---

## Method 1: Bootstrap Command (Detailed Guide)

### Prerequisites
- Claude Code Orchestrator installed and in PATH
- Python 3.9+ with pip

### Step 1: Choose a Template

Available templates:
- **`analytics`** - Data analysis, insights, statistical modeling
- **`ml-model`** - Machine learning, predictive modeling, deep learning
- **`webapp`** - Full-stack web applications, dashboards
- **`supply-chain`** - Operations research, optimization, logistics

### Step 2: Run Bootstrap Command

**Basic usage:**
```bash
orchestrator bootstrap <template> --output <directory>
```

**Examples:**

```bash
# Analytics project
orchestrator bootstrap analytics \
  --output ~/projects/customer-segmentation \
  --name "Customer Segmentation Analysis" \
  --description "Identify high-value customer segments"

# ML model with client governance
orchestrator bootstrap ml-model \
  --output ~/projects/demand-forecast \
  --client acme-corp \
  --name "Demand Forecasting Model"

# Web application
orchestrator bootstrap webapp \
  --output ~/projects/executive-dashboard \
  --name "Executive KPI Dashboard"

# Supply chain optimization
orchestrator bootstrap supply-chain \
  --output ~/projects/network-optimization \
  --name "Distribution Network Optimization"
```

**Parameters:**
- `<template>` - Template type (required)
- `--output, -o` - Target directory (required)
- `--client, -c` - Client name for governance (optional)
- `--name, -n` - Project name (optional, defaults to directory name)
- `--description, -d` - Project description (optional)
- `--dry-run` - Preview without creating files (optional)

### Step 3: Install Dependencies

```bash
cd <project-directory>

# Install Python dependencies
pip install -r requirements.txt

# For webapp projects, also install frontend dependencies
cd frontend && npm install
```

### Step 4: Configure Project

**Edit `intake.yaml`:**
```yaml
project:
  name: "Your Project Name"
  type: "analytics"  # or ml-model, webapp, supply-chain
  description: "Your project description"

requirements:
  functional:
    - "Your specific requirement 1"
    - "Your specific requirement 2"

  technical:
    - "Your technical constraint 1"
    - "Your technical constraint 2"

  data:
    - "Data source: /path/to/data"
    - "Expected volume: X records"

success_criteria:
  - "Metric 1 >= target"
  - "Metric 2 achieved"
```

### Step 5: Add Project-Specific Knowledge (Optional)

```bash
# Copy project knowledge template
cp .claude/knowledge/projects/README.md .claude/knowledge/projects/my-project.yaml

# Edit my-project.yaml with domain-specific information
vim .claude/knowledge/projects/my-project.yaml
```

### Step 6: Start Orchestrator Workflow

```bash
# Initialize orchestrator run
orchestrator run start --intake intake.yaml

# Execute first phase (planning)
orchestrator run next

# Review planning artifacts
ls .claude/checkpoints/planning/

# Approve consensus if required
orchestrator run approve

# Continue workflow
orchestrator run next
```

### Step 7: Development Iteration

```bash
# Add your data
cp /path/to/data.csv data/raw/

# Run analysis/development
jupyter lab  # For analytics/ML projects
# OR
npm run dev  # For webapp projects

# Test your code
pytest tests/

# Check repository hygiene
orchestrator run repo-hygiene

# Commit changes
git add .
git commit -m "feat: implement feature X"
git push
```

---

## Method 2: GitHub Template Button (Detailed Guide)

### Step 1: Create Repository from Template

1. **Navigate to:** https://github.com/kearney/claude-code-orchestrator
2. **Click:** Green **"Use this template"** button (top right)
3. **Fill in:**
   - **Repository name:** `my-new-project`
   - **Description:** Your project description
   - **Visibility:** Private (recommended) or Public
4. **Click:** **"Create repository from template"**

### Step 2: Clone Your New Repository

```bash
git clone https://github.com/your-org/my-new-project.git
cd my-new-project
```

### Step 3: Clean Up Unnecessary Files

The GitHub template includes everything. Remove what you don't need:

```bash
# Remove example client configs (keep kearney-default)
rm -rf clients/example-client/
rm -rf clients/acme-corp/  # If exists

# Remove example intake files
rm -rf intake/*.yaml

# Remove project-specific artifacts
rm -rf backups/
rm -rf data/  # You'll recreate this
rm -rf models/
rm -rf reports/

# Remove analytics/app directories if not needed
rm -rf analytics/  # If not analytics project
rm -rf apps/       # If not webapp project
```

### Step 4: Customize for Your Project

**Update `README.md`:**
```bash
# Replace template notice
sed -i '' 's/Claude Code Orchestrator/Your Project Name/g' README.md

# Remove sections that don't apply to your project
vim README.md
```

**Update `CLAUDE.md`:**
```markdown
# Replace placeholders
Project Name: My New Project
Project Type: analytics  # or ml-model, webapp, supply-chain
Description: Your description
```

**Update `pyproject.toml`:**
```toml
[project]
name = "my-new-project"  # Change this
description = "Your description"  # Change this
```

### Step 5: Set Up Project Structure

**For Analytics Projects:**
```bash
mkdir -p data/{raw,interim,processed}
mkdir -p notebooks
mkdir -p reports
```

**For ML Projects:**
```bash
mkdir -p data/{raw,interim,processed,features}
mkdir -p models/{experiments,checkpoints}
mkdir -p notebooks
```

**For Webapp Projects:**
```bash
mkdir -p frontend/{src,public}
mkdir -p backend/{api,models,services}
```

### Step 6: Create Intake YAML

```bash
cp intake/intake.template.yaml intake/my-project.yaml

# Edit with your project requirements
vim intake/my-project.yaml
```

### Step 7: Install Dependencies

```bash
pip install -r requirements.txt

# For webapp projects
cd frontend && npm install
cd ../backend && pip install -r requirements.txt
```

### Step 8: Start Development

```bash
# Initialize orchestrator run
orchestrator run start --intake intake/my-project.yaml

# Execute workflow
orchestrator run next
```

---

## Post-Creation Checklist

Use this checklist after creating a project with either method:

### Configuration

- [ ] **Update project name** in README.md, CLAUDE.md, pyproject.toml
- [ ] **Configure client governance** (if applicable)
  ```bash
  # Copy default governance
  cp clients/kearney-default/governance.yaml clients/my-client/governance.yaml

  # Customize for client
  vim clients/my-client/governance.yaml
  ```
- [ ] **Customize design system theme** (if client-specific branding)
  ```bash
  cp design_system/web/tokens.css design_system/clients/my-client/theme.css
  vim design_system/clients/my-client/theme.css
  ```
- [ ] **Update intake.yaml** with real project requirements

### Data Setup

- [ ] **Create data directories**
  ```bash
  mkdir -p data/{raw,interim,processed}
  ```
- [ ] **Place raw data files** in `data/raw/`
- [ ] **Create data dictionary** in `docs/data_dictionary.md`
- [ ] **Add .gitignore rules** for large data files

### Version Control

- [ ] **Create .gitignore** overrides for project-specific files
- [ ] **Set up branch protection** on main branch (GitHub settings)
- [ ] **Create initial commit**
  ```bash
  git add .
  git commit -m "chore: initial project setup from template"
  git push
  ```

### CI/CD

- [ ] **Configure GitHub secrets** (if using CI/CD)
  - `ORCHESTRATOR_API_KEY` (if applicable)
  - `CLIENT_CREDENTIALS` (if applicable)
- [ ] **Enable GitHub Actions** (Settings → Actions → Allow all actions)
- [ ] **Test CI pipeline**
  ```bash
  git commit --allow-empty -m "test: trigger CI"
  git push
  ```

### Documentation

- [ ] **Create project-specific knowledge** in `.claude/knowledge/projects/`
- [ ] **Document architectural decisions** (create first ADR)
  ```bash
  cp .claude/decisions/template.md .claude/decisions/ADR-001-initial-architecture.md
  vim .claude/decisions/ADR-001-initial-architecture.md
  ```
- [ ] **Update README.md** with project-specific instructions
- [ ] **Create user guide** in `docs/user_guide.md` (if applicable)

### Orchestrator Workflow

- [ ] **Validate intake configuration**
  ```bash
  orchestrator intake validate
  ```
- [ ] **Start orchestrator run**
  ```bash
  orchestrator run start --intake intake.yaml
  ```
- [ ] **Execute planning phase**
  ```bash
  orchestrator run next
  ```
- [ ] **Review and approve consensus**
  ```bash
  cat .claude/consensus/REQUEST.md
  orchestrator run approve
  ```

### Quality Gates

- [ ] **Run repository hygiene scan**
  ```bash
  orchestrator run repo-hygiene
  ```
- [ ] **Fix any hygiene issues** reported
- [ ] **Set up pre-commit hooks**
  ```bash
  pre-commit install
  pre-commit run --all-files
  ```
- [ ] **Run tests**
  ```bash
  pytest tests/
  ```

### Team Setup

- [ ] **Add collaborators** to GitHub repository
- [ ] **Set up Slack notifications** (if using)
- [ ] **Create project in project management tool** (Jira, etc.)
- [ ] **Schedule kickoff meeting** with stakeholders

---

## Troubleshooting

### Issue: Bootstrap Command Not Found

**Symptom:**
```bash
orchestrator: command not found
```

**Fix:**
```bash
# Install orchestrator CLI
cd /path/to/claude-code-orchestrator
pip install -e .

# Verify installation
orchestrator --version
```

### Issue: Template Files Not Copied

**Symptom:** Bootstrap creates directory but files are missing

**Fix:**
```bash
# Ensure you're in orchestrator root directory
cd /path/to/claude-code-orchestrator

# Check templates exist
ls templates/project-types/

# Run bootstrap with verbose output
orchestrator bootstrap analytics --output ~/test --dry-run
```

### Issue: Client Governance Not Found

**Symptom:**
```
Warning: Client governance not found: clients/acme-corp/governance.yaml
```

**Fix:**
```bash
# Create client governance from default
mkdir -p clients/acme-corp
cp clients/kearney-default/governance.yaml clients/acme-corp/governance.yaml

# Customize for client
vim clients/acme-corp/governance.yaml
```

### Issue: Git Not Initialized

**Symptom:** No git repository after bootstrap

**Fix:**
```bash
cd <project-directory>

# Initialize git manually
git init
git add .
git commit -m "chore: initial commit from template"

# Add remote
git remote add origin https://github.com/org/repo.git
git push -u origin main
```

### Issue: Dependencies Won't Install

**Symptom:**
```
ERROR: Could not find a version that satisfies the requirement...
```

**Fix:**
```bash
# Update pip
pip install --upgrade pip

# Install with verbose output
pip install -r requirements.txt -v

# If specific package fails, try without version constraint
pip install pandas  # Instead of pandas>=2.0.0
```

### Issue: Intake Validation Fails

**Symptom:**
```
Error: Invalid intake configuration
```

**Fix:**
```bash
# Validate intake YAML syntax
python -c "import yaml; yaml.safe_load(open('intake.yaml'))"

# Check against schema
orchestrator intake validate --verbose
```

### Issue: Orchestrator Workflow Won't Start

**Symptom:**
```
Error: No active workflow configuration
```

**Fix:**
```bash
# Ensure intake.yaml exists
ls intake.yaml

# Check workflow configuration
cat .claude/checkpoints/workflow.yaml

# Start run with explicit intake path
orchestrator run start --intake ./intake.yaml
```

---

## Advanced Usage

### Creating Custom Templates

You can create your own project templates:

1. **Copy existing template:**
   ```bash
   cp templates/project-types/analytics.yaml templates/project-types/my-template.yaml
   ```

2. **Customize template:**
   ```yaml
   name: "My Custom Template"
   type: "custom"
   description: "My project type"

   directory_structure:
     - "my_custom_dir/"

   agents:
     - name: "Custom Agent"
       role: "Do custom things"
   ```

3. **Use custom template:**
   ```bash
   orchestrator bootstrap my-template --output ~/projects/test
   ```

### Forking the Orchestrator Framework

If you need to modify the orchestrator framework itself:

1. **Fork on GitHub** (not "Use this template")
2. **Clone your fork:**
   ```bash
   git clone https://github.com/your-org/claude-code-orchestrator-fork.git
   ```
3. **Make changes** to orchestrator code
4. **Create feature branch:**
   ```bash
   git checkout -b feature/my-enhancement
   ```
5. **Submit PR** back to main repository (if contributing)

### Using with GitHub Codespaces

1. **Create codespace** from template repository
2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```
3. **Run bootstrap:**
   ```bash
   orchestrator bootstrap analytics --output /workspace/my-project
   ```
4. **Develop in browser** (VS Code web)

---

## FAQ

**Q: Should I use bootstrap command or GitHub template button?**
A: Use bootstrap command (Method 1) for 95% of projects. It's faster, more flexible, and gives you exactly what you need.

**Q: Can I use both methods?**
A: No need. Choose one method that fits your workflow.

**Q: How do I update an existing project with new template changes?**
A: Bootstrap into a temporary directory, then manually copy updated files to your project:
```bash
orchestrator bootstrap analytics --output /tmp/temp-project
cp /tmp/temp-project/.claude/skills/* my-project/.claude/skills/
```

**Q: What if I need a template type not in the list?**
A: Create a custom template (see "Creating Custom Templates" above) or start with the closest existing template and customize.

**Q: Can I make this template public?**
A: Check with Kearney legal/compliance first. Update `.github/template-config.yaml` `visibility: "public"` if approved.

**Q: How do I contribute improvements back to the template?**
A: Create a feature branch, make changes, submit PR to main orchestrator repository.

**Q: Do I need to keep the orchestrator repository after creating a project?**
A: Yes, if using bootstrap command. No, if using GitHub template button (project is fully standalone).

---

**Last Updated:** 2025-01-26
**Version:** 1.0.0
**Questions?** Open an issue on the main orchestrator repository.
