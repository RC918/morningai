# MorningAI 設計系統增強路線圖

## 文檔資訊
- **版本**: 1.0.0
- **建立日期**: 2025-10-23
- **負責人**: UI/UX 策略長
- **狀態**: 執行中
- **相關文檔**: COMPREHENSIVE_UI_UX_AUDIT_REPORT.md, TOP_TIER_SAAS_UI_UX_PLAN.md

---

## 執行摘要

本路線圖基於全面 UI/UX 審查報告，提供 8 週的設計系統增強計畫。目標是將 MorningAI 從當前的 83/100 分提升至 **90+/100 分**，成為頂尖的 SaaS UI/UX 典範。

**核心目標**:
1. 完善設計系統基礎設施（Token 作用域化、Storybook）
2. 提升使用者體驗流暢度（保存狀態、撤銷/重做、全局搜尋）
3. 強化無障礙性（Live Regions、跳過導航、ARIA 完整性）
4. 建立數據驅動的驗證機制（可用性測試、A/B 測試）

---

## 一、8 週執行計畫

### Week 1-2: 基礎設施強化 🏗️

#### Week 1: Token 作用域化與狀態反饋

**目標**: 解決 Token 全域污染問題，增強 Dashboard 保存狀態反饋

##### 任務 1.1: Token 作用域化 (#471) - P0
**預計工時**: 2 天  
**負責人**: 前端工程師 + UI 設計師

**問題描述**:
- 當前 Token 直接應用到 `:root`，可能污染其他組件
- 缺少主題容器策略，難以支援多主題

**解決方案**:
```javascript
// 1. 修改 design-tokens.js
export const applyDesignTokens = (scope = '.theme-morning-ai') => {
  const container = document.querySelector(scope) || document.documentElement
  const cssVars = getCSSVariables()
  
  Object.entries(cssVars).forEach(([property, value]) => {
    container.style.setProperty(property, value)
  })
}

// 2. 在 App.jsx 中應用
<div className="theme-morning-ai min-h-screen">
  {/* 所有內容 */}
</div>

// 3. 更新 Tailwind 配置
// tailwind.config.js
module.exports = {
  theme: {
    extend: {
      colors: {
        primary: 'var(--color-primary-500)',
        'primary-foreground': 'var(--color-primary-50)',
        // ... 其他顏色
      }
    }
  }
}
```

**驗收標準**:
- [ ] Token 僅在 `.theme-morning-ai` 容器內生效
- [ ] 現有頁面視覺無破壞（視覺回歸測試）
- [ ] Tailwind 整合完成，可使用 `bg-primary` 等類名
- [ ] 文檔更新（Design System/Tokens.md）

**風險與對策**:
- 風險：波及面大，可能破壞現有樣式
- 對策：分頁漸進遷移，建立視覺回歸基線

---

##### 任務 1.2: Dashboard 保存狀態反饋 (#474) - P0
**預計工時**: 1 天  
**負責人**: 前端工程師

**問題描述**:
- 用戶不確定 Dashboard 自訂是否已保存
- 缺少保存失敗的錯誤提示

**解決方案**:
```jsx
// 1. 增加保存狀態管理
const [saveStatus, setSaveStatus] = useState({
  status: 'saved', // 'saved' | 'saving' | 'unsaved' | 'error'
  lastSaved: new Date(),
  error: null
})

// 2. 保存狀態指示器
const SaveStatusIndicator = ({ status, lastSaved, error, onRetry }) => {
  const statusConfig = {
    saved: {
      icon: Check,
      text: `已保存 · ${formatRelativeTime(lastSaved)}`,
      className: 'text-success-600'
    },
    saving: {
      icon: Loader2,
      text: '保存中...',
      className: 'text-gray-600 animate-spin'
    },
    unsaved: {
      icon: AlertCircle,
      text: '有未保存的變更',
      className: 'text-warning-600'
    },
    error: {
      icon: XCircle,
      text: '保存失敗',
      className: 'text-error-600',
      action: { label: '重試', onClick: onRetry }
    }
  }
  
  const config = statusConfig[status]
  const Icon = config.icon
  
  return (
    <div className="flex items-center gap-2">
      <Icon className={`w-4 h-4 ${config.className}`} />
      <span className={`text-sm ${config.className}`}>
        {config.text}
      </span>
      {config.action && (
        <Button
          variant="ghost"
          size="sm"
          onClick={config.action.onClick}
        >
          {config.action.label}
        </Button>
      )}
    </div>
  )
}

// 3. 在 Dashboard 編輯工具列中使用
<div className="edit-toolbar">
  <SaveStatusIndicator
    status={saveStatus.status}
    lastSaved={saveStatus.lastSaved}
    error={saveStatus.error}
    onRetry={handleSave}
  />
  <Button onClick={handleSave}>保存</Button>
  <Button onClick={handleUndo}>撤銷</Button>
  <Button onClick={handleRedo}>重做</Button>
</div>
```

**驗收標準**:
- [ ] 保存狀態即時反饋（已保存/保存中/未保存/錯誤）
- [ ] 顯示最近保存時間（相對時間，如「2 分鐘前」）
- [ ] 保存失敗時顯示錯誤訊息與重試按鈕
- [ ] 離開頁面前提示未保存變更

---

##### 任務 1.3: 跳過導航連結 - P0
**預計工時**: 0.5 天  
**負責人**: 前端工程師

**問題描述**:
- 鍵盤用戶無法快速跳至主要內容
- 不符合 WCAG 2.1 AA 標準

**解決方案**:
```jsx
// 1. 在 App.jsx 頂部添加跳過導航連結
<a
  href="#main-content"
  className="sr-only focus:not-sr-only focus:absolute focus:top-4 focus:left-4 focus:z-50 focus:px-4 focus:py-2 focus:bg-primary-500 focus:text-white focus:rounded-md focus:shadow-lg"
>
  跳至主要內容
</a>

// 2. 在主要內容區域添加 ID
<main id="main-content" role="main" aria-label="主要內容區域">
  {/* 頁面內容 */}
</main>

// 3. 添加 CSS
/* index.css */
.sr-only {
  position: absolute;
  width: 1px;
  height: 1px;
  padding: 0;
  margin: -1px;
  overflow: hidden;
  clip: rect(0, 0, 0, 0);
  white-space: nowrap;
  border-width: 0;
}

.sr-only:focus {
  position: static;
  width: auto;
  height: auto;
  padding: 0.5rem 1rem;
  margin: 0;
  overflow: visible;
  clip: auto;
  white-space: normal;
}
```

**驗收標準**:
- [ ] Tab 鍵第一個焦點為「跳至主要內容」連結
- [ ] 點擊連結後焦點移至主要內容區域
- [ ] 連結僅在焦點時可見
- [ ] 符合 WCAG 2.1 AA 標準

---

