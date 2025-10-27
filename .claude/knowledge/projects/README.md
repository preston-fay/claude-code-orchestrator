# Project-Specific Knowledge Base

This directory contains domain-specific knowledge for individual client projects or industry verticals. Each project gets its own subdirectory with YAML knowledge files that augment the universal analytics best practices and Kearney standards.

## Directory Structure

```
.claude/knowledge/projects/
├── telco-churn/
│   ├── domain_knowledge.yaml        # Telecom industry context
│   ├── data_dictionary.yaml         # Project-specific data definitions
│   └── business_rules.yaml          # Client-specific logic
├── agricultural-commodities/
│   ├── domain_knowledge.yaml        # Cocoa/coffee markets
│   ├── data_dictionary.yaml         # Farm, cooperative, pricing data
│   └── business_rules.yaml          # Mondelēz-specific rules
├── financial-services/
│   ├── domain_knowledge.yaml        # Banking/credit context
│   ├── data_dictionary.yaml         # Transactional data
│   └── business_rules.yaml          # Regulatory compliance
└── README.md                         # This file
```

## When to Create Project-Specific Knowledge

Create a project directory when:
- **Starting a new client engagement** with significant analytics work
- **Working in a specialized domain** with unique terminology, metrics, or business logic
- **Reusing similar analyses** across multiple engagements in the same industry
- **Onboarding new team members** who need industry or client context

**Don't create** project directories for:
- One-off, simple analyses (just reference universal best practices)
- Projects with no domain-specific knowledge beyond general analytics
- Internal Kearney projects (unless they involve specialized analytics)

## What Goes in Project Knowledge

### 1. Domain Knowledge (`domain_knowledge.yaml`)

**Purpose**: Industry context, business dynamics, and domain expertise.

**Include**:
- Industry overview and key drivers
- Market structure (players, value chain, competition)
- Key performance indicators (KPIs) specific to the industry
- Industry benchmarks and norms
- Regulatory environment
- Common business challenges and strategies

**Example** (telco churn):
```yaml
name: telco_churn_domain_knowledge
industry: telecommunications

market_context:
  competitive_dynamics:
    - "Mature market with 4 major carriers (Verizon, AT&T, T-Mobile, Dish)"
    - "Price competition intense; differentiation through network quality and bundles"
    - "5G rollout driving customer acquisition"

  churn_drivers:
    primary:
      - "Price sensitivity (especially for prepaid customers)"
      - "Network quality (dropped calls, coverage gaps)"
      - "Customer service experiences"
    secondary:
      - "Device upgrade cycles"
      - "Competitor promotions"
      - "Life events (moving, job changes)"

kpis:
  churn_rate:
    definition: "% of customers who cancel service in a period"
    calculation: "churned_customers / total_customers_at_start"
    benchmark: "1.5-2.5% monthly for postpaid, 4-6% for prepaid"

  arpu:
    definition: "Average Revenue Per User"
    calculation: "total_revenue / average_customers"
    benchmark: "$50-70/month for postpaid"

  clv:
    definition: "Customer Lifetime Value"
    calculation: "ARPU * average_customer_lifetime - acquisition_cost"
    typical_value: "$1,500-3,000 over 3-5 years"
```

### 2. Data Dictionary (`data_dictionary.yaml`)

**Purpose**: Definitions of data elements specific to this project.

**Include**:
- Table/dataset descriptions
- Column definitions (name, type, description, valid values)
- Relationships between tables
- Data quality notes (known issues, missing data patterns)
- Privacy classifications (PII, confidential, public)

