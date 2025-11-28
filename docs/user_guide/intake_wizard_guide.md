# Intake Wizard User Guide

**The smart way to start your projects with perfect requirements gathering**

## Overview

The Intake Wizard is an intelligent interview system that helps you gather comprehensive project requirements through guided conversations. Instead of starting with a blank page, you answer structured questions that ensure your project has all the context needed for successful execution.

### What the Intake Wizard Does

- **Guides you through structured questions** tailored to your project type
- **Adapts questions based on your answers** using smart conditional logic
- **Validates your responses** to ensure completeness and accuracy
- **Applies client-specific constraints** automatically
- **Creates a complete project profile** ready for orchestrator workflows

### When to Use the Intake Wizard

- Starting any new consulting project
- Creating presentations, analyses, or ML models
- When you want comprehensive requirement gathering
- Before engaging orchestrator workflows

## Getting Started

### Step 1: Choose Your Project Type

The wizard begins by showing you available project templates:

- **Presentation Content** - For slide decks, reports, and client deliverables
- **Analytics Project** - For data analysis and insights generation
- **ML Model** - For machine learning and predictive modeling
- **Web Application** - For web-based tools and dashboards
- **Supply Chain** - For supply chain optimization projects

Each template includes:
- Estimated completion time
- Number of phases
- Brief description

### Step 2: Complete the Interview

The wizard guides you through several phases of questions:

#### Phase Structure
1. **Project Identity** - Basic project information
2. **Context & Requirements** - Specific to your project type
3. **Technical Specifications** - Implementation details
4. **Deliverables & Timeline** - Output expectations

#### Question Types
You'll encounter various question formats:

- **Text fields** for open-ended responses
- **Multiple choice** for predefined options
- **Number inputs** for quantitative data
- **Date pickers** for timeline information
- **Lists** for multiple items (e.g., data sources, stakeholders)

### Step 3: Review and Submit

Before completion, you can:
- Review all your responses
- Navigate back to edit any phase
- See validation warnings or errors
- Complete the intake to create your project

## Using the Interface

### Navigation

- **Progress Bar** - Shows completion percentage across all phases
- **Phase Indicators** - Visual markers for each phase (completed, current, upcoming)
- **Back/Continue Buttons** - Navigate between phases
- **Save Indicator** - Auto-saves your progress every 30 seconds

### Smart Features

#### Conditional Questions
Questions adapt based on your previous answers:

**Example:** If you select "Client Pitch" for presentation purpose, you'll see questions about:
- Target client information
- Competitive landscape
- Pricing considerations

If you select "Project Report-Out," you'll see questions about:
- Project timeline and phases
- Key findings and recommendations
- Stakeholder communication needs

#### Validation and Help
- **Real-time validation** shows errors as you type
- **Help text** provides guidance for complex questions
- **Required field indicators** (*) show what must be completed
- **Format examples** guide proper input formatting

#### Auto-Save
Your progress is automatically saved:
- Every 30 seconds while typing
- When moving between phases
- Before browser tab closure

### Keyboard Shortcuts

- **Tab/Shift+Tab** - Navigate between fields
- **Enter** - Continue to next question (when valid)
- **Ctrl/Cmd + S** - Manual save (though auto-save is active)

## Project Templates Deep Dive

### Presentation Content Template

**Best for:** Slide decks, client reports, executive briefings

**Key phases:**
1. **Presentation Type** - Determines if this is a pitch, report-out, or update
2. **Project Context** - Background, objectives, and stakeholder information
3. **Content Structure** - Key messages, supporting data, visual preferences
4. **Audience & Delivery** - Target audience analysis and presentation format

**Sample questions:**
- "What is the main objective of this presentation?"
- "Who is your primary audience?"
- "What supporting data or analysis do you have?"
- "What key decisions should the audience make after seeing this?"

### Analytics Project Template

**Best for:** Data analysis, insights generation, reporting dashboards

**Key phases:**
1. **Analysis Objectives** - Research questions and success metrics
2. **Data Sources** - Available datasets and collection methods
3. **Analysis Approach** - Methodologies and technical requirements
4. **Output Specifications** - Deliverable formats and visualization needs

**Sample questions:**
- "What business question are you trying to answer?"
- "What datasets do you have access to?"
- "What level of statistical rigor is required?"
- "Who will consume the analysis results?"

### ML Model Template

**Best for:** Predictive modeling, machine learning applications, AI tools

**Key phases:**
1. **Problem Definition** - Use case and success criteria
2. **Data Assessment** - Training data availability and quality
3. **Model Requirements** - Performance expectations and constraints
4. **Deployment Context** - Integration and operational considerations

