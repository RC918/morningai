# Vercel Environment Variables Configuration

## Overview

This document provides a comprehensive guide for configuring environment variables in Vercel for the MorningAI frontend applications.

## Environment Variable Naming Convention

### Frontend Variables (Client-Side)

All client-side environment variables **must** be prefixed with `VITE_`:

```
VITE_API_BASE_URL
VITE_SENTRY_DSN
VITE_SUPABASE_URL
```

**Why?** Vite only exposes environment variables prefixed with `VITE_` to the client bundle. This prevents accidental exposure of sensitive backend secrets.

### Backend Variables (Server-Side)

Backend variables should **not** be prefixed with `VITE_` and should only be used in serverless functions (if any):

```
JWT_SECRET_KEY
DATABASE_URL
REDIS_URL
```

**Warning**: Currently, some backend-style variables are configured in the Vercel frontend projects. These should be audited and moved to backend infrastructure.

## Current Environment Variables

### morningai (frontend-dashboard)

#### Production Environment

| Variable | Description | Example Value | Required |
|----------|-------------|---------------|----------|
| `VITE_API_BASE_URL` | Backend API endpoint | `https://api.morningai.app` | ✅ Yes |
| `VITE_SENTRY_DSN` | Sentry error tracking DSN | `https://...@sentry.io/...` | ✅ Yes |
| `VITE_SENTRY_TRACES_SAMPLE_RATE` | Sentry performance sampling | `0.1` | ⚠️ Recommended |
| `VITE_SENTRY_REPLAYS_SESSION_SAMPLE_RATE` | Sentry session replay sampling | `0.1` | ⚠️ Recommended |
| `VITE_SUPABASE_URL` | Supabase project URL | `https://xxx.supabase.co` | ✅ Yes |
| `VITE_SUPABASE_ANON_KEY` | Supabase anonymous key | `eyJ...` | ✅ Yes |
| `VITE_TOLGEE_API_KEY` | Tolgee i18n API key | `tgpak_...` | ⚠️ Recommended |
| `VITE_TOLGEE_PROJECT_ID` | Tolgee project ID | `...` | ⚠️ Recommended |
| `VITE_TOLGEE_API_URL` | Tolgee API endpoint | `https://app.tolgee.io` | ⚠️ Recommended |
| `NODE_ENV` | Node environment | `production` | ✅ Yes |

#### Preview/Staging Environment

| Variable | Description | Example Value | Required |
|----------|-------------|---------------|----------|
| `VITE_API_BASE_URL` | Staging backend API | `https://staging-api.morningai.app` | ✅ Yes |
| `VITE_SENTRY_DSN` | Sentry DSN (same as prod) | `https://...@sentry.io/...` | ✅ Yes |
| `VITE_SENTRY_TRACES_SAMPLE_RATE` | Higher sampling for testing | `1.0` | ⚠️ Recommended |
| `VITE_SENTRY_REPLAYS_SESSION_SAMPLE_RATE` | Higher sampling for testing | `1.0` | ⚠️ Recommended |
| `VITE_SUPABASE_URL` | Supabase URL (same as prod) | `https://xxx.supabase.co` | ✅ Yes |
| `VITE_SUPABASE_ANON_KEY` | Supabase key (same as prod) | `eyJ...` | ✅ Yes |
| `STAGING_TEST_EMAIL` | Test user email | `test@example.com` | ⚠️ Optional |
| `STAGING_TEST_PASSWORD` | Test user password | `...` | ⚠️ Optional |
| `VITE_USE_MOCK` | Enable mock data | `true` | ⚠️ Optional |
| `ENABLE_MOCK_USERS` | Enable mock users | `true` | ⚠️ Optional |
| `NODE_ENV` | Node environment | `development` | ✅ Yes |

#### Development Environment

Same as Preview/Staging, but with additional debugging flags:

| Variable | Description | Example Value |
|----------|-------------|---------------|
| `VITE_FEATURES` | Feature flags (comma-separated) | `new-ui,beta-features` |
| `VITE_PHASE` | Current development phase | `9` |

### owner-console

#### Production Environment

| Variable | Description | Example Value | Required |
|----------|-------------|---------------|----------|
| `VITE_API_BASE_URL` | Owner console API endpoint | `https://owner-api.morningai.app` | ✅ Yes |
| `VITE_OWNER_CONSOLE_API` | Alternative API endpoint | `https://owner-api.morningai.app` | ⚠️ Optional |
| `VITE_SENTRY_DSN` | Sentry DSN | `https://...@sentry.io/...` | ✅ Yes |

#### Preview/Staging Environment

| Variable | Description | Example Value | Required |
|----------|-------------|---------------|----------|
| `VITE_API_BASE_URL` | Staging owner console API | `https://staging-owner-api.morningai.app` | ✅ Yes |
| `VITE_SENTRY_DSN` | Sentry DSN | `https://...@sentry.io/...` | ✅ Yes |

## Variables to Remove (Security Audit)

### Current State (API Query - 2025-11-04)

The Vercel API shows the following variables currently exist in the morningai project:
- `NODE_ENV`
- `VITE_API_BASE_URL`
- `VITE_SENTRY_DSN`
- `VITE_SUPABASE_ANON_KEY`
- `VITE_SUPABASE_URL`
- `VITE_USE_MOCK`
- `VITE_FEATURES`
- `VITE_PHASE3_DEPLOYMENT_DATE`
- `VITE_TOLGEE_API_URL`

**Note**: `OPENAI_MAX_DAILY_COST` was removed via API on 2025-11-04.

### Backend-Only Variables (If Present, Remove from Vercel Frontend)

If any of the following variables are present in your Vercel frontend projects, they should be **removed** or **moved to backend infrastructure**:

