# Token Migration Plan

## 📋 概述

本文檔說明如何將 Morning AI 專案從硬編碼樣式逐步遷移到 Design Token 系統（`theme-apple.css`）。

**目標**: 確保設計一致性、簡化維護、支援 Dark Mode。

---

## 🎯 遷移策略

### 原則

1. **漸進式遷移**: 不一次性重寫所有元件
2. **優先級導向**: 先遷移高頻使用的元件
3. **保持穩定性**: 確保每次遷移不破壞現有功能
4. **測試驅動**: 每次遷移後執行 VRT 測試

### 範圍

**包含**:
- 自訂元件（非 shadcn/ui）
- 高度自訂的 shadcn/ui 元件
- 新建元件（強制使用 Tokens）

**排除**:
- 標準 shadcn/ui 元件（保持 Tailwind）
- 第三方元件庫
- 臨時/測試元件

---

## 📅 遷移時程

### Phase 1: 基礎設施（Week 5-6）✅ 已完成

- [x] 建立 `theme-apple.css` token 系統
- [x] 在 `App.jsx` 中啟用 `.theme-apple` class
- [x] 建立 `TokenExample` 範例元件
- [x] 撰寫 `THEME_USAGE_GUIDE.md`
- [x] 建立 VRT 測試基線

### Phase 2: 核心元件遷移（Week 7-8）

**目標**: 遷移 2-3 個核心自訂元件

#### 優先級 P0（必須遷移）

1. **BrandLoader** (`src/components/feedback/BrandLoader.jsx`)
   - **原因**: 高頻使用（loading states）
   - **複雜度**: 低（主要是顏色和間距）
   - **預估時間**: 1 小時
   - **Token 使用**: `--color-primary`, `--spacing-*`, `--shadow-*`

2. **PageLoader** (`src/components/feedback/PageLoader.jsx`)
   - **原因**: 高頻使用（page transitions）
   - **複雜度**: 低
   - **預估時間**: 1 小時
   - **Token 使用**: `--bg-primary`, `--text-primary`, `--spacing-*`

#### 優先級 P1（建議遷移）

3. **LanguageSwitcher** (`src/components/LanguageSwitcher.jsx`)
   - **原因**: 全域元件
   - **複雜度**: 中（有 hover/active states）
   - **預估時間**: 2 小時
   - **Token 使用**: `--color-primary`, `--border-*`, `--transition-*`

4. **AppleHero** (`src/components/AppleHero.jsx`)
   - **原因**: Landing page 核心元件
   - **複雜度**: 中（有動畫和漸層）
   - **預估時間**: 2 小時
   - **Token 使用**: `--bg-gradient-primary`, `--text-*`, `--spacing-*`

### Phase 3: 頁面級元件遷移（Week 9-10）

#### 優先級 P1

5. **LandingPage** (`src/components/LandingPage.jsx`)
   - **原因**: 首頁，高可見度
   - **複雜度**: 高（多個 sections）
   - **預估時間**: 4 小時
   - **Token 使用**: 全面使用所有 tokens

6. **LoginPage** (`src/components/LoginPage.jsx`)
   - **原因**: 認證流程核心頁面
   - **複雜度**: 中
   - **預估時間**: 3 小時
   - **Token 使用**: `--bg-*`, `--text-*`, `--border-*`, `--shadow-*`

#### 優先級 P2

7. **Sidebar** (`src/components/Sidebar.jsx`)
   - **原因**: Dashboard 核心導航
   - **複雜度**: 中（有 collapsed state）
   - **預估時間**: 3 小時
   - **Token 使用**: `--sidebar-width`, `--bg-*`, `--text-*`

8. **Dashboard** (`src/components/Dashboard.jsx`)
   - **原因**: 主要工作區
   - **複雜度**: 高（多個子元件）
   - **預估時間**: 5 小時
   - **Token 使用**: 全面使用所有 tokens

### Phase 4: 完整遷移（Week 11-12）

- 遷移剩餘自訂元件
- 移除所有硬編碼樣式
- 執行完整 VRT 測試
- 效能優化

---

## 🔧 遷移步驟（標準流程）

### 1. 準備階段

```bash
# 1. 建立 feature branch
git checkout -b feat/migrate-{component-name}-to-tokens

# 2. 確保 VRT baseline 存在
npm run test:vrt

# 3. 備份原始元件
cp src/components/{Component}.jsx src/components/{Component}.jsx.backup
```

### 2. 遷移階段

#### Step 1: 識別硬編碼樣式

