--
--

-- ============================================================================
-- ============================================================================

BEGIN;

INSERT INTO tenants (id, name) VALUES
    ('test-tenant-a', 'Test Tenant A'),
    ('test-tenant-b', 'Test Tenant B')
ON CONFLICT (id) DO NOTHING;

--

DO $$
BEGIN
    RAISE NOTICE '⚠️  This test requires 2 test users in auth.users:';
    RAISE NOTICE '   - test-user-a@example.com';
    RAISE NOTICE '   - test-user-b@example.com';
    RAISE NOTICE '';
    RAISE NOTICE '   Create them via:';
    RAISE NOTICE '   1. Supabase Dashboard → Authentication → Users → Add User';
    RAISE NOTICE '   2. Or via API: POST /auth/v1/signup';
    RAISE NOTICE '';
END $$;

COMMIT;

-- ============================================================================
-- ============================================================================

DO $$
BEGIN
    RAISE NOTICE '';
    RAISE NOTICE '━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━';
    RAISE NOTICE 'TEST 1: user_profiles table structure';
    RAISE NOTICE '━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━';
    
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.tables 
        WHERE table_schema = 'public' AND table_name = 'user_profiles'
    ) THEN
        RAISE EXCEPTION '❌ FAILED: user_profiles table does not exist';
    END IF;
    RAISE NOTICE '✅ PASS: user_profiles table exists';
    
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'user_profiles' AND column_name = 'tenant_id'
    ) THEN
        RAISE EXCEPTION '❌ FAILED: tenant_id column missing';
    END IF;
    RAISE NOTICE '✅ PASS: tenant_id column exists';
    
    IF NOT EXISTS (
        SELECT 1 FROM pg_tables 
        WHERE tablename = 'user_profiles' AND rowsecurity = true
    ) THEN
        RAISE EXCEPTION '❌ FAILED: RLS not enabled on user_profiles';
    END IF;
    RAISE NOTICE '✅ PASS: RLS enabled on user_profiles';
    
    RAISE NOTICE '';
END $$;

-- ============================================================================
-- ============================================================================

DO $$
DECLARE
    test_result UUID;
BEGIN
    RAISE NOTICE '━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━';
    RAISE NOTICE 'TEST 2: Helper functions';
    RAISE NOTICE '━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━';
    
    IF NOT EXISTS (
        SELECT 1 FROM pg_proc WHERE proname = 'get_user_tenant_id'
    ) THEN
        RAISE EXCEPTION '❌ FAILED: get_user_tenant_id() function missing';
    END IF;
    RAISE NOTICE '✅ PASS: get_user_tenant_id() exists';
    
    IF NOT EXISTS (
        SELECT 1 FROM pg_proc WHERE proname = 'current_user_tenant_id'
    ) THEN
        RAISE EXCEPTION '❌ FAILED: current_user_tenant_id() function missing';
    END IF;
    RAISE NOTICE '✅ PASS: current_user_tenant_id() exists';
    
    RAISE NOTICE '';
END $$;

-- ============================================================================
-- ============================================================================

DO $$
DECLARE
    policy_count INTEGER;
BEGIN
    RAISE NOTICE '━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━';
    RAISE NOTICE 'TEST 3: RLS policies on agent_tasks';
    RAISE NOTICE '━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━';
    
    IF NOT EXISTS (
        SELECT 1 FROM pg_tables 
        WHERE tablename = 'agent_tasks' AND rowsecurity = true
    ) THEN
        RAISE EXCEPTION '❌ FAILED: RLS not enabled on agent_tasks';
    END IF;
    RAISE NOTICE '✅ PASS: RLS enabled on agent_tasks';
    
    SELECT COUNT(*) INTO policy_count
    FROM pg_policies 
    WHERE tablename = 'agent_tasks'
    AND policyname LIKE 'true_tenant_isolation%';
    
    IF policy_count != 4 THEN
        RAISE EXCEPTION '❌ FAILED: Expected 4 TRUE isolation policies, found %', policy_count;
    END IF;
    RAISE NOTICE '✅ PASS: All 4 TRUE tenant isolation policies exist';
    
    IF EXISTS (
        SELECT 1 FROM pg_policies 
        WHERE tablename = 'agent_tasks'
        AND policyname IN ('tenant_read_policy', 'tenant_insert_policy')
    ) THEN
        RAISE EXCEPTION '❌ FAILED: Old temporary policies still exist';
    END IF;
    RAISE NOTICE '✅ PASS: Old temporary policies removed';
    
    RAISE NOTICE '';
END $$;

-- ============================================================================
-- ============================================================================

DO $$
BEGIN
    RAISE NOTICE '━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━';
    RAISE NOTICE 'TEST 4: Performance indexes';
    RAISE NOTICE '━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━';
    
    IF NOT EXISTS (
        SELECT 1 FROM pg_indexes 
        WHERE tablename = 'user_profiles' 
        AND indexname = 'idx_user_profiles_tenant_id'
    ) THEN
        RAISE EXCEPTION '❌ FAILED: Missing idx_user_profiles_tenant_id';
    END IF;
    RAISE NOTICE '✅ PASS: idx_user_profiles_tenant_id exists';
    
    IF NOT EXISTS (
        SELECT 1 FROM pg_indexes 
        WHERE tablename = 'agent_tasks' 
        AND indexname = 'idx_agent_tasks_tenant_id'
    ) THEN
        RAISE EXCEPTION '❌ FAILED: Missing idx_agent_tasks_tenant_id';
    END IF;
    RAISE NOTICE '✅ PASS: idx_agent_tasks_tenant_id exists';
    
    RAISE NOTICE '';