**Example**:
```yaml
name: telco_churn_data_dictionary
version: 1.0.0

datasets:
  customer_profile:
    description: "Customer demographic and account information"
    source: "Client CRM system (Salesforce)"
    refresh_frequency: "Daily"
    row_count: 2.5M

    columns:
      customer_id:
        type: string
        description: "Unique customer identifier"
        format: "CUST-XXXXXXX"
        privacy: confidential
        required: true

      tenure_months:
        type: integer
        description: "Number of months since account activation"
        range: [0, 300]
        privacy: public

      plan_type:
        type: categorical
        description: "Service plan tier"
        values: ["Prepaid", "Postpaid Basic", "Postpaid Premium", "Family Plan"]
        privacy: public

      arpu:
        type: float
        description: "Average revenue per user (last 3 months)"
        units: "USD/month"
        privacy: confidential

  usage_data:
    description: "Monthly usage metrics by customer"
    source: "Billing system"
    grain: "customer-month"

    columns:
      voice_minutes:
        type: integer
        description: "Total voice call minutes"
        units: "minutes"

      data_gb:
        type: float
        description: "Total data usage"
        units: "gigabytes"

      sms_count:
        type: integer
        description: "Total SMS messages sent"

relationships:
  - from: usage_data.customer_id
    to: customer_profile.customer_id
    type: many_to_one
```

### 3. Business Rules (`business_rules.yaml`)

**Purpose**: Client-specific logic, constraints, and decision rules.

**Include**:
- Segmentation logic (how to categorize customers, products, regions)
- Calculation formulas specific to client
- Business constraints (regulatory, operational, strategic)
- Decision thresholds and flags
- Exception handling rules

**Example**:
```yaml
name: telco_churn_business_rules
version: 1.0.0

segmentation:
  customer_value_tiers:
    high_value:
      definition: "ARPU > $80 OR tenure > 36 months"
      priority: 1
      retention_budget: "Up to $200 incentive"

    medium_value:
      definition: "ARPU $40-80 AND tenure 12-36 months"
      priority: 2
      retention_budget: "Up to $100 incentive"

    low_value:
      definition: "ARPU < $40 OR tenure < 12 months"
      priority: 3
      retention_budget: "Up to $50 incentive"

churn_prediction:
  risk_thresholds:
    high_risk: "Predicted churn probability > 0.7"
    medium_risk: "Predicted churn probability 0.4 - 0.7"
    low_risk: "Predicted churn probability < 0.4"

  intervention_triggers:
    proactive_call:
      condition: "high_risk AND customer_value_tier IN ['high_value', 'medium_value']"
      timing: "Within 48 hours of flag"

    retention_offer:
      condition: "high_risk AND customer_value_tier = 'high_value'"
      max_discount: "20% for 6 months"

regulatory_constraints:
  contact_frequency:
    rule: "Max 2 marketing contacts per customer per month"
    exception: "Service-related communications exempt"

  data_retention:
    rule: "Delete churned customer data after 7 years"
    exception: "Aggregated/anonymized data can be retained indefinitely"
```

## How Agents Use Project Knowledge

### Loading Project Knowledge

When working on a project, agents load **three layers** of knowledge:

1. **Universal** (`.claude/knowledge/analytics_best_practices.yaml`)
   - Core data science principles
   - Feature engineering patterns
   - Model evaluation methods

2. **Firm-wide** (`.claude/knowledge/kearney_standards.yaml`)
   - RAISE framework
   - Presentation standards
   - Client engagement principles

3. **Project-specific** (`.claude/knowledge/projects/{project}/`)
   - Domain knowledge (industry context)
   - Data dictionary (what the data means)
   - Business rules (client-specific logic)

### Example Agent Prompt

```
Data Agent: You are working on the Verizon churn prediction project.

Load knowledge:
- .claude/knowledge/analytics_best_practices.yaml
- .claude/knowledge/kearney_standards.yaml
- .claude/knowledge/projects/telco-churn/domain_knowledge.yaml
- .claude/knowledge/projects/telco-churn/data_dictionary.yaml
- .claude/knowledge/projects/telco-churn/business_rules.yaml

Task: Build a churn prediction model

Guidelines:
1. Follow analytics best practices (feature engineering, evaluation)
2. Apply Kearney standards (RAISE framework, quality gates)
3. Use domain knowledge to:
   - Select relevant features (ARPU, tenure, network quality)
   - Interpret results (benchmark churn rates)
   - Define segments (high/medium/low value tiers per business rules)
4. Use data dictionary to understand fields and relationships
5. Apply business rules for segmentation and intervention thresholds

Deliverable: Model artifacts + slide deck following Kearney presentation standards
```

