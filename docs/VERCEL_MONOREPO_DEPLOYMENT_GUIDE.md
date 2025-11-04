# Vercel Monorepo 部署標準指南

## 問題背景

在 monorepo 架構中，多個前端應用共享同一個 Git repository，但需要獨立部署到 Vercel。常見問題包括：

1. **根目錄 `vercel.json` 覆蓋問題** - 根目錄的配置會影響所有子項目
2. **Build Command 衝突** - 不同應用使用不同的構建命令
3. **環境變數混淆** - 不同應用需要不同的環境變數
4. **部署失敗難以調試** - 錯誤訊息不明確，浪費大量時間

## 標準化解決方案

### 1. 目錄結構規範

```
morningai/
├── vercel.json                          # 主應用配置（Tenant Dashboard）
├── handoff/20250928/40_App/
│   ├── frontend-dashboard/              # Tenant Dashboard
│   │   ├── vercel.json                  # ❌ 不需要（使用根目錄配置）
│   │   ├── package.json
│   │   └── src/
│   ├── owner-console/                   # Owner Console
│   │   ├── vercel.json                  # ✅ 必須（獨立配置）
│   │   ├── package.json
│   │   └── src/
│   └── [future-app]/                    # 未來的應用
│       ├── vercel.json                  # ✅ 必須（獨立配置）
│       ├── package.json
│       └── src/
```

### 2. Vercel 項目配置規範

#### 規則 1：每個前端應用 = 一個獨立的 Vercel 項目

| 應用 | Vercel 項目名稱 | Git Repository | Root Directory |
|------|----------------|----------------|----------------|
| Tenant Dashboard | `morningai` | RC918/morningai | `/` 或 `handoff/.../frontend-dashboard` |
| Owner Console | `morningai-owner-console` | RC918/morningai | `handoff/.../owner-console` |
| Future App | `morningai-[app-name]` | RC918/morningai | `handoff/.../[app-name]` |

#### 規則 2：主應用 vs 子應用配置

**主應用（Tenant Dashboard）**：
- 使用根目錄 `vercel.json`
- 或在 Vercel Dashboard 設置 Root Directory

**子應用（Owner Console, 其他）**：
- **必須**在應用目錄內創建 `vercel.json`
- **必須**在 Vercel Dashboard 設置 Root Directory
- **必須**關閉所有 Override 開關

### 3. vercel.json 模板

#### 模板 A：根目錄配置（主應用）

```json
{
  "$schema": "https://openapi.vercel.sh/vercel.json",
  "framework": "vite",
  "buildCommand": "cd handoff/20250928/40_App/frontend-dashboard && npm run build",
  "installCommand": "cd handoff/20250928/40_App/frontend-dashboard && npm install --include=dev",
  "outputDirectory": "handoff/20250928/40_App/frontend-dashboard/dist",
  "rewrites": [
    {
      "source": "/(.*)",
      "destination": "/index.html"
    }
  ]
}
```

**使用時機**：
- 主要的 Tenant Dashboard
- 部署到根域名或主要子域名

#### 模板 B：子應用配置（獨立應用）

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

**使用時機**：
- Owner Console
- 任何獨立部署的前端應用
- 配合 Vercel Dashboard 的 Root Directory 設置

**重要**：子應用的命令不需要 `cd`，因為 Root Directory 已經設置為應用目錄。

### 4. Vercel Dashboard 配置檢查清單

創建新的 Vercel 項目時，按照以下步驟配置：

#### Step 1: 基本設置
- [ ] 項目名稱：`morningai-[app-name]`
- [ ] Git Repository：`RC918/morningai`
- [ ] Production Branch：`main`

#### Step 2: Build & Development Settings
- [ ] **Root Directory**：`handoff/20250928/40_App/[app-name]` ✅ 必須設置
- [ ] **Framework Preset**：Vite（或其他框架）
- [ ] **Build Command**：關閉 Override（讓 vercel.json 生效）
- [ ] **Output Directory**：關閉 Override（讓 vercel.json 生效）
- [ ] **Install Command**：關閉 Override（讓 vercel.json 生效）

#### Step 3: 環境變數
根據應用需求設置：
```
VITE_API_BASE_URL=https://morningai-backend-v2.onrender.com
VITE_OWNER_CONSOLE=true  # 僅 Owner Console
```

應用於：Production, Preview, Development

#### Step 4: 驗證
- [ ] 觸發部署
- [ ] 檢查構建日誌
- [ ] 訪問預覽 URL
- [ ] 測試功能正常

### 5. 常見錯誤和解決方案

#### 錯誤 1：找不到目錄
```
sh: line 1: cd: handoff/20250928/40_App/frontend-dashboard: No such file or directory
```

**原因**：Root Directory 設置錯誤，或 Install Command 包含錯誤的 `cd` 路徑

**解決方案**：
1. 檢查 Vercel Dashboard 的 Root Directory 設置
2. 確保 vercel.json 的命令不包含 `cd`（如果 Root Directory 已設置）
3. 關閉所有 Override 開關

