"""
Documentarian Agent for Orchestrator v2.

The Documentarian agent creates and maintains documentation,
README files, and user guides. It is responsible for:
- Technical documentation
- API documentation
- User guides
- README files

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


def create_documentarian_agent() -> "DocumentarianAgent":
    """Factory function to create a DocumentarianAgent with default config."""
    config = BaseAgentConfig(
        id="documentarian",
        role="technical_writer",
        description="Documentation creation",
        skills=["technical_writing", "api_documentation", "user_guide_creation"],
        tools=["file_system", "git"],
        subagents={},
    )
    return DocumentarianAgent(config)


class DocumentarianAgent(BaseAgent):
    """Documentarian agent for documentation creation.

    Responsibilities:
    - Technical documentation
    - API documentation
    - User guides
    - README files
    - Code comments

    LLM Integration:
    - Uses documentarian.md template from subagent_prompts/
    - Produces comprehensive documentation artifacts
    - Creates API references and user guides
    - Generates README and changelog files

    Skills:
    - technical_writing
    - api_documentation
    - user_guide_creation

    Tools:
    - file_system
    - git
    """

    async def plan(
        self,
        task: TaskDefinition,
        phase: PhaseType,
        project_state: ProjectState,
        context: AgentContext | None = None,
    ) -> AgentPlan:
        """Plan documentation approach.

        When LLM context is available, generates a real plan based on
        code artifacts. Otherwise, returns a standard plan template.

        Args:
            task: Task to plan for.
            phase: Current phase.
            project_state: Project state.
            context: Optional agent context for LLM calls.

        Returns:
            Execution plan with documentation steps.
        """
        plan = await super().plan(task, phase, project_state, context)

        if not context and not self._agent_context:
            plan.steps = [
                AgentPlanStep(
                    step_id=f"{task.task_id}_analyze",
                    description="Analyze code artifacts and architecture",
                    estimated_tokens=300,
                ),
                AgentPlanStep(
                    step_id=f"{task.task_id}_structure",
                    description="Plan documentation structure",
                    estimated_tokens=200,
                ),
                AgentPlanStep(
                    step_id=f"{task.task_id}_write",
                    description="Write documentation content",
                    estimated_tokens=500,
                ),
                AgentPlanStep(
                    step_id=f"{task.task_id}_format",
                    description="Format and review documentation",
                    estimated_tokens=200,
                ),
            ]
            plan.estimated_tokens = sum(s.estimated_tokens for s in plan.steps)
            plan.expected_outputs = [
                "README.md",
                "docs/api_reference.md",
                "docs/user_guide.md",
            ]

        logger.info(
            f"Documentarian created plan with {len(plan.steps)} steps for {task.task_id}"
        )
        return plan

    async def act(
        self,
        plan: AgentPlan,
        project_state: ProjectState,
        context: AgentContext | None = None,
    ) -> AgentOutput:
        """Execute documentation steps.

        When LLM context is available, generates real documentation.
        Otherwise, creates template-based documentation.

        Args:
            plan: Execution plan.
            project_state: Project state.
            context: Optional agent context for LLM calls.

        Returns:
            Execution output with documentation artifacts.
        """
        ctx = context or self._agent_context
        phase = project_state.current_phase

        if ctx:
            logger.info(f"Documentarian executing with LLM for project {project_state.project_name}")
            return await super().act(plan, project_state, context)

        logger.info(f"Documentarian executing with templates for project {project_state.project_name}")
        self._record_tokens(input_tokens=600, output_tokens=500)

        # Create README
        readme_content = f"""# {project_state.project_name}

{project_state.description or "A project built with Claude Code Orchestrator."}

## Overview

This project was generated using the Claude Code Orchestrator framework,
which provides automated software development workflows powered by AI agents.

## Quick Start

### Prerequisites

- Python 3.11+
- pip or poetry

### Installation

```bash
# Clone the repository
git clone <repository-url>
cd {project_state.project_name.lower().replace(' ', '-')}

# Install dependencies
pip install -r requirements.txt

# Run the application
python -m src.main
```

## Project Structure

```
{project_state.project_name.lower().replace(' ', '-')}/
├── src/
│   ├── __init__.py
│   ├── main.py          # Application entry point
│   ├── models.py        # Data models
│   └── api.py           # API endpoints
├── tests/
│   └── test_main.py     # Unit tests
├── docs/
│   ├── api_reference.md # API documentation
│   └── user_guide.md    # User guide
├── requirements.txt
└── README.md
```

