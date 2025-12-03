-- ============================================================================
-- Migration 032: Vector Similarity Search Functions
-- ============================================================================
-- 
-- Purpose: Enable true vector similarity search for memory and failure_memory tables
-- Used by: handoff/20250928/40_App/orchestrator/memory/pgvector_store.py
-- Phase: Phase 2 - Brain Layer (pgvector similarity search)
--
-- Features:
-- - Cosine similarity search functions for memory and failure_memory tables
-- - HNSW indexes for better performance (vs default IVFFlat)
-- - Configurable similarity threshold and result limit
--
-- ============================================================================

-- Ensure pgvector extension is enabled
CREATE EXTENSION IF NOT EXISTS vector;

-- ============================================================================
-- HNSW Indexes for Better Performance
-- ============================================================================
-- HNSW (Hierarchical Navigable Small World) provides better query performance
-- than IVFFlat for most use cases, especially with smaller datasets

-- Drop existing indexes if they exist (for idempotency)
DROP INDEX IF EXISTS idx_memory_embedding_hnsw;
DROP INDEX IF EXISTS idx_failure_memory_embedding_hnsw;

-- Create HNSW index on memory table
-- m=16: number of connections per layer (default 16, higher = more accurate but slower build)
-- ef_construction=64: size of dynamic candidate list during construction (default 64)
CREATE INDEX idx_memory_embedding_hnsw ON memory 
USING hnsw (embedding vector_cosine_ops)
WITH (m = 16, ef_construction = 64);

-- Create HNSW index on failure_memory table
CREATE INDEX idx_failure_memory_embedding_hnsw ON failure_memory 
USING hnsw (embedding vector_cosine_ops)
WITH (m = 16, ef_construction = 64);

-- ============================================================================
-- Vector Similarity Search Functions
-- ============================================================================

-- Drop existing functions for idempotency
DROP FUNCTION IF EXISTS match_memory_by_similarity(vector, float, int);
DROP FUNCTION IF EXISTS match_failure_memory_by_similarity(vector, float, int);
DROP FUNCTION IF EXISTS match_memory_by_similarity(vector, float, int, text);
DROP FUNCTION IF EXISTS match_failure_memory_by_similarity(vector, float, int, text);

-- ----------------------------------------------------------------------------
-- Function: match_memory_by_similarity
-- ----------------------------------------------------------------------------
-- Searches the memory table for entries similar to the query embedding
-- Uses cosine similarity (1 - cosine distance)
--
-- Parameters:
--   query_embedding: The embedding vector to search for (1536 dimensions)
--   match_threshold: Minimum similarity score (0.0 to 1.0, default 0.7)
--   match_count: Maximum number of results to return (default 5)
--   key_filter: Optional key prefix filter (default NULL for no filter)
--
-- Returns: Table with id, key, text, similarity score
-- ----------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION match_memory_by_similarity(
    query_embedding vector(1536),
    match_threshold float DEFAULT 0.7,
    match_count int DEFAULT 5,
    key_filter text DEFAULT NULL
)
RETURNS TABLE (
    id bigint,
    key text,
    text text,
    similarity float
)
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $$
BEGIN
    RETURN QUERY
    SELECT
        m.id,
        m.key,
        m.text,
        1 - (m.embedding <=> query_embedding) AS similarity
    FROM memory m
    WHERE 
        m.embedding IS NOT NULL
        AND (key_filter IS NULL OR m.key LIKE key_filter || '%')
        AND 1 - (m.embedding <=> query_embedding) > match_threshold
    ORDER BY m.embedding <=> query_embedding
    LIMIT match_count;
END;
$$;

-- ----------------------------------------------------------------------------
-- Function: match_failure_memory_by_similarity
-- ----------------------------------------------------------------------------
-- Searches the failure_memory table for entries similar to the query embedding
-- Uses cosine similarity (1 - cosine distance)
--
-- Parameters:
--   query_embedding: The embedding vector to search for (1536 dimensions)
--   match_threshold: Minimum similarity score (0.0 to 1.0, default 0.7)
--   match_count: Maximum number of results to return (default 5)
--   key_filter: Optional key prefix filter (default NULL for no filter)
--
-- Returns: Table with id, key, text, metadata, similarity score
-- ----------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION match_failure_memory_by_similarity(
    query_embedding vector(1536),
    match_threshold float DEFAULT 0.7,
    match_count int DEFAULT 5,
    key_filter text DEFAULT NULL
)
RETURNS TABLE (
    id bigint,
    key text,
    text text,
    metadata jsonb,
    similarity float
)
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $$
BEGIN
    RETURN QUERY
    SELECT
        fm.id,
        fm.key,
        fm.text,
        fm.metadata,
        1 - (fm.embedding <=> query_embedding) AS similarity
    FROM failure_memory fm
    WHERE 
        fm.embedding IS NOT NULL
        AND (key_filter IS NULL OR fm.key LIKE key_filter || '%')
        AND 1 - (fm.embedding <=> query_embedding) > match_threshold
    ORDER BY fm.embedding <=> query_embedding
    LIMIT match_count;
