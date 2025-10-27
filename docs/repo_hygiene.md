# Repository Hygiene Guide

## Philosophy

A clean repository is a maintainable repository. The Claude Code Orchestrator enforces repository hygiene through automated scanning, **cleanliness scoring**, safety gates, and consensus-gated cleanup with clear policies about what belongs in version control.

## Cleanliness Score (NEW)

The hygiene system computes a **Cleanliness Score** (0-100) based on weighted components:

- **No Orphans** (30%): Files not referenced in code/docs
- **No Large Files** (25%): Binaries exceeding thresholds
- **No Dead Code** (20%): Unused functions/classes/imports
- **No Notebook Outputs** (15%): Clean Jupyter notebooks
- **No Secrets** (10%): No exposed credentials

**Grading:** A+ (95-100), A (90-94), B+ (85-89), B (80-84), C+ (75-79), D-F (<75)

**Quality Gates:** CI fails if score < 85, warns if orphans ≥ 10, blocks if orphans ≥ 50

### Core Principles

1. **Version control is for code, not data**: Large datasets, model artifacts, and binary files belong in artifact stores (S3, MLflow, DVC), not Git
2. **Dead code is technical debt**: Unused functions, imports, and files add maintenance burden and confuse contributors
3. **Explicit over implicit**: If a file is exempt from cleanup, it should be in `.tidyignore` with a comment explaining why
4. **Safety first**: All cleanup actions require approval and are reversible via Git
5. **Incremental improvement**: Hygiene is maintained through regular small cleanups, not infrequent large sweeps

## What Belongs in Version Control

### ✅ Should be committed

