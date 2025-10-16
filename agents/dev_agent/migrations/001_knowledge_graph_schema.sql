
CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS code_entities (
    id SERIAL PRIMARY KEY,
    session_id UUID,
    entity_type VARCHAR(50) NOT NULL,
    entity_name VARCHAR(255) NOT NULL,
    file_path TEXT NOT NULL,
    line_start INT NOT NULL,
    line_end INT NOT NULL,
    source_code TEXT,
    embedding VECTOR(1536),
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS entity_relationships (
    id SERIAL PRIMARY KEY,
    from_entity_id INT NOT NULL REFERENCES code_entities(id) ON DELETE CASCADE,
    to_entity_id INT NOT NULL REFERENCES code_entities(id) ON DELETE CASCADE,
    relationship_type VARCHAR(50) NOT NULL,
    weight FLOAT DEFAULT 1.0,
    created_at TIMESTAMP DEFAULT NOW(),
    CONSTRAINT unique_relationship UNIQUE(from_entity_id, to_entity_id, relationship_type)
);

CREATE TABLE IF NOT EXISTS learned_patterns (
    id SERIAL PRIMARY KEY,
    pattern_type VARCHAR(50) NOT NULL,
    pattern_name VARCHAR(255) NOT NULL,
    pattern_data JSONB NOT NULL,
    frequency INT DEFAULT 1,
    success_rate FLOAT DEFAULT 0.0,
    last_used TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS bug_fix_history (
    id SERIAL PRIMARY KEY,
    github_issue_id INT,
    issue_title TEXT NOT NULL,
    issue_description TEXT,
    bug_type VARCHAR(100),
    root_cause TEXT,
    fix_strategy TEXT,
    pr_number INT,
    success BOOLEAN DEFAULT false,
    execution_time_seconds INT,
    patterns_used JSONB DEFAULT '[]',
    created_at TIMESTAMP DEFAULT NOW()
);


CREATE INDEX IF NOT EXISTS idx_entities_embedding 
ON code_entities USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);

CREATE INDEX IF NOT EXISTS idx_entities_session 
ON code_entities(session_id);

CREATE INDEX IF NOT EXISTS idx_entities_type_name 
ON code_entities(entity_type, entity_name);

CREATE INDEX IF NOT EXISTS idx_entities_file 
ON code_entities(file_path);

CREATE INDEX IF NOT EXISTS idx_relationships_from 
ON entity_relationships(from_entity_id);

CREATE INDEX IF NOT EXISTS idx_relationships_to 
ON entity_relationships(to_entity_id);

CREATE INDEX IF NOT EXISTS idx_relationships_type 
ON entity_relationships(relationship_type);

CREATE INDEX IF NOT EXISTS idx_patterns_type 
ON learned_patterns(pattern_type);

CREATE INDEX IF NOT EXISTS idx_patterns_frequency 
ON learned_patterns(frequency DESC);

CREATE INDEX IF NOT EXISTS idx_patterns_success 
ON learned_patterns(success_rate DESC) 
WHERE success_rate > 0;

CREATE INDEX IF NOT EXISTS idx_bugfix_issue 
ON bug_fix_history(github_issue_id);

CREATE INDEX IF NOT EXISTS idx_bugfix_type 
ON bug_fix_history(bug_type);

CREATE INDEX IF NOT EXISTS idx_bugfix_success 
ON bug_fix_history(success);

CREATE INDEX IF NOT EXISTS idx_bugfix_created 
ON bug_fix_history(created_at DESC);

CREATE OR REPLACE FUNCTION update_modified_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_code_entities_modtime
    BEFORE UPDATE ON code_entities
    FOR EACH ROW
    EXECUTE FUNCTION update_modified_column();

COMMENT ON TABLE code_entities IS 'Stores code entities (files, functions, classes) with vector embeddings for semantic search';
COMMENT ON TABLE entity_relationships IS 'Stores relationships between code entities (calls, imports, inherits)';
COMMENT ON TABLE learned_patterns IS 'Stores learned patterns for bugs, fixes, and coding styles';
COMMENT ON TABLE bug_fix_history IS 'Tracks bug fix attempts and their outcomes';

COMMENT ON COLUMN code_entities.embedding IS 'OpenAI text-embedding-3-small (1536 dimensions) for semantic search';
COMMENT ON COLUMN entity_relationships.weight IS 'Relationship strength (0.0-1.0)';
COMMENT ON COLUMN learned_patterns.success_rate IS 'Success rate for fix patterns (0.0-1.0)';


ANALYZE code_entities;
ANALYZE entity_relationships;
ANALYZE learned_patterns;
ANALYZE bug_fix_history;
