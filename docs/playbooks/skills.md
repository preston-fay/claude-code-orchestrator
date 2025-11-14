# Skills Engine Playbook

## Overview
Skills Activation Engine v2 auto-matches reusable analytical patterns to inject concise, agent-specific code snippets.

## Quick Start

**Auto-matching is automatic** - no configuration needed. Skills activate based on task keywords.

### Example

```bash
# Task mentions "forecast seasonal trends"
orchestrator run next --intake myproject.yaml

# Skills Engine auto-detects and injects time_series_analytics snippets
# visible in agent context
```

## Enforcing Prerequisites

By default, missing MCP modules produce warnings. Enable strict mode:

```bash
# Fail-fast if MCP modules missing
orchestrator run next --skills-enforce

# Error output:
# ❌ Missing prerequisite: orchestrator.mcp.data.load_csv
# Hint: Ensure MCP modules are installed. Module path: orchestrator.mcp.data.load_csv
```

## Available Skills

| Skill | Keywords | Requires |
|-------|----------|----------|
| time_series_analytics | forecast, seasonal, prophet | mcp.data, mcp.models.train_prophet |
| optimization_modeling | optimize, maximize, minimize | mcp.analytics |
| survey_data_processing | survey, likert, sentiment | mcp.data |
| ml_classification | classification, predict, accuracy | mcp.models.train_classifier |
| wcag_accessibility | accessibility, wcag, a11y | none |

## Adding New Skills

Edit `src/orchestrator/skills/index.yaml`:

```yaml
my_new_skill:
  description: "Skill description"
  category: "analytics"
  keywords:
    - "keyword1"
    - "keyword2"
  requires:
    - "orchestrator.mcp.my_module"
  snippets:
    developer: |
      # Code snippet for developer agent
      from orchestrator.mcp.my_module import my_func
      result = my_func(data)
```

## Telemetry

Skills usage tracked in run metadata:

```json
{
  "skills_matched": ["time_series_analytics"],
  "skills_available": ["time_series_analytics"],
  "skills_missing_prereqs": [],
  "match_count": 1
}
```

## Troubleshooting

**Q: Why aren't my skills matching?**  
A: Check keywords in `index.yaml` match your task text. Matching is case-insensitive but exact.

**Q: What if I want to disable a skill temporarily?**  
A: Remove keywords from index.yaml or delete the skill entry.

**Q: Can I force-load a skill?**  
A: Not currently supported. Add relevant keywords to your task text as workaround.
