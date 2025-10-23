# Tolgee 翻譯管理系統設定指南

## 概述

Morning AI 使用 [Tolgee](https://tolgee.io) 作為翻譯管理平台，提供：
- **In-context 編輯**：直接在應用中編輯翻譯（按 Alt+T 開啟）
- **即時同步**：翻譯變更即時反映到應用
- **協作翻譯**：團隊成員可共同管理翻譯
- **版本控制**：翻譯變更可追蹤和回溯

## 應用範圍

目前使用 Tolgee 的應用：
- ✅ **frontend-dashboard** - 用戶主控台
- ✅ **owner-console** - 管理員控台

## 環境變數配置

### 必要變數

在以下位置設定這些環境變數：

#### 1. 本地開發環境

在各應用的根目錄創建 `.env.local` 文件（**不要提交到 git**）：

```bash
# frontend-dashboard/.env.local
VITE_TOLGEE_API_URL=https://app.tolgee.io
VITE_TOLGEE_API_KEY=your_api_key_here
VITE_TOLGEE_PROJECT_ID=your_project_id_here
```

```bash
# owner-console/.env.local
VITE_TOLGEE_API_URL=https://app.tolgee.io
VITE_TOLGEE_API_KEY=your_api_key_here
VITE_TOLGEE_PROJECT_ID=your_project_id_here
```

#### 2. Vercel 部署環境

在 Vercel Dashboard 中設定：

1. 登入 [Vercel Dashboard](https://vercel.com/dashboard)
2. 選擇專案（frontend-dashboard 或 owner-console）
3. 進入 **Settings** → **Environment Variables**
4. 加入以下變數：

| 變數名稱 | 值 | 環境 |
|---------|-----|------|
| `VITE_TOLGEE_API_URL` | `https://app.tolgee.io` | Production, Preview, Development |
| `VITE_TOLGEE_API_KEY` | `[您的 API Key]` | Production, Preview, Development |
| `VITE_TOLGEE_PROJECT_ID` | `[您的 Project ID]` | Production, Preview, Development |

#### 3. GitHub Secrets（可選）

如果 GitHub Actions 需要建置前端：

1. 進入 Repository → **Settings** → **Secrets and variables** → **Actions**
2. 加入相同的變數

### 變數說明

| 變數 | 必要性 | 說明 | 安全等級 |
|------|--------|------|----------|
| `VITE_TOLGEE_API_URL` | 可選 | Tolgee API 端點 | Public |
| `VITE_TOLGEE_API_KEY` | 可選 | Tolgee API 金鑰（用於 in-context 編輯） | Secret |
| `VITE_TOLGEE_PROJECT_ID` | 可選 | Tolgee 專案 ID | Public |

**重要**：應用在沒有 Tolgee 憑證的情況下仍可正常運作，會使用本地的 JSON 翻譯檔案。

## 獲取 Tolgee 憑證

### 1. 登入 Tolgee

訪問 [https://app.tolgee.io](https://app.tolgee.io) 並登入您的帳號。

### 2. 找到 Project ID

1. 選擇您的專案（例如：Morning AI）
2. 在專案設定中找到 **Project ID**
3. 複製 Project ID

### 3. 創建 API Key

1. 在專案設定中進入 **API Keys**
2. 點擊 **Create new API key**
3. 設定權限：
   - ✅ `translations.view` - 查看翻譯
   - ✅ `translations.edit` - 編輯翻譯
   - ✅ `keys.edit` - 編輯翻譯鍵
4. 複製生成的 API Key（**只會顯示一次**）

## 使用 In-Context 編輯

### 啟用 DevTools

In-context 編輯功能只在開發環境中啟用：

```javascript
// src/tolgee.js
const tolgee = Tolgee()
  .use(DevTools()) // 只在 DEV 模式啟用
  .init({
    enableDevTools: import.meta.env.DEV, // 只在開發環境啟用
    // ...
  });
```

### 使用步驟

1. **啟動開發伺服器**：
   ```bash
   npm run dev
   ```

2. **開啟 DevTools**：
   - 按 `Alt + T`（Windows/Linux）
   - 或 `Option + T`（Mac）

3. **編輯翻譯**：
   - 點擊頁面上的任何文字
   - 在彈出的編輯器中修改翻譯
   - 變更會即時反映

4. **同步到 Tolgee**：
   - 編輯的翻譯會自動同步到 Tolgee 平台
   - 其他開發者可以看到您的變更

## 翻譯檔案結構

### 本地翻譯檔案

應用使用本地 JSON 檔案作為 fallback：

```
src/
  locales/
    en-US.json    # 英文翻譯
    zh-TW.json    # 繁體中文翻譯
```

### 翻譯鍵命名規範

使用點號分隔的命名空間：

```json
{
  "dashboard": {
    "title": "控制台",
    "stats": {
      "totalTenants": "總租戶數",
      "activeAgents": "活躍代理"
    }
  }
}
```

在代碼中使用：

```javascript
const { t } = useTranslation();
<h1>{t('dashboard.title')}</h1>
<p>{t('dashboard.stats.totalTenants')}</p>
```

## 故障排除

### 問題 1：In-context 編輯無法開啟

**原因**：
- 缺少 Tolgee API Key 或 Project ID
- 不在開發環境

**解決方案**：
1. 確認 `.env.local` 中有正確的 Tolgee 憑證
2. 確認使用 `npm run dev` 啟動（不是 `npm run build`）
3. 檢查瀏覽器控制台是否有錯誤訊息

### 問題 2：翻譯沒有顯示

**原因**：
- 翻譯鍵不存在
- 語言設定錯誤

**解決方案**：
1. 檢查翻譯鍵是否在 `locales/*.json` 中存在
2. 確認語言切換器設定正確
3. 檢查 i18n 配置：
   ```javascript
   // src/i18n.js
   i18n.init({
     lng: 'zh-TW', // 預設語言
     fallbackLng: 'en-US', // 備用語言
   });
   ```

### 問題 3：部署後翻譯無法載入

**原因**：
- Vercel 環境變數未設定
- 建置時沒有包含翻譯檔案

**解決方案**：
1. 確認 Vercel 環境變數已設定
2. 檢查 `vite.config.js` 是否包含翻譯檔案：
   ```javascript
   export default defineConfig({
     // ...
     build: {
       rollupOptions: {
         input: {
           main: './index.html',
         },
       },
     },
   });
   ```

## 最佳實踐

### 1. 翻譯鍵管理

- ✅ 使用描述性的鍵名：`dashboard.stats.totalTenants`
- ✅ 使用命名空間組織：`dashboard.*`, `settings.*`
- ❌ 避免使用通用鍵名：`title`, `button`

### 2. 翻譯內容

- ✅ 保持翻譯簡潔明確
- ✅ 使用變數處理動態內容：`歡迎回來，{{name}}！`
- ❌ 避免在翻譯中硬編碼數字或日期格式

### 3. 協作流程

1. **開發者**：在 in-context 編輯器中添加新的翻譯鍵
2. **翻譯者**：在 Tolgee 平台上完善翻譯
3. **審核者**：在 Tolgee 平台上審核翻譯
4. **同步**：定期從 Tolgee 匯出翻譯到本地 JSON 檔案

### 4. 版本控制

- ✅ 提交本地 JSON 翻譯檔案到 git
- ❌ 不要提交 `.env.local` 或 API Key
- ✅ 在 PR 中說明翻譯變更

## 相關資源

- [Tolgee 官方文檔](https://tolgee.io/docs)
- [Tolgee React 整合](https://tolgee.io/integrations/react)
- [react-i18next 文檔](https://react.i18next.com/)
- [專案 env.schema.yaml](../config/env.schema.yaml) - 環境變數定義

## 支援

如有問題，請聯繫：
- **技術支援**：開發團隊
- **翻譯問題**：Tolgee 平台管理員
- **環境變數問題**：DevOps 團隊
