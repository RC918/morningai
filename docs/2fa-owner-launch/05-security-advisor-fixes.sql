-- ============================================================================
-- ============================================================================
--
--
--
-- Execute this in Supabase SQL Editor for Staging environment
-- ============================================================================

-- ============================================================================
-- ============================================================================

SELECT tablename, rowsecurity 
FROM pg_tables 
WHERE schemaname = 'public' 
  AND tablename IN ('agents', 'tasks');

SELECT schemaname, tablename, policyname, permissive, roles, cmd
FROM pg_policies 
WHERE tablename IN ('agents', 'tasks') 
ORDER BY tablename, policyname;

SELECT n.nspname, p.proname, p.proconfig
FROM pg_proc p
JOIN pg_namespace n ON p.pronamespace = n.oid
WHERE n.nspname = 'public' 
  AND p.proname IN ('update_updated_at_column', 'update_updated_at_col');

-- ============================================================================
-- ============================================================================

ALTER TABLE public.agents ENABLE ROW LEVEL SECURITY;

ALTER TABLE public.tasks ENABLE ROW LEVEL SECURITY;

-- ============================================================================
-- ============================================================================

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_policies 
        WHERE schemaname = 'public' 
        AND tablename = 'agents' 
        AND policyname = 'deny_all_anon_agents'
    ) THEN
        CREATE POLICY deny_all_anon_agents ON public.agents 
        FOR ALL TO anon 
        USING (false) 
        WITH CHECK (false);
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM pg_policies 
        WHERE schemaname = 'public' 
        AND tablename = 'agents' 
        AND policyname = 'deny_all_auth_agents'
    ) THEN
        CREATE POLICY deny_all_auth_agents ON public.agents 
        FOR ALL TO authenticated 
        USING (false) 
        WITH CHECK (false);
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM pg_policies 
        WHERE schemaname = 'public' 
        AND tablename = 'agents' 
        AND policyname = 'service_role_full_access_agents'
    ) THEN
        CREATE POLICY service_role_full_access_agents ON public.agents 
        FOR ALL TO service_role 
        USING (true) 
        WITH CHECK (true);
    END IF;
END $$;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_policies 
        WHERE schemaname = 'public' 
        AND tablename = 'tasks' 
        AND policyname = 'deny_all_anon_tasks'
    ) THEN
        CREATE POLICY deny_all_anon_tasks ON public.tasks 
        FOR ALL TO anon 
        USING (false) 
        WITH CHECK (false);
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM pg_policies 
        WHERE schemaname = 'public' 
        AND tablename = 'tasks' 
        AND policyname = 'deny_all_auth_tasks'
    ) THEN
        CREATE POLICY deny_all_auth_tasks ON public.tasks 
        FOR ALL TO authenticated 
        USING (false) 
        WITH CHECK (false);
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM pg_policies 
        WHERE schemaname = 'public' 
        AND tablename = 'tasks' 
        AND policyname = 'service_role_full_access_tasks'
    ) THEN
        CREATE POLICY service_role_full_access_tasks ON public.tasks 
        FOR ALL TO service_role 
        USING (true) 
        WITH CHECK (true);
    END IF;
END $$;

-- ============================================================================
-- ============================================================================

CREATE OR REPLACE FUNCTION public.update_updated_at_column()
RETURNS TRIGGER
LANGUAGE plpgsql
SET search_path = pg_catalog, public
AS $$
BEGIN
    NEW.updated_at = timezone('utc', now());
    RETURN NEW;
END;
$$;

COMMENT ON FUNCTION public.update_updated_at_column IS 
'Trigger function to auto-update updated_at column (search_path secured to prevent injection attacks)';

-- ============================================================================
-- ============================================================================

-- Verify RLS is enabled
SELECT tablename, rowsecurity 
FROM pg_tables 
WHERE schemaname = 'public' 
  AND tablename IN ('agents', 'tasks');

-- Verify policies are created
SELECT schemaname, tablename, policyname, permissive, roles, cmd
FROM pg_policies 
WHERE tablename IN ('agents', 'tasks') 
ORDER BY tablename, policyname;

SELECT n.nspname, p.proname, p.proconfig
FROM pg_proc p
JOIN pg_namespace n ON p.pronamespace = n.oid
WHERE n.nspname = 'public' 
  AND p.proname = 'update_updated_at_column';

-- ============================================================================
-- ============================================================================



-- ============================================================================
-- ============================================================================
-- ============================================================================

DO $$
BEGIN
    RAISE NOTICE '
╔════════════════════════════════════════════════════════════╗
║  Security Advisor Fixes Applied Successfully ✅            ║
╠════════════════════════════════════════════════════════════╣
║  Fixed:                                                    ║
║  ✅ RLS enabled on public.agents                           ║
║  ✅ RLS enabled on public.tasks                            ║
║  ✅ RLS policies created (deny anon/auth, allow service)   ║
║  ✅ Function search_path secured                           ║
╠════════════════════════════════════════════════════════════╣
║  Next Steps:                                               ║
║  1. Click "Rerun linter" in Security Advisor               ║
║  2. Verify 0 errors                                        ║
║  3. (Optional) Enable Leaked Password Protection           ║
║  4. (Optional) Accept MFA warning (custom TOTP in PR#1106) ║
╚════════════════════════════════════════════════════════════╝
';
END $$;
