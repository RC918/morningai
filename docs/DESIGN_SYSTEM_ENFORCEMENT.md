# 設計系統強制執行指南 (Design System Enforcement Guide)

## 概述 (Overview)

本文檔說明 MorningAI 專案如何強制使用 `@morningai/shared-ui` 設計系統，以及允許的第三方依賴例外清單。

## 目標 (Goals)

1. **統一 UI 體驗**: 確保所有應用使用一致的設計語言和元件
2. **減少重複代碼**: 避免在多個應用中重複實作相同的 UI 元件
3. **提升可維護性**: 集中管理 UI 元件，便於更新和修復
4. **加速開發**: 開發者可直接使用現成的高品質元件
5. **確保無障礙性**: 所有 shared-ui 元件都符合 WCAG AAA 標準

## 強制執行機制 (Enforcement Mechanisms)

### 1. ESLint 規則 (ESLint Rules)

**位置**: 
- `handoff/20250928/40_App/frontend-dashboard/eslint.config.js`
- `handoff/20250928/40_App/owner-console/eslint.config.js`

**規則**: `no-restricted-imports`

**阻擋的 import**:
- `@radix-ui/react-*` - Radix UI 元件庫
- `@mui/*` - Material-UI 元件庫
- `@headlessui/*` - Headless UI 元件庫
- `@chakra-ui/*` - Chakra UI 元件庫

**錯誤訊息**:
```
Direct import of UI component libraries is not allowed. 
Use @morningai/shared-ui instead. 
Allowed exceptions: lucide-react (icons), recharts (charts), date-fns (dates).
```

**執行方式**:
```bash
# 在應用目錄執行
pnpm lint

# 範例輸出
src/components/MyComponent.tsx
  2:1  warning  '@radix-ui/react-dialog' import is restricted from being used by a pattern. 
       Direct import of UI component libraries is not allowed. Use @morningai/shared-ui instead.
```

### 2. CI 審計腳本 (CI Audit Script)

**位置**: `scripts/audit-shared-ui-imports.sh`

**功能**:
- 掃描所有 TypeScript/JavaScript 檔案
- 檢測違規的 UI 元件庫 import
- 生成詳細的違規報告
- 排除測試檔案、stories、範例等

**執行方式**:
```bash
# 本地執行
./scripts/audit-shared-ui-imports.sh

# CI 自動執行（每個 PR）
# 見 .github/workflows/enforce-shared-ui.yml
```

**輸出範例**:
```
🔍 Auditing shared-ui import compliance...

📂 Scanning: handoff/20250928/40_App/frontend-dashboard/src
⚠️  src/components/MyComponent.tsx
   → 2:import { Dialog } from "@radix-ui/react-dialog"

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📊 Audit Summary
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Files scanned: 243
Violations found: 1

⚠️  Stage 1 (Warn Mode): Violations detected but not blocking
```

### 3. GitHub Actions Workflow

**位置**: `.github/workflows/enforce-shared-ui.yml`

**觸發條件**:
- Pull Request 到 `main` 分支
- 修改 frontend-dashboard 或 owner-console 的檔案

**功能**:
- 自動執行審計腳本
- 在 PR 中發布評論報告違規
- 提供修復建議和文檔連結

### 4. PR 模板檢查清單

**位置**: `.github/pull_request_template.md`

**檢查項目**:
- [ ] 我已使用 `@morningai/shared-ui` 元件，而非直接 import `@radix-ui/react-*`、`@mui/*` 等 UI 元件庫
- [ ] 我沒有直接 import `@headlessui/*` 或 `@chakra-ui/*`
- [ ] 如果使用第三方庫，僅限於允許的例外
- [ ] ESLint `no-restricted-imports` 規則通過
- [ ] CI 的 "Enforce Shared-UI Usage" 檢查通過

### 5. CODEOWNERS 審查

**位置**: `.github/CODEOWNERS`

**審查範圍**:
- `/packages/shared-ui/` - 所有 shared-ui 變更
- UI 元件目錄 - 應用層的 UI 元件變更
- ESLint 配置 - 強制執行規則的配置變更

**審查者**: @RC918 (Ryan Chen - 設計負責人)

## 允許的第三方依賴 (Allowed Third-Party Dependencies)

### 圖示庫 (Icons)

**允許**: `lucide-react`

