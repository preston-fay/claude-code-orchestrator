# Client Governance Configuration System

## Overview

The client governance system provides a flexible configuration overlay that allows client-specific quality standards, compliance requirements, and brand constraints to override Kearney's default baseline standards.

**Key Benefits:**
- **Tailored Quality Gates**: Each client can enforce their own code coverage thresholds, security requirements, and documentation standards
- **Compliance Automation**: Automatically enforce GDPR, HIPAA, SOC2, or other regulatory frameworks based on client requirements
- **Brand Consistency**: Apply client-specific design tokens, logos, color restrictions, and presentation templates
- **Transparent Governance**: All governance rules documented in version-controlled YAML files (no hidden policies)

---

## Why Client-Specific Governance?

**Problem**: One-size-fits-all quality standards don't work across diverse client engagements:
- Startup client needs speed → minimal test coverage, no peer review
- Financial services client needs compliance → GDPR enforcement, audit logging, strict PII handling
- High-security client needs validation → security scans, 90%+ test coverage, mandatory peer review

**Solution**: Client governance configs override Kearney defaults on a per-field basis. Only specify what differs from baseline; inherit everything else.

---

## Directory Structure

```
clients/
├── .schema/
│   └── governance.schema.json      # JSON Schema for validation
├── kearney-default/
│   └── governance.yaml             # Baseline standards for ALL projects
├── example-client/
│   └── governance.yaml             # Fictional example showing all options
├── <client-name>/
│   └── governance.yaml             # Client-specific overrides
└── README.md                       # This file
```

**File Purposes:**
- **`.schema/governance.schema.json`**: Defines valid governance structure, data types, and constraints
- **`kearney-default/governance.yaml`**: Baseline quality standards that apply to all Kearney projects
- **`example-client/governance.yaml`**: Comprehensive example with inline comments explaining every field
- **`<client-name>/governance.yaml`**: Client-specific overrides (inherits from kearney-default)

---

## How Governance Loading Works

### Precedence Rules (Highest to Lowest)

1. **Client-specific config** (`clients/<client-name>/governance.yaml`)
   - Overrides both Kearney defaults and hardcoded orchestrator defaults
   - Only specify fields that differ from baseline

2. **Kearney default config** (`clients/kearney-default/governance.yaml`)
   - Applies to ALL projects unless client overrides
   - Represents Kearney's standard quality expectations

3. **Hardcoded orchestrator defaults**
   - Fallback values if no config file specifies a field
   - Minimal, permissive settings (suitable for prototypes/demos)

### Loading Process

```python
# Simplified example of governance loading logic
def load_governance(client_name: str) -> dict:
    # Load schemas and defaults
    schema = load_json("clients/.schema/governance.schema.json")
    kearney_defaults = load_yaml("clients/kearney-default/governance.yaml")

    # Load client-specific config (if exists)
    client_config_path = f"clients/{client_name}/governance.yaml"
    client_config = load_yaml(client_config_path) if exists(client_config_path) else {}

    # Merge: client overrides kearney_defaults
    governance = deep_merge(kearney_defaults, client_config)

    # Validate against JSON Schema
    validate(governance, schema)

    return governance
```

**Deep Merge Behavior**: Client config overrides only specified fields; unspecified fields inherit from Kearney defaults.

**Example**:
```yaml
# clients/my-client/governance.yaml (client only specifies what differs)
client_name: "My Client"
quality_gates:
  min_test_coverage: 90  # Override: higher than Kearney default (70)
  require_security_scan: true  # Override: enable security scanning
# All other quality_gates fields inherit from kearney-default
# All compliance, brand_constraints, etc. inherit from kearney-default
```

**Result after merge**:
- `min_test_coverage`: 90 (from client config)
- `require_security_scan`: true (from client config)
- `min_hygiene_score`: 85 (from kearney-default, not overridden)
- `require_linting`: true (from kearney-default, not overridden)
- `max_complexity`: 10 (from kearney-default, not overridden)

