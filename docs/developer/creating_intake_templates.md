# Creating Intake Templates

**Developer guide for building and customizing intake templates**

## Overview

Intake templates define structured interviews that gather comprehensive project requirements. This guide covers creating new templates, customizing existing ones, and implementing advanced features like conditional logic and governance integration.

### What You'll Learn
- Template structure and YAML syntax
- Phase and question design patterns
- Conditional logic implementation
- Validation rule configuration
- Client governance integration
- Testing and deployment workflows

## Template Anatomy

### Basic Structure

Every intake template is a YAML file with this structure:

```yaml
# Template metadata
template:
  id: "my-template"
  name: "My Template"
  description: "Template description"
  version: "1.0.0"
  extends: "_base"  # Optional inheritance
  icon: "icon-name"
  color: "#7823DC"

# Optional brand constraints
brand_constraints:
  inherit_from_governance: true
  template_specific:
    font: "Arial"
    no_emojis: true

# Interview phases
phases:
  - id: "phase_1"
    name: "Phase Name"
    description: "Phase description"
    order: 10
    required: true
    questions:
      - id: "question_1"
        question: "What is your question?"
        type: "text"
        required: true

# Optional governance rules
governance:
  validation_rules:
    - field: "project_name"
      type: "length"
      min: 5
      max: 100

# Output configuration
output:
  format: "project_profile"
  include_governance: true
```

### File Location

Templates are stored in `/intake/templates/` with the naming convention:
- `{template_id}.yaml` for main templates
- `_base.yaml` for base templates
- `starter.{category}.yaml` for starter templates

## Building Your First Template

### Step 1: Create the Template File

Create `/intake/templates/my-project.yaml`:

```yaml
template:
  id: "my-project"
  name: "My Project Type"
  description: "Template for my specific project type"
  version: "1.0.0"
  extends: "_base"
  icon: "project"
  color: "#1976D2"

phases:
  - id: "project_basics"
    name: "Project Basics"
    description: "Essential project information"
    order: 10
    required: true
    questions:
      
      - id: "project_name"
        question: "What is the name of your project?"
        type: "text"
        required: true
        placeholder: "e.g., Customer Analytics Dashboard"
        help_text: "Choose a clear, descriptive name"
        validation:
          min_length: 5
          max_length: 100
          
      - id: "project_description"
        question: "Describe your project objectives"
        type: "textarea"
        required: true
        placeholder: "Describe what you're trying to accomplish..."
        help_text: "Be specific about goals and expected outcomes"
        validation:
          min_length: 50
          max_length: 500
```

### Step 2: Test the Template

```bash
# Validate template syntax
python scripts/validate_template.py intake/templates/my-project.yaml

# Test template in development
python scripts/test_template.py my-project --interactive
```

### Step 3: Register and Deploy

Add your template to the template registry:

```python
# In orchestrator_v2/services/intake_service.py
AVAILABLE_TEMPLATES = {
    "my-project": {
        "name": "My Project Type",
        "category": "custom",
        "estimated_minutes": 20
    }
}
```

## Question Types Reference

### Text Input
```yaml
- id: "short_text_field"
  question: "Enter short text"
  type: "text"
  required: true
  placeholder: "Example text"
  validation:
    min_length: 1
    max_length: 200
    pattern: "^[A-Za-z0-9\\s]+$"  # Alphanumeric only
```

### Text Area
```yaml
- id: "long_text_field"
  question: "Enter detailed description"
  type: "textarea"
  required: true
  placeholder: "Provide detailed information..."
  validation:
    min_length: 50
    max_length: 2000
```

### Number Input
```yaml
- id: "budget_amount"
  question: "What is your budget?"
  type: "number"
  required: true
  placeholder: "100000"
  min_value: 1000
  max_value: 10000000
  step: 1000
  unit: "USD"
  validation:
    min_value: 1000
    max_value: 10000000
```

