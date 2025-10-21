# Vercel Deployment Failure Incident Report

## 📋 事件摘要

**事件日期**：2025-10-21  
**影響範圍**：PR #527 Landing Page SEO 優化部署失敗  
**嚴重程度**：高（阻擋部署）  
**解決時間**：約 2 小時  
**根本原因**：Vercel 配置與依賴管理工具不一致  

---

## 🔍 問題描述

### 初始症狀

Vercel 部署失敗，錯誤訊息：

```
Running "cd frontend-dashboard-deploy && pnpm install"
ERR_PNPM_FETCH_404  GET https://registry.npmjs.org/@esbuild%2flinux-x64: Not Found - 404
ERR_INVALID_THIS
Value of 'this' must be of type URLSearchParams
```

### 關鍵觀察

1. **錯誤的目錄名稱**：Vercel 使用 `frontend-dashboard-deploy` 而非 `frontend-dashboard`
2. **錯誤的 package manager**：Vercel 使用 `pnpm install` 而非 `npm install`
3. **錯誤的分支**：Vercel 從 `devin/1760984943-improve-test-coverage` 建置，而非當前 PR 分支
4. **URLSearchParams 錯誤**：pnpm 內部錯誤，無法正確處理 registry 請求

---

## 🕵️ 根本原因分析

### 1. Vercel 配置層級衝突

Vercel 有多個配置層級，優先順序如下：

```
Production Overrides (最高優先級)
  ↓
vercel.json
  ↓
Framework Preset (最低優先級)
```

**問題**：
- vercel.json 設定：`"installCommand": "npm install --include=dev"`
- Production Overrides 設定：`pnpm install`（舊設定）
- **結果**：Production Overrides 覆蓋了 vercel.json

### 2. rootDirectory 導致路徑混淆

**原始配置**：
```json
{
  "rootDirectory": "handoff/20250928/40_App/frontend-dashboard",
  "buildCommand": "npm run build"
}
```

**問題**：
- Vercel 在處理 rootDirectory 時，會與 Production Overrides 產生衝突
- 導致實際執行的目錄變成 `frontend-dashboard-deploy`（舊目錄名）

### 3. pnpm-lock.yaml 被排除

**.vercelignore 內容**：
```
pnpm-lock.yaml
```

**問題**：
- Vercel 使用 pnpm install
- 但 pnpm-lock.yaml 被排除
- 導致 pnpm 無法正確解析依賴版本
- 引發 ERR_INVALID_THIS 錯誤

### 4. 依賴管理工具不一致

**專案實際使用**：npm  
**Vercel 嘗試使用**：pnpm  
**結果**：
- 缺少 pnpm-lock.yaml
- pnpm 無法正確安裝依賴
- 建置失敗

---

## ✅ 解決方案

### 1. 移除 rootDirectory，使用完整路徑

**修改前**：
```json
{
  "rootDirectory": "handoff/20250928/40_App/frontend-dashboard",
  "buildCommand": "npm run build",
  "installCommand": "npm install --include=dev",
  "outputDirectory": "dist"
}
```

**修改後**：
```json
{
  "buildCommand": "cd handoff/20250928/40_App/frontend-dashboard && npm run build",
  "installCommand": "cd handoff/20250928/40_App/frontend-dashboard && npm install --include=dev",
  "outputDirectory": "handoff/20250928/40_App/frontend-dashboard/dist"
}
```

**效果**：
- ✅ 避免 rootDirectory 與 Production Overrides 衝突
- ✅ 路徑明確，不會被覆蓋
- ✅ 符合工程團隊建議

### 2. 清除 Vercel Production Overrides

**操作步驟**：
1. 進入 Vercel Dashboard → Project Settings
2. General → Build & Development Settings
3. 清除 Production Overrides 區塊

**效果**：
- ✅ vercel.json 的 installCommand 生效
- ✅ 使用 npm 而非 pnpm

### 3. 統一使用 npm

**變更內容**：
- GitHub Actions workflows：pnpm → npm
- vercel.json：明確指定 npm
- 移除 pnpm-lock.yaml
- 提交 package-lock.json

