# Intake Clarification System

## Overview

The Intake Clarification System analyzes your project intake configuration and identifies underspecified or ambiguous areas **before** you start the orchestrator workflow. It generates targeted clarifying questions to improve specification quality and prevent costly rework during development.

**Key Benefits:**
- **Catch issues early**: Identify gaps before Planning Phase starts
- **Reduce rework cycles**: Fewer Consensus revisions and backtracking
- **Improve specifications**: Learn to write clear, measurable requirements
- **Save agent time**: Well-specified intakes lead to better first-pass outputs
- **Educational**: Teaches AI Coding Academy students how to scope projects

---

## Quick Start

### 1. Create Intake File

Start with a template:

```bash
orchestrator intake new --type ml
# Creates intake/ml-project.intake.yaml
```

### 2. Run Clarification Analysis

Before starting the orchestrator, analyze your intake:

```bash
orchestrator intake clarify intake/ml-project.intake.yaml
```

**Output:**
```
🔍 Analyzing intake file: intake/ml-project.intake.yaml

Found 7 clarifications:

#1 [CRITICAL] requirements
❓ What measurable criteria will define project success?
   Field: goals.success_criteria
   Reason: Success criteria are missing. Without clear metrics, it's impossible to validate if the project achieves its goals.
   Examples:
     • Model achieves R² ≥ 0.85 on holdout test set
     • Dashboard query performance <500ms (P95)
     • API handles 1000 requests/second with <200ms latency

#2 [CRITICAL] data
❓ What are the data sources for this project?
   Field: data.sources
   Reason: Analytics/ML projects require data sources to be specified.
   Examples:
     • Production PostgreSQL database (customer_transactions table)
     • S3 bucket with CSV files (s3://company-data/sales/)
     • Snowflake data warehouse (ANALYTICS.CUSTOMER_EVENTS)

...

Summary:
  Critical: 3
  High: 2
  Medium: 2

💡 Tips:
  - Address critical/high severity questions before starting orchestrator
  - Update your intake file with clarified information
  - Run 'orchestrator intake validate' after updates
  - Run this command again to check for remaining issues
```

### 3. Update Intake

Address the questions by updating your intake:

```yaml
goals:
  success_criteria:
    - "Model achieves F1 score ≥ 0.85 on holdout test set"
    - "Inference latency < 100ms (P95)"
    - "Model drift detection within 24 hours"

data:
  sources:
    - name: "Customer transactions"
      type: "PostgreSQL"
      volume: "10GB, 1M records"
      sensitivity: "confidential"
```

### 4. Re-Run Clarification

Verify your updates resolved the issues:

```bash
orchestrator intake clarify intake/ml-project.intake.yaml
```

**Ideal output:**
```
✅ No clarifications needed!

Your intake is well-specified and ready for orchestration.

💡 Next step: orchestrator run start --intake intake/ml-project.intake.yaml
```

---

## What Gets Checked

The clarifier analyzes multiple dimensions of your intake:

### 1. Success Criteria

**Critical Issues:**
- ✅ Missing success criteria entirely
- ✅ Vague criteria without measurements

**Examples:**
```yaml
# ❌ BAD: Vague, unmeasurable
success_criteria:
  - "High accuracy"
  - "Fast performance"
  - "Good user experience"

# ✅ GOOD: Specific, measurable
success_criteria:
  - "F1 score ≥ 0.85 on holdout test set"
  - "API response time < 200ms (P95)"
  - "User task completion rate ≥ 90%"
```

### 2. Data Sources

**Critical Issues:**
- ✅ Missing data sources for ML/analytics projects
- ✅ Data sources without volume information
- ✅ Sensitive data without compliance requirements

