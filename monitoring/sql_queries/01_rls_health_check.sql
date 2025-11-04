
SELECT
    t.tablename,
    t.rowsecurity as rls_enabled,
    (SELECT COUNT(*) FROM pg_policies WHERE tablename = t.tablename) as policy_count,
    CASE 
        WHEN t.rowsecurity = false THEN '🔴 CRITICAL: RLS DISABLED'
        WHEN (SELECT COUNT(*) FROM pg_policies WHERE tablename = t.tablename) = 0 THEN '🔴 CRITICAL: NO POLICIES'
        ELSE '✅ OK'
    END as status
FROM pg_tables t
WHERE t.schemaname = 'public'
  AND t.tablename IN ('agent_tasks', 'tenants', 'users', 'platform_bindings', 'external_integrations')
ORDER BY t.tablename;
