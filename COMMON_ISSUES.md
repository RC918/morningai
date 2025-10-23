# 常見問題與解決方案 (Common Issues and Solutions)

本文檔記錄專案中常見的問題及其解決方案，幫助團隊成員避免重複犯錯。

---

## 目錄

1. [Vercel 部署問題](#vercel-部署問題)
2. [Package Lock 衝突](#package-lock-衝突)
3. [Git Workflow](#git-workflow)

---

## Vercel 部署問題

### ❌ 問題：`rootDirectory` 屬性導致部署失敗

**錯誤訊息：**
```
The `vercel.json` schema validation failed with the following message: 
should NOT have additional property `rootDirectory`
```

**原因：**
Vercel 的 `vercel.json` schema 不支援 `rootDirectory` 屬性。這是一個常見的誤解，因為其他部署平台可能支援此屬性。

**❌ 錯誤的配置：**
```json
{
  "$schema": "https://openapi.vercel.sh/vercel.json",
  "framework": "vite",
  "buildCommand": "pnpm run build",
  "installCommand": "pnpm install --frozen-lockfile",
  "outputDirectory": "dist",
  "rootDirectory": "frontend-dashboard-deploy",  // ❌ 不支援
  "rewrites": [...]
}
```

**✅ 正確的配置：**
```json
{
  "$schema": "https://openapi.vercel.sh/vercel.json",
  "framework": "vite",
  "buildCommand": "cd handoff/20250928/40_App/frontend-dashboard && npm run build",
  "installCommand": "cd handoff/20250928/40_App/frontend-dashboard && npm install --include=dev",
  "outputDirectory": "handoff/20250928/40_App/frontend-dashboard/dist",
  "rewrites": [...]
}
```

**解決方案：**
1. 移除 `rootDirectory` 屬性
2. 在 `buildCommand` 和 `installCommand` 中使用 `cd` 命令切換到正確的目錄
3. 在 `outputDirectory` 中使用完整的相對路徑

**相關 PR：** #588

**參考資料：**
- [Vercel Configuration Documentation](https://vercel.com/docs/concepts/projects/project-configuration)
- [Vercel JSON Schema](https://openapi.vercel.sh/vercel.json)

---

## Package Lock 衝突

### ❌ 問題：`package-lock.json` 合併衝突

**錯誤訊息：**
```
CONFLICT (content): Merge conflict in handoff/20250928/40_App/frontend-dashboard/package-lock.json
```

**原因：**
- `package-lock.json` 是自動生成的檔案，包含所有依賴的精確版本
- 當多個分支同時修改 `package.json` 或更新依賴時，會產生衝突
- 手動解決 `package-lock.json` 的衝突非常困難且容易出錯

**❌ 錯誤的解決方式：**
- ❌ 手動編輯 `package-lock.json` 來解決衝突
- ❌ 隨意選擇一方的版本而不驗證

**✅ 正確的解決方式：**

#### 方法 1：接受目標分支的版本（推薦用於簡單情況）

```bash
# 假設要合併 main 到你的分支
git merge main

# 如果出現衝突，接受 main 的版本
git checkout --theirs handoff/20250928/40_App/frontend-dashboard/package-lock.json
git add handoff/20250928/40_App/frontend-dashboard/package-lock.json
git commit -m "Merge main: accept main's package-lock.json"
```

#### 方法 2：重新生成（推薦用於複雜情況）

```bash
# 1. 合併時出現衝突
git merge main

# 2. 刪除衝突的 package-lock.json
cd handoff/20250928/40_App/frontend-dashboard
rm package-lock.json

# 3. 重新生成
npm install

# 4. 提交
git add package-lock.json
git commit -m "Merge main: regenerate package-lock.json"
```

**注意事項：**
- ⚠️ 重新生成後，務必測試應用是否正常運行
- ⚠️ 如果使用 `npm install` 失敗，優先使用方法 1
- ⚠️ 提交前檢查 `package-lock.json` 的變更是否合理

**相關 PR：** #588

---

## Git Workflow

### 最佳實踐

#### 1. 合併前先更新本地分支

```bash
# 在開始工作前，先同步 main
git checkout main
git pull origin main

# 切回你的分支並合併最新的 main
git checkout your-branch
git merge main
```

#### 2. 處理衝突的一般流程

```bash
# 1. 嘗試合併
git merge main

# 2. 如果有衝突，查看衝突檔案
git status

# 3. 解決衝突
# - 對於程式碼檔案：手動編輯
# - 對於 package-lock.json：使用上述方法

# 4. 標記為已解決
git add <resolved-files>

# 5. 完成合併
git commit
```

#### 3. 避免衝突的建議

- ✅ 經常從 main 合併到你的分支
- ✅ 保持 PR 小而專注
- ✅ 在修改 `package.json` 後立即提交
- ✅ 與團隊溝通正在修改的檔案

---

## 檢查清單

### 提交 PR 前

- [ ] 已從 main 合併最新變更
- [ ] 已解決所有衝突
- [ ] 本地測試通過
- [ ] CI 檢查通過
- [ ] `vercel.json` 配置正確（如有修改）
- [ ] `package-lock.json` 已正確更新（如有依賴變更）

### 審查 PR 時

- [ ] 檢查 `vercel.json` 是否使用了不支援的屬性
- [ ] 檢查 `package-lock.json` 的變更是否合理
- [ ] 驗證部署預覽是否正常
- [ ] 確認沒有意外的檔案變更

---

## 相關資源

### 文檔
- [CONTRIBUTING.md](./CONTRIBUTING.md) - 貢獻指南
- [Vercel Documentation](https://vercel.com/docs)
- [npm Documentation](https://docs.npmjs.com/)

### 工具
- [Vercel CLI](https://vercel.com/docs/cli) - 本地測試部署
- [npm-check-updates](https://www.npmjs.com/package/npm-check-updates) - 檢查依賴更新

---

## 回報新問題

如果你遇到了新的常見問題，請：

1. 在 GitHub Issues 中創建一個新 issue，標籤為 `documentation`
2. 描述問題、原因和解決方案
3. 提供相關的 PR 連結
4. 團隊會將其添加到本文檔中

---

**最後更新：** 2025-10-22  
**維護者：** @RC918  
**相關 PR：** #588
