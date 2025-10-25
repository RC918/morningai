# UI/UX 速查表 (一頁速查)

**快速參考**: 常用命令、路徑、組件、Tokens  
**最後更新**: 2025-10-24

---

## 📂 關鍵路徑

| 資源 | 路徑 |
|------|------|
| **組件庫** | `handoff/20250928/40_App/frontend-dashboard/src/components/ui/` |
| **Design Tokens** | `docs/UX/tokens.json` |
| **Storybook Stories** | `handoff/20250928/40_App/frontend-dashboard/src/stories/` |
| **UI/UX 文檔** | `docs/UX/` |
| **設計系統指南** | `DESIGN_SYSTEM_GUIDELINES.md` |
| **完整資源指南** | `docs/UI_UX_RESOURCES.md` |
| **Issue 狀態追蹤** | `docs/UI_UX_ISSUE_STATUS.md` |

---

## ⚡ 常用命令

### Storybook

```bash
# 啟動 Storybook
cd handoff/20250928/40_App/frontend-dashboard && npm run storybook

# 構建 Storybook
npm run build-storybook
```

### 開發伺服器

```bash
# 啟動前端開發伺服器
cd handoff/20250928/40_App/frontend-dashboard && npm run dev

# 構建生產版本
npm run build

# 預覽生產構建
npm run preview
```

### 測試

```bash
# 運行所有測試
npm test

# 運行測試並生成覆蓋率報告
npm run test:coverage

# 運行 Lint
npm run lint

# 運行 Type Check
npm run typecheck
```

### 搜尋與查找

```bash
# 搜尋組件使用範例
rg "import.*Button" --type tsx

# 搜尋 Design Token 使用
rg "theme-morning-ai" --type tsx

# 查找特定功能實作
rg "useUndoRedo" --type tsx

# 列出所有組件
ls handoff/20250928/40_App/frontend-dashboard/src/components/ui/
```

---

## 🎨 Design Tokens 快速參考

### 色彩系統

```javascript
// Primary Colors (9 levels: 50-900)
colors.primary[500]  // 主色
colors.primary[600]  // 深色變體
colors.primary[400]  // 淺色變體

// Semantic Colors
colors.success[500]  // 成功狀態
colors.error[500]    // 錯誤狀態
colors.warning[500]  // 警告狀態
colors.info[500]     // 資訊狀態

// Neutral Colors
colors.neutral[50]   // 最淺灰
colors.neutral[900]  // 最深灰
```

### 間距系統

```javascript
spacing.xs   // 4px
spacing.sm   // 8px
spacing.md   // 16px
spacing.lg   // 24px
spacing.xl   // 32px
spacing.2xl  // 48px
spacing.3xl  // 64px
spacing.4xl  // 96px
```

### 字體系統

```javascript
typography.fontFamily.sans   // Inter
typography.fontFamily.mono   // IBM Plex Mono

typography.fontSize.xs       // 12px
typography.fontSize.sm       // 14px
typography.fontSize.base     // 16px
typography.fontSize.lg       // 18px
typography.fontSize.xl       // 20px
typography.fontSize.2xl      // 24px
typography.fontSize.3xl      // 30px
typography.fontSize.4xl      // 36px
```

### 圓角系統

```javascript
borderRadius.sm   // 4px
borderRadius.md   // 8px
borderRadius.lg   // 12px
borderRadius.xl   // 16px
borderRadius.2xl  // 24px
borderRadius.full // 9999px (完全圓形)
```

### 陰影系統

```javascript
shadows.xs   // 微小陰影
shadows.sm   // 小陰影
shadows.md   // 中等陰影
shadows.lg   // 大陰影
shadows.xl   // 超大陰影
shadows.2xl  // 最大陰影
```

### 動畫系統

```javascript
// 時長
animation.duration.fast    // 150ms
animation.duration.normal  // 300ms
animation.duration.slow    // 500ms
animation.duration.slower  // 1000ms

// 緩動曲線
animation.easing.easeIn     // cubic-bezier(0.4, 0, 1, 1)
animation.easing.easeOut    // cubic-bezier(0, 0, 0.2, 1)
animation.easing.easeInOut  // cubic-bezier(0.4, 0, 0.2, 1)
animation.easing.linear     // linear
```

---

## 🧩 核心組件清單

### 表單組件

| 組件 | 檔案 | 用途 |
|------|------|------|
| Button | `button.jsx` | 按鈕（6 種變體，3 種尺寸） |
| Input | `input.jsx` | 輸入框 |
| Textarea | `textarea.jsx` | 文本域 |
| Select | `select.jsx` | 下拉選單 |
| Checkbox | `checkbox.jsx` | 複選框 |
| Radio Group | `radio-group.jsx` | 單選按鈕組 |
| Switch | `switch.jsx` | 開關 |
| Slider | `slider.jsx` | 滑桿 |

### 佈局組件

| 組件 | 檔案 | 用途 |
|------|------|------|
| Card | `card.jsx` | 卡片容器 |
| Separator | `separator.jsx` | 分隔線 |
| Aspect Ratio | `aspect-ratio.jsx` | 寬高比容器 |
| Scroll Area | `scroll-area.jsx` | 滾動區域 |

### 導航組件

| 組件 | 檔案 | 用途 |
|------|------|------|
| Navigation Menu | `navigation-menu.jsx` | 導航菜單 |
| Tabs | `tabs.jsx` | 標籤頁 |
| Accordion | `accordion.jsx` | 手風琴 |
| Breadcrumb | `breadcrumb.jsx` | 麵包屑 |
| Pagination | `pagination.jsx` | 分頁 |

