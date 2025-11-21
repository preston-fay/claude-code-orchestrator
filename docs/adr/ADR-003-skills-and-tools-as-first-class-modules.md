# ADR-003: Skills and Tools as First-Class Modules

**Status:** Accepted
**Date:** 2025-11-21
**Deciders:** Platform Team
**Supersedes:** N/A

## Context

The current Orchestrator v1 has skills (`.claude/skills/`) as YAML methodology guides that agents read for context. This works but has limitations:

1. **Passive skills** - Skills are documentation, not executable modules
2. **No tool abstraction** - Agents directly use CLI commands without wrapper
3. **Discovery is manual** - Agents must know which skills exist
4. **No versioning** - Skills can't be updated independently
5. **No validation** - No way to verify skill outputs meet expected schema

For Orchestrator v2, we need:
- Skills as composable, executable building blocks
- Tools as standardized wrappers with consistent interfaces
- Automatic discovery based on task requirements
- Clear separation: skills = "how to think", tools = "how to act"

## Decision

**We will introduce a formal skills/ and tools/ module system where skills are executable methodology packages and tools are environment interaction wrappers, both with standardized interfaces and metadata.**

### Skills Architecture

Skills encode domain-agnostic problem-solving methodologies:

```yaml
# skills/time_series_forecasting/skill.yaml
skill:
  id: time_series_forecasting
  version: "1.0.0"
  category: analytics

  # Discovery metadata
  triggers:
    - "forecast"
    - "predict future"
    - "time series"
    - "trend analysis"

  input_schema:
    type: object
    properties:
      data_path: { type: string }
      target_column: { type: string }
      horizon: { type: integer }
      frequency: { type: string, enum: [daily, weekly, monthly] }
    required: [data_path, target_column, horizon]

  output_schema:
    type: object
    properties:
      forecast: { type: array }
      metrics: { type: object }
      model_path: { type: string }

  # Methodology steps
  methodology:
    - step: data_preparation
      description: "Load and validate time series data"
      tools: [file_system, duckdb]
    - step: exploration
      description: "Analyze patterns, seasonality, stationarity"
      tools: [duckdb, visualization]
    - step: model_selection
      description: "Choose appropriate model (ARIMA, Prophet, LSTM)"
      decision_factors:
        - data_size
        - seasonality_strength
        - required_interpretability
    - step: training
      description: "Train model with cross-validation"
      tools: [python_executor]
    - step: evaluation
      description: "Calculate MAPE, RMSE, residual analysis"
      tools: [python_executor, visualization]
    - step: forecasting
      description: "Generate predictions with confidence intervals"
      tools: [python_executor]

  # Best practices and pitfalls
  best_practices:
    - "Always check for stationarity before ARIMA"
    - "Use walk-forward validation for time series"
    - "Include uncertainty estimates in forecasts"

  common_pitfalls:
    - "Data leakage from future values"
    - "Ignoring seasonality patterns"
    - "Over-fitting to recent trends"
```

### Tools Architecture

Tools wrap environment interactions with consistent interfaces:

```yaml
# tools/git/tool.yaml
tool:
  id: git
  version: "1.0.0"
  category: version_control

  # Capabilities
  actions:
    - name: status
      description: "Get repository status"
      parameters: []
      returns: { type: object, properties: { modified: array, staged: array } }

    - name: commit
      description: "Create a commit"
      parameters:
        - name: message
          type: string
          required: true
        - name: files
          type: array
          default: ["."]
      returns: { type: object, properties: { sha: string } }

    - name: diff
      description: "Get diff of changes"
      parameters:
        - name: ref
          type: string
          default: "HEAD"
      returns: { type: string }

  # Safety constraints
  constraints:
    - "Never force push"
    - "Always verify branch before push"
    - "Require message for commits"

  # Requires
  requires:
    - "git CLI installed"
    - "Repository initialized"
```

### Module Structure

