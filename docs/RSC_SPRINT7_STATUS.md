# RSC Sprint 7 Status: Production Deployment & Infra Hardening

## Current Infrastructure State

### Backend Deployment (orchestrator_v2)

| Component | Status | Notes |
|-----------|--------|-------|
| Dockerfile | ✅ Valid | Multi-stage build, Python 3.11, uvicorn entrypoint |
| ECR Repository | ✅ Configured | `orchestrator-api` |
| App Runner | 📝 Documented | Service needs to be created in AWS Console |
| CI Workflow | ✅ Exists | `build-and-publish-image.yml` - builds and pushes to ECR |
| Health Check | ✅ Ready | `/health` endpoint returns status + version |

### Frontend Deployment (rsg-ui)

| Component | Status | Notes |
|-----------|--------|-------|
| Build System | ✅ Vite | React + TypeScript |
| API Client | ✅ Configured | Uses `VITE_ORCHESTRATOR_API_URL` with fallback |
| Amplify Config | ⚠️ Missing | Need to create `rsg-ui/amplify.yml` |

### Existing Workflows (.github/workflows/)

| Workflow | Purpose | Still Valid |
|----------|---------|-------------|
| `ci.yml` | Lint, test, coverage | ✅ Yes |
| `build-and-publish-image.yml` | Docker → ECR | ✅ Yes - needs App Runner deploy step |
| `release.yml` | Release automation | ✅ Yes |
| `docs.yml` | Documentation site | ✅ Yes |

### Documentation (docs/)

| Document | Status | Notes |
|----------|--------|-------|
| `DEPLOYMENT_APP_RUNNER.md` | ✅ Valid | Main backend deployment guide |
| `DEPLOYMENT_STEPS.md` | ⚠️ Stale | Old release process |
| `DEPLOYMENT_VALIDATION.md` | ⚠️ Stale | Manual validation |
| `RSC_DEPLOYMENT_GUIDE.md` | 🆕 To Create | Sprint 7 unified deployment guide |

## Sprint 7 Checklist

### Phase 1: Repo Scan & Status
- [x] Review existing infrastructure
- [x] Identify stale vs valid components
- [x] Create this status document

### Phase 2: Backend CI/CD
- [ ] Verify Dockerfile works with current layout
- [ ] Update `build-and-publish-image.yml` to include App Runner deploy
- [ ] Document required GitHub secrets
- [ ] Add graceful failure for missing secrets

### Phase 3: Frontend CI/CD
- [ ] Create `rsg-ui/amplify.yml`
- [ ] Verify `VITE_ORCHESTRATOR_API_URL` handling
- [ ] Document Amplify setup steps

### Phase 4: Secrets & Env Management
- [ ] Document GitHub secrets list
- [ ] Document App Runner env vars
- [ ] Document Amplify env vars

### Phase 5: Monitoring & Logging
- [ ] Verify `/health` endpoint
- [ ] Document CloudWatch log access
- [ ] Create ops checklist

### Phase 6: RSC UI Polishing
- [ ] Verify Launchpad as homepage
- [ ] Update browser title to "RSC — Ready-Set-Code Platform"
- [ ] Remove any debug/demo text

### Phase 7: Documentation
- [ ] Create `RSC_DEPLOYMENT_GUIDE.md`
- [ ] Update README to reference deployment guide
- [ ] Add troubleshooting section

## Environment Variable Summary

### Backend (App Runner)
```
WORKSPACE_BASE=/mnt/workspaces
ORCHESTRATOR_ENV=production
LOG_LEVEL=info
AWS_REGION=us-east-1
```

### Frontend (Amplify)
```
VITE_ORCHESTRATOR_API_URL=https://<app-runner-url>
VITE_RSC_ENV=production
```

### GitHub Actions
```
AWS_ACCESS_KEY_ID
AWS_SECRET_ACCESS_KEY
AWS_REGION
AWS_ACCOUNT_ID
ECR_REPOSITORY
APP_RUNNER_SERVICE_ARN
```

## Production URLs (Expected Shape)

- **Backend API**: `https://<random-id>.<region>.awsapprunner.com`
- **Frontend UI**: `https://<branch>.<app-id>.amplifyapp.com`
- **Health Check**: `https://<api-url>/health`