```jsx
// ❌ 遷移前
<div style={{
  padding: '16px',
  backgroundColor: '#FFFFFF',
  color: '#171717',
  borderRadius: '8px'
}}>
  內容
</div>
```

#### Step 2: 映射到 Tokens

| 硬編碼值 | Token | 說明 |
|---------|-------|------|
| `16px` | `var(--spacing-4)` | 間距 |
| `#FFFFFF` | `var(--bg-primary)` | 背景色 |
| `#171717` | `var(--text-primary)` | 文字色 |
| `8px` | `var(--radius-md)` | 圓角 |

#### Step 3: 替換為 Tokens

```jsx
// ✅ 遷移後
<div style={{
  padding: 'var(--spacing-4)',
  backgroundColor: 'var(--bg-primary)',
  color: 'var(--text-primary)',
  borderRadius: 'var(--radius-md)'
}}>
  內容
</div>
```

### 3. 測試階段

```bash
# 1. 本地測試
npm run dev
# 手動檢查元件顯示正常

# 2. Dark Mode 測試
# 切換 Dark Mode，確認樣式正確

# 3. VRT 測試
npm run test:vrt
# 檢查 screenshot diffs

# 4. 如果 VRT 失敗但視覺正確，更新 baseline
npm run test:vrt -- --update-snapshots
```

### 4. 提交階段

```bash
# 1. Commit 變更
git add src/components/{Component}.jsx
git commit -m "refactor({component}): Migrate to Design Tokens

- Replace hardcoded colors with semantic tokens
- Replace hardcoded spacing with spacing scale
- Add Dark Mode support via token system
- Update VRT baseline if needed"

# 2. Push 並建立 PR
git push origin feat/migrate-{component-name}-to-tokens
gh pr create --title "refactor: Migrate {Component} to Design Tokens"
```

---

## 📊 遷移檢查清單

### 元件遷移檢查清單

對每個遷移的元件，確認：

- [ ] 所有硬編碼顏色已替換為 semantic tokens
- [ ] 所有硬編碼間距已替換為 spacing scale
- [ ] 所有硬編碼字體大小已替換為 typography tokens
- [ ] 所有硬編碼圓角已替換為 radius tokens
- [ ] 所有硬編碼陰影已替換為 shadow tokens
- [ ] 所有過渡動畫已替換為 transition tokens
- [ ] Dark Mode 測試通過
- [ ] VRT 測試通過（或 baseline 已更新）
- [ ] 無 console errors/warnings
- [ ] 效能無明顯下降

### PR 檢查清單

- [ ] PR 標題清晰（`refactor: Migrate {Component} to Design Tokens`）
- [ ] PR 描述包含：
  - 遷移的元件列表
  - 使用的 tokens 類別
  - VRT baseline 是否更新
  - Dark Mode 測試結果
- [ ] CI 全部通過
- [ ] Code review 通過
- [ ] 合併後刪除 feature branch

---

## 🎨 Token 映射表

### 顏色映射

| Tailwind Class | Token | 說明 |
|----------------|-------|------|
| `bg-white` | `var(--bg-primary)` | 主背景 |
| `bg-gray-50` | `var(--bg-secondary)` | 次要背景 |
| `bg-gray-100` | `var(--bg-tertiary)` | 三級背景 |
| `text-gray-900` | `var(--text-primary)` | 主文字 |
| `text-gray-600` | `var(--text-secondary)` | 次要文字 |
| `text-gray-400` | `var(--text-tertiary)` | 三級文字 |
| `border-gray-200` | `var(--border-primary)` | 主邊框 |
| `border-gray-300` | `var(--border-secondary)` | 次要邊框 |
| `bg-blue-500` | `var(--color-primary)` | 品牌主色 |
| `bg-yellow-500` | `var(--color-secondary)` | 品牌次色 |
| `bg-green-500` | `var(--color-success)` | 成功色 |
| `bg-yellow-500` | `var(--color-warning)` | 警告色 |
| `bg-red-500` | `var(--color-error)` | 錯誤色 |
| `bg-blue-500` | `var(--color-info)` | 資訊色 |

### 間距映射

| Tailwind Class | Token | 值 |
|----------------|-------|-----|
| `p-1` | `var(--spacing-1)` | 4px |
| `p-2` | `var(--spacing-2)` | 8px |
| `p-3` | `var(--spacing-3)` | 12px |
| `p-4` | `var(--spacing-4)` | 16px |
| `p-5` | `var(--spacing-5)` | 20px |
| `p-6` | `var(--spacing-6)` | 24px |
| `p-8` | `var(--spacing-8)` | 32px |
| `p-10` | `var(--spacing-10)` | 40px |
| `p-12` | `var(--spacing-12)` | 48px |

