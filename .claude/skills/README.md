# Skills Framework

The Skills framework provides **methodology-focused, reusable patterns** that agents can apply to ANY domain. Skills teach **HOW** to solve classes of problems, not **WHAT** specific problems to solve. Think of skills as technique playbooks, not industry solutions.

## Philosophy: Patterns Over Prescriptions

**Skills are NOT:**
- ❌ Domain-specific solutions (e.g., "agricultural commodity forecasting")
- ❌ Industry playbooks (e.g., "retail supply chain optimization")
- ❌ Prescriptive use cases (e.g., "forecast cocoa prices")

**Skills ARE:**
- ✅ General analytical patterns (e.g., "time series forecasting methodology")
- ✅ Technique catalogs (e.g., "ARIMA, Prophet, LSTM - when to use each")
- ✅ Adaptable workflows (e.g., "how to formulate an optimization problem")
- ✅ Best practices libraries (e.g., "entity resolution process")

**The Goal**: A data scientist working in telecommunications can use the same skills as one working in healthcare or finance. The **techniques** are universal; the **application** is domain-specific.

---

## Available Skills

### 1. Time Series Analytics (`time_series_analytics.yaml`)

**What it teaches**: How to forecast ANY time-ordered metric using statistical and ML methods.

**Key Capabilities**:
- Classical forecasting (ARIMA, exponential smoothing)
- Modern approaches (Prophet for business time series)
- Deep learning (LSTM/GRU for complex patterns)
- Seasonal decomposition and trend analysis
- Anomaly detection and change point analysis
- Multi-horizon forecasting with uncertainty

**Generic Example Use Cases**:
- **Single metric forecasting**: Daily website traffic, monthly revenue, hourly system load
- **Multivariate forecasting**: Sales with marketing spend, energy demand with temperature
- **Seasonal pattern modeling**: Retail sales (weekly + yearly cycles), call center volume
- **Anomaly detection**: System monitoring, quality control, unusual spikes/drops
- **Hierarchical forecasting**: Company → Division → Product (ensure coherence)

**Adaptable to ANY domain**:
- **Telecom**: Call volume, churn rate, network traffic
- **Retail**: Sales, inventory, foot traffic
- **Finance**: Revenue, costs, transaction volume
- **Healthcare**: Patient admissions, equipment usage
- **Manufacturing**: Production output, defect rates

**Key Libraries**: `statsmodels`, `prophet`, `tensorflow`, `ruptures`, `pmdarima`

**Emphasis**: Learn **methodology** (how to test stationarity, choose seasonality, evaluate forecasts) not specific industries.

---

### 2. Survey Data Processing (`survey_data_processing.yaml`)

**What it teaches**: How to clean, match, and analyze ANY survey-structured data.

**Key Capabilities**:
- Data cleaning (missing values, outliers, validation)
- Entity resolution (match respondents despite typos, variations)
- Fuzzy matching (handle name variations, misspellings)
- Text analysis (sentiment, topics, keywords from open-ended responses)
- Categorical analysis (Likert scales, cross-tabs, chi-square tests)
- Survey weighting (correct for non-representative samples)

**Generic Example Use Cases**:
- **Customer feedback**: NPS surveys, satisfaction ratings, product reviews
- **Employee surveys**: Engagement surveys, culture assessments, exit interviews
- **Market research**: Brand perception, product preferences, willingness-to-pay
- **Longitudinal matching**: Track same respondents across waves (annual surveys)
- **Multi-language processing**: Detect language, translate, analyze sentiment

**Adaptable to ANY domain**:
- **Healthcare**: Patient satisfaction surveys, provider feedback
- **Education**: Student evaluations, alumni surveys
- **Government**: Citizen surveys, program evaluations
- **Hospitality**: Guest satisfaction, service quality
- **HR**: Employee engagement, diversity & inclusion surveys

**Key Libraries**: `pandas`, `recordlinkage`, `fuzzywuzzy`, `spacy`, `vaderSentiment`, `textblob`

**Emphasis**: Learn **processes** (entity resolution workflow, text analysis pipeline) not specific survey types.

---

### 3. Optimization Modeling (`optimization_modeling.yaml`)

**What it teaches**: How to formulate and solve resource allocation, routing, and decision problems.

**Key Capabilities**:
- Linear programming (continuous decision variables)
- Integer programming (yes/no decisions, discrete counts)
- Network optimization (routing, flows, shortest paths)
- Assignment and matching (assign workers to tasks)
- Scheduling (sequence tasks over time)
- Portfolio optimization (select projects within budget)
- Scenario optimization (robust decisions under uncertainty)

