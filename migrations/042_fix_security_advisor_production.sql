-- ============================================================================
-- Migration 041: Fix Security Advisor Production Issues
-- ============================================================================
-- 
-- This migration addresses Security Advisor issues observed in production:
-- 
-- ERRORS (1): Security Definer View
--   - public.vector_statistics: Missing security_invoker = true
--
-- WARNINGS (1): Materialized View in API
--   - public.vector_visualization: Accessible to anon via PostgREST
--
-- INFO (4): RLS Enabled No Policy
--   - public.checkpoints
--   - public.checkpoint_migrations
--   - public.checkpoint_blobs
--   - public.checkpoint_writes
--   (Created at runtime by LangGraph PostgresSaver.setup())
--
-- Root Cause:
-- - Migration 012 creates vector_statistics WITHOUT security_invoker
-- - Migration 016 fixes it, but if 012 runs after 016, the fix is lost
-- - Checkpoint tables are created at runtime AFTER Migration 040 runs
--
-- This migration is IDEMPOTENT and can be safely re-run.
-- ============================================================================

-- ============================================================================
-- Part 1: Fix vector_statistics Security Definer View (ERROR)
-- ============================================================================
-- 
-- Recreate the view with security_invoker = true to ensure it uses
-- caller's permissions instead of owner's permissions.
-- ============================================================================

DROP VIEW IF EXISTS public.vector_statistics;

CREATE VIEW public.vector_statistics 
WITH (security_invoker = true)
AS
SELECT 
    source,
    COUNT(*) as total_vectors,
    AVG(query_count) as avg_queries,
    MAX(query_count) as max_queries,
    MIN(created_at) as oldest_vector,
    MAX(created_at) as newest_vector,
    COUNT(CASE WHEN query_count = 0 THEN 1 END) as unused_count,
    COUNT(CASE WHEN query_count > 10 THEN 1 END) as popular_count
FROM vector_visualization
GROUP BY source
ORDER BY total_vectors DESC;

COMMENT ON VIEW public.vector_statistics IS 'Summary statistics for vector usage - SECURITY INVOKER mode (Migration 041)';

-- Grant permissions to appropriate roles
GRANT SELECT ON public.vector_statistics TO authenticated;
GRANT SELECT ON public.vector_statistics TO service_role;

-- ============================================================================
-- Part 2: Fix vector_visualization Materialized View in API (WARNING)
-- ============================================================================
-- 
-- Revoke anon access to prevent exposure via PostgREST Data API.
-- This is idempotent - REVOKE on non-existent privilege is a no-op.
-- ============================================================================

REVOKE ALL ON public.vector_visualization FROM anon;
REVOKE ALL ON public.vector_visualization FROM PUBLIC;

-- Ensure authenticated and service_role still have access
GRANT SELECT ON public.vector_visualization TO authenticated;
GRANT SELECT ON public.vector_visualization TO service_role;

COMMENT ON MATERIALIZED VIEW public.vector_visualization IS 'Vector visualization data - anon access revoked (Migration 041)';

-- ============================================================================
-- Part 3: Fix Checkpoint Tables RLS Policies (INFO x4)
-- ============================================================================
-- 
-- These tables are created at runtime by LangGraph PostgresSaver.setup().
-- Migration 040 couldn't apply policies because tables didn't exist.
-- 
-- We apply policies now that the tables exist in production.
-- This is idempotent - we drop existing policies before creating new ones.
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
            -- Enable RLS (idempotent)
            EXECUTE format('ALTER TABLE public.%I ENABLE ROW LEVEL SECURITY', tbl);
            
            -- Drop existing policy if any (idempotent)
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
            RAISE NOTICE 'RLS policy applied to % table', tbl;
        ELSE
            tables_skipped := tables_skipped + 1;
            RAISE NOTICE '% table does not exist (will be created by LangGraph at runtime)', tbl;
        END IF;
    END LOOP;
    
    RAISE NOTICE 'Checkpoint tables: % processed, % skipped', tables_processed, tables_skipped;
