# Project Constitution: {{project_name}}

> **Purpose:** This constitution establishes the fundamental principles, standards, and guardrails that govern all decisions and deliverables for this project. All agents, code, and artifacts must adhere to these principles.

**Version:** {{version}}
**Created:** {{created_at}}
**Last Updated:** {{updated_at}}

---

## 🎯 Core Principles

### Mission Statement
{{mission_statement}}

### Values
{{#each values}}
- **{{this.name}}**: {{this.description}}
{{/each}}

---

## 📐 Code Quality Standards

### Mandatory Requirements
{{#each code_quality.mandatory}}
- {{this}}
{{/each}}

### Code Style
{{#each code_quality.style}}
- {{this}}
{{/each}}

### Testing Requirements
{{#each code_quality.testing}}
- {{this}}
{{/each}}

### Documentation Requirements
{{#each code_quality.documentation}}
- {{this}}
{{/each}}

---

## 🎨 User Experience (UX) Principles

### Design Consistency
{{#each ux_principles.design}}
- {{this}}
{{/each}}

### Performance Standards
{{#each ux_principles.performance}}
- {{this}}
{{/each}}

### Accessibility
{{#each ux_principles.accessibility}}
- {{this}}
{{/each}}

---

## 🔒 Security & Privacy

### Security Standards
{{#each security.standards}}
- {{this}}
{{/each}}

### Privacy Requirements
{{#each security.privacy}}
- {{this}}
{{/each}}

### Secrets Management
{{#each security.secrets}}
- {{this}}
{{/each}}

---

## 📊 Data Principles

### Data Quality
{{#each data_principles.quality}}
- {{this}}
{{/each}}

### Data Governance
{{#each data_principles.governance}}
- {{this}}
{{/each}}

### Data Privacy
{{#each data_principles.privacy}}
- {{this}}
{{/each}}

---

## 🚫 Forbidden Practices

### Never Do This
{{#each forbidden.practices}}
- ❌ **{{this.practice}}**: {{this.reason}}
{{/each}}

### Technologies to Avoid
{{#each forbidden.technologies}}
- ❌ **{{this}}**
{{/each}}

### Anti-Patterns
{{#each forbidden.antipatterns}}
- ❌ **{{this.pattern}}**: {{this.why}}
{{/each}}

---

## ✅ Required Practices

### Always Do This
{{#each required.practices}}
- ✅ **{{this.practice}}**: {{this.reason}}
{{/each}}

### Technology Standards
{{#each required.technologies}}
- ✅ **{{this.name}}**: {{this.rationale}}
{{/each}}

---

## 🎓 Kearney Standards

### RAISE Framework Compliance
{{#if kearney.raise_compliance}}
This project must adhere to Kearney's RAISE framework:
- **R**igorous: Evidence-based decisions, validated assumptions
- **A**ctionable: Deliverables drive concrete business actions
- **I**nsightful: Deep understanding beyond surface observations
- **S**tructured: Clear methodology, reproducible analysis
- **E**ngaging: Compelling storytelling for C-suite audiences
{{/if}}

### Brand Compliance
{{#each kearney.brand_requirements}}
- {{this}}
{{/each}}

### Client-Specific Requirements
{{#each kearney.client_requirements}}
- {{this}}
{{/each}}

---

## 📋 Phase-Specific Guidelines

### Planning Phase
{{#each phase_guidelines.planning}}
- {{this}}
{{/each}}

### Data Engineering Phase
{{#each phase_guidelines.data_engineering}}
- {{this}}
{{/each}}

### Development Phase
{{#each phase_guidelines.development}}
- {{this}}
{{/each}}

### QA Phase
{{#each phase_guidelines.qa}}
- {{this}}
{{/each}}

### Documentation Phase
{{#each phase_guidelines.documentation}}
- {{this}}
{{/each}}

---

## 🔄 Amendment Process

This constitution can be amended through the following process:

1. **Proposal**: Document proposed change with rationale
2. **Review**: Consensus agent reviews for conflicts with client governance
3. **Approval**: Product owner or tech lead approves
4. **Documentation**: Update this constitution with version bump
5. **Communication**: Notify all team members

### Amendment History
{{#each amendments}}
- **{{this.version}}** ({{this.date}}): {{this.description}}
{{/each}}

---

## 📚 References

### Related Documents
- Project Intake: `intake/{{project_name}}.intake.yaml`
- Client Governance: `clients/{{client_name}}/governance.yaml`
- Architecture Decisions: `.claude/decisions/`
- Knowledge Base: `.claude/knowledge/`

### Standards & Frameworks
{{#each references.standards}}
- [{{this.name}}]({{this.url}})
{{/each}}

---

**Enforcement:** This constitution is enforced through:
- Preflight checks (orchestrator blocks execution if violated)
- QA agent validation (constitution compliance testing)
- CI/CD gates (automated linting and checks)
- Code review (Reviewer agent checks adherence)

**Status:** {{status}}
**Approved By:** {{approved_by}}
**Approval Date:** {{approval_date}}
