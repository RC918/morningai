-- ============================================================================
-- Migration 037: Create Tenant Quotas and Resource Usage Tables
-- ============================================================================
-- Purpose: Implement multi-tenant resource isolation with quota management
-- 
-- Phase 4: Engineering Optimization (#1820)
-- 
-- Tables Created:
-- - tenant_quotas: Configurable resource limits per tenant
-- - tenant_usage: Real-time resource usage tracking
-- - tenant_usage_history: Historical usage data for analytics
--
-- Security Model:
-- - RLS enabled with tenant isolation
-- - Only service_role can modify quotas
-- - Tenants can only view their own usage
-- ============================================================================

BEGIN;

-- ============================================================================
-- Step 1: Create tenant_quotas table
-- ============================================================================

CREATE TABLE IF NOT EXISTS tenant_quotas (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL UNIQUE,
    
    -- API Rate Limits
    api_requests_per_minute INTEGER NOT NULL DEFAULT 60,
    api_requests_per_hour INTEGER NOT NULL DEFAULT 1000,
    api_requests_per_day INTEGER NOT NULL DEFAULT 10000,
    
    -- Agent Execution Limits
    max_concurrent_tasks INTEGER NOT NULL DEFAULT 5,
    max_tasks_per_day INTEGER NOT NULL DEFAULT 100,
    max_task_duration_seconds INTEGER NOT NULL DEFAULT 300,
    
    -- Storage Limits (in bytes)
    max_storage_bytes BIGINT NOT NULL DEFAULT 1073741824,  -- 1GB default
    max_documents INTEGER NOT NULL DEFAULT 1000,
    max_embeddings INTEGER NOT NULL DEFAULT 10000,
    
    -- LLM Usage Limits
    max_llm_tokens_per_day INTEGER NOT NULL DEFAULT 100000,
    max_llm_requests_per_hour INTEGER NOT NULL DEFAULT 100,
    
    -- PR/Code Generation Limits
    max_prs_per_day INTEGER NOT NULL DEFAULT 10,
    max_code_generations_per_hour INTEGER NOT NULL DEFAULT 50,
    
    -- Metadata
    plan_tier VARCHAR(50) NOT NULL DEFAULT 'free',
    custom_limits JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    
    CONSTRAINT valid_plan_tier CHECK (plan_tier IN ('free', 'starter', 'pro', 'enterprise', 'custom'))
);

COMMENT ON TABLE tenant_quotas IS 
    'Phase 4: Tenant resource quotas for multi-tenant isolation. Defines limits per tenant.';

-- ============================================================================
-- Step 2: Create tenant_usage table (real-time tracking)
-- ============================================================================

CREATE TABLE IF NOT EXISTS tenant_usage (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL UNIQUE,
    
    -- Current Period Usage (resets periodically)
    api_requests_minute INTEGER NOT NULL DEFAULT 0,
    api_requests_hour INTEGER NOT NULL DEFAULT 0,
    api_requests_day INTEGER NOT NULL DEFAULT 0,
    
    -- Task Usage
    concurrent_tasks INTEGER NOT NULL DEFAULT 0,
    tasks_today INTEGER NOT NULL DEFAULT 0,
    
    -- Storage Usage
    storage_bytes_used BIGINT NOT NULL DEFAULT 0,
    documents_count INTEGER NOT NULL DEFAULT 0,
    embeddings_count INTEGER NOT NULL DEFAULT 0,
    
    -- LLM Usage
    llm_tokens_today INTEGER NOT NULL DEFAULT 0,
    llm_requests_hour INTEGER NOT NULL DEFAULT 0,
    
    -- PR/Code Usage
    prs_today INTEGER NOT NULL DEFAULT 0,
    code_generations_hour INTEGER NOT NULL DEFAULT 0,
    
    -- Reset Timestamps
    minute_reset_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    hour_reset_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    day_reset_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    
    -- Metadata
    last_activity_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

COMMENT ON TABLE tenant_usage IS 
    'Phase 4: Real-time tenant resource usage tracking. Updated on each API call.';

-- ============================================================================
-- Step 3: Create tenant_usage_history table (analytics)
-- ============================================================================

CREATE TABLE IF NOT EXISTS tenant_usage_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL,
    
    -- Period Information
    period_type VARCHAR(10) NOT NULL,  -- 'hourly', 'daily', 'monthly'
    period_start TIMESTAMPTZ NOT NULL,
    period_end TIMESTAMPTZ NOT NULL,
    
    -- Aggregated Usage
    api_requests_total INTEGER NOT NULL DEFAULT 0,
    tasks_total INTEGER NOT NULL DEFAULT 0,
    llm_tokens_total INTEGER NOT NULL DEFAULT 0,
    prs_total INTEGER NOT NULL DEFAULT 0,
    code_generations_total INTEGER NOT NULL DEFAULT 0,
    
    -- Peak Usage
    peak_concurrent_tasks INTEGER NOT NULL DEFAULT 0,
    peak_api_requests_minute INTEGER NOT NULL DEFAULT 0,
    
    -- Cost Tracking (for billing)
    estimated_cost_usd DECIMAL(10, 4) DEFAULT 0,
    
    -- Metadata
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    
    CONSTRAINT valid_period_type CHECK (period_type IN ('hourly', 'daily', 'monthly')),
    CONSTRAINT unique_tenant_period UNIQUE (tenant_id, period_type, period_start)
);

COMMENT ON TABLE tenant_usage_history IS 
    'Phase 4: Historical tenant usage data for analytics and billing.';

-- ============================================================================
-- Step 4: Create indexes for performance
-- ============================================================================

CREATE INDEX IF NOT EXISTS idx_tenant_quotas_tenant_id ON tenant_quotas(tenant_id);
CREATE INDEX IF NOT EXISTS idx_tenant_quotas_plan_tier ON tenant_quotas(plan_tier);

CREATE INDEX IF NOT EXISTS idx_tenant_usage_tenant_id ON tenant_usage(tenant_id);
CREATE INDEX IF NOT EXISTS idx_tenant_usage_last_activity ON tenant_usage(last_activity_at);

CREATE INDEX IF NOT EXISTS idx_tenant_usage_history_tenant_id ON tenant_usage_history(tenant_id);
CREATE INDEX IF NOT EXISTS idx_tenant_usage_history_period ON tenant_usage_history(period_type, period_start);
CREATE INDEX IF NOT EXISTS idx_tenant_usage_history_tenant_period ON tenant_usage_history(tenant_id, period_type, period_start);

-- ============================================================================
-- Step 5: Enable RLS
-- ============================================================================

ALTER TABLE tenant_quotas ENABLE ROW LEVEL SECURITY;
ALTER TABLE tenant_usage ENABLE ROW LEVEL SECURITY;
ALTER TABLE tenant_usage_history ENABLE ROW LEVEL SECURITY;

-- ============================================================================
-- Step 6: Create RLS Policies
-- ============================================================================

-- tenant_quotas: Service role full access, tenants can only read their own
CREATE POLICY "service_role_tenant_quotas_all" ON tenant_quotas
    FOR ALL
    TO service_role
    USING (true)
    WITH CHECK (true);

CREATE POLICY "tenant_read_own_quotas" ON tenant_quotas
    FOR SELECT
    TO authenticated
    USING (tenant_id = (SELECT tenant_id FROM user_profiles WHERE id = auth.uid()));

-- tenant_usage: Service role full access, tenants can only read their own
CREATE POLICY "service_role_tenant_usage_all" ON tenant_usage
    FOR ALL
    TO service_role
    USING (true)
    WITH CHECK (true);

CREATE POLICY "tenant_read_own_usage" ON tenant_usage
    FOR SELECT
    TO authenticated
    USING (tenant_id = (SELECT tenant_id FROM user_profiles WHERE id = auth.uid()));

-- tenant_usage_history: Service role full access, tenants can only read their own
CREATE POLICY "service_role_tenant_usage_history_all" ON tenant_usage_history
    FOR ALL
    TO service_role
    USING (true)
    WITH CHECK (true);

CREATE POLICY "tenant_read_own_usage_history" ON tenant_usage_history
    FOR SELECT
    TO authenticated
    USING (tenant_id = (SELECT tenant_id FROM user_profiles WHERE id = auth.uid()));

-- ============================================================================
-- Step 7: Create helper functions
-- ============================================================================

-- Function to get tenant quota with defaults
CREATE OR REPLACE FUNCTION get_tenant_quota(p_tenant_id UUID)
RETURNS TABLE (
    api_requests_per_minute INTEGER,
    api_requests_per_hour INTEGER,
    api_requests_per_day INTEGER,
    max_concurrent_tasks INTEGER,
    max_tasks_per_day INTEGER,
    max_task_duration_seconds INTEGER,
    max_storage_bytes BIGINT,
    max_documents INTEGER,
    max_embeddings INTEGER,
    max_llm_tokens_per_day INTEGER,
    max_llm_requests_per_hour INTEGER,
    max_prs_per_day INTEGER,
    max_code_generations_per_hour INTEGER,
    plan_tier VARCHAR
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        COALESCE(q.api_requests_per_minute, 60),
        COALESCE(q.api_requests_per_hour, 1000),
        COALESCE(q.api_requests_per_day, 10000),
        COALESCE(q.max_concurrent_tasks, 5),
        COALESCE(q.max_tasks_per_day, 100),
        COALESCE(q.max_task_duration_seconds, 300),
        COALESCE(q.max_storage_bytes, 1073741824::BIGINT),
        COALESCE(q.max_documents, 1000),
        COALESCE(q.max_embeddings, 10000),
        COALESCE(q.max_llm_tokens_per_day, 100000),
        COALESCE(q.max_llm_requests_per_hour, 100),
        COALESCE(q.max_prs_per_day, 10),
        COALESCE(q.max_code_generations_per_hour, 50),
        COALESCE(q.plan_tier, 'free'::VARCHAR)
    FROM tenant_quotas q
    WHERE q.tenant_id = p_tenant_id;
    
    -- Return defaults if no quota record exists
    IF NOT FOUND THEN
        RETURN QUERY SELECT 
            60, 1000, 10000, 5, 100, 300, 
            1073741824::BIGINT, 1000, 10000, 100000, 100, 10, 50, 'free'::VARCHAR;
    END IF;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER STABLE;

COMMENT ON FUNCTION get_tenant_quota IS 
    'Get tenant quota limits with defaults for missing records';

-- Function to check if tenant is within quota
CREATE OR REPLACE FUNCTION check_tenant_quota(
    p_tenant_id UUID,
    p_resource_type VARCHAR,
    p_increment INTEGER DEFAULT 1
)
RETURNS TABLE (
    allowed BOOLEAN,
    current_usage INTEGER,
    quota_limit INTEGER,
    remaining INTEGER
) AS $$
DECLARE
    v_usage INTEGER;
    v_limit INTEGER;
BEGIN
    -- Get current usage and limit based on resource type
    CASE p_resource_type
        WHEN 'api_minute' THEN
            SELECT u.api_requests_minute, q.api_requests_per_minute
            INTO v_usage, v_limit
            FROM tenant_usage u
            JOIN tenant_quotas q ON u.tenant_id = q.tenant_id
            WHERE u.tenant_id = p_tenant_id;
            
        WHEN 'api_hour' THEN
            SELECT u.api_requests_hour, q.api_requests_per_hour
            INTO v_usage, v_limit
            FROM tenant_usage u
            JOIN tenant_quotas q ON u.tenant_id = q.tenant_id
            WHERE u.tenant_id = p_tenant_id;
            
        WHEN 'api_day' THEN
            SELECT u.api_requests_day, q.api_requests_per_day
            INTO v_usage, v_limit
            FROM tenant_usage u
            JOIN tenant_quotas q ON u.tenant_id = q.tenant_id
            WHERE u.tenant_id = p_tenant_id;
            
        WHEN 'tasks_day' THEN
            SELECT u.tasks_today, q.max_tasks_per_day
            INTO v_usage, v_limit
            FROM tenant_usage u
            JOIN tenant_quotas q ON u.tenant_id = q.tenant_id
            WHERE u.tenant_id = p_tenant_id;
            
        WHEN 'concurrent_tasks' THEN
            SELECT u.concurrent_tasks, q.max_concurrent_tasks
            INTO v_usage, v_limit
            FROM tenant_usage u
            JOIN tenant_quotas q ON u.tenant_id = q.tenant_id
            WHERE u.tenant_id = p_tenant_id;
            
        WHEN 'llm_tokens_day' THEN
            SELECT u.llm_tokens_today, q.max_llm_tokens_per_day
            INTO v_usage, v_limit
            FROM tenant_usage u
            JOIN tenant_quotas q ON u.tenant_id = q.tenant_id
            WHERE u.tenant_id = p_tenant_id;
            
        WHEN 'prs_day' THEN
            SELECT u.prs_today, q.max_prs_per_day
            INTO v_usage, v_limit
            FROM tenant_usage u
            JOIN tenant_quotas q ON u.tenant_id = q.tenant_id
            WHERE u.tenant_id = p_tenant_id;
            
        ELSE
            -- Unknown resource type, allow by default
            RETURN QUERY SELECT true, 0, 0, 0;
            RETURN;
    END CASE;
    
    -- Use defaults if no records found
    IF v_usage IS NULL THEN
        v_usage := 0;
    END IF;
    IF v_limit IS NULL THEN
        v_limit := 1000;  -- Default limit
    END IF;
    
    RETURN QUERY SELECT 
        (v_usage + p_increment) <= v_limit,
        v_usage,
        v_limit,
        GREATEST(0, v_limit - v_usage - p_increment);
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

COMMENT ON FUNCTION check_tenant_quota IS 
    'Check if tenant is within quota for a specific resource type';

-- Function to increment tenant usage
CREATE OR REPLACE FUNCTION increment_tenant_usage(
    p_tenant_id UUID,
    p_resource_type VARCHAR,
    p_increment INTEGER DEFAULT 1
)
RETURNS BOOLEAN AS $$
DECLARE
    v_now TIMESTAMPTZ := NOW();
BEGIN
    -- Ensure usage record exists
    INSERT INTO tenant_usage (tenant_id)
    VALUES (p_tenant_id)
    ON CONFLICT (tenant_id) DO NOTHING;
    
    -- Reset counters if period has elapsed
    UPDATE tenant_usage
    SET 
        api_requests_minute = CASE 
            WHEN minute_reset_at < v_now - INTERVAL '1 minute' THEN 0 
            ELSE api_requests_minute 
        END,
        minute_reset_at = CASE 
            WHEN minute_reset_at < v_now - INTERVAL '1 minute' THEN v_now 
            ELSE minute_reset_at 
        END,
        api_requests_hour = CASE 
            WHEN hour_reset_at < v_now - INTERVAL '1 hour' THEN 0 
            ELSE api_requests_hour 
        END,
        hour_reset_at = CASE 
            WHEN hour_reset_at < v_now - INTERVAL '1 hour' THEN v_now 
            ELSE hour_reset_at 
        END,
        api_requests_day = CASE 
            WHEN day_reset_at < v_now - INTERVAL '1 day' THEN 0 
            ELSE api_requests_day 
        END,
        tasks_today = CASE 
            WHEN day_reset_at < v_now - INTERVAL '1 day' THEN 0 
            ELSE tasks_today 
        END,
        llm_tokens_today = CASE 
            WHEN day_reset_at < v_now - INTERVAL '1 day' THEN 0 
            ELSE llm_tokens_today 
        END,
        prs_today = CASE 
            WHEN day_reset_at < v_now - INTERVAL '1 day' THEN 0 
            ELSE prs_today 
        END,
        llm_requests_hour = CASE 
            WHEN hour_reset_at < v_now - INTERVAL '1 hour' THEN 0 
            ELSE llm_requests_hour 
        END,
        code_generations_hour = CASE 
            WHEN hour_reset_at < v_now - INTERVAL '1 hour' THEN 0 
            ELSE code_generations_hour 
        END,
        day_reset_at = CASE 
            WHEN day_reset_at < v_now - INTERVAL '1 day' THEN v_now 
            ELSE day_reset_at 
        END,
        updated_at = v_now,
        last_activity_at = v_now
    WHERE tenant_id = p_tenant_id;
    
    -- Increment the appropriate counter
    CASE p_resource_type
        WHEN 'api_minute' THEN
            UPDATE tenant_usage 
            SET api_requests_minute = api_requests_minute + p_increment,
                api_requests_hour = api_requests_hour + p_increment,
                api_requests_day = api_requests_day + p_increment
            WHERE tenant_id = p_tenant_id;
            
        WHEN 'task' THEN
            UPDATE tenant_usage 
            SET tasks_today = tasks_today + p_increment
            WHERE tenant_id = p_tenant_id;
            
        WHEN 'concurrent_task_start' THEN
            UPDATE tenant_usage 
            SET concurrent_tasks = concurrent_tasks + p_increment
            WHERE tenant_id = p_tenant_id;
            
        WHEN 'concurrent_task_end' THEN
            UPDATE tenant_usage 
            SET concurrent_tasks = GREATEST(0, concurrent_tasks - p_increment)
            WHERE tenant_id = p_tenant_id;
            
        WHEN 'llm_tokens' THEN
            UPDATE tenant_usage 
            SET llm_tokens_today = llm_tokens_today + p_increment,
                llm_requests_hour = llm_requests_hour + 1
            WHERE tenant_id = p_tenant_id;
            
        WHEN 'pr' THEN
            UPDATE tenant_usage 
            SET prs_today = prs_today + p_increment
            WHERE tenant_id = p_tenant_id;
            
        WHEN 'code_generation' THEN
            UPDATE tenant_usage 
            SET code_generations_hour = code_generations_hour + p_increment
            WHERE tenant_id = p_tenant_id;
            
        ELSE
            -- Unknown resource type, do nothing
            NULL;
    END CASE;
    
    RETURN true;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

COMMENT ON FUNCTION increment_tenant_usage IS 
    'Increment tenant usage counter for a specific resource type';

-- ============================================================================
-- Step 8: Grant permissions
-- ============================================================================

GRANT SELECT ON tenant_quotas TO authenticated;
GRANT SELECT ON tenant_usage TO authenticated;
GRANT SELECT ON tenant_usage_history TO authenticated;

GRANT ALL ON tenant_quotas TO service_role;
GRANT ALL ON tenant_usage TO service_role;
GRANT ALL ON tenant_usage_history TO service_role;

GRANT EXECUTE ON FUNCTION get_tenant_quota TO authenticated;
GRANT EXECUTE ON FUNCTION check_tenant_quota TO authenticated;
GRANT EXECUTE ON FUNCTION increment_tenant_usage TO service_role;

-- ============================================================================
-- Step 9: Verification
-- ============================================================================

DO $$
DECLARE
    table_count INTEGER;
    policy_count INTEGER;
    function_count INTEGER;
BEGIN
    -- Check tables created
    SELECT COUNT(*) INTO table_count
    FROM information_schema.tables
    WHERE table_schema = 'public'
    AND table_name IN ('tenant_quotas', 'tenant_usage', 'tenant_usage_history');
    
    -- Check RLS policies
    SELECT COUNT(*) INTO policy_count
    FROM pg_policies
    WHERE schemaname = 'public'
    AND tablename IN ('tenant_quotas', 'tenant_usage', 'tenant_usage_history');
    
    -- Check functions
    SELECT COUNT(*) INTO function_count
    FROM pg_proc
    WHERE proname IN ('get_tenant_quota', 'check_tenant_quota', 'increment_tenant_usage');
    
    RAISE NOTICE '
╔════════════════════════════════════════════════════════════╗
║  Migration 037: Tenant Quotas and Resource Usage           ║
╠════════════════════════════════════════════════════════════╣
║  Tables created: %/3                                       ║
║  RLS policies: %                                           ║
║  Helper functions: %/3                                     ║
╠════════════════════════════════════════════════════════════╣
║  Features:                                                 ║
║  - Configurable resource limits per tenant                 ║
║  - Real-time usage tracking                                ║
║  - Historical usage analytics                              ║
║  - Automatic counter reset by period                       ║
╚════════════════════════════════════════════════════════════╝
', table_count, policy_count, function_count;
    
    IF table_count < 3 THEN
        RAISE EXCEPTION 'Not all tables were created';
    END IF;
END $$;

COMMIT;