##### 任務 1.4: Live Regions - P1
**預計工時**: 2 天  
**負責人**: 前端工程師

**問題描述**:
- 動態內容更新未通知螢幕閱讀器
- 保存狀態、錯誤訊息、通知等無法被輔助技術感知

**解決方案**:
```jsx
// 1. 建立 LiveRegion 組件
const LiveRegion = ({ 
  message, 
  type = 'polite', // 'polite' | 'assertive'
  atomic = true 
}) => {
  return (
    <div
      role={type === 'assertive' ? 'alert' : 'status'}
      aria-live={type}
      aria-atomic={atomic}
      className="sr-only"
    >
      {message}
    </div>
  )
}

// 2. 在關鍵位置使用
// Dashboard 保存狀態
<LiveRegion
  message={saveStatus.status === 'saved' ? '已保存' : saveStatus.status === 'error' ? '保存失敗' : ''}
  type="polite"
/>

// 錯誤訊息
<LiveRegion
  message={errorMessage}
  type="assertive"
/>

// Toast 通知
const { toast } = useToast()
const showToast = (message, type) => {
  toast({
    title: message,
    variant: type
  })
  
  // 同時更新 Live Region
  setLiveMessage(message)
}

// 3. 表單驗證錯誤
<div>
  <Label htmlFor="email">電子郵件</Label>
  <Input
    id="email"
    type="email"
    aria-invalid={hasError}
    aria-describedby={hasError ? 'email-error' : undefined}
  />
  {hasError && (
    <p id="email-error" role="alert" className="text-error-500">
      請輸入有效的電子郵件地址
    </p>
  )}
</div>
```

**驗收標準**:
- [ ] 保存狀態變更時通知螢幕閱讀器
- [ ] 錯誤訊息使用 `role="alert"` 與 `aria-live="assertive"`
- [ ] Toast 通知同步更新 Live Region
- [ ] 表單驗證錯誤使用 `aria-invalid` 與 `aria-describedby`

---

#### Week 2: 撤銷/重做與全局搜尋

##### 任務 2.1: 撤銷/重做功能 (#474) - P1
**預計工時**: 5 天 (+67% 緩衝)  
**負責人**: 前端工程師

**時程調整理由**:
- 需要設計複雜的狀態管理（history stack）
- 需要處理多種操作類型（widget 添加/移除/排列）
- 需要測試邊界情況（undo/redo 限制、狀態同步）
- 需要 UI 設計（undo/redo 按鈕、快捷鍵提示）

**問題描述**:
- Dashboard 編輯誤操作無法恢復
- 用戶體驗不佳，容易誤刪小工具

**解決方案**:
```jsx
// 1. 實現 Undo/Redo 堆疊
const useUndoRedo = (initialState) => {
  const [history, setHistory] = useState([initialState])
  const [currentIndex, setCurrentIndex] = useState(0)
  
  const currentState = history[currentIndex]
  
  const canUndo = currentIndex > 0
  const canRedo = currentIndex < history.length - 1
  
  const setState = (newState) => {
    const newHistory = history.slice(0, currentIndex + 1)
    newHistory.push(newState)
    setHistory(newHistory)
    setCurrentIndex(newHistory.length - 1)
  }
  
  const undo = () => {
    if (canUndo) {
      setCurrentIndex(currentIndex - 1)
    }
  }
  
  const redo = () => {
    if (canRedo) {
      setCurrentIndex(currentIndex + 1)
    }
  }
  
  const reset = () => {
    setHistory([initialState])
    setCurrentIndex(0)
  }
  
  return {
    state: currentState,
    setState,
    undo,
    redo,
    canUndo,
    canRedo,
    reset
  }
}

// 2. 在 Dashboard 中使用
const Dashboard = () => {
  const {
    state: widgets,
    setState: setWidgets,
    undo,
    redo,
    canUndo,
    canRedo
  } = useUndoRedo(defaultWidgets)
  
  const handleAddWidget = (widget) => {
    setWidgets([...widgets, widget])
  }
  
  const handleRemoveWidget = (id) => {
    setWidgets(widgets.filter(w => w.id !== id))
  }
  
  const handleMoveWidget = (dragIndex, hoverIndex) => {
    const newWidgets = [...widgets]
    const [removed] = newWidgets.splice(dragIndex, 1)
    newWidgets.splice(hoverIndex, 0, removed)
    setWidgets(newWidgets)
  }
  
  return (
    <div>
      <div className="edit-toolbar">
        <Button
          onClick={undo}
          disabled={!canUndo}
          aria-label="撤銷"
        >
          <Undo2 className="w-4 h-4" />
          撤銷
        </Button>
        <Button
          onClick={redo}
          disabled={!canRedo}
          aria-label="重做"
        >
          <Redo2 className="w-4 h-4" />
          重做
        </Button>
      </div>
      {/* Dashboard 內容 */}
    </div>
  )
}

// 3. 鍵盤快捷鍵
useEffect(() => {
  const handleKeyDown = (e) => {
    if ((e.metaKey || e.ctrlKey) && e.key === 'z') {
      e.preventDefault()
      if (e.shiftKey) {
        redo()
      } else {
        undo()
      }
    }
  }
  
  window.addEventListener('keydown', handleKeyDown)
  return () => window.removeEventListener('keydown', handleKeyDown)
}, [undo, redo])
```

**驗收標準**:
- [ ] 支援撤銷/重做操作（添加、移除、移動小工具）
- [ ] 鍵盤快捷鍵（Cmd/Ctrl+Z 撤銷，Cmd/Ctrl+Shift+Z 重做）
- [ ] 按鈕狀態正確（無法撤銷/重做時禁用）
- [ ] 歷史記錄限制（最多 50 步）

---

##### 任務 2.2: 全局搜尋 (Cmd+K) - P1
**預計工時**: 7 天 (+40% 緩衝)  
**負責人**: 前端工程師

**時程調整理由**:
- 需要整合多個數據源（頁面、widget、設定、文檔）
- 需要實現搜尋演算法（模糊搜尋、權重排序）
- 需要設計複雜的 UI（搜尋結果分組、預覽）
- 需要優化性能（大量數據的搜尋速度）
- 需要支援多語言（中文/英文搜尋）

**問題描述**:
- 缺少全局搜尋功能
- 用戶難以快速找到小工具、頁面、設定

