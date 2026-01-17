-- Migration 044: Extend agent_type CHECK constraint for Blueprint 3.3 Agent Types
-- Issue: #4121 (EPIC K: Sync VALID_AGENT_TYPES with AgentType enum)
-- Blueprint Reference: Section 3.3 - Agent Catalog V2 (13 Agent Types)
--
-- This migration extends the agent_type CHECK constraint to include all
-- Blueprint 3.3 defined agent types, enabling the reputation system to
-- track new agent categories:
--   - Core Engineering Agents (5): planner, coding, reviewer, test, debugger
--   - UX/UI Agents (4): ui_consistency, ux_heuristic, visual_regression, design_token_governance
--   - Governance/Reasoning Agents (4): judge, debate_left, debate_right, risk_analyzer
--   - Legacy Agents (5): dev_agent, ops_agent, pm_agent, growth_strategist, meta_agent

-- Step 1: Drop the existing CHECK constraint
ALTER TABLE agent_reputation DROP CONSTRAINT IF EXISTS agent_reputation_agent_type_check;

-- Step 2: Add the new CHECK constraint with all Blueprint 3.3 agent types
ALTER TABLE agent_reputation ADD CONSTRAINT agent_reputation_agent_type_check 
    CHECK (agent_type IN (
        -- Core Engineering Agents (Blueprint 3.3)
        'planner',
        'coding', 
        'reviewer',
        'test',
        'debugger',
        -- UX/UI Agents (Blueprint 3.3)
        'ui_consistency',
        'ux_heuristic',
        'visual_regression',
        'design_token_governance',
        -- Governance/Reasoning Agents (Blueprint 3.3)
        'judge',
        'debate_left',
        'debate_right',
        'risk_analyzer',
        -- Legacy Agent Types (backward compatibility)
        'dev_agent',
        'ops_agent',
        'pm_agent',
        'growth_strategist',
        'meta_agent'
    ));

-- Step 3: Add comment documenting the change
COMMENT ON CONSTRAINT agent_reputation_agent_type_check ON agent_reputation IS 
    'Valid agent types as defined in Blueprint Section 3.3 (Agent Catalog V2). Extended in migration 044 to include all 18 Blueprint agent types.';
