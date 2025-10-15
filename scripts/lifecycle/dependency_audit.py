#!/usr/bin/env python3
"""
Dependency Audit Script
Audits Python and Node dependencies, identifies vulnerabilities, and auto-upgrades safe packages.
"""

import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Tuple
import yaml
import os

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))


def load_config() -> Dict[str, Any]:
    """Load lifecycle configuration."""
    config_path = Path(__file__).parent.parent.parent / "configs" / "lifecycle.yaml"
    with open(config_path) as f:
        return yaml.safe_load(f)


def audit_python_dependencies() -> Dict[str, Any]:
    """
    Audit Python dependencies using pip-audit.
    Returns vulnerabilities found and safe upgrade candidates.
    """
    print("Auditing Python dependencies...")

    result = {
        "tool": "pip-audit",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "vulnerabilities": [],
        "safe_upgrades": [],
        "errors": []
    }

    try:
        # Run pip-audit with JSON output
        proc = subprocess.run(
            ["pip-audit", "--format", "json"],
            capture_output=True,
            text=True,
            timeout=120
        )

        if proc.returncode == 0:
            # No vulnerabilities found
            result["status"] = "clean"
        else:
            # Parse vulnerabilities
            try:
                audit_data = json.loads(proc.stdout)
                result["status"] = "vulnerabilities_found"

                for vuln in audit_data.get("dependencies", []):
                    package_name = vuln.get("name")
                    current_version = vuln.get("version")

                    for issue in vuln.get("vulns", []):
                        severity = issue.get("severity", "unknown").lower()
                        result["vulnerabilities"].append({
                            "package": package_name,
                            "current_version": current_version,
                            "severity": severity,
                            "id": issue.get("id"),
                            "description": issue.get("description", ""),
                            "fix_versions": issue.get("fix_versions", [])
                        })
            except json.JSONDecodeError:
                result["errors"].append("Failed to parse pip-audit output")
                result["status"] = "error"

    except subprocess.TimeoutExpired:
        result["errors"].append("pip-audit timed out")
        result["status"] = "timeout"
    except FileNotFoundError:
        result["errors"].append("pip-audit not installed")
        result["status"] = "tool_missing"
    except Exception as e:
        result["errors"].append(f"pip-audit error: {str(e)}")
        result["status"] = "error"

    # Check for available upgrades using pip list --outdated
    try:
        proc = subprocess.run(
            ["pip", "list", "--outdated", "--format", "json"],
            capture_output=True,
            text=True,
            timeout=30
        )

        if proc.returncode == 0:
            outdated = json.loads(proc.stdout)
            for pkg in outdated:
                # Determine if upgrade is safe (patch or minor only)
                current = pkg.get("version", "0.0.0").split(".")
                latest = pkg.get("latest_version", "0.0.0").split(".")

                is_patch = len(current) >= 3 and len(latest) >= 3 and \
                          current[0] == latest[0] and current[1] == latest[1]
                is_minor = len(current) >= 2 and len(latest) >= 2 and \
                          current[0] == latest[0]

                result["safe_upgrades"].append({
                    "package": pkg.get("name"),
                    "current_version": pkg.get("version"),
                    "latest_version": pkg.get("latest_version"),
                    "type": "patch" if is_patch else ("minor" if is_minor else "major")
                })

    except Exception as e:
        result["errors"].append(f"Failed to check outdated packages: {str(e)}")

    return result


