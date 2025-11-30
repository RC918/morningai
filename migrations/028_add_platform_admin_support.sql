-- ============================================================================
-- Migration 028: Add Platform Admin Support
-- Phase 6 PR-5: Three-Tier Permission Architecture
-- ============================================================================
-- This migration adds platform admin support to enable cross-tenant access
-- for platform administrators while maintaining tenant isolation for regular users.
--
-- Three-Tier Architecture:
-- 1. Platform Admin - Cross-tenant access, system-wide management
-- 2. Tenant Admin - Tenant-level management (owner/admin roles)
-- 3. Tenant User - Standard tenant access (member/viewer roles)
-- ============================================================================

-- Add is_platform_admin column to user_profiles
ALTER TABLE user_profiles
ADD COLUMN IF NOT EXISTS is_platform_admin BOOLEAN NOT NULL DEFAULT FALSE;

-- Create index for platform admin queries
CREATE INDEX IF NOT EXISTS idx_user_profiles_is_platform_admin
    ON user_profiles(is_platform_admin)
    WHERE is_platform_admin = TRUE;

-- ============================================================================
-- Update RLS Policies for Platform Admin Cross-Tenant Access
-- ============================================================================

-- Drop existing policies that need to be updated
DROP POLICY IF EXISTS "users_can_read_tenant_profiles" ON user_profiles;
DROP POLICY IF EXISTS "admins_can_update_tenant_profiles" ON user_profiles;

-- Recreate with platform admin support
CREATE POLICY "users_can_read_tenant_profiles" ON user_profiles
    FOR SELECT
    TO authenticated
    USING (
        -- Platform admins can read all profiles
        EXISTS (
            SELECT 1 FROM user_profiles
            WHERE id = auth.uid() AND is_platform_admin = TRUE
        )
        OR
        -- Regular users can only read profiles in their tenant
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
        -- Platform admins can update any profile
        EXISTS (
            SELECT 1 FROM user_profiles
            WHERE id = auth.uid() AND is_platform_admin = TRUE
        )
        OR
        -- Tenant admins can update profiles in their tenant
        (
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
    )
    WITH CHECK (
        -- Platform admins can update to any tenant and set any is_platform_admin value
        EXISTS (
            SELECT 1 FROM user_profiles
            WHERE id = auth.uid() AND is_platform_admin = TRUE
        )
        OR
        (
            -- Tenant admins can only update within their tenant
            tenant_id = (
                SELECT tenant_id 
                FROM user_profiles 
                WHERE id = auth.uid()
            )
            -- SECURITY: Non-platform admins cannot set is_platform_admin to TRUE
            -- This prevents privilege escalation attacks
            AND is_platform_admin = FALSE
        )
    );

-- ============================================================================
-- Update ai_policies RLS for Platform Admin
-- ============================================================================

DROP POLICY IF EXISTS ai_policies_select_policy ON ai_policies;
DROP POLICY IF EXISTS ai_policies_insert_policy ON ai_policies;
DROP POLICY IF EXISTS ai_policies_update_policy ON ai_policies;
DROP POLICY IF EXISTS ai_policies_delete_policy ON ai_policies;

-- Platform admins can view all policies, others only their tenant's
CREATE POLICY ai_policies_select_policy ON ai_policies
    FOR SELECT
    USING (
        -- Platform admins can view all policies
        EXISTS (
            SELECT 1 FROM user_profiles
            WHERE id = auth.uid() AND is_platform_admin = TRUE
        )
        OR
        -- Regular users can view their tenant's policies or platform-scope policies
        tenant_id IN (
            SELECT tenant_id FROM user_profiles WHERE id = auth.uid()
        )
        OR scope = 'platform'
    );

-- Platform admins can create policies for any tenant
CREATE POLICY ai_policies_insert_policy ON ai_policies
    FOR INSERT
    WITH CHECK (
        -- Platform admins can create for any tenant
        EXISTS (
            SELECT 1 FROM user_profiles
            WHERE id = auth.uid() AND is_platform_admin = TRUE
        )
        OR
        -- Tenant admins can create for their tenant
        tenant_id IN (
            SELECT tenant_id FROM user_profiles 
            WHERE id = auth.uid() AND role IN ('owner', 'admin')
        )
    );

-- Platform admins can update any policy
CREATE POLICY ai_policies_update_policy ON ai_policies
    FOR UPDATE
    USING (
        -- Platform admins can update any policy
        EXISTS (
            SELECT 1 FROM user_profiles
            WHERE id = auth.uid() AND is_platform_admin = TRUE
        )
        OR
        -- Tenant admins can update their tenant's policies
        tenant_id IN (
            SELECT tenant_id FROM user_profiles 
            WHERE id = auth.uid() AND role IN ('owner', 'admin')
        )
    );

-- Platform admins can delete any policy, owners can delete their tenant's
CREATE POLICY ai_policies_delete_policy ON ai_policies
    FOR DELETE
    USING (
        -- Platform admins can delete any policy
        EXISTS (
            SELECT 1 FROM user_profiles
            WHERE id = auth.uid() AND is_platform_admin = TRUE
        )
        OR
        -- Tenant owners can delete their tenant's policies
        tenant_id IN (
            SELECT tenant_id FROM user_profiles 
            WHERE id = auth.uid() AND role = 'owner'
        )
    );

-- ============================================================================
-- Update agent_tasks RLS for Platform Admin (if exists)
-- ============================================================================

DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.tables 
        WHERE table_schema = 'public' AND table_name = 'agent_tasks'
    ) THEN
        -- Drop and recreate agent_tasks select policy
        DROP POLICY IF EXISTS "tenant_isolation_select" ON agent_tasks;
        
        EXECUTE '
        CREATE POLICY "tenant_isolation_select" ON agent_tasks
            FOR SELECT
            USING (
                EXISTS (
                    SELECT 1 FROM user_profiles
                    WHERE id = auth.uid() AND is_platform_admin = TRUE
                )
                OR
                tenant_id IN (
                    SELECT tenant_id FROM user_profiles WHERE id = auth.uid()
                )
            )
        ';
    END IF;
END $$;

-- ============================================================================
-- Comments for Documentation
-- ============================================================================

COMMENT ON COLUMN user_profiles.is_platform_admin IS
    'Platform admin flag for cross-tenant access. Platform admins can manage all tenants.';

COMMENT ON INDEX idx_user_profiles_is_platform_admin IS
    'Partial index for efficient platform admin lookups';

-- ============================================================================
-- Verification
-- ============================================================================

DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_schema = 'public' 
        AND table_name = 'user_profiles' 
        AND column_name = 'is_platform_admin'
    ) THEN
        RAISE NOTICE 'SUCCESS: is_platform_admin column added to user_profiles';
    ELSE
        RAISE EXCEPTION 'FAILED: is_platform_admin column not found';
    END IF;
END $$;

DO $$
BEGIN
    RAISE NOTICE '
╔══════════════════════════════════════════════════════════════════════════════╗
║                    Migration 028 Complete                                     ║
║                                                                              ║
║  Three-Tier Permission Architecture:                                         ║
║  - Added is_platform_admin column to user_profiles                           ║
║  - Updated RLS policies for cross-tenant platform admin access               ║
║  - Platform admins can now manage all tenants                                ║
║  - Tenant isolation preserved for non-platform-admin users                   ║
╚══════════════════════════════════════════════════════════════════════════════╝
';
END $$;