### Single Choice
```yaml
- id: "project_priority"
  question: "What is the project priority?"
  type: "choice"
  required: true
  options:
    - value: "low"
      label: "Low Priority"
      description: "Can be delayed if necessary"
    - value: "medium"
      label: "Medium Priority"  
      description: "Important but not urgent"
    - value: "high"
      label: "High Priority"
      description: "Critical business need"
    - value: "urgent"
      label: "Urgent"
      description: "Immediate action required"
```

### Multiple Choice
```yaml
- id: "data_sources"
  question: "Which data sources will you use?"
  type: "multi_choice"
  required: true
  validation:
    min_items: 1
    max_items: 5
  options:
    - value: "crm"
      label: "CRM System"
      description: "Customer relationship management data"
    - value: "sales"
      label: "Sales Data"
      description: "Transaction and revenue data"
    - value: "web"
      label: "Web Analytics"
      description: "Website behavior and traffic data"
    - value: "social"
      label: "Social Media"
      description: "Social platform engagement data"
```

### Date Input
```yaml
- id: "project_deadline"
  question: "When is the project deadline?"
  type: "date"
  required: true
  help_text: "Select the final delivery date"
  validation:
    min_date: "2024-01-01"
    max_date: "2025-12-31"
```

### List Input
```yaml
- id: "team_members"
  question: "Who are the team members?"
  type: "list"
  required: true
  min_items: 1
  max_items: 10
  help_text: "Add each team member"
  item_schema:
    type: "object"
    properties:
      name: 
        type: "text"
        validation:
          min_length: 2
          max_length: 50
      role:
        type: "choice"
        options:
          - value: "pm"
            label: "Project Manager"
          - value: "analyst"
            label: "Analyst"
          - value: "developer"
            label: "Developer"
      email:
        type: "text"
        validation:
          pattern: "^[\\w\\.-]+@[\\w\\.-]+\\.[a-zA-Z]{2,}$"
```

### Object Input
```yaml
- id: "project_contact"
  question: "Primary project contact"
  type: "object"
  required: true
  properties:
    name:
      question: "Contact name"
      type: "text"
      required: true
      validation:
        min_length: 2
        max_length: 50
    email:
      question: "Email address"
      type: "text"
      required: true
      validation:
        pattern: "^[\\w\\.-]+@[\\w\\.-]+\\.[a-zA-Z]{2,}$"
    phone:
      question: "Phone number"
      type: "text"
      required: false
      placeholder: "+1-555-123-4567"
```

### Derived Fields
```yaml
- id: "project_slug"
  type: "derived"
  derived_from: "project_name"
  transform: "slugify"  # Built-in transformations: slugify, uppercase, lowercase

- id: "full_project_name" 
  type: "derived"
  derived_from: ["client_name", "project_name"]
  transform: "template"
  template: "{client_name} - {project_name}"
```

## Conditional Logic

### Simple Conditions

Show questions based on previous answers:

```yaml
- id: "has_existing_data"
  question: "Do you have existing data to analyze?"
  type: "choice"
  required: true
  options:
    - value: "yes"
      label: "Yes, we have existing data"
    - value: "no" 
      label: "No, we need to collect data"

- id: "data_location"
  question: "Where is your existing data stored?"
  type: "choice"
  required: true
  # Only show if previous answer was "yes"
  condition:
    field: "has_existing_data"
    operator: "equals"
    value: "yes"
  options:
    - value: "database"
      label: "Database"
    - value: "files"
      label: "Files (CSV, Excel)"
    - value: "api"
      label: "API Access"

- id: "data_collection_method"
  question: "How will you collect the data?"
  type: "multi_choice"
  required: true
  # Only show if previous answer was "no"
  condition:
    field: "has_existing_data"
    operator: "equals"
    value: "no"
  options:
    - value: "surveys"
      label: "Surveys"
    - value: "interviews"
      label: "Interviews"
    - value: "observation"
      label: "Direct Observation"
```

### Complex Conditions

Use AND/OR logic for sophisticated conditionals:

