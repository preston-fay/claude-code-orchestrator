# Creating Excel/Word Intake Forms

## Overview

While the Markdown form (`PROJECT_INTAKE_FORM.md`) is recommended for version control,
you can create Excel or Word versions for stakeholders who prefer familiar tools.

---

## Option 1: Excel Intake Form

### Structure

Create an Excel workbook with multiple sheets:

**Sheet 1: Instructions**
- How to fill out the form
- Required vs. optional fields
- Examples of good success criteria
- Link to orchestrator documentation

**Sheet 2: Project Basics**
| Field | Value | Notes |
|-------|-------|-------|
| Project Name | | kebab-case |
| Project Type | [Dropdown: ML, Analytics, Web App, Service, CLI, Library] | |
| Description | | 1-2 sentences |
| Version | 0.1.0 | |

**Sheet 3: Goals & Success Criteria**
| Goal Type | Goal | Measurable? | Metric | Target |
|-----------|------|-------------|--------|--------|
| Primary | | ☐ | | |
| Primary | | ☐ | | |
| Success Criterion | | ☐ | | |
| Success Criterion | | ☐ | | |

**Sheet 4: Stakeholders**
| Role | Name | Email | Availability |
|------|------|-------|--------------|
| Product Owner | | | |
| Technical Lead | | | |

**Sheet 5: Constraints**
| Constraint Type | Value | Notes |
|-----------------|-------|-------|
| Timeline - Start Date | | |
| Timeline - MVP | | |
| Budget - Total | | |

**Sheet 6: Technology**
| Category | Technology | Required/Preferred/Avoid |
|----------|------------|-------------------------|
| Language | Python | Preferred |
| Framework | | |

**Sheet 7: Data Sources** (for ML/analytics)
| Source Name | Type | Volume | Sensitivity | Update Frequency |
|-------------|------|--------|-------------|------------------|
| | | | | |

**Sheet 8: ML/Analytics Config** (if applicable)
| Field | Value |
|-------|-------|
| Use Cases | |
| Model Types | |
| Latency Requirement | |

**Sheet 9: Testing & QA**
| Field | Value |
|-------|-------|
| Coverage Target | 80% |
| Test Types | |

**Sheet 10: Security**
| Field | Value |
|-------|-------|
| Vault Required? | Yes/No |
| Compliance | |

**Sheet 11: Risk Register**
| Risk | Severity | Likelihood | Mitigation |
|------|----------|------------|------------|
| | | | |

**Sheet 12: Orchestration Settings**
| Setting | Value |
|---------|-------|
| Enabled Agents | |
| Approval Gates | |

**Sheet 13: Summary & Review**
- Auto-calculated completeness percentage
- List of missing required fields
- Validation errors

### Excel Features to Use

#### Data Validation
- **Dropdowns** for project type, severity levels, compliance types
- **Date pickers** for timeline fields
- **Number validation** for coverage percentages (0-100)

#### Conditional Formatting
- **Red highlight** for empty required fields
- **Green highlight** for measurable success criteria
- **Yellow highlight** for vague criteria

#### Formulas
```excel
# Completeness percentage
=COUNTA(required_fields) / COUNTIF(required_fields, "<>")

# Success criteria measurability check
=IF(OR(ISNUMBER(SEARCH(">=", A2)), ISNUMBER(SEARCH(">", A2)), ISNUMBER(SEARCH("<=", A2)), ISNUMBER(SEARCH("<", A2))), "Measurable", "Vague - Add Number!")

# Validate email format
=IF(ISERROR(FIND("@", A2)), "Invalid Email", "OK")
```

#### Templates
- Create drop-down templates for common project types
- "Load ML Template" button → pre-fills ML-specific fields

### Excel Macro (VBA) for YAML Export

