-- ============================================================================
-- Migration 043: Create Memory v2 Tables (EPIC G)
-- ============================================================================
-- 
-- Purpose: Create tables for the 4-layer Memory v2 system (Blueprint Section 5.1)
-- Used by: handoff/20250928/40_App/orchestrator/memory/memory_v2.py
-- EPIC: G - Memory v2 (4-Layer Memory System)
--
-- Tables:
-- 1. memory_v2_knowledge - Knowledge Base layer (pgvector)
-- 2. memory_v2_governance - Governance Memory layer (PostgreSQL)
--
-- Note: Short-Term and Agent Interaction layers use Redis (no SQL tables needed)
--
-- ============================================================================

CREATE EXTENSION IF NOT EXISTS vector;

-- ============================================================================
-- Table 1: Knowledge Base Memory (Layer 3)
-- ============================================================================
-- Long-term knowledge from past tasks with vector similarity search

CREATE TABLE IF NOT EXISTS memory_v2_knowledge (
    id BIGSERIAL PRIMARY KEY,
    key TEXT NOT NULL UNIQUE,
    content TEXT NOT NULL,
    scope TEXT NOT NULL DEFAULT 'global',
    metadata JSONB DEFAULT '{}',
    embedding vector(1536),
    trace_id TEXT,
    agent_id TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ
);

