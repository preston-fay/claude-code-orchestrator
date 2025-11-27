"""
Architect Agent for Orchestrator v2.

The Architect agent designs system architecture, data models,
and technical specifications. It is responsible for:
- Creating architectural proposals
- Defining data models and schemas
- Selecting technologies and patterns
- Creating Architecture Decision Records (ADRs)

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

    LLM Integration:
    - Uses architect.md template from subagent_prompts/
    - Produces structured architectural documents
    - Creates data model specifications
    - Generates technology rationale

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
        context: AgentContext | None = None,
    ) -> AgentPlan:
        """Plan architecture design approach.

        When LLM context is available, generates a real plan based on
        project requirements. Otherwise, returns a standard plan template.

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
            context: Optional agent context for LLM calls.

        Returns:
            Execution plan with architecture-specific steps.
        """
        # Use parent's LLM-enabled plan method
        plan = await super().plan(task, phase, project_state, context)

        # If we got a simulated plan (no LLM context), enhance with architecture defaults
        if not context and not self._agent_context:
            plan.steps = [
                AgentPlanStep(
                    step_id=f"{task.task_id}_analyze",
                    description="Analyze requirements and constraints",
                    estimated_tokens=300,
                ),
                AgentPlanStep(
                    step_id=f"{task.task_id}_propose",
                    description="Create architecture proposal",
                    estimated_tokens=500,
                ),
                AgentPlanStep(
                    step_id=f"{task.task_id}_data_model",
                    description="Design data models and schemas",
                    estimated_tokens=400,
                ),
                AgentPlanStep(
                    step_id=f"{task.task_id}_tech_select",
                    description="Select technologies and patterns",
                    estimated_tokens=200,
                ),
                AgentPlanStep(
                    step_id=f"{task.task_id}_adr",
                    description="Create Architecture Decision Records",
                    estimated_tokens=300,
                ),
            ]
            plan.estimated_tokens = sum(s.estimated_tokens for s in plan.steps)
            plan.expected_outputs = [
                "architecture_proposal.md",
                "data_model.md",
                "adr_001_technology_stack.md",
            ]

        logger.info(
            f"Architect created plan with {len(plan.steps)} steps for {task.task_id}"
        )

        return plan

    async def act(
        self,
        plan: AgentPlan,
        project_state: ProjectState,
        context: AgentContext | None = None,
    ) -> AgentOutput:
        """Execute architecture design steps.

        When LLM context is available, generates real architectural artifacts.
        Otherwise, creates template-based placeholder artifacts.

        Creates architecture artifacts including:
        - Architecture proposal document
        - Data model definitions
        - ADRs for key decisions

        Args:
            plan: Execution plan.
            project_state: Project state.
            context: Optional agent context for LLM calls.

        Returns:
            Execution output with architecture artifacts.
        """
        ctx = context or self._agent_context
        phase = project_state.current_phase

        # If we have LLM context, use the parent's LLM-enabled act method
        if ctx:
            logger.info(f"Architect executing with LLM for project {project_state.project_name}")
            return await super().act(plan, project_state, context)

        # Otherwise, generate template-based artifacts
        logger.info(f"Architect executing with templates for project {project_state.project_name}")

        # Record token usage for architecture work (simulated)
        self._record_tokens(input_tokens=800, output_tokens=600)

        # Create architecture proposal artifact
        proposal_content = f"""# Architecture Proposal

## Project: {project_state.project_name}
## Client: {project_state.client}
## Phase: {phase.value}

### Executive Summary
This document outlines the proposed system architecture for the project.
The architecture follows modern best practices with a focus on scalability,
maintainability, and security.

### System Overview
The system is designed as a modular architecture with clear separation of concerns:

1. **Presentation Layer**: User-facing interfaces and API endpoints
2. **Business Logic Layer**: Core application logic and workflows
3. **Data Access Layer**: Database interactions and data transformations
4. **Infrastructure Layer**: Deployment, monitoring, and operations

### Technology Stack

