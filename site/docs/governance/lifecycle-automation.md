# Lifecycle Automation

The Lifecycle Automation layer provides continuous platform health monitoring through automated dependency auditing, security scanning, and weekly health reporting. This system keeps the platform self-maintaining with minimal manual intervention.

## Overview

Lifecycle Automation consists of four main components:

1. **Dependency Auditing** - Automatic detection and upgrading of outdated packages
2. **Security Scanning** - Continuous vulnerability monitoring across Python and Node ecosystems
3. **Weekly Hygiene Reports** - Comprehensive health summaries merging ops, governance, and security data
4. **Platform Health Webhook** - Real-time status updates to leadership dashboards

All automation runs on a weekly schedule via GitHub Actions and can be triggered manually when needed.

## Components

### 1. Dependency Auditing

**Script**: `scripts/lifecycle/dependency_audit.py`

Audits both Python and Node dependencies, identifies vulnerabilities, and automatically upgrades safe packages (patch/minor versions only).

**Features**:
- Scans for known CVEs using pip-audit and npm audit
- Identifies safe upgrade candidates (patch/minor versions)
- Auto-upgrades dependencies when no high/critical vulnerabilities exist
- Creates automated PRs for dependency upgrades
- Logs all changes to audit trail

**Configuration** (`configs/lifecycle.yaml`):
```yaml
python:
  audit_tool: pip-audit
  auto_upgrade: true
  upgrade_types:
    - patch
    - minor

node:
  audit_tool: npm
  auto_upgrade: true
  upgrade_types:
    - patch
    - minor

audit:
  severity_threshold: high
  branch_prefix: auto/dep-upgrade-
  create_pr: true
```

**Usage**:
```bash
# Run dependency audit
python scripts/lifecycle/dependency_audit.py

# Output: reports/lifecycle/dependencies/YYYY-MM-DD.json
```

**Sample Output**:
```
======================================================================
DEPENDENCY AUDIT SUMMARY
======================================================================

Python:
  Vulnerabilities: 0
  Safe upgrades available: 3

Node:
  Vulnerabilities: 1
  Safe upgrades available: 5

Action Plan:
  Manual review required: 1
  Auto-upgrades planned: 8
  Safe to auto-upgrade: NO

  Manual Review Required:
    - [HIGH] node/express
      Reason: High/critical severity requires manual review

======================================================================
```

**Auto-Upgrade Process**:
1. Script identifies safe upgrades (patch/minor only)
2. Applies upgrades using pip/npm
3. Creates git branch (e.g., `auto/dep-upgrade-20251015`)
4. Commits changes with detailed message
5. Opens PR with upgrade summary
6. CI runs tests on PR

### 2. Security Scanning

**Module**: `src/lifecycle/security_scan.py`

Aggregates security scan results from multiple tools and computes a platform security score (0-100).

**Tools Used**:
- **Bandit** - Python static analysis security scanner
- **pip-audit** - Python dependency CVE scanner
- **npm audit** - Node dependency CVE scanner
- **Trivy** - Optional filesystem/container scanner

**Security Score Computation**:

Starting at 100, points are deducted for findings:

| Severity | Deduction per Issue |
|----------|---------------------|
| Critical | -20 points |
| High | -10 points |
| Medium | -5 points |
| Low | -2 points |

Code quality issues (Bandit):
- High severity: -5 points
- Medium severity: -2 points
- Low severity: -1 point

**Usage**:
```bash
# Run security scan
python src/lifecycle/security_scan.py

# Output: reports/lifecycle/security/YYYY-MM-DD.json
```

**Sample Output**:
```
======================================================================
PLATFORM SECURITY SCAN SUMMARY
======================================================================

Platform Security Score: 87.5/100
Status: GOOD

Bandit (Python Static Analysis): CLEAN

pip-audit (Python CVEs):
  Critical: 0
  High: 0
  Medium: 2
  Low: 1

npm audit (Node CVEs):
  apps/web:
    Critical: 0
    High: 1
    Moderate: 3
    Low: 5

======================================================================
```

**Thresholds**:
- **Excellent**: >= 95
- **Good**: >= 85
- **Fair**: >= 70
- **Poor**: < 70

### 3. Weekly Hygiene Report

**Script**: `scripts/lifecycle/weekly_hygiene_report.py`

Generates comprehensive HTML/PDF reports combining data from multiple sources:

**Data Sources**:
1. **Governance Snapshots** - Data quality, model performance, compliance scores
2. **Security Scans** - Vulnerability findings and security score
3. **Dependency Audits** - Package health and upgrade status
4. **Ops Metrics** - API latency, error rates, uptime
5. **Steward Hygiene** - Code cleanliness, test coverage, lint status

**Report Sections**:

1. **Executive Summary** - KPI cards with week-over-week deltas
2. **Security & Dependency Findings** - Tables of vulnerabilities and audit results
3. **Operational Metrics** - API performance, error rates, cache hit rates
4. **Governance & Cleanliness** - Data quality, test coverage, lint status
5. **Recommendations** - Actionable items based on findings

