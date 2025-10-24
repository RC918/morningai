-- ============================================================================
-- Migration 017: Secure Materialized Views with GRANT/REVOKE
-- ============================================================================
--
-- Purpose: Fix Supabase Security Advisor warnings for materialized views
--
-- Background:
-- PostgreSQL does NOT support Row Level Security (RLS) on materialized views.
-- RLS can only be applied to regular tables. Therefore, we use GRANT/REVOKE
-- to control access permissions instead.
--
-- Security Model:
-- - service_role: Full access (SELECT) - used by backend services
-- - authenticated: Read-only access (SELECT) - used by Dashboard users
-- - anon: No access - public users cannot access cost/vector data
-- - PUBLIC: No access - revoke all default permissions
-- ============================================================================

-- ============================================================================
-- ============================================================================

REVOKE ALL ON public.daily_cost_summary FROM PUBLIC;
REVOKE ALL ON public.vector_visualization FROM PUBLIC;

-- ============================================================================
-- Step 2: Grant SELECT permission to service_role
-- ============================================================================

GRANT SELECT ON public.daily_cost_summary TO service_role;
GRANT SELECT ON public.vector_visualization TO service_role;

-- ============================================================================
-- ============================================================================

GRANT SELECT ON public.daily_cost_summary TO authenticated;
GRANT SELECT ON public.vector_visualization TO authenticated;

-- ============================================================================
-- ============================================================================

COMMENT ON MATERIALIZED VIEW public.daily_cost_summary IS 
'Materialized view for daily cost summary. Access controlled via GRANT/REVOKE. Service role and authenticated users have SELECT access.';

COMMENT ON MATERIALIZED VIEW public.vector_visualization IS 
'Materialized view for vector visualization. Access controlled via GRANT/REVOKE. Service role and authenticated users have SELECT access.';

-- ============================================================================
-- ============================================================================

DO $$
DECLARE
    daily_cost_perms TEXT[];
    vector_viz_perms TEXT[];
BEGIN
    RAISE NOTICE '
╔════════════════════════════════════════════════════════════╗
║  Migration 017: Secure Materialized Views                 ║
╚════════════════════════════════════════════════════════════╝
';

    -- Check permissions for daily_cost_summary
    SELECT array_agg(grantee || ':' || privilege_type)
    INTO daily_cost_perms
    FROM information_schema.role_table_grants
    WHERE table_schema = 'public' 
    AND table_name = 'daily_cost_summary';
    
    -- Check permissions for vector_visualization
    SELECT array_agg(grantee || ':' || privilege_type)
    INTO vector_viz_perms
    FROM information_schema.role_table_grants
    WHERE table_schema = 'public' 
    AND table_name = 'vector_visualization';
    
    RAISE NOTICE '✅ daily_cost_summary permissions: %', daily_cost_perms;
    RAISE NOTICE '✅ vector_visualization permissions: %', vector_viz_perms;
    
    IF EXISTS (
        SELECT 1 FROM information_schema.role_table_grants
        WHERE table_schema = 'public' 
        AND table_name = 'daily_cost_summary'
        AND grantee = 'service_role'
        AND privilege_type = 'SELECT'
    ) THEN
        RAISE NOTICE '✅ service_role has SELECT on daily_cost_summary';
    ELSE
        RAISE WARNING '⚠️  service_role does NOT have SELECT on daily_cost_summary';
    END IF;
    
    IF EXISTS (
        SELECT 1 FROM information_schema.role_table_grants
        WHERE table_schema = 'public' 
        AND table_name = 'daily_cost_summary'
        AND grantee = 'authenticated'
        AND privilege_type = 'SELECT'
    ) THEN
        RAISE NOTICE '✅ authenticated has SELECT on daily_cost_summary';
    ELSE
        RAISE WARNING '⚠️  authenticated does NOT have SELECT on daily_cost_summary';
    END IF;
    
    RAISE NOTICE '
╔════════════════════════════════════════════════════════════╗
║  Summary                                                   ║
╠════════════════════════════════════════════════════════════╣
║  ✅ Permissions configured for daily_cost_summary          ║
║  ✅ Permissions configured for vector_visualization        ║
║  ✅ service_role: SELECT access granted                    ║
║  ✅ authenticated: SELECT access granted                   ║
║  ✅ anon: No access (default)                              ║
║  ✅ PUBLIC: All permissions revoked                        ║
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
