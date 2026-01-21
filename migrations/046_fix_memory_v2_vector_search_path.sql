-- ============================================================================
-- Migration 046: Fix Memory v2 Vector Search Path
-- ============================================================================
-- 
-- Purpose: Fix the search_path in match_memory_v2_knowledge function to include
--          the extensions schema where the vector extension is installed.
--
-- Problem: Migration 043 created the function with SET search_path = public,
--          but Supabase installs the vector extension in the 'extensions' schema.
--          This causes "operator does not exist: extensions.vector <=> extensions.vector"
--          errors when calling the function.
--
-- Solution: Recreate the function with search_path = extensions, public
--
-- Related: D-4 Auto-Fix investigation, PR #4289
--
-- ============================================================================

-- Drop and recreate the function with corrected search_path
CREATE OR REPLACE FUNCTION match_memory_v2_knowledge(
    query_embedding vector(1024),
    match_threshold float DEFAULT 0.7,
    match_count int DEFAULT 10,
    scope_filter text DEFAULT NULL,
    trace_id_filter text DEFAULT NULL
)
RETURNS TABLE (
    id bigint,
    key text,
    content text,
    scope text,
    metadata jsonb,
    embedding vector(1024),
    trace_id text,
    agent_id text,
    created_at timestamptz,
    updated_at timestamptz,
    similarity float
)
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = extensions, public
AS $$
BEGIN
    RETURN QUERY
    SELECT
        m.id,
        m.key,
        m.content,
        m.scope,
        m.metadata,
        m.embedding,
        m.trace_id,
        m.agent_id,
        m.created_at,
        m.updated_at,
        1 - (m.embedding <=> query_embedding) AS similarity
    FROM memory_v2_knowledge m
    WHERE 
        m.embedding IS NOT NULL
        AND 1 - (m.embedding <=> query_embedding) > match_threshold
        AND (scope_filter IS NULL OR m.scope = scope_filter)
        AND (trace_id_filter IS NULL OR m.trace_id = trace_id_filter)
    ORDER BY m.embedding <=> query_embedding
    LIMIT match_count;
END;
$$;

-- Update comment to reflect the fix
COMMENT ON FUNCTION match_memory_v2_knowledge IS 
    'Vector similarity search for Memory v2 Knowledge Base layer (search_path fixed in migration 046)';

-- ============================================================================
-- Verification
-- ============================================================================

DO $$
DECLARE
    func_search_path TEXT;
BEGIN
    RAISE NOTICE '
==============================================================================
  Migration 046: Fix Memory v2 Vector Search Path - Verification
==============================================================================
';

    -- Check the function's search_path setting
    SELECT proconfig::text INTO func_search_path
    FROM pg_proc
    WHERE proname = 'match_memory_v2_knowledge';
    
    IF func_search_path LIKE '%extensions%' THEN
        RAISE NOTICE '  match_memory_v2_knowledge: search_path includes extensions schema';
        RAISE NOTICE '  Current config: %', func_search_path;
    ELSE
        RAISE WARNING '  match_memory_v2_knowledge: search_path may not include extensions schema';
        RAISE WARNING '  Current config: %', COALESCE(func_search_path, 'NULL');
    END IF;
    
    RAISE NOTICE '
==============================================================================
  Migration 046: COMPLETE
==============================================================================
  Fixed:
  - match_memory_v2_knowledge function search_path now includes extensions schema
  - Vector operators (<=> for cosine distance) will now resolve correctly
  
  Before: SET search_path = public
  After:  SET search_path = extensions, public
  
  This fixes the error:
  "operator does not exist: extensions.vector <=> extensions.vector"
==============================================================================
';
END $$;
