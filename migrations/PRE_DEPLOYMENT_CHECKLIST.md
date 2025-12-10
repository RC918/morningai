# Pre-Deployment Checklist for RLS Phase 2 (PR #308)

**MANDATORY**: 必須完成所有檢查才能部署到生產環境

---

## 🔴 HIGH RISK 檢查項目

### Check #1: 驗證預設租戶存在

**風險**: 如果預設租戶不存在 → Migration 003 失敗 → 系統停機

**執行步驟**:

1. 在 Supabase SQL Editor 執行檢查：
```sql
-- 檢查預設租戶是否存在
SELECT * FROM tenants WHERE id = '00000000-0000-0000-0000-000000000001';
```

**預期結果**:
- ✅ 返回 1 行：預設租戶存在，可以繼續
- ❌ 返回 0 行：需要創建預設租戶（見下方修復步驟）

**修復步驟**（如果不存在）:
```sql
-- 創建預設租戶
INSERT INTO tenants (id, name, created_at, updated_at) 
VALUES (
    '00000000-0000-0000-0000-000000000001', 
    'Default Tenant (Migration)', 
    NOW(), 
    NOW()
)
ON CONFLICT (id) DO NOTHING;

-- 驗證創建成功
SELECT * FROM tenants WHERE id = '00000000-0000-0000-0000-000000000001';
```

**狀態**: [ ] PASS / [ ] FAIL

---

### Check #2: 確認所有 users 有 tenant_id

**風險**: 如果有 NULL tenant_id → 用戶被 RLS 鎖定 → 無法存取任何資料

**執行步驟**:

1. 檢查是否有 NULL tenant_id：
```sql
-- 計算有多少用戶沒有 tenant_id
SELECT COUNT(*) as null_tenant_users FROM users WHERE tenant_id IS NULL;
```

**預期結果**:
- ✅ 返回 0：所有用戶都有 tenant_id，可以繼續
- ❌ 返回 > 0：有用戶沒有 tenant_id，需要修復（見下方）

**查看詳細資訊**（如果有 NULL）:
```sql
-- 列出所有沒有 tenant_id 的用戶
SELECT id, email, created_at 
FROM users 
WHERE tenant_id IS NULL 
LIMIT 10;
```

**修復步驟**（如果有 NULL）:
```sql
-- 方案 A: 全部分配到預設租戶
UPDATE users 
SET tenant_id = '00000000-0000-0000-0000-000000000001',
    updated_at = NOW()
WHERE tenant_id IS NULL;

-- 驗證修復成功
SELECT COUNT(*) FROM users WHERE tenant_id IS NULL;
-- 應返回 0
```

**狀態**: [ ] PASS / [ ] FAIL

---

## 🟡 MEDIUM RISK 檢查項目

### Check #3: 驗證 tenants 資料表結構

**執行步驟**:
```sql
-- 檢查 tenants 資料表結構
SELECT column_name, data_type, is_nullable 
FROM information_schema.columns 
WHERE table_name = 'tenants' 
ORDER BY ordinal_position;
```

**預期結果**:
- `id` (uuid, NO)
- `name` (text, NO)
- `created_at` (timestamp with time zone)
- `updated_at` (timestamp with time zone)

**狀態**: [ ] PASS / [ ] FAIL

---

### Check #4: 驗證 users.tenant_id 欄位存在

**執行步驟**:
```sql
-- 檢查 users.tenant_id 欄位
SELECT column_name, data_type, is_nullable 
FROM information_schema.columns 
WHERE table_name = 'users' AND column_name = 'tenant_id';
```

**預期結果**:
- 返回 1 行：`tenant_id` (uuid, YES 或 NO)

**如果欄位不存在**:
```sql
-- Migration 003 會自動創建此欄位，無需手動處理
-- 但建議先確認 users 資料表存在
SELECT COUNT(*) FROM users;
```

**狀態**: [ ] PASS / [ ] FAIL

---

### Check #5: 檢查現有 agent_tasks 資料量

**執行步驟**:
```sql
-- 統計現有 agent_tasks 數量
SELECT 
    COUNT(*) as total_tasks,
    COUNT(DISTINCT status) as status_count,
    MIN(created_at) as oldest_task,
    MAX(created_at) as newest_task
FROM agent_tasks;
```

