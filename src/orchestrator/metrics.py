"""Runtime metrics tracking and persistence."""

import json
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime
from dataclasses import dataclass, field


@dataclass
class PhaseMetrics:
    """Metrics for a single phase execution."""

    phase_name: str
    start_ts: str
    end_ts: Optional[str] = None
    duration_s: float = 0.0
    agent_runtimes: Dict[str, float] = field(default_factory=dict)
    agent_exit_codes: Dict[str, int] = field(default_factory=dict)
    agent_retries: Dict[str, int] = field(default_factory=dict)
    validation_status: Optional[str] = None
    artifacts_count: int = 0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "phase_name": self.phase_name,
            "start_ts": self.start_ts,
            "end_ts": self.end_ts,
            "duration_s": self.duration_s,
            "agent_runtimes": self.agent_runtimes,
            "agent_exit_codes": self.agent_exit_codes,
            "agent_retries": self.agent_retries,
            "validation_status": self.validation_status,
            "artifacts_count": self.artifacts_count,
        }


@dataclass
class RunMetrics:
    """Metrics for entire orchestrator run."""

    run_id: str
    start_ts: str
    end_ts: Optional[str] = None
    duration_s: float = 0.0
    phases: Dict[str, PhaseMetrics] = field(default_factory=dict)
    total_retries: int = 0
    cleanliness_score: Optional[float] = None
    status: str = "running"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "run_id": self.run_id,
            "start_ts": self.start_ts,
            "end_ts": self.end_ts,
            "duration_s": self.duration_s,
            "phases": {name: metrics.to_dict() for name, metrics in self.phases.items()},
            "total_retries": self.total_retries,
            "cleanliness_score": self.cleanliness_score,
            "status": self.status,
        }


