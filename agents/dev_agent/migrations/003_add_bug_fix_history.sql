
CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS bug_fix_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    issue_number INTEGER NOT NULL,
    issue_title TEXT NOT NULL,
    bug_description TEXT,
    bug_type VARCHAR(100),
    affected_files TEXT[],
    root_cause TEXT,
    fix_strategy TEXT,
    fix_code_diff TEXT,
    pr_number INTEGER,
    pr_url TEXT,
    success BOOLEAN DEFAULT FALSE,
    execution_time_seconds INTEGER,
    patterns_used JSONB DEFAULT '[]'::jsonb,
    test_results JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_bug_fix_history_issue ON bug_fix_history(issue_number);
CREATE INDEX IF NOT EXISTS idx_bug_fix_history_success ON bug_fix_history(success);
CREATE INDEX IF NOT EXISTS idx_bug_fix_history_type ON bug_fix_history(bug_type);
CREATE INDEX IF NOT EXISTS idx_bug_fix_history_created ON bug_fix_history(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_bug_fix_history_patterns ON bug_fix_history USING gin(patterns_used);

ALTER TABLE bug_fix_history ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Enable read access for authenticated users" ON bug_fix_history
    FOR SELECT
    USING (auth.role() = 'authenticated' OR auth.role() = 'service_role');

CREATE POLICY "Enable insert for authenticated users" ON bug_fix_history
    FOR INSERT
    WITH CHECK (auth.role() = 'authenticated' OR auth.role() = 'service_role');

CREATE POLICY "Enable update for authenticated users" ON bug_fix_history
    FOR UPDATE
    USING (auth.role() = 'authenticated' OR auth.role() = 'service_role');

CREATE OR REPLACE FUNCTION update_bug_fix_history_modtime()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS update_bug_fix_history_modtime ON bug_fix_history;
CREATE TRIGGER update_bug_fix_history_modtime
    BEFORE UPDATE ON bug_fix_history
    FOR EACH ROW
    EXECUTE FUNCTION update_bug_fix_history_modtime();

COMMENT ON TABLE bug_fix_history IS 'Tracks bug fix workflow attempts and outcomes for pattern learning';
COMMENT ON COLUMN bug_fix_history.issue_number IS 'GitHub issue number';
COMMENT ON COLUMN bug_fix_history.bug_type IS 'Classification of bug type (e.g., type_error, null_pointer, logic_error)';
COMMENT ON COLUMN bug_fix_history.patterns_used IS 'Array of pattern IDs from code_patterns table that were used';
COMMENT ON COLUMN bug_fix_history.success IS 'Whether the fix was successful (tests passed)';
COMMENT ON COLUMN bug_fix_history.test_results IS 'JSON object containing test execution results';
