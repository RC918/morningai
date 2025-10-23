
CREATE TABLE IF NOT EXISTS ttv_metrics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id TEXT NOT NULL,
    tenant_id TEXT NOT NULL,
    ttv_ms INTEGER NOT NULL,
    operation TEXT NOT NULL,
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    
    CONSTRAINT ttv_metrics_ttv_ms_positive CHECK (ttv_ms > 0)
);

CREATE INDEX IF NOT EXISTS idx_ttv_metrics_user_id ON ttv_metrics(user_id);
CREATE INDEX IF NOT EXISTS idx_ttv_metrics_tenant_id ON ttv_metrics(tenant_id);
CREATE INDEX IF NOT EXISTS idx_ttv_metrics_timestamp ON ttv_metrics(timestamp);
CREATE INDEX IF NOT EXISTS idx_ttv_metrics_operation ON ttv_metrics(operation);

CREATE TABLE IF NOT EXISTS path_tracking (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id TEXT NOT NULL,
    tenant_id TEXT NOT NULL,
    path_name TEXT NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('in_progress', 'completed', 'failed')),
    duration_ms INTEGER,
    error TEXT,
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    
    CONSTRAINT path_tracking_duration_positive CHECK (duration_ms IS NULL OR duration_ms >= 0)
);

CREATE INDEX IF NOT EXISTS idx_path_tracking_user_id ON path_tracking(user_id);
CREATE INDEX IF NOT EXISTS idx_path_tracking_tenant_id ON path_tracking(tenant_id);
CREATE INDEX IF NOT EXISTS idx_path_tracking_path_name ON path_tracking(path_name);
CREATE INDEX IF NOT EXISTS idx_path_tracking_status ON path_tracking(status);
CREATE INDEX IF NOT EXISTS idx_path_tracking_timestamp ON path_tracking(timestamp);

ALTER TABLE ttv_metrics ENABLE ROW LEVEL SECURITY;
ALTER TABLE path_tracking ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can insert their own TTV metrics"
    ON ttv_metrics FOR INSERT
    WITH CHECK (auth.uid()::text = user_id);

CREATE POLICY "Users can view their own TTV metrics"
    ON ttv_metrics FOR SELECT
    USING (auth.uid()::text = user_id);

CREATE POLICY "Service role has full access to TTV metrics"
    ON ttv_metrics FOR ALL
    USING (auth.jwt()->>'role' = 'service_role');

CREATE POLICY "Users can insert their own path tracking"
    ON path_tracking FOR INSERT
    WITH CHECK (auth.uid()::text = user_id);

CREATE POLICY "Users can view their own path tracking"
    ON path_tracking FOR SELECT
    USING (auth.uid()::text = user_id);

CREATE POLICY "Users can update their own path tracking"
    ON path_tracking FOR UPDATE
    USING (auth.uid()::text = user_id);

CREATE POLICY "Service role has full access to path tracking"
    ON path_tracking FOR ALL
    USING (auth.jwt()->>'role' = 'service_role');

COMMENT ON TABLE ttv_metrics IS 'Tracks Time to Value (TTV) metrics for UX baseline measurement';
COMMENT ON TABLE path_tracking IS 'Tracks critical user path completion for success rate measurement';

COMMENT ON COLUMN ttv_metrics.ttv_ms IS 'Time to Value in milliseconds from first login to first valuable operation';
COMMENT ON COLUMN ttv_metrics.operation IS 'Type of first valuable operation (e.g., dashboard_view, strategy_create)';

COMMENT ON COLUMN path_tracking.path_name IS 'Name of the critical path (e.g., login, dashboard_customization, decision_approval)';
COMMENT ON COLUMN path_tracking.status IS 'Current status of the path: in_progress, completed, or failed';
COMMENT ON COLUMN path_tracking.duration_ms IS 'Duration in milliseconds for completed/failed paths';
COMMENT ON COLUMN path_tracking.error IS 'Error message for failed paths';
