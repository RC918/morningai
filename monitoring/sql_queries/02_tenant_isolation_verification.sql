
SELECT
    COUNT(*) as total_tasks,
    COUNT(tenant_id) as tasks_with_tenant,
    COUNT(*) - COUNT(tenant_id) as null_tenant_count,
    ROUND(100.0 * COUNT(tenant_id) / NULLIF(COUNT(*), 0), 2) as tenant_coverage_percent,
    CASE 
        WHEN COUNT(*) - COUNT(tenant_id) > 0 THEN '🔴 CRITICAL: NULL tenant_id found'
        WHEN COUNT(*) = 0 THEN '🟡 WARNING: No tasks in database'
        ELSE '✅ OK'
    END as status
FROM agent_tasks;

SELECT
    tenant_id,
    COUNT(*) as task_count,
    ROUND(100.0 * COUNT(*) / (SELECT COUNT(*) FROM agent_tasks), 2) as percentage
FROM agent_tasks
GROUP BY tenant_id
ORDER BY task_count DESC
LIMIT 10;
