# Morning AI Deployment Guide

## Overview
This guide covers deploying the Morning AI application to your cloud stack:
- **Frontend**: React app deployed to Vercel
- **Backend**: Flask API deployed to Render
- **Database**: PostgreSQL on Supabase
- **Cache**: Redis on Upstash
- **Monitoring**: Sentry for error tracking
- **CDN**: Cloudflare for performance and security

## Required Environment Variables

### Supabase (Database)
```
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your-anon-key
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key
```

### Render (Backend Deployment)
```
RENDER_API_KEY=your-render-api-key
```

### Vercel (Frontend Deployment)
```
VERCEL_TOKEN=your-vercel-token
VERCEL_ORG_ID=your-org-id
VERCEL_PROJECT_ID=your-project-id
```

### Upstash (Redis Cache)
```
UPSTASH_REDIS_REST_URL=https://your-redis.upstash.io
UPSTASH_REDIS_REST_TOKEN=your-redis-token
```

### Sentry (Error Tracking)
```
SENTRY_DSN=https://your-sentry-dsn@sentry.io/project-id
SENTRY_AUTH_TOKEN=your-sentry-auth-token
```

### Cloudflare (Optional CDN/Security)
```
CLOUDFLARE_API_TOKEN=your-cloudflare-token
CLOUDFLARE_ZONE_ID=your-zone-id
```

## Deployment Steps

1. **Backend to Render**
   - Uses `render.yaml` configuration
   - Automatically installs dependencies from `requirements.txt`
   - Configures environment variables for database and cache

2. **Frontend to Vercel**
   - Uses `vercel.json` configuration
   - Builds React app with Vite
   - Configures SPA routing

3. **Database Setup**
   - Connect Flask app to Supabase PostgreSQL
   - Run database migrations
   - Populate sample data

4. **Cache Configuration**
   - Connect Flask app to Upstash Redis
   - Configure caching for API responses

5. **Monitoring Setup**
   - Configure Sentry for error tracking
   - Set up performance monitoring

## Local Testing
Both applications are currently running locally:
- Frontend: http://localhost:5174/
- Backend: http://localhost:5000/

## Production URLs
After deployment, you'll receive:
- Frontend URL from Vercel
- Backend URL from Render
- Database connection from Supabase
