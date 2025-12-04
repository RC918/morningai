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
--
-- Note: Different environments may have different policy naming conventions:
-- - Some have: user_authenticated_agent_reputation_read (from Migration 015)
-- - Some have: agent_reputation_select_policy (legacy naming)
-- This migration handles both cases.
-- ============================================================================

BEGIN;

-- ============================================================================
-- Drop existing authenticated-only policies (all known naming conventions)
-- ============================================================================

-- Migration 015 naming convention
DROP POLICY IF EXISTS "user_authenticated_agent_reputation_read" ON public.agent_reputation;
DROP POLICY IF EXISTS "user_authenticated_reputation_events_read" ON public.reputation_events;

-- Legacy naming convention (found in staging/production environments)
DROP POLICY IF EXISTS "agent_reputation_select_policy" ON public.agent_reputation;
DROP POLICY IF EXISTS "reputation_events_select_policy" ON public.reputation_events;

-- Other possible legacy naming patterns
DROP POLICY IF EXISTS "authenticated_agent_reputation_read" ON public.agent_reputation;
DROP POLICY IF EXISTS "authenticated_reputation_events_read" ON public.reputation_events;

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

    -- Verify no other SELECT policies exist (would conflict with platform_admin policy via OR)
    -- This checks for ANY SELECT policy that is not our new platform_admin policy
    SELECT COUNT(*) INTO policy_count
    FROM pg_policies
    WHERE schemaname = 'public' 
      AND tablename IN ('agent_reputation', 'reputation_events')
      AND cmd = 'SELECT'
      AND policyname NOT IN ('platform_admin_agent_reputation_read', 'platform_admin_reputation_events_read');
    
    IF policy_count = 0 THEN
        RAISE NOTICE '✅ No conflicting SELECT policies remain';
    ELSE
        RAISE EXCEPTION '❌ Conflicting SELECT policies still exist: %. These would combine with OR logic and bypass platform_admin restriction. Migration cannot proceed.', policy_count;
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