| Variable | Why Remove | Where to Move |
|----------|-----------|---------------|
| `JWT_SECRET_KEY` | Backend authentication secret | Render backend env vars |
| `COOKIE_SECURE` | Backend cookie configuration | Render backend env vars |
| `COOKIE_DOMAIN` | Backend cookie configuration | Render backend env vars |
| `COOKIE_SAMESITE` | Backend cookie configuration | Render backend env vars |
| `SENTRY_AUTH_TOKEN` | Sentry API token (build-time only) | GitHub Actions secrets |
| `SENTRY_ORG` | Sentry organization (build-time only) | GitHub Actions secrets |
| `SENTRY_PROJECT` | Sentry project (build-time only) | GitHub Actions secrets |
| `UPSTASH_REDIS_REST_URL` | Backend Redis URL | Render backend env vars |
| `UPSTASH_REDIS_REST_TOKEN` | Backend Redis token | Render backend env vars |

**Rationale**: These are backend-only variables and should not exist in frontend Vercel projects. Exposing them in the frontend bundle is a security risk.

**Action Required**: Audit your Vercel Dashboard and remove any of these variables if present.

## How to Configure Environment Variables

### Option 1: Vercel Dashboard (Recommended)

1. Go to [Vercel Dashboard](https://vercel.com/morning-ai/morningai/settings/environment-variables)
2. Click "Add New" button
3. Fill in:
   - **Key**: Variable name (e.g., `VITE_API_BASE_URL`)
   - **Value**: Variable value
   - **Environments**: Select Production, Preview, and/or Development
4. Click "Save"

### Option 2: Vercel CLI

```bash
# Add a variable for all environments
vercel env add VITE_API_BASE_URL

# Add a variable for specific environment
vercel env add VITE_API_BASE_URL production

# List all variables
vercel env ls

# Remove a variable
vercel env rm VITE_API_BASE_URL
```

### Option 3: Vercel API

```bash
# Add a variable
curl -X POST "https://api.vercel.com/v10/projects/prj_2vBtvZikIy4hahhoauNC2AKQMtaM/env" \
  -H "Authorization: Bearer $VERCEL_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "key": "VITE_API_BASE_URL",
    "value": "https://api.morningai.app",
    "type": "encrypted",
    "target": ["production", "preview", "development"]
  }'
```

## Environment-Specific Configuration

### Production

- Use production API endpoints
- Lower Sentry sampling rates (10%)
- No mock data or test users
- Strict error handling

### Staging (develop branch)

- Use staging API endpoints
- Higher Sentry sampling rates (100%)
- Test users enabled
- Relaxed error handling for debugging

### Preview (feature branches)

- Use staging or development API endpoints
- Full Sentry sampling (100%)
- Mock data enabled
- Debug mode enabled

## Validation and Testing

### Check if Variables are Loaded

Add this to your component for debugging:

```typescript
console.log('Environment:', {
  apiBaseUrl: import.meta.env.VITE_API_BASE_URL,
  sentryDsn: import.meta.env.VITE_SENTRY_DSN,
  supabaseUrl: import.meta.env.VITE_SUPABASE_URL,
  mode: import.meta.env.MODE,
  dev: import.meta.env.DEV,
  prod: import.meta.env.PROD,
});
```

### Common Issues

1. **Variable not available in client**:
   - Ensure it's prefixed with `VITE_`
   - Rebuild the deployment after adding the variable

2. **Variable has wrong value**:
   - Check which environment (Production/Preview/Development) is being deployed
   - Verify the variable is set for that specific environment

3. **Variable works locally but not on Vercel**:
   - Local `.env` files are not used on Vercel
   - All variables must be configured in Vercel Dashboard

## Security Best Practices

1. **Never commit secrets to git**:
   - Use `.env.local` for local development (gitignored)
   - Configure secrets only in Vercel Dashboard

2. **Use encrypted variables**:
   - Vercel encrypts all environment variables by default
   - Sensitive values are never exposed in logs

3. **Rotate secrets regularly**:
   - Follow the [Secret Rotation Policy](../security/SECRET_ROTATION_POLICY.md)
   - Update Vercel variables after rotation

4. **Audit variables quarterly**:
   - Review all configured variables
   - Remove unused variables
   - Verify no backend secrets are exposed

5. **Use different values per environment**:
   - Production should use production API keys
   - Staging/Preview should use test API keys

## Migration from .env Files

If you have local `.env` files, migrate them to Vercel:

```bash
# Read your .env file
cat .env

# For each VITE_* variable, add to Vercel
vercel env add VITE_API_BASE_URL production
vercel env add VITE_API_BASE_URL preview
vercel env add VITE_API_BASE_URL development
```

## Troubleshooting

### Variable Not Working After Adding

1. Trigger a new deployment (push a commit or redeploy)
2. Check the deployment logs for the variable value
3. Verify the variable is set for the correct environment

### Build Fails After Adding Variable

1. Check if the variable name is correct (typos)
2. Verify the variable value doesn't contain special characters that need escaping
3. Check build logs for specific error messages

### Variable Shows as Undefined

1. Ensure variable is prefixed with `VITE_`
2. Check if variable is set for the deployed environment
3. Rebuild the deployment

## References

- [Vite Environment Variables](https://vitejs.dev/guide/env-and-mode.html)
- [Vercel Environment Variables](https://vercel.com/docs/concepts/projects/environment-variables)
- [Environment Variables Schema](/config/env.schema.yaml)
- [Secret Rotation Policy](../security/SECRET_ROTATION_POLICY.md)

---

**Last Updated**: 2025-11-04
**Owner**: CTO + DevOps Team
**Status**: Active
