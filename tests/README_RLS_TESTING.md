# RLS (Row Level Security) Testing Guide

This document explains how to test RLS policies in the MorningAI application to ensure proper multi-tenant data isolation and security.

## Overview

The MorningAI application uses PostgreSQL Row Level Security (RLS) to enforce multi-tenant data isolation. This ensures that:
- Users can only access data from their own tenant
- Service role (backend) can access all data for administrative operations
- Anonymous users have limited access to public data only

## Test Files

### 1. `test_rls_policies_comprehensive.py`

**Purpose**: Tests basic RLS access control across all tables with RLS enabled.

**Coverage**:
- 13 tables with RLS policies
  - 2 public tables (faqs, faq_categories) - accessible to anonymous users
  - 7 authenticated-only tables (faq_search_history, embeddings, vector_queries, trace_metrics, alerts, agent_reputation, reputation_events)
  - 4 dev_agent tables (code_embeddings, code_patterns, code_relationships, embedding_cache_stats)

**Test Scenarios**:
- ✅ Service role has full access (SELECT + INSERT) to all tables
- ✅ Authenticated users have read-only access to all tables
- ✅ Anonymous users (anon key) can access public tables only
- ✅ Anonymous users are blocked from sensitive tables
- ✅ True anonymous (no API key) is completely blocked

**Run Command**:
```bash
cd /home/ubuntu/repos/morningai
pytest tests/test_rls_policies_comprehensive.py -v
```

**Manual Run**:
```bash
python tests/test_rls_policies_comprehensive.py
```

### 2. `test_rls_multi_tenant_isolation.py`

**Purpose**: Tests multi-tenant isolation to prevent cross-tenant data leakage.

**Coverage**:
- Tenant isolation on tables with `tenant_id` column
  - agent_tasks
  - user_profiles
- Dev agent tables RLS policies
- Cross-tenant data access prevention

**Test Scenarios**:
- ✅ Users from Tenant A cannot access Tenant B's data
- ✅ Service role can access data from all tenants
- ✅ INSERT/UPDATE/DELETE operations respect tenant boundaries
- ✅ Dev agent tables have proper RLS policies

**Run Command**:
```bash
cd /home/ubuntu/repos/morningai
pytest tests/test_rls_multi_tenant_isolation.py -v
```

**Manual Run**:
```bash
python tests/test_rls_multi_tenant_isolation.py
```

## Environment Setup

Both test files require the following environment variables:

```bash
export SUPABASE_URL="https://your-project.supabase.co"
export SUPABASE_SERVICE_ROLE_KEY="your-service-role-key"
export SUPABASE_ANON_KEY="your-anon-key"
```

**Security Note**: Never commit these keys to version control. Use environment variables or secret management.

## Test Architecture

### Access Levels

1. **service_role**: Full access to all tables and operations
   - Used by backend services
   - Bypasses RLS policies
   - Can perform SELECT, INSERT, UPDATE, DELETE on all tables

2. **authenticated**: Read-only access to most tables
   - Used by logged-in users
   - Subject to RLS policies
   - Can SELECT from all tables (except sensitive ones)
   - Cannot INSERT/UPDATE/DELETE (read-only)

3. **anonymous (anon key)**: Limited access to public tables only
   - Used for public-facing features (e.g., FAQ search)
   - Can SELECT from public tables (faqs, faq_categories)
   - Blocked from sensitive tables

4. **true anonymous (no API key)**: Completely blocked
   - No access to any tables
   - All requests return 401 Unauthorized

### Multi-Tenant Isolation

Tables with `tenant_id` column enforce strict tenant isolation:

```sql
-- Example: agent_tasks RLS policy
CREATE POLICY "true_tenant_isolation_read" ON agent_tasks
    FOR SELECT
    TO authenticated
    USING (
        tenant_id = (
            SELECT tenant_id 
            FROM user_profiles 
            WHERE id = auth.uid()
        )
    );
```

This ensures:
- User A from Tenant A can only see tasks where `tenant_id = Tenant A`
- User B from Tenant B can only see tasks where `tenant_id = Tenant B`
- Cross-tenant access is impossible via RLS

## RLS Policy Coverage

### Main Application Tables (9 tables)

| Table | RLS Enabled | Service Role | Authenticated | Anonymous |
|-------|-------------|--------------|---------------|-----------|
| faqs | ✅ | Full | Read | Read |
| faq_categories | ✅ | Full | Read | Read |
| faq_search_history | ✅ | Full | Read | Blocked |
| embeddings | ✅ | Full | Read | Blocked |
| vector_queries | ✅ | Full | Read | Blocked |
| trace_metrics | ✅ | Full | Read | Blocked |
| alerts | ✅ | Full | Read | Blocked |
| agent_reputation | ✅ | Full | Read | Blocked |
| reputation_events | ✅ | Full | Read | Blocked |

### Dev Agent Tables (4 tables)

