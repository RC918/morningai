-- ============================================================================
-- Migration 033: Create Error-Fix Pairs Table
-- ============================================================================
-- 
-- Purpose: Store error-fix pairs for AI learning and recall
-- Used by: handoff/20250928/40_App/orchestrator/memory/error_fix_pairs.py
-- Phase: Phase 2 - Brain Layer (Long-term Memory)
--
-- This table stores pairs of:
-- - Error: The error message/context that occurred
-- - Fix: The solution/fix that resolved the error
--
-- This enables the AI to learn from past mistakes and suggest fixes for
-- similar errors in the future.
--
-- ============================================================================

CREATE EXTENSION IF NOT EXISTS vector;

-- ============================================================================
-- Error-Fix Pairs Table
-- ============================================================================

CREATE TABLE IF NOT EXISTS error_fix_pairs (
    id BIGSERIAL PRIMARY KEY,
    
    -- Error information
    error_text TEXT NOT NULL,
    error_embedding vector(1536),
    error_type TEXT,
    error_context JSONB,
    
    -- Fix information
    fix_text TEXT NOT NULL,
    fix_embedding vector(1536),
    fix_type TEXT,
    fix_metadata JSONB,
    
    -- Relationship and tracking
    trace_id TEXT,
    task_type TEXT,
    success_count INTEGER DEFAULT 0,
    failure_count INTEGER DEFAULT 0,
    confidence_score FLOAT DEFAULT 0.5,
    
    -- Timestamps
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    last_used_at TIMESTAMPTZ
);

-- ============================================================================
-- Indexes
-- ============================================================================

-- HNSW index for error embedding similarity search
CREATE INDEX IF NOT EXISTS idx_error_fix_pairs_error_embedding_hnsw ON error_fix_pairs 
USING hnsw (error_embedding vector_cosine_ops)
WITH (m = 16, ef_construction = 64);

-- HNSW index for fix embedding similarity search (for finding similar fixes)
CREATE INDEX IF NOT EXISTS idx_error_fix_pairs_fix_embedding_hnsw ON error_fix_pairs 
USING hnsw (fix_embedding vector_cosine_ops)
WITH (m = 16, ef_construction = 64);

