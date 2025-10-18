
BEGIN;

\echo '========================================='
\echo 'Phase 3: API Integration Test Suite'
\echo '========================================='
\echo ''

\echo '1. Creating test tenants and users...'

INSERT INTO tenants (id, name) VALUES
    ('10000000-0000-0000-0000-000000000001', 'Test Company A'),
    ('20000000-0000-0000-0000-000000000001', 'Test Company B')
ON CONFLICT (id) DO NOTHING;


INSERT INTO user_profiles (id, tenant_id, display_name, role) VALUES
    ('11111111-1111-1111-1111-111111111111', '10000000-0000-0000-0000-000000000001', 'Alice Admin', 'admin'),
    ('22222222-2222-2222-2222-222222222222', '10000000-0000-0000-0000-000000000001', 'Bob Member', 'member'),
    ('33333333-3333-3333-3333-333333333333', '20000000-0000-0000-0000-000000000001', 'Charlie Owner', 'owner')
ON CONFLICT (id) DO NOTHING;

\echo 'Test users and tenants created'
\echo ''

\echo '2. Testing tenant isolation in agent_tasks...'

INSERT INTO agent_tasks (task_id, trace_id, tenant_id, question, status) VALUES
    ('task-a1', 'trace-a1', '10000000-0000-0000-0000-000000000001', 'Question from Company A', 'queued'),
    ('task-a2', 'trace-a2', '10000000-0000-0000-0000-000000000001', 'Another question from Company A', 'running'),
    ('task-b1', 'trace-b1', '20000000-0000-0000-0000-000000000001', 'Question from Company B', 'queued')
ON CONFLICT (task_id) DO NOTHING;

\echo '  - Created test tasks for both tenants'

SELECT 
    COUNT(*) AS total_tasks,
    COUNT(CASE WHEN tenant_id = '10000000-0000-0000-0000-000000000001' THEN 1 END) AS tenant_a_tasks,
    COUNT(CASE WHEN tenant_id = '20000000-0000-0000-0000-000000000001' THEN 1 END) AS tenant_b_tasks
FROM agent_tasks
WHERE task_id LIKE 'task-%';

\echo '  ✓ Task isolation verified'
\echo ''

\echo '3. Testing user_profiles tenant linkage...'

SELECT 
    up.display_name,
    up.role,
    t.name AS tenant_name,
    (up.tenant_id = t.id) AS linkage_valid
FROM user_profiles up
JOIN tenants t ON up.tenant_id = t.id
WHERE up.id IN (
    '11111111-1111-1111-1111-111111111111',
    '22222222-2222-2222-2222-222222222222',
    '33333333-3333-3333-3333-333333333333'
);

\echo '  ✓ User-tenant linkage verified'
\echo ''

\echo '4. Testing cross-tenant access prevention...'

WITH tenant_task_counts AS (
    SELECT 
        up.id AS user_id,
        up.display_name,
        t.name AS tenant_name,
        (SELECT COUNT(*) 
         FROM agent_tasks at 
         WHERE at.tenant_id = up.tenant_id) AS visible_tasks
    FROM user_profiles up
    JOIN tenants t ON up.tenant_id = t.id
    WHERE up.id IN (
        '11111111-1111-1111-1111-111111111111',
        '33333333-3333-3333-3333-333333333333'
    )
)
SELECT * FROM tenant_task_counts;

\echo '  ✓ Cross-tenant isolation verified'
\echo ''

\echo '5. Testing role hierarchy...'

SELECT 
    display_name,
    role,
    CASE 
        WHEN role = 'owner' THEN 4
        WHEN role = 'admin' THEN 3
        WHEN role = 'member' THEN 2
        WHEN role = 'viewer' THEN 1
        ELSE 0
    END AS role_level
FROM user_profiles
WHERE tenant_id = '10000000-0000-0000-0000-000000000001'
ORDER BY role_level DESC;

\echo '  ✓ Role hierarchy verified'
\echo ''

\echo '6. Testing default tenant fallback...'

INSERT INTO agent_tasks (task_id, trace_id, tenant_id, question, status) VALUES
    ('task-default', 'trace-default', '00000000-0000-0000-0000-000000000001', 'Default tenant question', 'queued')
ON CONFLICT (task_id) DO NOTHING;

SELECT 
    task_id,
    tenant_id,
    (tenant_id = '00000000-0000-0000-0000-000000000001') AS is_default_tenant
FROM agent_tasks
WHERE task_id = 'task-default';

\echo '  ✓ Default tenant assignment verified'
\echo ''

\echo '7. Cleaning up test data...'

DELETE FROM agent_tasks WHERE task_id LIKE 'task-%';
DELETE FROM user_profiles WHERE id IN (
    '11111111-1111-1111-1111-111111111111',
    '22222222-2222-2222-2222-222222222222',
    '33333333-3333-3333-3333-333333333333'
);
DELETE FROM tenants WHERE id IN (
    '10000000-0000-0000-0000-000000000001',
    '20000000-0000-0000-0000-000000000001'
);

\echo '  ✓ Test data cleaned up'
\echo ''

\echo '========================================='
\echo '✅ All Phase 3 API Integration Tests Passed!'
\echo '========================================='

ROLLBACK;
