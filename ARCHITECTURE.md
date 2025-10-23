# MorningAI 架構設計文檔

## 概述

MorningAI 採用**三層分離架構**，確保 Owner 和租戶的權限明確分割，提供安全、可擴展的多租戶 AI 平台。

## 架構原則

### 1. Owner/Admin Console - 獨立管理界面

**目的**: 為平台 Owner 提供獨立的管理控制台，用於控制 agents 和設置策略。

**特性**:
- 完全獨立的前端應用
- 僅 `role: 'Owner'` 的用戶可訪問
- 獨立的認證機制 (`owner_auth_token`)
- 獨立的部署 URL (例如 `admin.morningai.com`)

**功能模塊**:
- **Agent Governance**: 監控 agent 信譽、權限級別、合規性
- **Tenant Management**: 管理租戶賬戶、權限、配額
- **System Monitoring**: 監控系統健康狀況、性能指標
- **Platform Settings**: 配置平台級設置、安全策略

### 2. Tenant Dashboard - 租戶使用界面

**目的**: 為租戶用戶提供使用 agents 和查看自己數據的界面。

**特性**:
- 租戶用戶可訪問
- 基於租戶的數據隔離 (RLS)
- 租戶認證機制 (`auth_token`)
- 獨立的部署 URL (例如 `dashboard.morningai.com`)

**功能模塊**:
- **Dashboard**: 租戶數據概覽
- **Strategies**: 策略管理
- **Approvals**: 決策審批
- **History**: 歷史分析
- **Costs**: 成本分析

### 3. 權限分離 - Owner 和租戶有不同的訪問權限

**目的**: 確保 Owner 和租戶的數據和功能完全隔離。

**實現方式**:
- **Row Level Security (RLS)**: PostgreSQL 行級安全策略
- **API 權限驗證**: 基於 JWT token 的角色驗證
- **前端路由保護**: 基於用戶角色的路由訪問控制

## 系統架構圖

```
┌─────────────────────────────────────────────────────────────────┐
│                        用戶層                                    │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────────────┐         ┌──────────────────────┐     │
│  │   Owner Console      │         │  Tenant Dashboard    │     │
│  │  (admin.morningai)   │         │ (dashboard.morningai)│     │
│  ├──────────────────────┤         ├──────────────────────┤     │
│  │ • Agent Governance   │         │ • Dashboard          │     │
│  │ • Tenant Management  │         │ • Strategies         │     │
│  │ • System Monitoring  │         │ • Approvals          │     │
│  │ • Platform Settings  │         │ • History            │     │
│  └──────────┬───────────┘         └──────────┬───────────┘     │
│             │                                 │                  │
└─────────────┼─────────────────────────────────┼─────────────────┘
              │                                 │
              │ owner_auth_token                │ auth_token
              │ (Owner role)                    │ (Tenant role)
              │                                 │
              ▼                                 ▼
┌─────────────────────────────────────────────────────────────────┐
│                        API 層                                    │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │              API Backend (FastAPI)                        │  │
│  │         (morningai-backend-v2.onrender.com)              │  │
│  ├──────────────────────────────────────────────────────────┤  │
│  │                                                           │  │
│  │  Owner Endpoints:          Tenant Endpoints:             │  │
│  │  • /api/governance/*       • /api/dashboard/*            │  │
│  │  • /api/tenants/*          • /api/strategies/*           │  │
│  │  • /api/monitoring/*       • /api/approvals/*            │  │
│  │  • /api/platform/*         • /api/history/*              │  │
│  │                            • /api/costs/*                │  │
│  │                                                           │  │
│  │  權限驗證:                                                │  │
│  │  • JWT Token 驗證                                         │  │
│  │  • 角色檢查 (Owner vs Tenant)                            │  │
│  │  • RLS Policy 執行                                        │  │
│  └──────────────────────┬───────────────────────────────────┘  │
│                         │                                       │
└─────────────────────────┼───────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│                        數據層                                    │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │           Supabase PostgreSQL Database                    │  │
│  ├──────────────────────────────────────────────────────────┤  │
│  │                                                           │  │
│  │  Tables:                                                  │  │
│  │  • tenants                    (RLS: tenant_id)            │  │
│  │  • users                      (RLS: tenant_id)            │  │
│  │  • agents                     (RLS: tenant_id)            │  │
│  │  • agent_reputation           (RLS: tenant_id)            │  │
│  │  • agent_reputation_events    (RLS: tenant_id)            │  │
│  │  • governance_violations      (RLS: tenant_id)            │  │
│  │  • strategies                 (RLS: tenant_id)            │  │
│  │  • decisions                  (RLS: tenant_id)            │  │
│  │  • costs                      (RLS: tenant_id)            │  │
│  │                                                           │  │
│  │  RLS Policies:                                            │  │
│  │  • Owner: 可以訪問所有租戶的數據                          │  │
│  │  • Tenant: 只能訪問自己租戶的數據                         │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## 權限模型

### 角色定義

```typescript
enum UserRole {
  Owner = 'Owner',      // 平台所有者，可以訪問所有功能
  Admin = 'Admin',      // 租戶管理員，可以管理租戶內的用戶和設置
  User = 'User'         // 普通租戶用戶，可以使用 agents 和查看數據
}
```

### 權限矩陣

| 功能 | Owner | Admin | User |
|------|-------|-------|------|
| **Owner Console** |
| Agent Governance | ✅ | ❌ | ❌ |
| Tenant Management | ✅ | ❌ | ❌ |
| System Monitoring | ✅ | ❌ | ❌ |
| Platform Settings | ✅ | ❌ | ❌ |
| **Tenant Dashboard** |
| Dashboard | ✅ (所有租戶) | ✅ (自己租戶) | ✅ (自己租戶) |
| Strategies | ✅ (所有租戶) | ✅ (自己租戶) | ✅ (自己租戶) |
| Approvals | ✅ (所有租戶) | ✅ (自己租戶) | ✅ (自己租戶) |
| History | ✅ (所有租戶) | ✅ (自己租戶) | ✅ (自己租戶) |
| Costs | ✅ (所有租戶) | ✅ (自己租戶) | ✅ (自己租戶) |
| Tenant Settings | ✅ (所有租戶) | ✅ (自己租戶) | ❌ |

### RLS 策略示例

```sql
-- Owner 可以訪問所有數據
CREATE POLICY "owner_all_access" ON agents
  FOR ALL
  USING (
    EXISTS (
      SELECT 1 FROM users
      WHERE users.id = auth.uid()
      AND users.role = 'Owner'
    )
  );

