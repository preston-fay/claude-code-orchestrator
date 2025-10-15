# GitHub and AWS Amplify Setup Guide

This guide walks through deploying the Kearney Data Platform to GitHub and AWS Amplify.

## Prerequisites

- GitHub account
- AWS account with Amplify access
- GitHub CLI installed (`gh` command)
- Git configured locally

## Part 1: GitHub Repository Setup

### 1.1 Repository Creation

The repository has been created at:
**https://github.com/preston-fay/claude-code-orchestrator**

To verify:
```bash
gh repo view preston-fay/claude-code-orchestrator
```

### 1.2 Verify Git Configuration

```bash
cd /Users/pfay01/Projects/claude-code-orchestrator
git remote -v
```

Should show:
```
origin  https://github.com/preston-fay/claude-code-orchestrator.git (fetch)
origin  https://github.com/preston-fay/claude-code-orchestrator.git (push)
```

### 1.3 GitHub Actions

The repository includes CI/CD workflows in `.github/workflows/`:

- **ci.yml**: Runs on every push, performs linting, testing, and builds
- **release.yml**: Triggered on version tags (v*)
- **weekly-hygiene.yml**: Scheduled weekly repository hygiene scan

View workflow runs:
```bash
gh run list
```

## Part 2: AWS Amplify Deployment

### 2.1 Create Amplify App

1. **Navigate to AWS Amplify Console**
   - Open https://console.aws.amazon.com/amplify/
   - Click "New app" → "Host web app"

2. **Connect to GitHub**
   - Select "GitHub" as the source
   - Click "Connect branch"
   - Authorize AWS Amplify to access your GitHub account
   - Select repository: `preston-fay/claude-code-orchestrator`
   - Select branch: `main`

3. **Configure Build Settings**
   - Amplify will auto-detect `amplify.yml` in the repository
   - Verify the configuration looks correct:

```yaml
version: 1
backend:
  phases:
    build:
      commands:
        - pip3 install -r requirements-dataplatform.txt
        - python3 -c "from src.data.warehouse import DuckDBWarehouse"
frontend:
  phases:
    preBuild:
      commands:
        - cd apps/web
        - npm ci
    build:
      commands:
        - npm run build
  artifacts:
    baseDirectory: apps/web/dist
    files:
      - '**/*'
  cache:
    paths:
      - apps/web/node_modules/**/*
```

4. **Review and Deploy**
   - Click "Next" through the remaining screens
   - Click "Save and deploy"

### 2.2 Configure Environment Variables

In the Amplify Console, navigate to your app → "Environment variables":

#### Required Variables

| Variable | Description | Example Value |
|----------|-------------|---------------|
| `AMPLIFY_BRANCH` | Deployment branch | `main` |
| `NODE_VERSION` | Node.js version | `18` |
| `PYTHON_VERSION` | Python version | `3.11` |

#### Optional API Keys (for isochrone providers)

| Variable | Description | Where to Get |
|----------|-------------|--------------|
| `ORS_API_KEY` | OpenRouteService API key | https://openrouteservice.org/dev/#/signup |
| `MAPBOX_TOKEN` | Mapbox access token | https://account.mapbox.com/ |
| `ISO_MAX_RANGE_MIN` | Max isochrone range (minutes) | `60` (default) |

#### Database Configuration

| Variable | Description | Default |
|----------|-------------|---------|
| `WAREHOUSE_PATH` | DuckDB database path | `/tmp/warehouse.duckdb` |
| `WAREHOUSE_READ_ONLY` | Read-only mode | `false` |

### 2.3 Configure Build Image

Amplify needs a build image with both Node.js and Python:

1. In Amplify Console → App settings → Build settings
2. Scroll to "Build image settings"
3. Select "Amazon Linux 2023" (includes Node 18 and Python 3.11)

### 2.4 Verify Deployment

After the first deployment:

1. **Check Build Log**
   - Verify both backend (Python) and frontend (Node) builds succeeded
   - Look for "BUILD SUCCESSFUL" message

