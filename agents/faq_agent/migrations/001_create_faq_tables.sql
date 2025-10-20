
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

CREATE TABLE IF NOT EXISTS faqs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    question TEXT NOT NULL,
    answer TEXT NOT NULL,
    category VARCHAR(100),
    tags TEXT[],
    embedding VECTOR(1536),  -- OpenAI embedding dimension
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_by VARCHAR(255),
    view_count INTEGER DEFAULT 0,
    helpful_count INTEGER DEFAULT 0,
    not_helpful_count INTEGER DEFAULT 0,
    CONSTRAINT question_not_empty CHECK (char_length(question) > 0),
    CONSTRAINT answer_not_empty CHECK (char_length(answer) > 0)
);

CREATE TABLE IF NOT EXISTS faq_search_history (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    query TEXT NOT NULL,
    query_embedding VECTOR(1536),
    matched_faq_id UUID REFERENCES faqs(id) ON DELETE SET NULL,
    similarity_score FLOAT,
    result_count INTEGER,
    user_feedback VARCHAR(50),
    user_id VARCHAR(255),
    session_id VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    metadata JSONB DEFAULT '{}'
);

CREATE TABLE IF NOT EXISTS faq_categories (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(100) NOT NULL UNIQUE,
    description TEXT,
    parent_category_id UUID REFERENCES faq_categories(id) ON DELETE SET NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    CONSTRAINT category_name_not_empty CHECK (char_length(name) > 0)
);

CREATE INDEX IF NOT EXISTS idx_faqs_category ON faqs(category);
CREATE INDEX IF NOT EXISTS idx_faqs_created_at ON faqs(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_faqs_view_count ON faqs(view_count DESC);
CREATE INDEX IF NOT EXISTS idx_faqs_helpful_count ON faqs(helpful_count DESC);
CREATE INDEX IF NOT EXISTS idx_faqs_tags ON faqs USING GIN(tags);

CREATE INDEX IF NOT EXISTS idx_faqs_embedding ON faqs 
    USING ivfflat (embedding vector_cosine_ops)
    WITH (lists = 100);

CREATE INDEX IF NOT EXISTS idx_search_history_created_at ON faq_search_history(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_search_history_user_id ON faq_search_history(user_id);
CREATE INDEX IF NOT EXISTS idx_search_history_session_id ON faq_search_history(session_id);

CREATE INDEX IF NOT EXISTS idx_faqs_question_fts ON faqs 
    USING GIN(to_tsvector('english', question));
CREATE INDEX IF NOT EXISTS idx_faqs_answer_fts ON faqs 
    USING GIN(to_tsvector('english', answer));

CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_faqs_updated_at
    BEFORE UPDATE ON faqs
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE OR REPLACE FUNCTION match_faqs(
    query_embedding VECTOR(1536),
    match_threshold FLOAT DEFAULT 0.7,
    match_count INT DEFAULT 5,
    filter_category VARCHAR DEFAULT NULL
)
RETURNS TABLE (
    id UUID,
    question TEXT,
    answer TEXT,
    category VARCHAR,
    tags TEXT[],
    metadata JSONB,
    view_count INTEGER,
    helpful_count INTEGER,
    not_helpful_count INTEGER,
    similarity FLOAT
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT
        faqs.id,
        faqs.question,
        faqs.answer,
        faqs.category,
        faqs.tags,
        faqs.metadata,
        faqs.view_count,
        faqs.helpful_count,
        faqs.not_helpful_count,
        1 - (faqs.embedding <=> query_embedding) AS similarity
    FROM faqs
    WHERE 
        (filter_category IS NULL OR faqs.category = filter_category)
        AND (1 - (faqs.embedding <=> query_embedding)) > match_threshold
    ORDER BY faqs.embedding <=> query_embedding
    LIMIT match_count;
END;
$$;

INSERT INTO faq_categories (name, description) VALUES
    ('ops_agent', 'Ops Agent 相關問題')
ON CONFLICT (name) DO NOTHING;

INSERT INTO faq_categories (name, description) VALUES
    ('dev_agent', 'Dev Agent 相關問題')
ON CONFLICT (name) DO NOTHING;

INSERT INTO faq_categories (name, description) VALUES
    ('general', '一般問題')
ON CONFLICT (name) DO NOTHING;

COMMENT ON TABLE faqs IS 'FAQ Agent - FAQ 問答表';
COMMENT ON TABLE faq_search_history IS 'FAQ Agent - 搜索歷史表';
COMMENT ON TABLE faq_categories IS 'FAQ Agent - 分類表';
COMMENT ON FUNCTION match_faqs IS 'FAQ Agent - 向量相似度搜索函數';