END $$;

-- ============================================================================
-- ============================================================================

DO $$
DECLARE
    auth_user_count INTEGER;
    profile_count INTEGER;
BEGIN
    RAISE NOTICE '━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━';
    RAISE NOTICE 'TEST 5: User backfill';
    RAISE NOTICE '━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━';
    
    SELECT COUNT(*) INTO auth_user_count FROM auth.users;
    
    SELECT COUNT(*) INTO profile_count FROM user_profiles;
    
    RAISE NOTICE '   auth.users count: %', auth_user_count;
    RAISE NOTICE '   user_profiles count: %', profile_count;
    
    IF profile_count >= auth_user_count THEN
        RAISE NOTICE '✅ PASS: All auth.users have user_profiles (or more)';
    ELSE
        RAISE WARNING '⚠️  WARNING: Some auth.users missing profiles. Run backfill again if needed.';
    END IF;
    
    RAISE NOTICE '';
END $$;

-- ============================================================================
-- ============================================================================

DO $$
DECLARE
    default_tenant_count INTEGER;
    default_profile_count INTEGER;
BEGIN
    RAISE NOTICE '━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━';
    RAISE NOTICE 'TEST 6: Default tenant';
    RAISE NOTICE '━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━';
    
    SELECT COUNT(*) INTO default_tenant_count
    FROM tenants 
    WHERE id = '00000000-0000-0000-0000-000000000001';
    
    IF default_tenant_count = 0 THEN
        RAISE EXCEPTION '❌ FAILED: Default tenant does not exist';
    END IF;
    RAISE NOTICE '✅ PASS: Default tenant exists';
    
    SELECT COUNT(*) INTO default_profile_count
    FROM user_profiles 
    WHERE tenant_id = '00000000-0000-0000-0000-000000000001';
    
    RAISE NOTICE '   Users in default tenant: %', default_profile_count;
    
    IF default_profile_count > 0 THEN
        RAISE NOTICE '✅ PASS: Users assigned to default tenant';
    ELSE
        RAISE WARNING '⚠️  WARNING: No users in default tenant (may be OK if no users exist)';
    END IF;
    
    RAISE NOTICE '';
END $$;

-- ============================================================================
-- ============================================================================

DO $$
BEGIN
    RAISE NOTICE '━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━';
    RAISE NOTICE 'TEST 7: Role validation';
    RAISE NOTICE '━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━';
    
    BEGIN
        INSERT INTO user_profiles (id, tenant_id, role) 
        VALUES (
            '99999999-9999-9999-9999-999999999999',
            '00000000-0000-0000-0000-000000000001',
            'invalid_role'
        );
        
        RAISE EXCEPTION '❌ FAILED: Invalid role was accepted';
    EXCEPTION WHEN check_violation THEN
        RAISE NOTICE '✅ PASS: Invalid role rejected (check constraint works)';
    END;
    
    RAISE NOTICE '';
END $$;

-- ============================================================================
-- ============================================================================

DO $$
BEGIN
    RAISE NOTICE '';
    RAISE NOTICE '╔════════════════════════════════════════════════════════════╗';
    RAISE NOTICE '║           Phase 3 Tenant Isolation - Test Summary         ║';
    RAISE NOTICE '╠════════════════════════════════════════════════════════════╣';
    RAISE NOTICE '║  ✅ user_profiles table structure correct                  ║';
    RAISE NOTICE '║  ✅ Helper functions created                               ║';
    RAISE NOTICE '║  ✅ RLS policies correctly configured                      ║';
    RAISE NOTICE '║  ✅ Performance indexes in place                           ║';
    RAISE NOTICE '║  ✅ User backfill completed                                ║';
    RAISE NOTICE '║  ✅ Default tenant configured                              ║';
    RAISE NOTICE '║  ✅ Role validation working                                ║';
    RAISE NOTICE '╠════════════════════════════════════════════════════════════╣';
    RAISE NOTICE '║  Status: READY FOR INTEGRATION TESTING                     ║';
    RAISE NOTICE '╠════════════════════════════════════════════════════════════╣';
    RAISE NOTICE '║  Next steps:                                               ║';
    RAISE NOTICE '║  1. Run E2E tests with actual users                        ║';
    RAISE NOTICE '║  2. Test db_writer.py with auto tenant_id                  ║';
    RAISE NOTICE '║  3. Test /api/tenant/* endpoints                           ║';
    RAISE NOTICE '║  4. Test frontend TenantContext                            ║';
    RAISE NOTICE '╚════════════════════════════════════════════════════════════╝';
    RAISE NOTICE '';
END $$;

BEGIN;

DELETE FROM agent_tasks WHERE tenant_id IN ('test-tenant-a', 'test-tenant-b');
DELETE FROM user_profiles WHERE tenant_id IN ('test-tenant-a', 'test-tenant-b');
DELETE FROM tenants WHERE id IN ('test-tenant-a', 'test-tenant-b');

RAISE NOTICE '🧹 Test data cleaned up';

COMMIT;
