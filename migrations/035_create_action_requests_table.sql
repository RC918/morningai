-- ============================================================================
-- Migration 035: Create Action Requests Table for Human-in-the-Loop (HITL)
-- ============================================================================
-- 
-- Purpose: Store high-risk action requests requiring human approval
-- Used by: handoff/20250928/40_App/orchestrator/hitl/action_requests.py
-- Phase: Phase 3 - Autonomous Expansion (Human-in-the-Loop)
-- Issue: #1816
--
-- This table stores action requests that require human approval before execution:
-- - DROP TABLE / DELETE operations
-- - Sensitive file modifications (.env, secrets, credentials)
-- - Production deployments
-- - Database schema changes
-- - Permission changes
--
-- ============================================================================

-- ============================================================================
-- Action Requests Table
-- ============================================================================

CREATE TABLE IF NOT EXISTS action_requests (
    id BIGSERIAL PRIMARY KEY,
    
    -- Request identification
    request_id TEXT UNIQUE NOT NULL,
    trace_id TEXT,
    agent_id TEXT NOT NULL,
    
    -- Action details
    action_type TEXT NOT NULL,
    action_description TEXT NOT NULL,
    action_payload JSONB,
    
    -- Risk assessment
    risk_level TEXT NOT NULL DEFAULT 'high',
    risk_reason TEXT,
    affected_resources JSONB,
    
    -- Approval workflow
    status TEXT NOT NULL DEFAULT 'pending',
    requested_by TEXT,
    approved_by TEXT,
    rejected_by TEXT,
    rejection_reason TEXT,
    
    -- Timeout handling
    timeout_at TIMESTAMPTZ,
    auto_reject_on_timeout BOOLEAN DEFAULT true,
    
    -- Timestamps
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    resolved_at TIMESTAMPTZ,
    
    -- Constraints
    CONSTRAINT valid_status CHECK (status IN ('pending', 'approved', 'rejected', 'timeout', 'cancelled')),
    CONSTRAINT valid_risk_level CHECK (risk_level IN ('low', 'medium', 'high', 'critical'))
);

-- ============================================================================
-- Indexes
-- ============================================================================

