
CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS code_embeddings (
    id SERIAL PRIMARY KEY,
    file_path TEXT NOT NULL,
    file_hash TEXT NOT NULL,
    content_preview TEXT,
    embedding vector(1536),
    language TEXT,
    tokens_count INTEGER,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    metadata JSONB DEFAULT '{}'::jsonb,
    UNIQUE(file_path, file_hash)
);

CREATE INDEX IF NOT EXISTS code_embeddings_embedding_idx 
    ON code_embeddings 
    USING hnsw (embedding vector_cosine_ops)
    WITH (m = 16, ef_construction = 64);

CREATE INDEX IF NOT EXISTS code_embeddings_file_path_idx 
    ON code_embeddings(file_path);

CREATE INDEX IF NOT EXISTS code_embeddings_file_hash_idx 
    ON code_embeddings(file_hash);

CREATE INDEX IF NOT EXISTS code_embeddings_language_idx 
    ON code_embeddings(language);

CREATE INDEX IF NOT EXISTS code_embeddings_created_at_idx 
    ON code_embeddings(created_at DESC);


CREATE TABLE IF NOT EXISTS code_patterns (
    id SERIAL PRIMARY KEY,
    pattern_name TEXT NOT NULL,
    pattern_type TEXT NOT NULL,
    pattern_template TEXT NOT NULL,
    language TEXT NOT NULL,
    frequency INTEGER DEFAULT 1,
    confidence_score FLOAT DEFAULT 0.0,
    examples JSONB DEFAULT '[]'::jsonb,
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(pattern_name, language)
);

CREATE INDEX IF NOT EXISTS code_patterns_pattern_name_idx 
    ON code_patterns(pattern_name);

CREATE INDEX IF NOT EXISTS code_patterns_pattern_type_idx 
    ON code_patterns(pattern_type);

CREATE INDEX IF NOT EXISTS code_patterns_language_idx 
    ON code_patterns(language);

CREATE INDEX IF NOT EXISTS code_patterns_frequency_idx 
    ON code_patterns(frequency DESC);

CREATE INDEX IF NOT EXISTS code_patterns_confidence_idx 
    ON code_patterns(confidence_score DESC);


CREATE TABLE IF NOT EXISTS code_relationships (
    id SERIAL PRIMARY KEY,
    source_file TEXT NOT NULL,
    target_file TEXT NOT NULL,
    relationship_type TEXT NOT NULL,
    source_entity TEXT,
    target_entity TEXT,
    strength FLOAT DEFAULT 1.0,
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS code_relationships_source_file_idx 
    ON code_relationships(source_file);

CREATE INDEX IF NOT EXISTS code_relationships_target_file_idx 
    ON code_relationships(target_file);

CREATE INDEX IF NOT EXISTS code_relationships_type_idx 
    ON code_relationships(relationship_type);

CREATE INDEX IF NOT EXISTS code_relationships_strength_idx 
    ON code_relationships(strength DESC);

CREATE INDEX IF NOT EXISTS code_relationships_source_target_idx 
    ON code_relationships(source_file, target_file);


CREATE TABLE IF NOT EXISTS embedding_cache_stats (
    id SERIAL PRIMARY KEY,
    date DATE NOT NULL DEFAULT CURRENT_DATE,
    api_calls_count INTEGER DEFAULT 0,
    cache_hits_count INTEGER DEFAULT 0,
    cache_miss_count INTEGER DEFAULT 0,
    tokens_used INTEGER DEFAULT 0,
    estimated_cost FLOAT DEFAULT 0.0,
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(date)
);

CREATE INDEX IF NOT EXISTS embedding_cache_stats_date_idx 
    ON embedding_cache_stats(date DESC);


CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_code_embeddings_updated_at
    BEFORE UPDATE ON code_embeddings
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_code_patterns_updated_at
    BEFORE UPDATE ON code_patterns
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_code_relationships_updated_at
    BEFORE UPDATE ON code_relationships
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_embedding_cache_stats_updated_at
    BEFORE UPDATE ON embedding_cache_stats
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();


COMMENT ON TABLE code_embeddings IS 'Vector embeddings of code files for semantic search';
COMMENT ON TABLE code_patterns IS 'Learned code patterns and templates';
COMMENT ON TABLE code_relationships IS 'Relationships between code entities (imports, calls, inheritance)';
COMMENT ON TABLE embedding_cache_stats IS 'OpenAI API usage and cache performance metrics';

COMMENT ON COLUMN code_embeddings.embedding IS 'OpenAI text-embedding-3-small vector (1536 dimensions)';
COMMENT ON COLUMN code_embeddings.file_hash IS 'SHA256 hash of file content to detect changes';
COMMENT ON COLUMN code_patterns.confidence_score IS 'Confidence score (0.0-1.0) for pattern validity';
COMMENT ON COLUMN code_relationships.strength IS 'Relationship strength (0.0-1.0)';