```yaml
- id: "advanced_analytics"
  question: "Do you need advanced analytics features?"
  type: "choice"
  required: true
  # Show only for large budgets AND high priority projects
  condition:
    field: "budget_amount"
    operator: "greater_than"
    value: 100000
    and_conditions:
      - field: "project_priority"
        operator: "in"
        value: ["high", "urgent"]
  options:
    - value: "ml"
      label: "Machine Learning"
    - value: "ai"
      label: "Artificial Intelligence"  
    - value: "predictive"
      label: "Predictive Analytics"

- id: "compliance_requirements"
  question: "What compliance requirements apply?"
  type: "multi_choice"
  required: true
  # Show if dealing with sensitive data OR financial data
  condition:
    field: "data_sensitivity"
    operator: "equals"
    value: "sensitive"
    or_conditions:
      - field: "industry"
        operator: "in"
        value: ["finance", "healthcare", "government"]
  options:
    - value: "gdpr"
      label: "GDPR"
    - value: "hipaa"
      label: "HIPAA"
    - value: "sox"
      label: "SOX"
```

### Conditional Navigation

Control phase flow based on responses:

```yaml
phases:
  - id: "project_type"
    name: "Project Type"
    order: 10
    questions:
      - id: "project_category"
        question: "What type of project is this?"
        type: "choice"
        required: true
        # Different next phases based on selection
        conditional_next:
          "analytics": "data_analysis_setup"
          "webapp": "technical_requirements" 
          "ml": "model_requirements"
        options:
          - value: "analytics"
            label: "Data Analytics"
          - value: "webapp"
            label: "Web Application"
          - value: "ml"
            label: "Machine Learning"

  - id: "data_analysis_setup"
    name: "Data Analysis Setup"
    order: 20
    # Only available if analytics was selected
    condition:
      field: "project_category"
      operator: "equals"
      value: "analytics"
    questions:
      # Analytics-specific questions...

  - id: "technical_requirements"
    name: "Technical Requirements"
    order: 20
    # Only available if webapp was selected
    condition:
      field: "project_category"
      operator: "equals"
      value: "webapp"
    questions:
      # Web app-specific questions...
```

### Conditional Phase Display

Show/hide entire phases based on conditions:

```yaml
- id: "advanced_configuration"
  name: "Advanced Configuration"
  order: 90
  required: false
  # Only show for experienced users
  condition:
    field: "user_experience"
    operator: "equals"
    value: "expert"
    and_conditions:
      - field: "enable_advanced_features"
        operator: "equals"
        value: true
```

## Validation Rules

### Built-in Validation

```yaml
validation:
  # Text validation
  min_length: 5
  max_length: 100
  pattern: "^[A-Za-z0-9\\s]+$"
  
  # Number validation  
  min_value: 0
  max_value: 1000000
  
  # Date validation
  min_date: "2024-01-01"
  max_date: "2025-12-31"
  
  # List validation
  min_items: 1
  max_items: 10
  
  # Object validation
  required_fields: ["name", "email"]
```

### Custom Validation Functions

Define custom validation logic in Python:

```python
# In orchestrator_v2/services/validation_service.py

class CustomValidationService:
    
    def validate_project_name_uniqueness(self, value: str, context: dict) -> ValidationResult:
        """Ensure project name is unique within client organization."""
        existing_projects = self.project_service.get_projects_by_client(
            context.get("client_slug")
        )
        
        if any(p.name.lower() == value.lower() for p in existing_projects):
            return ValidationResult(
                is_valid=False,
                error_message="A project with this name already exists"
            )
        
        return ValidationResult(is_valid=True)
    
    def validate_email_domain(self, value: str, context: dict) -> ValidationResult:
        """Validate email domain against allowed list."""
        allowed_domains = context.get("allowed_email_domains", [])
        
        if not allowed_domains:
            return ValidationResult(is_valid=True)
            
        domain = value.split("@")[-1].lower()
        if domain not in allowed_domains:
            return ValidationResult(
                is_valid=False,
                error_message=f"Email domain must be one of: {', '.join(allowed_domains)}"
            )
        
        return ValidationResult(is_valid=True)
```

Register custom validators in your template:

