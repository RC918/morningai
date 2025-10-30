# Contribution Rules (Devin-friendly)

## Setup Instructions

### Python Dependencies

MorningAI uses service-separated dependency management. Each service has its own `requirements.txt`:

**Backend API Service**:
```bash
cd handoff/20250928/40_App/api-backend
pip install -r requirements.txt
```

**Orchestrator Service**:
```bash
cd orchestrator
pip install -r requirements.txt
pip install -e .  # Install orchestrator package
```

**Development/Testing Tools** (root):
```bash
pip install -r requirements.txt  # pytest, flake8, python-dotenv
```

**Important**: 
- Do NOT use root `requirements.txt` to run services
- Each service has its own `requirements.txt` with all required dependencies
- Root `requirements.txt` is only for development/testing tools

For detailed requirements structure, see [README.md](../README.md#python-依賴管理).

---

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

---

## Vercel 部署規範

### 🎯 核心原則

在 monorepo 中部署多個前端應用到 Vercel 時，必須遵循以下規範以避免配置衝突和部署失敗。

### 📋 必須遵守的規則

#### 規則 1：每個獨立前端應用必須有自己的 `vercel.json`

**例外**：主應用（Tenant Dashboard）可以使用根目錄的 `vercel.json`

```
✅ 正確結構：
handoff/20250928/40_App/
├── frontend-dashboard/     # 主應用，使用根目錄 vercel.json
│   └── package.json
├── owner-console/          # 獨立應用，必須有自己的 vercel.json
│   ├── vercel.json        ✅ 必須
│   └── package.json
└── future-app/             # 未來的應用
    ├── vercel.json        ✅ 必須
    └── package.json

❌ 錯誤結構：
handoff/20250928/40_App/
├── owner-console/
│   └── package.json       ❌ 缺少 vercel.json
```

#### 規則 2：使用標準化的 `vercel.json` 模板

**子應用模板**（Owner Console, 其他獨立應用）：
```json
{
  "$schema": "https://openapi.vercel.sh/vercel.json",
  "framework": "vite",
  "buildCommand": "npm run build",
  "installCommand": "npm install --include=dev",
  "outputDirectory": "dist",
  "rewrites": [
    {
      "source": "/(.*)",
      "destination": "/index.html"
    }
  ]
}
```

**重要**：
- ❌ 不要在命令中使用 `cd`（Root Directory 已在 Vercel Dashboard 設置）
- ✅ 使用簡化的命令（`npm run build` 而非 `cd ... && npm run build`）
- ✅ 必須包含 `rewrites` 配置（支持 SPA 客戶端路由）

#### 規則 3：Vercel Dashboard 配置檢查清單

創建新的 Vercel 項目時：

- [ ] **項目名稱**：`morningai-[app-name]`
- [ ] **Root Directory**：`handoff/20250928/40_App/[app-name]` ✅ 必須設置
- [ ] **Build Command**：關閉 Override（讓 vercel.json 生效）
- [ ] **Output Directory**：關閉 Override（讓 vercel.json 生效）
- [ ] **Install Command**：關閉 Override（讓 vercel.json 生效）
- [ ] **環境變數**：根據應用需求設置（應用於所有環境）

### 🚨 常見錯誤和解決方案

#### 錯誤 1：找不到目錄
```
sh: line 1: cd: handoff/.../frontend-dashboard: No such file or directory
```

**原因**：根目錄的 `vercel.json` 覆蓋了子應用的配置

**解決方案**：
1. 在子應用目錄創建獨立的 `vercel.json`
2. 確保 Vercel Dashboard 的 Root Directory 正確設置
3. 關閉所有 Override 開關

#### 錯誤 2：環境變數未生效
```javascript
console.log(import.meta.env.VITE_API_BASE_URL) // undefined
```

**解決方案**：
1. 在 Vercel Dashboard 檢查環境變數設置
2. 確保應用於所有環境（Production, Preview, Development）
3. 重新部署應用

### 📝 PR 提交檢查清單

提交包含新前端應用或修改 Vercel 配置的 PR 時：

- [ ] 子應用包含 `vercel.json` 文件
- [ ] `vercel.json` 使用標準模板
- [ ] 包含 `.env.example` 文件
- [ ] PR 描述中說明 Vercel 部署需求
- [ ] 在 `ARCHITECTURE.md` 中記錄新應用

### 🔍 CI 自動驗證

CI 會自動檢查：
- `vercel.json` 語法是否正確
- 前端應用是否缺少 `vercel.json`
- 配置結構是否符合規範

查看 `.github/workflows/validate-vercel-config.yml` 了解詳情。

### 📖 詳細文檔

完整的部署指南和故障排除：
- **[Vercel Monorepo 部署標準指南](./VERCEL_MONOREPO_DEPLOYMENT_GUIDE.md)**

---

**最後更新**：2025-10-23  
**相關 PR**：#639, #641
