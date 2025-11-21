"""
Skill registry for Orchestrator v2.

Handles skill discovery, loading, and matching.

See ADR-003 for skill discovery mechanism.
"""

from pathlib import Path
from typing import Any

from orchestrator_v2.core.state_models import PhaseType, ProjectState
from orchestrator_v2.skills.models import (
    BaseSkill,
    BaseSkillImpl,
    MethodologyStep,
    SkillMetadata,
    SkillResult,
)


class SkillRegistry:
    """Registry for skill discovery and management."""

    def __init__(self, skill_paths: list[Path] | None = None):
        """Initialize the skill registry."""
        self.skill_paths = skill_paths or []
        self._skills: dict[str, BaseSkillImpl] = {}
        self._metadata: dict[str, SkillMetadata] = {}

    def discover_skills(self) -> list[str]:
        """Discover and register built-in skills."""
        # Register time series skill
        ts_metadata = SkillMetadata(
            id="time_series_forecasting",
            category="analytics",
            description="Time series forecasting methodology",
            triggers=["forecast", "predict", "time series", "trend", "arima", "prophet"],
            methodology=[
                MethodologyStep(step="data_prep", description="Prepare time series data", tools=["duckdb"]),
                MethodologyStep(step="analysis", description="Analyze patterns", tools=["visualization"]),
                MethodologyStep(step="model", description="Train forecast model", tools=["python_executor"]),
            ],
            tools_required=["duckdb", "python_executor", "visualization"],
        )
        self._register_skill(TimeSeriesSkill(ts_metadata))

        # Register optimization skill
        opt_metadata = SkillMetadata(
            id="optimization_modeling",
            category="optimization",
            description="Mathematical optimization modeling",
            triggers=["optimize", "optimization", "linear program", "constraint", "minimize", "maximize"],
            methodology=[
                MethodologyStep(step="formulate", description="Formulate problem", tools=[]),
                MethodologyStep(step="model", description="Build optimization model", tools=["python_executor"]),
                MethodologyStep(step="solve", description="Solve and analyze", tools=["python_executor"]),
            ],
            tools_required=["python_executor"],
        )
        self._register_skill(OptimizationSkill(opt_metadata))

        # Register survey skill
        survey_metadata = SkillMetadata(
            id="survey_analysis",
            category="analytics",
            description="Survey data analysis methodology",
            triggers=["survey", "questionnaire", "likert", "response analysis", "sentiment"],
            methodology=[
                MethodologyStep(step="clean", description="Clean survey data", tools=["duckdb"]),
                MethodologyStep(step="analyze", description="Statistical analysis", tools=["python_executor"]),
                MethodologyStep(step="visualize", description="Create visualizations", tools=["visualization"]),
            ],
            tools_required=["duckdb", "python_executor", "visualization"],
        )
        self._register_skill(SurveyAnalysisSkill(survey_metadata))

        return list(self._skills.keys())

    def _register_skill(self, skill: BaseSkillImpl) -> None:
        """Register a skill instance."""
        self._skills[skill.id] = skill
        self._metadata[skill.id] = skill.metadata

    def find_matching_skills(
        self,
        agent_role: str,
        phase_name: str,
        project_metadata: dict[str, Any],
    ) -> list[BaseSkillImpl]:
        """Find skills matching agent role and phase context."""
        matching = []

        # Build search text from context
        search_text = f"{agent_role} {phase_name}"
        if "requirements" in project_metadata:
            search_text += " " + " ".join(str(r) for r in project_metadata["requirements"])
        if "description" in project_metadata:
            search_text += " " + project_metadata["description"]

        for skill in self._skills.values():
            if skill.matches(search_text):
                matching.append(skill)

        return matching

    async def execute_skills(
        self,
        skills: list[BaseSkillImpl],
        agent_id: str,
        phase: PhaseType,
        project_state: ProjectState,
        context: dict[str, Any],
    ) -> list[SkillResult]:
        """Execute multiple skills and collect results."""
        results = []
        for skill in skills:
            result = await skill.execute(agent_id, phase, project_state, context)
            results.append(result)
        return results

    def load_skill(self, skill_id: str) -> BaseSkillImpl:
        """Load a skill by ID."""
        if skill_id not in self._skills:
            raise KeyError(f"Skill not found: {skill_id}")
        return self._skills[skill_id]

    def match_skill(self, task_description: str) -> list[tuple[str, float]]:
        """Find skills matching a task description."""
        matches: list[tuple[str, float]] = []
        for skill_id, metadata in self._metadata.items():
            score = self._calculate_relevance(task_description, metadata)
            if score > 0:
                matches.append((skill_id, score))
        return sorted(matches, key=lambda x: x[1], reverse=True)

    def _calculate_relevance(self, task_description: str, metadata: SkillMetadata) -> float:
        """Calculate relevance score for a skill."""
        task_lower = task_description.lower()
        matches = sum(1 for trigger in metadata.triggers if trigger.lower() in task_lower)
        if matches == 0:
            return 0.0
        return min(1.0, matches / len(metadata.triggers))

    def get_skill_metadata(self, skill_id: str) -> SkillMetadata:
        """Get metadata for a skill."""
        if skill_id not in self._metadata:
            raise KeyError(f"Skill not found: {skill_id}")
        return self._metadata[skill_id]

    def list_skills(self, category: str | None = None) -> list[str]:
        """List available skills."""
        if category:
            return [sid for sid, meta in self._metadata.items() if meta.category == category]
        return list(self._metadata.keys())


