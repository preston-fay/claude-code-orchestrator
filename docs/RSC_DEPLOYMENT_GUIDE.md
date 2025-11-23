# RSC Deployment Guide

This is the canonical deployment guide for the Ready-Set-Code (RSC) platform.

## Overview

RSC is deployed as two components:

- **Backend API**: FastAPI application deployed via AWS App Runner
- **Frontend UI**: React (Vite) application deployed via AWS Amplify Hosting

```
┌─────────────────┐     ┌─────────────────┐
│   GitHub Repo   │     │   GitHub Repo   │
│   (main branch) │     │   (main branch) │
└────────┬────────┘     └────────┬────────┘
         │                       │
    ┌────▼────┐             ┌────▼────┐
    │ Actions │             │ Amplify │
    │ CI/CD   │             │ Console │
    └────┬────┘             └────┬────┘
         │                       │
    ┌────▼────┐             ┌────▼────┐
    │   ECR   │             │ Amplify │
    │ (Image) │             │ Hosting │
    └────┬────┘             └────┬────┘
         │                       │
    ┌────▼────┐             ┌────▼────┐
    │   App   │             │CloudFront│
    │ Runner  │             │  (CDN)   │
    └─────────┘             └─────────┘
```

---

## Backend Deployment (App Runner)

### Prerequisites

1. AWS Account with permissions for:
   - ECR (Elastic Container Registry)
   - App Runner
   - IAM (for service roles)

2. GitHub repository secrets configured

### GitHub Actions Workflow

**File:** `.github/workflows/backend-deploy.yml`

**Triggers:**
- Push to `main` branch (changes in `orchestrator_v2/`, `Dockerfile`, etc.)
- Manual workflow dispatch

**Jobs:**
1. **build_and_push**: Builds Docker image and pushes to ECR
2. **deploy_to_app_runner**: Updates App Runner service with new image

### Required GitHub Secrets

| Secret | Description | Example |
|--------|-------------|---------|
| `AWS_ACCESS_KEY_ID` | IAM access key | `AKIA...` |
| `AWS_SECRET_ACCESS_KEY` | IAM secret key | `wJalr...` |
| `AWS_ACCOUNT_ID` | AWS account number (optional) | `123456789012` |
| `APP_RUNNER_SERVICE_ARN` | ARN of App Runner service | `arn:aws:apprunner:...` |

### Creating the App Runner Service

1. **Open AWS Console** → App Runner

2. **Create Service**:
   - Source: Container registry (ECR)
   - Image URI: `<account-id>.dkr.ecr.us-east-1.amazonaws.com/rsc-backend:latest`
   - Deployment: Automatic (on image push)

3. **Configure Service**:
   - Service name: `rsc-backend`
   - CPU: 1 vCPU
   - Memory: 2 GB
   - Port: 8000

4. **Environment Variables** (set in App Runner console):

   | Variable | Value | Description |
   |----------|-------|-------------|
   | `WORKSPACE_BASE` | `/mnt/workspaces` | Base path for project workspaces |
   | `ORCHESTRATOR_ENV` | `production` | Environment identifier |
   | `LOG_LEVEL` | `info` | Logging level |
   | `AWS_REGION` | `us-east-1` | AWS region |

   **Optional (for specific features):**
   | Variable | Description |
   |----------|-------------|
   | `ANTHROPIC_API_KEY` | Default API key for LLM (if BYOK disabled) |
   | `GITHUB_PAT` | For auto-repo creation feature |

5. **Health Check**:
   - Path: `/health`
   - Protocol: HTTP
   - Interval: 10 seconds
   - Timeout: 5 seconds

6. **Copy Service ARN** → Add to GitHub Secrets as `APP_RUNNER_SERVICE_ARN`

### ECR Repository Setup

1. **Create ECR Repository** (if not exists):
   ```bash
   aws ecr create-repository --repository-name rsc-backend --region us-east-1
   ```

2. **Configure lifecycle policy** (optional, to clean old images):
   ```json
   {
     "rules": [{
       "rulePriority": 1,
       "description": "Keep last 10 images",
       "selection": {
         "tagStatus": "any",
         "countType": "imageCountMoreThan",
         "countNumber": 10
       },
       "action": {"type": "expire"}
     }]
   }
   ```

---

## Frontend Deployment (Amplify Hosting)

### Prerequisites

1. AWS Account with Amplify access
2. GitHub repository access (OAuth or GitHub App)

### Setting Up Amplify

1. **Open AWS Console** → Amplify

2. **Create New App**:
   - Select: Host web app
   - Source: GitHub
   - Repository: `preston-fay/claude-code-orchestrator`
   - Branch: `main`

3. **Configure Build Settings**:
   - Framework: Auto-detected (Vite)
   - Monorepo: Yes
   - Root directory: `rsg-ui`

   The build spec is already configured in `rsg-ui/amplify.yml`:
   ```yaml
   version: 1
   frontend:
     phases:
       preBuild:
         commands:
           - npm ci
       build:
         commands:
           - npm run build
     artifacts:
       baseDirectory: dist
       files:
         - '**/*'
   ```

4. **Environment Variables** (set in Amplify Console → App Settings → Environment Variables):

   | Variable | Value | Description |
   |----------|-------|-------------|
   | `VITE_ORCHESTRATOR_API_URL` | `https://<app-runner-url>` | Backend API URL |
   | `VITE_RSC_ENV` | `production` | Environment identifier |

   **Optional:**
   | Variable | Description |
   |----------|-------------|
   | `VITE_DEFAULT_USER_ID` | Default user for authentication |
   | `VITE_DEFAULT_USER_EMAIL` | Default email for display |

