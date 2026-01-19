-- Migration 045: Extend agenttypedb PostgreSQL enum for Blueprint 3.3 Agent Types
-- Issue: Sync api-backend AgentTypeDB with orchestrator AgentType enum
-- Blueprint Reference: Section 3.3 - Agent Catalog V2 (13 Agent Types)
--
-- This migration extends the PostgreSQL 'agenttypedb' enum used by the 'agents' table
-- to include all Blueprint 3.3 defined agent types. This aligns the api-backend
-- database schema with the orchestrator's AgentType enum in principal_context.py.
--
-- New agent types being added:
--   - Core Engineering Agents (5): planner, coding, reviewer, test, debugger
--   - UX/UI Agents (4): ui_consistency, ux_heuristic, visual_regression, design_token_governance
--   - Governance/Reasoning Agents (4): judge, debate_left, debate_right, risk_analyzer
--
-- Existing types preserved (backward compatibility):
--   - dev_agent, ops_agent, pm_agent, growth_strategist, meta_agent

-- Step 1: Add new enum values to agenttypedb
-- Note: PostgreSQL requires adding enum values one at a time with ALTER TYPE

-- Core Engineering Agents
ALTER TYPE agenttypedb ADD VALUE IF NOT EXISTS 'planner';
ALTER TYPE agenttypedb ADD VALUE IF NOT EXISTS 'coding';
ALTER TYPE agenttypedb ADD VALUE IF NOT EXISTS 'reviewer';
ALTER TYPE agenttypedb ADD VALUE IF NOT EXISTS 'test';
ALTER TYPE agenttypedb ADD VALUE IF NOT EXISTS 'debugger';

-- UX/UI Agents
ALTER TYPE agenttypedb ADD VALUE IF NOT EXISTS 'ui_consistency';
ALTER TYPE agenttypedb ADD VALUE IF NOT EXISTS 'ux_heuristic';
ALTER TYPE agenttypedb ADD VALUE IF NOT EXISTS 'visual_regression';
ALTER TYPE agenttypedb ADD VALUE IF NOT EXISTS 'design_token_governance';

-- Governance/Reasoning Agents
ALTER TYPE agenttypedb ADD VALUE IF NOT EXISTS 'judge';
ALTER TYPE agenttypedb ADD VALUE IF NOT EXISTS 'debate_left';
ALTER TYPE agenttypedb ADD VALUE IF NOT EXISTS 'debate_right';
ALTER TYPE agenttypedb ADD VALUE IF NOT EXISTS 'risk_analyzer';

-- Step 2: Add comment documenting the change
COMMENT ON TYPE agenttypedb IS 
    'Agent types as defined in Blueprint Section 3.3 (Agent Catalog V2). Extended in migration 045 to include all 18 Blueprint agent types. Synced with orchestrator/governance/principal_context.py::AgentType.';
