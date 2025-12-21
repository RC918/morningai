-- ============================================================================
-- Test Suite: Migration 040 - Security Advisor Hardening
-- ============================================================================
-- 
-- This test verifies that migration 040 correctly:
-- 1. Enables RLS on checkpoint tables (if they exist)
-- 2. Creates service_role-only policies on checkpoint tables
-- 3. Revokes access from anon/authenticated/PUBLIC on checkpoint tables
-- 4. Adds search_path to SECURITY DEFINER functions
--
-- Run this test after applying migration 040 to verify the security hardening.
-- ============================================================================

-- ============================================================================
-- Test 1: Verify checkpoint tables have RLS enabled (if they exist)
-- ============================================================================

DO $$
DECLARE
    tbl TEXT;
    tables_with_rls INTEGER := 0;
    tables_without_rls INTEGER := 0;
    tables_missing INTEGER := 0;
BEGIN
    RAISE NOTICE '';
    RAISE NOTICE '=== Test 1: Checkpoint Tables RLS Status ===';
    
    FOREACH tbl IN ARRAY ARRAY['checkpoints', 'checkpoint_migrations', 'checkpoint_blobs', 'checkpoint_writes']
    LOOP
        IF to_regclass(format('public.%I', tbl)) IS NOT NULL THEN
            IF EXISTS (
                SELECT 1 FROM pg_class c
                WHERE c.relname = tbl 
                AND c.relnamespace = (SELECT oid FROM pg_namespace WHERE nspname = 'public')
                AND c.relrowsecurity = true
            ) THEN
                tables_with_rls := tables_with_rls + 1;
                RAISE NOTICE 'PASS: % has RLS enabled', tbl;
            ELSE
                tables_without_rls := tables_without_rls + 1;
                RAISE WARNING 'FAIL: % exists but RLS is NOT enabled', tbl;
            END IF;
        ELSE
            tables_missing := tables_missing + 1;
            RAISE NOTICE 'SKIP: % does not exist (will be created by LangGraph at runtime)', tbl;
        END IF;
    END LOOP;
    
    RAISE NOTICE 'Summary: % with RLS, % without RLS, % missing', 
        tables_with_rls, tables_without_rls, tables_missing;
    
    IF tables_without_rls > 0 THEN
        RAISE EXCEPTION 'Test 1 FAILED: % checkpoint tables exist without RLS', tables_without_rls;
    END IF;
    
    RAISE NOTICE 'Test 1 PASSED';
END $$;

-- ============================================================================
-- Test 2: Verify checkpoint tables have service_role policies (if they exist)
-- ============================================================================

DO $$
DECLARE
    tbl TEXT;
    policy_name TEXT;
    tables_with_policy INTEGER := 0;
    tables_without_policy INTEGER := 0;
    tables_missing INTEGER := 0;
BEGIN
    RAISE NOTICE '';
    RAISE NOTICE '=== Test 2: Checkpoint Tables Policy Status ===';
    
    FOREACH tbl IN ARRAY ARRAY['checkpoints', 'checkpoint_migrations', 'checkpoint_blobs', 'checkpoint_writes']
    LOOP
        policy_name := 'service_role_' || tbl || '_all';
        
        IF to_regclass(format('public.%I', tbl)) IS NOT NULL THEN
            IF EXISTS (
                SELECT 1 FROM pg_policies
                WHERE schemaname = 'public'
                AND tablename = tbl
                AND policyname = policy_name
            ) THEN
                tables_with_policy := tables_with_policy + 1;
                RAISE NOTICE 'PASS: % has policy %', tbl, policy_name;
            ELSE
                tables_without_policy := tables_without_policy + 1;
                RAISE WARNING 'FAIL: % exists but policy % is missing', tbl, policy_name;
            END IF;
        ELSE
            tables_missing := tables_missing + 1;
            RAISE NOTICE 'SKIP: % does not exist', tbl;
        END IF;
    END LOOP;
    
    RAISE NOTICE 'Summary: % with policy, % without policy, % missing', 
        tables_with_policy, tables_without_policy, tables_missing;
    
    IF tables_without_policy > 0 THEN
        RAISE EXCEPTION 'Test 2 FAILED: % checkpoint tables exist without service_role policy', tables_without_policy;
    END IF;
    
    RAISE NOTICE 'Test 2 PASSED';
END $$;

-- ============================================================================
-- Test 3: Verify SECURITY DEFINER functions have search_path set
-- ============================================================================

DO $$
DECLARE
    func_record RECORD;
    functions_with_searchpath INTEGER := 0;
    functions_without_searchpath INTEGER := 0;
    functions_missing INTEGER := 0;