**Generic Example Use Cases**:
- **Resource allocation**: Allocate budget/labor/equipment to maximize output
- **Facility location**: Which sites to open, how to serve customers
- **Workforce scheduling**: Assign employees to shifts to meet coverage
- **Project portfolio**: Which projects to fund given budget constraint
- **Supply distribution**: Optimize flows from sources through facilities to customers

**Adaptable to ANY domain**:
- **Logistics**: Delivery routing, warehouse placement, inventory
- **Healthcare**: Nurse scheduling, OR scheduling, ambulance placement
- **Finance**: Portfolio allocation, capital budgeting
- **Energy**: Power generation scheduling, grid optimization
- **Manufacturing**: Production planning, machine scheduling

**Key Libraries**: `pulp`, `scipy.optimize`, `cvxpy`, `networkx`, `ortools`

**Emphasis**: Learn **problem formulation** (decision variables, objectives, constraints) not specific industries.

---

## How Agents Use Skills

### Universal Application Process

**Step 1: Identify Problem Pattern**
- "I need to forecast a metric" → `time_series_analytics.yaml`
- "I need to clean survey responses" → `survey_data_processing.yaml`
- "I need to optimize resource allocation" → `optimization_modeling.yaml`

**Step 2: Load Skill & Review Capabilities**
- Read YAML to understand available techniques
- Select appropriate capabilities for your problem
- Review when to use each technique

**Step 3: Adapt Generic Workflow to Your Domain**
- Use example use cases as **templates**, not prescriptions
- Replace generic terminology with domain-specific terms
- Apply domain knowledge to technique selection

**Step 4: Implement Using Best Practices**
- Follow data preparation guidelines
- Apply evaluation frameworks
- Avoid documented pitfalls

**Step 5: Validate & Iterate**
- Check against skill's quality criteria
- Perform sensitivity analysis
- Document methodology used

---

## Adapting Skills to Your Project

### Example: Time Series Analytics

**Generic Skill Says**: "Forecast a single metric using only its historical values"

**You Adapt It To**:
- **Telecom**: Forecast daily active users for mobile app
- **Retail**: Forecast weekly sales for product category
- **Finance**: Forecast monthly revenue for business unit
- **Healthcare**: Forecast daily patient admissions to hospital
- **Manufacturing**: Forecast hourly production output for assembly line

**The Workflow is Identical**:
1. Load and visualize data (trend, seasonality, outliers)
2. Decompose to understand components
3. Test stationarity; difference if needed
4. Fit Prophet (handles seasonality automatically)
5. Fit ARIMA as comparison baseline
6. Evaluate on holdout set
7. Generate forecast with uncertainty intervals

**What Changes**: Data source, domain terminology, business context. **What Stays Same**: Methodology, evaluation, best practices.

---

### Example: Survey Data Processing

**Generic Skill Says**: "Match entities across datasets despite name variations"

**You Adapt It To**:
- **Customer surveys**: Match customers across purchase and feedback surveys
- **Employee surveys**: Track employees across annual engagement surveys
- **Academic research**: Match participants across longitudinal study waves
- **Healthcare**: Link patients across different hospital systems
- **CRM**: Deduplicate customer records with typos

**The Workflow is Identical**:
1. Standardize text (uppercase, remove punctuation, trim whitespace)
2. Apply blocking (reduce comparison space)
3. Calculate similarity (Jaro-Winkler for names)
4. Classify matches (threshold or ML-based)
5. Cluster into entities (connected components)
6. Validate (manually review sample, tune thresholds)

**What Changes**: Entity type (customer, employee, patient), matching fields. **What Stays Same**: Algorithm, validation process, precision-recall tradeoffs.

---

### Example: Optimization Modeling

**Generic Skill Says**: "Allocate limited resources to activities to maximize benefit"

**You Adapt It To**:
- **Marketing**: Allocate budget across channels to maximize conversions
- **IT**: Allocate servers across services to maximize throughput
- **Manufacturing**: Allocate labor across product lines to maximize profit
- **Healthcare**: Allocate nurses across departments to maximize coverage
- **Finance**: Allocate capital across investments to maximize return

**The Formulation is Identical**:
```
Decision variables: x_j = amount allocated to activity j
Objective: maximize Σ benefit_j * x_j
Constraints: Σ resource_usage_ij * x_j ≤ resource_limit_i
```

**What Changes**: Definition of "activities", "resources", "benefit". **What Stays Same**: LP formulation, solving approach, sensitivity analysis.

---

