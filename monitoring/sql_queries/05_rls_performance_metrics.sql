
SELECT
    DATE_TRUNC('hour', created_at) as hour,
    COUNT(*) as tasks_created,
    COUNT(DISTINCT tenant_id) as active_tenants,
    COUNT(DISTINCT status) as distinct_statuses
FROM agent_tasks
WHERE created_at >= NOW() - INTERVAL '24 hours'
GROUP BY DATE_TRUNC('hour', created_at)
ORDER BY hour DESC
LIMIT 24;

SELECT
    status,
    COUNT(*) as count,
    ROUND(100.0 * COUNT(*) / (SELECT COUNT(*) FROM agent_tasks), 2) as percentage,
    MIN(created_at) as oldest,
    MAX(created_at) as newest
FROM agent_tasks
GROUP BY status
ORDER BY count DESC;

SELECT
    t.id as tenant_id,
    t.name as tenant_name,
    COUNT(at.task_id) as total_tasks,
    COUNT(at.task_id) FILTER (WHERE at.created_at >= NOW() - INTERVAL '24 hours') as tasks_last_24h,
    COUNT(at.task_id) FILTER (WHERE at.status = 'queued') as queued,
    COUNT(at.task_id) FILTER (WHERE at.status = 'running') as running,
    COUNT(at.task_id) FILTER (WHERE at.status = 'done') as done,
    COUNT(at.task_id) FILTER (WHERE at.status = 'error') as error
FROM tenants t
LEFT JOIN agent_tasks at ON at.tenant_id = t.id
GROUP BY t.id, t.name
ORDER BY total_tasks DESC
LIMIT 10;

SELECT
    task_id,
    tenant_id,
    status,
    question,
    created_at,
    started_at,
    EXTRACT(EPOCH FROM (NOW() - started_at))/3600 as hours_running,
    '🟡 WARNING: Long-running task' as alert
FROM agent_tasks
WHERE status = 'running'
  AND started_at < NOW() - INTERVAL '1 hour'
ORDER BY started_at
LIMIT 10;
