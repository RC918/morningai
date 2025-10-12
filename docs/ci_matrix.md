# CI Workflow Matrix

本文檔詳細列出 Morning AI 專案的所有 GitHub Actions 工作流，包含其用途、觸發條件、是否為 Branch Protection 必須檢查，以及 workflow_dispatch 支援狀態。

## 📊 總覽統計

- **總工作流數量**: 16
- **支援 workflow_dispatch**: 16 (100%)
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

**用途**: Backend 程式碼品質檢查與測試覆蓋率

**觸發條件**:
- ✅ `workflow_dispatch` - 手動觸發 (Phase 11 新增)
- ✅ `push` - 任何分支推送
- ✅ `pull_request` - 所有 PR

**執行內容**:
- 安裝 Python 3.12.x 與後端依賴
- 執行 pytest 單元測試
- 測試覆蓋率檢查 (目前門檻: 25%)

**為何非 Required**: 測試覆蓋率仍在提升中，避免阻擋開發速度

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
- ✅ `workflow_dispatch` - 手動觸發
- ✅ `schedule` - 每 5 分鐘執行一次

**執行內容**:
- 檢查 Redis 中的 Worker 心跳時間戳
- 驗證 Worker 進程存活
- 超時警報（超過 10 分鐘未更新）

**為何非 Required**: 監控工作流，失敗不影響開發流程

---

### 16. `auto-merge-faq`
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

所有 16 個工作流現在都支援手動觸發：

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
└── agent-mvp-e2e (完整 E2E)

部署流程
├── vercel-deploy (前端部署)
├── fly-deploy (沙箱部署)
└── auto-merge-faq (FAQ 自動合併)

監控系統
├── env-diagnose (多雲服務診斷)
├── sentry-smoke (Sentry 煙測)
├── sentry-smoke-cron (定時監控檢查)
└── worker-heartbeat-monitor (Worker 心跳監控)
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

## 📝 版本歷史

- **2025-10-12**: Phase 11 清債 - 所有工作流新增 `workflow_dispatch` 支援
- **2025-10-12**: Branch Protection 規則修正為 4 個 Required Checks
- **2025-10-11**: 新增 `ops-agent-sandbox-e2e` 工作流
- **2025-10-02**: 初始 CI 基礎設施建立

---

**最後更新**: 2025-10-12  
**維護者**: @RC918 (Ryan Chen)  
**文件版本**: 1.0.0
