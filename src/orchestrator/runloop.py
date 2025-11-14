"""Orchestrator run-loop implementation."""

import json
import yaml
from pathlib import Path
from typing import Optional, Dict, Any, List
from datetime import datetime
import logging
import subprocess
import time
import asyncio

from .types import (
    RunState,
    RunStatus,
    AgentOutcome,
    PhaseOutcome,
    ValidationResult,
    ValidationStatus,
)
from .checkpoints import validate_artifacts
from .prompt_loader import build_agent_context, load_and_interpolate
from .executors import get_executor, AgentExecResult
from .reliability import with_timeout, retry_async, RetryConfig


def _is_agent_error_retryable(exception: Exception, retry_cfg: RetryConfig) -> bool:
    """Check if agent execution error is retryable."""
    # Timeout errors are retryable
    if isinstance(exception, (asyncio.TimeoutError, TimeoutError)):
        return True

    # Check exit code if present
    if hasattr(exception, "exit_code"):
        if exception.exit_code in retry_cfg.retryable_exit_codes:
            return True

    # Check error message
    error_msg = str(exception).lower()
    for msg in retry_cfg.retryable_messages:
        if msg.lower() in error_msg:
            return True

    return False


class Orchestrator:
    """Production-grade orchestrator run-loop with stateful phases and consensus."""

    def __init__(self, project_root: Optional[Path] = None):
        """
        Initialize orchestrator.

        Args:
            project_root: Project root directory (defaults to cwd)
        """
        self.project_root = project_root or Path.cwd()
        self.config = self._load_config()
        self.state = self._load_state()
        self.logger = self._setup_logger()

    def _load_config(self) -> Dict[str, Any]:
        """Load orchestrator configuration from .claude/config.yaml."""
        config_path = self.project_root / ".claude" / "config.yaml"

        if not config_path.exists():
            raise FileNotFoundError(f"Config not found: {config_path}")

        with open(config_path) as f:
            return yaml.safe_load(f)

    def _load_state(self) -> RunState:
        """Load orchestrator state from .claude/orchestrator_state.json."""
        state_path = self._get_state_path()

        if not state_path.exists():
            # Initialize new state
            return RunState(
                run_id="",
                status=RunStatus.IDLE,
                created_at="",
                updated_at="",
            )

        with open(state_path) as f:
            data = json.load(f)
            return RunState.from_dict(data)

    def _save_state(self) -> None:
        """Save orchestrator state to .claude/orchestrator_state.json."""
        state_path = self._get_state_path()
        state_path.parent.mkdir(parents=True, exist_ok=True)

        self.state.updated_at = datetime.now().isoformat()

        with open(state_path, "w") as f:
            json.dump(self.state.to_dict(), f, indent=2)

    def _get_state_path(self) -> Path:
        """Get path to state file from config."""
        state_file = self.config.get("orchestrator", {}).get(
            "state_file", ".claude/orchestrator_state.json"
        )
        return self.project_root / state_file

    def _setup_logger(self) -> logging.Logger:
        """Setup logger for run-loop."""
        logger = logging.getLogger("orchestrator")
        logger.setLevel(logging.INFO)

        # Don't add handlers if already configured
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)

        return logger

    def _get_log_path(self) -> Path:
        """Get path to current run log file."""
        logs_dir = self.project_root / ".claude" / "logs"
        logs_dir.mkdir(parents=True, exist_ok=True)
        return logs_dir / f"run_{self.state.run_id}.log"

    def _log(self, message: str, level: str = "info") -> None:
        """Log message to both logger and run log file."""
        log_func = getattr(self.logger, level, self.logger.info)
        log_func(message)

        # Also append to run log file if run is active
        if self.state.run_id:
            log_path = self._get_log_path()
            with open(log_path, "a") as f:
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                f.write(f"[{timestamp}] [{level.upper()}] {message}\n")

    def start_run(
        self,
        intake_path: Optional[Path] = None,
        from_phase: Optional[str] = None,
        mode: str = "legacy",
    ) -> None:
        """
        Initialize a new orchestrator run.

        Args:
            intake_path: Optional path to intake YAML
            from_phase: Optional phase to start from (must be enabled)
            mode: Execution mode - "legacy" (default) or "code" (MCP code execution)
        """
        # Generate run ID
        run_id = datetime.now().strftime("%Y%m%d_%H%M%S")

        # Load intake if provided
        intake_summary = None
        if intake_path:
            intake_summary = self._load_intake(intake_path)

        # Get first enabled phase
        first_phase = from_phase or self._get_first_enabled_phase()

        if not first_phase:
            raise ValueError("No enabled phases found in configuration")

        # Initialize state with mode in metadata
        self.state = RunState(
            run_id=run_id,
            status=RunStatus.RUNNING,
            created_at=datetime.now().isoformat(),
            updated_at=datetime.now().isoformat(),
            current_phase=first_phase,
            intake_path=str(intake_path) if intake_path else None,
            intake_summary=intake_summary,
            metadata={"execution_mode": mode},
        )

        self._save_state()
        self._log(f"Started run {run_id}")
        self._log(f"Execution mode: {mode}")
        self._log(f"Current phase: {first_phase}")

        if intake_path:
            self._log(f"Loaded intake: {intake_path}")

    def _load_intake(self, intake_path: Path) -> Dict[str, Any]:
        """Load intake configuration from YAML."""
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
        """Get first enabled phase from config."""
        phases = self.config.get("workflow", {}).get("phases", {})

        for phase_name, phase_config in phases.items():
            if phase_config.get("enabled", True):
                return phase_name

        return None

    def _get_next_phase(self, current_phase: str) -> Optional[str]:
        """Get next enabled phase after current_phase."""
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
        """Get previous enabled phase before current_phase."""
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

    def _auto_detect_optional_agents(self, phase_name: str, base_agents: List[str]) -> List[str]:
        """Auto-detect optional specialized agents based on intake and governance.

        Args:
            phase_name: Current phase name
            base_agents: Base agent list from phase configuration

        Returns:
            Augmented agent list with auto-detected specialized agents
        """
        detected_agents = []
        intake = self.state.intake_summary or {}
        governance = self.config.get("governance", {})

        # Get intake requirements as lowercase text for keyword matching
        requirements_text = ""
        if "requirements" in intake:
            if isinstance(intake["requirements"], list):
                requirements_text = " ".join(str(r).lower() for r in intake["requirements"])
            elif isinstance(intake["requirements"], str):
                requirements_text = intake["requirements"].lower()

        project_type = ""
        if "project" in intake and isinstance(intake["project"], dict):
            project_type = str(intake["project"].get("type", "")).lower()

        # Database Architect: Detect before planning/data_engineering/developer phases
        if phase_name in ["planning", "data_engineering", "developer"]:
            db_keywords = ["db", "database", "sql", "postgres", "mysql", "schema", "migration"]
            if any(kw in requirements_text for kw in db_keywords) or any(kw in project_type for kw in db_keywords):
                if "database-architect" not in base_agents and "database_architect" not in base_agents:
                    detected_agents.append("database-architect")
                    self._log("Auto-detected: database-architect (database keywords found)")

        # Performance Engineer: Detect after developer phase
        if phase_name in ["developer", "qa"]:
            # Check for performance SLAs in governance
            perf_slas = governance.get("performance_slas", {})
            latency_sla = perf_slas.get("latency_p95_ms", 0)

            perf_keywords = ["performance", "latency", "throughput", "optimization", "scale"]
            has_perf_requirements = any(kw in requirements_text for kw in perf_keywords)

            environment = intake.get("environment", "")
            is_production = environment == "production"

            if (latency_sla > 0 or has_perf_requirements or is_production):
                if "performance-engineer" not in base_agents and "performance_engineer" not in base_agents:
                    detected_agents.append("performance-engineer")
                    reason = []
                    if latency_sla > 0:
                        reason.append(f"SLA: {latency_sla}ms")
                    if has_perf_requirements:
                        reason.append("performance keywords")
                    if is_production:
                        reason.append("production environment")
                    self._log(f"Auto-detected: performance-engineer ({', '.join(reason)})")

        # Security Auditor: Detect after developer phase
        if phase_name in ["developer", "qa"]:
            require_security_scan = governance.get("require_security_scan", False)
            compliance = governance.get("compliance", {})
            has_compliance = any(
                k in compliance for k in ["gdpr", "hipaa", "soc2", "pci-dss", "pci_dss"]
            )

            security_keywords = ["security", "authentication", "authorization", "compliance", "audit"]
            has_security_requirements = any(kw in requirements_text for kw in security_keywords)

            environment = intake.get("environment", "")
            is_production = environment == "production"

            if (require_security_scan or has_compliance or is_production or has_security_requirements):
                if "security-auditor" not in base_agents and "security_auditor" not in base_agents:
                    detected_agents.append("security-auditor")
                    reason = []
                    if require_security_scan:
                        reason.append("security scan required")
                    if has_compliance:
                        reason.append("compliance requirements")
                    if is_production:
                        reason.append("production environment")
                    if has_security_requirements:
                        reason.append("security keywords")
                    self._log(f"Auto-detected: security-auditor ({', '.join(reason)})")

        # Merge detected agents with base agents, preserving order and avoiding duplicates
        # For "database-architect", insert before "developer" if present
        # For others, append after base agents

        final_agents = []
        for agent in base_agents:
            # Insert database-architect before developer if detected
            if agent == "developer" and "database-architect" in detected_agents:
                if "database-architect" not in final_agents:
                    final_agents.append("database-architect")
                detected_agents.remove("database-architect")
            final_agents.append(agent)

        # Append remaining detected agents at the end
        for agent in detected_agents:
            if agent not in final_agents:
                final_agents.append(agent)

        return final_agents

    def run_phase(
        self,
        phase_name: str,
        force_parallel: bool = False,
        max_workers: Optional[int] = None,
        timeout_override: Optional[int] = None,
    ) -> PhaseOutcome:
        """
        Execute a single workflow phase.

        Args:
            phase_name: Name of the phase to execute
            force_parallel: Force parallel execution (only works for parallel-enabled phases)
            max_workers: Maximum concurrent workers
            timeout_override: Timeout override in seconds

        Returns:
            PhaseOutcome with execution results
        """
        self._log(f"Running phase: {phase_name}")

        phases = self.config.get("workflow", {}).get("phases", {})
        phase_config = phases.get(phase_name)

        if not phase_config:
            raise ValueError(f"Phase not found in config: {phase_name}")

        # Get phase settings
        requires_consensus = phase_config.get("requires_consensus", False)
        artifacts_required = phase_config.get("artifacts_required", [])
        base_agent_names = phase_config.get("agents", [])

        # Auto-detect optional specialized agents based on intake and governance
        agent_names = self._auto_detect_optional_agents(phase_name, base_agent_names)

        parallel = phase_config.get("parallel", False) or force_parallel

        # Execute agents (parallel or sequential)
        if parallel and len(agent_names) > 1:
            # Parallel execution
            self._log(f"Executing {len(agent_names)} agents in parallel")
            agent_outcomes = asyncio.run(
                self._run_agents_parallel(agent_names, phase_name, max_workers, timeout_override)
            )
        else:
            # Sequential execution
            agent_outcomes = []
            for agent_name in agent_names:
                outcome = self.invoke_agent(agent_name, phase_name, timeout_override)
                agent_outcomes.append(outcome)

                if not outcome.success:
                    self._log(f"Agent {agent_name} failed", level="error")

        # Validate artifacts
        validation = None
        if artifacts_required:
            self._log(f"Validating {len(artifacts_required)} required artifact(s)")
            validation = validate_artifacts(
                artifacts_required=artifacts_required,
                project_root=self.project_root,
                phase_name=phase_name,
            )
            self._log(f"Validation status: {validation.status.value}")

        # Check if consensus required
        awaiting_consensus = False
        if requires_consensus:
            self._generate_consensus_request(phase_name, agent_outcomes, validation)
            awaiting_consensus = True
            self._log(f"Consensus required for phase: {phase_name}")

        # Determine success
        all_agents_success = all(o.success for o in agent_outcomes)
        validation_ok = (
            validation is None
            or validation.status in (ValidationStatus.PASS, ValidationStatus.PARTIAL)
        )
        success = all_agents_success and validation_ok

        outcome = PhaseOutcome(
            phase_name=phase_name,
            success=success,
            agent_outcomes=agent_outcomes,
            validation=validation,
            requires_consensus=requires_consensus,
            awaiting_consensus=awaiting_consensus,
            completed_at=datetime.now().isoformat(),
        )

        return outcome

    async def _run_agents_parallel(
        self,
        agent_names: List[str],
        phase_name: str,
        max_workers: Optional[int] = None,
        timeout_override: Optional[int] = None,
    ) -> List[AgentOutcome]:
        """
        Run multiple agents in parallel with concurrency limit.

        Args:
            agent_names: List of agent names to execute
            phase_name: Current phase name
            max_workers: Optional concurrency limit (defaults to config max_parallel_agents)

        Returns:
            List of AgentOutcomes
        """
        # Get max workers from config if not specified
        if max_workers is None:
            orch_config = self.config.get("orchestrator", {})
            max_workers = orch_config.get("max_parallel_agents", 2)

        # Cap concurrency
        max_workers = min(max_workers, len(agent_names))

        self._log(f"Parallel execution: {len(agent_names)} agents, max_workers={max_workers}")

        # Create semaphore for concurrency control
        semaphore = asyncio.Semaphore(max_workers)

        async def run_agent_with_semaphore(agent_name: str) -> AgentOutcome:
            """Run agent with semaphore to limit concurrency."""
            async with semaphore:
                return await self._invoke_agent_async(agent_name, phase_name, timeout_override)

        # Execute all agents concurrently with limit
        tasks = [run_agent_with_semaphore(agent_name) for agent_name in agent_names]
        outcomes = await asyncio.gather(*tasks, return_exceptions=True)

        # Convert exceptions to failed outcomes
        results = []
        for i, outcome in enumerate(outcomes):
            if isinstance(outcome, Exception):
                self._log(f"Agent {agent_names[i]} raised exception: {outcome}", level="error")
                results.append(
                    AgentOutcome(
                        agent_name=agent_names[i],
                        success=False,
                        errors=[str(outcome)],
                    )
                )
            else:
                results.append(outcome)

        return results

    def invoke_agent(self, agent_name: str, phase_name: str, timeout_override: Optional[float] = None) -> AgentOutcome:
        """
        Invoke a single agent within a phase (sync wrapper for async execution).

        Args:
            agent_name: Name of the agent to invoke
            phase_name: Current phase name
            timeout_override: Optional timeout override in seconds

        Returns:
            AgentOutcome with execution results
        """
        # Run async execution in event loop
        return asyncio.run(self._invoke_agent_async(agent_name, phase_name, timeout_override))

    async def _invoke_agent_async(
        self, agent_name: str, phase_name: str, timeout_override: Optional[float] = None
    ) -> AgentOutcome:
        """
        Async implementation of agent invocation with real execution.

        Args:
            agent_name: Name of the agent to invoke
            phase_name: Current phase name
            timeout_override: Optional timeout override (seconds)

        Returns:
            AgentOutcome with execution results
        """
        self._log(f"Invoking agent: {agent_name} (phase: {phase_name})")

        start_time = time.time()

        try:
            # Get agent config
            subagents = self.config.get("subagents", {})
            agent_config = subagents.get(agent_name, {})

            # Get timeout from config or override
            orch_config = self.config.get("orchestrator", {})
            default_timeout = orch_config.get("timeout_minutes", 30) * 60
            timeout_seconds = timeout_override or default_timeout

            # Get retry config
            retry_cfg_dict = orch_config.get("retry", {})
            retry_cfg = RetryConfig(
                retries=retry_cfg_dict.get("retries", 2),
                base_delay=retry_cfg_dict.get("base_delay", 0.7),
                jitter=retry_cfg_dict.get("jitter", 0.25),
                backoff=retry_cfg_dict.get("backoff", 2.0),
                retryable_exit_codes=retry_cfg_dict.get("retryable_exit_codes", [75, 101]),
                retryable_messages=retry_cfg_dict.get(
                    "retryable_messages", ["rate limit", "transient network"]
                ),
            )

            # Build context
            context = build_agent_context(
                project_root=self.project_root,
                phase=phase_name,
                agent=agent_name,
                intake_summary=self.state.intake_summary,
                last_artifacts=self.state.phase_artifacts,
                entrypoints=self._get_agent_entrypoints(agent_name),
            )

            # Load and interpolate prompt
            prompt = load_and_interpolate(agent_name, context, self.project_root)
            self._log(f"Agent prompt prepared ({len(prompt)} chars)")

            # Get executor
            executor = get_executor(agent_name, agent_config)

            # Define execution function with retry
            async def execute_with_retry() -> AgentExecResult:
                """Execute agent with timeout."""
                return await with_timeout(
                    executor(
                        prompt=prompt,
                        phase_name=phase_name,
                        project_root=self.project_root,
                        timeout_seconds=timeout_seconds,
                    ),
                    seconds=timeout_seconds,
                    timeout_message=f"Agent {agent_name} execution timed out after {timeout_seconds}s",
                )

            # Execute with retry
            exec_result = await retry_async(
                execute_with_retry,
                config=retry_cfg,
                is_retryable=lambda e, _: _is_agent_error_retryable(e, retry_cfg),
            )

            # Write agent transcript
            self._write_agent_transcript(agent_name, phase_name, exec_result)

            # Convert to AgentOutcome
            execution_time = time.time() - start_time

            return AgentOutcome(
                agent_name=agent_name,
                success=exec_result.success,
                artifacts=exec_result.artifacts,
                notes=exec_result.stdout[:500] if exec_result.stdout else "",
                errors=[exec_result.stderr] if exec_result.stderr and not exec_result.success else [],
                exit_code=exec_result.exit_code,
                execution_time=execution_time,
            )

        except asyncio.TimeoutError as e:
            execution_time = time.time() - start_time
            self._log(f"Agent {agent_name} timeout: {e}", level="error")

            return AgentOutcome(
                agent_name=agent_name,
                success=False,
                errors=[f"Timeout after {timeout_seconds}s"],
                exit_code=124,
                execution_time=execution_time,
            )

        except Exception as e:
            execution_time = time.time() - start_time
            self._log(f"Agent {agent_name} error: {e}", level="error")

            return AgentOutcome(
                agent_name=agent_name,
                success=False,
                errors=[str(e)],
                execution_time=execution_time,
            )

    def _write_agent_transcript(
        self, agent_name: str, phase_name: str, exec_result: AgentExecResult
    ) -> None:
        """Write agent execution transcript to log file."""
        transcript_dir = self.project_root / ".claude" / "logs" / "agents"
        transcript_dir.mkdir(parents=True, exist_ok=True)

        transcript_file = transcript_dir / f"{self.state.run_id}_{phase_name}_{agent_name}.log"

        with open(transcript_file, "w") as f:
            f.write(f"# Agent Transcript: {agent_name}\n\n")
            f.write(f"Phase: {phase_name}\n")
            f.write(f"Run ID: {self.state.run_id}\n")
            f.write(f"Duration: {exec_result.duration_s:.2f}s\n")
            f.write(f"Exit Code: {exec_result.exit_code}\n\n")

            if exec_result.stdout:
                f.write("## STDOUT\n\n")
                f.write(exec_result.stdout)
                f.write("\n\n")

            if exec_result.stderr:
                f.write("## STDERR\n\n")
                f.write(exec_result.stderr)
                f.write("\n\n")

            if exec_result.artifacts:
                f.write("## Artifacts\n\n")
                for artifact in exec_result.artifacts:
                    f.write(f"- {artifact}\n")

        self._log(f"Agent transcript written: {transcript_file}")

    def _get_agent_entrypoints(self, agent_name: str) -> Optional[Dict[str, str]]:
        """Get entrypoints for an agent from config."""
        subagents = self.config.get("subagents", {})
        agent_config = subagents.get(agent_name, {})
        return agent_config.get("entrypoints")

    def _generate_consensus_request(
        self,
        phase_name: str,
        agent_outcomes: List[AgentOutcome],
        validation: Optional[ValidationResult],
    ) -> None:
        """Generate enhanced consensus request document with reviewer checklist."""
        from .packaging import package_phase_artifacts, get_metrics_digest

        consensus_dir = self.project_root / ".claude" / "consensus"
        consensus_dir.mkdir(parents=True, exist_ok=True)

        request_path = consensus_dir / "REQUEST.md"

        # Determine status ribbon
        all_success = all(o.success for o in agent_outcomes)
        validation_ok = (
            validation is None
            or validation.status.value in ("pass", "partial")
        )
        overall_success = all_success and validation_ok

        if overall_success:
            status_ribbon = "🟢 **STATUS: READY FOR REVIEW**"
            status_emoji = "✅"
        elif all_success and not validation_ok:
            status_ribbon = "🟡 **STATUS: PARTIAL SUCCESS** (artifacts incomplete)"
            status_emoji = "⚠️"
        else:
            status_ribbon = "🔴 **STATUS: NEEDS ATTENTION** (some agents failed)"
            status_emoji = "❌"

        # Package artifacts
        artifact_paths = []
        if validation and validation.found:
            artifact_paths = validation.found

        zip_path = None
        if artifact_paths:
            metrics_digest = get_metrics_digest(phase_name, agent_outcomes, validation)
            zip_path = package_phase_artifacts(
                phase_name, artifact_paths, self.project_root, self.state.run_id, metrics_digest
            )

        with open(request_path, "w") as f:
            # Status ribbon at top
            f.write(f"{status_ribbon}\n\n")
            f.write("---\n\n")

            f.write(f"# Consensus Request: {phase_name}\n\n")
            f.write(f"**Requested:** {datetime.now().isoformat()}\n\n")
            f.write(f"**Run ID:** {self.state.run_id}\n\n")

            f.write("## Phase Summary\n\n")
            f.write(f"Phase **{phase_name}** has completed and requires approval before proceeding.\n\n")

            # Summary table
            f.write("| Metric | Value |\n")
            f.write("|--------|-------|\n")
            f.write(f"| Phase | {phase_name} |\n")
            f.write(f"| Agents | {len(agent_outcomes)} |\n")

            artifacts_produced = sum(len(o.artifacts) for o in agent_outcomes)
            f.write(f"| Artifacts Produced | {artifacts_produced} |\n")

            if validation:
                f.write(f"| Validation Status | {status_emoji} {validation.status.value.upper()} |\n")

            f.write("\n")

            # Artifact bundle link
            if zip_path:
                f.write("## 📦 Artifact Bundle\n\n")
                f.write(f"All phase artifacts packaged: `{zip_path.relative_to(self.project_root)}`\n\n")
                f.write(f"- Contains {len(artifact_paths)} artifact(s)\n")
                f.write("- Includes MANIFEST.json with metadata\n\n")

            # Collapsible agent outcomes
            f.write("<details>\n")
            f.write("<summary><strong>📋 Agent Outcomes (click to expand)</strong></summary>\n\n")

            for outcome in agent_outcomes:
                status = "✅ Success" if outcome.success else "❌ Failed"
                f.write(f"### {outcome.agent_name}: {status}\n\n")

                if outcome.execution_time:
                    f.write(f"- **Duration:** {outcome.execution_time:.1f}s\n")
                if outcome.exit_code is not None:
                    f.write(f"- **Exit Code:** {outcome.exit_code}\n")

                if outcome.notes:
                    f.write(f"- **Notes:** {outcome.notes}\n")
                if outcome.errors:
                    f.write(f"- **Errors:**\n")
                    for err in outcome.errors:
                        f.write(f"  - {err}\n")
                if outcome.artifacts:
                    f.write(f"- **Artifacts:** {len(outcome.artifacts)} file(s)\n")
                    for artifact in outcome.artifacts[:5]:  # Show first 5
                        f.write(f"  - `{artifact}`\n")
                    if len(outcome.artifacts) > 5:
                        f.write(f"  - ... and {len(outcome.artifacts) - 5} more\n")

                f.write("\n")

            f.write("</details>\n\n")

            # Collapsible validation section
            if validation:
                f.write("<details>\n")
                f.write("<summary><strong>✅ Artifact Validation (click to expand)</strong></summary>\n\n")
                f.write(f"- **Status:** {status_emoji} {validation.status.value.upper()}\n")
                f.write(f"- **Found:** {len(validation.found)} file(s)\n")
                f.write(f"- **Missing:** {len(validation.missing)} pattern(s)\n\n")

                if validation.found:
                    f.write("**Found Artifacts:**\n\n")
                    for artifact in validation.found[:10]:  # Show first 10
                        f.write(f"- `{artifact}`\n")
                    if len(validation.found) > 10:
                        f.write(f"- ... and {len(validation.found) - 10} more\n")
                    f.write("\n")

                if validation.missing:
                    f.write("**Missing Patterns:**\n\n")
                    for pattern in validation.missing:
                        f.write(f"- `{pattern}`\n")
                    f.write("\n")

                if validation.validation_report_path:
                    f.write(f"📄 Full validation report: `{validation.validation_report_path}`\n\n")

                f.write("</details>\n\n")

            # Metrics and health - collapsible
            metrics_path = self.project_root / ".claude" / "metrics" / f"run_{self.state.run_id}.json"
            hygiene_path = self.project_root / "reports" / "hygiene_summary.json"

            if metrics_path.exists() or hygiene_path.exists():
                f.write("<details>\n")
                f.write("<summary><strong>📊 Metrics & Health (click to expand)</strong></summary>\n\n")

                if metrics_path.exists():
                    f.write("### Runtime Metrics\n\n")
                    f.write(f"📊 Full metrics: `.claude/metrics/run_{self.state.run_id}.json`\n\n")

                if hygiene_path.exists():
                    import json as json_mod
                    with open(hygiene_path) as hf:
                        hygiene = json_mod.load(hf)
                        score = hygiene.get("cleanliness_score", 0)
                        grade = hygiene.get("grade", "N/A")

                    f.write("### Repository Health\n\n")
                    f.write(f"🧹 Cleanliness Score: **{score}/100** (Grade: {grade})\n\n")
                    f.write("📄 Full report: `reports/hygiene_summary.json`\n\n")

                f.write("</details>\n\n")

            # Reviewer checklist
            f.write("## Reviewer Checklist\n\n")
            f.write("Before approving, verify:\n\n")
            f.write("- [ ] All agents completed successfully\n")
            f.write("- [ ] Required artifacts are present and valid\n")
            f.write("- [ ] No security vulnerabilities introduced\n")
            f.write("- [ ] Performance is acceptable (check agent runtimes)\n")
            f.write("- [ ] Documentation has been updated\n")
            f.write("- [ ] Code follows project standards\n")
            f.write("- [ ] Tests are passing (if applicable)\n")
            f.write("- [ ] No sensitive data exposed\n\n")

            f.write("## Decision Required\n\n")
            f.write("**Approve** to proceed to the next phase:\n")
            f.write("```bash\n")
            f.write("orchestrator run approve\n")
            f.write("```\n\n")

            f.write("**Reject** to mark for revision:\n")
            f.write("```bash\n")
            f.write('orchestrator run reject --reason "Reason for rejection"\n')
            f.write("```\n\n")

            f.write("---\n")
            f.write("*Generated by Orchestrator Run-Loop with Enhanced Consensus UX*\n")

        self._log(f"Consensus request generated: {request_path}")

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
        """Reject consensus and mark for revision."""
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
        """Record consensus decision to file."""
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

    def get_status(self) -> Dict[str, Any]:
        """
        Get current run status.

        Returns:
            Dictionary with comprehensive status information
        """
        status = self.state.to_dict()

        # Add checkpoint summary
        from .checkpoints import get_checkpoint_summary

        status["checkpoints"] = get_checkpoint_summary(self.project_root)

        # Add cleanliness score if available
        hygiene_summary_path = self.project_root / "reports" / "hygiene_summary.json"
        if hygiene_summary_path.exists():
            with open(hygiene_summary_path) as f:
                hygiene = json.load(f)
                status["cleanliness_score"] = hygiene.get("cleanliness_score")
                status["cleanliness_grade"] = hygiene.get("grade")

        return status

    def get_log_tail(self, lines: int = 50) -> str:
        """
        Get tail of run log.

        Args:
            lines: Number of lines to return

        Returns:
            Log tail as string
        """
        log_path = self._get_log_path()

        if not log_path.exists():
            return "No log file found"

        with open(log_path) as f:
            all_lines = f.readlines()
            tail_lines = all_lines[-lines:]
            return "".join(tail_lines)