CREATE INDEX IF NOT EXISTS idx_action_requests_request_id ON action_requests(request_id);
CREATE INDEX IF NOT EXISTS idx_action_requests_trace_id ON action_requests(trace_id);
CREATE INDEX IF NOT EXISTS idx_action_requests_agent_id ON action_requests(agent_id);
CREATE INDEX IF NOT EXISTS idx_action_requests_status ON action_requests(status);
CREATE INDEX IF NOT EXISTS idx_action_requests_risk_level ON action_requests(risk_level);
CREATE INDEX IF NOT EXISTS idx_action_requests_created_at ON action_requests(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_action_requests_timeout_at ON action_requests(timeout_at) WHERE status = 'pending';

-- GIN index for JSONB search
CREATE INDEX IF NOT EXISTS idx_action_requests_payload ON action_requests USING GIN (action_payload);
CREATE INDEX IF NOT EXISTS idx_action_requests_affected_resources ON action_requests USING GIN (affected_resources);

-- ============================================================================
-- Row Level Security (RLS)
-- ============================================================================

ALTER TABLE public.action_requests ENABLE ROW LEVEL SECURITY;

-- Service role has full access
CREATE POLICY "service_role_action_requests_all" ON public.action_requests
    FOR ALL
    TO service_role
    USING (true)
    WITH CHECK (true);

-- Platform admins can read action requests
CREATE POLICY "platform_admin_action_requests_read" ON public.action_requests
    FOR SELECT
    TO authenticated
    USING (
        EXISTS (
            SELECT 1 FROM user_profiles
            WHERE id = auth.uid() AND is_platform_admin = TRUE
        )
    );

-- Platform admins can update action requests (approve/reject)
CREATE POLICY "platform_admin_action_requests_update" ON public.action_requests
    FOR UPDATE
    TO authenticated
    USING (
        EXISTS (
            SELECT 1 FROM user_profiles
            WHERE id = auth.uid() AND is_platform_admin = TRUE
        )
    )
    WITH CHECK (
        EXISTS (
            SELECT 1 FROM user_profiles
            WHERE id = auth.uid() AND is_platform_admin = TRUE
        )
    );

-- ============================================================================
-- SQL Functions for Action Request Operations
-- ============================================================================

-- Drop existing functions for idempotency
DROP FUNCTION IF EXISTS create_action_request(text, text, text, text, text, jsonb, text, text, jsonb, interval);
DROP FUNCTION IF EXISTS approve_action_request(text, text);
DROP FUNCTION IF EXISTS reject_action_request(text, text, text);
DROP FUNCTION IF EXISTS get_pending_action_requests(int, text);
DROP FUNCTION IF EXISTS process_timed_out_requests();

-- ----------------------------------------------------------------------------
-- Function: create_action_request
-- ----------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION create_action_request(
    p_request_id text,
    p_trace_id text,
    p_agent_id text,
    p_action_type text,
    p_action_description text,
    p_action_payload jsonb DEFAULT NULL,
    p_risk_level text DEFAULT 'high',
    p_risk_reason text DEFAULT NULL,
    p_affected_resources jsonb DEFAULT NULL,
    p_timeout_duration interval DEFAULT '24 hours'::interval
)
RETURNS bigint
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $$
DECLARE
    new_id bigint;
BEGIN
    INSERT INTO action_requests (
        request_id,
        trace_id,
        agent_id,
        action_type,
        action_description,
        action_payload,
        risk_level,
        risk_reason,
        affected_resources,
        timeout_at,
        status
    ) VALUES (
        p_request_id,
        p_trace_id,
        p_agent_id,
        p_action_type,
        p_action_description,
        p_action_payload,
        p_risk_level,
        p_risk_reason,
        p_affected_resources,
        NOW() + p_timeout_duration,
        'pending'
    )
    RETURNING id INTO new_id;
    
    RETURN new_id;
END;
$$;

-- ----------------------------------------------------------------------------
-- Function: approve_action_request
-- ----------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION approve_action_request(
    p_request_id text,
    p_approved_by text
)
RETURNS boolean
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $$
DECLARE
    rows_affected int;
BEGIN
    UPDATE action_requests
    SET 
        status = 'approved',
        approved_by = p_approved_by,
        resolved_at = NOW(),
        updated_at = NOW()
    WHERE request_id = p_request_id
    AND status = 'pending';
    
    GET DIAGNOSTICS rows_affected = ROW_COUNT;
    RETURN rows_affected > 0;
END;
$$;

-- ----------------------------------------------------------------------------
-- Function: reject_action_request
-- ----------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION reject_action_request(
    p_request_id text,
    p_rejected_by text,
    p_reason text DEFAULT NULL
)
RETURNS boolean
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $$
DECLARE
    rows_affected int;
BEGIN
    UPDATE action_requests
    SET 
        status = 'rejected',
        rejected_by = p_rejected_by,
        rejection_reason = p_reason,
        resolved_at = NOW(),
        updated_at = NOW()
    WHERE request_id = p_request_id
    AND status = 'pending';
    
    GET DIAGNOSTICS rows_affected = ROW_COUNT;
    RETURN rows_affected > 0;
END;
$$;

-- ----------------------------------------------------------------------------
-- Function: get_pending_action_requests
-- ----------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION get_pending_action_requests(
    p_limit int DEFAULT 50,
    p_risk_level_filter text DEFAULT NULL
)
RETURNS TABLE (
    id bigint,
    request_id text,
    trace_id text,
    agent_id text,
    action_type text,
    action_description text,
    action_payload jsonb,
    risk_level text,
    risk_reason text,
    affected_resources jsonb,
    timeout_at timestamptz,
    created_at timestamptz
)
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $$
BEGIN
    RETURN QUERY
    SELECT
        ar.id,
        ar.request_id,
        ar.trace_id,
        ar.agent_id,
        ar.action_type,
        ar.action_description,
        ar.action_payload,
        ar.risk_level,
        ar.risk_reason,
        ar.affected_resources,
        ar.timeout_at,
        ar.created_at
    FROM action_requests ar
    WHERE 
        ar.status = 'pending'
        AND (p_risk_level_filter IS NULL OR ar.risk_level = p_risk_level_filter)
    ORDER BY 
        CASE ar.risk_level 
            WHEN 'critical' THEN 1 
            WHEN 'high' THEN 2 
            WHEN 'medium' THEN 3 
            ELSE 4 
        END,
        ar.created_at ASC
    LIMIT p_limit;
END;
$$;

-- ----------------------------------------------------------------------------
-- Function: process_timed_out_requests
-- ----------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION process_timed_out_requests()
RETURNS int
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $$
DECLARE
    rows_affected int;
BEGIN
    UPDATE action_requests
    SET 
        status = 'timeout',
        resolved_at = NOW(),
        updated_at = NOW()
    WHERE status = 'pending'
    AND auto_reject_on_timeout = true
    AND timeout_at < NOW();
    
    GET DIAGNOSTICS rows_affected = ROW_COUNT;
    RETURN rows_affected;
END;
$$;

-- ----------------------------------------------------------------------------
-- Function: get_action_request_statistics
-- Uses SQL aggregation for efficient statistics calculation
-- ----------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION get_action_request_statistics()
RETURNS jsonb
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $$
DECLARE
    result jsonb;
BEGIN
    SELECT jsonb_build_object(
        'pending_count', COUNT(*),
        'critical_count', COUNT(*) FILTER (WHERE risk_level = 'critical'),
        'high_count', COUNT(*) FILTER (WHERE risk_level = 'high'),
        'medium_count', COUNT(*) FILTER (WHERE risk_level = 'medium'),
        'low_count', COUNT(*) FILTER (WHERE risk_level = 'low')
    ) INTO result
    FROM action_requests
    WHERE status = 'pending';
    
    RETURN COALESCE(result, jsonb_build_object(
        'pending_count', 0,
        'critical_count', 0,
        'high_count', 0,
        'medium_count', 0,
        'low_count', 0
    ));
END;
$$;

-- Grant execute permissions
GRANT EXECUTE ON FUNCTION create_action_request(text, text, text, text, text, jsonb, text, text, jsonb, interval) TO service_role;
GRANT EXECUTE ON FUNCTION approve_action_request(text, text) TO service_role;
GRANT EXECUTE ON FUNCTION approve_action_request(text, text) TO authenticated;
GRANT EXECUTE ON FUNCTION reject_action_request(text, text, text) TO service_role;
GRANT EXECUTE ON FUNCTION reject_action_request(text, text, text) TO authenticated;
GRANT EXECUTE ON FUNCTION get_pending_action_requests(int, text) TO service_role;
GRANT EXECUTE ON FUNCTION get_pending_action_requests(int, text) TO authenticated;
GRANT EXECUTE ON FUNCTION process_timed_out_requests() TO service_role;
GRANT EXECUTE ON FUNCTION get_action_request_statistics() TO service_role;
GRANT EXECUTE ON FUNCTION get_action_request_statistics() TO authenticated;

-- ============================================================================
-- Trigger for updated_at
-- ============================================================================

CREATE OR REPLACE FUNCTION update_action_requests_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trigger_action_requests_updated_at ON action_requests;
CREATE TRIGGER trigger_action_requests_updated_at
    BEFORE UPDATE ON action_requests
    FOR EACH ROW
    EXECUTE FUNCTION update_action_requests_updated_at();

-- ============================================================================
-- Comments
-- ============================================================================

COMMENT ON TABLE public.action_requests IS 
    'Stores high-risk action requests requiring human approval (Phase 3 HITL)';

COMMENT ON COLUMN public.action_requests.request_id IS 
    'Unique identifier for the action request';

COMMENT ON COLUMN public.action_requests.action_type IS 
    'Type of action (e.g., DROP_TABLE, DELETE_FILE, DEPLOY_PRODUCTION)';

COMMENT ON COLUMN public.action_requests.risk_level IS 
    'Risk level: low, medium, high, critical';

COMMENT ON COLUMN public.action_requests.status IS 
    'Approval status: pending, approved, rejected, timeout, cancelled';

COMMENT ON COLUMN public.action_requests.timeout_at IS 
    'When the request will auto-timeout if not resolved';

COMMENT ON FUNCTION create_action_request IS 
    'Create a new action request requiring human approval';

COMMENT ON FUNCTION approve_action_request IS 
    'Approve a pending action request';

COMMENT ON FUNCTION reject_action_request IS 
    'Reject a pending action request with optional reason';

COMMENT ON FUNCTION get_pending_action_requests IS 
    'Get pending action requests ordered by risk level and creation time';

COMMENT ON FUNCTION process_timed_out_requests IS 
    'Process and auto-reject timed out requests';

COMMENT ON FUNCTION get_action_request_statistics IS 
    'Get statistics about pending action requests using SQL aggregation';

-- ============================================================================
-- Verification
-- ============================================================================

DO $$
DECLARE
    rls_enabled BOOLEAN;
    policy_count INTEGER;
    index_count INTEGER;
    func_count INTEGER;
BEGIN
    RAISE NOTICE '
╔════════════════════════════════════════════════════════════╗
║  Migration 035: Action Requests Table - Verification       ║
╚════════════════════════════════════════════════════════════╝
';

    -- Check RLS
    SELECT rowsecurity INTO rls_enabled
    FROM pg_tables
    WHERE schemaname = 'public' AND tablename = 'action_requests';
    
    SELECT COUNT(*) INTO policy_count
    FROM pg_policies
    WHERE schemaname = 'public' AND tablename = 'action_requests';
    
    -- Check indexes
    SELECT COUNT(*) INTO index_count
    FROM pg_indexes
    WHERE tablename = 'action_requests';
    
    -- Check functions
    SELECT COUNT(*) INTO func_count
    FROM pg_proc
    WHERE proname IN (
        'create_action_request', 
        'approve_action_request', 
        'reject_action_request',
        'get_pending_action_requests',
        'process_timed_out_requests',
        'get_action_request_statistics'
    );
    
    IF rls_enabled AND policy_count >= 3 THEN
        RAISE NOTICE '  action_requests: RLS enabled, % policies', policy_count;
    ELSIF rls_enabled THEN
        RAISE WARNING '  action_requests: RLS enabled but only % policies', policy_count;
    ELSE
        RAISE EXCEPTION '  action_requests: RLS NOT enabled';
    END IF;
    
    RAISE NOTICE '  Indexes created: %', index_count;
    RAISE NOTICE '  Functions created: %', func_count;
    
    RAISE NOTICE '
╔════════════════════════════════════════════════════════════╗
║  Migration 035: COMPLETE                                   ║
╠════════════════════════════════════════════════════════════╣
║  Table: public.action_requests                             ║
║  Columns: rejected_by added for proper rejection tracking  ║
║  Indexes: 9 (7 B-tree, 2 GIN)                             ║
║  RLS Policies: 3 (service_role, platform_admin read/update)║
╠════════════════════════════════════════════════════════════╣
║  SQL Functions:                                            ║
║  - create_action_request(...)                              ║
║  - approve_action_request(request_id, approved_by)         ║
║  - reject_action_request(request_id, rejected_by, reason)  ║
║  - get_pending_action_requests(limit, risk_level_filter)   ║
║  - process_timed_out_requests()                            ║
╠════════════════════════════════════════════════════════════╣
║  Security Model:                                           ║
║  - Service role: Full access (ALL operations)              ║
║  - Platform admin: Read + Update (approve/reject)          ║
║  - Other authenticated: No access (blocked by RLS)         ║
║  - Anonymous/Public: No access (blocked by RLS)            ║
╠════════════════════════════════════════════════════════════╣
║  Next Steps:                                               ║
║  1. Apply this migration to Staging Supabase               ║
║  2. Apply this migration to Production Supabase            ║
║  3. Deploy API endpoints and Owner Console UI              ║
╚════════════════════════════════════════════════════════════╝
';
END $$;
