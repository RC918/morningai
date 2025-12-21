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

-- ============================================================================
-- Migration 039 Tests: planner_events, memory, error_fix_pairs, failure_memory
-- ============================================================================

-- Setup: Create test data for planner_events (linked to agent_tasks via trace_id)
RESET ROLE;
SET LOCAL ROLE service_role;

INSERT INTO planner_events (trace_id, goal, planner_type, task_type, actual_plan_steps, num_steps, planning_time_ms, timestamp) VALUES
    ('a1111111-0000-0000-0000-000000000000', 'Plan for Tenant A task', 'llm', 'faq', '["step1", "step2"]', 2, 100.5, NOW()),
    ('a2222222-0000-0000-0000-000000000000', 'Plan for Tenant B task', 'llm', 'faq', '["step1"]', 1, 50.0, NOW())
ON CONFLICT DO NOTHING;

-- Setup: Create test data for platform-wide tables
INSERT INTO memory (key, text, created_at) VALUES
    ('test_key_1', 'Test memory content', NOW())
ON CONFLICT DO NOTHING;

-- TEST 11: User A can read planner_events for their own tasks (via trace_id JOIN)
RESET ROLE;
SET LOCAL ROLE authenticated;
SET LOCAL request.jwt.claims.sub = '10000000-0000-0000-0000-000000000001';

SELECT 
    trace_id,
    goal,
    'TEST 11: User A reads planner_events for own tasks' as test_name
FROM planner_events;
-- Expected: Only see planner_events with trace_id = 'a1111111-...' (Tenant A's task)

-- TEST 12: User A cannot read planner_events for Tenant B's tasks
SELECT 
    COUNT(*) as event_count,
    'TEST 12: User A tries to read Tenant B planner_events' as test_name
FROM planner_events
WHERE trace_id = 'a2222222-0000-0000-0000-000000000000';
-- Expected: 0 rows (blocked by RLS)

-- TEST 13: Regular user cannot read memory table (platform_admin only)
SELECT 
    COUNT(*) as memory_count,
    'TEST 13: Regular user tries to read memory table' as test_name
FROM memory;
-- Expected: 0 rows (blocked by RLS - platform_admin only)

-- TEST 14: Regular user cannot read error_fix_pairs table (platform_admin only)
SELECT 
    COUNT(*) as pairs_count,
    'TEST 14: Regular user tries to read error_fix_pairs table' as test_name
FROM error_fix_pairs;
-- Expected: 0 rows (blocked by RLS - platform_admin only)

-- TEST 15: Regular user cannot read failure_memory table (platform_admin only)
SELECT 
    COUNT(*) as failure_count,
    'TEST 15: Regular user tries to read failure_memory table' as test_name
FROM failure_memory;
-- Expected: 0 rows (blocked by RLS - platform_admin only)

-- TEST 16: Service role can read all planner_events
RESET ROLE;
SET LOCAL ROLE service_role;

SELECT 
    trace_id,
    goal,
    'TEST 16: Service role reads all planner_events' as test_name
FROM planner_events
WHERE trace_id IN ('a1111111-0000-0000-0000-000000000000', 'a2222222-0000-0000-0000-000000000000');
-- Expected: Both rows visible

-- TEST 17: Service role can read memory table
SELECT 
    COUNT(*) as memory_count,
    'TEST 17: Service role reads memory table' as test_name
FROM memory;
-- Expected: All rows visible

-- ============================================================================
-- End of RLS Phase 2 Tests
-- ============================================================================
