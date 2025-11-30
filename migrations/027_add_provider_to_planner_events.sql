-- Migration 027: Add provider column to planner_events table
--
-- This column tracks which LLM provider was used for plan generation,
-- enabling A/B testing analysis between OpenAI and Gemini providers.
--
-- Related: Phase 6 PR-4 (planner_events.provider field)

-- Add provider column (nullable to support existing records)
ALTER TABLE planner_events
ADD COLUMN IF NOT EXISTS provider VARCHAR(50);

-- Add index for provider-based queries (A/B testing analysis)
CREATE INDEX IF NOT EXISTS idx_planner_events_provider
    ON planner_events(provider);

-- Composite index for provider + timestamp queries
CREATE INDEX IF NOT EXISTS idx_planner_events_provider_timestamp
    ON planner_events(provider, timestamp DESC);

-- Comments for documentation
COMMENT ON COLUMN planner_events.provider IS
    'LLM provider used for plan generation (e.g., "openai", "gemini"). NULL for static plans or legacy records.';

COMMENT ON INDEX idx_planner_events_provider IS
    'Performance index for provider-based filtering (A/B testing analysis)';

COMMENT ON INDEX idx_planner_events_provider_timestamp IS
    'Composite index for provider-filtered time-range queries';
