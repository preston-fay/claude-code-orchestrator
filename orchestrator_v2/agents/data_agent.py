"""
Data Agent for Orchestrator v2.

The Data agent handles data engineering, ETL pipelines,
analytics, and model training. It is responsible for:
- Data ingestion and validation
- ETL pipeline development
- Feature engineering
- Model training and evaluation

This agent now uses real LLM calls when an AgentContext is provided,
falling back to simulated responses otherwise.

See ADR-001 for agent responsibilities.
"""

import logging

from orchestrator_v2.agents.base_agent import BaseAgent, BaseAgentConfig
from orchestrator_v2.engine.state_models import (
    AgentContext,
    AgentOutput,
    AgentPlan,
    AgentPlanStep,
    AgentSummary,
    PhaseType,
    ProjectState,
    TaskDefinition,
    TokenUsage,
)

logger = logging.getLogger(__name__)


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

    LLM Integration:
    - Uses data.md template from subagent_prompts/
    - Produces data pipeline reports
    - Creates data quality assessments
    - Generates model evaluation metrics

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
        context: AgentContext | None = None,
    ) -> AgentPlan:
        """Plan data engineering approach."""
        plan = await super().plan(task, phase, project_state, context)

        if not context and not self._agent_context:
            plan.steps = [
                AgentPlanStep(
                    step_id=f"{task.task_id}_ingest",
                    description="Ingest data from sources",
                    estimated_tokens=300,
                ),
                AgentPlanStep(
                    step_id=f"{task.task_id}_validate",
                    description="Validate data quality",
                    estimated_tokens=250,
                ),
                AgentPlanStep(
                    step_id=f"{task.task_id}_transform",
                    description="Transform and engineer features",
                    estimated_tokens=400,
                ),
                AgentPlanStep(
                    step_id=f"{task.task_id}_train",
                    description="Train models",
                    estimated_tokens=500,
                ),
                AgentPlanStep(
                    step_id=f"{task.task_id}_evaluate",
                    description="Evaluate model performance",
                    estimated_tokens=350,
                ),
            ]
            plan.estimated_tokens = sum(s.estimated_tokens for s in plan.steps)
            plan.expected_outputs = [
                "data_pipeline_report.md",
                "data_quality_report.md",
                "model_evaluation.md",
            ]

        logger.info(
            f"Data agent created plan with {len(plan.steps)} steps for {task.task_id}"
        )
        return plan

    async def act(
        self,
        plan: AgentPlan,
        project_state: ProjectState,
        context: AgentContext | None = None,
    ) -> AgentOutput:
        """Execute data engineering steps."""
        ctx = context or self._agent_context
        phase = project_state.current_phase

        if ctx:
            logger.info(f"Data agent executing with LLM for project {project_state.project_name}")
            return await super().act(plan, project_state, context)

        logger.info(f"Data agent executing with templates for project {project_state.project_name}")
        self._record_tokens(input_tokens=1000, output_tokens=800)

        # Create data pipeline report
        pipeline_content = f"""# Data Pipeline Report

## Project: {project_state.project_name}
## Client: {project_state.client}
## Phase: {phase.value}

### Executive Summary

Data pipeline execution completed successfully. All data has been
ingested, validated, transformed, and models have been trained.

### Data Sources

| Source | Type | Records | Status |
|--------|------|---------|--------|
| primary_data.csv | CSV | 10,000 | ✅ Loaded |
| reference_data.json | JSON | 500 | ✅ Loaded |
| external_api | REST API | 2,500 | ✅ Fetched |

### Ingestion Summary

- **Total records ingested**: 13,000
- **Ingestion time**: 4.2 seconds
- **Data format**: Normalized to Parquet
- **Storage location**: ./data/processed/

### Data Quality Report

| Check | Status | Details |
|-------|--------|---------|\n| Completeness | ✅ Pass | 98.5% non-null |
| Uniqueness | ✅ Pass | No duplicates |
| Validity | ⚠️ Warning | 12 invalid dates |
| Consistency | ✅ Pass | Cross-references valid |
| Timeliness | ✅ Pass | Data within SLA |

**Quality Score**: 95.2%

### Transformations Applied

1. **Missing Value Imputation**
   - Numeric: Median imputation
   - Categorical: Mode imputation
   - Records affected: 150

2. **Feature Scaling**
   - Method: StandardScaler
   - Features: 15 numeric columns

3. **Feature Engineering**
   - Created: date_features (day, month, quarter)
   - Created: interaction_terms (5 features)
   - Created: aggregated_metrics (3 features)

4. **Encoding**
   - Categorical: OneHotEncoder (8 columns)
   - Target: LabelEncoder

### Model Training

| Model | Algorithm | Status |
|-------|-----------|--------|
| Classification | Random Forest | ✅ Trained |
| Regression | XGBoost | ✅ Trained |
| Clustering | K-Means | ✅ Trained |

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

        # Create model evaluation report
        evaluation_content = f"""# Model Evaluation Report

