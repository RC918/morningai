-- ⚠️ PHASE 1: RLS ENABLEMENT - ASSUMES TENANT_ID EXISTS
--
-- This migration assumes tenant_id columns already exist on:
-- - tenants, users, platform_bindings, external_integrations, memory
--
-- If these tables/columns do not exist, this migration will FAIL.
-- Comment out sections for non-existent tables before applying.
--

ALTER TABLE IF EXISTS tenants ENABLE ROW LEVEL SECURITY;

CREATE POLICY IF NOT EXISTS "service_role_tenants_all" ON tenants
    FOR ALL TO service_role USING (true) WITH CHECK (true);

CREATE POLICY IF NOT EXISTS "users_read_own_tenant" ON tenants
    FOR SELECT TO authenticated
    USING (
        id IN (
            SELECT tenant_id FROM users WHERE id = auth.uid()
        )
    );

ALTER TABLE IF EXISTS users ENABLE ROW LEVEL SECURITY;

CREATE POLICY IF NOT EXISTS "service_role_users_all" ON users
    FOR ALL TO service_role USING (true) WITH CHECK (true);

CREATE POLICY IF NOT EXISTS "users_read_same_tenant" ON users
    FOR SELECT TO authenticated
    USING (
        tenant_id IN (
            SELECT tenant_id FROM users WHERE id = auth.uid()
        )
    );

CREATE POLICY IF NOT EXISTS "users_update_self" ON users
    FOR UPDATE TO authenticated
    USING (id = auth.uid())
    WITH CHECK (id = auth.uid());

ALTER TABLE IF EXISTS platform_bindings ENABLE ROW LEVEL SECURITY;

CREATE POLICY IF NOT EXISTS "service_role_platform_bindings_all" ON platform_bindings
    FOR ALL TO service_role USING (true) WITH CHECK (true);

CREATE POLICY IF NOT EXISTS "users_read_own_tenant_bindings" ON platform_bindings
    FOR SELECT TO authenticated
    USING (
        tenant_id IN (
            SELECT tenant_id FROM users WHERE id = auth.uid()
        )
    );

CREATE POLICY IF NOT EXISTS "admins_manage_tenant_bindings" ON platform_bindings
    FOR ALL TO authenticated
    USING (
        tenant_id IN (
            SELECT u.tenant_id FROM users u
            WHERE u.id = auth.uid() AND u.role = 'admin'
        )
    )
    WITH CHECK (
        tenant_id IN (
            SELECT u.tenant_id FROM users u
            WHERE u.id = auth.uid() AND u.role = 'admin'
        )
    );

ALTER TABLE IF EXISTS external_integrations ENABLE ROW LEVEL SECURITY;

CREATE POLICY IF NOT EXISTS "service_role_integrations_all" ON external_integrations
    FOR ALL TO service_role USING (true) WITH CHECK (true);

CREATE POLICY IF NOT EXISTS "users_read_own_tenant_integrations" ON external_integrations
    FOR SELECT TO authenticated
    USING (
        tenant_id IN (
            SELECT tenant_id FROM users WHERE id = auth.uid()
        )
    );

CREATE POLICY IF NOT EXISTS "admins_manage_integrations" ON external_integrations
    FOR ALL TO authenticated
    USING (
        tenant_id IN (
            SELECT u.tenant_id FROM users u
            WHERE u.id = auth.uid() AND u.role = 'admin'
        )
    )
    WITH CHECK (
        tenant_id IN (
            SELECT u.tenant_id FROM users u
            WHERE u.id = auth.uid() AND u.role = 'admin'
        )
    );

ALTER TABLE IF EXISTS memory ENABLE ROW LEVEL SECURITY;

CREATE POLICY IF NOT EXISTS "service_role_memory_all" ON memory
    FOR ALL TO service_role USING (true) WITH CHECK (true);



CREATE OR REPLACE FUNCTION is_tenant_admin()
RETURNS BOOLEAN AS $$
BEGIN
    RETURN EXISTS (
        SELECT 1 FROM users
        WHERE id = auth.uid()
        AND role IN ('admin', 'owner')
    );
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

CREATE OR REPLACE FUNCTION current_user_tenant_id()
RETURNS UUID AS $$
BEGIN
    RETURN (
        SELECT tenant_id FROM users WHERE id = auth.uid()
    );
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;


CREATE TABLE IF NOT EXISTS rls_audit_log (
    id BIGSERIAL PRIMARY KEY,
    user_id UUID,
    table_name TEXT,
    operation TEXT,
    attempted_at TIMESTAMPTZ DEFAULT NOW(),
    denied_reason TEXT,
    metadata JSONB
);

ALTER TABLE rls_audit_log ENABLE ROW LEVEL SECURITY;

CREATE POLICY "service_admins_read_audit" ON rls_audit_log
    FOR SELECT TO authenticated
    USING (
        auth.uid() IN (SELECT id FROM users WHERE role = 'admin')
        OR auth.role() = 'service_role'
    );

CREATE INDEX IF NOT EXISTS idx_users_tenant_id ON users(tenant_id);
CREATE INDEX IF NOT EXISTS idx_users_id_tenant ON users(id, tenant_id);
CREATE INDEX IF NOT EXISTS idx_platform_bindings_tenant ON platform_bindings(tenant_id);
CREATE INDEX IF NOT EXISTS idx_external_integrations_tenant ON external_integrations(tenant_id);

COMMENT ON POLICY "service_role_tenants_all" ON tenants IS 
    'Service role has full access for backend operations';
COMMENT ON POLICY "users_read_own_tenant" ON tenants IS 
    'Users can only read data from their own tenant';
COMMENT ON FUNCTION is_tenant_admin() IS 
    'Helper function to check if current user is a tenant administrator';
COMMENT ON FUNCTION current_user_tenant_id() IS 
    'Helper function to get current user tenant ID for RLS policies';
COMMENT ON TABLE rls_audit_log IS 
    'Audit log for tracking RLS policy violations and access attempts';
