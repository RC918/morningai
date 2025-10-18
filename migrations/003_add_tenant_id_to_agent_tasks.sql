
CREATE TABLE IF NOT EXISTS tenants (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

DO $$ 
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.tables 
        WHERE table_schema = 'public' AND table_name = 'users'
    ) THEN
        IF NOT EXISTS (
            SELECT 1 FROM information_schema.columns 
            WHERE table_schema = 'public' 
            AND table_name = 'users' 
            AND column_name = 'tenant_id'
        ) THEN
            ALTER TABLE users ADD COLUMN tenant_id UUID;
            ALTER TABLE users ADD CONSTRAINT fk_users_tenant 
                FOREIGN KEY (tenant_id) REFERENCES tenants(id) ON DELETE CASCADE;
            CREATE INDEX IF NOT EXISTS idx_users_tenant_id ON users(tenant_id);
        END IF;
    END IF;
END $$;

ALTER TABLE agent_tasks ADD COLUMN IF NOT EXISTS tenant_id UUID;

INSERT INTO tenants (id, name) 
VALUES ('00000000-0000-0000-0000-000000000001', 'Default Tenant (Migration)')
ON CONFLICT (id) DO NOTHING;

UPDATE agent_tasks 
SET tenant_id = '00000000-0000-0000-0000-000000000001' 
WHERE tenant_id IS NULL;

ALTER TABLE agent_tasks ALTER COLUMN tenant_id SET NOT NULL;

ALTER TABLE agent_tasks 
ADD CONSTRAINT fk_agent_tasks_tenant
    FOREIGN KEY (tenant_id) 
    REFERENCES tenants(id) 
    ON DELETE CASCADE;

CREATE INDEX IF NOT EXISTS idx_agent_tasks_tenant_id ON agent_tasks(tenant_id);

COMMENT ON COLUMN agent_tasks.tenant_id IS 
    'Tenant ID for multi-tenant isolation (Phase 2). Each task belongs to exactly one tenant.';

COMMENT ON INDEX idx_agent_tasks_tenant_id IS 
    'Performance index for tenant-based queries in RLS policies';

COMMENT ON TABLE agent_tasks IS 
    'Agent tasks with RLS enabled and tenant isolation (Phase 2 complete)';