5. **Deploy**: Click "Save and deploy"

### Custom Domain (Optional)

1. In Amplify Console → Domain management
2. Add domain
3. Configure DNS as instructed
4. SSL certificate is auto-provisioned

---

## Environment Matrix

| Environment | Backend URL | Frontend URL | Branch |
|-------------|-------------|--------------|--------|
| Production | `https://<id>.us-east-1.awsapprunner.com` | `https://main.<app-id>.amplifyapp.com` | `main` |
| Staging | (create separate service) | (create separate Amplify branch) | `develop` |
| Local | `http://localhost:8000` | `http://localhost:5173` | any |

---

## Monitoring & Logging

### Health Check

**Endpoint:** `GET /health`

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2024-01-15T10:30:00Z",
  "version": "2.0.0"
}
```

**Quick check:**
```bash
curl https://<app-runner-url>/health
```

### CloudWatch Logs

**Backend logs location:**
- Log group: `/aws/apprunner/rsc-backend/<service-id>/application`
- Stream: `<instance-id>`

**To view logs:**
1. AWS Console → CloudWatch → Log groups
2. Search for `apprunner/rsc-backend`
3. Select the most recent log stream

**Common log patterns:**
- `INFO` - Normal operations
- `WARNING` - Non-critical issues
- `ERROR` - Errors with stack traces

### Amplify Build Logs

1. Amplify Console → App → Hosting environments
2. Click on deployment
3. View build logs for failures

---

## Production Ops Checklist

### Verify API is Running

```bash
# Health check
curl https://<app-runner-url>/health

# Expected: {"status": "healthy", ...}
```

### Verify Frontend is Running

1. Navigate to `https://<amplify-url>`
2. Should see RSC Launchpad page
3. Click "Start New Project" to verify API connectivity

### Common Issues

#### API Returns 500 Errors

**Check:**
1. CloudWatch logs for stack traces
2. Environment variables in App Runner
3. Workspace paths and permissions

**Resolution:**
- Review error logs
- Verify all env vars are set
- Check IAM roles have necessary permissions

#### Frontend Can't Connect to API

**Symptoms:**
- "Failed to load projects" error
- Network errors in browser console

**Check:**
1. `VITE_ORCHESTRATOR_API_URL` is set correctly in Amplify
2. App Runner service is running
3. CORS is configured (already in FastAPI app)

**Resolution:**
- Verify URL format: `https://...awsapprunner.com` (no trailing slash)
- Redeploy Amplify after changing env vars

#### CI/CD Build Fails

**Check:**
1. GitHub Actions tab for error details
2. Docker build logs
3. Test failures

**Resolution:**
- Fix failing tests
- Update dependencies if needed
- Check Dockerfile for issues

#### App Runner Deploy Fails

**Check:**
1. Image URI is correct
2. App Runner service ARN is valid
3. IAM permissions for ECR access

**Resolution:**
- Verify ECR image exists: `aws ecr describe-images --repository-name rsc-backend`
- Check App Runner service exists
- Update IAM roles if needed

---

## Deployment Workflow

### Standard Deployment (Automatic)

1. Push changes to `main` branch
2. GitHub Actions builds and pushes image to ECR
3. App Runner automatically deploys new image
4. Amplify automatically rebuilds and deploys frontend

### Manual Deployment

**Backend:**
```bash
# Trigger workflow manually
gh workflow run backend-deploy.yml
```

**Frontend:**
1. Amplify Console → App → Click "Redeploy this version"

### Rollback

**Backend:**
1. Find previous image tag in ECR
2. Update App Runner to use that image:
   ```bash
   aws apprunner update-service \
     --service-arn <arn> \
     --source-configuration '{
       "ImageRepository": {
         "ImageIdentifier": "<account>.dkr.ecr.us-east-1.amazonaws.com/rsc-backend:<prev-tag>",
         "ImageRepositoryType": "ECR"
       }
     }'
   ```

**Frontend:**
1. Amplify Console → App → Select previous deployment
2. Click "Redeploy this version"

---

## Security Considerations

### Secrets Management

- **Never** commit secrets to the repository
- Use GitHub Secrets for CI/CD credentials
- Use App Runner environment variables for runtime secrets
- Rotate keys periodically

### IAM Best Practices

- Use least-privilege IAM roles
- Create separate roles for:
  - GitHub Actions (ECR push only)
  - App Runner service (minimum needed)

### Network Security

- App Runner provides automatic TLS/HTTPS
- Amplify provides automatic TLS/HTTPS
- Consider VPC connector for App Runner if accessing private resources

---

## Cost Optimization

### App Runner

- Scales to zero when idle (pay per request)
- Consider reserved instances for production
- Set appropriate min/max instances

### ECR

- Enable lifecycle policies to remove old images
- Use image scanning for security

### Amplify

- Hosting is pay-per-request
- Build minutes are charged separately

---

## Quick Reference

### URLs

- **Backend Health:** `https://<app-runner-url>/health`
- **Frontend:** `https://main.<app-id>.amplifyapp.com`
- **API Docs:** `https://<app-runner-url>/docs`

### Commands

```bash
# Check backend health
curl -s https://<url>/health | jq

# View App Runner logs
aws logs tail /aws/apprunner/rsc-backend/<service-id>/application --follow

# List ECR images
aws ecr list-images --repository-name rsc-backend

# Trigger manual deploy
gh workflow run backend-deploy.yml -r main
```

### Support

For issues:
- Check this guide's troubleshooting section
- Review CloudWatch logs
- Open an issue on GitHub