**解決方案**:
```jsx
// 1. 建立 CommandPalette 組件
import { Command } from 'cmdk'

const CommandPalette = ({ open, onOpenChange }) => {
  const [search, setSearch] = useState('')
  const navigate = useNavigate()
  
  const pages = [
    { id: 'dashboard', name: '監控儀表板', path: '/dashboard', icon: LayoutDashboard },
    { id: 'strategies', name: '策略管理', path: '/strategies', icon: Brain },
    { id: 'approvals', name: '決策審批', path: '/approvals', icon: CheckCircle },
    { id: 'history', name: '歷史分析', path: '/history', icon: History },
    { id: 'costs', name: '成本分析', path: '/costs', icon: DollarSign },
    { id: 'settings', name: '系統設定', path: '/settings', icon: Settings }
  ]
  
  const widgets = [
    { id: 'system-health', name: '系統健康度', category: '小工具' },
    { id: 'cost-overview', name: '成本總覽', category: '小工具' },
    { id: 'recent-decisions', name: '最近決策', category: '小工具' }
  ]
  
  const settings = [
    { id: 'profile', name: '個人資料', path: '/settings/profile', category: '設定' },
    { id: 'notifications', name: '通知設定', path: '/settings/notifications', category: '設定' },
    { id: 'api-keys', name: 'API 金鑰', path: '/settings/api-keys', category: '設定' }
  ]
  
  const allItems = [...pages, ...widgets, ...settings]
  
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="p-0">
        <Command>
          <CommandInput
            placeholder="搜尋頁面、小工具、設定..."
            value={search}
            onValueChange={setSearch}
          />
          <CommandList>
            <CommandEmpty>找不到結果</CommandEmpty>
            
            <CommandGroup heading="頁面">
              {pages.map((page) => (
                <CommandItem
                  key={page.id}
                  onSelect={() => {
                    navigate(page.path)
                    onOpenChange(false)
                  }}
                >
                  <page.icon className="w-4 h-4 mr-2" />
                  {page.name}
                </CommandItem>
              ))}
            </CommandGroup>
            
            <CommandGroup heading="小工具">
              {widgets.map((widget) => (
                <CommandItem
                  key={widget.id}
                  onSelect={() => {
                    // 添加小工具到 Dashboard
                    addWidget(widget.id)
                    onOpenChange(false)
                  }}
                >
                  <Plus className="w-4 h-4 mr-2" />
                  {widget.name}
                </CommandItem>
              ))}
            </CommandGroup>
            
            <CommandGroup heading="設定">
              {settings.map((setting) => (
                <CommandItem
                  key={setting.id}
                  onSelect={() => {
                    navigate(setting.path)
                    onOpenChange(false)
                  }}
                >
                  <Settings className="w-4 h-4 mr-2" />
                  {setting.name}
                </CommandItem>
              ))}
            </CommandGroup>
          </CommandList>
        </Command>
      </DialogContent>
    </Dialog>
  )
}

// 2. 在 App.jsx 中使用
const App = () => {
  const [commandOpen, setCommandOpen] = useState(false)
  
  useEffect(() => {
    const handleKeyDown = (e) => {
      if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
        e.preventDefault()
        setCommandOpen(true)
      }
    }
    
    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [])
  
  return (
    <>
      <CommandPalette open={commandOpen} onOpenChange={setCommandOpen} />
      {/* 其他內容 */}
    </>
  )
}
```

**驗收標準**:
- [ ] Cmd/Ctrl+K 開啟搜尋面板
- [ ] 支援搜尋頁面、小工具、設定
- [ ] 鍵盤導航（上下箭頭、Enter 選擇、Esc 關閉）
- [ ] 模糊搜尋（支援拼音、部分匹配）
- [ ] 搜尋歷史記錄

---

### Week 3-4: 組件文檔與測試 📚

#### Week 3: Storybook 建立

##### 任務 3.1: Storybook 初始化 (#473) - P2
**預計工時**: 2 天  
**負責人**: 前端工程師

**解決方案**:
```bash
# 1. 安裝 Storybook
cd frontend-dashboard-deploy
pnpm dlx storybook@latest init

# 2. 配置 Storybook
# .storybook/main.js
export default {
  stories: ['../src/**/*.stories.@(js|jsx|ts|tsx)'],
  addons: [
    '@storybook/addon-links',
    '@storybook/addon-essentials',
    '@storybook/addon-interactions',
    '@storybook/addon-a11y'
  ],
  framework: {
    name: '@storybook/react-vite',
    options: {}
  }
}

# 3. 配置主題
# .storybook/preview.js
import '../src/index.css'
import { applyDesignTokens } from '../src/lib/design-tokens'

applyDesignTokens()

export const parameters = {
  actions: { argTypesRegex: '^on[A-Z].*' },
  controls: {
    matchers: {
      color: /(background|color)$/i,
      date: /Date$/
    }
  }
}
```

**驗收標準**:
- [ ] Storybook 成功啟動（`pnpm run storybook`）
- [ ] 設計 Token 正確應用
- [ ] 無障礙插件啟用（@storybook/addon-a11y）

---

##### 任務 3.2: 核心組件 Stories - P2
**預計工時**: 3 天  
**負責人**: 前端工程師 + UI 設計師

**解決方案**:
```jsx
// 1. Button Stories
// src/components/ui/button.stories.jsx
import { Button } from './button'

export default {
  title: 'UI/Button',
  component: Button,
  tags: ['autodocs'],
  argTypes: {
    variant: {
      control: 'select',
      options: ['default', 'destructive', 'outline', 'secondary', 'ghost', 'link']
    },
    size: {
      control: 'select',
      options: ['default', 'sm', 'lg', 'icon']
    }
  }
}

export const Default = {
  args: {
    children: '按鈕',
    variant: 'default',
    size: 'default'
  }
}

export const AllVariants = () => (
  <div className="flex gap-4">
    <Button variant="default">Default</Button>
    <Button variant="destructive">Destructive</Button>
    <Button variant="outline">Outline</Button>
    <Button variant="secondary">Secondary</Button>
    <Button variant="ghost">Ghost</Button>
    <Button variant="link">Link</Button>
  </div>
)

export const AllSizes = () => (
  <div className="flex items-center gap-4">
    <Button size="sm">Small</Button>
    <Button size="default">Default</Button>
    <Button size="lg">Large</Button>
    <Button size="icon">
      <Plus className="w-4 h-4" />
    </Button>
  </div>
)

export const WithIcons = () => (
  <div className="flex gap-4">
    <Button>
      <Plus className="w-4 h-4" />
      新增
    </Button>
    <Button variant="outline">
      <Trash2 className="w-4 h-4" />
      刪除
    </Button>
  </div>
)

export const Disabled = {
  args: {
    children: '禁用按鈕',
    disabled: true
  }
}

// 2. Input Stories
// src/components/ui/input.stories.jsx
export default {
  title: 'UI/Input',
  component: Input
}

export const Default = {
  args: {
    placeholder: '請輸入...'
  }
}

export const WithLabel = () => (
  <div className="space-y-2">
    <Label htmlFor="email">電子郵件</Label>
    <Input id="email" type="email" placeholder="example@email.com" />
  </div>
)

export const WithError = () => (
  <div className="space-y-2">
    <Label htmlFor="password">密碼</Label>
    <Input
      id="password"
      type="password"
      aria-invalid="true"
      aria-describedby="password-error"
    />
    <p id="password-error" role="alert" className="text-sm text-error-500">
      密碼至少需要 8 個字元
    </p>
  </div>
)

// 3. Card Stories
// src/components/ui/card.stories.jsx
export const Default = () => (
  <Card>
    <CardHeader>
      <CardTitle>卡片標題</CardTitle>
      <CardDescription>卡片描述</CardDescription>
    </CardHeader>
    <CardContent>
      <p>卡片內容</p>
    </CardContent>
    <CardFooter>
      <Button>操作</Button>
    </CardFooter>
  </Card>
)
```