```yaml
- id: "project_name"
  question: "What is the project name?"
  type: "text"
  required: true
  validation:
    min_length: 5
    max_length: 50
    custom_validators:
      - "validate_project_name_uniqueness"

- id: "contact_email"
  question: "Primary contact email"
  type: "text"
  required: true
  validation:
    pattern: "^[\\w\\.-]+@[\\w\\.-]+\\.[a-zA-Z]{2,}$"
    custom_validators:
      - "validate_email_domain"
```

## Template Inheritance

### Base Template Pattern

Create reusable base templates:

```yaml
# _base.yaml
template:
  id: "_base"
  name: "Base Template"
  is_abstract: true

phases:
  - id: "project_identity"
    name: "Project Identity"
    order: 10
    required: true
    questions:
      - id: "project_name"
        question: "What is the name of your project?"
        type: "text"
        required: true
        validation:
          min_length: 5
          max_length: 100
          
      - id: "project_description"
        question: "Describe your project"
        type: "textarea"
        required: true
        validation:
          min_length: 20
          max_length: 1000

# Default governance for all templates
governance:
  validation_rules:
    - field: "project_name"
      type: "uniqueness"
      scope: "client"
      
brand_constraints:
  primary_color: "#7823DC"
  font_family: "Inter"
```

### Extending Base Templates

```yaml
# analytics.yaml
template:
  id: "analytics"
  name: "Analytics Project"
  extends: "_base"  # Inherits all phases and questions
  version: "1.0.0"

# Add analytics-specific phases
phases:
  # project_identity inherited from _base
  
  - id: "data_requirements"
    name: "Data Requirements"
    order: 20
    required: true
    questions:
      - id: "data_sources"
        question: "What data sources will you analyze?"
        type: "multi_choice"
        required: true
        options:
          - value: "sales"
            label: "Sales Data"
          - value: "customer"
            label: "Customer Data"
          - value: "web"
            label: "Web Analytics"

# Override base governance with analytics-specific rules
governance:
  inherit_from_base: true
  validation_rules:
    - field: "data_sources"
      type: "min_items"
      value: 1
      
brand_constraints:
  inherit_from_base: true
  analytics_specific:
    chart_types: ["bar", "line", "scatter"]
    color_palette: "data_visualization"
```

### Multi-level Inheritance

```yaml
# consulting_base.yaml
template:
  id: "consulting_base"
  extends: "_base"
  is_abstract: true

phases:
  # Inherits project_identity from _base
  
  - id: "client_context"
    name: "Client Context"
    order: 15
    questions:
      - id: "client_industry"
        question: "What industry is the client in?"
        type: "choice"
        required: true
        options:
          - value: "financial"
            label: "Financial Services"
          - value: "healthcare"
            label: "Healthcare"
          - value: "technology"
            label: "Technology"

# presentation.yaml
template:
  id: "presentation"
  extends: "consulting_base"  # Three levels: _base -> consulting_base -> presentation

phases:
  # Inherits project_identity and client_context
  
  - id: "presentation_specifics"
    name: "Presentation Details"
    order: 30
    questions:
      - id: "audience_level"
        question: "What is the audience level?"
        type: "choice"
        required: true
        options:
          - value: "executive"
            label: "Executive Leadership"
          - value: "manager"
            label: "Management Team"
          - value: "team"
            label: "Working Team"
```

## Client Governance Integration

### Governance File Structure

Create client-specific governance rules in `/clients/{client_slug}/governance.yaml`:

```yaml
# clients/acme-corp/governance.yaml
client:
  slug: "acme-corp"
  name: "ACME Corporation"

# Brand constraints applied to all templates
brand:
  primary_color: "#FF6600"
  secondary_color: "#0066CC"
  font_family: "Helvetica"
  logo_url: "/assets/acme-logo.png"
  
  # Presentation-specific branding
  presentation:
    template: "acme_corporate"
    max_slides: 25
    include_disclaimer: true

# Validation rules
validation:
  - templates: ["all"]
    rules:
      - field: "project_name"
        type: "pattern"
        pattern: "^ACME-[A-Z0-9]+-.*$"
        message: "Project names must start with 'ACME-' prefix"
      
      - field: "contact_email"
        type: "domain"
        allowed_domains: ["acme.com", "acme-consulting.com"]

  - templates: ["presentation", "analytics"]
    rules:
      - field: "budget_amount"
        type: "max_value"
        value: 500000
        message: "Projects over $500K require executive approval"

# Field defaults
defaults:
  project_owner: "ACME Project Office"
  compliance_level: "enterprise"
  security_classification: "internal"

# Required approvals
approvals:
  budget_over_100k:
    condition:
      field: "budget_amount"
      operator: "greater_than"
      value: 100000
    approvers: ["finance_director", "project_office"]
    
  external_data:
    condition:
      field: "data_sources"
      operator: "contains"
      value: "external"
    approvers: ["security_officer", "legal_counsel"]
```

### Template Governance Application

Templates automatically inherit and apply client governance:

```yaml
# Your template automatically gets client governance applied
template:
  id: "my-template"
  name: "My Template"
  # Governance will be applied based on user's client_slug

phases:
  - id: "project_basics"
    questions:
      - id: "project_name"
        question: "Project name"
        type: "text"
        required: true
        # Client validation rules automatically applied:
        # - ACME prefix requirement
        # - Uniqueness check within client
        
      - id: "contact_email"
        question: "Contact email"  
        type: "text"
        required: true
        # Client domain restrictions automatically applied
        
      - id: "budget_amount"
        question: "Project budget"
        type: "number"
        # Client budget limits automatically applied
        # Approval workflows triggered if needed
```

### Dynamic Governance

Apply different governance based on project characteristics:

```yaml
# In client governance file
conditional_governance:
  - name: "high_value_projects"
    condition:
      field: "budget_amount" 
      operator: "greater_than"
      value: 1000000
    additional_validation:
      - field: "executive_sponsor"
        type: "required"
        message: "Executive sponsor required for projects over $1M"
      - field: "risk_assessment"
        type: "required"
        message: "Risk assessment required for high-value projects"
    additional_phases:
      - id: "executive_review"
        name: "Executive Review"
        order: 100
        questions:
          - id: "executive_approval"
            question: "Executive approval received?"
            type: "choice"
            required: true
            options:
              - value: "approved"
                label: "Approved"
              - value: "pending"
                label: "Pending Approval"
```

## Advanced Features

### Multi-Language Support

```yaml
# Template with multiple languages
template:
  id: "multilingual-template"
  name: "Multilingual Template"
  supported_languages: ["en", "es", "fr"]

phases:
  - id: "project_basics"
    name:
      en: "Project Basics"
      es: "Información Básica del Proyecto"
      fr: "Informations de Base du Projet"
    questions:
      - id: "project_name"
        question:
          en: "What is the project name?"
          es: "¿Cuál es el nombre del proyecto?"
          fr: "Quel est le nom du projet ?"
        type: "text"
        required: true
        placeholder:
          en: "Enter project name"
          es: "Ingrese el nombre del proyecto"
          fr: "Entrez le nom du projet"
```

### Template Versioning

```yaml
template:
  id: "my-template"
  version: "2.0.0"
  changelog:
    "2.0.0": 
      - "Added conditional logic for advanced users"
      - "Improved validation rules"
      - "Added new question types"
    "1.1.0":
      - "Fixed validation bug"
      - "Added help text"
    "1.0.0":
      - "Initial release"
      
  # Migration rules for version upgrades
  migrations:
    "1.x.x -> 2.0.0":
      field_renames:
        "old_field_name": "new_field_name"
      field_transformations:
        "priority_level":
          from: "1,2,3"  # Old: numeric
          to: "low,medium,high"  # New: text values
          mapping:
            "1": "low"
            "2": "medium" 
            "3": "high"
```

### Dynamic Question Generation