**Sample questions:**
- "What business outcome are you trying to predict or optimize?"
- "How much training data do you have available?"
- "What accuracy level is acceptable for production use?"
- "How will the model integrate with existing systems?"

## Advanced Features

### Client-Specific Customization

When you belong to a specific client or organization, the wizard automatically applies:

- **Brand constraints** (colors, fonts, styling preferences)
- **Governance rules** (compliance requirements, approval processes)
- **Default values** (standard methodologies, preferred tools)
- **Custom validation** (organization-specific requirements)

### Template Inheritance

Templates can inherit from base templates, allowing:
- **Consistent question structure** across related project types
- **Organization-specific customization** without duplicating content
- **Rapid template development** by building on proven foundations

### Conditional Logic

Advanced templates use conditional logic to:
- **Show relevant questions only** based on previous answers
- **Skip unnecessary phases** for certain project types
- **Customize validation rules** based on selected options
- **Dynamic question text** that adapts to context

**Example conditions:**
```
If presentation_purpose = "client_pitch"
  Then show questions: target_client, competitive_analysis, pricing_strategy
  And require: market_research_data

If data_sensitivity = "highly_confidential"
  Then apply: enhanced_security_validation
  And show: data_handling_protocols
```

## Best Practices

### Before Starting
- **Gather relevant documents** (requirements, data sources, stakeholder lists)
- **Clarify project objectives** with key stakeholders
- **Review available templates** to choose the best fit
- **Set aside adequate time** (15-45 minutes depending on template)

### During the Interview
- **Be specific and detailed** in your responses
- **Use clear, professional language** (responses may be included in project documentation)
- **Reference specific sources** when mentioning data or requirements
- **Think about edge cases** and potential challenges

### Completing Responses
- **Review all phases** before final submission
- **Check for consistency** across related questions
- **Validate contact information** and dates
- **Ensure completeness** of required fields

## Troubleshooting

### Common Issues

**Q: My session seems stuck loading**
A: Check your internet connection and refresh the browser. Your progress is auto-saved and will be restored.

**Q: I made a mistake in an earlier phase**
A: Use the progress bar or Back button to navigate to any previous phase and make changes.

**Q: Some questions don't seem relevant**
A: The wizard adapts based on your answers. If questions seem irrelevant, check that your earlier responses accurately reflect your project type.

**Q: Validation errors are blocking me**
A: Read the error messages carefully. They provide specific guidance on what information is needed or what format is expected.

### Error Messages

**"This field is required"**
- Fill in the required information before proceeding

**"Invalid format"**
- Check examples in the help text and match the expected format

**"Response too long"**
- Shorten your response to fit within character limits

**"Invalid date format"**
- Use the date picker or format dates as YYYY-MM-DD

### Getting Help

**Within the wizard:**
- Click help icons (?) next to questions for detailed guidance
- Read placeholder text for formatting examples
- Check validation messages for specific requirements

**Need additional support:**
- Contact your project administrator
- Refer to the [API Reference Documentation](../api/intake_api_reference.md)
- Check the [Developer Guide](../developer/creating_intake_templates.md) for template customization

## Next Steps

After completing the intake wizard:

1. **Project Created** - Your responses generate a comprehensive project profile
2. **Orchestrator Ready** - The project is ready for workflow execution
3. **Review Dashboard** - Access your project dashboard to monitor progress
4. **Workflow Execution** - Start the Ready/Set/Go workflow process

### Project Dashboard Features
- **Complete requirement summary** from your intake responses
- **Generated project artifacts** based on your specifications
- **Workflow progress tracking** through Ready, Set, and Go phases
- **Edit intake responses** if requirements change

## Frequently Asked Questions

**Q: How long does the intake process take?**
A: Typically 15-45 minutes depending on template complexity and project scope.

**Q: Can I save my progress and return later?**
A: Yes, the wizard auto-saves every 30 seconds. You can return to complete it anytime within 24 hours.

**Q: Can I change my answers after submission?**
A: During intake, you can freely navigate back to change answers. After completion, contact your administrator to modify project requirements.

**Q: What happens to my responses?**
A: Responses are used to create your project profile and may be included in generated documentation. All data follows your organization's privacy policies.

**Q: Can I reuse responses for similar projects?**
A: While each intake session is unique, you can reference previous project profiles when starting new projects to speed up the process.

**Q: What if my project doesn't fit any template?**
A: Start with the closest template - the orchestrator can adapt to unique requirements. You can also request custom templates from your administrator.

---

*This guide covers the core functionality of the Intake Wizard. For technical implementation details, see the [API Reference Documentation](../api/intake_api_reference.md) and [Developer Guide](../developer/creating_intake_templates.md).*