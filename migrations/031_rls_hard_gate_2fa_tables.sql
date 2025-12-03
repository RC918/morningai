-- ============================================================================
-- Migration 031: RLS Hard Gate for 2FA Tables
-- ============================================================================
-- Purpose: Upgrade 2FA tables from soft gate to hard gate RLS
-- 
-- Hard Gate Definition:
-- - Physical blocking at database level (not application-level enforcement)
-- - Only service_role can access 2FA tables
-- - All other roles (anon, authenticated) are completely blocked
-- - This prevents autonomous agents from accidentally accessing sensitive 2FA data
--
-- Tables Affected:
-- - user_2fa: TOTP secrets and 2FA configuration
-- - totp_backup_codes: Single-use backup recovery codes
-- - trusted_devices: "Remember this device" tokens
--
-- Security Model:
-- - service_role: Full CRUD access (backend services only)
-- - authenticated: NO access (blocked by RLS)
-- - anon: NO access (blocked by RLS)
-- ============================================================================

BEGIN;

-- ============================================================================
-- Step 1: Ensure RLS is enabled on all 2FA tables
-- ============================================================================

ALTER TABLE IF EXISTS user_2fa ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS totp_backup_codes ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS trusted_devices ENABLE ROW LEVEL SECURITY;

-- ============================================================================
-- Step 2: Drop existing policies (clean slate for hard gate)
-- ============================================================================

-- Drop any existing policies on user_2fa
DROP POLICY IF EXISTS "Service role has full access to user_2fa" ON user_2fa;
DROP POLICY IF EXISTS "Users can view their own 2FA status" ON user_2fa;
DROP POLICY IF EXISTS "deny_all_anon_user_2fa" ON user_2fa;
DROP POLICY IF EXISTS "deny_all_auth_user_2fa" ON user_2fa;
DROP POLICY IF EXISTS "service_role_user_2fa_all" ON user_2fa;

-- Drop any existing policies on totp_backup_codes
DROP POLICY IF EXISTS "Service role has full access to totp_backup_codes" ON totp_backup_codes;
DROP POLICY IF EXISTS "Users can view their own backup codes" ON totp_backup_codes;
DROP POLICY IF EXISTS "deny_all_anon_backup_codes" ON totp_backup_codes;
DROP POLICY IF EXISTS "deny_all_auth_backup_codes" ON totp_backup_codes;
DROP POLICY IF EXISTS "service_role_totp_backup_codes_all" ON totp_backup_codes;

-- Drop any existing policies on trusted_devices
DROP POLICY IF EXISTS "Service role has full access to trusted_devices" ON trusted_devices;
DROP POLICY IF EXISTS "Users can view their own trusted devices" ON trusted_devices;
DROP POLICY IF EXISTS "deny_all_anon_trusted_devices" ON trusted_devices;
DROP POLICY IF EXISTS "deny_all_auth_trusted_devices" ON trusted_devices;
DROP POLICY IF EXISTS "service_role_trusted_devices_all" ON trusted_devices;

-- ============================================================================
-- Step 3: Create HARD GATE policies - Service Role Only
-- ============================================================================

-- user_2fa: Service role full access (HARD GATE)
CREATE POLICY "hard_gate_service_role_user_2fa_all" ON user_2fa
    FOR ALL
    TO service_role
    USING (true)
    WITH CHECK (true);

COMMENT ON POLICY "hard_gate_service_role_user_2fa_all" ON user_2fa IS 
    'HARD GATE: Only service_role (backend) can access 2FA secrets. No authenticated/anon access.';

-- totp_backup_codes: Service role full access (HARD GATE)
CREATE POLICY "hard_gate_service_role_totp_backup_codes_all" ON totp_backup_codes
    FOR ALL
    TO service_role
    USING (true)
    WITH CHECK (true);

COMMENT ON POLICY "hard_gate_service_role_totp_backup_codes_all" ON totp_backup_codes IS 
    'HARD GATE: Only service_role (backend) can access backup codes. No authenticated/anon access.';

-- trusted_devices: Service role full access (HARD GATE)
CREATE POLICY "hard_gate_service_role_trusted_devices_all" ON trusted_devices
    FOR ALL
    TO service_role
    USING (true)
    WITH CHECK (true);

COMMENT ON POLICY "hard_gate_service_role_trusted_devices_all" ON trusted_devices IS 
    'HARD GATE: Only service_role (backend) can access trusted devices. No authenticated/anon access.';

-- ============================================================================
-- Step 4: Explicit DENY policies for anon and authenticated roles
-- ============================================================================

-- Explicit deny for anon on all 2FA tables
CREATE POLICY "hard_gate_deny_anon_user_2fa" ON user_2fa
    FOR ALL
    TO anon
    USING (false)
    WITH CHECK (false);

CREATE POLICY "hard_gate_deny_anon_totp_backup_codes" ON totp_backup_codes
    FOR ALL
    TO anon
    USING (false)
    WITH CHECK (false);

CREATE POLICY "hard_gate_deny_anon_trusted_devices" ON trusted_devices
    FOR ALL
    TO anon
    USING (false)
    WITH CHECK (false);