END $$;

-- ============================================================================
-- Part 4: Verification
-- ============================================================================

DO $$
DECLARE
    v_view_has_security_invoker BOOLEAN;
    v_anon_has_vector_viz BOOLEAN;
    v_checkpoint_tables_with_policy INTEGER := 0;
    v_checkpoint_tables_total INTEGER := 0;
    tbl TEXT;
BEGIN
    RAISE NOTICE '';
    RAISE NOTICE '============================================================';
    RAISE NOTICE '  Migration 041: Security Advisor Production Fix';
    RAISE NOTICE '============================================================';
    
    -- Check 1: vector_statistics has security_invoker
    SELECT EXISTS (
        SELECT 1 FROM pg_class c
        JOIN pg_namespace n ON c.relnamespace = n.oid
        WHERE n.nspname = 'public'
        AND c.relname = 'vector_statistics'
        AND c.reloptions IS NOT NULL
        AND 'security_invoker=true' = ANY(c.reloptions)
    ) INTO v_view_has_security_invoker;
    
    IF v_view_has_security_invoker THEN
        RAISE NOTICE '[OK] vector_statistics: security_invoker = true';
    ELSE
        RAISE WARNING '[FAIL] vector_statistics: security_invoker NOT set';
    END IF;
    
    -- Check 2: vector_visualization anon access revoked
    BEGIN
        SELECT has_table_privilege('anon', 'public.vector_visualization', 'SELECT') 
        INTO v_anon_has_vector_viz;
        
        IF NOT v_anon_has_vector_viz THEN
            RAISE NOTICE '[OK] vector_visualization: anon access revoked';
        ELSE
            RAISE WARNING '[FAIL] vector_visualization: anon still has access';
        END IF;
    EXCEPTION WHEN undefined_table THEN
        RAISE NOTICE '[SKIP] vector_visualization: table does not exist';
    END;
    
    -- Check 3: Checkpoint tables have RLS policies
    FOREACH tbl IN ARRAY ARRAY['checkpoints', 'checkpoint_migrations', 'checkpoint_blobs', 'checkpoint_writes']
    LOOP
        IF to_regclass(format('public.%I', tbl)) IS NOT NULL THEN
            v_checkpoint_tables_total := v_checkpoint_tables_total + 1;
            
            IF EXISTS (
                SELECT 1 FROM pg_policies
                WHERE schemaname = 'public'
                AND tablename = tbl
                AND policyname = 'service_role_' || tbl || '_all'
            ) THEN
                v_checkpoint_tables_with_policy := v_checkpoint_tables_with_policy + 1;
            END IF;
        END IF;
    END LOOP;
    
    IF v_checkpoint_tables_total > 0 THEN
        IF v_checkpoint_tables_with_policy = v_checkpoint_tables_total THEN
            RAISE NOTICE '[OK] checkpoint tables: %/% have RLS policies', 
                v_checkpoint_tables_with_policy, v_checkpoint_tables_total;
        ELSE
            RAISE WARNING '[PARTIAL] checkpoint tables: %/% have RLS policies', 
                v_checkpoint_tables_with_policy, v_checkpoint_tables_total;
        END IF;
    ELSE
        RAISE NOTICE '[SKIP] checkpoint tables: none exist yet (created at runtime)';
    END IF;
    
    RAISE NOTICE '============================================================';
    RAISE NOTICE '  Expected Security Advisor Status After Migration:';
    RAISE NOTICE '  - Errors: 1 -> 0 (vector_statistics fixed)';
    RAISE NOTICE '  - Warnings: 1 -> 0 (vector_visualization fixed)';
    RAISE NOTICE '  - Info: 4 -> 0 (checkpoint tables fixed)';
    RAISE NOTICE '============================================================';
END $$;
