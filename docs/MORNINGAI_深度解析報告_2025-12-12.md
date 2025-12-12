# MorningAI 深度解析報告

**報告日期**: 2025年12月12日  
**最新提交**: `26c16705` (feat: add DISABLE_SENTRY_FOR_TESTS env var and production protection)  
**自上次報告 (2025-11-20) 以來**: 467 個新提交  
**分析範圍**: RC918/morningai 完整代碼庫

---

## 一、專案現況總覽

MorningAI 是一個高度成熟的自主 AI 代理編排平台，專為軟體開發自動化設計。專案採用微服務架構，支援多租戶 SaaS 模式，具備完整的安全治理機制。

### 代碼規模統計

| 組件 | 檔案數 | 代碼行數 | 主要語言 |
|------|--------|----------|----------|
| Orchestrator | 94+ | 94,676 | Python |
| API Backend | 27 routes | ~15,000 | Python |
| Owner Console | 12 dirs | ~8,000 | TypeScript/React |
| Frontend Dashboard | - | ~6,000 | TypeScript/React |
| Migrations | 38 | ~7,500 | SQL |
| **總計** | 2,332 py + 364 ts/tsx | **~130,000+** | - |

### 技術棧

**後端**: Python 3.11+, FastAPI, Flask, Pydantic, Redis Queue (RQ), PostgreSQL, Supabase  
**前端**: React 18, TypeScript, Vite, TailwindCSS, Zustand  
**基礎設施**: Render (Backend), Vercel (Frontend), Supabase (DB), Upstash (Redis), Sentry (Monitoring)  
**AI/LLM**: OpenAI GPT-4, Google Gemini, LangGraph  
**工具鏈**: pnpm workspaces, Turbo, Husky, pytest

---

## 二、近期重大變更 (2025-11-20 至 2025-12-12)

### 2.1 新增功能 (按組件分類)

#### Orchestrator (48 commits)

| 功能 | Issue/PR | 說明 |
|------|----------|------|
| **Auto-Fix 執行系統** | #2251, #2252, #2337 | 從 AI reviewer 評論自動執行修復，含安全機制 |
| **Session Command 處理** | #2242, #2318, #2321-2324 | 並發安全的 session 命令處理，整合 worker.py |
| **Multi-Signal Trigger** | #2213, #2275 | 多信號觸發系統，支援複合條件 |
| **LangGraph Rollout Tracker** | #2214, #2278, #2280, #2284 | 100% rollout 追蹤器，整合 worker.py |
| **AI Reviewer 速率限制** | #2253, #2327 | 防止 API 過載的速率限制機制 |
| **Review Follow-up Mode** | #2211, #2257 | 審查後續追蹤模式 |
| **Internal Reviewer Re-review** | #2212, #2262 | 內部審查員重新審查機制 |
| **Comment Triage Agent** | #2246 | AI reviewer 評論分類代理 |
| **Failure Learning Enhancement** | #2124, #2126, #2231 | Wave 3 失敗學習增強 |

#### Owner Console (51 commits)

| 功能 | Issue/PR | 說明 |
|------|----------|------|
| **SessionStatusCard** | #2279 | 標準化設計規範的 session 狀態卡片 |
| **SessionCommandInput** | #1823, #2175 | 互動式 session 命令輸入 |
| **Command History** | #2180, #2189 | localStorage 持久化命令歷史 |

#### API Backend

| 功能 | Issue/PR | 說明 |
|------|----------|------|
| **/metrics 端點** | Epic #2311, #2329 | JSON 和 Prometheus 格式的指標端點 |
| **/sessions/{id}/command** | #2179, #2184, #2317 | Session 命令 API，含快速命令 ID 驗證 |
| **RLS Phase 2 驗證** | #2310 | RLS 驗證基礎設施 |

#### 安全與治理

| 功能 | Issue/PR | 說明 |
|------|----------|------|
| **TRUE Tenant Isolation** | Migration 006 | 真正的租戶隔離 RLS policies |
| **DISABLE_SENTRY_FOR_TESTS** | #2336 | 測試環境 Sentry 控制，生產環境保護 |

### 2.2 架構變更

#### 新增模組

```
orchestrator/
├── utils/
│   ├── auto_fix_executor.py    # Auto-fix 執行器
│   ├── auto_fix_policy.py      # Auto-fix 政策 (724 行)
│   ├── rate_limit.py           # 速率限制
│   └── retry.py                # 重試邏輯
├── deepwiki/                   # DeepWiki 知識庫整合
├── meta_agent/                 # Meta Agent (VM 支援)
└── webhooks/
    └── review_follow_up.py     # 審查後續追蹤
```

#### 新增 API 路由

```
api-backend/src/routes/
├── metrics.py          # /metrics 端點 (309 行)
├── action_requests.py  # Action requests API
└── deepwiki.py         # DeepWiki API
```

---

## 三、環境變數與配置

### 3.1 新增環境變數 (自 2025-11-20)

#### Auto-Fix 系統

