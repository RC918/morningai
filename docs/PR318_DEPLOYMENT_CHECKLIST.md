# PR #318 部署檢查清單

## 🚨 CRITICAL: Breaking Changes

### 1. `/api/agent/faq` 端點現在需要認證

**變更位置**: `handoff/20250928/40_App/api-backend/src/routes/agent.py:72`

```python
@bp.route("/faq", methods=["POST"])
@jwt_required  # ⚠️ NEW: Breaking Change
def create_faq_task():
```

**影響範圍**:
- 所有調用 `/api/agent/faq` 的客戶端必須提供 JWT token
- 未提供 token 的請求將收到 `401 Unauthorized`

**受影響的客戶端**:
- Frontend Dashboard
- 任何直接調用 API 的腳本或工具
- E2E 測試腳本
- Postman/Curl 測試

**修復方案**:
1. 更新所有客戶端添加 `Authorization: Bearer <JWT_TOKEN>` header
2. 確保 JWT token 有效且未過期
3. 測試所有現有功能仍能正常運作

---

## ✅ 部署前檢查 (PRE-DEPLOYMENT)

### 1. 驗證預設租戶存在

```sql
-- 在 Supabase SQL Editor 執行
SELECT * FROM tenants WHERE id = '00000000-0000-0000-0000-000000000001';

-- 如果不存在，創建它
INSERT INTO tenants (id, name) 
VALUES ('00000000-0000-0000-0000-000000000001', 'Default Tenant (Migration)')
ON CONFLICT (id) DO NOTHING;
```

**風險**: 如果不存在 → Migration 失敗 → 系統停機 ⚠️

### 2. 確認所有 users 有 tenant_id

```sql
-- 檢查是否有 NULL
SELECT COUNT(*) FROM users WHERE tenant_id IS NULL;

-- 如果有 NULL，修復
UPDATE users 
SET tenant_id = '00000000-0000-0000-0000-000000000001' 
WHERE tenant_id IS NULL;
```

**風險**: 如果有 NULL → 用戶被鎖定 → 無法存取資料 ⚠️

### 3. 備份資料庫

```bash
# 在 Supabase Dashboard
# Settings → Database → Backup
# 或使用 pg_dump
pg_dump -h <host> -U <user> -d <db> > backup_$(date +%Y%m%d_%H%M%S).sql
```

---

## 📦 部署順序 (MUST FOLLOW)

### Step 1: 執行 Migration 005 (user_profiles 表)

```bash
# 使用提供的腳本
python scripts/apply_phase3_migrations.py --migration 005

# 或手動執行
psql -h <host> -U <user> -d <db> -f migrations/005_create_user_profiles_table.sql
```

**驗證**:
```sql
-- 確認表已創建
SELECT * FROM information_schema.tables WHERE table_name = 'user_profiles';

-- 確認 RLS 已啟用
SELECT tablename, rowsecurity FROM pg_tables WHERE tablename = 'user_profiles';

-- 確認用戶已回填
SELECT COUNT(*) FROM user_profiles;
```

### Step 2: 執行 Migration 006 (RLS policies)

```bash
python scripts/apply_phase3_migrations.py --migration 006

# 或手動
psql -h <host> -U <user> -d <db> -f migrations/006_update_rls_policies_true_tenant_isolation.sql
```

**驗證**:
```sql
-- 確認 policies 已創建
SELECT policyname FROM pg_policies 
WHERE tablename = 'agent_tasks' 
AND policyname LIKE 'true_tenant_isolation%';
-- 應該返回 4 個 policies

-- 確認舊 policies 已刪除
SELECT policyname FROM pg_policies 
WHERE tablename = 'agent_tasks' 
AND policyname IN ('tenant_read_policy', 'tenant_insert_policy');
-- 應該返回 0 行
```

### Step 3: 執行測試腳本

```bash
# 測試 RLS 隔離
psql -h <host> -U <user> -d <db> -f migrations/tests/test_phase3_tenant_isolation.sql

# 測試 API 整合
psql -h <host> -U <user> -d <db> -f migrations/tests/test_phase3_api_integration.sql
```

**預期結果**: 所有測試應顯示 ✅ PASS

### Step 4: 部署後端 (Backend)

```bash
# 如果使用 CI/CD，merge PR 會自動部署
# 手動部署範例：
cd handoff/20250928/40_App/api-backend
git pull origin phase3-rls-tenant-isolation-20251018
# 重啟服務
systemctl restart api-backend
# 或 Docker
docker-compose up -d --build api-backend
```

### Step 5: 部署前端 (Frontend)

```bash
cd handoff/20250928/40_App/frontend-dashboard
git pull origin phase3-rls-tenant-isolation-20251018
npm run build
# Vercel 會自動部署
```

### Step 6: 驗證部署

