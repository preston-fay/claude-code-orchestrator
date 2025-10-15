"""Type definitions for orchestrator run-loop."""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any
from datetime import datetime
from enum import Enum


class RunStatus(str, Enum):
    """Run status enumeration."""
    IDLE = "idle"
    RUNNING = "running"
    AWAITING_CONSENSUS = "awaiting_consensus"
    NEEDS_REVISION = "needs_revision"
    ABORTED = "aborted"
    COMPLETED = "completed"


class ValidationStatus(str, Enum):
    """Artifact validation status."""
    PASS = "pass"
    FAIL = "fail"
    PARTIAL = "partial"


@dataclass
class AgentOutcome:
    """Result from invoking a single agent."""
    agent_name: str
    success: bool
    artifacts: List[str] = field(default_factory=list)
    notes: str = ""
    errors: List[str] = field(default_factory=list)
    exit_code: Optional[int] = None
    execution_time: Optional[float] = None


@dataclass
class ValidationResult:
    """Result from checkpoint artifact validation."""
    status: ValidationStatus
    required: List[str]
    found: List[str]
    missing: List[str]
    validation_report_path: Optional[str] = None
    notes: str = ""


@dataclass
class PhaseOutcome:
    """Result from executing a complete phase."""
    phase_name: str
    success: bool
    agent_outcomes: List[AgentOutcome] = field(default_factory=list)
    validation: Optional[ValidationResult] = None
    requires_consensus: bool = False
    awaiting_consensus: bool = False
    completed_at: Optional[str] = None
    notes: str = ""


@dataclass
class RunState:
    """Complete orchestrator run state."""
    run_id: str
    status: RunStatus
    created_at: str
    updated_at: str
    current_phase: Optional[str] = None
    completed_phases: List[str] = field(default_factory=list)
    phase_artifacts: Dict[str, List[str]] = field(default_factory=dict)
    awaiting_consensus: bool = False
    consensus_phase: Optional[str] = None
    intake_path: Optional[str] = None
    intake_summary: Optional[Dict[str, Any]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "run_id": self.run_id,
            "status": self.status.value if isinstance(self.status, RunStatus) else self.status,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "current_phase": self.current_phase,
            "completed_phases": self.completed_phases,
            "phase_artifacts": self.phase_artifacts,
            "awaiting_consensus": self.awaiting_consensus,
            "consensus_phase": self.consensus_phase,
            "intake_path": self.intake_path,
            "intake_summary": self.intake_summary,
            "metadata": self.metadata,
            "errors": self.errors,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "RunState":
        """Deserialize from dictionary."""
        status = data.get("status", "idle")
        if isinstance(status, str):
            status = RunStatus(status)

        return cls(
            run_id=data.get("run_id", ""),
            status=status,
            created_at=data.get("created_at", ""),
            updated_at=data.get("updated_at", ""),
            current_phase=data.get("current_phase"),
            completed_phases=data.get("completed_phases", []),
            phase_artifacts=data.get("phase_artifacts", {}),
            awaiting_consensus=data.get("awaiting_consensus", False),
            consensus_phase=data.get("consensus_phase"),
            intake_path=data.get("intake_path"),
            intake_summary=data.get("intake_summary"),
            metadata=data.get("metadata", {}),
            errors=data.get("errors", []),
        )