**驗收標準**:
- [ ] 至少 20 個核心組件有 Stories
- [ ] 每個組件至少 3 個變體範例
- [ ] 包含互動狀態（hover, focus, disabled）
- [ ] 無障礙檢查通過（a11y addon）

---

#### Week 4: 可用性測試準備

##### 任務 4.1: 可用性測試腳本 (#478) - P1
**預計工時**: 2 天  
**負責人**: UI/UX 設計師

**測試者招募計畫**:

**招募目標**: 5 位跨角色用戶

**角色分佈**:
1. **運營人員** (1 位): 每日使用 Dashboard 監控系統
2. **客服人員** (1 位): 處理用戶問題，查看成本數據
3. **業務人員** (1 位): 查看成本分析，設定預算
4. **管理員** (1 位): 審批決策，管理策略
5. **新手用戶** (1 位): 首次使用系統，評估引導流程

**招募渠道**:
- 現有用戶邀請（Email + 站內通知）
- 社群媒體招募（LinkedIn, Facebook 社團）
- 用戶訪談名單（過去參與過訪談的用戶）
- 內部員工（非開發團隊）

**招募標準**:
- 使用過類似 SaaS 系統（Dashboard, 監控工具）
- 願意提供 60 分鐘時間
- 願意螢幕錄製
- 能清楚表達想法

**招募獎勵**:
- 現金獎勵: NT$ 1,000 / 人
- 或 MorningAI 免費使用 3 個月
- 測試報告副本（如需要）

**招募時程**:
- **Week 2**: 發布招募訊息
- **Week 3**: 篩選與確認測試者
- **Week 4**: 執行測試

**測試腳本範例**:
```markdown
# MorningAI 可用性測試腳本

## 測試資訊
- **測試時間**: 60 分鐘
- **測試者**: 5 位跨角色用戶（運營、客服、業務、管理員、新手）
- **測試環境**: 生產環境（Staging）
- **測試工具**: Zoom + 螢幕錄製

## 測試任務

### 任務 1: 首次登入與引導 (10 分鐘)
**目標**: 評估首次體驗流暢度

1. 請使用提供的帳號登入系統
2. 完成引導流程（如有）
3. 進入 Dashboard

**觀察指標**:
- 首次價值時間 (TTV)
- 是否遇到困惑
- 是否需要幫助

### 任務 2: Dashboard 自訂 (15 分鐘)
**目標**: 評估 Dashboard 自訂體驗

1. 進入編輯模式
2. 添加一個小工具（成本總覽）
3. 移除一個小工具
4. 重新排列小工具
5. 保存變更

**觀察指標**:
- 是否能找到編輯按鈕
- 是否理解拖拽操作
- 是否確認保存成功

### 任務 3: 決策審批 (10 分鐘)
**目標**: 評估審批流程效率

1. 進入決策審批頁面
2. 查看待審批任務
3. 批准一個低風險任務
4. 拒絕一個高風險任務

**觀察指標**:
- 是否理解風險等級
- 是否能快速做出決策
- 是否需要更多資訊

### 任務 4: 成本分析 (10 分鐘)
**目標**: 評估成本管理體驗

1. 進入成本分析頁面
2. 查看今日成本
3. 查看本月成本趨勢
4. 設定預算預警（如有）

**觀察指標**:
- 是否理解成本數據
- 是否能找到關鍵資訊
- 是否需要更多細節

### 任務 5: 全局搜尋 (5 分鐘)
**目標**: 評估搜尋功能可用性

1. 使用 Cmd/Ctrl+K 開啟搜尋
2. 搜尋「成本」
3. 選擇一個結果

**觀察指標**:
- 是否知道快捷鍵
- 搜尋結果是否相關
- 是否能快速找到目標

## 後測問卷

### SUS (系統可用性量表)
1-5 分（1=非常不同意，5=非常同意）

1. 我認為我會經常使用這個系統
2. 我認為這個系統過於複雜
3. 我認為這個系統易於使用
4. 我認為需要技術支援才能使用這個系統
5. 我認為這個系統的各項功能整合良好
6. 我認為這個系統有太多不一致之處
7. 我認為大多數人能快速學會使用這個系統
8. 我認為這個系統使用起來很麻煩
9. 我對使用這個系統感到自信
10. 我需要學習很多東西才能使用這個系統

### NPS (淨推薦值)
0-10 分

您有多大可能向朋友或同事推薦 MorningAI？

### 開放式問題
1. 您最喜歡 MorningAI 的哪個功能？
2. 您認為哪個功能最需要改進？
3. 您在使用過程中遇到的最大困難是什麼？
4. 您希望增加哪些功能？
```

**驗收標準**:
- [ ] 測試腳本完整（5 個任務）
- [ ] SUS 與 NPS 問卷準備
- [ ] 測試環境準備（Staging）
- [ ] 招募 5 位測試者

---

##### 任務 4.2: 執行可用性測試 - P1
**預計工時**: 3 天  
**負責人**: UI/UX 設計師 + 產品經理

**執行流程**:
1. **Day 1**: 測試 2 位用戶
2. **Day 2**: 測試 2 位用戶
3. **Day 3**: 測試 1 位用戶 + 初步分析

**驗收標準**:
- [ ] 完成 5 位用戶測試
- [ ] 錄製所有測試過程
- [ ] 收集 SUS 與 NPS 數據
- [ ] 記錄所有問題與建議

**數據分析方法**:

**定量數據分析**:

1. **TTV (首次價值時間)**
   - 計算平均值、中位數、P90
   - 與目標值 (< 10 分鐘) 比較
   - 識別異常值（> 20 分鐘）

2. **任務成功率**
   - 計算各任務成功率
   - 識別失敗原因
   - 優先級排序（成功率 < 90% 為高優先級）

3. **SUS 分數**
   - 計算平均 SUS 分數（0-100）
   - 與目標值 (> 80) 比較
   - 與業界基準 (68) 比較

4. **NPS 分數**
   - 計算 NPS = (Promoters% - Detractors%)
   - 分類：Promoters (9-10), Passives (7-8), Detractors (0-6)
   - 分析 Detractors 的反饋

**定性數據分析**:

1. **問題分類**
   - 按嚴重程度：Critical (阻塞任務), High (困難), Medium (不便), Low (建議)
   - 按功能模組：Dashboard, 決策審批, 搜尋, 引導

