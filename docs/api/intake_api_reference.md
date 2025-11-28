# Intake API Reference

Complete technical documentation for the Claude Code Orchestrator intake template system API.

## API Overview

The Intake API provides RESTful endpoints for managing structured requirement gathering sessions. It supports adaptive interviews, conditional logic, validation, and seamless integration with the orchestrator workflow engine.

**Base URL:** `http://localhost:8000/api/intake`  
**Authentication:** Bearer token (inherits from main application)  
**Content-Type:** `application/json`  
**API Version:** v2.0

### Quick Start

```bash
# Create a session
curl -X POST "http://localhost:8000/api/intake/sessions" \
  -H "Content-Type: application/json" \
  -d '{
    "template_id": "presentation",
    "client_slug": "kearney-default"
  }'

# Submit responses
curl -X PUT "http://localhost:8000/api/intake/sessions/{session_id}/responses" \
  -H "Content-Type: application/json" \
  -d '{
    "phase_id": "project_identity",
    "responses": {
      "project_name": "Q4 Strategy Review",
      "project_description": "Comprehensive review of Q4 strategic initiatives"
    },
    "auto_advance": true
  }'
```

## Session Management

### Create Session

Creates a new intake interview session with template and governance applied.

```http
POST /api/intake/sessions
```

**Request Body:**
```json
{
  "template_id": "presentation",
  "client_slug": "kearney-default",
  "user_id": "user-123",
  "metadata": {
    "source": "project_wizard",
    "referrer": "/dashboard"
  }
}
```

**Parameters:**
- `template_id` (string, required): ID of the template to use
- `client_slug` (string, optional): Client for governance rules (default: "kearney-default")
- `user_id` (string, optional): User creating the session
- `metadata` (object, optional): Additional session metadata

**Response (201 Created):**
```json
{
  "session_id": "session-abc123",
  "template_id": "presentation",
  "client_slug": "kearney-default", 
  "current_phase_id": "presentation_type",
  "progress_percent": 0.0,
  "is_complete": false,
  "created_at": "2024-11-28T10:00:00Z",
  "governance_notices": [
    "Kearney brand standards will be applied automatically"
  ],
  "estimated_completion_minutes": 20
}
```

**Error Responses:**
- `400 Bad Request`: Invalid template_id or client_slug
- `404 Not Found`: Template not found
- `500 Internal Server Error`: Session creation failed

---

### Get Session Status

Retrieves the current state of an intake session including progress, current phase, and available actions.

```http
GET /api/intake/sessions/{session_id}
```

**Parameters:**
- `session_id` (string, required): Session identifier

**Response (200 OK):**
```json
{
  "session_id": "session-abc123",
  "template_id": "presentation",
  "current_phase_id": "project_identity",
  "progress_percent": 25.0,
  "is_complete": false,
  "last_activity": "2024-11-28T10:15:00Z",
  "phases": [
    {
      "phase_id": "presentation_type",
      "name": "Presentation Type",
      "description": "What kind of presentation are you creating?",
      "order": 5,
      "is_current": false,
      "is_complete": true,
      "is_available": true,
      "progress_percent": 100.0
    },
    {
      "phase_id": "project_identity", 
      "name": "Project Identity",
      "description": "Basic project information and context",
      "order": 10,
      "is_current": true,
      "is_complete": false,
      "is_available": true,
      "progress_percent": 40.0
    },
    {
      "phase_id": "audience_analysis",
      "name": "Audience Analysis",
      "description": "Understanding your target audience", 
      "order": 20,
      "is_current": false,
      "is_complete": false,
      "is_available": false,
      "progress_percent": 0.0
    }
  ],
  "current_questions": [
    {
      "id": "project_name",
      "question": "What is the name of your project?",
      "type": "text",
      "required": true,
      "placeholder": "e.g., Q4 Strategy Review",
      "help_text": "Choose a clear, descriptive name for your project",
      "validation": {
        "max_length": 100
      }
    }
  ],
  "responses": {
    "presentation_purpose": "project_report",
    "project_name": "Q4 Strategy Review"
  },
  "validation_errors": [],
  "governance_data": {
    "client_slug": "kearney-default",
    "brand_constraints": {
      "primary_color": "#7823DC",
      "font_family": "Arial"
    }
  }
}
```

**Error Responses:**
- `404 Not Found`: Session not found
- `410 Gone`: Session expired

---

### Submit Responses

Submits user responses for the current phase with validation and optional auto-advancement.

```http
PUT /api/intake/sessions/{session_id}/responses
```

