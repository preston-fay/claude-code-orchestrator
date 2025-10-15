"""Pre-release quality gates: tests, hygiene, security checks."""

import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum
import json


class GateStatus(str, Enum):
    """Quality gate status."""

    PASS = "pass"
    WARN = "warn"
    FAIL = "fail"
    SKIP = "skip"


@dataclass
class GateResult:
    """Result of a quality gate check."""

    gate_name: str
    status: GateStatus
    message: str
    details: Dict[str, Any] = field(default_factory=dict)
    blocking: bool = True  # If True, FAIL prevents release

    @property
    def passed(self) -> bool:
        """Check if gate passed (PASS or WARN)."""
        return self.status in (GateStatus.PASS, GateStatus.WARN, GateStatus.SKIP)


@dataclass
class GatesReport:
    """Aggregated quality gates report."""

    gates: List[GateResult]
    timestamp: str
    blocking_failures: int = 0
    warnings: int = 0

    @property
    def all_passed(self) -> bool:
        """Check if all blocking gates passed."""
        return self.blocking_failures == 0

    @property
    def summary(self) -> str:
        """Get summary status."""
        if self.blocking_failures > 0:
            return f"❌ {self.blocking_failures} blocking failure(s)"
        elif self.warnings > 0:
            return f"⚠️ {self.warnings} warning(s)"
        else:
            return "✅ All gates passed"


def run_tests_gate(project_root: Path) -> GateResult:
    """
    Run test suite.

    Args:
        project_root: Project root directory

    Returns:
        GateResult with test execution status
    """
    try:
        # Run pytest
        result = subprocess.run(
            ["pytest", "tests/", "-v", "--tb=short"],
            cwd=project_root,
            capture_output=True,
            text=True,
            timeout=300,  # 5 minute timeout
        )

        if result.returncode == 0:
            # Count tests from output
            passed_match = result.stdout.count(" PASSED")
            return GateResult(
                gate_name="tests",
                status=GateStatus.PASS,
                message=f"All tests passed ({passed_match} tests)",
                details={"passed": passed_match, "exit_code": 0},
                blocking=True,
            )
        elif result.returncode == 5:
            # No tests collected
            return GateResult(
                gate_name="tests",
                status=GateStatus.WARN,
                message="No tests found",
                details={"exit_code": 5},
                blocking=False,
            )
        else:
            # Tests failed
            failed_count = result.stdout.count(" FAILED")
            return GateResult(
                gate_name="tests",
                status=GateStatus.FAIL,
                message=f"Tests failed ({failed_count} failures)",
                details={"failed": failed_count, "exit_code": result.returncode, "stderr": result.stderr[:500]},
                blocking=True,
            )

    except subprocess.TimeoutExpired:
        return GateResult(
            gate_name="tests",
            status=GateStatus.FAIL,
            message="Test suite timed out after 5 minutes",
            blocking=True,
        )
    except FileNotFoundError:
        return GateResult(
            gate_name="tests",
            status=GateStatus.SKIP,
            message="pytest not found, skipping tests",
            blocking=False,
        )
    except Exception as e:
        return GateResult(
            gate_name="tests",
            status=GateStatus.FAIL,
            message=f"Test execution error: {e}",
            blocking=True,
        )


