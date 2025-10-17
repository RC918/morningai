# Row Level Security (RLS) Implementation Guide

**Date**: 2025-10-17  
**Status**: Ready for Deployment  
**Priority**: P0 (Critical Security Issue)

---

## Executive Summary

This guide provides complete instructions for implementing Row Level Security (RLS) in MorningAI's Supabase database. RLS is **critical** for multi-tenant data isolation and prevents tenant data leaks.

**Current Risk**: Without RLS, any authenticated user can potentially access data from other tenants using the service role key or direct database queries.

**Estimated Time**: 2-3 hours (including testing)

---

## What is Row Level Security?

Row Level Security (RLS) is a PostgreSQL feature that restricts which rows users can access in database tables based on security policies. In Supabase:

- **Service Role** (used by backend): Bypasses RLS, has full access
- **Authenticated Users**: Subject to RLS policies
- **Anonymous Users**: Most restrictive access

---

## Migration Files

We've created two SQL migration files:

### 1. `migrations/001_enable_rls_agent_tasks.sql`
- Enables RLS on `agent_tasks` table
- Creates basic policies for service role, authenticated, and anonymous users
- Includes commented-out `tenant_id` column for future enhancement
- **Safe to deploy**: Does not break existing functionality

### 2. `migrations/002_enable_rls_multi_tenant_tables.sql`
- Enables RLS on all multi-tenant tables:
  - `tenants`
  - `users`
  - `platform_bindings`
  - `external_integrations`
  - `memory` (agent embeddings)
- Creates helper functions: `is_tenant_admin()`, `current_user_tenant_id()`
- Adds audit logging for RLS violations
- Creates performance indexes

---

## Deployment Steps

### Step 1: Backup Database

```bash
# From Supabase Dashboard
# Project Settings → Database → Backups → Create Manual Backup
```

Or using CLI:
```bash
supabase db dump -f backup_before_rls_$(date +%Y%m%d).sql
```

### Step 2: Apply Migration 001 (agent_tasks)

**Via Supabase Dashboard**:
1. Go to: https://app.supabase.com → Your Project → SQL Editor
2. Copy contents of `migrations/001_enable_rls_agent_tasks.sql`
3. Paste and click "Run"
4. Verify: No errors appear

**Via Supabase CLI**:
```bash
supabase db push migrations/001_enable_rls_agent_tasks.sql
```

### Step 3: Verify Migration 001

Run this query in SQL Editor:
```sql
-- Check if RLS is enabled
SELECT tablename, rowsecurity
FROM pg_tables
WHERE schemaname = 'public' AND tablename = 'agent_tasks';

-- List all policies
SELECT * FROM pg_policies WHERE tablename = 'agent_tasks';
```

Expected:
- `rowsecurity` should be `true`
- At least 3 policies exist (service_role, authenticated, anon)

### Step 4: Test Migration 001

Test queries:
```sql
-- As service role (should succeed)
SELECT COUNT(*) FROM agent_tasks;

-- As authenticated user (should succeed with current policies)
SET ROLE authenticated;
SELECT COUNT(*) FROM agent_tasks;
RESET ROLE;

-- As anonymous (should return 0 rows or error)
SET ROLE anon;
SELECT COUNT(*) FROM agent_tasks;
RESET ROLE;
```

### Step 5: Apply Migration 002 (Multi-Tenant Tables)

**IMPORTANT**: Only apply if tables exist:
- Check which tables exist in your database first
- Comment out policies for non-existent tables
- Apply migration via SQL Editor or CLI

```bash
supabase db push migrations/002_enable_rls_multi_tenant_tables.sql
```

### Step 6: Verify Migration 002

```sql
-- Check RLS status for all tables
SELECT tablename, rowsecurity
FROM pg_tables
WHERE schemaname = 'public'
  AND tablename IN ('tenants', 'users', 'platform_bindings', 'external_integrations', 'memory')
ORDER BY tablename;

-- Check helper functions exist
SELECT proname FROM pg_proc
WHERE proname IN ('is_tenant_admin', 'current_user_tenant_id');
```

---

## Testing RLS Policies

### Test 1: Service Role Full Access

