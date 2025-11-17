"""Tests for intake clarification analyzer."""

import pytest

from src.orchestrator.intake.clarifier import (
    IntakeClarifier,
    clarify_intake,
    ClarificationQuestion,
)


class TestClarificationQuestions:
    """Test clarification question generation."""

    def test_missing_success_criteria(self):
        """Test that missing success criteria generates critical question."""
        intake = {
            "project": {"name": "test", "type": "ml"},
            "goals": {"primary": ["Build ML model"]},
        }

        questions = clarify_intake(intake)

        # Should have at least one critical question about success/measurable criteria
        success_criteria_questions = [
            q for q in questions if ("success" in q.question.lower() or "measurable criteria" in q.question.lower())
               and q.field == "goals.success_criteria"
        ]
        assert len(success_criteria_questions) > 0
        assert any(q.severity == "critical" for q in success_criteria_questions)

    def test_vague_success_criteria(self):
        """Test that vague success criteria generates questions."""
        intake = {
            "project": {"name": "test", "type": "ml"},
            "goals": {
                "primary": ["Build ML model"],
                "success_criteria": ["High accuracy", "Fast performance", "Good user experience"],
            },
        }

        questions = clarify_intake(intake)

        # Should ask for measurable criteria
        measurable_questions = [
            q for q in questions if "measurable" in q.reason.lower() or "quantif" in q.reason.lower()
        ]
        assert len(measurable_questions) > 0

    def test_missing_data_sources_for_ml_project(self):
        """Test ML project without data sources generates critical question."""
        intake = {
            "project": {"name": "test", "type": "ml"},
            "goals": {"primary": ["Build ML model"], "success_criteria": ["Accuracy > 85%"]},
        }

        questions = clarify_intake(intake)

        # Should have critical question about data sources
        data_source_questions = [q for q in questions if "data source" in q.question.lower()]
        assert len(data_source_questions) > 0
        assert any(q.severity == "critical" for q in data_source_questions)

    def test_data_sources_without_volume(self):
        """Test that data sources without volume info generate questions."""
        intake = {
            "project": {"name": "test", "type": "analytics"},
            "goals": {"primary": ["Build dashboards"], "success_criteria": ["Query time < 500ms"]},
            "data": {
                "sources": [
                    {"name": "Customer DB", "type": "PostgreSQL", "sensitivity": "confidential"}
                ]
            },
        }

        questions = clarify_intake(intake)

        # Should ask about data volume
        volume_questions = [q for q in questions if "volume" in q.question.lower()]
        assert len(volume_questions) > 0

    def test_ml_project_without_model_types(self):
        """Test ML project without specified model types."""
        intake = {
            "project": {"name": "test", "type": "ml"},
            "goals": {"primary": ["Build ML model"], "success_criteria": ["Accuracy > 85%"]},
            "analytics_ml": {"required": True, "use_cases": ["Prediction"]},
            "data": {"sources": [{"name": "data", "volume": "1GB"}]},
        }

        questions = clarify_intake(intake)

        # Should ask about model types
        model_type_questions = [q for q in questions if "model" in q.question.lower()]
        assert len(model_type_questions) > 0

    def test_ml_project_without_latency_requirements(self):
        """Test ML project without latency requirements."""
        intake = {
            "project": {"name": "test", "type": "ml"},
            "goals": {"primary": ["Build ML model"], "success_criteria": ["Accuracy > 85%"]},
            "analytics_ml": {"required": True, "model_types": ["classification"]},
            "data": {"sources": [{"name": "data", "volume": "1GB"}]},
        }

        questions = clarify_intake(intake)

        # Should ask about latency
        latency_questions = [q for q in questions if "latency" in q.question.lower()]
        assert len(latency_questions) > 0

    def test_ml_project_without_accuracy_target(self):
        """Test ML project without accuracy target."""
        intake = {
            "project": {"name": "test", "type": "ml"},
            "goals": {
                "primary": ["Build ML model"],
                "success_criteria": ["Model deployed successfully"],  # No accuracy metric
            },
            "analytics_ml": {
                "required": True,
                "use_cases": ["Customer churn prediction"],
                "model_types": ["classification"],
                "latency_requirements": "<100ms",
            },
            "data": {"sources": [{"name": "data", "volume": "1GB"}]},
        }

        questions = clarify_intake(intake)

        # Should ask for accuracy/performance metric
        accuracy_questions = [q for q in questions if "accuracy" in q.question.lower() or "performance metric" in q.question.lower()]
        assert len(accuracy_questions) > 0
        assert any(q.severity == "critical" for q in accuracy_questions)

    def test_sensitive_data_without_compliance(self):
        """Test confidential data without compliance requirements."""
        intake = {
            "project": {"name": "test", "type": "analytics"},
            "goals": {"primary": ["Analytics"], "success_criteria": ["Query time < 500ms"]},
            "data": {
                "sources": [
                    {"name": "Customer PII", "type": "Database", "sensitivity": "confidential"}
                ]
            },
            "constraints": {},
        }

        questions = clarify_intake(intake)

        # Should ask about compliance (GDPR, HIPAA, etc.)
        compliance_questions = [q for q in questions if "compliance" in q.question.lower()]
        assert len(compliance_questions) > 0
        assert any(q.severity == "critical" for q in compliance_questions)

    def test_tbd_timeline(self):
        """Test TBD timeline generates question."""
        intake = {
            "project": {"name": "test", "type": "webapp"},
            "goals": {"primary": ["Build webapp"], "success_criteria": ["Load time < 2s"]},
            "constraints": {"timeline": "TBD"},
        }

        questions = clarify_intake(intake)

        # Should ask about timeline
        timeline_questions = [q for q in questions if "timeline" in q.question.lower()]
        assert len(timeline_questions) > 0

    def test_well_specified_intake(self):
        """Test well-specified intake generates few/no questions."""
        intake = {
            "project": {"name": "test-ml", "type": "ml"},
            "goals": {
                "primary": ["Build churn prediction model"],
                "success_criteria": [
                    "F1 score ≥ 0.85 on holdout test set",
                    "Inference latency < 100ms (P95)",
                    "Model drift detection within 24 hours",
                ],
            },
            "analytics_ml": {
                "required": True,
                "use_cases": ["Customer churn prediction"],
                "model_types": ["Random Forest", "XGBoost"],
                "data_volume": "10GB historical data, 1M records",
                "latency_requirements": "Real-time: <100ms",
            },
            "data": {
                "sources": [
                    {
                        "name": "Customer transactions",
                        "type": "PostgreSQL",
                        "sensitivity": "confidential",
                        "volume": "10GB, 1M records",
                    }
                ]
            },
            "constraints": {
                "timeline": "3 months to MVP",
                "compliance": ["GDPR", "SOC2"],
            },
            "stakeholders": {"product_owner": "Jane Doe", "tech_lead": "John Smith"},
            "testing": {"test_types": ["unit", "integration", "performance"]},
            "secrets_policy": {"vault_required": True},
        }

        questions = clarify_intake(intake)

        # Should have very few questions (ideally zero, but some heuristic checks might flag)
        assert len(questions) <= 2  # Allow for minor heuristic false positives

    def test_question_severity_ordering(self):
        """Test that questions are ordered by severity."""
        intake = {
            "project": {"name": "test", "type": "ml"},
            "goals": {"primary": ["Build model"]},  # Missing success criteria (critical)
            "constraints": {"timeline": "TBD"},  # Missing timeline (high)
        }

        questions = clarify_intake(intake)

        # Check that critical questions come before high severity
        if len(questions) >= 2:
            severity_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
            for i in range(len(questions) - 1):
                assert severity_order[questions[i].severity] <= severity_order[
                    questions[i + 1].severity
                ]

    def test_filter_by_severity(self):
        """Test filtering questions by severity."""
        intake = {
            "project": {"name": "test", "type": "ml"},
            "goals": {"primary": ["Build model"]},
        }

        clarifier = IntakeClarifier(intake)
        all_questions = clarifier.analyze()

        critical_questions = [q for q in all_questions if q.severity == "critical"]
        high_questions = [q for q in all_questions if q.severity == "high"]

        # Should have at least some critical questions
        assert len(critical_questions) > 0
        # Should have at least some high severity questions
        assert len(high_questions) > 0

    def test_is_measurable_heuristic(self):
        """Test the measurable criterion heuristic."""
        from src.orchestrator.intake.clarifier import IntakeClarifier

        # Measurable criteria
        assert IntakeClarifier._is_measurable("Accuracy > 85%")
        assert IntakeClarifier._is_measurable("Response time < 200ms")
        assert IntakeClarifier._is_measurable("Test coverage ≥ 80%")
        assert IntakeClarifier._is_measurable("F1 score = 0.90")

        # Vague criteria
        assert not IntakeClarifier._is_measurable("High accuracy")
        assert not IntakeClarifier._is_measurable("Fast performance")
        assert not IntakeClarifier._is_measurable("Good quality")
        assert not IntakeClarifier._is_measurable("Better user experience")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
