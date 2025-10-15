"""
Security Scanning Module
Aggregates security scan results from multiple tools and computes a platform security score.
"""

import json
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
import yaml


def load_config() -> Dict[str, Any]:
    """Load lifecycle configuration."""
    config_path = Path(__file__).parent.parent.parent / "configs" / "lifecycle.yaml"
    with open(config_path) as f:
        return yaml.safe_load(f)


def run_bandit_scan(src_path: Path) -> Dict[str, Any]:
    """
    Run Bandit static analysis on Python code.
    Returns findings categorized by severity.
    """
    print(f"Running Bandit scan on {src_path}...")

    result = {
        "tool": "bandit",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "findings": [],
        "summary": {
            "high": 0,
            "medium": 0,
            "low": 0
        },
        "status": "success"
    }

    try:
        proc = subprocess.run(
            ["bandit", "-r", str(src_path), "-f", "json"],
            capture_output=True,
            text=True,
            timeout=120
        )

        # Bandit returns non-zero if findings exist
        if proc.stdout:
            try:
                bandit_data = json.loads(proc.stdout)

                for finding in bandit_data.get("results", []):
                    severity = finding.get("issue_severity", "UNDEFINED").lower()
                    confidence = finding.get("issue_confidence", "UNDEFINED").lower()

                    result["findings"].append({
                        "severity": severity,
                        "confidence": confidence,
                        "issue": finding.get("issue_text", ""),
                        "file": finding.get("filename", ""),
                        "line": finding.get("line_number", 0),
                        "test_id": finding.get("test_id", "")
                    })

                    # Update summary
                    if severity in result["summary"]:
                        result["summary"][severity] += 1

                result["status"] = "findings" if result["findings"] else "clean"

            except json.JSONDecodeError:
                result["status"] = "error"
                result["error"] = "Failed to parse Bandit output"

    except subprocess.TimeoutExpired:
        result["status"] = "timeout"
        result["error"] = "Bandit scan timed out"
    except FileNotFoundError:
        result["status"] = "tool_missing"
        result["error"] = "Bandit not installed"
    except Exception as e:
        result["status"] = "error"
        result["error"] = str(e)

    return result


def run_pip_audit() -> Dict[str, Any]:
    """
    Run pip-audit to check for known CVEs in Python dependencies.
    Returns vulnerability findings.
    """
    print("Running pip-audit for CVE scanning...")

    result = {
        "tool": "pip-audit",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "vulnerabilities": [],
        "summary": {
            "critical": 0,
            "high": 0,
            "medium": 0,
            "low": 0
        },
        "status": "success"
    }

    try:
        proc = subprocess.run(
            ["pip-audit", "--format", "json"],
            capture_output=True,
            text=True,
            timeout=120
        )

        if proc.returncode == 0:
            result["status"] = "clean"
        else:
            try:
                audit_data = json.loads(proc.stdout)

                for vuln in audit_data.get("dependencies", []):
                    package_name = vuln.get("name")
                    current_version = vuln.get("version")

                    for issue in vuln.get("vulns", []):
                        severity = issue.get("severity", "unknown").lower()

                        result["vulnerabilities"].append({
                            "package": package_name,
                            "version": current_version,
                            "severity": severity,
                            "id": issue.get("id"),
                            "description": issue.get("description", ""),
                            "fix_versions": issue.get("fix_versions", [])
                        })

                        # Update summary
                        if severity in result["summary"]:
                            result["summary"][severity] += 1

                result["status"] = "vulnerabilities" if result["vulnerabilities"] else "clean"

            except json.JSONDecodeError:
                result["status"] = "error"
                result["error"] = "Failed to parse pip-audit output"

    except subprocess.TimeoutExpired:
        result["status"] = "timeout"
        result["error"] = "pip-audit timed out"
    except FileNotFoundError:
        result["status"] = "tool_missing"
        result["error"] = "pip-audit not installed"
    except Exception as e:
        result["status"] = "error"
        result["error"] = str(e)

    return result


def run_npm_audit(project_path: Path) -> Dict[str, Any]:
    """
    Run npm audit to check for known CVEs in Node dependencies.
    Returns vulnerability findings.
    """
    print(f"Running npm audit for {project_path}...")

    result = {
        "tool": "npm-audit",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "vulnerabilities": [],
        "summary": {
            "critical": 0,
            "high": 0,
            "moderate": 0,
            "low": 0
        },
        "status": "success",
        "project": str(project_path)
    }

    if not (project_path / "package.json").exists():
        result["status"] = "no_package_json"
        return result

    try:
        proc = subprocess.run(
            ["npm", "audit", "--json"],
            cwd=project_path,
            capture_output=True,
            text=True,
            timeout=120
        )

        try:
            audit_data = json.loads(proc.stdout)

            vulnerabilities = audit_data.get("vulnerabilities", {})
            for pkg_name, vuln_data in vulnerabilities.items():
                severity = vuln_data.get("severity", "unknown").lower()

                result["vulnerabilities"].append({
                    "package": pkg_name,
                    "severity": severity,
                    "via": vuln_data.get("via", []),
                    "fix_available": vuln_data.get("fixAvailable", False),
                    "range": vuln_data.get("range", "unknown")
                })

                # Update summary
                if severity in result["summary"]:
                    result["summary"][severity] += 1

            result["status"] = "vulnerabilities" if result["vulnerabilities"] else "clean"

        except json.JSONDecodeError:
            result["status"] = "error"
            result["error"] = "Failed to parse npm audit output"

    except subprocess.TimeoutExpired:
        result["status"] = "timeout"
        result["error"] = "npm audit timed out"
    except Exception as e:
        result["status"] = "error"
        result["error"] = str(e)

    return result


