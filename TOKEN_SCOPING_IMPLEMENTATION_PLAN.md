# Token 作用域化實作計劃

**目標**: 將全域 CSS 變數轉換為作用域化的主題容器  
**優先級**: 🔴 **P0** (Week 3-4 關鍵任務)  
**預估工時**: 3-4 天  
**風險**: 🟡 **中等** (波及面大，需要視覺回歸測試)

---

## 📋 執行摘要

### 目標

將當前的全域 Design Tokens 轉換為作用域化的主題系統，使用 `.theme-apple` 容器類別，避免全域樣式污染，提升可維護性與可擴展性。

### 關鍵成果

- ✅ 建立 `.theme-apple` 主題容器
- ✅ 識別所有全域樣式
- ✅ 漸進式遷移所有頁面
- ✅ 執行視覺回歸測試
- ✅ 建立回滾策略

---

## 🎯 為什麼需要 Token 作用域化？

### 當前問題

1. **全域污染**: 所有 CSS 變數都定義在 `:root`，容易與其他樣式衝突
2. **難以維護**: 無法輕鬆切換主題或支援多主題
3. **擴展困難**: 未來要支援多品牌/多主題時會很困難
4. **測試困難**: 全域樣式難以隔離測試

### 解決方案

使用 **作用域化主題容器** (`.theme-apple`)，將所有 Design Tokens 封裝在特定容器內，實現:

- ✅ 樣式隔離
- ✅ 主題切換
- ✅ 多品牌支援
- ✅ 更好的可測試性

---

## 📊 當前 Design Tokens 分析

### Token 類別

根據 `docs/UX/tokens.json`，我們有以下 Token 類別:

1. **Color Tokens** (最多)
   - Primary: 9 個色階
   - Accent (Purple, Orange): 各 9 個色階
   - Semantic (Success, Error, Warning, Info): 各 9 個色階
   - Neutral: 9 個色階
   - Background: 3 個

2. **Typography Tokens**
   - Font Family: 3 個
   - Font Size: 7 個
   - Line Height: 7 個
   - Font Weight: 4 個

3. **Spacing Tokens**: 8 個

4. **Radius Tokens**: 6 個

5. **Shadow Tokens**: 5 個

6. **Animation Tokens**
   - Duration: 4 個
   - Easing: 4 個

7. **Breakpoint Tokens**: 3 個

**總計**: 約 **120+ Design Tokens**

---

## 🔍 識別全域樣式

### 步驟 1: 搜尋全域 CSS 變數

```bash
# 搜尋所有 :root 定義
grep -r ":root" handoff/20250928/40_App/frontend-dashboard/src --include="*.css"

# 搜尋所有 CSS 變數使用
grep -r "var(--" handoff/20250928/40_App/frontend-dashboard/src --include="*.css" --include="*.jsx"
```

### 步驟 2: 分析 Tailwind 配置

檢查是否有 Tailwind 擴展配置使用了全域變數。

### 步驟 3: 檢查內聯樣式

```bash
# 搜尋內聯樣式中的 CSS 變數
grep -r "style={{" handoff/20250928/40_App/frontend-dashboard/src --include="*.jsx" | grep "var(--"
```

---

## 🏗️ 實作步驟

### Phase 1: 建立主題容器 (1 天)

#### 1.1 建立主題 CSS 檔案

**檔案**: `handoff/20250928/40_App/frontend-dashboard/src/styles/theme-apple.css`

