# Project Constitution: Customer Churn Prediction Model

> **Purpose:** This constitution establishes the fundamental principles, standards, and guardrails for the Customer Churn Prediction ML project.

**Version:** 1.0.0
**Created:** 2025-01-15
**Last Updated:** 2025-01-15

---

## 🎯 Core Principles

### Mission Statement
Build a production-grade ML model that predicts customer churn with 85%+ accuracy while maintaining explainability for business stakeholders and regulatory compliance.

### Values
- **Reproducibility**: All experiments, training runs, and results must be fully reproducible
- **Explainability**: Model decisions must be interpretable for non-technical stakeholders
- **Fairness**: Model must be tested for bias across customer segments
- **Privacy-First**: No PII in training data; all features must be anonymized

---

## 📐 Code Quality Standards

### Mandatory Requirements
- All Python functions must have docstrings (Google style)
- Test coverage must be ≥80% for data pipelines and ≥70% for model code
- All code must pass `ruff` linting with zero errors
- Type hints required for all function signatures
- No hardcoded credentials or API keys (use environment variables)

### Code Style
- Use Black formatter with line length 100
- Use isort for import sorting
- Follow PEP 8 naming conventions
- Maximum function complexity: McCabe score ≤10

### Testing Requirements
- Unit tests for all data validation functions
- Integration tests for ETL pipeline end-to-end
- Model performance tests (accuracy, precision, recall, F1)
- Data drift tests using statistical tests (KS test, PSI)
- Smoke tests for inference API endpoints

### Documentation Requirements
- README with setup instructions and architecture overview
- Data dictionary documenting all features and transformations
- Model card documenting training data, performance, limitations
- API documentation using OpenAPI/Swagger specification

---

## 🎨 User Experience (UX) Principles