**效果**：
- ✅ 所有環境使用相同 package manager
- ✅ 避免 lockfile 衝突
- ✅ CI/CD 與 Vercel 一致

---

## 📊 時間軸

| 時間 | 事件 |
|------|------|
| 10:00 | PR #527 建立，Vercel 自動部署 |
| 10:05 | Vercel 部署失敗，錯誤：pnpm install 失敗 |
| 10:10 | 檢查 Vercel 建置日誌，發現使用 pnpm |
| 10:20 | 分析 vercel.json，發現 rootDirectory 設定 |
| 10:30 | 檢查 .vercelignore，發現排除 pnpm-lock.yaml |
| 10:45 | 識別根本原因：Production Overrides 覆蓋 vercel.json |
| 11:00 | 實施解決方案：移除 rootDirectory |
| 11:10 | 推送修復，Vercel 重新部署 |
| 11:15 | ✅ 部署成功，所有 CI 檢查通過 |

---

## 🎯 預防措施

### 1. 文檔化

- ✅ 建立 [DEPENDENCY_MANAGEMENT.md](./DEPENDENCY_MANAGEMENT.md)
- ✅ 建立 [VERCEL_DEPLOYMENT_GUIDE.md](./VERCEL_DEPLOYMENT_GUIDE.md)
- ✅ 更新 CONTRIBUTING.md

### 2. 自動化檢查

- ✅ 新增 `.github/workflows/dependency-check.yml`
- 自動檢測：
  - 禁止的 lockfile（pnpm-lock.yaml, yarn.lock）
  - package-lock.json 是否存在
  - vercel.json 是否使用 npm
  - GitHub Actions 是否使用 npm

### 3. 團隊培訓

- 明確規定：專案統一使用 npm
- 禁止使用 pnpm/yarn
- 新成員 onboarding 時說明依賴管理政策

### 4. 定期審查

- 每月檢查 Vercel 配置
- 每季審查 CI/CD workflows
- 確保所有環境使用相同 package manager

---

## 📈 影響評估

### 正面影響

1. **系統韌性提升**：
   - 新增自動化檢查，防止類似問題再發生
   - 文檔化最佳實踐，降低人為錯誤

2. **團隊效率提升**：
   - 明確的依賴管理政策
   - 標準化的部署流程
   - 減少除錯時間

3. **知識累積**：
   - 詳細的事件報告
   - 可重現的解決方案
   - 團隊學習資源

### 技術債務清理

- ✅ 移除 pnpm 相關配置
- ✅ 統一 CI/CD 與 Vercel 配置
- ✅ 清理過時的 Production Overrides

---

## 🔄 後續行動

### 立即行動（已完成）

- [x] 修復 vercel.json 配置
- [x] 統一使用 npm
- [x] 建立文檔
- [x] 新增 CI 檢查

### 短期行動（1 週內）

- [ ] 審查所有 Vercel 專案配置
- [ ] 確認 Production Overrides 已清除
- [ ] 團隊內部分享事件報告

### 長期行動（1 個月內）

- [ ] 建立 Vercel 配置模板
- [ ] 自動化 Vercel 配置驗證
- [ ] 定期審查依賴管理政策

---

## 📚 學到的教訓

### 1. 配置層級很重要

Vercel 的 Production Overrides 會覆蓋 vercel.json，必須確保兩者一致或清除 Overrides。

### 2. 依賴管理工具要統一

混用 npm/pnpm/yarn 會導致：
- lockfile 衝突
- CI/CD 不一致
- 難以除錯的錯誤

### 3. 文檔化是關鍵

沒有文檔，相同問題會重複發生。建立清晰的文檔與自動化檢查是預防的最佳方式。

### 4. rootDirectory 不是必要的

使用完整路徑更明確，避免與其他配置衝突。

---

## 📞 聯絡資訊

**事件負責人**：Devin AI  
**技術審查**：Ryan Chen (@RC918)  
**問題回報**：GitHub Issues

---

## 🔄 版本歷史

| 日期 | 版本 | 變更內容 |
|------|------|----------|
| 2025-10-21 | 1.0.0 | 初版發布，記錄 Vercel pnpm 衝突事件 |