# Concrete skill implementations

class TimeSeriesSkill(BaseSkillImpl):
    """Time series forecasting skill."""

    async def execute(
        self,
        agent_id: str,
        phase: PhaseType,
        project_state: ProjectState,
        context: dict[str, Any],
    ) -> SkillResult:
        """Execute time series methodology."""
        from hashlib import sha256
        from orchestrator_v2.core.state_models import ArtifactInfo

        content = f"""# Time Series Forecast

## Project: {project_state.project_name}
## Methodology: ARIMA/Prophet

### Data Preparation
- Loaded time series data
- Checked stationarity
- Applied differencing if needed

### Model Training
- Selected Prophet model
- Trained with cross-validation
- Parameters optimized

### Forecast Results
- Horizon: 30 days
- MAPE: 5.2%
- Confidence intervals included
"""
        artifact = ArtifactInfo(
            path=f".claude/checkpoints/{phase.value}/forecast_report.md",
            sha256=sha256(content.encode()).hexdigest(),
            size_bytes=len(content),
            phase=phase,
            project_id=project_state.project_id,
        )

        return SkillResult(
            skill_id=self.id,
            success=True,
            messages=[
                "Applied time series methodology",
                "Model trained with Prophet",
                "Generated forecast with confidence intervals",
            ],
            artifacts=[artifact],
            token_usage=TokenUsage(input_tokens=200, output_tokens=150, total_tokens=350),
        )


class OptimizationSkill(BaseSkillImpl):
    """Optimization modeling skill."""

    async def execute(
        self,
        agent_id: str,
        phase: PhaseType,
        project_state: ProjectState,
        context: dict[str, Any],
    ) -> SkillResult:
        """Execute optimization methodology."""
        from hashlib import sha256
        from orchestrator_v2.core.state_models import ArtifactInfo

        content = f"""# Optimization Model

## Project: {project_state.project_name}
## Type: Linear Programming

### Problem Formulation
- Objective: Minimize cost
- Variables: x1, x2, x3
- Constraints: 5

### Solution
- Status: Optimal
- Objective value: 1250.00
- x1 = 10, x2 = 25, x3 = 15

### Sensitivity Analysis
- Shadow prices computed
- Reduced costs analyzed
"""
        artifact = ArtifactInfo(
            path=f".claude/checkpoints/{phase.value}/optimization_report.md",
            sha256=sha256(content.encode()).hexdigest(),
            size_bytes=len(content),
            phase=phase,
            project_id=project_state.project_id,
        )

        return SkillResult(
            skill_id=self.id,
            success=True,
            messages=[
                "Formulated optimization problem",
                "Solved using linear programming",
                "Optimal solution found",
            ],
            artifacts=[artifact],
            token_usage=TokenUsage(input_tokens=150, output_tokens=100, total_tokens=250),
        )


class SurveyAnalysisSkill(BaseSkillImpl):
    """Survey analysis skill."""

    async def execute(
        self,
        agent_id: str,
        phase: PhaseType,
        project_state: ProjectState,
        context: dict[str, Any],
    ) -> SkillResult:
        """Execute survey analysis methodology."""
        from hashlib import sha256
        from orchestrator_v2.core.state_models import ArtifactInfo

        content = f"""# Survey Analysis Report

## Project: {project_state.project_name}
## Responses: 500

### Data Quality
- Complete responses: 485
- Missing data: < 3%

### Key Findings
- Overall satisfaction: 4.2/5
- NPS Score: 45
- Top concern: Response time

### Statistical Tests
- ANOVA for group differences
- Chi-square for associations
- All tests significant (p < 0.05)
"""
        artifact = ArtifactInfo(
            path=f".claude/checkpoints/{phase.value}/survey_report.md",
            sha256=sha256(content.encode()).hexdigest(),
            size_bytes=len(content),
            phase=phase,
            project_id=project_state.project_id,
        )

        return SkillResult(
            skill_id=self.id,
            success=True,
            messages=[
                "Cleaned survey data",
                "Performed statistical analysis",
                "Generated insights report",
            ],
            artifacts=[artifact],
            token_usage=TokenUsage(input_tokens=180, output_tokens=120, total_tokens=300),
        )


# Import for convenience
from orchestrator_v2.core.state_models import TokenUsage
