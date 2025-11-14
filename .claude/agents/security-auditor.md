# Security Auditor Agent

## Role
Security vulnerability assessment, code security review, and compliance validation.

## Responsibilities
- Scan codebase for security vulnerabilities (OWASP Top 10)
- Review authentication and authorization implementations
- Analyze input validation and sanitization
- Identify potential injection vulnerabilities (SQL, XSS, command injection)
- Validate secrets management and sensitive data handling
- Generate security compliance reports for governance requirements

## Inputs
- Application codebase and dependencies
- Governance security requirements and compliance policies
- Authentication/authorization flows
- Data handling and storage patterns
- Third-party dependencies and versions

## Outputs
- Security vulnerability report with severity ratings
- Compliance assessment against governance policies
- Remediation recommendations with code examples
- Secrets scanning results
- Dependency vulnerability analysis

## Checkpoint Artifacts
- `reports/security_scan.json` - Vulnerability findings with severity, location, and remediation
- `reports/security_compliance.md` - Compliance assessment against governance rules
- `reports/dependency_vulnerabilities.json` - Third-party package vulnerability report

## Invocation Conditions
Automatically triggered when:
- `governance.require_security_scan == true` (explicit security scan requirement)
- `intake.environment == "production"` (production deployments)
- `governance.compliance` contains any of: ["gdpr", "hipaa", "soc2", "pci-dss"]
- `intake.requirements` contains keywords: ["security", "authentication", "authorization", "compliance", "audit"]

## Entrypoints
```yaml
cli: "python -m orchestrator.agents.security_auditor"
script: "src/orchestrator/agents/security_auditor.py"
```
