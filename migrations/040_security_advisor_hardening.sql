-- ============================================================================
-- Migration 040: Security Advisor Hardening
-- ============================================================================
-- 
-- This migration addresses Supabase Security Advisor warnings:
-- 
-- ERRORS (4): RLS disabled on LangGraph checkpoint tables
--   - checkpoints
--   - checkpoint_migrations  
--   - checkpoint_blobs
--   - checkpoint_writes
--
-- WARNINGS (5): SECURITY DEFINER functions without search_path
--   - get_tenant_quota
--   - check_tenant_quota
--   - increment_tenant_usage
--   - get_user_tenant_id
--   - current_user_tenant_id
--
-- Note: Checkpoint tables are created at runtime by LangGraph's PostgresSaver.setup()
-- so we use conditional logic to handle cases where tables don't exist yet.
--
-- KNOWN LIMITATION: If checkpoint tables are created AFTER this migration runs
-- (e.g., in a fresh environment), they won't have RLS enabled. Consider:
-- 1. Re-running this migration after first LangGraph workflow execution
-- 2. Adding app-side enforcement after checkpointer.setup()
-- 3. Vendoring the checkpoint table schema into a migration
-- ============================================================================

-- ============================================================================
-- Part 1: Enable RLS on LangGraph Checkpoint Tables (Refactored)
-- ============================================================================
-- 
-- These tables store LangGraph workflow state. They are created automatically
-- by PostgresSaver.setup() at runtime, not via migrations. The checkpointer
-- connects using service_role, so we create permissive policies for that role.
--
-- We also REVOKE access from anon/authenticated/PUBLIC to ensure these tables
-- are not accessible via PostgREST even if RLS is misconfigured.
--
-- Refactored: Single DO block with loop to reduce code duplication.
-- ============================================================================

DO $$
DECLARE
    tbl TEXT;
    policy_name TEXT;
    tables_processed INTEGER := 0;
    tables_skipped INTEGER := 0;
BEGIN
    -- Iterate over all checkpoint tables
    FOREACH tbl IN ARRAY ARRAY['checkpoints', 'checkpoint_migrations', 'checkpoint_blobs', 'checkpoint_writes']
    LOOP
        policy_name := 'service_role_' || tbl || '_all';
        
        IF to_regclass(format('public.%I', tbl)) IS NOT NULL THEN
            -- Enable RLS
            EXECUTE format('ALTER TABLE public.%I ENABLE ROW LEVEL SECURITY', tbl);
            
            -- Drop existing policy if any (idempotency)
            EXECUTE format('DROP POLICY IF EXISTS %I ON public.%I', policy_name, tbl);
            
            -- Create permissive policy for service_role
            EXECUTE format(
                'CREATE POLICY %I ON public.%I FOR ALL TO service_role USING (true) WITH CHECK (true)',
                policy_name, tbl
            );
            
            -- REVOKE access from roles that shouldn't access checkpoint data
            -- This provides defense-in-depth even if RLS is somehow bypassed
            EXECUTE format('REVOKE ALL ON public.%I FROM anon', tbl);
            EXECUTE format('REVOKE ALL ON public.%I FROM authenticated', tbl);
            EXECUTE format('REVOKE ALL ON public.%I FROM PUBLIC', tbl);
            
            -- Ensure service_role has access
            EXECUTE format('GRANT ALL ON public.%I TO service_role', tbl);
            
            tables_processed := tables_processed + 1;
            RAISE NOTICE 'RLS enabled on % table with service_role policy and REVOKE from anon/authenticated', tbl;
        ELSE
            tables_skipped := tables_skipped + 1;
            RAISE NOTICE '% table does not exist yet (will be created by LangGraph at runtime)', tbl;
        END IF;
    END LOOP;
    
    RAISE NOTICE 'Checkpoint tables: % processed, % skipped (not yet created)', tables_processed, tables_skipped;
END $$;

-- ============================================================================
-- Part 2: Add search_path to SECURITY DEFINER Functions (Refactored)
-- ============================================================================
-- 
-- These functions were created without SET search_path, which is a security
-- best practice for SECURITY DEFINER functions to prevent search_path 
-- injection attacks.
--
-- Function signatures (verified from original migrations):
--   - get_tenant_quota(UUID) - from migration 037
--   - check_tenant_quota(UUID, VARCHAR, INTEGER) - from migration 037
--   - increment_tenant_usage(UUID, VARCHAR, INTEGER) - from migration 037
--   - get_user_tenant_id(UUID) - from migration 006
--   - current_user_tenant_id() - from migration 006
--
-- Refactored: Single DO block with loop to reduce code duplication.
-- ============================================================================

DO $$
DECLARE
    func_record RECORD;
    functions_fixed INTEGER := 0;
    functions_skipped INTEGER := 0;