```python
# In Python (backend)
from supabase import create_client
import os

client = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_SERVICE_ROLE_KEY")  # Service role bypasses RLS
)

# Should succeed - service role has full access
response = client.table("agent_tasks").select("*").execute()
print(f"Service role: {len(response.data)} tasks")
```

### Test 2: Authenticated User Restricted Access

```python
# Using authenticated user token (JWT)
client_auth = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_ANON_KEY")  # Public anon key
)

# Set auth header with user JWT
client_auth.auth.set_session(access_token, refresh_token)

# Should only see tenant's own data (once tenant_id is added)
response = client_auth.table("agent_tasks").select("*").execute()
print(f"Authenticated user: {len(response.data)} tasks")
```

### Test 3: Anonymous User No Access

```python
client_anon = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_ANON_KEY")
)

# Should return empty or error
try:
    response = client_anon.table("agent_tasks").select("*").execute()
    print(f"Anonymous: {len(response.data)} tasks (should be 0)")
except Exception as e:
    print(f"Anonymous access denied: {e}")
```

---

## Rollback Plan

If issues occur after deployment:

### Quick Rollback (Disable RLS)
```sql
-- Disable RLS on agent_tasks (emergency only)
ALTER TABLE agent_tasks DISABLE ROW LEVEL SECURITY;

-- Disable RLS on other tables if needed
ALTER TABLE tenants DISABLE ROW LEVEL SECURITY;
ALTER TABLE users DISABLE ROW LEVEL SECURITY;
```

### Full Rollback
```sql
-- Drop all RLS policies
DROP POLICY IF EXISTS "service_role_all_access" ON agent_tasks;
DROP POLICY IF EXISTS "users_read_own_tenant" ON agent_tasks;
DROP POLICY IF EXISTS "users_insert_own_tenant" ON agent_tasks;
DROP POLICY IF EXISTS "users_update_own_tenant" ON agent_tasks;
DROP POLICY IF EXISTS "anon_no_access" ON agent_tasks;

-- Disable RLS
ALTER TABLE agent_tasks DISABLE ROW LEVEL SECURITY;

-- Drop helper functions
DROP FUNCTION IF EXISTS is_tenant_admin();
DROP FUNCTION IF EXISTS current_user_tenant_id();

-- Drop audit table
DROP TABLE IF EXISTS rls_audit_log;
```

---

## Phase 2: Adding tenant_id Column

After initial RLS deployment and verification:

### Step 1: Add tenant_id to agent_tasks

```sql
-- Add tenant_id column
ALTER TABLE agent_tasks
ADD COLUMN tenant_id UUID REFERENCES auth.users(id);

-- Populate existing data with default tenant
-- Replace 'default-tenant-uuid' with actual tenant UUID
UPDATE agent_tasks
SET tenant_id = 'default-tenant-uuid'
WHERE tenant_id IS NULL;

-- Make tenant_id required
ALTER TABLE agent_tasks
ALTER COLUMN tenant_id SET NOT NULL;

-- Add index for performance
CREATE INDEX idx_agent_tasks_tenant_id ON agent_tasks(tenant_id);
```

### Step 2: Update RLS Policies

```sql
-- Drop old policies
DROP POLICY "users_read_own_tenant" ON agent_tasks;
DROP POLICY "users_insert_own_tenant" ON agent_tasks;
DROP POLICY "users_update_own_tenant" ON agent_tasks;

-- Create new tenant-aware policies
CREATE POLICY "users_read_own_tenant_v2" ON agent_tasks
    FOR SELECT
    TO authenticated
    USING (
        tenant_id = (SELECT tenant_id FROM users WHERE id = auth.uid())
    );

CREATE POLICY "users_insert_own_tenant_v2" ON agent_tasks
    FOR INSERT
    TO authenticated
    WITH CHECK (
        tenant_id = (SELECT tenant_id FROM users WHERE id = auth.uid())
    );

CREATE POLICY "users_update_own_tenant_v2" ON agent_tasks
    FOR UPDATE
    TO authenticated
    USING (
        tenant_id = (SELECT tenant_id FROM users WHERE id = auth.uid())
    )
    WITH CHECK (
        tenant_id = (SELECT tenant_id FROM users WHERE id = auth.uid())
    );
```

### Step 3: Update Backend Code

