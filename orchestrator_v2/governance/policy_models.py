"""
Governance policy models for Orchestrator v2.

Defines the data structures for governance policies and gates.

See ADR-004 for governance architecture.
"""

from typing import Any

from pydantic import BaseModel, Field


class GateConfig(BaseModel):
    """Configuration for a quality gate."""
    id: str
    gate_type: str  # metric, tool, validator
    description: str = ""

    # Evaluation
    metric: str | None = None
    operator: str = ">="
    threshold: Any = None
    tool: str | None = None
    tool_args: list[str] = Field(default_factory=list)
    checks: list[dict[str, Any]] = Field(default_factory=list)

    # Applicability
    applies_to_phases: list[str] = Field(default_factory=list)
    applies_to_artifacts: list[str] = Field(default_factory=list)

    # Actions
    on_failure_action: str = "block"  # block, warn
    failure_message: str = ""
    remediation: str = ""


class Gate(BaseModel):
    """Quality gate definition."""
    config: GateConfig
    enabled: bool = True


class QualityGates(BaseModel):
    """Quality gate settings."""
    min_test_coverage: int = 70
    require_linting: bool = True
    max_complexity: int = 15
    require_documentation: bool = False
    security_scan_required: bool = False
    require_accessibility_audit: bool = False


class BrandConstraints(BaseModel):
    """Brand compliance constraints."""
    colors: list[str] = Field(default_factory=list)
    fonts: list[str] = Field(default_factory=list)
    forbidden_terms: list[str] = Field(default_factory=list)
    no_emojis: bool = True


class ComplianceConfig(BaseModel):
    """Compliance configuration."""
    gdpr: dict[str, Any] | None = None
    hipaa: dict[str, Any] | None = None
    soc2: dict[str, Any] | None = None


class DeploymentConfig(BaseModel):
    """Deployment configuration."""
    approval_required: bool = False
    deployment_windows: list[str] = Field(default_factory=list)


class NotificationConfig(BaseModel):
    """Notification configuration."""
    slack_webhook: str | None = None
    email: list[str] = Field(default_factory=list)


class GovernancePolicy(BaseModel):
    """Complete governance policy.

    See ADR-004 for policy hierarchy.
    """
    # Quality
    quality_gates: QualityGates = Field(default_factory=QualityGates)

    # Brand
    brand_constraints: BrandConstraints = Field(default_factory=BrandConstraints)

    # Compliance
    compliance: ComplianceConfig = Field(default_factory=ComplianceConfig)

    # Deployment
    deployment: DeploymentConfig = Field(default_factory=DeploymentConfig)

    # Notifications
    notifications: NotificationConfig = Field(default_factory=NotificationConfig)

    # Custom gates
    custom_gates: list[Gate] = Field(default_factory=list)


class AuditEntry(BaseModel):
    """Audit log entry for governance decisions."""
    timestamp: str
    workflow_id: str
    phase: str
    gate_id: str

    evaluation: dict[str, Any]
    context: dict[str, Any]
    remediation: dict[str, Any] | None = None