**目的**: 評估資料回填所需時間和影響

**狀態**: [ ] PASS / [ ] FAIL / [ ] N/A (no data)

---

## 🟢 LOW RISK 檢查項目

### Check #6: 驗證 RLS 已在 agent_tasks 啟用

**執行步驟**:
```sql
-- 檢查 RLS 狀態
SELECT tablename, rowsecurity 
FROM pg_tables 
WHERE schemaname = 'public' AND tablename = 'agent_tasks';
```

**預期結果**:
- `rowsecurity` = `true`

**狀態**: [ ] PASS / [ ] FAIL

---

### Check #7: 列出現有 RLS 政策

**執行步驟**:
```sql
-- 列出所有 agent_tasks 的 RLS 政策
SELECT 
    policyname, 
    cmd as operation,
    roles,
    qual as using_expression
FROM pg_policies 
WHERE tablename = 'agent_tasks'
ORDER BY policyname;
```

**預期結果** (Phase 1 政策):
- `service_role_all_access` (ALL, service_role)
- `users_read_own_tenant` (SELECT, authenticated)
- `users_insert_own_tenant` (INSERT, authenticated)
- `users_update_own_tenant` (UPDATE, authenticated)
- `anon_no_access` (ALL, anon)

**狀態**: [ ] PASS / [ ] FAIL

---

## 📋 Staging 環境測試

### Test #1: 在 Staging 執行 Migration 003

**執行步驟**:
1. 連接到 Staging Supabase
2. 複製 `migrations/003_add_tenant_id_to_agent_tasks.sql` 的內容
3. 在 SQL Editor 執行
4. 檢查是否有錯誤訊息

**預期結果**:
- ✅ 執行成功，無錯誤
- ✅ `agent_tasks.tenant_id` 欄位已創建
- ✅ 所有現有記錄的 tenant_id 已填充

**驗證**:
```sql
-- 確認 tenant_id 欄位存在且無 NULL
SELECT 
    COUNT(*) as total,
    COUNT(tenant_id) as with_tenant_id,
    COUNT(*) - COUNT(tenant_id) as null_count
FROM agent_tasks;
-- null_count 應為 0
```

**狀態**: [ ] PASS / [ ] FAIL

---

### Test #2: 在 Staging 執行 Migration 004

**執行步驟**:
1. 在 Staging Supabase SQL Editor
2. 複製 `migrations/004_update_rls_policies_with_tenant_isolation.sql` 的內容
3. 執行
4. 檢查是否有錯誤訊息

**預期結果**:
- ✅ 執行成功，無錯誤
- ✅ 舊政策已刪除
- ✅ 新政策已創建

**驗證**:
```sql
-- 確認新政策使用 tenant_id 檢查
SELECT policyname, qual 
FROM pg_policies 
WHERE tablename = 'agent_tasks' AND policyname = 'users_read_own_tenant';
-- qual 應包含 "tenant_id = ..."
```

**狀態**: [ ] PASS / [ ] FAIL

---

### Test #3: 在 Staging 執行 RLS 測試

**執行步驟**:
1. 在 Staging Supabase SQL Editor
2. 複製 `migrations/tests/test_rls_phase2.sql` 的內容
3. 逐個執行測試案例
4. 記錄結果

**預期結果**:
- ✅ Test 1-10 全部通過
- ✅ 租戶隔離正常運作
- ✅ Service role 保持完整權限

**狀態**: [ ] PASS / [ ] FAIL

---

## 💾 Production 備份

### Backup #1: 資料庫備份

**執行步驟**:
1. 前往 Supabase Dashboard
2. Project Settings → Database → Backups
3. 點擊 "Create Manual Backup"
4. 命名: `pre-rls-phase2-backup-YYYYMMDD`
5. 等待備份完成

**狀態**: [ ] COMPLETED / [ ] PENDING

---

### Backup #2: 匯出 agent_tasks 資料