#### 錯誤 2：環境變數未生效
```
console.log(import.meta.env.VITE_API_BASE_URL) // undefined
```

**原因**：環境變數未設置或未重新部署

**解決方案**：
1. 在 Vercel Dashboard 檢查環境變數
2. 確保應用於所有環境（Production, Preview, Development）
3. 重新部署應用

#### 錯誤 3：根目錄配置覆蓋子應用
```
# 子應用嘗試使用主應用的構建命令
```

**原因**：子應用沒有自己的 vercel.json

**解決方案**：
1. 在子應用目錄創建 vercel.json
2. 使用模板 B（子應用配置）
3. 確保 Root Directory 正確設置

### 6. 新應用部署流程

當需要部署新的前端應用時，按照以下流程：

#### Step 1: 創建應用目錄和配置
```bash
cd handoff/20250928/40_App
mkdir new-app
cd new-app

# 創建 vercel.json（使用模板 B）
cat > vercel.json << 'JSON'
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
JSON

# 創建 .env.example
cat > .env.example << 'ENV'
VITE_API_BASE_URL=https://morningai-backend-v2.onrender.com
VITE_APP_NAME=new-app
ENV
```

#### Step 2: 在 Vercel 創建項目
1. 登入 Vercel Dashboard
2. 點擊 "Add New Project"
3. 選擇 `RC918/morningai` repository
4. 配置：
   - Project Name: `morningai-new-app`
   - Root Directory: `handoff/20250928/40_App/new-app`
   - Framework: Vite
   - 關閉所有 Override 開關
5. 添加環境變數
6. 點擊 "Deploy"

#### Step 3: 驗證部署
1. 檢查構建日誌
2. 訪問預覽 URL
3. 測試功能
4. 合併到 main 分支

#### Step 4: 更新文檔
在 `ARCHITECTURE.md` 中記錄新應用：
```markdown
## 前端應用

| 應用 | 部署 URL | Vercel 項目 | 用途 |
|------|---------|-------------|------|
| Tenant Dashboard | dashboard.morningai.com | morningai | 租戶使用 |
| Owner Console | admin.morningai.com | morningai-owner-console | 平台管理 |
| New App | new-app.morningai.com | morningai-new-app | [用途說明] |
```

### 7. CI/CD 自動化驗證

為了防止配置錯誤，建議添加 CI 檢查：

```yaml
# .github/workflows/validate-vercel-config.yml
name: Validate Vercel Config

on:
  pull_request:
    paths:
      - '**/vercel.json'
      - 'handoff/**/package.json'

jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Validate vercel.json files
        run: |
          # 檢查所有 vercel.json 是否有效
          for file in $(find . -name "vercel.json" -not -path "*/node_modules/*"); do
            echo "Validating $file"
            jq empty "$file" || exit 1
          done
      
      - name: Check for conflicting configs
        run: |
          # 檢查子應用是否有獨立的 vercel.json
          apps=$(find handoff/20250928/40_App -maxdepth 1 -type d -not -name "40_App" -not -name "api-*")
          for app in $apps; do
            if [ -f "$app/package.json" ]; then
              if [ ! -f "$app/vercel.json" ]; then
                echo "Warning: $app has package.json but no vercel.json"
              fi
            fi
          done
```

### 8. 團隊協作規範

#### 對於 UI/UX 設計師
- 創建新前端應用時，**必須**同時創建 `vercel.json`
- 使用模板 B（子應用配置）
- 在 PR 中說明 Vercel 部署需求

#### 對於工程師
- 審查 PR 時，檢查是否有 `vercel.json`
- 驗證配置是否符合規範
- 測試部署是否成功

#### 對於 DevOps
- 維護 Vercel 項目列表
- 定期審查配置
- 更新文檔

### 9. 快速參考

#### 檢查清單：新應用部署
- [ ] 創建應用目錄
- [ ] 添加 `vercel.json`（使用模板 B）
- [ ] 添加 `.env.example`
- [ ] 在 Vercel 創建項目
- [ ] 設置 Root Directory
- [ ] 關閉所有 Override
- [ ] 添加環境變數
- [ ] 測試部署
- [ ] 更新 `ARCHITECTURE.md`

#### 故障排除步驟
1. 檢查 Vercel 構建日誌
2. 驗證 Root Directory 設置
3. 確認 vercel.json 存在且有效
4. 檢查環境變數
5. 嘗試清除緩存重新部署

### 10. 相關資源

- [Vercel Monorepo 官方文檔](https://vercel.com/docs/monorepos)
- [Vercel 配置參考](https://vercel.com/docs/projects/project-configuration)
- 內部文檔：`ARCHITECTURE.md`
- 內部文檔：`CONTRIBUTING.md`

---

**維護者**：DevOps Team  
**最後更新**：2025-10-23  
**版本**：1.0
