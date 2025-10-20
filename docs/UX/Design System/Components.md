# 組件指南

## 概述

MorningAI 組件庫基於 Radix UI 與 Tailwind CSS 構建，提供一套完整、可訪問、可自訂的 UI 組件。所有組件遵循 WCAG 2.1 AA 標準，支援鍵盤導航與螢幕閱讀器。

## 組件架構

### 組件分類

```
components/
├── ui/                          # 基礎組件 (Radix UI)
│   ├── button.jsx
│   ├── input.jsx
│   ├── select.jsx
│   ├── dialog.jsx
│   ├── dropdown-menu.jsx
│   ├── tooltip.jsx
│   └── ...
├── layout/                      # 佈局組件
│   ├── Sidebar.jsx
│   ├── Header.jsx
│   ├── Footer.jsx
│   └── Container.jsx
├── dashboard/                   # 儀表板組件
│   ├── Dashboard.jsx
│   ├── DashboardWidget.jsx
│   └── DashboardGrid.jsx
└── shared/                      # 共用組件
    ├── LoadingSpinner.jsx
    ├── ErrorBoundary.jsx
    ├── EmptyState.jsx
    └── Skeleton.jsx
```

## 基礎組件

### Button (按鈕)

**變體**
- `default`: 主要按鈕
- `secondary`: 次要按鈕
- `outline`: 外框按鈕
- `ghost`: 幽靈按鈕
- `destructive`: 危險操作按鈕

**尺寸**
- `sm`: 小型 (px-3 py-1.5 text-sm)
- `md`: 中型 (px-4 py-2 text-base)
- `lg`: 大型 (px-6 py-3 text-lg)

**範例**

```jsx
import { Button } from '@/components/ui/button'

// 主要按鈕
<Button variant="default" size="md">
  保存變更
</Button>

// 次要按鈕
<Button variant="secondary" size="md">
  取消
</Button>

// 危險操作
<Button variant="destructive" size="md">
  刪除
</Button>

// 載入狀態
<Button disabled>
  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
  處理中...
</Button>
```

**無障礙**
```jsx
// 圖示按鈕需要 aria-label
<Button variant="ghost" size="sm" aria-label="關閉對話框">
  <X className="h-4 w-4" aria-hidden="true" />
</Button>

// 禁用狀態需要說明
<Button disabled aria-disabled="true" title="請先填寫必填欄位">
  提交
</Button>
```

### Input (輸入框)

**類型**
- `text`: 文字輸入
- `email`: 電子郵件
- `password`: 密碼
- `number`: 數字
- `search`: 搜尋

**範例**

```jsx
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'

// 基本輸入
<div className="space-y-2">
  <Label htmlFor="email">電子郵件</Label>
  <Input
    id="email"
    type="email"
    placeholder="your@email.com"
    aria-required="true"
  />
</div>

// 錯誤狀態
<div className="space-y-2">
  <Label htmlFor="password">密碼</Label>
  <Input
    id="password"
    type="password"
    aria-invalid="true"
    aria-describedby="password-error"
  />
  <p id="password-error" className="text-sm text-error-500" role="alert">
    密碼至少需要 8 個字元
  </p>
</div>

// 搜尋框
<div className="relative">
  <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" aria-hidden="true" />
  <Input
    type="search"
    placeholder="搜尋小工具..."
    className="pl-10"
    aria-label="搜尋小工具"
  />
</div>
```

### Select (下拉選單)

**範例**

```jsx
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'

<Select defaultValue="all">
  <SelectTrigger className="w-[180px]" aria-label="選擇時間範圍">
    <SelectValue placeholder="選擇時間範圍" />
  </SelectTrigger>
  <SelectContent>
    <SelectItem value="all">全部時間</SelectItem>
    <SelectItem value="today">今天</SelectItem>
    <SelectItem value="week">本週</SelectItem>
    <SelectItem value="month">本月</SelectItem>
  </SelectContent>
</Select>
```

### Dialog (對話框)

**範例**

```jsx
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog'

<Dialog>
  <DialogTrigger asChild>
    <Button variant="outline">開啟對話框</Button>
  </DialogTrigger>
  <DialogContent>
    <DialogHeader>
      <DialogTitle>確認刪除</DialogTitle>
      <DialogDescription>
        此操作無法復原。確定要刪除此項目嗎？
      </DialogDescription>
    </DialogHeader>
    <DialogFooter>
      <Button variant="secondary">取消</Button>
      <Button variant="destructive">刪除</Button>
    </DialogFooter>
  </DialogContent>
</Dialog>
```

