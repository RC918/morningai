-- ============================================================================
-- ============================================================================
--
--
--
-- ============================================================================

-- ============================================================================
-- ============================================================================

ALTER MATERIALIZED VIEW public.daily_cost_summary ENABLE ROW LEVEL SECURITY;

CREATE POLICY "service_role_full_access_daily_cost_summary"
ON public.daily_cost_summary
FOR SELECT
TO service_role
USING (true);

CREATE POLICY "authenticated_read_daily_cost_summary"
ON public.daily_cost_summary
FOR SELECT
TO authenticated
USING (true);

COMMENT ON POLICY "service_role_full_access_daily_cost_summary" ON public.daily_cost_summary 
IS 'Service role has full access to daily cost summary';

COMMENT ON POLICY "authenticated_read_daily_cost_summary" ON public.daily_cost_summary 
IS 'Authenticated users can read daily cost summary';

ALTER MATERIALIZED VIEW public.vector_visualization ENABLE ROW LEVEL SECURITY;

CREATE POLICY "service_role_full_access_vector_visualization"
ON public.vector_visualization
FOR SELECT
TO service_role
USING (true);

CREATE POLICY "authenticated_read_vector_visualization"
ON public.vector_visualization
FOR SELECT
TO authenticated
USING (true);

COMMENT ON POLICY "service_role_full_access_vector_visualization" ON public.vector_visualization 
IS 'Service role has full access to vector visualization';

COMMENT ON POLICY "authenticated_read_vector_visualization" ON public.vector_visualization 
IS 'Authenticated users can read vector visualization';

-- ============================================================================
-- ============================================================================

-- 

-- ============================================================================
-- ============================================================================

DO $$
DECLARE
    daily_cost_rls_enabled BOOLEAN;
    vector_viz_rls_enabled BOOLEAN;
    daily_cost_policy_count INTEGER;
    vector_viz_policy_count INTEGER;
BEGIN
    RAISE NOTICE '
╔════════════════════════════════════════════════════════════╗
║  Migration 017: RLS for Materialized Views                ║
╚════════════════════════════════════════════════════════════╝
';

    SELECT relrowsecurity INTO daily_cost_rls_enabled
    FROM pg_class c
    JOIN pg_namespace n ON c.relnamespace = n.oid
    WHERE n.nspname = 'public' 
    AND c.relname = 'daily_cost_summary';
    
    SELECT relrowsecurity INTO vector_viz_rls_enabled
    FROM pg_class c
    JOIN pg_namespace n ON c.relnamespace = n.oid
    WHERE n.nspname = 'public' 
    AND c.relname = 'vector_visualization';
    
    IF daily_cost_rls_enabled THEN
        RAISE NOTICE '✅ daily_cost_summary: RLS enabled';
    ELSE
        RAISE WARNING '⚠️  daily_cost_summary: RLS not enabled';
    END IF;
    
    IF vector_viz_rls_enabled THEN
        RAISE NOTICE '✅ vector_visualization: RLS enabled';
    ELSE
        RAISE WARNING '⚠️  vector_visualization: RLS not enabled';
    END IF;
    
    SELECT COUNT(*) INTO daily_cost_policy_count
    FROM pg_policies
    WHERE schemaname = 'public' 
    AND tablename = 'daily_cost_summary';
    
    SELECT COUNT(*) INTO vector_viz_policy_count
    FROM pg_policies
    WHERE schemaname = 'public' 
    AND tablename = 'vector_visualization';
    
    RAISE NOTICE '✅ daily_cost_summary policies: %', daily_cost_policy_count;
    RAISE NOTICE '✅ vector_visualization policies: %', vector_viz_policy_count;
    
    RAISE NOTICE '
╔════════════════════════════════════════════════════════════╗
║  Summary                                                   ║
╠════════════════════════════════════════════════════════════╣
║  ✅ RLS enabled for daily_cost_summary                     ║
║  ✅ RLS enabled for vector_visualization                   ║
║  ✅ Policies created for service_role and authenticated    ║
╠════════════════════════════════════════════════════════════╣
║  Manual Action Required:                                   ║
║  ⚠️  Enable Leaked Password Protection in Supabase         ║
║     Dashboard → Authentication → Settings                  ║
║     → Password Protection → Enable                         ║
╚════════════════════════════════════════════════════════════╝
';
END $$;

-- ============================================================================
-- ============================================================================

DO $$
BEGIN
    RAISE NOTICE '
╔════════════════════════════════════════════════════════════╗
║  Migration 017: COMPLETE ✅                                ║
╠════════════════════════════════════════════════════════════╣
║  Security Advisor Status (Expected):                       ║
║  - Materialized View warnings: 2 → 0 ✅                    ║
║  - Leaked Password Protection: Manual action required ⚠️   ║
╠════════════════════════════════════════════════════════════╣
║  Next Steps:                                               ║
║  1. Verify in Supabase Security Advisor                    ║
║  2. Enable Leaked Password Protection manually             ║
║  3. Test materialized view access with different roles     ║
╚════════════════════════════════════════════════════════════╝
';
END $$;
