"""Constitution validator for Claude Code Orchestrator."""

from pathlib import Path
from typing import Dict, List, Optional


class ConstitutionError(Exception):
    """Raised when constitution validation fails."""
    pass


class ConstitutionViolation:
    """Represents a violation of the constitution."""

    def __init__(self, section: str, rule: str, severity: str, details: str):
        self.section = section
        self.rule = rule
        self.severity = severity  # "critical", "high", "medium", "low"
        self.details = details

    def __str__(self) -> str:
        return f"[{self.severity.upper()}] {self.section}: {self.rule} - {self.details}"


def validate_constitution(constitution_path: Optional[Path] = None) -> bool:
    """Validate that a constitution file exists and is well-formed.

    Args:
        constitution_path: Path to constitution.md (defaults to .claude/constitution.md)

    Returns:
        True if constitution exists and is valid

    Raises:
        ConstitutionError: If constitution is missing or invalid
    """
    if constitution_path is None:
        constitution_path = Path(".claude/constitution.md")

    if not constitution_path.exists():
        raise ConstitutionError(
            f"Constitution not found at {constitution_path}. "
            f"Run 'orchestrator constitution generate' to create one."
        )

    # Read constitution
    content = constitution_path.read_text()

    # Basic validation checks
    required_sections = [
        "# Project Constitution:",
        "## 🎯 Core Principles",
        "## 📐 Code Quality Standards",
        "## 🔒 Security & Privacy",
    ]

    missing_sections = []
    for section in required_sections:
        if section not in content:
            missing_sections.append(section)

    if missing_sections:
        raise ConstitutionError(
            f"Constitution is missing required sections: {', '.join(missing_sections)}"
        )

    # Check for minimal content
    if len(content) < 500:
        raise ConstitutionError("Constitution is too short - appears incomplete")

    return True


def check_code_against_constitution(
    code_files: List[Path],
    constitution_path: Optional[Path] = None,
) -> List[ConstitutionViolation]:
    """Check code files against constitution rules.

    This performs basic checks like:
    - Hardcoded credentials detection
    - Missing docstrings
    - Forbidden imports

    Args:
        code_files: List of Python files to check
        constitution_path: Path to constitution.md

    Returns:
        List of violations found
    """
    if constitution_path is None:
        constitution_path = Path(".claude/constitution.md")

    violations: List[ConstitutionViolation] = []

    # Load constitution
    if not constitution_path.exists():
        return violations

    constitution = constitution_path.read_text()

    # Check for forbidden practices mentioned in constitution
    forbidden_patterns = _extract_forbidden_patterns(constitution)

    for code_file in code_files:
        if not code_file.exists():
            continue

        code = code_file.read_text()

        # Check for hardcoded credentials
        if "password =" in code.lower() or "api_key =" in code.lower():
            if "No hardcoded credentials" in constitution:
                violations.append(
                    ConstitutionViolation(
                        section="Security",
                        rule="No hardcoded credentials",
                        severity="critical",
                        details=f"{code_file}: Appears to have hardcoded credentials",
                    )
                )

        # Check for missing docstrings (basic heuristic)
        if code.count("def ") > 0:
            # Count functions
            func_count = code.count("def ")
            docstring_count = code.count('"""') // 2  # Opening and closing

            if docstring_count < func_count * 0.5:  # Less than 50% have docstrings
                if "docstring" in constitution.lower():
                    violations.append(
                        ConstitutionViolation(
                            section="Code Quality",
                            rule="All functions must have docstrings",
                            severity="high",
                            details=f"{code_file}: Many functions missing docstrings ({docstring_count}/{func_count})",
                        )
                    )

        # Check for forbidden imports
        for pattern in forbidden_patterns:
            if pattern.lower() in code.lower():
                violations.append(
                    ConstitutionViolation(
                        section="Forbidden Practices",
                        rule=f"Forbidden: {pattern}",
                        severity="medium",
                        details=f"{code_file}: Contains forbidden pattern '{pattern}'",
                    )
                )

    return violations


def _extract_forbidden_patterns(constitution: str) -> List[str]:
    """Extract forbidden patterns from constitution.

    Looks for lines starting with ❌ in the Forbidden Practices section.
    """
    patterns = []
    in_forbidden_section = False

    for line in constitution.split("\n"):
        if "## 🚫 Forbidden Practices" in line:
            in_forbidden_section = True
            continue

        if in_forbidden_section and line.startswith("##"):
            # Next section, stop
            break

        if in_forbidden_section and line.strip().startswith("- ❌"):
            # Extract pattern (simplified)
            pattern = line.strip()[4:].split(":")[0].strip().replace("**", "")
            patterns.append(pattern)

    return patterns


def check_checkpoint_against_constitution(
    checkpoint: Dict,
    constitution_path: Optional[Path] = None,
) -> List[ConstitutionViolation]:
    """Check a checkpoint artifact against constitution requirements.

    Args:
        checkpoint: Checkpoint data (e.g., architecture decisions, test results)
        constitution_path: Path to constitution.md

    Returns:
        List of violations found
    """
    if constitution_path is None:
        constitution_path = Path(".claude/constitution.md")

    violations: List[ConstitutionViolation] = []

    if not constitution_path.exists():
        return violations

    constitution = constitution_path.read_text()

    # Check test coverage requirement
    if "test_coverage" in checkpoint:
        coverage = checkpoint["test_coverage"]

        # Extract coverage requirement from constitution
        if "coverage must be ≥80%" in constitution.lower():
            if coverage < 80:
                violations.append(
                    ConstitutionViolation(
                        section="Code Quality",
                        rule="Test coverage must be ≥80%",
                        severity="high",
                        details=f"Current coverage is {coverage}%, below required 80%",
                    )
                )

    # Check performance requirements
    if "performance_metrics" in checkpoint:
        metrics = checkpoint["performance_metrics"]

        # Check against performance standards in constitution
        if "response time <200ms" in constitution.lower():
            if metrics.get("avg_response_time", 0) > 200:
                violations.append(
                    ConstitutionViolation(
                        section="UX Performance",
                        rule="API response time <200ms (P95)",
                        severity="medium",
                        details=f"Average response time is {metrics['avg_response_time']}ms",
                    )
                )

    # Check documentation requirements
    if "documentation" in checkpoint:
        docs = checkpoint["documentation"]
        if "All functions must have docstrings" in constitution:
            if not docs.get("docstring_coverage", 100) >= 80:
                violations.append(
                    ConstitutionViolation(
                        section="Code Quality",
                        rule="All functions must have docstrings",
                        severity="medium",
                        details=f"Docstring coverage is {docs.get('docstring_coverage', 0)}%",
                    )
                )

    return violations