**無障礙**
- 自動管理焦點 (開啟時焦點移至對話框)
- Esc 鍵關閉
- 點擊背景關閉
- `aria-labelledby` 與 `aria-describedby` 自動設定

### Dropdown Menu (下拉選單)

**範例**

```jsx
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'

<DropdownMenu>
  <DropdownMenuTrigger asChild>
    <Button variant="ghost" size="sm">
      <MoreVertical className="h-4 w-4" />
    </Button>
  </DropdownMenuTrigger>
  <DropdownMenuContent align="end">
    <DropdownMenuLabel>操作</DropdownMenuLabel>
    <DropdownMenuSeparator />
    <DropdownMenuItem>
      <Edit className="mr-2 h-4 w-4" />
      編輯
    </DropdownMenuItem>
    <DropdownMenuItem>
      <Copy className="mr-2 h-4 w-4" />
      複製
    </DropdownMenuItem>
    <DropdownMenuSeparator />
    <DropdownMenuItem className="text-error-500">
      <Trash className="mr-2 h-4 w-4" />
      刪除
    </DropdownMenuItem>
  </DropdownMenuContent>
</DropdownMenu>
```

### Tooltip (提示框)

**範例**

```jsx
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from '@/components/ui/tooltip'

<TooltipProvider>
  <Tooltip>
    <TooltipTrigger asChild>
      <Button variant="ghost" size="sm" aria-label="更多資訊">
        <Info className="h-4 w-4" />
      </Button>
    </TooltipTrigger>
    <TooltipContent>
      <p>此功能僅限專業版用戶使用</p>
    </TooltipContent>
  </Tooltip>
</TooltipProvider>
```

### Card (卡片)

**範例**

```jsx
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from '@/components/ui/card'

<Card>
  <CardHeader>
    <CardTitle>今日成本</CardTitle>
    <CardDescription>過去 24 小時的 API 使用成本</CardDescription>
  </CardHeader>
  <CardContent>
    <div className="text-3xl font-bold">$45.67</div>
    <p className="text-sm text-success-500">
      ↓ 12% 較昨日
    </p>
  </CardContent>
  <CardFooter>
    <Button variant="outline" size="sm" className="w-full">
      查看詳情
    </Button>
  </CardFooter>
</Card>
```

## 佈局組件

### Sidebar (側欄)

**功能**
- 可折疊
- 響應式 (移動端自動隱藏)
- 支援巢狀選單
- 徽章顯示 (如待審批數量)

**範例**

```jsx
import { Sidebar } from '@/components/layout/Sidebar'

<Sidebar
  isCollapsed={isCollapsed}
  onToggle={() => setIsCollapsed(!isCollapsed)}
  user={currentUser}
  menuItems={[
    {
      label: 'Dashboard',
      icon: LayoutDashboard,
      href: '/dashboard',
      active: true
    },
    {
      label: '待審批',
      icon: CheckCircle,
      href: '/approvals',
      badge: 3
    },
    // ...
  ]}
/>
```

### Container (容器)

**範例**

```jsx
import { Container } from '@/components/layout/Container'

// 標準容器 (max-w-7xl)
<Container>
  <h1>頁面標題</h1>
  <p>內容...</p>
</Container>

// 窄容器 (max-w-4xl)
<Container size="narrow">
  <article>文章內容...</article>
</Container>

// 全寬容器
<Container size="full">
  <div>全寬內容...</div>
</Container>
```

## 儀表板組件

### Dashboard Widget (小工具)

**類型**
- `metric`: KPI 指標
- `chart`: 圖表
- `list`: 列表
- `table`: 表格

**範例**

```jsx
import { DashboardWidget } from '@/components/dashboard/DashboardWidget'

// KPI 指標
<DashboardWidget
  type="metric"
  title="CPU 使用率"
  value="45%"
  trend={{ value: -5, direction: 'down' }}
  icon={Cpu}
/>

// 圖表
<DashboardWidget
  type="chart"
  title="響應時間趨勢"
  data={responseTimeData}
  chartType="line"
/>

// 列表
<DashboardWidget
  type="list"
  title="最近決策"
  items={recentDecisions}
  renderItem={(item) => (
    <div className="flex items-center justify-between">
      <span>{item.title}</span>
      <Badge variant={item.status}>{item.statusText}</Badge>
    </div>
  )}
/>
```

## 共用組件

### Loading Spinner (載入動畫)

