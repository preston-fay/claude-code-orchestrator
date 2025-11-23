"""
Phase Execution Service for RSC.

Provides real agent execution for all phases:
- DATA: Data profiling, schema extraction, analytics prep
- DEVELOPMENT: Code scaffolding, feature implementation
- QA: Test generation, quality gate evaluation
- DOCUMENTATION: System docs, README, API reference

Uses LLM provider registry with Sonnet 4.5 (default) or Haiku 4.5 (fallback).
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any

from orchestrator_v2.engine.state_models import (
    AgentContext,
    PhaseType,
    ProjectState,
    TaskDefinition,
)
from orchestrator_v2.llm import get_provider_registry
from orchestrator_v2.user.models import UserProfile

logger = logging.getLogger(__name__)


class PhaseExecutionService:
    """Service to execute all phases with real agent logic."""

    def __init__(self):
        self.registry = get_provider_registry()

    async def execute_phase(
        self,
        phase: PhaseType,
        project_state: ProjectState,
        user: UserProfile,
    ) -> dict[str, Any]:
        """Execute a specific phase.

        Args:
            phase: Phase to execute.
            project_state: Current project state.
            user: User profile with LLM credentials.

        Returns:
            Dict containing artifact paths and metadata.
        """
        logger.info(f"Executing phase {phase.value} for project {project_state.project_id}")

        # Build agent context
        model = user.default_model or "claude-sonnet-4-5-20250929"
        context = AgentContext(
            project_state=project_state,
            task=TaskDefinition(
                task_id=f"{phase.value}_execution",
                description=f"Execute {phase.value} phase",
            ),
            user_id=user.user_id,
            llm_api_key=user.anthropic_api_key,
            llm_provider=user.default_provider or "anthropic",
            model=model,
        )

        # Route to appropriate phase handler
        if phase == PhaseType.DATA:
            return await self._execute_data_phase(project_state, context)
        elif phase == PhaseType.DEVELOPMENT:
            return await self._execute_development_phase(project_state, context)
        elif phase == PhaseType.QA:
            return await self._execute_qa_phase(project_state, context)
        elif phase == PhaseType.DOCUMENTATION:
            return await self._execute_documentation_phase(project_state, context)
        else:
            return {
                "artifacts": [],
                "summary": f"Phase {phase.value} execution not yet implemented",
                "agents": [],
            }

    async def _execute_data_phase(
        self,
        project_state: ProjectState,
        context: AgentContext,
    ) -> dict[str, Any]:
        """Execute DATA phase - profiling, schema, analytics prep."""
        logger.info("Executing DATA phase")

        brief = project_state.brief or "No brief provided"
        capabilities = ", ".join(project_state.capabilities or ["generic"])

        # Generate data artifacts via LLM
        prompt = f"""You are a data engineer. Analyze requirements and produce data phase artifacts.

PROJECT: {project_state.project_name}
BRIEF: {brief}
CAPABILITIES: {capabilities}

Generate the following as JSON with these keys:

1. "data_overview": Markdown document covering:
   - Data requirements based on brief
   - Expected data sources
   - Data quality requirements
   - Storage considerations
   - Processing pipeline overview

2. "schema": JSON object with data schema:
   - entities: array of entity definitions
   - relationships: array of relationships
   - validation_rules: object with rules

3. "profile_report": Markdown profiling report with:
   - Data profiling methodology
   - Expected data characteristics
   - Quality metrics to track
   - Recommendations

Output ONLY valid JSON with these three keys."""

        try:
            result = await self.registry.generate(
                prompt=prompt,
                model=context.model,
                context=context,
                max_tokens=3000,
            )

            text = result.text.strip()
            if text.startswith("```"):
                text = text.split("```")[1]
                if text.startswith("json"):
                    text = text[4:]
                text = text.strip()

            output = json.loads(text)

            # Save artifacts
            artifacts_dir = self._get_artifacts_dir(project_state, "data")
            saved_paths = []

            # Save data overview
            overview_path = artifacts_dir / "data_overview.md"
            overview_content = output.get("data_overview", "")
            if isinstance(overview_content, dict):
                overview_content = json.dumps(overview_content, indent=2)
            overview_path.write_text(f"# Data Overview\n\n{overview_content}")
            saved_paths.append(str(overview_path))

            # Save schema
            schema_path = artifacts_dir / "schema.json"
            schema_content = output.get("schema", {})
            schema_path.write_text(json.dumps(schema_content, indent=2))
            saved_paths.append(str(schema_path))

            # Save profile report
            profile_path = artifacts_dir / "profile_report.md"
            profile_content = output.get("profile_report", "")
            if isinstance(profile_content, dict):
                profile_content = json.dumps(profile_content, indent=2)
            profile_path.write_text(f"# Data Profiling Report\n\n{profile_content}")
            saved_paths.append(str(profile_path))

            return {
                "artifacts": saved_paths,
                "summary": f"Data phase completed. Generated {len(saved_paths)} artifacts.",
                "agents": ["data_agent"],
            }

        except Exception as e:
            logger.error(f"Data phase failed: {e}")
            return {
                "artifacts": [],
                "summary": f"Data phase failed: {str(e)}",
                "agents": ["data_agent"],
            }

    async def _execute_development_phase(
        self,
        project_state: ProjectState,
        context: AgentContext,
    ) -> dict[str, Any]:
        """Execute DEVELOPMENT phase - code scaffolding and implementation."""
        logger.info("Executing DEVELOPMENT phase")

        brief = project_state.brief or "No brief provided"
        capabilities = project_state.capabilities or ["generic"]

        # Determine what to scaffold based on capabilities
        scaffold_react = "app_build" in capabilities or "frontend_ui" in capabilities
        scaffold_fastapi = "app_build" in capabilities or "backend_api" in capabilities
        scaffold_analytics = "analytics_forecasting" in capabilities or "analytics_dashboard" in capabilities
        scaffold_ml = any(cap in capabilities for cap in ["ml_classification", "ml_regression", "ml_clustering"])

        prompt = f"""You are a senior developer. Generate development artifacts for this project.

