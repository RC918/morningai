# Contribution Rules (Devin-friendly)

## 分工規則
- **Design PR**：只允許改動 `docs/UX/**`, `docs/UX/tokens.json`, `docs/**.md`, `frontend/樣式與文案`。
  - 不得改動 `handoff/**/30_API/openapi/**`, `**/api/**`, `**/src/**` 的後端與 API 相關檔。
- **Backend/Engineering PR**：只允許改動 `**/api/**`, `**/src/**`, `handoff/**/30_API/openapi/**`。
  - 不得改動 `docs/UX/**` 與設計稿資源。

## 變更 API / 資料欄位（OpenAPI/DB）
1. 先建立 **RFC Issue**（label: `rfc`），說明動機、影響、相容策略、逐步 rollout。
2. 經 Owner 核准後，才可提交工程 PR。

## 驗收
- 所有 PR 需通過：OpenAPI 驗證、Post-deploy Health 斷言、CI 覆蓋率 Gate。
- 違規改動將被 CI 自動阻擋（見 `.github/workflows/pr-guard.yml`）。

---

## GitHub Actions Workflow 最佳實踐

### 🚨 防止無限循環

**強制規則**：所有 workflows 必須使用 `branches` 或 `branches-ignore` filter。

#### ✅ 推薦配置

**標準 CI workflows**（測試、構建、驗證）：
```yaml
on:
  workflow_dispatch:  # 允許手動觸發
  push:
    branches: [main]  # 只在 main 分支觸發
  pull_request:
    branches: [main]  # 只對合併到 main 的 PRs 觸發
```

**部署 workflows**：
```yaml
on:
  push:
    branches: [main]
    paths:
      - 'src/**'
      - 'package.json'
  workflow_dispatch:
```

**自動化系統 workflows**（會創建 PRs/推送代碼）：
```yaml
on:
  workflow_dispatch:
  push:
    branches-ignore:
      - 'orchestrator/**'  # 排除自動化分支
      - 'bot/**'
      - 'automated/**'
  pull_request:
    branches-ignore:
      - 'orchestrator/**'
```

#### ❌ 禁止的模式

**完全沒有 filter**（會導致無限循環）：
```yaml
# ❌ FORBIDDEN - 任何 push 都會觸發
on:
  push:
  pull_request:
```

**只有 paths filter**（不足夠）：
```yaml
# ⚠️ RISKY - 沒有 branches filter
on:
  pull_request:
    paths:
      - 'docs/**'
```

### 📋 自動合併 Workflows 特別規則

如果 workflow 會自動 merge PRs，**必須**：

1. **限制 branches**：
   ```yaml
   pull_request:
     branches: [main]  # 只允許合併到 main 的 PRs
   ```

2. **驗證提交者**：
   ```yaml
   if: |
     github.event.pull_request.user.login == 'devin-ai-integration[bot]'
   ```

3. **檢查檔案範圍**：
   ```yaml
   # 只有特定檔案變更才 auto-merge
   paths:
     - 'docs/FAQ.md'
   ```

### 🛡️ Rate Limiting 和監控

**所有會創建 PRs 或推送代碼的 workflows 應該**：

1. **添加 concurrency 控制**：
   ```yaml
   concurrency:
     group: ${{ github.workflow }}-${{ github.ref }}
     cancel-in-progress: true
   ```

2. **設置 timeout**：
   ```yaml
   jobs:
     auto-create-pr:
       runs-on: ubuntu-latest
       timeout-minutes: 10  # 防止卡住
   ```

3. **添加條件檢查**：
   ```yaml
   if: |
     github.event_name == 'workflow_dispatch' ||
     github.ref == 'refs/heads/main'
   ```

### 📝 Workflow 變更檢查清單

創建或修改 workflows 時，確認：

- [ ] 所有 `push:` 和 `pull_request:` 觸發器都有 `branches` 或 `branches-ignore`
- [ ] Auto-merge workflows 有嚴格的 branches filter
- [ ] 會創建 PRs/推送的 workflows 不會觸發自己
- [ ] 使用 `workflow_dispatch` 允許手動觸發（方便調試）
- [ ] 設置適當的 `timeout-minutes`
- [ ] 有 `concurrency` 控制（如果適用）

### 🔍 審查工具

使用 audit script 檢查所有 workflows：

```bash
# 在 repo 根目錄運行
bash .github/scripts/audit_workflows.sh
```

這會自動檢測：
- 缺少 branches filter 的 workflows
- 可能導致無限循環的配置
- Auto-merge 風險

### 📚 參考資料

- **PR #447**: Orchestrator 無限循環修復範例
- **相關事件**: 66 個測試 PRs 被自動創建（2025-10-18）
- **Root Cause Analysis**: `/home/ubuntu/ORCHESTRATOR_INFINITE_LOOP_ROOT_CAUSE_ANALYSIS.md`
