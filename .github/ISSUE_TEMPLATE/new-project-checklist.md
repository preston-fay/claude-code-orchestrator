---
name: New Project Setup Checklist
about: Checklist for setting up a new project from the orchestrator template
title: 'New Project Setup: [Project Name]'
labels: ['setup', 'documentation', 'new-project']
assignees: ''
---

# New Project Setup: [Project Name]

**Project Type:** [analytics / ml-model / webapp / supply-chain]
**Client:** [Client Name or "Internal"]
**Created From:** [bootstrap command / GitHub template button]
**Target Completion:** [Date]

---

## 📋 Setup Checklist

### Phase 1: Initial Configuration

- [ ] **Project created**
  - Method used: [bootstrap / GitHub template]
  - Output directory: `_____`
  - Template type: `_____`

- [ ] **Update project metadata**
  - [ ] Update `README.md` (replace project name and description)
  - [ ] Update `CLAUDE.md` (add project-specific context)
  - [ ] Update `pyproject.toml` (change project name, description, version)
  - [ ] Remove template notice from README if desired

- [ ] **Configure version control**
  - [ ] Verify `.gitignore` is appropriate for project type
  - [ ] Create initial commit (if not already done)
    ```bash
    git add .
    git commit -m "chore: initial project setup from orchestrator template"
    ```
  - [ ] Create GitHub repository (if needed)
  - [ ] Add remote and push
    ```bash
    git remote add origin https://github.com/org/[repo-name].git
    git push -u origin main
    ```

### Phase 2: Client & Governance

- [ ] **Configure client governance** (if applicable)
  - [ ] Create client directory: `clients/[client-name]/`
  - [ ] Copy default governance:
    ```bash
    cp clients/kearney-default/governance.yaml clients/[client-name]/governance.yaml
    ```
  - [ ] Customize governance for client:
    - [ ] Update `quality_gates` (test coverage, security requirements)
    - [ ] Update `compliance` (GDPR, HIPAA, SOC2, etc.)
    - [ ] Update `brand_constraints` (colors, fonts, logo)
    - [ ] Update `deployment` (approval workflows, windows)
    - [ ] Update `documentation` (language, required docs)
    - [ ] Add `notifications` (stakeholder emails, Slack webhook)

- [ ] **Customize design system** (if client-specific branding)
  - [ ] Create client theme: `design_system/clients/[client-name]/theme.css`
  - [ ] Add client logo: `design_system/clients/[client-name]/logo.svg`
  - [ ] Test C-suite presentation templates with client theme

### Phase 3: Project Configuration

- [ ] **Update intake.yaml**
  - [ ] Set accurate project name and description
  - [ ] Define functional requirements (specific to project goals)
  - [ ] Define technical requirements (tech stack, constraints)
  - [ ] Define data requirements (sources, volume, quality)
  - [ ] Set timeline and budget constraints
  - [ ] Define success criteria (measurable outcomes)
  - [ ] Validate intake configuration:
    ```bash
    orchestrator intake validate
    ```

- [ ] **Create project-specific knowledge**
  - [ ] Copy template:
    ```bash
    cp .claude/knowledge/projects/README.md .claude/knowledge/projects/[project-slug].yaml
    ```
  - [ ] Document domain knowledge (business context, terminology)
  - [ ] Document data sources and schemas
  - [ ] Document business rules and constraints

### Phase 4: Data & Infrastructure

**For Analytics/ML Projects:**

- [ ] **Set up data directories**
  - [ ] Create `data/raw/` for original data
  - [ ] Create `data/interim/` for intermediate processing
  - [ ] Create `data/processed/` for analysis-ready data
  - [ ] Add appropriate `.gitkeep` files
  - [ ] Update `.gitignore` for large data files

- [ ] **Place initial data**
  - [ ] Copy raw data files to `data/raw/`
  - [ ] Verify data quality and completeness
  - [ ] Create `docs/data_dictionary.md` with schema documentation
  - [ ] Document data sources and provenance

- [ ] **Configure model storage** (ML projects only)
  - [ ] Verify `models/` directory structure
  - [ ] Set up MLflow tracking (if applicable):
    ```bash
    mlflow ui
    ```
  - [ ] Configure model registry or S3 bucket for artifacts

**For Webapp Projects:**

- [ ] **Configure frontend**
  - [ ] Install frontend dependencies: `cd frontend && npm install`
  - [ ] Update `frontend/package.json` with project name
  - [ ] Configure environment variables in `frontend/.env.local`
  - [ ] Test development server: `npm run dev`

- [ ] **Configure backend**
  - [ ] Install backend dependencies: `pip install -r backend/requirements.txt`
  - [ ] Configure database connection in `backend/.env`
  - [ ] Run database migrations (if applicable)
  - [ ] Test API server: `uvicorn backend.main:app --reload`

### Phase 5: Development Environment

- [ ] **Install dependencies**
  ```bash
  # Python dependencies
  pip install -r requirements.txt

  # Development dependencies
  pip install -r requirements-dev.txt

  # For webapp projects
  cd frontend && npm install
  ```

- [ ] **Set up pre-commit hooks**
  ```bash
  pre-commit install
  pre-commit run --all-files
  ```

- [ ] **Verify tooling**
  - [ ] Test linting: `flake8 src/ tests/`
  - [ ] Test formatting: `black src/ tests/ --check`
  - [ ] Test type checking: `mypy src/` (if using type hints)