END;
$$;

-- Grant execute permissions to service_role
GRANT EXECUTE ON FUNCTION match_memory_by_similarity(vector, float, int, text) TO service_role;
GRANT EXECUTE ON FUNCTION match_failure_memory_by_similarity(vector, float, int, text) TO service_role;

-- ============================================================================
-- Comments
-- ============================================================================

COMMENT ON FUNCTION match_memory_by_similarity IS 
    'Search memory table by vector similarity using cosine distance (Phase 2 Brain Layer)';

COMMENT ON FUNCTION match_failure_memory_by_similarity IS 
    'Search failure_memory table by vector similarity using cosine distance (Phase 2 Brain Layer)';

COMMENT ON INDEX idx_memory_embedding_hnsw IS 
    'HNSW index for fast vector similarity search on memory table';

COMMENT ON INDEX idx_failure_memory_embedding_hnsw IS 
    'HNSW index for fast vector similarity search on failure_memory table';

-- ============================================================================
-- Verification
-- ============================================================================

DO $$
DECLARE
    memory_idx_exists BOOLEAN;
    failure_idx_exists BOOLEAN;
    memory_func_exists BOOLEAN;
    failure_func_exists BOOLEAN;
BEGIN
    RAISE NOTICE '
╔════════════════════════════════════════════════════════════╗
║  Migration 032: Vector Similarity Functions - Verification ║
╚════════════════════════════════════════════════════════════╝
';

    -- Check HNSW indexes
    SELECT EXISTS (
        SELECT 1 FROM pg_indexes 
        WHERE indexname = 'idx_memory_embedding_hnsw'
    ) INTO memory_idx_exists;
    
    SELECT EXISTS (
        SELECT 1 FROM pg_indexes 
        WHERE indexname = 'idx_failure_memory_embedding_hnsw'
    ) INTO failure_idx_exists;
    
    -- Check functions
    SELECT EXISTS (
        SELECT 1 FROM pg_proc 
        WHERE proname = 'match_memory_by_similarity'
    ) INTO memory_func_exists;
    
    SELECT EXISTS (
        SELECT 1 FROM pg_proc 
        WHERE proname = 'match_failure_memory_by_similarity'
    ) INTO failure_func_exists;
    
    IF memory_idx_exists THEN
        RAISE NOTICE '  idx_memory_embedding_hnsw: Created';
    ELSE
        RAISE WARNING '  idx_memory_embedding_hnsw: NOT created';
    END IF;
    
    IF failure_idx_exists THEN
        RAISE NOTICE '  idx_failure_memory_embedding_hnsw: Created';
    ELSE
        RAISE WARNING '  idx_failure_memory_embedding_hnsw: NOT created';
    END IF;
    
    IF memory_func_exists THEN
        RAISE NOTICE '  match_memory_by_similarity(): Created';
    ELSE
        RAISE WARNING '  match_memory_by_similarity(): NOT created';
    END IF;
    
    IF failure_func_exists THEN
        RAISE NOTICE '  match_failure_memory_by_similarity(): Created';
    ELSE
        RAISE WARNING '  match_failure_memory_by_similarity(): NOT created';
    END IF;
    
    RAISE NOTICE '
╔════════════════════════════════════════════════════════════╗
║  Migration 032: COMPLETE                                   ║
╠════════════════════════════════════════════════════════════╣
║  HNSW Indexes:                                             ║
║  - idx_memory_embedding_hnsw (m=16, ef_construction=64)    ║
║  - idx_failure_memory_embedding_hnsw (m=16, ef=64)         ║
╠════════════════════════════════════════════════════════════╣
║  SQL Functions:                                            ║
║  - match_memory_by_similarity(embedding, threshold, count) ║
║  - match_failure_memory_by_similarity(embedding, ...)      ║
╠════════════════════════════════════════════════════════════╣
║  Next Steps:                                               ║
║  1. Apply this migration to Staging Supabase               ║
║  2. Apply this migration to Production Supabase            ║
║  3. Update pgvector_store.py to use these functions        ║
╚════════════════════════════════════════════════════════════╝
';
END $$;