**Examples:**
```yaml
# ❌ BAD: No volume, no compliance
data:
  sources:
    - name: "Customer PII"
      type: "Database"
      sensitivity: "confidential"

# ✅ GOOD: Complete specification
data:
  sources:
    - name: "Customer transactions"
      type: "PostgreSQL"
      volume: "10GB, 1M records, growing 1GB/month"
      sensitivity: "confidential"
constraints:
  compliance:
    - "GDPR"
    - "SOC2"
```

### 3. ML/Analytics Configuration

**High Issues:**
- ✅ ML project without model types specified
- ✅ ML project without latency requirements
- ✅ Classification/regression without accuracy targets

**Examples:**
```yaml
# ❌ BAD: Missing key details
analytics_ml:
  required: true
  use_cases:
    - "Prediction"

# ✅ GOOD: Complete specification
analytics_ml:
  required: true
  use_cases:
    - "Customer churn prediction"
  model_types:
    - "Random Forest"
    - "XGBoost"
  data_volume: "10GB historical data, 1M records"
  latency_requirements: "Real-time: <100ms"
```

### 4. Technical Preferences

**Medium Issues:**
- ✅ Too many technology restrictions
- ✅ Conflicting framework preferences

**Examples:**
```yaml
# ⚠️ WARNING: Over-constrained
tech_preferences:
  avoid:
    - "Java"
    - "Python 2"
    - "MongoDB"
    - "React"
    - "Vue"
    - "Angular"
    - "MySQL"
    - "PostgreSQL"  # Too restrictive!

# ✅ BETTER: Strategic constraints
tech_preferences:
  avoid:
    - "Python 2"  # End of life
    - "Unmaintained libraries"
```

### 5. Constraints & Timeline

**High Issues:**
- ✅ Timeline set to "TBD"
- ✅ Sensitive data without compliance specification
- ✅ Missing stakeholder identification

**Examples:**
```yaml
# ❌ BAD: Underspecified
constraints:
  timeline: "TBD"
  budget: "TBD"

stakeholders:
  product_owner: "To be determined"

# ✅ GOOD: Clear constraints
constraints:
  timeline: "3 months to MVP, 6 months to production"
  budget: "$150K for initial development"

stakeholders:
  product_owner: "Jane Doe (VP of Analytics)"
  tech_lead: "John Smith (Senior ML Engineer)"
```

---

## Question Severity Levels

### 🔴 Critical
**Impact:** Will likely cause workflow failure or major rework

**Examples:**
- Missing success criteria
- No data sources for ML/analytics project
- No accuracy target for ML classification
- Confidential data without compliance requirements

**Action:** **Must** address before starting orchestrator

---

### 🟡 High
**Impact:** Will cause significant delays or suboptimal decisions

**Examples:**
- Data sources without volume information
- ML project without model types
- Timeline set to "TBD"
- No latency requirements for real-time systems

**Action:** **Should** address before starting; may proceed with caution

---

### 🔵 Medium
**Impact:** May cause minor issues or inefficiencies

**Examples:**
- Too many technology restrictions
- Missing test type specifications
- Stakeholders marked "To be determined"

**Action:** Nice to address; can proceed

---

### 🟢 Low
**Impact:** Quality-of-life improvements

**Examples:**
- Missing secondary goals
- Optional documentation not specified

**Action:** Can defer to later phases

---

## Filtering Clarifications

### Filter by Severity

Show only critical issues:
```bash
orchestrator intake clarify intake/my-project.yaml --severity critical
```

Show high and critical:
```bash
# Run twice with different filters
orchestrator intake clarify intake/my-project.yaml --severity critical
orchestrator intake clarify intake/my-project.yaml --severity high
```

### Filter by Category

Focus on specific areas:

```bash
# Data-related questions only
orchestrator intake clarify intake/my-project.yaml --category data

# Requirements questions only
orchestrator intake clarify intake/my-project.yaml --category requirements

# Security questions only
orchestrator intake clarify intake/my-project.yaml --category security
```