- [ ] **Run initial tests**
  ```bash
  pytest tests/ -v
  ```

### Phase 6: CI/CD Setup

- [ ] **Configure GitHub Actions**
  - [ ] Review `.github/workflows/ci.yaml`
  - [ ] Update workflow triggers if needed
  - [ ] Add repository secrets (Settings → Secrets → Actions):
    - [ ] `ORCHESTRATOR_API_KEY` (if applicable)
    - [ ] `CLIENT_CREDENTIALS` (if applicable)
    - [ ] `SLACK_WEBHOOK` (if using Slack notifications)

- [ ] **Enable GitHub features**
  - [ ] Enable Issues (Settings → Features)
  - [ ] Enable Projects (if tracking work in GitHub)
  - [ ] Disable Wikis (use `docs/` instead)

- [ ] **Configure branch protection** (Settings → Branches)
  - [ ] Protect `main` branch
  - [ ] Require pull request reviews (recommended: 1)
  - [ ] Require status checks to pass
  - [ ] Require branches to be up to date

- [ ] **Test CI pipeline**
  ```bash
  git commit --allow-empty -m "test: trigger CI pipeline"
  git push
  ```
  - [ ] Verify GitHub Actions workflow runs successfully
  - [ ] Review workflow logs for any issues

### Phase 7: Documentation

- [ ] **Create architectural decisions**
  - [ ] Copy ADR template:
    ```bash
    cp .claude/decisions/template.md .claude/decisions/ADR-001-initial-architecture.md
    ```
  - [ ] Document initial architecture decisions
  - [ ] Document technology selection rationale

- [ ] **Update project documentation**
  - [ ] Complete `README.md` with project-specific instructions
  - [ ] Create `docs/architecture.md` (system design, data flows)
  - [ ] Create `docs/deployment_guide.md` (how to deploy)
  - [ ] Create `docs/user_guide.md` (if client-facing)
  - [ ] Update `CONTRIBUTING.md` with team workflows

### Phase 8: Orchestrator Workflow

- [ ] **Start orchestrator run**
  ```bash
  orchestrator run start --intake intake.yaml
  ```

- [ ] **Execute planning phase**
  ```bash
  orchestrator run next
  ```
  - [ ] Review planning artifacts in `.claude/checkpoints/planning/`
  - [ ] Verify architectural decisions are documented
  - [ ] Check consensus request: `cat .claude/consensus/REQUEST.md`

- [ ] **Approve consensus** (if required)
  ```bash
  orchestrator run approve
  ```

- [ ] **Continue workflow phases**
  - [ ] Data Engineering: `orchestrator run next`
  - [ ] Development: `orchestrator run next`
  - [ ] QA: `orchestrator run next`
  - [ ] Documentation: `orchestrator run next`

### Phase 9: Quality Gates

- [ ] **Run repository hygiene scan**
  ```bash
  orchestrator run repo-hygiene
  ```
  - [ ] Review `reports/repo_hygiene_report.md`
  - [ ] Fix any violations (large files, secrets, notebook outputs)
  - [ ] Verify cleanliness score meets governance threshold

- [ ] **Run security scan** (if required by governance)
  ```bash
  bandit -r src/ -f json -o reports/security_scan.json
  ```

- [ ] **Check test coverage** (if required by governance)
  ```bash
  pytest tests/ --cov=src --cov-report=html
  # Open htmlcov/index.html to view coverage report
  ```

### Phase 10: Team Onboarding

- [ ] **Add team members**
  - [ ] Add collaborators to GitHub repository
  - [ ] Assign roles (admin, write, read)
  - [ ] Add to project board (if using GitHub Projects)

- [ ] **Set up communication**
  - [ ] Create Slack channel (if applicable)
  - [ ] Add Slack webhook to governance configuration
  - [ ] Send team welcome message with repository link

- [ ] **Schedule meetings**
  - [ ] Project kickoff meeting
  - [ ] Weekly standup or sync meetings
  - [ ] Demo/review cadence with stakeholders

### Phase 11: Final Validation

- [ ] **Verify all files are correct**
  - [ ] No template placeholders remaining (`grep -r "{{" .`)
  - [ ] No example or dummy data committed
  - [ ] No secrets or credentials in version control

- [ ] **Test end-to-end**
  - [ ] Clone repository to fresh directory
  - [ ] Follow README.md instructions from scratch
  - [ ] Verify all commands work as documented

- [ ] **Create project milestone**
  - [ ] Create GitHub milestone for MVP or Phase 1
  - [ ] Add issues for initial sprint
  - [ ] Assign issues to team members

---

## 📝 Notes

**Customizations Made:**
<!-- Document any non-standard configurations or customizations -->

**Blockers or Issues:**
<!-- Document any setup issues encountered and how they were resolved -->

**Additional Context:**
<!-- Any other relevant information about this project setup -->

---

## ✅ Completion

Once all checklist items are complete:

1. **Review with team lead** - Confirm setup meets requirements
2. **Update this issue** - Add any lessons learned or improvements for next time
3. **Close this issue** - Project setup is complete!
4. **Start development** - Begin first sprint or iteration

---

**Setup completed by:** @[username]
**Date completed:** [YYYY-MM-DD]
**Time to complete:** [X hours/days]

<!--
This issue template is maintained in .github/ISSUE_TEMPLATE/new-project-checklist.md
To improve this template, submit a PR to the orchestrator repository.
-->