def audit_node_dependencies() -> Dict[str, Any]:
    """
    Audit Node dependencies using npm audit.
    Returns vulnerabilities found and safe upgrade candidates.
    """
    print("Auditing Node dependencies...")

    result = {
        "tool": "npm",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "vulnerabilities": [],
        "safe_upgrades": [],
        "errors": []
    }

    # Find package.json locations
    project_root = Path(__file__).parent.parent.parent
    node_projects = []

    # Check for package.json in common locations
    possible_locations = [
        project_root / "apps" / "web",
        project_root,
    ]

    for loc in possible_locations:
        if (loc / "package.json").exists():
            node_projects.append(loc)

    if not node_projects:
        result["status"] = "no_node_projects"
        return result

    all_vulnerabilities = []
    all_safe_upgrades = []

    for project_path in node_projects:
        try:
            # Run npm audit with JSON output
            proc = subprocess.run(
                ["npm", "audit", "--json"],
                cwd=project_path,
                capture_output=True,
                text=True,
                timeout=120
            )

            try:
                audit_data = json.loads(proc.stdout)

                # Parse vulnerabilities
                vulnerabilities = audit_data.get("vulnerabilities", {})
                for pkg_name, vuln_data in vulnerabilities.items():
                    severity = vuln_data.get("severity", "unknown").lower()
                    all_vulnerabilities.append({
                        "package": pkg_name,
                        "current_version": vuln_data.get("range", "unknown"),
                        "severity": severity,
                        "via": vuln_data.get("via", []),
                        "fix_available": vuln_data.get("fixAvailable", False),
                        "project": str(project_path.relative_to(project_root))
                    })

            except json.JSONDecodeError:
                result["errors"].append(f"Failed to parse npm audit output for {project_path}")

        except subprocess.TimeoutExpired:
            result["errors"].append(f"npm audit timed out for {project_path}")
        except Exception as e:
            result["errors"].append(f"npm audit error for {project_path}: {str(e)}")

        # Check for outdated packages
        try:
            proc = subprocess.run(
                ["npm", "outdated", "--json"],
                cwd=project_path,
                capture_output=True,
                text=True,
                timeout=30
            )

            # npm outdated returns non-zero if there are outdated packages
            if proc.stdout:
                try:
                    outdated = json.loads(proc.stdout)
                    for pkg_name, pkg_data in outdated.items():
                        current = pkg_data.get("current", "0.0.0").split(".")
                        latest = pkg_data.get("latest", "0.0.0").split(".")

                        is_patch = len(current) >= 3 and len(latest) >= 3 and \
                                  current[0] == latest[0] and current[1] == latest[1]
                        is_minor = len(current) >= 2 and len(latest) >= 2 and \
                                  current[0] == latest[0]

                        all_safe_upgrades.append({
                            "package": pkg_name,
                            "current_version": pkg_data.get("current"),
                            "latest_version": pkg_data.get("latest"),
                            "type": "patch" if is_patch else ("minor" if is_minor else "major"),
                            "project": str(project_path.relative_to(project_root))
                        })
                except json.JSONDecodeError:
                    pass  # No outdated packages or parse error

        except Exception as e:
            result["errors"].append(f"Failed to check outdated npm packages: {str(e)}")

    result["vulnerabilities"] = all_vulnerabilities
    result["safe_upgrades"] = all_safe_upgrades
    result["status"] = "vulnerabilities_found" if all_vulnerabilities else "clean"

    return result


def determine_action_plan(config: Dict, python_audit: Dict, node_audit: Dict) -> Dict[str, Any]:
    """
    Determine which packages need manual review vs auto-upgrade.
    """
    severity_threshold = config.get("audit", {}).get("severity_threshold", "high")
    auto_upgrade_python = config.get("python", {}).get("auto_upgrade", True)
    auto_upgrade_node = config.get("node", {}).get("auto_upgrade", True)
    python_upgrade_types = set(config.get("python", {}).get("upgrade_types", ["patch", "minor"]))
    node_upgrade_types = set(config.get("node", {}).get("upgrade_types", ["patch", "minor"]))

    plan = {
        "manual_review": [],
        "auto_upgrade": [],
        "safe_to_proceed": True
    }

    # Check Python vulnerabilities
    for vuln in python_audit.get("vulnerabilities", []):
        severity = vuln.get("severity", "unknown")
        if severity in ["critical", "high"]:
            plan["manual_review"].append({
                "type": "vulnerability",
                "ecosystem": "python",
                "package": vuln["package"],
                "severity": severity,
                "reason": "High/critical severity requires manual review"
            })
            plan["safe_to_proceed"] = False

    # Check Node vulnerabilities
    for vuln in node_audit.get("vulnerabilities", []):
        severity = vuln.get("severity", "unknown")
        if severity in ["critical", "high"]:
            plan["manual_review"].append({
                "type": "vulnerability",
                "ecosystem": "node",
                "package": vuln["package"],
                "severity": severity,
                "reason": "High/critical severity requires manual review"
            })
            plan["safe_to_proceed"] = False

    # Determine auto-upgrades for Python
    if auto_upgrade_python:
        for upgrade in python_audit.get("safe_upgrades", []):
            if upgrade["type"] in python_upgrade_types:
                plan["auto_upgrade"].append({
                    "ecosystem": "python",
                    "package": upgrade["package"],
                    "from": upgrade["current_version"],
                    "to": upgrade["latest_version"],
                    "type": upgrade["type"]
                })

    # Determine auto-upgrades for Node
    if auto_upgrade_node:
        for upgrade in node_audit.get("safe_upgrades", []):
            if upgrade["type"] in node_upgrade_types:
                plan["auto_upgrade"].append({
                    "ecosystem": "node",
                    "package": upgrade["package"],
                    "from": upgrade["current_version"],
                    "to": upgrade["latest_version"],
                    "type": upgrade["type"],
                    "project": upgrade.get("project", "")
                })

    return plan