2. **主題分析 (Thematic Analysis)**
   - 轉錄所有錄音/錄影
   - 標記關鍵語句
   - 歸納主題
   - 計算頻率

3. **改進建議優先級**
   - 優先級矩陣：影響範圍 × 嚴重程度 × 實施難度
   - P0 (高影響 + 高嚴重 + 低難度)
   - P1 (高影響 + 中嚴重 + 中難度)
   - P2 (中影響 + 低嚴重 + 高難度)

**測試報告結構**:
1. 執行摘要（關鍵發現、優先改進項目）
2. 測試者背景（角色、經驗、年齡、性別）
3. 定量結果（TTV, 任務成功率, SUS, NPS）
4. 定性結果（主要問題、用戶引述）
5. 改進建議（P0/P1/P2 分類）
6. 附錄（測試錄影、原始數據）

---

### Week 5-6: 進階功能與優化 🚀

#### Week 5: 暗色主題與微互動

##### 任務 5.1: 暗色主題實現 - P2
**預計工時**: 10 天 (+100% 緩衝)  
**負責人**: 前端工程師 + UI 設計師

**時程調整理由**:
- 需要設計完整的暗色 Token 系統（50+ 顏色變數）
- 需要確保所有組件的對比度符合 WCAG AA（手動檢查 77 個組件）
- 需要處理圖片/圖標的暗色適配
- 需要測試所有頁面的視覺效果
- 需要實現主題切換動畫
- 需要處理第三方組件的暗色適配（Recharts, Radix UI）

**解決方案**:
```javascript
// 1. 擴展 tokens.json
{
  "color": {
    "light": {
      "primary": { "50": "#eff6ff", "500": "#3b82f6", "900": "#1e3a8a" },
      "background": { "primary": "#ffffff", "secondary": "#f9fafb" }
    },
    "dark": {
      "primary": { "50": "#1e3a8a", "500": "#60a5fa", "900": "#eff6ff" },
      "background": { "primary": "#0f172a", "secondary": "#1e293b" }
    }
  }
}

// 2. 主題切換邏輯
const useTheme = () => {
  const [theme, setTheme] = useState(() => {
    return localStorage.getItem('theme') || 'light'
  })
  
  useEffect(() => {
    const root = document.documentElement
    root.classList.remove('light', 'dark')
    root.classList.add(theme)
    localStorage.setItem('theme', theme)
    
    // 應用對應的 Token
    applyDesignTokens(theme)
  }, [theme])
  
  const toggleTheme = () => {
    setTheme(prev => prev === 'light' ? 'dark' : 'light')
  }
  
  return { theme, toggleTheme }
}

// 3. 主題切換器
const ThemeSwitcher = () => {
  const { theme, toggleTheme } = useTheme()
  
  return (
    <Button
      variant="ghost"
      size="icon"
      onClick={toggleTheme}
      aria-label={`切換至${theme === 'light' ? '暗色' : '淺色'}模式`}
    >
      {theme === 'light' ? (
        <Moon className="w-4 h-4" />
      ) : (
        <Sun className="w-4 h-4" />
      )}
    </Button>
  )
}
```

**驗收標準**:
- [ ] 淺色/暗色主題完整實現
- [ ] 主題切換流暢（無閃爍）
- [ ] 主題偏好持久化（localStorage）
- [ ] 所有組件支援暗色模式
- [ ] 色彩對比度符合 WCAG AA

---

##### 任務 5.2: 微互動與動畫增強 - P2
**預計工時**: 3 天  
**負責人**: 前端工程師

**解決方案**:
```jsx
// 1. 按鈕點擊反饋
const Button = ({ children, onClick, ...props }) => {
  const [isPressed, setIsPressed] = useState(false)
  
  const handleClick = (e) => {
    setIsPressed(true)
    setTimeout(() => setIsPressed(false), 150)
    onClick?.(e)
  }
  
  return (
    <motion.button
      whileTap={{ scale: 0.95 }}
      onClick={handleClick}
      {...props}
    >
      {children}
    </motion.button>
  )
}

// 2. 卡片懸停效果
const Card = ({ children, ...props }) => {
  return (
    <motion.div
      whileHover={{ y: -4, boxShadow: '0 10px 30px rgba(0,0,0,0.1)' }}
      transition={{ duration: 0.2 }}
      {...props}
    >
      {children}
    </motion.div>
  )
}

// 3. 列表項進場動畫
const ListItem = ({ children, index }) => {
  return (
    <motion.div
      initial={{ opacity: 0, x: -20 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ delay: index * 0.05 }}
    >
      {children}
    </motion.div>
  )
}

// 4. 數字滾動動畫
const AnimatedNumber = ({ value }) => {
  const [displayValue, setDisplayValue] = useState(0)
  
  useEffect(() => {
    const duration = 1000
    const steps = 60
    const increment = (value - displayValue) / steps
    
    let current = displayValue
    const timer = setInterval(() => {
      current += increment
      if (
        (increment > 0 && current >= value) ||
        (increment < 0 && current <= value)
      ) {
        setDisplayValue(value)
        clearInterval(timer)
      } else {
        setDisplayValue(current)
      }
    }, duration / steps)
    
    return () => clearInterval(timer)
  }, [value])
  
  return <span>{Math.round(displayValue)}</span>
}
```

**驗收標準**:
- [ ] 按鈕點擊有視覺反饋
- [ ] 卡片懸停有提升效果
- [ ] 列表項有進場動畫
- [ ] 數字變化有滾動動畫
- [ ] 所有動畫支援 reduced-motion

---

#### Week 6: 性能優化與視覺回歸

##### 任務 6.1: 圖片與字體優化 - P1
**預計工時**: 2 天  
**負責人**: 前端工程師

**解決方案**:
```jsx
// 1. 圖片懶加載
const LazyImage = ({ src, alt, ...props }) => {
  const [isLoaded, setIsLoaded] = useState(false)
  const imgRef = useRef(null)
  
  useEffect(() => {
    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          setIsLoaded(true)
          observer.disconnect()
        }
      },
      { rootMargin: '50px' }
    )
    
    if (imgRef.current) {
      observer.observe(imgRef.current)
    }
    
    return () => observer.disconnect()
  }, [])
  
  return (
    <div ref={imgRef} className="relative">
      {!isLoaded && (
        <div className="absolute inset-0 bg-gray-200 animate-pulse" />
      )}
      {isLoaded && (
        <img
          src={src}
          alt={alt}
          loading="lazy"
          {...props}
        />
      )}
    </div>
  )
}

// 2. 字體優化
// index.html
<link
  rel="preload"
  href="/fonts/Inter-Variable.woff2"
  as="font"
  type="font/woff2"
  crossorigin
/>

// index.css
@font-face {
  font-family: 'Inter';
  src: url('/fonts/Inter-Variable.woff2') format('woff2');
  font-weight: 100 900;
  font-display: swap;
  font-style: normal;
}

// 3. WebP 圖片支援
const getImageUrl = (filename) => {
  const supportsWebP = document.createElement('canvas')
    .toDataURL('image/webp')
    .indexOf('data:image/webp') === 0
  
  return supportsWebP
    ? `/images/${filename}.webp`
    : `/images/${filename}.png`
}
```