**範例**

```jsx
import { LoadingSpinner } from '@/components/shared/LoadingSpinner'

// 全頁載入
<LoadingSpinner size="lg" fullPage />

// 區塊載入
<div className="relative h-64">
  <LoadingSpinner size="md" />
</div>

// 按鈕載入
<Button disabled>
  <LoadingSpinner size="sm" className="mr-2" />
  處理中...
</Button>
```

### Empty State (空狀態)

**範例**

```jsx
import { EmptyState } from '@/components/shared/EmptyState'

<EmptyState
  icon={Inbox}
  title="尚無任務"
  description="建立第一個任務以開始使用 Morning AI"
  action={
    <Button onClick={handleCreateTask}>
      <Plus className="mr-2 h-4 w-4" />
      建立任務
    </Button>
  }
/>
```

### Skeleton (骨架屏)

**範例**

```jsx
import { Skeleton } from '@/components/shared/Skeleton'

// 文字骨架
<div className="space-y-2">
  <Skeleton className="h-4 w-full" />
  <Skeleton className="h-4 w-3/4" />
  <Skeleton className="h-4 w-1/2" />
</div>

// 卡片骨架
<Card>
  <CardHeader>
    <Skeleton className="h-6 w-1/3" />
    <Skeleton className="h-4 w-2/3" />
  </CardHeader>
  <CardContent>
    <Skeleton className="h-32 w-full" />
  </CardContent>
</Card>
```

### Error Boundary (錯誤邊界)

**範例**

```jsx
import { ErrorBoundary } from '@/components/shared/ErrorBoundary'

<ErrorBoundary
  fallback={({ error, eventId, resetError }) => (
    <div className="flex flex-col items-center justify-center min-h-screen">
      <h1 className="text-2xl font-bold mb-4">發生錯誤</h1>
      <p className="text-gray-600 mb-4">{error.message}</p>
      <p className="text-sm text-gray-400 mb-6">事件 ID: {eventId}</p>
      <div className="flex gap-4">
        <Button onClick={resetError}>重試</Button>
        <Button variant="outline" onClick={() => window.location.href = '/'}>
          返回首頁
        </Button>
      </div>
    </div>
  )}
>
  <App />
</ErrorBoundary>
```

## 組件開發規範

### 命名規範

**組件檔案**
- PascalCase: `DashboardWidget.jsx`
- 一個檔案一個組件

**Props**
- camelCase: `isLoading`, `onSubmit`
- 布林值以 `is`, `has`, `should` 開頭
- 事件處理以 `on` 開頭

### Props 定義

```jsx
import PropTypes from 'prop-types'

function Button({ 
  variant = 'default',
  size = 'md',
  disabled = false,
  children,
  onClick,
  ...props 
}) {
  return (
    <button
      className={cn(buttonVariants({ variant, size }))}
      disabled={disabled}
      onClick={onClick}
      {...props}
    >
      {children}
    </button>
  )
}

Button.propTypes = {
  variant: PropTypes.oneOf(['default', 'secondary', 'outline', 'ghost', 'destructive']),
  size: PropTypes.oneOf(['sm', 'md', 'lg']),
  disabled: PropTypes.bool,
  children: PropTypes.node.isRequired,
  onClick: PropTypes.func,
}

export { Button }
```

### 樣式規範

**使用 Tailwind 類別**
```jsx
// ✅ 正確：使用 Tailwind 類別
<div className="flex items-center gap-4 p-6 rounded-lg bg-white shadow-md">
  {/* ... */}
</div>

// ❌ 錯誤：內聯樣式
<div style={{ display: 'flex', padding: '24px' }}>
  {/* ... */}
</div>
```

**條件樣式**
```jsx
import { cn } from '@/lib/utils'

<button
  className={cn(
    'px-4 py-2 rounded-lg font-medium transition-colors',
    variant === 'primary' && 'bg-primary-500 text-white hover:bg-primary-600',
    variant === 'secondary' && 'bg-gray-200 text-gray-900 hover:bg-gray-300',
    disabled && 'opacity-50 cursor-not-allowed'
  )}
>
  {children}
</button>
```

### 無障礙規範

**語義化 HTML**
```jsx
// ✅ 正確：使用語義元素
<nav aria-label="主導航">
  <ul>
    <li><a href="/dashboard">Dashboard</a></li>
  </ul>
</nav>

// ❌ 錯誤：使用 div
<div className="nav">
  <div onClick={() => navigate('/dashboard')}>Dashboard</div>
</div>
```