**Available categories:**
- `requirements` - Goals, success criteria, stakeholders
- `data` - Data sources, volume, quality
- `technical` - Tech preferences, architecture
- `security` - Secrets, compliance, privacy
- `testing` - Test types, coverage

---

## Example Workflows

### Workflow 1: New ML Project

```bash
# 1. Create intake from template
orchestrator intake new --type ml

# 2. Edit intake with project details
vim intake/ml-project.intake.yaml

# 3. Run clarification
orchestrator intake clarify intake/ml-project.intake.yaml

# 4. Address critical/high questions
# Update intake.yaml based on questions

# 5. Validate intake schema
orchestrator intake validate intake/ml-project.intake.yaml

# 6. Re-run clarification (should have fewer/no questions)
orchestrator intake clarify intake/ml-project.intake.yaml

# 7. Start orchestrator
orchestrator run start --intake intake/ml-project.intake.yaml
```

### Workflow 2: Iterative Refinement

```bash
# Start with basic intake
orchestrator intake clarify intake/basic.yaml
# Found 12 clarifications (4 critical, 5 high, 3 medium)

# Address only critical first
orchestrator intake clarify intake/basic.yaml --severity critical
# 4 critical questions → update intake

orchestrator intake clarify intake/basic.yaml --severity critical
# 0 critical questions ✅

# Now address high severity
orchestrator intake clarify intake/basic.yaml --severity high
# 5 high questions → update intake

orchestrator intake clarify intake/basic.yaml --severity high
# 1 high question remaining (acceptable)

# Start orchestrator with 1 high + 3 medium remaining
orchestrator run start --intake intake/basic.yaml
```

### Workflow 3: Team Review

```bash
# Junior engineer creates intake
orchestrator intake new --type analytics
vim intake/analytics-dashboard.yaml

# Run clarification and save output
orchestrator intake clarify intake/analytics-dashboard.yaml > clarifications.txt

# Send to senior engineer for review
# Senior engineer reviews clarifications.txt and provides answers

# Junior engineer updates intake based on answers
vim intake/analytics-dashboard.yaml

# Verify clarifications resolved
orchestrator intake clarify intake/analytics-dashboard.yaml
# ✅ No clarifications needed!

# Start orchestrator
orchestrator run start --intake intake/analytics-dashboard.yaml
```

---

## Measurability Heuristic

The clarifier uses a heuristic to detect vague vs. measurable criteria:

### ✅ Measurable Criteria

Criteria that pass the measurability test:
```
✅ "Accuracy > 85%"                    (has number + comparison)
✅ "Response time < 200ms"             (has number + units)
✅ "Test coverage ≥ 80%"               (has number + percentage)
✅ "F1 score = 0.90"                   (has number + comparison)
✅ "Query time <500ms (P95)"           (has number + units)
✅ "User satisfaction ≥4.5/5.0"        (has number + scale)
```

### ❌ Vague Criteria

Criteria that fail (trigger clarification question):
```
❌ "High accuracy"                     (vague adjective)
❌ "Fast performance"                  (vague adjective)
❌ "Good quality"                      (vague adjective)
❌ "Better user experience"            (vague comparative)
❌ "Improved latency"                  (vague, no baseline)
❌ "Low error rate"                    (vague, no threshold)
```

### Making Criteria Measurable

| Vague | Measurable |
|-------|------------|
| "High accuracy" | "F1 score ≥ 0.85" |
| "Fast performance" | "API response time < 200ms (P95)" |
| "Good quality" | "Data quality score ≥ 95%" |
| "Better UX" | "Task completion rate ≥ 90%" |
| "Low error rate" | "Error rate < 1% (< 100 errors/10K requests)" |

---

## Common Clarification Questions

### For ML Projects

1. **What is the target accuracy/performance metric?**
   - F1 score ≥ 0.85, AUC-ROC ≥ 0.90
   - RMSE ≤ 5.0, R² ≥ 0.80
   - MAPE < 10%, MAE < 2.5