PROJECT: {project_state.project_name}
BRIEF: {brief}
CAPABILITIES: {", ".join(capabilities)}

SCAFFOLD REQUIREMENTS:
- React frontend: {scaffold_react}
- FastAPI backend: {scaffold_fastapi}
- Analytics code: {scaffold_analytics}
- ML code: {scaffold_ml}

Generate JSON with these keys:

1. "dev_summary": Markdown summary of:
   - Components to be built
   - Architecture decisions
   - Implementation approach
   - File structure created

2. "file_changes": Array of file operations:
   [
     {{"path": "src/app.py", "operation": "create", "description": "Main app entry"}}
   ]

3. "scaffolding_notes": Key implementation notes and next steps

Output ONLY valid JSON."""

        try:
            result = await self.registry.generate(
                prompt=prompt,
                model=context.model,
                context=context,
                max_tokens=3000,
            )

            text = result.text.strip()
            if text.startswith("```"):
                text = text.split("```")[1]
                if text.startswith("json"):
                    text = text[4:]
                text = text.strip()

            output = json.loads(text)

            # Save artifacts
            artifacts_dir = self._get_artifacts_dir(project_state, "development")
            saved_paths = []

            # Save dev summary
            summary_path = artifacts_dir / "dev_summary.md"
            summary_content = output.get("dev_summary", "Development summary")
            if isinstance(summary_content, dict):
                summary_content = json.dumps(summary_content, indent=2)
            summary_path.write_text(f"# Development Summary\n\n{summary_content}")
            saved_paths.append(str(summary_path))

            # Save file change log
            changelog_path = artifacts_dir / "file_change_log.json"
            file_changes = output.get("file_changes", [])
            changelog_path.write_text(json.dumps({
                "changes": file_changes,
                "timestamp": datetime.utcnow().isoformat(),
                "capabilities": capabilities,
            }, indent=2))
            saved_paths.append(str(changelog_path))

            return {
                "artifacts": saved_paths,
                "summary": f"Development phase completed. Generated {len(saved_paths)} artifacts.",
                "agents": ["developer_agent"],
            }

        except Exception as e:
            logger.error(f"Development phase failed: {e}")
            return {
                "artifacts": [],
                "summary": f"Development phase failed: {str(e)}",
                "agents": ["developer_agent"],
            }

    async def _execute_qa_phase(
        self,
        project_state: ProjectState,
        context: AgentContext,
    ) -> dict[str, Any]:
        """Execute QA phase - test generation and quality gates."""
        logger.info("Executing QA phase")

        brief = project_state.brief or "No brief provided"
        capabilities = project_state.capabilities or ["generic"]

        prompt = f"""You are a QA engineer. Generate test artifacts for this project.

PROJECT: {project_state.project_name}
BRIEF: {brief}
CAPABILITIES: {", ".join(capabilities)}

Generate JSON with these keys:

1. "qa_results": JSON object with:
   - test_plan: array of test cases to implement
   - coverage_targets: coverage goals
   - test_types: unit, integration, e2e
   - status: "planned" (not yet executed)

2. "quality_gate_report": Markdown report with:
   - Quality gate criteria
   - Current assessment
   - Recommendations
   - Risk areas
   - Next steps for testing

