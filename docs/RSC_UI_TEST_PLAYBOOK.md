# RSC UI Test Playbook

This playbook describes how to smoke-test the Kearney Ready-Set-Code (RSC) web interface.

## Prerequisites

1. **Python environment** with orchestrator dependencies installed
2. **Node.js** (v18+) for the React UI
3. **API key** set in user profile (for prompt console testing)

## Starting the Application

### 1. Start API Server

```bash
cd orchestrator_v2
uvicorn api.server:app --reload --port 8000
```

Verify: `curl http://localhost:8000/health` returns `{"status":"ok"}`

### 2. Start RSC UI

```bash
cd rsg-ui
npm install  # first time only
npm run dev
```

Verify: Open http://localhost:5173 in browser

---

## Test Scenarios

### 1. Project List Page

**URL:** `/` or `/projects`

**Verify:**
- [ ] Page loads without errors
- [ ] Project table shows columns: Name, Type, Client, Current Phase, Status, Created
- [ ] "New Project" button is visible
- [ ] Clicking a project row navigates to detail page

### 2. Create New Project

**Action:** Click "New Project" button

**Verify:**
- [ ] Modal opens with form fields
- [ ] Template cards are displayed (Blank, Golden Path, Territory Demo, App Build)
- [ ] Can enter project name and client
- [ ] Selecting a template highlights the card
- [ ] "Create Project" button works
- [ ] After creation, redirects to project detail page

**Test each template:**
- [ ] Blank Project → type shows "Blank"
- [ ] Golden Path → type shows "Analytics"
- [ ] Territory Demo → type shows "Territory"
- [ ] App Build → type shows "App Build"

### 3. Project Detail Page

**URL:** `/projects/{projectId}`

**Verify:**
- [ ] Page loads without crashing (no `.map of undefined` errors)
- [ ] Project Info card shows: Type, Client, Status, Created, Current Phase
- [ ] Workspace path shown with "Copy" button (if set)
- [ ] LLM Model dropdown shows Sonnet 4.5 / Haiku 4.5 options
- [ ] RSG Status cards display correctly (Ready/Set/Go)
- [ ] Phases list shows appropriate phases for project type
- [ ] Navigation links visible: Features, App Build (for app_build type), Refresh

### 4. LLM Model Settings

**Location:** Project Detail page, right side panel

**Verify:**
- [ ] Current model displayed (Sonnet 4.5 default)
- [ ] Dropdown allows switching to Haiku 4.5
- [ ] Selection persists after refresh
- [ ] "API Key Set" badge shows if key is configured
- [ ] No API key exposure in UI

### 5. Orchestrator Prompt Console

**Location:** Project Detail page, bottom section

**Verify:**
- [ ] Console shows placeholder suggestions
- [ ] Can type a message in textarea
- [ ] Enter key sends message
- [ ] "Send" button works
- [ ] Loading state shows "Thinking..."
- [ ] Response displays with:
  - [ ] Model used (Sonnet 4.5 / Haiku 4.5)
  - [ ] Token count
- [ ] Error state displays if API key not set

**Test prompts:**
- "What should I do next?"
- "How do I add a new feature?"
- "What is the current status?"

### 6. Features Page

**URL:** `/projects/{projectId}/features`

**Verify:**
- [ ] Page loads without errors
- [ ] "Create Feature" form visible
- [ ] Feature list table displays
- [ ] Clicking feature opens detail modal
- [ ] Modal tabs work: Summary, Plan, Build Plan, Results, Actions

### 7. App Build Page

**URL:** `/projects/{projectId}/build`

**Verify:**
- [ ] Page loads without errors
- [ ] Only accessible for App Build project types
- [ ] Description textarea present
- [ ] "Plan Build" button works (requires backend)
- [ ] Results display correctly

---

## Console Error Checks

Open browser DevTools (F12) → Console tab

**Should NOT see:**
- [ ] `TypeError: Cannot read properties of undefined`
- [ ] `project.phases.map is not a function`
- [ ] Any red console errors on page load

---

## Kearney Design Compliance

**Verify styling:**
- [ ] Primary color is purple (#7823DC)
- [ ] No red or green colors for status
- [ ] Error states use purple tints with charcoal text
- [ ] Status badges use violet tints
- [ ] Buttons use purple theme

---

## API Endpoint Verification

Test these endpoints work:

```bash
# List projects
curl http://localhost:8000/projects

# Get templates
curl http://localhost:8000/project-templates

# Create project
curl -X POST http://localhost:8000/projects \
  -H "Content-Type: application/json" \
  -d '{"project_name": "Test", "template_id": "blank"}'

# Get project
curl http://localhost:8000/projects/{project_id}

# Chat (requires API key)
curl -X POST http://localhost:8000/projects/{project_id}/chat \
  -H "Content-Type: application/json" \
  -H "X-User-Id: dev-user" \
  -d '{"message": "What is the status?"}'
```

---

## Known Limitations

1. **Features page** uses direct `fetch()` instead of API client - may need proxy config
2. **App Build page** uses different API path - backend integration pending
3. **Console memory** is session-only (no persistence between page loads)

---

## Troubleshooting

### "Failed to load projects"
- Check API server is running on port 8000
- Verify CORS is enabled
- Check Settings panel has correct API URL

### "Failed to get response" in console
- Verify API key is set in Settings panel
- Check user profile has `llm_api_key` configured
- Verify model selection is valid

### Project detail crash
- Should be fixed - if still crashing, check for `undefined` access in console
- Verify project has `completed_phases` array

---

## URL Reference

| Page | URL |
|------|-----|
| Project List | `/` or `/projects` |
| Project Detail | `/projects/{projectId}` |
| Features | `/projects/{projectId}/features` |
| App Build | `/projects/{projectId}/build` |