2. **What is the data volume?**
   - 10K rows, 50MB
   - 500GB total, growing 10GB/month
   - 1M events/day, ~100GB/month

3. **What are the latency requirements?**
   - Real-time: <100ms (e.g., fraud detection)
   - Near-real-time: <5 seconds (e.g., recommendations)
   - Batch: Hourly or daily (e.g., nightly reports)

4. **What types of models are needed?**
   - Binary classification (logistic regression, random forest)
   - Time series forecasting (ARIMA, Prophet, LSTM)
   - Clustering (K-means, DBSCAN)

### For Analytics Projects

1. **What is the data volume and update frequency?**
   - 100GB static data, updated monthly
   - 1TB data warehouse, real-time streaming
   - 10M rows, batch updates nightly

2. **What are the query performance requirements?**
   - Dashboard queries < 500ms
   - Report generation < 5 seconds
   - Batch queries acceptable (< 1 hour)

3. **What data quality standards apply?**
   - Data quality metrics > 95%
   - Missing values < 5% per column
   - Freshness: Data updated within 1 hour

### For Web Apps

1. **What are the performance requirements?**
   - Page load time < 2 seconds
   - Time to Interactive (TTI) < 3 seconds
   - API response time < 200ms (P95)

2. **What are the scalability requirements?**
   - Support 1000 concurrent users
   - Handle 10K requests/second
   - Auto-scale to handle 10x traffic spikes

---

## For AI Coding Academy

### Teaching Intake Specification

**Module: Writing Clear Requirements**

**Learning Objectives:**
- Distinguish vague vs. measurable success criteria
- Understand the cost of underspecified intakes
- Practice iterative refinement based on clarification questions

**Exercise 1: Vague to Measurable**
Give students vague criteria, have them make measurable:
- "Build a fast recommendation engine" →?
- "Create a dashboard with good performance" →?
- "Develop an accurate prediction model" →?

**Exercise 2: Intake Triage**
Provide intakes with varying quality:
- Intake A: Well-specified (0 questions)
- Intake B: Missing critical info (7 critical questions)
- Intake C: Some gaps (3 high, 2 medium questions)

Students run clarification and rank by readiness.

**Exercise 3: Fixing Bad Intakes**
Provide a deliberately bad intake with 15+ clarifications.
Students must:
1. Run clarification
2. Prioritize questions
3. Update intake to resolve critical/high
4. Re-run to verify <5 questions remain

**Grading Rubric:**
- **Clarity** (40%): Success criteria are measurable
- **Completeness** (30%): All required fields present
- **Realism** (20%): Constraints and timelines are realistic
- **Improvement** (10%): Reduced clarifications from initial to final

### Instructor Dashboard

Track student intake quality:
```bash
# Batch analyze all student intakes
for intake in student-intakes/*.yaml; do
  echo "=== $intake ==="
  orchestrator intake clarify "$intake" --severity critical | grep "Found"
done

# Output:
# === student-1.yaml ===
# Found 8 clarifications
# === student-2.yaml ===
# Found 2 clarifications  ✅ Better!
# === student-3.yaml ===
# Found 0 clarifications  ✅ Excellent!
```

---

## Troubleshooting

### "No clarifications needed" but Intake Seems Vague

The clarifier uses heuristics, not perfect semantic analysis. It may miss:
- Domain-specific ambiguities
- Implicit assumptions
- Organizational context

**Solution:** Combine clarifier with human review:
```bash
# Run clarifier
orchestrator intake clarify intake/project.yaml

# Also get peer review from experienced engineer
# Use clarifier as a baseline, not the final word
```

### Too Many Questions (Overwhelming)

If you get 20+ questions:

**Solution 1: Focus on critical first**
```bash
orchestrator intake clarify intake/project.yaml --severity critical
# Address only critical, run again
orchestrator intake clarify intake/project.yaml --severity high
# Then address high severity
```