class MetricsTracker:
    """Track and persist runtime metrics."""

    def __init__(self, project_root: Path, run_id: str):
        """
        Initialize metrics tracker.

        Args:
            project_root: Project root directory
            run_id: Run identifier
        """
        self.project_root = project_root
        self.run_id = run_id
        self.metrics = RunMetrics(
            run_id=run_id, start_ts=datetime.now().isoformat()
        )

        # Create metrics directory
        self.metrics_dir = project_root / ".claude" / "metrics"
        self.metrics_dir.mkdir(parents=True, exist_ok=True)

    def start_phase(self, phase_name: str) -> None:
        """Record phase start."""
        self.metrics.phases[phase_name] = PhaseMetrics(
            phase_name=phase_name, start_ts=datetime.now().isoformat()
        )

    def end_phase(
        self,
        phase_name: str,
        validation_status: Optional[str] = None,
        artifacts_count: int = 0,
    ) -> None:
        """Record phase completion."""
        if phase_name not in self.metrics.phases:
            return

        phase_metrics = self.metrics.phases[phase_name]
        phase_metrics.end_ts = datetime.now().isoformat()

        # Calculate duration
        start = datetime.fromisoformat(phase_metrics.start_ts)
        end = datetime.fromisoformat(phase_metrics.end_ts)
        phase_metrics.duration_s = (end - start).total_seconds()

        phase_metrics.validation_status = validation_status
        phase_metrics.artifacts_count = artifacts_count

    def record_agent_execution(
        self,
        phase_name: str,
        agent_name: str,
        duration_s: float,
        exit_code: int,
        retry_count: int = 0,
    ) -> None:
        """Record agent execution metrics."""
        if phase_name not in self.metrics.phases:
            self.start_phase(phase_name)

        phase_metrics = self.metrics.phases[phase_name]
        phase_metrics.agent_runtimes[agent_name] = duration_s
        phase_metrics.agent_exit_codes[agent_name] = exit_code

        if retry_count > 0:
            phase_metrics.agent_retries[agent_name] = retry_count
            self.metrics.total_retries += retry_count

    def set_cleanliness_score(self, score: float) -> None:
        """Update cleanliness score."""
        self.metrics.cleanliness_score = score

    def set_status(self, status: str) -> None:
        """Update run status."""
        self.metrics.status = status

    def finalize(self) -> None:
        """Finalize metrics (set end time and total duration)."""
        self.metrics.end_ts = datetime.now().isoformat()

        # Calculate total duration
        start = datetime.fromisoformat(self.metrics.start_ts)
        end = datetime.fromisoformat(self.metrics.end_ts)
        self.metrics.duration_s = (end - start).total_seconds()

    def save_json(self) -> Path:
        """
        Save metrics as JSON.

        Returns:
            Path to saved JSON file
        """
        json_path = self.metrics_dir / f"run_{self.run_id}.json"

        with open(json_path, "w") as f:
            json.dump(self.metrics.to_dict(), f, indent=2)

        return json_path

    def save_prometheus(self) -> Path:
        """
        Save metrics in Prometheus text format.

        Returns:
            Path to saved metrics file
        """
        prom_path = self.metrics_dir / "metrics.prom"

        lines = []

        # Phase durations
        for phase_name, phase_metrics in self.metrics.phases.items():
            if phase_metrics.duration_s > 0:
                lines.append(
                    f'orchestrator_phase_duration_seconds{{phase="{phase_name}"}} {phase_metrics.duration_s:.2f}'
                )

        # Agent runtimes
        for phase_name, phase_metrics in self.metrics.phases.items():
            for agent_name, runtime in phase_metrics.agent_runtimes.items():
                lines.append(
                    f'orchestrator_agent_runtime_seconds{{phase="{phase_name}",agent="{agent_name}"}} {runtime:.2f}'
                )

        # Agent retries
        for phase_name, phase_metrics in self.metrics.phases.items():
            for agent_name, retries in phase_metrics.agent_retries.items():
                lines.append(
                    f'orchestrator_agent_retries_total{{phase="{phase_name}",agent="{agent_name}"}} {retries}'
                )

        # Total retries
        lines.append(f"orchestrator_total_retries {self.metrics.total_retries}")

        # Cleanliness score
        if self.metrics.cleanliness_score is not None:
            lines.append(f"orchestrator_cleanliness_score {self.metrics.cleanliness_score:.1f}")

        # Total duration
        if self.metrics.duration_s > 0:
            lines.append(f"orchestrator_run_duration_seconds {self.metrics.duration_s:.2f}")

        with open(prom_path, "w") as f:
            f.write("\n".join(lines))
            f.write("\n")

        return prom_path

    def get_summary(self) -> Dict[str, Any]:
        """
        Get metrics summary for display.

        Returns:
            Dictionary with key metrics
        """
        summary = {
            "run_id": self.run_id,
            "status": self.metrics.status,
            "duration_s": self.metrics.duration_s,
            "phases_completed": len([p for p in self.metrics.phases.values() if p.end_ts]),
            "total_retries": self.metrics.total_retries,
            "cleanliness_score": self.metrics.cleanliness_score,
        }

        # Last phase info
        if self.metrics.phases:
            last_phase = list(self.metrics.phases.values())[-1]
            summary["last_phase"] = last_phase.phase_name
            summary["last_phase_duration_s"] = last_phase.duration_s

            # Last exit code
            if last_phase.agent_exit_codes:
                summary["last_exit_code"] = list(last_phase.agent_exit_codes.values())[-1]

        return summary


def load_metrics(project_root: Path, run_id: str) -> Optional[RunMetrics]:
    """
    Load metrics from JSON file.

    Args:
        project_root: Project root directory
        run_id: Run identifier

    Returns:
        RunMetrics if file exists, None otherwise
    """
    json_path = project_root / ".claude" / "metrics" / f"run_{run_id}.json"

    if not json_path.exists():
        return None

    with open(json_path) as f:
        data = json.load(f)

    # Reconstruct RunMetrics
    metrics = RunMetrics(
        run_id=data["run_id"],
        start_ts=data["start_ts"],
        end_ts=data.get("end_ts"),
        duration_s=data.get("duration_s", 0.0),
        total_retries=data.get("total_retries", 0),
        cleanliness_score=data.get("cleanliness_score"),
        status=data.get("status", "running"),
    )

    # Reconstruct phases
    for phase_name, phase_data in data.get("phases", {}).items():
        metrics.phases[phase_name] = PhaseMetrics(
            phase_name=phase_data["phase_name"],
            start_ts=phase_data["start_ts"],
            end_ts=phase_data.get("end_ts"),
            duration_s=phase_data.get("duration_s", 0.0),
            agent_runtimes=phase_data.get("agent_runtimes", {}),
            agent_exit_codes=phase_data.get("agent_exit_codes", {}),
            agent_retries=phase_data.get("agent_retries", {}),
            validation_status=phase_data.get("validation_status"),
            artifacts_count=phase_data.get("artifacts_count", 0),
        )

    return metrics
