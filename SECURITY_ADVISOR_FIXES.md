# Supabase Security Advisor 修復指南

本文件說明如何修復 Supabase Security Advisor 中的 3 個警告。

## 📋 警告清單

### ✅ 1. Materialized View in API - `public.daily_cost_summary`
**狀態**: 已透過 Migration 017 修復

**問題**: Materialized view 可透過 API 存取但未啟用 RLS

**修復方式**:
- 啟用 RLS: `ALTER MATERIALIZED VIEW public.daily_cost_summary ENABLE ROW LEVEL SECURITY`
- 建立 policies 限制存取權限（service_role 和 authenticated）

### ✅ 2. Materialized View in API - `public.vector_visualization`
**狀態**: 已透過 Migration 017 修復

**問題**: Materialized view 可透過 API 存取但未啟用 RLS

**修復方式**:
- 啟用 RLS: `ALTER MATERIALIZED VIEW public.vector_visualization ENABLE ROW LEVEL SECURITY`
- 建立 policies 限制存取權限（service_role 和 authenticated）

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

### 驗證 RLS 已啟用
```sql
-- 檢查 daily_cost_summary RLS 狀態
SELECT 
    schemaname, 
    tablename, 
    rowsecurity 
FROM pg_tables 
WHERE tablename IN ('daily_cost_summary', 'vector_visualization');

-- 檢查 policies
SELECT 
    schemaname,
    tablename,
    policyname,
    roles,
    cmd
FROM pg_policies
WHERE tablename IN ('daily_cost_summary', 'vector_visualization');
```

### 驗證存取權限
```sql
-- 測試 authenticated 使用者可以讀取
SELECT COUNT(*) FROM public.daily_cost_summary;
SELECT COUNT(*) FROM public.vector_visualization;

-- 測試 anon 使用者無法存取（應該回傳 0 或錯誤）
SET ROLE anon;
SELECT COUNT(*) FROM public.daily_cost_summary;  -- 應該失敗
RESET ROLE;
```

## 📝 技術細節

### Materialized Views 的 RLS
- Materialized views 支援 RLS，但需要明確啟用
- RLS policies 的運作方式與一般 tables 相同
- 只有符合 policy 條件的 rows 會被回傳

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

### Q: 為什麼 materialized views 需要 RLS？
A: 雖然我們已經用 GRANT/REVOKE 限制權限，但 Supabase Security Advisor 建議所有可透過 API 存取的物件都應該啟用 RLS，提供額外的安全層。

### Q: 啟用 Leaked Password Protection 會影響現有使用者嗎？
A: 不會。這個功能只在新使用者註冊或現有使用者變更密碼時生效。現有密碼不會被檢查。

### Q: 如果使用者使用了洩漏的密碼會怎樣？
A: Supabase 會拒絕該密碼並要求使用者選擇不同的密碼。

### Q: 這些修復會影響效能嗎？
A: RLS 對 materialized views 的效能影響極小，因為這些 views 主要由 service_role 存取。Leaked Password Protection 只在註冊/變更密碼時執行，不影響日常操作。
