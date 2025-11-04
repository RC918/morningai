--
--

\echo '========================================================================';
\echo 'RLS PHASE 2 PRE-DEPLOYMENT VERIFICATION';
\echo '========================================================================';
\echo '';


\echo '🔴 CHECK #1: 驗證預設租戶存在';
\echo '---';

DO $$ 
DECLARE
    tenant_exists BOOLEAN;
BEGIN
    SELECT EXISTS (
        SELECT 1 FROM tenants 
        WHERE id = '00000000-0000-0000-0000-000000000001'
    ) INTO tenant_exists;
    
    IF tenant_exists THEN
        RAISE NOTICE '✅ PASS: 預設租戶存在';
    ELSE
        RAISE WARNING '❌ FAIL: 預設租戶不存在！';
        RAISE NOTICE 'ACTION REQUIRED: 執行以下修復指令';
        RAISE NOTICE 'INSERT INTO tenants (id, name) VALUES (''00000000-0000-0000-0000-000000000001'', ''Default Tenant'');';
    END IF;
END $$;

SELECT 
    id,
    name,
    created_at,
    '✅ CHECK #1 PASS' as status
FROM tenants 
WHERE id = '00000000-0000-0000-0000-000000000001';

\echo '';


\echo '🔴 CHECK #2: 確認所有 users 有 tenant_id';
\echo '---';

DO $$ 
DECLARE
    null_count INTEGER;
    total_users INTEGER;
BEGIN
    SELECT COUNT(*) INTO null_count FROM users WHERE tenant_id IS NULL;
    SELECT COUNT(*) INTO total_users FROM users;
    
    IF null_count = 0 THEN
        RAISE NOTICE '✅ PASS: 所有用戶都有 tenant_id (總數: %)', total_users;
    ELSE
        RAISE WARNING '❌ FAIL: 有 % 個用戶沒有 tenant_id (總數: %)', null_count, total_users;
        RAISE NOTICE 'ACTION REQUIRED: 執行以下修復指令';
        RAISE NOTICE 'UPDATE users SET tenant_id = ''00000000-0000-0000-0000-000000000001'' WHERE tenant_id IS NULL;';
    END IF;
END $$;

SELECT 
    COUNT(*) as total_users,
    COUNT(tenant_id) as users_with_tenant,
    COUNT(*) - COUNT(tenant_id) as null_tenant_users,
    CASE 
        WHEN COUNT(*) - COUNT(tenant_id) = 0 THEN '✅ CHECK #2 PASS'
        ELSE '❌ CHECK #2 FAIL'
    END as status
FROM users;

SELECT 
    id,
    email,
    created_at,
    '⚠️ 需要修復' as status
FROM users 
WHERE tenant_id IS NULL 
LIMIT 5;

\echo '';


\echo '🟡 CHECK #3: 驗證 tenants 資料表結構';
\echo '---';

SELECT 
    column_name,
    data_type,
    is_nullable,
    '✅ CHECK #3' as status
FROM information_schema.columns 
WHERE table_schema = 'public' AND table_name = 'tenants' 
ORDER BY ordinal_position;

\echo '';


\echo '🟡 CHECK #4: 驗證 users.tenant_id 欄位存在';
\echo '---';

DO $$ 
DECLARE
    column_exists BOOLEAN;
BEGIN
    SELECT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'users' AND column_name = 'tenant_id'
    ) INTO column_exists;
    
    IF column_exists THEN
        RAISE NOTICE '✅ PASS: users.tenant_id 欄位存在';
    ELSE
        RAISE WARNING '⚠️ WARNING: users.tenant_id 欄位不存在 (Migration 003 會自動創建)';
    END IF;
END $$;

SELECT 
    column_name,
    data_type,
    is_nullable,
    '✅ CHECK #4' as status
FROM information_schema.columns 
WHERE table_schema = 'public' 
  AND table_name = 'users' 
  AND column_name = 'tenant_id';

\echo '';


\echo '📊 CHECK #5: 檢查現有 agent_tasks 資料量';
\echo '---';

SELECT 
    COUNT(*) as total_tasks,
    COUNT(DISTINCT status) as distinct_statuses,
    COUNT(DISTINCT COALESCE(tenant_id, '00000000-0000-0000-0000-000000000000'::uuid)) as distinct_tenants,
    MIN(created_at) as oldest_task,
    MAX(created_at) as newest_task,
    '📊 INFO' as status