-- 租戶用戶只能訪問自己租戶的數據
CREATE POLICY "tenant_own_data" ON agents
  FOR ALL
  USING (
    tenant_id = (
      SELECT tenant_id FROM users
      WHERE users.id = auth.uid()
    )
  );
```

## 認證流程

### Owner Console 認證

```
1. 用戶訪問 admin.morningai.com/login
2. 輸入 Owner 憑證
3. Backend 驗證憑證並檢查 role = 'Owner'
4. 返回 JWT token (owner_auth_token)
5. Frontend 存儲 token 並重定向到 /dashboard
6. 所有 API 請求帶上 Authorization: Bearer {owner_auth_token}
7. Backend 驗證 token 並檢查 Owner 權限
```

### Tenant Dashboard 認證

```
1. 用戶訪問 dashboard.morningai.com/login
2. 輸入租戶憑證
3. Backend 驗證憑證並獲取 tenant_id
4. 返回 JWT token (auth_token) 包含 tenant_id
5. Frontend 存儲 token 並重定向到 /dashboard
6. 所有 API 請求帶上 Authorization: Bearer {auth_token}
7. Backend 驗證 token 並應用 RLS 策略
```

## API 端點設計

### Owner 專屬端點

```
GET    /api/governance/agents              # 獲取所有 agents 的信譽數據
GET    /api/governance/events              # 獲取信譽事件
GET    /api/governance/violations          # 獲取違規記錄
GET    /api/governance/statistics          # 獲取統計數據

GET    /api/tenants                        # 獲取所有租戶
POST   /api/tenants                        # 創建新租戶
GET    /api/tenants/{tenant_id}            # 獲取租戶詳情
PUT    /api/tenants/{tenant_id}            # 更新租戶
DELETE /api/tenants/{tenant_id}            # 刪除租戶

GET    /api/monitoring/health              # 系統健康狀況
GET    /api/monitoring/metrics             # 性能指標
GET    /api/monitoring/logs                # 系統日誌

