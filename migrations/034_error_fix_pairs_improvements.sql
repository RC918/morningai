-- ============================================================================
-- Migration 034: Error-Fix Pairs Improvements
-- ============================================================================
-- 
-- Purpose: Improve error-fix pairs SQL functions for better performance
-- Related Issues: #1834, #1835
-- Phase: Phase 2 - Brain Layer (Code Quality Improvements)
--
-- Changes:
-- 1. Refactor update_error_fix_pair_stats to use CASE expressions (#1835)
-- 2. Add get_error_fix_pairs_stats for DB-level aggregation (#1834)
--
-- ============================================================================

-- ============================================================================
-- #1835: Refactor update_error_fix_pair_stats using CASE expressions
-- ============================================================================
-- 
-- Previous implementation used IF/ELSE with two separate UPDATE statements.
-- New implementation uses a single UPDATE with CASE expressions for:
-- - Better readability
-- - Single atomic operation
-- - Reduced code duplication
--
-- ============================================================================

DROP FUNCTION IF EXISTS update_error_fix_pair_stats(bigint, boolean);

CREATE OR REPLACE FUNCTION update_error_fix_pair_stats(
    p_pair_id bigint,
    p_was_successful boolean
)
RETURNS float
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $$
DECLARE
    new_confidence float;
    new_success_count integer;
    new_failure_count integer;
BEGIN
    UPDATE error_fix_pairs
    SET 
        success_count = success_count + CASE WHEN p_was_successful THEN 1 ELSE 0 END,
        failure_count = failure_count + CASE WHEN p_was_successful THEN 0 ELSE 1 END,
        last_used_at = NOW(),
        updated_at = NOW()
    WHERE id = p_pair_id
    RETURNING success_count, failure_count INTO new_success_count, new_failure_count;
    
    -- Calculate confidence score: success_count / total_count
    -- Avoid division by zero
    IF new_success_count + new_failure_count > 0 THEN
        new_confidence := new_success_count::float / (new_success_count + new_failure_count)::float;
        
        -- Update confidence score in a separate statement to use calculated value
        UPDATE error_fix_pairs
        SET confidence_score = new_confidence
        WHERE id = p_pair_id;
    ELSE
        new_confidence := 0.5; -- Default confidence
    END IF;
    
    RETURN COALESCE(new_confidence, 0.0);
END;
$$;

-- Grant execute permissions
GRANT EXECUTE ON FUNCTION update_error_fix_pair_stats(bigint, boolean) TO service_role;

COMMENT ON FUNCTION update_error_fix_pair_stats IS 
    'Update success/failure stats and confidence score for an error-fix pair (refactored with CASE expressions)';

-- ============================================================================
-- #1834: Add get_error_fix_pairs_stats for DB-level aggregation
-- ============================================================================
-- 
-- This function performs aggregation at the database level instead of
-- fetching all records and aggregating in Python.
--
-- Benefits:
-- - Reduced data transfer
-- - Better performance for large datasets
-- - Atomic snapshot of statistics
--
-- ============================================================================

DROP FUNCTION IF EXISTS get_error_fix_pairs_stats();

CREATE OR REPLACE FUNCTION get_error_fix_pairs_stats()
RETURNS TABLE (
    total_pairs bigint,
    with_embeddings bigint,
    total_success bigint,
    total_failure bigint,
    avg_confidence float,
    error_type_distribution jsonb
)
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $$
BEGIN
    RETURN QUERY
    SELECT 
        COUNT(*)::bigint AS total_pairs,
        COUNT(CASE WHEN error_embedding IS NOT NULL THEN 1 END)::bigint AS with_embeddings,
        COALESCE(SUM(success_count), 0)::bigint AS total_success,
        COALESCE(SUM(failure_count), 0)::bigint AS total_failure,
        COALESCE(AVG(confidence_score), 0.5)::float AS avg_confidence,
        COALESCE(
            (SELECT jsonb_object_agg(error_type, type_count)
             FROM (
                 SELECT COALESCE(error_type, 'unknown') AS error_type, COUNT(*) AS type_count
                 FROM error_fix_pairs
                 GROUP BY error_type
             ) t),
            '{}'::jsonb
        ) AS error_type_distribution
    FROM error_fix_pairs;
END;
$$;

-- Grant execute permissions
GRANT EXECUTE ON FUNCTION get_error_fix_pairs_stats() TO service_role;
GRANT EXECUTE ON FUNCTION get_error_fix_pairs_stats() TO authenticated;

COMMENT ON FUNCTION get_error_fix_pairs_stats IS 
    'Get aggregated statistics about error-fix pairs (DB-level aggregation for performance)';

-- ============================================================================
-- Verification
-- ============================================================================

DO $$
DECLARE
    func_count INTEGER;
BEGIN
    RAISE NOTICE '
╔════════════════════════════════════════════════════════════╗
║  Migration 034: Error-Fix Pairs Improvements - Verification║
╚════════════════════════════════════════════════════════════╝
';

    -- Check functions
    SELECT COUNT(*) INTO func_count
    FROM pg_proc
    WHERE proname IN ('update_error_fix_pair_stats', 'get_error_fix_pairs_stats');
    
    RAISE NOTICE '  Functions created/updated: %', func_count;
    
    RAISE NOTICE '
╔════════════════════════════════════════════════════════════╗
║  Migration 034: COMPLETE                                   ║
╠════════════════════════════════════════════════════════════╣
║  Changes:                                                  ║
║  - update_error_fix_pair_stats: Refactored with CASE      ║
║  - get_error_fix_pairs_stats: New DB-level aggregation    ║
╠════════════════════════════════════════════════════════════╣
║  Related Issues:                                           ║
║  - #1834: DB-level aggregation for stats                  ║
║  - #1835: CASE expressions for update function            ║
╚════════════════════════════════════════════════════════════╝
';
END $$;