```python
# Custom question generator
class DynamicQuestionGenerator:
    
    def generate_data_source_questions(self, context: dict) -> list[QuestionDefinition]:
        """Generate questions based on selected data sources."""
        
        selected_sources = context.get("data_sources", [])
        questions = []
        
        for source in selected_sources:
            if source == "database":
                questions.append(QuestionDefinition(
                    id=f"database_connection_{source}",
                    question=f"What is the connection string for {source}?",
                    type="text",
                    required=True
                ))
                
            elif source == "api":
                questions.extend([
                    QuestionDefinition(
                        id=f"api_endpoint_{source}",
                        question=f"What is the API endpoint for {source}?",
                        type="text",
                        required=True
                    ),
                    QuestionDefinition(
                        id=f"api_key_{source}",
                        question=f"API key for {source}",
                        type="text",
                        required=True,
                        hidden=True  # Secure field
                    )
                ])
                
        return questions

# Register generator in template
template:
  id: "dynamic-template"
  dynamic_generators:
    - trigger_field: "data_sources"
      generator: "generate_data_source_questions"
      insert_after: "data_sources"
```

### Integration Hooks

```yaml
# Template with external integrations
template:
  id: "integration-template"
  integrations:
    jira:
      enabled: true
      create_epic: true
      epic_template: "Analytics Project Epic"
      
    slack:
      enabled: true
      notify_channel: "#project-updates"
      message_template: "New project created: {project_name}"
      
    calendar:
      enabled: true
      create_milestone_events: true
      calendar_id: "team-calendar"

# Hooks for external actions
hooks:
  on_session_created:
    - action: "notify_slack"
      channel: "#intake-notifications"
      message: "New intake session started by {user_name}"
      
  on_session_completed:
    - action: "create_jira_epic"
      project: "PROJ" 
      summary: "{project_name}"
      description: "{project_description}"
      
    - action: "send_email"
      to: "{contact_email}"
      template: "project_created"
      subject: "Your project '{project_name}' has been created"
```

## Testing Templates

### Unit Testing

```python
# test_my_template.py
import pytest
from orchestrator_v2.services.intake_service import TemplateService
from orchestrator_v2.services.validation_service import ValidationService

class TestMyTemplate:
    
    @pytest.fixture
    def template_service(self):
        return TemplateService()
    
    @pytest.fixture
    def validation_service(self):
        return ValidationService()
    
    @pytest.fixture
    async def template(self, template_service):
        return await template_service.load_template("my-template")
    
    async def test_template_loads_successfully(self, template):
        assert template is not None
        assert template.template.id == "my-template"
        assert len(template.phases) > 0
    
    async def test_required_questions_present(self, template):
        phase = template.phase_map["project_basics"]
        question_ids = {q.id for q in phase.questions}
        
        required_questions = {"project_name", "project_description"}
        assert required_questions.issubset(question_ids)
    
    async def test_conditional_logic(self, template, validation_service):
        # Test that conditional questions appear correctly
        responses = {"has_existing_data": "yes"}
        
        phase = template.phase_map["data_setup"]
        visible_questions = validation_service.get_visible_questions(phase, responses)
        
        # Should include data_location question
        assert any(q.id == "data_location" for q in visible_questions)
        
        # Should not include data_collection_method
        assert not any(q.id == "data_collection_method" for q in visible_questions)
    
    async def test_validation_rules(self, validation_service):
        # Test field validation
        result = await validation_service.validate_field_value(
            field_type="text",
            value="ABC",  # Too short
            validation_rules={"min_length": 5, "max_length": 100}
        )
        
        assert not result.is_valid
        assert "min_length" in result.error_type
```

### Integration Testing

```python
# test_template_integration.py
import pytest
from fastapi.testclient import TestClient
from orchestrator_v2.api.server import app

class TestTemplateIntegration:
    
    @pytest.fixture
    def client(self):
        return TestClient(app)
    
    def test_template_session_workflow(self, client):
        # Create session
        response = client.post("/api/intake/sessions", json={
            "template_id": "my-template",
            "client_slug": "test-client"
        })
        assert response.status_code == 201
        session_data = response.json()
        session_id = session_data["session_id"]
        
        # Submit responses for first phase
        response = client.put(f"/api/intake/sessions/{session_id}/responses", json={
            "phase_id": "project_basics",
            "responses": {
                "project_name": "Test Project",
                "project_description": "This is a test project for validation"
            },
            "auto_advance": True
        })
        assert response.status_code == 200
        
        result = response.json()
        assert result["success"] is True
        assert result["validation_result"]["is_valid"] is True
        
        # Complete session
        response = client.post(f"/api/intake/sessions/{session_id}/complete")
        assert response.status_code == 201
        
        completion = response.json()
        assert completion["success"] is True
        assert "project_id" in completion
```

