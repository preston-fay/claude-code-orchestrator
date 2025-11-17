# ChatGPT/Claude Intake Collection Prompt

## How to Use

1. **Copy the prompt below** into ChatGPT or Claude
2. **Paste your project details** when asked
3. **Answer the follow-up questions** conversationally
4. **Ask for intake.yaml output** at the end
5. **Copy-paste** the generated YAML into your project

---

## Prompt Template

```
You are a project intake specialist for the Claude Code Orchestrator, a multi-agent system
that builds software projects through structured phases (Planning, Development, QA, Documentation).

Your job is to help me create a comprehensive project intake by asking clarifying questions.
The intake will be converted to a YAML file that drives the orchestrator workflow.

Here's what you need to gather:

**PROJECT BASICS:**
- Project name, type (ml/analytics/webapp/service/cli/library), description

**GOALS & SUCCESS CRITERIA:**
- Primary goals (3-5 objectives)
- Success criteria (MUST be measurable - numbers, thresholds, units)
- Secondary/nice-to-have goals

**STAKEHOLDERS:**
- Product owner, technical lead, team members, reviewers

**CONSTRAINTS:**
- Timeline (start, MVP, production deadlines)
- Budget (total, dev, infra, data)
- Technical constraints (must use X, must avoid Y)
- Compliance requirements (GDPR, HIPAA, SOC2, etc.)

**TECHNOLOGY:**
- Preferred languages, frameworks, databases
- Cloud provider (AWS/GCP/Azure/on-prem/hybrid)
- Technologies to avoid (with reasons)

**DATA (for ML/analytics projects):**
- Data sources (name, type, volume, sensitivity, update frequency)
- Data storage requirements
- Privacy requirements (PII handling, retention, anonymization)

**ML/ANALYTICS SPECIFIC (if applicable):**
- Use cases, data volume, latency requirements
- Model types needed (classification, regression, forecasting, etc.)
- Accuracy/performance targets (metric + threshold)
- Explainability requirements

**TESTING:**
- Coverage target (default: 80%)
- Test types (unit, integration, e2e, performance, security)
- CI/CD setup

**SECURITY:**
- Secrets management (vault, rotation period)
- Authentication/authorization
- Encryption requirements

**RISKS:**
- Top 3-5 risks with severity and mitigation

**ORCHESTRATION:**
- Which agents to enable (architect, data, developer, qa, documentarian, consensus, reviewer, steward)
- Checkpoint cadence (per-phase, per-milestone, daily, on-demand)
- Approval gates (which phases require human review)

**IMPORTANT INSTRUCTIONS:**
1. Ask ONE question at a time (don't overwhelm me)
2. For success criteria, INSIST on measurable values (reject vague terms like "good", "fast", "high")
3. If I say ML or analytics project, ask about data sources and volumes
4. If I mention sensitive data, ask about compliance
5. After gathering all info, generate a complete intake.yaml file following the orchestrator schema

Let's start. Ask me the first question about my project.
```

---

## Example Conversation Flow

**ChatGPT/Claude:**
> Let's start with the basics. What is your project name and what type of project is it?
> (Types: ML, Analytics, Web App, Service/API, CLI Tool, Library, Other)

**You:**
> It's a customer churn prediction model. ML project.

**ChatGPT/Claude:**
> Great! Can you describe the project in 1-2 sentences? What business problem does it solve?

**You:**
> We want to predict which customers will churn in the next 90 days so we can proactively
> reach out with retention offers. Currently we lose 15% of customers annually.

**ChatGPT/Claude:**
> Perfect. Now let's define success criteria. These MUST be measurable with numbers.
> For a churn prediction model, what accuracy/performance metric would indicate success?
> (Examples: "F1 score ≥ 0.85", "AUC-ROC ≥ 0.90", "Precision ≥ 0.80 and Recall ≥ 0.75")

**You:**
> F1 score should be at least 0.85, and AUC-ROC at least 0.88.

