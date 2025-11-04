
SELECT
    COUNT(*) as total_users,
    COUNT(tenant_id) as users_with_tenant,
    COUNT(*) - COUNT(tenant_id) as null_tenant_users,
    ROUND(100.0 * COUNT(tenant_id) / NULLIF(COUNT(*), 0), 2) as tenant_coverage_percent,
    CASE 
        WHEN COUNT(*) - COUNT(tenant_id) > 0 THEN '🔴 CRITICAL: Users without tenant_id (will be locked out)'
        WHEN COUNT(*) = 0 THEN '🟡 WARNING: No users in database'
        ELSE '✅ OK'
    END as status
FROM users;

SELECT
    id,
    email,
    created_at,
    '⚠️ NEEDS IMMEDIATE FIX' as action_required
FROM users
WHERE tenant_id IS NULL
LIMIT 10;

SELECT
    t.id as tenant_id,
    t.name as tenant_name,
    COUNT(u.id) as user_count,
    ROUND(100.0 * COUNT(u.id) / (SELECT COUNT(*) FROM users), 2) as percentage
FROM tenants t
LEFT JOIN users u ON u.tenant_id = t.id
GROUP BY t.id, t.name
ORDER BY user_count DESC
LIMIT 10;
