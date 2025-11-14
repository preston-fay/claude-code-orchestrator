# ADR-000: Repository Hygiene

**Status:** Accepted
**Date:** 2025-11-14
**Context:** Phase 1.1 - Backups & Ignore Hygiene

---

## Context

The orchestrator repository had 8 backup YAML files tracked in version control under `backups/`:
- `config_*.yaml` (7 files with timestamps)
- `hygiene_*.yaml` (1 file)

These backup files are **ephemeral artifacts**, not source code. Tracking them in git causes:
- **Repository bloat** - Each backup adds to git history size
- **Merge conflicts** - Backup timestamps differ across branches
- **Unclear intent** - Are these reference configs or just old copies?
- **Maintenance burden** - No clear retention or cleanup policy

---

## Decision

We will **not track backup files in version control**. Instead:

### 1. Local Backup Storage

All backup files are relocated to: `~/.orchestrator/backups/`

This provides:
- ✅ **Persistence** - Backups remain available locally
- ✅ **Developer convenience** - Easy to restore if needed
- ✅ **Clean repository** - Git history uncluttered

### 2. Gitignore Rules

Added to `.gitignore`:
```gitignore
# Backups (ephemeral, keep local only)
backups/*.yaml

# Working directory
.work/

# Reports tmp directories
reports/**/tmp/
```

Existing rules already covered:
- `__pycache__/`
- `.pytest_cache/`
- `.coverage`
- `.mypy_cache/`
- `data/processed/`
- `reports/`

### 3. Gitattributes Normalization

Created `.gitattributes`:
```gitattributes
* text=auto
```

Ensures consistent line endings across platforms (Windows/Linux/macOS).

### 4. Automated Enforcement

Created `scripts/steward/check_backups.sh`:
- Runs in CI to prevent accidental tracking
- Fails if `backups/*.yaml` is tracked
- Provides clear remediation steps

### 5. Documentation

Created `backups/README.md` with:
- Explanation of relocation
- Restore instructions
- Rationale for the change

---

## Alternatives Considered

### Alternative 1: Keep Backups in Git

**Pros:**
- Version history of config changes
- Accessible to all team members

**Cons:**
- Bloats repository
- Creates merge conflicts
- No clear retention policy
- Wrong tool for the job (use config versioning or dedicated backup system)

**Decision:** Rejected. Use git tags or proper config versioning instead.

### Alternative 2: Delete Backups Entirely

**Pros:**
- Cleanest solution
- Forces good config management practices

**Cons:**
- Loses potentially useful reference configs
- May break workflows that depend on backups

**Decision:** Rejected. Too risky without understanding backup usage.

### Alternative 3: Cloud/S3 Backup Storage

**Pros:**
- Accessible to all team members
- Proper backup infrastructure
- Retention policies

**Cons:**
- Requires infrastructure setup
- Overkill for ephemeral local configs
- Costs money

**Decision:** Rejected. Local storage is sufficient for now.

---

## Consequences

### Positive

✅ **Cleaner repository** - No ephemeral files in git history
✅ **Faster operations** - Less data to transfer/clone
✅ **Fewer conflicts** - Timestamped files won't collide
✅ **Clear intent** - Only source code in version control
✅ **Automated enforcement** - CI prevents regression

### Negative

⚠️ **Local-only backups** - Not shared across team (acceptable for dev backups)
⚠️ **Manual restore** - Requires copying from `~/.orchestrator/backups/`
⚠️ **Lost on machine wipe** - Backups not cloud-backed (acceptable risk)

### Neutral

➖ **One-time migration** - Developers must run relocation once
➖ **New convention** - Team must learn local backup location

---

## Migration Steps

### For Existing Developers

If you have uncommitted changes in `backups/`:

```bash
# 1. Create local backup directory
mkdir -p ~/.orchestrator/backups

# 2. Copy your backups
cp backups/*.yaml ~/.orchestrator/backups/

# 3. Pull latest changes (includes updated .gitignore)
git pull

# 4. Verify backups are ignored
git status  # Should show no changes in backups/
```

