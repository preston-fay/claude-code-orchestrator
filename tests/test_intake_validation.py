"""
Validation Logic Tests for Intake Template System.

Tests comprehensive validation scenarios including field validation,
conditional logic, complex data structures, and edge cases.
"""

import re
from datetime import datetime, timedelta
from typing import Any

import pytest
from pydantic import ValidationError as PydanticValidationError

from orchestrator_v2.models.intake import (
    ConditionDefinition,
    ConditionOperator,
    OptionDefinition,
    PhaseDefinition,
    QuestionDefinition,
    QuestionType,
    TemplateDefinition,
    TemplateMetadata,
    ValidationError,
    ValidationRules,
    ItemSchema,
)
from orchestrator_v2.services.intake_service import (
    ConditionalLogicEngine,
    ValidationService,
)


class TestFieldValidation:
    """Test individual field validation rules."""
    
    @pytest.fixture
    def validation_service(self):
        """Create validation service instance."""
        return ValidationService()
    
    @pytest.fixture
    def sample_template(self):
        """Create template with comprehensive validation rules."""
        return TemplateDefinition(
            template=TemplateMetadata(
                id="validation_test",
                name="Validation Test Template",
                description="Template for testing validation"
            ),
            phases=[
                PhaseDefinition(
                    id="validation_phase",
                    name="Validation Phase",
                    questions=[
                        # Text validation
                        QuestionDefinition(
                            id="short_text",
                            question="Short text",
                            type=QuestionType.TEXT,
                            required=True,
                            validation=ValidationRules(
                                min_length=2,
                                max_length=10,
                                pattern=r"^[A-Za-z]+$"
                            )
                        ),
                        QuestionDefinition(
                            id="email",
                            question="Email address",
                            type=QuestionType.TEXT,
                            required=True,
                            validation=ValidationRules(
                                pattern=r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
                            )
                        ),
                        # Number validation
                        QuestionDefinition(
                            id="score",
                            question="Score (0-100)",
                            type=QuestionType.NUMBER,
                            required=True,
                            min_value=0,
                            max_value=100
                        ),
                        QuestionDefinition(
                            id="percentage",
                            question="Percentage",
                            type=QuestionType.NUMBER,
                            required=False,
                            min_value=0.0,
                            max_value=1.0,
                            step=0.01
                        ),
                        # Choice validation
                        QuestionDefinition(
                            id="priority",
                            question="Priority level",
                            type=QuestionType.CHOICE,
                            required=True,
                            options=[
                                OptionDefinition(value="low", label="Low"),
                                OptionDefinition(value="medium", label="Medium"),
                                OptionDefinition(value="high", label="High")
                            ]
                        ),
                        # Multi-choice validation
                        QuestionDefinition(
                            id="skills",
                            question="Skills",
                            type=QuestionType.MULTI_CHOICE,
                            required=False,
                            options=[
                                OptionDefinition(value="python", label="Python"),
                                OptionDefinition(value="javascript", label="JavaScript"),
                                OptionDefinition(value="sql", label="SQL"),
                                OptionDefinition(value="java", label="Java")
                            ]
                        ),
                        # Date validation
                        QuestionDefinition(
                            id="start_date",
                            question="Start date",
                            type=QuestionType.DATE,
                            required=True
                        ),
                        # List validation
                        QuestionDefinition(
                            id="tasks",
                            question="Task list",
                            type=QuestionType.LIST,
                            required=False,
                            min_items=2,
                            max_items=5,
                            item_schema=ItemSchema(
                                type=QuestionType.TEXT,
                                validation=ValidationRules(max_length=100)
                            )
                        ),
                        # Complex object validation
                        QuestionDefinition(
                            id="contact_info",
                            question="Contact information",
                            type=QuestionType.OBJECT,
                            required=True,
                            properties={
                                "name": {
                                    "type": "text",
                                    "required": True,
                                    "validation": {
                                        "min_length": 1,
                                        "max_length": 50
                                    }
                                },
                                "phone": {
                                    "type": "text",
                                    "required": False,
                                    "validation": {
                                        "pattern": r"^\+?[\d\s\-\(\)]+$"
                                    }
                                }
                            }
                        )
                    ]
                )
            ]
        )
    
    async def test_text_length_validation(self, validation_service, sample_template):
        """Test text field length validation."""
        # Test minimum length
        responses = {"short_text": "A"}  # Too short (min=2)
        result = await validation_service.validate_phase_responses(
            sample_template, "validation_phase", responses
        )
        assert not result.is_valid
        assert any(e.error_type == "min_length" for e in result.errors)
        
        # Test maximum length
        responses = {"short_text": "ThisIsTooLong"}  # Too long (max=10)
        result = await validation_service.validate_phase_responses(
            sample_template, "validation_phase", responses
        )
        assert not result.is_valid
        assert any(e.error_type == "max_length" for e in result.errors)
        
        # Test valid length
        responses = {"short_text": "Valid"}  # Just right
        result = await validation_service.validate_phase_responses(
            sample_template, "validation_phase", responses
        )
        # Should be valid for this field (other required fields may fail)
        text_errors = [e for e in result.errors if e.field_id == "short_text"]
        assert len(text_errors) == 0
    
    async def test_text_pattern_validation(self, validation_service, sample_template):
        """Test text field pattern validation."""
        # Test invalid pattern (contains numbers)
        responses = {"short_text": "Test123"}
        result = await validation_service.validate_phase_responses(
            sample_template, "validation_phase", responses
        )
        assert not result.is_valid
        assert any(e.error_type == "pattern" for e in result.errors)
        
        # Test valid pattern (letters only)
        responses = {"short_text": "Test"}
        result = await validation_service.validate_phase_responses(
            sample_template, "validation_phase", responses
        )
        # Check that pattern error is not present
        pattern_errors = [e for e in result.errors if e.field_id == "short_text" and e.error_type == "pattern"]
        assert len(pattern_errors) == 0
    
    async def test_email_validation(self, validation_service, sample_template):
        """Test email pattern validation."""
        # Test invalid emails
        invalid_emails = [
            "invalid",
            "@domain.com",
            "user@",
            "user@domain",
            "user.domain.com",
            "user@@domain.com"
        ]
        
        for invalid_email in invalid_emails:
            responses = {"email": invalid_email}
            result = await validation_service.validate_phase_responses(
                sample_template, "validation_phase", responses
            )
            email_errors = [e for e in result.errors if e.field_id == "email"]
            assert len(email_errors) > 0, f"Email '{invalid_email}' should be invalid"
        
        # Test valid emails
        valid_emails = [
            "user@domain.com",
            "test.user+tag@example.org",
            "user123@sub.domain.co.uk",
            "admin@localhost.localdomain"
        ]
        
        for valid_email in valid_emails:
            responses = {"email": valid_email}
            result = await validation_service.validate_phase_responses(
                sample_template, "validation_phase", responses
            )
            email_errors = [e for e in result.errors if e.field_id == "email" and e.error_type == "pattern"]
            assert len(email_errors) == 0, f"Email '{valid_email}' should be valid"
    
    async def test_number_range_validation(self, validation_service, sample_template):
        """Test number field range validation."""
        # Test below minimum
        responses = {"score": -10}
        result = await validation_service.validate_phase_responses(
            sample_template, "validation_phase", responses
        )
        assert not result.is_valid
        assert any(e.error_type == "min_value" and e.field_id == "score" for e in result.errors)
        
        # Test above maximum
        responses = {"score": 150}
        result = await validation_service.validate_phase_responses(
            sample_template, "validation_phase", responses
        )
        assert not result.is_valid
        assert any(e.error_type == "max_value" and e.field_id == "score" for e in result.errors)
        
        # Test invalid type
        responses = {"score": "not_a_number"}
        result = await validation_service.validate_phase_responses(
            sample_template, "validation_phase", responses
        )
        assert not result.is_valid
        assert any(e.error_type == "invalid_type" and e.field_id == "score" for e in result.errors)
        
        # Test valid value
        responses = {"score": 75}
        result = await validation_service.validate_phase_responses(
            sample_template, "validation_phase", responses
        )
        score_errors = [e for e in result.errors if e.field_id == "score"]
        assert len(score_errors) == 0
    
    async def test_choice_validation(self, validation_service, sample_template):
        """Test choice field validation."""
        # Test invalid choice
        responses = {"priority": "urgent"}  # Not in options
        result = await validation_service.validate_phase_responses(
            sample_template, "validation_phase", responses
        )
        assert not result.is_valid
        assert any(e.error_type == "invalid_choice" and e.field_id == "priority" for e in result.errors)
        
        # Test valid choices
        for valid_choice in ["low", "medium", "high"]:
            responses = {"priority": valid_choice}
            result = await validation_service.validate_phase_responses(
                sample_template, "validation_phase", responses
            )
            choice_errors = [e for e in result.errors if e.field_id == "priority"]
            assert len(choice_errors) == 0, f"Choice '{valid_choice}' should be valid"
    
    async def test_multi_choice_validation(self, validation_service, sample_template):
        """Test multi-choice field validation."""
        # Test invalid type (not a list)
        responses = {"skills": "python"}
        result = await validation_service.validate_phase_responses(
            sample_template, "validation_phase", responses
        )
        assert not result.is_valid
        assert any(e.error_type == "invalid_type" and e.field_id == "skills" for e in result.errors)
        
        # Test invalid choices
        responses = {"skills": ["python", "ruby"]}  # ruby not in options
        result = await validation_service.validate_phase_responses(
            sample_template, "validation_phase", responses
        )
        assert not result.is_valid
        assert any(e.error_type == "invalid_choice" and e.field_id == "skills" for e in result.errors)
        
        # Test valid choices
        responses = {"skills": ["python", "javascript"]}
        result = await validation_service.validate_phase_responses(
            sample_template, "validation_phase", responses
        )
        skill_errors = [e for e in result.errors if e.field_id == "skills"]
        assert len(skill_errors) == 0
        
        # Test empty list (allowed for non-required field)
        responses = {"skills": []}
        result = await validation_service.validate_phase_responses(
            sample_template, "validation_phase", responses
        )
        skill_errors = [e for e in result.errors if e.field_id == "skills"]
        assert len(skill_errors) == 0
    
    async def test_date_validation(self, validation_service, sample_template):
        """Test date field validation."""
        # Test invalid date format
        responses = {"start_date": "not-a-date"}
        result = await validation_service.validate_phase_responses(
            sample_template, "validation_phase", responses
        )
        assert not result.is_valid
        assert any(e.error_type == "invalid_date" and e.field_id == "start_date" for e in result.errors)
        
        # Test valid date formats
        valid_dates = [
            "2024-01-15",
            "2024-01-15T10:30:00",
            "2024-01-15T10:30:00Z",
            "2024-01-15T10:30:00+00:00"
        ]
        
        for valid_date in valid_dates:
            responses = {"start_date": valid_date}
            result = await validation_service.validate_phase_responses(
                sample_template, "validation_phase", responses
            )
            date_errors = [e for e in result.errors if e.field_id == "start_date"]
            assert len(date_errors) == 0, f"Date '{valid_date}' should be valid"
    
    async def test_list_validation(self, validation_service, sample_template):
        """Test list field validation."""
        # Test invalid type (not a list)
        responses = {"tasks": "task1, task2"}
        result = await validation_service.validate_phase_responses(
            sample_template, "validation_phase", responses
        )
        assert not result.is_valid
        assert any(e.error_type == "invalid_type" and e.field_id == "tasks" for e in result.errors)
        
        # Test too few items
        responses = {"tasks": ["task1"]}  # min_items=2
        result = await validation_service.validate_phase_responses(
            sample_template, "validation_phase", responses
        )
        assert not result.is_valid
        assert any(e.error_type == "min_items" and e.field_id == "tasks" for e in result.errors)
        
        # Test too many items
        responses = {"tasks": ["task1", "task2", "task3", "task4", "task5", "task6"]}  # max_items=5
        result = await validation_service.validate_phase_responses(
            sample_template, "validation_phase", responses
        )
        assert not result.is_valid
        assert any(e.error_type == "max_items" and e.field_id == "tasks" for e in result.errors)
        
        # Test valid list
        responses = {"tasks": ["task1", "task2", "task3"]}
        result = await validation_service.validate_phase_responses(
            sample_template, "validation_phase", responses
        )
        task_errors = [e for e in result.errors if e.field_id == "tasks"]
        assert len(task_errors) == 0
    
    async def test_required_field_validation(self, validation_service, sample_template):
        """Test required field validation."""
        # Test missing required fields
        responses = {"percentage": 0.5}  # Missing required fields
        result = await validation_service.validate_phase_responses(
            sample_template, "validation_phase", responses
        )
        assert not result.is_valid
        
        # Check that all required fields have errors
        required_fields = ["short_text", "email", "score", "priority", "start_date", "contact_info"]
        for field in required_fields:
            assert any(e.field_id == field and e.error_type == "required" for e in result.errors)
        
        # Test empty string as missing
        responses = {"short_text": "", "email": ""}
        result = await validation_service.validate_phase_responses(
            sample_template, "validation_phase", responses
        )
        assert not result.is_valid
        assert any(e.field_id == "short_text" and e.error_type == "required" for e in result.errors)
        assert any(e.field_id == "email" and e.error_type == "required" for e in result.errors)
    
    async def test_comprehensive_valid_responses(self, validation_service, sample_template):
        """Test validation with all valid responses."""
        responses = {
            "short_text": "Valid",
            "email": "test@example.com",
            "score": 85,
            "percentage": 0.75,
            "priority": "high",
            "skills": ["python", "sql"],
            "start_date": "2024-01-15",
            "tasks": ["task1", "task2", "task3"],
            "contact_info": {
                "name": "John Doe",
                "phone": "+1-555-123-4567"
            }
        }
        
        result = await validation_service.validate_phase_responses(
            sample_template, "validation_phase", responses
        )
        assert result.is_valid, f"Validation failed with errors: {[e.message for e in result.errors]}"
        assert len(result.errors) == 0