def run_hygiene_gate(project_root: Path, min_score: int = 85) -> GateResult:
    """
    Check repository hygiene score.

    Args:
        project_root: Project root directory
        min_score: Minimum acceptable cleanliness score

    Returns:
        GateResult with hygiene check status
    """
    hygiene_summary = project_root / "reports" / "hygiene_summary.json"

    if not hygiene_summary.exists():
        return GateResult(
            gate_name="hygiene",
            status=GateStatus.WARN,
            message="Hygiene report not found (run 'orchestrator run repo-hygiene')",
            blocking=False,
        )

    try:
        with open(hygiene_summary) as f:
            data = json.load(f)

        score = data.get("cleanliness_score", 0)
        grade = data.get("grade", "F")

        if score >= min_score:
            return GateResult(
                gate_name="hygiene",
                status=GateStatus.PASS,
                message=f"Cleanliness score: {score}/100 (Grade: {grade})",
                details={"score": score, "grade": grade},
                blocking=False,
            )
        elif score >= min_score - 10:
            return GateResult(
                gate_name="hygiene",
                status=GateStatus.WARN,
                message=f"Cleanliness score below target: {score}/100 (min: {min_score})",
                details={"score": score, "grade": grade},
                blocking=False,
            )
        else:
            return GateResult(
                gate_name="hygiene",
                status=GateStatus.FAIL,
                message=f"Cleanliness score too low: {score}/100 (min: {min_score})",
                details={"score": score, "grade": grade},
                blocking=True,
            )

    except (json.JSONDecodeError, KeyError, ValueError) as e:
        return GateResult(
            gate_name="hygiene",
            status=GateStatus.WARN,
            message=f"Could not parse hygiene report: {e}",
            blocking=False,
        )


def run_security_gate(project_root: Path) -> GateResult:
    """
    Run security checks (bandit for Python).

    Args:
        project_root: Project root directory

    Returns:
        GateResult with security scan status
    """
    try:
        # Run bandit security scanner
        result = subprocess.run(
            ["bandit", "-r", "src/", "-f", "json", "-q"],
            cwd=project_root,
            capture_output=True,
            text=True,
            timeout=120,
        )

        if result.returncode == 0:
            return GateResult(
                gate_name="security",
                status=GateStatus.PASS,
                message="No security issues found",
                blocking=True,
            )
        else:
            # Parse bandit JSON output
            try:
                report = json.loads(result.stdout)
                high = len([r for r in report.get("results", []) if r.get("issue_severity") == "HIGH"])
                medium = len([r for r in report.get("results", []) if r.get("issue_severity") == "MEDIUM"])

                if high > 0:
                    return GateResult(
                        gate_name="security",
                        status=GateStatus.FAIL,
                        message=f"Security issues found: {high} high, {medium} medium",
                        details={"high": high, "medium": medium},
                        blocking=True,
                    )
                elif medium > 0:
                    return GateResult(
                        gate_name="security",
                        status=GateStatus.WARN,
                        message=f"Security warnings: {medium} medium severity",
                        details={"high": 0, "medium": medium},
                        blocking=False,
                    )
            except json.JSONDecodeError:
                pass

            return GateResult(
                gate_name="security",
                status=GateStatus.WARN,
                message="Could not parse security scan results",
                blocking=False,
            )

    except FileNotFoundError:
        return GateResult(
            gate_name="security",
            status=GateStatus.SKIP,
            message="bandit not installed, skipping security scan (install: pip install bandit)",
            blocking=False,
        )
    except subprocess.TimeoutExpired:
        return GateResult(
            gate_name="security",
            status=GateStatus.WARN,
            message="Security scan timed out",
            blocking=False,
        )
    except Exception as e:
        return GateResult(
            gate_name="security",
            status=GateStatus.WARN,
            message=f"Security scan error: {e}",
            blocking=False,
        )


def run_git_status_gate(project_root: Path) -> GateResult:
    """
    Check git working tree status.

    Args:
        project_root: Project root directory

    Returns:
        GateResult indicating if working tree is clean
    """
    try:
        # Check for uncommitted changes
        result = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=project_root,
            capture_output=True,
            text=True,
            check=True,
        )

        if result.stdout.strip():
            # Has uncommitted changes
            lines = result.stdout.strip().split("\n")
            return GateResult(
                gate_name="git_status",
                status=GateStatus.FAIL,
                message=f"Working tree has {len(lines)} uncommitted change(s)",
                details={"uncommitted_files": len(lines)},
                blocking=True,
            )
        else:
            return GateResult(
                gate_name="git_status",
                status=GateStatus.PASS,
                message="Working tree is clean",
                blocking=True,
            )

    except subprocess.CalledProcessError as e:
        return GateResult(
            gate_name="git_status",
            status=GateStatus.WARN,
            message=f"Could not check git status: {e}",
            blocking=False,
        )


