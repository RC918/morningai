# Supabase 安全問題修復指南

**日期**: 2025-10-17  
**問題**: Supabase Security Advisor 檢測到 7 個安全問題  
**狀態**: 修復腳本已準備好

---

## 📊 檢測到的問題

### 🔴 錯誤（5個）- RLS Disabled

1. `public.agent_tasks` - RLS 未啟用
2. `public.code_relationships` - RLS 未啟用
3. `public.embedding_cache_stats` - RLS 未啟用
4. `public.code_embeddings` - RLS 未啟用
5. `public.code_patterns` - RLS 未啟用

### ⚠️ 警告（2個）

1. `public.update_updated_at_column` - Function Search Path Mutable（函數搜索路徑可變）
2. `public.vector` - Extension in Public schema（擴展在 public schema 中）

---

## 🔧 修復方案

### 問題分析

1. **RLS 策略文件存在但未執行**: Week 5 創建了 `002_add_rls_policies.sql`，但在 migration 過程中沒有被執行
2. **agent_tasks 表缺少 RLS**: 這是之前創建的表，當時沒有添加 RLS
3. **函數搜索路徑問題**: `update_updated_at_column()` 函數沒有明確設置 `search_path`，存在安全風險
4. **vector 擴展警告**: pgvector 擴展安裝在 public schema（這是正常的，但會觸發警告）

### 修復內容

已創建 `003_fix_security_issues.sql` migration，包含：

1. ✅ 為 `agent_tasks` 啟用 RLS 並添加策略
2. ✅ 重新創建 `update_updated_at_column()` 函數，添加 `SECURITY DEFINER` 和明確的 `search_path`
3. ✅ 重新創建所有觸發器
4. ✅ 確保所有 Knowledge Graph 表格的 RLS 都已啟用
5. ✅ 添加完整的 RLS 策略（Service role + Authenticated users）

---

## 🚀 執行修復（一鍵命令）

### 方式 A: 自動執行腳本（推薦）⭐

```bash
cd ~/repos/morningai && \
source .venv/bin/activate && \
export $(cat .env | grep -v '^#' | grep -v '^$' | xargs) && \
python3 agents/dev_agent/migrations/run_security_fix.py
```

**預期輸出**:
```
======================================================================
Security Fix Migration
Fixing issues detected by Supabase Security Advisor
======================================================================

--- Connecting to Database ---
✓ Connected successfully

--- Executing Security Fixes ---
✓ Security fixes applied successfully!

--- Verifying RLS Status ---
  agent_tasks: ✓ ENABLED
  code_embeddings: ✓ ENABLED
  code_patterns: ✓ ENABLED
  code_relationships: ✓ ENABLED
  embedding_cache_stats: ✓ ENABLED

--- Verifying RLS Policies ---
  agent_tasks: 6 policies
  code_embeddings: 5 policies
  code_patterns: 5 policies
  code_relationships: 5 policies
  embedding_cache_stats: 4 policies

======================================================================
✓ All security fixes applied successfully!
======================================================================
```

### 方式 B: 手動執行 SQL（備選）

1. 打開 Supabase Dashboard > SQL Editor
2. 複製 `agents/dev_agent/migrations/003_fix_security_issues.sql` 的內容
3. 執行 SQL

---

## ✅ 驗證修復

### Step 1: 執行修復腳本（上面的命令）

### Step 2: 刷新 Supabase Security Advisor

1. 前往 Supabase Dashboard
2. 點擊左側導航 **Advisors** > **Security Advisor**
3. 點擊右上角 **Refresh** 按鈕
4. 等待掃描完成（約 10-30 秒）

### Step 3: 確認結果

✅ **預期結果**:
- **Errors**: 0（所有 RLS 錯誤應該消失）
- **Warnings**: 可能還有 1 個（vector extension in public schema）
  - 這是正常的，pgvector 必須安裝在 public schema

⚠️ **如果 vector extension 警告仍然存在**:
- 這是**安全的**，可以忽略
- pgvector 擴展必須在 public schema 中才能正常工作
- Supabase 會對所有 public schema 擴展發出警告，這是預期行為

---

## 📋 修復後的安全配置

### RLS 策略摘要

每個表格都有以下策略：

1. **Service Role** (Backend API):
   - 完全訪問權限（SELECT, INSERT, UPDATE, DELETE）
   - 用於後端應用程序

2. **Authenticated Users** (已登入用戶):
   - SELECT: ✅ 允許讀取
   - INSERT: ✅ 允許插入
   - UPDATE: ✅ 允許更新
   - DELETE: ✅ 允許刪除（部分表格）

3. **Anonymous Users** (未登入):
   - ❌ 無訪問權限

### 函數安全配置

```sql
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER 
SECURITY DEFINER              -- 使用函數所有者權限執行
SET search_path = public, pg_temp  -- 明確指定搜索路徑
AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;
```

**說明**:
- `SECURITY DEFINER`: 防止權限升級攻擊
- `SET search_path`: 防止 schema 注入攻擊

---

## 🎯 下一步

修復完成後：

1. ✅ Supabase 安全問題解決
2. ✅ Week 5 完整部署完成
3. 🚀 可以開始 Week 6: Bug Fix Workflow

---

## 📞 如需協助

如果遇到問題：

1. **連接錯誤**: 確認 `.env` 中的 `SUPABASE_URL` 和 `SUPABASE_DB_PASSWORD` 正確
2. **權限錯誤**: 確認使用的是 `service_role` key 而非 `anon` key
3. **SQL 錯誤**: 檢查 Supabase 版本是否支持所有 SQL 語法

---

**報告生成**: 2025-10-17  
**作者**: Devin (CTO)  
**批准**: Ryan Chen (Project Owner)