---

## When to Create Client Configs

### Always Create for:
1. **New Client Engagements**: Create config when contract is signed, before project kickoff
2. **Regulated Industries**: Clients in finance, healthcare, government (GDPR, HIPAA, FedRAMP requirements)
3. **Brand-Sensitive Clients**: Clients with strict design guidelines, logo requirements, or forbidden terminology
4. **High-Security Environments**: Clients requiring security scans, encryption, audit logging

### Consider Creating for:
1. **Clients with Custom Workflows**: Non-standard deployment windows, approval thresholds, or release processes
2. **Multi-Project Clients**: Single governance config applies to all projects for that client (consistency)
3. **Compliance Demonstrability**: Client needs audit trail showing governance was enforced

### Don't Bother for:
1. **One-off Prototypes**: Use kearney-default (sufficient for internal demos)
2. **Kearney Internal Projects**: kearney-default already represents our standards
3. **Clients with No Special Requirements**: If defaults work, don't add overhead

---

## Common Override Scenarios

### Scenario 1: High-Security Client (Financial Services)

**Requirements**: GDPR compliance, 90% test coverage, security scanning, audit logging, strict PII handling

```yaml
# clients/secure-bank/governance.yaml
client_name: "Secure Bank Corp"
engagement_id: "ENG-2024-042"
effective_date: "2024-03-01"

quality_gates:
  min_test_coverage: 90  # Override: higher than default
  require_security_scan: true  # Override: enable SAST/dependency scanning
  require_peer_review: true  # Override: all code must be reviewed

compliance:
  frameworks:
    - "SOC2"
    - "GDPR"  # Add GDPR to SOC2 baseline
  pii_handling: "strict"  # Override: encrypt all PII, anonymize for analytics
  encryption_at_rest: true  # Override: enable for sensitive data
  audit_logging: true  # Override: maintain detailed access logs
  anonymization_required: true  # Override: GDPR Article 25 compliance

notifications:
  quality_gate_failure:
    - "qa-lead@kearney.com"
    - "client-pm@securebank.com"
  deployment_notifications:
    - "ops@securebank.com"

# All other fields inherit from kearney-default
```

**What changed**: 6 quality/compliance fields overridden, added notifications. All brand/deployment/documentation settings inherited.

---

### Scenario 2: Fast-Moving Startup Client

**Requirements**: Speed over perfection, minimal process overhead, rapid iteration

```yaml
# clients/agile-startup/governance.yaml
client_name: "Agile Startup Inc"
engagement_id: "ENG-2024-089"
effective_date: "2024-05-15"

quality_gates:
  min_hygiene_score: 70  # Override: lower than default (allow some tech debt)
  min_test_coverage: 50  # Override: lower coverage acceptable for MVP
  require_peer_review: false  # Keep default: no review required (speed)

deployment:
  environments:
    - "development"
    - "production"  # Skip staging (move fast)
  require_approval: false  # Override: no manual approval gates
  rollback_required: false  # Keep default: no automated rollback needed

documentation:
  min_documentation_score: 50  # Override: lower doc standards for MVP
  require_runbook: false  # Keep default: no ops runbook yet

# All compliance, brand_constraints inherit from kearney-default
```

**What changed**: Relaxed quality gates and deployment requirements. Compliance and brand settings inherited.

---

### Scenario 3: Brand-Conscious Client (CPG Company)

**Requirements**: Strict brand guidelines, custom fonts, competitor color restrictions, co-branding

