"""Constitution generator for Claude Code Orchestrator."""

import datetime
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml


class ConstitutionGeneratorError(Exception):
    """Raised when constitution generation fails."""
    pass


@dataclass
class ConstitutionConfig:
    """Configuration for generating a project constitution."""

    project_name: str
    project_type: str  # webapp, ml, analytics, etc.
    mission_statement: str

    # Core principles
    values: List[Dict[str, str]] = field(default_factory=list)

    # Code quality
    code_quality_mandatory: List[str] = field(default_factory=list)
    code_quality_style: List[str] = field(default_factory=list)
    code_quality_testing: List[str] = field(default_factory=list)
    code_quality_documentation: List[str] = field(default_factory=list)

    # UX principles
    ux_design: List[str] = field(default_factory=list)
    ux_performance: List[str] = field(default_factory=list)
    ux_accessibility: List[str] = field(default_factory=list)

    # Security
    security_standards: List[str] = field(default_factory=list)
    security_privacy: List[str] = field(default_factory=list)
    security_secrets: List[str] = field(default_factory=list)

    # Data principles
    data_quality: List[str] = field(default_factory=list)
    data_governance: List[str] = field(default_factory=list)
    data_privacy: List[str] = field(default_factory=list)

    # Forbidden practices
    forbidden_practices: List[Dict[str, str]] = field(default_factory=list)
    forbidden_technologies: List[str] = field(default_factory=list)
    forbidden_antipatterns: List[Dict[str, str]] = field(default_factory=list)

    # Required practices
    required_practices: List[Dict[str, str]] = field(default_factory=list)
    required_technologies: List[Dict[str, str]] = field(default_factory=list)

    # Kearney standards
    raise_compliance: bool = True
    brand_requirements: List[str] = field(default_factory=list)
    client_requirements: List[str] = field(default_factory=list)

    # Phase-specific guidelines
    planning_guidelines: List[str] = field(default_factory=list)
    data_engineering_guidelines: List[str] = field(default_factory=list)
    development_guidelines: List[str] = field(default_factory=list)
    qa_guidelines: List[str] = field(default_factory=list)
    documentation_guidelines: List[str] = field(default_factory=list)

    # Metadata
    version: str = "1.0.0"
    client_name: Optional[str] = None
    approved_by: Optional[str] = None

    @classmethod
    def from_intake(cls, intake: Dict[str, Any]) -> "ConstitutionConfig":
        """Create ConstitutionConfig from intake.yaml."""
        project = intake["project"]
        goals = intake.get("goals", {})

        # Extract mission from goals
        mission = goals.get("primary", [""])[0] if goals.get("primary") else "Build high-quality software"

        # Create basic config
        config = cls(
            project_name=project["name"],
            project_type=project["type"],
            mission_statement=mission,
        )

        # Add constitution section if it exists
        if "constitution" in intake:
            const = intake["constitution"]
            config.code_quality_mandatory = const.get("code_quality", [])
            config.ux_design = const.get("ux_principles", [])
            config.security_standards = const.get("security", [])
            config.data_quality = const.get("data_quality", [])
            config.forbidden_practices = [
                {"practice": p, "reason": "Specified in intake"}
                for p in const.get("forbidden", [])
            ]

        # Add defaults based on project type
        config._add_defaults_by_type()

        # Add Kearney brand requirements
        config._add_kearney_defaults()

        return config

    def _add_defaults_by_type(self):
        """Add default constitution items based on project type."""
        # Common defaults for all projects
        if not self.code_quality_mandatory:
            self.code_quality_mandatory = [
                "All functions must have docstrings",
                f"Test coverage must be ≥80%",
                "All code must pass linting with zero errors",
                "No hardcoded credentials or secrets",
            ]

        if not self.security_standards:
            self.security_standards = [
                "All API endpoints must require authentication",
                "All database connections must use SSL/TLS",
                "Use secrets manager for all credentials",
            ]

        # Project-type specific defaults
        if self.project_type == "ml":
            self._add_ml_defaults()
        elif self.project_type == "analytics":
            self._add_analytics_defaults()
        elif self.project_type == "webapp":
            self._add_webapp_defaults()

    def _add_ml_defaults(self):
        """Add ML-specific constitution defaults."""
        if not self.data_quality:
            self.data_quality = [
                "Missing value rate must be <5% per feature",
                "All data quality metrics tracked in MLflow/DVC",
                "Training/test split must be stratified (no data leakage)",
            ]

        if not self.forbidden_practices:
            self.forbidden_practices = [
                {
                    "practice": "Train/test split without time stratification",
                    "reason": "Causes data leakage and overoptimistic metrics",
                },
                {
                    "practice": "Cherry-picking metrics",
                    "reason": "Report all standard metrics (accuracy, precision, recall, F1, AUC-ROC)",
                },
                {
                    "practice": "Deploying models without explainability",
                    "reason": "SHAP values required for all predictions",
                },
            ]

        if not self.required_practices:
            self.required_practices = [
                {
                    "practice": "Version all experiments",
                    "reason": "Use MLflow for tracking all training runs",
                },
                {
                    "practice": "Monitor drift",
                    "reason": "Implement data drift and model drift detection",
                },
            ]

    def _add_analytics_defaults(self):
        """Add analytics-specific constitution defaults."""
        if not self.data_quality:
            self.data_quality = [
                "Data quality metrics must be >95%",
                "All ETL pipelines must have data validation checks",
                "All data sources must have documented lineage",
            ]

        if not self.ux_performance:
            self.ux_performance = [
                "Dashboard queries must complete in <500ms",
                "ETL pipeline must process data within SLA",
            ]

    def _add_webapp_defaults(self):
        """Add webapp-specific constitution defaults."""
        if not self.ux_performance:
            self.ux_performance = [
                "Page load time <2 seconds",
                "Time to Interactive (TTI) <3 seconds",
                "API response time <200ms (P95)",
            ]

        if not self.ux_accessibility:
            self.ux_accessibility = [
                "Must meet WCAG 2.1 AA standards",
                "All interactive elements must be keyboard accessible",
                "All images must have alt text",
            ]

    def _add_kearney_defaults(self):
        """Add Kearney-specific requirements."""
        if not self.brand_requirements:
            self.brand_requirements = [
                "All charts use Kearney 6-color palette (primary: #7823DC)",
                "All fonts use Inter typeface",
                "All deliverables follow KDS (Kearney Design System)",
            ]

        if not self.ux_design:
            self.ux_design = [
                "All visualizations must use Kearney Design System colors",
                "All dashboards must be C-suite presentable (RAISE framework)",
            ]


