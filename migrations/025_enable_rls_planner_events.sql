-- ============================================================================
-- Migration 025: Enable RLS on planner_events table
-- ============================================================================
--
-- Purpose: Fix Supabase Security Advisor error "RLS Disabled in Public"
-- Table: public.planner_events (created in migration 024)
--
-- Security Model:
-- - Service role: Full access (ALL operations) - for orchestrator backend
-- - Authenticated: Read-only access (SELECT) - for monitoring dashboard
-- - Anonymous/Public: No access (blocked by RLS)
--
-- Related: Migration 024 (create_planner_events_table.sql)
-- ============================================================================

-- Enable Row Level Security
ALTER TABLE public.planner_events ENABLE ROW LEVEL SECURITY;

-- ============================================================================
-- Service Role Policy: Full access for backend services
-- ============================================================================
CREATE POLICY "service_role_planner_events_all" ON public.planner_events
    FOR ALL
    TO service_role
    USING (true)
    WITH CHECK (true);

COMMENT ON POLICY "service_role_planner_events_all" ON public.planner_events IS 
    'Service role (orchestrator backend) has full access to record and manage planner events';

-- ============================================================================
-- Authenticated User Policy: Read-only access for dashboard
-- ============================================================================
CREATE POLICY "authenticated_planner_events_read" ON public.planner_events
    FOR SELECT
    TO authenticated
    USING (true);

COMMENT ON POLICY "authenticated_planner_events_read" ON public.planner_events IS 
    'Authenticated users can read planner events for monitoring dashboard and analytics';

-- ============================================================================
-- Verification
-- ============================================================================
DO $$
DECLARE
    rls_enabled BOOLEAN;
    policy_count INTEGER;
BEGIN
    -- Check RLS is enabled
    SELECT rowsecurity INTO rls_enabled
    FROM pg_tables
    WHERE schemaname = 'public' AND tablename = 'planner_events';
    
    -- Count policies
    SELECT COUNT(*) INTO policy_count
    FROM pg_policies
    WHERE schemaname = 'public' AND tablename = 'planner_events';
    
    RAISE NOTICE '
╔════════════════════════════════════════════════════════════╗
║  Migration 025: Enable RLS on planner_events               ║
╠════════════════════════════════════════════════════════════╣
║  Table: public.planner_events                              ║
║  RLS Enabled: %                                            ║
║  Policies Created: %                                       ║
╠════════════════════════════════════════════════════════════╣
║  Security Model:                                           ║
║  - service_role: Full access (ALL operations)              ║
║  - authenticated: Read-only access (SELECT)                ║
║  - anonymous/public: No access (blocked by RLS)            ║
╠════════════════════════════════════════════════════════════╣
║  Supabase Security Advisor: Error should be RESOLVED       ║
╚════════════════════════════════════════════════════════════╝
', rls_enabled, policy_count;

    IF NOT rls_enabled THEN
        RAISE EXCEPTION 'FAILED: RLS not enabled on planner_events';
    END IF;
    
    IF policy_count < 2 THEN
        RAISE EXCEPTION 'FAILED: Expected 2 policies, found %', policy_count;
    END IF;
    
    RAISE NOTICE 'Migration 025: COMPLETE - planner_events table secured';
END $$;
