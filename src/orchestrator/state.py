"""Orchestrator state management."""

import json
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime


class OrchestratorState:
    """Manages orchestrator state persistence."""

    def __init__(self, state_file: Optional[Path] = None):
        """Initialize state manager."""
        if state_file is None:
            base = Path(__file__).parent.parent.parent
            state_file = base / ".claude" / "orchestrator_state.json"

        self.state_file = state_file
        self._ensure_state_file()

    def _ensure_state_file(self):
        """Ensure state file exists with default structure."""
        self.state_file.parent.mkdir(parents=True, exist_ok=True)

        if not self.state_file.exists():
            default_state = {
                "status": "idle",
                "current_phase": None,
                "current_project": None,
                "started_at": None,
                "updated_at": datetime.utcnow().isoformat(),
                "completed_phases": [],
                "checkpoint_artifacts": {},
                "metadata": {}
            }
            self._write_state(default_state)

    def _read_state(self) -> Dict[str, Any]:
        """Read state from file."""
        try:
            with open(self.state_file, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            # If file is corrupted, reset to default
            self._ensure_state_file()
            with open(self.state_file, 'r') as f:
                return json.load(f)

    def _write_state(self, state: Dict[str, Any]):
        """Write state to file."""
        state["updated_at"] = datetime.utcnow().isoformat()
        with open(self.state_file, 'w') as f:
            json.dump(state, f, indent=2)

    def is_busy(self) -> bool:
        """Check if orchestrator is currently running a workflow."""
        state = self._read_state()
        return state.get("status") == "running"

    def get_status(self) -> str:
        """Get current orchestrator status."""
        state = self._read_state()
        return state.get("status", "idle")

    def get_current_phase(self) -> Optional[str]:
        """Get current workflow phase if running."""
        state = self._read_state()
        return state.get("current_phase")

    def get_current_project(self) -> Optional[str]:
        """Get current project name if any."""
        state = self._read_state()
        return state.get("current_project")

    def start_workflow(self, project_name: str, initial_phase: str = "planning"):
        """Mark workflow as started."""
        state = self._read_state()
        state.update({
            "status": "running",
            "current_project": project_name,
            "current_phase": initial_phase,
            "started_at": datetime.utcnow().isoformat(),
            "completed_phases": [],
        })
        self._write_state(state)

    def update_phase(self, phase: str):
        """Update current phase."""
        state = self._read_state()
        if state.get("current_phase"):
            # Mark previous phase as completed
            if state["current_phase"] not in state.get("completed_phases", []):
                state.setdefault("completed_phases", []).append(state["current_phase"])

        state["current_phase"] = phase
        self._write_state(state)

    def complete_workflow(self):
        """Mark workflow as complete."""
        state = self._read_state()

        # Mark final phase as completed
        if state.get("current_phase"):
            if state["current_phase"] not in state.get("completed_phases", []):
                state.setdefault("completed_phases", []).append(state["current_phase"])

        state.update({
            "status": "completed",
            "current_phase": None,
            "completed_at": datetime.utcnow().isoformat(),
        })
        self._write_state(state)

    def abort_workflow(self):
        """Abort current workflow."""
        state = self._read_state()
        state.update({
            "status": "aborted",
            "current_phase": None,
            "aborted_at": datetime.utcnow().isoformat(),
        })
        self._write_state(state)

    def reset(self):
        """Reset to idle state."""
        state = self._read_state()
        state.update({
            "status": "idle",
            "current_phase": None,
            "current_project": None,
            "started_at": None,
            "completed_phases": [],
        })
        self._write_state(state)

    def get_full_state(self) -> Dict[str, Any]:
        """Get complete state dictionary."""
        return self._read_state()


# Global state instance
_state = None


def get_state() -> OrchestratorState:
    """Get global state instance."""
    global _state
    if _state is None:
        _state = OrchestratorState()
    return _state


def is_busy() -> bool:
    """Quick check if orchestrator is busy."""
    return get_state().is_busy()
