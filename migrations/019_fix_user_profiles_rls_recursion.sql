--
--
--
--

-- ============================================================================
-- ============================================================================

DROP POLICY IF EXISTS "users_can_read_tenant_profiles" ON user_profiles;
DROP POLICY IF EXISTS "admins_can_update_tenant_profiles" ON user_profiles;

DROP POLICY IF EXISTS "users_can_read_own_profile" ON user_profiles;
CREATE POLICY "users_can_read_own_profile" ON user_profiles
    FOR SELECT
    TO authenticated
    USING (id = auth.uid());

CREATE POLICY "users_can_update_own_profile" ON user_profiles
    FOR UPDATE
    TO authenticated
    USING (id = auth.uid())
    WITH CHECK (id = auth.uid());

CREATE POLICY "service_role_full_access" ON user_profiles
    FOR ALL
    TO service_role
    USING (true)
    WITH CHECK (true);

-- ============================================================================
-- ============================================================================

CREATE OR REPLACE FUNCTION current_user_tenant_id()
RETURNS UUID AS $$
DECLARE
    result UUID;
BEGIN
    SET search_path = public;
    
    SELECT tenant_id INTO result
    FROM user_profiles 
    WHERE id = auth.uid();
    
    RETURN result;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER STABLE;

COMMENT ON FUNCTION current_user_tenant_id IS 
    'SECURITY DEFINER function: Returns tenant_id for current user. Bypasses RLS to prevent recursion.';

-- ============================================================================
-- ============================================================================

DROP POLICY IF EXISTS "true_tenant_isolation_read" ON agent_tasks;
DROP POLICY IF EXISTS "true_tenant_isolation_insert" ON agent_tasks;
DROP POLICY IF EXISTS "true_tenant_isolation_update" ON agent_tasks;
DROP POLICY IF EXISTS "true_tenant_isolation_delete" ON agent_tasks;

CREATE POLICY "true_tenant_isolation_read" ON agent_tasks
    FOR SELECT
    TO authenticated
    USING (tenant_id = current_user_tenant_id());

CREATE POLICY "true_tenant_isolation_insert" ON agent_tasks
    FOR INSERT
    TO authenticated
    WITH CHECK (tenant_id = current_user_tenant_id());

CREATE POLICY "true_tenant_isolation_update" ON agent_tasks
    FOR UPDATE
    TO authenticated
    USING (tenant_id = current_user_tenant_id())
    WITH CHECK (tenant_id = current_user_tenant_id());

CREATE POLICY "true_tenant_isolation_delete" ON agent_tasks
    FOR DELETE
    TO authenticated
    USING (tenant_id = current_user_tenant_id());

-- ============================================================================
-- ============================================================================

DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.tables 
        WHERE table_schema = 'public' AND table_name = 'documents'
    ) AND EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_schema = 'public' 
        AND table_name = 'documents' 
        AND column_name = 'tenant_id'
    ) THEN
        EXECUTE 'DROP POLICY IF EXISTS "true_tenant_isolation_read" ON documents';
        EXECUTE 'DROP POLICY IF EXISTS "true_tenant_isolation_insert" ON documents';
        EXECUTE 'DROP POLICY IF EXISTS "true_tenant_isolation_update" ON documents';
        EXECUTE 'DROP POLICY IF EXISTS "true_tenant_isolation_delete" ON documents';
        
        EXECUTE '
            CREATE POLICY "true_tenant_isolation_read" ON documents
            FOR SELECT TO authenticated
            USING (tenant_id = current_user_tenant_id())
        ';
        
        EXECUTE '
            CREATE POLICY "true_tenant_isolation_insert" ON documents
            FOR INSERT TO authenticated
            WITH CHECK (tenant_id = current_user_tenant_id())
        ';
        
        EXECUTE '
            CREATE POLICY "true_tenant_isolation_update" ON documents
            FOR UPDATE TO authenticated
            USING (tenant_id = current_user_tenant_id())
            WITH CHECK (tenant_id = current_user_tenant_id())
        ';
        
        EXECUTE '
            CREATE POLICY "true_tenant_isolation_delete" ON documents
            FOR DELETE TO authenticated
            USING (tenant_id = current_user_tenant_id())
        ';
        
        RAISE NOTICE 'Updated documents table policies to use current_user_tenant_id()';
    END IF;
END $$;

-- ============================================================================
-- ============================================================================

DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM pg_policies 
        WHERE schemaname = 'public' 
        AND tablename = 'user_profiles'
        AND policyname = 'users_can_read_own_profile'
    ) THEN
        RAISE NOTICE 'SUCCESS: Non-recursive user_profiles policies created';
    ELSE
        RAISE EXCEPTION 'FAILED: user_profiles policies not found';
    END IF;
    
    IF EXISTS (
        SELECT 1 FROM pg_policies 
        WHERE schemaname = 'public' 
        AND tablename = 'agent_tasks'
        AND policyname LIKE 'true_tenant_isolation%'
    ) THEN
        RAISE NOTICE 'SUCCESS: agent_tasks policies updated';
    ELSE
        RAISE EXCEPTION 'FAILED: agent_tasks policies not found';
    END IF;
    
    IF EXISTS (
        SELECT 1 FROM pg_proc 
        WHERE proname = 'current_user_tenant_id'
        AND prosecdef = true  -- SECURITY DEFINER
    ) THEN
        RAISE NOTICE 'SUCCESS: current_user_tenant_id() is SECURITY DEFINER';
    ELSE
        RAISE EXCEPTION 'FAILED: current_user_tenant_id() not found or not SECURITY DEFINER';
    END IF;
END $$;

RAISE NOTICE '
╔════════════════════════════════════════════════════════════╗
║  Migration 007: Fix RLS Recursion - COMPLETE             ║
╠════════════════════════════════════════════════════════════╣
║  ✅ Removed recursive user_profiles policies              ║
║  ✅ Created non-recursive policies                        ║
║  ✅ Updated agent_tasks to use current_user_tenant_id()   ║
║  ✅ Function properly configured as SECURITY DEFINER      ║
╠════════════════════════════════════════════════════════════╣
║  Impact:                                                   ║
║  - Fixes infinite recursion error (42P17)                 ║
║  - Enables real user JWT testing                          ║
║  - Maintains tenant isolation security                    ║
╚════════════════════════════════════════════════════════════╝
';