2. **Test Endpoints**
   - Frontend: `https://main.XXXXX.amplifyapp.com/`
   - API: `https://main.XXXXX.amplifyapp.com/api/metrics`
   - Admin: `https://main.XXXXX.amplifyapp.com/admin`

3. **Verify Functionality**
   ```bash
   curl https://main.XXXXX.amplifyapp.com/api/metrics
   ```

## Part 3: Branch Protection (Optional)

Protect the `main` branch to enforce CI checks:

### 3.1 Enable Branch Protection

```bash
# Via GitHub CLI
gh api repos/preston-fay/claude-code-orchestrator/branches/main/protection \
  --method PUT \
  --field required_status_checks='{"strict":true,"contexts":["test (ubuntu-latest, 3.11)","lint","build-frontend"]}' \
  --field enforce_admins=true \
  --field required_pull_request_reviews='{"required_approving_review_count":1}' \
  --field restrictions=null
```

Or via GitHub web UI:
1. Repository → Settings → Branches
2. Add rule for `main` branch
3. Enable:
   - ✅ Require status checks before merging
   - ✅ Require branches to be up to date
   - ✅ Require CI to pass
   - ✅ Require pull request reviews (1 approval)

### 3.2 Verify Protection

```bash
gh api repos/preston-fay/claude-code-orchestrator/branches/main/protection
```

## Part 4: Continuous Deployment

### 4.1 Auto-Deployment

Amplify automatically deploys on every push to `main`:

1. Make changes locally
2. Commit and push:
   ```bash
   git add .
   git commit -m "feat: add new feature"
   git push origin main
   ```
3. Watch deployment in Amplify Console

### 4.2 Manual Deployment

To manually trigger a deployment:

```bash
aws amplify start-job --app-id <APP_ID> --branch-name main --job-type RELEASE
```

Or in the Amplify Console → "Redeploy this version"

### 4.3 Preview Deployments

For pull requests, Amplify can create preview environments:

1. In Amplify Console → App settings → Previews
2. Enable "Enable pull request previews from forks"
3. Each PR will get a unique URL: `https://pr-XXX.XXXXX.amplifyapp.com/`

## Part 5: Monitoring and Logs

### 5.1 View Logs

**Build Logs:**
- Amplify Console → App → Build History → Click build → View logs

**Runtime Logs:**
- CloudWatch Logs → Log groups → `/aws/amplify/<app-id>`

### 5.2 Metrics

View deployment metrics in Amplify Console:
- Build frequency
- Build duration
- Success/failure rate

### 5.3 Alarms (Optional)

Create CloudWatch alarms for:
- Build failures
- High error rates
- Slow response times

```bash
aws cloudwatch put-metric-alarm \
  --alarm-name amplify-build-failure \
  --alarm-description "Alert on Amplify build failure" \
  --metric-name BuildFailureCount \
  --namespace AWS/Amplify \
  --statistic Sum \
  --period 300 \
  --threshold 1 \
  --comparison-operator GreaterThanThreshold
```

## Part 6: Custom Domain (Optional)

### 6.1 Add Custom Domain

1. In Amplify Console → Domain management → Add domain
2. Enter your domain (e.g., `dataplatform.kearney.com`)
3. Follow DNS verification steps
4. Amplify will provision SSL certificate via ACM
5. Wait for DNS propagation (~24 hours)

### 6.2 Configure Subdomain

For API subdomain:
1. Add `api.dataplatform.kearney.com` → Amplify app
2. Configure rewrites in `amplify.yml`:

```yaml
customHeaders:
  - pattern: '**'
    headers:
      - key: 'Strict-Transport-Security'
        value: 'max-age=31536000; includeSubDomains'
      - key: 'X-Frame-Options'
        value: 'SAMEORIGIN'
redirects:
  - source: '/api/<*>'
    target: 'https://api.dataplatform.kearney.com/<*>'
    status: '302'
```

## Part 7: Troubleshooting

### Common Issues

#### Build Fails: "Module not found"
**Solution:** Check `requirements-dataplatform.txt` includes all dependencies