**驗收標準**:
- [ ] 所有圖片使用懶加載
- [ ] 字體使用 `font-display: swap`
- [ ] 支援 WebP 格式（fallback 到 PNG）
- [ ] Lighthouse 性能分數 > 90

---

##### 任務 6.2: 視覺回歸測試 - P1
**預計工時**: 3 天  
**負責人**: 前端工程師

**解決方案**:
```bash
# 1. 安裝 Playwright
pnpm add -D @playwright/test

# 2. 配置 Playwright
# playwright.config.js
export default {
  testDir: './tests',
  use: {
    baseURL: 'http://localhost:5173',
    screenshot: 'only-on-failure',
    video: 'retain-on-failure'
  },
  projects: [
    { name: 'chromium', use: { ...devices['Desktop Chrome'] } },
    { name: 'firefox', use: { ...devices['Desktop Firefox'] } },
    { name: 'webkit', use: { ...devices['Desktop Safari'] } },
    { name: 'mobile', use: { ...devices['iPhone 12'] } }
  ]
}

# 3. 撰寫視覺回歸測試
# tests/visual-regression.spec.js
import { test, expect } from '@playwright/test'

test.describe('Visual Regression', () => {
  test('Dashboard', async ({ page }) => {
    await page.goto('/dashboard')
    await page.waitForLoadState('networkidle')
    await expect(page).toHaveScreenshot('dashboard.png')
  })
  
  test('Login Page', async ({ page }) => {
    await page.goto('/login')
    await expect(page).toHaveScreenshot('login.png')
  })
  
  test('Settings Page', async ({ page }) => {
    await page.goto('/settings')
    await page.waitForLoadState('networkidle')
    await expect(page).toHaveScreenshot('settings.png')
  })
})

# 4. 執行測試
pnpm playwright test
```

**驗收標準**:
- [ ] 至少 10 個關鍵頁面有視覺回歸測試
- [ ] 支援多瀏覽器（Chrome, Firefox, Safari）
- [ ] 支援移動端測試
- [ ] CI 整合（GitHub Actions）

---

### Week 7-8: 驗證與文檔 📊

#### Week 7: 指標回歸與 A/B 測試

##### 任務 7.1: 指標回歸分析 (#479) - P1
**預計工時**: 3 天  
**負責人**: 產品經理 + 數據分析師

**分析指標**:
```markdown
## 效率指標
- 首次價值時間 (TTV): 目標 < 10 分鐘
- 任務完成率: 目標 > 90%
- 關鍵路徑成功率: 目標 > 95%

## 質量指標
- 錯誤率: 目標月降 > 20%
- 崩潰率: 目標連續下降
- NPS: 目標 > 35

## 可用性指標
- SUS: 目標 > 80
- WCAG 合規: 目標 AA 完整
- 性能: LCP < 2.5s, CLS < 0.1, INP < 200ms

## 數據來源
- Google Analytics: 用戶行為數據
- Sentry: 錯誤與崩潰數據
- Lighthouse: 性能數據
- 可用性測試: SUS 與 NPS 數據
```

**驗收標準**:
- [ ] 完成指標回歸分析報告
- [ ] 對比改進前後數據
- [ ] 識別改進空間
- [ ] 提出下一步行動計畫

---

##### 任務 7.2: A/B 測試 (#480) - P2
**預計工時**: 3 天  
**負責人**: 產品經理 + 前端工程師

**測試項目**:
```markdown
## 測試 1: Dashboard 引導文案
- A 版本: "開始自訂您的儀表板"
- B 版本: "添加小工具以追蹤關鍵指標"
- 指標: 點擊率、完成率

## 測試 2: 審批按鈕顏色
- A 版本: 綠色（success）
- B 版本: 藍色（primary）
- 指標: 點擊率、誤操作率

## 測試 3: 成本預警閾值預設值
- A 版本: 80%
- B 版本: 90%
- 指標: 設定完成率、預警觸發率
```

**驗收標準**:
- [ ] 至少 3 個 A/B 測試
- [ ] 每個測試至少 100 位用戶
- [ ] 統計顯著性 p < 0.05
- [ ] 產出 A/B 測試報告

---

#### Week 8: 文檔完善與知識沉澱

##### 任務 8.1: 設計系統文檔更新 (#481) - P1
**預計工時**: 2 天  
**負責人**: UI/UX 設計師

**文檔清單**:
```markdown
## 更新文檔
- [ ] Design System/README.md
- [ ] Design System/Tokens.md（Token 作用域化）
- [ ] Design System/Components.md（新增組件）
- [ ] Design System/Animation.md（微互動）
- [ ] Design System/Accessibility.md（Live Regions、跳過導航）
- [ ] Design System/Copywriting.md（A/B 測試結果）

## 新增文檔
- [ ] Design System/Themes.md（暗色主題）
- [ ] Design System/Testing.md（視覺回歸測試）
- [ ] Design System/Performance.md（性能優化）
```

**驗收標準**:
- [ ] 所有文檔更新完成
- [ ] 包含程式碼範例
- [ ] 包含最佳實踐
- [ ] 包含常見問題 (FAQ)

---

##### 任務 8.2: 工程交付文檔 - P1
**預計工時**: 2 天  
**負責人**: 前端工程師

**文檔清單**:
```markdown
## 開發指南
- [ ] 環境設定
- [ ] 開發工作流程
- [ ] 代碼規範
- [ ] Git 工作流程

## 組件開發
- [ ] 組件開發指南
- [ ] Storybook 使用
- [ ] 測試指南
- [ ] 無障礙檢查清單

## 部署與維護
- [ ] 構建與部署
- [ ] 性能監控
- [ ] 錯誤追蹤
- [ ] 版本發佈流程
```

**驗收標準**:
- [ ] 工程文檔完整
- [ ] 新成員可依文檔上手
- [ ] 包含故障排除指南
- [ ] 包含聯繫方式

---

##### 任務 8.3: 最終驗收與發佈 - P0
**預計工時**: 2 天  
**負責人**: 全體團隊

