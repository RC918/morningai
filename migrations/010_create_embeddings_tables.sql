
CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS embeddings (
    id BIGSERIAL PRIMARY KEY,
    embedding vector(1536),  -- OpenAI ada-002 dimension
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS vector_queries (
    id BIGSERIAL PRIMARY KEY,
    vector_id BIGINT REFERENCES embeddings(id) ON DELETE CASCADE,
    query_embedding vector(1536),
    similarity_score FLOAT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_embeddings_vector 
ON embeddings USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);

CREATE INDEX IF NOT EXISTS idx_embeddings_metadata_gin 
ON embeddings USING gin(metadata jsonb_path_ops);

CREATE INDEX IF NOT EXISTS idx_embeddings_created_at 
ON embeddings(created_at DESC);

CREATE INDEX IF NOT EXISTS idx_vector_queries_vector_id 
ON vector_queries(vector_id);

CREATE INDEX IF NOT EXISTS idx_vector_queries_created_at 
ON vector_queries(created_at DESC);

CREATE INDEX IF NOT EXISTS idx_vector_queries_similarity 
ON vector_queries(similarity_score DESC);

CREATE OR REPLACE FUNCTION update_embeddings_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER embeddings_updated_at_trigger
BEFORE UPDATE ON embeddings
FOR EACH ROW
EXECUTE FUNCTION update_embeddings_updated_at();

COMMENT ON TABLE embeddings IS 'Stores vector embeddings with metadata for semantic search';
COMMENT ON TABLE vector_queries IS 'Tracks vector query history and similarity scores';
COMMENT ON COLUMN embeddings.embedding IS 'Vector embedding (1536 dimensions for OpenAI ada-002)';
COMMENT ON COLUMN embeddings.metadata IS 'JSON metadata including source, category, text, etc.';
COMMENT ON INDEX idx_embeddings_vector IS 'IVFFlat index for fast cosine similarity search';