```bash
# 1. 檢查健康狀態
curl https://api.morningai.com/health

# 2. 測試 FAQ 端點 (需要 JWT)
curl -X POST https://api.morningai.com/api/agent/faq \
  -H "Authorization: Bearer <JWT_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{"question": "Test after deployment"}'

# 3. 測試租戶端點
curl https://api.morningai.com/api/tenant/me \
  -H "Authorization: Bearer <JWT_TOKEN>"
```

---

## 🧪 測試清單

### Backend API 測試

- [ ] `/api/agent/faq` POST 需要 JWT token
- [ ] `/api/agent/faq` POST 無 token 返回 401
- [ ] `/api/agent/tasks/<id>` GET 可正常取得任務狀態
- [ ] `/api/tenant/me` GET 返回當前用戶租戶資訊
- [ ] `/api/tenant/members` GET 列出租戶成員

### Database 測試

- [ ] `user_profiles` 表存在且有正確欄位
- [ ] `agent_tasks` 有 4 個 TRUE isolation policies
- [ ] 舊的 temporary policies 已刪除
- [ ] RLS 啟用在 `user_profiles` 和 `agent_tasks`
- [ ] 所有用戶已分配到租戶

### Frontend 測試

- [ ] `/tenant-settings` 頁面可訪問
- [ ] TenantContext 正確載入租戶資訊
- [ ] 成員列表顯示正確
- [ ] 只有 admin/owner 可更新成員角色

---

## 🔄 Rollback 計劃

如果部署失敗，執行以下步驟：

### 1. 回滾 Backend Code

```bash
git checkout main
# 重啟服務
```

### 2. 回滾 Database Migrations

```sql
-- 刪除新的 policies
DROP POLICY IF EXISTS "true_tenant_isolation_read" ON agent_tasks;
DROP POLICY IF EXISTS "true_tenant_isolation_insert" ON agent_tasks;
DROP POLICY IF EXISTS "true_tenant_isolation_update" ON agent_tasks;
DROP POLICY IF EXISTS "true_tenant_isolation_delete" ON agent_tasks;

-- 恢復舊的 policies (從 migration 004)
-- ... (參考 migrations/004_update_rls_policies_with_tenant_isolation.sql)

-- 刪除 user_profiles 表 (如果必要)
DROP TABLE IF EXISTS user_profiles CASCADE;
```

### 3. 回滾 Frontend

```bash
# Vercel 會自動回滾到上一個成功部署
# 或手動切換到之前的 deployment
```

---

## 📊 監控指標

部署後監控以下指標：

1. **API 錯誤率**
   - 監控 401 錯誤數量 (預期會增加，因為 Breaking Change)
   - 監控 500 錯誤 (不應增加)

2. **資料庫效能**
   - RLS policy 查詢時間
   - `user_profiles` JOIN 效能
   - Index 使用率

3. **用戶行為**
   - 登入失敗率
   - 任務創建成功率
   - 租戶切換頻率

---

## 📞 問題排查

### 問題 1: 用戶無法存取任務

**症狀**: 用戶看不到自己的任務

**檢查**:
```sql
-- 1. 確認用戶有 user_profile
SELECT * FROM user_profiles WHERE id = '<user_id>';

-- 2. 確認任務有正確的 tenant_id
SELECT task_id, tenant_id FROM agent_tasks WHERE task_id = '<task_id>';

-- 3. 確認 RLS policies 生效
EXPLAIN SELECT * FROM agent_tasks WHERE tenant_id = '<tenant_id>';
```

### 問題 2: 401 Unauthorized 錯誤

**症狀**: 所有 API 請求返回 401

**檢查**:
```bash
# 1. JWT token 是否有效
curl -X POST https://api.morningai.com/api/agent/faq \
  -H "Authorization: Bearer <TOKEN>" \
  -v

# 2. 檢查 JWT_SECRET_KEY 環境變數
echo $JWT_SECRET_KEY

# 3. 檢查 middleware 日誌
tail -f /var/log/api-backend.log | grep "jwt"
```

### 問題 3: 資料庫效能問題

**症狀**: API 回應緩慢

**檢查**:
```sql
-- 確認 indexes 存在
SELECT * FROM pg_indexes 
WHERE tablename IN ('user_profiles', 'agent_tasks')
AND indexname LIKE 'idx_%tenant_id';

-- 查看慢查詢
SELECT * FROM pg_stat_statements 
ORDER BY mean_exec_time DESC 
LIMIT 10;
```

---

## ✅ 完成檢查

部署完成後，確認以下項目：

- [ ] 所有 CI 測試通過
- [ ] Backend 健康檢查通過
- [ ] Frontend 正常載入
- [ ] 可以創建新任務 (需要 JWT)
- [ ] 租戶隔離生效 (用戶只能看到自己租戶的資料)
- [ ] 監控儀表板無異常
- [ ] 用戶反饋正常

---

## 📝 Notes

- Migration 005 & 006 是**不可逆**的變更
- 建議在**低流量時段**部署
- 提前通知用戶可能的短暫停機
- 準備好快速回滾計劃

---

Generated for PR #318
Date: 2025-10-18
Link: https://github.com/RC918/morningai/pull/318