def run_trivy_scan(target_path: Path) -> Optional[Dict[str, Any]]:
    """
    Run Trivy filesystem scan (optional, if available).
    Returns vulnerability findings from container/filesystem scan.
    """
    print(f"Running Trivy scan on {target_path}...")

    result = {
        "tool": "trivy",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "vulnerabilities": [],
        "summary": {
            "critical": 0,
            "high": 0,
            "medium": 0,
            "low": 0
        },
        "status": "success"
    }

    try:
        proc = subprocess.run(
            ["trivy", "fs", "--format", "json", str(target_path)],
            capture_output=True,
            text=True,
            timeout=300
        )

        if proc.stdout:
            try:
                trivy_data = json.loads(proc.stdout)

                for target in trivy_data.get("Results", []):
                    for vuln in target.get("Vulnerabilities", []):
                        severity = vuln.get("Severity", "UNKNOWN").lower()

                        result["vulnerabilities"].append({
                            "package": vuln.get("PkgName"),
                            "version": vuln.get("InstalledVersion"),
                            "severity": severity,
                            "vulnerability_id": vuln.get("VulnerabilityID"),
                            "title": vuln.get("Title", ""),
                            "fixed_version": vuln.get("FixedVersion", "")
                        })

                        # Update summary
                        if severity in result["summary"]:
                            result["summary"][severity] += 1

                result["status"] = "vulnerabilities" if result["vulnerabilities"] else "clean"

            except json.JSONDecodeError:
                result["status"] = "error"
                result["error"] = "Failed to parse Trivy output"

    except FileNotFoundError:
        # Trivy not installed - this is optional
        return None
    except subprocess.TimeoutExpired:
        result["status"] = "timeout"
        result["error"] = "Trivy scan timed out"
    except Exception as e:
        result["status"] = "error"
        result["error"] = str(e)

    return result


def compute_platform_security_score(scan_results: Dict[str, Any]) -> float:
    """
    Compute a platform security score (0-100) based on aggregated scan results.

    Scoring methodology:
    - Start at 100
    - Deduct points for vulnerabilities based on severity:
      - Critical: -20 points each
      - High: -10 points each
      - Medium: -5 points each
      - Low: -2 points each
    - Deduct points for code quality issues (Bandit findings):
      - High severity: -5 points each
      - Medium severity: -2 points each
      - Low severity: -1 point each
    - Minimum score: 0
    """
    score = 100.0

    # Deduct for pip-audit vulnerabilities
    if "pip_audit" in scan_results and scan_results["pip_audit"]["status"] == "vulnerabilities":
        summary = scan_results["pip_audit"]["summary"]
        score -= summary.get("critical", 0) * 20
        score -= summary.get("high", 0) * 10
        score -= summary.get("medium", 0) * 5
        score -= summary.get("low", 0) * 2

    # Deduct for npm audit vulnerabilities
    if "npm_audit" in scan_results:
        for npm_result in scan_results["npm_audit"]:
            if npm_result["status"] == "vulnerabilities":
                summary = npm_result["summary"]
                score -= summary.get("critical", 0) * 20
                score -= summary.get("high", 0) * 10
                score -= summary.get("moderate", 0) * 5
                score -= summary.get("low", 0) * 2

    # Deduct for Bandit code quality issues
    if "bandit" in scan_results and scan_results["bandit"]["status"] == "findings":
        summary = scan_results["bandit"]["summary"]
        score -= summary.get("high", 0) * 5
        score -= summary.get("medium", 0) * 2
        score -= summary.get("low", 0) * 1

    # Deduct for Trivy vulnerabilities (if available)
    if "trivy" in scan_results and scan_results["trivy"] and \
       scan_results["trivy"]["status"] == "vulnerabilities":
        summary = scan_results["trivy"]["summary"]
        score -= summary.get("critical", 0) * 20
        score -= summary.get("high", 0) * 10
        score -= summary.get("medium", 0) * 5
        score -= summary.get("low", 0) * 2

    # Ensure score doesn't go below 0
    return max(0.0, score)