**執行步驟**:
```sql
-- 匯出現有 agent_tasks 資料 (for rollback)
COPY (
    SELECT * FROM agent_tasks
) TO '/tmp/agent_tasks_backup_YYYYMMDD.csv' CSV HEADER;
```

或使用 Supabase Dashboard 匯出功能

**狀態**: [ ] COMPLETED / [ ] PENDING

---

## 🚀 部署執行順序

**必須按照以下順序執行**:

1. [ ] ✅ 完成所有 HIGH RISK 檢查 (#1, #2)
2. [ ] ✅ 完成 Staging 測試 (Test #1, #2, #3)
3. [ ] ✅ 創建 Production 備份
4. [ ] 在 Production 執行 Migration 003
5. [ ] 驗證 Migration 003 成功
6. [ ] 在 Production 執行 Migration 004
7. [ ] 驗證 Migration 004 成功
8. [ ] 執行 Production RLS 測試（簡化版）
9. [ ] 監控應用程式日誌 (10 分鐘)
10. [ ] 確認無異常後，Merge PR #308

---

## 📞 緊急回滾計劃

**如果部署後出現問題**:

### Rollback Migration 004 (RLS 政策)
```sql
-- 快速回滾到 Phase 1 政策
DROP POLICY IF EXISTS "users_read_own_tenant" ON agent_tasks;
DROP POLICY IF EXISTS "users_insert_own_tenant" ON agent_tasks;
DROP POLICY IF EXISTS "users_update_own_tenant" ON agent_tasks;
DROP POLICY IF EXISTS "users_delete_own_tenant" ON agent_tasks;

-- 恢復 Phase 1 政策 (允許所有已驗證用戶)
CREATE POLICY "users_read_own_tenant" ON agent_tasks
    FOR SELECT TO authenticated USING (true);

CREATE POLICY "users_insert_own_tenant" ON agent_tasks
    FOR INSERT TO authenticated WITH CHECK (true);

CREATE POLICY "users_update_own_tenant" ON agent_tasks
    FOR UPDATE TO authenticated USING (true) WITH CHECK (true);
```

### Rollback Migration 003 (tenant_id 欄位)
```sql
-- 注意：此操作會刪除資料，僅在緊急情況使用
DROP INDEX IF EXISTS idx_agent_tasks_tenant_id;
ALTER TABLE agent_tasks DROP CONSTRAINT IF EXISTS fk_agent_tasks_tenant;
ALTER TABLE agent_tasks DROP COLUMN IF EXISTS tenant_id;
```

---

## ✅ 最終檢查清單

**部署前必須全部完成**:

- [ ] 🔴 HIGH RISK Check #1: 預設租戶存在
- [ ] 🔴 HIGH RISK Check #2: 所有 users 有 tenant_id
- [ ] 🟡 MEDIUM RISK Check #3: tenants 資料表結構正確
- [ ] 🟡 MEDIUM RISK Check #4: users.tenant_id 欄位存在
- [ ] 🟢 Staging Test #1: Migration 003 執行成功
- [ ] 🟢 Staging Test #2: Migration 004 執行成功
- [ ] 🟢 Staging Test #3: RLS 測試全部通過
- [ ] 💾 Production 備份已完成
- [ ] 📞 團隊已知悉緊急回滾計劃

**簽核**:
- 工程師: _____________ 日期: _______
- 審核者: _____________ 日期: _______

---

## 📝 Execution Log

Record deployment execution here for audit trail. See also [RLS_DEPLOYMENT_STATUS.md](../docs/RLS_DEPLOYMENT_STATUS.md) for comprehensive status tracking.

### Staging Deployment Log

| Date | Migration | Executor | Result | Notes |
|------|-----------|----------|--------|-------|
| - | - | - | - | No deployments yet |

### Production Deployment Log

| Date | Migration | Executor | Result | Notes |
|------|-----------|----------|--------|-------|
| - | - | - | - | No deployments yet |

### Health Check Verification Log

| Date | Environment | Workflow Run | Result | Notes |
|------|-------------|--------------|--------|-------|
| - | - | - | - | No checks run yet |

---

**準備好部署了嗎？** 
如果所有檢查都是 ✅ PASS，且 Staging 測試成功，即可進行 Production 部署！
