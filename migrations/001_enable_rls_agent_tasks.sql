-- ⚠️ PHASE 1: RLS ENABLEMENT ONLY - NO TENANT ISOLATION YET
--
-- This migration enables RLS on agent_tasks but DOES NOT provide true tenant isolation.
-- All authenticated users can still see ALL data from ALL tenants.
--
-- Phase 2 (separate migration) will add tenant_id column and implement true isolation.
--

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
        true  -- WARNING: Allows access to ALL tenants' data
    );

CREATE POLICY "users_insert_own_tenant" ON agent_tasks
    FOR INSERT
    TO authenticated
    WITH CHECK (
        true  -- WARNING: Allows inserting into ANY tenant
    );

CREATE POLICY "users_update_own_tenant" ON agent_tasks
    FOR UPDATE
    TO authenticated
    USING (
        true  -- WARNING: Allows updating ANY tenant's data
    )
    WITH CHECK (
        true
    );

CREATE POLICY "anon_no_access" ON agent_tasks
    FOR ALL
    TO anon
    USING (false);



COMMENT ON TABLE agent_tasks IS 'RLS enabled (Phase 1) - tenant isolation NOT yet implemented';