```css
/* Apple Theme - Scoped Design Tokens */

.theme-apple {
  /* Color Tokens - Primary */
  --color-primary-50: #eff6ff;
  --color-primary-100: #dbeafe;
  --color-primary-200: #bfdbfe;
  --color-primary-300: #93c5fd;
  --color-primary-400: #60a5fa;
  --color-primary-500: #0ea5e9;
  --color-primary-600: #0284c7;
  --color-primary-700: #0369a1;
  --color-primary-800: #075985;
  --color-primary-900: #0c4a6e;

  /* Color Tokens - Accent Purple */
  --color-accent-purple-50: #faf5ff;
  --color-accent-purple-100: #f3e8ff;
  --color-accent-purple-200: #e9d5ff;
  --color-accent-purple-300: #d8b4fe;
  --color-accent-purple-400: #c084fc;
  --color-accent-purple-500: #8b5cf6;
  --color-accent-purple-600: #7c3aed;
  --color-accent-purple-700: #6d28d9;
  --color-accent-purple-800: #5b21b6;
  --color-accent-purple-900: #4c1d95;

  /* Color Tokens - Accent Orange */
  --color-accent-orange-50: #fffbeb;
  --color-accent-orange-100: #fef3c7;
  --color-accent-orange-200: #fde68a;
  --color-accent-orange-300: #fcd34d;
  --color-accent-orange-400: #fbbf24;
  --color-accent-orange-500: #f59e0b;
  --color-accent-orange-600: #d97706;
  --color-accent-orange-700: #b45309;
  --color-accent-orange-800: #92400e;
  --color-accent-orange-900: #78350f;

  /* Color Tokens - Semantic Success */
  --color-success-50: #ecfdf5;
  --color-success-100: #d1fae5;
  --color-success-200: #a7f3d0;
  --color-success-300: #6ee7b7;
  --color-success-400: #34d399;
  --color-success-500: #10b981;
  --color-success-600: #059669;
  --color-success-700: #047857;
  --color-success-800: #065f46;
  --color-success-900: #064e3b;

  /* Color Tokens - Semantic Error */
  --color-error-50: #fef2f2;
  --color-error-100: #fee2e2;
  --color-error-200: #fecaca;
  --color-error-300: #fca5a5;
  --color-error-400: #f87171;
  --color-error-500: #ef4444;
  --color-error-600: #dc2626;
  --color-error-700: #b91c1c;
  --color-error-800: #991b1b;
  --color-error-900: #7f1d1d;

  /* Color Tokens - Semantic Warning */
  --color-warning-50: #fffbeb;
  --color-warning-100: #fef3c7;
  --color-warning-200: #fde68a;
  --color-warning-300: #fcd34d;
  --color-warning-400: #fbbf24;
  --color-warning-500: #f59e0b;
  --color-warning-600: #d97706;
  --color-warning-700: #b45309;
  --color-warning-800: #92400e;
  --color-warning-900: #78350f;

  /* Color Tokens - Semantic Info */
  --color-info-50: #eff6ff;
  --color-info-100: #dbeafe;
  --color-info-200: #bfdbfe;
  --color-info-300: #93c5fd;
  --color-info-400: #60a5fa;
  --color-info-500: #0ea5e9;
  --color-info-600: #0284c7;
  --color-info-700: #0369a1;
  --color-info-800: #075985;
  --color-info-900: #0c4a6e;

  /* Color Tokens - Neutral */
  --color-neutral-50: #fafafa;
  --color-neutral-100: #f5f5f5;
  --color-neutral-200: #e5e5e5;
  --color-neutral-300: #d4d4d4;
  --color-neutral-400: #a3a3a3;
  --color-neutral-500: #737373;
  --color-neutral-600: #525252;
  --color-neutral-700: #404040;
  --color-neutral-800: #262626;
  --color-neutral-900: #171717;

  /* Color Tokens - Background */
  --color-bg-base: #F5F6F7;
  --color-bg-surface: #ffffff;
  --color-bg-overlay: rgba(0, 0, 0, 0.4);

  /* Typography Tokens - Font Family */
  --font-family-primary: Inter, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
  --font-family-secondary: 'IBM Plex Sans', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
  --font-family-mono: 'IBM Plex Mono', 'Courier New', monospace;

  /* Typography Tokens - Font Size */
  --font-size-caption: 12px;
  --font-size-small: 14px;
  --font-size-body: 16px;
  --font-size-heading3: 20px;
  --font-size-heading2: 28px;
  --font-size-heading1: 36px;
  --font-size-display: 48px;

  /* Typography Tokens - Line Height */
  --line-height-caption: 16px;
  --line-height-small: 20px;
  --line-height-body: 24px;
  --line-height-heading3: 28px;
  --line-height-heading2: 36px;
  --line-height-heading1: 44px;
  --line-height-display: 60px;

  /* Typography Tokens - Font Weight */
  --font-weight-regular: 400;
  --font-weight-medium: 500;
  --font-weight-semibold: 600;
  --font-weight-bold: 700;

  /* Spacing Tokens */
  --space-xs: 4px;
  --space-sm: 8px;
  --space-md: 16px;
  --space-lg: 24px;
  --space-xl: 32px;
  --space-2xl: 48px;
  --space-3xl: 64px;
  --space-4xl: 96px;

  /* Radius Tokens */
  --radius-sm: 4px;
  --radius-md: 8px;
  --radius-lg: 12px;
  --radius-xl: 16px;
  --radius-2xl: 24px;
  --radius-full: 9999px;

  /* Shadow Tokens */
  --shadow-sm: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
  --shadow-md: 0 1px 3px 0 rgba(0, 0, 0, 0.1), 0 1px 2px -1px rgba(0, 0, 0, 0.1);
  --shadow-lg: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -2px rgba(0, 0, 0, 0.1);
  --shadow-xl: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -4px rgba(0, 0, 0, 0.1);
  --shadow-2xl: 0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 8px 10px -6px rgba(0, 0, 0, 0.1);

  /* Animation Tokens - Duration */
  --duration-instant: 50ms;
  --duration-fast: 150ms;
  --duration-normal: 300ms;
  --duration-slow: 500ms;

  /* Animation Tokens - Easing */
  --easing-linear: linear;
  --easing-ease-in: cubic-bezier(0.4, 0, 1, 1);
  --easing-ease-out: cubic-bezier(0, 0, 0.2, 1);
  --easing-ease-in-out: cubic-bezier(0.4, 0, 0.2, 1);
}

/* Apply theme to body by default */
body {
  @apply theme-apple;
}
```