## Documentation

- [API Reference](docs/api_reference.md)
- [User Guide](docs/user_guide.md)

## Development

### Running Tests

```bash
pytest tests/ -v
```

### Code Style

This project uses Black for formatting and Ruff for linting.

```bash
black src/ tests/
ruff check src/ tests/
```

## License

MIT License - see LICENSE file for details.

## Contributing

Contributions welcome! Please read CONTRIBUTING.md first.
"""

        self._create_artifact(
            "README.md",
            readme_content,
            phase,
            project_state.project_id,
        )

        # Create API reference
        api_content = f"""# API Reference

## {project_state.project_name} API

### Overview

This document describes the API endpoints and data models for the project.

### Base URL

```
http://localhost:8000/api/v1
```

### Authentication

All endpoints require authentication via Bearer token:

```
Authorization: Bearer <token>
```

### Endpoints

#### Health Check

```
GET /health
```

Returns service health status.

**Response:**
```json
{{
  "status": "healthy",
  "version": "1.0.0"
}}
```

#### Resources

##### List Resources

```
GET /resources
```

Query Parameters:
- `page` (int): Page number (default: 1)
- `limit` (int): Items per page (default: 20)

**Response:**
```json
{{
  "items": [...],
  "total": 100,
  "page": 1,
  "limit": 20
}}
```

##### Get Resource

```
GET /resources/{{id}}
```

**Response:**
```json
{{
  "id": "uuid",
  "name": "string",
  "created_at": "datetime"
}}
```

##### Create Resource

```
POST /resources
```

**Request Body:**
```json
{{
  "name": "string",
  "description": "string"
}}
```

### Error Responses

All errors follow this format:

```json
{{
  "error": {{
    "code": "ERROR_CODE",
    "message": "Human readable message"
  }}
}}
```

### Rate Limiting

- 100 requests per minute per user
- 429 Too Many Requests when exceeded
"""

        self._create_artifact(
            "docs/api_reference.md",
            api_content,
            phase,
            project_state.project_id,
        )

        # Create user guide
        user_guide = f"""# User Guide

## {project_state.project_name}

### Getting Started

Welcome to {project_state.project_name}! This guide will help you get up and running.

### Installation

1. **Download**: Get the latest release from GitHub
2. **Install**: Run `pip install -r requirements.txt`
3. **Configure**: Copy `.env.example` to `.env` and update settings
4. **Run**: Execute `python -m src.main`

### Basic Usage

#### Starting the Application

```bash
python -m src.main
```

The application will start on `http://localhost:8000`.

#### Configuration

Key configuration options:

| Option | Description | Default |
|--------|-------------|---------|
| DEBUG | Enable debug mode | false |
| PORT | Server port | 8000 |
| DATABASE_URL | Database connection | sqlite:///data.db |

### Features

#### Feature 1: Data Management

[Description of feature]

#### Feature 2: API Access

[Description of feature]

### Troubleshooting

#### Common Issues

**Issue**: Application won't start
**Solution**: Check that all dependencies are installed

**Issue**: Database errors
**Solution**: Run database migrations

### Support

For support, please:
1. Check the FAQ
2. Search existing issues
3. Create a new issue on GitHub
"""

        self._create_artifact(
            "docs/user_guide.md",
            user_guide,
            phase,
            project_state.project_id,
        )

        self._record_event(
            "documentarian_acted",
            phase.value,
            artifacts=len(self._artifacts),
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
            execution_summary=f"Documentation created for {project_state.project_name}",
            recommendations=[
                "Review documentation for accuracy",
                "Add project-specific examples",
                "Include screenshots where helpful",
            ],
        )

    async def summarize(
        self,
        plan: AgentPlan,
        output: AgentOutput,
        project_state: ProjectState,
    ) -> AgentSummary:
        """Summarize documentation work."""
        summary = await super().summarize(plan, output, project_state)
        summary.summary = (
            f"Documentarian completed {len(plan.steps)} documentation steps: "
            f"artifact analysis, structure planning, content writing, "
            f"and formatting. Produced {len(self._artifacts)} artifacts."
        )
        summary.recommendations = output.recommendations + [
            "Set up documentation hosting",
            "Consider adding API examples",
        ]
        return summary