Output ONLY valid JSON."""

        try:
            result = await self.registry.generate(
                prompt=prompt,
                model=context.model,
                context=context,
                max_tokens=2500,
            )

            text = result.text.strip()
            if text.startswith("```"):
                text = text.split("```")[1]
                if text.startswith("json"):
                    text = text[4:]
                text = text.strip()

            output = json.loads(text)

            # Save artifacts
            artifacts_dir = self._get_artifacts_dir(project_state, "qa")
            saved_paths = []

            # Save QA results
            results_path = artifacts_dir / "qa_results.json"
            qa_results = output.get("qa_results", {"status": "planned"})
            results_path.write_text(json.dumps(qa_results, indent=2))
            saved_paths.append(str(results_path))

            # Save quality gate report
            gate_path = artifacts_dir / "quality_gate_report.md"
            gate_content = output.get("quality_gate_report", "Quality gates to be evaluated")
            if isinstance(gate_content, dict):
                gate_content = json.dumps(gate_content, indent=2)
            gate_path.write_text(f"# Quality Gate Report\n\n{gate_content}")
            saved_paths.append(str(gate_path))

            return {
                "artifacts": saved_paths,
                "summary": f"QA phase completed. Generated {len(saved_paths)} artifacts. Tests planned but not executed.",
                "agents": ["qa_agent"],
            }

        except Exception as e:
            logger.error(f"QA phase failed: {e}")
            return {
                "artifacts": [],
                "summary": f"QA phase failed: {str(e)}",
                "agents": ["qa_agent"],
            }

    async def _execute_documentation_phase(
        self,
        project_state: ProjectState,
        context: AgentContext,
    ) -> dict[str, Any]:
        """Execute DOCUMENTATION phase - final docs generation."""
        logger.info("Executing DOCUMENTATION phase")

        brief = project_state.brief or "No brief provided"
        capabilities = project_state.capabilities or ["generic"]

        # Load PRD if exists
        prd_content = ""
        workspace = project_state.workspace_path
        if workspace:
            prd_path = Path(workspace) / "artifacts" / "planning" / "PRD.md"
            if prd_path.exists():
                prd_content = prd_path.read_text()[:2000]

        prompt = f"""You are a technical writer. Generate documentation for this project.

PROJECT: {project_state.project_name}
BRIEF: {brief}
CAPABILITIES: {", ".join(capabilities)}
APP_URL: {project_state.app_url or "Not deployed yet"}
REPO_URL: {project_state.app_repo_url or "Not available"}

PRD SUMMARY:
{prd_content[:1000] if prd_content else "PRD not yet generated"}

Generate JSON with these keys:

1. "system_overview": Markdown overview with:
   - Project purpose
   - Key components
   - Architecture summary
   - Technology stack

2. "how_to_run": Markdown guide with:
   - Prerequisites
   - Installation steps
   - Running locally
   - Configuration

3. "api_reference": Markdown API docs with:
   - Endpoints
   - Request/response formats
   - Authentication
   - Examples

4. "release_notes": Markdown release notes with:
   - Version
   - Features
   - Known issues
   - Roadmap

Output ONLY valid JSON."""

        try:
            result = await self.registry.generate(
                prompt=prompt,
                model=context.model,
                context=context,
                max_tokens=3500,
            )

            text = result.text.strip()
            if text.startswith("```"):
                text = text.split("```")[1]
                if text.startswith("json"):
                    text = text[4:]
                text = text.strip()

            output = json.loads(text)

            # Save artifacts
            artifacts_dir = self._get_artifacts_dir(project_state, "documentation")
            saved_paths = []

            # Save system overview
            overview_path = artifacts_dir / "system_overview.md"
            content = output.get("system_overview", "System overview")
            if isinstance(content, dict):
                content = json.dumps(content, indent=2)
            overview_path.write_text(content)
            saved_paths.append(str(overview_path))

            # Save how to run
            run_path = artifacts_dir / "how_to_run.md"
            content = output.get("how_to_run", "How to run guide")
            if isinstance(content, dict):
                content = json.dumps(content, indent=2)
            run_path.write_text(content)
            saved_paths.append(str(run_path))

            # Save API reference
            api_path = artifacts_dir / "api_reference.md"
            content = output.get("api_reference", "API reference")
            if isinstance(content, dict):
                content = json.dumps(content, indent=2)
            api_path.write_text(content)
            saved_paths.append(str(api_path))

            # Save release notes
            notes_path = artifacts_dir / "release_notes.md"
            content = output.get("release_notes", "Release notes")
            if isinstance(content, dict):
                content = json.dumps(content, indent=2)
            notes_path.write_text(content)
            saved_paths.append(str(notes_path))

            return {
                "artifacts": saved_paths,
                "summary": f"Documentation phase completed. Generated {len(saved_paths)} artifacts.",
                "agents": ["documentarian_agent"],
            }

        except Exception as e:
            logger.error(f"Documentation phase failed: {e}")
            return {
                "artifacts": [],
                "summary": f"Documentation phase failed: {str(e)}",
                "agents": ["documentarian_agent"],
            }

    def _get_artifacts_dir(self, project_state: ProjectState, phase: str) -> Path:
        """Get artifacts directory for a phase, creating if needed."""
        workspace = project_state.workspace_path
        if not workspace:
            workspace = f"/home/user/.orchestrator/workspaces/{project_state.project_id}"

        artifacts_dir = Path(workspace) / "artifacts" / phase
        artifacts_dir.mkdir(parents=True, exist_ok=True)
        return artifacts_dir


# Singleton instance
_execution_service: PhaseExecutionService | None = None


def get_execution_service() -> PhaseExecutionService:
    """Get the phase execution service singleton."""
    global _execution_service
    if _execution_service is None:
        _execution_service = PhaseExecutionService()
    return _execution_service
