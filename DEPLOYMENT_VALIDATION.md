# Post-Deploy Validation Guide

This guide helps you verify that your Claude Code Orchestrator API is running correctly after deployment to AWS App Runner.

---

## A. Confirm App Runner Service is Running

### Get the Service URL

1. Open AWS Console → App Runner
2. Click on your service (e.g., `orchestrator-api`)
3. Find the **Default domain** in the service overview:
   ```
   https://xxxxxxxxxx.us-east-1.awsapprunner.com
   ```

### Confirm Instance Health

In the App Runner console:

1. Check **Status**: Should be `Running`
2. Check **Health**: Should show green checkmark
3. Review **Metrics** tab for:
   - Active instances: 1+
   - Request count increasing after tests
   - No 5xx errors

### CloudWatch Logs

If issues occur, check logs:

1. Go to CloudWatch → Log groups
2. Find `/aws/apprunner/<service-name>/<service-id>/application`
3. Look for startup errors or exceptions

---

## B. Health Endpoint Tests

### Basic Health Check

```bash
curl -i https://<app-runner-url>/health
```

**Expected Response:**
```
HTTP/2 200
content-type: application/json

{"status":"healthy"}
```

### What to Check

| Status Code | Meaning | Action |
|-------------|---------|--------|
| 200 | Healthy | All good |
| 502 | Bad Gateway | Container not started; check logs |
| 503 | Service Unavailable | Health check failing; check /health endpoint |
| 504 | Gateway Timeout | Container taking too long to respond |

---

## C. RSG Test Sequence

Run this minimal test sequence to verify the full API stack:

### 1. Create a Test Project

```bash
curl -X POST https://<url>/projects \
     -H "Content-Type: application/json" \
     -d '{"name":"DeployTest","description":"Deployment validation test"}'
```

**Expected Response:**
```json
{
  "project_id": "uuid-here",
  "name": "DeployTest",
  "description": "Deployment validation test",
  "status": "created",
  "created_at": "2024-01-01T00:00:00Z"
}
```

Save the `project_id` for subsequent tests.

### 2. Start Ready Stage

```bash
curl -X POST https://<url>/rsg/<project_id>/ready/start
```

**Expected Response:**
```json
{
  "project_id": "uuid-here",
  "stage": "ready",
  "status": "in_progress",
  "planning_complete": false,
  "architecture_complete": false,
  "message": "Ready stage started"
}
```

### 3. Get RSG Overview

```bash
curl https://<url>/rsg/<project_id>/overview
```

**Expected Response:**
```json
{
  "project_id": "uuid-here",
  "current_stage": "ready",
  "ready": {
    "status": "in_progress",
    "planning_complete": false,
    "architecture_complete": false
  },
  "set": {
    "status": "not_started",
    "data_complete": false,
    "development_complete": false
  },
  "go": {
    "status": "not_started",
    "qa_complete": false,
    "documentation_complete": false
  }
}
```

### 4. List All Projects

```bash
curl https://<url>/projects
```

**Expected Response:**
```json
{
  "projects": [
    {
      "project_id": "uuid-here",
      "name": "DeployTest",
      "status": "created",
      "created_at": "2024-01-01T00:00:00Z"
    }
  ],
  "total": 1
}
```

---

## D. Workspace Path Expectations

Inside App Runner, workspaces are created at:

```
/mnt/workspaces/<project_id>/
    repo/           # Project repository files
    .orchestrator/  # Orchestrator state and config
    artifacts/      # Phase output artifacts
    logs/           # Execution logs
    tmp/            # Temporary files
```

### Important Notes

- **Ephemeral Storage**: App Runner instances have ephemeral storage
- **State Persistence**: For production, configure external persistence (S3, EFS)
- **Logs**: Always stream to CloudWatch for durability

---

## E. Common Failure Causes

### Container Won't Start

| Symptom | Cause | Fix |
|---------|-------|-----|
| 502 errors | Missing dependencies | Check Dockerfile, rebuild image |
| Import errors in logs | Missing Python package | Add to pyproject.toml |
| Port binding error | Wrong port | Ensure CMD uses port 8000 |

### Health Check Failing

| Symptom | Cause | Fix |
|---------|-------|-----|
| Timeout | Slow startup | Increase health check timeout |
| 404 on /health | Wrong path | Verify endpoint exists |
| Connection refused | App not listening | Check host is 0.0.0.0 |

### API Errors

| Symptom | Cause | Fix |
|---------|-------|-----|
| 500 errors | Unhandled exception | Check CloudWatch logs |
| 422 errors | Invalid request body | Check request JSON format |
| 404 errors | Wrong endpoint | Verify API routes |

---

## F. Automated Verification

Use the verification script for automated testing:

```bash
python scripts/verify_deployment.py --url https://xxxxx.awsapprunner.com
```

This script will:
1. Check health endpoint
2. Create a test project
3. Start Ready stage
4. Fetch RSG overview
5. Report success/failure with details

### Expected Output (Success)

```
Orchestrator Deployment Verification
=====================================
Target: https://xxxxx.awsapprunner.com

[1/4] Health Check................ OK
[2/4] Create Project.............. OK (id: abc-123)
[3/4] Start Ready Stage........... OK
[4/4] Get RSG Overview............ OK

=====================================
VERIFICATION PASSED
All endpoints responding correctly
=====================================
```

### Expected Output (Failure)

```
Orchestrator Deployment Verification
=====================================
Target: https://xxxxx.awsapprunner.com

[1/4] Health Check................ FAILED
      Error: Connection refused

=====================================
VERIFICATION FAILED
Check App Runner logs for details
=====================================
```

---

## G. Cleanup

After validation, optionally delete the test project:

```bash
curl -X DELETE https://<url>/projects/<project_id>
```

---

## H. Next Steps After Validation

Once all checks pass:

1. **Configure monitoring** - Set up CloudWatch alarms
2. **Add custom domain** (optional) - Route53 + ACM certificate
3. **Connect frontend** - Point React app to API URL
4. **Load testing** (optional) - Verify performance under load

---

## Quick Reference

| Check | Command | Expected |
|-------|---------|----------|
| Health | `curl <url>/health` | `{"status":"healthy"}` |
| Projects | `curl <url>/projects` | List of projects |
| RSG | `curl <url>/rsg/<id>/overview` | Stage status |

---

## Related Documentation

- [DEPLOYMENT_APP_RUNNER.md](DEPLOYMENT_APP_RUNNER.md) - Deployment instructions
- [ORCHESTRATOR_QUICK_REFERENCE.md](ORCHESTRATOR_QUICK_REFERENCE.md) - Quick reference
- [AWS App Runner Troubleshooting](https://docs.aws.amazon.com/apprunner/latest/dg/troubleshooting.html)
