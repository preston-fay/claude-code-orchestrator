# GitHub Deployment Steps for Orchestrator v1.0.0

The feature branch is pushed and ready. Complete these steps to deploy:

## Option 1: Use GitHub CLI (Recommended)

```bash
# 1. Authenticate (one-time setup)
gh auth login
# Follow prompts to authenticate with GitHub

# 2. Create Pull Request
gh pr create \
  --title "feat: add complete methodology framework for project replication" \
  --body-file PR_BODY.md \
  --base main \
  --head feature/orchestrator-methodology-framework

# 3. Merge Pull Request
gh pr merge --merge --delete-branch

# 4. Switch to main and pull
git checkout main
git pull origin main

# 5. Create Release
gh release create v1.0.0 \
  --title "v1.0.0 - Orchestrator Methodology Framework" \
  --notes-file RELEASE_NOTES.md \
  --target main

# 6. Add Topics
gh repo edit preston-fay/claude-code-orchestrator \
  --add-topic orchestrator \
  --add-topic claude-code \
  --add-topic methodology \
  --add-topic multi-agent \
  --add-topic project-template \
  --add-topic bootstrap

# 7. Enable Template Repository (manual step)
# Go to: https://github.com/preston-fay/claude-code-orchestrator/settings
# Check: ☑️ Template repository
```

## Option 2: Use GitHub Web UI

### Step 1: Create Pull Request
1. Go to: https://github.com/preston-fay/claude-code-orchestrator
2. Click "Compare & pull request" for `feature/orchestrator-methodology-framework`
3. Title: `feat: add complete methodology framework for project replication`
4. Body: Copy content from `PR_BODY.md` (created below)
5. Click "Create pull request"

### Step 2: Merge Pull Request
1. Review the PR files changed
2. Click "Merge pull request"
3. Click "Confirm merge"
4. Click "Delete branch" (optional cleanup)

### Step 3: Create Release
1. Go to: https://github.com/preston-fay/claude-code-orchestrator/releases
2. Click "Draft a new release"
3. Tag: `v1.0.0`
4. Target: `main`
5. Title: `v1.0.0 - Orchestrator Methodology Framework`
6. Description: Copy content from `RELEASE_NOTES.md` (created below)
7. Click "Publish release"

### Step 4: Add Topics
1. Go to: https://github.com/preston-fay/claude-code-orchestrator
2. Click ⚙️ (settings icon) next to "About"
3. Add topics: `orchestrator`, `claude-code`, `methodology`, `multi-agent`, `project-template`, `bootstrap`
4. Click "Save changes"

### Step 5: Enable Template Repository
1. Go to: https://github.com/preston-fay/claude-code-orchestrator/settings
2. Scroll to "Template repository" section
3. Check: ☑️ Template repository
4. Save changes

## Files Created

- `PR_BODY.md` - Pull request description
- `RELEASE_NOTES.md` - Release notes for v1.0.0
- `deploy-to-github.sh` - Automated deployment script (requires `gh` auth)

## Verification

After deployment:

```bash
# Verify release exists
gh release view v1.0.0

# Verify topics
gh repo view preston-fay/claude-code-orchestrator --json repositoryTopics

# Test template functionality
# Go to: https://github.com/preston-fay/claude-code-orchestrator
# Click "Use this template" → Should create new repo from template
```