def generate_constitution(
    config: ConstitutionConfig,
    output_path: Optional[Path] = None,
) -> str:
    """Generate a constitution markdown file from config.

    Args:
        config: Constitution configuration
        output_path: Where to write constitution (defaults to .claude/constitution.md)

    Returns:
        Generated constitution as markdown string

    Raises:
        ConstitutionGeneratorError: If generation fails
    """
    if output_path is None:
        output_path = Path(".claude/constitution.md")

    # Generate markdown
    md = _render_constitution(config)

    # Write to file
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(md)

    return md


def _render_constitution(config: ConstitutionConfig) -> str:
    """Render constitution to markdown."""
    today = datetime.date.today().isoformat()

    md = f"""# Project Constitution: {config.project_name}

> **Purpose:** This constitution establishes the fundamental principles, standards, and guardrails for the {config.project_name} project. All agents, code, and artifacts must adhere to these principles.

**Version:** {config.version}
**Project Type:** {config.project_type}
**Created:** {today}
**Last Updated:** {today}

---

## 🎯 Core Principles

### Mission Statement
{config.mission_statement}

### Values
"""

    if config.values:
        for value in config.values:
            md += f"- **{value['name']}**: {value['description']}\n"
    else:
        md += "- **Quality**: Deliver high-quality, maintainable code\n"
        md += "- **Security**: Protect user data and system integrity\n"
        md += "- **Performance**: Build fast, efficient systems\n"

    md += "\n---\n\n"

    # Code Quality
    md += "## 📐 Code Quality Standards\n\n"
    md += "### Mandatory Requirements\n"
    for req in config.code_quality_mandatory:
        md += f"- {req}\n"

    if config.code_quality_style:
        md += "\n### Code Style\n"
        for style in config.code_quality_style:
            md += f"- {style}\n"

    if config.code_quality_testing:
        md += "\n### Testing Requirements\n"
        for test in config.code_quality_testing:
            md += f"- {test}\n"

    if config.code_quality_documentation:
        md += "\n### Documentation Requirements\n"
        for doc in config.code_quality_documentation:
            md += f"- {doc}\n"

    md += "\n---\n\n"

    # UX Principles
    md += "## 🎨 User Experience (UX) Principles\n\n"
    if config.ux_design:
        md += "### Design Consistency\n"
        for design in config.ux_design:
            md += f"- {design}\n"
        md += "\n"

    if config.ux_performance:
        md += "### Performance Standards\n"
        for perf in config.ux_performance:
            md += f"- {perf}\n"
        md += "\n"

    if config.ux_accessibility:
        md += "### Accessibility\n"
        for acc in config.ux_accessibility:
            md += f"- {acc}\n"
        md += "\n"

    md += "---\n\n"

    # Security & Privacy
    md += "## 🔒 Security & Privacy\n\n"
    md += "### Security Standards\n"
    for sec in config.security_standards:
        md += f"- {sec}\n"

    if config.security_privacy:
        md += "\n### Privacy Requirements\n"
        for priv in config.security_privacy:
            md += f"- {priv}\n"

    if config.security_secrets:
        md += "\n### Secrets Management\n"
        for secret in config.security_secrets:
            md += f"- {secret}\n"

    md += "\n---\n\n"

    # Data Principles
    if config.data_quality or config.data_governance or config.data_privacy:
        md += "## 📊 Data Principles\n\n"

        if config.data_quality:
            md += "### Data Quality\n"
            for qual in config.data_quality:
                md += f"- {qual}\n"
            md += "\n"

        if config.data_governance:
            md += "### Data Governance\n"
            for gov in config.data_governance:
                md += f"- {gov}\n"
            md += "\n"

        if config.data_privacy:
            md += "### Data Privacy\n"
            for priv in config.data_privacy:
                md += f"- {priv}\n"
            md += "\n"

        md += "---\n\n"

    # Forbidden Practices
    if config.forbidden_practices or config.forbidden_technologies or config.forbidden_antipatterns:
        md += "## 🚫 Forbidden Practices\n\n"

        if config.forbidden_practices:
            md += "### Never Do This\n"
            for practice in config.forbidden_practices:
                md += f"- ❌ **{practice['practice']}**: {practice['reason']}\n"
            md += "\n"

        if config.forbidden_technologies:
            md += "### Technologies to Avoid\n"
            for tech in config.forbidden_technologies:
                md += f"- ❌ {tech}\n"
            md += "\n"

        if config.forbidden_antipatterns:
            md += "### Anti-Patterns\n"
            for pattern in config.forbidden_antipatterns:
                md += f"- ❌ **{pattern['pattern']}**: {pattern['why']}\n"
            md += "\n"

        md += "---\n\n"

    # Required Practices
    if config.required_practices or config.required_technologies:
        md += "## ✅ Required Practices\n\n"

        if config.required_practices:
            md += "### Always Do This\n"
            for practice in config.required_practices:
                md += f"- ✅ **{practice['practice']}**: {practice['reason']}\n"
            md += "\n"

        if config.required_technologies:
            md += "### Technology Standards\n"
            for tech in config.required_technologies:
                md += f"- ✅ **{tech['name']}**: {tech['rationale']}\n"
            md += "\n"

        md += "---\n\n"

    # Kearney Standards
    md += "## 🎓 Kearney Standards\n\n"
    if config.raise_compliance:
        md += """### RAISE Framework Compliance
This project must adhere to Kearney's RAISE framework:
- **R**igorous: Evidence-based decisions, validated assumptions
- **A**ctionable: Deliverables drive concrete business actions
- **I**nsightful: Deep understanding beyond surface observations
- **S**tructured: Clear methodology, reproducible analysis
- **E**ngaging: Compelling storytelling for C-suite audiences

"""

    if config.brand_requirements:
        md += "### Brand Compliance\n"
        for req in config.brand_requirements:
            md += f"- {req}\n"
        md += "\n"

    if config.client_requirements:
        md += "### Client-Specific Requirements\n"
        for req in config.client_requirements:
            md += f"- {req}\n"
        md += "\n"

    md += "---\n\n"

    # Phase-Specific Guidelines
    if any([
        config.planning_guidelines,
        config.data_engineering_guidelines,
        config.development_guidelines,
        config.qa_guidelines,
        config.documentation_guidelines,
    ]):
        md += "## 📋 Phase-Specific Guidelines\n\n"

        if config.planning_guidelines:
            md += "### Planning Phase\n"
            for guide in config.planning_guidelines:
                md += f"- {guide}\n"
            md += "\n"

        if config.data_engineering_guidelines:
            md += "### Data Engineering Phase\n"
            for guide in config.data_engineering_guidelines:
                md += f"- {guide}\n"
            md += "\n"

        if config.development_guidelines:
            md += "### Development Phase\n"
            for guide in config.development_guidelines:
                md += f"- {guide}\n"
            md += "\n"

        if config.qa_guidelines:
            md += "### QA Phase\n"
            for guide in config.qa_guidelines:
                md += f"- {guide}\n"
            md += "\n"

        if config.documentation_guidelines:
            md += "### Documentation Phase\n"
            for guide in config.documentation_guidelines:
                md += f"- {guide}\n"
            md += "\n"

        md += "---\n\n"

    # Footer
    md += """## 📚 References

### Related Documents
- Project Intake: `intake/{project_name}.intake.yaml`
- Client Governance: `clients/{client_name}/governance.yaml`
- Architecture Decisions: `.claude/decisions/`
- Knowledge Base: `.claude/knowledge/`

---

**Enforcement:** This constitution is enforced through:
- Preflight checks (orchestrator blocks execution if violated)
- QA agent validation (constitution compliance testing)
- CI/CD gates (automated linting and checks)
- Code review (Reviewer agent checks adherence)

**Status:** Draft
""".format(project_name=config.project_name, client_name=config.client_name or "default")

    if config.approved_by:
        md += f"**Approved By:** {config.approved_by}\n"
        md += f"**Approval Date:** {today}\n"

    return md