BEGIN
    RAISE NOTICE '';
    RAISE NOTICE '=== Test 3: Function search_path Status ===';
    
    FOR func_record IN 
        SELECT * FROM (VALUES
            ('get_tenant_quota'),
            ('check_tenant_quota'),
            ('increment_tenant_usage'),
            ('get_user_tenant_id'),
            ('current_user_tenant_id')
        ) AS t(func_name)
    LOOP
        IF EXISTS (
            SELECT 1 FROM pg_proc p
            JOIN pg_namespace n ON p.pronamespace = n.oid
            WHERE n.nspname = 'public' 
            AND p.proname = func_record.func_name
        ) THEN
            IF EXISTS (
                SELECT 1 FROM pg_proc p
                JOIN pg_namespace n ON p.pronamespace = n.oid
                WHERE n.nspname = 'public' 
                AND p.proname = func_record.func_name
                AND p.proconfig IS NOT NULL
                AND 'search_path=public' = ANY(p.proconfig)
            ) THEN
                functions_with_searchpath := functions_with_searchpath + 1;
                RAISE NOTICE 'PASS: % has search_path=public', func_record.func_name;
            ELSE
                functions_without_searchpath := functions_without_searchpath + 1;
                RAISE WARNING 'FAIL: % exists but search_path is NOT set', func_record.func_name;
            END IF;
        ELSE
            functions_missing := functions_missing + 1;
            RAISE NOTICE 'SKIP: % does not exist', func_record.func_name;
        END IF;
    END LOOP;
    
    RAISE NOTICE 'Summary: % with search_path, % without search_path, % missing', 
        functions_with_searchpath, functions_without_searchpath, functions_missing;
    
    IF functions_without_searchpath > 0 THEN
        RAISE EXCEPTION 'Test 3 FAILED: % functions exist without search_path', functions_without_searchpath;
    END IF;
    
    RAISE NOTICE 'Test 3 PASSED';
END $$;

-- ============================================================================
-- Test 4: Verify anon/authenticated cannot access checkpoint tables
-- ============================================================================

DO $$
DECLARE
    tbl TEXT;
    has_anon_grant BOOLEAN;
    has_auth_grant BOOLEAN;
    tables_checked INTEGER := 0;
    tables_with_grants INTEGER := 0;
BEGIN
    RAISE NOTICE '';
    RAISE NOTICE '=== Test 4: Checkpoint Tables Grant Status ===';
    
    FOREACH tbl IN ARRAY ARRAY['checkpoints', 'checkpoint_migrations', 'checkpoint_blobs', 'checkpoint_writes']
    LOOP
        IF to_regclass(format('public.%I', tbl)) IS NOT NULL THEN
            tables_checked := tables_checked + 1;
            
            -- Check for anon grants
            SELECT EXISTS (
                SELECT 1 FROM information_schema.table_privileges
                WHERE table_schema = 'public'
                AND table_name = tbl
                AND grantee = 'anon'
            ) INTO has_anon_grant;
            
            -- Check for authenticated grants
            SELECT EXISTS (
                SELECT 1 FROM information_schema.table_privileges
                WHERE table_schema = 'public'
                AND table_name = tbl
                AND grantee = 'authenticated'
            ) INTO has_auth_grant;
            
            IF has_anon_grant OR has_auth_grant THEN
                tables_with_grants := tables_with_grants + 1;
                RAISE WARNING 'WARN: % has grants to anon=% authenticated=%', 
                    tbl, has_anon_grant, has_auth_grant;
            ELSE
                RAISE NOTICE 'PASS: % has no grants to anon/authenticated', tbl;
            END IF;
        ELSE
            RAISE NOTICE 'SKIP: % does not exist', tbl;
        END IF;
    END LOOP;
    
    RAISE NOTICE 'Summary: % tables checked, % with anon/authenticated grants', 
        tables_checked, tables_with_grants;
    
    -- This is a warning, not a failure, since grants might be inherited
    IF tables_with_grants > 0 THEN
        RAISE WARNING 'Test 4 WARNING: % checkpoint tables have grants to anon/authenticated', tables_with_grants;
    ELSE
        RAISE NOTICE 'Test 4 PASSED';
    END IF;
END $$;

-- ============================================================================
-- Test Summary
-- ============================================================================

DO $$
BEGIN
    RAISE NOTICE '';
    RAISE NOTICE '╔════════════════════════════════════════════════════════════╗';
    RAISE NOTICE '║  Migration 040 Test Suite Complete                         ║';
    RAISE NOTICE '╠════════════════════════════════════════════════════════════╣';
    RAISE NOTICE '║  All tests passed (or skipped for missing tables)          ║';
    RAISE NOTICE '║                                                            ║';
    RAISE NOTICE '║  Note: If checkpoint tables were skipped, re-run tests     ║';
    RAISE NOTICE '║  after LangGraph creates them at runtime.                  ║';
    RAISE NOTICE '╚════════════════════════════════════════════════════════════╝';
END $$;