**Request Body:**
```json
{
  "phase_id": "project_identity",
  "responses": {
    "project_name": "Q4 Strategy Review",
    "project_description": "Comprehensive review of our Q4 strategic initiatives and performance metrics",
    "project_timeline": "2024-12-15",
    "key_stakeholders": ["John Smith", "Sarah Johnson"]
  },
  "auto_advance": true,
  "validate_only": false
}
```

**Parameters:**
- `phase_id` (string, required): Phase being submitted
- `responses` (object, required): Field ID to value mapping
- `auto_advance` (boolean, optional): Auto-advance to next phase if valid (default: false)
- `validate_only` (boolean, optional): Only validate, don't save responses (default: false)

**Response (200 OK):**
```json
{
  "success": true,
  "validation_result": {
    "is_valid": true,
    "errors": [],
    "warnings": [
      {
        "field_id": "project_timeline",
        "message": "Timeline is quite aggressive for this scope",
        "severity": "warning"
      }
    ]
  },
  "next_phase_id": "audience_analysis",
  "advanced": true,
  "progress_percent": 50.0,
  "phase_complete": true,
  "derived_responses": {
    "project_slug": "q4-strategy-review"
  }
}
```

**Validation Error Response (422 Unprocessable Entity):**
```json
{
  "success": false,
  "validation_result": {
    "is_valid": false,
    "errors": [
      {
        "field_id": "project_name",
        "error_type": "required",
        "message": "Project name is required"
      },
      {
        "field_id": "project_timeline", 
        "error_type": "invalid_format",
        "message": "Date must be in YYYY-MM-DD format"
      }
    ],
    "warnings": []
  },
  "advanced": false,
  "progress_percent": 25.0
}
```

---

### Navigate Between Phases

Controls movement between phases, including validation of navigation constraints.

```http
POST /api/intake/sessions/{session_id}/navigate
```

**Request Body:**
```json
{
  "action": "next",
  "target_phase_id": "audience_analysis",
  "force": false
}
```

**Parameters:**
- `action` (string, required): Navigation action - "next", "previous", "goto"
- `target_phase_id` (string, optional): Required for "goto" action
- `force` (boolean, optional): Force navigation even with validation errors (default: false)

**Response (200 OK):**
```json
{
  "success": true,
  "previous_phase_id": "project_identity",
  "current_phase_id": "audience_analysis",
  "navigation_allowed": true,
  "validation_warnings": [],
  "progress_percent": 50.0
}
```

**Navigation Blocked Response (400 Bad Request):**
```json
{
  "success": false,
  "error": "navigation_blocked",
  "message": "Cannot advance with validation errors",
  "validation_errors": [
    {
      "field_id": "project_name",
      "message": "Project name is required before proceeding"
    }
  ],
  "current_phase_id": "project_identity"
}
```

---

### Complete Session

Completes the intake session, performs final validation, and creates the project.

```http
POST /api/intake/sessions/{session_id}/complete
```

**Request Body:**
```json
{
  "final_validation": true,
  "create_project": true,
  "force_complete": false
}
```

**Parameters:**
- `final_validation` (boolean, optional): Perform comprehensive validation (default: true)
- `create_project` (boolean, optional): Create project after validation (default: true)  
- `force_complete` (boolean, optional): Complete even with warnings (default: false)

**Response (201 Created):**
```json
{
  "success": true,
  "project_id": "project-xyz789",
  "validation_result": {
    "is_valid": true,
    "errors": [],
    "warnings": [
      {
        "field_id": "global",
        "message": "Some optional fields were left blank"
      }
    ]
  },
  "intake_summary": {
    "total_responses": 15,
    "phases_completed": 4,
    "governance_applied": true,
    "project_type": "presentation",
    "completion_time_seconds": 1240
  },
  "next_steps": {
    "redirect_url": "/projects/project-xyz789/ready",
    "workflow_status": "ready_to_start",
    "estimated_ready_time_hours": 2
  }
}
```

**Validation Failed Response (422 Unprocessable Entity):**
```json
{
  "success": false,
  "error": "validation_failed",
  "validation_result": {
    "is_valid": false,
    "errors": [
      {
        "field_id": "audience_analysis.target_audience",
        "message": "Target audience must be specified for client presentations"
      }
    ]
  },
  "required_phases": ["audience_analysis"],
  "completion_blocked": true
}
```

---

### Delete Session

Deletes an intake session and all associated data.

```http
DELETE /api/intake/sessions/{session_id}
```

