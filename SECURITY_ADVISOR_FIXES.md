# Supabase Security Advisor 修復指南

本文件說明如何修復 Supabase Security Advisor 中的 3 個警告。

## 📋 警告清單

### ✅ 1. Materialized View in API - `public.daily_cost_summary`
**狀態**: 已透過 Migration 017 修復

**問題**: Materialized view 可透過 API 存取但未設定存取權限

**修復方式**:
- 使用 GRANT/REVOKE 控制存取權限（PostgreSQL 不支援 materialized views 的 RLS）
- 撤銷 PUBLIC 的所有權限
- 授予 service_role 和 authenticated 讀取權限（SELECT）

### ✅ 2. Materialized View in API - `public.vector_visualization`
**狀態**: 已透過 Migration 017 修復

**問題**: Materialized view 可透過 API 存取但未設定存取權限

**修復方式**:
- 使用 GRANT/REVOKE 控制存取權限（PostgreSQL 不支援 materialized views 的 RLS）
- 撤銷 PUBLIC 的所有權限
- 授予 service_role 和 authenticated 讀取權限（SELECT）

### ⚠️ 3. Leaked Password Protection Disabled
**狀態**: 需要手動啟用

**問題**: Supabase Auth 的洩漏密碼保護功能未啟用

**風險**: 使用者可能使用已知洩漏的密碼註冊，增加帳號被盜風險

## 🔧 手動啟用 Leaked Password Protection

### 步驟 1: 登入 Supabase Dashboard
1. 前往 [Supabase Dashboard](https://app.supabase.com/)
2. 選擇你的專案

### 步驟 2: 進入 Authentication 設定
1. 點選左側選單的 **Authentication**
2. 點選 **Settings** 標籤

### 步驟 3: 啟用 Password Protection
1. 找到 **Password Protection** 區塊
2. 啟用 **"Check for leaked passwords"** 選項
3. 儲存設定

### 步驟 4: 驗證設定
1. 回到 **Security Advisor**
2. 點選 **Refresh** 按鈕
3. 確認 "Leaked Password Protection Disabled" 警告已消失

## 📊 預期結果

完成所有修復後，Supabase Security Advisor 應該顯示：
- ✅ **0 Errors**
- ✅ **0 Warnings**

## 🔍 驗證方式

### 驗證權限已設定
```sql
-- 檢查 materialized views 的 ACL 權限
SELECT 
    c.relname,
    c.relacl
FROM pg_class c
JOIN pg_namespace n ON c.relnamespace = n.oid
WHERE n.nspname = 'public' 
AND c.relname IN ('daily_cost_summary', 'vector_visualization');

-- 檢查特定角色的權限
SELECT 
    table_name,
    grantee,
    privilege_type
FROM information_schema.role_table_grants
WHERE table_schema = 'public' 
AND table_name IN ('daily_cost_summary', 'vector_visualization')
ORDER BY table_name, grantee;
```

### 驗證存取權限
```sql
-- 測試 authenticated 使用者可以讀取
SELECT COUNT(*) FROM public.daily_cost_summary;
SELECT COUNT(*) FROM public.vector_visualization;

-- 測試 anon 使用者無法存取（應該回傳權限錯誤）
SET ROLE anon;
SELECT COUNT(*) FROM public.daily_cost_summary;  -- 應該失敗
RESET ROLE;
```

## 📝 技術細節

### Materialized Views 的權限控制
- **重要**: PostgreSQL **不支援** materialized views 的 Row Level Security (RLS)
- RLS 只能用於普通 tables，不能用於 materialized views
- 因此使用 GRANT/REVOKE 來控制存取權限
- 這是 PostgreSQL 的限制，不是 Supabase 的限制

### 權限模型
- `PUBLIC`: 撤銷所有權限（預設情況下任何人都可以存取）
- `service_role`: 授予 SELECT 權限（backend 服務使用）
- `authenticated`: 授予 SELECT 權限（已登入的 Dashboard 使用者）
- `anon`: 無權限（未登入的使用者無法存取）

### Leaked Password Protection
- 使用 [Have I Been Pwned](https://haveibeenpwned.com/) API
- 檢查密碼是否出現在已知的資料洩漏事件中
- 不會傳送完整密碼，使用 k-anonymity 保護隱私
- 只在使用者註冊或變更密碼時檢查

## 🚀 部署檢查清單

- [x] Migration 017 已建立
- [ ] Migration 017 已套用到 Supabase
- [ ] Leaked Password Protection 已手動啟用
- [ ] Security Advisor 顯示 0 warnings
- [ ] 測試 authenticated 使用者可以存取 materialized views
- [ ] 測試 anon 使用者無法存取 materialized views

## 📚 相關文件

- [Supabase RLS Documentation](https://supabase.com/docs/guides/auth/row-level-security)
- [Supabase Auth Configuration](https://supabase.com/docs/guides/auth/auth-helpers/auth-ui)
- [Have I Been Pwned API](https://haveibeenpwned.com/API/v3)

## ❓ 常見問題

### Q: 為什麼不使用 RLS 而是使用 GRANT/REVOKE？
A: PostgreSQL **不支援** materialized views 的 Row Level Security (RLS)。這是 PostgreSQL 的限制，不是 Supabase 的限制。因此我們使用 GRANT/REVOKE 來控制存取權限，這是 materialized views 唯一可用的權限控制方式。

### Q: GRANT/REVOKE 和 RLS 有什麼差別？
A: 
- **GRANT/REVOKE**: 控制哪些**角色**可以存取整個 table/view（粗粒度）
- **RLS**: 控制哪些**使用者**可以存取哪些**特定 rows**（細粒度）
- 對於 materialized views，我們只能使用 GRANT/REVOKE

### Q: 啟用 Leaked Password Protection 會影響現有使用者嗎？
A: 不會。這個功能只在新使用者註冊或現有使用者變更密碼時生效。現有密碼不會被檢查。

### Q: 如果使用者使用了洩漏的密碼會怎樣？
A: Supabase 會拒絕該密碼並要求使用者選擇不同的密碼。

### Q: 這些修復會影響效能嗎？
A: GRANT/REVOKE 對效能沒有影響，因為權限檢查在 PostgreSQL 層級進行。Leaked Password Protection 只在註冊/變更密碼時執行，不影響日常操作。
