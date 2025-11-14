"""Phase transition and advancement logic."""

import yaml
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime

from ..types import RunStatus, PhaseOutcome, AgentOutcome, ValidationResult, ValidationStatus


class PhaseTransitionMixin:
    """Mixin providing phase navigation and consensus logic."""

    def _load_intake(self, intake_path: Path) -> Dict[str, Any]:
        """
        Load intake configuration from YAML.

        Args:
            intake_path: Path to intake YAML file

        Returns:
            Dictionary with intake summary
        """
        if not intake_path.exists():
            raise FileNotFoundError(f"Intake file not found: {intake_path}")

        with open(intake_path) as f:
            intake = yaml.safe_load(f)

        # Extract summary
        return {
            "project_name": intake.get("project", {}).get("name", "Unknown"),
            "project_type": intake.get("project", {}).get("type", "Unknown"),
            "description": intake.get("project", {}).get("description", ""),
            "requirements": intake.get("requirements", []),
        }

    def _get_first_enabled_phase(self) -> Optional[str]:
        """
        Get first enabled phase from config.

        Returns:
            Name of first enabled phase, or None if no phases are enabled
        """
        phases = self.config.get("workflow", {}).get("phases", {})

        for phase_name, phase_config in phases.items():
            if phase_config.get("enabled", True):
                return phase_name

        return None

    def _get_next_phase(self, current_phase: str) -> Optional[str]:
        """
        Get next enabled phase after current_phase.

        Args:
            current_phase: Name of current phase

        Returns:
            Name of next enabled phase, or None if at end
        """
        phases = self.config.get("workflow", {}).get("phases", {})
        phase_names = list(phases.keys())

        try:
            current_idx = phase_names.index(current_phase)
        except ValueError:
            return None

        # Find next enabled phase
        for idx in range(current_idx + 1, len(phase_names)):
            phase_name = phase_names[idx]
            if phases[phase_name].get("enabled", True):
                return phase_name

        return None

    def _get_previous_phase(self, current_phase: str) -> Optional[str]:
        """
        Get previous enabled phase before current_phase.

        Args:
            current_phase: Name of current phase

        Returns:
            Name of previous enabled phase, or None if at beginning
        """
        phases = self.config.get("workflow", {}).get("phases", {})
        phase_names = list(phases.keys())

        try:
            current_idx = phase_names.index(current_phase)
        except ValueError:
            return None

        # Find previous enabled phase (going backwards)
        for idx in range(current_idx - 1, -1, -1):
            phase_name = phase_names[idx]
            if phases[phase_name].get("enabled", True):
                return phase_name

        return None

    def next_phase(
        self,
        force_parallel: bool = False,
        max_workers: Optional[int] = None,
        timeout_override: Optional[int] = None,
    ) -> PhaseOutcome:
        """
        Execute the next phase in the workflow.

        Args:
            force_parallel: Force parallel execution (only for parallel-enabled phases)
            max_workers: Maximum concurrent workers (capped by config limit)
            timeout_override: Timeout in seconds (overrides config)

        Returns:
            PhaseOutcome with execution results
        """
        if self.state.status == RunStatus.IDLE:
            raise RuntimeError("No active run. Start a run first with start_run()")

        if self.state.status == RunStatus.AWAITING_CONSENSUS:
            raise RuntimeError(
                f"Run is awaiting consensus on phase: {self.state.consensus_phase}. "
                "Approve or reject before continuing."
            )

        if self.state.status == RunStatus.COMPLETED:
            raise RuntimeError("Run already completed")

        if not self.state.current_phase:
            raise RuntimeError("No current phase set")

        # Execute current phase
        outcome = self.run_phase(
            self.state.current_phase,
            force_parallel=force_parallel,
            max_workers=max_workers,
            timeout_override=timeout_override,
        )

        # Handle outcome
        if outcome.awaiting_consensus:
            self.state.status = RunStatus.AWAITING_CONSENSUS
            self.state.consensus_phase = outcome.phase_name
            self._save_state()
            self._log(f"Phase {outcome.phase_name} requires consensus")
            return outcome

        if outcome.success:
            # Mark phase as completed
            self.state.completed_phases.append(outcome.phase_name)

            # Store artifacts
            if outcome.validation and outcome.validation.found:
                self.state.phase_artifacts[outcome.phase_name] = outcome.validation.found

            # Move to next phase
            next_phase = self._get_next_phase(self.state.current_phase)

            if next_phase:
                self.state.current_phase = next_phase
                self._save_state()
                self._log(f"Advanced to phase: {next_phase}")
            else:
                # No more phases - mark as completed
                self.state.status = RunStatus.COMPLETED
                self.state.current_phase = None
                self._save_state()
                self._log("Run completed successfully")

        else:
            # Phase failed
            self.state.status = RunStatus.NEEDS_REVISION
            self._save_state()
            self._log(f"Phase {outcome.phase_name} failed", level="error")

        return outcome

    def approve_consensus(self) -> None:
        """Approve consensus and advance to next phase."""
        if not self.state.awaiting_consensus:
            raise RuntimeError("No consensus awaiting approval")

        phase_name = self.state.consensus_phase

        # Record decision
        self._record_consensus_decision(phase_name, approved=True, reason="")

        # Mark phase as completed
        if phase_name not in self.state.completed_phases:
            self.state.completed_phases.append(phase_name)

        # Clear consensus state
        self.state.awaiting_consensus = False
        self.state.consensus_phase = None

        # Advance to next phase
        next_phase = self._get_next_phase(phase_name)

        if next_phase:
            self.state.current_phase = next_phase
            self.state.status = RunStatus.RUNNING
            self._log(f"Consensus approved. Advanced to phase: {next_phase}")
        else:
            # No more phases
            self.state.status = RunStatus.COMPLETED
            self.state.current_phase = None
            self._log("Consensus approved. Run completed.")

        self._save_state()

    def reject_consensus(self, reason: str) -> None:
        """
        Reject consensus and mark for revision.

        Args:
            reason: Reason for rejection
        """
        if not self.state.awaiting_consensus:
            raise RuntimeError("No consensus awaiting decision")

        phase_name = self.state.consensus_phase

        # Record decision
        self._record_consensus_decision(phase_name, approved=False, reason=reason)

        # Clear consensus state but mark as needing revision
        self.state.awaiting_consensus = False
        self.state.consensus_phase = None
        self.state.status = RunStatus.NEEDS_REVISION

        self._log(f"Consensus rejected for phase: {phase_name}. Reason: {reason}")
        self._save_state()

    def _record_consensus_decision(
        self, phase_name: str, approved: bool, reason: str
    ) -> None:
        """
        Record consensus decision to file.

        Args:
            phase_name: Phase name
            approved: Whether consensus was approved
            reason: Reason for decision (for rejections)
        """
        consensus_dir = self.project_root / ".claude" / "consensus"
        consensus_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        decision_path = consensus_dir / f"DECISION_{timestamp}.md"

        with open(decision_path, "w") as f:
            f.write(f"# Consensus Decision: {phase_name}\n\n")
            f.write(f"**Decided:** {datetime.now().isoformat()}\n\n")
            f.write(f"**Run ID:** {self.state.run_id}\n\n")
            f.write(f"**Decision:** {'✅ APPROVED' if approved else '❌ REJECTED'}\n\n")

            if reason:
                f.write(f"**Reason:** {reason}\n\n")

            f.write("---\n")
            f.write("*Generated by Orchestrator Run-Loop*\n")

    def abort_run(self) -> None:
        """Abort the current run."""
        if self.state.status == RunStatus.IDLE:
            raise RuntimeError("No active run to abort")

        self.state.status = RunStatus.ABORTED
        self._log("Run aborted by user")
        self._save_state()

    def resume_run(self) -> None:
        """Resume an aborted or paused run."""
        if self.state.status not in (RunStatus.ABORTED, RunStatus.NEEDS_REVISION):
            raise RuntimeError(f"Cannot resume from status: {self.state.status}")

        self.state.status = RunStatus.RUNNING
        self._log("Run resumed")
        self._save_state()

    def jump_to_phase(self, phase_name: str) -> None:
        """
        Jump to a specific phase (admin/debug mode).

        Args:
            phase_name: Target phase name (must be enabled)
        """
        phases = self.config.get("workflow", {}).get("phases", {})

        if phase_name not in phases:
            raise ValueError(f"Phase not found: {phase_name}")

        if not phases[phase_name].get("enabled", True):
            raise ValueError(f"Phase not enabled: {phase_name}")

        self.state.current_phase = phase_name
        self.state.status = RunStatus.RUNNING
        self._log(f"Jumped to phase: {phase_name} (admin mode)")
        self._save_state()