**Parameters:**
- `session_id` (string, required): Session identifier

**Response (204 No Content)**

**Error Responses:**
- `404 Not Found`: Session not found
- `409 Conflict`: Cannot delete completed session

---

## Template Operations

### List Available Templates

Retrieves all available intake templates with filtering and metadata.

```http
GET /api/intake/templates
```

**Query Parameters:**
- `client_slug` (string, optional): Filter templates by client governance
- `category` (string, optional): Filter by template category
- `include_abstract` (boolean, optional): Include abstract/base templates (default: false)

**Response (200 OK):**
```json
[
  {
    "template_id": "presentation",
    "name": "Presentation Content",
    "description": "Create consulting project deliverables or client pitch decks",
    "category": "consulting", 
    "version": "1.0.0",
    "estimated_time_minutes": 20,
    "question_count": 15,
    "phase_count": 4,
    "icon": "presentation",
    "color": "#7823DC",
    "is_abstract": false,
    "requires_governance": true,
    "supported_clients": ["kearney-default", "accenture"],
    "tags": ["presentation", "consulting", "deliverable"]
  },
  {
    "template_id": "analytics",
    "name": "Analytics Project", 
    "description": "Data analysis and insights generation projects",
    "category": "analytics",
    "version": "2.1.0",
    "estimated_time_minutes": 35,
    "question_count": 22,
    "phase_count": 5,
    "icon": "analytics",
    "color": "#1E88E5",
    "is_abstract": false,
    "requires_governance": false,
    "supported_clients": ["all"],
    "tags": ["analytics", "data", "insights"]
  }
]
```

---

### Get Template Definition

Retrieves the complete template structure with governance rules applied.

```http
GET /api/intake/templates/{template_id}
```

**Query Parameters:**
- `client_slug` (string, optional): Apply client-specific governance
- `include_conditions` (boolean, optional): Include conditional logic details (default: true)
- `resolve_inheritance` (boolean, optional): Resolve template inheritance (default: true)

**Response (200 OK):**
```json
{
  "template": {
    "id": "presentation",
    "name": "Presentation Content",
    "description": "Create consulting project deliverables or client pitch decks",
    "version": "1.0.0",
    "extends": "_base",
    "icon": "presentation",
    "color": "#7823DC"
  },
  "phases": [
    {
      "id": "presentation_type",
      "name": "Presentation Type",
      "description": "What kind of presentation are you creating?",
      "order": 5,
      "required": true,
      "questions": [
        {
          "id": "presentation_purpose",
          "question": "What is the purpose of this presentation?",
          "type": "choice",
          "required": true,
          "options": [
            {
              "value": "project_report",
              "label": "Project Report-Out",
              "description": "Presenting findings from a completed engagement"
            },
            {
              "value": "client_pitch", 
              "label": "Client Pitch / Proposal",
              "description": "Proposing a new engagement to a potential client"
            }
          ],
          "conditional_next": {
            "client_pitch": "client_analysis",
            "project_report": "project_identity"
          }
        }
      ]
    }
  ],
  "governance_applied": true,
  "brand_constraints": {
    "primary_color": "#7823DC",
    "font_family": "Arial",
    "no_emojis": true
  },
  "estimated_completion_time": 1200,
  "inheritance_chain": ["_base", "presentation"]
}
```

**Error Responses:**
- `404 Not Found`: Template not found
- `400 Bad Request`: Invalid client_slug

---

## Utility Endpoints

### Validate Responses

Validates responses against template and governance rules without saving.

```http
POST /api/intake/validate
```

**Request Body:**
```json
{
  "template_id": "presentation",
  "client_slug": "kearney-default",
  "phase_id": "project_identity",
  "responses": {
    "project_name": "Q4 Strategy Review",
    "project_description": "Strategic review",
    "project_timeline": "invalid-date"
  },
  "validation_level": "strict"
}
```

**Parameters:**
- `template_id` (string, required): Template to validate against
- `client_slug` (string, optional): Client governance context
- `phase_id` (string, optional): Specific phase to validate
- `responses` (object, required): Field values to validate
- `validation_level` (string, optional): "strict", "normal", "lenient" (default: "normal")

**Response (200 OK):**
```json
{
  "is_valid": false,
  "validation_level": "normal",
  "errors": [
    {
      "field_id": "project_timeline",
      "error_type": "invalid_format", 
      "message": "Date must be in YYYY-MM-DD format",
      "details": {
        "provided_value": "invalid-date",
        "expected_format": "YYYY-MM-DD"
      }
    }
  ],
  "warnings": [
    {
      "field_id": "project_description",
      "message": "Description is quite brief for a strategic project",
      "severity": "low"
    }
  ],
  "suggestions": [
    {
      "field_id": "project_description",
      "suggestion": "Consider adding more detail about project scope and objectives"
    }
  ]
}
```

