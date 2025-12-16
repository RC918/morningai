# Vercel Deployment Guide

## Overview

This guide explains how to properly configure environment variables for the frontend dashboard when deploying to Vercel.

## Problem

The frontend dashboard needs to communicate with the backend API. If the `VITE_API_BASE_URL` environment variable is not configured in Vercel, the frontend will default to the production backend URL (`https://morningai-backend-v2.onrender.com`).

Previously, when this variable was not set, the frontend would default to `http://localhost:5001`, causing **ConnectionError** in production because the frontend would try to connect to localhost instead of the actual backend API.

## Solution

### Default Behavior (Recommended)

The frontend now defaults to the production backend URL if `VITE_API_BASE_URL` is not set:

```javascript
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'https://morningai-backend-v2.onrender.com'
```

This means **no environment variable configuration is required** for production deployments to work correctly.

### Custom Backend URL (Optional)

If you need to point to a different backend (e.g., staging environment), configure the environment variable in Vercel:

1. Go to your Vercel project settings
2. Navigate to **Settings** → **Environment Variables**
3. Add the following variable:
   - **Name**: `VITE_API_BASE_URL`
   - **Value**: Your backend URL (e.g., `https://staging-backend.example.com`)
   - **Environment**: Select the appropriate environment(s)

## Environment Variables

### Required Variables

None - the frontend will work with default settings.

### Optional Variables

| Variable | Description | Default | Example |
|----------|-------------|---------|---------|
| `VITE_API_BASE_URL` | Backend API base URL | `https://morningai-backend-v2.onrender.com` | `https://staging-backend.example.com` |
| `VITE_USE_MOCK` | Enable mock API responses | `false` | `true` |
| `VITE_SENTRY_DSN` | Sentry error tracking DSN | - | `https://...@sentry.io/...` |
| `VITE_ENV` | Environment name | - | `production`, `staging`, `development` |

## Vercel Configuration

The `vercel.json` file is already configured correctly:

```json
{
  "$schema": "https://openapi.vercel.sh/vercel.json",
  "framework": "vite",
  "buildCommand": "cd handoff/20250928/40_App/frontend-dashboard && npm run build",
  "installCommand": "cd handoff/20250928/40_App/frontend-dashboard && npm install --include=dev",
  "outputDirectory": "handoff/20250928/40_App/frontend-dashboard/dist",
  "rewrites": [
    {
      "source": "/(.*)",
      "destination": "/index.html"
    }
  ]
}
```

## Local Development

For local development, create a `.env` file in the `handoff/20250928/40_App/frontend-dashboard` directory:

```bash
# .env
VITE_API_BASE_URL=http://localhost:5001
VITE_USE_MOCK=false
```

Or copy from the example:

```bash
cd handoff/20250928/40_App/frontend-dashboard
cp .env.example .env
# Edit .env with your local settings
```

## Testing

### Test Backend Connection

After deployment, verify the frontend can connect to the backend:

1. Open the browser console on your deployed site
2. Check for any API errors
3. Verify API calls are going to the correct backend URL

### Health Check

The frontend includes a health check endpoint that can be used to verify backend connectivity:

```javascript
import { apiClient } from './lib/api'

const health = await apiClient.checkHealth()
console.log('Backend health:', health)
```

## Troubleshooting

### ConnectionError: Failed to fetch

**Symptom**: Sentry reports `ConnectionError` with URL showing `localhost` or incorrect backend URL.

**Cause**: The `VITE_API_BASE_URL` environment variable was not set, and the old default was `localhost`.

**Solution**: This has been fixed. The new default is the production backend URL. If you still see this error:
1. Clear your browser cache
2. Redeploy the frontend
3. Verify the environment variable is not set to an incorrect value

### CORS Errors

**Symptom**: Browser console shows CORS policy errors.

**Cause**: The backend is not configured to allow requests from your Vercel domain.

**Solution**: Update the backend's CORS configuration to include your Vercel domain:
- Add your Vercel domain to the `CORS_ORIGINS` environment variable in the backend
- Example: `https://morningai.vercel.app,https://morningai-git-*.vercel.app`

### 404 Not Found

**Symptom**: API requests return 404 errors.

**Cause**: The API endpoint path is incorrect or the backend is not deployed.

**Solution**:
1. Verify the backend is running: `curl https://morningai-backend-v2.onrender.com/health`
2. Check the API endpoint path in your code
3. Verify the backend has the required routes deployed

## Related Files

- Frontend API clients:
  - `handoff/20250928/40_App/frontend-dashboard/src/lib/api.js`
  - `handoff/20250928/40_App/frontend-dashboard/src/lib/api-client.js`
  - `handoff/20250928/40_App/frontend-dashboard/src/lib/api-client.ts`
- Environment example: `handoff/20250928/40_App/frontend-dashboard/.env.example`
- Vercel config: `vercel.json`

## Backend Deployment

The backend is deployed on Render.com:
- **Production URL**: https://morningai-backend-v2.onrender.com
- **Health Check**: https://morningai-backend-v2.onrender.com/health
- **API Base**: https://morningai-backend-v2.onrender.com/api

## Support

If you encounter issues:
1. Check Sentry for error details: https://morningai-core.sentry.io
2. Verify backend health: `curl https://morningai-backend-v2.onrender.com/health`
3. Check Vercel deployment logs
4. Review browser console for client-side errors

---

**Last Updated**: 2025-10-24  
**Related Issue**: Sentry #6970568381 - ConnectionError in agent.create_faq_task