## Creating New Skills

### Principles for Generic Skills

**DO:**
- ✅ Focus on **technique** and **methodology**
- ✅ Provide **adaptable workflows** with placeholders
- ✅ Use **generic terminology** (metric, entity, resource, activity)
- ✅ Include **multiple example adaptations** across domains
- ✅ Teach **how to select** techniques (decision trees, when-to-use)

**DON'T:**
- ❌ Hard-code **domain-specific use cases** (cocoa forecasting, nurse scheduling)
- ❌ Use **industry jargon** (SKU, churn, yield, utilization) without explaining
- ❌ Provide **only one example** (limits perceived applicability)
- ❌ Assume **domain knowledge** (e.g., "everyone knows what ARPU means")

### Template Structure for Generic Skills

```yaml
name: skill_name
version: 1.0.0
category: data_science | data_engineering | operations_research

description: >
  Universal [technique area] patterns applicable to ANY [problem class].
  Learn HOW to [solve problem type], not WHAT specific problems to solve.

capabilities:
  - name: capability_name
    description: "What this technique does (domain-agnostic)"
    techniques: [List of specific algorithms/methods]
    when_to_use:
      - "Generic scenario 1 (any domain)"
      - "Generic scenario 2 (any domain)"
    strengths: [Universal strengths]
    limitations: [Universal limitations]
    libraries: [python packages]

methodology_patterns:
  pattern_1:
    description: "Generic problem pattern"
    when_applicable: "Any time you have [generic structure]"
    workflow:
      step_1: "Generic step (adaptable terminology)"
      step_2: "Generic step"
    generic_example: "Generic use case"

example_use_cases:
  - name: generic_use_case
    description: "Generic problem statement"
    data_structure: "Generic columns and format"
    workflow: [Generic steps]
    adaptable_to:
      - "Domain 1 example"
      - "Domain 2 example"
      - "Domain 3 example"

adaptation_guide:
  step_1: "Understand your data structure"
  step_2: "Select appropriate techniques from capabilities"
  step_3: "Customize workflows to your domain"
  step_4: "Apply domain-specific validation"

best_practices: [Universal, domain-agnostic guidelines]
common_pitfalls: [Universal mistakes to avoid]
dependencies: [Python libraries]
references: [Textbooks, papers, online resources]
```

---

## Skill File Structure

Each skill YAML follows this pattern:

### Metadata
```yaml
name: skill_name
version: 1.0.0
category: data_science | data_engineering | operations_research
description: "Universal patterns for [problem class]"
```

### Capabilities
```yaml
capabilities:
  - name: capability_name
    description: "What it does"
    techniques: [algorithms]
    when_to_use: [scenarios]
    strengths: [pros]
    limitations: [cons]
    libraries: [packages]
```

### Methodology Patterns
```yaml
methodology_patterns:
  pattern_1:
    description: "Generic workflow"
    workflow: [steps]
    generic_example: "Adaptable template"
```

### Example Use Cases
```yaml
example_use_cases:
  - name: generic_use_case
    description: "Generic problem"
    workflow: [steps]
    adaptable_to: [domain examples]
```

### Adaptation Guide
```yaml
adaptation_guide:
  step_1: "How to adapt to your domain"
  step_2: "How to select techniques"
  step_3: "How to customize workflows"
```

### Supporting Sections
```yaml
best_practices: [universal guidelines]
common_pitfalls: [mistakes to avoid]
dependencies: [libraries]
references: [resources]
```

---

## Integration with Orchestrator

Skills are loaded by agents during task execution:

### Planning Phase (Architect Agent)
- **Load relevant skills** based on problem pattern (forecast, survey, optimize)
- **Select techniques** appropriate to data and constraints
- **Design workflow** following skill's methodology patterns

### Data Engineering Phase (Data Agent)
- **Load data skills** (survey_data_processing, time_series_analytics)
- **Apply preprocessing** per skill's data preparation guidelines
- **Validate quality** using skill's quality gates

### Development Phase (Developer Agent)
- **Load technical skills** (optimization_modeling, time_series_analytics)
- **Implement models** following skill's example workflows
- **Use recommended libraries** from skill dependencies

### QA Phase (QA Agent)
- **Load all relevant skills** used by other agents
- **Validate against best practices** from skills
- **Check for pitfalls** documented in skills
- **Run evaluation** per skill's metrics frameworks

### Documentation Phase (Documentarian Agent)
- **Reference skills used** in methodology documentation
- **Cite techniques applied** from skill capabilities
- **Document adaptations** made for specific domain

---

## Multi-Skill Tasks