-- Indexes for knowledge base
CREATE INDEX IF NOT EXISTS idx_memory_v2_knowledge_key ON memory_v2_knowledge(key);
CREATE INDEX IF NOT EXISTS idx_memory_v2_knowledge_scope ON memory_v2_knowledge(scope);
CREATE INDEX IF NOT EXISTS idx_memory_v2_knowledge_trace_id ON memory_v2_knowledge(trace_id);
CREATE INDEX IF NOT EXISTS idx_memory_v2_knowledge_agent_id ON memory_v2_knowledge(agent_id);
CREATE INDEX IF NOT EXISTS idx_memory_v2_knowledge_created_at ON memory_v2_knowledge(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_memory_v2_knowledge_metadata ON memory_v2_knowledge USING GIN (metadata);

-- HNSW index for vector similarity search
CREATE INDEX IF NOT EXISTS idx_memory_v2_knowledge_embedding ON memory_v2_knowledge 
    USING hnsw (embedding vector_cosine_ops)
    WITH (m = 16, ef_construction = 64);

-- ============================================================================
-- Table 2: Governance Memory (Layer 4)
-- ============================================================================
-- Safety/compliance patterns, drift analysis, routing decisions

CREATE TABLE IF NOT EXISTS memory_v2_governance (
    id BIGSERIAL PRIMARY KEY,
    key TEXT NOT NULL UNIQUE,
    content TEXT NOT NULL,
    scope TEXT NOT NULL DEFAULT 'global',
    metadata JSONB DEFAULT '{}',
    trace_id TEXT,
    agent_id TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ
);

-- Indexes for governance memory
CREATE INDEX IF NOT EXISTS idx_memory_v2_governance_key ON memory_v2_governance(key);
CREATE INDEX IF NOT EXISTS idx_memory_v2_governance_scope ON memory_v2_governance(scope);
CREATE INDEX IF NOT EXISTS idx_memory_v2_governance_trace_id ON memory_v2_governance(trace_id);
CREATE INDEX IF NOT EXISTS idx_memory_v2_governance_agent_id ON memory_v2_governance(agent_id);
CREATE INDEX IF NOT EXISTS idx_memory_v2_governance_created_at ON memory_v2_governance(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_memory_v2_governance_metadata ON memory_v2_governance USING GIN (metadata);

-- ============================================================================
-- Row Level Security (RLS)
-- ============================================================================

-- Knowledge Base RLS
ALTER TABLE public.memory_v2_knowledge ENABLE ROW LEVEL SECURITY;

CREATE POLICY "service_role_memory_v2_knowledge_all" ON public.memory_v2_knowledge
    FOR ALL
    TO service_role
    USING (true)
    WITH CHECK (true);

CREATE POLICY "authenticated_memory_v2_knowledge_read" ON public.memory_v2_knowledge
    FOR SELECT
    TO authenticated
    USING (true);

-- Governance Memory RLS
ALTER TABLE public.memory_v2_governance ENABLE ROW LEVEL SECURITY;

CREATE POLICY "service_role_memory_v2_governance_all" ON public.memory_v2_governance
    FOR ALL
    TO service_role
    USING (true)
    WITH CHECK (true);

CREATE POLICY "authenticated_memory_v2_governance_read" ON public.memory_v2_governance
    FOR SELECT
    TO authenticated
    USING (true);

-- ============================================================================
-- Vector Similarity Search Function for Knowledge Base
-- ============================================================================

CREATE OR REPLACE FUNCTION match_memory_v2_knowledge(
    query_embedding vector(1536),
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
    embedding vector(1536),
    trace_id text,
    agent_id text,
    created_at timestamptz,
    updated_at timestamptz,
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

-- ============================================================================
-- Comments
-- ============================================================================

COMMENT ON TABLE public.memory_v2_knowledge IS 
    'EPIC G: Memory v2 Knowledge Base layer - Long-term knowledge with vector similarity search';

COMMENT ON TABLE public.memory_v2_governance IS 
    'EPIC G: Memory v2 Governance layer - Safety/compliance patterns, drift analysis, routing decisions';

COMMENT ON COLUMN public.memory_v2_knowledge.key IS 
    'Unique memory key identifier';

COMMENT ON COLUMN public.memory_v2_knowledge.content IS 
    'Memory content text';

COMMENT ON COLUMN public.memory_v2_knowledge.scope IS 
    'Memory scope: task, session, agent, workflow, global';

COMMENT ON COLUMN public.memory_v2_knowledge.embedding IS 
    'Vector embedding (1536 dimensions) for similarity search';

COMMENT ON COLUMN public.memory_v2_knowledge.metadata IS 
    'JSONB metadata for additional context';

COMMENT ON FUNCTION match_memory_v2_knowledge IS 
    'Vector similarity search for Memory v2 Knowledge Base layer';

-- ============================================================================
-- Verification
-- ============================================================================

DO $$
DECLARE
    knowledge_rls_enabled BOOLEAN;
    governance_rls_enabled BOOLEAN;
    knowledge_policy_count INTEGER;
    governance_policy_count INTEGER;
BEGIN
    RAISE NOTICE '
==============================================================================
  Migration 043: Memory v2 Tables (EPIC G) - Verification
==============================================================================
';

    -- Check Knowledge Base table
    SELECT rowsecurity INTO knowledge_rls_enabled
    FROM pg_tables
    WHERE schemaname = 'public' AND tablename = 'memory_v2_knowledge';
    
    SELECT COUNT(*) INTO knowledge_policy_count
    FROM pg_policies
    WHERE schemaname = 'public' AND tablename = 'memory_v2_knowledge';
    
    IF knowledge_rls_enabled AND knowledge_policy_count >= 2 THEN
        RAISE NOTICE '  memory_v2_knowledge: RLS enabled, % policies', knowledge_policy_count;
    ELSIF knowledge_rls_enabled THEN
        RAISE WARNING '  memory_v2_knowledge: RLS enabled but only % policies', knowledge_policy_count;
    ELSE
        RAISE EXCEPTION '  memory_v2_knowledge: RLS NOT enabled';
    END IF;

    -- Check Governance table
    SELECT rowsecurity INTO governance_rls_enabled
    FROM pg_tables
    WHERE schemaname = 'public' AND tablename = 'memory_v2_governance';
    
    SELECT COUNT(*) INTO governance_policy_count
    FROM pg_policies
    WHERE schemaname = 'public' AND tablename = 'memory_v2_governance';
    
    IF governance_rls_enabled AND governance_policy_count >= 2 THEN
        RAISE NOTICE '  memory_v2_governance: RLS enabled, % policies', governance_policy_count;
    ELSIF governance_rls_enabled THEN
        RAISE WARNING '  memory_v2_governance: RLS enabled but only % policies', governance_policy_count;
    ELSE
        RAISE EXCEPTION '  memory_v2_governance: RLS NOT enabled';
    END IF;
    
    RAISE NOTICE '
==============================================================================
  Migration 043: COMPLETE
==============================================================================
  Tables Created:
  - public.memory_v2_knowledge (Knowledge Base layer with pgvector)
  - public.memory_v2_governance (Governance Memory layer)
  
  Functions Created:
  - match_memory_v2_knowledge (vector similarity search)
  
  Security Model:
  - Service role: Full access (ALL operations)
  - Authenticated: Read-only access (SELECT)
  - Anonymous/Public: No access (blocked by RLS)
  
  EPIC G: Memory v2 (Blueprint Section 5.1)
  4-Layer Memory System:
  1. Short-Term Memory - Redis (no SQL table)
  2. Agent Interaction Memory - Redis (no SQL table)
  3. Knowledge Base - memory_v2_knowledge (this migration)
  4. Governance Memory - memory_v2_governance (this migration)
==============================================================================
';
END $$;