```vba
Sub ExportToYAML()
    Dim yamlContent As String
    Dim filePath As String

    ' Build YAML content
    yamlContent = "project:" & vbNewLine
    yamlContent = yamlContent & "  name: " & Range("B2").Value & vbNewLine
    yamlContent = yamlContent & "  type: " & LCase(Range("B3").Value) & vbNewLine
    yamlContent = yamlContent & "  description: " & Range("B4").Value & vbNewLine
    ' ... continue for all fields ...

    ' Save to file
    filePath = ThisWorkbook.Path & "\intake\" & Range("B2").Value & ".intake.yaml"
    Open filePath For Output As #1
    Print #1, yamlContent
    Close #1

    MsgBox "Intake YAML exported to: " & filePath
End Sub
```

**Add Button:**
1. Insert → Shapes → Button
2. Assign macro `ExportToYAML`
3. Label: "Export to intake.yaml"

### Template Download

Create the Excel file:
```bash
# Use Python to generate Excel template
python scripts/generate_excel_intake_template.py
```

Or manually:
1. Open Excel
2. Create sheets as described above
3. Add data validation, formulas, conditional formatting
4. Save as `Project_Intake_Template.xlsx`
5. Protect sheets (except input cells)

---

## Option 2: Word Intake Form

### Structure

Create a Word document with:

**Title Page**
- Project Name
- Date
- Prepared By

**Table of Contents** (auto-generated)

**Section 1: Instructions**
- How to use this form
- Required fields (marked with *)
- Tips for success criteria

**Section 2-14: Same sections as Markdown form**
- Use tables for structured data
- Use form fields for easy filling
- Use checkboxes for Yes/No, multi-select

### Word Features to Use

#### Form Controls
1. Enable Developer tab: File → Options → Customize Ribbon → Check "Developer"
2. Insert form controls:
   - **Text fields** for names, descriptions
   - **Dropdown lists** for project type, severity
   - **Checkboxes** for compliance, test types
   - **Date pickers** for timelines

#### Styles
- **Heading 1**: Section titles
- **Heading 2**: Subsection titles
- **Table Grid**: For structured data
- **Intense Quote**: For examples and tips

#### Content Controls
```
1. Place cursor where field should go
2. Developer Tab → Rich Text Content Control
3. Click Properties
4. Set title, tag, placeholder text
5. Lock control (can edit content only)
```

#### Table Templates
**Success Criteria Table:**
| Success Criterion | Metric | Target | Measurement Method |
|-------------------|--------|--------|-------------------|
| [Type here] | [Type here] | [Type here] | [Type here] |

Copy this table template for each section.

### Word-to-YAML Conversion Script

```python
# scripts/word_to_yaml.py
from docx import Document
import yaml

def extract_from_word(docx_path):
    doc = Document(docx_path)

    intake = {
        'project': {},
        'goals': {},
        'stakeholders': {},
        # ... etc
    }

    # Extract from tables
    for table in doc.tables:
        # Parse table data into intake dict
        pass

    # Write YAML
    with open('intake/project.intake.yaml', 'w') as f:
        yaml.dump(intake, f)

if __name__ == '__main__':
    extract_from_word('Project_Intake_Form.docx')
```

**Usage:**
```bash
python scripts/word_to_yaml.py
# Creates intake/project.intake.yaml
```

### Template Download

1. Create Word document with sections
2. Add form controls
3. Protect document: Review → Restrict Editing → Allow only filling in forms
4. Save as `Project_Intake_Template.docx`

---

## Option 3: Google Forms → YAML

### Advantages
- Easy to share link
- Auto-collects responses in spreadsheet
- Can embed in company portal
- Version control via form revisions

### Setup

1. **Create Google Form** with sections matching intake structure
2. **Configure question types:**
   - Short answer: Names, descriptions
   - Paragraph: Detailed explanations
   - Multiple choice: Project type
   - Checkboxes: Compliance, test types
   - Linear scale: Coverage percentage
   - Grid: Risk matrix

3. **Link to Google Sheets** for responses

4. **Use Google Apps Script** to convert to YAML:

