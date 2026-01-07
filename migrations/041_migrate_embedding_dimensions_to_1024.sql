-- ============================================================================
-- Migration 041: Migrate Embedding Dimensions from 1536 to 1024
-- ============================================================================
-- 
-- Purpose: Update all vector columns and SQL functions from 1536 to 1024 dimensions
-- to support AliCloud text-embedding-v3 which only supports [512, 768, 1024]
--
-- Related PRs:
-- - PR #3660: EmbeddingClient dynamic dimension selection
-- - PR #3652: Migrate to EmbeddingClient abstraction layer
--
-- IMPORTANT: This migration will TRUNCATE all embedding data!
-- All embeddings will need to be regenerated after this migration.
--
-- Affected tables:
-- - embeddings (migration 010)
-- - vector_queries (migration 010)
-- - error_fix_pairs (migration 033)
-- - memory (migration 023)
-- - failure_memory (migration 036)
-- - code_embeddings (dev_agent migration 001)
--
-- Affected SQL functions:
-- - match_memory_by_similarity (migration 032)
-- - match_failure_memory_by_similarity (migration 032)
-- - match_error_fix_pairs_by_error (migration 033)
--
-- ============================================================================

-- ============================================================================
-- Step 1: Truncate existing embedding data
-- ============================================================================
-- WARNING: This will delete all existing embeddings!
-- They will need to be regenerated with the new dimension size.

TRUNCATE TABLE embeddings CASCADE;
TRUNCATE TABLE vector_queries CASCADE;
TRUNCATE TABLE error_fix_pairs CASCADE;
TRUNCATE TABLE memory CASCADE;
TRUNCATE TABLE failure_memory CASCADE;

-- Note: code_embeddings is in dev_agent schema, handled separately if exists
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'code_embeddings') THEN
        TRUNCATE TABLE code_embeddings CASCADE;
        RAISE NOTICE 'Truncated code_embeddings table';
    END IF;
END $$;

-- ============================================================================
-- Step 2: Alter vector columns from 1536 to 1024 dimensions
-- ============================================================================

-- embeddings table
ALTER TABLE embeddings ALTER COLUMN embedding TYPE vector(1024);

-- vector_queries table
ALTER TABLE vector_queries ALTER COLUMN query_embedding TYPE vector(1024);

-- error_fix_pairs table
ALTER TABLE error_fix_pairs ALTER COLUMN error_embedding TYPE vector(1024);
ALTER TABLE error_fix_pairs ALTER COLUMN fix_embedding TYPE vector(1024);

-- memory table
ALTER TABLE memory ALTER COLUMN embedding TYPE vector(1024);

-- failure_memory table
ALTER TABLE failure_memory ALTER COLUMN embedding TYPE vector(1024);

-- code_embeddings table (if exists)
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'code_embeddings') THEN
        EXECUTE 'ALTER TABLE code_embeddings ALTER COLUMN embedding TYPE vector(1024)';
        RAISE NOTICE 'Altered code_embeddings.embedding to vector(1024)';
    END IF;
END $$;

-- ============================================================================
-- Step 3: Recreate SQL functions with new dimension size
-- ============================================================================

-- Drop existing functions
DROP FUNCTION IF EXISTS match_memory_by_similarity(vector, float, int, text);
DROP FUNCTION IF EXISTS match_failure_memory_by_similarity(vector, float, int, text);
DROP FUNCTION IF EXISTS match_error_fix_pairs_by_error(vector, float, int, text);

-- Recreate match_memory_by_similarity with vector(1024)
CREATE OR REPLACE FUNCTION match_memory_by_similarity(
    query_embedding vector(1024),
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

-- Recreate match_failure_memory_by_similarity with vector(1024)
CREATE OR REPLACE FUNCTION match_failure_memory_by_similarity(
    query_embedding vector(1024),
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

-- Recreate match_error_fix_pairs_by_error with vector(1024)
CREATE OR REPLACE FUNCTION match_error_fix_pairs_by_error(
    query_embedding vector(1024),
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

-- Grant execute permissions
GRANT EXECUTE ON FUNCTION match_memory_by_similarity(vector, float, int, text) TO service_role;
GRANT EXECUTE ON FUNCTION match_failure_memory_by_similarity(vector, float, int, text) TO service_role;
GRANT EXECUTE ON FUNCTION match_error_fix_pairs_by_error(vector, float, int, text) TO service_role;

-- ============================================================================
-- Step 4: Update comments
-- ============================================================================

COMMENT ON COLUMN embeddings.embedding IS 'Vector embedding (1024 dimensions for AliCloud text-embedding-v3)';
COMMENT ON COLUMN vector_queries.query_embedding IS 'Query embedding vector (1024 dimensions)';
COMMENT ON COLUMN error_fix_pairs.error_embedding IS 'Vector embedding of the error text (1024 dimensions)';
COMMENT ON COLUMN error_fix_pairs.fix_embedding IS 'Vector embedding of the fix text (1024 dimensions)';
COMMENT ON COLUMN memory.embedding IS 'Vector embedding (1024 dimensions for AliCloud text-embedding-v3)';
COMMENT ON COLUMN failure_memory.embedding IS 'Vector embedding (1024 dimensions), NULL when not computed';

-- ============================================================================
-- Verification
-- ============================================================================

DO $$
DECLARE
    embeddings_dim INTEGER;
    memory_dim INTEGER;
    error_fix_dim INTEGER;
BEGIN
    RAISE NOTICE '
============================================================================
  Migration 041: Embedding Dimensions Migration - Verification
============================================================================
';

    -- Check embeddings table dimension
    SELECT atttypmod INTO embeddings_dim
    FROM pg_attribute a
    JOIN pg_class c ON a.attrelid = c.oid
    WHERE c.relname = 'embeddings' AND a.attname = 'embedding';
    
    -- Check memory table dimension
    SELECT atttypmod INTO memory_dim
    FROM pg_attribute a
    JOIN pg_class c ON a.attrelid = c.oid
    WHERE c.relname = 'memory' AND a.attname = 'embedding';
    
    -- Check error_fix_pairs table dimension
    SELECT atttypmod INTO error_fix_dim
    FROM pg_attribute a
    JOIN pg_class c ON a.attrelid = c.oid
    WHERE c.relname = 'error_fix_pairs' AND a.attname = 'error_embedding';

    RAISE NOTICE '  embeddings.embedding dimension: %', embeddings_dim;
    RAISE NOTICE '  memory.embedding dimension: %', memory_dim;
    RAISE NOTICE '  error_fix_pairs.error_embedding dimension: %', error_fix_dim;

    RAISE NOTICE '
============================================================================
  Migration 041: COMPLETE
============================================================================
  Changes Applied:
  - All vector columns changed from vector(1536) to vector(1024)
  - All SQL functions recreated with vector(1024) parameter type
  - All existing embedding data truncated (needs regeneration)
  
  Next Steps:
  1. Deploy Python code with dynamic dimension selection (PR #3660)
  2. Re-index code_embeddings if using Knowledge Graph
  3. Error-fix pairs will accumulate automatically from new failures
============================================================================
';
END $$;
