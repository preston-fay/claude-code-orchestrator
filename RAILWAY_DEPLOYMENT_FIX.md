# Railway Deployment Configuration Fix

## Problem: Multiple Redundant Deployments

You're seeing multiple deployments because you likely have multiple Railway services watching the same GitHub repository. Each service tries to deploy the entire app, causing redundant builds.

## Solution Options:

### Option 1: Keep Only One Service (Recommended)
1. Go to Railway Dashboard
2. Delete or disable these redundant services:
   - `truthful-respect` 
   - `claude-code-orchestrator` (if it's a duplicate)
3. Keep only `eloquent-liberation` as your main deployment

### Option 2: Configure Service-Specific Deployments
If you need multiple services (e.g., separate frontend/backend):

1. **For Backend Service** (Python/FastAPI):
   ```json
   // railway.json for backend
   {
     "build": {
       "builder": "DOCKERFILE",
       "dockerfilePath": "Dockerfile"
     },
     "deploy": {
       "startCommand": "uvicorn orchestrator_v2.api.server:app --host 0.0.0.0 --port $PORT",
       "healthcheckPath": "/health"
     }
   }
   ```

2. **For Frontend Service** (React):
   ```json
   // railway.json for frontend
   {
     "build": {
       "builder": "NIXPACKS",
       "buildCommand": "cd rsg-ui && npm install && npm run build"
     },
     "deploy": {
       "startCommand": "cd rsg-ui && npm run preview",
       "healthcheckPath": "/"
     }
   }
   ```

### Option 3: Disable Auto-Deploy
1. Go to each Railway service settings
2. Under "Deployments" → "Triggers"
3. Disable "Deploy on Push"
4. Manually trigger deployments when ready

## Current Issues to Fix:

### 1. Frontend Build (if separate service)
The React app has a separate Dockerfile that's trying to build:
```dockerfile
# rsg-ui/Dockerfile exists and might be conflicting
```

### 2. Health Check Timing
Your `railway.json` has a 60-second timeout, but services aren't starting fast enough:
```json
{
  "deploy": {
    "healthcheckTimeout": 120  // Increase to 120 seconds
  }
}
```

## Recommended Immediate Actions:

1. **Check your Railway dashboard** for duplicate services
2. **Delete redundant services** to stop multiple deployments
3. **Ensure only ONE service** is watching the main branch
4. **Or configure different branches** for different services:
   - `main` → production
   - `staging` → staging environment
   - `frontend` → frontend-only service

## Verification Commands:

```bash
# Check if you have multiple railway.json files
find . -name "railway.json" -type f

# Check for multiple Dockerfiles
find . -name "Dockerfile" -type f

# See what's in your Railway config
cat railway.json
```

## Expected Result:
After cleanup, you should see:
- ONE deployment per push
- ONE service running your app
- Faster deployment times
- No redundant builds

## If You Want Separate Frontend/Backend:

1. Create two Railway services
2. Backend service:
   - Points to root directory
   - Uses main Dockerfile
   - Runs Python/FastAPI

3. Frontend service:
   - Points to `rsg-ui` directory
   - Uses Node.js buildpack
   - Runs React app

4. Configure environment variables:
   - Frontend: `VITE_API_URL=https://backend-service.railway.app`
   - Backend: `CORS_ORIGINS=https://frontend-service.railway.app`

This will prevent the multiple deployment issue you're seeing.