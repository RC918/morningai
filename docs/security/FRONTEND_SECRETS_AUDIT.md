# Frontend Secrets Audit Report

**Document ID**: SEC-AUDIT-001  
**Version**: 1.0  
**Audit Date**: 2025-12-10  
**Auditor**: Engineering Team  
**Scope**: Vercel Environment Variables for Frontend Applications

## Executive Summary

This audit reviews the environment variables configured in Vercel for MorningAI frontend applications (frontend-dashboard, owner-console) to identify and document backend-style secrets that should not be exposed in frontend deployments.

**Key Findings**:
- The existing documentation (`docs/deployment/VERCEL_ENVIRONMENT_VARIABLES.md`) already identifies backend-style secrets that should be removed
- `OPENAI_MAX_DAILY_COST` was removed via API on 2025-11-04
- Current Vercel configuration appears to follow best practices with `VITE_*` prefixed variables
- One critical security flag (`VITE_E2E`) requires strict environment controls

## Audit Scope

### Applications Covered

| Application | Vercel Project | Build Framework |
|-------------|----------------|-----------------|
| frontend-dashboard | morningai | Vite |
| owner-console | morningai-owner-console | Vite |

### Environment Types

| Environment | Description | Security Level |
|-------------|-------------|----------------|
| Production | Live user-facing deployment | Highest |
| Preview | PR preview deployments | Medium |
| Development | Local development | Low |

## Legitimate Frontend Variables

The following `VITE_*` prefixed variables are designed for frontend use and are safe to expose in Vercel:

### Core Configuration

| Variable | Security Level | Description | Required |
|----------|---------------|-------------|----------|
| `VITE_API_BASE_URL` | Public | Backend API endpoint (use `/api` for Vercel proxy) | Yes |
| `VITE_SUPABASE_URL` | Public | Supabase project URL | Yes |
| `VITE_SUPABASE_ANON_KEY` | Public | Supabase anonymous key (designed for public use) | Yes |
| `NODE_ENV` | Public | Environment mode | Yes |

### Monitoring and Observability

| Variable | Security Level | Description | Required |
|----------|---------------|-------------|----------|
| `VITE_SENTRY_DSN` | Public | Sentry error tracking DSN | Yes |
| `VITE_SENTRY_TRACES_SAMPLE_RATE` | Public | Sentry performance sampling rate | Recommended |
| `VITE_SENTRY_REPLAYS_SESSION_SAMPLE_RATE` | Public | Sentry session replay sampling | Recommended |
| `VITE_TRACE_VIEWER_URL` | Public | Trace viewer URL (Jaeger, Tempo, etc.) | Optional |

### Feature Flags

| Variable | Security Level | Description | Required |
|----------|---------------|-------------|----------|
| `VITE_FEATURES` | Public | Enabled features (comma-separated) | Optional |
| `VITE_USE_MOCK` | Public | Enable mock API mode | Optional |
| `VITE_FEATURE_OWNER_CONSOLE_API` | Public | Enable real backend API for Owner Console | Optional |
| `VITE_PHASE` | Public | Current development phase | Optional |

### Internationalization (i18n)

| Variable | Security Level | Description | Required |
|----------|---------------|-------------|----------|
| `VITE_TOLGEE_API_KEY` | Public | Tolgee i18n API key | Recommended |
| `VITE_TOLGEE_PROJECT_ID` | Public | Tolgee project ID | Recommended |
| `VITE_TOLGEE_API_URL` | Public | Tolgee API endpoint | Recommended |

### Testing (CI Only)

| Variable | Security Level | Description | Required |
|----------|---------------|-------------|----------|
| `VITE_E2E` | **CRITICAL** | Enable E2E test mode (localStorage token storage) | CI Only |
| `VITE_USE_MOCK_AUTH` | Public | Enable mock authentication | CI Only |

## Backend-Style Secrets to Remove

If any of the following variables are present in Vercel frontend projects, they **MUST** be removed immediately:

### Critical (Immediate Action Required)

| Variable | Risk Level | Why Remove | Move To |
|----------|-----------|-----------|---------|
| `JWT_SECRET_KEY` | **CRITICAL** | Backend authentication secret | Render backend env vars |
| `DATABASE_URL` | **CRITICAL** | Database connection string | Render backend env vars |
| `OPENAI_API_KEY` | **CRITICAL** | LLM API key (billing risk) | Render backend env vars |
| `SUPABASE_SERVICE_ROLE_KEY` | **CRITICAL** | Admin-level Supabase access | Render backend env vars |
| `ENCRYPTION_MASTER_KEY` | **CRITICAL** | Data encryption key | Render backend env vars |
| `FLASK_SECRET_KEY` | **CRITICAL** | Backend session secret | Render backend env vars |
| `TOTP_ENCRYPTION_KEY` | **CRITICAL** | 2FA encryption key | Render backend env vars |
| `GEMINI_API_KEY` | **CRITICAL** | LLM API key (billing risk) | Render backend env vars |

### High (Remove Within 24 Hours)

