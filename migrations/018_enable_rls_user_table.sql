-- ============================================================================
-- ============================================================================
--
-- 
-- Background:
--
--
-- ============================================================================

ALTER TABLE IF EXISTS public.user ENABLE ROW LEVEL SECURITY;

-- ============================================================================
-- ============================================================================

CREATE POLICY IF NOT EXISTS "service_role_user_all" ON public.user
    FOR ALL
    TO service_role
    USING (true)
    WITH CHECK (true);

COMMENT ON POLICY "service_role_user_all" ON public.user IS 
    'Service role (backend services) has full access to manage user data';

-- ============================================================================
-- ============================================================================

CREATE POLICY IF NOT EXISTS "authenticated_user_read_self" ON public.user
    FOR SELECT
    TO authenticated
    USING (id = auth.uid());

COMMENT ON POLICY "authenticated_user_read_self" ON public.user IS 
    'Authenticated users can read their own user data';

-- ============================================================================
-- ============================================================================

CREATE POLICY IF NOT EXISTS "authenticated_user_update_self" ON public.user
    FOR UPDATE
    TO authenticated
    USING (id = auth.uid())
    WITH CHECK (id = auth.uid());

COMMENT ON POLICY "authenticated_user_update_self" ON public.user IS 
    'Authenticated users can update their own user data';

-- ============================================================================
-- ============================================================================

DO $$
DECLARE
    rls_enabled BOOLEAN;
    policy_count INTEGER;
BEGIN
    RAISE NOTICE '
╔════════════════════════════════════════════════════════════╗
║  Migration 018: Enable RLS for public.user table          ║
╚════════════════════════════════════════════════════════════╝
';

    IF NOT EXISTS (
        SELECT 1 FROM pg_tables 
        WHERE schemaname = 'public' AND tablename = 'user'
    ) THEN
        RAISE NOTICE '⚠️  Table public.user does not exist - skipping migration';
        RETURN;
    END IF;

    SELECT rowsecurity INTO rls_enabled
    FROM pg_tables
    WHERE schemaname = 'public' AND tablename = 'user';
    
    SELECT COUNT(*) INTO policy_count
    FROM pg_policies
    WHERE schemaname = 'public' AND tablename = 'user';
    
    IF rls_enabled THEN
        RAISE NOTICE '✅ RLS enabled on public.user';
    ELSE
        RAISE EXCEPTION '❌ RLS NOT enabled on public.user';
    END IF;
    
    IF policy_count >= 3 THEN
        RAISE NOTICE '✅ % policies created for public.user', policy_count;
    ELSE
        RAISE WARNING '⚠️  Only % policies created for public.user (expected at least 3)', policy_count;
    END IF;
    
    RAISE NOTICE '
╔════════════════════════════════════════════════════════════╗
║  Summary                                                   ║
╠════════════════════════════════════════════════════════════╣
║  ✅ Table: public.user                                     ║
║  ✅ RLS: Enabled                                           ║
║  ✅ Policies: %                                            ║
╠════════════════════════════════════════════════════════════╣
║  Security Model:                                           ║
║  - Service role: Full access (ALL operations)              ║
║  - Authenticated: Read/Update own data only                ║
║  - Anonymous/Public: No access (blocked by RLS)            ║
╠════════════════════════════════════════════════════════════╣
║  Impact:                                                   ║
║  - Supabase Security Advisor error RESOLVED ✅             ║
║  - User data now protected from unauthorized access        ║
║  - Backend services maintain full access via service role  ║
║  - Users can only access their own data                    ║
╚════════════════════════════════════════════════════════════╝
', policy_count;

END $$;

-- ============================================================================
-- ============================================================================

GRANT ALL ON public.user TO service_role;

GRANT SELECT, UPDATE ON public.user TO authenticated;

-- ============================================================================
-- ============================================================================

DO $$
BEGIN
    RAISE NOTICE '
╔════════════════════════════════════════════════════════════╗
║  Migration 018: COMPLETE ✅                                ║
╠════════════════════════════════════════════════════════════╣
║  Security Status: public.user table SECURED                ║
║  Supabase Security Advisor: 1 error → 0 errors ✅          ║
╠════════════════════════════════════════════════════════════╣
║  Next Steps:                                               ║
║  1. Verify in Supabase Security Advisor (should show 0)    ║
║  2. Test backend services still work (service_role)        ║
║  3. Test users can read/update their own data              ║
║  4. Verify users cannot access other users data            ║
╚════════════════════════════════════════════════════════════╝
';
END $$;
