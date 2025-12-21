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
-- WARNINGS (3): SECURITY DEFINER functions without search_path
--   - get_tenant_quota
--   - check_tenant_quota
--   - increment_tenant_usage
--
-- Note: Checkpoint tables are created at runtime by LangGraph's PostgresSaver.setup()
-- so we use conditional logic to handle cases where tables don't exist yet.
-- ============================================================================

-- ============================================================================
-- Part 1: Enable RLS on LangGraph Checkpoint Tables
-- ============================================================================
-- 
-- These tables store LangGraph workflow state. They are created automatically
-- by PostgresSaver.setup() at runtime, not via migrations. The checkpointer
-- connects using service_role, so we create permissive policies for that role.
--
-- We use DO blocks to conditionally enable RLS only if tables exist.
-- ============================================================================

-- Enable RLS on checkpoints table (if exists)
DO $$
BEGIN
    IF to_regclass('public.checkpoints') IS NOT NULL THEN
        ALTER TABLE public.checkpoints ENABLE ROW LEVEL SECURITY;
        
        -- Drop existing policy if any
        DROP POLICY IF EXISTS "service_role_checkpoints_all" ON public.checkpoints;
        
        -- Create permissive policy for service_role
        CREATE POLICY "service_role_checkpoints_all" ON public.checkpoints
            FOR ALL
            TO service_role
            USING (true)
            WITH CHECK (true);
            
        RAISE NOTICE 'RLS enabled on checkpoints table';
    ELSE
        RAISE NOTICE 'checkpoints table does not exist yet (will be created by LangGraph at runtime)';
    END IF;
END $$;

-- Enable RLS on checkpoint_migrations table (if exists)
DO $$
BEGIN
    IF to_regclass('public.checkpoint_migrations') IS NOT NULL THEN
        ALTER TABLE public.checkpoint_migrations ENABLE ROW LEVEL SECURITY;
        
        DROP POLICY IF EXISTS "service_role_checkpoint_migrations_all" ON public.checkpoint_migrations;
        
        CREATE POLICY "service_role_checkpoint_migrations_all" ON public.checkpoint_migrations
            FOR ALL
            TO service_role
            USING (true)
            WITH CHECK (true);
            
        RAISE NOTICE 'RLS enabled on checkpoint_migrations table';
    ELSE
        RAISE NOTICE 'checkpoint_migrations table does not exist yet (will be created by LangGraph at runtime)';
    END IF;
END $$;

-- Enable RLS on checkpoint_blobs table (if exists)
DO $$
BEGIN
    IF to_regclass('public.checkpoint_blobs') IS NOT NULL THEN
        ALTER TABLE public.checkpoint_blobs ENABLE ROW LEVEL SECURITY;
        
        DROP POLICY IF EXISTS "service_role_checkpoint_blobs_all" ON public.checkpoint_blobs;
        
        CREATE POLICY "service_role_checkpoint_blobs_all" ON public.checkpoint_blobs
            FOR ALL
            TO service_role
            USING (true)
            WITH CHECK (true);
            
        RAISE NOTICE 'RLS enabled on checkpoint_blobs table';
    ELSE
        RAISE NOTICE 'checkpoint_blobs table does not exist yet (will be created by LangGraph at runtime)';
    END IF;
END $$;

-- Enable RLS on checkpoint_writes table (if exists)
DO $$
BEGIN
    IF to_regclass('public.checkpoint_writes') IS NOT NULL THEN
        ALTER TABLE public.checkpoint_writes ENABLE ROW LEVEL SECURITY;
        
        DROP POLICY IF EXISTS "service_role_checkpoint_writes_all" ON public.checkpoint_writes;
        
        CREATE POLICY "service_role_checkpoint_writes_all" ON public.checkpoint_writes
            FOR ALL
            TO service_role
            USING (true)
            WITH CHECK (true);
            
        RAISE NOTICE 'RLS enabled on checkpoint_writes table';
    ELSE
        RAISE NOTICE 'checkpoint_writes table does not exist yet (will be created by LangGraph at runtime)';
    END IF;
END $$;

