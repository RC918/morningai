# 設計系統快速修復指南 (2 分鐘)

> 快速修復 shared-ui import 違規的實用指南

## 🚨 發現違規？按照這 3 步驟修復

### Step 1: 確認違規類型 (30 秒)

CI 審計腳本會告訴你哪個檔案有問題。常見違規：

```typescript
// ❌ 違規：直接 import Radix UI
import { Dialog } from '@radix-ui/react-dialog';

// ❌ 違規：直接 import MUI
import { Button } from '@mui/material';

// ❌ 違規：直接 import Headless UI
import { Menu } from '@headlessui/react';
```

### Step 2: 檢查 shared-ui 是否有對應元件 (30 秒)

**方法 A：查看 Storybook**
```bash
cd packages/shared-ui
pnpm storybook
# 瀏覽器開啟 http://localhost:6006
```

**方法 B：查看原始碼**
```bash
ls packages/shared-ui/src/components/ui/
# 或查看 packages/shared-ui/src/index.ts
```

**方法 C：查看文檔**
- 查看 `packages/shared-ui/README.md`
- 查看 `docs/DESIGN_SYSTEM_ENFORCEMENT.md`

### Step 3: 修復 import (1 分鐘)

#### 情況 A：元件已存在於 shared-ui ✅

**修復前**：
```typescript
import { Dialog, DialogContent, DialogTitle } from '@radix-ui/react-dialog';
import { Button } from '@mui/material';
```

**修復後**：
```typescript
import { Dialog, DialogContent, DialogTitle, Button } from '@morningai/shared-ui';
```

#### 情況 B：元件不存在於 shared-ui 🔧

**選項 1：快速新增到 shared-ui（推薦）**

1. 在 `packages/shared-ui/src/components/ui/` 建立元件
2. 基於 Radix UI 實作（保持一致性）
3. 匯出到 `packages/shared-ui/src/index.ts`

**範例**：
```typescript
// packages/shared-ui/src/components/ui/my-component.tsx
import * as RadixMyComponent from '@radix-ui/react-my-component';
import { cn } from '../../utils';

export function MyComponent({ className, ...props }) {
  return (
    <RadixMyComponent.Root
      className={cn('base-styles', className)}
      {...props}
    />
  );
}

// packages/shared-ui/src/index.ts
export { MyComponent } from './components/ui/my-component';
```

**選項 2：使用 Slot 作為臨時解決方案**

如果只需要 `Slot`（用於 composition）：

```typescript
// packages/shared-ui/src/index.ts
export { Slot } from '@radix-ui/react-slot';

// 你的檔案
import { Slot } from '@morningai/shared-ui';
```

## 📋 常見修復範例

### Dialog / Modal

```typescript
// ❌ 修復前
import { Dialog, DialogContent } from '@radix-ui/react-dialog';

// ✅ 修復後
import { Dialog, DialogContent } from '@morningai/shared-ui';
```

### Button

```typescript
// ❌ 修復前
import { Button } from '@mui/material';

// ✅ 修復後
import { Button } from '@morningai/shared-ui';
```

### Dropdown / Select

```typescript
// ❌ 修復前
import { Select, SelectTrigger } from '@radix-ui/react-select';

// ✅ 修復後
import { Select, SelectTrigger } from '@morningai/shared-ui';
```

### Tooltip

```typescript
// ❌ 修復前
import { Tooltip, TooltipContent } from '@radix-ui/react-tooltip';

// ✅ 修復後
import { Tooltip, TooltipContent } from '@morningai/shared-ui';
```

### Popover

```typescript
// ❌ 修復前
import { Popover, PopoverContent } from '@radix-ui/react-popover';

// ✅ 修復後
import { Popover, PopoverContent } from '@morningai/shared-ui';
```

## ✅ 驗證修復

```bash
# 1. 執行 ESLint（檢查跨應用 import）
pnpm lint

# 2. 執行審計腳本（檢查 UI 元件庫 import）
./scripts/audit-shared-ui-imports.sh

# 3. 執行測試
pnpm test

# 4. 本地運行應用
pnpm dev
```

## 🎯 允許的例外

這些第三方庫**可以**直接 import：

### ✅ 圖示庫
```typescript
import { ChevronDown, Search, User } from 'lucide-react';
```

### ✅ 圖表庫
```typescript
import { LineChart, Line, XAxis, YAxis } from 'recharts';
```

### ✅ 日期處理
```typescript
import { format, parseISO, addDays } from 'date-fns';
import { zhTW, enUS } from 'date-fns/locale';
```

## 🚫 不允許的 import

這些庫**不可以**直接 import，必須透過 shared-ui：

- `@radix-ui/react-*` - 應透過 shared-ui 使用
- `@mui/*` - 設計風格不一致
- `@headlessui/*` - 功能與 Radix UI 重疊
- `@chakra-ui/*` - 設計風格不一致

## 💡 Pro Tips

### Tip 1: 批次修復
如果有多個檔案違規，可以使用 find + sed：

```bash
# 範例：批次替換 Dialog import
find handoff/20250928/40_App/frontend-dashboard/src -name "*.tsx" -exec sed -i "s/@radix-ui\/react-dialog/@morningai\/shared-ui/g" {} +
```

### Tip 2: 使用 IDE 自動完成
在 VSCode 中，輸入 `import { ` 後按 `Ctrl+Space`，會自動建議 shared-ui 的元件。

### Tip 3: 查看現有用法
搜尋代碼庫中其他檔案如何使用該元件：

```bash
grep -r "import.*Dialog.*from.*shared-ui" handoff/20250928/40_App/
```

## 🆘 需要幫助？

### 問題 1: 不確定用哪個 shared-ui 元件
→ 查看 Storybook 或詢問 @RC918

### 問題 2: shared-ui 元件功能不足
→ 在 shared-ui 中擴展元件或提出功能請求

### 問題 3: 緊急情況需要繞過
→ Stage 2 時可使用 `design-exception` 標籤（需 @RC918 審核）

## 📚 延伸閱讀

- **完整文檔**: `docs/DESIGN_SYSTEM_ENFORCEMENT.md`
- **Shared-UI README**: `packages/shared-ui/README.md`
- **Radix UI 文檔**: https://www.radix-ui.com/primitives/docs/overview/introduction
- **WCAG AAA 標準**: https://www.w3.org/WAI/WCAG2AAA-Conformance

## ⏰ Timeline

- **Stage 1 (當前)**: Warn mode - 違規會報告但不阻擋（1 週）
- **Stage 2 (下週)**: Diff-only enforcement - 新代碼必須合規
- **Stage 3 (未來)**: Full enforcement - 所有代碼必須合規

---

**最後更新**: 2025-11-21  
**維護者**: @RC918 (Ryan Chen)  
**版本**: 1.0.0

**有問題？** 在 PR 中標記 @RC918 或在 Slack #design-system 頻道討論
