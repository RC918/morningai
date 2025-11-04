
CREATE TABLE IF NOT EXISTS agent_reputation (
    agent_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    agent_type TEXT NOT NULL CHECK (agent_type IN ('dev_agent', 'ops_agent', 'pm_agent', 'growth_strategist', 'meta_agent')),
    reputation_score INTEGER NOT NULL DEFAULT 100,
    
    pr_merged_count INTEGER NOT NULL DEFAULT 0,
    pr_reverted_count INTEGER NOT NULL DEFAULT 0,
    human_escalation_count INTEGER NOT NULL DEFAULT 0,
    test_pass_count INTEGER NOT NULL DEFAULT 0,
    test_fail_count INTEGER NOT NULL DEFAULT 0,
    violation_count INTEGER NOT NULL DEFAULT 0,
    cost_overrun_count INTEGER NOT NULL DEFAULT 0,
    
    test_pass_rate FLOAT NOT NULL DEFAULT 1.0,
    cost_efficiency_score FLOAT NOT NULL DEFAULT 1.0,
    
    permission_level TEXT NOT NULL DEFAULT 'sandbox_only' 
        CHECK (permission_level IN ('sandbox_only', 'staging_access', 'prod_low_risk', 'prod_full_access')),
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_updated TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_activity TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    CONSTRAINT reputation_score_range CHECK (reputation_score >= 0 AND reputation_score <= 999),
    CONSTRAINT test_pass_rate_range CHECK (test_pass_rate >= 0.0 AND test_pass_rate <= 1.0),
    CONSTRAINT cost_efficiency_range CHECK (cost_efficiency_score >= 0.0)
);

CREATE TABLE IF NOT EXISTS reputation_events (
    event_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    agent_id UUID NOT NULL REFERENCES agent_reputation(agent_id) ON DELETE CASCADE,
    event_type TEXT NOT NULL CHECK (event_type IN (
        'pr_merged',
        'pr_reverted',
        'human_escalation',
        'test_passed',
        'test_failed',
        'cost_overrun',
        'violation_detected',
        'ci_success',
        'ci_failure',
        'permission_upgraded',
        'permission_downgraded'
    )),
    delta INTEGER NOT NULL,
    reason TEXT,
    trace_id UUID,
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    CONSTRAINT delta_range CHECK (delta >= -100 AND delta <= 100)
);

