# Tailwind v4 配置與主題 Token 指南

## 概述

本指南記錄了 Tailwind CSS v4 在 morningai 專案中的正確配置方式，特別是關於 `@theme` 塊和設計 token 的使用。此指南源自於 2025-11-02 修復的一個關鍵佈局問題（PR #1034）。

## 問題症狀

如果你遇到以下任何症狀，可能是 Tailwind v4 配置錯誤：

- 整個頁面佈局被壓縮成一條窄直線
- `max-w-3xl` 等容器寬度 utilities 渲染為 `64px` 而非預期的 `768px`
- 在瀏覽器 DevTools 中檢查元素時，發現 `--container-3xl` 等 CSS 變數為空值
- 生產環境中 CSS 樣式與本地開發環境不一致
- 來自 `@morningai/shared-ui` 的樣式在生產環境中消失

## 根本原因

Tailwind v4 引入了重大架構變更，使用 CSS 設計 token 系統。常見的配置錯誤包括：

### 1. 缺少 `tailwind.config.js` 或 content 路徑配置錯誤

**問題**: Tailwind v4 在構建時會掃描 `content` 路徑中的文件，移除未使用的 CSS classes。如果沒有包含 `@morningai/shared-ui` 的路徑，shared-ui 的樣式會在生產環境中被清除。

**解決方案**: 確保 `tailwind.config.js` 包含所有相關路徑：

```javascript
// handoff/20250928/40_App/frontend-dashboard/tailwind.config.js
export default {
  content: [
    './index.html',
    './src/**/*.{js,ts,jsx,tsx}',
    // ⚠️ 關鍵：必須包含 shared-ui 路徑
    '../../packages/shared-ui/src/**/*.{js,ts,jsx,tsx}',
  ],
  // ... 其他配置
}
```

### 2. `@theme` 塊放置位置錯誤

**問題**: Tailwind v4 需要在**構建時**讀取 `@theme` 塊中的 token 定義。如果 `@theme` 塊放在 `@import "tailwindcss"` **之後**，tokens 將無法被正確處理。

**錯誤示例**:
```css
/* ❌ 錯誤：@theme 在 @import 之後 */
@import "tailwindcss";

@theme {
  --container-3xl: 48rem;
}
```

**正確示例**:
```css
/* ✅ 正確：@theme 必須在 @import 之前 */
@theme {
  --container-3xl: 48rem;
}

@import "tailwindcss";
```

### 3. 重複的 `@theme` 塊

**問題**: 如果 CSS 文件中存在多個 `@theme` 塊，後面的會覆蓋前面的定義，導致 token 值不正確。

**解決方案**: 確保整個 CSS 文件中只有**一個** `@theme` 塊，且放在最頂部（在所有 `@import` 之前）。

### 4. 使用錯誤的 token 名稱

**問題**: Tailwind v4 的 `max-w-*` utilities 使用 `--container-*` tokens，而非 `--spacing-*`、`--space-*` 或 `--size-*`。

**Token 映射表**:

| Utility Class | CSS 輸出 | 需要的 Token | 值 |
|--------------|----------|-------------|-----|
| `max-w-xs` | `max-width: var(--container-xs)` | `--container-xs` | `20rem` (320px) |
| `max-w-sm` | `max-width: var(--container-sm)` | `--container-sm` | `24rem` (384px) |
| `max-w-md` | `max-width: var(--container-md)` | `--container-md` | `28rem` (448px) |
| `max-w-lg` | `max-width: var(--container-lg)` | `--container-lg` | `32rem` (512px) |
| `max-w-xl` | `max-width: var(--container-xl)` | `--container-xl` | `36rem` (576px) |
| `max-w-2xl` | `max-width: var(--container-2xl)` | `--container-2xl` | `42rem` (672px) |
| `max-w-3xl` | `max-width: var(--container-3xl)` | `--container-3xl` | `48rem` (768px) |
| `max-w-4xl` | `max-width: var(--container-4xl)` | `--container-4xl` | `56rem` (896px) |
| `max-w-5xl` | `max-width: var(--container-5xl)` | `--container-5xl` | `64rem` (1024px) |
| `max-w-6xl` | `max-width: var(--container-6xl)` | `--container-6xl` | `72rem` (1152px) |
| `max-w-7xl` | `max-width: var(--container-7xl)` | `--container-7xl` | `80rem` (1280px) |

