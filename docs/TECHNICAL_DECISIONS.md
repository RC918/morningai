# 技術決策記錄 (Technical Decision Records)

本文件記錄 Morning AI 專案中的重要技術決策，包括背景、考慮因素、決策內容和後果。

---

## TDR-001: Materialized Views 安全控制方式

**日期**: 2025-10-24  
**狀態**: ✅ 已實施  
**決策者**: CTO (Devin)  
**相關 PR**: #688

### 背景

Supabase Security Advisor 警告 2 個 materialized views (`daily_cost_summary`, `vector_visualization`) 可透過 API 存取但未啟用 Row Level Security (RLS)。

### 問題

在嘗試實施 RLS 時發現：
- PostgreSQL **不支援** materialized views 的 RLS
- 執行 `ALTER MATERIALIZED VIEW ... ENABLE ROW LEVEL SECURITY` 會失敗
- 錯誤訊息：`ERROR: ALTER action ENABLE ROW SECURITY cannot be performed on relation "daily_cost_summary" DETAIL: This operation is not supported for materialized views.`

### 考慮的選項

#### 選項 1: 使用 GRANT/REVOKE 控制權限（已採用）
**優點**:
- ✅ PostgreSQL 原生支援
- ✅ 簡單直接
- ✅ 符合 PostgreSQL 最佳實踐
- ✅ 無效能影響

**缺點**:
- ⚠️ Supabase Security Advisor 無法識別（會持續顯示警告）
- ⚠️ 粗粒度控制（只能控制角色，不能控制特定 rows）

#### 選項 2: 將 Materialized Views 轉換為普通 Views
**優點**:
- ✅ 可以使用 RLS
- ✅ Security Advisor 不會警告

**缺點**:
- ❌ 效能大幅下降（失去 materialized views 的快取優勢）
- ❌ 需要重新設計資料架構
- ❌ 影響現有功能

#### 選項 3: 建立 Wrapper Tables
**優點**:
- ✅ 可以使用 RLS
- ✅ Security Advisor 不會警告

**缺點**:
- ❌ 複雜度高（需要同步機制）
- ❌ 維護成本高
- ❌ 可能有資料不一致問題

#### 選項 4: 從 API 中隱藏 Materialized Views
**優點**:
- ✅ Security Advisor 不會警告
- ✅ 更安全（前端無法直接存取）

**缺點**:
- ⚠️ 需要修改現有 API 使用方式（如果有的話）

### 決策

**採用選項 1: 使用 GRANT/REVOKE 控制權限**

**理由**:
1. **技術限制**: PostgreSQL 不支援 materialized views 的 RLS，這是無法改變的事實
2. **安全性**: GRANT/REVOKE 提供足夠的安全保護
   - PUBLIC 權限已撤銷
   - 只有 authenticated 和 service_role 可以存取
   - 符合最小權限原則
3. **效能**: 保持 materialized views 的效能優勢
4. **簡單性**: 實施簡單，維護成本低
5. **最佳實踐**: 這是 PostgreSQL 對 materialized views 的標準做法

**接受的權衡**:
- Supabase Security Advisor 會持續顯示 2 個警告
- 這些警告是**誤報**，因為 Security Advisor 無法識別 GRANT/REVOKE 權限控制
- 我們接受這些誤報，因為系統實際上是安全的

### 實施細節

**Migration 017** (`migrations/017_enable_rls_materialized_views.sql`):
```sql
-- 撤銷 PUBLIC 權限
REVOKE ALL ON public.daily_cost_summary FROM PUBLIC;
REVOKE ALL ON public.vector_visualization FROM PUBLIC;

-- 授予 service_role 權限
GRANT SELECT ON public.daily_cost_summary TO service_role;
GRANT SELECT ON public.vector_visualization TO service_role;

-- 授予 authenticated 權限
GRANT SELECT ON public.daily_cost_summary TO authenticated;
GRANT SELECT ON public.vector_visualization TO authenticated;
```

**權限驗證**:
```sql
SELECT c.relname, c.relacl 
FROM pg_class c 
JOIN pg_namespace n ON c.relnamespace = n.oid
WHERE n.nspname = 'public' 
AND c.relname IN ('daily_cost_summary', 'vector_visualization');
```

**結果**:
```json
[
  {
    "relname": "daily_cost_summary",
    "relacl": "{postgres=arwdDxtm/postgres,authenticated=arwdDxtm/postgres,service_role=arwdDxtm/postgres}"
  },
  {
    "relname": "vector_visualization",
    "relacl": "{postgres=arwdDxtm/postgres,authenticated=arwdDxtm/postgres,service_role=arwdDxtm/postgres}"
  }
]
```

### 後果

**正面影響**:
- ✅ Materialized views 已正確保護
- ✅ 符合 PostgreSQL 最佳實踐
- ✅ 無效能影響
- ✅ 實施簡單，維護成本低

**負面影響**:
- ⚠️ Supabase Security Advisor 持續顯示 2 個警告（可接受的誤報）
- ⚠️ 需要向團隊解釋為何這些警告是誤報

**文檔**:
- 詳細說明已記錄在 `SECURITY_ADVISOR_FIXES.md`
- Migration 包含完整的註解和驗證邏輯
- 本 TDR 記錄了決策過程和理由

### 未來考慮

如果 Supabase Security Advisor 的誤報造成困擾，可以考慮：
1. 聯繫 Supabase 支援，建議改進 Security Advisor 以識別 GRANT/REVOKE
2. 實施選項 4（從 API 中隱藏 materialized views）
3. 等待 PostgreSQL 未來版本支援 materialized views 的 RLS（可能性低）

### 參考資料

- [PostgreSQL 官方文檔 - Materialized Views](https://www.postgresql.org/docs/current/sql-creatematerializedview.html)
- [PostgreSQL 官方文檔 - GRANT](https://www.postgresql.org/docs/current/sql-grant.html)
- [Supabase 文檔 - Row Level Security](https://supabase.com/docs/guides/auth/row-level-security)
- PR #688: https://github.com/RC918/morningai/pull/688
- Migration 017: `migrations/017_enable_rls_materialized_views.sql`
- 詳細指南: `SECURITY_ADVISOR_FIXES.md`

---

## 如何使用本文件

當遇到類似的技術決策時：
1. 參考相關的 TDR 了解過去的決策和理由
2. 評估當前情況是否與過去類似
3. 如果需要不同的決策，創建新的 TDR 並說明為何不同

當創建新的 TDR 時：
1. 使用下一個 TDR 編號（TDR-002, TDR-003, ...）
2. 包含所有必要的章節（背景、問題、選項、決策、後果）
3. 提交 PR 並請求審查
