# Project Intake Form

**Instructions:** Fill out this form during your intake meeting. Use this to create your `intake.yaml` file.

---

## Section 1: Project Basics

### 1.1 Project Information
- **Project Name** (kebab-case, e.g., customer-churn-model): _______________
- **Project Type** (select one):
  - ☐ ML (Machine Learning)
  - ☐ Analytics (Dashboards, Reports, ETL)
  - ☐ Web App (SPA, Full-Stack)
  - ☐ Service (API, Microservice)
  - ☐ CLI (Command-Line Tool)
  - ☐ Library (Reusable Package)
  - ☐ Other: _______________

- **Brief Description** (1-2 sentences):
  ```
  _______________________________________________________________________________
  _______________________________________________________________________________
  ```

- **Initial Version**: _______________ (default: 0.1.0)

---

## Section 2: Goals & Success Criteria

### 2.1 Primary Goals
**List 3-5 main objectives. Be specific.**

1. _______________________________________________________________________________
2. _______________________________________________________________________________
3. _______________________________________________________________________________
4. _______________________________________________________________________________
5. _______________________________________________________________________________

### 2.2 Secondary Goals (Nice-to-Haves)

1. _______________________________________________________________________________
2. _______________________________________________________________________________
3. _______________________________________________________________________________

### 2.3 Success Criteria ⚠️ **MUST BE MEASURABLE**

**Bad Example:** "High accuracy", "Fast performance"
**Good Example:** "F1 score ≥ 0.85", "API response time <200ms (P95)"

| Success Criterion | Target | Measurement Method |
|-------------------|--------|-------------------|
| 1. | | |
| 2. | | |
| 3. | | |
| 4. | | |
| 5. | | |

**Validation Questions:**
- ✅ Can you measure this with a number?
- ✅ Can you test this automatically?
- ✅ Is the threshold clear (no ambiguity)?

---

## Section 3: Stakeholders

### 3.1 Key People

- **Product Owner / Decision Maker**: _______________
  - Email: _______________
  - Role: _______________

- **Technical Lead**: _______________
  - Email: _______________
  - Skills: _______________

### 3.2 Team Members
| Name | Role | Email | Availability |
|------|------|-------|--------------|
| | | | |
| | | | |
| | | | |

### 3.3 Reviewers (Code Review, QA)
| Name | Expertise | Email |
|------|-----------|-------|
| | | |
| | | |

---

## Section 4: Constraints

### 4.1 Timeline
- **Start Date**: _______________
- **MVP Deadline**: _______________
- **Production Deadline**: _______________
- **Milestones**:
  1. _______________ by _______________
  2. _______________ by _______________
  3. _______________ by _______________

### 4.2 Budget
- **Total Budget**: $_______________
- **Development Budget**: $_______________
- **Infrastructure Budget**: $_______________
- **Data/Licensing Budget**: $_______________

### 4.3 Team Size
- **Full-time**: _______________ people
- **Part-time**: _______________ people

### 4.4 Technical Constraints
**List any technical limitations or requirements:**

1. _______________________________________________________________________________
2. _______________________________________________________________________________
3. _______________________________________________________________________________

**Examples:**
- Must use on-premises servers (no cloud)
- Must integrate with existing legacy system (Java 8)
- Must support offline mode

### 4.5 Compliance Requirements
☐ GDPR (EU data protection)
☐ HIPAA (Healthcare data)
☐ SOC2 (Security controls)
☐ CCPA (California privacy)
☐ PCI-DSS (Payment card data)
☐ FedRAMP (US government)
☐ Other: _______________

---

## Section 5: Technology Preferences

### 5.1 Preferred Languages
☐ Python
☐ JavaScript/TypeScript
☐ Java
☐ Go
☐ Rust
☐ R
☐ Other: _______________

### 5.2 Preferred Frameworks
**Backend:**
- _______________
- _______________

**Frontend (if applicable):**
- _______________
- _______________

**ML/Data (if applicable):**
- _______________
- _______________

### 5.3 Databases
☐ PostgreSQL
☐ MySQL
☐ MongoDB
☐ Redis
☐ Snowflake
☐ BigQuery
☐ Other: _______________

### 5.4 Cloud Provider
☐ AWS
☐ GCP (Google Cloud)
☐ Azure
☐ On-Premises
☐ Hybrid
☐ None (local only)

### 5.5 Technologies to AVOID
**List any technologies that should NOT be used (with reason):**

| Technology | Reason |
|------------|--------|
| | |
| | |