---

### Preview Template

Retrieves template structure for preview/development purposes with all conditional paths.

```http
GET /api/intake/preview/{template_id}
```

**Query Parameters:**
- `include_hidden` (boolean, optional): Include hidden questions (default: false)
- `expand_conditions` (boolean, optional): Show all conditional branches (default: true)
- `client_slug` (string, optional): Preview with client governance

**Response (200 OK):**
```json
{
  "template_id": "presentation",
  "total_questions": 15,
  "conditional_questions": 8,
  "hidden_questions": 2,
  "validation_rules": 12,
  "phases": [
    {
      "phase_id": "presentation_type",
      "question_count": 1,
      "conditional_paths": [
        {
          "condition": "presentation_purpose = 'client_pitch'",
          "leads_to": ["client_analysis", "market_research"],
          "adds_questions": 6
        },
        {
          "condition": "presentation_purpose = 'project_report'", 
          "leads_to": ["project_identity", "findings_analysis"],
          "adds_questions": 4
        }
      ]
    }
  ],
  "dependency_graph": {
    "presentation_purpose": ["client_info", "market_analysis", "project_scope"],
    "client_info": ["competitive_analysis"],
    "data_sources": ["analysis_methodology", "validation_approach"]
  },
  "estimated_paths": [
    {
      "path": "client_pitch_path",
      "total_questions": 18,
      "estimated_minutes": 25
    },
    {
      "path": "project_report_path", 
      "total_questions": 13,
      "estimated_minutes": 18
    }
  ]
}
```

---

### Health Check

Checks API health and system status.

```http
GET /api/intake/health
```

**Response (200 OK):**
```json
{
  "status": "healthy",
  "timestamp": "2024-11-28T10:00:00Z",
  "version": "2.0.0",
  "checks": {
    "template_loader": "healthy",
    "session_storage": "healthy", 
    "governance_service": "healthy",
    "validation_service": "healthy"
  },
  "statistics": {
    "active_sessions": 12,
    "templates_loaded": 8,
    "sessions_today": 47,
    "average_response_time_ms": 89
  }
}
```

---

## Data Models

### Session Objects

**IntakeSession**
```typescript
{
  session_id: string;
  user_id?: string;
  template_id: string;
  client_slug: string;
  current_phase_id?: string;
  phase_order: string[];
  completed_phases: string[];
  responses: Record<string, any>;
  derived_responses: Record<string, any>;
  governance_data: Record<string, any>;
  validation_errors: ValidationError[];
  is_complete: boolean;
  project_id?: string;
  created_at: string;
  updated_at: string;
  last_activity: string;
  metadata: Record<string, any>;
}
```

**SessionStatusResponse**
```typescript
{
  session_id: string;
  template_id: string;
  current_phase_id?: string;
  progress_percent: number;
  is_complete: boolean;
  last_activity: string;
  phases: PhaseStatus[];
  current_questions: QuestionDefinition[];
  responses: Record<string, any>;
  validation_errors: ValidationError[];
  governance_data: Record<string, any>;
}
```

### Template Objects

**TemplateDefinition**
```typescript
{
  template: TemplateMetadata;
  phases: PhaseDefinition[];
  brand_constraints?: BrandConstraints;
  governance?: GovernanceConfig;
  output?: OutputConfig;
}
```

**QuestionDefinition**
```typescript
{
  id: string;
  question?: string;
  type: QuestionType;
  required: boolean;
  default?: any;
  placeholder?: string;
  help_text?: string;
  validation?: ValidationRules;
  condition?: ConditionDefinition;
  options?: OptionDefinition[];
  min_value?: number;
  max_value?: number;
  min_items?: number;
  max_items?: number;
  hidden: boolean;
  readonly: boolean;
  width: string;
}
```

### Validation Objects

**ValidationError**
```typescript
{
  field_id: string;
  error_type: string;
  message: string;
  details?: Record<string, any>;
  severity?: 'error' | 'warning' | 'info';
}
```

**ValidationResult**
```typescript
{
  is_valid: boolean;
  errors: ValidationError[];
  warnings: ValidationError[];
  suggestions?: ValidationSuggestion[];
}
```

### Response Objects

