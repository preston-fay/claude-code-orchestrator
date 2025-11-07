# AI Code Review Setup Guide

## Overview

The Claude Code Orchestrator includes an AI-powered code review system that automatically reviews pull requests using Claude API. This guide walks you through setting up and configuring automated code reviews for your project.

## Features

✨ **Comprehensive Reviews:**
- Security analysis (input validation, injection prevention, authentication)
- Performance optimization (algorithm efficiency, database queries, memory usage)
- Code quality (readability, maintainability, modularity, documentation)
- Best practices (error handling, logging, testing coverage, code duplication)
- Architecture adherence (design patterns, separation of concerns, dependencies)

🎯 **Intelligent Analysis:**
- Multi-perspective code review (security, performance, style, architecture)
- Severity classification (Critical, Major, Minor, Suggestions)
- Before/after code samples for recommendations
- Positive highlights (acknowledges good practices)
- Actionable recommendations with effort estimates

📊 **Automated Workflow:**
- Triggers on PR open/update
- Posts comprehensive review as PR comment
- Uploads full review report as workflow artifact
- Handles large codebases gracefully (file size limits)
- Cost-aware (tracks token usage)

---

## Prerequisites

1. **Python 3.11+** installed
2. **Anthropic API Key** from https://console.anthropic.com/settings/keys
3. **GitHub repository** with Actions enabled
4. **Orchestrator installed** (`pip install -e .`)

---

## Setup Instructions

### Step 1: Get Anthropic API Key

1. Visit https://console.anthropic.com/settings/keys
2. Sign in or create an account
3. Click **Create Key**
4. Name your key (e.g., "GitHub Actions AI Review")
5. Copy the API key (starts with `sk-ant-...`)
6. **Save it securely** - you won't be able to see it again

**Cost Expectations:**
- Average review: $0.10 - $0.50 per PR (depending on code size)
- Small PR (< 500 lines): ~$0.10
- Medium PR (500-2000 lines): ~$0.25
- Large PR (2000-5000 lines): ~$0.50
- Token pricing: https://www.anthropic.com/pricing

### Step 2: Add API Key to GitHub Secrets

1. Go to your GitHub repository
2. Navigate to **Settings** → **Secrets and variables** → **Actions**
3. Click **New repository secret**
4. Name: `ANTHROPIC_API_KEY`
5. Value: Paste your API key (`sk-ant-...`)
6. Click **Add secret**

**Security Best Practices:**
- ✅ Never commit API keys to repository
- ✅ Use GitHub Secrets for CI/CD
- ✅ Use `.env` files for local development (add to `.gitignore`)
- ✅ Rotate keys periodically (every 90 days)
- ✅ Use separate keys for dev/staging/production
- ✅ Monitor usage in Anthropic console
- ❌ Never share keys in chat/email/Slack

### Step 3: Enable Reviewer in Configuration

The reviewer is already enabled in `.claude/config.yaml`:

```yaml
subagents:
  reviewer:
    enabled: true  # AI-powered code review via Claude API
    prompt_template: subagent_prompts/reviewer.md
    checkpoint_artifacts:
      - code_review.md
      - improvements.md
      - review_checklist.md
    timeout_minutes: 15  # Review timeout
```

**No changes needed** - this is already configured for Phase 1A.

### Step 4: Verify GitHub Actions Workflow

The AI code review workflow is located at:
`.github/workflows/ai-code-review.yml`

**Triggers:**
- Pull request opened
- Pull request synchronized (new commits pushed)
- Pull request reopened

**Workflow Steps:**
1. Checkout code with full git history
2. Set up Python 3.11 and install dependencies
3. Get changed files between base and head
4. Create review scope configuration
5. Run AI code review via Claude API
6. Post review summary to PR as comment
7. Upload full review report as artifact

**Permissions Required:**
- `contents: read` - Read repository code
- `pull-requests: write` - Post review comments
- `issues: write` - Create issue comments

### Step 5: Test the Integration

#### Option A: Create Test Pull Request

1. Create a new branch:
   ```bash
   git checkout -b test/ai-review
   ```

2. Make a change to a Python file (e.g., add a function with a known issue):
   ```python
   # src/test_security.py
   def authenticate_user(username, password):
       # Security issue: SQL injection vulnerability
       query = f"SELECT * FROM users WHERE username='{username}' AND password='{password}'"
       result = db.execute(query)
       return result
   ```

3. Commit and push:
   ```bash
   git add src/test_security.py
   git commit -m "test: add authentication function for AI review testing"
   git push origin test/ai-review
   ```

4. Create PR on GitHub:
   ```bash
   gh pr create --title "Test: AI Code Review" --body "Testing AI-powered code review"
   ```