def apply_auto_upgrades(plan: Dict[str, Any]) -> List[str]:
    """
    Apply auto-upgrades to dependencies.
    Returns list of upgraded packages.
    """
    upgraded = []

    for upgrade in plan.get("auto_upgrade", []):
        ecosystem = upgrade["ecosystem"]
        package = upgrade["package"]

        try:
            if ecosystem == "python":
                print(f"Upgrading {package} to {upgrade['to']}...")
                subprocess.run(
                    ["pip", "install", "--upgrade", package],
                    check=True,
                    capture_output=True
                )
                upgraded.append(f"{package} ({upgrade['from']} -> {upgrade['to']})")

            elif ecosystem == "node":
                project = Path(__file__).parent.parent.parent / upgrade.get("project", "")
                print(f"Upgrading {package} to {upgrade['to']} in {upgrade.get('project', 'root')}...")
                subprocess.run(
                    ["npm", "update", package],
                    cwd=project,
                    check=True,
                    capture_output=True
                )
                upgraded.append(f"{package} ({upgrade['from']} -> {upgrade['to']}) in {upgrade.get('project', '')}")

        except subprocess.CalledProcessError as e:
            print(f"Failed to upgrade {package}: {e}")

    return upgraded


def create_upgrade_pr(upgraded: List[str], config: Dict) -> bool:
    """
    Create a PR for auto-upgraded dependencies using gh CLI.
    """
    if not upgraded:
        print("No packages upgraded, skipping PR creation")
        return False

    if not config.get("audit", {}).get("create_pr", False):
        print("PR creation disabled in config")
        return False

    branch_prefix = config.get("audit", {}).get("branch_prefix", "auto/dep-upgrade-")
    date_str = datetime.utcnow().strftime("%Y%m%d")
    branch_name = f"{branch_prefix}{date_str}"

    try:
        # Create branch
        subprocess.run(["git", "checkout", "-b", branch_name], check=True, capture_output=True)

        # Stage changes
        subprocess.run(["git", "add", "requirements*.txt", "package*.json", "package-lock.json"],
                      capture_output=True)

        # Commit
        commit_msg = f"chore: auto-upgrade dependencies ({date_str})\n\nUpgraded packages:\n" + \
                    "\n".join(f"- {pkg}" for pkg in upgraded)

        subprocess.run(["git", "commit", "-m", commit_msg], check=True, capture_output=True)

        # Push
        subprocess.run(["git", "push", "-u", "origin", branch_name], check=True, capture_output=True)

        # Create PR using gh CLI
        pr_body = f"""Automated dependency upgrade

This PR upgrades safe dependencies (patch/minor versions only).

## Upgraded Packages

{chr(10).join(f'- {pkg}' for pkg in upgraded)}

## Review Checklist

- [ ] All tests pass
- [ ] No breaking changes
- [ ] Security scans clean

Generated by lifecycle automation."""

        labels = config.get("audit", {}).get("pr_labels", ["dependencies", "automated"])
        label_args = []
        for label in labels:
            label_args.extend(["--label", label])

        subprocess.run(
            ["gh", "pr", "create", "--title", f"chore: auto-upgrade dependencies ({date_str})",
             "--body", pr_body] + label_args,
            check=True,
            capture_output=True
        )

        print(f"Created PR for branch {branch_name}")
        return True

    except subprocess.CalledProcessError as e:
        print(f"Failed to create PR: {e}")
        return False


