"""
Planning Pipeline Service for RSC.

Coordinates multi-agent consensus to generate planning artifacts:
- PRD.md (Hybrid Grade - exec + engineering)
- architecture.md (with Mermaid diagrams)
- feature_backlog.json
- feature_story_map.md
- skills_plan.json

Agents involved: Architect → Reviewer → Consensus → Documentarian → Steward
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


class PlanningPipelineService:
    """Service to run the full planning pipeline with multi-agent consensus."""

    def __init__(self):
        self.registry = get_provider_registry()

    async def run_planning_pipeline(
        self,
        project_state: ProjectState,
        user: UserProfile,
    ) -> dict[str, Any]:
        """Run the complete planning pipeline.

        Args:
            project_state: Current project state.
            user: User profile with LLM credentials.

        Returns:
            Dict containing artifact paths and metadata.
        """
        logger.info(f"Starting planning pipeline for project {project_state.project_id}")

        # Build agent context
        model = user.default_model or "claude-sonnet-4-5-20250929"
        context = AgentContext(
            project_state=project_state,
            task=TaskDefinition(
                task_id="planning_pipeline",
                description="Generate planning artifacts",
            ),
            user_id=user.user_id,
            llm_api_key=user.anthropic_api_key,
            llm_provider=user.default_provider or "anthropic",
            model=model,
        )

        # Load domain knowledge if applicable
        domain_context = await self._load_domain_context(project_state)

        # Step 1: Architect generates drafts
        logger.info("Step 1: Architect generating drafts")
        architect_output = await self._run_architect(project_state, context, domain_context)

        # Step 2: Reviewer critiques
        logger.info("Step 2: Reviewer providing feedback")
        reviewer_output = await self._run_reviewer(project_state, context, architect_output)

        # Step 3: Consensus merges
        logger.info("Step 3: Consensus merging outputs")
        consensus_output = await self._run_consensus(
            project_state, context, architect_output, reviewer_output
        )

        # Step 4: Documentarian finalizes
        logger.info("Step 4: Documentarian finalizing artifacts")
        final_artifacts = await self._run_documentarian(project_state, context, consensus_output)

        # Step 5: Steward saves artifacts
        logger.info("Step 5: Steward saving artifacts")
        saved_paths = await self._run_steward(project_state, final_artifacts)

        logger.info(f"Planning pipeline completed. Saved {len(saved_paths)} artifacts")

        return {
            "artifacts": saved_paths,
            "summary": f"Generated {len(saved_paths)} planning artifacts",
            "agents": ["architect", "reviewer", "consensus", "documentarian", "steward"],
        }

    async def _load_domain_context(self, project_state: ProjectState) -> str:
        """Load domain-specific context based on project brief/capabilities."""
        context_parts = []

        brief = project_state.brief or ""
        capabilities = project_state.capabilities or []

        # Check for territory-related projects
        territory_keywords = ["territory", "territory optimizer", "territory alignment"]
        if any(kw in brief.lower() for kw in territory_keywords) or "territory_alignment" in capabilities:
            # Load territory blueprint if it exists
            blueprint_path = Path(__file__).parent.parent.parent / "docs" / "territory_system_blueprint.md"
            if blueprint_path.exists():
                context_parts.append(f"Territory System Blueprint:\n{blueprint_path.read_text()}")

        return "\n\n".join(context_parts)

    async def _run_architect(
        self,
        project_state: ProjectState,
        context: AgentContext,
        domain_context: str,
    ) -> dict[str, str]:
        """Architect agent generates initial drafts."""
        brief = project_state.brief or "No brief provided"
        capabilities = ", ".join(project_state.capabilities) if project_state.capabilities else "generic"

        prompt = f"""You are an experienced software architect. Generate planning artifacts for this project.

PROJECT: {project_state.project_name}
CLIENT: {project_state.client}
BRIEF: {brief}
CAPABILITIES: {capabilities}

{f"DOMAIN CONTEXT:{chr(10)}{domain_context}" if domain_context else ""}

Generate the following artifacts as JSON with these keys:

1. "prd_draft": A comprehensive Product Requirements Document with:
   - Executive Summary (3-5 sentences for C-suite)
   - Goals and Success Metrics (with KPIs)
   - Functional Requirements (detailed)
   - Non-Functional Requirements
   - User Stories / Flows
   - Data Requirements
   - Constraints and Assumptions
   - Risks and Mitigations
   - Timeline Overview

2. "architecture_draft": Technical architecture document with:
   - System Overview
   - Component Architecture (describe main components)
   - Data Flow (how data moves through system)
   - Technology Stack recommendations
   - API Contracts (if applicable)
   - Deployment Architecture
   - Security Considerations

3. "backlog_draft": JSON array of feature objects with fields:
   - id: string
   - title: string
   - description: string
   - priority: "high" | "medium" | "low"
   - effort_points: number (1-8)
   - dependencies: string[]

4. "skills_plan_draft": JSON object mapping capabilities to required skills