```yaml
# clients/brand-corp/governance.yaml
client_name: "Brand Corp International"
engagement_id: "ENG-2024-061"
effective_date: "2024-04-10"

brand_constraints:
  theme_path: "clients/brand-corp/theme.json"  # Override: custom design tokens
  custom_fonts:
    - "Helvetica Neue"
    - "Brand Corp Sans"  # Custom licensed font
  color_restrictions:
    - "#FF0000"  # Competitor A primary color
    - "#0000FF"  # Competitor B primary color
  logo_path: "clients/brand-corp/logo.svg"  # Override: add client logo
  forbid_terms:
    - "Competitor A"
    - "Competitor B"
    - "legacy system"  # Sensitive internally
  require_disclaimers: true  # Override: add legal disclaimers to all deliverables
  presentation_template: "clients/brand-corp/template.pptx"  # Override: custom PowerPoint

# All quality_gates, compliance, deployment, documentation inherit from kearney-default
```

**What changed**: Extensive brand customization. All technical standards inherited from defaults.

---

### Scenario 4: Regulated Healthcare Client (HIPAA)

**Requirements**: HIPAA compliance, PHI handling, geographic restrictions, encryption, no cloud processing

```yaml
# clients/healthcare-co/governance.yaml
client_name: "Healthcare Co"
engagement_id: "ENG-2024-033"
effective_date: "2024-02-20"

quality_gates:
  require_security_scan: true  # Override: enable security scanning
  require_data_classification: true  # Override: all data must be classified

compliance:
  frameworks:
    - "SOC2"
    - "HIPAA"  # Add HIPAA to baseline
  pii_handling: "strict"  # Override: PHI is more sensitive than PII
  data_retention_days: 2555  # Override: 7 years (HIPAA requirement)
  encryption_at_rest: true  # Override: required for PHI
  encryption_in_transit: true  # Keep default: always required
  audit_logging: true  # Override: required for HIPAA
  anonymization_required: true  # Override: de-identify PHI for analytics
  geographic_restrictions:
    - "RU"  # No data processing in Russia
    - "CN"  # No data processing in China

custom_rules:
  - rule_id: "no-cloud-processing"
    description: "PHI must not be processed in third-party cloud environments"
    severity: "error"
    check_type: "manual_review"
  - rule_id: "phi-access-logging"
    description: "All PHI access must be logged with user ID and timestamp"
    severity: "error"
    check_type: "code_pattern"
    pattern: "access_phi\\(.*\\).*log\\("

# All brand_constraints, deployment, documentation inherit from kearney-default
```

**What changed**: Added HIPAA framework, strict data controls, custom compliance rules. Brand and deployment inherited.

---

## Field-by-Field Override Reference

### Quality Gates (`quality_gates`)

| Field | Kearney Default | Common Overrides | When to Override |
|-------|-----------------|------------------|------------------|
| `min_hygiene_score` | 85 | 70 (startup), 95 (enterprise) | Client has different cleanliness standards |
| `require_security_scan` | false | true (finance, healthcare) | Client-facing app or sensitive data |
| `require_data_classification` | false | true (regulated industries) | Multiple data sensitivity levels |
| `min_test_coverage` | 70 | 50 (MVP), 90 (production) | Project maturity and risk tolerance |
| `require_type_hints` | false | true (large codebases) | Long-lived project or team size >3 |
| `require_linting` | true | false (never recommended) | N/A - always enforce linting |
| `max_complexity` | 10 | 5 (strict), 15 (lenient) | Code maintainability standards |
| `require_peer_review` | false | true (team projects) | Multiple developers or client-facing code |

### Compliance (`compliance`)

| Field | Kearney Default | Common Overrides | When to Override |
|-------|-----------------|------------------|------------------|
| `frameworks` | ["SOC2"] | Add GDPR, HIPAA, PCI-DSS | Client industry or data type |
| `pii_handling` | "standard" | "strict" (GDPR), "none" | PII sensitivity and volume |
| `data_retention_days` | 365 | 90, 2555 (HIPAA: 7 years) | Client contract or regulations |
| `encryption_at_rest` | false | true (PII, PHI, confidential) | Data sensitivity classification |
| `encryption_in_transit` | true | false (never recommended) | N/A - always encrypt transit |
| `audit_logging` | false | true (SOC2 evidence, forensics) | Compliance needs or security incidents |
| `anonymization_required` | false | true (GDPR, multi-party sharing) | Privacy regulations or data sharing |
| `geographic_restrictions` | [] | ["RU", "CN"] (data sovereignty) | Client legal or contractual requirements |