CREATE INDEX IF NOT EXISTS idx_reputation_events_agent ON reputation_events(agent_id);
CREATE INDEX IF NOT EXISTS idx_reputation_events_trace ON reputation_events(trace_id);
CREATE INDEX IF NOT EXISTS idx_reputation_events_type ON reputation_events(event_type);
CREATE INDEX IF NOT EXISTS idx_reputation_events_created ON reputation_events(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_agent_reputation_type ON agent_reputation(agent_type);
CREATE INDEX IF NOT EXISTS idx_agent_reputation_level ON agent_reputation(permission_level);
CREATE INDEX IF NOT EXISTS idx_agent_reputation_score ON agent_reputation(reputation_score DESC);

CREATE OR REPLACE FUNCTION update_agent_reputation(
    p_agent_id UUID,
    p_delta INTEGER
) RETURNS void AS $$
BEGIN
    UPDATE agent_reputation
    SET 
        reputation_score = GREATEST(0, LEAST(999, reputation_score + p_delta)),
        last_updated = NOW()
    WHERE agent_id = p_agent_id;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION calculate_test_pass_rate(
    p_agent_id UUID
) RETURNS FLOAT AS $$
DECLARE
    v_pass_count INTEGER;
    v_fail_count INTEGER;
    v_total INTEGER;
BEGIN
    SELECT test_pass_count, test_fail_count
    INTO v_pass_count, v_fail_count
    FROM agent_reputation
    WHERE agent_id = p_agent_id;
    
    v_total := v_pass_count + v_fail_count;
    
    IF v_total = 0 THEN
        RETURN 1.0;
    END IF;
    
    RETURN v_pass_count::FLOAT / v_total::FLOAT;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION update_permission_level(
    p_agent_id UUID
) RETURNS TEXT AS $$
DECLARE
    v_score INTEGER;
    v_new_level TEXT;
    v_old_level TEXT;
BEGIN
    SELECT reputation_score, permission_level
    INTO v_score, v_old_level
    FROM agent_reputation
    WHERE agent_id = p_agent_id;
    
    IF v_score >= 160 THEN
        v_new_level := 'prod_full_access';
    ELSIF v_score >= 130 THEN
        v_new_level := 'prod_low_risk';
    ELSIF v_score >= 90 THEN
        v_new_level := 'staging_access';
    ELSE
        v_new_level := 'sandbox_only';
    END IF;
    
    IF v_new_level != v_old_level THEN
        UPDATE agent_reputation
        SET 
            permission_level = v_new_level,
            last_updated = NOW()
        WHERE agent_id = p_agent_id;
        
        INSERT INTO reputation_events (agent_id, event_type, delta, reason)
        VALUES (
            p_agent_id,
            CASE 
                WHEN v_new_level > v_old_level THEN 'permission_upgraded'
                ELSE 'permission_downgraded'
            END,
            0,
            format('Permission changed from %s to %s (score: %s)', v_old_level, v_new_level, v_score)
        );
    END IF;
    
    RETURN v_new_level;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION record_reputation_event(
    p_agent_id UUID,
    p_event_type TEXT,
    p_delta INTEGER,
    p_reason TEXT DEFAULT NULL,
    p_trace_id UUID DEFAULT NULL,
    p_metadata JSONB DEFAULT NULL
) RETURNS UUID AS $$
DECLARE
    v_event_id UUID;
BEGIN
    INSERT INTO reputation_events (agent_id, event_type, delta, reason, trace_id, metadata)
    VALUES (p_agent_id, p_event_type, p_delta, p_reason, p_trace_id, p_metadata)
    RETURNING event_id INTO v_event_id;
    
    PERFORM update_agent_reputation(p_agent_id, p_delta);
    
    CASE p_event_type
        WHEN 'pr_merged' THEN
            UPDATE agent_reputation
            SET pr_merged_count = pr_merged_count + 1
            WHERE agent_id = p_agent_id;
        
        WHEN 'pr_reverted' THEN
            UPDATE agent_reputation
            SET pr_reverted_count = pr_reverted_count + 1
            WHERE agent_id = p_agent_id;
        
        WHEN 'human_escalation' THEN
            UPDATE agent_reputation
            SET human_escalation_count = human_escalation_count + 1
            WHERE agent_id = p_agent_id;
        
        WHEN 'test_passed' THEN
            UPDATE agent_reputation
            SET 
                test_pass_count = test_pass_count + 1,
                test_pass_rate = calculate_test_pass_rate(p_agent_id)
            WHERE agent_id = p_agent_id;
        
        WHEN 'test_failed' THEN
            UPDATE agent_reputation
            SET 
                test_fail_count = test_fail_count + 1,
                test_pass_rate = calculate_test_pass_rate(p_agent_id)
            WHERE agent_id = p_agent_id;
        
        WHEN 'violation_detected' THEN
            UPDATE agent_reputation
            SET violation_count = violation_count + 1
            WHERE agent_id = p_agent_id;
        
        WHEN 'cost_overrun' THEN
            UPDATE agent_reputation
            SET cost_overrun_count = cost_overrun_count + 1
            WHERE agent_id = p_agent_id;
        
        ELSE
            NULL;
    END CASE;
    
    PERFORM update_permission_level(p_agent_id);
    
    UPDATE agent_reputation
    SET last_activity = NOW()
    WHERE agent_id = p_agent_id;
    
    RETURN v_event_id;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION get_agent_reputation_summary(
    p_agent_id UUID
) RETURNS JSONB AS $$
DECLARE
    v_summary JSONB;
BEGIN
    SELECT jsonb_build_object(
        'agent_id', agent_id,
        'agent_type', agent_type,
        'reputation_score', reputation_score,
        'permission_level', permission_level,
        'statistics', jsonb_build_object(
            'pr_merged', pr_merged_count,
            'pr_reverted', pr_reverted_count,
            'human_escalations', human_escalation_count,
            'test_pass_rate', test_pass_rate,
            'violations', violation_count,
            'cost_overruns', cost_overrun_count
        ),
        'timestamps', jsonb_build_object(
            'created_at', created_at,
            'last_updated', last_updated,
            'last_activity', last_activity
        )
    )
    INTO v_summary
    FROM agent_reputation
    WHERE agent_id = p_agent_id;
    
    RETURN v_summary;
END;
$$ LANGUAGE plpgsql;

INSERT INTO agent_reputation (agent_type, reputation_score, permission_level)
VALUES 
    ('dev_agent', 100, 'sandbox_only'),
    ('ops_agent', 100, 'sandbox_only'),
    ('pm_agent', 100, 'sandbox_only'),
    ('growth_strategist', 100, 'sandbox_only'),
    ('meta_agent', 130, 'staging_access')  -- Meta agent starts with higher permissions
ON CONFLICT (agent_id) DO NOTHING;

COMMENT ON TABLE agent_reputation IS 'Tracks reputation scores and permissions for AI agents';
COMMENT ON TABLE reputation_events IS 'Audit log of all reputation-affecting events';
COMMENT ON FUNCTION update_agent_reputation IS 'Updates agent reputation score with bounds checking';
COMMENT ON FUNCTION record_reputation_event IS 'Records a reputation event and updates all related metrics';
COMMENT ON FUNCTION get_agent_reputation_summary IS 'Returns comprehensive reputation summary for an agent';
