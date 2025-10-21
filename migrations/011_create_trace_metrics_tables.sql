
CREATE TABLE IF NOT EXISTS trace_metrics (
    id BIGSERIAL PRIMARY KEY,
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    trace_id VARCHAR(255) UNIQUE NOT NULL,
    duration_ms FLOAT NOT NULL,
    status VARCHAR(50),
    url TEXT,
    method VARCHAR(10),
    llm_model VARCHAR(100),
    llm_tokens INTEGER DEFAULT 0,
    llm_cost DECIMAL(10, 4) DEFAULT 0.0,
    error TEXT,
    user_agent TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_trace_metrics_timestamp 
ON trace_metrics(timestamp DESC);

CREATE INDEX IF NOT EXISTS idx_trace_metrics_trace_id 
ON trace_metrics(trace_id);

CREATE INDEX IF NOT EXISTS idx_trace_metrics_cost 
ON trace_metrics(llm_cost DESC) WHERE llm_cost > 0;

CREATE TABLE IF NOT EXISTS alerts (
    id BIGSERIAL PRIMARY KEY,
    type VARCHAR(50) NOT NULL,
    message TEXT NOT NULL,
    severity VARCHAR(20) NOT NULL,
    trace_id VARCHAR(255),
    value JSONB,
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    acknowledged BOOLEAN DEFAULT FALSE,
    acknowledged_at TIMESTAMPTZ,
    acknowledged_by VARCHAR(255)
);

CREATE INDEX IF NOT EXISTS idx_alerts_timestamp 
ON alerts(timestamp DESC);

CREATE INDEX IF NOT EXISTS idx_alerts_type_severity 
ON alerts(type, severity);

CREATE INDEX IF NOT EXISTS idx_alerts_unacknowledged 
ON alerts(acknowledged) WHERE acknowledged = FALSE;

CREATE MATERIALIZED VIEW IF NOT EXISTS daily_cost_summary AS
SELECT 
    DATE(timestamp) as date,
    llm_model,
    COUNT(*) as request_count,
    SUM(llm_tokens) as total_tokens,
    SUM(llm_cost) as total_cost,
    AVG(duration_ms) as avg_duration,
    COUNT(CASE WHEN error IS NOT NULL THEN 1 END) as error_count
FROM trace_metrics
WHERE timestamp > NOW() - INTERVAL '90 days'
GROUP BY DATE(timestamp), llm_model
ORDER BY DATE(timestamp) DESC, total_cost DESC;

CREATE UNIQUE INDEX IF NOT EXISTS idx_daily_cost_summary 
ON daily_cost_summary(date, llm_model);

CREATE OR REPLACE FUNCTION refresh_daily_cost_summary()
RETURNS void AS $$
BEGIN
    REFRESH MATERIALIZED VIEW CONCURRENTLY daily_cost_summary;
END;
$$ LANGUAGE plpgsql;


COMMENT ON TABLE trace_metrics IS 'Stores Vercel trace data for performance and cost monitoring';
COMMENT ON TABLE alerts IS 'Stores monitoring alerts triggered by trace analysis';
COMMENT ON MATERIALIZED VIEW daily_cost_summary IS 'Daily aggregation of LLM costs and usage';
COMMENT ON FUNCTION refresh_daily_cost_summary() IS 'Refresh daily cost summary materialized view';
