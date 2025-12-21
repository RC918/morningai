-- ============================================================================
-- Migration 039: RLS Phase 2 - Complete Tenant Isolation
-- ============================================================================
-- 
-- Purpose: Fix security gaps in RLS policies where authenticated users
--          could read data from all tenants instead of only their own.
--
-- Changes:
-- 1. planner_events: Add tenant isolation via JOIN to agent_tasks.trace_id
-- 2. memory, error_fix_pairs, failure_memory: Restrict to platform_admin only
--    (these are AI learning tables, not tenant-scoped business data)
--
-- Security Model:
-- - Tenant-scoped tables: Only users can read their own tenant's data
-- - Platform-wide tables: Only platform_admin and service_role can read
-- - Anonymous: No access (blocked by RLS)
--
-- ============================================================================

-- ============================================================================
-- Part 1: planner_events - Add tenant isolation via trace_id JOIN
-- ============================================================================
-- 
-- planner_events contains task planning data (goal, plan_steps) that may
-- contain tenant-specific information. We isolate by joining to agent_tasks
-- via trace_id, which has tenant_id.
--

-- Ensure supporting index exists on agent_tasks.trace_id
CREATE INDEX IF NOT EXISTS idx_agent_tasks_trace_id ON agent_tasks(trace_id);

-- Drop the overly permissive policy
DROP POLICY IF EXISTS "authenticated_planner_events_read" ON public.planner_events;

-- Create tenant isolation policy via JOIN to agent_tasks
-- Users can only see planner_events for tasks belonging to their tenant
CREATE POLICY "tenant_isolation_planner_events_read" ON public.planner_events
    FOR SELECT
    TO authenticated
    USING (
        EXISTS (
            SELECT 1 FROM agent_tasks t 
            WHERE t.trace_id = planner_events.trace_id 
            AND t.tenant_id = current_user_tenant_id()
        )
    );

-- Platform admin can read all planner_events for monitoring
CREATE POLICY "platform_admin_planner_events_read" ON public.planner_events
    FOR SELECT
    TO authenticated
    USING (
        EXISTS (
            SELECT 1 FROM user_profiles
            WHERE id = auth.uid() AND is_platform_admin = TRUE
        )
    );

COMMENT ON POLICY "tenant_isolation_planner_events_read" ON public.planner_events IS 
    'Phase 2: Tenant users can only read planner_events for their own tasks (via trace_id JOIN)';

COMMENT ON POLICY "platform_admin_planner_events_read" ON public.planner_events IS 
    'Phase 2: Platform admins can read all planner_events for monitoring';

-- ============================================================================
-- Part 2: memory - Restrict to platform_admin only
-- ============================================================================
-- 
-- memory table stores agent memory vectors. While not directly tenant-scoped,
-- the text content may contain tenant data, code snippets, or sensitive info.
-- Restrict to platform_admin for debugging/monitoring purposes only.
--

-- Drop the overly permissive policy
DROP POLICY IF EXISTS "authenticated_memory_read" ON public.memory;

-- Create platform_admin only policy
CREATE POLICY "platform_admin_memory_read" ON public.memory
    FOR SELECT
    TO authenticated
    USING (
        EXISTS (
            SELECT 1 FROM user_profiles
            WHERE id = auth.uid() AND is_platform_admin = TRUE
        )
    );

COMMENT ON POLICY "platform_admin_memory_read" ON public.memory IS 
    'Phase 2: Only platform admins can read memory table (may contain sensitive content)';

-- ============================================================================
-- Part 3: error_fix_pairs - Restrict to platform_admin only
-- ============================================================================
-- 
-- error_fix_pairs stores AI learning data (error patterns and fixes).
-- The error_text and fix_text may contain tenant code, stack traces, or secrets.
-- Restrict to platform_admin for AI debugging purposes only.
--

-- Drop the overly permissive policy
DROP POLICY IF EXISTS "authenticated_error_fix_pairs_read" ON public.error_fix_pairs;

-- Create platform_admin only policy
CREATE POLICY "platform_admin_error_fix_pairs_read" ON public.error_fix_pairs
    FOR SELECT
    TO authenticated
    USING (
        EXISTS (
            SELECT 1 FROM user_profiles
            WHERE id = auth.uid() AND is_platform_admin = TRUE
        )
    );

COMMENT ON POLICY "platform_admin_error_fix_pairs_read" ON public.error_fix_pairs IS 
    'Phase 2: Only platform admins can read error_fix_pairs (may contain sensitive content)';

-- ============================================================================
-- Part 4: failure_memory - Restrict to platform_admin only
-- ============================================================================
-- 
-- failure_memory stores failure records for AI learning.
-- The text and metadata may contain tenant-specific error details.
-- Restrict to platform_admin for debugging purposes only.
--

-- Drop the overly permissive policy
DROP POLICY IF EXISTS "authenticated_failure_memory_read" ON public.failure_memory;

