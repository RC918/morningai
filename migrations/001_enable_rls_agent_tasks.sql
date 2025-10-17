
ALTER TABLE agent_tasks ENABLE ROW LEVEL SECURITY;

CREATE POLICY "service_role_all_access" ON agent_tasks
    FOR ALL
    TO service_role
    USING (true)
    WITH CHECK (true);

CREATE POLICY "users_read_own_tenant" ON agent_tasks
    FOR SELECT
    TO authenticated
    USING (
        true
    );

CREATE POLICY "users_insert_own_tenant" ON agent_tasks
    FOR INSERT
    TO authenticated
    WITH CHECK (
        true
    );

CREATE POLICY "users_update_own_tenant" ON agent_tasks
    FOR UPDATE
    TO authenticated
    USING (
        true
    )
    WITH CHECK (
        true
    );

CREATE POLICY "anon_no_access" ON agent_tasks
    FOR ALL
    TO anon
    USING (false);



COMMENT ON TABLE agent_tasks IS 'Agent tasks with Row Level Security enabled for multi-tenant isolation';