#### Frontend 404 Errors
**Solution:** Verify `baseDirectory` in `amplify.yml` points to `apps/web/dist`

#### API Returns 500
**Solution:** Check CloudWatch logs for Python errors

#### Slow Builds
**Solution:** Enable caching in `amplify.yml`:
```yaml
cache:
  paths:
    - apps/web/node_modules/**/*
    - '~/.cache/pip/**/*'
```

### Debug Commands

```bash
# View recent builds
gh run list --repo preston-fay/claude-code-orchestrator

# View specific run logs
gh run view RUN_ID --log

# Check Amplify app status
aws amplify get-app --app-id <APP_ID>

# List all deployments
aws amplify list-jobs --app-id <APP_ID> --branch-name main
```

## Part 8: Security Best Practices

### 8.1 Environment Variables

- **Never commit secrets** to the repository
- Store all API keys in Amplify environment variables
- Use AWS Secrets Manager for sensitive data

### 8.2 Access Control

- Enable IAM authentication for Amplify
- Restrict who can trigger deployments
- Use GitHub branch protection

### 8.3 Audit Logging

- Enable CloudTrail for Amplify API calls
- Review access logs regularly
- Set up alerts for suspicious activity

### 8.4 Dependency Scanning

The CI workflow includes:
- `npm audit` for frontend dependencies
- `pip-audit` for Python dependencies (optional)
- Dependabot for automated updates

Enable Dependabot in GitHub:
1. Repository → Settings → Security → Dependabot
2. Enable "Dependabot alerts"
3. Enable "Dependabot security updates"

## Part 9: Release Process

### 9.1 Create Release

Using the orchestrator CLI:

```bash
# Prepare release (dry run)
orchestrator release prepare --dry-run

# Cut release
orchestrator release cut --execute

# This will:
# 1. Bump version in pyproject.toml and package.json
# 2. Generate CHANGELOG.md
# 3. Create git tag (e.g., v1.0.0)
# 4. Push tag to GitHub
# 5. Trigger release workflow
```

### 9.2 GitHub Release

The release workflow will:
1. Build artifacts
2. Run all tests
3. Create GitHub release
4. Upload artifacts
5. Deploy to production (if configured)

### 9.3 Rollback

To rollback a deployment:

```bash
# In Amplify Console
1. Navigate to build history
2. Find last known good build
3. Click "Redeploy this version"

# Or via CLI
aws amplify start-job \
  --app-id <APP_ID> \
  --branch-name main \
  --job-type RELEASE \
  --job-id <GOOD_BUILD_ID>
```

## Part 10: Next Steps

### Recommended Enhancements

1. **Visual Regression Testing**
   - Add Playwright screenshots in CI
   - Compare against baselines

2. **Performance Monitoring**
   - Integrate AWS X-Ray for tracing
   - Set up CloudWatch dashboards

3. **Cost Optimization**
   - Enable Amplify build caching
   - Use CloudFront for static assets

4. **Multi-Environment Setup**
   - Create `dev`, `staging`, `prod` branches
   - Configure environment-specific variables

5. **Client Theme Overrides**
   - Implement `clients/<slug>/theme.json`
   - Add merge script for per-client branding

## Quick Reference

### Important URLs

- **Repository**: https://github.com/preston-fay/claude-code-orchestrator
- **Actions**: https://github.com/preston-fay/claude-code-orchestrator/actions
- **Amplify Console**: https://console.aws.amazon.com/amplify/
- **Production**: https://main.XXXXX.amplifyapp.com/ (replace with your domain)

### Key Commands

```bash
# View GitHub repo
gh repo view

# List CI runs
gh run list

# Watch latest run
gh run watch

# Deploy to Amplify
git push origin main

# Check deployment status
aws amplify list-jobs --app-id <APP_ID> --branch-name main

# View logs
aws logs tail /aws/amplify/<app-id> --follow
```

## Support

For issues or questions:
- Create an issue: https://github.com/preston-fay/claude-code-orchestrator/issues
- Review docs: `docs/` directory
- Check CI logs: https://github.com/preston-fay/claude-code-orchestrator/actions
