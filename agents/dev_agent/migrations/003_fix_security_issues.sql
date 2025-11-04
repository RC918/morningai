-- Fix Security Issues Detected by Supabase Security Advisor
-- Date: 2025-10-17
-- Issues: 
--   1. RLS not enabled on agent_tasks table
--   2. Fix update_updated_at_column() function search_path
--   3. Ensure all RLS policies are properly applied

-- ========================================
-- 1. Enable RLS on agent_tasks table
-- ========================================
ALTER TABLE IF EXISTS agent_tasks ENABLE ROW LEVEL SECURITY;

-- Add RLS policies for agent_tasks
DO $$
BEGIN
    -- Service role full access
    IF NOT EXISTS (
        SELECT 1 FROM pg_policies 
        WHERE tablename = 'agent_tasks' 
        AND policyname = 'Service role has full access to agent_tasks'
    ) THEN
        CREATE POLICY "Service role has full access to agent_tasks"
        ON agent_tasks
        FOR ALL
        TO service_role
        USING (true)
        WITH CHECK (true);
    END IF;

    -- Authenticated users read access
    IF NOT EXISTS (
        SELECT 1 FROM pg_policies 
        WHERE tablename = 'agent_tasks' 
        AND policyname = 'Authenticated users can read agent_tasks'
    ) THEN
        CREATE POLICY "Authenticated users can read agent_tasks"
        ON agent_tasks
        FOR SELECT
        TO authenticated
        USING (true);
    END IF;

    -- Authenticated users insert access
    IF NOT EXISTS (
        SELECT 1 FROM pg_policies 
        WHERE tablename = 'agent_tasks' 
        AND policyname = 'Authenticated users can insert agent_tasks'
    ) THEN
        CREATE POLICY "Authenticated users can insert agent_tasks"
        ON agent_tasks
        FOR INSERT
        TO authenticated
        WITH CHECK (true);
    END IF;

    -- Authenticated users update access
    IF NOT EXISTS (
        SELECT 1 FROM pg_policies 
        WHERE tablename = 'agent_tasks' 
        AND policyname = 'Authenticated users can update agent_tasks'
    ) THEN
        CREATE POLICY "Authenticated users can update agent_tasks"
        ON agent_tasks
        FOR UPDATE
        TO authenticated
        USING (true)
        WITH CHECK (true);
    END IF;

    -- Authenticated users delete access
    IF NOT EXISTS (
        SELECT 1 FROM pg_policies 
        WHERE tablename = 'agent_tasks' 
        AND policyname = 'Authenticated users can delete agent_tasks'
    ) THEN
        CREATE POLICY "Authenticated users can delete agent_tasks"
        ON agent_tasks
        FOR DELETE
        TO authenticated
        USING (true);
    END IF;
END
$$;

-- ========================================
-- 2. Fix update_updated_at_column() search_path
-- ========================================
-- Recreate function with SECURITY DEFINER and explicit search_path
DROP FUNCTION IF EXISTS update_updated_at_column() CASCADE;

CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER 
SECURITY DEFINER
SET search_path = public, pg_temp
AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Recreate all triggers that use this function
-- code_embeddings
DROP TRIGGER IF EXISTS update_code_embeddings_updated_at ON code_embeddings;
CREATE TRIGGER update_code_embeddings_updated_at
    BEFORE UPDATE ON code_embeddings
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- code_patterns
DROP TRIGGER IF EXISTS update_code_patterns_updated_at ON code_patterns;
CREATE TRIGGER update_code_patterns_updated_at
    BEFORE UPDATE ON code_patterns
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- code_relationships
DROP TRIGGER IF EXISTS update_code_relationships_updated_at ON code_relationships;
CREATE TRIGGER update_code_relationships_updated_at
    BEFORE UPDATE ON code_relationships
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- embedding_cache_stats
DROP TRIGGER IF EXISTS update_embedding_cache_stats_updated_at ON embedding_cache_stats;
CREATE TRIGGER update_embedding_cache_stats_updated_at
    BEFORE UPDATE ON embedding_cache_stats
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- agent_tasks (if exists)
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'agent_tasks' 
        AND column_name = 'updated_at'
    ) THEN
        EXECUTE 'DROP TRIGGER IF EXISTS update_agent_tasks_updated_at ON agent_tasks';
        EXECUTE 'CREATE TRIGGER update_agent_tasks_updated_at
            BEFORE UPDATE ON agent_tasks
            FOR EACH ROW
            EXECUTE FUNCTION update_updated_at_column()';
    END IF;
END
$$;

-- ========================================
-- 3. Re-verify RLS is enabled on all tables
-- ========================================
ALTER TABLE code_embeddings ENABLE ROW LEVEL SECURITY;
ALTER TABLE code_patterns ENABLE ROW LEVEL SECURITY;
ALTER TABLE code_relationships ENABLE ROW LEVEL SECURITY;
ALTER TABLE embedding_cache_stats ENABLE ROW LEVEL SECURITY;

-- ========================================
-- Comments
-- ========================================
COMMENT ON FUNCTION update_updated_at_column() IS 'Automatically updates the updated_at column. Uses SECURITY DEFINER with explicit search_path for security.';
COMMENT ON POLICY "Service role has full access to agent_tasks" ON agent_tasks IS 'Service role (application backend) has unrestricted access';

-- Done
SELECT 'Security fixes applied successfully!' AS status;