| Table | RLS Enabled | Service Role | Authenticated | Anonymous |
|-------|-------------|--------------|---------------|-----------|
| code_embeddings | ✅ | Full | Full | Blocked |
| code_patterns | ✅ | Full | Full | Blocked |
| code_relationships | ✅ | Full | Full | Blocked |
| embedding_cache_stats | ✅ | Full | Full | Blocked |

**Note**: Dev agent tables grant full access to authenticated users (not just read-only) because developers need to create/update code patterns and embeddings.

### Multi-Tenant Tables (2 tables)

| Table | RLS Enabled | Tenant Isolation | Service Role |
|-------|-------------|------------------|--------------|
| agent_tasks | ✅ | Yes (tenant_id) | Bypass |
| user_profiles | ✅ | Yes (tenant_id) | Bypass |

## Common Issues

### 1. Tests Fail with 401 Unauthorized

**Cause**: Missing or invalid API keys

**Solution**:
```bash
# Verify environment variables are set
echo $SUPABASE_URL
echo $SUPABASE_SERVICE_ROLE_KEY
echo $SUPABASE_ANON_KEY

# Re-export if needed
export SUPABASE_URL="https://..."
export SUPABASE_SERVICE_ROLE_KEY="..."
export SUPABASE_ANON_KEY="..."
```

### 2. Tests Fail with "Table does not exist"

**Cause**: Migrations not applied or testing against wrong database

**Solution**:
```bash
# Verify you're testing against the correct Supabase project
echo $SUPABASE_URL

# Check if migrations are applied
psql $DATABASE_URL -c "SELECT tablename FROM pg_tables WHERE schemaname='public' AND tablename='agent_tasks';"
```

### 3. Multi-Tenant Tests Fail

**Cause**: RLS policies not properly configured or user_profiles missing tenant_id

**Solution**:
```bash
# Run the tenant isolation SQL test first
psql $DATABASE_URL -f migrations/tests/test_phase3_tenant_isolation.sql

# Verify RLS policies exist
psql $DATABASE_URL -c "SELECT tablename, policyname FROM pg_policies WHERE tablename='agent_tasks';"
```

## CI/CD Integration

RLS tests are automatically run in CI via pytest:

```yaml
# .github/workflows/backend.yml
- name: Run RLS tests
  run: |
    export SUPABASE_URL=${{ secrets.SUPABASE_URL }}
    export SUPABASE_SERVICE_ROLE_KEY=${{ secrets.SUPABASE_SERVICE_ROLE_KEY }}
    export SUPABASE_ANON_KEY=${{ secrets.SUPABASE_ANON_KEY }}
    pytest tests/test_rls_policies_comprehensive.py -v
    pytest tests/test_rls_multi_tenant_isolation.py -v
```

## Best Practices

1. **Always test RLS after schema changes**: Any new table should have RLS policies and tests
2. **Test all access levels**: service_role, authenticated, anonymous, and true anonymous
3. **Test multi-tenant isolation**: Ensure cross-tenant data leakage is impossible
4. **Use service_role sparingly**: Only backend services should use service_role key
5. **Never expose service_role key**: Keep it secret, never send to frontend
6. **Document RLS policies**: Add comments to SQL migrations explaining policy intent

## Adding New RLS Tests

When adding a new table with RLS:

1. **Add RLS policies in migration**:
```sql
ALTER TABLE new_table ENABLE ROW LEVEL SECURITY;

CREATE POLICY "service_role_new_table_all" ON new_table
    FOR ALL TO service_role USING (true) WITH CHECK (true);

CREATE POLICY "authenticated_new_table_read" ON new_table
    FOR SELECT TO authenticated USING (true);
```

2. **Add table to test file**:
```python
# In test_rls_policies_comprehensive.py
TABLES_AUTHENTICATED_ONLY = [
    # ... existing tables ...
    'new_table'
]
```

3. **Run tests**:
```bash
pytest tests/test_rls_policies_comprehensive.py::TestAuthenticatedRoleAccess::test_authenticated_can_select[new_table] -v
```

4. **Add multi-tenant tests if table has tenant_id**:
```python
# In test_rls_multi_tenant_isolation.py
TABLES_WITH_TENANT_ID = [
    # ... existing tables ...
    'new_table'
]
```

## Security Checklist

Before deploying to production:

- [ ] All tables with sensitive data have RLS enabled
- [ ] Service role policies exist for backend operations
- [ ] Authenticated user policies are read-only (unless write access is required)
- [ ] Anonymous access is limited to public tables only
- [ ] Multi-tenant tables have tenant_id isolation policies
- [ ] All RLS tests pass in CI
- [ ] No service_role key in frontend code
- [ ] RLS policies are documented in migration files

## References

- [PostgreSQL RLS Documentation](https://www.postgresql.org/docs/current/ddl-rowsecurity.html)
- [Supabase RLS Guide](https://supabase.com/docs/guides/auth/row-level-security)
- Migration files:
  - `migrations/002_enable_rls_multi_tenant_tables.sql`
  - `migrations/006_update_rls_policies_true_tenant_isolation.sql`
  - `migrations/014_enable_rls_all_public_tables.sql`
  - `agents/dev_agent/migrations/002_add_rls_policies.sql`
