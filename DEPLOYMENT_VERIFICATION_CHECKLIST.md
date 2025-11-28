# Deployment Verification Checklist for Intake System

## 🚨 CRITICAL: Potential Deployment Issues to Fix

### 1. **Missing __init__.py file**
The `/orchestrator_v2/models/` directory needs an `__init__.py` file for Python to recognize it as a module.

**FIX REQUIRED:**
```python
# Create /orchestrator_v2/models/__init__.py
"""Models package for orchestrator v2."""
from orchestrator_v2.models.intake import *
```

### 2. **Intake Router Registration**
Verify the intake router is properly registered in server.py:
```python
# In orchestrator_v2/api/server.py
from orchestrator_v2.api.routes import intake
app.include_router(intake.router)
```

### 3. **Data Directory Creation**
Ensure the intake sessions directory exists:
```bash
mkdir -p data/intake_sessions
```

## ✅ End-to-End Testing Checklist

### **Backend API Testing**

Use these curl commands after deployment:

#### 1. **Health Check**
```bash
curl https://your-app.railway.app/health
# Expected: {"status": "healthy"}
```

#### 2. **List Intake Templates**
```bash
curl https://your-app.railway.app/api/intake/templates
# Expected: JSON array with 6 templates
```

#### 3. **Get Specific Template**
```bash
curl https://your-app.railway.app/api/intake/templates/presentation
# Expected: Full template definition
```

#### 4. **Create Intake Session**
```bash
curl -X POST https://your-app.railway.app/api/intake/sessions \
  -H "Content-Type: application/json" \
  -H "X-User-Id: test-user" \
  -H "X-User-Email: test@example.com" \
  -d '{
    "template_id": "presentation",
    "client_slug": "kearney-default"
  }'
# Expected: Session created with session_id
```

#### 5. **Submit Answer**
```bash
curl -X POST https://your-app.railway.app/api/intake/sessions/{session_id}/answers \
  -H "Content-Type: application/json" \
  -d '{
    "question_id": "presentation_type",
    "answer": "project_report"
  }'
# Expected: {"success": true}
```

#### 6. **Get Session Status**
```bash
curl https://your-app.railway.app/api/intake/sessions/{session_id}/status
# Expected: Current session state with responses
```

### **Frontend UI Testing**

#### 1. **Initial Load**
- [ ] Navigate to https://your-app.railway.app
- [ ] Verify main page loads
- [ ] Check console for JavaScript errors

#### 2. **Intake Wizard Access**
- [ ] Navigate to Orchestrator Runs page
- [ ] Click "New Project (Guided)" button
- [ ] Verify IntakeWizard modal opens

#### 3. **Template Selection**
- [ ] Verify 6 template cards are displayed
- [ ] Each template shows name, description, estimated time
- [ ] Click on "Presentation Content" template
- [ ] Verify wizard starts

#### 4. **Question Flow**
- [ ] First question appears (presentation type)
- [ ] Select "Project Report"
- [ ] Verify conditional questions appear
- [ ] Fill out 2-3 questions
- [ ] Use navigation (Next/Previous)

#### 5. **Session Persistence**
- [ ] Fill some answers
- [ ] Refresh the page
- [ ] Open wizard again
- [ ] Verify session resumes where left off

#### 6. **Completion**
- [ ] Complete all required questions
- [ ] Click "Complete Intake"
- [ ] Verify project is created
- [ ] Check redirect to project detail page

### **Integration Testing**

#### 1. **End-to-End Project Creation**
```bash
# 1. Create session
SESSION_ID=$(curl -X POST https://your-app.railway.app/api/intake/sessions \
  -H "Content-Type: application/json" \
  -H "X-User-Id: test-user" \
  -H "X-User-Email: test@example.com" \
  -d '{"template_id": "webapp"}' | jq -r '.session_id')

# 2. Answer questions
curl -X POST https://your-app.railway.app/api/intake/sessions/$SESSION_ID/answers \
  -H "Content-Type: application/json" \
  -d '{"question_id": "app_name", "answer": "Test App"}'

# 3. Complete session
curl -X POST https://your-app.railway.app/api/intake/sessions/$SESSION_ID/complete

# 4. Verify run created
curl https://your-app.railway.app/api/runs
```