def aggregate_scan_results() -> Dict[str, Any]:
    """
    Run all security scans and aggregate results.
    Returns comprehensive security report with PlatformSecurityScore.
    """
    project_root = Path(__file__).parent.parent.parent

    results = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "platform_security_score": 0.0,
        "scan_results": {}
    }

    # Run Bandit scan on src directory
    src_path = project_root / "src"
    if src_path.exists():
        results["scan_results"]["bandit"] = run_bandit_scan(src_path)

    # Run pip-audit
    results["scan_results"]["pip_audit"] = run_pip_audit()

    # Run npm audit on all Node projects
    npm_results = []
    possible_locations = [
        project_root / "apps" / "web",
        project_root,
    ]

    for loc in possible_locations:
        if (loc / "package.json").exists():
            npm_results.append(run_npm_audit(loc))

    if npm_results:
        results["scan_results"]["npm_audit"] = npm_results

    # Run Trivy scan (optional)
    trivy_result = run_trivy_scan(project_root)
    if trivy_result:
        results["scan_results"]["trivy"] = trivy_result

    # Compute platform security score
    results["platform_security_score"] = compute_platform_security_score(results["scan_results"])

    # Determine overall status
    score = results["platform_security_score"]
    if score >= 95:
        results["status"] = "excellent"
    elif score >= 85:
        results["status"] = "good"
    elif score >= 70:
        results["status"] = "fair"
    else:
        results["status"] = "poor"

    return results


def save_security_report(results: Dict[str, Any]):
    """Save security scan report to JSON file."""
    report_dir = Path(__file__).parent.parent.parent / "reports" / "lifecycle" / "security"
    report_dir.mkdir(parents=True, exist_ok=True)

    date_str = datetime.utcnow().strftime("%Y-%m-%d")
    report_path = report_dir / f"{date_str}.json"

    with open(report_path, "w") as f:
        json.dump(results, f, indent=2)

    print(f"\nSecurity report saved to: {report_path}")


def print_security_summary(results: Dict[str, Any]):
    """Print human-readable security summary."""
    print("\n" + "=" * 70)
    print("PLATFORM SECURITY SCAN SUMMARY")
    print("=" * 70)

    print(f"\nPlatform Security Score: {results['platform_security_score']:.1f}/100")
    print(f"Status: {results['status'].upper()}")

    scan_results = results.get("scan_results", {})

    # Bandit summary
    if "bandit" in scan_results:
        bandit = scan_results["bandit"]
        if bandit["status"] == "findings":
            print(f"\nBandit (Python Static Analysis):")
            print(f"  High severity: {bandit['summary']['high']}")
            print(f"  Medium severity: {bandit['summary']['medium']}")
            print(f"  Low severity: {bandit['summary']['low']}")
        elif bandit["status"] == "clean":
            print(f"\nBandit (Python Static Analysis): CLEAN")

    # pip-audit summary
    if "pip_audit" in scan_results:
        pip_audit = scan_results["pip_audit"]
        if pip_audit["status"] == "vulnerabilities":
            print(f"\npip-audit (Python CVEs):")
            print(f"  Critical: {pip_audit['summary']['critical']}")
            print(f"  High: {pip_audit['summary']['high']}")
            print(f"  Medium: {pip_audit['summary']['medium']}")
            print(f"  Low: {pip_audit['summary']['low']}")
        elif pip_audit["status"] == "clean":
            print(f"\npip-audit (Python CVEs): CLEAN")

    # npm audit summary
    if "npm_audit" in scan_results:
        print(f"\nnpm audit (Node CVEs):")
        for npm_result in scan_results["npm_audit"]:
            project = npm_result.get("project", "unknown")
            if npm_result["status"] == "vulnerabilities":
                print(f"  {project}:")
                print(f"    Critical: {npm_result['summary']['critical']}")
                print(f"    High: {npm_result['summary']['high']}")
                print(f"    Moderate: {npm_result['summary']['moderate']}")
                print(f"    Low: {npm_result['summary']['low']}")
            elif npm_result["status"] == "clean":
                print(f"  {project}: CLEAN")

    # Trivy summary (if available)
    if "trivy" in scan_results and scan_results["trivy"]:
        trivy = scan_results["trivy"]
        if trivy["status"] == "vulnerabilities":
            print(f"\nTrivy (Filesystem Scan):")
            print(f"  Critical: {trivy['summary']['critical']}")
            print(f"  High: {trivy['summary']['high']}")
            print(f"  Medium: {trivy['summary']['medium']}")
            print(f"  Low: {trivy['summary']['low']}")
        elif trivy["status"] == "clean":
            print(f"\nTrivy (Filesystem Scan): CLEAN")

    print("\n" + "=" * 70)


if __name__ == "__main__":
    """Run security scan when executed directly."""
    import sys

    print("Starting platform security scan...")

    results = aggregate_scan_results()
    print_security_summary(results)
    save_security_report(results)

    # Exit code based on score
    score = results["platform_security_score"]
    if score < 70:
        print("\nERROR: Platform security score below acceptable threshold (70)")
        sys.exit(1)
    else:
        print(f"\nPlatform security scan complete (score: {score:.1f}/100)")
        sys.exit(0)
