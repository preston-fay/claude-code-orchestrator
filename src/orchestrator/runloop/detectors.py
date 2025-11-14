"""Auto-detection logic for specialized agents (Phase 3)."""

from typing import List, Any, Dict


class AgentDetectorMixin:
    """Mixin providing auto-detection logic for specialized agents."""

    def _auto_detect_optional_agents(self, phase_name: str, base_agents: List[str]) -> List[str]:
        """
        Auto-detect optional specialized agents based on intake and governance.

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
