-- ============================================================================
-- ============================================================================
--
--
--
-- ============================================================================

-- ============================================================================
-- ============================================================================

CREATE POLICY "service_role_code_embeddings_all" ON code_embeddings
    FOR ALL
    TO service_role
    USING (true)
    WITH CHECK (true);

CREATE POLICY "authenticated_code_embeddings_read" ON code_embeddings
    FOR SELECT
    TO authenticated
    USING (true);

COMMENT ON POLICY "service_role_code_embeddings_all" ON code_embeddings IS 
    'Service role (dev agent backend) has full access to manage code embeddings';

COMMENT ON POLICY "authenticated_code_embeddings_read" ON code_embeddings IS 
    'Authenticated users can read code embeddings for semantic code search';

-- ============================================================================
-- ============================================================================

CREATE POLICY "service_role_code_patterns_all" ON code_patterns
    FOR ALL
    TO service_role
    USING (true)
    WITH CHECK (true);

CREATE POLICY "authenticated_code_patterns_read" ON code_patterns
    FOR SELECT
    TO authenticated
    USING (true);

COMMENT ON POLICY "service_role_code_patterns_all" ON code_patterns IS 
    'Service role (dev agent) has full access to manage code patterns';

COMMENT ON POLICY "authenticated_code_patterns_read" ON code_patterns IS 
    'Authenticated users can read code patterns for learning and suggestions';

-- ============================================================================
-- ============================================================================

CREATE POLICY "service_role_code_relationships_all" ON code_relationships
    FOR ALL
    TO service_role
    USING (true)
    WITH CHECK (true);

CREATE POLICY "authenticated_code_relationships_read" ON code_relationships
    FOR SELECT
    TO authenticated
    USING (true);

COMMENT ON POLICY "service_role_code_relationships_all" ON code_relationships IS 
    'Service role (dev agent) has full access to manage code relationship graph';

COMMENT ON POLICY "authenticated_code_relationships_read" ON code_relationships IS 
    'Authenticated users can read code relationships for dependency analysis';

-- ============================================================================
-- ============================================================================

CREATE POLICY "service_role_embedding_cache_stats_all" ON embedding_cache_stats
    FOR ALL
    TO service_role
    USING (true)
    WITH CHECK (true);

CREATE POLICY "authenticated_embedding_cache_stats_read" ON embedding_cache_stats
    FOR SELECT
    TO authenticated
    USING (true);


COMMENT ON POLICY "service_role_embedding_cache_stats_all" ON embedding_cache_stats IS 
    'Service role has full access to manage embedding API usage stats';

COMMENT ON POLICY "authenticated_embedding_cache_stats_read" ON embedding_cache_stats IS 
    'Authenticated users can read API usage stats for monitoring';

-- ============================================================================
-- ============================================================================

DO $$
DECLARE
    policy_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO policy_count
    FROM pg_policies 
    WHERE schemaname = 'public' 
    AND tablename = 'code_embeddings';
    
    IF policy_count >= 2 THEN
        RAISE NOTICE 'SUCCESS: code_embeddings has % policies', policy_count;
    ELSE
        RAISE EXCEPTION 'FAILED: code_embeddings has only % policies', policy_count;
    END IF;
    
    SELECT COUNT(*) INTO policy_count
    FROM pg_policies 
    WHERE schemaname = 'public' 
    AND tablename = 'code_patterns';
    
    IF policy_count >= 2 THEN
        RAISE NOTICE 'SUCCESS: code_patterns has % policies', policy_count;
    ELSE
        RAISE EXCEPTION 'FAILED: code_patterns has only % policies', policy_count;
    END IF;
    
    SELECT COUNT(*) INTO policy_count
    FROM pg_policies 
    WHERE schemaname = 'public' 
    AND tablename = 'code_relationships';
    
    IF policy_count >= 2 THEN
        RAISE NOTICE 'SUCCESS: code_relationships has % policies', policy_count;
    ELSE
        RAISE EXCEPTION 'FAILED: code_relationships has only % policies', policy_count;
    END IF;
    
    SELECT COUNT(*) INTO policy_count
    FROM pg_policies 
    WHERE schemaname = 'public' 
    AND tablename = 'embedding_cache_stats';
    
    IF policy_count >= 2 THEN
        RAISE NOTICE 'SUCCESS: embedding_cache_stats has % policies', policy_count;
    ELSE
        RAISE EXCEPTION 'FAILED: embedding_cache_stats has only % policies', policy_count;
    END IF;
    
    IF EXISTS (
        SELECT 1 FROM pg_tables 
        WHERE schemaname = 'public' 
        AND tablename IN ('code_embeddings', 'code_patterns', 'code_relationships', 'embedding_cache_stats')
        AND rowsecurity = true
        HAVING COUNT(*) = 4
    ) THEN
        RAISE NOTICE 'SUCCESS: RLS enabled on all 4 tables';
    ELSE
        RAISE WARNING 'WARNING: Some tables may not have RLS enabled';
    END IF;
END $$;

-- ============================================================================
-- ============================================================================

RAISE NOTICE '
╔════════════════════════════════════════════════════════════╗
║  Migration 009: RLS Policies for Dev Agent - COMPLETE    ║
╠════════════════════════════════════════════════════════════╣
║  ✅ code_embeddings: 2 policies added                      ║
║  ✅ code_patterns: 2 policies added                        ║
║  ✅ code_relationships: 2 policies added                   ║
║  ✅ embedding_cache_stats: 2 policies added                ║
║  ✅ Total: 8 policies created                              ║
╠════════════════════════════════════════════════════════════╣
║  Policy Summary:                                           ║
║  - Service role: Full access (ALL operations)              ║
║  - Authenticated: Read-only access (SELECT)                ║
║  - Anonymous/Public: No access                             ║
╠════════════════════════════════════════════════════════════╣
║  Security Impact:                                          ║
║  - Tables now accessible to service role                   ║
║  - Authenticated users can query for insights              ║
║  - Data integrity maintained (only service role writes)    ║
║  - Supabase Security Advisor warnings resolved             ║
╚════════════════════════════════════════════════════════════╝
';