-- ============================================================================
-- Part 2: Add search_path to SECURITY DEFINER Functions
-- ============================================================================
-- 
-- These functions were created in migration 037 without SET search_path,
-- which is a security best practice for SECURITY DEFINER functions to prevent
-- search_path injection attacks.
--
-- We use ALTER FUNCTION to add the search_path setting without recreating
-- the entire function body.
-- ============================================================================

-- Fix get_tenant_quota function
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM pg_proc p
        JOIN pg_namespace n ON p.pronamespace = n.oid
        WHERE n.nspname = 'public' AND p.proname = 'get_tenant_quota'
    ) THEN
        ALTER FUNCTION public.get_tenant_quota(UUID) SET search_path = public;
        RAISE NOTICE 'Added search_path to get_tenant_quota function';
    ELSE
        RAISE NOTICE 'get_tenant_quota function does not exist';
    END IF;
END $$;

-- Fix check_tenant_quota function
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM pg_proc p
        JOIN pg_namespace n ON p.pronamespace = n.oid
        WHERE n.nspname = 'public' AND p.proname = 'check_tenant_quota'
    ) THEN
        ALTER FUNCTION public.check_tenant_quota(UUID, VARCHAR, INTEGER) SET search_path = public;
        RAISE NOTICE 'Added search_path to check_tenant_quota function';
    ELSE
        RAISE NOTICE 'check_tenant_quota function does not exist';
    END IF;
END $$;

-- Fix increment_tenant_usage function
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM pg_proc p
        JOIN pg_namespace n ON p.pronamespace = n.oid
        WHERE n.nspname = 'public' AND p.proname = 'increment_tenant_usage'
    ) THEN
        ALTER FUNCTION public.increment_tenant_usage(UUID, VARCHAR, INTEGER) SET search_path = public;
        RAISE NOTICE 'Added search_path to increment_tenant_usage function';
    ELSE
        RAISE NOTICE 'increment_tenant_usage function does not exist';
    END IF;
END $$;

-- ============================================================================
-- Part 3: Fix get_user_tenant_id function (also flagged in staging)
-- ============================================================================
-- 
-- This function was flagged in staging but not production. Adding search_path
-- for consistency.
-- ============================================================================

DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM pg_proc p
        JOIN pg_namespace n ON p.pronamespace = n.oid
        WHERE n.nspname = 'public' AND p.proname = 'get_user_tenant_id'
    ) THEN
        ALTER FUNCTION public.get_user_tenant_id(UUID) SET search_path = public;
        RAISE NOTICE 'Added search_path to get_user_tenant_id function';
    ELSE
        RAISE NOTICE 'get_user_tenant_id function does not exist';
    END IF;
END $$;

-- ============================================================================
-- Part 4: Verification
-- ============================================================================

DO $$
DECLARE
    v_checkpoint_tables_count INTEGER := 0;
    v_functions_fixed INTEGER := 0;
BEGIN
    -- Count checkpoint tables with RLS enabled
    SELECT COUNT(*) INTO v_checkpoint_tables_count
    FROM pg_tables t
    JOIN pg_class c ON c.relname = t.tablename AND c.relnamespace = (SELECT oid FROM pg_namespace WHERE nspname = t.schemaname)
    WHERE t.schemaname = 'public'
    AND t.tablename IN ('checkpoints', 'checkpoint_migrations', 'checkpoint_blobs', 'checkpoint_writes')
    AND c.relrowsecurity = true;
    
    -- Count functions with search_path set
    SELECT COUNT(*) INTO v_functions_fixed
    FROM pg_proc p
    JOIN pg_namespace n ON p.pronamespace = n.oid
    WHERE n.nspname = 'public'
    AND p.proname IN ('get_tenant_quota', 'check_tenant_quota', 'increment_tenant_usage', 'get_user_tenant_id')
    AND p.proconfig IS NOT NULL
    AND 'search_path=public' = ANY(p.proconfig);
    
    RAISE NOTICE '';
    RAISE NOTICE '============================================================';
    RAISE NOTICE 'Migration 040 Verification Results';
    RAISE NOTICE '============================================================';
    RAISE NOTICE 'Checkpoint tables with RLS enabled: %', v_checkpoint_tables_count;
    RAISE NOTICE 'Functions with search_path fixed: %', v_functions_fixed;
    RAISE NOTICE '============================================================';
END $$;