Output ONLY valid JSON with these four keys."""

        try:
            result = await self.registry.generate(
                prompt=prompt,
                model=context.model,
                context=context,
                max_tokens=4000,
            )

            # Parse JSON from response
            text = result.text.strip()
            # Handle markdown code blocks
            if text.startswith("```"):
                text = text.split("```")[1]
                if text.startswith("json"):
                    text = text[4:]
                text = text.strip()

            return json.loads(text)
        except Exception as e:
            logger.error(f"Architect failed: {e}")
            # Return minimal drafts on failure
            return {
                "prd_draft": f"# PRD for {project_state.project_name}\n\n{brief}",
                "architecture_draft": f"# Architecture for {project_state.project_name}\n\nCapabilities: {capabilities}",
                "backlog_draft": [{"id": "1", "title": "Initial setup", "priority": "high", "effort_points": 3}],
                "skills_plan_draft": {"capabilities": project_state.capabilities or ["generic"]},
            }

    async def _run_reviewer(
        self,
        project_state: ProjectState,
        context: AgentContext,
        architect_output: dict[str, Any],
    ) -> dict[str, str]:
        """Reviewer agent critiques architect's output."""
        prompt = f"""You are a senior technical reviewer. Review these planning drafts and provide feedback.

PROJECT: {project_state.project_name}
BRIEF: {project_state.brief or "No brief provided"}

ARCHITECT'S DRAFTS:
{json.dumps(architect_output, indent=2)[:3000]}...

Provide feedback as JSON with these keys:
- "prd_feedback": List of improvements for the PRD
- "architecture_feedback": List of improvements for architecture
- "backlog_feedback": List of improvements for backlog
- "missing_elements": Things the architect missed
- "risks_identified": Additional risks to consider
- "recommendations": Priority recommendations

Be constructive and specific. Output ONLY valid JSON."""

        try:
            result = await self.registry.generate(
                prompt=prompt,
                model=context.model,
                context=context,
                max_tokens=2000,
            )

            text = result.text.strip()
            if text.startswith("```"):
                text = text.split("```")[1]
                if text.startswith("json"):
                    text = text[4:]
                text = text.strip()

            return json.loads(text)
        except Exception as e:
            logger.error(f"Reviewer failed: {e}")
            return {
                "prd_feedback": ["Review completed"],
                "architecture_feedback": ["Architecture looks reasonable"],
                "backlog_feedback": ["Backlog is well-structured"],
                "missing_elements": [],
                "risks_identified": [],
                "recommendations": [],
            }

    async def _run_consensus(
        self,
        project_state: ProjectState,
        context: AgentContext,
        architect_output: dict[str, Any],
        reviewer_output: dict[str, Any],
    ) -> dict[str, Any]:
        """Consensus agent merges architect and reviewer outputs."""
        # Simply merge the outputs - in production this would be more sophisticated
        return {
            "architect": architect_output,
            "reviewer": reviewer_output,
            "consensus_notes": "Merged architect drafts with reviewer feedback",
        }

    async def _run_documentarian(
        self,
        project_state: ProjectState,
        context: AgentContext,
        consensus_output: dict[str, Any],
    ) -> dict[str, str]:
        """Documentarian agent finalizes artifacts into polished documents."""
        architect = consensus_output.get("architect", {})
        reviewer = consensus_output.get("reviewer", {})

        # Generate final PRD
        prd_content = await self._generate_final_prd(project_state, context, architect, reviewer)

        # Generate final architecture (with Mermaid diagrams)
        arch_content = await self._generate_final_architecture(project_state, context, architect, reviewer)

        # Generate backlog JSON
        backlog_json = json.dumps(architect.get("backlog_draft", []), indent=2)

        # Generate story map
        story_map = self._generate_story_map(project_state, architect.get("backlog_draft", []))

        # Generate skills plan
        skills_plan = json.dumps(architect.get("skills_plan_draft", {}), indent=2)

        return {
            "PRD.md": prd_content,
            "architecture.md": arch_content,
            "feature_backlog.json": backlog_json,
            "feature_story_map.md": story_map,
            "skills_plan.json": skills_plan,
        }

    async def _generate_final_prd(
        self,
        project_state: ProjectState,
        context: AgentContext,
        architect: dict,
        reviewer: dict,
    ) -> str:
        """Generate the final PRD document."""
        prd_draft = architect.get("prd_draft", "")
        feedback = reviewer.get("prd_feedback", [])

        prompt = f"""Create a polished Product Requirements Document (PRD) in Markdown.

PROJECT: {project_state.project_name}
BRIEF: {project_state.brief or "No brief provided"}
CAPABILITIES: {", ".join(project_state.capabilities or ["generic"])}

DRAFT PRD:
{prd_draft if isinstance(prd_draft, str) else json.dumps(prd_draft, indent=2)}

REVIEWER FEEDBACK:
{json.dumps(feedback, indent=2)}

Create a comprehensive PRD with these sections:
1. Executive Summary (C-suite friendly, 3-5 sentences)
2. Goals and Success Metrics
3. Functional Requirements
4. Non-Functional Requirements
5. User Stories / Flows
6. Data Requirements and Assumptions
7. Constraints
8. Risks and Mitigations
9. Timeline Overview
10. Appendix (if needed)

Output ONLY the Markdown document, no code blocks."""

        try:
            result = await self.registry.generate(
                prompt=prompt,
                model=context.model,
                context=context,
                max_tokens=3000,
            )
            return result.text.strip()
        except Exception as e:
            logger.error(f"PRD generation failed: {e}")
            return f"""# Product Requirements Document

## {project_state.project_name}

### Executive Summary
{project_state.brief or "Project requirements to be defined."}

### Capabilities
{", ".join(project_state.capabilities or ["generic"])}

### Status
Draft - generated {datetime.utcnow().isoformat()}
"""

    async def _generate_final_architecture(
        self,
        project_state: ProjectState,
        context: AgentContext,
        architect: dict,
        reviewer: dict,
    ) -> str:
        """Generate the final architecture document with Mermaid diagrams."""
        arch_draft = architect.get("architecture_draft", "")
        feedback = reviewer.get("architecture_feedback", [])
        capabilities = project_state.capabilities or []

        # Determine which diagrams to include
        include_sequence = any(cap in capabilities for cap in ["app_build", "backend_api", "service_api"])
        include_data_flow = any(cap in capabilities for cap in ["data_pipeline", "analytics_forecasting", "ml_classification"])

        prompt = f"""Create a polished Technical Architecture Document in Markdown with Mermaid diagrams.

PROJECT: {project_state.project_name}
CAPABILITIES: {", ".join(capabilities)}

DRAFT ARCHITECTURE:
{arch_draft if isinstance(arch_draft, str) else json.dumps(arch_draft, indent=2)}

REVIEWER FEEDBACK:
{json.dumps(feedback, indent=2)}

Include these sections:
1. System Overview (with Mermaid flowchart)
2. Component Architecture
3. {"Data Flow Diagram (Mermaid)" if include_data_flow else "Data Considerations"}
4. Technology Stack
5. {"API Contracts and Sequence Diagrams (Mermaid)" if include_sequence else "Integration Points"}
6. Deployment Architecture
7. Security Considerations
8. Non-Functional Requirements

Use Mermaid syntax for diagrams like:
```mermaid
flowchart TD
    A[Component] --> B[Component]
```

Output ONLY the Markdown document."""

        try:
            result = await self.registry.generate(
                prompt=prompt,
                model=context.model,
                context=context,
                max_tokens=3000,
            )
            return result.text.strip()
        except Exception as e:
            logger.error(f"Architecture generation failed: {e}")
            return f"""# Technical Architecture

## {project_state.project_name}

### System Overview

```mermaid
flowchart TD
    Client[Client] --> API[API Layer]
    API --> Service[Service Layer]
    Service --> Data[Data Layer]
```

### Capabilities
{", ".join(capabilities)}

### Status
Draft - generated {datetime.utcnow().isoformat()}
"""

    def _generate_story_map(self, project_state: ProjectState, backlog: list) -> str:
        """Generate a story map from the backlog."""
        if not backlog:
            backlog = []

        high_priority = [f for f in backlog if f.get("priority") == "high"]
        medium_priority = [f for f in backlog if f.get("priority") == "medium"]
        low_priority = [f for f in backlog if f.get("priority") == "low"]

        content = f"""# Feature Story Map

## {project_state.project_name}

### High Priority (Must Have)
"""
        for feature in high_priority:
            content += f"- **{feature.get('title', 'Untitled')}**: {feature.get('description', 'No description')}\n"

        content += "\n### Medium Priority (Should Have)\n"
        for feature in medium_priority:
            content += f"- **{feature.get('title', 'Untitled')}**: {feature.get('description', 'No description')}\n"

        content += "\n### Low Priority (Nice to Have)\n"
        for feature in low_priority:
            content += f"- **{feature.get('title', 'Untitled')}**: {feature.get('description', 'No description')}\n"

        content += f"\n---\nGenerated: {datetime.utcnow().isoformat()}\n"

        return content

    async def _run_steward(
        self,
        project_state: ProjectState,
        artifacts: dict[str, str],
    ) -> list[str]:
        """Steward agent saves artifacts to workspace."""
        saved_paths = []

        workspace_path = project_state.workspace_path
        if not workspace_path:
            # Use default workspace location
            workspace_path = f"/home/user/.orchestrator/workspaces/{project_state.project_id}"

        artifacts_dir = Path(workspace_path) / "artifacts" / "planning"
        artifacts_dir.mkdir(parents=True, exist_ok=True)

        for filename, content in artifacts.items():
            file_path = artifacts_dir / filename
            file_path.write_text(content)
            saved_paths.append(str(file_path))
            logger.info(f"Saved artifact: {file_path}")

        return saved_paths


# Singleton instance
_planning_service: PlanningPipelineService | None = None


def get_planning_service() -> PlanningPipelineService:
    """Get the planning pipeline service singleton."""
    global _planning_service
    if _planning_service is None:
        _planning_service = PlanningPipelineService()
    return _planning_service
