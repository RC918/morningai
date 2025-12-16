# CI Workflow Matrix

本文檔詳細列出 Morning AI 專案的所有 GitHub Actions 工作流，包含其用途、觸發條件、是否為 Branch Protection 必須檢查，以及 workflow_dispatch 支援狀態。

## 📊 總覽統計

- **總工作流數量**: 25
- **支援 workflow_dispatch**: 23 (96%)
- **Branch Protection 必須檢查**: 4

---

## 🔴 Branch Protection 必須檢查 (Required)

這些工作流是 main 分支保護規則中的必須檢查項目，所有 PR 必須通過這些檢查才能合併。

### 1. `orchestrator-e2e` (run)
**檔案**: `.github/workflows/orchestrator-e2e.yml`

**用途**: Orchestrator 端到端測試，驗證 Agent 編排系統核心功能

**觸發條件**:
- ✅ `workflow_dispatch` - 手動觸發
- ✅ `push` - 任何分支推送
- ✅ `pull_request` - 所有 PR

**執行內容**:
- 安裝 Python 3.12.x 與 orchestrator 依賴
- 執行 orchestrator demo 腳本
- 驗證 Agent 編排邏輯正確性

**為何是 Required**: 確保 Agent 編排系統核心邏輯不被破壞

---

### 2. `post-deploy-health` (check)
**檔案**: `.github/workflows/post-deploy-health.yml`

**用途**: 部署後健康檢查，驗證生產環境 API 端點可用性

**觸發條件**:
- ✅ `workflow_dispatch` - 手動觸發
- ✅ `push` - main 分支推送
- ✅ `pull_request` - 所有 PR

**執行內容**:
- 檢查 Backend API 健康端點 (`/health`, `/api/health`)
- 驗證 Render 服務存活狀態
- 確認基本路由可訪問

**為何是 Required**: 確保部署不會破壞生產環境基本可用性

---

### 3. `post-deploy-health-assertions` (validate)
**檔案**: `.github/workflows/post-deploy-health-assertions.yml`

**用途**: 部署後斷言驗證，深度檢查生產環境功能完整性

**觸發條件**:
- ✅ `workflow_dispatch` - 手動觸發
- ✅ `push` - main 分支推送
- ✅ `schedule` - 每小時執行一次 (UTC 00:00)

**執行內容**:
- 驗證 Backend API 回應格式正確
- 檢查關鍵端點功能（認證、資料存取等）
- 斷言回應狀態碼與資料結構符合預期

**為何是 Required**: 確保生產環境功能完整性與資料正確性

---

### 4. `ops-agent-sandbox-e2e` (e2e-test)
**檔案**: `.github/workflows/ops-agent-sandbox-e2e.yml`

**用途**: Ops Agent Sandbox 端到端測試，驗證 Agent 沙箱隔離環境

**觸發條件**:
- ✅ `workflow_dispatch` - 手動觸發
- ✅ `push` - main 分支推送 (僅當 sandbox 相關檔案變更時)
- ✅ `pull_request` - 所有 PR (僅當 sandbox 相關檔案變更時，且非 draft PR)

**執行內容**:
- 部署臨時 Fly.io 沙箱環境 (ephemeral app)
- 安裝 Playwright 與 Python 依賴
- 啟動 MCP Server
- 執行沙箱隔離測試
- 自動清理臨時環境

**為何是 Required**: 確保 Agent 沙箱隔離機制正常運作，防止安全漏洞

**特殊機制**: 
- 僅在 sandbox 相關檔案變更時執行完整測試
- 未變更時自動跳過（節省 CI 資源與 Fly.io 費用）
- 使用 unique app name 避免部署衝突

---

## 🟢 重要但非 Required 的工作流

這些工作流提供重要的品質保證與部署功能，但不阻擋 PR 合併。

### 5. `backend-ci`
**檔案**: `.github/workflows/backend.yml`

**用途**: Backend 程式碼品質檢查、Ruff lint 與測試覆蓋率

**觸發條件**:
- ✅ `workflow_dispatch` - 手動觸發 (Phase 11 新增)
- ✅ `push` - 任何分支推送
- ✅ `pull_request` - 所有 PR

**執行內容**:
- **lint job** (blocking): 執行 Ruff linter 檢查 Python 程式碼品質
  - 使用 Ruff (10-100x faster than flake8)
  - 配置於 `pyproject.toml` [tool.ruff] section
  - Line length: 120 characters
  - Per-file-ignores 用於特殊情況 (migrations, tests, main.py)
- **validate-env-schema job**: 驗證環境變數 schema
- **validate-openapi-spec job**: 驗證 OpenAPI 規格
- **test job**: 執行 pytest 單元測試，測試覆蓋率檢查 (目前門檻: 80%)

**為何非 Required**: 測試覆蓋率已達 80%，但保持非 Required 以避免阻擋緊急修復

---

### 6. `frontend-ci`
**檔案**: `.github/workflows/frontend.yml`

**用途**: Frontend 程式碼品質檢查、建置與 lint

**觸發條件**:
- ✅ `workflow_dispatch` - 手動觸發 (Phase 11 新增)
- ✅ `push` - 任何分支推送
- ✅ `pull_request` - 所有 PR

**執行內容**:
- 安裝 Node.js 18 與 pnpm 依賴
- 執行前端建置 (`pnpm run build`)
- 執行 ESLint 檢查 (`pnpm run lint`)
- 執行煙測 (`pnpm run test:smoke`)

**為何非 Required**: Frontend 與 Backend 獨立部署，不影響後端穩定性