**驗收清單**:
```markdown
## 功能驗收
- [ ] Token 作用域化完成
- [ ] Dashboard 保存狀態反饋
- [ ] 撤銷/重做功能
- [ ] 全局搜尋 (Cmd+K)
- [ ] 跳過導航連結
- [ ] Live Regions
- [ ] Storybook 建立
- [ ] 暗色主題（選配）

## 測試驗收
- [ ] 可用性測試完成（5 位用戶）
- [ ] SUS > 80
- [ ] NPS > 35
- [ ] 視覺回歸測試通過
- [ ] 無障礙測試通過（WCAG AA）
- [ ] 性能測試通過（Lighthouse > 90）

## 文檔驗收
- [ ] 設計系統文檔更新
- [ ] 工程交付文檔完成
- [ ] Storybook 文檔完整
- [ ] 可用性測試報告
- [ ] A/B 測試報告
- [ ] 指標回歸分析報告

## 發佈準備
- [ ] 所有 PR 合併
- [ ] CI/CD 通過
- [ ] Staging 環境驗證
- [ ] 生產環境部署計畫
- [ ] 回滾計畫
```

**驗收標準**:
- [ ] 所有驗收項目完成
- [ ] 產品經理簽核
- [ ] CTO 簽核
- [ ] 準備發佈至生產環境

---

## 二、成功指標追蹤

### 2.1 基線指標（改進前）

**重要說明**: 為確保數據驅動的驗證機制，已建立實際測量系統。

| 指標 | 當前值 | 測量方法 | 數據來源 | 測量日期 | 樣本數 | 狀態 |
|-----|--------|---------|---------|---------|-------|------|
| 首次價值時間 (TTV) | 待測量 | 自動追蹤（CustomEvent） | Sentry + GA | Week 2 | 50+ | 🔄 實施中 |
| 關鍵路徑成功率 | 待測量 | 自動追蹤（Path Tracking） | Supabase | Week 2 | 100+ | 🔄 實施中 |
| 系統可用性 (SUS) | 待測量 | 問卷調查（10 題） | Supabase | Week 7 | 30+ | ⏳ 待實施 |
| NPS | 待測量 | 問卷調查（0-10 分） | Supabase | Week 7 | 30+ | ⏳ 待實施 |
| LCP | < 2.5s | Lighthouse CI | CI/CD | 2025-10-20 | 每次部署 | ✅ 已實施 |
| CLS | < 0.1 | Lighthouse CI | CI/CD | 2025-10-20 | 每次部署 | ✅ 已實施 |
| INP | < 200ms | Lighthouse CI | CI/CD | 2025-10-20 | 每次部署 | ✅ 已實施 |
| WCAG 合規 | AA (部分) | axe DevTools | 手動審查 | 2025-10-20 | 77 組件 | ✅ 已實施 |

**測量機制實施計畫**:

**Week 1**: 部署 TTV 與路徑追蹤代碼
- 在 App.jsx 添加 TTV 追蹤（CustomEvent + localStorage）
- 在 useAppStore.js 添加路徑追蹤（trackPathStart, trackPathComplete, trackPathFail）
- 建立 Supabase 數據表（ttv_metrics, path_tracking）

**Week 2**: 收集基線數據
- TTV: 收集 50+ 樣本，計算平均值、中位數、P90
- 路徑成功率: 收集 100+ 路徑樣本，計算各路徑成功率
- 建立基線報告

**Week 7**: 實施 SUS 與 NPS 問卷
- 創建 SUSQuestionnaire 與 NPSQuestionnaire 組件
- 設置觸發時機（使用 7 天後、完成關鍵任務後、每季度）
- 收集 30+ 問卷回覆

**預期基線**（基於初步數據）:
- TTV 平均: 12-18 分鐘（中位數: 10-15 分鐘，P90: 20-25 分鐘）
- 關鍵路徑成功率: 登入 95-98%, Dashboard 自訂 85-90%, 決策審批 90-95%, 成本查看 95-98%, 策略管理 80-85%
- SUS: 目標 > 80（業界基準 68）
- NPS: 目標 > 35

### 2.2 目標指標（改進後）

| 指標 | 目標值 | 預期達成日期 | 驗證方式 |
|-----|--------|------------|---------|
| 首次價值時間 (TTV) | < 10 分鐘 | Week 8 | 可用性測試 |
| 關鍵路徑成功率 | > 95% | Week 8 | 可用性測試 |
| 系統可用性 (SUS) | > 80 | Week 7 | SUS 問卷 |
| NPS | > 35 | Week 7 | NPS 問卷 |
| LCP | < 2.5s | Week 6 | Lighthouse |
| CLS | < 0.1 | Week 6 | Lighthouse |
| INP | < 200ms | Week 6 | Lighthouse |
| WCAG 合規 | AA (完整) | Week 2 | axe DevTools |

### 2.3 週度追蹤

**Week 1-2**:
- [ ] Token 作用域化完成
- [ ] 保存狀態反饋完成
- [ ] 跳過導航完成
- [ ] Live Regions 完成
- [ ] WCAG 合規達標

**Week 3-4**:
- [ ] 撤銷/重做完成
- [ ] 全局搜尋完成
- [ ] Storybook 建立
- [ ] 可用性測試完成
- [ ] SUS > 80, NPS > 35

**Week 5-6**:
- [ ] 暗色主題完成（選配）
- [ ] 微互動完成
- [ ] 性能優化完成
- [ ] 視覺回歸測試完成
- [ ] Lighthouse > 90

**Week 7-8**:
- [ ] 指標回歸分析完成
- [ ] A/B 測試完成
- [ ] 文檔更新完成
- [ ] 最終驗收通過
- [ ] 準備發佈

---

## 三、風險管理

### 3.1 技術風險

| 風險 | 影響 | 機率 | 對策 |
|-----|------|------|------|
| Token 作用域化破壞現有樣式 | 高 | 中 | 分頁漸進遷移，建立視覺回歸基線 |
| Storybook 配置困難 | 中 | 低 | 使用官方模板，參考最佳實踐 |
| 暗色主題色彩對比度不足 | 中 | 中 | 使用對比度檢查工具，遵循 WCAG AA |
| 性能優化影響功能 | 高 | 低 | 充分測試，保留回滾計畫 |

### 3.2 資源風險

| 風險 | 影響 | 機率 | 對策 |
|-----|------|------|------|
| 前端工程師資源不足 | 高 | 中 | 優先 P0/P1 任務，P2 任務可延後 |
| 可用性測試招募困難 | 中 | 中 | 提早兩週啟動招募，提供獎勵 |
| 設計師與工程師協作不順 | 中 | 低 | 建立每日站會，使用 Figma 協作 |

### 3.3 時程風險

| 風險 | 影響 | 機率 | 對策 |
|-----|------|------|------|
| 任務延期 | 高 | 中 | 每週檢視進度，及時調整計畫 |
| 測試發現重大問題 | 高 | 低 | 預留 buffer 時間，快速修復 |
| 文檔撰寫時間不足 | 中 | 中 | 邊做邊寫，避免最後集中撰寫 |

---

## 四、團隊協作

### 4.1 角色與職責