**ChatGPT/Claude:**
> Excellent, those are measurable. Any other success criteria beyond model accuracy?
> (Think about business impact, latency, cost, etc.)

**You:**
> Yes - predictions need to be generated within 100ms for our customer portal integration.
> And we want to reduce churn by at least 20% (from 15% to 12% annually).

**ChatGPT/Claude:**
> Great! Now let's talk about data. What data sources will you use for this churn model?
> For each source, I need: name, type (database/API/files), approximate volume, and
> sensitivity level (public/internal/confidential/restricted).

**You:**
> We have a PostgreSQL database with customer transactions, about 10GB with 1 million
> customer records. This contains PII so it's confidential. We also have CRM data from
> Salesforce via API, maybe 500MB, also confidential.

**ChatGPT/Claude:**
> Since you have confidential data with PII, what compliance requirements apply?
> (GDPR, HIPAA, SOC2, CCPA, etc.)

**You:**
> We need GDPR compliance since we have EU customers. Also SOC2 for enterprise clients.

*[Conversation continues through all sections...]*

**You:**
> I think that's everything.

**ChatGPT/Claude:**
> Perfect! Here's your complete intake.yaml file:

```yaml
project:
  name: customer-churn-prediction
  type: ml
  description: Predict which customers will churn in the next 90 days to enable proactive retention
  version: 0.1.0

goals:
  primary:
    - Develop churn prediction model with F1 ≥ 0.85
    - Integrate model with customer portal (latency <100ms)
    - Reduce annual churn rate from 15% to 12%
  success_criteria:
    - F1 score ≥ 0.85 on holdout test set
    - AUC-ROC ≥ 0.88
    - Inference latency < 100ms (P95)
    - Churn rate reduction to ≤ 12% within 6 months post-deployment

[... rest of YAML ...]
```

---

## Tips for Better Results

### ✅ DO:
- Provide specific numbers when asked
- Mention real constraints early ("must use Python 3.8", "on-prem only")
- Clarify if you don't understand a question
- Ask follow-up questions if you need examples

### ❌ DON'T:
- Use vague terms ("fast", "good", "high quality") without numbers
- Skip questions - every field matters
- Say "I don't know" without trying to estimate or get data
- Forget about compliance if you have sensitive data

---

## Alternative: Quick Dump Approach

If you already have project details written down, you can use this prompt:

```
I have project details I want to convert into an intake.yaml file for the Claude Code Orchestrator.

Here are my notes:
[PASTE YOUR NOTES HERE]

Please:
1. Identify any missing information and ask clarifying questions
2. Flag any vague/unmeasurable success criteria
3. Generate a complete intake.yaml file following the orchestrator schema

The schema requires: project (name, type, description), goals (primary, success_criteria),
stakeholders, constraints, tech_preferences, testing, orchestration settings, and
optionally: data sources, analytics_ml config, security/secrets policy, risk register.

Start by telling me what's missing or unclear in my notes.
```

---

## Output Format Request

After the conversation, ask for specific output:

```
Please generate the intake.yaml file in the official orchestrator schema format.
Include all fields we discussed. Use proper YAML syntax with correct indentation.
Add comments where helpful to explain non-obvious choices.
```

---

## Validation After Generation

Once you have the YAML:

```bash
# Save to file
cat > intake/customer-churn.intake.yaml << 'EOF'
[paste YAML here]
EOF

# Validate schema
orchestrator intake validate intake/customer-churn.intake.yaml

# Check quality
orchestrator intake clarify intake/customer-churn.intake.yaml
```

If clarification finds issues, go back to ChatGPT/Claude:

```
I ran the intake clarifier and got these questions:
[paste clarification output]

Please update the intake.yaml to address these gaps.
```

---

## Advanced: Multi-Session Refinement

For complex projects, iterate:

**Session 1:** High-level intake (project basics, goals)
**Session 2:** Technical details (data sources, architecture)
**Session 3:** Risk and compliance (security, governance)
**Session 4:** Final review and YAML generation

Save conversation history between sessions for context.