FROM agent_tasks;

SELECT 
    status,
    COUNT(*) as count,
    '📊 按狀態統計' as category
FROM agent_tasks
GROUP BY status
ORDER BY count DESC;

\echo '';


\echo '🟢 CHECK #6: 驗證 RLS 已在 agent_tasks 啟用';
\echo '---';

DO $$ 
DECLARE
    rls_enabled BOOLEAN;
BEGIN
    SELECT rowsecurity INTO rls_enabled
    FROM pg_tables 
    WHERE schemaname = 'public' AND tablename = 'agent_tasks';
    
    IF rls_enabled THEN
        RAISE NOTICE '✅ PASS: RLS 已啟用';
    ELSE
        RAISE WARNING '❌ FAIL: RLS 未啟用！';
    END IF;
END $$;

SELECT 
    tablename,
    rowsecurity as rls_enabled,
    CASE 
        WHEN rowsecurity THEN '✅ CHECK #6 PASS'
        ELSE '❌ CHECK #6 FAIL'
    END as status
FROM pg_tables 
WHERE schemaname = 'public' AND tablename = 'agent_tasks';

\echo '';


\echo '📋 CHECK #7: 列出現有 RLS 政策';
\echo '---';

SELECT 
    policyname,
    cmd as operation,
    roles,
    LEFT(qual::text, 50) as using_clause_preview,
    '📋 現有政策' as category
FROM pg_policies 
WHERE tablename = 'agent_tasks'
ORDER BY policyname;

\echo '';


\echo '========================================================================';
\echo 'SUMMARY: 最終檢查結果';
\echo '========================================================================';

DO $$ 
DECLARE
    check1_pass BOOLEAN; -- 預設租戶存在
    check2_pass BOOLEAN; -- 所有 users 有 tenant_id
    check6_pass BOOLEAN; -- RLS 已啟用
    null_user_count INTEGER;
BEGIN
    SELECT EXISTS (
        SELECT 1 FROM tenants WHERE id = '00000000-0000-0000-0000-000000000001'
    ) INTO check1_pass;
    
    SELECT COUNT(*) INTO null_user_count FROM users WHERE tenant_id IS NULL;
    check2_pass := (null_user_count = 0);
    
    SELECT rowsecurity INTO check6_pass
    FROM pg_tables 
    WHERE schemaname = 'public' AND tablename = 'agent_tasks';
    
    RAISE NOTICE '';
    RAISE NOTICE '========================================';
    RAISE NOTICE 'CRITICAL CHECKS (MUST PASS):';
    RAISE NOTICE '========================================';
    
    IF check1_pass THEN
        RAISE NOTICE '✅ CHECK #1 PASS: 預設租戶存在';
    ELSE
        RAISE WARNING '❌ CHECK #1 FAIL: 預設租戶不存在';
    END IF;
    
    IF check2_pass THEN
        RAISE NOTICE '✅ CHECK #2 PASS: 所有 users 有 tenant_id';
    ELSE
        RAISE WARNING '❌ CHECK #2 FAIL: 有 % 個用戶沒有 tenant_id', null_user_count;
    END IF;
    
    IF check6_pass THEN
        RAISE NOTICE '✅ CHECK #6 PASS: RLS 已啟用';
    ELSE
        RAISE WARNING '❌ CHECK #6 FAIL: RLS 未啟用';
    END IF;
    
    RAISE NOTICE '';
    
    IF check1_pass AND check2_pass AND check6_pass THEN
        RAISE NOTICE '🎉 所有 CRITICAL 檢查通過！可以繼續部署。';
    ELSE
        RAISE WARNING '⚠️ 有 CRITICAL 檢查失敗！請修復後再部署。';
    END IF;
    
    RAISE NOTICE '========================================';
END $$;

\echo '';
\echo '========================================================================';
\echo 'PRE-DEPLOYMENT VERIFICATION COMPLETE';
\echo '========================================================================';
\echo '';
\echo '下一步:';
\echo '1. 如果所有 CRITICAL 檢查通過 → 繼續 Staging 測試';
\echo '2. 如果有檢查失敗 → 執行上方顯示的修復指令';
\echo '3. 完整部署流程見: migrations/PRE_DEPLOYMENT_CHECKLIST.md';
\echo '';