-- Create platform_admin only policy
CREATE POLICY "platform_admin_failure_memory_read" ON public.failure_memory
    FOR SELECT
    TO authenticated
    USING (
        EXISTS (
            SELECT 1 FROM user_profiles
            WHERE id = auth.uid() AND is_platform_admin = TRUE
        )
    );

COMMENT ON POLICY "platform_admin_failure_memory_read" ON public.failure_memory IS 
    'Phase 2: Only platform admins can read failure_memory (may contain sensitive content)';

-- ============================================================================
-- Verification
-- ============================================================================

DO $$
DECLARE
    planner_events_policies INTEGER;
    memory_policies INTEGER;
    error_fix_pairs_policies INTEGER;
    failure_memory_policies INTEGER;
    has_trace_id_index BOOLEAN;
BEGIN
    RAISE NOTICE '
============================================================================
  Migration 039: RLS Phase 2 - Complete Tenant Isolation - Verification
============================================================================
';

    -- Check planner_events policies
    SELECT COUNT(*) INTO planner_events_policies
    FROM pg_policies
    WHERE schemaname = 'public' AND tablename = 'planner_events';
    
    -- Check memory policies
    SELECT COUNT(*) INTO memory_policies
    FROM pg_policies
    WHERE schemaname = 'public' AND tablename = 'memory';
    
    -- Check error_fix_pairs policies
    SELECT COUNT(*) INTO error_fix_pairs_policies
    FROM pg_policies
    WHERE schemaname = 'public' AND tablename = 'error_fix_pairs';
    
    -- Check failure_memory policies
    SELECT COUNT(*) INTO failure_memory_policies
    FROM pg_policies
    WHERE schemaname = 'public' AND tablename = 'failure_memory';
    
    -- Check trace_id index
    SELECT EXISTS (
        SELECT 1 FROM pg_indexes 
        WHERE tablename = 'agent_tasks' AND indexname = 'idx_agent_tasks_trace_id'
    ) INTO has_trace_id_index;
    
    -- Verify planner_events
    IF planner_events_policies >= 3 THEN
        RAISE NOTICE '  planner_events: % policies (service_role + tenant_isolation + platform_admin)', planner_events_policies;
    ELSE
        RAISE WARNING '  planner_events: Only % policies found', planner_events_policies;
    END IF;
    
    -- Verify memory
    IF memory_policies >= 2 THEN
        RAISE NOTICE '  memory: % policies (service_role + platform_admin)', memory_policies;
    ELSE
        RAISE WARNING '  memory: Only % policies found', memory_policies;
    END IF;
    
    -- Verify error_fix_pairs
    IF error_fix_pairs_policies >= 2 THEN
        RAISE NOTICE '  error_fix_pairs: % policies (service_role + platform_admin)', error_fix_pairs_policies;
    ELSE
        RAISE WARNING '  error_fix_pairs: Only % policies found', error_fix_pairs_policies;
    END IF;
    
    -- Verify failure_memory
    IF failure_memory_policies >= 2 THEN
        RAISE NOTICE '  failure_memory: % policies (service_role + platform_admin)', failure_memory_policies;
    ELSE
        RAISE WARNING '  failure_memory: Only % policies found', failure_memory_policies;
    END IF;
    
    -- Verify index
    IF has_trace_id_index THEN
        RAISE NOTICE '  idx_agent_tasks_trace_id: EXISTS (required for JOIN performance)';
    ELSE
        RAISE WARNING '  idx_agent_tasks_trace_id: NOT FOUND';
    END IF;
    
    -- Verify no overly permissive policies remain
    IF NOT EXISTS (
        SELECT 1 FROM pg_policies 
        WHERE schemaname = 'public' 
        AND tablename IN ('planner_events', 'memory', 'error_fix_pairs', 'failure_memory')
        AND policyname LIKE 'authenticated_%_read'
    ) THEN
        RAISE NOTICE '  Overly permissive policies: REMOVED';
    ELSE
        RAISE WARNING '  Overly permissive policies: STILL EXIST';
    END IF;
    
    RAISE NOTICE '
============================================================================
  Migration 039: COMPLETE
============================================================================
  Security Model After Migration:
  
  planner_events:
    - service_role: Full access (ALL operations)
    - authenticated (tenant user): Read own tenant data via trace_id JOIN
    - authenticated (platform_admin): Read all data
    - anonymous: No access
  
  memory, error_fix_pairs, failure_memory:
    - service_role: Full access (ALL operations)
    - authenticated (platform_admin): Read-only access
    - authenticated (regular user): No access
    - anonymous: No access
  
  Next Steps:
  1. Apply this migration to Staging Supabase
  2. Run RLS tests to verify tenant isolation
  3. Apply this migration to Production Supabase
============================================================================
';
END $$;