## Project: {project_state.project_name}
## Phase: {phase.value}

### Classification Model Performance

| Metric | Training | Validation | Test |
|--------|----------|------------|------|
| Accuracy | 0.94 | 0.91 | 0.89 |
| Precision | 0.93 | 0.90 | 0.88 |
| Recall | 0.92 | 0.88 | 0.86 |
| F1 Score | 0.925 | 0.89 | 0.87 |
| AUC-ROC | 0.96 | 0.93 | 0.91 |

### Confusion Matrix (Test Set)

```
              Predicted
            |  Pos  |  Neg  |
Actual Pos  |  850  |  120  |
Actual Neg  |   95  | 1435  |
```

### Regression Model Performance

| Metric | Training | Validation | Test |
|--------|----------|------------|------|
| RMSE | 12.5 | 15.3 | 16.1 |
| MAE | 8.2 | 10.1 | 11.0 |
| R² | 0.92 | 0.88 | 0.86 |
| MAPE | 5.2% | 6.8% | 7.2% |

### Feature Importance (Top 10)

| Rank | Feature | Importance |
|------|---------|------------|
| 1 | feature_a | 0.185 |
| 2 | feature_b | 0.142 |
| 3 | feature_c | 0.118 |
| 4 | feature_d | 0.095 |
| 5 | feature_e | 0.082 |

### Model Artifacts

- `models/classifier_v1.pkl` - Random Forest classifier
- `models/regressor_v1.pkl` - XGBoost regressor
- `models/preprocessor.pkl` - Feature preprocessor

### Recommendations

1. Consider ensemble methods for improved accuracy
2. Investigate feature_d for potential feature engineering
3. Monitor for data drift in production
"""

        self._create_artifact(
            "model_evaluation.md",
            evaluation_content,
            phase,
            project_state.project_id,
        )

        # Run subagents
        subagent_summaries = []
        for subagent_id, subagent_config in self.config.subagents.items():
            summary = await self._run_subagent(subagent_config, phase, project_state, ctx)
            subagent_summaries.append(summary)

        self._record_event(
            "data_acted",
            phase.value,
            artifacts=len(self._artifacts),
            subagents=len(subagent_summaries),
            used_llm=ctx is not None,
        )

        return AgentOutput(
            step_id=plan.steps[0].step_id if plan.steps else "no_step",
            success=True,
            artifacts=self._artifacts.copy(),
            token_usage=TokenUsage(
                input_tokens=self._token_usage.input_tokens,
                output_tokens=self._token_usage.output_tokens,
                total_tokens=self._token_usage.total_tokens,
            ),
            execution_summary="Data pipeline completed. Quality: 95.2%. Models trained and evaluated.",
            recommendations=[
                "Monitor for data drift in production",
                "Consider ensemble methods",
                "Address invalid date records",
            ],
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
            f"Data agent completed {len(plan.steps)} pipeline steps: "
            f"ingestion, validation, transformation, training, and evaluation. "
            f"Produced {len(self._artifacts)} artifacts. Data quality: 95.2%."
        )
        summary.recommendations = output.recommendations + [
            "Set up monitoring dashboard",
            "Schedule retraining pipeline",
        ]
        return summary