| Variable | Risk Level | Why Remove | Move To |
|----------|-----------|-----------|---------|
| `UPSTASH_REDIS_REST_URL` | High | Backend Redis URL | Render backend env vars |
| `UPSTASH_REDIS_REST_TOKEN` | High | Backend Redis token | Render backend env vars |
| `REDIS_URL` | High | Backend Redis connection | Render backend env vars |
| `ADMIN_PASSWORD` | High | Admin credentials | Render backend env vars |
| `GITHUB_TOKEN` | High | GitHub API token | GitHub Actions secrets |

### Medium (Remove Within 7 Days)

| Variable | Risk Level | Why Remove | Move To |
|----------|-----------|-----------|---------|
| `COOKIE_SECURE` | Medium | Backend cookie configuration | Render backend env vars |
| `COOKIE_DOMAIN` | Medium | Backend cookie configuration | Render backend env vars |
| `COOKIE_SAMESITE` | Medium | Backend cookie configuration | Render backend env vars |
| `SENTRY_AUTH_TOKEN` | Medium | Sentry API token (build-time only) | GitHub Actions secrets |
| `SENTRY_ORG` | Medium | Sentry organization | GitHub Actions secrets |
| `SENTRY_PROJECT` | Medium | Sentry project | GitHub Actions secrets |
| `RENDER_API_KEY` | Medium | Render deployment key | GitHub Actions secrets |
| `VERCEL_TOKEN` | Medium | Vercel API token | GitHub Actions secrets |

## Security Recommendations

### 1. VITE_E2E Flag Control

**Risk**: `VITE_E2E=true` enables localStorage token storage, creating XSS vulnerability.

**Recommendation**:
- **Production**: MUST be `false` or unset
- **Preview**: MUST be `false` or unset
- **CI/E2E Tests**: May be `true` only in isolated test builds

**Verification**:
```bash
# Check Vercel production environment
vercel env ls production | grep VITE_E2E
# Should return empty or VITE_E2E=false
```

### 2. Supabase Anon Key Security

**Risk**: While `VITE_SUPABASE_ANON_KEY` is designed for public use, it requires proper RLS policies.

**Recommendation**:
- Ensure RLS is enabled on all tables (verified by `rls-supabase-health.yml` workflow)
- Use TRUE tenant isolation policies (4 policies per table)
- Never expose `SUPABASE_SERVICE_ROLE_KEY` in frontend

### 3. API Base URL Configuration

**Recommendation**:
- Use `/api` (relative path) for Vercel deployments to leverage proxy rewrites
- This enables same-site cookies and avoids CORS issues
- Direct backend URLs should only be used for local development

### 4. Quarterly Audit Schedule

**Recommendation**: Perform this audit quarterly to ensure:
- No new backend secrets have been added
- Unused variables are removed
- Security levels are still appropriate

## Verification Checklist

### Pre-Deployment Verification

- [ ] No `JWT_SECRET_KEY` in Vercel environment
- [ ] No `DATABASE_URL` in Vercel environment
- [ ] No `OPENAI_API_KEY` in Vercel environment
- [ ] No `SUPABASE_SERVICE_ROLE_KEY` in Vercel environment
- [ ] `VITE_E2E` is `false` or unset in Production
- [ ] `VITE_E2E` is `false` or unset in Preview
- [ ] All `VITE_*` variables are documented in `env.schema.yaml`

### Post-Deployment Verification

- [ ] Browser DevTools shows no sensitive data in `import.meta.env`
- [ ] Network tab shows no backend secrets in requests
- [ ] Source maps (if enabled) don't expose secrets

## How to Audit Vercel Environment Variables

### Option 1: Vercel Dashboard

1. Go to [Vercel Dashboard](https://vercel.com/morning-ai/morningai/settings/environment-variables)
2. Review all configured variables
3. Check each variable against the "Backend-Style Secrets to Remove" list
4. Remove any matching variables

### Option 2: Vercel CLI

```bash
# List all environment variables
vercel env ls

# List variables for specific environment
vercel env ls production
vercel env ls preview
vercel env ls development

# Remove a variable
vercel env rm VARIABLE_NAME production
```

### Option 3: Vercel API

```bash
# List all environment variables
curl -X GET "https://api.vercel.com/v10/projects/prj_XXXXX/env" \
  -H "Authorization: Bearer $VERCEL_TOKEN"
```

## Audit Log

| Date | Auditor | Findings | Actions Taken |
|------|---------|----------|---------------|
| 2025-11-04 | Engineering Team | `OPENAI_MAX_DAILY_COST` found | Removed via API |
| 2025-12-10 | Engineering Team | Initial comprehensive audit | Documentation created |

## Related Documents

- [Vercel Environment Variables Configuration](../deployment/VERCEL_ENVIRONMENT_VARIABLES.md)
- [Environment Schema](../../config/env.schema.yaml)
- [PWA Environment Variables](../PWA_ENVIRONMENT_VARIABLES.md)
- [Secret Rotation Policy](SECRET_ROTATION_POLICY.md)

## Version History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2025-12-10 | Engineering Team | Initial audit document |

---

**Next Audit Due**: 2026-03-10  
**Document Owner**: Engineering Team  
**Approver**: CTO
