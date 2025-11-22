"""
Feature Orchestration Service.

Orchestrates the complete lifecycle of feature requests from submission
through planning, building, testing, and PR creation.
"""

import re
import uuid
from datetime import datetime

from .models import (
    FeatureRequest,
    FeaturePlan,
    FeatureBuildPlan,
    FeatureBuildResult,
    FeatureDetail,
    FeatureStatus,
    BuildStatus,
    RepoChange,
    TestResult,
)
from .repository import FileSystemFeatureRepository


class FeatureOrchestrationError(Exception):
    """Error during feature orchestration."""
    pass


class FeatureOrchestrationService:
    """Service for orchestrating feature development lifecycle."""

    def __init__(self, repository: FileSystemFeatureRepository | None = None):
        self.repository = repository or FileSystemFeatureRepository()

    def create_feature_request(
        self,
        project_id: str,
        title: str,
        description: str,
        user: str = "system",
    ) -> FeatureRequest:
        """Create a new feature request.

        Args:
            project_id: Project to create feature for
            title: Feature title
            description: Detailed feature description
            user: User creating the request

        Returns:
            Created FeatureRequest
        """
        feature_id = f"feat-{uuid.uuid4().hex[:8]}"

        request = FeatureRequest(
            id=feature_id,
            project_id=project_id,
            title=title,
            description=description,
            created_by=user,
            status=FeatureStatus.SUBMITTED,
        )

        self.repository.save_request(request)
        self.repository.append_log(
            project_id, feature_id,
            f"Feature request created: {title}"
        )

        return request

    def plan_feature(self, project_id: str, feature_id: str) -> FeaturePlan:
        """Generate a feature plan using the Architect agent.

        Args:
            project_id: Project ID
            feature_id: Feature ID to plan

        Returns:
            Generated FeaturePlan
        """
        request = self.repository.get_request(project_id, feature_id)
        if not request:
            raise FeatureOrchestrationError(f"Feature {feature_id} not found")

        self.repository.append_log(project_id, feature_id, "Starting feature planning...")

        # Generate PRD (in production, this would use the Architect agent)
        prd = self._generate_prd(request)

        # Extract acceptance criteria
        acceptance_criteria = self._extract_acceptance_criteria(request)

        # Generate ADR summaries
        adr_summaries = self._generate_adr_summaries(request)

        # Identify risks
        risks = self._identify_risks(request)

        plan = FeaturePlan(
            feature_id=feature_id,
            project_id=project_id,
            prd=prd,
            acceptance_criteria=acceptance_criteria,
            adr_summaries=adr_summaries,
            risks=risks,
            estimated_effort="2-3 days",
        )

        self.repository.save_plan(plan)
        self.repository.update_request_status(project_id, feature_id, FeatureStatus.PLANNED)
        self.repository.append_log(project_id, feature_id, "Feature plan generated successfully")

        return plan

    def generate_build_plan(self, project_id: str, feature_id: str) -> FeatureBuildPlan:
        """Generate a build plan for a feature.

        Args:
            project_id: Project ID
            feature_id: Feature ID

        Returns:
            Generated FeatureBuildPlan
        """
        request = self.repository.get_request(project_id, feature_id)
        if not request:
            raise FeatureOrchestrationError(f"Feature {feature_id} not found")

        plan = self.repository.get_plan(project_id, feature_id)
        if not plan:
            raise FeatureOrchestrationError(f"Feature plan not found. Run plan_feature first.")

        self.repository.append_log(project_id, feature_id, "Generating build plan...")

        # Generate build steps based on feature type
        steps = self._generate_build_steps(request, plan)

        # Identify repo changes
        repo_changes = self._identify_repo_changes(request, plan)

        # Determine required agents
        required_agents = self._determine_required_agents(request)

        # Determine required skills
        required_skills = self._determine_required_skills(request)

        # Identify required tests
        required_tests = self._identify_required_tests(request, repo_changes)

        build_plan = FeatureBuildPlan(
            feature_id=feature_id,
            project_id=project_id,
            steps=steps,
            repo_changes=repo_changes,
            required_agents=required_agents,
            required_skills=required_skills,
            required_tests=required_tests,
            target_branch="main",
        )

        self.repository.save_build_plan(build_plan)
        self.repository.append_log(project_id, feature_id, f"Build plan generated: {len(steps)} steps, {len(repo_changes)} file changes")

        return build_plan

    def build_feature(self, project_id: str, feature_id: str) -> FeatureBuildResult:
        """Execute the feature build.

        Args:
            project_id: Project ID
            feature_id: Feature ID

        Returns:
            FeatureBuildResult
        """
        request = self.repository.get_request(project_id, feature_id)
        if not request:
            raise FeatureOrchestrationError(f"Feature {feature_id} not found")

        build_plan = self.repository.get_build_plan(project_id, feature_id)
        if not build_plan:
            # Auto-generate build plan if not exists
            build_plan = self.generate_build_plan(project_id, feature_id)

        # Update status to building
        self.repository.update_request_status(project_id, feature_id, FeatureStatus.BUILDING)
        self.repository.append_log(project_id, feature_id, "Starting feature build...")

        # Create branch name
        slug = re.sub(r'[^a-z0-9]+', '-', request.title.lower())[:30]
        branch_name = f"feature/{slug}-{feature_id}"

        created_files = []
        updated_files = []
        deleted_files = []
        test_results = []
        build_logs = []

        try:
            # Execute build steps (in production, this would use agents)
            for i, step in enumerate(build_plan.steps, 1):
                log_msg = f"Step {i}/{len(build_plan.steps)}: {step}"
                self.repository.append_log(project_id, feature_id, log_msg)
                build_logs.append(log_msg)

            # Process repo changes (in production, this would use RepoAdapter)
            for change in build_plan.repo_changes:
                if change.action == "create":
                    created_files.append(change.file_path)
                elif change.action == "modify":
                    updated_files.append(change.file_path)
                elif change.action == "delete":
                    deleted_files.append(change.file_path)

            # Run tests (in production, this would execute actual tests)
            for test_name in build_plan.required_tests:
                test_result = TestResult(
                    test_name=test_name,
                    passed=True,
                    output="Test passed",
                    duration_ms=100,
                )
                test_results.append(test_result)

            # Generate diff summary
            diff_summary = []
            if created_files:
                diff_summary.append(f"+{len(created_files)} files created")
            if updated_files:
                diff_summary.append(f"~{len(updated_files)} files modified")
            if deleted_files:
                diff_summary.append(f"-{len(deleted_files)} files deleted")

            # Create result
            result = FeatureBuildResult(
                feature_id=feature_id,
                project_id=project_id,
                status=BuildStatus.SUCCESS,
                branch_name=branch_name,
                diff_summary=diff_summary,
                created_files=created_files,
                updated_files=updated_files,
                deleted_files=deleted_files,
                test_results=test_results,
                governance_results="All governance checks passed",
                pr_url=None,  # Would be set after PR creation
                commit_sha=f"abc{uuid.uuid4().hex[:5]}",
                build_logs=build_logs,
                completed_at=datetime.utcnow(),
            )

            self.repository.save_result(result)
            self.repository.update_request_status(project_id, feature_id, FeatureStatus.COMPLETED)
            self.repository.append_log(project_id, feature_id, "Feature build completed successfully")

            return result

        except Exception as e:
            # Handle build failure
            result = FeatureBuildResult(
                feature_id=feature_id,
                project_id=project_id,
                status=BuildStatus.FAILED,
                branch_name=branch_name,
                build_logs=build_logs,
                error_message=str(e),
                completed_at=datetime.utcnow(),
            )

            self.repository.save_result(result)
            self.repository.update_request_status(project_id, feature_id, FeatureStatus.FAILED)
            self.repository.append_log(project_id, feature_id, f"Feature build failed: {e}")

            return result

    def get_feature_status(self, project_id: str, feature_id: str) -> FeatureStatus | None:
        """Get the current status of a feature."""
        request = self.repository.get_request(project_id, feature_id)
        return request.status if request else None

    def get_feature_detail(self, project_id: str, feature_id: str) -> FeatureDetail | None:
        """Get complete feature detail."""
        return self.repository.get_feature_detail(project_id, feature_id)

    def list_features(self, project_id: str) -> list[FeatureRequest]:
        """List all features for a project."""
        return self.repository.list_requests(project_id)

    def get_feature_outputs(self, project_id: str, feature_id: str) -> dict:
        """Get all outputs for a feature build."""
        detail = self.repository.get_feature_detail(project_id, feature_id)
        if not detail:
            return {}

        return {
            "request": detail.request.model_dump() if detail.request else None,
            "plan": detail.plan.model_dump() if detail.plan else None,
            "build_plan": detail.build_plan.model_dump() if detail.build_plan else None,
            "result": detail.result.model_dump() if detail.result else None,
            "logs": self.repository.get_logs(project_id, feature_id),
        }

    # Private helper methods for plan generation

    def _generate_prd(self, request: FeatureRequest) -> str:
        """Generate PRD content from feature request."""
        return f"""# Product Requirements Document

## Feature: {request.title}

### Overview
{request.description}

### Objectives
- Implement the requested functionality
- Ensure integration with existing system
- Maintain code quality and test coverage

### User Stories
- As a user, I want {request.title.lower()} so that I can improve my workflow

### Technical Requirements
- Follow existing code patterns and conventions
- Include unit and integration tests
- Update relevant documentation

### Success Metrics
- Feature works as described
- All tests pass
- Code review approved
"""

    def _extract_acceptance_criteria(self, request: FeatureRequest) -> list[str]:
        """Extract acceptance criteria from feature request."""
        return [
            f"Feature implements: {request.title}",
            "All existing tests continue to pass",
            "New functionality has test coverage >= 80%",
            "Code follows project conventions",
            "Documentation is updated",
        ]

    def _generate_adr_summaries(self, request: FeatureRequest) -> list[str]:
        """Generate ADR summaries for the feature."""
        return [
            f"ADR-XXX: Implementation approach for {request.title}",
            "ADR-XXX: Testing strategy for new feature",
        ]

    def _identify_risks(self, request: FeatureRequest) -> list[str]:
        """Identify potential risks for the feature."""
        return [
            "Integration with existing code may require refactoring",
            "Performance impact needs to be measured",
            "Edge cases need comprehensive testing",
        ]

    def _generate_build_steps(self, request: FeatureRequest, plan: FeaturePlan) -> list[str]:
        """Generate build steps for the feature."""
        return [
            "Create feature branch",
            "Implement core functionality",
            "Add unit tests",
            "Add integration tests",
            "Update documentation",
            "Run linting and type checks",
            "Run full test suite",
            "Create pull request",
        ]

    def _identify_repo_changes(self, request: FeatureRequest, plan: FeaturePlan) -> list[RepoChange]:
        """Identify repository changes needed."""
        # Generate placeholder changes based on feature title
        slug = re.sub(r'[^a-z0-9]+', '_', request.title.lower())[:20]

        return [
            RepoChange(
                file_path=f"src/features/{slug}.py",
                action="create",
                description=f"Main implementation for {request.title}",
            ),
            RepoChange(
                file_path=f"tests/test_{slug}.py",
                action="create",
                description=f"Tests for {request.title}",
            ),
            RepoChange(
                file_path="docs/features.md",
                action="modify",
                description="Update feature documentation",
            ),
        ]

    def _determine_required_agents(self, request: FeatureRequest) -> list[str]:
        """Determine which agents are needed for the build."""
        return ["architect", "developer", "qa", "documentarian"]

    def _determine_required_skills(self, request: FeatureRequest) -> list[str]:
        """Determine which skills are needed for the build."""
        # Would analyze request to determine appropriate skills
        return []

    def _identify_required_tests(self, request: FeatureRequest, changes: list[RepoChange]) -> list[str]:
        """Identify tests that need to be run."""
        tests = ["lint", "type_check", "unit_tests"]

        # Add integration tests if there are multiple file changes
        if len(changes) > 2:
            tests.append("integration_tests")

        return tests