### 反饋組件

| 組件 | 檔案 | 用途 |
|------|------|------|
| Dialog | `dialog.jsx` | 對話框 |
| Alert Dialog | `alert-dialog.jsx` | 警告對話框 |
| Toast | `toast.jsx` | 輕提示 |
| Alert | `alert.jsx` | 警告 |
| Skeleton | `skeleton.jsx` | 骨架屏 |
| Progress | `progress.jsx` | 進度條 |
| Spinner | `spinner.jsx` | 加載動畫 |

### 數據展示組件

| 組件 | 檔案 | 用途 |
|------|------|------|
| Table | `table.jsx` | 表格 |
| Chart | `chart.jsx` | 圖表 |
| Avatar | `avatar.jsx` | 頭像 |
| Badge | `badge.jsx` | 徽章 |
| Calendar | `calendar.jsx` | 日曆 |

### 互動組件

| 組件 | 檔案 | 用途 |
|------|------|------|
| Popover | `popover.jsx` | 彈出框 |
| Tooltip | `tooltip.jsx` | 工具提示 |
| Dropdown Menu | `dropdown-menu.jsx` | 下拉菜單 |
| Context Menu | `context-menu.jsx` | 右鍵菜單 |
| Command | `command.jsx` | 命令面板 (Cmd+K) |

### 特殊組件

| 組件 | 檔案 | 用途 |
|------|------|------|
| Lazy Image | `lazy-image.jsx` | 懶加載圖片 |
| Empty State | `empty-state.jsx` | 空狀態 |
| Loading States | `loading-states.jsx` | 加載狀態 |

---

## 📋 PR 規則速查

### Design PR (設計師)

**✅ 允許改動**:
- `docs/UX/**`
- `docs/UX/tokens.json`
- `docs/**.md`
- `frontend/樣式與文案`

**❌ 禁止改動**:
- `handoff/**/30_API/openapi/**`
- `**/api/**`
- `**/src/**` 的後端與 API 相關檔

### Engineering PR (工程師)

**✅ 允許改動**:
- `**/api/**`
- `**/src/**`
- `handoff/**/30_API/openapi/**`

**❌ 禁止改動**:
- `docs/UX/**` 與設計稿資源

### API 變更流程

1. **建立 RFC Issue** (label: `rfc`)
2. **等待 Owner 核准**
3. **提交工程 PR**

---

## 🔗 快速連結

### GitHub

- [UI/UX Milestone #6](https://github.com/RC918/morningai/milestone/6)
- [UI/UX Issues](https://github.com/RC918/morningai/issues?q=is%3Aissue+label%3Aux)
- [UI/UX PRs](https://github.com/RC918/morningai/pulls?q=is%3Apr+label%3Aux)

### 文檔

- [UI/UX 快速上手](docs/UI_UX_QUICKSTART.md) - 5 分鐘入門
- [UI/UX 資源指南](docs/UI_UX_RESOURCES.md) - 完整資源索引
- [UI/UX Issue 狀態](docs/UI_UX_ISSUE_STATUS.md) - 進度追蹤
- [CONTRIBUTING.md](CONTRIBUTING.md) - 貢獻指南
- [DESIGN_SYSTEM_GUIDELINES.md](DESIGN_SYSTEM_GUIDELINES.md) - 設計系統指南

### 預覽環境

- Vercel 預覽連結: 在 PR 頁面查看
- Chromatic Storybook: 在 PR 頁面查看

---

## 💡 常見任務模板

### 使用現有組件

```jsx
import { Button } from '@/components/ui/button'

<Button variant="primary" size="md">
  Click me
</Button>
```

### 使用 Design Tokens

```jsx
import { applyDesignTokens } from '@/lib/design-tokens'

// 在 App.jsx 中應用
<div className="theme-morning-ai">
  {/* 所有內容 */}
</div>
```

### 創建新組件

```jsx
// src/components/ui/my-component.jsx
import * as React from 'react'
import { cn } from '@/lib/utils'

const MyComponent = React.forwardRef(({ className, ...props }, ref) => {
  return (
    <div
      ref={ref}
      className={cn(
        "rounded-md border p-4", // 使用 Tailwind + Tokens
        className
      )}
      {...props}
    />
  )
})
MyComponent.displayName = "MyComponent"

export { MyComponent }
```

### 創建 Storybook Story

```jsx
// src/stories/MyComponent.stories.jsx
import { MyComponent } from '@/components/ui/my-component'

export default {
  title: 'Components/MyComponent',
  component: MyComponent,
  tags: ['autodocs'],
}

export const Default = {
  args: {
    children: 'Hello World',
  },
}
```

---

## 🆘 故障排除

### Storybook 無法啟動

```bash
# 清除緩存
rm -rf node_modules/.cache

# 重新安裝依賴
npm install

# 重新啟動
npm run storybook
```

### 樣式不生效

1. 確認在 `.theme-morning-ai` 容器內
2. 確認使用 Design Tokens 而非硬編碼值
3. 檢查 Tailwind 配置是否正確

### 組件找不到

```bash
# 搜尋組件位置
rg "export.*MyComponent" --type tsx

# 檢查 import 路徑
rg "import.*MyComponent" --type tsx
```

---

**提示**: 將此速查表加入書籤，隨時查閱！
