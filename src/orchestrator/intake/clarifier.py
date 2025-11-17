"""Intake clarification analyzer for Claude Code Orchestrator.

Detects underspecified intake configurations and generates clarifying questions
to improve specification quality before workflow execution.
"""

from dataclasses import dataclass
from typing import Any, Dict, List, Optional


@dataclass
class ClarificationQuestion:
    """Represents a clarifying question about the intake."""

    field: str  # JSON path to field (e.g., "goals.success_criteria")
    question: str  # The question to ask
    reason: str  # Why this clarification is needed
    examples: List[str]  # Example answers
    severity: str  # "critical", "high", "medium", "low"
    category: str  # "requirements", "technical", "data", "testing", etc.

    def __str__(self) -> str:
        examples_str = "\n  ".join(f"• {ex}" for ex in self.examples)
        return (
            f"[{self.severity.upper()}] {self.category}\n"
            f"❓ {self.question}\n"
            f"  Field: {self.field}\n"
            f"  Reason: {self.reason}\n"
            f"  Examples:\n  {examples_str}"
        )


class IntakeClarifier:
    """Analyzes intake configurations and generates clarifying questions."""

    def __init__(self, intake: Dict[str, Any]):
        self.intake = intake
        self.questions: List[ClarificationQuestion] = []

    def analyze(self) -> List[ClarificationQuestion]:
        """Analyze intake and generate all clarifying questions."""
        self.questions = []

        # Run all checks
        self._check_success_criteria()
        self._check_data_sources()
        self._check_analytics_ml()
        self._check_tech_preferences()
        self._check_constraints()
        self._check_testing()
        self._check_stakeholders()
        self._check_security()

        # Sort by severity
        severity_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
        self.questions.sort(key=lambda q: severity_order.get(q.severity, 4))

        return self.questions

    def _check_success_criteria(self):
        """Check if success criteria are well-defined."""
        goals = self.intake.get("goals", {})

        # Check if success criteria exist
        if not goals.get("success_criteria"):
            self.questions.append(
                ClarificationQuestion(
                    field="goals.success_criteria",
                    question="What measurable criteria will define project success?",
                    reason="Success criteria are missing. Without clear metrics, it's impossible to validate if the project achieves its goals.",
                    examples=[
                        "Model achieves R² ≥ 0.85 on holdout test set",
                        "Dashboard query performance <500ms (P95)",
                        "API handles 1000 requests/second with <200ms latency",
                        "User satisfaction score ≥4.5/5.0 in UAT",
                    ],
                    severity="critical",
                    category="requirements",
                )
            )
        else:
            # Check if success criteria are measurable
            criteria = goals["success_criteria"]
            vague_criteria = [c for c in criteria if not self._is_measurable(c)]

            if vague_criteria:
                self.questions.append(
                    ClarificationQuestion(
                        field="goals.success_criteria",
                        question=f"How will you measure these success criteria: {', '.join(vague_criteria)}?",
                        reason="Success criteria should be quantifiable and measurable.",
                        examples=[
                            "Instead of 'fast performance', specify 'page load <2 seconds (P95)'",
                            "Instead of 'high accuracy', specify 'F1 score ≥0.90'",
                            "Instead of 'good user experience', specify 'task completion rate ≥90%'",
                        ],
                        severity="high",
                        category="requirements",
                    )
                )

    def _check_data_sources(self):
        """Check if data sources are well-specified."""
        data = self.intake.get("data", {})
        sources = data.get("sources", [])

        if not sources and self.intake.get("project", {}).get("type") in ["analytics", "ml"]:
            self.questions.append(
                ClarificationQuestion(
                    field="data.sources",
                    question="What are the data sources for this project?",
                    reason="Analytics/ML projects require data sources to be specified.",
                    examples=[
                        "Production PostgreSQL database (customer_transactions table)",
                        "S3 bucket with CSV files (s3://company-data/sales/)",
                        "Snowflake data warehouse (ANALYTICS.CUSTOMER_EVENTS)",
                        "REST API endpoint (https://api.example.com/events)",
                    ],
                    severity="critical",
                    category="data",
                )
            )
        else:
            # Check if sources have volume information
            for source in sources:
                if "volume" not in source and "data_volume" not in str(source):
                    self.questions.append(
                        ClarificationQuestion(
                            field=f"data.sources.{source.get('name', 'unknown')}.volume",
                            question=f"What is the volume/size of data source '{source.get('name')}'?",
                            reason="Data volume affects architecture decisions (batch vs. streaming, database choice, etc.).",
                            examples=[
                                "10K rows, 50MB",
                                "500GB total, growing 10GB/month",
                                "1M events/day, ~100GB/month",
                                "50M records, 2TB historical data",
                            ],
                            severity="high",
                            category="data",
                        )
                    )

    def _check_analytics_ml(self):
        """Check analytics/ML configuration."""
        analytics = self.intake.get("analytics_ml", {})

        if analytics.get("required"):
            # Check for model types
            if not analytics.get("model_types"):
                self.questions.append(
                    ClarificationQuestion(
                        field="analytics_ml.model_types",
                        question="What types of ML models or analytics are needed?",
                        reason="Model type affects data requirements, infrastructure, and implementation approach.",
                        examples=[
                            "Binary classification (logistic regression, random forest)",
                            "Time series forecasting (ARIMA, Prophet, LSTM)",
                            "Clustering for customer segmentation (K-means, DBSCAN)",
                            "Regression for demand prediction (XGBoost, neural network)",
                        ],
                        severity="high",
                        category="data",
                    )
                )

            # Check for latency requirements
            if not analytics.get("latency_requirements"):
                self.questions.append(
                    ClarificationQuestion(
                        field="analytics_ml.latency_requirements",
                        question="What are the latency requirements for model predictions or analytics queries?",
                        reason="Latency requirements determine whether you need real-time, near-real-time, or batch processing.",
                        examples=[
                            "Real-time: <100ms (e.g., fraud detection)",
                            "Near-real-time: <5 seconds (e.g., recommendation engine)",
                            "Batch: Hourly or daily (e.g., nightly reports)",
                            "Mixed: Real-time for API, batch for analytics",
                        ],
                        severity="high",
                        category="data",
                    )
                )

            # Check for accuracy targets
            use_cases = analytics.get("use_cases", [])
            if any("classif" in uc.lower() or "predict" in uc.lower() for uc in use_cases):
                success_criteria = self.intake.get("goals", {}).get("success_criteria", [])
                has_accuracy_target = any(
                    metric in str(success_criteria).lower()
                    for metric in ["accuracy", "precision", "recall", "f1", "auc", "rmse", "mae", "r²"]
                )

                if not has_accuracy_target:
                    self.questions.append(
                        ClarificationQuestion(
                            field="goals.success_criteria",
                            question="What is the target accuracy/performance metric for the ML model?",
                            reason="Without a target metric, you can't validate if the model is good enough to deploy.",
                            examples=[
                                "Classification: F1 score ≥0.85, AUC-ROC ≥0.90",
                                "Regression: RMSE ≤5.0, R² ≥0.80",
                                "Forecasting: MAPE <10%, MAE <2.5",
                                "Clustering: Silhouette score ≥0.6",
                            ],
                            severity="critical",
                            category="requirements",
                        )
                    )

    def _check_tech_preferences(self):
        """Check if tech preferences are reasonable."""
        tech = self.intake.get("tech_preferences", {})

        # Check if avoiding too many things
        avoid = tech.get("avoid", [])
        if len(avoid) > 5:
            self.questions.append(
                ClarificationQuestion(
                    field="tech_preferences.avoid",
                    question=f"You're avoiding {len(avoid)} technologies. Are all of these restrictions necessary?",
                    reason="Over-constraining technology choices limits architectural options.",
                    examples=[
                        "Avoid only if there's a strong reason (licensing, security, skill gaps)",
                        "Consider separating 'must avoid' from 'prefer not to use'",
                    ],
                    severity="medium",
                    category="technical",
                )
            )

        # Check for conflicting preferences
        frameworks = tech.get("frameworks", [])
        if "React" in frameworks and "Vue" in frameworks:
            self.questions.append(
                ClarificationQuestion(
                    field="tech_preferences.frameworks",
                    question="You listed both React and Vue. Which one should be used?",
                    reason="Listing multiple competing frameworks creates ambiguity.",
                    examples=[
                        "Choose React (more common in enterprise)",
                        "Choose Vue (team expertise)",
                        "Leave it to Architect to decide based on requirements",
                    ],
                    severity="medium",
                    category="technical",
                )
            )

    def _check_constraints(self):
        """Check if constraints are specified."""
        constraints = self.intake.get("constraints", {})

        # Check timeline
        if constraints.get("timeline", "TBD") == "TBD":
            self.questions.append(
                ClarificationQuestion(
                    field="constraints.timeline",
                    question="What is the project timeline or deadline?",
                    reason="Timeline affects scope, architecture complexity, and agent planning.",
                    examples=[
                        "MVP in 4 weeks, full release in 12 weeks",
                        "3-month timeline for initial deployment",
                        "No hard deadline, prioritize quality over speed",
                    ],
                    severity="high",
                    category="requirements",
                )
            )

        # Check compliance requirements
        data_sources = self.intake.get("data", {}).get("sources", [])
        has_sensitive_data = any(
            src.get("sensitivity") in ["confidential", "restricted"]
            for src in data_sources
        )

        if has_sensitive_data and not constraints.get("compliance"):
            self.questions.append(
                ClarificationQuestion(
                    field="constraints.compliance",
                    question="You have confidential/restricted data. What compliance requirements apply?",
                    reason="Sensitive data often requires compliance with GDPR, HIPAA, SOC2, etc.",
                    examples=[
                        "GDPR (EU data protection)",
                        "HIPAA (health data in US)",
                        "SOC2 (security controls)",
                        "CCPA (California privacy)",
                    ],
                    severity="critical",
                    category="security",
                )
            )

    def _check_testing(self):
        """Check testing configuration."""
        testing = self.intake.get("testing", {})

        # Check if test types are specified
        if not testing.get("test_types"):
            project_type = self.intake.get("project", {}).get("type")

            if project_type == "ml":
                self.questions.append(
                    ClarificationQuestion(
                        field="testing.test_types",
                        question="What types of tests are needed for this ML project?",
                        reason="ML projects require specialized testing (data validation, model performance, drift detection).",
                        examples=[
                            "Unit tests for data transformations",
                            "Integration tests for ETL pipeline",
                            "Model performance tests (accuracy, fairness)",
                            "Data drift tests",
                        ],
                        severity="medium",
                        category="testing",
                    )
                )

    def _check_stakeholders(self):
        """Check if stakeholders are identified."""
        stakeholders = self.intake.get("stakeholders", {})

        if not stakeholders.get("product_owner") or stakeholders.get("product_owner") == "To be determined":
            self.questions.append(
                ClarificationQuestion(
                    field="stakeholders.product_owner",
                    question="Who is the product owner or primary decision-maker for this project?",
                    reason="A product owner is needed for approval gates and requirement clarifications.",
                    examples=[
                        "Jane Doe (VP of Analytics)",
                        "John Smith (Project Manager)",
                        "Client stakeholder: Sarah Johnson",
                    ],
                    severity="medium",
                    category="requirements",
                )
            )

    def _check_security(self):
        """Check security configuration."""
        secrets = self.intake.get("secrets_policy", {})

        # Check if vault is required for sensitive projects
        data_sensitivity = self._get_max_data_sensitivity()
        if data_sensitivity in ["confidential", "restricted"] and not secrets.get("vault_required"):
            self.questions.append(
                ClarificationQuestion(
                    field="secrets_policy.vault_required",
                    question="You have confidential data. Should secrets be managed in a vault (e.g., AWS Secrets Manager)?",
                    reason="Confidential data typically requires centralized secrets management.",
                    examples=[
                        "Yes, use AWS Secrets Manager",
                        "Yes, use HashiCorp Vault",
                        "No, environment variables are sufficient for this use case",
                    ],
                    severity="high",
                    category="security",
                )
            )

    def _get_max_data_sensitivity(self) -> str:
        """Get the highest data sensitivity level."""
        data_sources = self.intake.get("data", {}).get("sources", [])
        sensitivities = [src.get("sensitivity", "public") for src in data_sources]

        sensitivity_order = {"restricted": 3, "confidential": 2, "internal": 1, "public": 0}
        if not sensitivities:
            return "public"

        return max(sensitivities, key=lambda s: sensitivity_order.get(s, 0))

    @staticmethod
    def _is_measurable(criterion: str) -> bool:
        """Check if a success criterion is measurable (contains numbers, %, etc.)."""
        criterion_lower = criterion.lower()

        # Vague words that indicate unmeasurable criteria (check first)
        vague_words = ["good", "fast", "high", "low", "quality", "better", "improved"]
        if any(word in criterion_lower for word in vague_words):
            return False

        # Measurable requires numbers OR comparison operators
        has_number = any(char.isdigit() for char in criterion)

        comparison_operators = ["<", ">", "≤", "≥", "="]
        has_comparison = any(op in criterion for op in comparison_operators)

        # True if has numbers or comparison operators
        if has_number or has_comparison:
            return True

        # Check for explicit units that suggest measurement
        units = ["%", "ms", "seconds", "minutes", "hours", "kb", "mb", "gb"]
        if any(unit in criterion_lower for unit in units):
            return True

        return False


def clarify_intake(intake: Dict[str, Any]) -> List[ClarificationQuestion]:
    """Analyze intake and return clarifying questions.

    Args:
        intake: Parsed intake YAML as dictionary

    Returns:
        List of clarifying questions sorted by severity
    """
    clarifier = IntakeClarifier(intake)
    return clarifier.analyze()