### 字體映射

| Tailwind Class | Token | 值 |
|----------------|-------|-----|
| `text-xs` | `var(--font-size-xs)` | 12px |
| `text-sm` | `var(--font-size-sm)` | 14px |
| `text-base` | `var(--font-size-base)` | 16px |
| `text-lg` | `var(--font-size-lg)` | 18px |
| `text-xl` | `var(--font-size-xl)` | 20px |
| `text-2xl` | `var(--font-size-2xl)` | 24px |
| `text-3xl` | `var(--font-size-3xl)` | 30px |
| `font-light` | `var(--font-weight-light)` | 300 |
| `font-normal` | `var(--font-weight-normal)` | 400 |
| `font-medium` | `var(--font-weight-medium)` | 500 |
| `font-semibold` | `var(--font-weight-semibold)` | 600 |
| `font-bold` | `var(--font-weight-bold)` | 700 |

### 圓角映射

| Tailwind Class | Token | 值 |
|----------------|-------|-----|
| `rounded-none` | `var(--radius-none)` | 0px |
| `rounded-sm` | `var(--radius-sm)` | 4px |
| `rounded` | `var(--radius-md)` | 8px |
| `rounded-md` | `var(--radius-md)` | 8px |
| `rounded-lg` | `var(--radius-lg)` | 12px |
| `rounded-xl` | `var(--radius-xl)` | 16px |
| `rounded-2xl` | `var(--radius-2xl)` | 24px |
| `rounded-full` | `var(--radius-full)` | 9999px |

### 陰影映射

| Tailwind Class | Token |
|----------------|-------|
| `shadow-sm` | `var(--shadow-sm)` |
| `shadow` | `var(--shadow-md)` |
| `shadow-md` | `var(--shadow-md)` |
| `shadow-lg` | `var(--shadow-lg)` |
| `shadow-xl` | `var(--shadow-xl)` |
| `shadow-2xl` | `var(--shadow-2xl)` |

---

## 📈 進度追蹤

### 遷移進度

| 元件 | 狀態 | 負責人 | 完成日期 | PR |
|------|------|--------|----------|-----|
| TokenExample | ✅ 完成 | Devin | 2025-10-21 | #555 |
| BrandLoader | ⏳ 待遷移 | - | - | - |
| PageLoader | ⏳ 待遷移 | - | - | - |
| LanguageSwitcher | ⏳ 待遷移 | - | - | - |
| AppleHero | ⏳ 待遷移 | - | - | - |
| LandingPage | ⏳ 待遷移 | - | - | - |
| LoginPage | ⏳ 待遷移 | - | - | - |
| Sidebar | ⏳ 待遷移 | - | - | - |
| Dashboard | ⏳ 待遷移 | - | - | - |

### 統計

- **總元件數**: 9
- **已遷移**: 1 (11%)
- **進行中**: 0
- **待遷移**: 8 (89%)

---

## 🚨 常見問題

### Q: 遷移後 VRT 測試失敗怎麼辦？

**A**: 
1. 手動檢查視覺差異是否符合預期
2. 如果視覺正確，更新 baseline: `npm run test:vrt -- --update-snapshots`
3. 如果視覺不正確，檢查 token 映射是否正確

### Q: Dark Mode 顯示不正確？

**A**:
1. 確認使用的是 semantic tokens（如 `--text-primary`）而非 neutral tokens（如 `--color-neutral-900`）
2. 檢查 `theme-apple.css` 中是否有對應的 `.theme-apple.dark` 覆蓋
3. 使用瀏覽器 DevTools 檢查 computed styles

### Q: 效能下降？

**A**:
1. CSS 變數本身不會影響效能
2. 檢查是否有不必要的 inline styles 重複計算
3. 考慮使用 CSS Modules 或 styled-components 優化

### Q: 與 Tailwind 衝突？

**A**:
1. 避免在同一元件中混用 Tailwind 和 Tokens
2. 優先使用 Tokens（除非是 shadcn/ui 元件）
3. 如果必須混用，確保 CSS 特異性正確

---

## 📚 相關資源

- **Token 定義**: `src/styles/theme-apple.css`
- **使用指南**: `THEME_USAGE_GUIDE.md`
- **範例元件**: `src/components/examples/TokenExample.jsx`
- **VRT 測試**: `tests/vrt.spec.ts`
- **品牌資產**: `public/assets/brand/README.md`

---

**最後更新**: 2025-10-21  
**維護者**: Devin (AI Assistant)  
**版本**: 1.0.0