class TestConditionalValidation:
    """Test validation with conditional logic."""
    
    @pytest.fixture
    def conditional_template(self):
        """Create template with conditional validation rules."""
        return TemplateDefinition(
            template=TemplateMetadata(
                id="conditional_test",
                name="Conditional Test Template",
                description="Template for testing conditional validation"
            ),
            phases=[
                PhaseDefinition(
                    id="conditional_phase",
                    name="Conditional Phase",
                    questions=[
                        QuestionDefinition(
                            id="has_experience",
                            question="Do you have experience?",
                            type=QuestionType.CHOICE,
                            required=True,
                            options=[
                                OptionDefinition(value="yes", label="Yes"),
                                OptionDefinition(value="no", label="No")
                            ]
                        ),
                        QuestionDefinition(
                            id="years_experience",
                            question="Years of experience",
                            type=QuestionType.NUMBER,
                            required=True,
                            min_value=1,
                            max_value=50,
                            condition=ConditionDefinition(
                                field="has_experience",
                                operator=ConditionOperator.EQUALS,
                                value="yes"
                            )
                        ),
                        QuestionDefinition(
                            id="training_needed",
                            question="What training do you need?",
                            type=QuestionType.TEXTAREA,
                            required=True,
                            condition=ConditionDefinition(
                                field="has_experience",
                                operator=ConditionOperator.EQUALS,
                                value="no"
                            )
                        ),
                        QuestionDefinition(
                            id="advanced_skills",
                            question="Advanced skills",
                            type=QuestionType.MULTI_CHOICE,
                            required=False,
                            options=[
                                OptionDefinition(value="leadership", label="Leadership"),
                                OptionDefinition(value="architecture", label="Architecture")
                            ],
                            condition=ConditionDefinition(
                                field="years_experience",
                                operator=ConditionOperator.GREATER_THAN,
                                value=5
                            )
                        ),
                        # Complex condition with AND logic
                        QuestionDefinition(
                            id="senior_responsibilities",
                            question="Senior responsibilities",
                            type=QuestionType.LIST,
                            required=True,
                            min_items=1,
                            item_schema=ItemSchema(type=QuestionType.TEXT),
                            condition=ConditionDefinition(
                                field="has_experience",
                                operator=ConditionOperator.EQUALS,
                                value="yes",
                                and_conditions=[
                                    ConditionDefinition(
                                        field="years_experience",
                                        operator=ConditionOperator.GREATER_EQUAL,
                                        value=10
                                    )
                                ]
                            )
                        )
                    ]
                )
            ]
        )
    
    @pytest.fixture
    def validation_service(self):
        """Create validation service instance."""
        return ValidationService()
    
    async def test_conditional_required_fields_shown(self, validation_service, conditional_template):
        """Test that conditionally required fields are validated when condition is met."""
        # Response that triggers years_experience to be required
        responses = {
            "has_experience": "yes"
            # Missing years_experience which should be required
        }
        
        result = await validation_service.validate_phase_responses(
            conditional_template, "conditional_phase", responses
        )
        
        assert not result.is_valid
        assert any(e.field_id == "years_experience" and e.error_type == "required" for e in result.errors)
        # training_needed should not be required since condition not met
        assert not any(e.field_id == "training_needed" for e in result.errors)
    
    async def test_conditional_required_fields_hidden(self, validation_service, conditional_template):
        """Test that conditionally required fields are not validated when condition is not met."""
        # Response that hides years_experience and shows training_needed
        responses = {
            "has_experience": "no"
            # Missing training_needed which should be required
        }
        
        result = await validation_service.validate_phase_responses(
            conditional_template, "conditional_phase", responses
        )
        
        assert not result.is_valid
        assert any(e.field_id == "training_needed" and e.error_type == "required" for e in result.errors)
        # years_experience should not be required since condition not met
        assert not any(e.field_id == "years_experience" for e in result.errors)
    
    async def test_nested_conditional_validation(self, validation_service, conditional_template):
        """Test validation with nested conditional logic."""
        # Response that triggers advanced_skills (years > 5)
        responses = {
            "has_experience": "yes",
            "years_experience": 8  # > 5, so advanced_skills becomes available
        }
        
        result = await validation_service.validate_phase_responses(
            conditional_template, "conditional_phase", responses
        )
        
        assert result.is_valid  # All required fields present
        
        # senior_responsibilities should not be required (years < 10)
        assert not any(e.field_id == "senior_responsibilities" for e in result.errors)
    
    async def test_complex_and_condition(self, validation_service, conditional_template):
        """Test validation with complex AND conditions."""
        # Response that triggers senior_responsibilities (has_experience=yes AND years>=10)
        responses = {
            "has_experience": "yes",
            "years_experience": 15  # >= 10, so senior_responsibilities becomes required
            # Missing senior_responsibilities
        }
        
        result = await validation_service.validate_phase_responses(
            conditional_template, "conditional_phase", responses
        )
        
        assert not result.is_valid
        assert any(e.field_id == "senior_responsibilities" and e.error_type == "required" for e in result.errors)
    
    async def test_conditional_validation_with_valid_responses(self, validation_service, conditional_template):
        """Test complete valid responses with conditional fields."""
        # Scenario 1: Experienced user
        responses = {
            "has_experience": "yes",
            "years_experience": 8,
            "advanced_skills": ["leadership"]  # Optional but valid
        }
        
        result = await validation_service.validate_phase_responses(
            conditional_template, "conditional_phase", responses
        )
        assert result.is_valid
        
        # Scenario 2: Senior user
        responses = {
            "has_experience": "yes",
            "years_experience": 15,
            "advanced_skills": ["leadership", "architecture"],
            "senior_responsibilities": ["Team leadership", "System design"]
        }
        
        result = await validation_service.validate_phase_responses(
            conditional_template, "conditional_phase", responses
        )
        assert result.is_valid
        
        # Scenario 3: Inexperienced user
        responses = {
            "has_experience": "no",
            "training_needed": "Need comprehensive training on software development fundamentals"
        }
        
        result = await validation_service.validate_phase_responses(
            conditional_template, "conditional_phase", responses
        )
        assert result.is_valid


