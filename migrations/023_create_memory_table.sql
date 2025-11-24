-- ============================================================================
-- Migration 023: Create Memory Table for Agent Memory Storage
-- ============================================================================
-- 
-- Purpose: Create the 'memory' table for lightweight agent memory storage
-- Used by: handoff/20250928/40_App/orchestrator/memory/pgvector_store.py
-- Phase: Phase 2 - Optional agent memory feature
--
-- ============================================================================

CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS memory (
    id BIGSERIAL PRIMARY KEY,
    key TEXT NOT NULL,
    text TEXT NOT NULL,
    embedding vector(1536),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_memory_key ON memory(key);
CREATE INDEX IF NOT EXISTS idx_memory_created_at ON memory(created_at DESC);

-- ============================================================================
-- Row Level Security (RLS)
-- ============================================================================

ALTER TABLE public.memory ENABLE ROW LEVEL SECURITY;

CREATE POLICY "service_role_memory_all" ON public.memory
    FOR ALL
    TO service_role
    USING (true)
    WITH CHECK (true);

CREATE POLICY "authenticated_memory_read" ON public.memory
    FOR SELECT
    TO authenticated
    USING (true);

COMMENT ON TABLE public.memory IS 
    'Lightweight agent memory store for orchestrator (Phase 2 feature)';

COMMENT ON COLUMN public.memory.key IS 
    'Memory key identifier for retrieval';

COMMENT ON COLUMN public.memory.text IS 
    'Memory content text';

COMMENT ON COLUMN public.memory.embedding IS 
    'Vector embedding (1536 dimensions for OpenAI text-embedding-3-small)';

COMMENT ON POLICY "service_role_memory_all" ON public.memory IS 
    'Service role (orchestrator backend) has full access to manage memory';

COMMENT ON POLICY "authenticated_memory_read" ON public.memory IS 
    'Authenticated users can read memory for debugging/monitoring';

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
║  Migration 023: Memory Table - Verification               ║
╚════════════════════════════════════════════════════════════╝
';

    SELECT rowsecurity INTO rls_enabled
    FROM pg_tables
    WHERE schemaname = 'public' AND tablename = 'memory';
    
    SELECT COUNT(*) INTO policy_count
    FROM pg_policies
    WHERE schemaname = 'public' AND tablename = 'memory';
    
    IF rls_enabled AND policy_count >= 2 THEN
        RAISE NOTICE '✅ memory: RLS enabled, % policies', policy_count;
    ELSIF rls_enabled THEN
        RAISE WARNING '⚠️  memory: RLS enabled but only % policies', policy_count;
    ELSE
        RAISE EXCEPTION '❌ memory: RLS NOT enabled';
    END IF;
    
    RAISE NOTICE '
╔════════════════════════════════════════════════════════════╗
║  Migration 023: COMPLETE ✅                                ║
╠════════════════════════════════════════════════════════════╣
║  Table: public.memory                                      ║
║  Indexes: 2 (key, created_at)                              ║
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
║  3. Verify memory functionality in orchestrator            ║
╚════════════════════════════════════════════════════════════╝
';
END $$;
