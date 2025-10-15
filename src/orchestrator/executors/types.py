"""Type definitions for agent executors."""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional


@dataclass
class AgentExecResult:
    """Result from executing an agent."""

    stdout: str
    stderr: str
    exit_code: int
    artifacts: List[str] = field(default_factory=list)
    duration_s: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def success(self) -> bool:
        """Check if execution was successful."""
        return self.exit_code == 0

    @property
    def retryable(self) -> bool:
        """Check if failure is retryable based on exit code."""
        # Common retryable exit codes
        retryable_codes = [75, 101, 111, 125]  # temp fail, network, connection refused, etc
        return self.exit_code in retryable_codes

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "stdout": self.stdout,
            "stderr": self.stderr,
            "exit_code": self.exit_code,
            "artifacts": self.artifacts,
            "duration_s": self.duration_s,
            "metadata": self.metadata,
            "success": self.success,
        }