```javascript
function exportToYAML() {
  var sheet = SpreadsheetApp.getActiveSpreadsheet().getSheetByName('Form Responses 1');
  var data = sheet.getDataRange().getValues();

  // Last response (latest row)
  var row = data[data.length - 1];

  var yaml = "project:\n";
  yaml += "  name: " + row[1] + "\n";  // Assuming column B is project name
  yaml += "  type: " + row[2].toLowerCase() + "\n";
  // ... continue building YAML ...

  // Save to Google Drive
  var file = DriveApp.createFile('intake.yaml', yaml, MimeType.PLAIN_TEXT);
  Logger.log('YAML saved: ' + file.getUrl());
}
```

5. **Add menu button** to form:

```javascript
function onOpen() {
  var ui = SpreadsheetApp.getUi();
  ui.createMenu('Orchestrator')
    .addItem('Export to intake.yaml', 'exportToYAML')
    .addToUi();
}
```

---

## Option 4: Typeform / JotForm (No-Code)

### Advantages
- Beautiful UX
- Conditional logic (show ML questions only if ML project)
- Integration with Slack, email
- Analytics on response quality

### Setup

1. **Create Typeform account** (or JotForm)
2. **Import questions** from Markdown form
3. **Add conditional logic:**
   - If "Project Type" = "ML" → Show ML questions
   - If "Data Sensitivity" = "Confidential" → Show compliance questions
4. **Configure integrations:**
   - Webhook → Your server converts to YAML
   - Email → Send responses to team
   - Slack → Notify when form submitted

### Webhook Handler

```python
# Flask app to receive Typeform webhook
from flask import Flask, request
import yaml

app = Flask(__name__)

@app.route('/typeform-webhook', methods=['POST'])
def typeform_webhook():
    data = request.json

    # Extract form responses
    answers = data['form_response']['answers']

    # Build intake dict
    intake = {}
    for answer in answers:
        field_id = answer['field']['id']
        # Map field_id to intake schema
        # intake['project']['name'] = ...

    # Write YAML
    with open('intake/project.intake.yaml', 'w') as f:
        yaml.dump(intake, f)

    return 'OK', 200

if __name__ == '__main__':
    app.run()
```

---

## Comparison Matrix

| Format | Ease of Use | Version Control | Collaboration | Auto-Validation | YAML Export |
|--------|-------------|-----------------|---------------|-----------------|-------------|
| **Markdown** | Medium | ✅ Excellent | Good (via git) | Manual | Manual conversion |
| **Excel** | ✅ Easy | Poor | Good (OneDrive) | ✅ Formulas | VBA macro |
| **Word** | ✅ Easy | Poor | Good (OneDrive) | Limited | Python script |
| **Google Forms** | ✅ Very Easy | Good (revisions) | ✅ Excellent | ✅ Built-in | Apps Script |
| **Typeform** | ✅ Very Easy | Good | ✅ Excellent | ✅ Built-in | Webhook |
| **ChatGPT/Claude** | Medium | N/A | N/A | ✅ AI-powered | Direct output |

---

## Recommended Approach by Team Size

### Small Team (1-5 people)
**Use:** Markdown + ChatGPT/Claude
- Version control in git
- AI-assisted conversion to YAML
- No complex tooling needed

### Medium Team (5-20 people)
**Use:** Google Forms + Apps Script
- Easy for non-technical stakeholders
- Auto-converts to YAML
- Tracks submission history

### Large Organization (20+ people)
**Use:** Typeform + Webhook + Slack
- Professional UX
- Integration with existing tools
- Analytics on form quality
- Automated notifications

### Client-Facing
**Use:** Word or Excel template
- Familiar to clients
- Can email or attach to contracts
- Offline capability
- Manual YAML conversion (you control quality)

---

## Next Steps

1. **Choose your format** based on team size and preferences
2. **Create template** using instructions above
3. **Test with pilot project** to refine questions
4. **Document conversion process** for your team
5. **Train stakeholders** on filling out forms

**Sample files available:**
- `templates/intake-forms/PROJECT_INTAKE_FORM.md` ✅ Created
- `templates/intake-forms/CHATGPT_INTAKE_PROMPT.md` ✅ Created
- `templates/intake-forms/excel_template.xlsx` (Create using Excel)
- `templates/intake-forms/word_template.docx` (Create using Word)
