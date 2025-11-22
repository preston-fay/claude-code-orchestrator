"""
Governance engine for Orchestrator v2.

Central engine for enforcing quality gates and compliance.

See ADR-004 for governance architecture.
"""

from datetime import datetime
from typing import Any

from orchestrator_v2.engine.exceptions import GovernanceError
from orchestrator_v2.engine.state_models import (
    GateResult,
    GateStatus,
    GovernanceResults,
    PhaseType,
    ProjectState,
)
from orchestrator_v2.governance.policy_loader import PolicyLoader
from orchestrator_v2.governance.policy_models import (
    AuditEntry,
    GovernancePolicy,
)


class GovernanceEngine:
    """Central governance enforcement engine."""

    def __init__(self, policy_loader: PolicyLoader | None = None):
        """Initialize the governance engine."""
        self.policy_loader = policy_loader or PolicyLoader()
        self._policy: GovernancePolicy | None = None
        self._audit_log: list[AuditEntry] = []

    def load_policy(self, client: str) -> GovernancePolicy:
        """Load governance policy for a client."""
        self._policy = self.policy_loader.load_policies(client)
        return self._policy

    async def evaluate_phase_transition(
        self,
        project_state: ProjectState,
        phase: PhaseType,
        from_phase: PhaseType | None = None,
    ) -> GovernanceResults:
        """Evaluate governance gates for phase transition.

        Args:
            project_state: Current project state.
            phase: Phase to evaluate.
            from_phase: Previous phase (optional, for backward compatibility).

        Returns:
            Governance evaluation results.
        """
        if self._policy is None:
            self.load_policy(project_state.client)

        results = GovernanceResults()

        # Evaluate quality gates
        quality_results = await self._evaluate_quality_gates(phase, project_state)
        results.quality_gates.extend(quality_results)

        # Evaluate compliance
        compliance_results = await self._evaluate_compliance(project_state)
        results.compliance_checks.extend(compliance_results)

        # Determine overall status
        blocked = any(g.status == GateStatus.BLOCKED for g in results.quality_gates)
        results.passed = not blocked

        if blocked:
            results.failed_rules = [
                g.gate_id for g in results.quality_gates
                if g.status == GateStatus.BLOCKED
            ]

        # Log to audit trail
        self._log_governance_evaluation(phase, project_state, results)

        return results

    async def _evaluate_quality_gates(
        self,
        phase: PhaseType,
        state: ProjectState,
    ) -> list[GateResult]:
        """Evaluate quality gates for a phase."""
        results: list[GateResult] = []

        if self._policy is None:
            return results

        # Test coverage gate
        if phase in [PhaseType.DEVELOPMENT, PhaseType.QA]:
            coverage = state.metadata.get("test_coverage", 85)
            threshold = self._policy.quality_gates.min_test_coverage

            status = GateStatus.PASSED if coverage >= threshold else GateStatus.BLOCKED
            results.append(GateResult(
                gate_id="test_coverage",
                status=status,
                threshold=threshold,
                actual=coverage,
                message=f"Test coverage {coverage}% {'meets' if coverage >= threshold else 'below'} required {threshold}%",
            ))

        # Security scan gate
        if phase in [PhaseType.DEVELOPMENT, PhaseType.QA]:
            # Check if security scan artifact exists and has no FAIL
            security_passed = state.metadata.get("security_scan_passed", True)

            if self._policy.quality_gates.security_scan_required:
                status = GateStatus.PASSED if security_passed else GateStatus.BLOCKED
                results.append(GateResult(
                    gate_id="security_scan",
                    status=status,
                    threshold=0,
                    actual=0 if security_passed else 1,
                    message="Security scan " + ("passed" if security_passed else "FAILED - vulnerabilities found"),
                ))

        # Documentation gate
        if phase == PhaseType.DOCUMENTATION:
            has_docs = state.metadata.get("has_documentation", True)

            if self._policy.quality_gates.require_documentation:
                status = GateStatus.PASSED if has_docs else GateStatus.BLOCKED
                results.append(GateResult(
                    gate_id="documentation",
                    status=status,
                    threshold=1,
                    actual=1 if has_docs else 0,
                    message="Documentation " + ("present" if has_docs else "missing"),
                ))

        return results

    async def _evaluate_compliance(
        self,
        state: ProjectState,
    ) -> list[Any]:
        """Evaluate compliance requirements."""
        results = []

        if self._policy is None:
            return results

        # GDPR compliance check
        if self._policy.compliance.gdpr_enabled:
            pii_in_repo = state.metadata.get("pii_in_repo", False)
            if pii_in_repo:
                results.append({
                    "check": "gdpr_pii",
                    "status": "failed",
                    "message": "PII detected in repository",
                })

        return results

    def _log_governance_evaluation(
        self,
        phase: PhaseType,
        state: ProjectState,
        results: GovernanceResults,
    ) -> None:
        """Log governance evaluation to audit trail."""
        # Add to project state metadata
        if "governance_audit" not in state.metadata:
            state.metadata["governance_audit"] = []

        audit_record = {
            "timestamp": datetime.utcnow().isoformat(),
            "phase": phase.value,
            "passed": results.passed,
            "gates_evaluated": len(results.quality_gates),
            "gates_passed": sum(1 for g in results.quality_gates if g.status == GateStatus.PASSED),
            "gates_blocked": sum(1 for g in results.quality_gates if g.status == GateStatus.BLOCKED),
            "failed_rules": results.failed_rules,
        }
        state.metadata["governance_audit"].append(audit_record)

        # Also log to internal audit log
        for gate in results.quality_gates:
            self.audit_log(
                gate_id=gate.gate_id,
                phase=phase.value,
                result=gate,
                context={
                    "workflow_id": state.run_id,
                    "project_id": state.project_id,
                    "client": state.client,
                },
            )

    def get_constraints(
        self,
        phase: PhaseType,
        agent_id: str,
    ) -> dict[str, Any]:
        """Get governance constraints for agent."""
        if self._policy is None:
            return {}

        return {
            "quality_gates": self._policy.quality_gates.model_dump(),
            "brand_constraints": self._policy.brand_constraints.model_dump(),
        }

    def audit_log(
        self,
        gate_id: str,
        phase: str,
        result: GateResult,
        context: dict[str, Any],
    ) -> None:
        """Log governance decision for audit."""
        entry = AuditEntry(
            timestamp=datetime.utcnow().isoformat(),
            workflow_id=context.get("workflow_id", ""),
            phase=phase,
            gate_id=gate_id,
            evaluation={
                "status": result.status.value,
                "threshold": result.threshold,
                "actual": result.actual,
            },
            context=context,
        )
        self._audit_log.append(entry)

    def get_audit_trail(self, workflow_id: str) -> list[AuditEntry]:
        """Get audit trail for a workflow."""
        return [
            e for e in self._audit_log
            if e.workflow_id == workflow_id
        ]