| 角色 | 職責 | 人員 |
|-----|------|------|
| UI/UX 策略長 | 整體規劃、設計審查、可用性測試 | Ryan Chen |
| UI 設計師 | 視覺設計、高保真模型、設計規範 | TBD |
| UX 設計師 | 用戶研究、流程設計、可用性測試 | TBD |
| 前端工程師 | 組件開發、Storybook、測試 | TBD |
| 產品經理 | 需求管理、優先級排序、驗收 | TBD |
| 數據分析師 | 指標追蹤、A/B 測試分析 | TBD |

### 4.2 會議節奏

**每日站會** (15 分鐘):
- 昨天完成了什麼
- 今天計畫做什麼
- 遇到什麼阻礙

**每週回顧** (60 分鐘):
- 回顧本週進度
- 檢視指標達成情況
- 調整下週計畫

**設計評審** (每週 1 次，60 分鐘):
- 設計師展示設計稿
- 工程師評估可行性
- 產品經理確認需求

**可用性測試** (Week 7，每天 2 位用戶):
- 執行測試腳本
- 記錄問題與建議
- 每日總結與調整

### 4.3 工具與平台

| 工具 | 用途 |
|-----|------|
| Figma | 設計協作、高保真模型 |
| Storybook | 組件展示、互動測試 |
| GitHub | 代碼管理、PR 審查 |
| Linear | 任務管理、進度追蹤 |
| Slack | 即時溝通 |
| Zoom | 可用性測試、遠端會議 |
| Google Analytics | 用戶行為數據 |
| Sentry | 錯誤追蹤 |
| Lighthouse | 性能測試 |

---

## 五、交付物清單

### 5.1 設計交付物

- [ ] 高保真模型（Figma）
  - [ ] Dashboard 自訂流程
  - [ ] 全局搜尋介面
  - [ ] 暗色主題設計
  - [ ] 微互動設計

- [ ] 設計規範文檔
  - [ ] Token 作用域化指南
  - [ ] 暗色主題指南
  - [ ] 微互動指南
  - [ ] 無障礙檢查清單

- [ ] 可用性測試報告
  - [ ] 測試腳本
  - [ ] 測試錄影
  - [ ] SUS 與 NPS 數據
  - [ ] 問題與建議清單

### 5.2 工程交付物

- [ ] 代碼實現
  - [ ] Token 作用域化
  - [ ] Dashboard 保存狀態反饋
  - [ ] 撤銷/重做功能
  - [ ] 全局搜尋 (Cmd+K)
  - [ ] 跳過導航連結
  - [ ] Live Regions
  - [ ] 暗色主題（選配）
  - [ ] 微互動

- [ ] Storybook
  - [ ] 至少 20 個組件 Stories
  - [ ] 互動測試
  - [ ] 無障礙檢查

- [ ] 測試
  - [ ] 視覺回歸測試
  - [ ] 單元測試
  - [ ] E2E 測試

- [ ] 文檔
  - [ ] 開發指南
  - [ ] 組件開發指南
  - [ ] 測試指南
  - [ ] 部署指南

### 5.3 數據交付物

- [ ] 指標回歸分析報告
  - [ ] 改進前後對比
  - [ ] 達成情況分析
  - [ ] 改進建議

- [ ] A/B 測試報告
  - [ ] 測試設計
  - [ ] 數據分析
  - [ ] 結論與建議

- [ ] 可用性測試報告
  - [ ] 測試過程記錄
  - [ ] SUS 與 NPS 數據
  - [ ] 問題與建議清單
  - [ ] 改進優先級

---

## 六、下一步行動

### 6.1 立即行動（本週）

1. **啟動 Week 1 任務**
   - [ ] 分配任務給團隊成員
   - [ ] 建立 GitHub Issues
   - [ ] 設定 Linear 看板

2. **準備開發環境**
   - [ ] 建立 feature branch
   - [ ] 配置 Storybook
   - [ ] 設定視覺回歸測試

3. **設計準備**
   - [ ] 建立 Figma 專案
   - [ ] 準備設計資源
   - [ ] 建立設計規範模板

### 6.2 短期行動（2 週內）

1. **完成基礎設施強化**
   - [ ] Token 作用域化
   - [ ] 保存狀態反饋
   - [ ] 跳過導航
   - [ ] Live Regions

2. **啟動可用性測試招募**
   - [ ] 撰寫招募文案
   - [ ] 發佈招募資訊
   - [ ] 篩選測試者

3. **建立指標追蹤儀表板**
   - [ ] 設定 Google Analytics
   - [ ] 設定 Sentry
   - [ ] 建立 Lighthouse CI

### 6.3 中期行動（4 週內）

1. **完成進階功能**
   - [ ] 撤銷/重做
   - [ ] 全局搜尋
   - [ ] Storybook

2. **執行可用性測試**
   - [ ] 測試 5 位用戶
   - [ ] 收集 SUS 與 NPS
   - [ ] 產出測試報告

3. **啟動 A/B 測試**
   - [ ] 設計測試方案
   - [ ] 實現 A/B 測試
   - [ ] 收集數據

### 6.4 長期行動（8 週內）

1. **完成所有功能**
   - [ ] 暗色主題（選配）
   - [ ] 微互動
   - [ ] 性能優化

2. **完成所有測試**
   - [ ] 視覺回歸測試
   - [ ] A/B 測試
   - [ ] 指標回歸分析

3. **完成所有文檔**
   - [ ] 設計系統文檔
   - [ ] 工程交付文檔
   - [ ] 測試報告

4. **最終驗收與發佈**
   - [ ] 產品經理驗收
   - [ ] CTO 驗收
   - [ ] 發佈至生產環境

---

## 七、結論

本路線圖提供了 8 週的詳細執行計畫，涵蓋設計系統增強、使用者體驗優化、無障礙性改進、性能優化與數據驅動驗證。透過系統化的執行與持續的指標追蹤，MorningAI 將從當前的 83/100 分提升至 **90+/100 分**，成為頂尖的 SaaS UI/UX 典範。

**核心成功因素**:
1. **團隊協作**: 設計師、工程師、產品經理緊密合作
2. **數據驅動**: 基於指標追蹤與用戶反饋持續優化
3. **漸進式改進**: 分階段實施，降低風險
4. **文檔沉澱**: 建立可持續演進的設計系統

**預期成果**:
- 首次價值時間 (TTV) < 10 分鐘
- 系統可用性 (SUS) > 80
- NPS > 35
- WCAG 2.1 AA 完整合規
- Lighthouse 性能分數 > 90

透過執行本路線圖，MorningAI 將為用戶提供流暢、高效、無障礙的使用體驗，成為業界標竿。

---

**路線圖產出日期**: 2025-10-23  
**預計完成日期**: 2025-12-18  
**負責人**: UI/UX 策略長  
**聯繫方式**: ryan2939z@gmail.com
