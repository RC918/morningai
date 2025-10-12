# Scripts Overview

本目錄包含 Morning AI 專案的標準化管理腳本，用於自動化常見的維運任務。

## 📋 腳本清單

### 1. `scripts/run_main_health.sh`
**功能**：一鍵觸發 main 分支的關鍵健康檢查工作流並等待結果

**使用時機**：
- 發布前驗證主幹穩定性
- 手動觸發完整健康檢查
- 驗證 Branch Protection 配置是否正常

**執行方式**：
```bash
cd ~/repos/morningai
bash scripts/run_main_health.sh
```

**涵蓋的工作流**：
- `openapi-verify` - OpenAPI 規格驗證
- `orchestrator-e2e` - Orchestrator 端到端測試
- `agent-mvp-smoke` - Agent MVP 煙測
- `Ops Agent Sandbox E2E` - Ops Agent Sandbox 端到端測試
- `post-deploy-health` - 部署後健康檢查

**安全注意事項**：
- ⚠️ 需要 `gh` CLI 已登入並具有 workflow dispatch 權限
- ⚠️ 某些 workflow 可能不支援 `workflow_dispatch`，會產生 HTTP 422 錯誤（腳本會自動忽略）
- ⚠️ 僅觸發 `main` 分支，不會影響其他開發分支

---

### 2. `scripts/release_main.sh`
**功能**：自動建立 Git tag 並發布 GitHub Release，自動避免重複 tag

**使用時機**：
- 主幹穩定後建立正式版本發布
- 生產環境部署前標記版本
- 建立版本里程碑

**執行方式**：
```bash
cd ~/repos/morningai
bash scripts/release_main.sh
```

**Tag 命名規則**：
- 格式：`vYYYYMMDD-HHMM`
- 如果 tag 已存在，會自動加上秒數後綴：`vYYYYMMDD-HHMM-SS`
- 範例：`v20251012-1530` 或 `v20251012-1530-45`

**安全注意事項**：
- 🔴 **高風險操作**：會直接 push tag 到遠端並建立 public release
- ⚠️ 需要 `gh` CLI 已登入並具有 repo 寫入權限
- ⚠️ 會執行 `git reset --hard origin/main` 清理本地變更
- ⚠️ Release 建立後無法直接刪除，只能標記為 Draft

**失敗處理**：
- 如果沒有 push 權限，會報錯並終止
- 如果 Release 建立失敗，tag 已經 push 但 Release 頁面不存在，需手動建立

---

### 3. `scripts/deploy_prod_and_health.sh`
**功能**：觸發生產環境部署相關的工作流並等待健康檢查完成

**使用時機**：
- 生產環境完整部署流程
- 部署後全面健康檢查
- 驗證 Vercel、Fly.io 部署狀態
- 驗證 Sentry 監控整合

**執行方式**：
```bash
cd ~/repos/morningai
bash scripts/deploy_prod_and_health.sh
```

**涵蓋的工作流**：
- `vercel-deploy` - Vercel 前端部署
- `Fly Deploy` - Fly.io Ops Agent Sandbox 部署
- `post-deploy-health` - 部署後健康檢查
- `Post-Deploy Health Assertions` - 部署後斷言驗證
- `Sentry Smoke Test` - Sentry 監控煙測

**安全注意事項**：
- 🔴 **極高風險操作**：會觸發實際的生產環境部署
- ⚠️ 需要 `gh` CLI 已登入並具有 workflow dispatch 權限
- ⚠️ 請確保 `main` 分支已通過所有測試再執行
- ⚠️ 部署失敗可能需要手動回滾（Vercel 或 Fly.io Dashboard）

**失敗處理**：
- 如果任一 workflow run 失敗，腳本會返回非零退出碼
- 部署失敗需檢查：
  1. Vercel Dashboard：https://vercel.com/dashboard
  2. Fly.io Dashboard：https://fly.io/dashboard
  3. GitHub Actions logs
- 回滾方式：
  - Vercel：在 Dashboard 選擇 previous deployment 並 "Promote to Production"
  - Fly.io：使用 `flyctl releases list` 和 `flyctl releases rollback`

---

## 🔐 認證要求

所有腳本都需要 GitHub CLI (`gh`) 已完成認證：

```bash
# 檢查認證狀態
gh auth status

# 如果未認證，執行登入
gh auth login

# 確保具有 repo 和 workflow 權限
gh auth refresh -s repo,workflow
```

---

## 🚨 使用前檢查清單

執行任何腳本前，請確認：

- [ ] `gh` CLI 已安裝並認證
- [ ] 當前目錄位於專案根目錄 (`~/repos/morningai`)
- [ ] `main` 分支已通過所有 Required Checks（針對 release 和 deploy 腳本）
- [ ] 了解腳本可能觸發的資源消耗（CI minutes、部署次數）
- [ ] 已閱讀並理解該腳本的風險提示

---

## 📊 腳本執行記錄

建議執行重要腳本時保留執行記錄：

```bash
# 帶有時間戳記的執行記錄
bash scripts/release_main.sh 2>&1 | tee logs/release-$(date +%Y%m%d-%H%M%S).log
```

---

## 🔄 維護規範

- 所有腳本需包含：功能說明、使用時機、風險提示、安全提示、失敗處理
- 使用 `set -euo pipefail` 確保錯誤時立即終止
- 使用 `|| true` 容忍預期的非關鍵錯誤（如 HTTP 422）
- 每個腳本應有對應的測試案例或驗證步驟

---

## 📞 故障排除

如果腳本執行失敗，請檢查：

1. **認證問題**：`gh auth status` 確認已登入
2. **權限問題**：確認 GitHub Token 具有 `repo` 和 `workflow` scope
3. **網路問題**：確認可以存取 `api.github.com`
4. **分支狀態**：確認 `main` 分支最新且無衝突
5. **工作流配置**：確認 `.github/workflows/` 中的 workflow 檔案正確

如果問題持續，請聯繫專案維護者或查看 GitHub Actions logs。