GET    /api/platform/settings              # 平台設置
PUT    /api/platform/settings              # 更新平台設置
```

### 租戶端點

```
GET    /api/dashboard/stats                # 租戶 Dashboard 統計
GET    /api/strategies                     # 租戶策略
POST   /api/strategies                     # 創建策略
GET    /api/approvals                      # 待審批決策
POST   /api/approvals/{decision_id}/approve # 審批決策
GET    /api/history                        # 歷史記錄
GET    /api/costs                          # 成本分析
```

## 部署架構

### 前端部署

```
Owner Console:
  - URL: https://admin.morningai.com
  - Platform: Vercel / Netlify
  - Build: npm run build (Vite)
  - Env: VITE_API_BASE_URL, VITE_OWNER_CONSOLE=true

Tenant Dashboard:
  - URL: https://dashboard.morningai.com
  - Platform: Vercel / Netlify
  - Build: npm run build (Vite)
  - Env: VITE_API_BASE_URL, VITE_OWNER_CONSOLE=false
```

### 後端部署

```
API Backend:
  - URL: https://morningai-backend-v2.onrender.com
  - Platform: Render.com
  - Runtime: Python 3.12 (FastAPI)
  - Database: Supabase PostgreSQL
  - Env: DATABASE_URL, JWT_SECRET, SUPABASE_URL, SUPABASE_KEY
```

## 安全考慮

### 1. 認證安全

- 使用 JWT token 進行認證
- Token 包含用戶 ID、角色、租戶 ID
- Token 有效期：30 天（可配置）
- 支持 Token 刷新機制

### 2. 授權安全

- 所有 API 端點都需要驗證 token
- Owner 端點額外檢查 `role = 'Owner'`
- 租戶端點應用 RLS 策略確保數據隔離

### 3. 數據安全

- 所有敏感數據加密存儲
- 使用 HTTPS 傳輸
- RLS 策略防止跨租戶數據訪問
- 定期備份數據庫

### 4. 前端安全

- 不在前端存儲敏感信息
- Token 存儲在 localStorage（考慮使用 httpOnly cookie）
- XSS 防護（React 自動轉義）
- CSRF 防護（使用 CORS 策略）

## 擴展性考慮

### 1. 水平擴展

- 前端：靜態資源，可以通過 CDN 擴展
- 後端：無狀態 API，可以通過負載均衡器擴展
- 數據庫：Supabase 提供自動擴展

### 2. 功能擴展

- 新增 Owner Console 功能：在 `owner-console/src/pages/` 添加新頁面
- 新增 Tenant Dashboard 功能：在 `frontend-dashboard/src/components/` 添加新組件
- 新增 API 端點：在 `api-backend/src/routes/` 添加新路由

### 3. 多租戶擴展

- 支持無限數量的租戶
- 每個租戶的數據完全隔離
- 可以為不同租戶設置不同的配額和權限

## 監控和日誌

### 1. 前端監控

- Sentry 錯誤追蹤
- Google Analytics 用戶行為分析
- 性能監控（Core Web Vitals）

### 2. 後端監控

- API 響應時間監控
- 錯誤率監控
- 數據庫查詢性能監控

### 3. 日誌記錄

- 所有 API 請求記錄
- 錯誤日誌記錄
- 審計日誌（Owner 操作記錄）

## 開發工作流

### 1. 本地開發

```bash
# Owner Console
cd handoff/20250928/40_App/owner-console
npm install
npm run dev  # http://localhost:5173

# Tenant Dashboard
cd handoff/20250928/40_App/frontend-dashboard
npm install
npm run dev  # http://localhost:5174

# API Backend
cd handoff/20250928/40_App/api-backend
poetry install
poetry run uvicorn app.main:app --reload  # http://localhost:8000
```

### 2. 測試

```bash
# Frontend 測試
npm run test

# Backend 測試
poetry run pytest

# E2E 測試
npm run test:e2e
```

### 3. 部署

```bash
# Frontend 構建
npm run build

# Backend 部署
git push origin main  # 自動觸發 Render 部署
```

## 相關文檔

- [Owner Console README](handoff/20250928/40_App/owner-console/README.md)
- [UX Design System](docs/UX/README.md)
- [API Documentation](handoff/20250928/40_App/30_API/openapi/)
- [Database Schema](migrations/)
- [Contributing Guide](docs/CONTRIBUTING.md)

## 更新歷史

- **2025-10-20**: 初始版本 - 創建獨立的 Owner Console 架構
- **2025-10-23**: PR #618 - 實現 Agent Governance 功能
- **2025-10-23**: PR #626 - 實現 RLS 監控測試