### Load Testing

```python
# test_template_performance.py
import asyncio
import time
from concurrent.futures import ThreadPoolExecutor
from orchestrator_v2.api.client import IntakeClient

async def test_concurrent_sessions():
    """Test template performance under load."""
    
    client = IntakeClient("http://localhost:8000")
    
    async def create_and_complete_session():
        start_time = time.time()
        
        # Create session
        session = await client.create_session(
            template_id="my-template",
            client_slug="load-test"
        )
        
        # Submit responses
        await client.submit_responses(
            session_id=session.session_id,
            phase_id="project_basics",
            responses={
                "project_name": f"Load Test Project {session.session_id}",
                "project_description": "Load testing project description"
            }
        )
        
        # Complete session
        await client.complete_session(session.session_id)
        
        end_time = time.time()
        return end_time - start_time
    
    # Run 50 concurrent sessions
    tasks = [create_and_complete_session() for _ in range(50)]
    durations = await asyncio.gather(*tasks)
    
    # Analyze performance
    avg_duration = sum(durations) / len(durations)
    max_duration = max(durations)
    
    assert avg_duration < 5.0  # Average under 5 seconds
    assert max_duration < 15.0  # Maximum under 15 seconds
    
    print(f"Average session duration: {avg_duration:.2f}s")
    print(f"Maximum session duration: {max_duration:.2f}s")
```

## Deployment and Maintenance

### Template Validation Script

```python
# scripts/validate_template.py
#!/usr/bin/env python3
"""Validate template syntax and logic."""

import sys
import yaml
from pathlib import Path
from orchestrator_v2.services.template_loader import TemplateLoader
from orchestrator_v2.services.validation_service import ValidationService

def validate_template(template_path: Path) -> bool:
    """Validate a template file."""
    
    try:
        # Load and parse YAML
        with open(template_path, 'r') as f:
            template_data = yaml.safe_load(f)
        
        # Validate structure
        loader = TemplateLoader()
        template = loader.parse_template(template_data)
        
        # Validate questions and logic
        validator = ValidationService()
        validation_result = validator.validate_template(template)
        
        if validation_result.is_valid:
            print(f"✅ Template {template_path.name} is valid")
            return True
        else:
            print(f"❌ Template {template_path.name} has errors:")
            for error in validation_result.errors:
                print(f"  - {error.message}")
            return False
            
    except Exception as e:
        print(f"❌ Failed to validate {template_path.name}: {e}")
        return False

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python validate_template.py <template_path>")
        sys.exit(1)
    
    template_path = Path(sys.argv[1])
    is_valid = validate_template(template_path)
    sys.exit(0 if is_valid else 1)
```

### Batch Template Updates

```python
# scripts/update_templates.py
#!/usr/bin/env python3
"""Update multiple templates with common changes."""

import yaml
from pathlib import Path
from typing import Dict, Any

def update_template_version(template_path: Path, new_version: str):
    """Update template version."""
    
    with open(template_path, 'r') as f:
        template = yaml.safe_load(f)
    
    template['template']['version'] = new_version
    
    with open(template_path, 'w') as f:
        yaml.dump(template, f, default_flow_style=False, sort_keys=False)

def add_governance_rules(template_path: Path, rules: list):
    """Add governance rules to template."""
    
    with open(template_path, 'r') as f:
        template = yaml.safe_load(f)
    
    if 'governance' not in template:
        template['governance'] = {}
    if 'validation_rules' not in template['governance']:
        template['governance']['validation_rules'] = []
    
    template['governance']['validation_rules'].extend(rules)
    
    with open(template_path, 'w') as f:
        yaml.dump(template, f, default_flow_style=False, sort_keys=False)

def bulk_update_templates():
    """Apply updates to all templates."""
    
    template_dir = Path("intake/templates")
    
    # New governance rules to add
    new_rules = [
        {
            "field": "project_name",
            "type": "uniqueness", 
            "scope": "global",
            "message": "Project name must be unique across all clients"
        }
    ]
    
    for template_file in template_dir.glob("*.yaml"):
        if template_file.name.startswith("_"):
            continue  # Skip base templates
            
        print(f"Updating {template_file.name}...")
        
        # Update version
        update_template_version(template_file, "2.1.0")
        
        # Add governance rules
        add_governance_rules(template_file, new_rules)
        
        print(f"✅ Updated {template_file.name}")

if __name__ == "__main__":
    bulk_update_templates()
    print("✅ All templates updated successfully")
```