**Solution 2: Category-by-category**
```bash
orchestrator intake clarify intake/project.yaml --category requirements
# Fix requirements
orchestrator intake clarify intake/project.yaml --category data
# Fix data
orchestrator intake clarify intake/project.yaml --category security
# Fix security
```

### False Positives

Clarifier may flag legitimate cases:

**Example:** "Data source volume not specified" but you're building a prototype with sample data.

**Solution:** Add explanation in intake:
```yaml
data:
  sources:
    - name: "Sample dataset"
      type: "CSV"
      description: "Prototype using 100-row sample (full dataset TBD after POC)"
      volume: "Sample: 100 rows, 5KB"
```

---

## CLI Reference

### `orchestrator intake clarify`

Analyze intake and generate clarifying questions.

**Syntax:**
```bash
orchestrator intake clarify <intake-file> [OPTIONS]
```

**Arguments:**
- `intake-file`: Path to intake YAML file (required)

**Options:**
- `--severity, -s`: Filter by severity (critical, high, medium, low)
- `--category, -c`: Filter by category (requirements, data, technical, security, testing)

**Examples:**
```bash
# Analyze all aspects
orchestrator intake clarify intake/ml-project.yaml

# Only critical issues
orchestrator intake clarify intake/ml-project.yaml --severity critical

# Only data-related questions
orchestrator intake clarify intake/ml-project.yaml --category data

# Combine filters (NOT YET SUPPORTED - run separately)
orchestrator intake clarify intake/ml-project.yaml --severity critical --category data
```

**Exit Codes:**
- `0`: Success (questions generated or no questions needed)
- `1`: Error (file not found, invalid YAML, etc.)

---

## Best Practices

### 1. Run Early and Often
```bash
# After creating intake
orchestrator intake new --type ml
orchestrator intake clarify intake/ml-project.yaml

# After updates
vim intake/ml-project.yaml
orchestrator intake clarify intake/ml-project.yaml

# Before starting orchestrator
orchestrator intake clarify intake/ml-project.yaml
orchestrator run start --intake intake/ml-project.yaml
```

### 2. Address Critical First
Don't try to fix everything at once:
1. Run clarification
2. Filter to critical: `--severity critical`
3. Fix critical issues
4. Move to high severity
5. Acceptable to start with some medium/low remaining

### 3. Use as a Teaching Tool
For mentoring junior engineers:
1. Have them write intake
2. Run clarification together
3. Discuss why each question was flagged
4. Guide them to write better specs

### 4. Combine with Validation
```bash
# Both should pass
orchestrator intake validate intake/project.yaml   # Schema valid
orchestrator intake clarify intake/project.yaml    # Well-specified
```

### 5. Save Clarification Output
Track improvement over time:
```bash
# Initial clarification
orchestrator intake clarify intake/v1.yaml > clarifications-v1.txt
# 15 questions

# After updates
orchestrator intake clarify intake/v2.yaml > clarifications-v2.txt
# 5 questions (improvement!)

# Compare
diff clarifications-v1.txt clarifications-v2.txt
```

---

## Next Steps

1. **Try it on an existing intake:**
   ```bash
   orchestrator intake clarify intake/your-project.yaml
   ```

2. **Address critical/high questions** by updating intake

3. **Create intake best practices doc** for your team based on common questions

4. **Integrate into workflow:**
   - Add to PR checklist: "Run intake clarification before starting orchestrator"
   - Add to CI: Fail if >5 critical questions
   - Add to onboarding: "Learn to write good intakes using clarification tool"

5. **Teach to AI Coding Academy students** - Make clarification part of intake curriculum

---

**Related Documentation:**
- [Intake System](./intake.md) - Creating and validating intake files
- [Constitution System](./constitution.md) - Defining project principles
- [Orchestrator Workflow](../README.md) - Running the full orchestrator
- [CLAUDE.md](../CLAUDE.md) - Orchestrator manifest and agent roles