class TestEdgeCases:
    """Test edge cases and boundary conditions."""
    
    @pytest.fixture
    def edge_case_template(self):
        """Create template with edge case scenarios."""
        return TemplateDefinition(
            template=TemplateMetadata(
                id="edge_case_test",
                name="Edge Case Test Template",
                description="Template for testing edge cases"
            ),
            phases=[
                PhaseDefinition(
                    id="edge_phase",
                    name="Edge Case Phase",
                    questions=[
                        # Zero values
                        QuestionDefinition(
                            id="zero_value",
                            question="Zero value test",
                            type=QuestionType.NUMBER,
                            required=False,
                            min_value=0,
                            max_value=0  # Only allows zero
                        ),
                        # Empty patterns
                        QuestionDefinition(
                            id="any_text",
                            question="Any text",
                            type=QuestionType.TEXT,
                            required=False,
                            validation=ValidationRules(pattern=".*")  # Matches anything
                        ),
                        # Very long text
                        QuestionDefinition(
                            id="long_text",
                            question="Long text",
                            type=QuestionType.TEXTAREA,
                            required=False,
                            validation=ValidationRules(max_length=10000)
                        ),
                        # Decimal precision
                        QuestionDefinition(
                            id="precise_decimal",
                            question="Precise decimal",
                            type=QuestionType.NUMBER,
                            required=False,
                            min_value=0.001,
                            max_value=0.999,
                            step=0.001
                        ),
                        # Unicode text
                        QuestionDefinition(
                            id="unicode_text",
                            question="Unicode text",
                            type=QuestionType.TEXT,
                            required=False,
                            validation=ValidationRules(max_length=100)
                        ),
                        # Large list
                        QuestionDefinition(
                            id="large_list",
                            question="Large list",
                            type=QuestionType.LIST,
                            required=False,
                            max_items=100,
                            item_schema=ItemSchema(type=QuestionType.TEXT)
                        ),
                        # Derived field (should be skipped in validation)
                        QuestionDefinition(
                            id="derived_slug",
                            question=None,
                            type=QuestionType.DERIVED,
                            derived_from="any_text",
                            transform="slugify"
                        )
                    ]
                )
            ]
        )
    
    @pytest.fixture
    def validation_service(self):
        """Create validation service instance.""" 
        return ValidationService()
    
    async def test_zero_boundary_values(self, validation_service, edge_case_template):
        """Test validation with zero boundary values."""
        # Test exact zero (should be valid)
        responses = {"zero_value": 0}
        result = await validation_service.validate_phase_responses(
            edge_case_template, "edge_phase", responses
        )
        zero_errors = [e for e in result.errors if e.field_id == "zero_value"]
        assert len(zero_errors) == 0
        
        # Test negative value (should be invalid)
        responses = {"zero_value": -1}
        result = await validation_service.validate_phase_responses(
            edge_case_template, "edge_phase", responses
        )
        assert any(e.field_id == "zero_value" and e.error_type == "min_value" for e in result.errors)
        
        # Test positive value (should be invalid)
        responses = {"zero_value": 1}
        result = await validation_service.validate_phase_responses(
            edge_case_template, "edge_phase", responses
        )
        assert any(e.field_id == "zero_value" and e.error_type == "max_value" for e in result.errors)
    
    async def test_empty_and_whitespace_strings(self, validation_service, edge_case_template):
        """Test validation with empty and whitespace strings."""
        # Test empty string
        responses = {"any_text": ""}
        result = await validation_service.validate_phase_responses(
            edge_case_template, "edge_phase", responses
        )
        text_errors = [e for e in result.errors if e.field_id == "any_text"]
        assert len(text_errors) == 0  # Empty string should be valid for non-required field
        
        # Test whitespace only
        responses = {"any_text": "   "}
        result = await validation_service.validate_phase_responses(
            edge_case_template, "edge_phase", responses
        )
        text_errors = [e for e in result.errors if e.field_id == "any_text"]
        assert len(text_errors) == 0  # Whitespace should be valid
        
        # Test single character
        responses = {"any_text": "a"}
        result = await validation_service.validate_phase_responses(
            edge_case_template, "edge_phase", responses
        )
        text_errors = [e for e in result.errors if e.field_id == "any_text"]
        assert len(text_errors) == 0
    
    async def test_very_long_text(self, validation_service, edge_case_template):
        """Test validation with very long text."""
        # Test text at exact maximum length
        long_text = "a" * 10000
        responses = {"long_text": long_text}
        result = await validation_service.validate_phase_responses(
            edge_case_template, "edge_phase", responses
        )
        text_errors = [e for e in result.errors if e.field_id == "long_text"]
        assert len(text_errors) == 0
        
        # Test text exceeding maximum length
        too_long_text = "a" * 10001
        responses = {"long_text": too_long_text}
        result = await validation_service.validate_phase_responses(
            edge_case_template, "edge_phase", responses
        )
        assert any(e.field_id == "long_text" and e.error_type == "max_length" for e in result.errors)
    
    async def test_decimal_precision(self, validation_service, edge_case_template):
        """Test validation with high precision decimals."""
        # Test minimum boundary
        responses = {"precise_decimal": 0.001}
        result = await validation_service.validate_phase_responses(
            edge_case_template, "edge_phase", responses
        )
        decimal_errors = [e for e in result.errors if e.field_id == "precise_decimal"]
        assert len(decimal_errors) == 0
        
        # Test maximum boundary
        responses = {"precise_decimal": 0.999}
        result = await validation_service.validate_phase_responses(
            edge_case_template, "edge_phase", responses
        )
        decimal_errors = [e for e in result.errors if e.field_id == "precise_decimal"]
        assert len(decimal_errors) == 0
        
        # Test high precision value
        responses = {"precise_decimal": 0.123456}
        result = await validation_service.validate_phase_responses(
            edge_case_template, "edge_phase", responses
        )
        decimal_errors = [e for e in result.errors if e.field_id == "precise_decimal"]
        assert len(decimal_errors) == 0
        
        # Test value below minimum
        responses = {"precise_decimal": 0.0009}
        result = await validation_service.validate_phase_responses(
            edge_case_template, "edge_phase", responses
        )
        assert any(e.field_id == "precise_decimal" and e.error_type == "min_value" for e in result.errors)
    
    async def test_unicode_text_validation(self, validation_service, edge_case_template):
        """Test validation with Unicode text."""
        unicode_texts = [
            "Hello 🌍",  # Emoji
            "Здравствуй мир",  # Cyrillic
            "こんにちは世界",  # Japanese
            "مرحبا بالعالم",  # Arabic
            "Héllö Wörld",  # Accented characters
            "测试文本",  # Chinese
            "🚀🎉💻📊",  # Multiple emojis
        ]
        
        for unicode_text in unicode_texts:
            responses = {"unicode_text": unicode_text}
            result = await validation_service.validate_phase_responses(
                edge_case_template, "edge_phase", responses
            )
            unicode_errors = [e for e in result.errors if e.field_id == "unicode_text"]
            assert len(unicode_errors) == 0, f"Unicode text '{unicode_text}' should be valid"
    
    async def test_large_list_validation(self, validation_service, edge_case_template):
        """Test validation with large lists."""
        # Test empty list
        responses = {"large_list": []}
        result = await validation_service.validate_phase_responses(
            edge_case_template, "edge_phase", responses
        )
        list_errors = [e for e in result.errors if e.field_id == "large_list"]
        assert len(list_errors) == 0  # Empty list should be valid for non-required field
        
        # Test maximum size list
        large_list = [f"item_{i}" for i in range(100)]
        responses = {"large_list": large_list}
        result = await validation_service.validate_phase_responses(
            edge_case_template, "edge_phase", responses
        )
        list_errors = [e for e in result.errors if e.field_id == "large_list"]
        assert len(list_errors) == 0
        
        # Test oversized list
        oversized_list = [f"item_{i}" for i in range(101)]
        responses = {"large_list": oversized_list}
        result = await validation_service.validate_phase_responses(
            edge_case_template, "edge_phase", responses
        )
        assert any(e.field_id == "large_list" and e.error_type == "max_items" for e in result.errors)
    
    async def test_derived_fields_skipped(self, validation_service, edge_case_template):
        """Test that derived fields are skipped in validation."""
        responses = {}  # No responses at all
        result = await validation_service.validate_phase_responses(
            edge_case_template, "edge_phase", responses
        )
        
        # Should not have any errors for derived field
        derived_errors = [e for e in result.errors if e.field_id == "derived_slug"]
        assert len(derived_errors) == 0
    
    async def test_null_and_none_values(self, validation_service, edge_case_template):
        """Test validation with null and None values."""
        # Test None values
        responses = {
            "zero_value": None,
            "any_text": None,
            "unicode_text": None
        }
        result = await validation_service.validate_phase_responses(
            edge_case_template, "edge_phase", responses
        )
        
        # None values should be treated as missing (valid for non-required fields)
        none_errors = [e for e in result.errors if "null" in e.message.lower() or "none" in e.message.lower()]
        assert len(none_errors) == 0
    
    async def test_type_coercion_edge_cases(self, validation_service, edge_case_template):
        """Test edge cases in type coercion."""
        # Test string numbers
        responses = {"precise_decimal": "0.500"}  # String that can be converted to float
        result = await validation_service.validate_phase_responses(
            edge_case_template, "edge_phase", responses
        )
        decimal_errors = [e for e in result.errors if e.field_id == "precise_decimal"]
        assert len(decimal_errors) == 0
        
        # Test boolean as number (should fail)
        responses = {"precise_decimal": True}
        result = await validation_service.validate_phase_responses(
            edge_case_template, "edge_phase", responses
        )
        # Note: Python bool is a subclass of int, so True == 1, which would be out of range
        assert any(e.field_id == "precise_decimal" for e in result.errors)