## 正確配置範例

### 1. `src/index.css` 配置

```css
/*
  Tailwind v4 配置注意事項：
  - @theme 塊必須放在 @import "tailwindcss" 之前
  - max-w-* utilities 使用 --container-* tokens
  - 詳細說明：docs/TAILWIND_V4_CONFIGURATION_GUIDE.md
*/

@theme {
  /* Max-width tokens - 用於 max-w-* utilities */
  --container-xs: 20rem;     /* 320px - max-w-xs */
  --container-sm: 24rem;     /* 384px - max-w-sm */
  --container-md: 28rem;     /* 448px - max-w-md */
  --container-lg: 32rem;     /* 512px - max-w-lg */
  --container-xl: 36rem;     /* 576px - max-w-xl */
  --container-2xl: 42rem;    /* 672px - max-w-2xl */
  --container-3xl: 48rem;    /* 768px - max-w-3xl */
  --container-4xl: 56rem;    /* 896px - max-w-4xl */
  --container-5xl: 64rem;    /* 1024px - max-w-5xl */
  --container-6xl: 72rem;    /* 1152px - max-w-6xl */
  --container-7xl: 80rem;    /* 1280px - max-w-7xl */
}

@import "tailwindcss";
@import "./materials.css";
@import "./accessibility.css";
/* 其他 imports... */
```

### 2. `tailwind.config.js` 配置

```javascript
/** @type {import('tailwindcss').Config} */
export default {
  content: [
    './index.html',
    './src/**/*.{js,ts,jsx,tsx}',
    // 包含 shared-ui 以防止 CSS 被清除
    '../../packages/shared-ui/src/**/*.{js,ts,jsx,tsx}',
  ],
  safelist: [
    // 基礎佈局 classes（可能動態生成）
    'flex', 'grid', 'inline-flex', 'inline-grid',
    'w-full', 'h-full', 'min-h-screen',
    
    // Grid columns
    { pattern: /grid-cols-(1|2|3|4|6|12)/ },
    
    // Gap utilities
    { pattern: /gap-(1|2|3|4|6|8)/ },
    
    // 常用 spacing
    { pattern: /p(x|y|t|b|l|r)?-(0|1|2|3|4|6|8|12|16)/ },
    { pattern: /m(x|y|t|b|l|r)?-(0|1|2|3|4|6|8|12|16|auto)/ },
    
    // cva 元件的顏色變體
    { pattern: /bg-(primary|secondary|accent|success|warning|error|info)-(50|100|200|300|400|500|600|700|800|900)/ },
    { pattern: /text-(primary|secondary|accent|success|warning|error|info)-(50|100|200|300|400|500|600|700|800|900)/ },
    { pattern: /border-(primary|secondary|accent|success|warning|error|info)-(50|100|200|300|400|500|600|700|800|900)/ },
    
    // 常用文字大小
    { pattern: /text-(xs|sm|base|lg|xl|2xl|3xl|4xl|5xl|6xl)/ },
    
    // 常用字重
    { pattern: /font-(light|normal|medium|semibold|bold)/ },
    
    // Radix UI 狀態 classes
    'data-[state=open]', 'data-[state=closed]',
    'data-[side=top]', 'data-[side=right]', 'data-[side=bottom]', 'data-[side=left]',
    
    // 動畫 classes
    'animate-in', 'animate-out',
    'fade-in', 'fade-out',
    'zoom-in', 'zoom-out',
    'slide-in-from-top', 'slide-in-from-bottom', 'slide-in-from-left', 'slide-in-from-right',
  ],
  theme: {
    extend: {
      // 確保 max-width utilities 使用正確的值
      maxWidth: {
        'xs': '20rem',
        'sm': '24rem',
        'md': '28rem',
        'lg': '32rem',
        'xl': '36rem',
        '2xl': '42rem',
        '3xl': '48rem',
        '4xl': '56rem',
        '5xl': '64rem',
        '6xl': '72rem',
        '7xl': '80rem',
      },
    },
  },
  plugins: [],
}
```