Complex problems often require combining multiple skills:

**Example Task**: "Build a recommendation system for product assortment using customer survey data and sales forecasts"

**Skills Needed**:
1. `survey_data_processing.yaml` → Clean and analyze customer preference surveys
2. `time_series_analytics.yaml` → Forecast demand by product
3. `optimization_modeling.yaml` → Optimize product mix (portfolio selection)

**Orchestration**:
- **Data Agent** loads survey + time series skills → Prepares data
- **Developer Agent** loads optimization skill → Builds recommendation model
- **QA Agent** loads all three skills → Validates end-to-end

---

## Best Practices

### For Using Skills
1. **Start generic, adapt gradually**: Don't force-fit domain specifics early
2. **Read entire skill first**: Understand full capability catalog before diving in
3. **Use adaptation guide**: Follow the skill's own guidance for customization
4. **Document adaptations**: Note how you tailored generic workflow to your domain
5. **Cite techniques**: Reference specific capabilities used (e.g., "Applied Jaro-Winkler fuzzy matching per survey_data_processing capability 3")

### For Creating Skills
1. **Test domain-neutrality**: Can this skill apply to 3+ unrelated industries?
2. **Provide diverse examples**: Show adaptability across domains
3. **Use generic terminology**: "entity" not "customer", "metric" not "revenue"
4. **Include decision trees**: Help users select techniques ("Use X when..., Use Y when...")
5. **Validate with non-experts**: Can someone outside your domain understand and apply it?

---

## FAQs

**Q: Why are skills domain-agnostic instead of industry-specific?**

A: **Reusability and scalability**. A telecom analyst can use the same time series skill as a healthcare analyst. We don't need separate "telecom forecasting" and "healthcare forecasting" skills—the methodology is identical.

**Q: What if my domain has unique requirements not covered by generic skills?**

A: Use the **project knowledge base** (`.claude/knowledge/projects/[your-project]/`) to add domain-specific context. Skills provide methodology; project knowledge provides domain expertise.

**Q: How do I know which skill to use?**

A: **Match problem pattern, not domain**:
- Need to predict future values? → `time_series_analytics.yaml`
- Need to clean survey responses? → `survey_data_processing.yaml`
- Need to optimize allocation? → `optimization_modeling.yaml`

**Q: Can I create domain-specific skills for my industry?**

A: **No**. Keep skills generic. Instead:
- Use generic skills + project-specific knowledge files
- Contribute **new generic patterns** if you discover a reusable methodology
- Create **example adaptations** showing how to apply generic skills to your domain

**Q: What makes a good skill?**

A: **Technique-focused, not domain-focused**:
- Good: "How to apply ARIMA, Prophet, LSTM to ANY time series"
- Bad: "How to forecast agricultural commodity prices"

---

## Roadmap: Future Skills

**Under Consideration** (all domain-agnostic):
- **Geospatial Analytics**: GIS, mapping, spatial optimization for ANY location-based data
- **Recommendation Systems**: Collaborative filtering, content-based (e-commerce, content, etc.)
- **Image Classification**: Computer vision patterns for ANY image recognition task
- **A/B Testing**: Experimental design and analysis for ANY intervention
- **Causal Inference**: Methods for estimating causal effects from observational data
- **Graph Analytics**: Network analysis, community detection, influence propagation

**Key Requirement**: Must be applicable to 3+ unrelated industries.

---

## Contributing

We welcome contributions that **enhance generalizability**:

- ✅ Add **new example adaptations** showing skills applied to new domains
- ✅ Improve **adaptation guides** with better decision frameworks
- ✅ Add **new generic capabilities** to existing skills
- ✅ Create **new domain-agnostic skills** following our template
- ❌ Do NOT add domain-specific use cases or industry jargon

**Contribution Checklist**:
- [ ] Can this be applied to 3+ unrelated domains?
- [ ] Does it use generic terminology?
- [ ] Does it teach **how** (methodology) not **what** (domain solution)?
- [ ] Is the adaptation guide clear?

---

## References

- [YAML Specification](https://yaml.org/spec/1.2/spec.html)
- [Claude Code Orchestrator Manifest](../../CLAUDE.md)
- [Analytics Best Practices](../../knowledge/analytics_best_practices.yaml) - Universal data science patterns
- [Kearney Standards](../../knowledge/kearney_standards.yaml) - Firm-wide quality standards

---

**Maintained by**: Claude Code Orchestrator Team
**Last Updated**: 2025-01-26
**Version**: 2.0.0 (Domain-Agnostic Rewrite)