#### 1.2 匯入主題檔案

**檔案**: `handoff/20250928/40_App/frontend-dashboard/src/index.css`

```css
@tailwind base;
@tailwind components;
@tailwind utilities;

/* Import theme */
@import './styles/theme-apple.css';
```

#### 1.3 更新 App.jsx

確保根元素有 `.theme-apple` 類別:

```jsx
// App.jsx
function App() {
  return (
    <div className="theme-apple min-h-screen">
      {/* ... */}
    </div>
  )
}
```

---

### Phase 2: 漸進式遷移 (2 天)

#### 優先順序

1. **P0 - 核心頁面** (第 1 天)
   - Dashboard.jsx
   - LoginPage.jsx
   - LandingPage.jsx

2. **P1 - 次要頁面** (第 2 天)
   - Settings.jsx
   - DecisionApproval.jsx
   - Reports.jsx
   - WIPPage.jsx

3. **P2 - 組件** (如有時間)
   - 所有 UI 組件

#### 遷移步驟 (每個頁面)

1. **識別樣式使用**
   ```bash
   # 搜尋該頁面的樣式
   grep -n "className\|style" Dashboard.jsx
   ```

2. **替換全域變數**
   - 將 `var(--old-token)` 替換為 `var(--color-primary-500)` 等

3. **測試頁面**
   - 本地測試
   - 視覺檢查

4. **執行視覺回歸測試**
   ```bash
   npm run test:vrt
   ```

5. **提交變更**
   ```bash
   git add .
   git commit -m "feat(theme): Migrate Dashboard to scoped tokens"
   ```

---

### Phase 3: 視覺回歸測試 (0.5 天)

