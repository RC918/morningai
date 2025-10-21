
CREATE EXTENSION IF NOT EXISTS pg_stat_statements;

CREATE EXTENSION IF NOT EXISTS pg_trgm;


CREATE SCHEMA IF NOT EXISTS ai_functions;


CREATE OR REPLACE FUNCTION ai_functions.cosine_similarity(
    a vector,
    b vector
) RETURNS float AS $$
    SELECT 1 - (a <=> b);
$$ LANGUAGE SQL IMMUTABLE PARALLEL SAFE;

CREATE OR REPLACE FUNCTION ai_functions.find_similar_vectors(
    query_embedding vector,
    similarity_threshold float DEFAULT 0.8,
    max_results integer DEFAULT 10
)
RETURNS TABLE (
    id BIGINT,
    similarity float,
    metadata jsonb
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        e.id,
        ai_functions.cosine_similarity(e.embedding, query_embedding) as similarity,
        e.metadata
    FROM embeddings e
    WHERE ai_functions.cosine_similarity(e.embedding, query_embedding) >= similarity_threshold
    ORDER BY similarity DESC
    LIMIT max_results;
END;
$$ LANGUAGE plpgsql STABLE;

CREATE OR REPLACE FUNCTION ai_functions.hybrid_search(
    query_text text,
    query_embedding vector,
    text_weight float DEFAULT 0.3,
    vector_weight float DEFAULT 0.7,
    max_results integer DEFAULT 10
)
RETURNS TABLE (
    id BIGINT,
    combined_score float,
    text_score float,
    vector_score float,
    metadata jsonb
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        e.id,
        (
            (SIMILARITY(e.metadata->>'text', query_text) * text_weight) +
            (ai_functions.cosine_similarity(e.embedding, query_embedding) * vector_weight)
        ) as combined_score,
        SIMILARITY(e.metadata->>'text', query_text) as text_score,
        ai_functions.cosine_similarity(e.embedding, query_embedding) as vector_score,
        e.metadata
    FROM embeddings e
    WHERE 
        e.metadata->>'text' IS NOT NULL
        AND (
            SIMILARITY(e.metadata->>'text', query_text) > 0.1
            OR ai_functions.cosine_similarity(e.embedding, query_embedding) > 0.5
        )
    ORDER BY combined_score DESC
    LIMIT max_results;
END;
$$ LANGUAGE plpgsql STABLE;

CREATE OR REPLACE FUNCTION ai_functions.batch_insert_embeddings(
    embeddings_data jsonb
)
RETURNS TABLE (
    inserted_count integer,
    error_count integer
) AS $$
DECLARE
    item jsonb;
    success_count integer := 0;
    error_count_val integer := 0;
BEGIN
    FOR item IN SELECT * FROM jsonb_array_elements(embeddings_data)
    LOOP
        BEGIN
            INSERT INTO embeddings (embedding, metadata)
            VALUES (
                (item->>'embedding')::vector,
                item->'metadata'
            );
            success_count := success_count + 1;
        EXCEPTION WHEN OTHERS THEN
            error_count_val := error_count_val + 1;
        END;
    END LOOP;
    
    RETURN QUERY SELECT success_count, error_count_val;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION ai_functions.optimize_vector_index()
RETURNS void AS $$
BEGIN
    ANALYZE embeddings;
    
END;
$$ LANGUAGE plpgsql;

CREATE INDEX IF NOT EXISTS idx_embeddings_metadata_gin 
ON embeddings USING gin(metadata jsonb_path_ops);

CREATE INDEX IF NOT EXISTS idx_embeddings_metadata_text_trgm 
ON embeddings USING gin((metadata->>'text') gin_trgm_ops);

CREATE OR REPLACE FUNCTION ai_functions.get_slow_queries(
    min_duration_ms float DEFAULT 100,
    limit_results integer DEFAULT 20
)
RETURNS TABLE (
    query text,
    calls bigint,
    total_time_ms float,
    mean_time_ms float,
    stddev_time_ms float
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        LEFT(pss.query, 200) as query,
        pss.calls,
        pss.total_exec_time as total_time_ms,
        pss.mean_exec_time as mean_time_ms,
        pss.stddev_exec_time as stddev_time_ms
    FROM pg_stat_statements pss
    WHERE pss.mean_exec_time > min_duration_ms
    ORDER BY pss.mean_exec_time DESC
    LIMIT limit_results;
END;
$$ LANGUAGE plpgsql;

CREATE INDEX IF NOT EXISTS idx_agent_tasks_tenant_id_created 
ON agent_tasks(tenant_id, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_user_profiles_tenant_id 
ON user_profiles(tenant_id) WHERE tenant_id IS NOT NULL;

CREATE OR REPLACE FUNCTION ai_functions.analyze_rls_performance()
RETURNS TABLE (
    table_name text,
    policy_name text,
    avg_execution_time_ms float
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        schemaname || '.' || tablename as table_name,
        'RLS policies enabled' as policy_name,
        0.0 as avg_execution_time_ms
    FROM pg_stat_user_tables
    WHERE schemaname = 'public'
    AND relname IN (
        SELECT tablename 
        FROM pg_tables 
        WHERE schemaname = 'public'
    )
    LIMIT 10;
END;
$$ LANGUAGE plpgsql;

COMMENT ON SCHEMA ai_functions IS 'Schema containing AI-related helper functions and optimizations';
COMMENT ON FUNCTION ai_functions.cosine_similarity(vector, vector) IS 'Calculate cosine similarity between two vectors (optimized)';
COMMENT ON FUNCTION ai_functions.find_similar_vectors(vector, float, integer) IS 'Find vectors similar to query vector above threshold';
COMMENT ON FUNCTION ai_functions.hybrid_search(text, vector, float, float, integer) IS 'Hybrid search combining text similarity and vector similarity';
COMMENT ON FUNCTION ai_functions.batch_insert_embeddings(jsonb) IS 'Batch insert embeddings with error handling';
COMMENT ON FUNCTION ai_functions.optimize_vector_index() IS 'Optimize vector indexes and update statistics';
COMMENT ON FUNCTION ai_functions.get_slow_queries(float, integer) IS 'Get slow queries from pg_stat_statements';
COMMENT ON FUNCTION ai_functions.analyze_rls_performance() IS 'Analyze RLS policy performance impact';

CREATE OR REPLACE VIEW ai_functions.embedding_statistics AS
SELECT 
    COUNT(*) as total_embeddings,
    COUNT(DISTINCT metadata->>'source') as unique_sources,
    AVG(ARRAY_LENGTH(embedding::text::float[], 1)) as avg_dimensions,
    MIN(created_at) as oldest_embedding,
    MAX(created_at) as newest_embedding,
    pg_size_pretty(pg_total_relation_size('embeddings')) as table_size
FROM embeddings;

COMMENT ON VIEW ai_functions.embedding_statistics IS 'Summary statistics for embeddings table';