### Design Consistency
- All dashboards must use Kearney 6-color chart palette (#D2D2D2, #A5A5A5, etc.)
- All visualizations must have clear titles, axis labels, and legends
- All metrics must include confidence intervals or error bars

### Performance Standards
- Inference API must respond in <100ms (P95)
- Batch predictions must process 10K records/minute minimum
- Dashboard queries must complete in <500ms
- Model retraining must complete in <4 hours

### Accessibility
- All dashboards must meet WCAG 2.1 AA standards
- Color schemes must be colorblind-friendly
- All charts must have text alternatives for screen readers

---

## 🔒 Security & Privacy

### Security Standards
- All API endpoints must require authentication (OAuth2 + JWT)
- All database connections must use SSL/TLS
- Model artifacts must be signed and versioned
- Access control: Principle of least privilege (RBAC)

### Privacy Requirements
- No PII in training data (pseudonymize customer IDs)
- No PII in model logs or metrics
- Data retention: Raw data deleted after 90 days
- GDPR compliance: Right to explanation for predictions

### Secrets Management
- Use AWS Secrets Manager for all credentials
- Rotate database passwords every 90 days
- API keys must have expiration dates
- Never commit .env files or credentials to git

---

## 📊 Data Principles

### Data Quality
- Missing value rate must be <5% per feature
- Outliers must be investigated and documented (not blindly removed)
- Data validation checks at ingestion, transformation, and pre-training
- All data quality metrics tracked in DVC/MLflow

### Data Governance
- All data sources must have documented lineage
- Feature engineering logic must be version-controlled
- Training/test split must be stratified by time (no data leakage)
- Feature store must be the single source of truth for features

### Data Privacy
- Remove PII before data enters feature store
- Use differential privacy for sensitive features (epsilon=1.0)
- Log all data access with user ID and timestamp
- Anonymized data only for development/staging environments

---

## 🚫 Forbidden Practices

### Never Do This
- ❌ **Train/test split without time stratification**: Causes data leakage and overoptimistic metrics
- ❌ **Feature engineering on full dataset**: Must engineer on training set only, then apply to test
- ❌ **Cherry-picking metrics**: Report all standard metrics (accuracy, precision, recall, F1, AUC-ROC)
- ❌ **Deploying models without explainability**: SHAP values required for all predictions
- ❌ **Ignoring class imbalance**: Must use stratified sampling or SMOTE/class weights

### Technologies to Avoid
- ❌ **pickle for model serialization** (use joblib or ONNX for production)
- ❌ **print() for logging** (use proper logging library)
- ❌ **Global variables** (use configuration management)

### Anti-Patterns
- ❌ **Jupyter notebooks in production**: Notebooks for exploration only, not production code
- ❌ **Manual hyperparameter tuning**: Use Optuna/Ray Tune for systematic search
- ❌ **Training without validation set**: Must have train/validation/test split

---

## ✅ Required Practices

### Always Do This
- ✅ **Version all experiments**: Use MLflow for tracking all training runs
- ✅ **Log hyperparameters**: Every experiment must log all hyperparameters
- ✅ **Test for bias**: Run fairness metrics across customer segments (age, geography)
- ✅ **Monitor drift**: Implement data drift and model drift detection
- ✅ **Document assumptions**: All modeling assumptions must be documented in ADRs

### Technology Standards
- ✅ **MLflow**: All experiments tracked in MLflow (models, metrics, artifacts)
- ✅ **DVC**: Data versioning using DVC with S3 backend
- ✅ **Pytest**: All tests written with pytest framework
- ✅ **FastAPI**: Inference API built with FastAPI
- ✅ **PostgreSQL**: Feature store implemented in PostgreSQL

---

## 🎓 Kearney Standards

### RAISE Framework Compliance
This project must adhere to Kearney's RAISE framework:
- **R**igorous: Validate model performance on out-of-time test set, document all assumptions
- **A**ctionable: Provide feature importance and SHAP values for business action
- **I**nsightful: Explain why customers churn (not just predict)
- **S**tructured: Reproducible pipeline with clear methodology
- **E**ngaging: Executive dashboard with clear ROI metrics (cost of false positives/negatives)

### Brand Compliance
- All charts use Kearney color palette (primary: #7823DC)
- All fonts use Inter typeface
- All deliverables include Kearney logo and branding

### Client-Specific Requirements
- Model must integrate with client's Salesforce CRM
- Predictions must be explainable to non-technical executives
- Model must comply with financial services regulations (no discrimination)

---

## 📋 Phase-Specific Guidelines

### Planning Phase
- Architect must document baseline model performance expectations
- Architect must specify train/validation/test split strategy
- Architect must identify potential bias risks and mitigation strategies

### Data Engineering Phase
- Data agent must create data quality report before feature engineering
- Data agent must document all feature transformations in data dictionary
- Data agent must validate no PII in processed features

### Development Phase
- Developer must implement model monitoring (drift detection)
- Developer must create model card documenting intended use and limitations
- Developer must implement SHAP explainability for all predictions

### QA Phase
- QA agent must validate model performance on holdout test set
- QA agent must verify no data leakage (train/test contamination)
- QA agent must validate inference API meets latency requirements (<100ms)
- QA agent must test for bias across customer segments

### Documentation Phase
- Documentarian must create data dictionary with feature descriptions
- Documentarian must create model card (Model Card Toolkit)
- Documentarian must document model limitations and failure modes

---

## 🔄 Amendment Process

This constitution can be amended through the following process:

1. **Proposal**: Document proposed change with rationale in ADR
2. **Review**: Consensus agent reviews for conflicts with governance
3. **Approval**: Tech lead approves change
4. **Documentation**: Update constitution with version bump
5. **Communication**: Notify team via Slack/email

### Amendment History
- **1.0.0** (2025-01-15): Initial constitution approved

---

## 📚 References

### Related Documents
- Project Intake: `intake/customer-churn-ml.intake.yaml`
- Client Governance: `clients/financial-services-co/governance.yaml`
- Architecture Decisions: `.claude/decisions/`
- Data Dictionary: `docs/data_dictionary.md`
- Model Card: `docs/model_card.md`

### Standards & Frameworks
- [MLOps Best Practices](https://ml-ops.org/)
- [Model Cards for Model Reporting](https://arxiv.org/abs/1810.03993)
- [Fairness Indicators](https://www.tensorflow.org/responsible_ai/fairness_indicators/guide)
- [Kearney RAISE Framework](https://www.kearney.com/)

---

**Enforcement:** This constitution is enforced through:
- Preflight checks (orchestrator validates constitution exists before starting)
- QA agent validation (runs constitution compliance tests)
- CI/CD gates (linting, test coverage, security scans)
- Code review (Reviewer agent checks adherence)

**Status:** Approved
**Approved By:** Jane Doe (Tech Lead)
**Approval Date:** 2025-01-15