---

## Section 6: Data (For ML/Analytics Projects)

### 6.1 Data Sources
**For EACH data source, provide:**

| Source Name | Type | Description | Volume | Sensitivity | Update Frequency |
|-------------|------|-------------|--------|-------------|------------------|
| | (DB/API/CSV/S3) | | (GB/rows) | (public/internal/confidential) | (real-time/daily/monthly) |
| | | | | | |
| | | | | | |

### 6.2 Data Storage Requirements
- **Where will processed data be stored?** _______________
- **Data warehouse needed?** ☐ Yes ☐ No
  If yes, which? _______________
- **Feature store needed?** ☐ Yes ☐ No
  If yes, which? _______________

### 6.3 Privacy Requirements
☐ Remove PII before processing
☐ Anonymize/Pseudonymize customer IDs
☐ Implement row-level security
☐ Differential privacy for sensitive features
☐ Data retention policy (specify): _______________
☐ Right to be forgotten (GDPR)
☐ Other: _______________

---

## Section 7: ML/Analytics Specific (Skip if not applicable)

### 7.1 Is ML/Analytics Required?
☐ Yes ☐ No

If yes, continue. If no, skip to Section 8.

### 7.2 Use Cases
**What will the model/analytics be used for?**

1. _______________________________________________________________________________
2. _______________________________________________________________________________
3. _______________________________________________________________________________

### 7.3 Data Volume
- **Historical data available**: _______________
- **Expected growth rate**: _______________
- **Number of features**: _______________
- **Number of records**: _______________

### 7.4 Latency Requirements
☐ Real-time (<100ms) - e.g., fraud detection
☐ Near real-time (<5 seconds) - e.g., recommendations
☐ Batch (hourly/daily) - e.g., nightly reports
☐ Mixed (specify): _______________

### 7.5 Model Types Needed
☐ Classification (binary/multiclass)
☐ Regression (predict continuous values)
☐ Time series forecasting
☐ Clustering (segmentation)
☐ Anomaly detection
☐ NLP (text analysis)
☐ Computer vision (image/video)
☐ Reinforcement learning
☐ Other: _______________

### 7.6 Accuracy/Performance Target
**What accuracy/performance is "good enough"?**

- **Metric**: _______________ (e.g., F1 score, RMSE, AUC-ROC)
- **Threshold**: _______________ (e.g., ≥0.85, <5.0)
- **Baseline (current)**: _______________ (if known)

### 7.7 Explainability Requirements
☐ Black box OK (no explanation needed)
☐ Some explainability (feature importance)
☐ Full explainability (per-prediction SHAP values)
☐ Regulatory requirement (specify): _______________

---

## Section 8: Testing Requirements

### 8.1 Test Coverage Target
- **Minimum coverage**: _______________% (default: 80%)

### 8.2 Test Types Required
☐ Unit tests
☐ Integration tests
☐ End-to-end (E2E) tests
☐ Performance tests
☐ Security tests
☐ Load/Stress tests
☐ Other: _______________

### 8.3 CI/CD
- **Enable CI/CD?** ☐ Yes ☐ No
- **CI Platform**: _______________
  (e.g., GitHub Actions, GitLab CI, Jenkins)

---

## Section 9: Documentation

### 9.1 Required Documentation
☐ README (project overview, setup)
☐ API Reference (endpoints, parameters)
☐ User Guide (how to use)
☐ Architecture Documentation (system design)
☐ Deployment Guide (how to deploy)
☐ Security Documentation (compliance, threat model)
☐ Other: _______________

### 9.2 API Documentation Format
☐ OpenAPI/Swagger
☐ Markdown
☐ JSDoc
☐ Sphinx
☐ None

---

## Section 10: Security & Secrets

### 10.1 Secrets Management
- **Vault required?** ☐ Yes ☐ No
  If yes, which? _______________
  (e.g., AWS Secrets Manager, HashiCorp Vault)

- **Secret rotation period**: _______________
  (e.g., 90 days)

- **Encryption at rest required?** ☐ Yes ☐ No

### 10.2 Authentication/Authorization
- **Authentication method**: _______________
  (e.g., OAuth2, JWT, API keys)

- **Authorization model**: _______________
  (e.g., RBAC, ABAC, none)

- **SSO required?** ☐ Yes ☐ No
  If yes, provider: _______________

---

## Section 11: Risk Register

**Identify top 3-5 risks and mitigation strategies:**