def save_audit_report(python_audit: Dict, node_audit: Dict, action_plan: Dict, upgraded: List[str]):
    """Save audit report to JSON file."""
    report_dir = Path(__file__).parent.parent.parent / "reports" / "lifecycle" / "dependencies"
    report_dir.mkdir(parents=True, exist_ok=True)

    date_str = datetime.utcnow().strftime("%Y-%m-%d")
    report_path = report_dir / f"{date_str}.json"

    report = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "python": python_audit,
        "node": node_audit,
        "action_plan": action_plan,
        "upgraded": upgraded
    }

    with open(report_path, "w") as f:
        json.dump(report, f, indent=2)

    print(f"\nAudit report saved to: {report_path}")


def print_summary(python_audit: Dict, node_audit: Dict, action_plan: Dict):
    """Print human-readable summary."""
    print("\n" + "=" * 70)
    print("DEPENDENCY AUDIT SUMMARY")
    print("=" * 70)

    # Python summary
    python_vulns = len(python_audit.get("vulnerabilities", []))
    python_upgrades = len([u for u in python_audit.get("safe_upgrades", [])
                           if u["type"] in ["patch", "minor"]])

    print(f"\nPython:")
    print(f"  Vulnerabilities: {python_vulns}")
    print(f"  Safe upgrades available: {python_upgrades}")

    # Node summary
    node_vulns = len(node_audit.get("vulnerabilities", []))
    node_upgrades = len([u for u in node_audit.get("safe_upgrades", [])
                         if u["type"] in ["patch", "minor"]])

    print(f"\nNode:")
    print(f"  Vulnerabilities: {node_vulns}")
    print(f"  Safe upgrades available: {node_upgrades}")

    # Action plan
    manual_count = len(action_plan.get("manual_review", []))
    auto_count = len(action_plan.get("auto_upgrade", []))

    print(f"\nAction Plan:")
    print(f"  Manual review required: {manual_count}")
    print(f"  Auto-upgrades planned: {auto_count}")
    print(f"  Safe to auto-upgrade: {'YES' if action_plan['safe_to_proceed'] else 'NO'}")

    # Manual review items
    if manual_count > 0:
        print(f"\n  Manual Review Required:")
        for item in action_plan["manual_review"]:
            print(f"    - [{item['severity'].upper()}] {item['ecosystem']}/{item['package']}")
            print(f"      Reason: {item['reason']}")

    print("\n" + "=" * 70)


def main():
    """Main entry point."""
    print("Starting dependency audit...")

    # Load configuration
    config = load_config()

    # Run audits
    python_audit = audit_python_dependencies()
    node_audit = audit_node_dependencies()

    # Determine action plan
    action_plan = determine_action_plan(config, python_audit, node_audit)

    # Print summary
    print_summary(python_audit, node_audit, action_plan)

    # Apply auto-upgrades if safe
    upgraded = []
    if action_plan["safe_to_proceed"] and action_plan["auto_upgrade"]:
        print("\nApplying auto-upgrades...")
        upgraded = apply_auto_upgrades(action_plan)

        if upgraded:
            print(f"\nSuccessfully upgraded {len(upgraded)} packages:")
            for pkg in upgraded:
                print(f"  - {pkg}")

            # Create PR if configured
            create_upgrade_pr(upgraded, config)
    elif not action_plan["safe_to_proceed"]:
        print("\nAuto-upgrade skipped due to high/critical vulnerabilities requiring manual review")
    else:
        print("\nNo auto-upgrades to apply")

    # Save report
    save_audit_report(python_audit, node_audit, action_plan, upgraded)

    # Exit code based on vulnerabilities
    total_vulns = len(python_audit.get("vulnerabilities", [])) + \
                 len(node_audit.get("vulnerabilities", []))

    if total_vulns > 0:
        print(f"\nWARNING: {total_vulns} vulnerabilities found")
        sys.exit(1)
    else:
        print("\nAll checks passed")
        sys.exit(0)


if __name__ == "__main__":
    main()
