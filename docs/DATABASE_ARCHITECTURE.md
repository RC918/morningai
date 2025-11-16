# MorningAI Database Architecture

## Overview

MorningAI uses **two separate Supabase PostgreSQL databases** to ensure proper isolation between production and testing environments.

## Database Instances

### 1. Production Database

**Purpose**: Live production data for all MorningAI services

**Details**:
- **Project Name**: `morningai`
- **Project ID**: `qevmlbsunnwgrsdibdoi`
- **URL**: https://qevmlbsunnwgrsdibdoi.supabase.co
- **Environment**: Production
- **Schema**: Full production schema with all tables
- **Access**: Production services only
- **Backups**: Automatic daily backups
- **Connection**: Pooler (port 6543)

**Tables** (Full Schema):
- `tenants` - Tenant metadata
- `user_profiles` - User profiles with RLS policies
- `agent_tasks` - Agent task tracking
- `faqs` - FAQ content
- `faq_categories` - FAQ categories
- `faq_search_history` - Search history
- `embeddings` - Vector embeddings
- `vector_queries` - Vector search queries
- `trace_metrics` - Performance metrics
- `alerts` - System alerts
- `agent_reputation` - Agent reputation scores
- `reputation_events` - Reputation event log
- `code_embeddings` - Code vector embeddings
- `code_patterns` - Code pattern analysis
- `code_relationships` - Code relationship graph
- `embedding_cache_stats` - Cache statistics
- ...and more

**Environment Variables**:
```bash
SUPABASE_URL=https://qevmlbsunnwgrsdibdoi.supabase.co
SUPABASE_ANON_KEY=<production-anon-key>
SUPABASE_SERVICE_ROLE_KEY=<production-service-role-key>
```

### 2. Staging Database

**Purpose**: Security testing and RLS validation (P0 testing)

**Details**:
- **Project Name**: `morningai-staging`
- **Project ID**: `dckisglnlemvpvmyvnut`
- **URL**: https://dckisglnlemvpvmyvnut.supabase.co
- **Environment**: Staging
- **Schema**: Minimal test schema (intentionally limited)
- **Access**: Staging services and RLS tests
- **Connection**: Pooler (port 6543)

**Tables** (Minimal Schema):
- `tenants` - Test tenant data
- `user_profiles` - User profiles with **non-recursive RLS policies** (P0 fix)
- `agent_tasks` - Agent tasks with tenant isolation

**Purpose of Minimal Schema**:
1. **Lightweight**: Fast test execution without unnecessary tables
2. **Focused**: Only tables needed for P0 security testing (RLS policies)
3. **Isolated**: No production data contamination
4. **Cost-effective**: Minimal storage and compute usage

**Environment Variables**:
```bash
SUPABASE_URL=https://dckisglnlemvpvmyvnut.supabase.co
SUPABASE_ANON_KEY=<staging-anon-key>
SUPABASE_SERVICE_ROLE_KEY=<staging-service-role-key>
```

## RLS Testing Architecture

### Migration 007: Fix Infinite Recursion

**Problem**: Production database had recursive RLS policies on `user_profiles` that caused infinite recursion errors (42P17).

**Solution**: Migration 007 creates non-recursive policies using a `SECURITY DEFINER` function:

```sql
-- Non-recursive function that bypasses RLS
CREATE OR REPLACE FUNCTION current_user_tenant_id()
RETURNS UUID AS $$
DECLARE
    result UUID;
BEGIN
    SET search_path = public;
    
    SELECT tenant_id INTO result
    FROM user_profiles 
    WHERE id = auth.uid();
    
    RETURN result;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER STABLE;

-- Non-recursive policies
CREATE POLICY "Users can read own profile"
  ON user_profiles FOR SELECT
  USING (id = auth.uid());

CREATE POLICY "Users can update own profile"
  ON user_profiles FOR UPDATE
  USING (id = auth.uid());
```

**Testing Strategy**:
1. **Staging**: Apply Migration 007 and verify with RLS tests
2. **Production**: Apply Migration 007 after staging validation

### RLS Test Suite

**Test File**: `tests/test_rls_with_real_users.py`

**Test Coverage**:
- ✅ Authenticated users can read agent_tasks (no infinite recursion)
- ✅ Authenticated users can read user_profiles (no infinite recursion)
- ✅ Cross-tenant read isolation (User A cannot read Tenant B tasks)
- ✅ Cross-tenant write isolation (User A cannot insert into Tenant B)
- ✅ Users only see own tenant tasks
- ✅ Service role bypasses RLS (can see all tenants)
- ✅ Environment safeguards (prevent production testing)

