# Secret Rotation Policy

**MorningAI Platform - Security Operations**  
**Status**: Active  
**Priority**: P1 (High Security)  
**Last Updated**: 2025-11-03  
**Next Review**: 2026-02-03 (Quarterly)

---

## Executive Summary

This document defines the secret rotation policy for the MorningAI platform, covering all sensitive credentials, API keys, tokens, and encryption keys. Regular rotation of secrets is a critical security practice that limits the window of exposure if credentials are compromised.

**Scope**: 24 critical and secret-level environment variables  
**Rotation Frequency**: Quarterly for production, as-needed for staging/development  
**Responsibility**: CTO + DevOps Team  
**Compliance**: OWASP, SOC 2, PCI DSS

---

## Table of Contents

1. [Overview](#overview)
2. [Secret Inventory](#secret-inventory)
3. [Rotation Schedule](#rotation-schedule)
4. [Rotation Procedures](#rotation-procedures)
5. [Emergency Rotation](#emergency-rotation)
6. [Verification & Testing](#verification--testing)
7. [Audit & Compliance](#audit--compliance)
8. [Quarterly Rotation Drills](#quarterly-rotation-drills)
9. [Appendix](#appendix)

---

## 1. Overview

### 1.1 Purpose

This policy establishes:
- **What secrets** need to be rotated
- **When** they should be rotated
- **How** to rotate them safely
- **Who** is responsible for rotation
- **How** to verify successful rotation

### 1.2 Principles

**Defense in Depth**: Regular rotation limits exposure window  
**Zero Trust**: Assume credentials may be compromised  
**Least Privilege**: Rotate with minimal service disruption  
**Auditability**: Log all rotation activities  
**Automation**: Automate where possible to reduce human error

### 1.3 Scope

This policy covers all secrets defined in `config/env.schema.yaml` with:
- `security_level: critical` (12 secrets)
- `security_level: secret` (12 secrets)

**Total**: 24 secrets requiring rotation management

---

## 2. Secret Inventory

### 2.1 Critical-Level Secrets (Tier 1)

These secrets have the highest security impact and require the most stringent rotation policies.

| Secret Name | Category | Used By | Rotation Frequency | Impact if Compromised |
|-------------|----------|---------|-------------------|----------------------|
| `JWT_SECRET_KEY` | Authentication | Backend API | Quarterly | **CRITICAL**: All user sessions invalidated, full authentication bypass possible |
| `ADMIN_PASSWORD` | Authentication | Backend API | Quarterly | **CRITICAL**: Full system admin access |
| `FLASK_SECRET_KEY` | Security | Backend API | Quarterly | **CRITICAL**: Session hijacking, CSRF bypass |
| `SECRET_KEY` | Security | Backend API (deprecated) | Quarterly | **CRITICAL**: Session hijacking (legacy) |
| `ENCRYPTION_MASTER_KEY` | Security | Backend API | Quarterly | **CRITICAL**: All encrypted data exposed |
| `MASTER_KEY` | Security | Backend API (deprecated) | Quarterly | **CRITICAL**: All encrypted data exposed (legacy) |
| `SUPABASE_SERVICE_ROLE_KEY` | Cloud Services | Backend API | Quarterly | **CRITICAL**: Full database admin access, bypass RLS |
| `GITHUB_TOKEN` | Integration | Orchestrator, Agents | Quarterly | **HIGH**: Repository write access, workflow manipulation |
| `OPENAI_API_KEY` | Integration | Backend API, Agents | Quarterly | **HIGH**: Unauthorized API usage, cost abuse |
| `STRIPE_SECRET_KEY` | Payment | Backend API (Phase 10) | Quarterly | **CRITICAL**: Unauthorized payments, refunds, customer data access |
| `STRIPE_WEBHOOK_SECRET_KEY` | Payment | Backend API (Phase 10) | Quarterly | **CRITICAL**: Payment webhook spoofing |
| `STRIPE_WEBHOOK_SECRET` | Payment | Backend API (deprecated) | Quarterly | **CRITICAL**: Payment webhook spoofing (legacy) |

**Total Critical Secrets**: 12

### 2.2 Secret-Level Secrets (Tier 2)

These secrets have moderate security impact and require regular rotation.

| Secret Name | Category | Used By | Rotation Frequency | Impact if Compromised |
|-------------|----------|---------|-------------------|----------------------|
| `DATABASE_URL` | Database | Backend API, Orchestrator | Quarterly | **HIGH**: Full database access (credentials in URL) |
| `REDIS_URL` | Database | Backend API, Orchestrator | Quarterly | **MEDIUM**: Queue manipulation, cache poisoning |
| `SUPABASE_ANON_KEY` | Cloud Services | Frontend, Backend | Quarterly | **MEDIUM**: Limited database access (RLS enforced) |
| `CLOUDFLARE_API_TOKEN` | Cloud Services | Infrastructure | Quarterly | **HIGH**: DNS/CDN manipulation |
| `VERCEL_TOKEN` | Cloud Services | CI/CD | Quarterly | **MEDIUM**: Deployment manipulation |
| `RENDER_API_KEY` | Cloud Services | CI/CD | Quarterly | **MEDIUM**: Deployment manipulation |
| `UPSTASH_REDIS_REST_TOKEN` | Cloud Services | Backend API | Quarterly | **MEDIUM**: Redis access via REST API |
| `FLY_API_TOKEN` | Infrastructure | Sandbox deployments | As-needed | **LOW**: Sandbox environment access only |
| `SENTRY_AUTH_TOKEN` | Monitoring | CI/CD | As-needed | **LOW**: Error tracking API access |
| `SLACK_WEBHOOK_URL` | Integration | Backend API | As-needed | **LOW**: Notification spam |
| `TELEGRAM_BOT_TOKEN` | Integration | Orchestrator | As-needed | **LOW**: Bot impersonation |
| `TEST_ADMIN_JWT` | Testing | E2E Tests | As-needed | **LOW**: Test environment only |

**Total Secret-Level Secrets**: 12

### 2.3 Deprecated Secrets (Grace Period: Until 2025-11-30)

These secrets are being phased out but must still be rotated during the grace period:

- `SECRET_KEY` → Migrate to `FLASK_SECRET_KEY`
- `MASTER_KEY` → Migrate to `ENCRYPTION_MASTER_KEY`
- `STRIPE_WEBHOOK_SECRET` → Migrate to `STRIPE_WEBHOOK_SECRET_KEY`

**Action Required**: Complete migration by 2025-11-30, then remove deprecated secrets.

---

## 3. Rotation Schedule

### 3.1 Production Environment

**Quarterly Rotation** (Every 90 days):
- All Tier 1 (Critical) secrets
- All Tier 2 (Secret) secrets with "Quarterly" frequency

**Next Scheduled Rotation**: 2026-02-03

**Rotation Windows**:
- Q1: February 1-7
- Q2: May 1-7
- Q3: August 1-7
- Q4: November 1-7

**Timing**: Perform rotations during low-traffic periods (weekends, off-peak hours)

### 3.2 Staging Environment

**As-Needed Rotation**:
- Rotate when production secrets are rotated (to maintain parity)
- Rotate when suspected compromise
- Rotate when team members leave

**Note**: Staging secrets must be different from production secrets.

### 3.3 Development Environment

**As-Needed Rotation**:
- Use test/dummy values (not real secrets)
- Rotate when shared with external parties
- Rotate when developers leave

---

## 4. Rotation Procedures

### 4.1 Pre-Rotation Checklist

Before rotating any secret:

- [ ] **Schedule**: Choose low-traffic window
- [ ] **Backup**: Backup current secret values (encrypted storage)
- [ ] **Notification**: Notify team of upcoming rotation
- [ ] **Rollback Plan**: Document rollback procedure
- [ ] **Monitoring**: Prepare monitoring dashboards
- [ ] **Testing**: Prepare test scripts to verify new secrets

### 4.2 General Rotation Workflow

```
┌─────────────────────────────────────────────────────────────┐
│  1. Generate New Secret                                      │
│     - Use cryptographically secure random generator         │
│     - Meet minimum length requirements (32+ chars)          │
└────────────────┬────────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────────┐
│  2. Update Secret in Platform                                │
│     - Render: Dashboard → Service → Environment             │
│     - Vercel: Dashboard → Project → Settings → Environment  │
│     - Supabase: Dashboard → Project → Settings → API        │
│     - Third-party: Provider dashboard                       │
└────────────────┬────────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────────┐
│  3. Deploy with New Secret                                   │
│     - Trigger redeployment (auto or manual)                 │
│     - Monitor deployment logs                               │
│     - Check health endpoints                                │
└────────────────┬────────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────────┐
│  4. Verify Service Health                                    │
│     - Check /healthz endpoint                               │
│     - Test authentication flows                             │
│     - Monitor error rates in Sentry                         │
└────────────────┬────────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────────┐
│  5. Revoke Old Secret                                        │
│     - Wait 24-48 hours for propagation                      │
│     - Revoke old secret in provider dashboard               │
│     - Verify no services using old secret                   │
└────────────────┬────────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────────┐
│  6. Document Rotation                                        │
│     - Log rotation in audit trail                           │
│     - Update rotation schedule                              │
│     - Archive old secret (encrypted)                        │
└─────────────────────────────────────────────────────────────┘
```

### 4.3 Secret-Specific Procedures

#### 4.3.1 JWT_SECRET_KEY

**Impact**: All user sessions will be invalidated  
**Downtime**: None (graceful rotation possible)

**Procedure**:
```bash
# 1. Generate new secret (48 characters recommended)
NEW_SECRET=$(python3 -c "import secrets; print(secrets.token_urlsafe(48))")

# 2. Update in Render
# - Go to Render Dashboard → morningai-backend-v2 → Environment
# - Update JWT_SECRET_KEY value
# - Click "Save Changes" (triggers auto-redeploy)

# 3. Verify deployment
curl https://morningai-backend-v2.onrender.com/healthz

# 4. Test authentication
curl -X POST https://morningai-backend-v2.onrender.com/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"password"}'

# 5. Monitor Sentry for auth errors
# Check: https://sentry.io/organizations/morningai/issues/?environment=production

# 6. Document rotation
echo "$(date): Rotated JWT_SECRET_KEY in production" >> docs/rotation_log.txt
```

**Expected Impact**: All users will need to re-login (sessions invalidated)  
**Communication**: Notify users via email/dashboard banner

#### 4.3.2 DATABASE_URL (Supabase)

**Impact**: Database connection interrupted during rotation  
**Downtime**: 2-5 minutes

**Procedure**:
```bash
# 1. Generate new database password in Supabase
# - Go to Supabase Dashboard → Project Settings → Database
# - Click "Reset Database Password"
# - Copy new connection string (Pooler mode, port 6543)

# 2. Update in Render (both services)
# Backend:
# - Render Dashboard → morningai-backend-v2 → Environment
# - Update DATABASE_URL
# - Save (triggers redeploy)

# Orchestrator:
# - Render Dashboard → morningai-orchestrator-api → Environment
# - Update DATABASE_URL
# - Save (triggers redeploy)

# 3. Verify database connectivity
curl https://morningai-backend-v2.onrender.com/healthz | jq '.database'
# Expected: "connected"

# 4. Test database operations
# Run smoke tests to verify CRUD operations

# 5. Old password automatically revoked by Supabase
```

**Rollback**: Revert to old DATABASE_URL in Render, redeploy

#### 4.3.3 OPENAI_API_KEY

**Impact**: AI features unavailable during rotation  
**Downtime**: None (if done correctly)

**Procedure**:
```bash
# 1. Generate new API key in OpenAI Dashboard
# - Go to https://platform.openai.com/api-keys
# - Click "Create new secret key"
# - Name: "MorningAI Production - 2025-11-03"
# - Copy key immediately (shown once)

# 2. Update in Render
# - Render Dashboard → morningai-backend-v2 → Environment
# - Update OPENAI_API_KEY
# - Save (triggers redeploy)

# 3. Verify AI functionality
curl -X POST https://morningai-backend-v2.onrender.com/api/embeddings/test \
  -H "Authorization: Bearer $ADMIN_JWT"

# 4. Revoke old key in OpenAI Dashboard
# - Wait 24 hours for propagation
# - Go to https://platform.openai.com/api-keys
# - Find old key, click "Revoke"

# 5. Monitor usage
# Check OpenAI Dashboard for API usage with new key
```

**Cost Impact**: None (usage-based billing continues)

#### 4.3.4 GITHUB_TOKEN

**Impact**: CI/CD workflows may fail during rotation  
**Downtime**: None (if done correctly)

**Procedure**:
```bash
# 1. Generate new Personal Access Token (PAT)
# - Go to GitHub Settings → Developer settings → Personal access tokens → Tokens (classic)
# - Click "Generate new token (classic)"
# - Name: "MorningAI CI/CD - 2025-11-03"
# - Expiration: 90 days (matches rotation schedule)
# - Scopes: repo, workflow
# - Click "Generate token"
# - Copy token immediately

# 2. Update in GitHub Secrets
# - Go to Repository → Settings → Secrets and variables → Actions
# - Update GITHUB_TOKEN secret
# - Click "Update secret"

# 3. Update in Render (if used)
# - Render Dashboard → morningai-orchestrator-api → Environment
# - Update GITHUB_TOKEN
# - Save

# 4. Test CI/CD
# - Trigger a test workflow run
# - Verify GitHub API operations work

# 5. Revoke old token
# - Wait 24 hours
# - Go to GitHub Settings → Developer settings → Personal access tokens
# - Find old token, click "Delete"
```

**Note**: Set token expiration to 90 days to force rotation

#### 4.3.5 STRIPE_SECRET_KEY (Phase 10)

**Impact**: Payment processing unavailable during rotation  
**Downtime**: Critical - must be zero downtime

**Procedure**:
```bash
# 1. Generate new Restricted Key in Stripe Dashboard
# - Go to Stripe Dashboard → Developers → API keys
# - Click "Create restricted key"
# - Name: "MorningAI Production - 2025-11-03"
# - Permissions: Charges (Write), Customers (Write), PaymentIntents (Write)
# - Click "Create key"
# - Copy key

# 2. Update in Render
# - Render Dashboard → morningai-backend-v2 → Environment
# - Update STRIPE_SECRET_KEY
# - Save (triggers redeploy)

# 3. Verify payment processing
# - Run test payment (use Stripe test card)
# - Verify webhook delivery

# 4. Rotate webhook secret
# - Stripe Dashboard → Developers → Webhooks
# - Click webhook endpoint
# - Click "Roll secret"
# - Copy new signing secret
# - Update STRIPE_WEBHOOK_SECRET_KEY in Render

# 5. Revoke old key
# - Wait 48 hours (payment processing critical)
# - Stripe Dashboard → Developers → API keys
# - Find old key, click "Delete"

# 6. Monitor payment success rate
# Check Stripe Dashboard for any failed payments
```

**Critical**: Test thoroughly before revoking old key

#### 4.3.6 SUPABASE_SERVICE_ROLE_KEY

**Impact**: Backend admin operations unavailable  
**Downtime**: 2-5 minutes

**Procedure**:
```bash
# 1. Generate new service role key
# - Supabase Dashboard → Project Settings → API
# - Click "Reset service_role key"
# - Confirm reset
# - Copy new key

# 2. Update in Render
# - Render Dashboard → morningai-backend-v2 → Environment
# - Update SUPABASE_SERVICE_ROLE_KEY
# - Save (triggers redeploy)

# 3. Verify admin operations
curl https://morningai-backend-v2.onrender.com/healthz | jq '.database'

# 4. Test RLS bypass operations
# Run admin smoke tests

# 5. Old key automatically revoked by Supabase
```

**Warning**: Service role key bypasses Row Level Security (RLS)

#### 4.3.7 REDIS_URL / UPSTASH_REDIS_REST_TOKEN

**Impact**: Queue and cache operations interrupted  
**Downtime**: 2-5 minutes

**Procedure**:
```bash
# 1. Reset password in Upstash Dashboard
# - Go to Upstash Console → Redis → Your Database
# - Click "Reset Password"
# - Copy new password
# - Update REDIS_URL: rediss://default:NEW_PASSWORD@HOST:6379

# 2. Update in Render (both services)
# Backend:
# - Update REDIS_URL
# Orchestrator:
# - Update REDIS_URL
# - Update UPSTASH_REDIS_REST_TOKEN (if using REST API)

# 3. Verify Redis connectivity
curl https://morningai-backend-v2.onrender.com/healthz | jq '.redis'
# Expected: {"status":"connected","protocol":"rediss","tls_enabled":true}

# 4. Test queue operations
# Enqueue test task, verify processing

# 5. Old password automatically revoked by Upstash
```

#### 4.3.8 Cloud Provider Tokens (Vercel, Render, Cloudflare)

**Impact**: Deployment and infrastructure operations  
**Downtime**: None (if done correctly)

**Procedure**:
```bash
# Vercel Token:
# 1. Vercel Dashboard → Settings → Tokens
# 2. Create new token with same scopes
# 3. Update in GitHub Secrets
# 4. Test deployment
# 5. Revoke old token after 24 hours

# Render API Key:
# 1. Render Dashboard → Account Settings → API Keys
# 2. Create new API key
# 3. Update in GitHub Secrets
# 4. Test deployment
# 5. Revoke old key after 24 hours

# Cloudflare API Token:
# 1. Cloudflare Dashboard → My Profile → API Tokens
# 2. Create new token with same permissions
# 3. Update in Render environment
# 4. Test DNS operations
# 5. Revoke old token after 24 hours
```

### 4.4 Bulk Rotation Procedure (Quarterly)

For quarterly rotation of all secrets:

```bash
# Week 1: Preparation
- [ ] Schedule rotation window (low-traffic period)
- [ ] Notify team (1 week advance notice)
- [ ] Backup all current secrets (encrypted)
- [ ] Prepare monitoring dashboards
- [ ] Review rollback procedures

# Week 2: Tier 1 (Critical) Secrets
Day 1: JWT_SECRET_KEY, FLASK_SECRET_KEY
Day 2: ENCRYPTION_MASTER_KEY
Day 3: SUPABASE_SERVICE_ROLE_KEY
Day 4: GITHUB_TOKEN, OPENAI_API_KEY
Day 5: STRIPE_SECRET_KEY, STRIPE_WEBHOOK_SECRET_KEY (if Phase 10 active)

# Week 3: Tier 2 (Secret) Secrets
Day 1: DATABASE_URL, REDIS_URL
Day 2: SUPABASE_ANON_KEY
Day 3: CLOUDFLARE_API_TOKEN, VERCEL_TOKEN, RENDER_API_KEY
Day 4: UPSTASH_REDIS_REST_TOKEN
Day 5: Buffer day for issues

# Week 4: Verification & Cleanup
Day 1-2: Verify all services healthy
Day 3-4: Revoke old secrets
Day 5: Document rotation, update audit log
```

---

## 5. Emergency Rotation

### 5.1 When to Perform Emergency Rotation

Immediately rotate secrets if:

- ✅ Secret accidentally committed to repository
- ✅ Secret exposed in logs or error messages
- ✅ Secret shared with unauthorized party
- ✅ Team member with secret access leaves (involuntary)
- ✅ Suspected security breach or compromise
- ✅ Secret detected by secret scanning tools
- ✅ Third-party provider reports breach

### 5.1 Response Time SLO

Emergency rotation response times are tiered based on security impact:

| Tier | Target | Maximum | Rationale |
|------|--------|---------|-----------|
| Tier 1 (Critical) | 4 hours | 8 hours | High security impact - authentication, encryption, payment systems |
| Tier 2 (Secret) | 8 hours | 24 hours | Moderate security impact - database connections, API tokens |

**Note**: The 4-hour target for all secrets may be too aggressive for complex scenarios (e.g., DATABASE_URL requiring coordination across multiple services, STRIPE_SECRET_KEY requiring payment system testing). Tiered SLOs provide realistic planning while maintaining security.

**Escalation**: If maximum time is exceeded, escalate to Security Team immediately.

### 5.2 Emergency Rotation Procedure

**Timeline**: Complete within SLO target (4-8 hours depending on tier)

```
Hour 0: Detection & Assessment
- [ ] Identify compromised secret(s)
- [ ] Assess blast radius (what services affected)
- [ ] Notify security team immediately
- [ ] Begin incident response

Hour 1: Immediate Mitigation
- [ ] Generate new secret
- [ ] Update in all environments (production first)
- [ ] Force redeploy all affected services
- [ ] Monitor for unauthorized access

Hour 2: Verification
- [ ] Verify all services healthy with new secret
- [ ] Check audit logs for unauthorized access
- [ ] Review Sentry for related errors
- [ ] Test critical user flows

Hour 3: Revocation & Cleanup
- [ ] Revoke old secret immediately (no 24-hour wait)
- [ ] Remove secret from git history (if committed)
- [ ] Update .gitleaksignore if needed
- [ ] Scan for other potential exposures

Hour 4: Documentation & Post-Mortem
- [ ] Document incident in security log
- [ ] Update rotation audit trail
- [ ] Schedule post-mortem meeting
- [ ] Identify process improvements
```

### 5.3 Git History Cleanup (If Secret Committed)

If a secret was committed to git:

```bash
# 1. Rotate secret immediately (assume compromised)

# 2. Remove from git history using git-filter-repo
pip install git-filter-repo

# Remove specific file
git filter-repo --path .env --invert-paths

# Or remove specific string
git filter-repo --replace-text <(echo "SECRET_VALUE==>REDACTED")

# 3. Force push (coordinate with team)
git push --force-with-lease origin main

# 4. All team members must re-clone repository
# Notify team: "Repository history rewritten, please re-clone"

# 5. Verify secret removed
git log --all --full-history --source --all -- .env
```

**Warning**: Force pushing rewrites history. Coordinate with entire team.

---

## 6. Verification & Testing

### 6.1 Post-Rotation Health Checks

After rotating any secret, verify:

**Backend API**:
```bash
# Health check
curl https://morningai-backend-v2.onrender.com/healthz | jq '.'

# Expected response:
{
  "status": "healthy",
  "database": "connected",
  "redis": {"status": "connected", "tls_enabled": true},
  "services": {"backend_services": "available"}
}
```

**Orchestrator API**:
```bash
# Health check
curl https://morningai-orchestrator-api.onrender.com/health | jq '.'

# Expected response:
{
  "status": "healthy",
  "redis": "connected",
  "queue_stats": {"pending_tasks": 0, "processing_tasks": 0}
}
```

**Authentication Flow**:
```bash
# Test login
curl -X POST https://morningai-backend-v2.onrender.com/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"password"}' | jq '.'

# Should return access_token
```

**Database Operations**:
```bash
# Test database read
curl https://morningai-backend-v2.onrender.com/api/tenants \
  -H "Authorization: Bearer $JWT_TOKEN" | jq '.'
```

**AI Operations** (if OPENAI_API_KEY rotated):
```bash
# Test embeddings
curl -X POST https://morningai-backend-v2.onrender.com/api/embeddings/test \
  -H "Authorization: Bearer $JWT_TOKEN"
```

### 6.2 Monitoring After Rotation

Monitor for 24-48 hours after rotation:

**Sentry Error Tracking**:
- Check for authentication errors
- Check for database connection errors
- Check for API key errors

**Render Logs**:
- Monitor deployment logs
- Check for startup errors
- Verify no secret-related errors

**Application Metrics**:
- Monitor error rates
- Check response times
- Verify no spike in 401/403 errors

### 6.3 Rollback Procedure

If rotation causes issues:

```bash
# 1. Identify issue
# - Check Sentry errors
# - Review Render logs
# - Check health endpoints

# 2. Revert to old secret
# - Render Dashboard → Service → Environment
# - Update secret to old value
# - Save (triggers redeploy)

# 3. Verify service recovery
curl https://morningai-backend-v2.onrender.com/healthz

# 4. Investigate root cause
# - Why did new secret fail?
# - Was it generated correctly?
# - Was it updated in all locations?

# 5. Retry rotation
# - Fix root cause
# - Generate new secret
# - Retry rotation procedure
```

---

## 7. Audit & Compliance

### 7.1 Rotation Audit Log

Maintain audit log in `docs/rotation_audit_log.md`:

```markdown
| Date | Secret | Environment | Rotated By | Reason | Status |
|------|--------|-------------|------------|--------|--------|
| 2025-11-03 | JWT_SECRET_KEY | Production | CTO | Quarterly | ✅ Success |
| 2025-11-03 | DATABASE_URL | Production | CTO | Quarterly | ✅ Success |
| 2025-10-15 | GITHUB_TOKEN | Production | DevOps | Emergency (exposed in logs) | ✅ Success |
```

### 7.2 Compliance Requirements

**SOC 2 (CC6.1 - Logical Access Controls)**:
- ✅ Secrets rotated quarterly
- ✅ Rotation documented in audit log
- ✅ Access to secrets restricted (Render dashboard, GitHub secrets)

**PCI DSS (Requirement 8.2.4)**:
- ✅ Passwords/keys changed quarterly
- ✅ Old secrets revoked after rotation
- ✅ Rotation enforced for payment-related secrets

**OWASP (Secrets Management)**:
- ✅ Secrets not hardcoded in code
- ✅ Secrets stored in secure vaults (Render, GitHub Secrets)
- ✅ Regular rotation schedule enforced

### 7.3 Reporting

**Quarterly Report** (due 7 days after rotation window):

```markdown
# Q1 2026 Secret Rotation Report

**Rotation Window**: February 1-7, 2026  
**Rotated By**: CTO + DevOps Team

## Summary
- Total secrets rotated: 24
- Successful rotations: 24
- Failed rotations: 0
- Emergency rotations: 0
- Downtime: 0 minutes

## Secrets Rotated
- [x] JWT_SECRET_KEY (Production, Staging)
- [x] DATABASE_URL (Production, Staging)
- [x] OPENAI_API_KEY (Production, Staging)
- ... (full list)

## Issues Encountered
- None

## Recommendations
- Consider automating rotation for non-critical secrets
- Implement secret expiration in providers (GitHub PAT, Stripe keys)

**Next Rotation**: May 1-7, 2026
```

---

## 8. Quarterly Rotation Drills

### 8.1 Purpose

Verify rotation procedures and SLO achievability through regular practice. Drills ensure:
- Rotation procedures remain accurate and up-to-date
- Team members are familiar with rotation workflows
- SLO targets are realistic and achievable
- Issues are identified in non-emergency scenarios

### 8.2 Schedule

**Frequency**: Every quarter (Q1, Q2, Q3, Q4)  
**Timing**: 2 weeks before actual quarterly rotation  
**Duration**: 2-4 hours  
**Environment**: Staging only (never production)

**Quarterly Schedule**:
- Q1 (January): Drill in mid-January, actual rotation early February
- Q2 (April): Drill in mid-April, actual rotation early May
- Q3 (July): Drill in mid-July, actual rotation early August
- Q4 (October): Drill in mid-October, actual rotation early November

### 8.3 Drill Scope

Each drill rotates 2 representative secrets:
- **1 Tier 1 (Critical)**: JWT_SECRET_KEY or DATABASE_URL
- **1 Tier 2 (Secret)**: REDIS_URL or CLOUDFLARE_API_TOKEN

**Participants**:
- CTO (rotation executor)
- DevOps Lead (backup executor)
- 1 team member (observer/trainee)

### 8.4 Drill Procedure

```bash
# Pre-drill (30 minutes)
- [ ] Schedule drill time (low-traffic period)
- [ ] Notify team of drill
- [ ] Prepare staging environment
- [ ] Review rotation procedures

# Drill execution (60-90 minutes)
- [ ] Start timer
- [ ] Rotate Tier 1 secret following documented procedure
- [ ] Record actual time taken
- [ ] Document any issues or deviations
- [ ] Rotate Tier 2 secret following documented procedure
- [ ] Record actual time taken
- [ ] Verify all staging services healthy

# Post-drill (30-60 minutes)
- [ ] Compare actual vs. target SLO times
- [ ] Document lessons learned
- [ ] Update procedures if needed
- [ ] Schedule procedure updates (if required)
```

### 8.5 Documentation

Record for each drill in `docs/rotation_drill_log.md`:

```markdown
| Date | Quarter | Secrets Rotated | Tier 1 Time | Tier 2 Time | Issues | Procedure Updates |
|------|---------|----------------|-------------|-------------|--------|-------------------|
| 2025-01-15 | Q1 2025 | JWT_SECRET_KEY, REDIS_URL | 2.5h | 1.5h | None | ✅ No changes needed |
| 2025-04-15 | Q2 2025 | DATABASE_URL, CLOUDFLARE_API_TOKEN | 3.5h | 2h | DATABASE_URL took longer due to multi-service coordination | ⚠️ Updated DATABASE_URL procedure with parallel deployment steps |
```

### 8.6 Success Criteria

A drill is considered successful if:
- ✅ All rotations completed within maximum SLO time
- ✅ No production impact
- ✅ All staging services remain healthy
- ✅ Procedures followed accurately (or deviations documented)
- ✅ Team members understand rotation workflow

### 8.7 Continuous Improvement

After each drill:
1. Review actual times vs. SLO targets
2. Identify bottlenecks or inefficiencies
3. Update procedures to reflect learnings
4. Adjust SLO targets if consistently unrealistic
5. Train additional team members if needed

---

## 9. Appendix

### 9.1 Secret Generation Commands

**JWT Secret (48 characters)**:
```bash
python3 -c "import secrets; print(secrets.token_urlsafe(48))"
```

**Encryption Key (32 bytes hex)**:
```bash
openssl rand -hex 32
```

**API Key (32 characters)**:
```bash
python3 -c "import secrets; print(secrets.token_urlsafe(32))"
```

**Strong Password (20 characters)**:
```bash
python3 -c "import secrets, string; chars=string.ascii_letters+string.digits+string.punctuation; print(''.join(secrets.choice(chars) for _ in range(20)))"
```

### 9.2 Secret Storage Locations

**Production Secrets**:
- Backend API: Render Dashboard → morningai-backend-v2 → Environment
- Orchestrator: Render Dashboard → morningai-orchestrator-api → Environment
- Frontend: Vercel Dashboard → morningai → Settings → Environment Variables
- CI/CD: GitHub Repository → Settings → Secrets and variables → Actions

**Staging Secrets**:
- Backend API: Render Dashboard → morningai-backend-v2-stg → Environment
- Orchestrator: Render Dashboard → morningai-orchestrator-api-stg → Environment

**Local Development**:
- `.env` files (gitignored)
- Never use production secrets locally

### 9.3 Minimum Secret Requirements

From `config/env.schema.yaml`:

- **JWT_SECRET_KEY**: min_length 32 characters
- **FLASK_SECRET_KEY**: min_length 32 characters
- **ENCRYPTION_MASTER_KEY**: min_length 32 characters
- **All other secrets**: Recommended 32+ characters

### 9.4 Related Documentation

- [Secret Scanning Guide](SECRET_SCANNING_GUIDE.md) - Prevention of secret exposure
- [Environments Guide](ENVIRONMENTS.md) - Environment configuration
- [Environment Schema](../config/env.schema.yaml) - Complete secret inventory

### 9.5 Contact & Escalation

**Primary Contact**: CTO  
**Secondary Contact**: DevOps Team  
**Emergency Contact**: Security Team

**Escalation Path**:
1. CTO (primary responsibility)
2. DevOps Team (backup)
3. Security Team (emergency)

### 9.6 Secret Inventory Verification

This section provides automated verification that all secrets documented in this policy match the canonical source (`config/env.schema.yaml`).

**Verification Script**: `scripts/verify_secret_inventory.py`

**Usage**:
```bash
python scripts/verify_secret_inventory.py
```

#### Critical-Level Secrets (Tier 1)

| Secret Name | Category | Required | Security Level | Verified |
|-------------|----------|----------|----------------|----------|
| `ADMIN_PASSWORD` | Authentication | ✅ Yes | critical | ✅ |
| `ENCRYPTION_MASTER_KEY` | Security | ⚠️ Optional | critical | ✅ |
| `FLASK_SECRET_KEY` | Security | ⚠️ Optional | critical | ✅ |
| `GITHUB_TOKEN` | Integration | ✅ Yes | critical | ✅ |
| `JWT_SECRET_KEY` | Authentication | ✅ Yes | critical | ✅ |
| `MASTER_KEY` | Security | ⚠️ Optional | critical | ✅ |
| `OPENAI_API_KEY` | Integration | ✅ Yes | critical | ✅ |
| `SECRET_KEY` | Security | ✅ Yes | critical | ✅ |
| `STRIPE_SECRET_KEY` | Payment | ⚠️ Optional | critical | ✅ |
| `STRIPE_WEBHOOK_SECRET` | Payment | ⚠️ Optional | critical | ✅ |
| `STRIPE_WEBHOOK_SECRET_KEY` | Payment | ⚠️ Optional | critical | ✅ |
| `SUPABASE_SERVICE_ROLE_KEY` | Cloud Services | ✅ Yes | critical | ✅ |

**Total Critical Secrets**: 12

#### Secret-Level Secrets (Tier 2)

| Secret Name | Category | Required | Security Level | Verified |
|-------------|----------|----------|----------------|----------|
| `CLOUDFLARE_API_TOKEN` | Cloud Services | ✅ Yes | secret | ✅ |
| `DATABASE_URL` | Database | ✅ Yes | secret | ✅ |
| `FLY_API_TOKEN` | Infrastructure | ⚠️ Optional | secret | ✅ |
| `REDIS_URL` | Database | ⚠️ Optional | secret | ✅ |
| `RENDER_API_KEY` | Cloud Services | ✅ Yes | secret | ✅ |
| `SENTRY_AUTH_TOKEN` | Monitoring | ⚠️ Optional | secret | ✅ |
| `SLACK_WEBHOOK_URL` | Integration | ⚠️ Optional | secret | ✅ |
| `SUPABASE_ANON_KEY` | Cloud Services | ✅ Yes | secret | ✅ |
| `TELEGRAM_BOT_TOKEN` | Integration | ⚠️ Optional | secret | ✅ |
| `TEST_ADMIN_JWT` | Testing | ⚠️ Optional | secret | ✅ |
| `UPSTASH_REDIS_REST_TOKEN` | Cloud Services | ✅ Yes | secret | ✅ |
| `VERCEL_TOKEN` | Cloud Services | ✅ Yes | secret | ✅ |

**Total Secret-Level Secrets**: 12

**Grand Total**: 24 secrets

#### Verification Status

- ✅ All secrets from `config/env.schema.yaml` are documented
- ✅ Security levels match between schema and policy
- ✅ Categories are correctly assigned
- ✅ Last verified: 2025-11-03

**Maintenance**: Run verification script after any changes to `config/env.schema.yaml` or this policy document.

### 9.7 RACI Matrix

Responsibility Assignment Matrix for secret rotation activities.

**Legend**:
- **R** (Responsible): Executes the task
- **A** (Accountable): Ultimately answerable for completion
- **C** (Consulted): Provides input
- **I** (Informed): Kept up-to-date

#### Tier 1 (Critical) Secrets

| Secret | Storage Location | Data Owner (A) | Rotation Executor (R) | Approver (A) | Informed (I) |
|--------|-----------------|----------------|----------------------|--------------|--------------|
| JWT_SECRET_KEY | Render Env Vars | CTO | DevOps Lead | CTO | Security Team |
| ADMIN_PASSWORD | Render Env Vars | CTO | DevOps Lead | CTO | Security Team |
| FLASK_SECRET_KEY | Render Env Vars | CTO | DevOps Lead | CTO | Security Team |
| SECRET_KEY | Render Env Vars | CTO | DevOps Lead | CTO | Security Team |
| ENCRYPTION_MASTER_KEY | Render Env Vars | CTO | DevOps Lead | CTO | Security Team |
| MASTER_KEY | Render Env Vars | CTO | DevOps Lead | CTO | Security Team |
| SUPABASE_SERVICE_ROLE_KEY | Supabase Dashboard | CTO | DevOps Lead | CTO | Backend Team |
| GITHUB_TOKEN | GitHub Settings | CTO | DevOps Lead | CTO | DevOps Team |
| OPENAI_API_KEY | OpenAI Dashboard | CTO | DevOps Lead | CTO | AI Team |
| STRIPE_SECRET_KEY | Stripe Dashboard | CTO | DevOps Lead | CTO | Finance Team |
| STRIPE_WEBHOOK_SECRET_KEY | Stripe Dashboard | CTO | DevOps Lead | CTO | Finance Team |
| STRIPE_WEBHOOK_SECRET | Stripe Dashboard | CTO | DevOps Lead | CTO | Finance Team |

#### Tier 2 (Secret) Secrets

| Secret | Storage Location | Data Owner (A) | Rotation Executor (R) | Approver (A) | Informed (I) |
|--------|-----------------|----------------|----------------------|--------------|--------------|
| DATABASE_URL | Supabase Dashboard | CTO | DevOps Lead | CTO | Backend Team |
| REDIS_URL | Upstash Dashboard | CTO | DevOps Lead | CTO | Backend Team |
| SUPABASE_ANON_KEY | Supabase Dashboard | CTO | DevOps Lead | CTO | Frontend Team |
| CLOUDFLARE_API_TOKEN | Cloudflare Dashboard | CTO | DevOps Lead | CTO | Infrastructure Team |
| VERCEL_TOKEN | Vercel Dashboard | CTO | DevOps Lead | CTO | Frontend Team |
| RENDER_API_KEY | Render Dashboard | CTO | DevOps Lead | CTO | Infrastructure Team |
| UPSTASH_REDIS_REST_TOKEN | Upstash Dashboard | CTO | DevOps Lead | CTO | Backend Team |
| FLY_API_TOKEN | Fly.io Dashboard | CTO | DevOps Lead | CTO | Infrastructure Team |
| SENTRY_AUTH_TOKEN | Sentry Dashboard | CTO | DevOps Lead | CTO | DevOps Team |
| SLACK_WEBHOOK_URL | Slack Workspace | CTO | DevOps Lead | CTO | Operations Team |
| TELEGRAM_BOT_TOKEN | Telegram BotFather | CTO | DevOps Lead | CTO | Operations Team |
| TEST_ADMIN_JWT | Generated | CTO | DevOps Lead | CTO | QA Team |

**Notes**:
- CTO is accountable for all secret rotations (policy owner)
- DevOps Lead executes rotations following documented procedures
- Team-specific notifications ensure awareness of potential service impacts
- Emergency rotations may require direct CTO execution

### 9.8 Platform UI Navigation Paths

Detailed navigation paths for accessing secret management interfaces in each platform.

#### Render Dashboard

**Environment Variables Configuration**:
1. Navigate to: https://dashboard.render.com/
2. Select service: `morningai-backend-v2` or `morningai-orchestrator-api`
3. Click **"Environment"** tab in left sidebar
4. Locate variable by name (e.g., `JWT_SECRET_KEY`)
5. Click **"Edit"** button (pencil icon)
6. Update value in text field
7. Click **"Save Changes"** (triggers automatic redeploy)
8. Monitor deployment in **"Events"** tab

**Screenshot**: See `docs/screenshots/render-env-vars.png` (if available)

**Notes**:
- Changes trigger automatic redeploy (2-5 minute downtime)
- Old value is not retained (no rollback via UI)
- Use "Manual Deploy" to redeploy without changing variables

#### Supabase Dashboard

**Database Password Reset**:
1. Navigate to: https://app.supabase.com/project/YOUR_PROJECT_ID
2. Click **"Settings"** (gear icon) in left sidebar
3. Select **"Database"** section
4. Scroll to **"Connection string"** section
5. Click **"Reset database password"** button
6. Confirm reset in modal dialog
7. Copy new connection string (Pooler mode, port 6543)
8. Update `DATABASE_URL` in Render

**API Keys Management**:
1. Navigate to: https://app.supabase.com/project/YOUR_PROJECT_ID
2. Click **"Settings"** → **"API"**
3. View **"Project API keys"** section
4. For `service_role` key: Click **"Reset service_role key"**
5. Confirm reset (irreversible)
6. Copy new key immediately (shown once)
7. Update `SUPABASE_SERVICE_ROLE_KEY` in Render

**Notes**:
- Service role key reset is immediate and irreversible
- Anon key (`SUPABASE_ANON_KEY`) is read-only, rarely needs rotation
- Database password reset affects all connection strings

#### GitHub Personal Access Tokens

**Token Creation (2025 Latest)**:
1. Navigate to: https://github.com/settings/tokens
2. Click **"Generate new token"** → **"Generate new token (classic)"**
3. Configure token:
   - **Note**: "MorningAI Orchestrator - Q1 2026"
   - **Expiration**: 90 days (recommended for quarterly rotation)
   - **Scopes**: Select required permissions:
     - ✅ `repo` (Full control of private repositories)
     - ✅ `workflow` (Update GitHub Action workflows)
     - ✅ `read:org` (Read org and team membership)
4. Click **"Generate token"**
5. Copy token immediately (shown once only)
6. Update `GITHUB_TOKEN` in Render
7. Test token: `curl -H "Authorization: token YOUR_TOKEN" https://api.github.com/user`

**Token Revocation**:
1. Navigate to: https://github.com/settings/tokens
2. Locate old token by note/date
3. Click **"Delete"** button
4. Confirm deletion

**Notes**:
- Fine-grained tokens (beta) offer better security but may have limitations
- Classic tokens recommended for CI/CD workflows
- Set expiration to enforce rotation (90 days = quarterly)

#### OpenAI API Keys

**Key Creation**:
1. Navigate to: https://platform.openai.com/api-keys
2. Click **"+ Create new secret key"**
3. Configure key:
   - **Name**: "MorningAI Production - Q1 2026"
   - **Permissions**: All (or restrict to specific models)
   - **Project**: Select appropriate project
4. Click **"Create secret key"**
5. Copy key immediately (shown once only)
6. Update `OPENAI_API_KEY` in Render
7. Test key: `curl https://api.openai.com/v1/models -H "Authorization: Bearer YOUR_KEY"`

**Key Revocation**:
1. Navigate to: https://platform.openai.com/api-keys
2. Locate old key by name/date
3. Click **"Revoke"** button
4. Confirm revocation

**Notes**:
- Keys are project-scoped (ensure correct project selected)
- Monitor usage at: https://platform.openai.com/usage
- Set usage limits to prevent cost overruns

#### Stripe Dashboard

**Secret Key Rotation**:
1. Navigate to: https://dashboard.stripe.com/test/apikeys (or `/live/apikeys` for production)
2. View **"Secret key"** section
3. Click **"Roll key"** button
4. Confirm roll (creates new key, old key remains valid for 24 hours)
5. Copy new secret key
6. Update `STRIPE_SECRET_KEY` in Render
7. Test new key with API call
8. After 24 hours, old key automatically revoked

**Webhook Secret Rotation**:
1. Navigate to: https://dashboard.stripe.com/webhooks
2. Select webhook endpoint
3. Click **"Roll secret"** in **"Signing secret"** section
4. Confirm roll
5. Copy new signing secret
6. Update `STRIPE_WEBHOOK_SECRET_KEY` in Render
7. Test webhook delivery

**Notes**:
- Stripe provides 24-hour grace period for key rotation
- Test mode and live mode keys are separate
- Webhook secrets are endpoint-specific

#### Vercel Dashboard

**Token Creation**:
1. Navigate to: https://vercel.com/account/tokens
2. Click **"Create Token"**
3. Configure token:
   - **Token Name**: "MorningAI CI/CD - Q1 2026"
   - **Scope**: Select team/account
   - **Expiration**: No expiration (manual rotation)
4. Click **"Create"**
5. Copy token immediately
6. Update `VERCEL_TOKEN` in GitHub Secrets
7. Test deployment trigger

**Token Revocation**:
1. Navigate to: https://vercel.com/account/tokens
2. Locate old token by name
3. Click **"Delete"** button
4. Confirm deletion

**Notes**:
- Tokens are account or team-scoped
- Used primarily in CI/CD (GitHub Actions)
- No automatic expiration (set calendar reminder)

#### Cloudflare Dashboard

**API Token Creation**:
1. Navigate to: https://dash.cloudflare.com/profile/api-tokens
2. Click **"Create Token"**
3. Use template: **"Edit zone DNS"** or create custom
4. Configure permissions:
   - **Zone**: DNS:Edit
   - **Zone Resources**: Include specific zones
5. Set **IP Address Filtering** (optional, recommended)
6. Set **TTL** (optional, recommended for quarterly rotation)
7. Click **"Continue to summary"** → **"Create Token"**
8. Copy token immediately
9. Update `CLOUDFLARE_API_TOKEN` in Render
10. Test token: `curl -X GET "https://api.cloudflare.com/client/v4/user/tokens/verify" -H "Authorization: Bearer YOUR_TOKEN"`

**Token Revocation**:
1. Navigate to: https://dash.cloudflare.com/profile/api-tokens
2. Locate token by name
3. Click **"Roll"** (creates new) or **"Delete"** (revokes)
4. Confirm action

**Notes**:
- API tokens preferred over Global API Key (more secure)
- Set TTL to enforce rotation (90 days recommended)
- Test token immediately after creation

---

## Approval & Sign-off

**Prepared by**: CTO  
**Review Date**: 2025-11-03  
**Approved by**: _Pending_  
**Next Review**: 2026-02-03 (Quarterly)

**Stakeholders**:
- CTO: Policy owner, rotation execution
- DevOps Team: Rotation execution, monitoring
- Security Team: Audit, compliance verification

---

**Last Updated**: 2025-11-03  
**Version**: 1.0  
**Status**: Active