### Knowledge Hierarchy

When guidance conflicts across layers:
- **Project-specific > Firm-wide > Universal**
- Client requirements override Kearney defaults
- Document deviations with rationale

## Creating a New Project

Follow these steps when starting a new project:

### Step 1: Create Project Directory

```bash
mkdir -p .claude/knowledge/projects/{project-name}
```

### Step 2: Copy Template Files

Use the templates below as starting points.

### Step 3: Customize for Project

- Replace placeholder content with actual project details
- Interview client SMEs for domain knowledge
- Document data dictionaries based on provided datasets
- Capture business rules from client requirements

### Step 4: Validate with Team

- Review with project lead for accuracy
- Get sign-off from client on business rules (if applicable)
- Share with team for awareness

### Step 5: Keep Updated

- Update as new information emerges
- Version control changes (git)
- Document major revisions in changelog

## Template Files

### Template: `domain_knowledge.yaml`

```yaml
name: {project}_domain_knowledge
version: 1.0.0
industry: {industry_name}
client: {client_name}

description: >
  Domain knowledge for {project_name} project.

market_context:
  industry_overview:
    - "Key industry characteristic 1"
    - "Key industry characteristic 2"

  competitive_landscape:
    - "Major players and market shares"
    - "Competitive dynamics"

  trends_and_drivers:
    - "Trend 1"
    - "Trend 2"

kpis:
  kpi_1:
    definition: "What this measures"
    calculation: "Formula or methodology"
    benchmark: "Industry norm or target"
    unit: "%, $, count, etc."

  kpi_2:
    definition: ""
    calculation: ""
    benchmark: ""

business_model:
  revenue_streams:
    - "Stream 1"
    - "Stream 2"

  cost_structure:
    - "Cost category 1"
    - "Cost category 2"

challenges_and_opportunities:
  key_challenges:
    - "Challenge 1"
    - "Challenge 2"

  opportunities:
    - "Opportunity 1"
    - "Opportunity 2"

references:
  - "Industry reports, academic papers, etc."
```

### Template: `data_dictionary.yaml`

```yaml
name: {project}_data_dictionary
version: 1.0.0

datasets:
  dataset_1:
    description: "What this dataset contains"
    source: "Where data comes from"
    refresh_frequency: "Daily/Weekly/Monthly/Static"
    row_count: X
    grain: "One row per {entity}"

    columns:
      column_1:
        type: "string/integer/float/date/categorical"
        description: "What this column means"
        format: "Format specification if applicable"
        range: [min, max] # for numeric
        values: ["value1", "value2"] # for categorical
        privacy: "public/confidential/pii"
        required: true/false

      column_2:
        type: ""
        description: ""
        # ...

  dataset_2:
    description: ""
    # ...

relationships:
  - from: dataset_1.column_x
    to: dataset_2.column_y
    type: one_to_one/one_to_many/many_to_many

data_quality_notes:
  - "Known issue 1"
  - "Known issue 2"
```

### Template: `business_rules.yaml`

```yaml
name: {project}_business_rules
version: 1.0.0

segmentation:
  segment_1:
    definition: "Logical condition defining this segment"
    priority: 1
    notes: "Why this segment matters"

  segment_2:
    definition: ""
    priority: 2
    notes: ""

calculations:
  metric_1:
    formula: "Mathematical formula or pseudocode"
    inputs: ["input1", "input2"]
    output: "What this produces"

  metric_2:
    formula: ""
    inputs: []
    output: ""

decision_rules:
  rule_1:
    condition: "When does this rule apply?"
    action: "What to do when condition is met"
    exception: "When NOT to apply this rule"

  rule_2:
    condition: ""
    action: ""
    exception: ""

constraints:
  regulatory:
    - "Compliance requirement 1"
    - "Compliance requirement 2"

  operational:
    - "Business constraint 1"
    - "Business constraint 2"

  strategic:
    - "Strategic priority 1"
    - "Strategic priority 2"
```

## Best Practices