### 3. Vite 配置

```javascript
// vite.config.js
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

export default defineConfig({
  plugins: [
    react(),
    tailwindcss(), // ✅ 使用 @tailwindcss/vite plugin
  ],
  // ... 其他配置
})
```

**重要**: Tailwind v4 使用 `@tailwindcss/vite` plugin，**不需要** `postcss.config.js`。如果你看到 `postcss.config.js` 文件，應該移除它（除非有其他 PostCSS plugins 需要使用）。

## 驗證步驟

### 1. 本地構建驗證

```bash
cd handoff/20250928/40_App/frontend-dashboard
pnpm run build
```

檢查構建輸出的 CSS 文件（通常在 `dist/assets/index-*.css`）：

```bash
# 檢查 --container-3xl token 是否存在且值正確
grep -o "\-\-container-3xl:[^;]*" dist/assets/index-*.css
# 預期輸出: --container-3xl:48rem

# 檢查 max-w-3xl utility 是否正確編譯
grep -o "\.max-w-3xl{[^}]*}" dist/assets/index-*.css
# 預期輸出: .max-w-3xl{max-width:var(--container-3xl)}
```

### 2. 瀏覽器 DevTools 驗證

在瀏覽器中打開應用，按 F12 打開 DevTools：

```javascript
// 在 Console 中執行
const testDiv = document.createElement('div');
testDiv.className = 'max-w-3xl';
document.body.appendChild(testDiv);
const maxWidth = getComputedStyle(testDiv).maxWidth;
console.log('max-w-3xl computed maxWidth:', maxWidth);
document.body.removeChild(testDiv);

// 預期輸出: max-w-3xl computed maxWidth: 768px
```

檢查 CSS 變數：

```javascript
// 檢查 :root 上的 --container-3xl token
const rootStyles = getComputedStyle(document.documentElement);
const container3xl = rootStyles.getPropertyValue('--container-3xl');
console.log('--container-3xl:', container3xl);

// 預期輸出: --container-3xl: 48rem
```

### 3. Vercel 部署驗證

部署到 Vercel 後：

1. **硬刷新頁面**: 按 `Ctrl+Shift+R` (Windows/Linux) 或 `Cmd+Shift+R` (Mac) 清除瀏覽器快取
2. 執行上述 DevTools 驗證步驟
3. 檢查頁面佈局是否正常（不應該被壓縮成窄條）

**注意**: Vercel 可能會快取構建產物。如果部署後仍看到舊版本，可能需要：
- 在 Vercel Dashboard 中手動觸發重新部署
- 清除 Vercel 的構建快取

## 常見陷阱與反模式

### ❌ 不要做

1. **不要在 `@import "tailwindcss"` 之後放置 `@theme` 塊**
   ```css
   /* ❌ 錯誤 */
   @import "tailwindcss";
   @theme { /* ... */ }
   ```

2. **不要創建多個 `@theme` 塊**
   ```css
   /* ❌ 錯誤 */
   @theme { --container-3xl: 48rem; }
   @import "tailwindcss";
   @theme { --container-3xl: 64rem; } /* 這會覆蓋上面的定義 */
   ```

3. **不要使用錯誤的 token 名稱**
   ```css
   /* ❌ 錯誤 */
   @theme {
     --spacing-3xl: 48rem;  /* max-w-3xl 不會使用這個 */
     --space-3xl: 48rem;    /* max-w-3xl 也不會使用這個 */
     --size-3xl: 48rem;     /* max-w-3xl 還是不會使用這個 */
   }
   ```

4. **不要忘記在 `content` 中包含 shared-ui 路徑**
   ```javascript
   /* ❌ 錯誤 */
   content: [
     './src/**/*.{js,ts,jsx,tsx}',
     // 缺少 shared-ui 路徑！
   ]
   ```

5. **不要為 Tailwind v4 創建 `postcss.config.js`**
   - Tailwind v4 使用 `@tailwindcss/vite` plugin，不需要 PostCSS 配置
   - 如果存在 `postcss.config.js`，可能會導致衝突