### Brand Constraints (`brand_constraints`)

| Field | Kearney Default | Common Overrides | When to Override |
|-------|-----------------|------------------|------------------|
| `theme_path` | "design_system/web/tokens.css" | "clients/<name>/theme.json" | Client has design system |
| `custom_fonts` | [] | ["Client Sans", "Client Serif"] | Brand guidelines specify fonts |
| `color_restrictions` | [] | ["#FF0000", "#00FF00"] | Avoid competitor colors |
| `logo_path` | "" | "clients/<name>/logo.svg" | Co-branding required |
| `forbid_terms` | [] | ["competitor name", "legacy"] | Sensitive terminology |
| `require_disclaimers` | false | true (legal, liability) | Client legal requirement |
| `presentation_template` | "" | "clients/<name>/template.pptx" | Custom PowerPoint template |

### Deployment (`deployment`)

| Field | Kearney Default | Common Overrides | When to Override |
|-------|-----------------|------------------|------------------|
| `environments` | ["development", "production"] | Add "staging", "uat" | Client has UAT process |
| `require_approval` | false | true (production systems) | Client-managed deployments |
| `approval_threshold` | "tech-lead" | "client-stakeholder" | Client approval required |
| `deployment_window` | null | {"days": ["Saturday"], "hours_utc": "02:00-06:00"} | Avoid business hours downtime |
| `rollback_required` | false | true (production systems) | High-availability requirements |
| `canary_required` | false | true (high-traffic apps) | Gradual rollout needed |

### Documentation (`documentation`)

| Field | Kearney Default | Common Overrides | When to Override |
|-------|-----------------|------------------|------------------|
| `require_adr` | true | false (never recommended) | N/A - always document decisions |
| `require_data_dictionary` | false | true (analytics projects) | Complex data sources |
| `min_documentation_score` | 70 | 50 (MVP), 90 (handoff) | Project maturity |
| `require_runbook` | false | true (production systems) | Operational handoff needed |
| `require_user_guide` | false | true (non-technical users) | End-user facing tools |
| `language` | "en" | "es", "fr", "de", "zh" | Client language preference |
| `require_code_comments` | true | false (never recommended) | N/A - always comment complex logic |
| `api_documentation_format` | "Markdown" | "OpenAPI", "Swagger" | API-first projects |

### Notifications (`notifications`)

| Field | Kearney Default | Common Overrides | When to Override |
|-------|-----------------|------------------|------------------|
| `checkpoint_completion` | [] | ["pm@client.com", "lead@kearney.com"] | Client PM wants updates |
| `quality_gate_failure` | [] | ["qa-lead@kearney.com"] | QA team monitors failures |
| `deployment_notifications` | [] | ["ops@client.com"] | Client ops team needs alerts |
| `slack_webhook` | "" | "https://hooks.slack.com/..." | Team uses Slack |

---

## Validation

### Validate Config Before Using

**Step 1: Check YAML Syntax**
```bash
# Ensure valid YAML (no syntax errors)
python -c "import yaml; yaml.safe_load(open('clients/my-client/governance.yaml'))"
```

**Step 2: Validate Against JSON Schema**
```python
import json
import yaml
from jsonschema import validate, ValidationError

# Load schema and client config
schema = json.load(open("clients/.schema/governance.schema.json"))
client_config = yaml.safe_load(open("clients/my-client/governance.yaml"))

# Validate
try:
    validate(instance=client_config, schema=schema)
    print("✅ Config is valid")
except ValidationError as e:
    print(f"❌ Validation error: {e.message}")
```

