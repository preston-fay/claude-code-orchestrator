"""
App Builder Service

Service for planning and scaffolding app builds using LLM.
"""

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from orchestrator_v2.app_builder.models import (
    AppBuildState,
    AppBuildStatus,
    ArtifactInfo,
)
from orchestrator_v2.engine.state_models import ProjectState
from orchestrator_v2.llm.provider_registry import registry
from orchestrator_v2.user.models import UserProfile


class AppBuilderService:
    """Service for app build planning and scaffolding."""

    def __init__(self):
        self.artifact_phase = "app_build"

    async def plan_app_build(
        self,
        project_state: ProjectState,
        workspace: Path,
        user: UserProfile,
        brief_override: str | None = None,
        capabilities_override: list[str] | None = None,
    ) -> dict[str, Any]:
        """
        Generate app build plan using LLM.

        Creates:
        - app_prd.md: Product requirements document
        - app_architecture.md: System architecture
        - app_user_flows.md: User flows and interactions
        """
        # Update state to planning
        if not hasattr(project_state, 'app_build') or project_state.app_build is None:
            project_state.app_build = AppBuildState()

        project_state.app_build.status = AppBuildStatus.PLANNING
        project_state.app_build.last_updated_at = datetime.now(timezone.utc)
        project_state.app_build.last_run_id = str(uuid.uuid4())

        brief = brief_override or project_state.brief or "No brief provided"
        capabilities = capabilities_override or project_state.capabilities or []

        # Build the planning prompt
        prompt = f"""You are an expert software architect. Generate a comprehensive app build plan.

PROJECT BRIEF:
{brief}

CAPABILITIES:
{', '.join(capabilities) if capabilities else 'General purpose application'}

Generate a complete app build plan with the following documents:

1. **Product Requirements Document (PRD)**: Clear requirements, user stories, acceptance criteria
2. **System Architecture**: Components, data flow, technology choices, API design
3. **User Flows**: Key user journeys, screens/pages, interactions

Respond in JSON format:
{{
  "prd": {{
    "title": "App Name PRD",
    "overview": "Brief overview",
    "goals": ["goal1", "goal2"],
    "user_stories": [
      {{"as_a": "user type", "i_want": "capability", "so_that": "benefit"}}
    ],
    "functional_requirements": ["req1", "req2"],
    "non_functional_requirements": ["perf req", "security req"],
    "acceptance_criteria": ["criteria1", "criteria2"]
  }},
  "architecture": {{
    "overview": "Architecture overview",
    "components": [
      {{"name": "Component", "purpose": "What it does", "technology": "Tech stack"}}
    ],
    "data_flow": "Description of data flow",
    "api_design": [
      {{"endpoint": "/api/resource", "method": "GET", "purpose": "Description"}}
    ],
    "technology_stack": {{
      "frontend": "React/TypeScript",
      "backend": "FastAPI/Python",
      "database": "PostgreSQL",
      "deployment": "Docker/Cloud"
    }},
    "security_considerations": ["consideration1", "consideration2"]
  }},
  "user_flows": [
    {{
      "name": "Flow Name",
      "description": "What user accomplishes",
      "steps": ["Step 1", "Step 2", "Step 3"],
      "screens": ["Screen1", "Screen2"]
    }}
  ]
}}"""

        try:
            # Get LLM response
            model = user.default_model or "claude-sonnet-4-5-20250929"
            provider = user.default_provider or "anthropic"
            api_key = user.anthropic_api_key

            response = await registry.generate(
                provider=provider,
                model=model,
                prompt=prompt,
                api_key=api_key,
                max_tokens=4000,
                context={"project_id": project_state.project_id, "phase": "app_build_plan"}
            )

            # Parse response
            content = response.get("content", "")

            # Extract JSON from response
            json_start = content.find("{")
            json_end = content.rfind("}") + 1
            if json_start >= 0 and json_end > json_start:
                plan_data = json.loads(content[json_start:json_end])
            else:
                raise ValueError("No valid JSON found in LLM response")

            # Create artifacts directory
            artifacts_dir = workspace / "artifacts" / self.artifact_phase
            artifacts_dir.mkdir(parents=True, exist_ok=True)

            artifacts = []

            # Generate PRD markdown
            prd_content = self._format_prd_markdown(plan_data.get("prd", {}))
            prd_path = artifacts_dir / "app_prd.md"
            prd_path.write_text(prd_content)
            artifacts.append(ArtifactInfo(
                id=str(uuid.uuid4()),
                name="app_prd.md",
                path=str(prd_path),
                artifact_type="markdown",
                created_at=datetime.now(timezone.utc)
            ))

            # Generate architecture markdown
            arch_content = self._format_architecture_markdown(plan_data.get("architecture", {}))
            arch_path = artifacts_dir / "app_architecture.md"
            arch_path.write_text(arch_content)
            artifacts.append(ArtifactInfo(
                id=str(uuid.uuid4()),
                name="app_architecture.md",
                path=str(arch_path),
                artifact_type="markdown",
                created_at=datetime.now(timezone.utc)
            ))

            # Generate user flows markdown
            flows_content = self._format_user_flows_markdown(plan_data.get("user_flows", []))
            flows_path = artifacts_dir / "app_user_flows.md"
            flows_path.write_text(flows_content)
            artifacts.append(ArtifactInfo(
                id=str(uuid.uuid4()),
                name="app_user_flows.md",
                path=str(flows_path),
                artifact_type="markdown",
                created_at=datetime.now(timezone.utc)
            ))

            # Update state
            project_state.app_build.artifacts.extend(artifacts)
            project_state.app_build.last_updated_at = datetime.now(timezone.utc)

            return {
                "status": "success",
                "artifacts": [a.model_dump() for a in artifacts],
                "summary": f"Generated app build plan with {len(artifacts)} artifacts",
                "token_usage": response.get("usage", {})
            }

        except Exception as e:
            project_state.app_build.status = AppBuildStatus.FAILED
            project_state.app_build.last_error = str(e)
            project_state.app_build.last_updated_at = datetime.now(timezone.utc)
            raise

    async def run_app_scaffold(
        self,
        project_state: ProjectState,
        workspace: Path,
        user: UserProfile,
        target_stack: str | None = None,
        include_tests: bool = True,
        include_docs: bool = True,
    ) -> dict[str, Any]:
        """
        Generate app scaffold artifacts using LLM.

        Creates:
        - app_structure.json: Directory and file structure
        - app_scaffold_instructions.md: How to apply changes
        - Example component files as artifacts
        """
        # Update state
        if not hasattr(project_state, 'app_build') or project_state.app_build is None:
            project_state.app_build = AppBuildState()

        project_state.app_build.status = AppBuildStatus.SCAFFOLDING
        project_state.app_build.last_updated_at = datetime.now(timezone.utc)
        project_state.app_build.last_run_id = str(uuid.uuid4())

        # Determine stack
        stack = target_stack or project_state.app_build.target_stack or "react-fastapi"
        project_state.app_build.target_stack = stack

        brief = project_state.brief or "No brief provided"
        capabilities = project_state.capabilities or []

        # Read existing PRD if available
        prd_content = ""
        prd_path = workspace / "artifacts" / self.artifact_phase / "app_prd.md"
        if prd_path.exists():
            prd_content = prd_path.read_text()[:3000]

        # Build scaffold prompt
        prompt = f"""You are an expert full-stack developer. Generate a complete app scaffold.

PROJECT BRIEF:
{brief}

CAPABILITIES:
{', '.join(capabilities) if capabilities else 'General purpose'}

TARGET STACK: {stack}
INCLUDE TESTS: {include_tests}
INCLUDE DOCS: {include_docs}

{f'PRD SUMMARY:{chr(10)}{prd_content[:1500]}' if prd_content else ''}

Generate a complete scaffold with:
1. Directory structure
2. Key file contents (components, API routes, models)
3. Configuration files
4. Setup instructions

Respond in JSON format:
{{
  "structure": {{
    "directories": [
      "src/",
      "src/components/",
      "src/pages/",
      "src/api/",
      "backend/",
      "backend/routes/",
      "tests/"
    ],
    "files": [
      {{
        "path": "src/App.tsx",
        "description": "Main application component",
        "key_imports": ["react", "react-router-dom"]
      }}
    ]
  }},
  "components": [
    {{
      "name": "AppShell.tsx",
      "path": "src/components/AppShell.tsx",
      "content": "// React component code here",
      "purpose": "Main application shell with navigation"
    }},
    {{
      "name": "HomePage.tsx",
      "path": "src/pages/HomePage.tsx",
      "content": "// React component code here",
      "purpose": "Landing page"
    }}
  ],
  "backend_files": [
    {{
      "name": "main.py",
      "path": "backend/main.py",
      "content": "# FastAPI app code here",
      "purpose": "FastAPI application entry point"
    }}
  ],
  "config_files": [
    {{
      "name": "package.json",
      "path": "package.json",
      "content": "// JSON content",
      "purpose": "Node.js dependencies"
    }}
  ],
  "instructions": {{
    "prerequisites": ["Node.js 18+", "Python 3.11+", "npm or yarn"],
    "setup_steps": [
      "Clone/create the repository",
      "Install frontend dependencies: npm install",
      "Install backend dependencies: pip install -r requirements.txt",
      "Start development servers"
    ],
    "environment_variables": [
      {{"name": "DATABASE_URL", "description": "Database connection string"}},
      {{"name": "API_KEY", "description": "API authentication key"}}
    ],
    "notes": "Additional setup notes"
  }}
}}"""

        try:
            # Get LLM response
            model = user.default_model or "claude-sonnet-4-5-20250929"
            provider = user.default_provider or "anthropic"
            api_key = user.anthropic_api_key

            response = await registry.generate(
                provider=provider,
                model=model,
                prompt=prompt,
                api_key=api_key,
                max_tokens=6000,
                context={"project_id": project_state.project_id, "phase": "app_scaffold"}
            )

            # Parse response
            content = response.get("content", "")

            json_start = content.find("{")
            json_end = content.rfind("}") + 1
            if json_start >= 0 and json_end > json_start:
                scaffold_data = json.loads(content[json_start:json_end])
            else:
                raise ValueError("No valid JSON found in LLM response")

            # Create artifacts directory
            artifacts_dir = workspace / "artifacts" / self.artifact_phase
            artifacts_dir.mkdir(parents=True, exist_ok=True)

            artifacts = []

            # Save structure JSON
            structure_path = artifacts_dir / "app_structure.json"
            structure_path.write_text(json.dumps(scaffold_data.get("structure", {}), indent=2))
            artifacts.append(ArtifactInfo(
                id=str(uuid.uuid4()),
                name="app_structure.json",
                path=str(structure_path),
                artifact_type="json",
                created_at=datetime.now(timezone.utc)
            ))

            # Generate instructions markdown
            instructions_content = self._format_instructions_markdown(scaffold_data.get("instructions", {}))
            instructions_path = artifacts_dir / "app_scaffold_instructions.md"
            instructions_path.write_text(instructions_content)
            artifacts.append(ArtifactInfo(
                id=str(uuid.uuid4()),
                name="app_scaffold_instructions.md",
                path=str(instructions_path),
                artifact_type="markdown",
                created_at=datetime.now(timezone.utc)
            ))

            # Save component files
            components_dir = artifacts_dir / "scaffold_components"
            components_dir.mkdir(exist_ok=True)

            for component in scaffold_data.get("components", []):
                comp_path = components_dir / component["name"]
                comp_path.write_text(component.get("content", f"// {component['name']}"))
                artifacts.append(ArtifactInfo(
                    id=str(uuid.uuid4()),
                    name=component["name"],
                    path=str(comp_path),
                    artifact_type="code",
                    created_at=datetime.now(timezone.utc)
                ))

            # Save backend files
            for backend_file in scaffold_data.get("backend_files", []):
                be_path = components_dir / backend_file["name"]
                be_path.write_text(backend_file.get("content", f"# {backend_file['name']}"))
                artifacts.append(ArtifactInfo(
                    id=str(uuid.uuid4()),
                    name=backend_file["name"],
                    path=str(be_path),
                    artifact_type="code",
                    created_at=datetime.now(timezone.utc)
                ))

            # Update state to completed
            project_state.app_build.status = AppBuildStatus.COMPLETED
            project_state.app_build.artifacts.extend(artifacts)
            project_state.app_build.last_updated_at = datetime.now(timezone.utc)

            return {
                "status": "success",
                "artifacts": [a.model_dump() for a in artifacts],
                "summary": f"Generated app scaffold with {len(artifacts)} artifacts",
                "token_usage": response.get("usage", {}),
                "next_steps": scaffold_data.get("instructions", {}).get("setup_steps", [])
            }

        except Exception as e:
            project_state.app_build.status = AppBuildStatus.FAILED
            project_state.app_build.last_error = str(e)
            project_state.app_build.last_updated_at = datetime.now(timezone.utc)
            raise

    def _format_prd_markdown(self, prd: dict) -> str:
        """Format PRD data as markdown."""
        lines = [
            f"# {prd.get('title', 'Product Requirements Document')}",
            "",
            "## Overview",
            prd.get("overview", "No overview provided."),
            "",
            "## Goals",
        ]

        for goal in prd.get("goals", []):
            lines.append(f"- {goal}")

        lines.extend(["", "## User Stories", ""])
        for story in prd.get("user_stories", []):
            lines.append(f"- As a **{story.get('as_a', 'user')}**, I want to **{story.get('i_want', '')}** so that **{story.get('so_that', '')}**")

        lines.extend(["", "## Functional Requirements", ""])
        for req in prd.get("functional_requirements", []):
            lines.append(f"- {req}")

        lines.extend(["", "## Non-Functional Requirements", ""])
        for req in prd.get("non_functional_requirements", []):
            lines.append(f"- {req}")

        lines.extend(["", "## Acceptance Criteria", ""])
        for criteria in prd.get("acceptance_criteria", []):
            lines.append(f"- [ ] {criteria}")

        return "\n".join(lines)

    def _format_architecture_markdown(self, arch: dict) -> str:
        """Format architecture data as markdown."""
        lines = [
            "# System Architecture",
            "",
            "## Overview",
            arch.get("overview", "No overview provided."),
            "",
            "## Components",
            "",
        ]

        for comp in arch.get("components", []):
            lines.append(f"### {comp.get('name', 'Component')}")
            lines.append(f"**Purpose:** {comp.get('purpose', 'N/A')}")
            lines.append(f"**Technology:** {comp.get('technology', 'N/A')}")
            lines.append("")

        lines.extend(["## Data Flow", "", arch.get("data_flow", "No data flow described."), ""])

        lines.extend(["## API Design", ""])
        for api in arch.get("api_design", []):
            lines.append(f"- `{api.get('method', 'GET')} {api.get('endpoint', '/')}` - {api.get('purpose', '')}")

        lines.extend(["", "## Technology Stack", ""])
        stack = arch.get("technology_stack", {})
        for key, value in stack.items():
            lines.append(f"- **{key.title()}:** {value}")

        lines.extend(["", "## Security Considerations", ""])
        for sec in arch.get("security_considerations", []):
            lines.append(f"- {sec}")

        return "\n".join(lines)

    def _format_user_flows_markdown(self, flows: list) -> str:
        """Format user flows data as markdown."""
        lines = ["# User Flows", ""]

        for i, flow in enumerate(flows, 1):
            lines.append(f"## {i}. {flow.get('name', 'Flow')}")
            lines.append("")
            lines.append(flow.get("description", "No description."))
            lines.append("")
            lines.append("### Steps")
            for j, step in enumerate(flow.get("steps", []), 1):
                lines.append(f"{j}. {step}")
            lines.append("")
            lines.append("### Screens")
            for screen in flow.get("screens", []):
                lines.append(f"- {screen}")
            lines.append("")

        return "\n".join(lines)

    def _format_instructions_markdown(self, instructions: dict) -> str:
        """Format setup instructions as markdown."""
        lines = [
            "# App Scaffold Instructions",
            "",
            "## Prerequisites",
            "",
        ]

        for prereq in instructions.get("prerequisites", []):
            lines.append(f"- {prereq}")

        lines.extend(["", "## Setup Steps", ""])
        for i, step in enumerate(instructions.get("setup_steps", []), 1):
            lines.append(f"{i}. {step}")

        lines.extend(["", "## Environment Variables", ""])
        for env in instructions.get("environment_variables", []):
            lines.append(f"- `{env.get('name', 'VAR')}`: {env.get('description', '')}")

        if instructions.get("notes"):
            lines.extend(["", "## Notes", "", instructions["notes"]])

        return "\n".join(lines)


# Singleton service instance
_app_builder_service: AppBuilderService | None = None


def get_app_builder_service() -> AppBuilderService:
    """Get the singleton app builder service instance."""
    global _app_builder_service
    if _app_builder_service is None:
        _app_builder_service = AppBuilderService()
    return _app_builder_service
