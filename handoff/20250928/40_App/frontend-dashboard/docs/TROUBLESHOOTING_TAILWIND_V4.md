# Tailwind v4 疑難排解指南

## 快速診斷：佈局被壓縮成窄條

### 症狀

- 整個頁面被壓縮成一條窄直線（寬度約 64px）
- 文字垂直堆疊，每行只有一個字元
- `max-w-3xl` 等容器寬度 utilities 不正常

### 快速檢查

在瀏覽器 DevTools Console 中執行：

```javascript
// 檢查 max-w-3xl 的實際寬度
const testDiv = document.createElement('div');
testDiv.className = 'max-w-3xl';
document.body.appendChild(testDiv);
const maxWidth = getComputedStyle(testDiv).maxWidth;
console.log('max-w-3xl computed maxWidth:', maxWidth);
document.body.removeChild(testDiv);

// 預期輸出: 768px
// 如果輸出: 64px，表示 Tailwind v4 配置有問題
```

檢查 CSS 變數：

```javascript
// 檢查 --container-3xl token
const rootStyles = getComputedStyle(document.documentElement);
const container3xl = rootStyles.getPropertyValue('--container-3xl');
console.log('--container-3xl:', container3xl);

// 預期輸出: 48rem 或 768px
// 如果輸出為空或錯誤值，表示 @theme 塊配置有問題
```

### 常見原因與解決方案

#### 1. `@theme` 塊位置錯誤

**檢查**: 打開 `src/index.css`，確認 `@theme` 塊在 `@import "tailwindcss"` **之前**

```css
/* ✅ 正確 */
@theme {
  --container-3xl: 48rem;
}

@import "tailwindcss";
```

```css
/* ❌ 錯誤 */
@import "tailwindcss";

@theme {
  --container-3xl: 48rem;
}
```

**修復**: 將 `@theme` 塊移到所有 `@import` 語句之前

#### 2. 重複的 `@theme` 塊

**檢查**: 搜尋 `src/index.css` 中是否有多個 `@theme {` 出現

```bash
grep -n "@theme" src/index.css
```

**修復**: 刪除重複的 `@theme` 塊，只保留一個（在最頂部）

#### 3. 使用錯誤的 token 名稱

**檢查**: 確認 `@theme` 塊中使用 `--container-*` 而非 `--spacing-*` 或 `--space-*`

```css
/* ✅ 正確 */
@theme {
  --container-3xl: 48rem;
}
```

```css
/* ❌ 錯誤 */
@theme {
  --spacing-3xl: 48rem;  /* max-w-3xl 不會使用這個 */
  --space-3xl: 48rem;    /* max-w-3xl 也不會使用這個 */
}
```

**修復**: 將所有 `--spacing-*` 或 `--space-*` 改為 `--container-*`

#### 4. 缺少 `tailwind.config.js` 或 content 路徑錯誤

**檢查**: 確認專案根目錄有 `tailwind.config.js`，且包含 shared-ui 路徑

```javascript
// tailwind.config.js
export default {
  content: [
    './index.html',
    './src/**/*.{js,ts,jsx,tsx}',
    '../../packages/shared-ui/src/**/*.{js,ts,jsx,tsx}', // ⚠️ 必須包含
  ],
  // ...
}
```

**修復**: 如果缺少，創建 `tailwind.config.js` 並添加正確的 content 路徑

#### 5. 瀏覽器快取問題

**症狀**: 本地構建正確，但部署後仍看到舊版本

**修復**: 
- 執行硬刷新: `Ctrl+Shift+R` (Windows/Linux) 或 `Cmd+Shift+R` (Mac)
- 清除瀏覽器快取
- 在無痕模式中測試

### 完整修復步驟

1. **檢查 `src/index.css`**:
   ```bash
   cd handoff/20250928/40_App/frontend-dashboard
   head -20 src/index.css
   ```
   
   確認前幾行是：
   ```css
   @theme {
     --container-xs: 20rem;
     --container-sm: 24rem;
     --container-md: 28rem;
     --container-lg: 32rem;
     --container-xl: 36rem;
     --container-2xl: 42rem;
     --container-3xl: 48rem;
     --container-4xl: 56rem;
     --container-5xl: 64rem;
     --container-6xl: 72rem;
     --container-7xl: 80rem;
   }
   
   @import "tailwindcss";
   ```

2. **檢查 `tailwind.config.js`**:
   ```bash
   cat tailwind.config.js
   ```
   
   確認包含 shared-ui 路徑

3. **重新構建**:
   ```bash
   pnpm run build
   ```

4. **驗證構建輸出**:
   ```bash
   # 檢查 --container-3xl token
   grep -o "\-\-container-3xl:[^;]*" dist/assets/index-*.css
   # 預期: --container-3xl:48rem
   
   # 檢查 max-w-3xl utility
   grep -o "\.max-w-3xl{[^}]*}" dist/assets/index-*.css
   # 預期: .max-w-3xl{max-width:var(--container-3xl)}
   ```

5. **提交並部署**:
   ```bash
   git add src/index.css tailwind.config.js
   git commit -m "fix: Configure Tailwind v4 with correct container tokens"
   git push
   ```

6. **部署後驗證**:
   - 等待 CI 通過
   - 等待 Vercel 部署完成
   - 在瀏覽器中打開預覽 URL
   - 執行硬刷新 (`Ctrl+Shift+R`)
   - 執行上述快速檢查腳本

### 需要更多幫助？

查看完整的配置指南：
- **[Tailwind v4 Configuration Guide](../../../../docs/TAILWIND_V4_CONFIGURATION_GUIDE.md)** - 詳細的配置說明、token 映射表、常見陷阱
- **[PR #1034](https://github.com/RC918/morningai/pull/1034)** - 此問題的完整修復記錄
- **[Theme Usage Guide](../../../../THEME_USAGE_GUIDE.md)** - Design tokens 使用指南

### 預防措施

為了防止此問題再次發生：

1. **不要在 `@import "tailwindcss"` 之後添加 `@theme` 塊**
2. **不要創建多個 `@theme` 塊**
3. **使用正確的 token 名稱** (`--container-*` for max-width utilities)
4. **確保 `tailwind.config.js` 包含所有相關的 content 路徑**
5. **部署後執行硬刷新驗證**

---

**最後更新**: 2025-11-02  
**相關 PR**: #1034  
**維護者**: Ryan Chen (@RC918)