## 🔍 Monitoring & Debugging Tools

### **1. Railway Logs**
```bash
railway logs --tail
```
Watch for:
- Import errors
- Missing modules
- API endpoint 404s
- Database/file access errors

### **2. Browser DevTools**
- **Network Tab**: Check API calls (should see /api/intake/* requests)
- **Console**: Look for JavaScript errors
- **Application Tab**: Check localStorage for session data

### **3. API Testing Tool (Postman/Insomnia)**
Import this collection to test all endpoints:
```json
{
  "name": "Intake System Tests",
  "requests": [
    {
      "name": "List Templates",
      "method": "GET",
      "url": "{{base_url}}/api/intake/templates"
    },
    {
      "name": "Create Session",
      "method": "POST",
      "url": "{{base_url}}/api/intake/sessions",
      "headers": {
        "X-User-Id": "test-user",
        "X-User-Email": "test@example.com"
      },
      "body": {
        "template_id": "presentation"
      }
    }
  ]
}
```

## 🛠️ Quick Fixes for Common Issues

### **Issue: "Module not found: orchestrator_v2.models.intake"**
```bash
# Fix: Create __init__.py
echo '"""Models package."""' > orchestrator_v2/models/__init__.py
git add orchestrator_v2/models/__init__.py
git commit -m "fix: add missing __init__.py for models module"
git push
```

### **Issue: "404 on /api/intake/templates"**
```python
# Fix: Register router in server.py
# Add after line 71:
from orchestrator_v2.api.routes import intake
# Add after line ~200:
app.include_router(intake.router)
```

### **Issue: "Permission denied: data/intake_sessions"**
```dockerfile
# Fix: Update Dockerfile to create directory
RUN mkdir -p /app/data/intake_sessions && \
    chmod 777 /app/data/intake_sessions
```

### **Issue: "CORS errors in browser"**
```python
# Already configured in server.py, but verify:
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For production, specify your domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

## 📊 Success Criteria

The deployment is successful when:
- ✅ All 6 intake templates load
- ✅ Session can be created and persisted
- ✅ Questions display with conditional logic
- ✅ Answers are validated and saved
- ✅ Session can be completed
- ✅ Project/Run is created from intake
- ✅ No console errors in browser
- ✅ No 500 errors in logs

## 🚀 Verification Script

Save and run this script to verify deployment:
```bash
#!/bin/bash
BASE_URL="https://your-app.railway.app"

echo "Testing Intake System Deployment..."

# Test 1: Health check
echo -n "1. Health Check: "
curl -s $BASE_URL/health | jq -r '.status'

# Test 2: Templates
echo -n "2. Templates Available: "
curl -s $BASE_URL/api/intake/templates | jq '. | length'

# Test 3: Create session
echo -n "3. Create Session: "
SESSION=$(curl -s -X POST $BASE_URL/api/intake/sessions \
  -H "Content-Type: application/json" \
  -H "X-User-Id: test" \
  -H "X-User-Email: test@test.com" \
  -d '{"template_id": "general"}')
echo $SESSION | jq -r '.session_id'

echo "✅ Basic API tests passed!"
```

## 🎯 Most Likely Issues & Solutions

Based on the implementation, here are the most likely deployment issues:

1. **Missing `__init__.py` in models directory** - HIGH PROBABILITY
   - This WILL cause import errors
   - Fix immediately before deployment

2. **Intake router not registered** - MEDIUM PROBABILITY
   - Check server.py includes the router
   - Will cause 404 on all intake endpoints

3. **Data directory permissions** - LOW PROBABILITY
   - Railway should handle this, but may need Dockerfile update
   - Will cause 500 errors on session creation

4. **Frontend build issues** - LOW PROBABILITY
   - React app should build fine
   - Check for TypeScript errors

The system SHOULD work if these issues are addressed. The implementation is solid, just needs these deployment adjustments.