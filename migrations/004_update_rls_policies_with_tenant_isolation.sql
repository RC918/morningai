--
--
--
--

DROP POLICY IF EXISTS "users_read_own_tenant" ON agent_tasks;
DROP POLICY IF EXISTS "users_insert_own_tenant" ON agent_tasks;
DROP POLICY IF EXISTS "users_update_own_tenant" ON agent_tasks;
DROP POLICY IF EXISTS "users_delete_own_tenant" ON agent_tasks;



CREATE POLICY "users_read_own_tenant" ON agent_tasks
    FOR SELECT
    TO authenticated
    USING (
        tenant_id = (
            SELECT tenant_id 
            FROM users 
            WHERE id = auth.uid()
        )
    );

CREATE POLICY "users_insert_own_tenant" ON agent_tasks
    FOR INSERT
    TO authenticated
    WITH CHECK (
        tenant_id = (
            SELECT tenant_id 
            FROM users 
            WHERE id = auth.uid()
        )
    );

CREATE POLICY "users_update_own_tenant" ON agent_tasks
    FOR UPDATE
    TO authenticated
    USING (
        tenant_id = (
            SELECT tenant_id 
            FROM users 
            WHERE id = auth.uid()
        )
    )
    WITH CHECK (
        tenant_id = (
            SELECT tenant_id 
            FROM users 
            WHERE id = auth.uid()
        )
    );

CREATE POLICY "users_delete_own_tenant" ON agent_tasks
    FOR DELETE
    TO authenticated
    USING (
        tenant_id = (
            SELECT tenant_id 
            FROM users 
            WHERE id = auth.uid()
        )
    );

COMMENT ON POLICY "users_read_own_tenant" ON agent_tasks IS 
    'Phase 2: Users can only read tasks from their own tenant. Uses auth.uid() to lookup tenant_id.';

COMMENT ON POLICY "users_insert_own_tenant" ON agent_tasks IS 
    'Phase 2: Users can only insert tasks into their own tenant. Enforces tenant isolation on INSERT.';

COMMENT ON POLICY "users_update_own_tenant" ON agent_tasks IS 
    'Phase 2: Users can only update tasks from their own tenant. Both USING and WITH CHECK enforce isolation.';

COMMENT ON POLICY "users_delete_own_tenant" ON agent_tasks IS 
    'Phase 2: Users can only delete tasks from their own tenant. Prevents cross-tenant deletion.';

COMMENT ON TABLE agent_tasks IS 
    'RLS enabled with TRUE tenant isolation (Phase 2 complete). Users can only access their own tenant data.';

--
