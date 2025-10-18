
DROP POLICY IF EXISTS "users_read_own_tenant" ON agent_tasks;
DROP POLICY IF EXISTS "users_insert_own_tenant" ON agent_tasks;
DROP POLICY IF EXISTS "users_update_own_tenant" ON agent_tasks;
DROP POLICY IF EXISTS "users_delete_own_tenant" ON agent_tasks;
DROP POLICY IF EXISTS "authenticated_users_can_read" ON agent_tasks;
DROP POLICY IF EXISTS "authenticated_users_can_insert" ON agent_tasks;
DROP POLICY IF EXISTS "authenticated_users_can_update" ON agent_tasks;
DROP POLICY IF EXISTS "authenticated_users_can_delete" ON agent_tasks;


CREATE POLICY "tenant_read_policy" ON agent_tasks
    FOR SELECT
    TO authenticated
    USING (true);  -- Allow all reads for now, to be restricted later

CREATE POLICY "tenant_insert_policy" ON agent_tasks
    FOR INSERT
    TO authenticated
    WITH CHECK (tenant_id = '00000000-0000-0000-0000-000000000001');  -- Only allow insert to default tenant

CREATE POLICY "tenant_update_policy" ON agent_tasks
    FOR UPDATE
    TO authenticated
    USING (true)  -- Allow updates for now
    WITH CHECK (tenant_id IS NOT NULL);  -- Ensure tenant_id is never set to NULL

CREATE POLICY "tenant_delete_policy" ON agent_tasks
    FOR DELETE
    TO authenticated
    USING (true);  -- Allow deletes for now

COMMENT ON POLICY "tenant_read_policy" ON agent_tasks IS 
    'Temporary policy: Allows authenticated users to read all tasks. Will be restricted when users table is created.';

COMMENT ON POLICY "tenant_insert_policy" ON agent_tasks IS 
    'Enforces that new tasks must be created in default tenant until users table with tenant_id is available.';

COMMENT ON POLICY "tenant_update_policy" ON agent_tasks IS 
    'Temporary policy: Allows authenticated users to update tasks. Ensures tenant_id remains non-null.';

COMMENT ON POLICY "tenant_delete_policy" ON agent_tasks IS 
    'Temporary policy: Allows authenticated users to delete tasks. Will be restricted when users table is created.';

COMMENT ON TABLE agent_tasks IS 
    'RLS enabled with tenant_id column (Phase 2). Awaiting users table for full tenant isolation.';
