
SELECT
    policyname,
    cmd as operation,
    roles,
    CASE 
        WHEN qual::text LIKE '%tenant_id%' THEN '✅ Tenant-aware'
        WHEN qual::text = 'true' THEN '🔴 CRITICAL: USING(true) - NO ISOLATION'
        ELSE '🟡 WARNING: Unknown policy logic'
    END as isolation_status,
    LEFT(qual::text, 100) as policy_logic_preview
FROM pg_policies
WHERE tablename = 'agent_tasks'
  AND policyname NOT IN ('service_role_all_access', 'anon_no_access')
ORDER BY policyname;

SELECT
    CASE 
        WHEN COUNT(*) FILTER (WHERE qual::text = 'true' AND policyname LIKE 'users_%') > 0 
        THEN '🔴 CRITICAL: Phase 1 policies still active (USING true)'
        WHEN COUNT(*) FILTER (WHERE qual::text LIKE '%tenant_id%') >= 3
        THEN '✅ OK: Phase 2 tenant isolation active'
        ELSE '🟡 WARNING: Unexpected policy configuration'
    END as phase_status,
    COUNT(*) FILTER (WHERE qual::text = 'true' AND policyname LIKE 'users_%') as phase1_policies,
    COUNT(*) FILTER (WHERE qual::text LIKE '%tenant_id%') as phase2_policies
FROM pg_policies
WHERE tablename = 'agent_tasks';