---

### 7. `openapi-verify` (lint)
**檔案**: `.github/workflows/openapi-verify.yml`

**用途**: OpenAPI 規格驗證，確保 API 契約正確性

**觸發條件**:
- ✅ `workflow_dispatch` - 手動觸發
- ✅ `push` - 任何分支推送
- ✅ `pull_request` - 所有 PR

**執行內容**:
- 安裝 `check-openapi-spec` 驗證工具
- 檢查 OpenAPI YAML/JSON 格式正確性
- 驗證 API 規格完整性

**為何非 Required**: API 規格驗證重要但不阻擋緊急修復部署

**注意**: 此工作流的 job 名稱為 `lint`，但並非 Branch Protection 的 `lint` 檢查（該檢查已移除）

---

### 8. `agent-mvp-smoke`
**檔案**: `.github/workflows/agent-mvp-smoke.yml`

**用途**: Agent MVP 煙測，快速驗證 Agent API 基本功能

**觸發條件**:
- ✅ `workflow_dispatch` - 手動觸發 (支援 `check_agent_faq` 參數)
- ✅ `push` - main 分支推送
- ✅ `pull_request` - main 分支 PR

**執行內容**:
- 執行 Agent MVP 基本功能測試
- 可選擇性測試 `/api/agent/faq` 端點
- 快速驗證 Agent API 可用性

**為何非 Required**: 煙測為快速驗證，完整 E2E 測試由其他工作流負責

---

### 9. `agent-mvp-e2e`
**檔案**: `.github/workflows/agent-mvp-e2e.yml`

**用途**: Agent MVP 端到端測試，完整驗證 Agent 工作流

**觸發條件**:
- ✅ `workflow_dispatch` - 手動觸發 (支援 `test_sentry` 參數)
- ✅ `push` - main 分支推送
- ✅ `pull_request` - main 分支 PR

**執行內容**:
- 完整 Agent MVP 端到端測試
- 驗證 FAQ → PR → CI → Merge 閉環
- 可選擇性測試 Sentry 整合

**為何非 Required**: E2E 測試較耗時，避免阻擋開發流程

---

### 10. `env-diagnose`
**檔案**: `.github/workflows/env-diagnose.yml`

**用途**: 多雲服務連線診斷，驗證所有第三方服務可用性

**觸發條件**:
- ✅ `workflow_dispatch` - 僅手動觸發

**執行內容**:
- 檢查 6 個關鍵服務連線狀態：
  - Supabase (Database)
  - Redis (Upstash)
  - Cloudflare (CDN)
  - Vercel (Frontend)
  - Render (Backend)
  - Sentry (Monitoring)
- 驗證環境變數配置正確性

**為何非 Required**: 診斷工具，僅在環境問題發生時手動觸發

---

### 11. `vercel-deploy`
**檔案**: `.github/workflows/vercel-deploy.yml`

**用途**: Vercel 前端部署，自動部署到生產環境

**觸發條件**:
- ✅ `workflow_dispatch` - 手動觸發
- ✅ `push` - main 分支推送
- ✅ `pull_request` - 所有 PR (預覽部署)

**執行內容**:
- 安裝 Vercel CLI
- 執行前端建置與部署
- PR 產生預覽 URL

**為何非 Required**: 前端部署失敗不影響後端服務

---

### 12. `fly-deploy` (Fly Deploy)
**檔案**: `.github/workflows/fly-deploy.yml`

**用途**: Fly.io Ops Agent Sandbox 部署

**觸發條件**:
- ✅ `workflow_dispatch` - 手動觸發
- ✅ `push` - main 分支推送 (僅當相關檔案變更時)

**執行內容**:
- 部署 Ops Agent Sandbox 到 Fly.io
- 更新生產環境沙箱版本

**為何非 Required**: 沙箱部署失敗不影響主系統運作

**並發控制**: 使用 `cancel-in-progress: false` 避免部署衝突

---

### 13. `sentry-smoke` (Sentry Smoke Test)
**檔案**: `.github/workflows/sentry-smoke.yml`

**用途**: Sentry 監控系統煙測

**觸發條件**:
- ✅ `workflow_dispatch` - 僅手動觸發 (支援 `environment` 參數)

**執行內容**:
- 發送測試事件到 Sentry
- 驗證 Sentry DSN 配置正確
- 確認監控系統正常運作

**為何非 Required**: 監控系統測試，不影響核心功能

---

### 14. `sentry-smoke-cron`
**檔案**: `.github/workflows/sentry-smoke-cron.yml`

**用途**: Sentry 監控系統定時健康檢查

**觸發條件**:
- ✅ `workflow_dispatch` - 手動觸發
- ✅ `schedule` - 每週一 UTC 04:00 (台北時間 12:00)

**執行內容**:
- 定期發送測試事件到 Sentry
- 確認監控系統持續運作
- 避免監控盲區

**為何非 Required**: 定時檢查，失敗不阻擋開發

---

### 15. `worker-heartbeat-monitor`
**檔案**: `.github/workflows/worker-heartbeat-monitor.yml`

**用途**: RQ Worker 心跳監控，確保後台任務處理正常

**觸發條件**:
- ✅ `workflow_dispatch` - 手動觸發（支援 `verify` 參數進行生產驗證）
- ✅ `schedule` - 每 15 分鐘執行一次

**執行內容**:
- 檢查 Redis 中的 Worker 心跳時間戳
- 驗證 Worker 進程存活
- 超時警報（超過 10 分鐘未更新）
- 成功時自動關閉開啟的 heartbeat alert issues
- 驗證模式：創建測試 issue 並驗證自動關閉機制

