"""
Architect Agent for Orchestrator v2.

The Architect agent designs system architecture, data models,
and technical specifications. It is responsible for:
- Creating architectural proposals
- Defining data models and schemas
- Selecting technologies and patterns
- Creating Architecture Decision Records (ADRs)

See ADR-001 for agent responsibilities.
"""

from orchestrator_v2.agents.base_agent import BaseAgent, BaseAgentConfig
from orchestrator_v2.engine.state_models import (
    AgentOutput,
    AgentPlan,
    AgentPlanStep,
    AgentSummary,
    PhaseType,
    ProjectState,
    TaskDefinition,
    TokenUsage,
)


def create_architect_agent() -> "ArchitectAgent":
    """Factory function to create an ArchitectAgent with default config."""
    config = BaseAgentConfig(
        id="architect",
        role="architect",
        description="System architecture and technical design",
        skills=["architecture_design", "data_modeling", "api_design"],
        tools=["file_system", "git", "visualization"],
        subagents={
            "architect.data": BaseAgentConfig(
                id="architect.data",
                role="data_architect",
                description="Data architecture specialization",
                skills=["data_modeling"],
                tools=["file_system"],
            ),
            "architect.security": BaseAgentConfig(
                id="architect.security",
                role="security_architect",
                description="Security architecture",
                skills=["security_design"],
                tools=["file_system", "security_scanner"],
            ),
        },
    )
    return ArchitectAgent(config)


class ArchitectAgent(BaseAgent):
    """Architect agent for system design and technical decisions.

    Responsibilities:
    - System architecture design
    - Technology selection
    - Data model definition
    - API contract design
    - Creating ADRs for decisions

    Subagents:
    - architect.data: Data architecture specialization
    - architect.security: Security architecture

    Skills:
    - architecture_design
    - data_modeling
    - api_design

    Tools:
    - file_system
    - git
    - visualization
    """

    async def plan(
        self,
        task: TaskDefinition,
        phase: PhaseType,
        project_state: ProjectState,
    ) -> AgentPlan:
        """Plan architecture design approach.

        Creates plan for:
        1. Requirements analysis
        2. Architecture proposal
        3. Data model design
        4. Technology selection
        5. ADR creation

        Args:
            task: Task to plan for.
            phase: Current phase.
            project_state: Project state.

        Returns:
            Execution plan with architecture-specific steps.
        """
        # Get base plan
        plan = await super().plan(task, phase, project_state)

        # Override with architecture-specific steps
        plan.steps = [
            AgentPlanStep(
                step_id=f"{task.task_id}_analyze",
                description="Analyze requirements and constraints",
            ),
            AgentPlanStep(
                step_id=f"{task.task_id}_propose",
                description="Create architecture proposal",
            ),
            AgentPlanStep(
                step_id=f"{task.task_id}_data_model",
                description="Design data models and schemas",
            ),
            AgentPlanStep(
                step_id=f"{task.task_id}_tech_select",
                description="Select technologies and patterns",
            ),
            AgentPlanStep(
                step_id=f"{task.task_id}_adr",
                description="Create Architecture Decision Records",
            ),
        ]

        plan.estimated_tokens = 1500

        return plan

    async def act(
        self,
        plan: AgentPlan,
        project_state: ProjectState,
    ) -> AgentOutput:
        """Execute architecture design steps.

        Creates architecture artifacts including:
        - Architecture proposal document
        - Data model definitions
        - ADRs for key decisions

        Args:
            plan: Execution plan.
            project_state: Project state.

        Returns:
            Execution output with architecture artifacts.
        """
        phase = project_state.current_phase

        # Record token usage for architecture work
        self._record_tokens(input_tokens=800, output_tokens=600)

        # Create architecture proposal artifact
        proposal_content = f"""# Architecture Proposal

## Project: {project_state.project_name}
## Agent: {self.id}
## Phase: {phase.value}

### Executive Summary
This document outlines the proposed system architecture for the project.

### System Overview
[Architecture description based on requirements]

### Technology Stack
- Backend: Python/FastAPI
- Database: PostgreSQL
- Cache: Redis
- Deployment: Docker/Kubernetes

### Data Models
[Data model definitions]

### API Contracts
[API endpoint definitions]

### Quality Attributes
- Scalability: Horizontal scaling via Kubernetes
- Security: OAuth2/JWT authentication
- Performance: Sub-100ms response times

### Decisions
See ADR documents for key architectural decisions.

### Steps Executed
"""
        for step in plan.steps:
            proposal_content += f"- {step.description}\n"

        self._create_artifact(
            "architecture_proposal.md",
            proposal_content,
            phase,
            project_state.project_id,
        )

        # Create data model artifact
        data_model_content = f"""# Data Model Definitions

## Project: {project_state.project_name}

### Entity Definitions
[Entity schemas and relationships]

### Database Schema
[SQL/ORM definitions]

### Validation Rules
[Data validation constraints]
"""

        self._create_artifact(
            "data_model.md",
            data_model_content,
            phase,
            project_state.project_id,
        )

        # Run subagents for specialized architecture tasks
        subagent_summaries = []
        for subagent_id, subagent_config in self.config.subagents.items():
            summary = await self._run_subagent(subagent_config, phase, project_state)
            subagent_summaries.append(summary)

        # Emit event
        self._record_event(
            "architect_acted",
            phase.value,
            artifacts=len(self._artifacts),
            subagents=len(subagent_summaries),
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
        )

    async def summarize(
        self,
        plan: AgentPlan,
        output: AgentOutput,
        project_state: ProjectState,
    ) -> AgentSummary:
        """Summarize architecture work.

        Summary includes:
        - Architecture decisions made
        - Artifacts created
        - Recommendations for development

        Args:
            plan: Execution plan.
            output: Execution output.
            project_state: Project state.

        Returns:
            Execution summary.
        """
        summary = await super().summarize(plan, output, project_state)

        # Enhance summary with architecture-specific details
        summary.summary = (
            f"Architect completed {len(plan.steps)} design steps: "
            f"requirements analysis, architecture proposal, data modeling, "
            f"technology selection, and ADR creation. "
            f"Produced {len(self._artifacts)} artifacts."
        )

        return summary