### Do:
- **Start small**: Capture only essential knowledge, expand as needed
- **Use plain language**: Avoid jargon unless it's standard industry terminology
- **Cite sources**: Reference where knowledge came from (client docs, interviews, research)
- **Version control**: Track changes, especially to business rules
- **Keep current**: Update as project evolves, don't let it go stale

### Don't:
- **Copy-paste without customization**: Templates are starting points, not final products
- **Include sensitive data**: No actual customer records, only metadata and examples
- **Over-engineer**: Simple YAML beats complex schemas
- **Duplicate universal knowledge**: Don't repeat analytics best practices here
- **Create orphaned directories**: If project ends, archive (don't delete) its knowledge

## Examples from Other Industries

### Example: Agricultural Commodities

```
.claude/knowledge/projects/agricultural-commodities/
├── domain_knowledge.yaml
│   - Cocoa/coffee markets, pricing dynamics
│   - West African production regions
│   - Seasonality and climate impacts
│   - Sustainability certifications (Fair Trade, Rainforest Alliance)
├── data_dictionary.yaml
│   - Farm-level data (GPS, yields, quality scores)
│   - Cooperative data (membership, capacity)
│   - Pricing data (futures, spot, farm-gate)
│   - Weather data (rainfall, temperature, ENSO indices)
└── business_rules.yaml
    - Quality grading system (1-5 scale)
    - Sustainability sourcing requirements (30% certified)
    - Pricing formulas (farm-gate = futures * quality_factor - logistics)
    - Supplier segmentation (strategic, preferred, transactional)
```

### Example: Financial Services

```
.claude/knowledge/projects/financial-services/
├── domain_knowledge.yaml
│   - Credit risk modeling context
│   - Regulatory environment (FCRA, ECOA, fair lending)
│   - Industry benchmarks (default rates, approval rates)
│   - Consumer credit bureau data (FICO, VantageScore)
├── data_dictionary.yaml
│   - Application data (income, employment, debt-to-income)
│   - Credit bureau data (trade lines, inquiries, utilization)
│   - Transactional data (deposits, withdrawals, overdrafts)
│   - Collections data (delinquency stage, recovery)
└── business_rules.yaml
    - Credit score cutoffs (approve > 680, review 620-680, decline < 620)
    - Debt-to-income limits (< 43% for qualified mortgages)
    - Adverse action requirements (provide reasons for decline)
    - Model monitoring thresholds (PSI > 0.1 triggers review)
```

## Maintenance and Governance

### Ownership
- **Project Lead**: Responsible for accuracy and completeness
- **Data Agent**: Updates data dictionary as new sources added
- **Developer Agent**: Updates business rules as logic changes
- **QA Agent**: Validates knowledge against project artifacts

### Review Cadence
- **Weekly**: During active project phase
- **Monthly**: During steady-state
- **End of project**: Final update and archival

### Archival
When a project ends:
1. Create final version with "ARCHIVED" tag
2. Move to `.claude/knowledge/projects/_archived/{project}/`
3. Document lessons learned in `project_retrospective.md`
4. Keep for future reference (similar projects, knowledge reuse)

## FAQs

**Q: How detailed should the data dictionary be?**
A: Detailed enough for a new analyst to understand the data without asking questions. Include all fields used in analysis, not every single column.

**Q: What if business rules change mid-project?**
A: Update the YAML, increment the version number, and document the change in git commit message. Inform the team of material changes.

**Q: Should I include client-confidential information?**
A: No actual client data (customer names, financials, etc.). Only metadata, structures, and de-identified examples. Follow client's data classification policies.

**Q: Can I reuse knowledge across similar projects?**
A: Yes! Copy and adapt. If you find yourself reusing often, consider promoting to a shared industry template.

**Q: How do I handle conflicting information between knowledge files?**
A: Project-specific knowledge overrides general knowledge. Document the conflict and why the exception exists.

## Contact

For questions or to contribute templates for new industries, contact the Claude Code Orchestrator maintainers.

---

**Version**: 1.0.0
**Last Updated**: 2025-01-26
**Maintainer**: Claude Code Orchestrator Team