**Step 3: Test Governance Loading**
```python
# Test that orchestrator can load and merge config
from orchestrator.governance import load_governance

governance = load_governance("my-client")
print(f"Loaded governance for: {governance['client_name']}")
print(f"Min test coverage: {governance['quality_gates']['min_test_coverage']}")
```

### Common Validation Errors

**Error 1: Invalid enum value**
```yaml
compliance:
  pii_handling: "very-strict"  # ❌ Invalid (must be: strict, standard, minimal, none)
```
**Fix**: Use valid enum value from schema

**Error 2: Missing required field**
```yaml
# ❌ Missing required field: client_name
quality_gates:
  min_test_coverage: 80
```
**Fix**: Add `client_name` (required by schema)

**Error 3: Invalid regex pattern**
```yaml
custom_rules:
  - rule_id: "my-rule"
    pattern: "[invalid regex (("  # ❌ Invalid regex
```
**Fix**: Test regex pattern before adding to config

---

## Best Practices

### DO:
- ✅ **Start from example**: Copy `example-client/governance.yaml`, delete irrelevant sections
- ✅ **Override minimally**: Only specify fields that differ from kearney-default
- ✅ **Document rationale**: Add inline comments explaining WHY fields were overridden
- ✅ **Validate before commit**: Run JSON Schema validation to catch errors early
- ✅ **Version control**: Commit governance configs to track changes over engagement lifecycle
- ✅ **Review with client**: Share governance config during kickoff (transparency)

### DON'T:
- ❌ **Copy entire kearney-default**: Only override what differs (maintainability)
- ❌ **Hardcode secrets**: Use environment variables for Slack webhooks, API keys
- ❌ **Relax security defaults**: encryption_in_transit, require_linting should stay true
- ❌ **Skip validation**: Invalid configs cause orchestrator runtime errors
- ❌ **Create one-off configs**: Reuse configs across projects for same client (consistency)

---

## FAQ

### Q: What if client doesn't need custom governance?
**A**: Don't create a client config. Kearney defaults will apply automatically.

### Q: Can I override just one field?
**A**: Yes! That's the point. Only specify fields that differ from baseline.

### Q: What happens if I specify an invalid value?
**A**: Orchestrator will fail at startup with JSON Schema validation error. Fix config and retry.

### Q: Can I create governance for internal Kearney projects?
**A**: Usually not needed (kearney-default represents our standards). Create config only if project has unique requirements (e.g., open-source project with different quality gates).

### Q: How do I add a new compliance framework not in the schema?
**A**: Update `clients/.schema/governance.schema.json` to add new enum value to `compliance.frameworks`. Submit PR with justification.

### Q: Can governance change mid-project?
**A**: Yes. Update `governance.yaml` and commit. Orchestrator reloads config at each checkpoint. Use `effective_date` field to document when changes took effect.

### Q: What if client and Kearney default conflict?
**A**: Client config always wins (highest precedence). Document conflicts in inline comments.

### Q: Do I need separate configs for multiple projects with same client?
**A**: No. One client config applies to all projects for that client. If project needs unique rules, use project-specific overrides (future feature).

---

## Troubleshooting

### Issue: "Validation error: 'client_name' is a required property"
**Cause**: Client config missing required `client_name` field
**Fix**: Add `client_name: "Your Client Name"` at top of config

### Issue: "Validation error: 'very-strict' is not one of ['strict', 'standard', 'minimal', 'none']"
**Cause**: Invalid enum value for `pii_handling`
**Fix**: Use valid value from schema (see `clients/.schema/governance.schema.json`)

### Issue: "Config file not found: clients/my-client/governance.yaml"
**Cause**: Typo in client name or file doesn't exist
**Fix**: Verify client directory exists and filename is exactly `governance.yaml`

### Issue: "Deep merge failed: conflicting types for field 'quality_gates'"
**Cause**: Client config has wrong type for field (e.g., string instead of object)
**Fix**: Check schema for correct type, fix client config