**環境變數**:
- `ALLOWED_HEARTBEAT_CREATORS`: 允許自動關閉的 issue 建立者清單（以逗號分隔）。空字串會回退至預設值 `['github-actions[bot]']`。預設值：`github-actions[bot]`

**為何非 Required**: 監控工作流，失敗不影響開發流程

**並發控制**: 使用 `cancel-in-progress: true` 並依 event_name 區分，允許排程與手動運行並存

---

### 16. `tolgee-sync` (Tolgee Translation Sync)
**檔案**: `.github/workflows/tolgee-sync.yml`

**用途**: Tolgee 翻譯同步，自動同步翻譯檔案與 Tolgee 平台

**觸發條件**:
- ✅ `workflow_dispatch` - 手動觸發（支援 `bootstrap` 參數進行首次推送）
- ✅ `push` - main 分支推送
- ✅ `schedule` - 每天 10:00 Asia/Taipei (cron: '0 2 * * *')

**執行內容**:
- 檢查 Tolgee 專案是否需要 bootstrap（Owner Console #24693, Frontend Dashboard #24702）
- **自動運行**（push/schedule）:
  - 如果兩個專案都有 keys: 執行正常同步（pull → validate → create PR）
  - 如果任一專案為空: 優雅退出（綠色，日誌有清楚說明和手動 bootstrap 指示）
- **手動 Bootstrap 模式**（workflow_dispatch + bootstrap=true）:
  - 推送現有翻譯到空的 Tolgee 專案（首次設定）
  - 可能因 Tolgee 方案限制失敗（預期行為，會顯示清楚的錯誤訊息）
- **正常同步模式**（當兩個專案都有 keys）:
  - Preflight 驗證（dry-run pull + validate）
  - 從 Tolgee 拉取最新翻譯
  - 驗證翻譯檔案結構完整性
  - 如有變更自動創建 PR
  - **自動設置 i18n check status**（PR #1449）:
    - 檢測 PR 是否為 locales-only（僅包含翻譯 JSON 文件）
    - 如果是，自動設置 "Changed Files Strict i18n Check" 為 success
    - 使用 belt-and-suspenders 方法：同時設置 commit status 和 check run
    - 避免 GITHUB_TOKEN 創建的 PR 被 branch protection 卡住

**行為**:
- 使用 concurrency control 防止並發運行（`cancel-in-progress: true`）
- Bootstrap 僅在手動觸發時執行（防止 `plan_key_limit_exceeded` 錯誤）
- 當檢測到需要 bootstrap 時，自動運行會優雅退出（不產生紅色通知）
- 優雅退出時日誌包含清楚的說明、當前狀態和手動 bootstrap 操作指示
- **Per-project bootstrap flags**（PR #1436）: OC 和 FD 可以獨立運行，FD 為空不會阻塞 OC 同步

**為何非 Required**: 翻譯同步工作流，失敗不影響開發流程

