-- Migration 030: Create RPC function for planner metrics aggregation
-- This function performs database-level aggregation for better performance
-- compared to fetching all events and aggregating in Python.

-- Drop existing function if it exists (for idempotency)
DROP FUNCTION IF EXISTS get_planner_metrics_by_provider(integer, text);

-- Create the RPC function for metrics aggregation
CREATE OR REPLACE FUNCTION get_planner_metrics_by_provider(
    p_days integer DEFAULT 7,
    p_planner_type text DEFAULT NULL
)
RETURNS TABLE (
    provider text,
    total_requests bigint,
    avg_latency_ms numeric,
    success_rate numeric,
    error_rate numeric
)
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $$
BEGIN
    RETURN QUERY
    SELECT
        pe.provider::text,
        COUNT(*)::bigint AS total_requests,
        AVG(pe.planning_time_ms)::numeric AS avg_latency_ms,
        (COUNT(CASE WHEN jsonb_array_length(pe.actual_plan_steps) > 0 THEN 1 END)::numeric / COUNT(*)::numeric) AS success_rate,
        (COUNT(CASE WHEN pe.actual_plan_steps IS NULL OR jsonb_array_length(pe.actual_plan_steps) = 0 THEN 1 END)::numeric / COUNT(*)::numeric) AS error_rate
    FROM planner_events pe
    WHERE pe.provider IS NOT NULL
      AND pe.timestamp >= (NOW() - (p_days || ' days')::interval)
      AND (p_planner_type IS NULL OR pe.planner_type = p_planner_type)
    GROUP BY pe.provider;
END;
$$;

-- Grant execute permission to authenticated users
GRANT EXECUTE ON FUNCTION get_planner_metrics_by_provider(integer, text) TO authenticated;
GRANT EXECUTE ON FUNCTION get_planner_metrics_by_provider(integer, text) TO service_role;

-- Add comment for documentation
COMMENT ON FUNCTION get_planner_metrics_by_provider IS 
'Aggregates planner metrics by provider for experiment comparison.
Uses database-level aggregation for better performance.
Parameters:
  - p_days: Number of days to look back (default: 7)
  - p_planner_type: Filter by planner type (default: NULL for all types)
Returns: provider, total_requests, avg_latency_ms, success_rate, error_rate';