### Issue: "Governance loaded but min_test_coverage is 70 (expected 90)"
**Cause**: Client config not overriding field correctly (possible indentation error)
**Fix**: Check YAML indentation, ensure field is under correct parent object

---

## Example Workflow: Creating Config for New Client

**Step 1: Copy Example Template**
```bash
# Create client directory
mkdir -p clients/new-client

# Copy example as starting point
cp clients/example-client/governance.yaml clients/new-client/governance.yaml
```

**Step 2: Customize for Client**
```bash
# Edit config (delete irrelevant sections, override necessary fields)
# Example: High-security financial client
vim clients/new-client/governance.yaml
```

```yaml
client_name: "New Financial Client"
engagement_id: "ENG-2025-015"
effective_date: "2025-02-01"

quality_gates:
  min_test_coverage: 90  # Override: higher than default
  require_security_scan: true  # Override: enable SAST
  require_peer_review: true  # Override: all code reviewed

compliance:
  frameworks:
    - "SOC2"
    - "PCI-DSS"  # Add: credit card data
  pii_handling: "strict"  # Override
  encryption_at_rest: true  # Override
  audit_logging: true  # Override

# Delete all other sections (inherit from kearney-default)
```

**Step 3: Validate**
```bash
# Validate YAML syntax
python -c "import yaml; yaml.safe_load(open('clients/new-client/governance.yaml'))"

# Validate against schema
python scripts/validate_governance.py clients/new-client/governance.yaml
```

**Step 4: Test Loading**
```python
from orchestrator.governance import load_governance
gov = load_governance("new-client")
assert gov["quality_gates"]["min_test_coverage"] == 90
print("✅ Governance loaded successfully")
```

**Step 5: Commit and Document**
```bash
git add clients/new-client/governance.yaml
git commit -m "feat: add governance config for New Financial Client

- 90% test coverage requirement
- PCI-DSS compliance
- Security scanning and audit logging enabled

Effective: 2025-02-01"
```

**Step 6: Review with Client (Optional)**
- Share `governance.yaml` during project kickoff
- Explain quality gates and compliance controls
- Adjust based on client feedback

---

## Related Documentation

- **JSON Schema Reference**: `clients/.schema/governance.schema.json` (complete field definitions)
- **Example Client Config**: `clients/example-client/governance.yaml` (shows all available options)
- **Kearney Defaults**: `clients/kearney-default/governance.yaml` (baseline standards)
- **ADR-001**: Multi-Agent Orchestration (how governance integrates with checkpoints)
- **Orchestrator Documentation**: `docs/orchestrator_guide.md` (governance loading internals)

---

## Contributing

### Adding New Governance Fields

1. **Update JSON Schema**: Add new field to `clients/.schema/governance.schema.json`
2. **Update Kearney Default**: Add default value to `clients/kearney-default/governance.yaml`
3. **Update Example**: Add example value with comments to `clients/example-client/governance.yaml`
4. **Update README**: Document new field in "Field-by-Field Override Reference" section
5. **Update Orchestrator**: Implement governance enforcement logic for new field
6. **Test**: Validate that new field is loaded correctly and enforced by orchestrator

### Updating Kearney Defaults

**When to update**:
- Kearney adopts new firm-wide standard (e.g., new compliance framework)
- Industry best practices change (e.g., higher test coverage expectations)
- New technology capabilities (e.g., better security scanning tools)

**Process**:
1. Propose change in ADR (Architecture Decision Record)
2. Get consensus from Kearney leadership
3. Update `clients/kearney-default/governance.yaml`
4. Update `effective_date` field
5. Notify all active projects (existing client configs may need updates)
6. Commit with detailed explanation in commit message

---

**Last Updated**: 2025-01-26
**Maintainer**: Kearney Data & Analytics Team
**Questions**: Contact data-platform@kearney.com
