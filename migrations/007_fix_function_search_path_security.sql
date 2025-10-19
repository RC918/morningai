-- ============================================================================
-- ============================================================================
-- 
--
-- ============================================================================

-- ============================================================================
-- ============================================================================

DROP FUNCTION IF EXISTS is_tenant_admin() CASCADE;

CREATE OR REPLACE FUNCTION public.is_tenant_admin()
RETURNS BOOLEAN 
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path TO public, pg_temp
STABLE
AS $$
BEGIN
    RETURN EXISTS (
        SELECT 1 FROM public.user_profiles
        WHERE id = auth.uid()
        AND role IN ('admin', 'owner')
    );
END;
$$;

COMMENT ON FUNCTION is_tenant_admin() IS 
    'Helper function: Check if current user is a tenant administrator (owner or admin). SECURITY DEFINER with explicit search_path for security.';

-- ============================================================================
-- ============================================================================

DROP FUNCTION IF EXISTS current_user_tenant_id() CASCADE;

CREATE OR REPLACE FUNCTION public.current_user_tenant_id()
RETURNS UUID 
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path TO public, pg_temp
STABLE
AS $$
BEGIN
    RETURN (
        SELECT tenant_id 
        FROM public.user_profiles 
        WHERE id = auth.uid()
    );
END;
$$;

COMMENT ON FUNCTION current_user_tenant_id() IS 
    'Helper function: Returns the tenant_id for the currently authenticated user. Used in RLS policies and queries. SECURITY DEFINER with explicit search_path.';

-- ============================================================================
-- ============================================================================

DROP FUNCTION IF EXISTS get_user_tenant_id(UUID) CASCADE;

CREATE OR REPLACE FUNCTION public.get_user_tenant_id(user_id UUID)
RETURNS UUID 
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path TO public, pg_temp
STABLE
AS $$
DECLARE
    tenant_uuid UUID;
BEGIN
    SELECT tenant_id INTO tenant_uuid
    FROM public.user_profiles
    WHERE id = user_id;
    
    RETURN tenant_uuid;
END;
$$;

COMMENT ON FUNCTION get_user_tenant_id(UUID) IS 
    'Helper function: Returns the tenant_id for a given user_id. Used in backend code for tenant resolution. SECURITY DEFINER with explicit search_path.';

-- ============================================================================
-- ============================================================================

DROP FUNCTION IF EXISTS update_user_profiles_updated_at() CASCADE;

CREATE OR REPLACE FUNCTION public.update_user_profiles_updated_at()
RETURNS TRIGGER 
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path TO public, pg_temp
AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$;

COMMENT ON FUNCTION update_user_profiles_updated_at() IS 
    'Trigger function: Automatically updates updated_at column on user_profiles. SECURITY DEFINER with explicit search_path for security.';

DROP TRIGGER IF EXISTS user_profiles_updated_at_trigger ON user_profiles;

CREATE TRIGGER user_profiles_updated_at_trigger
    BEFORE UPDATE ON user_profiles
    FOR EACH ROW
    EXECUTE FUNCTION update_user_profiles_updated_at();

-- ============================================================================
-- ============================================================================

DO $$
DECLARE
    func_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO func_count
    FROM pg_proc p
    JOIN pg_namespace n ON p.pronamespace = n.oid
    WHERE n.nspname = 'public'
    AND p.proname IN (
        'is_tenant_admin',
        'current_user_tenant_id',
        'get_user_tenant_id',
        'update_user_profiles_updated_at'
    )
    AND p.prosecdef = true;  -- SECURITY DEFINER
    
    IF func_count = 4 THEN
        RAISE NOTICE 'SUCCESS: All 4 functions recreated with SECURITY DEFINER';
    ELSE
        RAISE EXCEPTION 'FAILED: Expected 4 functions, found %', func_count;
    END IF;
    
    IF EXISTS (
        SELECT 1 FROM pg_trigger 
        WHERE tgname = 'user_profiles_updated_at_trigger'
    ) THEN
        RAISE NOTICE 'SUCCESS: user_profiles_updated_at_trigger recreated';
    ELSE
        RAISE EXCEPTION 'FAILED: user_profiles_updated_at_trigger not found';
    END IF;
END $$;

-- ============================================================================
-- ============================================================================

DO $$
BEGIN
    RAISE NOTICE '
╔════════════════════════════════════════════════════════════╗
║  Migration 007: Function search_path Security - COMPLETE  ║
╠════════════════════════════════════════════════════════════╣
║  ✅ Fixed is_tenant_admin() search_path                    ║
║  ✅ Fixed current_user_tenant_id() search_path             ║
║  ✅ Fixed get_user_tenant_id() search_path                 ║
║  ✅ Fixed update_user_profiles_updated_at() search_path    ║
║  ✅ All functions use: SET search_path = public, pg_temp   ║
║  ✅ Trigger recreated successfully                         ║
╠════════════════════════════════════════════════════════════╣
║  Security Impact:                                          ║
║  - Prevents search_path injection attacks                  ║
║  - Ensures functions only access intended schemas          ║
║  - Supabase Security Advisor warnings resolved             ║
╚════════════════════════════════════════════════════════════╝
';
END $$;
