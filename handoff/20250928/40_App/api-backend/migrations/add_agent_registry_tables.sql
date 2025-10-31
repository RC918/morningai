
CREATE TYPE agent_type_enum AS ENUM ('dev_agent', 'ops_agent', 'pm_agent', 'growth_strategist', 'meta_agent');
CREATE TYPE agent_status_enum AS ENUM ('active', 'idle', 'busy', 'offline', 'error');
CREATE TYPE permission_level_enum AS ENUM ('sandbox_only', 'staging_access', 'prod_low_risk', 'prod_full_access');
CREATE TYPE task_status_enum AS ENUM ('queued', 'assigned', 'running', 'completed', 'failed', 'cancelled');

CREATE TABLE agents (
    agent_id VARCHAR(36) PRIMARY KEY,
    agent_type agent_type_enum NOT NULL,
    status agent_status_enum NOT NULL DEFAULT 'idle',
    permission_level permission_level_enum NOT NULL DEFAULT 'sandbox_only',
    reputation_score INTEGER NOT NULL DEFAULT 500 CHECK (reputation_score >= 0 AND reputation_score <= 999),
    capabilities TEXT NOT NULL DEFAULT '[]',
    metadata TEXT NOT NULL DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    last_activity TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    
    pr_merged_count INTEGER NOT NULL DEFAULT 0 CHECK (pr_merged_count >= 0),
    pr_reverted_count INTEGER NOT NULL DEFAULT 0 CHECK (pr_reverted_count >= 0),
    test_pass_count INTEGER NOT NULL DEFAULT 0 CHECK (test_pass_count >= 0),
    test_fail_count INTEGER NOT NULL DEFAULT 0 CHECK (test_fail_count >= 0),
    test_pass_rate REAL NOT NULL DEFAULT 0.0 CHECK (test_pass_rate >= 0.0 AND test_pass_rate <= 1.0)
);

CREATE TABLE tasks (
    task_id VARCHAR(36) PRIMARY KEY,
    status task_status_enum NOT NULL DEFAULT 'queued',
    agent_id VARCHAR(36) REFERENCES agents(agent_id) ON DELETE SET NULL,
    tenant_id VARCHAR(36),
    task_type VARCHAR(100) NOT NULL,
    payload TEXT NOT NULL DEFAULT '{}',
    result TEXT,
    error_message TEXT,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    assigned_at TIMESTAMP WITH TIME ZONE,
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    cancelled_at TIMESTAMP WITH TIME ZONE,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_agents_type ON agents(agent_type);
CREATE INDEX idx_agents_status ON agents(status);
CREATE INDEX idx_agents_permission_level ON agents(permission_level);
CREATE INDEX idx_agents_reputation_score ON agents(reputation_score);
CREATE INDEX idx_agents_last_activity ON agents(last_activity);

CREATE INDEX idx_tasks_status ON tasks(status);
CREATE INDEX idx_tasks_agent_id ON tasks(agent_id);
CREATE INDEX idx_tasks_tenant_id ON tasks(tenant_id);
CREATE INDEX idx_tasks_task_type ON tasks(task_type);
CREATE INDEX idx_tasks_created_at ON tasks(created_at);
CREATE INDEX idx_tasks_updated_at ON tasks(updated_at);

CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_tasks_updated_at 
    BEFORE UPDATE ON tasks 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

COMMENT ON TABLE agents IS 'Agent Registry - stores registered AI agents and their metadata';
COMMENT ON TABLE tasks IS 'Task Router - stores tasks assigned to agents';
COMMENT ON COLUMN agents.agent_id IS 'Unique UUID identifier for the agent';
COMMENT ON COLUMN agents.reputation_score IS 'Agent reputation score (0-999) affecting permission levels';
COMMENT ON COLUMN agents.capabilities IS 'JSON array of agent capabilities';
COMMENT ON COLUMN agents.metadata IS 'JSON object for additional agent metadata';
COMMENT ON COLUMN tasks.task_id IS 'Unique UUID identifier for the task';
COMMENT ON COLUMN tasks.payload IS 'JSON object containing task parameters';
COMMENT ON COLUMN tasks.result IS 'JSON object containing task execution results';