### For New Clones

No action needed. `.gitignore` prevents tracking from the start.

### Restore Instructions

To restore an old backup:

```bash
# List available backups
ls -lh ~/.orchestrator/backups/

# Copy specific backup to config
cp ~/.orchestrator/backups/config_20251014_211132.yaml config/my-config.yaml

# Or restore to backups/ directory (not tracked)
cp ~/.orchestrator/backups/config_*.yaml backups/
```

---

## Enforcement

### CI/CD Pipeline

Added to `.github/workflows/quick-ci.yaml`:

```yaml
- name: Steward backups check
  run: bash scripts/steward/check_backups.sh
```

If backup YAMLs are accidentally tracked, CI fails with:

```
ERROR: backups/*.yaml is tracked. Move to ~/.orchestrator/backups/ and git rm it.

To fix:
  cp backups/*.yaml ~/.orchestrator/backups/
  git rm --cached backups/*.yaml
  git commit -m 'chore: untrack backup YAML files'
```

### Local Development

Run manually:

```bash
bash scripts/steward/check_backups.sh
# ✓ OK: no tracked backup YAMLs.
```

---

## Validation

### Commands Run

```bash
# Initial state
git ls-files 'backups/*.yaml'
# Output: 8 tracked files

# Migration
mkdir -p ~/.orchestrator/backups
cp backups/*.yaml ~/.orchestrator/backups/
git rm --cached backups/*.yaml

# Verification
bash scripts/steward/check_backups.sh
# ✓ OK: no tracked backup YAMLs.

git status
# Shows backups/*.yaml as deleted from index
```

### Files Modified

```
.gitignore              (added backups/*.yaml, .work/, reports/**/tmp/)
.gitattributes          (created, added * text=auto)
backups/README.md       (created, relocation docs)
scripts/steward/check_backups.sh  (created, enforcement)
```

### Files Relocated

```
~/.orchestrator/backups/config_$(date +%Y%m%d_%H%M%S).yaml
~/.orchestrator/backups/config_20251014_211132.yaml
~/.orchestrator/backups/config_20251014_212453.yaml
~/.orchestrator/backups/config_20251014_214629.yaml
~/.orchestrator/backups/config_20251014_215618.yaml
~/.orchestrator/backups/config_20251014_220641.yaml
~/.orchestrator/backups/config_20251014_222105.yaml
~/.orchestrator/backups/hygiene_20251014_213930.yaml
```

---

## Future Considerations

### If Backups Become Critical

If backup configs become critical for team collaboration:

1. **Use git tags** for important config snapshots:
   ```bash
   git tag config-snapshot-2025-11-14
   ```

2. **Version control configs explicitly** in `config/versions/`:
   ```
   config/versions/
   ├── v1.0.0.yaml
   ├── v1.1.0.yaml
   └── v2.0.0.yaml
   ```

3. **Implement proper backup system**:
   - S3/GCS for cloud backups
   - Retention policies (30/60/90 days)
   - Automated backup on config changes

### Non-YAML Backups

Python source backups (`.py` files) in `backups/` were **not modified** in this ADR:
- `admin_routes.py.20251015_102924`
- `app.py.20251015_101242`
- `app.py.security_20251015_104902`

These will be evaluated separately. Options:
1. Delete (if source control history is sufficient)
2. Move to `~/.orchestrator/backups/`
3. Add to `.gitignore` pattern: `backups/*.py.*`

---

## References

- **12-Factor App** - Store config in environment, not files
- **Git Best Practices** - Don't commit generated/ephemeral artifacts
- **Phase 1.1 Roadmap** - reports/progress_phase1.md

---

## Related Decisions

- **ADR-003:** Unified Configuration System (config management strategy)
- **Phase 1.2:** Introduced `config/default.yaml` as canonical config source

---

**Supersedes:** None
**Superseded By:** None