```python
# In db_writer.py
def upsert_task_queued(
    task_id: str,
    trace_id: str,
    question: str,
    tenant_id: str,  # Add this parameter
    job_id: Optional[str] = None
) -> bool:
    """Insert or update task with tenant_id"""
    data = {
        "task_id": task_id,
        "trace_id": trace_id,
        "question": question,
        "tenant_id": tenant_id,  # Include in data
        "status": "queued",
        # ... rest of fields
    }
    # ... rest of function
```

---

## Monitoring & Alerts

### Query to Check RLS Status

```sql
-- Daily check: RLS enabled on critical tables
SELECT
    schemaname,
    tablename,
    rowsecurity as rls_enabled,
    (SELECT COUNT(*) FROM pg_policies WHERE tablename = t.tablename) as policy_count
FROM pg_tables t
WHERE schemaname = 'public'
  AND tablename IN ('agent_tasks', 'tenants', 'users', 'platform_bindings')
ORDER BY tablename;
```

### Audit Log Monitoring

```sql
-- Check for unusual access patterns
SELECT
    table_name,
    operation,
    COUNT(*) as attempts,
    MAX(attempted_at) as last_attempt
FROM rls_audit_log
WHERE attempted_at > NOW() - INTERVAL '24 hours'
GROUP BY table_name, operation
ORDER BY attempts DESC;
```

---

## Performance Considerations

### Indexes

RLS policies rely on indexes for good performance. We've created:

```sql
-- agent_tasks
CREATE INDEX idx_agent_tasks_tenant_id ON agent_tasks(tenant_id);

-- users
CREATE INDEX idx_users_tenant_id ON users(tenant_id);
CREATE INDEX idx_users_id_tenant ON users(id, tenant_id);

-- platform_bindings
CREATE INDEX idx_platform_bindings_tenant ON platform_bindings(tenant_id);

-- external_integrations
CREATE INDEX idx_external_integrations_tenant ON external_integrations(tenant_id);
```

### Query Optimization

Always include `tenant_id` in WHERE clauses when using authenticated users:

```python
# Good: Explicit tenant filter
client.table("agent_tasks").select("*").eq("tenant_id", tenant_id).execute()

# Better: RLS handles it automatically
# Just query normally, RLS enforces isolation
client.table("agent_tasks").select("*").execute()
```

---

## Security Best Practices

1. **Never disable RLS in production** - Even temporarily
2. **Use service role sparingly** - Only in backend code, never expose to frontend
3. **Audit regularly** - Review `rls_audit_log` weekly
4. **Test policies** - Before each deployment, verify RLS works as expected
5. **Monitor performance** - RLS adds overhead, ensure queries remain fast
6. **Document exceptions** - If a policy needs loosening, document why

---

## FAQ

### Q: Will RLS affect backend performance?
**A**: Minimal impact (<5%) if proper indexes exist. We've added all necessary indexes.

### Q: What if backend needs to access all tenants?
**A**: Use service role key (`SUPABASE_SERVICE_ROLE_KEY`) which bypasses RLS.

### Q: Can RLS be bypassed?
**A**: Only with service role key. Never expose this key to frontend or client code.

### Q: Do we need RLS if we already filter by tenant in code?
**A**: **YES**. Code filters can have bugs. RLS is defense-in-depth at database level.

### Q: What about agent_tasks created before tenant_id exists?
**A**: Current policies allow all authenticated users to see them. Once tenant_id is added, migrate existing tasks to a default tenant.

---

## Success Criteria

- [ ] RLS enabled on `agent_tasks` table
- [ ] RLS enabled on all multi-tenant tables
- [ ] All policies created successfully
- [ ] Backend can still access all data via service role
- [ ] Authenticated users can only see own tenant data (after tenant_id added)
- [ ] Anonymous users have no access
- [ ] All tests pass
- [ ] No performance degradation (< 5% impact)
- [ ] Audit log exists and works

---

## Next Steps

1. **Immediate**: Deploy migrations 001 and 002
2. **Week 1**: Monitor audit logs and performance
3. **Week 2**: Add `tenant_id` to `agent_tasks` and update policies
4. **Week 3**: Implement tenant_id in backend code
5. **Week 4**: Full multi-tenant testing with multiple tenants

---

**Owner**: Engineering Team  
**Reviewer**: CTO / Security Lead  
**Last Updated**: 2025-10-17
