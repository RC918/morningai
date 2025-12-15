# Shared UI 使用指南

本指南說明如何在 MorningAI monorepo 中使用 `@morningai/shared-ui` 共享元件庫。

## 📚 目錄

- [快速開始](#快速開始)
- [安裝與設定](#安裝與設定)
- [使用元件](#使用元件)
- [Dashboard 卡片 Archetypes](#dashboard-卡片-archetypes)
- [Apple Kit 使用指南](#apple-kit-使用指南)
- [Design Tokens](#design-tokens)
- [動畫系統](#動畫系統)
- [Storybook](#storybook)
- [最佳實踐](#最佳實踐)
- [常見問題](#常見問題)

## 快速開始

### 為什麼使用 Shared UI？

- ✅ **統一設計系統** - 所有應用使用相同的 UI 元件和設計語言
- ✅ **減少重複程式碼** - 28% 程式碼減少（47 個重複元件消除）
- ✅ **更容易維護** - 修復一次，所有應用自動更新
- ✅ **Apple 級設計** - 內建 spring 動畫、haptic 反饋、無障礙支援
- ✅ **類型安全** - 完整的 TypeScript 支援

### 基本原則

1. **優先使用 shared-ui** - 開發新功能前，先檢查 shared-ui 是否有可用元件
2. **不要重複造輪子** - 避免在應用層重新實作已存在的元件
3. **新元件放 shared-ui** - 如果元件會被多個應用使用，應加入 shared-ui
4. **使用 Design Tokens** - 使用 CSS 變數而非硬編碼顏色/間距

## 安裝與設定

### 在 Workspace Package 中安裝

```bash
# 在你的應用 package.json 中加入
pnpm add @morningai/shared-ui@workspace:*
```

### 在 CSS 中匯入 Design Tokens

```css
/* 在你的主 CSS 檔案中 */
@import '@morningai/shared-ui/tokens.css';
```

或使用 `@source` directive（Tailwind CSS 4）：

```css
@source '@morningai/shared-ui/tokens.css';
```

## 使用元件

### 基本元件使用

```tsx
import { Button, Card, Input, Badge } from '@morningai/shared-ui'

function MyComponent() {
  return (
    <Card>
      <h2>歡迎使用 MorningAI</h2>
      <Input placeholder="輸入文字..." />
      <Button variant="primary">提交</Button>
      <Badge>新功能</Badge>
    </Card>
  )
}
```

### Apple 風格元件

```tsx
import { AppleButton, AppleInput } from '@morningai/shared-ui'
import { User, Lock } from 'lucide-react'

function LoginForm() {
  return (
    <form>
      <AppleInput
        label="Email"
        type="email"
        leftIcon={<User className="h-4 w-4" />}
        required
        haptic="light"
      />
      <AppleInput
        label="Password"
        type="password"
        leftIcon={<Lock className="h-4 w-4" />}
        showPasswordToggle
        required
        haptic="light"
      />
      <AppleButton 
        type="submit" 
        variant="primary"
        haptic="medium"
      >
        登入
      </AppleButton>
    </form>
  )
}
```

### 完整元件列表

#### Layout & Structure (5)
- `Card`, `Separator`, `AspectRatio`, `ScrollArea`, `Resizable`

#### Navigation (7)
- `Tabs`, `Accordion`, `Breadcrumb`, `NavigationMenu`, `Menubar`, `Sidebar`, `Pagination`

#### Forms & Inputs (11)
- `Input`, `Textarea`, `Checkbox`, `RadioGroup`, `Switch`, `Slider`, `Select`, `InputOTP`, `Calendar`, `Form`, `Label`

#### Buttons & Actions (3)
- `Button`, `Toggle`, `ToggleGroup`

#### Feedback & Overlays (14)
- `Dialog`, `AlertDialog`, `Sheet`, `Drawer`, `Popover`, `Tooltip`, `HoverCard`, `ContextMenu`, `DropdownMenu`, `Command`, `Alert`, `Toast`, `Progress`, `Skeleton`

#### Data Display (7)
- `Table`, `Badge`, `Avatar`, `Chart`, `Carousel`, `Collapsible`

#### Apple Components (2)
- `AppleButton`, `AppleInput`

## Dashboard 卡片 Archetypes

Dashboard 卡片 Archetypes 是專為儀表板設計的標準化卡片組件，提供一致的視覺風格和互動模式。

### Archetype 選擇指南

| Archetype | 用途 | Icon 規格 | 互動性 | 使用場景 |
|-----------|------|-----------|--------|----------|
| **StatCard** | KPI 展示 | 40×40px 圓形 | 無 | 數據統計、指標展示 |
| **StatusCard** | 狀態篩選 | 28×28px 方形 | 有 (onClick, isActive) | 篩選器、狀態切換 |
| **MetricCard** | 實體摘要 | 依內容 | 無 | 詳細指標、趨勢展示 |
| **SettingsCard** | 設定面板 | 依內容 | 按鈕動作 | 設定頁面、配置面板 |
| **SectionCard** | 區塊容器 | 可選 | 可選 action | 內容分組、區塊標題 |

### 使用範例

```tsx
import { 
  StatCard, 
  StatusCard, 
  MetricCard, 
  SettingsCard,
  SectionCard,
  TimelineList,
  SystemStatusList,
  ProgressTrack
} from '@morningai/shared-ui'

// StatCard - KPI 展示
<StatCard 
  label="總收入" 
  value="$45,231" 
  trend="+12.5%" 
  icon={<DollarSign />}
/>

// StatusCard - 狀態篩選（支援互動）
<StatusCard 
  label="進行中" 
  count={12} 
  isActive={true}
  onClick={() => setFilter('active')}
/>

// MetricCard - 指標摘要
<MetricCard
  title="轉換率"
  value="3.2%"
  delta="+0.5%"
  deltaType="positive"
/>

// SettingsCard - 設定面板
<SettingsCard
  title="雙因素認證"
  description="增強帳戶安全性"
  icon={<Shield />}
  action={<Button>設定</Button>}
/>

// SectionCard - 區塊容器
<SectionCard title="系統狀態" subtitle="即時監控">
  <SystemStatusList items={statusItems} />
</SectionCard>

// TimelineList - 活動時間軸
<TimelineList items={[
  { time: '10:30', title: '系統更新', description: '完成部署' },
  { time: '09:15', title: '用戶登入', description: 'admin@example.com' }
]} />

// ProgressTrack - 進度追蹤（自動 clamp 0-100%）
<ProgressTrack items={[
  { label: '任務完成', value: 85, target: 90 },
  { label: '測試覆蓋', value: 72, target: 80 }
]} />
```

### 完整 Dashboard 組件清單

| 組件 | 檔案 | 用途 |
|------|------|------|
| StatCard | `stat-card.tsx` | KPI 統計卡片（支援 trend、badge、icon） |
| StatusCard | `status-card.tsx` | 狀態篩選卡片（支援 onClick、isActive） |
| MetricCard | `metric-card.tsx` | 指標摘要卡片（支援 delta、趨勢） |
| SettingsCard | `settings-card.tsx` | 設定面板卡片（支援 icon、action） |
| SectionCard | `section-card.tsx` | 區塊容器卡片（支援 title、subtitle、action） |
| TimelineList | `timeline-list.tsx` | 時間軸列表（活動記錄） |
| SystemStatusList | `system-status-list.tsx` | 系統狀態列表（服務監控） |
| ProgressTrack | `progress-track.tsx` | 進度追蹤列表（自動 clamp 0-100%） |

## Apple Kit 使用指南

Apple Kit 是一套 iOS 風格的 UI 組件，提供 Apple 級的視覺效果和互動體驗。

### 架構層次

Apple Kit 採用三層架構：

1. **Visual Primitives（視覺基元）** - 基礎樣式和動畫
   - Spring 動畫配置
   - Haptic 反饋模式
   - 圓角和陰影系統

2. **Experience Components（體驗組件）** - 可複用的 UI 組件
   - AppleButton、AppleInput（位於 shared-ui）
   - 其他 Apple 組件（位於 frontend-dashboard）

3. **Theme Layer（主題層）** - 設計 tokens 和變數
   - Apple 專用色彩
   - 動畫時長和緩動曲線

### 組件位置

| 組件 | 位置 | 說明 |
|------|------|------|
| AppleButton | `@morningai/shared-ui` | iOS 風格按鈕（4 種變體，3 種尺寸，Spring 動畫） |
| AppleInput | `@morningai/shared-ui` | iOS 風格輸入框（浮動標籤，錯誤/成功狀態） |
| AppleDynamicToast | `frontend-dashboard` | iOS 風格輕提示（4 種變體，自動消失） |
| AppleModal | `frontend-dashboard` | iOS 風格對話框（Backdrop blur，Focus trap） |
| AppleSheet | `frontend-dashboard` | iOS 風格底部抽屜（拖動關閉，Snap points） |
| AppleTabBar | `frontend-dashboard` | iOS 風格標籤欄（活動指示器，Badge 支援） |
| AppleSegmentedControl | `frontend-dashboard` | iOS 風格分段控制器（滑動指示器） |
| AppleLiveActivity | `frontend-dashboard` | iOS 風格實時活動（進度條，自動消失） |
| AppleControlCenter | `frontend-dashboard` | iOS 風格控制中心（快速設置面板） |
| AppleSpotlight | `frontend-dashboard` | iOS 風格 Spotlight 搜尋（Cmd+K） |
| AppleActionSheet | `frontend-dashboard` | iOS 風格操作表（多種操作樣式） |
| ApplePicker | `frontend-dashboard` | iOS 風格選擇器（滾輪式選擇） |

### 使用模式

#### 從 shared-ui 匯入（推薦）

```tsx
import { AppleButton, AppleInput } from '@morningai/shared-ui'

function LoginForm() {
  return (
    <form>
      <AppleInput
        label="Email"
        type="email"
        leftIcon={<User className="h-4 w-4" />}
        required
        haptic="light"
      />
      <AppleButton 
        type="submit" 
        variant="primary"
        haptic="medium"
      >
        登入
      </AppleButton>
    </form>
  )
}
```

#### 從 frontend-dashboard 匯入（進階組件）

```tsx
// 僅在 frontend-dashboard 內部使用
import { AppleModal } from '@/components/apple/apple-modal'
import { AppleSheet } from '@/components/apple/apple-sheet'

function MyFeature() {
  return (
    <>
      <AppleModal open={isOpen} onClose={() => setIsOpen(false)}>
        <h2>確認操作</h2>
        <p>您確定要繼續嗎？</p>
      </AppleModal>
      
      <AppleSheet open={isSheetOpen} onClose={() => setIsSheetOpen(false)}>
        <div>底部抽屜內容</div>
      </AppleSheet>
    </>
  )
}
```

### Apple Theme vs Core Tokens

Apple Kit 使用專用的主題變數，與核心 Design Tokens 分離：

```css
/* Core Tokens（全局使用） */
--color-primary-600
--space-md
--radius-lg

/* Apple Theme（Apple 組件專用） */
--apple-blue
--apple-gray
--apple-spring-duration
--apple-haptic-light
```

### 無障礙支援

所有 Apple 組件都符合 WCAG AAA 標準：

- 完整的 ARIA 標籤和角色
- 鍵盤導航支援
- 螢幕閱讀器優化
- Focus trap 和焦點管理
- Live region 公告
- `prefers-reduced-motion` 支援

## Design Tokens

### 使用 CSS 變數

```tsx
// ✅ 好的做法 - 使用 CSS 變數
<div className="bg-[var(--color-primary-600)] text-white">
  內容
</div>

// ❌ 不好的做法 - 硬編碼顏色
<div className="bg-blue-600 text-white">
  內容
</div>
```

### 在 JavaScript 中匯入 Tokens

```tsx
import tokens from '@morningai/shared-ui/tokens.json'

const primaryColor = tokens.color.primary[500]
const spacing = tokens.space.md
const springEasing = tokens.animation.easing.spring
```

### Token 類別

#### Colors
- **Primary**: `--color-primary-{50-900}`
- **Accent**: `--color-accent-purple-{50-900}`, `--color-accent-orange-{50-900}`
- **Semantic**: `--color-success-{50-900}`, `--color-error-{50-900}`, `--color-warning-{50-900}`
- **Neutral**: `--color-neutral-{50-900}`

#### Spacing
- `--space-xs` (4px), `--space-sm` (8px), `--space-md` (16px), `--space-lg` (24px), `--space-xl` (32px)

#### Radius
- `--radius-sm` (4px), `--radius-md` (8px), `--radius-lg` (12px), `--radius-xl` (16px), `--radius-2xl` (24px)

#### Shadows
- `--shadow-sm`, `--shadow-md`, `--shadow-lg`, `--shadow-xl`, `--shadow-2xl`

## 動畫系統

### Spring 動畫

所有動畫使用 spring physics 達到 Apple 級的自然動態效果：

```tsx
import { motion } from 'framer-motion'
import { getSpringConfig } from '@morningai/shared-ui'

function AnimatedCard() {
  const springConfig = getSpringConfig('smooth')
  
  return (
    <motion.div
      whileHover={{ scale: 1.02 }}
      whileTap={{ scale: 0.98 }}
      transition={springConfig}
    >
      卡片內容
    </motion.div>
  )
}
```

### Spring 預設

- `gentle` - 柔和的動畫（stiffness: 120, damping: 14）
- `default` - 標準動畫（stiffness: 170, damping: 26）
- `bouncy` - 彈跳動畫（stiffness: 180, damping: 12）
- `snappy` - 快速動畫（stiffness: 300, damping: 30）
- `smooth` - 平滑動畫（stiffness: 100, damping: 20）
- `wobbly` - 搖晃動畫（stiffness: 180, damping: 10）

### Reduced Motion 支援

所有動畫自動支援 `prefers-reduced-motion`：

```tsx
import { useReducedMotion } from '@morningai/shared-ui'

function MyComponent() {
  const prefersReducedMotion = useReducedMotion()
  
  return (
    <motion.div
      animate={prefersReducedMotion ? {} : { scale: 1.1 }}
    >
      內容
    </motion.div>
  )
}
```

## Storybook

### 啟動 Storybook

```bash
# 方法 1: 啟動 shared-ui Storybook（推薦）
cd packages/shared-ui && pnpm storybook

# 方法 2: 啟動 owner-console Storybook
cd handoff/20250928/40_App/owner-console && pnpm storybook

# 方法 3: 啟動 frontend-dashboard Storybook
cd handoff/20250928/40_App/frontend-dashboard && pnpm storybook
```

### 建置 Storybook

```bash
cd packages/shared-ui && pnpm build-storybook
```

### 查看元件範例

Storybook 提供所有 shared-ui 元件的互動式範例和文件。

## 最佳實踐

### 1. 檢查 Shared UI 是否有可用元件

在開發新功能前，先檢查 shared-ui 是否已有可用元件：

```bash
# 查看所有可用元件
cat packages/shared-ui/src/index.ts

# 或啟動 Storybook 瀏覽
pnpm --filter frontend-dashboard storybook
```

### 2. 新元件應加入 Shared UI

如果元件會被多個應用使用，應加入 `packages/shared-ui/`：

```bash
# 在 packages/shared-ui/src/components/ 中建立新元件
packages/shared-ui/src/components/my-component.tsx

# 在 index.ts 中匯出
export { MyComponent } from './components/my-component'

# 建置 shared-ui
pnpm --filter @morningai/shared-ui build
```

### 3. 使用 Design Tokens

```tsx
// ✅ 好的做法
<div className="bg-[var(--color-primary-600)] p-[var(--space-md)]">
  內容
</div>

// ❌ 不好的做法
<div className="bg-blue-600 p-4">
  內容
</div>
```

### 4. 避免重複實作

```tsx
// ❌ 不好的做法 - 在應用層重新實作
// src/components/my-button.tsx
export function MyButton() {
  return <button className="...">按鈕</button>
}

// ✅ 好的做法 - 使用 shared-ui
import { Button } from '@morningai/shared-ui'

export function MyFeature() {
  return <Button>按鈕</Button>
}
```

### 5. 加入 Storybook Story

新元件應加入 Storybook story：

```tsx
// packages/shared-ui/src/stories/my-component.stories.tsx
import type { Meta, StoryObj } from '@storybook/react'
import { MyComponent } from '../components/my-component'

const meta: Meta<typeof MyComponent> = {
  title: 'Components/MyComponent',
  component: MyComponent,
}

export default meta
type Story = StoryObj<typeof MyComponent>

export const Default: Story = {
  args: {
    // props
  },
}
```

## 常見問題

### Q: 如何知道 shared-ui 有哪些元件？

A: 有三種方式：
1. 查看 `packages/shared-ui/src/index.ts`
2. 查看 `packages/shared-ui/README.md`
3. 啟動 Storybook: `pnpm --filter frontend-dashboard storybook`

### Q: 我需要的元件不在 shared-ui 中，怎麼辦？

A: 
1. 如果元件只會在一個應用中使用，可以在應用層實作
2. 如果元件可能被多個應用使用，應加入 `packages/shared-ui/`
3. 不確定時，先在應用層實作，之後再決定是否移到 shared-ui

### Q: 如何更新 shared-ui 元件？

A:
1. 修改 `packages/shared-ui/src/components/` 中的元件
2. 執行 `pnpm --filter @morningai/shared-ui build`
3. 所有使用該元件的應用會自動使用新版本

### Q: ESLint 報錯說不能從本地路徑匯入 Apple 元件？

A: 這是正確的！Apple 元件已移到 shared-ui，應該這樣匯入：

```tsx
// ❌ 錯誤
import { AppleButton } from '@/components/apple/apple-button'

// ✅ 正確
import { AppleButton } from '@morningai/shared-ui'
```

### Q: 如何在 shared-ui 中加入新的 Design Token？

A:
1. 編輯 `packages/shared-ui/src/tokens.json`
2. 執行 `pnpm --filter @morningai/shared-ui build`
3. 在應用中使用新的 CSS 變數

### Q: 動畫在某些使用者的裝置上不顯示？

A: 這是正常的！如果使用者啟用了「減少動態效果」（prefers-reduced-motion），動畫會自動停用以提升無障礙性。

## 相關文件

- [packages/shared-ui/README.md](../packages/shared-ui/README.md) - Shared UI 套件文件
- [CONTRIBUTING.md](../CONTRIBUTING.md) - 貢獻指南
- [UI_UX_QUICKSTART.md](./UI_UX_QUICKSTART.md) - UI/UX 快速開始
- [UI_UX_CHEATSHEET.md](./UI_UX_CHEATSHEET.md) - UI/UX 速查表

## 需要協助？

如有任何問題或建議，請：
1. 查看 Storybook 中的元件範例
2. 查看 `packages/shared-ui/README.md`
3. 在 GitHub 上開 Issue
4. 聯繫設計系統團隊

---

**最後更新**: 2025-12-15
