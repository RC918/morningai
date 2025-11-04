# Vercel Deployment Guide

## 🚀 Vercel 部署最佳實踐

本文檔記錄 Morning AI 專案在 Vercel 上的標準部署配置與最佳實踐。

---

## 📋 標準配置

### vercel.json 範本

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

### 關鍵配置說明

#### 1. 不使用 rootDirectory

**❌ 錯誤配置**：
```json
{
  "rootDirectory": "handoff/20250928/40_App/frontend-dashboard",
  "buildCommand": "npm run build"
}
```

**✅ 正確配置**：
```json
{
  "buildCommand": "cd handoff/20250928/40_App/frontend-dashboard && npm run build",
  "installCommand": "cd handoff/20250928/40_App/frontend-dashboard && npm install --include=dev",
  "outputDirectory": "handoff/20250928/40_App/frontend-dashboard/dist"
}
```

**原因**：
- Vercel 的 rootDirectory 會與 Production Overrides 衝突
- 使用完整路徑更明確，避免配置被覆蓋
- 符合工程團隊建議

#### 2. 明確指定 installCommand

**為什麼需要？**
- Vercel 預設會嘗試自動偵測（pnpm/yarn/npm）
- Production Overrides 可能使用舊設定
- 明確指定避免使用錯誤的 package manager

**正確寫法**：
```json
{
  "installCommand": "cd handoff/20250928/40_App/frontend-dashboard && npm install --include=dev"
}
```

**注意事項**：
- 使用 `--include=dev` 確保安裝 devDependencies（Vite 需要）
- 不要使用 `npm ci`（Vercel 環境可能沒有 package-lock.json）

#### 3. 完整的 outputDirectory 路徑

```json
{
  "outputDirectory": "handoff/20250928/40_App/frontend-dashboard/dist"
}
```

---

## 🔧 Vercel Dashboard 設定

### Production Overrides

**重要**：清除所有 Production Overrides 設定，讓 vercel.json 生效。

**檢查步驟**：
1. 進入 Vercel Dashboard → Project Settings
2. 點擊 "General" → "Build & Development Settings"
3. 確認 Production Overrides 區塊為空或與 vercel.json 一致

### Framework Preset

- **Framework**: Vite
- **Build Command**: 留空（使用 vercel.json）
- **Output Directory**: 留空（使用 vercel.json）
- **Install Command**: 留空（使用 vercel.json）

---

## 🚨 常見問題排查

### 問題 1: Vercel 使用 pnpm 而非 npm

**症狀**：
```
Running "cd handoff/20250928/40_App/frontend-dashboard && pnpm install"
ERR_INVALID_THIS
```

**根本原因**：
1. Vercel Production Overrides 使用舊設定（pnpm）
2. vercel.json 的 installCommand 被忽略
3. .vercelignore 排除了 pnpm-lock.yaml

**解決方案**：
```json
{
  "installCommand": "cd handoff/20250928/40_App/frontend-dashboard && npm install --include=dev"
}
```

並清除 Vercel Dashboard 的 Production Overrides。

### 問題 2: 找不到 dist 目錄

**症狀**：
```
Error: No Output Directory named "dist" found after the Build completed.
```

**原因**：
- outputDirectory 路徑不正確
- buildCommand 執行失敗

**解決方案**：
```json
{
  "buildCommand": "cd handoff/20250928/40_App/frontend-dashboard && npm run build",
  "outputDirectory": "handoff/20250928/40_App/frontend-dashboard/dist"
}
```

### 問題 3: 路由 404 錯誤

**症狀**：
- 首頁正常，但重新整理子路由時出現 404

**原因**：
- SPA 需要將所有路由重定向到 index.html

**解決方案**：
```json
{
  "rewrites": [
    {
      "source": "/(.*)",
      "destination": "/index.html"
    }
  ]
}
```

---

## 📊 部署檢查清單

### 部署前檢查

- [ ] vercel.json 已正確配置
- [ ] package-lock.json 已提交到 Git
- [ ] 本地 `npm run build` 測試通過
- [ ] .vercelignore 不排除必要檔案
- [ ] 環境變數已在 Vercel Dashboard 設定

### 部署後驗證

- [ ] Preview URL 可正常訪問
- [ ] 所有路由正常運作
- [ ] 靜態資源載入正常
- [ ] 控制台無錯誤訊息
- [ ] SEO meta tags 正確顯示

---

## 🔍 除錯技巧

### 1. 查看 Build Logs

```
Vercel Dashboard → Deployments → [選擇部署] → Build Logs
```

**關鍵資訊**：
- 使用的 package manager（npm/pnpm/yarn）
- 執行的 install/build 指令
- 錯誤訊息與堆疊追蹤

### 2. 檢查 Deployment Settings

```
Vercel Dashboard → Project Settings → General
```

**確認項目**：
- Framework Preset
- Root Directory（應為空）
- Build & Development Settings
- Production Overrides（應為空或與 vercel.json 一致）

### 3. 本地模擬 Vercel 環境

```bash
# 安裝 Vercel CLI
npm install -g vercel

# 本地測試
vercel dev

# 模擬生產建置
vercel build
```

---

## 📚 .vercelignore 最佳實踐

### 標準 .vercelignore

```
# 依賴管理
node_modules/
pnpm-lock.yaml
yarn.lock

# 測試與覆蓋率
coverage/
.nyc_output/
*.test.js
*.spec.js

# 開發工具
.vscode/
.idea/
*.log

# 環境變數（本地）
.env.local
.env.*.local

# 文檔與報告
docs/
*.md
!README.md
```

**注意事項**：
- ✅ 排除 pnpm-lock.yaml（避免 pnpm 被使用）
- ✅ 保留 package-lock.json（npm 需要）
- ✅ 排除測試檔案（加速建置）

---

## 🔄 持續改進

### 監控指標

1. **建置時間**：目標 < 2 分鐘
2. **部署成功率**：目標 > 95%
3. **Preview URL 可用性**：目標 100%

### 定期檢查

- 每月檢查 Vercel 配置是否與 vercel.json 一致
- 每季更新依賴版本
- 每半年審查 .vercelignore 規則

---

## 📞 支援資源

- [Vercel Documentation](https://vercel.com/docs)
- [vercel.json Configuration](https://vercel.com/docs/projects/project-configuration)
- [Deployment Troubleshooting](https://vercel.com/docs/deployments/troubleshoot-a-build)

---

## 🔄 版本歷史

| 日期 | 版本 | 變更內容 |
|------|------|----------|
| 2025-10-21 | 1.0.0 | 初版發布，記錄 pnpm 衝突解決方案 |

---

## 📞 聯絡資訊

如有任何疑問，請聯絡：
- **技術負責人**：Ryan Chen (@RC918)
- **問題回報**：GitHub Issues