**當前狀態** (2025-11-23):
- Owner Console (Project #24693): 正常運作（448 keys）
- Frontend Dashboard (Project #24702): 暫停同步（0 keys，需要 bootstrap 或手動填充）
- 自動運行行為: OC 正常同步，FD 優雅退出（綠色），不產生紅色 CI 通知

**i18n Check 自動設置機制** (PR #1449):
- **問題**: github-actions[bot] 使用 GITHUB_TOKEN 創建的 PR 會被 GitHub 抑制 workflow 運行，導致 "Changed Files Strict i18n Check" 永遠處於 "Expected — Waiting for status to be reported" 狀態
- **解決方案**: Workflow 自動檢測 locales-only PR 並設置 i18n check status
- **實施方式**:
  1. 在 PR 創建後，使用 fallback 邏輯找到 open PR（通過 head branch `chore/tolgee-sync`）
  2. 列出 PR 的所有變更文件，檢測是否為 locales-only（僅包含 `handoff/.*/40_App/(owner-console/src/locales/|frontend-dashboard/src/i18n/locales/).*\.json`）
  3. 如果是 locales-only，設置 commit status: `context: "Changed Files Strict i18n Check"`, `state: success`
  4. 同時創建 check run: `name: "Changed Files Strict i18n Check"`, `conclusion: success`（belt-and-suspenders 方法）
  5. 兩者都指向 workflow run URL，提供可追溯性
- **為何需要 belt-and-suspenders**: Branch protection 可能配置為要求 commit status 或 check run，同時設置兩者確保最大兼容性
- **GITHUB_TOKEN 抑制說明**: GitHub 為防止無限循環，會抑制由 GITHUB_TOKEN 觸發的 workflow 運行。這意味著 bot 創建的 PR 不會自動觸發 i18n check workflow，需要手動設置 status

**故障排除**:
- 如看到 `plan_key_limit_exceeded` 錯誤: Tolgee 方案 key 數量已達上限，需要升級方案或手動清理 keys
- 如需要 bootstrap 空專案: 前往 Actions → Tolgee Translation Sync → Run workflow → 勾選 "Bootstrap" checkbox
- 如 bootstrap 失敗: 檢查 Tolgee 方案限制，考慮透過 Tolgee UI 手動填充或升級方案
- **如 PR 卡在 "Expected — Waiting for status to be reported"**: 
  - 原因: PR head SHA 更新後，舊 SHA 的 status 不再有效
  - 解決: 手動觸發 tolgee-sync workflow（Actions → Tolgee Translation Sync → Run workflow）
  - Workflow 會自動找到 open PR 並為當前 head SHA 設置 status

**相關 PR**:
- PR #1431: 穩定化 Tolgee CI（Bootstrap 改為手動觸發）
- PR #1436: 實施 per-project bootstrap flags（OC/FD 獨立運行）
- PR #1449: 為 locales-only PR 自動設置 i18n check status（解決 GITHUB_TOKEN 抑制問題）

---

### 17. `ux-metrics-update` (UX Metrics Update)
**檔案**: `.github/workflows/ux-metrics-update.yml`

**用途**: UX Metrics 數據更新，自動更新 UX 指標並創建 PR

**觸發條件**:
- ✅ `workflow_dispatch` - 手動觸發
- ✅ `push` - main 分支推送（僅當 metrics 相關檔案變更時）
- ✅ `schedule` - 定期執行

**執行內容**:
- 收集 UX metrics 數據
- 更新 `metrics/ux-metrics.json` 和 `handoff/.../public/metrics/ux-metrics.json`
- 如有變更自動創建或更新 PR（branch: `chore/ux-metrics`）
- **自動設置 i18n check status**（PR #1454）:
  - 檢測 PR 是否為 metrics-only（僅包含 metrics JSON 文件）
  - 如果是，自動設置 "Changed Files Strict i18n Check" 為 success
  - 使用 belt-and-suspenders 方法：同時設置 commit status 和 check run
  - 與 tolgee-sync 使用相同的模式，避免 GITHUB_TOKEN 創建的 PR 被卡住

**行為**:
- 使用 PR 模式（PR #1425）: 創建/更新 PR 而非直接推送到 main
- 使用 `paths-ignore` 防止無限循環
- 設置固定 bot 分支 `chore/ux-metrics`
- **Metrics-only detection**: 檢測 PR 是否只包含 `metrics/ux-metrics.json` 和 `handoff/.*/40_App/(owner-console|frontend-dashboard)/public/metrics/ux-metrics.json`

**為何非 Required**: Metrics 更新工作流，失敗不影響開發流程

**i18n Check 自動設置機制** (PR #1454):
- 完全鏡像 PR #1449 (Tolgee) 的實施方式
- 使用相同的 fallback 邏輯找到 open PR（通過 head branch `chore/ux-metrics`）
- 檢測 metrics-only PR 並設置 "Changed Files Strict i18n Check" status
- 使用 belt-and-suspenders 方法確保兼容性

**性能優化** (PR #1494):
- **pnpm 緩存**: 使用 `actions/cache@v4` 緩存 pnpm store，減少依賴安裝時間
  - 首次運行或 lockfile 變更：正常安裝（~30 秒）
  - 後續運行（緩存命中）：快速恢復（~5 秒）
  - 節省時間：~25 秒/次運行
  - 緩存 key 基於 `pnpm-lock.yaml` hash，確保依賴變更時緩存失效
  - 使用 `restore-keys` 提供 fallback，即使 exact match 失敗也能使用部分緩存
- **淺層 checkout**: 使用 `fetch-depth: 1` 僅獲取最新 commit
  - 不下載完整 git 歷史，減少網絡傳輸
  - 節省時間：~5-10 秒/次運行
  - 安全性：`aggregate-metrics.mjs` 僅使用 GitHub API，不依賴 git 歷史
  - 兼容性：`peter-evans/create-pull-request` 內部自動處理分支更新
- **總效益**: 每次運行節省 ~30-40 秒
  - 實測數據：Checkout ~2 秒，Install ~5 秒（有緩存）
  - 每月節省：~165 分鐘（假設 300 次運行）
  - 緩存命中率：100%（驗證測試）
- **驗證狀態**: ✅ 已通過兩次測試運行驗證（Run 19607623782, 19607676533）
  - ✅ 緩存正常工作
  - ✅ 無 push 失敗或 non-fast-forward 錯誤
  - ✅ PR 創建/更新成功

**相關 PR**:
- PR #1425: 切換為 PR 模式（符合 repository rules）
- PR #1454: 為 metrics-only PR 自動設置 i18n check status（與 PR #1449 相同模式）
- PR #1494: 性能優化（pnpm 緩存 + 淺層 checkout）

---

### 18. `auto-merge-faq`
**檔案**: `.github/workflows/auto-merge-faq.yml`

**用途**: 自動合併 FAQ 文件更新 PR

**觸發條件**:
- ✅ `workflow_dispatch` - 手動觸發 (Phase 11 新增)
- ✅ `pull_request` - PR 開啟或同步更新 (僅 `docs/FAQ.md` 變更)
- ✅ `check_suite` - CI 檢查完成時觸發

**執行內容**:
- 檢查 PR 是否僅修改 `docs/FAQ.md`
- 驗證 PR 來自 `github-actions[bot]` 或包含 `trace-id`
- 自動啟用 auto-merge (squash 模式)

**為何非 Required**: 自動化工具，不影響開發流程

**安全機制**: 僅處理 bot 建立的 PR 或特定標記的 PR

---

### 19. `coverage-trend` (Coverage Trend Tracking)
**檔案**: `.github/workflows/coverage-trend.yml`

**用途**: 覆蓋率趨勢追蹤，自動記錄覆蓋率數據到 Redis

**觸發條件**:
- ✅ `workflow_dispatch` - 手動觸發
- ✅ `workflow_run` - 在 `backend-ci` 或 `test-apps` workflow 成功完成後觸發（僅 main 分支）

**執行內容**:
- 下載 `backend-ci` 和 `test-apps` 的覆蓋率 artifacts
- 解析 `coverage.json` 獲取覆蓋率百分比
- 使用 `coverage_dashboard.py` 記錄覆蓋率到 Redis
- 生成 GitHub Actions Summary 顯示當前覆蓋率狀態

**環境變數**:
- `REDIS_URL`: Redis 連接 URL（必需，用於存儲趨勢數據）

**為何非 Required**: 趨勢追蹤工具，失敗不影響開發流程

**相關工具**:
- `tools/monitoring/coverage_dashboard.py`: 覆蓋率趨勢 dashboard 腳本
- 支援 `--record MODULE COVERAGE` 記錄覆蓋率
- 支援 `--days N` 查看 N 天趨勢
- 支援 `--summary` 顯示摘要表格

**覆蓋率門檻**:
| 模組 | 門檻 |
|------|------|
| API Backend | 74% |
| Orchestrator | 50% |
| Shared-UI | 60% |
| Frontend Dashboard | 80% |
| Owner Console | 70% |

---

### 20. `redis-security-check` (Redis Security Check)
**檔案**: `.github/workflows/redis-security-check.yml`

**用途**: Redis 安全性檢查，定期檢查 Redis 版本是否存在已知漏洞

**觸發條件**:
- ✅ `workflow_dispatch` - 手動觸發（支援 `force_check` 參數）
- ✅ `schedule` - 每週一 09:00 UTC (17:00 台北時間)
- ✅ `push` - main 分支推送（僅當 Redis 相關檔案變更時）

**執行內容**:
- 檢查 Redis Python 套件版本是否過時
- 連接 Redis 伺服器檢查實際版本
- 驗證是否受 CVE-2025-49844 (RediShell) 影響
- 檢查 TLS 加密是否啟用
- 如發現漏洞，自動創建 GitHub Issue

**環境變數**:
- `REDIS_URL`: Redis 連接 URL（可選）
- `UPSTASH_REDIS_REST_URL`: Upstash Redis URL（可選，優先使用）

**CVE-2025-49844 檢查**:
- **受影響版本**: Redis < 8.2.2
- **風險等級**: Critical
- **Upstash 用戶**: 低風險（雲端管理，自動更新）
- **自建 Redis**: 需手動升級到 8.2.2+

**為何非 Required**: 安全監控工具，失敗不阻擋開發流程

**自動 Issue 創建**:
- 當檢測到漏洞時，自動創建帶有 `security`, `redis`, `cve`, `critical` 標籤的 Issue
- 包含修復建議和參考連結
- 避免重複創建（檢查現有 open issues）

---

### 21. `migration-health-check` (Validate migration files)
**檔案**: `.github/workflows/migration-health-check.yml`

**用途**: Migration 檔案健康檢查，驗證 migration 檔案命名規範與完整性

**觸發條件**:
- ✅ `workflow_dispatch` - 手動觸發
- ✅ `push` - main 分支推送（僅當 `migrations/` 變更時）
- ✅ `pull_request` - 所有 PR（僅當 `migrations/` 或 `scripts/run_migrations.sh` 變更時）

**執行內容**:
- 檢查 migration runner 腳本存在且可執行
- 使用統一 runner 列出所有 migrations
- 檢測重複的 migration 編號（警告模式）
- 驗證命名規範（`NNN_*.sql`）
- 檢測 migration 序號中的大間隙（>5）
- 驗證 dry-run 模式可正常運作
- 生成包含統計資訊的 summary

**為何非 Required**: Migration 健康檢查為輔助工具，失敗不阻擋開發流程

**注意事項**:
- 重複編號檢查設為警告而非錯誤，因目前存在既有的重複（024_create_failure_memory_table.sql 和 024_create_planner_events_table.sql）
- 命名規範排除特殊檔案：`PRE_DEPLOYMENT`、`backfill`、`rollback` 開頭的檔案
- 依賴 `scripts/run_migrations.sh`（PR-6 新增的統一 migration runner）

**相關 PR**:
- PR #1756: 統一 Migration Runner（PR-6）
- PR #1757: Migration Health Check CI（PR-7）

---

### 22. `qwen-pr-review` (Qwen AI Code Review) - **已停用**
**檔案**: `.github/workflows/qwen-pr-review.yml`

**狀態**: ⚠️ **已停用 (2025-12-16)** - 改用 GitHub Copilot 作為主要 AI 程式碼審查工具

**用途**: AI 自動程式碼審查，使用阿里雲 Qwen LLM 對 PR 進行智能審查

**觸發條件**:
- ✅ `workflow_dispatch` - 僅限手動觸發（用於測試或一次性審查）
- ❌ ~~`pull_request`~~ - 已停用自動觸發
- ❌ Fork PR - 自動跳過（保護 secrets）
- ❌ Bot PR - 自動跳過（避免浪費 API 費用）
- ❌ `no-ai-review` label - 可選擇跳過特定 PR

**如何重新啟用**: 取消註解 `qwen-pr-review.yml` 中的 `pull_request` 觸發器

**執行內容**:
- 取得 PR diff 並截斷至 80KB（控制 token 成本）
- 根據 PR labels 調整審查重點（`ui`/`frontend`, `backend`/`api`, `security`, `database`/`migration`, `infra`/`devops`）
- 呼叫 Qwen API 進行程式碼審查
- 發佈 sticky comment 顯示審查結果
- 使用 checklist 格式標示問題嚴重程度（CRITICAL/HIGH/MEDIUM/LOW）

**環境變數/Secrets**:
- `QWEN_API_KEY`: 阿里雲 DashScope API Key（必需，在 Settings → Secrets → Actions 設定）

**安全機制**:
- **Fork PR 跳過**: 防止 secrets 洩漏給外部貢獻者
- **Bot PR 跳過**: 避免 Dependabot 等 bot 浪費 API 費用
- **Shell injection 防護**: PR metadata 透過 step `env:` 傳遞，使用 `jq` 安全 JSON encode
- **@mention 移除**: 使用 perl 移除 AI 輸出中的 @mentions，避免垃圾通知
- **敏感檔案偵測**: 大小寫不敏感偵測 `.env`、`.pem`、`.key` 等檔案並警告
- **GITHUB_ENV 安全寫入**: 使用 `printf` 而非 `echo` 處理 multiline 變數

**成本控制**:
- **並發控制**: 同一 PR 只執行一個 job，快速 push 時取消舊的執行
- **Commit SHA 去重**: 相同 commit 不重複審查（使用 hidden HTML marker）
- **Diff 截斷**: 大型 diff 自動截斷至 80KB
- **API 重試**: 暫時性錯誤（429, 5xx）自動重試，非暫時性錯誤（4xx）立即失敗

**智能功能**:
- **Label-based 審查重點**: 根據 PR labels 調整 AI prompt
  - `ui`/`frontend`: React patterns, a11y, responsive design
  - `backend`/`api`: SQL injection, auth, input validation
  - `security`: OWASP Top 10, secrets handling
  - `database`/`migration`: migration safety, query performance
  - `infra`/`devops`: infrastructure security, deployment safety
- **Smart Markdown 截斷**: 偵測未閉合的 code fence 並自動補上關閉標記

**為何非 Required**: AI 審查為輔助工具，失敗不應阻擋 PR 合併

**Opt-out 機制**: 加上 `no-ai-review` label 可跳過特定 PR 的 AI 審查

**相關 PR**:
- PR #2540: 初始實作 Qwen AI Code Review workflow
- Issue #2551: nektos/act 自動化測試
- Issue #2552: docs/ci_matrix.md 文件補充

---

### 23. `qwen-review-tests` (Qwen Review Tests)
**檔案**: `.github/workflows/qwen-review-tests.yml`

**用途**: Qwen AI Code Review workflow 的單元測試，驗證 shell script 邏輯正確性

**觸發條件**:
- ✅ `workflow_dispatch` - 手動觸發
- ✅ `push` - 當 `qwen-pr-review.yml`、`qwen-review-tests.yml` 變更時（測試邏輯內嵌於 workflow 的 `run:` 區塊）
- ✅ `pull_request` - 當相關檔案變更時

**執行內容**:
- **GITHUB_ENV multiline 測試**: 驗證特殊字元（引號、反斜線、變數）正確處理
- **JSON encoding 測試**: 驗證 `jq` 安全編碼各種危險輸入
- **@mention 移除測試**: 驗證 perl regex 正確處理 @username vs email@domain.com
- **敏感檔案偵測測試**: 驗證大小寫不敏感 regex pattern，包含路徑、備份檔案、edge cases
- **Markdown 截斷測試**: 驗證 code fence 計數與自動關閉邏輯
- **API 重試邏輯測試**: 驗證 HTTP status code 分類（transient vs non-transient）
- **Exponential backoff 測試**: 驗證 2^attempt 計算與 30 秒上限
- **nektos/act dry-run**: 使用 act 驗證 workflow YAML 語法

**為何非 Required**: 測試工具，失敗不阻擋開發流程

**維護注意事項**: 目前測試邏輯直接內嵌於 workflow 的 `run:` 區塊，與 production workflow 的邏輯是「重寫」而非「共用」。若 production workflow 邏輯變更，需同步更新測試。未來建議抽出共用腳本（如 `scripts/qwen_pr_review.sh`），由 production workflow 與 tests workflow 共同 source，以避免 drift。

**相關 Issue**: #2551 (nektos/act 自動化測試)

---

### 24. `dependency-check` (Dependency Management Check)
**檔案**: `.github/workflows/dependency-check.yml`

**用途**: 依賴管理一致性檢查，確保 monorepo 使用統一的套件管理器 (pnpm) 並防止 lockfile 漂移

**觸發條件**:
- ✅ `push` - main 分支推送（當任一 package.json 或 lockfile 變更時）
- ✅ `pull_request` - 所有 PR（當 package.json、lockfile、workflows、vercel.json 變更時）

**執行內容**:
- **禁止的 lockfile 檢查**: 確保沒有 `yarn.lock` 或 `package-lock.json`（僅允許 `pnpm-lock.yaml`）
- **pnpm-lock.yaml 存在性檢查**: 確保 lockfile 存在
- **Lockfile 同步檢查** (新增): 使用 `pnpm install --lockfile-only` 重新生成 lockfile 並比對 hash，確保 lockfile 與 package.json 同步
- **vercel.json 配置檢查**: 確保 Vercel 使用 pnpm 而非 yarn/npm
- **GitHub Actions workflows 檢查**: 掃描所有 workflows 確保使用 pnpm

**為何非 Required**: 依賴管理檢查重要但不阻擋緊急修復

**Lockfile 同步檢查說明**:
此檢查防止 dev/CI/prod 環境因 lockfile 未更新而安裝不同版本的依賴。當 package.json 變更但 lockfile 未重新生成時，CI 會失敗並提供明確的修復指令：
```bash
pnpm install
git add pnpm-lock.yaml
git commit -m "chore: update pnpm-lock.yaml"
```

**相關 Issue**: #2579 (CI Lockfile Sync Check)

---

### 25. `verify-system-state-tests` (test)
**檔案**: `.github/workflows/verify-system-state-tests.yml`

**用途**: verify_system_state.sh 回歸測試，確保文件與程式碼一致性檢查腳本正常運作

**觸發條件**:
- ✅ `workflow_dispatch` - 手動觸發
- ✅ `push` - main 分支推送（當 verify_system_state.sh 或其測試檔案變更時）
- ✅ `pull_request` - 所有 PR（當 verify_system_state.sh 或其測試檔案變更時）

**執行內容**:
- **回歸測試**: 執行 43 個測試案例，涵蓋 10 個驗證類別
- **語法檢查**: 驗證 verify_system_state.sh bash 語法正確

**測試覆蓋範圍**:
- React 版本提取與比對
- pnpm overrides 讀取
- pgvector 驗證
- 雙 orchestrator 架構驗證
- Production URL 映射
- Alembic 狀態
- Phase API 模組
- 關鍵依賴
- ADR 驗證
- Edge cases（空 JSON、unicode、malformed JSON 等）

**為何非 Required**: 腳本測試重要但不阻擋緊急修復

**維護注意事項**:
此測試套件與 `verify_system_state.sh` 腳本需要長期同步維護。當修改腳本輸出格式、新增驗證項目、或變更 repo 結構時，需同步更新測試。測試 fixtures 會自動從真實 repo 讀取預期值（如 React 版本），以降低手動同步成本。

**相關 Issue**: #2581 (verify_system_state.sh Regression Tests)

---

## 📋 Branch Protection 規則說明

**目前配置的 4 個 Required Checks**:

1. **`orchestrator-e2e / run`** - Orchestrator 核心邏輯驗證
2. **`post-deploy-health / check`** - 生產環境基本可用性
3. **`Post-Deploy Health Assertions / validate`** - 生產環境功能完整性
4. **`Ops Agent Sandbox E2E / e2e-test`** - Agent 沙箱隔離機制

**為何選擇這 4 個?**
- **覆蓋核心功能**: Orchestrator (核心)、Health (可用性)、Assertions (正確性)、Sandbox (安全性)
- **平衡速度與品質**: 避免過多檢查阻擋開發，但確保關鍵功能不被破壞
- **成本考量**: ops-agent-sandbox-e2e 使用條件執行避免不必要的 Fly.io 費用

**其他重要工作流為何非 Required?**
- `backend-ci` / `frontend-ci`: 測試覆蓋率仍在提升中
- `openapi-verify`: API 規格驗證重要但不阻擋緊急修復
- `agent-mvp-e2e`: E2E 測試較耗時，完整測試可選擇性執行
- 部署與監控工作流: 失敗不應阻擋程式碼合併

---

## 🔧 使用指南

### 手動觸發工作流

所有 18 個工作流現在都支援手動觸發：

```bash
# 觸發單一工作流
gh workflow run "backend-ci" -r main

# 觸發多個工作流（健康檢查）
bash scripts/run_main_health.sh

# 觸發生產部署相關工作流
bash scripts/deploy_prod_and_health.sh
```

### 查看工作流執行狀態

```bash
# 列出所有工作流
gh workflow list

# 查看特定工作流的最近執行記錄
gh run list --workflow "backend-ci" --limit 5

# 監控特定執行直到完成
gh run watch <run_id> --exit-status
```

### 驗證 Branch Protection 配置

```bash
# 查詢 main 分支保護規則（需要適當權限）
gh api repos/RC918/morningai/branches/main/protection \
  -H "Accept: application/vnd.github+json" \
  --jq '.required_status_checks.checks[] | .context'
```

---

## 📊 工作流依賴關係

```
main 分支合併條件
├── orchestrator-e2e (run) ✓
├── post-deploy-health (check) ✓
├── Post-Deploy Health Assertions (validate) ✓
└── Ops Agent Sandbox E2E (e2e-test) ✓

品質檢查（非阻擋）
├── backend-ci (測試覆蓋率 25%)
├── frontend-ci (建置 + lint + 煙測)
├── openapi-verify (API 規格驗證)
├── agent-mvp-smoke (快速煙測)
├── agent-mvp-e2e (完整 E2E)
└── migration-health-check (Migration 檔案健康檢查)

部署流程
├── vercel-deploy (前端部署)
├── fly-deploy (沙箱部署)
└── auto-merge-faq (FAQ 自動合併)

監控系統
├── env-diagnose (多雲服務診斷)
├── sentry-smoke (Sentry 煙測)
├── sentry-smoke-cron (定時監控檢查)
└── worker-heartbeat-monitor (Worker 心跳監控)

翻譯與 Metrics
├── tolgee-sync (翻譯同步)
└── ux-metrics-update (UX Metrics 更新)
```

---

## 🚨 故障排除

### 工作流失敗常見原因

1. **環境變數缺失**: 檢查 GitHub Secrets 是否正確配置
2. **依賴版本衝突**: 檢查 `requirements.txt` 或 `package.json`
3. **Fly.io 配額**: ops-agent-sandbox-e2e 可能受 Fly.io 免費額度限制
4. **Redis 連線**: worker-heartbeat-monitor 失敗通常是 Redis 連線問題
5. **Sentry DSN**: sentry-smoke 失敗檢查 `SENTRY_DSN` 環境變數

### 緊急情況處理

如果 Branch Protection 阻擋緊急修復：
1. 暫時停用特定檢查（需要 Admin 權限）
2. 使用 Admin override 強制合併
3. 修復後立即重新啟用保護規則

### 聯絡資訊

如果遇到 CI 問題無法解決，請：
1. 查看 GitHub Actions logs 詳細錯誤訊息
2. 檢查 <ref_file file="/home/ubuntu/repos/morningai/docs/scripts_overview.md" /> 腳本使用指南
3. 聯繫專案維護者 @RC918

---

## 🛡️ Branch Protection：證據連結

### Required Status Checks 配置

根據 Branch Protection 規則，`main` 分支必須通過以下 4 個檢查才能合併 PR：

1. **orchestrator-e2e / run** - Orchestrator 端到端測試
2. **post-deploy-health / check** - 部署後健康檢查
3. **post-deploy-health-assertions / validate** - 部署後斷言驗證
4. **ops-agent-sandbox-e2e / e2e-test** - Ops Agent Sandbox E2E 測試

### 驗證方式

**API 查詢**（需要 repo admin 權限）:
```bash
gh api repos/RC918/morningai/branches/main/protection \
  -H "Accept: application/vnd.github+json" \
  --jq '.required_status_checks.checks'
```

**手動驗證**:
前往 https://github.com/RC918/morningai/settings/branches 查看 `main` 分支的 Protection Rules。

### Required Checks 對應表

以下表格列出 4 個 Required Status Checks 的完整對應關係：

| Workflow 檔案 | 顯示名稱 | Job 名稱 | 觸發事件 | Branch Protection Context |
|--------------|---------|---------|---------|---------------------------|
| `.github/workflows/orchestrator-e2e.yml` | orchestrator-e2e | `run` | `workflow_dispatch`<br/>`push`<br/>`pull_request` | `orchestrator-e2e / run` |
| `.github/workflows/post-deploy-health.yml` | post-deploy-health | `check` | `workflow_dispatch`<br/>`push: { branches: [ main ] }`<br/>`pull_request` | `post-deploy-health / check` |
| `.github/workflows/post-deploy-health-assertions.yml` | Post-Deploy Health Assertions | `validate` | `workflow_dispatch`<br/>`push: { branches: [ main ] }`<br/>`pull_request: { branches: [ main ] }`<br/>`schedule` (cron) | `post-deploy-health-assertions / validate` |
| `.github/workflows/ops-agent-sandbox-e2e.yml` | Ops Agent Sandbox E2E | `e2e-test` | `workflow_dispatch`<br/>`push: { branches: [main] }`<br/>`pull_request` | `ops-agent-sandbox-e2e / e2e-test` |

**關鍵要點**：
- ✅ 所有 4 個 Required workflows 都支援 `pull_request` 觸發器，確保能在 PR 上回報狀態
- ✅ Job 名稱必須與 Branch Protection 設定中的 context 名稱完全匹配
- ✅ `post-deploy-health-assertions` 在 2025-10-13 修復了缺少 `pull_request` 觸發器的問題（[PR #236](https://github.com/RC918/morningai/pull/236)）

### 為何某些工作流非 Required？

以下工作流雖然重要，但不設為 Required 的原因：

- **openapi-verify / lint**: 用於 OpenAPI 規格驗證，但 lint 失敗不應阻擋緊急修復的合併
- **frontend-ci / build**: 前端建置由 Vercel 自動執行，不需要在 GitHub Actions 再次驗證
- **backend-ci / test**: 後端測試覆蓋率已達標（25%），但不設為 Required 以允許實驗性 PR
- **agent-mvp-smoke / smoke**: 煙測用於快速驗證，但不應阻擋所有 PR
- **fly-deploy / deploy**: 部署工作流不應作為 PR 合併的前置條件
- **Vercel**: Vercel 自動部署預覽，但不應阻擋 PR 合併

---

## 📝 版本歷史

- **2025-12-16**: 停用 `qwen-pr-review` 自動觸發，改用 GitHub Copilot 作為主要 AI 程式碼審查工具
- **2025-12-16**: 新增 `qwen-pr-review` 和 `qwen-review-tests` 工作流文檔，記錄安全機制、成本控制、智能功能（Issue #2551, #2552）
- **2025-11-30**: 新增 `coverage-trend` 和 `redis-security-check` 工作流文檔
- **2025-11-30**: 記錄覆蓋率趨勢追蹤機制（Redis 存儲、dashboard 工具）
- **2025-11-30**: 記錄 Redis CVE-2025-49844 安全監控機制
- **2025-11-23**: 新增 `tolgee-sync` 和 `ux-metrics-update` 工作流文檔
- **2025-11-23**: 記錄 PR #1449 和 #1454 的 i18n check 自動設置機制（解決 GITHUB_TOKEN 抑制問題）
- **2025-11-23**: 記錄 PR #1436 的 per-project bootstrap flags（OC/FD 獨立運行）
- **2025-11-23**: 更新 Tolgee 當前狀態（OC: 448 keys, FD: 0 keys）
- **2025-10-13**: 修復 `post-deploy-health-assertions` 缺少 `pull_request` 觸發器問題
- **2025-10-13**: 新增 Required Checks 對應表，記錄 workflow 檔案與 job 名稱對應關係
- **2025-10-12**: Phase 11 清債 - 所有工作流新增 `workflow_dispatch` 支援
- **2025-10-12**: Branch Protection 規則修正為 4 個 Required Checks
- **2025-10-11**: 新增 `ops-agent-sandbox-e2e` 工作流
- **2025-10-02**: 初始 CI 基礎設施建立

---

**最後更新**: 2025-12-16  
**維護者**: @RC918 (Ryan Chen)  
**文件版本**: 1.5.0
