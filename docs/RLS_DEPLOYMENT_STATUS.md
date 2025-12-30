# RLS Phase 2 Deployment Status

**Last Updated**: 2025-12-30  
**Document Owner**: Engineering Team  
**Related Documents**:
- [RLS_IMPLEMENTATION_GUIDE.md](./RLS_IMPLEMENTATION_GUIDE.md) - Implementation details
- [PRE_DEPLOYMENT_CHECKLIST.md](../migrations/PRE_DEPLOYMENT_CHECKLIST.md) - Deployment checklist
- [POST_DEPLOY_SMOKE_TEST_CHECKLIST.md](./runbooks/POST_DEPLOY_SMOKE_TEST_CHECKLIST.md) - Post-deploy verification

---

## Overview

This document tracks the deployment status of RLS (Row Level Security) Phase 2 migrations across all Supabase environments. RLS Phase 2 implements TRUE tenant isolation, ensuring users can only access data from their own tenant.

### Migration Chain

| Migration | Description | Status |
|-----------|-------------|--------|
| 001_enable_rls_agent_tasks.sql | Enable RLS on agent_tasks | Baseline |
| 002_enable_rls_multi_tenant_tables.sql | Enable RLS on multi-tenant tables | Baseline |
| **003_add_tenant_id_to_agent_tasks.sql** | Add tenant_id column to agent_tasks | **Phase 2** |
| **004_update_rls_policies_with_tenant_isolation.sql** | Temporary tenant policies | **Phase 2** |
| 005_create_user_profiles_table.sql | Create user_profiles table | Prerequisite for 006 |
| **006_update_rls_policies_true_tenant_isolation.sql** | TRUE tenant isolation policies | **Phase 2 Final** |
| **039_rls_phase2_complete_tenant_isolation.sql** | Tenant isolation for planner_events, platform_admin for memory/error_fix_pairs/failure_memory | **Phase 2 Hardening** |

---

## Environment Deployment Status

### Staging Environment

| Item | Status | Applied By | Date | Notes |
|------|--------|------------|------|-------|
| Supabase Project Ref | `dckisglnlemvpvmyvnut` | - | - | Staging instance |
| Migration 003 | [x] Applied | Ryan | 2025-12-10 | tenant_id column added |
| Migration 004 | [x] Applied | Ryan | 2025-12-10 | Temporary policies |
| Migration 005 | [x] Applied | Ryan | 2025-12-10 | user_profiles table |
| Migration 006 | [x] Applied | Ryan | 2025-12-10 | TRUE isolation policies |
| Migration 039 | [x] Applied | Ryan | 2025-12-21 | Phase 2 hardening (full migration) |
| RLS Test Suite | [x] Verified | Ryan | 2025-12-10 | 4 policies, 2 functions |
| Health Check Workflow | [x] Passing | - | 2025-12-10 | rls-supabase-health.yml |

### Production Environment

| Item | Status | Applied By | Date | Notes |
|------|--------|------------|------|-------|
| Supabase Project Ref | - | - | - | Production instance |
| Migration 003 | [x] Applied | Ryan | 2025-12-10 | tenant_id column added |
| Migration 004 | [x] Applied | Ryan | 2025-12-10 | Temporary policies |
| Migration 005 | [x] Applied | Ryan | 2025-12-10 | user_profiles table |
| Migration 006 | [x] Applied | Ryan | 2025-12-10 | TRUE isolation policies |
| Migration 039 | [x] Applied | Ryan + Devin | 2025-12-30 | Phase 2 hardening (hotfix - memory table skipped) |
| RLS Test Suite | [x] Verified | Ryan | 2025-12-10 | 4 policies, 2 functions |
| Health Check Workflow | [x] Passing | - | 2025-12-10 | rls-supabase-health.yml |

---

## Verification Workflows

### 1. Ephemeral RLS Verification (CI)

**Workflow**: `.github/workflows/rls-verification.yml`  
**Trigger**: PR changes to `migrations/**`  
**Purpose**: Validates RLS semantics against ephemeral PostgreSQL

This workflow runs on every PR that touches migration files and verifies that RLS policies work correctly in an isolated test environment.

### 2. Supabase Health Check (Nightly/On-Demand)

**Workflow**: `.github/workflows/rls-supabase-health.yml`  
**Trigger**: Nightly cron + manual workflow_dispatch  
**Purpose**: Validates RLS is enabled and policies are correct on actual Supabase environments

This workflow performs read-only checks against staging and production Supabase instances to verify:
- RLS is enabled on critical tables
- Expected policies exist
- No policy drift has occurred

---

## Deployment Procedure

### Step 1: Staging Deployment

1. Complete all items in [PRE_DEPLOYMENT_CHECKLIST.md](../migrations/PRE_DEPLOYMENT_CHECKLIST.md)
2. Apply migrations in order:
   ```bash
   # Connect to staging Supabase SQL Editor or use psql
   psql "$SUPABASE_STAGING_DB_URL" -f migrations/003_add_tenant_id_to_agent_tasks.sql
   psql "$SUPABASE_STAGING_DB_URL" -f migrations/004_update_rls_policies_with_tenant_isolation.sql
   psql "$SUPABASE_STAGING_DB_URL" -f migrations/005_create_user_profiles_table.sql
   psql "$SUPABASE_STAGING_DB_URL" -f migrations/006_update_rls_policies_true_tenant_isolation.sql
   ```
3. Run RLS test suite:
   ```bash
   psql "$SUPABASE_STAGING_DB_URL" -f migrations/tests/test_rls_phase2.sql
   ```