**ARIA 屬性**
```jsx
// 按鈕
<button aria-label="關閉對話框" onClick={onClose}>
  <X className="h-4 w-4" aria-hidden="true" />
</button>

// 狀態提示
<div role="status" aria-live="polite">
  已保存變更
</div>

// 錯誤提示
<div role="alert" aria-live="assertive">
  保存失敗，請重試
</div>

// 載入狀態
<div role="status" aria-live="polite" aria-busy="true">
  <LoadingSpinner />
  <span className="sr-only">載入中...</span>
</div>
```

**鍵盤導航**
```jsx
function Dropdown({ items, onSelect }) {
  const [selectedIndex, setSelectedIndex] = useState(0)

  const handleKeyDown = (e) => {
    switch (e.key) {
      case 'ArrowDown':
        e.preventDefault()
        setSelectedIndex((prev) => Math.min(prev + 1, items.length - 1))
        break
      case 'ArrowUp':
        e.preventDefault()
        setSelectedIndex((prev) => Math.max(prev - 1, 0))
        break
      case 'Enter':
        e.preventDefault()
        onSelect(items[selectedIndex])
        break
      case 'Escape':
        e.preventDefault()
        onClose()
        break
    }
  }

  return (
    <div role="listbox" onKeyDown={handleKeyDown} tabIndex={0}>
      {items.map((item, index) => (
        <div
          key={item.id}
          role="option"
          aria-selected={index === selectedIndex}
          onClick={() => onSelect(item)}
        >
          {item.label}
        </div>
      ))}
    </div>
  )
}
```

## 性能優化

### Code Splitting

```jsx
import { lazy, Suspense } from 'react'

// 路由級別分割
const Dashboard = lazy(() => import('./components/Dashboard'))
const Strategies = lazy(() => import('./components/StrategyManagement'))

function App() {
  return (
    <Suspense fallback={<LoadingSpinner fullPage />}>
      <Routes>
        <Route path="/dashboard" element={<Dashboard />} />
        <Route path="/strategies" element={<Strategies />} />
      </Routes>
    </Suspense>
  )
}
```

### Memoization

```jsx
import { memo, useMemo, useCallback } from 'react'

// 組件 memo
const DashboardWidget = memo(function DashboardWidget({ data, onRefresh }) {
  // 昂貴計算使用 useMemo
  const processedData = useMemo(() => {
    return data.map(item => ({
      ...item,
      value: calculateValue(item)
    }))
  }, [data])

  // 回調函數使用 useCallback
  const handleRefresh = useCallback(() => {
    onRefresh()
  }, [onRefresh])

  return (
    <Card>
      {/* ... */}
    </Card>
  )
})
```

### 虛擬化

```jsx
import { FixedSizeList } from 'react-window'

function LargeList({ items }) {
  const Row = ({ index, style }) => (
    <div style={style}>
      {items[index].name}
    </div>
  )

  return (
    <FixedSizeList
      height={600}
      itemCount={items.length}
      itemSize={50}
      width="100%"
    >
      {Row}
    </FixedSizeList>
  )
}
```

## 測試

### 單元測試

```jsx
import { render, screen, fireEvent } from '@testing-library/react'
import { Button } from './Button'

describe('Button', () => {
  it('renders children correctly', () => {
    render(<Button>Click me</Button>)
    expect(screen.getByText('Click me')).toBeInTheDocument()
  })

  it('calls onClick when clicked', () => {
    const handleClick = jest.fn()
    render(<Button onClick={handleClick}>Click me</Button>)
    fireEvent.click(screen.getByText('Click me'))
    expect(handleClick).toHaveBeenCalledTimes(1)
  })

  it('is disabled when disabled prop is true', () => {
    render(<Button disabled>Click me</Button>)
    expect(screen.getByText('Click me')).toBeDisabled()
  })
})
```

### 無障礙測試

```jsx
import { render } from '@testing-library/react'
import { axe, toHaveNoViolations } from 'jest-axe'

expect.extend(toHaveNoViolations)

describe('Button accessibility', () => {
  it('should not have accessibility violations', async () => {
    const { container } = render(<Button>Click me</Button>)
    const results = await axe(container)
    expect(results).toHaveNoViolations()
  })
})
```

## 版本歷史

| 版本 | 日期 | 變更內容 | 作者 |
|------|------|----------|------|
| 1.0.0 | 2025-10-20 | 初版建立 | UI/UX 設計團隊 |