**理由**: 
- Lucide 是高品質的開源圖示庫
- 提供一致的視覺風格
- 支援 tree-shaking，不影響 bundle size
- 已整合到 shared-ui 的設計系統中

**使用範例**:
```tsx
import { ChevronDown, Search, User } from 'lucide-react';

<Button>
  <Search className="size-4" />
  搜尋
</Button>
```

### 圖表庫 (Charts)

**允許**: `recharts`

**理由**:
- React 生態系中最成熟的圖表庫
- 提供豐富的圖表類型和客製化選項
- 響應式設計，支援無障礙
- 與 React 整合良好

**使用範例**:
```tsx
import { LineChart, Line, XAxis, YAxis } from 'recharts';

<LineChart data={data}>
  <Line type="monotone" dataKey="value" stroke="#8884d8" />
  <XAxis dataKey="name" />
  <YAxis />
</LineChart>
```

### 日期處理 (Date Utilities)

**允許**: `date-fns`

**理由**:
- 輕量級、模組化的日期處理庫
- 支援 tree-shaking，只打包使用的函數
- 提供完整的國際化支援
- 函數式 API，易於測試

**使用範例**:
```tsx
import { format, parseISO, addDays } from 'date-fns';
import { zhTW, enUS } from 'date-fns/locale';

const formattedDate = format(new Date(), 'PPP', { locale: zhTW });
// 輸出: 2025年11月21日
```

### 為什麼不允許其他 UI 元件庫？

**不允許的庫**:
- `@radix-ui/react-*` - 應透過 shared-ui 使用
- `@mui/*` - 設計風格不一致
- `@headlessui/*` - 功能與 Radix UI 重疊
- `@chakra-ui/*` - 設計風格不一致

**理由**:
1. **設計一致性**: 不同 UI 庫有不同的設計語言，會導致視覺不一致
2. **Bundle Size**: 多個 UI 庫會顯著增加 bundle size
3. **維護成本**: 需要學習和維護多個庫的 API
4. **無障礙性**: shared-ui 已確保所有元件符合 WCAG AAA，直接使用第三方庫可能不符合標準

## 三階段推出計劃 (3-Stage Rollout)

### Stage 1: Warn Mode (當前階段)

**時程**: 合併後運行 1 週

**行為**:
- 跨應用 import 限制維持 `error`（嚴格執行）
- UI 元件庫限制由 CI 審計腳本以 `warn` 模式處理（警告但不阻擋）
- CI 審計腳本執行但不阻擋 PR 合併
- 在 PR 中發布違規報告和修復建議
- 收集反饋並調整規則

**目標**:
- 讓團隊熟悉新規則
- 識別誤報和邊緣情況
- 提供遷移指南和支援

### Stage 2: Diff-Only Enforcement (計劃中)

**時程**: Stage 1 結束後（合併後約 1 週）

**行為**:
- 僅檢查 PR 中新增/修改的程式碼
- 違規會阻擋 PR 合併
- 現有程式碼的違規不會阻擋
- 逐步遷移現有違規

**目標**:
- 確保新程式碼符合規範
- 避免增加新的技術債
- 給予時間遷移現有程式碼

### Stage 3: Full Enforcement (未來)

**時程**: 待定（所有現有違規修復後）

**行為**:
- 檢查所有程式碼（包含現有程式碼）
- 任何違規都會阻擋 PR 合併
- 完全強制執行設計系統政策

**目標**:
- 100% 合規
- 完全統一的設計系統
- 零技術債

## 如何修復違規 (How to Fix Violations)

### 步驟 1: 識別違規

執行 ESLint 或查看 CI 報告：
```bash
pnpm lint
```

### 步驟 2: 檢查 shared-ui 是否有對應元件

查看 Storybook 或 shared-ui 原始碼：
```bash
# 啟動 Storybook
pnpm --filter @morningai/shared-ui storybook

# 或查看原始碼
ls packages/shared-ui/src/components/ui/
```

### 步驟 3a: 使用現有的 shared-ui 元件

**修復前**:
```tsx
import { Dialog } from '@radix-ui/react-dialog';

<Dialog>
  <DialogContent>內容</DialogContent>
</Dialog>
```

**修復後**:
```tsx
import { Dialog, DialogContent } from '@morningai/shared-ui';

<Dialog>
  <DialogContent>內容</DialogContent>
</Dialog>
```