### ✅ 應該做

1. **在所有 `@import` 之前定義 `@theme` 塊**
2. **使用正確的 token 名稱** (`--container-*` for max-width utilities)
3. **在 `tailwind.config.js` 中包含所有相關的 content 路徑**
4. **使用 `safelist` 保護動態生成的 classes**
5. **在部署後進行硬刷新驗證**

## Safelist 建議

對於使用 `cva` (class-variance-authority) 或 Radix UI 等動態生成 classes 的情況，建議在 `safelist` 中添加相關模式：

```javascript
safelist: [
  // cva 變體
  { pattern: /bg-(primary|secondary|accent)-(50|100|200|300|400|500|600|700|800|900)/ },
  
  // Radix UI 狀態
  'data-[state=open]',
  'data-[state=closed]',
  
  // 動畫
  'animate-in',
  'animate-out',
  
  // 根據實際使用情況添加更多...
]
```

## 已知問題

### 瀏覽器快取

**症狀**: 部署後仍看到舊版本的佈局問題

**解決方案**: 
- 執行硬刷新 (`Ctrl+Shift+R` 或 `Cmd+Shift+R`)
- 清除瀏覽器快取
- 在無痕模式中測試

### Vercel 構建快取

**症狀**: Vercel 部署完成但使用舊版本的 CSS

**解決方案**:
- 在 Vercel Dashboard 中手動觸發重新部署
- 檢查部署日誌確認構建步驟正確執行
- 驗證 git commit hash 與部署的版本一致

### CORS 錯誤

**症狀**: 預覽 URL 無法連接後端 API

**解決方案**: 這是獨立的後端配置問題，與 Tailwind v4 配置無關。需要在後端添加 Vercel 預覽域名到 CORS 允許列表。

## 影響範圍

此配置適用於所有使用 Tailwind v4 的應用：

- ✅ `handoff/20250928/40_App/frontend-dashboard`
- ⚠️ `handoff/20250928/40_App/owner-console` (如果使用 Tailwind v4，需要類似配置)
- ⚠️ 其他使用 `@morningai/shared-ui` 的應用

**重要**: 如果其他應用也使用 Tailwind v4 和 shared-ui，請確保它們的 `tailwind.config.js` 也包含正確的 content 路徑。

## 相關資源

- **PR #1034**: https://github.com/RC918/morningai/pull/1034
- **Devin Session**: https://app.devin.ai/sessions/560c0fcf99364ef3a0cb4290434a2eb8
- **Frontend Dashboard Preview**: https://morningai-git-devin-1762015630-integrate-shar-c2e80f-morning-ai.vercel.app
- **Tailwind CSS v4 文檔**: https://tailwindcss.com/docs/v4-beta
- **@tailwindcss/vite Plugin**: https://github.com/tailwindlabs/tailwindcss/tree/next/packages/%40tailwindcss-vite

## 疑難排解

如果遇到佈局問題，請按照以下步驟排查：

1. **檢查 `@theme` 塊位置**
   - 確認在 `@import "tailwindcss"` 之前
   - 確認沒有重複的 `@theme` 塊

2. **檢查 token 名稱**
   - 使用 `--container-*` 而非 `--spacing-*` 或其他名稱

3. **檢查 `tailwind.config.js`**
   - 確認 content 路徑包含 shared-ui
   - 確認 safelist 包含動態生成的 classes

4. **檢查構建輸出**
   - 運行 `pnpm run build`
   - 檢查生成的 CSS 文件中的 token 定義

5. **瀏覽器驗證**
   - 硬刷新頁面
   - 使用 DevTools 檢查 computed styles
   - 檢查 CSS 變數值

6. **查看詳細的疑難排解指南**
   - `handoff/20250928/40_App/frontend-dashboard/docs/TROUBLESHOOTING_TAILWIND_V4.md`

## 維護者

- 創建日期: 2025-11-02
- 最後更新: 2025-11-02
- 維護者: Ryan Chen (@RC918)
- 相關 PR: #1034

---

如有任何問題或需要進一步協助，請參考上述相關資源或聯繫專案維護者。