### Template Analytics

Monitor template usage and performance:

```python
# scripts/template_analytics.py
#!/usr/bin/env python3
"""Generate analytics report for template usage."""

from datetime import datetime, timedelta
from collections import defaultdict
from orchestrator_v2.services.intake_service import IntakeSessionRepository

def generate_template_analytics():
    """Generate template usage analytics."""
    
    repo = IntakeSessionRepository()
    
    # Get sessions from last 30 days
    since_date = datetime.utcnow() - timedelta(days=30)
    sessions = repo.get_sessions_since(since_date)
    
    # Analyze usage patterns
    template_usage = defaultdict(int)
    completion_rates = defaultdict(list)
    average_duration = defaultdict(list)
    
    for session in sessions:
        template_usage[session.template_id] += 1
        
        if session.is_complete:
            completion_rates[session.template_id].append(1)
            duration = (session.updated_at - session.created_at).total_seconds()
            average_duration[session.template_id].append(duration)
        else:
            completion_rates[session.template_id].append(0)
    
    # Generate report
    print("📊 Template Analytics Report")
    print("=" * 50)
    
    for template_id in template_usage:
        usage = template_usage[template_id]
        completion_rate = sum(completion_rates[template_id]) / len(completion_rates[template_id])
        avg_duration = sum(average_duration[template_id]) / len(average_duration[template_id]) if average_duration[template_id] else 0
        
        print(f"\n{template_id}:")
        print(f"  Sessions: {usage}")
        print(f"  Completion Rate: {completion_rate:.1%}")
        print(f"  Average Duration: {avg_duration/60:.1f} minutes")

if __name__ == "__main__":
    generate_template_analytics()
```

## Best Practices

### Design Principles

1. **Start Simple**: Begin with essential questions and add complexity gradually
2. **User-Focused**: Write questions from the user's perspective
3. **Progressive Disclosure**: Use conditional logic to show relevant questions only
4. **Clear Language**: Use plain language, avoid jargon
5. **Logical Flow**: Order questions in a natural conversation flow

### Performance Optimization

1. **Minimize Question Count**: Ask only necessary questions
2. **Efficient Conditionals**: Use simple conditions when possible
3. **Template Caching**: Leverage built-in template caching
4. **Lazy Loading**: Load question details on-demand
5. **Validation Optimization**: Validate incrementally, not all at once

### Security Considerations

1. **Sensitive Data**: Mark sensitive fields with `hidden: true`
2. **Input Validation**: Always validate user inputs
3. **Access Control**: Use client governance for data access rules
4. **Audit Trail**: Enable session logging for compliance
5. **Data Retention**: Implement appropriate data cleanup policies

### Maintenance Guidelines

1. **Version Control**: Use semantic versioning for templates
2. **Testing**: Test templates thoroughly before deployment
3. **Documentation**: Document complex conditional logic
4. **Monitoring**: Track template performance and user feedback
5. **Regular Updates**: Keep templates current with business needs

---

*This guide provides comprehensive coverage of intake template development. For API integration details, see the [API Reference](../api/intake_api_reference.md). For end-user guidance, see the [User Guide](../user_guide/intake_wizard_guide.md).*