--
--


INSERT INTO tenants (id, name) VALUES 
    ('00000000-0000-0000-0000-000000000001', 'Tenant A (Test)'),
    ('00000000-0000-0000-0000-000000000002', 'Tenant B (Test)')
ON CONFLICT (id) DO NOTHING;

INSERT INTO users (id, tenant_id, email) VALUES
    ('10000000-0000-0000-0000-000000000001', '00000000-0000-0000-0000-000000000001', 'user_a@test.com'),
    ('20000000-0000-0000-0000-000000000002', '00000000-0000-0000-0000-000000000002', 'user_b@test.com')
ON CONFLICT (id) DO NOTHING;

INSERT INTO agent_tasks (task_id, tenant_id, trace_id, question, status) VALUES
    ('a1111111-0000-0000-0000-000000000000', '00000000-0000-0000-0000-000000000001', 'a1111111-0000-0000-0000-000000000000', 'Task for Tenant A', 'queued'),
    ('a2222222-0000-0000-0000-000000000000', '00000000-0000-0000-0000-000000000002', 'a2222222-0000-0000-0000-000000000000', 'Task for Tenant B', 'queued')
ON CONFLICT (task_id) DO NOTHING;

SET LOCAL ROLE authenticated;
SET LOCAL request.jwt.claims.sub = '10000000-0000-0000-0000-000000000001';

SELECT 
    task_id, 
    tenant_id, 
    question,
    'TEST 1: User A reads all tasks' as test_name
FROM agent_tasks;


RESET ROLE;
SET LOCAL ROLE authenticated;
SET LOCAL request.jwt.claims.sub = '20000000-0000-0000-0000-000000000002';

SELECT 
    task_id, 
    tenant_id, 
    question,
    'TEST 2: User B reads all tasks' as test_name
FROM agent_tasks;


RESET ROLE;
SET LOCAL ROLE authenticated;
SET LOCAL request.jwt.claims.sub = '10000000-0000-0000-0000-000000000001';

SELECT 
    task_id, 
    tenant_id, 
    question,
    'TEST 3: User A tries to read Tenant B task' as test_name
FROM agent_tasks 
WHERE tenant_id = '00000000-0000-0000-0000-000000000002';


SELECT 
    task_id, 
    tenant_id, 
    question,
    'TEST 4: User A tries to read specific Tenant B task' as test_name
FROM agent_tasks 
WHERE task_id = 'a2222222-0000-0000-0000-000000000000';


UPDATE agent_tasks 
SET status = 'completed' 
WHERE task_id = 'a2222222-0000-0000-0000-000000000000'
RETURNING task_id, tenant_id, status, 'TEST 5: User A tries to update Tenant B task' as test_name;


UPDATE agent_tasks 
SET status = 'running' 
WHERE task_id = 'a1111111-0000-0000-0000-000000000000'
RETURNING task_id, tenant_id, status, 'TEST 6: User A updates own task' as test_name;


RESET ROLE;
SET LOCAL ROLE authenticated;
SET LOCAL request.jwt.claims.sub = '10000000-0000-0000-0000-000000000001';

DELETE FROM agent_tasks 
WHERE task_id = 'a2222222-0000-0000-0000-000000000000'
RETURNING task_id, tenant_id, 'TEST 7: User A tries to delete Tenant B task' as test_name;


RESET ROLE;
SET LOCAL ROLE service_role;

SELECT 
    task_id, 
    tenant_id, 
    question,
    'TEST 8: Service role reads all tasks' as test_name
FROM agent_tasks
WHERE task_id IN ('a1111111-0000-0000-0000-000000000000', 'a2222222-0000-0000-0000-000000000000');


RESET ROLE;
SET LOCAL ROLE anon;

SELECT 
    COUNT(*) as task_count,
    'TEST 9: Anon role reads all tasks' as test_name
FROM agent_tasks;


RESET ROLE;
SET LOCAL ROLE authenticated;
SET LOCAL request.jwt.claims.sub = '10000000-0000-0000-0000-000000000001';

INSERT INTO agent_tasks (task_id, tenant_id, trace_id, question, status) 
VALUES (
    'a3333333-0000-0000-0000-000000000000', 
    '00000000-0000-0000-0000-000000000002',  -- Tenant B (not User A's tenant)
    'a3333333-0000-0000-0000-000000000000', 
    'Malicious task', 
    'queued'
);




--
--
