# Intake Template System

## Overview

The intake template system provides structured interviews that gather the raw material the orchestrator needs to deliver perfect outputs. Each project type has a corresponding intake template that guides users through a series of questions, adapting based on their answers.

**Philosophy**: "Perfect prompts for perfect prompts" - Before the orchestrator can orchestrate, it needs comprehensive context about what you're trying to accomplish.

## How It Works

```
┌─────────────────────────────────────────────────────────────────────┐
│                         RSC WORKFLOW                                │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  1. User selects project type (e.g., "presentation")                │
│                      ↓                                              │
│  2. System loads intake template from intake/templates/{type}.yaml  │
│                      ↓                                              │
│  3. RSG-UI renders intake interview (Ready Stage)                   │
│                      ↓                                              │
│  4. User answers questions (adaptive, conditional logic)            │
│                      ↓                                              │
│  5. System validates responses against schema                       │
│                      ↓                                              │
│  6. System pulls client governance constraints automatically        │
│                      ↓                                              │
│  7. Completed intake feeds into orchestrator workflow               │
│                      ↓                                              │
│  8. Orchestrator has raw material to generate perfect output        │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

## Directory Structure

```
intake/
├── README.md                    # This file
├── schema/
│   └── intake.schema.json       # JSON schema for validating intake templates
└── templates/
    ├── _base.yaml               # Common fields shared across all templates
    ├── general.yaml             # General project intake (fallback)
    ├── analytics.yaml           # Data analytics project intake
    ├── ml-model.yaml            # ML/AI model project intake
    ├── webapp.yaml              # Web application project intake
    ├── supply-chain.yaml        # Supply chain optimization intake
    └── presentation.yaml        # Presentation/deck intake (consulting focus)
```

## Template Structure

Each intake template YAML file follows this structure:

```yaml
# Template metadata
template:
  id: "presentation"
  name: "Presentation Content"
  description: "Create consulting project deliverables or client pitch decks"
  version: "1.0.0"
  extends: "_base"              # Inherits common fields
  
# Brand constraints (pulled from client governance)
brand_constraints:
  inherit_from_governance: true
  overrides: {}                 # Template-specific overrides

# Interview phases (ordered)
phases:
  - id: "core_identity"
    name: "Core Identity"
    description: "Basic information about your presentation"
    required: true
    questions:
      - id: "presentation_type"
        question: "What type of presentation is this?"
        type: "choice"
        required: true
        options:
          - value: "project_report"
            label: "Project Report (reporting out on consulting work)"
          - value: "client_pitch"
            label: "Client Pitch (proposing a new engagement)"
          - value: "internal_update"
            label: "Internal Update (team/leadership briefing)"
        conditional_next:
          project_report: "audience_analysis"
          client_pitch: "pitch_context"
          internal_update: "audience_analysis"

# Ad-hoc section (always allowed)
ad_hoc:
  enabled: true
  prompt: "Is there any additional context that would help us create a better presentation?"
  max_items: 10

# Output configuration
output:
  format: "intake_response"
  validation: "strict"
  merge_with_governance: true
```

## Question Types

| Type | Description | Validation |
|------|-------------|------------|
| `text` | Free-form text input | min_length, max_length, pattern |
| `textarea` | Multi-line text | min_length, max_length |
| `choice` | Single selection from options | options array required |
| `multi_choice` | Multiple selections | options array, min_items, max_items |
| `number` | Numeric input | min, max, step |
| `date` | Date picker | min_date, max_date |
| `file` | File upload | accepted_types, max_size |
| `list` | Dynamic list of items | item_schema, min_items, max_items |

## Conditional Logic

Questions can adapt based on previous answers:

```yaml
questions:
  - id: "has_competitors"
    question: "Will you be comparing against competitors?"
    type: "choice"
    options:
      - value: "yes"
        label: "Yes"
      - value: "no"
        label: "No"

  - id: "competitor_list"
    question: "List the key competitors to address:"
    type: "list"
    condition:
      field: "has_competitors"
      operator: "equals"
      value: "yes"
    item_schema:
      type: "text"
      placeholder: "Competitor name"
    min_items: 1
    max_items: 5
```

## Client Governance Integration

Templates automatically pull constraints from the client's `governance.yaml`:

```yaml
# In clients/kearney/governance.yaml
brand:
  colors:
    primary: "#7823DC"          # Kearney purple
  fonts:
    primary: "Arial"            # Presentations use Arial
    fallback: "Helvetica, sans-serif"
  constraints:
    no_emojis: true
    no_gridlines: true
    label_first_approach: true

# Automatically applied to presentation intake
# User sees: "Note: Kearney brand standards will be applied automatically"
```

## RSG-UI Integration

The frontend renders intake interviews during the Ready stage:

```typescript
// rsg-ui/src/components/IntakeWizard.tsx
interface IntakeWizardProps {
  templateId: string;
  clientSlug?: string;
  onComplete: (responses: IntakeResponse) => void;
}

// API endpoint
POST /api/intake/{template_id}/start
POST /api/intake/{template_id}/answer
POST /api/intake/{template_id}/complete
GET  /api/intake/{template_id}/status
```

## Adding a New Template

1. Create `intake/templates/{your_template}.yaml`
2. Define phases and questions
3. Reference `_base.yaml` for common fields
4. Add JSON schema validation in `intake/schema/`
5. Update RSG-UI to recognize the new template type
6. Test with sample data

## Validation

All intake responses are validated against:
1. Template schema (field types, required fields)
2. Client governance (brand constraints)
3. Custom validators (business rules)

```python
from intake.validator import IntakeValidator

validator = IntakeValidator(template_id="presentation", client_slug="kearney")
result = validator.validate(responses)

if result.is_valid:
    orchestrator.start_workflow(intake=result.data)
else:
    raise ValidationError(result.errors)
```

## Best Practices

1. **Required vs. Optional**: Mark only truly essential fields as required
2. **Sensible Defaults**: Provide defaults where appropriate
3. **Conditional Logic**: Don't ask questions that don't apply
4. **Ad-hoc Always**: Always allow users to add custom context
5. **Progressive Disclosure**: Start simple, reveal complexity as needed
6. **Help Text**: Provide clear guidance for each question