def run_build_gate(project_root: Path) -> GateResult:
    """
    Verify package can be built.

    Args:
        project_root: Project root directory

    Returns:
        GateResult indicating if build succeeds
    """
    try:
        # Try building with python -m build (if available)
        result = subprocess.run(
            ["python", "-m", "build", "--wheel", "--outdir", "dist/"],
            cwd=project_root,
            capture_output=True,
            text=True,
            timeout=120,
        )

        if result.returncode == 0:
            return GateResult(
                gate_name="build",
                status=GateStatus.PASS,
                message="Package built successfully",
                blocking=True,
            )
        else:
            return GateResult(
                gate_name="build",
                status=GateStatus.FAIL,
                message=f"Build failed: {result.stderr[:200]}",
                blocking=True,
            )

    except FileNotFoundError:
        # Build module not available
        return GateResult(
            gate_name="build",
            status=GateStatus.SKIP,
            message="build module not found (install: pip install build)",
            blocking=False,
        )
    except subprocess.TimeoutExpired:
        return GateResult(
            gate_name="build",
            status=GateStatus.FAIL,
            message="Build timed out after 2 minutes",
            blocking=True,
        )


def run_all_gates(
    project_root: Path,
    skip_gates: Optional[List[str]] = None,
    min_hygiene_score: int = 85,
) -> GatesReport:
    """
    Run all quality gates.

    Args:
        project_root: Project root directory
        skip_gates: List of gate names to skip
        min_hygiene_score: Minimum hygiene score

    Returns:
        GatesReport with all gate results
    """
    from datetime import datetime

    if skip_gates is None:
        skip_gates = []

    gates = []

    # Run each gate
    gate_functions = {
        "git_status": lambda: run_git_status_gate(project_root),
        "tests": lambda: run_tests_gate(project_root),
        "hygiene": lambda: run_hygiene_gate(project_root, min_hygiene_score),
        "security": lambda: run_security_gate(project_root),
        "build": lambda: run_build_gate(project_root),
    }

    for gate_name, gate_func in gate_functions.items():
        if gate_name in skip_gates:
            gates.append(
                GateResult(
                    gate_name=gate_name,
                    status=GateStatus.SKIP,
                    message="Skipped by user",
                    blocking=False,
                )
            )
        else:
            gates.append(gate_func())

    # Count failures and warnings
    blocking_failures = sum(1 for g in gates if g.status == GateStatus.FAIL and g.blocking)
    warnings = sum(1 for g in gates if g.status == GateStatus.WARN)

    return GatesReport(
        gates=gates,
        timestamp=datetime.now().isoformat(),
        blocking_failures=blocking_failures,
        warnings=warnings,
    )


def save_gates_report(report: GatesReport, project_root: Path) -> Path:
    """
    Save gates report to JSON file.

    Args:
        report: GatesReport to save
        project_root: Project root directory

    Returns:
        Path to saved report
    """
    gates_dir = project_root / ".claude" / "release"
    gates_dir.mkdir(parents=True, exist_ok=True)

    report_path = gates_dir / f"gates_report_{report.timestamp.replace(':', '-')}.json"

    data = {
        "timestamp": report.timestamp,
        "summary": report.summary,
        "all_passed": report.all_passed,
        "blocking_failures": report.blocking_failures,
        "warnings": report.warnings,
        "gates": [
            {
                "name": g.gate_name,
                "status": g.status.value,
                "message": g.message,
                "details": g.details,
                "blocking": g.blocking,
            }
            for g in report.gates
        ],
    }

    with open(report_path, "w") as f:
        json.dump(data, f, indent=2)

    return report_path
