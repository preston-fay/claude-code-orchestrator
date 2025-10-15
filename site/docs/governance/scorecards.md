---
sidebar_position: 2
title: Scorecards & KPIs
---

# Governance Scorecards & KPIs

The governance system tracks four key performance indices that measure platform health across data quality, model performance, reliability, and security.

## Scorecard Overview

The governance scorecard provides real-time visibility into platform health through four standardized indices, each scored from 0-100:

### 1. Data Quality Index

**What it measures:**
- Null percentage across datasets
- Duplicate record rates
- Data freshness (time since last modification)
- Steward cleanliness score integration

**Computation:**
```
Data Quality Index = (Null Score × 0.3) + (Duplicate Score × 0.3) + (Cleanliness Score × 0.4)

Where:
- Null Score = 100 - Average Null Percentage
- Duplicate Score = 100 - Duplicate Percentage
- Cleanliness Score = Steward 4S Total (if available)
```

**Thresholds:**
- 90-100: Excellent
- 75-89: Good
- 60-74: Fair
- < 60: Needs Attention

### 2. Model Performance Index

**What it measures:**
- R2 scores from model metrics
- RMSE against targets
- Model freshness (registry updates)
- Accuracy metrics when available

**Computation:**
```
Model Performance Index = Average of:
- R2 Score × 100
- (1 - min(RMSE / 0.20, 1)) × 100
- Accuracy × 100 (if available)
```

**Thresholds:**
- R2 >= 0.80 (target)
- RMSE <= 0.20 (target)
- MAE <= 0.15 (target)
- Accuracy >= 0.85 (target)

### 3. Platform Reliability Index

**What it measures:**
- API latency (p95)
- Error rates
- Cache hit rates
- System uptime

**Computation:**
```
Platform Reliability Index = 100 - Penalties

Penalties:
- Latency > 400ms: -1 point per 10ms over threshold
- Error rate > 1%: -10 points per 1% over threshold
- Cache hit < 80%: -0.5 points per 1% under threshold
```

**Thresholds:**
- Latency p95 < 400ms
- Error rate < 1%
- Cache hit rate > 80%

### 4. Security Compliance Index

**What it measures:**
- Authentication/authorization checks (Phase 11)
- Audit log anomalies
- Feature flag change frequency
- Security event rates

**Computation:**
```
Security Compliance Index = Base Score - Adjustment

Base Score: 95
Adjustment: Based on recent security events and flag changes
```

**Thresholds:**
- >20 flag changes/week: -0.5 points per extra change
- Security events: -5 points per critical event
- Audit anomalies: -2 points per anomaly

## Accessing Scorecards

### Via API

```bash
curl http://localhost:8000/api/gov/scorecard
```

Response:
```json
{
  "data_quality_index": 87.5,
  "model_performance_index": 82.3,
  "platform_reliability_index": 91.2,
  "security_compliance_index": 95.0,
  "timestamp": "2024-10-15T12:00:00Z"
}
```

### Via Dashboard

Navigate to `/governance` in the web application to view the interactive dashboard with:
- Real-time scorecard tiles
- 7-day trend charts
- Recent findings list

### Via CLI

```bash
orchestrator gov snapshot
```

## Trend Analysis

The governance system maintains historical snapshots for trend analysis:

```bash
# View 7-day trends
curl http://localhost:8000/api/gov/trends?days=7

# View 30-day trends
curl http://localhost:8000/api/gov/trends?days=30

# View 90-day trends
curl http://localhost:8000/api/gov/trends?days=90
```

## Quality Gates

Scorecard indices are used in CI/CD quality gates:

| Gate | Metric | Threshold | Severity |
|------|--------|-----------|----------|
| Data Freshness | Days since update | < 7 days | Error |
| Model Performance | R2 score | >= 0.80 | Warning |
| Cleanliness | 4S total | >= 85 | Error |
| Latency | p95 | < 400ms | Warning |

See [Quality Gates](/governance/quality-gates) for details on CI integration.

## Alerts and Notifications

The governance system generates alerts when indices fall below thresholds:

**Drift Alerts:** Triggered when datasets show significant distribution changes
**Performance Alerts:** Triggered when models fail performance targets
**Reliability Alerts:** Triggered when platform metrics degrade
**Security Alerts:** Triggered on unusual security events

Alerts appear in:
- Weekly governance reports
- Dashboard "Recent Findings" section
- CI/CD PR comments
- Optional Slack/Teams webhooks (if configured)

## Customizing Thresholds

Edit `configs/governance.yaml` to adjust thresholds:

```yaml
# Data freshness requirements
freshness_days_min: 7

# Cleanliness requirements
cleanliness_min: 85

# Performance targets
perf_targets:
  rmse_max: 0.20
  r2_min: 0.80
  mae_max: 0.15
  accuracy_min: 0.85

# Operational thresholds
ops:
  latency_p95_max_ms: 400
  error_rate_max_pct: 1.0
  cache_hit_rate_min_pct: 80.0
```

## Best Practices

**Daily Monitoring:**
- Review scorecard each morning
- Investigate any indices below 75
- Track week-over-week trends

**Weekly Review:**
- Examine weekly governance report
- Address all drift alerts
- Review security compliance events

**Monthly Audit:**
- Validate threshold appropriateness
- Review historical trends
- Update targets based on platform evolution

## Related Documentation

- [Quality Gates](/governance/quality-gates) - CI/CD integration
- [Weekly Reports](/governance/weekly-report) - Automated insights
- [Feature Flags](/governance/feature-flags) - Safe rollouts
