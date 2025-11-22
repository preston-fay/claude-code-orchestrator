# Deploying Orchestrator API to AWS App Runner

This guide walks you through deploying the Claude Code Orchestrator API to AWS App Runner, giving you a public HTTPS endpoint with zero infrastructure management.

## Why App Runner?

- No Kubernetes or ECS complexity
- No VPC configuration required
- No load balancer setup
- Automatic HTTPS with AWS-managed certificates
- Auto-scaling built-in
- Continuous deployment from ECR

---

## Prerequisites

Before deploying, ensure you have:

1. **AWS Account** with appropriate permissions
2. **AWS CLI** installed and configured
3. **ECR repository** with images pushed (see `ORCHESTRATOR_QUICK_REFERENCE.md`)
4. **GitHub Actions** configured to push to ECR (already done)

---

## Deployment Steps

### Step 1: Get Your ECR Image URI

Run the helper script to get your ECR URI:

```bash
python scripts/print_ecr_uri.py
```

Example output:
```
123456789012.dkr.ecr.us-east-1.amazonaws.com/orchestrator-api
```

Or use the deployment helper:

```bash
./scripts/deploy_to_apprunner.sh
```

### Step 2: Create App Runner Service

1. **Open AWS Console** → Navigate to **App Runner**
2. Click **Create service**

### Step 3: Configure Source

- **Source type**: Container registry
- **Provider**: Amazon ECR
- **Image repository**: `<your-ecr-uri>` (from Step 1)
- **Image tag**: `latest`

### Step 4: Configure Deployment

- **Deployment trigger**: Automatic
- Check: **"Deploy new image versions automatically"**

This enables continuous deployment whenever you push a new image to ECR.

### Step 5: Configure Service

**Runtime settings:**

| Setting | Value |
|---------|-------|
| Port | `8000` |
| CPU | 1 vCPU |
| Memory | 2 GB |

**Health check:**

| Setting | Value |
|---------|-------|
| Protocol | HTTP |
| Path | `/health` |
| Interval | 10 seconds |
| Timeout | 5 seconds |
| Healthy threshold | 1 |
| Unhealthy threshold | 5 |

### Step 6: Configure Environment Variables

Add the following environment variables:

| Variable | Value | Description |
|----------|-------|-------------|
| `WORKSPACE_BASE` | `/mnt/workspaces` | Base path for workspaces |
| `ORCHESTRATOR_ENV` | `production` | Environment identifier |
| `AWS_REGION` | `us-east-1` | AWS region |
| `LOG_LEVEL` | `info` | Logging verbosity |

### Step 7: Configure IAM Role

App Runner needs permission to pull images from ECR. Create or select a role with the following policy:

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "ecr:GetAuthorizationToken",
                "ecr:BatchCheckLayerAvailability",
                "ecr:GetDownloadUrlForLayer",
                "ecr:BatchGetImage"
            ],
            "Resource": "*"
        }
    ]
}
```

### Step 8: Create Service

1. Review your configuration
2. Click **Create & deploy**
3. Wait for the service to deploy (typically 2-5 minutes)

---

## Post-Deployment

### Get Your Public URL

Once deployed, App Runner provides a URL like:

```
https://xxxxxxxxxx.us-east-1.awsapprunner.com
```

### Verify Deployment

Test the health endpoint:

```bash
curl https://your-app-url.awsapprunner.com/health
```

Expected response:
```json
{"status": "healthy"}
```

### Test API Endpoints

```bash
# List projects
curl https://your-app-url.awsapprunner.com/projects

# Create a project
curl -X POST https://your-app-url.awsapprunner.com/projects \
  -H "Content-Type: application/json" \
  -d '{"name": "My Project", "description": "Test project"}'
```

---

## Continuous Deployment

With auto-deploy enabled, any push to `main` will:

1. Trigger GitHub Actions
2. Build new Docker image
3. Push to ECR with `latest` tag
4. App Runner automatically deploys the new image

No manual intervention required!

---

## Monitoring

### CloudWatch Logs

App Runner automatically sends logs to CloudWatch:

- Log group: `/aws/apprunner/<service-name>/<service-id>/application`

### Metrics

Available in CloudWatch Metrics:

- Request count
- Response latency
- 2xx/4xx/5xx response counts
- Active instances
- CPU/Memory utilization

---

## Troubleshooting

### Service fails to start

1. Check CloudWatch logs for error messages
2. Verify the health check path (`/health`) returns 200
3. Ensure port 8000 is correct

### Image pull fails

1. Verify IAM role has ECR permissions
2. Check ECR repository exists
3. Confirm image tag exists in ECR

### Health checks failing

1. Verify `/health` endpoint returns 200
2. Check timeout settings (increase if needed)
3. Review application startup logs

---

## Cost Considerations

App Runner pricing (as of 2024):

- **Compute**: $0.064 per vCPU-hour
- **Memory**: $0.007 per GB-hour
- **Provisioned instances**: Minimum charge applies

For a 1 vCPU / 2 GB configuration running 24/7:
- ~$50-70/month (varies by usage)

Auto-pause can reduce costs for development/staging environments.

---

## Security Best Practices

1. **Never commit secrets** - Use environment variables
2. **Enable ECR image scanning** - Already configured
3. **Use least-privilege IAM** - Minimal ECR pull permissions
4. **Enable CloudWatch alarms** - Monitor for anomalies
5. **Regular updates** - Keep base images current

---

## Next Steps

After deployment:

1. **Configure custom domain** (optional) - Route53 + App Runner
2. **Set up CloudWatch alarms** - Latency, errors, availability
3. **Connect frontend** - Point React/Amplify app to API URL
4. **Enable WAF** (optional) - Web Application Firewall protection

---

## Quick Reference

| Resource | Value |
|----------|-------|
| Entry point | `orchestrator_v2.main:app` |
| Port | `8000` |
| Health check | `/health` |
| Base image | `python:3.11-slim` |
| ECR repo | `orchestrator-api` |
| Region | `us-east-1` |

---

## Related Documentation

- [ORCHESTRATOR_QUICK_REFERENCE.md](ORCHESTRATOR_QUICK_REFERENCE.md) - Docker and ECR setup
- [docs/ORCHESTRATOR_OVERVIEW.md](docs/ORCHESTRATOR_OVERVIEW.md) - Architecture overview
- [AWS App Runner Documentation](https://docs.aws.amazon.com/apprunner/)