```
orchestrator/
├── skills/
│   ├── __init__.py
│   ├── registry.py              # Skill discovery and loading
│   ├── base.py                  # BaseSkill class
│   ├── time_series_forecasting/
│   │   ├── skill.yaml
│   │   ├── __init__.py
│   │   └── executor.py          # Skill execution logic
│   ├── optimization_modeling/
│   │   ├── skill.yaml
│   │   ├── __init__.py
│   │   └── executor.py
│   └── survey_analysis/
│       ├── skill.yaml
│       ├── __init__.py
│       └── executor.py
├── tools/
│   ├── __init__.py
│   ├── registry.py              # Tool discovery and loading
│   ├── base.py                  # BaseTool class
│   ├── git/
│   │   ├── tool.yaml
│   │   ├── __init__.py
│   │   └── wrapper.py
│   ├── file_system/
│   │   ├── tool.yaml
│   │   └── wrapper.py
│   ├── duckdb/
│   │   ├── tool.yaml
│   │   └── wrapper.py
│   └── python_executor/
│       ├── tool.yaml
│       └── wrapper.py
```

### Discovery Mechanism

```python
class SkillRegistry:
    def discover_for_task(self, task: str) -> List[Skill]:
        """Find skills matching task description via trigger keywords."""
        matches = []
        for skill in self.skills.values():
            if any(trigger in task.lower() for trigger in skill.triggers):
                matches.append(skill)
        return sorted(matches, key=lambda s: s.relevance_score(task))

class ToolRegistry:
    def get_for_skill(self, skill: Skill) -> List[Tool]:
        """Get tools required by a skill's methodology."""
        tool_ids = set()
        for step in skill.methodology:
            tool_ids.update(step.tools)
        return [self.tools[tid] for tid in tool_ids]
```

### Agent Integration

Agents declare skill and tool dependencies in their config:

```yaml
# agents/developer.yaml
agent:
  id: developer
  skills:
    - code_generation
    - test_writing
    - refactoring
  tools:
    - git
    - file_system
    - python_executor
    - linter
```

At runtime:
1. Agent receives task
2. Registry finds relevant skills from triggers
3. Agent loads skill methodology
4. Agent requests tools from skill's steps
5. Agent executes methodology using tools
6. Outputs validated against skill's output_schema

## Consequences

### Benefits

1. **Composability** - Skills and tools can be mixed and matched
2. **Discoverability** - Automatic matching of skills to tasks
3. **Standardization** - Consistent interfaces for all tools
4. **Validation** - Input/output schemas catch errors early
5. **Versioning** - Skills/tools can evolve independently
6. **Reusability** - Same skill works across project types
7. **Auditability** - Clear record of which skills/tools used

### Trade-offs

1. **Overhead** - More structure than simple prompt templates
2. **Migration** - Existing skills need conversion to new format
3. **Maintenance** - More code to maintain for wrappers

### Risks & Mitigations

| Risk | Mitigation |
|------|------------|
| Skill proliferation | Strict review process, prefer extending over creating |
| Tool wrapper bugs | Comprehensive testing, fallback to direct CLI |
| Schema rigidity | Allow `additionalProperties` in schemas |

## Alternatives Considered

### 1. Keep Skills as Documentation
- **Pros:** Simple, no execution overhead
- **Cons:** No validation, no automatic discovery
- **Why rejected:** Want executable, composable modules

### 2. Skills as Prompts Only
- **Pros:** Simpler than full modules
- **Cons:** No schema validation, no tool binding
- **Why rejected:** Need structured outputs and tool integration

### 3. External Skill Marketplace
- **Pros:** Community contributions
- **Cons:** Security concerns, quality control
- **Why rejected:** Start with internal skills, consider later

## Implementation Notes

### Base Classes

```python
class BaseSkill(ABC):
    @abstractmethod
    def validate_input(self, input: dict) -> None: ...

    @abstractmethod
    async def execute(self, input: dict, tools: ToolSet) -> dict: ...

    @abstractmethod
    def validate_output(self, output: dict) -> None: ...

class BaseTool(ABC):
    @abstractmethod
    async def invoke(self, action: str, params: dict) -> Any: ...

    @abstractmethod
    def get_capabilities(self) -> List[ToolAction]: ...
```

### Tool Safety

All tools enforce:
- Parameter validation
- Timeout limits
- Output size limits
- Audit logging
- Sandboxing where appropriate

## Related Decisions

- ADR-001: Agent Architecture (agents declare skill/tool dependencies)
- ADR-004: Governance Engine (skills may have compliance requirements)
- ADR-005: Token Efficiency (skill execution tracked for budgets)
