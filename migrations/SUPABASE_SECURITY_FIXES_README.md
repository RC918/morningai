# Supabase Security Advisor Fixes

## Overview

This document describes the security fixes implemented to resolve warnings from Supabase Security Advisor.

## Issues Identified

### Warnings (5 total)

1. **4 functions with unsafe search_path** (CRITICAL)
   - `is_tenant_admin()`
   - `current_user_tenant_id()` 
   - `get_user_tenant_id()`
   - `update_user_profiles_updated_at()`

2. **1 extension in public schema** (MEDIUM)
   - `vector` extension

### Info (4 total)

3. **4 tables with RLS enabled but no policies** (MEDIUM)
   - `code_embeddings`
   - `code_patterns`
   - `code_relationships`
   - `embedding_cache_stats`

## Root Cause

這些問題是技術債累積的結果：

1. **Function search_path**: 在快速開發時，SECURITY DEFINER 函數沒有明確設置 `search_path`，可能導致 search_path 注入攻擊
2. **Extension schema**: `vector` extension 被安裝在 `public` schema，造成命名空間污染和安全風險
3. **Missing RLS policies**: Dev agent 的表啟用了 RLS 但沒有定義策略，導致無人能訪問這些表

## Solutions

### Migration 007: Fix Function search_path Security

**File**: `migrations/007_fix_function_search_path_security.sql`

**What it does**:
- Adds `SET search_path = public, pg_temp` to all 4 SECURITY DEFINER functions
- Recreates functions with proper security settings
- Recreates the `user_profiles_updated_at_trigger`

**Security impact**:
- ✅ Prevents search_path injection attacks
- ✅ Ensures functions only access intended schemas
- ✅ Follows PostgreSQL security best practices

### Migration 008: Fix Extension Schema Security

**File**: `migrations/008_fix_extension_schema_security.sql`

**What it does**:
- Creates `extensions` schema if it doesn't exist
- Moves `vector` extension from `public` to `extensions` schema
- Grants usage on `extensions` schema to authenticated and service_role
- Recreates any vector columns that were dropped

**Security impact**:
- ✅ Isolates extensions from application tables
- ✅ Reduces namespace pollution
- ✅ Follows Supabase recommendations

**Note**: If you use `vector` type in your tables, reference it as `extensions.vector(dimensions)` going forward.

### Migration 009: Add RLS Policies for Dev Agent Tables

**File**: `migrations/009_add_rls_policies_dev_agent_tables.sql`

**What it does**:
- Adds 8 RLS policies total (2 per table)
- Service role: Full access (ALL operations)
- Authenticated users: Read-only access (SELECT)

**Tables fixed**:
1. `code_embeddings` - Vector embeddings for semantic code search
2. `code_patterns` - Learned code patterns and templates
3. `code_relationships` - Code dependency graph
4. `embedding_cache_stats` - API usage metrics

**Security impact**:
- ✅ Tables now accessible to service role (backend can operate)
- ✅ Authenticated users can query for insights
- ✅ Data integrity maintained (only service role can write)

## Deployment Order

**CRITICAL**: Execute migrations in order:

```bash
# 1. Fix function search_path (highest priority)
psql $DATABASE_URL -f migrations/007_fix_function_search_path_security.sql

# 2. Fix extension schema
psql $DATABASE_URL -f migrations/008_fix_extension_schema_security.sql

# 3. Add RLS policies
psql $DATABASE_URL -f migrations/009_add_rls_policies_dev_agent_tables.sql
```

**Verification**:

```sql
-- Check all functions have search_path set
SELECT 
    p.proname AS function_name,
    p.prosecdef AS security_definer,
    pg_get_function_identity_arguments(p.oid) AS arguments
FROM pg_proc p
JOIN pg_namespace n ON p.pronamespace = n.oid
WHERE n.nspname = 'public'
AND p.proname IN (
    'is_tenant_admin',
    'current_user_tenant_id',
    'get_user_tenant_id',
    'update_user_profiles_updated_at'
);
-- All should have security_definer = true

-- Check vector extension schema
SELECT e.extname, n.nspname 
FROM pg_extension e
JOIN pg_namespace n ON e.extnamespace = n.oid
WHERE e.extname = 'vector';
-- Should show: vector | extensions

-- Check RLS policies
SELECT tablename, COUNT(*) AS policy_count
FROM pg_policies
WHERE tablename IN (
    'code_embeddings',
    'code_patterns', 
    'code_relationships',
    'embedding_cache_stats'
)
GROUP BY tablename;
-- Each table should have 2 policies
```

## Rollback Plan

If issues arise, rollback migrations in reverse order:

```sql
-- Rollback Migration 009
DROP POLICY IF EXISTS "service_role_code_embeddings_all" ON code_embeddings;
DROP POLICY IF EXISTS "authenticated_code_embeddings_read" ON code_embeddings;
-- (repeat for other tables)

-- Rollback Migration 008
-- Note: Cannot easily move extension back. Contact DBA if needed.

-- Rollback Migration 007
-- Recreate functions without search_path (not recommended)
```

## Testing

After deployment, verify:

1. ✅ All API endpoints still work
2. ✅ Dev agent can access code embeddings
3. ✅ Semantic code search functions
4. ✅ No 403 Forbidden errors in logs
5. ✅ Supabase Security Advisor shows 0 warnings

## Expected Results

**Before**:
- 🔴 Warnings: 5
- 🟡 Info: 4

**After**:
- ✅ Warnings: 0
- ✅ Info: 0

## References

- [PostgreSQL SECURITY DEFINER Best Practices](https://www.postgresql.org/docs/current/sql-createfunction.html)
- [Supabase Row Level Security Guide](https://supabase.com/docs/guides/auth/row-level-security)
- [PostgreSQL Extension Schema](https://www.postgresql.org/docs/current/extend-extensions.html)

---

**Created**: 2025-10-18  
**Author**: Devin AI (requested by Ryan Chen)  
**Priority**: HIGH - Security fixes  
**Estimated Time**: 15-30 minutes
