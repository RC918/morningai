
CREATE MATERIALIZED VIEW IF NOT EXISTS vector_visualization AS
SELECT 
    e.id,
    e.embedding,
    e.metadata->>'source' as source,
    e.metadata->>'category' as category,
    e.metadata->>'text' as text_preview,
    e.created_at,
    COUNT(q.id) as query_count,
    MAX(q.created_at) as last_queried
FROM embeddings e
LEFT JOIN vector_queries q ON q.vector_id = e.id
WHERE e.created_at > NOW() - INTERVAL '30 days'
GROUP BY e.id, e.embedding, e.metadata, e.created_at;

CREATE UNIQUE INDEX IF NOT EXISTS idx_vector_viz_id 
ON vector_visualization(id);

CREATE INDEX IF NOT EXISTS idx_vector_viz_source 
ON vector_visualization(source);

CREATE INDEX IF NOT EXISTS idx_vector_viz_query_count 
ON vector_visualization(query_count DESC);

CREATE OR REPLACE FUNCTION refresh_vector_viz()
RETURNS void AS $$
BEGIN
    REFRESH MATERIALIZED VIEW CONCURRENTLY vector_visualization;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION ai_functions_cosine_similarity(
    a vector,
    b vector
) RETURNS float AS $$
    SELECT 1 - (a <=> b);
$$ LANGUAGE SQL IMMUTABLE;

CREATE OR REPLACE FUNCTION get_vector_clusters(
    sample_size INTEGER DEFAULT 1000,
    min_cluster_size INTEGER DEFAULT 5
)
RETURNS TABLE (
    cluster_id INTEGER,
    vector_count BIGINT,
    avg_query_count FLOAT,
    source TEXT,
    representative_text TEXT
) AS $$
BEGIN
    RETURN QUERY
    WITH sampled_vectors AS (
        SELECT 
            id,
            embedding,
            source,
            text_preview,
            query_count
        FROM vector_visualization
        ORDER BY RANDOM()
        LIMIT sample_size
    ),
    clustered AS (
        SELECT 
            v1.id,
            v1.source,
            v1.text_preview,
            v1.query_count,
            COUNT(v2.id) as similar_count,
            ARRAY_AGG(v2.id) as similar_ids
        FROM sampled_vectors v1
        LEFT JOIN sampled_vectors v2 
            ON v1.id != v2.id 
            AND ai_functions_cosine_similarity(v1.embedding, v2.embedding) > 0.8
        GROUP BY v1.id, v1.source, v1.text_preview, v1.query_count
    )
    SELECT 
        ROW_NUMBER() OVER (ORDER BY COUNT(*) DESC)::INTEGER as cluster_id,
        COUNT(*)::BIGINT as vector_count,
        AVG(c.query_count)::FLOAT as avg_query_count,
        c.source::TEXT,
        MAX(c.text_preview)::TEXT as representative_text
    FROM clustered c
    WHERE c.similar_count >= min_cluster_size
    GROUP BY c.source, c.similar_count
    HAVING COUNT(*) >= min_cluster_size
    ORDER BY vector_count DESC;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION detect_memory_drift(
    lookback_days INTEGER DEFAULT 7
)
RETURNS TABLE (
    source TEXT,
    old_count BIGINT,
    new_count BIGINT,
    drift_percentage FLOAT,
    status TEXT
) AS $$
BEGIN
    RETURN QUERY
    WITH old_vectors AS (
        SELECT 
            metadata->>'source' as source,
            COUNT(*) as count
        FROM embeddings
        WHERE created_at BETWEEN 
            NOW() - INTERVAL '1 day' * (lookback_days * 2) 
            AND NOW() - INTERVAL '1 day' * lookback_days
        GROUP BY metadata->>'source'
    ),
    new_vectors AS (
        SELECT 
            metadata->>'source' as source,
            COUNT(*) as count
        FROM embeddings
        WHERE created_at >= NOW() - INTERVAL '1 day' * lookback_days
        GROUP BY metadata->>'source'
    )
    SELECT 
        COALESCE(o.source, n.source)::TEXT,
        COALESCE(o.count, 0)::BIGINT as old_count,
        COALESCE(n.count, 0)::BIGINT as new_count,
        CASE 
            WHEN COALESCE(o.count, 0) = 0 THEN 100.0
            ELSE ((n.count - o.count)::FLOAT / o.count * 100)
        END::FLOAT as drift_percentage,
        CASE 
            WHEN COALESCE(n.count, 0) > COALESCE(o.count, 0) * 1.5 THEN 'HIGH_GROWTH'
            WHEN COALESCE(n.count, 0) < COALESCE(o.count, 0) * 0.5 THEN 'HIGH_DECLINE'
            WHEN ABS(COALESCE(n.count, 0) - COALESCE(o.count, 0))::FLOAT / NULLIF(o.count, 1) > 0.2 THEN 'MODERATE_DRIFT'
            ELSE 'STABLE'
        END::TEXT as status
    FROM old_vectors o
    FULL OUTER JOIN new_vectors n ON o.source = n.source
    ORDER BY drift_percentage DESC NULLS LAST;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE VIEW vector_statistics AS
SELECT 
    source,
    COUNT(*) as total_vectors,
    AVG(query_count) as avg_queries,
    MAX(query_count) as max_queries,
    MIN(created_at) as oldest_vector,
    MAX(created_at) as newest_vector,
    COUNT(CASE WHEN query_count = 0 THEN 1 END) as unused_count,
    COUNT(CASE WHEN query_count > 10 THEN 1 END) as popular_count
FROM vector_visualization
GROUP BY source
ORDER BY total_vectors DESC;

COMMENT ON MATERIALIZED VIEW vector_visualization IS 'Aggregated vector data for PCA/t-SNE visualization';
COMMENT ON FUNCTION refresh_vector_viz() IS 'Refresh vector visualization materialized view';
COMMENT ON FUNCTION ai_functions_cosine_similarity(vector, vector) IS 'Calculate cosine similarity between two vectors';
COMMENT ON FUNCTION get_vector_clusters(INTEGER, INTEGER) IS 'Identify vector clusters using similarity threshold';
COMMENT ON FUNCTION detect_memory_drift(INTEGER) IS 'Detect significant changes in vector distribution over time';
COMMENT ON VIEW vector_statistics IS 'Summary statistics for vector usage by source';
