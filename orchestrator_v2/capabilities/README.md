# Capabilities

Reusable analytical capabilities for Orchestrator v2.

## Purpose

This module contains:
- **Skills**: Reusable analytical methodologies (time-series, optimization, survey)
- **Tools**: Sandboxed tool implementations for agent actions

## Skills

Skills are proven analytical patterns stored as YAML configurations that agents can apply to projects.

### Available Skills

- `time_series/`: ARIMA, Prophet, LSTM approaches for forecasting
- `optimization/`: Linear programming, constraint optimization
- `survey/`: Survey analysis, sentiment analysis

### Using Skills

```python
from orchestrator_v2.capabilities.skills.registry import SkillRegistry

registry = SkillRegistry()
registry.load_skills()

skill = registry.get_skill("time_series_analytics")
result = skill.apply(project_state)
```

## Tools

Tools provide sandboxed actions that agents can execute.

### Available Tools

- `git_tool.py`: Git operations (commit, push, branch)
- `data_tool.py`: Data processing operations
- `security_tool.py`: Security scanning
- `deploy_tool.py`: Deployment operations
- `viz_tool.py`: Visualization generation

### Creating New Tools

1. Extend `BaseTool` in a new file
2. Define tool actions with the `@ToolAction` decorator
3. Register with the `ToolRegistry`

## Related Documentation

- CLAUDE.md: Using Skills section
- .claude/skills/README.md: Skill authoring guide