- **Source code** (.py, .js, .ts, etc.)
- **Tests** (test_*.py, *.test.js, etc.)
- **Documentation** (README.md, docs/*.md, inline comments)
- **Configuration** (pyproject.toml, .yaml configs, .env.example)
- **Small reference data** (< 100KB, e.g., sample datasets for tests)
- **Infrastructure code** (.github/workflows/, Dockerfiles)
- **Project metadata** (LICENSE, CHANGELOG.md)

### ❌ Should NOT be committed

- **Large binary files** (> 1MB by default)
- **Trained models** (.pkl, .h5, .joblib, .ckpt) → use MLflow, S3, or DVC
- **Raw datasets** (data/raw/, data/external/) → use data versioning tools
- **Generated artifacts** (build/, dist/, *.pyc, __pycache__/)
- **Secrets** (.env, *.pem, credentials.json, API keys)
- **Jupyter notebook outputs** (cell outputs, execution counts)
- **Personal IDE settings** (.vscode/, .idea/)
- **OS files** (.DS_Store, Thumbs.db)

### 🔍 Review case-by-case

- **Processed data** (data/processed/) → If < 10MB and useful for tests, OK. Otherwise, version with DVC.
- **Documentation images** (docs/*.png) → If < 500KB and essential, OK. Otherwise, use external hosting.
- **Example notebooks** (examples/*.ipynb) → OK if outputs cleared. Add to `.tidyignore` if outputs are intentional.
- **Analytics dashboards** (analytics/*.html) → OK if static and < 1MB. Otherwise, deploy to hosting.

## Forbidden Artifacts

The following should **never** be committed:

1. **Secrets and credentials**
   - API keys, tokens, passwords
   - Private keys (.pem, .key)
   - Service account credentials (credentials.json, service-account.json)

2. **Large binary data**
   - Datasets > 10MB
   - Model checkpoints > 1MB
   - Videos, large images (> 1MB)

3. **Generated files**
   - Compiled Python (.pyc, __pycache__/)
   - Node modules (node_modules/)
   - Build artifacts (dist/, build/)

4. **Personal configuration**
   - IDE workspace files
   - Editor settings not shared by team
   - Local environment variables (.env)

## Running Hygiene Checks

### Quick Start

```bash
# Dry-run scan (no changes, generates reports)
orchestrator run repo-hygiene

# Review reports
open reports/repo_hygiene_report.md
open reports/PR_PLAN.md

# Apply approved cleanup (requires Consensus)
orchestrator run repo-hygiene --apply
```

### Natural Language Triggers

```bash
# These all trigger the same hygiene scan
"tidy repo"
"cleanup repository"
"hygiene check"
```

### Command Line Options

```bash
# Override large file threshold
orchestrator run repo-hygiene --large-file-mb 5

# Dry-run with custom threshold
orchestrator run repo-hygiene --large-file-mb 10

# Apply cleanup (executes approved actions)
orchestrator run repo-hygiene --apply
```

## Understanding Reports

After running a hygiene scan, you'll find these reports in `reports/`:

### 1. `repo_hygiene_report.md`
**Executive summary** with statistics and severity breakdown.

```markdown
## Summary
- Orphaned files: 12 files (3.2 MB)
- Large binaries: 5 files (47.8 MB)
- Dead code: 8 functions, 3 imports
- Notebook outputs: 4 notebooks

## Severity Breakdown
- Critical: 17 (orphans + large files)
- Warning: 11 (dead code + notebooks)
- Info: 3 (unused imports)
```

### 2. `PR_PLAN.md`
**Actionable cleanup plan** with checkboxes for approval.

```markdown
## Safe Actions (Low Risk)
- [ ] 1. Remove orphaned test file: tests/old/legacy_test.py
      - Command: git rm tests/old/legacy_test.py
      - Reason: No references found, last modified 6 months ago
      - Risk: SAFE
```

**Risk Levels:**
- **SAFE**: No dependencies, safe to delete (orphaned files, old tests)
- **NEEDS_REVIEW**: May have hidden dependencies (large binaries, utils)
- **MANUAL_REVIEW**: Requires code inspection (dead code, unused imports)

### 3. `dead_code.md`
**Static analysis results** with file:line references.

```markdown
## Unused Functions
- calculate_legacy_metric in [src/utils/old.py:42](src/utils/old.py#L42)
- process_deprecated_format in [src/data/loaders.py:15](src/data/loaders.py#L15)
```

### 4. `large_files.csv`
**Large binary files** exceeding threshold.

| path | size_mb | type | whitelisted | recommendation |
|------|---------|------|-------------|----------------|
| docs/old_diagram.png | 15.2 | .png | false | REVIEW |
| data/raw/sample.csv | 47.8 | .csv | true | KEEP |

### 5. `orphans.csv`
**Unreferenced files** (no imports or mentions).

| path | last_modified | references_found | recommendation |
|------|---------------|------------------|----------------|
| tests/old/legacy_test.py | 2024-04-15 | 0 | REVIEW |

## Dry-Run vs. Apply Mode

### Dry-Run (Default)

```bash
orchestrator run repo-hygiene
```

**What it does:**
- ✅ Scans repository for hygiene issues
- ✅ Generates all 5 reports
- ✅ Creates PR_PLAN.md with proposed actions
- ❌ Does NOT modify any files
- ❌ Does NOT delete anything

**Use when:**
- Running regular hygiene audits
- Exploring what needs cleanup
- Generating reports for team review

### Apply Mode

```bash
orchestrator run repo-hygiene --apply
```

**What it does:**
- ✅ Runs full scan (same as dry-run)
- ✅ Executes approved actions from PR_PLAN.md
- ✅ Clears notebook outputs (if not whitelisted)
- ✅ Runs tests after each deletion group
- ❌ Only executes SAFE actions (not NEEDS_REVIEW or RISKY)

**Use when:**
- You've reviewed PR_PLAN.md and approve the changes
- Consensus agent has approved the cleanup
- You're ready to create a hygiene PR

**Safety mechanisms:**
- Requires explicit `--apply` flag
- Routes to Consensus agent for approval
- Only executes checked actions in PR_PLAN.md
- Stops on first test failure
- All changes are reversible via `git revert`

## Approval Flow

The hygiene system enforces a consensus-gated approval process:

```
1. Developer runs: orchestrator run repo-hygiene
   ↓
2. Steward generates reports + PR_PLAN.md
   ↓
3. Steward hands off to Consensus agent
   ↓
4. Consensus reviews PR_PLAN.md, checks safe actions
   ↓
5. Developer runs: orchestrator run repo-hygiene --apply
   ↓
6. Developer agent executes approved actions
   ↓
7. Tests run after each deletion group
   ↓
8. Developer creates PR with hygiene template
   ↓
9. Team reviews PR, merges if green
```

**Key approval gates:**
- **Consensus** approves the PR plan before execution
- **Tests** must pass after each deletion
- **PR review** by team before merging

## Configuration

### `configs/hygiene.yaml`

Customize thresholds and rules:

```yaml
# File size threshold (MB)
large_file_mb: 1

# Binary extensions to check
binary_exts: [".png", ".jpg", ".pdf", ...]

# Clear notebook outputs on --apply?
notebook_clear_outputs: false

# Directories exempt from cleanup
whitelist_globs:
  - "data/external/**"
  - "docs/**"
  - ".github/**"

# Dead code analysis
dead_code:
  min_confidence: 60
  exclude_patterns: ["__init__\\.py$", "test_.*\\.py$"]
  exclude_names: ["__all__", "__version__", "main"]
```

### `.tidyignore`

Explicitly exempt files from cleanup:

```
# Keep example datasets
data/external/sample/**

# Preserve documentation assets
docs/static/**

# Training notebooks (outputs intentional)
notebooks/experiments/**
```

**Best practices:**
- Add comments explaining WHY each exemption exists
- Use glob patterns for directories
- Review `.tidyignore` during hygiene scans

## CI Integration

The hygiene system integrates with GitHub Actions CI:

### Automated Checks

In `.github/workflows/ci.yml`:

```yaml
hygiene:
  runs-on: ubuntu-latest
  steps:
    - uses: actions/checkout@v4
    - name: Setup Python
      uses: actions/setup-python@v5
      with:
        python-version: "3.12"
    - name: Install dependencies
      run: pip install -e ".[dev]"
    - name: Run hygiene scan
      run: |
        python3 scripts/scan_repo.py
        python3 scripts/dead_code_report.py
        python3 scripts/notebook_sanitizer.py
        python3 scripts/hygiene_glue.py
    - name: Upload reports
      uses: actions/upload-artifact@v4
      with:
        name: hygiene-reports
        path: reports/
    - name: Check for violations
      run: |
        # Fail if non-whitelisted notebook outputs found
        python3 -c "import csv; ..."
```

**Checks enforced:**
- ✅ No notebook outputs in non-whitelisted directories
- ✅ No files exceeding size threshold (unless whitelisted)
- ⚠️ Dead code warnings (not blocking)

## Troubleshooting

### "Orchestrator is busy"

```
⚠️  Orchestrator is currently running a workflow.
```

**Solution:** Wait for current workflow to finish, or run `orchestrator run --abort`.

### "Reports directory not found"

```
Error: reports/ does not exist
```

**Solution:** The `reports/` directory is created automatically. Check that it's not `.gitignore`d.

### "False positive: file is not orphaned"

If a file is flagged as orphaned but is actually used:

1. **Add to `.tidyignore`**:
   ```
   # This file is used by external process
   scripts/legacy_importer.py
   ```

2. **Or add a reference** in code/docs:
   ```python
   # See also: scripts/legacy_importer.py
   ```

### "Notebook outputs keep being flagged"

If notebook outputs are intentional (e.g., tutorial notebooks):

1. **Whitelist the directory** in `configs/hygiene.yaml`:
   ```yaml
   whitelist_globs:
     - "notebooks/tutorials/**"
   ```

2. **Or add to `.tidyignore`**:
   ```
   # Tutorial notebooks (outputs intentional)
   notebooks/tutorials/**/*.ipynb
   ```

## Best Practices

### 1. Run Hygiene Regularly

- **Weekly**: Run dry-run scan, review reports
- **Monthly**: Execute approved cleanup
- **Before releases**: Ensure clean state

### 2. Incremental Cleanup

- Don't try to clean everything at once
- Focus on high-severity items first (orphans, large files)
- Split large cleanups into multiple PRs

### 3. Document Exemptions

- Every `.tidyignore` entry should have a comment
- Explain WHY, not just WHAT
- Review exemptions quarterly

### 4. Test After Cleanup

- Run full test suite after deletions
- Check that imports still resolve
- Verify functionality unchanged

### 5. Coordinate with Team

- Announce hygiene PRs in team chat
- Give 24 hours for review before merging
- Avoid hygiene cleanup during feature development sprints

## Integration with Orchestrator

The Steward agent is a core component of the Claude Code Orchestrator:

### Workflow Integration

```yaml
# In .claude/config.yaml
workflow:
  phases:
    - name: repo_hygiene
      agents: [steward]
      requires_consensus: true
      optional: true  # Ad-hoc, not part of standard workflow
```

### Subagent Communication

**Steward** → **Consensus**: "Please approve these cleanup actions"
**Consensus** → **Steward**: "Approved: actions 1, 2, 4, 7"
**Steward** → **Developer**: "Execute these approved actions"
**Developer** → **QA**: "Verify tests pass after cleanup"

## FAQ

**Q: How often should I run hygiene checks?**
A: Weekly dry-runs, monthly apply (with approval).

**Q: What if I disagree with a recommendation?**
A: Add the file to `.tidyignore` with a comment explaining why it's needed.

**Q: Can I customize the large file threshold?**
A: Yes, use `--large-file-mb 5` or edit `configs/hygiene.yaml`.

**Q: Will this delete my data files?**
A: No. `data/` is whitelisted by default. Check `.tidyignore` and `configs/hygiene.yaml`.

**Q: What if cleanup breaks something?**
A: All changes are Git commits. Revert with `git revert <commit>`. Tests run after each deletion group.

**Q: How do I skip hygiene CI checks temporarily?**
A: Add `[skip hygiene]` to your commit message (configure in `.github/workflows/ci.yml`).

## Framework Validation

Beyond file cleanliness, the hygiene system validates the orchestrator framework components:

### Skills Validation

**Location:** `.claude/skills/*.yaml`

**Checks:**

1. **YAML Syntax**: All skill files parse correctly
2. **Required Fields**: `name`, `category`, `description`, `methodology`, `when_to_use`
3. **Category Values**: Must be one of: `analytics`, `ml`, `optimization`, `survey`
4. **Methodology Structure**: Array of steps with `step` and `rationale` fields
5. **No Duplicates**: No two skills with same name

**Example validation:**

```python
def validate_skills():
    skills_dir = Path('.claude/skills/')
    violations = []

    for skill_file in skills_dir.glob('*.yaml'):
        try:
            skill = yaml.safe_load(skill_file.read_text())
        except yaml.YAMLError as e:
            violations.append(f"{skill_file}: Invalid YAML syntax - {e}")
            continue

        # Check required fields
        required = ['name', 'category', 'description', 'methodology', 'when_to_use']
        for field in required:
            if field not in skill:
                violations.append(f"{skill_file}: Missing required field '{field}'")

        # Validate category
        valid_categories = ['analytics', 'ml', 'optimization', 'survey']
        if skill.get('category') not in valid_categories:
            violations.append(
                f"{skill_file}: Invalid category '{skill.get('category')}'. "
                f"Must be one of: {valid_categories}"
            )

        # Validate methodology structure
        methodology = skill.get('methodology', [])
        if not isinstance(methodology, list):
            violations.append(f"{skill_file}: 'methodology' must be a list")
        else:
            for i, step in enumerate(methodology):
                if not isinstance(step, dict):
                    violations.append(f"{skill_file}: methodology[{i}] must be a dict")
                elif 'step' not in step:
                    violations.append(f"{skill_file}: methodology[{i}] missing 'step'")

    return violations
```

**Hygiene Report Includes:**

```markdown
## Skills Validation

✓ 12 skills validated
✗ 2 issues found:

- .claude/skills/custom_skill.yaml: Missing required field 'when_to_use'
- .claude/skills/old_skill.yaml: Invalid category 'legacy'. Must be: analytics, ml, optimization, survey
```

---

### Knowledge Base Validation

**Location:** `.claude/knowledge/**/*.yaml`

**Checks:**

1. **YAML Syntax**: All knowledge files parse correctly
2. **Directory Structure**: Universal, firm-wide, project-specific tiers exist
3. **No Empty Files**: Knowledge files have content (> 100 bytes)
4. **No Secrets**: No API keys, credentials in knowledge files
5. **Naming Convention**: Project knowledge follows `<project-slug>.yaml` pattern

**Example validation:**

```python
def validate_knowledge():
    knowledge_dir = Path('.claude/knowledge/')
    violations = []

    # Check directory structure
    required_dirs = ['universal', 'kearney', 'projects']
    for dir_name in required_dirs:
        dir_path = knowledge_dir / dir_name
        if not dir_path.exists():
            violations.append(f"Missing required directory: {dir_path}")

    # Validate YAML files
    for yaml_file in knowledge_dir.rglob('*.yaml'):
        if yaml_file.name == 'README.md':
            continue

        # Check file size
        if yaml_file.stat().st_size < 100:
            violations.append(f"{yaml_file}: File too small (< 100 bytes)")

        # Check YAML syntax
        try:
            content = yaml.safe_load(yaml_file.read_text())
        except yaml.YAMLError as e:
            violations.append(f"{yaml_file}: Invalid YAML - {e}")
            continue

        # Check for secrets
        text = yaml_file.read_text()
        secret_patterns = ['api_key', 'password', 'secret', 'token']
        for pattern in secret_patterns:
            if pattern in text.lower():
                violations.append(
                    f"{yaml_file}: Potential secret detected ('{pattern}')"
                )

    return violations
```

**Hygiene Report Includes:**

```markdown
## Knowledge Base Validation

✓ Universal knowledge validated (3 files)
✓ Firm-wide knowledge validated (2 files)
✓ Project-specific knowledge validated (5 files)
✗ 1 issue found:

- .claude/knowledge/projects/old-project.yaml: File too small (< 100 bytes)
```

---

### ADR Validation

**Location:** `.claude/decisions/ADR-*.md`

**Checks:**

1. **Naming Convention**: `ADR-###-title.md` format
2. **Required Sections**: Status, Context, Decision, Rationale, Alternatives, Consequences
3. **Valid Status**: Proposed, Accepted, Deprecated, Superseded
4. **Sequential Numbering**: ADR-001, ADR-002, ADR-003 (gaps OK)
5. **No Empty ADRs**: Each section has content

**Example validation:**

```python
def validate_adrs():
    decisions_dir = Path('.claude/decisions/')
    violations = []

    adr_files = sorted(decisions_dir.glob('ADR-*.md'))

    for adr_file in adr_files:
        # Check naming convention
        if not re.match(r'ADR-\d{3}-.+\.md', adr_file.name):
            violations.append(
                f"{adr_file}: Invalid naming. Use 'ADR-###-title.md'"
            )

        # Read content
        content = adr_file.read_text()

        # Check required sections
        required_sections = [
            '## Status',
            '## Context',
            '## Decision',
            '## Rationale',
            '## Alternatives',
            '## Consequences'
        ]

        for section in required_sections:
            if section not in content:
                violations.append(f"{adr_file}: Missing section '{section}'")

        # Validate status
        status_match = re.search(r'## Status\s+(\w+)', content)
        if status_match:
            status = status_match.group(1)
            valid_statuses = ['Proposed', 'Accepted', 'Deprecated', 'Superseded']
            if status not in valid_statuses:
                violations.append(
                    f"{adr_file}: Invalid status '{status}'. "
                    f"Must be: {valid_statuses}"
                )

    # Check for numbering gaps (informational, not error)
    adr_numbers = []
    for adr_file in adr_files:
        match = re.match(r'ADR-(\d{3})', adr_file.name)
        if match:
            adr_numbers.append(int(match.group(1)))

    if adr_numbers:
        expected = list(range(1, max(adr_numbers) + 1))
        gaps = set(expected) - set(adr_numbers)
        if gaps:
            violations.append(
                f"ADR numbering gaps (not critical): {sorted(gaps)}"
            )

    return violations
```

**Hygiene Report Includes:**

```markdown
## ADR Validation

✓ 15 ADRs validated
✗ 3 issues found:

- .claude/decisions/ADR-007-cache-strategy.md: Missing section '## Alternatives'
- .claude/decisions/ADR-012-api-versioning.md: Invalid status 'Draft'. Must be: Proposed, Accepted, Deprecated, Superseded
- ADR numbering gaps (not critical): [5, 9]
```

---

### Client Governance Validation

**Location:** `clients/*/governance.yaml`

**Checks:**

1. **Schema Compliance**: Validates against `clients/.schema/governance.schema.json`
2. **Required Fields**: `client_name`, `quality_gates`, `compliance`, `brand_constraints`
3. **Valid Values**: Test coverage 0-100, valid compliance frameworks (GDPR, HIPAA, SOC2)
4. **Color Format**: Hex colors match `#[0-9A-Fa-f]{6}` pattern
5. **Email Format**: Notification emails valid

**Example validation:**

```python
import jsonschema

def validate_governance():
    schema_file = Path('clients/.schema/governance.schema.json')
    schema = json.loads(schema_file.read_text())

    violations = []

    for gov_file in Path('clients').glob('*/governance.yaml'):
        if gov_file.parent.name in ['.schema', 'README.md']:
            continue

        try:
            governance = yaml.safe_load(gov_file.read_text())
        except yaml.YAMLError as e:
            violations.append(f"{gov_file}: Invalid YAML - {e}")
            continue

        # Validate against JSON schema
        try:
            jsonschema.validate(governance, schema)
        except jsonschema.ValidationError as e:
            violations.append(f"{gov_file}: Schema validation failed - {e.message}")

        # Additional checks
        # Test coverage range
        coverage = governance.get('quality_gates', {}).get('min_test_coverage')
        if coverage is not None and not (0 <= coverage <= 100):
            violations.append(
                f"{gov_file}: min_test_coverage must be 0-100, got {coverage}"
            )

        # Color format
        colors = governance.get('brand_constraints', {}).get('colors', [])
        for color in colors:
            if not re.match(r'^#[0-9A-Fa-f]{6}$', color):
                violations.append(
                    f"{gov_file}: Invalid color format '{color}'. Use #RRGGBB"
                )

        # Email format
        emails = governance.get('notifications', {}).get('email', [])
        for email in emails:
            if '@' not in email or '.' not in email.split('@')[1]:
                violations.append(f"{gov_file}: Invalid email '{email}'")

    return violations
```

**Hygiene Report Includes:**

```markdown
## Client Governance Validation

✓ kearney-default governance validated
✓ acme-corp governance validated
✗ 2 issues found:

- clients/new-client/governance.yaml: min_test_coverage must be 0-100, got 105
- clients/old-client/governance.yaml: Invalid color format 'purple'. Use #RRGGBB
```

---

### Template Compliance Validation

**Location:** `design_system/templates/**/*.html`, `design_system/templates/**/*.css`

**Checks:**

1. **Font Compliance**: Arial for presentations, Inter for web apps
2. **Color Palette**: Only approved colors used
3. **No Gridlines**: D3.js charts don't use gridlines
4. **Brand Terms**: No forbidden terminology in user-facing text
5. **File Size**: Templates < 500KB (reasonable for version control)

**Example validation:**

```python
def validate_templates():
    templates_dir = Path('design_system/templates/')
    violations = []

    # Load governance for brand constraints
    governance = yaml.safe_load(
        Path('clients/kearney-default/governance.yaml').read_text()
    )
    brand = governance.get('brand_constraints', {})

    # Check CSS files
    for css_file in templates_dir.rglob('*.css'):
        content = css_file.read_text()

        # Font compliance
        if 'presentation' in css_file.parts or 'c-suite' in css_file.parts:
            # Presentations must use Arial
            if 'font-family' in content and 'Arial' not in content:
                violations.append(
                    f"{css_file}: Presentations must use Arial font"
                )
        elif 'web' in css_file.parts or 'app' in css_file.parts:
            # Web apps must use Inter
            if 'font-family' in content and 'Inter' not in content:
                violations.append(
                    f"{css_file}: Web applications must use Inter font"
                )

        # Color compliance
        colors_found = re.findall(r'#[0-9A-Fa-f]{6}', content)
        allowed_colors = [c.upper() for c in brand.get('colors', [])]
        for color in colors_found:
            if color.upper() not in allowed_colors:
                violations.append(
                    f"{css_file}: Unapproved color {color}. "
                    f"Allowed: {allowed_colors}"
                )

    # Check HTML files
    for html_file in templates_dir.rglob('*.html'):
        content = html_file.read_text()

        # Gridlines check (D3.js charts)
        if '.tickLine' in content or 'grid: true' in content:
            violations.append(
                f"{html_file}: Charts must not use gridlines (Kearney standard)"
            )

        # Forbidden terms
        forbidden = brand.get('forbidden_terms', [])
        text_lower = content.lower()
        for term in forbidden:
            if term.lower() in text_lower:
                violations.append(
                    f"{html_file}: Contains forbidden term '{term}'"
                )

        # File size check
        size_kb = html_file.stat().st_size / 1024
        if size_kb > 500:
            violations.append(
                f"{html_file}: File too large ({size_kb:.1f} KB > 500 KB)"
            )

    return violations
```

**Hygiene Report Includes:**

```markdown
## Template Compliance Validation

✓ C-suite templates validated (3 files)
✓ Web templates validated (5 files)
✗ 2 issues found:

- design_system/templates/c-suite/old-presentation.html: Charts must not use gridlines (Kearney standard)
- design_system/templates/web/app.css: Unapproved color #FF5733. Allowed: ['#7823DC', '#FFFFFF', '#000000']
```

---

### Running Framework Validation

**Included in standard hygiene scan:**

```bash
orchestrator run repo-hygiene
```

**Standalone validation:**

```bash
# Validate specific components
python3 scripts/validate_skills.py
python3 scripts/validate_knowledge.py
python3 scripts/validate_adrs.py
python3 scripts/validate_governance.py
python3 scripts/validate_templates.py
```

**CI Integration:**

Add to `.github/workflows/ci.yml`:

```yaml
framework-validation:
  runs-on: ubuntu-latest
  steps:
    - uses: actions/checkout@v4
    - name: Validate framework components
      run: |
        python3 scripts/validate_skills.py
        python3 scripts/validate_knowledge.py
        python3 scripts/validate_adrs.py
        python3 scripts/validate_governance.py
        python3 scripts/validate_templates.py
    - name: Check for violations
      run: |
        if grep -q "✗" reports/framework_validation.md; then
          echo "Framework validation failed"
          exit 1
        fi
```

---

## See Also

- [Steward Agent Specification](.claude/agents/steward.md)
- [Hygiene Configuration](../configs/hygiene.yaml)
- [Tidyignore Patterns](../.tidyignore)
- [PR Template](../.github/PULL_REQUEST_TEMPLATE.md)
- [Skills README](../.claude/skills/README.md)
- [Knowledge Base README](../.claude/knowledge/README.md)
- [ADR System](../.claude/decisions/README.md)
- [Client Governance](../clients/README.md)
- [Template Documentation](../design_system/templates/README.md)