**Environment Variables for Testing**:
```bash
# Required for RLS tests
RLS_TESTS_ALLOWED=true
TEST_SUPABASE_URL=https://dckisglnlemvpvmyvnut.supabase.co
SUPABASE_URL=https://dckisglnlemvpvmyvnut.supabase.co
SUPABASE_ANON_KEY=<staging-anon-key>
SUPABASE_SERVICE_ROLE_KEY=<staging-service-role-key>
```

## Database Selection Guide

### When to Use Production Database

- ✅ Production services (backend, orchestrator)
- ✅ Production deployments
- ✅ Real user data
- ❌ **NEVER** for testing or development

### When to Use Staging Database

- ✅ RLS security testing
- ✅ Migration validation
- ✅ Integration tests
- ✅ Staging deployments
- ❌ **NEVER** for production services

### When to Use Local Database

- ✅ Local development
- ✅ Unit tests
- ✅ Schema experimentation
- ❌ **NEVER** for staging or production

## Common Issues and Solutions

### Issue 1: Tests Failing with Infinite Recursion (42P17)

**Symptom**: Tests fail with "infinite recursion detected in policy for relation user_profiles"

**Root Cause**: Tests are connecting to production database instead of staging

**Solution**:
```bash
# Verify you're using staging database
export SUPABASE_URL=https://dckisglnlemvpvmyvnut.supabase.co
export SUPABASE_ANON_KEY=<staging-anon-key>
export SUPABASE_SERVICE_ROLE_KEY=<staging-service-role-key>
```

### Issue 2: Tests Failing with "Table Does Not Exist" (42P01)

**Symptom**: Tests fail with "relation does not exist" for tables like `faqs`, `embeddings`, etc.

**Root Cause**: Staging database has minimal schema (only 3 tables)

**Solution**: This is expected behavior. Staging database intentionally has minimal schema. Tests that require full production schema should be skipped or mocked in staging.

### Issue 3: Schema Cache Error (PGRST204)

**Symptom**: Tests fail with "Could not find the 'column_name' column in the schema cache"

**Root Cause**: Table schema in staging doesn't match test expectations

**Solution**: Update staging table schema to match production, or update tests to handle schema differences.

## Migration Strategy

### Applying Migrations to Staging

1. **Manual Execution** (Recommended for P0 fixes):
   - Open Supabase SQL Editor for `morningai-staging`
   - Copy SQL from migration file
   - Execute in SQL Editor
   - Verify with test queries

2. **Automated Execution** (Future):
   - Use Alembic or custom migration tool
   - Apply to staging first
   - Validate with RLS tests
   - Apply to production after validation

### Applying Migrations to Production

⚠️ **CRITICAL**: Always test in staging first!

1. Verify staging tests pass
2. Create backup of production database
3. Apply migration during maintenance window
4. Run smoke tests
5. Monitor for errors

## Security Best Practices

### 1. Never Mix Credentials

- ❌ **NEVER** use production credentials in staging
- ❌ **NEVER** use staging credentials in production
- ✅ Use separate API keys for each environment
- ✅ Rotate keys quarterly

### 2. RLS Policy Testing

- ✅ Always test RLS policies in staging first
- ✅ Use real JWT tokens (not anon key) for testing
- ✅ Test cross-tenant isolation
- ✅ Verify service role bypass

### 3. Data Isolation

- ✅ Staging and production databases are completely separate
- ✅ No data replication between environments
- ✅ Test data is synthetic (not production data)

## Related Documentation

- [ENVIRONMENTS.md](ENVIRONMENTS.md) - Complete environment configuration
- [RLS_TESTING.md](../tests/README_RLS_TESTING.md) - RLS testing guide
- [Migration 007](../migrations/007_fix_user_profiles_rls_recursion.sql) - RLS fix migration
- [Staging Setup Guide](ops/STAGING_SETUP_GUIDE.md) - Staging environment setup

## Summary

MorningAI's two-database architecture ensures:
1. **Production Safety**: Production data is never touched by tests
2. **Fast Testing**: Minimal staging schema enables fast test execution
3. **Security Focus**: Staging is optimized for P0 security testing (RLS)
4. **Cost Efficiency**: Minimal staging schema reduces costs
5. **Clear Separation**: No confusion between production and staging

This architecture is intentional and should be maintained to ensure safe, efficient testing and deployment workflows.