| Risk | Severity | Likelihood | Mitigation |
|------|----------|------------|------------|
| | (Low/Medium/High/Critical) | (Low/Medium/High) | |
| | | | |
| | | | |
| | | | |
| | | | |

**Common risks:**
- Data quality issues from upstream systems
- Model performance degradation over time
- Technical complexity (never built this before)
- Resource constraints (budget, people, time)
- Dependency on external systems/APIs

---

## Section 12: Environments

### 12.1 Development
- **Where will development happen?** _______________
- **Sample data available?** ☐ Yes ☐ No

### 12.2 Staging
- **Staging environment needed?** ☐ Yes ☐ No
- **Data source**: _______________
  (e.g., anonymized production data, synthetic)

### 12.3 Production
- **Scaling requirements**: _______________
  (e.g., auto-scale to 1000 concurrent users)

- **Monitoring needed**:
  ☐ Application metrics (latency, errors)
  ☐ Infrastructure metrics (CPU, memory)
  ☐ Business metrics (conversions, revenue)
  ☐ Model metrics (accuracy, drift)

- **Backup strategy**: _______________
  (e.g., daily backups, point-in-time recovery)

---

## Section 13: Orchestration Preferences

### 13.1 Enabled Agents
**Which agents should participate in this project?**

☐ Architect (system design, technical specs) - **Recommended**
☐ Data (ETL, feature engineering, model training)
☐ Developer (code implementation) - **Recommended**
☐ QA (testing, validation) - **Recommended**
☐ Documentarian (README, guides) - **Recommended**
☐ Consensus (review proposals, resolve conflicts) - **Recommended**
☐ Reviewer (code review, feedback)
☐ Steward (repo hygiene, dead code detection)

**Default:** architect, developer, qa, documentarian, consensus

### 13.2 Checkpoint Cadence
**How often should checkpoints be created?**

☐ Per-phase (after Planning, Development, QA, etc.) - **Recommended**
☐ Per-milestone (after each major feature)
☐ Daily (end of each day)
☐ On-demand (manual trigger only)

### 13.3 Approval Gates
**Which phases require human approval before continuing?**

☐ Planning (review architecture before building)
☐ Data Engineering (review data pipeline before models)
☐ Development (review code before testing)
☐ Quality Assurance (review tests before deployment)
☐ Documentation (review docs before release)

**Recommended for critical projects:** Planning + QA

---

## Section 14: Constitution Principles (Optional)

**Define project-specific principles that override defaults:**

### 14.1 Code Quality Standards
1. _______________________________________________________________________________
2. _______________________________________________________________________________
3. _______________________________________________________________________________

### 14.2 UX Principles
1. _______________________________________________________________________________
2. _______________________________________________________________________________

### 14.3 Security Requirements
1. _______________________________________________________________________________
2. _______________________________________________________________________________

### 14.4 Data Quality Standards
1. _______________________________________________________________________________
2. _______________________________________________________________________________

### 14.5 Forbidden Practices
**What should NEVER be done in this project?**

1. _______________________________________________________________________________
2. _______________________________________________________________________________
3. _______________________________________________________________________________

### 14.6 Required Practices
**What MUST always be done?**

1. _______________________________________________________________________________
2. _______________________________________________________________________________
3. _______________________________________________________________________________

---

## Section 15: Additional Context

### 15.1 Attachments
**Any wireframes, mockups, diagrams, or reference documents?**

| Attachment Name | File Path | Description |
|-----------------|-----------|-------------|
| | | |
| | | |

### 15.2 Notes
**Anything else we should know?**

```
_______________________________________________________________________________
_______________________________________________________________________________
_______________________________________________________________________________
_______________________________________________________________________________
```

---

## Completion Checklist

Before submitting this intake form, verify:

☐ All required fields marked with ⚠️ are filled
☐ Success criteria are MEASURABLE (numbers, thresholds)
☐ Data sources specified (for ML/analytics projects)
☐ Compliance requirements identified
☐ Stakeholders identified with contact info
☐ Timeline and budget are realistic
☐ Risks documented with mitigation plans

---

## Next Steps

1. **Convert to intake.yaml** using template
2. **Run clarification**: `orchestrator intake clarify intake/project.yaml`
3. **Address questions** and update intake
4. **Generate constitution**: `orchestrator constitution generate`
5. **Start orchestrator**: `orchestrator run start`

---

**Form Completed By:** _______________
**Date:** _______________
**Reviewed By:** _______________
**Date:** _______________