-- Explicit deny for authenticated on all 2FA tables
-- This is the KEY difference from soft gate - authenticated users CANNOT access
CREATE POLICY "hard_gate_deny_authenticated_user_2fa" ON user_2fa
    FOR ALL
    TO authenticated
    USING (false)
    WITH CHECK (false);

CREATE POLICY "hard_gate_deny_authenticated_totp_backup_codes" ON totp_backup_codes
    FOR ALL
    TO authenticated
    USING (false)
    WITH CHECK (false);

CREATE POLICY "hard_gate_deny_authenticated_trusted_devices" ON trusted_devices
    FOR ALL
    TO authenticated
    USING (false)
    WITH CHECK (false);

COMMENT ON POLICY "hard_gate_deny_anon_user_2fa" ON user_2fa IS 
    'HARD GATE: Explicitly deny anon access to 2FA secrets';
COMMENT ON POLICY "hard_gate_deny_authenticated_user_2fa" ON user_2fa IS 
    'HARD GATE: Explicitly deny authenticated user direct access to 2FA secrets (must go through backend)';

-- ============================================================================
-- Step 5: Verification
-- ============================================================================

DO $$
DECLARE
    table_name TEXT;
    policy_count INTEGER;
    rls_enabled BOOLEAN;
    service_role_policy_exists BOOLEAN;
    deny_anon_policy_exists BOOLEAN;
    deny_auth_policy_exists BOOLEAN;
BEGIN
    RAISE NOTICE '
╔════════════════════════════════════════════════════════════╗
║  Migration 031: RLS Hard Gate for 2FA Tables               ║
╚════════════════════════════════════════════════════════════╝
';

    FOR table_name IN 
        SELECT unnest(ARRAY['user_2fa', 'totp_backup_codes', 'trusted_devices'])
    LOOP
        -- Check RLS enabled
        SELECT rowsecurity INTO rls_enabled
        FROM pg_tables
        WHERE schemaname = 'public' AND tablename = table_name;
        
        -- Check service_role policy exists
        SELECT EXISTS(
            SELECT 1 FROM pg_policies 
            WHERE schemaname = 'public' 
              AND tablename = table_name 
              AND policyname LIKE 'hard_gate_service_role%'
        ) INTO service_role_policy_exists;
        
        -- Check deny anon policy exists
        SELECT EXISTS(
            SELECT 1 FROM pg_policies 
            WHERE schemaname = 'public' 
              AND tablename = table_name 
              AND policyname LIKE 'hard_gate_deny_anon%'
        ) INTO deny_anon_policy_exists;
        
        -- Check deny authenticated policy exists
        SELECT EXISTS(
            SELECT 1 FROM pg_policies 
            WHERE schemaname = 'public' 
              AND tablename = table_name 
              AND policyname LIKE 'hard_gate_deny_authenticated%'
        ) INTO deny_auth_policy_exists;
        
        -- Count total policies
        SELECT COUNT(*) INTO policy_count
        FROM pg_policies
        WHERE schemaname = 'public' AND tablename = table_name;
        
        IF rls_enabled AND service_role_policy_exists AND deny_anon_policy_exists AND deny_auth_policy_exists THEN
            RAISE NOTICE '✅ %: HARD GATE enabled (% policies)', table_name, policy_count;
        ELSE
            RAISE WARNING '⚠️  %: HARD GATE incomplete - RLS: %, service_role: %, deny_anon: %, deny_auth: %', 
                table_name, rls_enabled, service_role_policy_exists, deny_anon_policy_exists, deny_auth_policy_exists;
        END IF;
    END LOOP;
    
    RAISE NOTICE '
╔════════════════════════════════════════════════════════════╗
║  Summary                                                   ║
╠════════════════════════════════════════════════════════════╣
║  Security Model (HARD GATE):                               ║
║  - service_role: Full access (backend services only)       ║
║  - authenticated: NO access (physically blocked)           ║
║  - anon: NO access (physically blocked)                    ║
╠════════════════════════════════════════════════════════════╣
║  Protected Tables:                                         ║
║  ✅ user_2fa - TOTP secrets and 2FA configuration          ║
║  ✅ totp_backup_codes - Single-use backup recovery codes   ║
║  ✅ trusted_devices - Remember this device tokens          ║
╠════════════════════════════════════════════════════════════╣
║  Why HARD GATE?                                            ║
║  - Autonomous agents cannot accidentally access 2FA data   ║
║  - Physical database-level blocking (not app-level)        ║
║  - Even if agent bypasses app logic, DB blocks access      ║
╚════════════════════════════════════════════════════════════╝
';
END $$;

COMMIT;

-- ============================================================================
-- Final Status
-- ============================================================================

DO $$
BEGIN
    RAISE NOTICE '
╔════════════════════════════════════════════════════════════╗
║  Migration 031: COMPLETE ✅                                ║
╠════════════════════════════════════════════════════════════╣
║  2FA Tables now have HARD GATE RLS protection              ║
║  Only backend services (service_role) can access           ║
╠════════════════════════════════════════════════════════════╣
║  Next Steps:                                               ║
║  1. Test backend 2FA operations still work                 ║
║  2. Verify frontend cannot directly access 2FA tables      ║
║  3. Monitor for any authentication errors                  ║
╚════════════════════════════════════════════════════════════╝
';
END $$;
