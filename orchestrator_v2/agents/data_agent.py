"""
Data Agent for Orchestrator v2.

The Data agent handles data engineering, ETL pipelines,
analytics, and model training. It is responsible for:
- Data ingestion and validation
- ETL pipeline development
- Feature engineering
- Model training and evaluation

See ADR-001 for agent responsibilities.
"""

from orchestrator_v2.agents.base_agent import BaseAgent, BaseAgentConfig
from orchestrator_v2.core.state_models import (
    AgentOutput,
    AgentPlan,
    AgentPlanStep,
    AgentSummary,
    PhaseType,
    ProjectState,
    TaskDefinition,
    TokenUsage,
)


def create_data_agent() -> "DataAgent":
    """Factory function to create a DataAgent with default config."""
    config = BaseAgentConfig(
        id="data",
        role="data_engineer",
        description="Data engineering, ETL, and analytics",
        skills=[
            "time_series_forecasting",
            "optimization_modeling",
            "survey_analysis",
            "data_validation",
        ],
        tools=["file_system", "duckdb", "python_executor", "visualization"],
        subagents={
            "data.ingestion": BaseAgentConfig(
                id="data.ingestion",
                role="data_ingestion",
                description="Data loading specialization",
                skills=["data_ingestion"],
                tools=["file_system", "duckdb"],
            ),
            "data.transform": BaseAgentConfig(
                id="data.transform",
                role="data_transform",
                description="Transformation specialization",
                skills=["data_transformation"],
                tools=["duckdb", "python_executor"],
            ),
            "data.training": BaseAgentConfig(
                id="data.training",
                role="model_training",
                description="Model training specialization",
                skills=["model_training"],
                tools=["python_executor"],
            ),
        },
    )
    return DataAgent(config)


class DataAgent(BaseAgent):
    """Data agent for data engineering and analytics.

    Responsibilities:
    - Data ingestion from sources
    - Data validation and quality checks
    - ETL pipeline development
    - Feature engineering
    - Model training
    - Model evaluation

    Subagents:
    - data.ingestion: Data loading specialization
    - data.transform: Transformation specialization
    - data.training: Model training specialization

    Skills:
    - time_series_forecasting
    - optimization_modeling
    - survey_analysis
    - data_validation

    Tools:
    - file_system
    - duckdb
    - python_executor
    - visualization
    """

    async def plan(
        self,
        task: TaskDefinition,
        phase: PhaseType,
        project_state: ProjectState,
    ) -> AgentPlan:
        """Plan data engineering approach."""
        plan = await super().plan(task, phase, project_state)

        plan.steps = [
            AgentPlanStep(
                step_id=f"{task.task_id}_ingest",
                description="Ingest data from sources",
            ),
            AgentPlanStep(
                step_id=f"{task.task_id}_validate",
                description="Validate data quality",
            ),
            AgentPlanStep(
                step_id=f"{task.task_id}_transform",
                description="Transform and engineer features",
            ),
            AgentPlanStep(
                step_id=f"{task.task_id}_train",
                description="Train models",
            ),
            AgentPlanStep(
                step_id=f"{task.task_id}_evaluate",
                description="Evaluate model performance",
            ),
        ]

        plan.estimated_tokens = 2000
        return plan

    async def act(
        self,
        plan: AgentPlan,
        project_state: ProjectState,
    ) -> AgentOutput:
        """Execute data engineering steps."""
        phase = project_state.current_phase
        self._record_tokens(input_tokens=1000, output_tokens=800)

        # Create data pipeline report
        pipeline_content = f"""# Data Pipeline Report

## Project: {project_state.project_name}
## Agent: {self.id}
## Phase: {phase.value}

### Data Sources
- Source 1: [Description]

### Validation Results
- Total records: [count]
- Valid records: [count]
- Quality score: [percentage]

### Transformations Applied
1. Missing value imputation
2. Feature scaling
3. Feature engineering

### Model Training
- Algorithm: [Model type]
- Training samples: [count]

### Evaluation Metrics
- Accuracy: [value]
- F1 Score: [value]

### Steps Executed
"""
        for step in plan.steps:
            pipeline_content += f"- {step.description}\n"

        self._create_artifact(
            "data_pipeline_report.md",
            pipeline_content,
            phase,
            project_state.project_id,
        )

        # Run subagents
        for subagent_id, subagent_config in self.config.subagents.items():
            await self._run_subagent(subagent_config, phase, project_state)

        self._record_event("data_acted", phase.value, artifacts=len(self._artifacts))

        return AgentOutput(
            step_id=plan.steps[0].step_id if plan.steps else "no_step",
            success=True,
            artifacts=self._artifacts.copy(),
            token_usage=TokenUsage(
                input_tokens=self._token_usage.input_tokens,
                output_tokens=self._token_usage.output_tokens,
                total_tokens=self._token_usage.total_tokens,
            ),
        )

    async def summarize(
        self,
        plan: AgentPlan,
        output: AgentOutput,
        project_state: ProjectState,
    ) -> AgentSummary:
        """Summarize data engineering work."""
        summary = await super().summarize(plan, output, project_state)
        summary.summary = (
            f"Data agent completed {len(plan.steps)} pipeline steps. "
            f"Produced {len(self._artifacts)} artifacts."
        )
        return summary