5. **Expected Result:**
   - GitHub Actions workflow runs (~2-5 minutes)
   - AI reviewer posts comprehensive review as PR comment
   - Review identifies SQL injection vulnerability as **Critical Issue**
   - Review provides before/after code samples with parameterized query recommendation
   - Full review report available as workflow artifact

#### Option B: Manual Local Testing

1. Export API key locally:
   ```bash
   export ANTHROPIC_API_KEY="sk-ant-..."
   export ORCHESTRATOR_EXECUTION_MODE="api"
   ```

2. Run orchestrator review manually:
   ```bash
   # Initialize orchestrator for review phase
   orchestrator run start --from review

   # Run next phase (reviewer)
   orchestrator run next
   ```

3. View review output:
   ```bash
   cat .claude/checkpoints/code_review.md
   ```

4. **Expected Output:**
   - Comprehensive code review report in Markdown
   - Issues categorized by severity (Critical, Major, Minor, Suggestions)
   - Specific file:line references
   - Before/after code samples
   - Review categories (Code Quality, Security, Performance, Best Practices, Architecture)
   - Token usage metadata at the end

---

## Configuration Options

### Execution Mode

The orchestrator supports three execution modes (`.claude/config.yaml`):

```yaml
orchestrator:
  execution_mode: in_session  # Default for local development
```

**Modes:**
- **`in_session`** (default): Prints instructions for Claude Code to execute manually
- **`api`**: Calls Claude API automatically (requires `ANTHROPIC_API_KEY`)
- **`stub`**: Simulated responses for testing (no API key needed)

**Override via Environment Variable:**
```bash
export ORCHESTRATOR_EXECUTION_MODE="api"  # Force API mode
```

In GitHub Actions, the workflow sets `ORCHESTRATOR_EXECUTION_MODE=api` automatically.

### Review Timeout

Adjust review timeout in `.claude/config.yaml`:

```yaml
subagents:
  reviewer:
    timeout_minutes: 15  # Default: 15 minutes
```

For large codebases, increase to 20-30 minutes.

### File Size Limits

The GitHub Actions workflow limits file sizes to prevent token overflow:

```yaml
# In ai-code-review.yml
if len(content) > 50000:  # ~12K tokens
    prompt += f'### File: {file_path} (truncated - too large)'
```

**Adjust Limit:**
Edit `.github/workflows/ai-code-review.yml`, line ~140:
```python
if len(content) > 50000:  # Change to 100000 for larger files
```

**Note:** Larger limits increase API costs and review time.

### Review Scope

Control what the reviewer analyzes in `review_scope.yaml`:

```yaml
review_scope:
  - code_quality      # Code readability, maintainability, modularity
  - security          # Input validation, injection prevention, auth
  - performance       # Algorithm efficiency, database queries, memory
  - best_practices    # Error handling, logging, testing coverage
  - architecture_adherence  # Design patterns, separation of concerns
```

**Review Depth Options:**
- `STANDARD` - Balanced review (default)
- `THOROUGH` - Deep analysis, more detailed findings
- `SECURITY_FOCUSED` - Emphasizes security vulnerabilities

Edit in `.github/workflows/ai-code-review.yml`, line ~70:
```yaml
## Review Depth
SECURITY_FOCUSED  # For authentication/payment code
```

---

## Troubleshooting

### Issue: "API key not found" Error

**Symptoms:**
- Workflow fails with "No ANTHROPIC_API_KEY found"
- Review uses stub mode instead of real API

**Solution:**
1. Verify secret exists: GitHub repo → Settings → Secrets → Actions
2. Check secret name is exactly `ANTHROPIC_API_KEY` (case-sensitive)
3. Verify workflow has permission to access secrets (check `.github/workflows/ai-code-review.yml` permissions)
4. Re-create secret if needed

### Issue: Review Timeout

**Symptoms:**
- Workflow times out after 15 minutes
- No review output generated

**Solution:**
1. Increase timeout in `.claude/config.yaml`:
   ```yaml
   reviewer:
     timeout_minutes: 30  # Increase from 15
   ```
2. Reduce file size limits to review fewer lines
3. Split large PRs into smaller changesets

### Issue: Review Not Posted to PR

**Symptoms:**
- Workflow succeeds but no comment on PR
- Review artifact exists but not posted

**Solution:**
1. Check workflow permissions in `.github/workflows/ai-code-review.yml`:
   ```yaml
   permissions:
     contents: read
     pull-requests: write  # Required for posting comments
     issues: write         # Required for issue comments
   ```
2. Verify GitHub token has necessary permissions
3. Check workflow logs for GitHub API errors

### Issue: High API Costs

**Symptoms:**
- Anthropic bill higher than expected
- Multiple reviews triggering on same PR

