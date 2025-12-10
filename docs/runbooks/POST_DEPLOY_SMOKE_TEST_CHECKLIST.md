# Post-Deploy & Rollback Smoke Test Checklist

**Last Updated**: 2025-12-10  
**Document Owner**: Engineering Team  
**Purpose**: Standardized verification procedure after deployments or rollbacks

---

## Overview

This checklist provides a unified, ordered set of verification steps to run after any deployment or rollback operation. It consolidates checks from multiple systems (RLS, LangGraph canary, backend health) into a single actionable procedure.

**When to use this checklist**:
- After deploying RLS Phase 2 migrations
- After executing RLS Quick Rollback or Full Rollback
- After LangGraph canary rollback
- After any production deployment
- After emergency reverts

**Target completion time**: 5-10 minutes (excluding monitoring period)

---

## Scenario Selector

Use this table to quickly identify which sections are required for your scenario:

| Scenario | Required Sections | Optional Sections |
|----------|-------------------|-------------------|
| **General prod deploy** | Section 1, Section 4 | Section 5 |
| **RLS deploy** | Section 1, Section 2, Section 4 | Section 5 |
| **RLS quick rollback** | Section 1, Section 2, Section 4 | Section 5 |
| **RLS full rollback** | Section 1, Section 2, Section 4 | Section 5 |
| **Canary rollout** | Section 1, Section 3, Section 4 | Section 5 |
| **Canary rollback** | Section 1, Section 3, Section 4 | Section 5 |

---

## Verification Matrix

The following matrix classifies all checks by priority and automation status. Use this to quickly identify which checks are mandatory for your scenario.

| Check | Category | Automation | Trigger | Source |
|-------|----------|------------|---------|--------|
| Backend health (`/healthz` + key APIs) | **Must-pass** | Workflow | Every prod deploy | `post-deploy-health-assertions.yml` |
| Application smoke (`/healthz`, `/api/billing/plans`) | **Must-pass** | Workflow | Every prod deploy | `agent-mvp-smoke.yml` |
| RLS Supabase health (RLS enabled, policies) | **Must-pass** | Workflow | RLS deploy/rollback | `rls-supabase-health.yml` |
| LangGraph canary metrics | **Must-pass** (canary) | Manual | Canary rollout/rollback | Canary dashboard |
| Agent FAQ endpoint | Optional | Workflow | On-demand | `agent-mvp-smoke.yml` |
| Sentry integration test | Optional | Workflow | On-demand | `agent-mvp-smoke.yml` |
| Observability scan (Sentry, logs) | Optional | Manual | After major deploy | Sentry, Render |
| Performance metrics (latency, SLA) | Periodic | Workflow | Hourly | `post-deploy-health-assertions.yml` |

**Legend**:
- **Must-pass**: Deployment/rollback should not proceed if this fails
- **Optional**: Recommended but not blocking
- **Periodic**: Runs on schedule, not per-deploy

---

## Rollback Triggers

The following conditions should trigger immediate rollback consideration. These are quantified thresholds based on existing workflows and runbooks.

### Global Rollback Triggers (Any Deploy)

| Trigger | Threshold | Source | Action |
|---------|-----------|--------|--------|
| Health endpoint failure | `/healthz` returns non-200 or `status != "healthy"` | `post-deploy-health-assertions.yml` | P0 - Immediate rollback |
| Core API failure | `/api/billing/plans` or `/api/governance/status` returns non-200 | `post-deploy-health-assertions.yml` | P0 - Immediate rollback |
| SLA breach | Success rate < 90% over 10 requests | `post-deploy-health-assertions.yml` | P1 - Investigate, consider rollback |

### RLS-Specific Rollback Triggers