class TestComplexValidationScenarios:
    """Test complex real-world validation scenarios."""
    
    @pytest.fixture 
    def complex_template(self):
        """Create a complex template mimicking real-world usage."""
        return TemplateDefinition(
            template=TemplateMetadata(
                id="project_intake",
                name="Project Intake Template",
                description="Complex project intake form"
            ),
            phases=[
                PhaseDefinition(
                    id="project_info",
                    name="Project Information",
                    questions=[
                        QuestionDefinition(
                            id="project_type",
                            question="Project type",
                            type=QuestionType.CHOICE,
                            required=True,
                            options=[
                                OptionDefinition(value="new_development", label="New Development"),
                                OptionDefinition(value="enhancement", label="Enhancement"),
                                OptionDefinition(value="maintenance", label="Maintenance")
                            ]
                        ),
                        QuestionDefinition(
                            id="budget_range",
                            question="Budget range",
                            type=QuestionType.CHOICE,
                            required=True,
                            options=[
                                OptionDefinition(value="small", label="< $50k"),
                                OptionDefinition(value="medium", label="$50k - $200k"), 
                                OptionDefinition(value="large", label="> $200k")
                            ]
                        ),
                        # Conditional fields based on project type
                        QuestionDefinition(
                            id="existing_system",
                            question="Existing system details",
                            type=QuestionType.TEXTAREA,
                            required=True,
                            validation=ValidationRules(min_length=50, max_length=1000),
                            condition=ConditionDefinition(
                                field="project_type",
                                operator=ConditionOperator.IN,
                                value=["enhancement", "maintenance"]
                            )
                        ),
                        QuestionDefinition(
                            id="technology_stack",
                            question="Technology stack",
                            type=QuestionType.MULTI_CHOICE,
                            required=True,
                            options=[
                                OptionDefinition(value="python", label="Python"),
                                OptionDefinition(value="javascript", label="JavaScript"),
                                OptionDefinition(value="java", label="Java"),
                                OptionDefinition(value="dotnet", label=".NET"),
                                OptionDefinition(value="other", label="Other")
                            ],
                            condition=ConditionDefinition(
                                field="project_type",
                                operator=ConditionOperator.EQUALS,
                                value="new_development"
                            )
                        ),
                        # Complex budget validation based on project size
                        QuestionDefinition(
                            id="detailed_budget",
                            question="Detailed budget breakdown",
                            type=QuestionType.LIST,
                            required=True,
                            min_items=3,
                            max_items=10,
                            item_schema=ItemSchema(
                                type=QuestionType.OBJECT,
                                properties={
                                    "category": {
                                        "type": "choice",
                                        "required": True,
                                        "options": [
                                            {"value": "development", "label": "Development"},
                                            {"value": "testing", "label": "Testing"},
                                            {"value": "deployment", "label": "Deployment"},
                                            {"value": "maintenance", "label": "Maintenance"}
                                        ]
                                    },
                                    "amount": {
                                        "type": "number",
                                        "required": True,
                                        "min_value": 1000,
                                        "max_value": 1000000
                                    },
                                    "description": {
                                        "type": "text",
                                        "required": False,
                                        "max_length": 200
                                    }
                                }
                            ),
                            condition=ConditionDefinition(
                                field="budget_range",
                                operator=ConditionOperator.IN,
                                value=["medium", "large"]
                            )
                        ),
                        # Team composition with complex validation
                        QuestionDefinition(
                            id="team_members",
                            question="Team members",
                            type=QuestionType.LIST,
                            required=True,
                            min_items=1,
                            max_items=20,
                            item_schema=ItemSchema(
                                type=QuestionType.OBJECT,
                                properties={
                                    "name": {
                                        "type": "text",
                                        "required": True,
                                        "validation": {"min_length": 2, "max_length": 50}
                                    },
                                    "role": {
                                        "type": "choice",
                                        "required": True,
                                        "options": [
                                            {"value": "developer", "label": "Developer"},
                                            {"value": "designer", "label": "Designer"},
                                            {"value": "pm", "label": "Project Manager"},
                                            {"value": "qa", "label": "QA Engineer"}
                                        ]
                                    },
                                    "email": {
                                        "type": "text",
                                        "required": True,
                                        "validation": {
                                            "pattern": r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
                                        }
                                    },
                                    "availability": {
                                        "type": "number",
                                        "required": True,
                                        "min_value": 0.1,
                                        "max_value": 1.0,
                                        "unit": "percentage"
                                    }
                                }
                            )
                        )
                    ]
                )
            ]
        )
    
    @pytest.fixture
    def validation_service(self):
        """Create validation service instance."""
        return ValidationService()
    
    async def test_new_development_project_validation(self, validation_service, complex_template):
        """Test validation for new development project scenario."""
        responses = {
            "project_type": "new_development",
            "budget_range": "large",
            "technology_stack": ["python", "javascript"],
            "detailed_budget": [
                {
                    "category": "development",
                    "amount": 150000,
                    "description": "Core development work"
                },
                {
                    "category": "testing",
                    "amount": 30000,
                    "description": "QA and testing"
                },
                {
                    "category": "deployment",
                    "amount": 20000,
                    "description": "Infrastructure setup"
                }
            ],
            "team_members": [
                {
                    "name": "John Doe",
                    "role": "developer",
                    "email": "john.doe@company.com",
                    "availability": 1.0
                },
                {
                    "name": "Jane Smith",
                    "role": "designer",
                    "email": "jane.smith@company.com", 
                    "availability": 0.5
                }
            ]
        }
        
        result = await validation_service.validate_phase_responses(
            complex_template, "project_info", responses
        )
        
        assert result.is_valid, f"Validation failed with errors: {[e.message for e in result.errors]}"
        
        # existing_system should not be required for new development
        assert not any(e.field_id == "existing_system" for e in result.errors)
    
    async def test_enhancement_project_validation(self, validation_service, complex_template):
        """Test validation for enhancement project scenario."""
        responses = {
            "project_type": "enhancement",
            "budget_range": "small",
            "existing_system": "Legacy system built in PHP with MySQL database. Requires modernization of user interface and performance improvements. Current system handles 1000 users daily with response times around 3-5 seconds.",
            "team_members": [
                {
                    "name": "Bob Wilson",
                    "role": "developer",
                    "email": "bob.wilson@company.com",
                    "availability": 0.75
                }
            ]
        }
        
        result = await validation_service.validate_phase_responses(
            complex_template, "project_info", responses
        )
        
        assert result.is_valid, f"Validation failed with errors: {[e.message for e in result.errors]}"
        
        # technology_stack should not be required for enhancement
        assert not any(e.field_id == "technology_stack" for e in result.errors)
        # detailed_budget should not be required for small budget
        assert not any(e.field_id == "detailed_budget" for e in result.errors)
    
    async def test_complex_validation_errors(self, validation_service, complex_template):
        """Test complex validation scenarios with multiple errors."""
        responses = {
            "project_type": "new_development",
            "budget_range": "large",
            "technology_stack": ["invalid_tech"],  # Invalid choice
            "detailed_budget": [
                {
                    "category": "development",
                    "amount": 500,  # Below minimum
                    "description": "Too low budget"
                },
                {
                    "category": "invalid_category",  # Invalid choice
                    "amount": 50000,
                    "description": "Valid description"
                }
                # Only 2 items, but min_items=3
            ],
            "team_members": [
                {
                    "name": "A",  # Too short
                    "role": "invalid_role",  # Invalid choice
                    "email": "invalid-email",  # Invalid format
                    "availability": 1.5  # Above maximum
                }
            ]
        }
        
        result = await validation_service.validate_phase_responses(
            complex_template, "project_info", responses
        )
        
        assert not result.is_valid
        
        # Should have multiple validation errors
        assert len(result.errors) >= 5  # At least one error per invalid field
        
        # Check specific error types
        error_types = [e.error_type for e in result.errors]
        assert "invalid_choice" in error_types
        assert "min_value" in error_types  
        assert "max_value" in error_types
        assert "min_length" in error_types
        assert "min_items" in error_types
        assert "pattern" in error_types
    
    async def test_nested_object_validation(self, validation_service, complex_template):
        """Test validation of nested objects within lists."""
        responses = {
            "project_type": "new_development",
            "budget_range": "medium",
            "technology_stack": ["python"],
            "detailed_budget": [
                {
                    "category": "development",
                    "amount": 75000
                    # Missing description is OK (not required)
                },
                {
                    "category": "testing", 
                    "amount": 15000,
                    "description": "A" * 250  # Exceeds max_length=200
                },
                {
                    "category": "deployment",
                    "amount": 10000,
                    "description": "Valid description"
                }
            ],
            "team_members": [
                {
                    "name": "Valid Name",
                    "role": "developer",
                    "email": "valid@email.com",
                    "availability": 0.8
                }
            ]
        }
        
        result = await validation_service.validate_phase_responses(
            complex_template, "project_info", responses
        )
        
        assert not result.is_valid
        
        # Should have error for the too-long description in budget item
        description_errors = [e for e in result.errors if "description" in e.field_id or "max_length" in e.error_type]
        assert len(description_errors) > 0
    
    async def test_conditional_field_interdependencies(self, validation_service, complex_template):
        """Test complex scenarios with interdependent conditional fields."""
        # Test that changing one field affects validation of others
        base_responses = {
            "project_type": "enhancement",  # Requires existing_system
            "budget_range": "large",  # Requires detailed_budget
            "team_members": [
                {
                    "name": "Team Lead",
                    "role": "pm",
                    "email": "lead@company.com",
                    "availability": 1.0
                }
            ]
        }
        
        # Missing both conditional required fields
        result = await validation_service.validate_phase_responses(
            complex_template, "project_info", base_responses
        )
        
        assert not result.is_valid
        assert any(e.field_id == "existing_system" and e.error_type == "required" for e in result.errors)
        assert any(e.field_id == "detailed_budget" and e.error_type == "required" for e in result.errors)
        
        # Add existing_system but keep missing detailed_budget
        responses_with_system = base_responses.copy()
        responses_with_system["existing_system"] = "Detailed description of the existing system that needs enhancement. The system is currently built using older technologies and requires modernization."
        
        result = await validation_service.validate_phase_responses(
            complex_template, "project_info", responses_with_system
        )
        
        assert not result.is_valid
        # existing_system error should be gone
        assert not any(e.field_id == "existing_system" and e.error_type == "required" for e in result.errors)
        # but detailed_budget error should remain
        assert any(e.field_id == "detailed_budget" and e.error_type == "required" for e in result.errors)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])