**Solution:**
1. Monitor token usage in workflow artifacts (see metadata at end of review)
2. Reduce file size limits to review less code
3. Add file type filters (review only `.py`, skip `.txt`, `.md`, etc.)
4. Use review depth `STANDARD` instead of `THOROUGH`
5. Set up billing alerts in Anthropic console

**Token Usage Optimization:**
```python
# In ai-code-review.yml, add file type filter
if file_path.endswith('.py'):  # Only review Python files
    with open(file_path) as f:
        content = f.read()
```

### Issue: Review Too Generic

**Symptoms:**
- Review doesn't reference specific code
- Recommendations are vague

**Solution:**
1. Ensure file contents are included in prompt (check `ai-code-review.yml` line ~130)
2. Verify review scope includes relevant categories
3. Use `THOROUGH` review depth for more detailed analysis
4. Check that changed files are correctly detected

### Issue: False Positives

**Symptoms:**
- Reviewer flags valid code as problematic
- Recommendations don't apply to project context

**Solution:**
1. Customize reviewer prompt (`subagent_prompts/reviewer.md`) with project-specific rules
2. Add coding standards to prompt context
3. Include architecture documentation in review scope
4. Train reviewer with project-specific examples

---

## Advanced Configuration

### Custom Reviewer Prompt

Customize the reviewer agent prompt for project-specific needs:

**File:** `subagent_prompts/reviewer.md`

**Example Customizations:**

**Add Project-Specific Rules:**
```markdown
### Project-Specific Guidelines

- All database queries must use SQLAlchemy ORM (no raw SQL)
- All API endpoints must include rate limiting
- All functions must have docstrings (PEP 257)
- All external API calls must have retry logic with exponential backoff
```

**Add Language-Specific Checks:**
```markdown
### Python-Specific Checks

- Type hints required for all function signatures (PEP 484)
- Use `logging` module, not `print()` statements
- Use `pathlib.Path` for file operations, not `os.path`
- Follow PEP 8 style guide (enforced by Black)
```

**Add Security Requirements:**
```markdown
### Security Checklist

- [ ] All user inputs are validated and sanitized
- [ ] All database queries use parameterized queries
- [ ] All passwords are hashed with bcrypt (cost factor 12+)
- [ ] All secrets are loaded from environment variables
- [ ] All API endpoints require authentication
```

### Cost Tracking

Track AI review costs in your workflow:

**Add Cost Calculation Step:**
```yaml
- name: Calculate review cost
  run: |
    # Extract token usage from review metadata
    INPUT_TOKENS=$(grep "Tokens:" .claude/checkpoints/code_review.md | awk '{print $2}')
    OUTPUT_TOKENS=$(grep "Tokens:" .claude/checkpoints/code_review.md | awk '{print $4}')

    # Anthropic pricing (as of 2025): $3/M input, $15/M output
    COST=$(echo "scale=2; ($INPUT_TOKENS * 3 / 1000000) + ($OUTPUT_TOKENS * 15 / 1000000)" | bc)

    echo "Review cost: \$$COST"
    echo "Input tokens: $INPUT_TOKENS"
    echo "Output tokens: $OUTPUT_TOKENS"
```

### Inline Comments (Future Enhancement)

**Note:** Phase 1A posts reviews as PR comments. Inline comments (specific line annotations) are planned for Phase 1B.

**Preview of Inline Comment Format:**
```python
# src/auth.py, line 12
# ⚠️ AI Review - Critical Issue
# SQL injection vulnerability: use parameterized query
query = f"SELECT * FROM users WHERE username='{username}'"  # ← Flagged by AI
```

---

## Usage Examples

### Example 1: Security-Focused Review for Authentication Code

**PR:** Changes to `src/auth/` module

**Review Output:**
```markdown
# Code Review Report: User Authentication API

## Summary
**Status:** APPROVED WITH SUGGESTIONS
**Issues Found:** Critical: 0, Major: 1, Minor: 2, Suggestions: 3

## Executive Summary
The authentication implementation is secure and well-structured. One major issue
identified: JWT secret not validated at startup. Minor issues: inconsistent error
format, hardcoded token expiration. Overall approved after addressing major issue.

### Major Issues (Should Fix)

**Issue 1: JWT Secret Loaded Without Validation**
- **File:** `src/auth/authService.py:12`
- **Severity:** Major
- **Category:** Security / Configuration
- **Description:** JWT secret loaded from environment without validation...
- **Code:**
  ```python
  JWT_SECRET = os.getenv("JWT_SECRET")  # No validation
  ```
- **Recommendation:**
  ```python
  JWT_SECRET = os.getenv("JWT_SECRET")
  if not JWT_SECRET or len(JWT_SECRET) < 32:
      raise ValueError("JWT_SECRET must be set and at least 32 characters")
  ```
```

### Example 2: Performance Review for Data Processing

**PR:** Changes to `src/data/processor.py`