**ResponseSubmissionResult**
```typescript
{
  success: boolean;
  validation_result: ValidationResult;
  next_phase_id?: string;
  advanced: boolean;
  progress_percent: number;
  phase_complete: boolean;
  derived_responses?: Record<string, any>;
}
```

**ProjectCreationResult**
```typescript
{
  success: boolean;
  project_id?: string;
  validation_result: ValidationResult;
  intake_summary: IntakeSummary;
  next_steps: NextSteps;
}
```

## Error Handling

### Standard Error Response

All API endpoints return errors in this format:

```json
{
  "error": "error_type",
  "message": "Human readable error message",
  "details": {
    "field": "specific_field_if_applicable",
    "provided_value": "what_was_provided",
    "expected": "what_was_expected"
  },
  "request_id": "req-abc123",
  "timestamp": "2024-11-28T10:00:00Z"
}
```

### HTTP Status Codes

- **200 OK**: Successful request
- **201 Created**: Resource created successfully
- **204 No Content**: Successful deletion
- **400 Bad Request**: Invalid request parameters
- **401 Unauthorized**: Authentication required
- **403 Forbidden**: Insufficient permissions
- **404 Not Found**: Resource not found
- **409 Conflict**: Resource conflict (e.g., duplicate session)
- **410 Gone**: Resource expired
- **422 Unprocessable Entity**: Validation failed
- **429 Too Many Requests**: Rate limit exceeded
- **500 Internal Server Error**: Server error

### Common Error Types

**validation_failed**
```json
{
  "error": "validation_failed",
  "message": "One or more fields contain invalid data",
  "details": {
    "validation_errors": [/* ValidationError objects */]
  }
}
```

**session_not_found**
```json
{
  "error": "session_not_found", 
  "message": "Session with ID 'session-abc123' not found",
  "details": {
    "session_id": "session-abc123"
  }
}
```

**template_not_found**
```json
{
  "error": "template_not_found",
  "message": "Template 'invalid-template' not found",
  "details": {
    "template_id": "invalid-template",
    "available_templates": ["presentation", "analytics", "ml-model"]
  }
}
```

## Rate Limiting

The API implements rate limiting to ensure fair usage:

- **Session Creation**: 10 sessions per user per hour
- **Response Submission**: 100 requests per session per hour  
- **Navigation**: 200 requests per session per hour
- **Template Retrieval**: 1000 requests per user per hour

Rate limit headers are included in responses:
```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 87
X-RateLimit-Reset: 1701172800
```

## Authentication & Authorization

The Intake API inherits authentication from the main orchestrator application:

```bash
# Include Authorization header with all requests
curl -H "Authorization: Bearer $API_TOKEN" \
     -H "Content-Type: application/json" \
     "http://localhost:8000/api/intake/sessions"
```

### Permissions

- **User Sessions**: Users can only access their own sessions
- **Admin Sessions**: Admins can access all sessions  
- **Template Access**: Based on client governance rules
- **Session Sharing**: Sessions can be shared via session tokens

## SDK Examples

### Python Client

```python
from orchestrator_v2.api.client import IntakeClient

# Initialize client
client = IntakeClient(base_url="http://localhost:8000", api_key="your-token")

# Create session
session = await client.create_session(
    template_id="presentation",
    client_slug="kearney-default"
)

# Submit responses
result = await client.submit_responses(
    session_id=session.session_id,
    phase_id="project_identity",
    responses={
        "project_name": "Q4 Strategy Review",
        "project_description": "Strategic review of Q4 initiatives"
    },
    auto_advance=True
)

# Complete session
completion = await client.complete_session(session.session_id)
print(f"Project created: {completion.project_id}")
```

### JavaScript Client

```javascript
import { IntakeAPI } from './api/intake';

const client = new IntakeAPI('http://localhost:8000', 'your-token');

// Create session
const session = await client.createSession({
  templateId: 'presentation',
  clientSlug: 'kearney-default'
});

// Submit responses
const result = await client.submitResponses(
  session.sessionId,
  'project_identity',
  {
    project_name: 'Q4 Strategy Review',
    project_description: 'Strategic review of Q4 initiatives'
  },
  { autoAdvance: true }
);

// Complete session
const completion = await client.completeSession(session.sessionId);
console.log(`Project created: ${completion.projectId}`);
```

---

*This API reference covers all endpoints and functionality of the Intake Template System. For implementation guides, see the [User Guide](../user_guide/intake_wizard_guide.md) and [Developer Guide](../developer/creating_intake_templates.md).*