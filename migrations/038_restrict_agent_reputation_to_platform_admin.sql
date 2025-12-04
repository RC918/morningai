-- ============================================================================
-- Migration 038: Restrict agent_reputation tables to platform_admin only
-- ============================================================================
-- Issue: #1940
-- 
-- Background:
-- Migration 015 restricted agent_reputation and reputation_events to 
-- authenticated users (auth.uid() IS NOT NULL). However, these tables contain
-- internal system data about AI agent performance and should only be accessible
-- to platform administrators.
--
-- This migration updates the RLS policies to restrict access to users with
-- is_platform_admin = TRUE in user_profiles.
-- ============================================================================

BEGIN;

-- ============================================================================
-- Drop existing authenticated-only policies
-- ============================================================================

DROP POLICY IF EXISTS "user_authenticated_agent_reputation_read" ON public.agent_reputation;
DROP POLICY IF EXISTS "user_authenticated_reputation_events_read" ON public.reputation_events;

-- ============================================================================
-- Create platform_admin-only policies for agent_reputation
-- ============================================================================

CREATE POLICY "platform_admin_agent_reputation_read" ON public.agent_reputation
    FOR SELECT
    TO authenticated
    USING (
        EXISTS (
            SELECT 1 FROM user_profiles
            WHERE id = auth.uid() AND is_platform_admin = TRUE
        )
    );

COMMENT ON POLICY "platform_admin_agent_reputation_read" ON public.agent_reputation IS 
    'Only platform administrators can read agent reputation data. This is internal system data for AI governance.';

-- ============================================================================
-- Create platform_admin-only policies for reputation_events
-- ============================================================================

CREATE POLICY "platform_admin_reputation_events_read" ON public.reputation_events
    FOR SELECT
    TO authenticated
    USING (
        EXISTS (
            SELECT 1 FROM user_profiles
            WHERE id = auth.uid() AND is_platform_admin = TRUE
        )
    );

COMMENT ON POLICY "platform_admin_reputation_events_read" ON public.reputation_events IS 
    'Only platform administrators can read reputation events. This is internal system data for AI governance audit trail.';

-- ============================================================================
-- Verification
-- ============================================================================

DO $$
DECLARE
    policy_count INTEGER;
BEGIN
    RAISE NOTICE '
╔════════════════════════════════════════════════════════════╗
║  Migration 038: Agent Reputation RLS Restriction           ║
╚════════════════════════════════════════════════════════════╝
';

    -- Verify agent_reputation policy
    SELECT COUNT(*) INTO policy_count
    FROM pg_policies
    WHERE schemaname = 'public' 
      AND tablename = 'agent_reputation'
      AND policyname = 'platform_admin_agent_reputation_read';
    
    IF policy_count > 0 THEN
        RAISE NOTICE '✅ agent_reputation: Restricted to platform_admin only';
    ELSE
        RAISE EXCEPTION '❌ agent_reputation: platform_admin policy not created';
    END IF;

    -- Verify reputation_events policy
    SELECT COUNT(*) INTO policy_count
    FROM pg_policies
    WHERE schemaname = 'public' 
      AND tablename = 'reputation_events'
      AND policyname = 'platform_admin_reputation_events_read';
    
    IF policy_count > 0 THEN
        RAISE NOTICE '✅ reputation_events: Restricted to platform_admin only';
    ELSE
        RAISE EXCEPTION '❌ reputation_events: platform_admin policy not created';
    END IF;

    -- Verify old policies are removed
    SELECT COUNT(*) INTO policy_count
    FROM pg_policies
    WHERE schemaname = 'public' 
      AND tablename IN ('agent_reputation', 'reputation_events')
      AND policyname LIKE 'user_authenticated%';
    
    IF policy_count = 0 THEN
        RAISE NOTICE '✅ Old user_authenticated policies removed';
    ELSE
        RAISE WARNING '⚠️  Old user_authenticated policies still exist: %', policy_count;
    END IF;

    RAISE NOTICE '
╔════════════════════════════════════════════════════════════╗
║  Summary                                                   ║
╠════════════════════════════════════════════════════════════╣
║  Security Model (Updated):                                 ║
║  - Service role: Full access (ALL operations)              ║
║  - Platform admins: Read access to agent reputation data   ║
║  - Regular users: No access to agent reputation data       ║
║  - Anon key: No access                                     ║
╠════════════════════════════════════════════════════════════╣
║  Affected Tables:                                          ║
║  ✅ agent_reputation - platform_admin only                 ║
║  ✅ reputation_events - platform_admin only                ║
╚════════════════════════════════════════════════════════════╝
';
END $$;

COMMIT;

-- ============================================================================
-- Post-migration notes
-- ============================================================================

DO $$
BEGIN
    RAISE NOTICE '
╔════════════════════════════════════════════════════════════╗
║  Migration 038: COMPLETE ✅                                ║
╠════════════════════════════════════════════════════════════╣
║  Next Steps:                                               ║
║  1. Verify platform_admin users can access governance UI   ║
║  2. Verify regular users cannot see agent reputation data  ║
║  3. Update governance dashboard to handle 403 gracefully   ║
╚════════════════════════════════════════════════════════════╝
';
END $$;
