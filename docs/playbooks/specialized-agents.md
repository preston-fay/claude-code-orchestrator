# Specialized Agents - Playbook

This playbook explains how specialized agents are automatically detected and how to use them.

## Overview

Three specialized agents automatically trigger based on project requirements:

| Agent | Triggers | Phase | Output |
|-------|----------|-------|--------|
| **Performance Engineer** | Performance SLAs, production env, perf keywords | developer, qa | Performance profile, recommendations, load test results |
| **Security Auditor** | Security scan required, compliance, production | developer, qa | Vulnerability scan, compliance report, dependency check |
| **Database Architect** | Database keywords, SQL mentions | planning, developer | Schema SQL, migrations, ER diagrams |

## Automatic Detection

### Performance Engineer

Triggers when:
```yaml
# In governance.yaml
performance_slas:
  latency_p95_ms: 200  # Set target > 0
```

OR when intake contains: `performance`, `latency`, `throughput`, `optimization`, `scale`

OR when `intake.environment == "production"`

### Security Auditor

Triggers when:
```yaml
# In governance.yaml
quality_gates:
  require_security_scan: true

# OR
compliance:
  gdpr: {...}
  hipaa: {...}
```

OR when intake contains: `security`, `authentication`, `authorization`, `compliance`

OR when `intake.environment == "production"`

### Database Architect

Triggers when:
```yaml
# In intake.yaml
project:
  type: "database migration"

requirements:
  - "PostgreSQL schema design"
  - "Database optimization"
```

OR when intake contains: `db`, `database`, `sql`, `postgres`, `mysql`, `schema`, `migration`

## Manual Override

Disable auto-detection by explicitly listing agents in phase config:

```yaml
# .claude/config.yaml
workflow:
  phases:
    developer:
      agents:
        - developer
        # Omit specialized agents to disable auto-detection for this phase
```

Force a specialized agent even without triggers:

```yaml
workflow:
  phases:
    developer:
      agents:
        - developer
        - performance-engineer  # Always run
```

## Artifacts

### Performance Engineer
- `reports/performance_profile.json` - Metrics (P50, P95, P99 latency, throughput, error rate)
- `reports/performance_recommendations.md` - Prioritized optimization recommendations
- `reports/load_test_results.json` - Load testing metrics

### Security Auditor
- `reports/security_scan.json` - Vulnerability findings (SQL injection, XSS, secrets, etc.)
- `reports/security_compliance.md` - GDPR/HIPAA/SOC2 compliance status
- `reports/dependency_vulnerabilities.json` - Third-party package vulnerabilities

### Database Architect
- `schema.sql` - Complete database schema (CREATE TABLE statements, indexes, constraints)
- `migrations/` - Versioned migration scripts with up/down
- `reports/database_architecture.md` - ER diagrams and data dictionary
- `reports/index_recommendations.json` - Index optimization suggestions

## Examples

### Example 1: Production API with SLA

**Intake**:
```yaml
project:
  name: "Customer API"
  type: "REST API"

environment: "production"

requirements:
  - "Handle 1000 requests/second"
  - "P95 latency under 200ms"
```

**Governance**:
```yaml
performance_slas:
  latency_p95_ms: 200

quality_gates:
  require_security_scan: true
```

**Result**: Both Performance Engineer and Security Auditor auto-detected for `developer` phase.

### Example 2: Database Migration Project

**Intake**:
```yaml
project:
  name: "User Schema Migration"
  type: "database"

requirements:
  - "Migrate from MySQL to PostgreSQL"
  - "Add new user authentication tables"
```

**Result**: Database Architect auto-detected for `planning` and `developer` phases, inserted before developer agent.

### Example 3: Internal Analytics (No Triggers)

**Intake**:
```yaml
project:
  name: "Sales Dashboard"
  type: "analytics"

environment: "internal"

requirements:
  - "Visualize quarterly sales data"
  - "Export to Excel"
```

**Result**: No specialized agents detected. Base workflow runs unchanged.

## Debugging

### Check if Agent Was Detected

Look in run logs:
```bash
orchestrator run log | grep "Auto-detected"
```

Output:
```
Auto-detected: database-architect (database keywords found)
Auto-detected: security-auditor (security scan required, production environment)
```

### Verify Agent Execution

```bash
ls reports/
# Should show specialized agent artifacts:
# - performance_profile.json
# - security_scan.json
# - database_architecture.md
```

### Force Detection for Testing

Temporarily modify intake or governance:
```bash
# Add to intake.yaml
requirements:
  - "Test performance optimization"  # Triggers performance-engineer

# Or update governance
echo "  latency_p95_ms: 100" >> clients/my-client/governance.yaml
```

## See Also

- [ADR-005: Specialized Agents](../adr/005-specialized-agents.md)
- [Agent Definitions](.claude/agents/)
- [Governance Configuration](../../clients/README.md)
