"""
Feature Engine Service

Service for creating, planning, and building features.
"""

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from orchestrator_v2.feature_engine.models import (
    ArtifactInfo,
    FeatureRequest,
    FeatureStatus,
)
from orchestrator_v2.feature_engine.repository import get_feature_repository
from orchestrator_v2.engine.state_models import ProjectState
from orchestrator_v2.llm.provider_registry import registry
from orchestrator_v2.user.models import UserProfile


class FeatureEngineService:
    """Service for feature management and execution."""

    def __init__(self):
        self.repo = get_feature_repository()

    async def create_feature(
        self,
        project_id: str,
        title: str,
        description: str = "",
        priority: str = "medium",
        tags: list[str] | None = None,
    ) -> FeatureRequest:
        """Create a new feature request."""
        # Get next feature number
        next_num = await self.repo.get_next_feature_number(project_id)
        feature_id = f"F-{next_num:03d}"

        now = datetime.now(timezone.utc)
        feature = FeatureRequest(
            feature_id=feature_id,
            title=title,
            description=description,
            status=FeatureStatus.SUBMITTED,
            created_at=now,
            updated_at=now,
            priority=priority,
            tags=tags or [],
        )

        await self.repo.save_feature(project_id, feature)
        return feature

    async def plan_feature(
        self,
        project_id: str,
        feature_id: str,
        project_state: ProjectState,
        workspace: Path,
        user: UserProfile,
    ) -> dict[str, Any]:
        """
        Generate a plan for a feature using LLM.

        Creates:
        - feature_spec.md: Requirements and acceptance criteria
        - feature_design.md: Technical design approach
        """
        feature = await self.repo.get_feature(project_id, feature_id)
        if not feature:
            raise ValueError(f"Feature not found: {feature_id}")

        feature.status = FeatureStatus.PLANNED
        feature.updated_at = datetime.now(timezone.utc)

        prompt = f"""You are a senior software architect. Create a detailed plan for this feature.

PROJECT CONTEXT:
- Name: {project_state.project_name}
- Brief: {project_state.brief or 'No brief'}
- Capabilities: {', '.join(project_state.capabilities or ['generic'])}

FEATURE REQUEST:
- ID: {feature.feature_id}
- Title: {feature.title}
- Description: {feature.description or 'No description provided'}
- Priority: {feature.priority}

Generate a comprehensive feature plan with:
1. Detailed requirements specification
2. Acceptance criteria (testable)
3. Technical design approach
4. File changes needed
5. Estimated complexity

Respond in JSON format:
{{
  "spec": {{
    "requirements": ["req1", "req2"],
    "acceptance_criteria": ["criteria1", "criteria2"],
    "user_stories": [
      {{"as_a": "user", "i_want": "capability", "so_that": "benefit"}}
    ],
    "out_of_scope": ["item1"]
  }},
  "design": {{
    "approach": "Technical approach description",
    "components": ["component1", "component2"],
    "file_changes": [
      {{"file": "path/to/file.ts", "action": "create|modify", "description": "what changes"}}
    ],
    "dependencies": ["dependency1"],
    "risks": ["risk1"]
  }},
  "complexity": "low|medium|high",
  "estimated_effort": "Description of effort"
}}"""

        try:
            model = user.default_model or "claude-sonnet-4-5-20250929"
            provider = user.default_provider or "anthropic"
            api_key = user.anthropic_api_key

            response = await registry.generate(
                provider=provider,
                model=model,
                prompt=prompt,
                api_key=api_key,
                max_tokens=3000,
                context={"project_id": project_id, "feature_id": feature_id, "phase": "feature_plan"}
            )

            content = response.get("content", "")
            json_start = content.find("{")
            json_end = content.rfind("}") + 1
            if json_start >= 0 and json_end > json_start:
                plan_data = json.loads(content[json_start:json_end])
            else:
                raise ValueError("No valid JSON in LLM response")

            # Create artifacts directory
            feature_dir = workspace / "artifacts" / "features" / feature_id
            feature_dir.mkdir(parents=True, exist_ok=True)

            artifacts = []

            # Generate spec markdown
            spec_content = self._format_spec_markdown(feature, plan_data.get("spec", {}))
            spec_path = feature_dir / "feature_spec.md"
            spec_path.write_text(spec_content)
            artifacts.append(ArtifactInfo(
                id=str(uuid.uuid4()),
                name="feature_spec.md",
                path=str(spec_path),
                artifact_type="markdown",
                created_at=datetime.now(timezone.utc)
            ))

            # Generate design markdown
            design_content = self._format_design_markdown(feature, plan_data.get("design", {}))
            design_path = feature_dir / "feature_design.md"
            design_path.write_text(design_content)
            artifacts.append(ArtifactInfo(
                id=str(uuid.uuid4()),
                name="feature_design.md",
                path=str(design_path),
                artifact_type="markdown",
                created_at=datetime.now(timezone.utc)
            ))

            # Update feature
            feature.artifacts.extend(artifacts)
            feature.plan_summary = f"Complexity: {plan_data.get('complexity', 'medium')}. {plan_data.get('estimated_effort', '')}"
            await self.repo.save_feature(project_id, feature)

            return {
                "feature_id": feature_id,
                "status": "planned",
                "artifacts": [a.model_dump() for a in artifacts],
                "summary": feature.plan_summary,
                "token_usage": response.get("usage", {})
            }

        except Exception as e:
            feature.status = FeatureStatus.FAILED
            await self.repo.save_feature(project_id, feature)
            raise

    async def build_feature(
        self,
        project_id: str,
        feature_id: str,
        project_state: ProjectState,
        workspace: Path,
        user: UserProfile,
    ) -> dict[str, Any]:
        """
        Generate implementation artifacts for a feature.

        Creates:
        - Code snippets
        - Test stubs
        - Implementation guide
        """
        feature = await self.repo.get_feature(project_id, feature_id)
        if not feature:
            raise ValueError(f"Feature not found: {feature_id}")

        feature.status = FeatureStatus.BUILDING
        feature.updated_at = datetime.now(timezone.utc)

        # Read existing spec if available
        spec_content = ""
        feature_dir = workspace / "artifacts" / "features" / feature_id
        spec_path = feature_dir / "feature_spec.md"
        if spec_path.exists():
            spec_content = spec_path.read_text()[:2000]

        prompt = f"""You are a senior developer. Generate implementation artifacts for this feature.

PROJECT CONTEXT:
- Name: {project_state.project_name}
- Capabilities: {', '.join(project_state.capabilities or ['generic'])}

FEATURE:
- ID: {feature.feature_id}
- Title: {feature.title}
- Description: {feature.description or 'No description'}

{f'SPEC SUMMARY:{chr(10)}{spec_content}' if spec_content else ''}

Generate implementation artifacts:
1. Key code snippets (components, functions, API routes)
2. Test stubs
3. Step-by-step implementation guide

Respond in JSON format:
{{
  "code_snippets": [
    {{
      "filename": "component.tsx",
      "language": "typescript",
      "content": "// code here",
      "description": "What this file does"
    }}
  ],
  "test_stubs": [
    {{
      "filename": "component.test.ts",
      "language": "typescript",
      "content": "// test code",
      "description": "What tests cover"
    }}
  ],
  "implementation_guide": [
    "Step 1: Do this",
    "Step 2: Do that"
  ],
  "notes": "Additional implementation notes"
}}"""

        try:
            model = user.default_model or "claude-sonnet-4-5-20250929"
            provider = user.default_provider or "anthropic"
            api_key = user.anthropic_api_key

            response = await registry.generate(
                provider=provider,
                model=model,
                prompt=prompt,
                api_key=api_key,
                max_tokens=4000,
                context={"project_id": project_id, "feature_id": feature_id, "phase": "feature_build"}
            )

            content = response.get("content", "")
            json_start = content.find("{")
            json_end = content.rfind("}") + 1
            if json_start >= 0 and json_end > json_start:
                build_data = json.loads(content[json_start:json_end])
            else:
                raise ValueError("No valid JSON in LLM response")

            # Save artifacts
            feature_dir.mkdir(parents=True, exist_ok=True)
            code_dir = feature_dir / "code"
            code_dir.mkdir(exist_ok=True)

            artifacts = []

            # Save code snippets
            for snippet in build_data.get("code_snippets", []):
                code_path = code_dir / snippet["filename"]
                code_path.write_text(snippet.get("content", ""))
                artifacts.append(ArtifactInfo(
                    id=str(uuid.uuid4()),
                    name=snippet["filename"],
                    path=str(code_path),
                    artifact_type="code",
                    created_at=datetime.now(timezone.utc)
                ))

            # Save test stubs
            for test in build_data.get("test_stubs", []):
                test_path = code_dir / test["filename"]
                test_path.write_text(test.get("content", ""))
                artifacts.append(ArtifactInfo(
                    id=str(uuid.uuid4()),
                    name=test["filename"],
                    path=str(test_path),
                    artifact_type="test",
                    created_at=datetime.now(timezone.utc)
                ))

            # Save implementation guide
            guide_content = self._format_implementation_guide(feature, build_data)
            guide_path = feature_dir / "implementation_guide.md"
            guide_path.write_text(guide_content)
            artifacts.append(ArtifactInfo(
                id=str(uuid.uuid4()),
                name="implementation_guide.md",
                path=str(guide_path),
                artifact_type="markdown",
                created_at=datetime.now(timezone.utc)
            ))

            # Update feature
            feature.status = FeatureStatus.COMPLETED
            feature.artifacts.extend(artifacts)
            feature.build_summary = f"Generated {len(build_data.get('code_snippets', []))} code files, {len(build_data.get('test_stubs', []))} tests"
            await self.repo.save_feature(project_id, feature)

            return {
                "feature_id": feature_id,
                "status": "completed",
                "artifacts": [a.model_dump() for a in artifacts],
                "summary": feature.build_summary,
                "token_usage": response.get("usage", {})
            }

        except Exception as e:
            feature.status = FeatureStatus.FAILED
            await self.repo.save_feature(project_id, feature)
            raise

    def _format_spec_markdown(self, feature: FeatureRequest, spec: dict) -> str:
        """Format spec as markdown."""
        lines = [
            f"# Feature Specification: {feature.title}",
            f"**ID:** {feature.feature_id}",
            f"**Priority:** {feature.priority}",
            "",
            "## Requirements",
            "",
        ]

        for req in spec.get("requirements", []):
            lines.append(f"- {req}")

        lines.extend(["", "## Acceptance Criteria", ""])
        for criteria in spec.get("acceptance_criteria", []):
            lines.append(f"- [ ] {criteria}")

        lines.extend(["", "## User Stories", ""])
        for story in spec.get("user_stories", []):
            lines.append(f"- As a **{story.get('as_a', 'user')}**, I want to **{story.get('i_want', '')}** so that **{story.get('so_that', '')}**")

        if spec.get("out_of_scope"):
            lines.extend(["", "## Out of Scope", ""])
            for item in spec["out_of_scope"]:
                lines.append(f"- {item}")

        return "\n".join(lines)

    def _format_design_markdown(self, feature: FeatureRequest, design: dict) -> str:
        """Format design as markdown."""
        lines = [
            f"# Technical Design: {feature.title}",
            "",
            "## Approach",
            design.get("approach", "No approach specified."),
            "",
            "## Components",
            "",
        ]

        for comp in design.get("components", []):
            lines.append(f"- {comp}")

        lines.extend(["", "## File Changes", ""])
        for change in design.get("file_changes", []):
            lines.append(f"- `{change.get('file', '')}` ({change.get('action', 'modify')}): {change.get('description', '')}")

        if design.get("dependencies"):
            lines.extend(["", "## Dependencies", ""])
            for dep in design["dependencies"]:
                lines.append(f"- {dep}")

        if design.get("risks"):
            lines.extend(["", "## Risks", ""])
            for risk in design["risks"]:
                lines.append(f"- {risk}")

        return "\n".join(lines)

    def _format_implementation_guide(self, feature: FeatureRequest, build_data: dict) -> str:
        """Format implementation guide as markdown."""
        lines = [
            f"# Implementation Guide: {feature.title}",
            "",
            "## Steps",
            "",
        ]

        for i, step in enumerate(build_data.get("implementation_guide", []), 1):
            lines.append(f"{i}. {step}")

        if build_data.get("notes"):
            lines.extend(["", "## Notes", "", build_data["notes"]])

        lines.extend(["", "## Generated Files", ""])
        for snippet in build_data.get("code_snippets", []):
            lines.append(f"- `{snippet['filename']}`: {snippet.get('description', '')}")

        for test in build_data.get("test_stubs", []):
            lines.append(f"- `{test['filename']}`: {test.get('description', '')}")

        return "\n".join(lines)


# Singleton service instance
_feature_service: FeatureEngineService | None = None


def get_feature_service() -> FeatureEngineService:
    """Get the singleton feature engine service instance."""
    global _feature_service
    if _feature_service is None:
        _feature_service = FeatureEngineService()
    return _feature_service