#### 3.1 執行基線測試

```bash
# 在遷移前建立基線
npm run test:vrt

# 基線會儲存在 tests/__screenshots__/
```

#### 3.2 遷移後測試

```bash
# 遷移後執行測試
npm run test:vrt

# 比對差異
```

#### 3.3 審查差異

- 檢查所有視覺差異
- 確認差異是預期的 (應該沒有差異)
- 如有非預期差異，回滾並修復

---

### Phase 4: 整合與驗證 (0.5 天)

#### 4.1 整合測試

```bash
# 執行所有測試
npm run build
npm run lint
npm run test:smoke
npm run test:vrt
```

#### 4.2 手動驗證

- [ ] Dashboard 顯示正常
- [ ] Login 顯示正常
- [ ] Landing Page 顯示正常
- [ ] 所有顏色正確
- [ ] 所有字體正確
- [ ] 所有間距正確
- [ ] 響應式正常

#### 4.3 提交 PR

```bash
git checkout -b devin/$(date +%s)-token-scoping
git add .
git commit -m "feat(theme): Implement scoped token system with .theme-apple"
git push origin devin/$(date +%s)-token-scoping
```

---

## 🔄 回滾策略

### 如果出現問題

1. **立即回滾**
   ```bash
   git revert HEAD
   git push origin main
   ```

2. **識別問題**
   - 檢查視覺回歸測試報告
   - 檢查瀏覽器 Console
   - 檢查 CSS 變數是否正確

3. **修復問題**
   - 在本地修復
   - 重新測試
   - 重新提交

### 回滾檢查清單

- [ ] 確認 main 分支正常
- [ ] 通知團隊回滾
- [ ] 記錄問題原因
- [ ] 建立修復計劃

---

## 📊 進度追蹤

### 遷移檢查清單

#### Phase 1: 建立主題容器
- [ ] 建立 `theme-apple.css`
- [ ] 定義所有 120+ Design Tokens
- [ ] 匯入到 `index.css`
- [ ] 更新 `App.jsx`
- [ ] 本地測試

#### Phase 2: 漸進式遷移
- [ ] Dashboard.jsx
- [ ] LoginPage.jsx
- [ ] LandingPage.jsx
- [ ] Settings.jsx
- [ ] DecisionApproval.jsx
- [ ] Reports.jsx
- [ ] WIPPage.jsx

#### Phase 3: 視覺回歸測試
- [ ] 建立基線 (遷移前)
- [ ] 執行測試 (遷移後)
- [ ] 審查差異
- [ ] 修復非預期差異

#### Phase 4: 整合與驗證
- [ ] 執行 build
- [ ] 執行 lint
- [ ] 執行 smoke tests
- [ ] 執行 VRT
- [ ] 手動驗證
- [ ] 提交 PR

---

## 🎯 成功標準

### 必須達成

- ✅ 所有頁面使用 `.theme-apple` 容器
- ✅ 所有 CSS 變數都在 `.theme-apple` 作用域內
- ✅ 視覺回歸測試通過 (無非預期差異)
- ✅ 所有 CI 檢查通過
- ✅ 手動驗證通過

### 加分項

- ✅ 建立主題切換功能 (未來)
- ✅ 支援多主題 (未來)
- ✅ 文檔完整

---

## 📝 相關文件

- **Design Tokens**: `docs/UX/tokens.json`
- **視覺回歸測試**: `tests/vrt.spec.ts`
- **Playwright 配置**: `playwright.config.ts`
- **API 端點驗證**: `API_ENDPOINT_VERIFICATION_REPORT.md`

---

## 🚀 下一步

完成 Token 作用域化後:

1. **Week 3-4**: 實作 i18n 工作流程
2. **Week 5-6**: Dashboard 能力增強
3. **Week 7-8**: 可用性測試與優化

---

**文件版本**: 1.0  
**最後更新**: 2025-10-21  
**負責人**: Devin AI