**Review Output:**
```markdown
### Major Issues (Should Fix)

**Issue 1: N+1 Query Problem**
- **File:** `src/data/processor.py:45`
- **Severity:** Major
- **Category:** Performance
- **Description:** Loop executes database query for each item (N+1 problem)
- **Impact:** Performance degrades linearly with data size (10K items = 10K queries)
- **Code:**
  ```python
  for user_id in user_ids:
      user = db.query(User).filter_by(id=user_id).first()  # N queries
  ```
- **Recommendation:**
  ```python
  # Single bulk query
  users = db.query(User).filter(User.id.in_(user_ids)).all()
  user_dict = {user.id: user for user in users}
  for user_id in user_ids:
      user = user_dict[user_id]
  ```
- **Effort:** 1 hour
- **Impact:** ~100x faster on large datasets
```

### Example 3: Code Quality Review for Refactoring

**PR:** Refactor of `src/utils/helpers.py`

**Review Output:**
```markdown
## Positive Highlights

Excellent work on several aspects:

1. **Code Organization:** Functions are well-named, single-purpose, and properly documented
2. **Test Coverage:** 96% coverage with excellent edge case testing
3. **Type Hints:** Complete type annotations (PEP 484) improve maintainability
4. **Error Handling:** Comprehensive try-catch with specific exception types

### Suggestions (Consider)

**Suggestion 1: Extract Magic Numbers to Constants**
- **File:** `src/utils/helpers.py:23, 45, 78`
- **Category:** Code Quality / Maintainability
- **Description:** Several magic numbers (30, 100, 3600) appear without explanation
- **Benefit:** Clearer intent, easier configuration
- **Recommendation:**
  ```python
  # At module level
  DEFAULT_TIMEOUT_SECONDS = 30
  MAX_RETRY_ATTEMPTS = 3
  CACHE_TTL_SECONDS = 3600
  ```
- **Effort:** 30 minutes
```

---

## FAQ

**Q: How much does AI code review cost?**
A: Typical cost is $0.10-$0.50 per PR depending on size. Small PRs (< 500 lines) cost ~$0.10. See "Cost Expectations" section for details.

**Q: Can I run AI review locally?**
A: Yes! Set `export ANTHROPIC_API_KEY="sk-ant-..."` and `export ORCHESTRATOR_EXECUTION_MODE="api"`, then run `orchestrator run start --from review`.

**Q: Does the reviewer have access to my code?**
A: Yes, the reviewer reads changed files to provide specific feedback. Code is sent to Anthropic Claude API per their privacy policy: https://www.anthropic.com/legal/privacy

**Q: Can I customize the review criteria?**
A: Yes! Edit `subagent_prompts/reviewer.md` to add project-specific rules, security requirements, or style guidelines.

**Q: Does this replace human code review?**
A: No, AI review complements human review. It catches common issues (security, performance, style) so humans can focus on architecture, business logic, and design decisions.

**Q: What languages are supported?**
A: Phase 1A focuses on Python. The reviewer can analyze any language, but Python files are prioritized in the GitHub Actions workflow.

**Q: Can I review only specific files?**
A: Yes! Modify `.github/workflows/ai-code-review.yml` to add file filters:
```python
if file_path.endswith('.py') and 'src/' in file_path:  # Only review src/*.py
```

**Q: How do I disable AI review for a specific PR?**
A: Add `[skip ci]` to your commit message, or close/reopen the PR to skip the review workflow.

**Q: Can I use a different LLM (GPT-4, Gemini)?**
A: Phase 1A uses Claude Sonnet 4. Support for other LLMs is planned for Phase 2. The LLM executor is in `src/orchestrator/executors/llm_exec.py` (currently hardcoded to `claude-sonnet-4-20250514`).

---

## Next Steps

1. ✅ **Setup Complete:** You're ready to receive AI-powered code reviews on PRs
2. 📊 **Monitor Usage:** Track costs and token usage in Anthropic console
3. 🎯 **Customize:** Tailor reviewer prompt to your project's specific needs
4. 🚀 **Test:** Create a test PR to validate the integration
5. 📖 **Document:** Share this guide with your team

**Phase 1B Roadmap (Coming Soon):**
- Inline comments on specific code lines
- Multi-file diff analysis
- Historical review metrics
- Cost optimization dashboard
- Support for multiple LLMs

---

## Support

**Issues:** https://github.com/YOUR-ORG/claude-code-orchestrator/issues
**Documentation:** https://github.com/YOUR-ORG/claude-code-orchestrator/tree/main/docs
**Anthropic API Docs:** https://docs.anthropic.com/claude/reference/getting-started-with-the-api

---

**Last Updated:** 2025-11-07
**Version:** Phase 1A
**Author:** Claude Code Orchestrator Team