**Usage**:
```bash
# Generate weekly report
python scripts/lifecycle/weekly_hygiene_report.py

# Output: reports/lifecycle/weekly/YYYY-WWW/
#   - report.html
#   - report.json
#   - report.pdf (if Puppeteer configured)
```

**Brand Compliance**:
- Inter font with Arial fallback
- No emojis (text symbols ▲▼─ only)
- No gridlines in tables/charts
- Label-first data presentation
- Kearney purple (#7823DC) spot color

**Sample HTML Report Structure**:
```html
<!DOCTYPE html>
<html>
<head>
  <style>
    body { font-family: Inter, Arial, sans-serif; }
    /* No gridlines per brand requirements */
  </style>
</head>
<body>
  <h1>Weekly Platform Hygiene Report</h1>

  <section>
    <h2>Executive Summary</h2>
    <!-- KPI cards with scores and deltas -->
  </section>

  <section>
    <h2>Security & Dependency Findings</h2>
    <!-- Tables without gridlines -->
  </section>

  <!-- Additional sections... -->
</body>
</html>
```

### 4. Platform Health Webhook

**Module**: `src/lifecycle/health_webhook.py`

Posts compact health summaries to external webhooks for leadership dashboards.

**Supported Formats**:
- **Slack** - Rich blocks with color-coded status
- **Microsoft Teams** - Adaptive Cards
- **Generic JSON** - Universal format

**Generic JSON Payload**:
```json
{
  "timestamp": "2025-10-20T09:00:00Z",
  "scores": {
    "security": 96,
    "ops": 92,
    "governance": 94,
    "reliability": 97
  },
  "release": "v1.3.2",
  "status": "healthy"
}
```

**Configuration**:
```yaml
webhook:
  enabled: true
  url_secret: LIFECYCLE_WEBHOOK_URL
  format: slack  # slack, teams, or generic
  retry_count: 3
  retry_backoff: 2
  timeout: 10
```

**Setup**:
1. Set webhook URL as environment variable or in `configs/secrets.yaml`:
   ```bash
   export LIFECYCLE_WEBHOOK_URL="https://hooks.slack.com/services/YOUR/WEBHOOK/URL"
   ```

2. Run webhook poster:
   ```bash
   python src/lifecycle/health_webhook.py
   ```

**Retry Logic**:
- Automatic retry on failure with exponential backoff
- Configurable retry count and backoff multiplier
- All attempts logged to audit trail

## CI/CD Integration

### Lifecycle CI Workflow

**File**: `.github/workflows/lifecycle-ci.yml`

**Schedule**:
- **Weekly**: Every Monday at 06:00 UTC
- **Manual**: Via workflow_dispatch

**Jobs**:

1. **dependency-audit**
   - Runs dependency audit
   - Creates auto-upgrade PR if safe
   - Uploads audit report as artifact

2. **security-scan**
   - Runs all security tools
   - Computes platform security score
   - Fails if score < 70
   - Uploads scan reports as artifacts

3. **weekly-report**
   - Generates HTML/JSON reports
   - Creates GitHub issue with summary
   - Uploads report as artifact

4. **health-webhook**
   - Posts health summary to configured webhook
   - Logs success/failure to audit trail

5. **summary**
   - Aggregates job results
   - Posts workflow summary

**Manual Trigger**:
```bash
# Trigger specific task
gh workflow run lifecycle-ci.yml -f task=security-scan

# Run all lifecycle automation
gh workflow run lifecycle-ci.yml -f task=all
```

**Artifacts**:
- `dependency-audit-report` - Retained 90 days
- `security-scan-report` - Retained 90 days
- `weekly-hygiene-report` - Retained 365 days

## Monitoring

### Daily Checks

Quick health check using latest reports:

```bash
# Check latest security score
jq '.platform_security_score' reports/lifecycle/security/$(ls -t reports/lifecycle/security | head -1)

# Check latest dependency audit
jq '.action_plan.manual_review | length' reports/lifecycle/dependencies/$(ls -t reports/lifecycle/dependencies | head -1)
```

### Weekly Review

1. **Monday Morning** (automated):
   - Weekly report generated and emailed/posted
   - Review GitHub issue created by workflow

2. **Review Checklist**:
   - [ ] Security score >= 85
   - [ ] No critical/high vulnerabilities requiring manual review
   - [ ] All operational metrics within thresholds
   - [ ] Test coverage >= 70%
   - [ ] Auto-upgrade PRs merged (if any)

### Alerts

Lifecycle automation logs to `governance/audit/lifecycle.ndjson`:

```json
{"timestamp": "2025-10-15T06:00:00Z", "event": "dependency_audit", "vulnerabilities_found": 3}
{"timestamp": "2025-10-15T06:15:00Z", "event": "security_scan", "platform_security_score": 87.5}
{"timestamp": "2025-10-15T06:30:00Z", "event": "lifecycle_weekly_report_generated", "week": "2025-W42"}
{"timestamp": "2025-10-15T06:45:00Z", "event": "health_webhook_posted", "success": true}
```

## Configuration Reference

### lifecycle.yaml

Complete configuration file with all available options:

```yaml
python:
  audit_tool: pip-audit
  auto_upgrade: true
  upgrade_types: [patch, minor]
  exclude_packages: []

node:
  audit_tool: npm
  auto_upgrade: true
  upgrade_types: [patch, minor]
  exclude_packages: []

security:
  tools: [bandit, pip-audit, npm-audit]
  severity_threshold: high
  fail_on_critical: true

audit:
  severity_threshold: high
  branch_prefix: auto/dep-upgrade-
  create_pr: true
  pr_labels: [dependencies, automated]

reports:
  weekly:
    enabled: true
    schedule: "0 7 * * 1"
    output_formats: [html, pdf, json]
    sections:
      - executive_summary
      - security_findings
      - dependency_audit
      - ops_metrics
      - governance_scores
      - recommendations

webhook:
  enabled: true
  url_secret: LIFECYCLE_WEBHOOK_URL
  format: slack
  retry_count: 3
  retry_backoff: 2
  timeout: 10

scoring:
  weights:
    security: 0.30
    ops: 0.25
    governance: 0.25
    reliability: 0.20
```

## Best Practices

### 1. Dependency Management

- Review auto-upgrade PRs promptly (usually safe)
- Never skip manual review for high/critical vulnerabilities
- Keep exclude lists minimal
- Monitor audit logs for recurring issues

### 2. Security Scanning

- Maintain security score >= 85
- Address critical vulnerabilities within 24 hours
- Review Bandit findings regularly (many are false positives)
- Use Trivy for container/Docker security

### 3. Weekly Reports

- Review reports every Monday morning
- Share executive summary with leadership
- Track trends over time (week-over-week deltas)
- Act on recommendations promptly

### 4. Webhooks

- Test webhook integration thoroughly
- Use secret management for webhook URLs
- Monitor webhook audit logs for failures
- Set up alerts for critical status changes

## Troubleshooting

### Dependency Audit Fails

**Issue**: pip-audit or npm audit not installed

**Solution**:
```bash
pip install pip-audit
npm install -g npm
```

### Security Scan Times Out

**Issue**: Large codebase causes timeout

**Solution**: Increase timeout in config:
```yaml
security:
  timeout: 300  # 5 minutes
```

### Weekly Report Missing Data

**Issue**: No recent governance snapshots

**Solution**: Run governance profiling first:
```bash
orchestrator gov profile --all
orchestrator gov snapshot
```

### Webhook Posting Fails

**Issue**: Webhook URL not configured or invalid

**Solution**:
1. Check environment variable: `echo $LIFECYCLE_WEBHOOK_URL`
2. Test webhook manually:
   ```bash
   curl -X POST "$LIFECYCLE_WEBHOOK_URL" \
     -H "Content-Type: application/json" \
     -d '{"text": "Test message"}'
   ```

### Auto-Upgrade PR Not Created

**Issue**: No safe upgrades available or git push failed

**Solution**: Check audit report:
```bash
jq '.action_plan' reports/lifecycle/dependencies/$(ls -t reports/lifecycle/dependencies | head -1)
```

## API Integration

Lifecycle automation can be integrated with other systems via API:

### Get Latest Security Score

```python
import json
from pathlib import Path

def get_latest_security_score():
    security_dir = Path("reports/lifecycle/security")
    latest_report = sorted(security_dir.glob("*.json"))[-1]

    with open(latest_report) as f:
        data = json.load(f)

    return data["platform_security_score"]

score = get_latest_security_score()
print(f"Current security score: {score}/100")
```

### Subscribe to Audit Events

```python
import json

def watch_audit_log(event_type):
    audit_file = "governance/audit/lifecycle.ndjson"

    with open(audit_file) as f:
        for line in f:
            event = json.loads(line)
            if event["event"] == event_type:
                yield event

# Watch for weekly reports
for event in watch_audit_log("lifecycle_weekly_report_generated"):
    print(f"New report: {event['report_path']}")
```

## Future Enhancements

Planned improvements for lifecycle automation:

1. **Real-time Alerting** - Slack/Teams notifications for critical issues
2. **Trend Analysis** - ML-based anomaly detection on security scores
3. **Cost Tracking** - Integration with AWS Cost Explorer
4. **Automated Rollback** - Auto-revert failed dependency upgrades
5. **Custom Rules Engine** - User-defined health checks and alerts
6. **Performance Profiling** - Automated performance regression detection

## Related Documentation

- [Governance Overview](./overview.md)
- [Scorecards](./scorecards.md)
- [Feature Flags](./feature-flags.md)
- [Quality Gates](./quality-gates.md)

---

**Status**: Production Ready
**Last Updated**: October 15, 2025
**Maintained By**: Platform Engineering Team
