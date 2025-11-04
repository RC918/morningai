-- 
--
--

-- ============================================================================
-- ============================================================================

CREATE TABLE IF NOT EXISTS user_profiles (
    id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    display_name TEXT,
    role TEXT NOT NULL DEFAULT 'member',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    
    CONSTRAINT valid_role CHECK (role IN ('owner', 'admin', 'member', 'viewer'))
);

-- ============================================================================
-- ============================================================================

CREATE INDEX IF NOT EXISTS idx_user_profiles_tenant_id 
    ON user_profiles(tenant_id);

CREATE INDEX IF NOT EXISTS idx_user_profiles_role 
    ON user_profiles(role);

-- ============================================================================
-- ============================================================================

INSERT INTO user_profiles (id, tenant_id, role)
SELECT 
    au.id,
    '00000000-0000-0000-0000-000000000001' AS tenant_id,
    'owner' AS role
FROM auth.users au
WHERE NOT EXISTS (
    SELECT 1 FROM user_profiles up WHERE up.id = au.id
);

-- ============================================================================
-- ============================================================================

CREATE OR REPLACE FUNCTION update_user_profiles_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER user_profiles_updated_at_trigger
    BEFORE UPDATE ON user_profiles
    FOR EACH ROW
    EXECUTE FUNCTION update_user_profiles_updated_at();

-- ============================================================================
-- ============================================================================

ALTER TABLE user_profiles ENABLE ROW LEVEL SECURITY;

CREATE POLICY "users_can_read_own_profile" ON user_profiles
    FOR SELECT
    TO authenticated
    USING (id = auth.uid());

CREATE POLICY "users_can_read_tenant_profiles" ON user_profiles
    FOR SELECT
    TO authenticated
    USING (
        tenant_id = (
            SELECT tenant_id 
            FROM user_profiles 
            WHERE id = auth.uid()
        )
    );

CREATE POLICY "admins_can_update_tenant_profiles" ON user_profiles
    FOR UPDATE
    TO authenticated
    USING (
        tenant_id = (
            SELECT tenant_id 
            FROM user_profiles 
            WHERE id = auth.uid()
        )
        AND EXISTS (
            SELECT 1 FROM user_profiles
            WHERE id = auth.uid() 
            AND role IN ('owner', 'admin')
        )
    )
    WITH CHECK (
        tenant_id = (
            SELECT tenant_id 
            FROM user_profiles 
            WHERE id = auth.uid()
        )
    );

CREATE POLICY "users_can_create_own_profile" ON user_profiles
    FOR INSERT
    TO authenticated
    WITH CHECK (id = auth.uid());

-- ============================================================================
-- ============================================================================

COMMENT ON TABLE user_profiles IS 
    'Phase 3: User profiles with tenant relationships. Links auth.users to tenants for RLS queries.';

COMMENT ON COLUMN user_profiles.id IS 
    'Foreign key to auth.users.id. One-to-one relationship.';

COMMENT ON COLUMN user_profiles.tenant_id IS 
    'Tenant this user belongs to. Used in RLS policies for tenant isolation.';

COMMENT ON COLUMN user_profiles.role IS 
    'User role within tenant: owner (full access), admin (manage users), member (standard), viewer (read-only)';

COMMENT ON COLUMN user_profiles.display_name IS 
    'Optional display name for UI. Falls back to auth.users.email if NULL.';

COMMENT ON INDEX idx_user_profiles_tenant_id IS 
    'Performance: Fast lookups for RLS policies checking user tenant';

COMMENT ON POLICY "users_can_read_own_profile" ON user_profiles IS 
    'Allows users to read their own profile data';

COMMENT ON POLICY "users_can_read_tenant_profiles" ON user_profiles IS 
    'Allows users to see other members in their tenant (for member lists)';

COMMENT ON POLICY "admins_can_update_tenant_profiles" ON user_profiles IS 
    'Only owners/admins can update user profiles within their tenant';

COMMENT ON POLICY "users_can_create_own_profile" ON user_profiles IS 
    'Allows new users to create their profile during signup';

-- ============================================================================
-- ============================================================================

DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.tables 
        WHERE table_schema = 'public' AND table_name = 'user_profiles'
    ) THEN
        RAISE NOTICE 'SUCCESS: user_profiles table created';
    ELSE
        RAISE EXCEPTION 'FAILED: user_profiles table not found';
    END IF;
END $$;

DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM pg_indexes 
        WHERE schemaname = 'public' 
        AND tablename = 'user_profiles' 
        AND indexname = 'idx_user_profiles_tenant_id'
    ) THEN
        RAISE NOTICE 'SUCCESS: idx_user_profiles_tenant_id index created';
    ELSE
        RAISE EXCEPTION 'FAILED: idx_user_profiles_tenant_id index not found';
    END IF;
END $$;

DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM pg_tables 
        WHERE schemaname = 'public' 
        AND tablename = 'user_profiles' 
        AND rowsecurity = true
    ) THEN
        RAISE NOTICE 'SUCCESS: RLS enabled on user_profiles';
    ELSE
        RAISE EXCEPTION 'FAILED: RLS not enabled on user_profiles';
    END IF;
END $$;

DO $$
DECLARE
    user_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO user_count FROM user_profiles;
    RAISE NOTICE 'SUCCESS: Backfilled % existing users to user_profiles', user_count;
END $$;