| 變數 | 預設值 | 說明 |
|------|--------|------|
| `AUTO_FIX_ENABLED` | false | Auto-fix 主開關 |
| `AUTO_FIX_CATEGORIES` | "style,documentation" | 允許的修復類別 |
| `AUTO_FIX_REPOS_ALLOWLIST` | "" | 允許的 repo 清單 |
| `AUTO_FIX_MAX_RETRIES` | 3 | 每 PR 最大重試次數 |
| `AUTO_FIX_PER_REPO_PER_HOUR` | 10 | 每 repo 每小時限制 |
| `AUTO_FIX_PER_PR_PER_HOUR` | 3 | 每 PR 每小時限制 |
| `AUTO_FIX_GLOBAL_PER_HOUR` | 100 | 全局每小時限制 |
| `AUTO_FIX_CANARY_PERCENT` | 10 | Canary rollout 百分比 |

#### Meta Agent

| 變數 | 預設值 | 說明 |
|------|--------|------|
| `ENABLE_META_AGENT` | false | Meta Agent 開關 |
| `ENABLE_META_AGENT_VM` | false | Meta Agent VM 模式 |

#### 監控與測試

| 變數 | 預設值 | 說明 |
|------|--------|------|
| `DISABLE_SENTRY_FOR_TESTS` | false | 測試環境禁用 Sentry |
| `REDIS_HOST` | localhost | Redis fallback host |
| `REDIS_PORT` | 6379 | Redis fallback port |
| `REDIS_DB` | 0 | Redis fallback database |

### 3.2 配置檔案

- **env.schema.yaml**: 2,231 行，142 個變數定義
- **settings.py**: 1,790 行，完整的 Pydantic 配置類

---

## 四、資料庫與遷移

### 4.1 遷移檔案 (38 個)

| 遷移 | 說明 | 狀態 |
|------|------|------|
| 001-005 | 基礎 RLS 設置 | 已部署 |
| **006** | TRUE Tenant Isolation | **已部署 (2025-12-12)** |
| 007-008 | Function/Extension 安全修復 | 已部署 |
| 009-020 | 各表 RLS 政策 | 已部署 |
| 021-038 | 功能表和安全修復 | 已部署 |

### 4.2 RLS 政策現況

**Staging & Production (2025-12-12 部署)**:

| Policy | Roles | 用途 |
|--------|-------|------|
| `anon_no_access` | anon | 阻擋匿名存取 |
| `service_role_all_access` | service_role | Service key 存取 |
| `true_tenant_isolation_read` | authenticated | 租戶隔離 SELECT |
| `true_tenant_isolation_insert` | authenticated | 租戶隔離 INSERT |
| `true_tenant_isolation_update` | authenticated | 租戶隔離 UPDATE |
| `true_tenant_isolation_delete` | authenticated | 租戶隔離 DELETE |

---

## 五、Orchestrator 架構

### 5.1 核心模組

```
orchestrator/
├── langgraph_orchestrator.py   # 主編排器 (134,768 行)
├── graph.py                    # LangGraph 圖定義
├── llm_planner_adapter.py      # LLM Planner 適配器
├── llm_reviewer_adapter.py     # LLM Reviewer 適配器
├── observer_node.py            # Observer 節點
├── rollout_tracker.py          # Rollout 追蹤器
├── experiment_manager.py       # 實驗管理器
├── experiment_metrics.py       # 實驗指標
├── orchestrator_metrics.py     # Orchestrator 指標
├── failure_recorder.py         # 失敗記錄器
├── failure_memory.py           # 失敗記憶
└── agent_eval_integration.py   # Agent 評估整合
```

### 5.2 Agent 子系統

| Agent | 目錄 | 功能 |
|-------|------|------|
| **Meta Agent** | meta_agent/ | 高層任務規劃 |
| **PM Agent** | pm_agent/ | 專案管理 |
| **Ops Agent** | ops_agent/ | 運維操作 |
| **Security Agent** | security_agent/ | 安全審查 |
| **Refactor Agent** | refactor_agent/ | 代碼重構 |
| **Project Engineer** | project_engineer/ | 代碼生成 |
| **Governance Agent** | governance_agent/ | 治理決策 |

### 5.3 Feature Flags 控制

| Flag | 預設 | 說明 |
|------|------|------|
| `USE_LANGGRAPH` | false | LangGraph 模式 |
| `USE_LANGGRAPH_PERCENT` | 0 | LangGraph 流量百分比 |
| `USE_LLM_PLANNER` | false | LLM Planner |
| `USE_LLM_REVIEWER` | false | LLM Reviewer |
| `USE_CODE_GENERATION` | false | 代碼生成 |
| `ENABLE_PROJECT_ENGINEER_CODEGEN` | false | ProjectEngineer 代碼生成 |
| `ENABLE_PROJECT_ENGINEER_FIXER` | false | ProjectEngineer 自動修復 |
| `REASONING_MODE_ENABLED` | false | Gemini 深度思考模式 |
| `DISABLE_GEMINI3` | false | Gemini 3 緊急開關 |