BEGIN
    -- Define functions to fix with their exact signatures
    FOR func_record IN 
        SELECT * FROM (VALUES
            ('get_tenant_quota', 'uuid'),
            ('check_tenant_quota', 'uuid, character varying, integer'),
            ('increment_tenant_usage', 'uuid, character varying, integer'),
            ('get_user_tenant_id', 'uuid'),
            ('current_user_tenant_id', '')
        ) AS t(func_name, arg_types)
    LOOP
        -- Check if function exists
        IF EXISTS (
            SELECT 1 FROM pg_proc p
            JOIN pg_namespace n ON p.pronamespace = n.oid
            WHERE n.nspname = 'public' 
            AND p.proname = func_record.func_name
        ) THEN
            -- Use dynamic SQL with exact signature
            BEGIN
                IF func_record.arg_types = '' THEN
                    -- No arguments
                    EXECUTE format(
                        'ALTER FUNCTION public.%I() SET search_path = public',
                        func_record.func_name
                    );
                ELSE
                    EXECUTE format(
                        'ALTER FUNCTION public.%I(%s) SET search_path = public',
                        func_record.func_name, func_record.arg_types
                    );
                END IF;
                functions_fixed := functions_fixed + 1;
                RAISE NOTICE 'Added search_path to %(%)', func_record.func_name, func_record.arg_types;
            EXCEPTION WHEN undefined_function THEN
                -- Function exists but with different signature
                functions_skipped := functions_skipped + 1;
                RAISE WARNING 'Function % exists but signature (%) does not match', 
                    func_record.func_name, func_record.arg_types;
            END;
        ELSE
            functions_skipped := functions_skipped + 1;
            RAISE NOTICE 'Function % does not exist', func_record.func_name;
        END IF;
    END LOOP;
    
    RAISE NOTICE 'Functions: % fixed, % skipped', functions_fixed, functions_skipped;
END $$;

-- ============================================================================
-- Part 3: Verification
-- ============================================================================

DO $$
DECLARE
    v_checkpoint_tables_with_rls INTEGER := 0;
    v_checkpoint_tables_total INTEGER := 0;
    v_functions_with_searchpath INTEGER := 0;
    v_functions_total INTEGER := 0;
    tbl TEXT;
BEGIN
    -- Count checkpoint tables with RLS enabled
    FOREACH tbl IN ARRAY ARRAY['checkpoints', 'checkpoint_migrations', 'checkpoint_blobs', 'checkpoint_writes']
    LOOP
        IF to_regclass(format('public.%I', tbl)) IS NOT NULL THEN
            v_checkpoint_tables_total := v_checkpoint_tables_total + 1;
            
            IF EXISTS (
                SELECT 1 FROM pg_class c
                WHERE c.relname = tbl 
                AND c.relnamespace = (SELECT oid FROM pg_namespace WHERE nspname = 'public')
                AND c.relrowsecurity = true
            ) THEN
                v_checkpoint_tables_with_rls := v_checkpoint_tables_with_rls + 1;
            END IF;
        END IF;
    END LOOP;
    
    -- Count functions with search_path set
    SELECT COUNT(*) INTO v_functions_total
    FROM pg_proc p
    JOIN pg_namespace n ON p.pronamespace = n.oid
    WHERE n.nspname = 'public'
    AND p.proname IN ('get_tenant_quota', 'check_tenant_quota', 'increment_tenant_usage', 
                      'get_user_tenant_id', 'current_user_tenant_id');
    
    SELECT COUNT(*) INTO v_functions_with_searchpath
    FROM pg_proc p
    JOIN pg_namespace n ON p.pronamespace = n.oid
    WHERE n.nspname = 'public'
    AND p.proname IN ('get_tenant_quota', 'check_tenant_quota', 'increment_tenant_usage', 
                      'get_user_tenant_id', 'current_user_tenant_id')
    AND p.proconfig IS NOT NULL
    AND 'search_path=public' = ANY(p.proconfig);
    
    RAISE NOTICE '';
    RAISE NOTICE '╔════════════════════════════════════════════════════════════╗';
    RAISE NOTICE '║  Migration 040: Security Advisor Hardening                 ║';
    RAISE NOTICE '╠════════════════════════════════════════════════════════════╣';
    RAISE NOTICE '║  Checkpoint tables with RLS: %/%                            ║', 
        v_checkpoint_tables_with_rls, v_checkpoint_tables_total;
    RAISE NOTICE '║  Functions with search_path: %/%                            ║', 
        v_functions_with_searchpath, v_functions_total;
    RAISE NOTICE '╠════════════════════════════════════════════════════════════╣';
    RAISE NOTICE '║  Security hardening applied:                               ║';
    RAISE NOTICE '║  - RLS enabled on checkpoint tables                        ║';
    RAISE NOTICE '║  - service_role-only policies created                      ║';
    RAISE NOTICE '║  - REVOKE from anon/authenticated/PUBLIC                   ║';
    RAISE NOTICE '║  - search_path set on SECURITY DEFINER functions           ║';
    RAISE NOTICE '╚════════════════════════════════════════════════════════════╝';
    
    -- Warn if checkpoint tables don't exist yet
    IF v_checkpoint_tables_total = 0 THEN
        RAISE WARNING 'No checkpoint tables found. They will be created by LangGraph at runtime.';
        RAISE WARNING 'Re-run this migration after first LangGraph workflow execution to enable RLS.';
    END IF;
END $$;