| Component          | Technology                | Rationale |
|-------------------|---------------------------|-----------| 
| Backend Framework | Python/FastAPI            | High performance, async support, excellent typing |
| Database          | PostgreSQL                | Robust, scalable, excellent JSON support |
| Cache             | Redis                     | In-memory performance, pub/sub capabilities |
| Message Queue     | RabbitMQ/Redis Streams    | Reliable async processing |
| Containerization  | Docker + Kubernetes       | Scalable deployment, orchestration |

### Quality Attributes

- **Scalability**: Horizontal scaling via container orchestration
- **Security**: OAuth2/JWT authentication, encrypted data at rest
- **Performance**: Sub-100ms response times for API endpoints
- **Maintainability**: Clean architecture, comprehensive documentation

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

#### Core Entities
The data model centers around the following core entities:

1. **Project**: Main work container
2. **Task**: Individual work items within a project
3. **User**: System users and their roles
4. **Artifact**: Generated outputs and documents

### Database Schema

```sql
-- Projects table
CREATE TABLE projects (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    client_id UUID REFERENCES clients(id),
    status VARCHAR(50) DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tasks table  
CREATE TABLE tasks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID REFERENCES projects(id),
    title VARCHAR(255) NOT NULL,
    description TEXT,
    status VARCHAR(50) DEFAULT 'pending',
    assigned_to UUID REFERENCES users(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Artifacts table
CREATE TABLE artifacts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID REFERENCES projects(id),
    task_id UUID REFERENCES tasks(id),
    path VARCHAR(500) NOT NULL,
    hash VARCHAR(64) NOT NULL,
    size_bytes BIGINT,
    artifact_type VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Validation Rules

- Project names must be unique per client
- Task status transitions follow defined workflow
- Artifacts are immutable once created
"""

        self._create_artifact(
            "data_model.md",
            data_model_content,
            phase,
            project_state.project_id,
        )

        # Create ADR artifact
        adr_content = f"""# ADR-001: Technology Stack Selection

## Status
Accepted

## Context
Project {project_state.project_name} requires a technology stack that supports:
- Rapid development and iteration
- Scalable deployment
- Strong type safety and maintainability
- Integration with AI/LLM services

## Decision
We will use the following technology stack:

### Backend
- **Language**: Python 3.11+
- **Framework**: FastAPI
- **Async Runtime**: asyncio with uvicorn

### Database
- **Primary**: PostgreSQL 15+
- **Cache**: Redis 7+

### Infrastructure
- **Containers**: Docker
- **Orchestration**: Kubernetes (optional)
- **CI/CD**: GitHub Actions

## Consequences

### Positive
- Strong Python ecosystem for AI/ML integrations
- FastAPI provides excellent performance and auto-documentation
- PostgreSQL is battle-tested and feature-rich
- Container-based deployment enables portability

### Negative
- Python GIL may limit CPU-bound parallelism
- Requires team expertise in async programming
- Infrastructure complexity with Kubernetes

## Alternatives Considered

1. **Node.js/Express**: Rejected due to weaker typing and async complexity
2. **Go/Gin**: Rejected due to less mature AI/ML ecosystem
3. **Java/Spring**: Rejected due to development velocity requirements
"""

        self._create_artifact(
            "adr_001_technology_stack.md",
            adr_content,
            phase,
            project_state.project_id,
        )

        # Run subagents if configured
        subagent_summaries = []
        for subagent_id, subagent_config in self.config.subagents.items():
            summary = await self._run_subagent(subagent_config, phase, project_state, ctx)
            subagent_summaries.append(summary)

        # Emit event
        self._record_event(
            "architect_acted",
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
            execution_summary=f"Created architecture documentation for {project_state.project_name}",
            recommendations=[
                "Review architecture proposal with stakeholders",
                "Validate data model against requirements",
                "Consider security review of proposed stack",
            ],
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

        # Add architect-specific recommendations
        summary.recommendations = output.recommendations + [
            "Conduct architecture review meeting",
            "Document any deviations during implementation",
        ]

        return summary