4. Trigger health check workflow manually to verify
5. **Run [Post-Deploy Smoke Test Checklist](./runbooks/POST_DEPLOY_SMOKE_TEST_CHECKLIST.md)** - Section 2 (RLS Verification)
6. Update status table above

### Step 2: Production Deployment

1. Ensure staging deployment is successful and verified
2. Create production database backup
3. Apply migrations in order (same as staging)
4. Run simplified production verification (read-only checks only)
5. Monitor application logs for 10 minutes
6. Trigger health check workflow for production
7. **Run [Post-Deploy Smoke Test Checklist](./runbooks/POST_DEPLOY_SMOKE_TEST_CHECKLIST.md)** - "After RLS Phase 2 Deployment" scenario
8. Update status table above

---

## Rollback Procedure

If issues occur after deployment, use the tiered rollback approach below. Start with Step 1 and escalate only if needed.

### Step 1: Quick Rollback (Policy Only) - First Response

**When to use**: Phase 2 TRUE tenant isolation policies are causing issues (users locked out, permission errors), but the underlying schema (tenant_id column) is fine.

**Time to execute**: ~1 minute

```sql
-- Revert to Phase 1 policies (allows all authenticated users)
DROP POLICY IF EXISTS "true_tenant_isolation_read" ON agent_tasks;
DROP POLICY IF EXISTS "true_tenant_isolation_insert" ON agent_tasks;
DROP POLICY IF EXISTS "true_tenant_isolation_update" ON agent_tasks;
DROP POLICY IF EXISTS "true_tenant_isolation_delete" ON agent_tasks;

CREATE POLICY "users_read_own_tenant" ON agent_tasks
    FOR SELECT TO authenticated USING (true);

CREATE POLICY "users_insert_own_tenant" ON agent_tasks
    FOR INSERT TO authenticated WITH CHECK (true);

CREATE POLICY "users_update_own_tenant" ON agent_tasks
    FOR UPDATE TO authenticated USING (true) WITH CHECK (true);
```

**After executing**: Run [Post-Deploy Smoke Test Checklist](./runbooks/POST_DEPLOY_SMOKE_TEST_CHECKLIST.md) - "After RLS Quick Rollback" scenario to verify application is working, then investigate root cause before re-applying Phase 2 policies.

### Step 2: Full Rollback (Schema + Policy) - Escalation

**When to use**: Quick Rollback did not resolve the issue, OR the tenant_id column itself is causing problems.

**Time to execute**: ~5-10 minutes

Follow the complete [emergency rollback plan](../migrations/PRE_DEPLOYMENT_CHECKLIST.md#-緊急回滾計劃), which includes:
- Dropping the tenant_id column and related constraints
- Restoring from backup if necessary
- Full application restart

**Warning**: This is a destructive operation. Only use if Quick Rollback fails and the system is still broken.

**After executing**: Run [Post-Deploy Smoke Test Checklist](./runbooks/POST_DEPLOY_SMOKE_TEST_CHECKLIST.md) - "After RLS Full Rollback" scenario to verify system recovery.

---

## Execution Logs

All deployment and verification logs are maintained here as the single source of truth.

### Staging Deployment Log

| Date | Migration | Executor | Result | Notes |
|------|-----------|----------|--------|-------|
| 2025-12-12 | Policy Cleanup | Ryan + Devin | Success | Removed old `tenant_*` policies with `qual=true` |
| 2025-12-12 | Code Deploy | Ryan | Success | 467 commits deployed via Render |
| 2025-12-12 | Verification | Ryan + Devin | Success | 5 policies verified (4 true_tenant_isolation + service_role) |
| 2025-12-21 | Migration 039 | Ryan | Success | Full migration applied (PR #2819) |

### Production Deployment Log

| Date | Migration | Executor | Result | Notes |
|------|-----------|----------|--------|-------|
| 2025-12-12 | Policy Cleanup | Ryan + Devin | Success | Removed old permissive policies (~12 policies dropped) |
| 2025-12-12 | Code Deploy | Ryan | Success | 467 commits deployed via Render (commit 26c16705) |
| 2025-12-12 | Verification | Ryan + Devin | Success | 6 policies verified (4 true_tenant_isolation + service_role + anon_no_access) |
| 2025-12-30 | Migration 039 | Ryan + Devin | Success | Hotfix applied (memory table skipped - does not exist in prod) |

### Health Check Results Log

| Date | Environment | Workflow Run | Result | Notes |
|------|-------------|--------------|--------|-------|
| 2025-12-12 | Staging | Manual | Pass | Health checks returning 200, no errors in logs |
| 2025-12-12 | Production | Manual | Pass | Health checks returning 200, no errors in logs |

---

## Contacts

- **Engineering Lead**: TBD
- **Security Lead**: TBD
- **On-Call**: TBD

---

## Changelog

| Date | Change | Author |
|------|--------|--------|
| 2025-12-30 | Add Migration 039 deployment status (Staging: full, Production: hotfix due to missing memory table) | Ryan + Devin |
| 2025-12-12 | Add deployment logs for Staging and Production policy cleanup and code deploy | Ryan + Devin |
| 2025-12-10 | Improve emergency rollback link text readability (Gemini suggestion) | Engineering Team |
| 2025-12-10 | Fix anchor link to PRE_DEPLOYMENT_CHECKLIST.md emergency rollback section | Engineering Team |
| 2025-12-10 | Update deployment status (migrations applied), add smoke test checklist references | Engineering Team |
| 2025-12-10 | Clarify Quick vs Full Rollback procedure, unify execution logs | Engineering Team |
| 2025-12-10 | Initial document creation | Engineering Team |