-- Standard indexes for filtering
CREATE INDEX IF NOT EXISTS idx_error_fix_pairs_error_type ON error_fix_pairs(error_type);
CREATE INDEX IF NOT EXISTS idx_error_fix_pairs_task_type ON error_fix_pairs(task_type);
CREATE INDEX IF NOT EXISTS idx_error_fix_pairs_trace_id ON error_fix_pairs(trace_id);
CREATE INDEX IF NOT EXISTS idx_error_fix_pairs_created_at ON error_fix_pairs(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_error_fix_pairs_confidence ON error_fix_pairs(confidence_score DESC);

-- GIN index for JSONB metadata search
CREATE INDEX IF NOT EXISTS idx_error_fix_pairs_error_context ON error_fix_pairs USING GIN (error_context);
CREATE INDEX IF NOT EXISTS idx_error_fix_pairs_fix_metadata ON error_fix_pairs USING GIN (fix_metadata);

-- ============================================================================
-- Row Level Security (RLS)
-- ============================================================================

ALTER TABLE public.error_fix_pairs ENABLE ROW LEVEL SECURITY;

CREATE POLICY "service_role_error_fix_pairs_all" ON public.error_fix_pairs
    FOR ALL
    TO service_role
    USING (true)
    WITH CHECK (true);

CREATE POLICY "authenticated_error_fix_pairs_read" ON public.error_fix_pairs
    FOR SELECT
    TO authenticated
    USING (true);

-- ============================================================================
-- SQL Functions for Error-Fix Pair Operations
-- ============================================================================

-- Drop existing functions for idempotency
DROP FUNCTION IF EXISTS match_error_fix_pairs_by_error(vector, float, int, text);
DROP FUNCTION IF EXISTS update_error_fix_pair_stats(bigint, boolean);

-- ----------------------------------------------------------------------------
-- Function: match_error_fix_pairs_by_error
-- ----------------------------------------------------------------------------
-- Searches for error-fix pairs similar to the given error embedding
--
-- Parameters:
--   query_embedding: The error embedding vector to search for
--   match_threshold: Minimum similarity score (0.0 to 1.0, default 0.7)
--   match_count: Maximum number of results to return (default 5)
--   error_type_filter: Optional error type filter (default NULL)
--
-- Returns: Table with error-fix pair details and similarity score
-- ----------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION match_error_fix_pairs_by_error(
    query_embedding vector(1536),
    match_threshold float DEFAULT 0.7,
    match_count int DEFAULT 5,
    error_type_filter text DEFAULT NULL
)
RETURNS TABLE (
    id bigint,
    error_text text,
    error_type text,
    fix_text text,
    fix_type text,
    confidence_score float,
    success_count integer,
    failure_count integer,
    similarity float
)
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $$
BEGIN
    RETURN QUERY
    SELECT
        efp.id,
        efp.error_text,
        efp.error_type,
        efp.fix_text,
        efp.fix_type,
        efp.confidence_score,
        efp.success_count,
        efp.failure_count,
        1 - (efp.error_embedding <=> query_embedding) AS similarity
    FROM error_fix_pairs efp
    WHERE 
        efp.error_embedding IS NOT NULL
        AND (error_type_filter IS NULL OR efp.error_type = error_type_filter)
        AND 1 - (efp.error_embedding <=> query_embedding) > match_threshold
    ORDER BY efp.error_embedding <=> query_embedding
    LIMIT match_count;
END;
$$;

-- ----------------------------------------------------------------------------
-- Function: update_error_fix_pair_stats
-- ----------------------------------------------------------------------------
-- Updates the success/failure counts and confidence score for an error-fix pair
--
-- Parameters:
--   pair_id: The ID of the error-fix pair to update
--   was_successful: Whether the fix was successful
--
-- Returns: The updated confidence score
-- ----------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION update_error_fix_pair_stats(
    pair_id bigint,
    was_successful boolean
)
RETURNS float
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $$
DECLARE
    new_confidence float;
BEGIN
    IF was_successful THEN
        UPDATE error_fix_pairs
        SET 
            success_count = success_count + 1,
            confidence_score = (success_count + 1)::float / (success_count + failure_count + 1)::float,
            last_used_at = NOW(),
            updated_at = NOW()
        WHERE id = pair_id
        RETURNING confidence_score INTO new_confidence;
    ELSE
        UPDATE error_fix_pairs
        SET 
            failure_count = failure_count + 1,
            confidence_score = success_count::float / (success_count + failure_count + 1)::float,
            last_used_at = NOW(),
            updated_at = NOW()
        WHERE id = pair_id
        RETURNING confidence_score INTO new_confidence;
    END IF;
    
    RETURN COALESCE(new_confidence, 0.0);
END;
$$;

-- Grant execute permissions
GRANT EXECUTE ON FUNCTION match_error_fix_pairs_by_error(vector, float, int, text) TO service_role;
GRANT EXECUTE ON FUNCTION update_error_fix_pair_stats(bigint, boolean) TO service_role;

-- ============================================================================
-- Comments
-- ============================================================================

COMMENT ON TABLE public.error_fix_pairs IS 
    'Stores error-fix pairs for AI learning and recall (Phase 2 Brain Layer)';

COMMENT ON COLUMN public.error_fix_pairs.error_text IS 
    'The error message or context that occurred';

COMMENT ON COLUMN public.error_fix_pairs.error_embedding IS 
    'Vector embedding of the error text for similarity search';

COMMENT ON COLUMN public.error_fix_pairs.fix_text IS 
    'The solution or fix that resolved the error';

COMMENT ON COLUMN public.error_fix_pairs.fix_embedding IS 
    'Vector embedding of the fix text for finding similar solutions';

COMMENT ON COLUMN public.error_fix_pairs.confidence_score IS 
    'Confidence score based on success/failure ratio (0.0 to 1.0)';

COMMENT ON FUNCTION match_error_fix_pairs_by_error IS 
    'Search for error-fix pairs similar to a given error embedding';

COMMENT ON FUNCTION update_error_fix_pair_stats IS 
    'Update success/failure stats and confidence score for an error-fix pair';

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
║  Migration 033: Error-Fix Pairs Table - Verification       ║
╚════════════════════════════════════════════════════════════╝
';

    -- Check RLS
    SELECT rowsecurity INTO rls_enabled
    FROM pg_tables
    WHERE schemaname = 'public' AND tablename = 'error_fix_pairs';
    
    SELECT COUNT(*) INTO policy_count
    FROM pg_policies
    WHERE schemaname = 'public' AND tablename = 'error_fix_pairs';
    
    -- Check indexes
    SELECT COUNT(*) INTO index_count
    FROM pg_indexes
    WHERE tablename = 'error_fix_pairs';
    
    -- Check functions
    SELECT COUNT(*) INTO func_count
    FROM pg_proc
    WHERE proname IN ('match_error_fix_pairs_by_error', 'update_error_fix_pair_stats');
    
    IF rls_enabled AND policy_count >= 2 THEN
        RAISE NOTICE '  error_fix_pairs: RLS enabled, % policies', policy_count;
    ELSIF rls_enabled THEN
        RAISE WARNING '  error_fix_pairs: RLS enabled but only % policies', policy_count;
    ELSE
        RAISE EXCEPTION '  error_fix_pairs: RLS NOT enabled';
    END IF;
    
    RAISE NOTICE '  Indexes created: %', index_count;
    RAISE NOTICE '  Functions created: %', func_count;
    
    RAISE NOTICE '
╔════════════════════════════════════════════════════════════╗
║  Migration 033: COMPLETE                                   ║
╠════════════════════════════════════════════════════════════╣
║  Table: public.error_fix_pairs                             ║
║  Indexes: 9 (2 HNSW, 5 B-tree, 2 GIN)                      ║
║  RLS Policies: 2 (service_role, authenticated)             ║
╠════════════════════════════════════════════════════════════╣
║  SQL Functions:                                            ║
║  - match_error_fix_pairs_by_error(embedding, ...)          ║
║  - update_error_fix_pair_stats(pair_id, was_successful)    ║
╠════════════════════════════════════════════════════════════╣
║  Security Model:                                           ║
║  - Service role: Full access (ALL operations)              ║
║  - Authenticated: Read-only access (SELECT)                ║
║  - Anonymous/Public: No access (blocked by RLS)            ║
╠════════════════════════════════════════════════════════════╣
║  Next Steps:                                               ║
║  1. Apply this migration to Staging Supabase               ║
║  2. Apply this migration to Production Supabase            ║
║  3. Implement error_fix_pairs.py Python wrapper            ║
╚════════════════════════════════════════════════════════════╝
';
END $$;