| Trigger | Threshold | Source | Action |
|---------|-----------|--------|--------|
| RLS disabled | Any critical table (`agent_tasks`, `tenants`, `user_profiles`) has `rowsecurity = false` | `rls-supabase-health.yml` | P0 - Follow [RLS Quick Rollback](../RLS_DEPLOYMENT_STATUS.md#step-1-quick-rollback-policy-only---first-response) |
| Missing policies | TRUE tenant isolation policies < 4 | `rls-supabase-health.yml` | P0 - Follow RLS Quick Rollback |
| Permission errors | Widespread user reports of "permission denied" or data access issues | User reports | P0 - Follow RLS Quick Rollback |

### LangGraph Canary Rollback Triggers

As defined in [Canary Rollback Runbook](./canary_rollback.md):

| Trigger | Threshold | Source | Action |
|---------|-----------|--------|--------|
| p95 latency breach | > 2500ms | Canary dashboard | Follow canary rollback |
| 5xx error rate breach | > 1.0% | Canary dashboard | Follow canary rollback |
| Planner failure rate breach | > 5.0% | Canary dashboard | Follow canary rollback |
| SLO compliance | `canary.slo_compliance.all_ok = false` | Canary dashboard | Follow canary rollback |

---

## Section 1: Backend Health Verification [MUST-PASS]

These checks verify the core backend is operational. **All must pass before proceeding.**

### 1.1 Automated Health Check (GitHub Action)

**Workflow**: `post-deploy-health-assertions.yml`  
**Trigger**: Automatic on push to main, or manual via workflow_dispatch  
**Schedule**: Runs hourly

**Manual trigger**:
1. Go to [Actions > Post-Deploy Health Assertions](https://github.com/RC918/morningai/actions/workflows/post-deploy-health-assertions.yml)
2. Click "Run workflow"
3. Wait for completion (typically < 2 minutes)

**Pass criteria**:
- [ ] `/healthz` returns Phase 8, Version 8.x.x, Status healthy
- [ ] `/api/governance/status` returns 200
- [ ] `/api/business-intelligence/summary` returns 200
- [ ] `/api/security/reviews/pending` returns 401/403 (protected) or 200 (with JWT)
- [ ] SLA baseline: >= 90% success rate, reasonable latency

### 1.2 Manual Health Check (if workflow unavailable)

```bash
# Core health endpoint
curl -sS https://morningai-backend-v2.onrender.com/healthz | jq '.'

# Expected: {"phase": "Phase 8", "version": "8.0.0", "status": "healthy", ...}

# Billing plans endpoint
curl -sS https://morningai-backend-v2.onrender.com/api/billing/plans | head -c 200

# Expected: 200 OK with JSON response
```

**Status**: [ ] PASS / [ ] FAIL

> **Gating**: If any check in Section 1 fails, **do not proceed**. Initiate rollback per [Rollback Triggers](#rollback-triggers).

---

## Section 2: RLS (Row Level Security) Verification [MUST-PASS for RLS changes]

These checks verify RLS is correctly configured on Supabase environments. **Must pass for any RLS-related deployment or rollback.**

### 2.1 Automated RLS Health Check (GitHub Action)

**Workflow**: `rls-supabase-health.yml`  
**Trigger**: Nightly at 6:00 UTC, or manual via workflow_dispatch  
**Environments**: Staging and Production

**Manual trigger**:
1. Go to [Actions > RLS Supabase Health Check](https://github.com/RC918/morningai/actions/workflows/rls-supabase-health.yml)
2. Click "Run workflow"
3. Select environment: `staging`, `production`, or `both`
4. Wait for completion (typically < 1 minute)

**Pass criteria**:
- [ ] RLS ENABLED on `agent_tasks`
- [ ] RLS ENABLED on `tenants`
- [ ] RLS ENABLED on `user_profiles`
- [ ] TRUE tenant isolation policies >= 4
- [ ] No warnings about missing policies

### 2.2 Manual RLS Verification (if workflow unavailable)

Run these queries in Supabase SQL Editor:

```sql
-- Check RLS status on critical tables
SELECT tablename, rowsecurity 
FROM pg_tables 
WHERE schemaname = 'public' 
AND tablename IN ('agent_tasks', 'tenants', 'user_profiles')
ORDER BY tablename;

-- Expected: All tables show rowsecurity = true

-- Check TRUE tenant isolation policies
SELECT policyname, tablename, cmd 
FROM pg_policies 
WHERE policyname LIKE 'true_tenant_isolation%'
ORDER BY tablename, policyname;

-- Expected: 4 policies (read, insert, update, delete) on agent_tasks

-- Check helper functions exist
SELECT proname, prorettype::regtype 
FROM pg_proc 
WHERE proname IN ('get_user_tenant_id', 'current_user_tenant_id');

-- Expected: 2 functions
```

**Status**: [ ] PASS / [ ] FAIL

> **Gating**: If any RLS check fails, **do not proceed**. Follow [RLS Quick Rollback](../RLS_DEPLOYMENT_STATUS.md#step-1-quick-rollback-policy-only---first-response).

---

## Section 3: LangGraph Canary Verification [MUST-PASS for canary changes]

These checks verify LangGraph canary deployment status. **Must pass for any canary rollout or rollback.**

### 3.1 Canary Metrics Dashboard

**URL**: [https://api.morningai.app/api/phase7/monitoring/dashboard](https://api.morningai.app/api/phase7/monitoring/dashboard)

**Check via curl**:
```bash
curl -sS https://api.morningai.app/api/phase7/monitoring/dashboard | jq '.'
```

**Key metrics to verify**:
- [ ] `canary.flags.use_langgraph_percent` matches expected value (0 after rollback)
- [ ] `canary.slo_compliance.all_ok` is `true`
- [ ] `canary.rates.error_5xx_rate` < 1.0%
- [ ] `canary.rates.failure_rate` < 5.0%

### 3.2 After Canary Rollback

If you just executed a canary rollback, verify:

- [ ] `USE_LANGGRAPH_PERCENT=0` in Render environment
- [ ] Worker logs show "Using simple orchestrator" (not "Using LangGraph orchestrator")
- [ ] `canary.counts.decisions_langgraph` stopped incrementing
- [ ] `canary.counts.decisions_simple` continues incrementing

**Reference**: [Canary Rollback Runbook](./canary_rollback.md)

**Status**: [ ] PASS / [ ] FAIL / [ ] N/A (canary not in use)

> **Gating**: If any canary check fails, **do not proceed**. Follow [Canary Rollback Runbook](./canary_rollback.md).

---

## Section 4: Application Smoke Tests [MUST-PASS]

These checks verify core application functionality. **Core endpoints must pass.**

### 4.1 Automated Smoke Test (GitHub Action)

**Workflow**: `agent-mvp-smoke.yml`  
**Trigger**: Automatic on push to main, or manual via workflow_dispatch

**Manual trigger**:
1. Go to [Actions > agent-mvp-smoke](https://github.com/RC918/morningai/actions/workflows/agent-mvp-smoke.yml)
2. Click "Run workflow"
3. Optionally enable "check_agent_faq" and "test_sentry"
4. Wait for completion

**Pass criteria**:
- [ ] `/healthz` returns 200
- [ ] `/api/billing/plans` returns 200
- [ ] (Optional) `/api/agent/faq` returns 202

### 4.2 Manual Functional Test

If automated tests are unavailable, perform these manual checks:

1. **Owner Console Access**:
   - [ ] Can log in to Owner Console
   - [ ] Dashboard loads without errors

2. **Tenant Dashboard Access**:
   - [ ] Can log in to Tenant Dashboard
   - [ ] Task list loads correctly

3. **Basic Task Flow** (staging only):
   - [ ] Can submit a test task
   - [ ] Task appears in task list
   - [ ] Task status updates correctly

**Status**: [ ] PASS / [ ] FAIL

> **Gating**: If core smoke tests fail, **do not proceed**. Initiate rollback per [Rollback Triggers](#rollback-triggers).

---

## Section 5: Observability Verification [OPTIONAL]

These checks verify monitoring and alerting are operational. **Recommended after major deployments or incidents.**

### 5.1 Sentry Integration

**Dashboard**: [Sentry Project](https://sentry.io) (requires login)

**Check for**:
- [ ] No new critical errors in the last 10 minutes
- [ ] No spike in error rate
- [ ] No unhandled exceptions related to recent changes

### 5.2 Render Logs

**Dashboard**: [Render Dashboard](https://dashboard.render.com)

**Check for**:
- [ ] `morningai-backend-v2` service is running
- [ ] No error logs in the last 10 minutes
- [ ] Worker processes are healthy

**Status**: [ ] PASS / [ ] FAIL

---

## Scenario-Specific Checklists

### After RLS Phase 2 Deployment

Run these sections in order:
1. [ ] Section 1: Backend Health Verification
2. [ ] Section 2: RLS Verification (critical)
3. [ ] Section 4: Application Smoke Tests
4. [ ] Section 5: Observability Verification

**Reference**: [RLS Deployment Status](../RLS_DEPLOYMENT_STATUS.md)

### After RLS Quick Rollback

Run these sections in order:
1. [ ] Section 2.2: Manual RLS Verification (confirm policies reverted)
2. [ ] Section 1: Backend Health Verification
3. [ ] Section 4: Application Smoke Tests

**Expected state after Quick Rollback**:
- RLS still enabled on tables
- Policies allow all authenticated users (not tenant-isolated)
- Application should be functional

### After RLS Full Rollback

Run these sections in order:
1. [ ] Section 2.2: Manual RLS Verification (confirm schema reverted)
2. [ ] Section 1: Backend Health Verification
3. [ ] Section 4: Application Smoke Tests
4. [ ] Section 5: Observability Verification

**Expected state after Full Rollback**:
- `tenant_id` column removed from `agent_tasks`
- RLS policies reverted to Phase 1
- Application should be functional

### After LangGraph Canary Rollback

Run these sections in order:
1. [ ] Section 3: LangGraph Canary Verification (critical)
2. [ ] Section 1: Backend Health Verification
3. [ ] Section 4: Application Smoke Tests
4. [ ] Section 5: Observability Verification

**Reference**: [Canary Rollback Runbook](./canary_rollback.md)

---

## Escalation Procedure

If any **must-pass** check fails:

1. **Do not proceed** with deployment or mark rollback as complete
2. **Document the failure**: Note which check failed and the error message
3. **Check rollback triggers**: If threshold is met, initiate appropriate rollback:
   - RLS issues: [RLS Deployment Status](../RLS_DEPLOYMENT_STATUS.md)
   - Canary issues: [Canary Rollback Runbook](./canary_rollback.md)
4. **Notify stakeholders**: Post in #engineering Slack channel
5. **Create incident report**: Document timeline, impact, and resolution

---

## Execution Log

After running the checklist, record the results below. This log serves as an audit trail for deployments and rollbacks.

| Date | Environment(s) | Scenario | Must-pass Result | Optional Run? | Executor / CI Job | Notes / Links |
|------|----------------|----------|------------------|---------------|-------------------|---------------|
| 2025-12-10 | staging, prod | RLS Phase 2 deploy | PASS | Yes | Ryan / GH Actions | Initial deployment |
| - | - | - | - | - | - | - |

**Instructions**: After completing verification, add a row with:
- **Date**: YYYY-MM-DD format
- **Environment(s)**: `staging`, `prod`, or `both`
- **Scenario**: `RLS deploy`, `RLS quick rollback`, `canary rollback`, `general prod deploy`, etc.
- **Must-pass Result**: `PASS` (all must-pass checks OK) or `FAIL` (any must-pass check failed)
- **Optional Run?**: `Yes`, `No`, or specific notes (e.g., `Perf only`)
- **Executor / CI Job**: Person name or GitHub Actions run ID
- **Notes / Links**: Workflow URLs, incident docs, etc.

---

## Contacts

- **Engineering Lead**: TBD
- **On-Call**: Check PagerDuty rotation
- **Slack Channels**:
  - `#engineering` - General engineering discussion
  - `#incidents` - Active incident response

---

## Changelog

| Date | Change | Author |
|------|--------|--------|
| 2025-12-10 | Add Scenario Selector, gating statements, fix table list, improve URL formatting | Devin |
| 2025-12-10 | Add Verification Matrix, Rollback Triggers, Execution Log; classify checks as must-pass/optional | Devin |
| 2025-12-10 | Initial document creation | Devin |
