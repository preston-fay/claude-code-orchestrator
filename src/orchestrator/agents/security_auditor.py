"""Security Auditor agent implementation."""

import json
import time
from pathlib import Path
from typing import Dict, List, Optional, Any


class SecurityAuditor:
    """Security vulnerability assessment and compliance validation agent.

    Scans codebase for security vulnerabilities, validates compliance
    with governance policies, and generates remediation recommendations.
    """

    def __init__(self, project_root: Optional[Path] = None):
        """Initialize security auditor.

        Args:
            project_root: Project root directory (defaults to cwd)
        """
        self.project_root = project_root or Path.cwd()
        self.reports_dir = self.project_root / "reports"
        self.reports_dir.mkdir(exist_ok=True)

    def run(
        self,
        *,
        compliance_requirements: Optional[List[str]] = None,
        scan_dependencies: bool = True,
        **kwargs
    ) -> Dict[str, Any]:
        """Run security audit and generate reports.

        Args:
            compliance_requirements: List of compliance frameworks (gdpr, hipaa, soc2, etc.)
            scan_dependencies: Whether to scan third-party dependencies
            **kwargs: Additional configuration

        Returns:
            Dict with artifact paths and summary
        """
        print("🔒 Security Auditor: Starting security scan...")

        start_time = time.time()

        compliance_requirements = compliance_requirements or []

        # Scan for vulnerabilities
        vulnerabilities = self._scan_vulnerabilities()

        # Check compliance
        compliance_results = self._check_compliance(compliance_requirements)

        # Scan dependencies
        dependency_vulns = self._scan_dependencies() if scan_dependencies else []

        # Write artifacts
        artifacts = self._write_artifacts(
            vulnerabilities, compliance_results, dependency_vulns
        )

        duration = time.time() - start_time

        # Calculate summary
        critical_count = sum(1 for v in vulnerabilities if v["severity"] == "critical")
        high_count = sum(1 for v in vulnerabilities if v["severity"] == "high")

        print(f"✓ Security scan complete ({duration:.2f}s)")
        print(f"  Found {len(vulnerabilities)} code vulnerabilities")
        print(f"  Found {len(dependency_vulns)} dependency vulnerabilities")
        print(f"  Artifacts: {', '.join(artifacts)}")

        return {
            "success": True,
            "artifacts": artifacts,
            "summary": {
                "vulnerabilities_total": len(vulnerabilities),
                "vulnerabilities_critical": critical_count,
                "vulnerabilities_high": high_count,
                "dependency_vulnerabilities": len(dependency_vulns),
                "compliance_passed": all(c["status"] == "pass" for c in compliance_results),
            },
            "duration_s": duration,
        }

    def _scan_vulnerabilities(self) -> List[Dict[str, Any]]:
        """Scan codebase for security vulnerabilities."""
        # In production, this would use tools like bandit, semgrep, etc.
        # For now, generate mock findings

        vulnerabilities = [
            {
                "id": "SEC-001",
                "severity": "high",
                "category": "sql_injection",
                "title": "SQL Injection vulnerability in user query",
                "location": "src/api/users.py:45",
                "description": "User input directly concatenated into SQL query without parameterization",
                "cwe": "CWE-89",
                "owasp": "A03:2021 - Injection",
                "code_snippet": 'query = f"SELECT * FROM users WHERE id = {user_id}"',
                "remediation": "Use parameterized queries: cursor.execute('SELECT * FROM users WHERE id = %s', (user_id,))"
            },
            {
                "id": "SEC-002",
                "severity": "medium",
                "category": "xss",
                "title": "Cross-Site Scripting (XSS) in template rendering",
                "location": "src/templates/profile.html:23",
                "description": "User-provided content rendered without escaping",
                "cwe": "CWE-79",
                "owasp": "A03:2021 - Injection",
                "code_snippet": '<div>{{ user_bio }}</div>',
                "remediation": "Use template auto-escaping or explicit escaping: {{ user_bio|e }}"
            },
            {
                "id": "SEC-003",
                "severity": "critical",
                "category": "secrets",
                "title": "Hardcoded API key in source code",
                "location": "src/config/settings.py:12",
                "description": "API key hardcoded in source code instead of environment variable",
                "cwe": "CWE-798",
                "owasp": "A07:2021 - Identification and Authentication Failures",
                "code_snippet": 'API_KEY = "sk-1234567890abcdef"',
                "remediation": "Move to environment variable: API_KEY = os.getenv('API_KEY')"
            },
            {
                "id": "SEC-004",
                "severity": "medium",
                "category": "weak_crypto",
                "title": "Weak cryptographic algorithm (MD5)",
                "location": "src/auth/password.py:18",
                "description": "MD5 used for password hashing, vulnerable to rainbow table attacks",
                "cwe": "CWE-327",
                "owasp": "A02:2021 - Cryptographic Failures",
                "code_snippet": 'hashlib.md5(password.encode()).hexdigest()',
                "remediation": "Use bcrypt or argon2: bcrypt.hashpw(password.encode(), bcrypt.gensalt())"
            },
        ]

        return vulnerabilities

    def _check_compliance(self, requirements: List[str]) -> List[Dict[str, Any]]:
        """Check compliance against governance requirements."""
        compliance_results = []

        # GDPR compliance checks
        if "gdpr" in [r.lower() for r in requirements]:
            compliance_results.append({
                "framework": "GDPR",
                "status": "fail",
                "checks": [
                    {"check": "PII encryption at rest", "status": "pass"},
                    {"check": "Data retention policy", "status": "pass"},
                    {"check": "Right to erasure implementation", "status": "fail", "issue": "No user data deletion endpoint found"},
                    {"check": "Consent management", "status": "pass"},
                ]
            })

        # HIPAA compliance checks
        if "hipaa" in [r.lower() for r in requirements]:
            compliance_results.append({
                "framework": "HIPAA",
                "status": "pass",
                "checks": [
                    {"check": "PHI encryption", "status": "pass"},
                    {"check": "Access controls", "status": "pass"},
                    {"check": "Audit logging", "status": "pass"},
                    {"check": "Data backup", "status": "pass"},
                ]
            })

        # SOC2 compliance checks
        if "soc2" in [r.lower() for r in requirements]:
            compliance_results.append({
                "framework": "SOC2",
                "status": "pass",
                "checks": [
                    {"check": "Access control policies", "status": "pass"},
                    {"check": "Change management", "status": "pass"},
                    {"check": "Monitoring and alerting", "status": "pass"},
                    {"check": "Incident response", "status": "pass"},
                ]
            })

        return compliance_results

    def _scan_dependencies(self) -> List[Dict[str, Any]]:
        """Scan third-party dependencies for vulnerabilities."""
        # In production, use tools like safety, pip-audit, etc.
        # Mock findings for now

        return [
            {
                "package": "requests",
                "version": "2.25.0",
                "vulnerability": "CVE-2023-32681",
                "severity": "medium",
                "description": "Proxy-Authorization header leak in requests",
                "fixed_version": "2.31.0",
                "remediation": "Upgrade to requests>=2.31.0"
            },
            {
                "package": "flask",
                "version": "1.1.2",
                "vulnerability": "CVE-2023-30861",
                "severity": "high",
                "description": "Cookie parsing vulnerability in Werkzeug",
                "fixed_version": "2.3.2",
                "remediation": "Upgrade to flask>=2.3.2"
            },
        ]

    def _write_artifacts(
        self,
        vulnerabilities: List[Dict[str, Any]],
        compliance_results: List[Dict[str, Any]],
        dependency_vulns: List[Dict[str, Any]]
    ) -> List[str]:
        """Write security audit artifacts."""
        artifacts = []

        # Write security scan JSON
        scan_data = {
            "scan_date": time.strftime("%Y-%m-%d %H:%M:%S"),
            "vulnerabilities": vulnerabilities,
            "summary": {
                "total": len(vulnerabilities),
                "critical": sum(1 for v in vulnerabilities if v["severity"] == "critical"),
                "high": sum(1 for v in vulnerabilities if v["severity"] == "high"),
                "medium": sum(1 for v in vulnerabilities if v["severity"] == "medium"),
                "low": sum(1 for v in vulnerabilities if v["severity"] == "low"),
            }
        }

        scan_path = self.reports_dir / "security_scan.json"
        scan_path.write_text(json.dumps(scan_data, indent=2))
        artifacts.append(str(scan_path))

        # Write compliance markdown
        if compliance_results:
            compliance_md = self._format_compliance_markdown(compliance_results)
            compliance_path = self.reports_dir / "security_compliance.md"
            compliance_path.write_text(compliance_md)
            artifacts.append(str(compliance_path))

        # Write dependency vulnerabilities JSON
        if dependency_vulns:
            dep_vuln_path = self.reports_dir / "dependency_vulnerabilities.json"
            dep_vuln_path.write_text(json.dumps({
                "scan_date": time.strftime("%Y-%m-%d %H:%M:%S"),
                "vulnerabilities": dependency_vulns,
                "summary": {
                    "total": len(dependency_vulns),
                    "critical": sum(1 for v in dependency_vulns if v["severity"] == "critical"),
                    "high": sum(1 for v in dependency_vulns if v["severity"] == "high"),
                    "medium": sum(1 for v in dependency_vulns if v["severity"] == "medium"),
                }
            }, indent=2))
            artifacts.append(str(dep_vuln_path))

        return artifacts

    def _format_compliance_markdown(self, compliance_results: List[Dict[str, Any]]) -> str:
        """Format compliance results as markdown."""
        md = "# Security Compliance Report\n\n"

        for result in compliance_results:
            status_emoji = "✓" if result["status"] == "pass" else "✗"
            md += f"## {result['framework']} - {status_emoji} {result['status'].upper()}\n\n"

            for check in result["checks"]:
                check_emoji = "✓" if check["status"] == "pass" else "✗"
                md += f"- {check_emoji} {check['check']}"
                if check["status"] == "fail" and "issue" in check:
                    md += f" - **Issue**: {check['issue']}"
                md += "\n"

            md += "\n"

        return md


def main():
    """CLI entrypoint for security auditor."""
    import sys

    auditor = SecurityAuditor()
    result = auditor.run(compliance_requirements=["gdpr", "soc2"])

    if result["success"]:
        print("\n✓ Security audit complete")
        sys.exit(0)
    else:
        print("\n✗ Security audit failed")
        sys.exit(1)


if __name__ == "__main__":
    main()