---

## 六、API 端點

### 6.1 主要路由 (27 個)

| 路由檔案 | 端點 | 功能 |
|----------|------|------|
| auth.py | /auth/* | 基礎認證 |
| auth_2fa.py | /auth/2fa/* | 雙因素認證 |
| auth_enhanced.py | /auth/enhanced/* | 增強認證 |
| sessions.py | /sessions/* | Session 管理 |
| agent.py | /agent/* | Agent 操作 |
| metrics.py | /metrics | 指標端點 |
| webhooks.py | /webhooks/* | Webhook 處理 |
| governance.py | /governance/* | 治理 API |
| experiments.py | /experiments/* | 實驗 API |
| deepwiki.py | /deepwiki/* | DeepWiki API |
| faq.py | /faq/* | FAQ 向量搜索 |
| vectors.py | /vectors/* | 向量操作 |

### 6.2 新增端點 (2025-11-20 後)

```
GET  /metrics                    # JSON/Prometheus 指標
POST /sessions/{id}/command      # Session 命令
GET  /sessions/{id}/command/{cmd_id}  # 命令狀態
```

---

## 七、前端架構

### 7.1 Owner Console

```
owner-console/src/
├── components/
│   ├── SessionStatusCard/      # Session 狀態卡片
│   ├── SessionCommandInput/    # 命令輸入
│   └── ...
├── pages/
├── stores/                     # Zustand stores
├── hooks/
├── lib/
└── utils/
```

### 7.2 Frontend Dashboard

```
frontend-dashboard/src/
├── components/
├── pages/
├── stores/
└── utils/
```

---

## 八、測試與 CI/CD

### 8.1 測試配置

- **pytest.ini**: 根目錄、api-backend、agents 各有配置
- **測試覆蓋率**: 持續改進中 (#2330)

### 8.2 CI 工作流

- GitHub Actions 自動化測試
- Vercel Preview 部署
- Render 自動部署

---

## 九、部署狀態

### 9.1 環境配置

| 環境 | 後端 | 前端 | 資料庫 |
|------|------|------|--------|
| **Production** | Render | Vercel | Supabase |
| **Staging** | Render | Vercel | Supabase |

### 9.2 最新部署 (2025-12-12)

| 環境 | 程式碼版本 | RLS 狀態 | 危險 Flag |
|------|-----------|----------|-----------|
| Staging | 26c16705 | TRUE tenant isolation | 全部關閉 |
| Production | 26c16705 | TRUE tenant isolation | 全部關閉 |

---

## 十、Epic #2311 進度

### 10.1 Phase 狀態

| Phase | 名稱 | 狀態 | 完成項目 |
|-------|------|------|----------|
| Phase 0 | Foundation | 完成 | 5/5 |
| Phase 1 | Core | 完成 | 7/7 |
| Phase 2 | Integration | 進行中 | 2/6 |
| Phase 3 | Governance | 待開始 | 1/12 |
| Phase 4 | LangGraph Rollout | 待開始 | 0/10 |

### 10.2 已完成的關鍵項目

- /metrics 端點 (JSON + Prometheus)
- Session command 處理
- RLS TRUE tenant isolation
- Auto-fix 安全機制

---

## 十一、風險與建議

### 11.1 已解決的風險

| 風險 | 狀態 | 解決方案 |
|------|------|----------|
| 硬編碼路徑 | 已修復 | 使用環境變數 + 動態檢測 |
| Token 估算 | 已優化 | 支援 tiktoken |
| Redis 回退 | 已強化 | 強制 TLS + 明確錯誤處理 |
| RLS 寬鬆政策 | 已修復 | TRUE tenant isolation |

### 11.2 待處理項目

| 項目 | 優先級 | 建議 |
|------|--------|------|
| Epic #2311 Phase 2-4 | 高 | 繼續推進 |
| Qwen3 遷移 | 中 | Epic 完成後開始 |
| TypeScript Strict Mode | 低 | 持續清零 |

---

## 十二、下一步建議

1. **繼續 Epic #2311** - 完成 Phase 2 Integration 剩餘工作
2. **監控部署** - 觀察 1-2 天確認無異常
3. **Qwen3 遷移** - 可在 Epic #2311 完成後開始 Phase A
4. **漸進式功能啟用** - 先在單一 repo 啟用 auto-fix

---

## 附錄：關鍵檔案參考

| 檔案 | 路徑 | 說明 |
|------|------|------|
| 設定類 | common/config/settings.py | 1,790 行 |
| 環境 Schema | config/env.schema.yaml | 2,231 行 |
| 主編排器 | orchestrator/langgraph_orchestrator.py | 134,768 行 |
| Auto-fix 政策 | orchestrator/utils/auto_fix_policy.py | 724 行 |
| Metrics 端點 | api-backend/src/routes/metrics.py | 309 行 |
| RLS 遷移 | migrations/006_update_rls_policies_true_tenant_isolation.sql | 315 行 |

---

*報告生成時間: 2025-12-12 04:20 UTC*
