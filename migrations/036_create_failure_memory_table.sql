-- ============================================================================
-- Migration 036: Create Failure Memory Table for Failure Record Storage
-- ============================================================================
-- 
-- Purpose: Create the 'failure_memory' table for storing failure records
-- Used by: handoff/20250928/40_App/orchestrator/failure_memory.py
-- Phase: Phase 5 - Failure memory persistence to pgvector
--
-- ============================================================================

CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS failure_memory (
    id BIGSERIAL PRIMARY KEY,
    key TEXT NOT NULL,
    text TEXT NOT NULL,
    embedding vector(1536),
    metadata JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_failure_memory_key ON failure_memory(key);
CREATE INDEX IF NOT EXISTS idx_failure_memory_created_at ON failure_memory(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_failure_memory_metadata ON failure_memory USING GIN (metadata);

-- ============================================================================
-- Row Level Security (RLS)
-- ============================================================================

ALTER TABLE public.failure_memory ENABLE ROW LEVEL SECURITY;

CREATE POLICY "service_role_failure_memory_all" ON public.failure_memory
    FOR ALL
    TO service_role
    USING (true)
    WITH CHECK (true);

CREATE POLICY "authenticated_failure_memory_read" ON public.failure_memory
    FOR SELECT
    TO authenticated
    USING (true);

COMMENT ON TABLE public.failure_memory IS 
    'Failure record storage for orchestrator (Phase 5 feature)';

COMMENT ON COLUMN public.failure_memory.key IS 
    'Failure key identifier (failure:<trace_id> or failure:<error_type>:<timestamp>)';

COMMENT ON COLUMN public.failure_memory.text IS 
    'Serialized failure content for embedding and recall';

COMMENT ON COLUMN public.failure_memory.embedding IS 
    'Vector embedding (1536 dimensions for OpenAI text-embedding-3-small), NULL when not computed';

COMMENT ON COLUMN public.failure_memory.metadata IS 
    'JSONB metadata including failure_id, trace_id, error_type, task_type, etc.';

COMMENT ON POLICY "service_role_failure_memory_all" ON public.failure_memory IS 
    'Service role (orchestrator backend) has full access to manage failure memory';

COMMENT ON POLICY "authenticated_failure_memory_read" ON public.failure_memory IS 
    'Authenticated users can read failure memory for debugging/monitoring';

-- ============================================================================
-- Verification
-- ============================================================================

DO $$
DECLARE
    rls_enabled BOOLEAN;
    policy_count INTEGER;
BEGIN
    RAISE NOTICE '
╔════════════════════════════════════════════════════════════╗
║  Migration 036: Failure Memory Table - Verification        ║
╚════════════════════════════════════════════════════════════╝
';

    SELECT rowsecurity INTO rls_enabled
    FROM pg_tables
    WHERE schemaname = 'public' AND tablename = 'failure_memory';
    
    SELECT COUNT(*) INTO policy_count
    FROM pg_policies
    WHERE schemaname = 'public' AND tablename = 'failure_memory';
    
    IF rls_enabled AND policy_count >= 2 THEN
        RAISE NOTICE '  failure_memory: RLS enabled, % policies', policy_count;
    ELSIF rls_enabled THEN
        RAISE WARNING '  failure_memory: RLS enabled but only % policies', policy_count;
    ELSE
        RAISE EXCEPTION '  failure_memory: RLS NOT enabled';
    END IF;
    
    RAISE NOTICE '
╔════════════════════════════════════════════════════════════╗
║  Migration 036: COMPLETE                                   ║
╠════════════════════════════════════════════════════════════╣
║  Table: public.failure_memory                              ║
║  Indexes: 3 (key, created_at, metadata GIN)                ║
║  RLS Policies: 2 (service_role, authenticated)             ║
╠════════════════════════════════════════════════════════════╣
║  Security Model:                                           ║
║  - Service role: Full access (ALL operations)              ║
║  - Authenticated: Read-only access (SELECT)                ║
║  - Anonymous/Public: No access (blocked by RLS)            ║
╠════════════════════════════════════════════════════════════╣
║  Next Steps:                                               ║
║  1. Apply this migration to Staging Supabase               ║
║  2. Apply this migration to Production Supabase            ║
║  3. Verify failure_memory functionality in orchestrator    ║
╚════════════════════════════════════════════════════════════╝
';
END $$;