### 步驟 3b: 元件不存在 - 加入 shared-ui

如果 shared-ui 沒有需要的元件：

1. **在 shared-ui 中建立元件**:
```bash
cd packages/shared-ui
# 建立新元件
touch src/components/ui/my-component.tsx
```

2. **實作元件** (基於 Radix UI):
```tsx
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
```

3. **加入 Storybook story**:
```tsx
// packages/shared-ui/src/stories/MyComponent.stories.tsx
import { MyComponent } from '../components/ui/my-component';

export default {
  title: 'Components/MyComponent',
  component: MyComponent,
};

export const Default = () => <MyComponent />;
```

4. **匯出元件**:
```tsx
// packages/shared-ui/src/index.ts
export { MyComponent } from './components/ui/my-component';
```

5. **在應用中使用**:
```tsx
import { MyComponent } from '@morningai/shared-ui';
```

### 步驟 4: 驗證修復

```bash
# 執行 ESLint
pnpm lint

# 執行審計腳本
./scripts/audit-shared-ui-imports.sh

# 執行測試
pnpm test
```

## 常見問題 (FAQ)

### Q1: 為什麼不能直接使用 Radix UI？

A: shared-ui 基於 Radix UI 建構，但加入了：
- 統一的設計 tokens（顏色、間距、字型等）
- WCAG AAA 無障礙性增強
- 一致的 API 和命名規範
- 完整的 TypeScript 類型定義
- Storybook 文檔和範例

### Q2: 如果 shared-ui 的元件不符合我的需求怎麼辦？

A: 有三個選項：
1. **擴展現有元件**: 透過 props 和 className 客製化
2. **提出功能請求**: 在 shared-ui 中加入新功能
3. **建立新元件**: 在 shared-ui 中建立新元件供所有人使用

### Q3: 測試檔案和 Storybook stories 也需要遵守嗎？

A: 不需要。以下檔案類型會被排除：
- `*.test.tsx`, `*.test.ts`
- `*.spec.tsx`, `*.spec.ts`
- `*.stories.tsx`, `*.stories.ts`
- `__tests__/` 目錄
- `scripts/` 目錄
- `examples/` 目錄

### Q4: 我可以申請例外嗎？

A: 可以，但需要：
1. 在 PR 中說明理由
2. 獲得設計負責人 (@RC918) 批准
3. 更新此文檔記錄例外情況

### Q5: 如果有緊急情況需要立即合併怎麼辦？

A: 請參考 [Emergency Override Runbook](./EMERGENCY_OVERRIDE_RUNBOOK.md)。此流程僅用於真正的緊急情況（生產環境重大 bug、時間敏感的業務需求等），需要：
1. 獲得 @RC918 的明確批准
2. 臨時移除 branch protection 檢查
3. 合併後立即復原檢查
4. 建立 follow-up issue 追蹤修復（7 天期限）

**注意**：沒有自動繞過機制。所有例外都需要明確的管理員批准和記錄。

### Q6: Stage 1 (warn mode) 會持續多久？

A: Stage 1 已完成（2025-11-21 至 2025-11-28）。當前處於 **Stage 2: Diff-Only Enforcement**，違規會阻擋 PR 合併。

## 相關資源 (Resources)

- 📚 [快速修復指南（2 分鐘）](./DESIGN_SYSTEM_QUICKSTART.md)
- 🚨 [緊急繞過流程](./EMERGENCY_OVERRIDE_RUNBOOK.md)
- 🎨 [Storybook](https://storybook.morningai.com) (執行 `pnpm --filter @morningai/shared-ui storybook`)
- 📖 [Radix UI 文檔](https://www.radix-ui.com/primitives/docs/overview/introduction)
- ♿ [WCAG AAA 標準](https://www.w3.org/WAI/WCAG2AAA-Conformance)
- 🔧 [ESLint no-restricted-imports](https://eslint.org/docs/latest/rules/no-restricted-imports)

## 支援與反饋 (Support & Feedback)

如有問題或建議，請：
1. 在 PR 中留言 (標記 @RC918)
2. 在 Slack #design-system 頻道討論
3. 提交 GitHub Issue

---

**最後更新**: 2025-11-21  
**維護者**: @RC918 (Ryan Chen)  
**版本**: 1.0.0 (Stage 1 - Warn Mode)
