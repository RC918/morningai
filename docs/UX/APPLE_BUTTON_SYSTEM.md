# Apple Button System

Apple 風格的按鈕組件系統，整合 Spring Animation 和觸覺反饋模擬。

## 概述

AppleButton 組件基於 iOS Human Interface Guidelines 設計，提供：

- **8 種變體**：Primary, Secondary, Destructive, Outline, Ghost, Link, Filled, Tinted
- **6 種尺寸**：sm, default, lg, icon, icon-sm, icon-lg
- **4 種觸覺反饋**：none, light, medium, heavy
- **Spring 動畫**：使用 Framer Motion 實現流暢的彈性動畫
- **完整可訪問性**：鍵盤導航、焦點管理、ARIA 支援

## 安裝

```bash
# 已包含在項目中
import { AppleButton } from '@/components/ui/apple-button'
```

## 基本用法

### 簡單按鈕

```jsx
import { AppleButton } from '@/components/ui/apple-button'

function MyComponent() {
  return (
    <AppleButton variant="primary">
      Click Me
    </AppleButton>
  )
}
```

### 帶圖標

```jsx
import { Download } from 'lucide-react'

<AppleButton variant="primary">
  <Download className="size-4" />
  Download
</AppleButton>
```

### 圖標按鈕

```jsx
<AppleButton variant="primary" size="icon">
  <Plus className="size-5" />
</AppleButton>
```

## 變體 (Variants)

### Primary
主要操作按鈕，用於最重要的操作。

```jsx
<AppleButton variant="primary">
  Save Changes
</AppleButton>
```

**使用場景**：
- 表單提交
- 確認操作
- 主要 CTA

### Secondary
次要操作按鈕。

```jsx
<AppleButton variant="secondary">
  Learn More
</AppleButton>
```

**使用場景**：
- 次要操作
- 輔助功能
- 非關鍵操作

### Destructive
破壞性操作按鈕，用於刪除、取消等操作。

```jsx
<AppleButton variant="destructive" haptic="heavy">
  <Trash2 className="size-4" />
  Delete
</AppleButton>
```

**使用場景**：
- 刪除操作
- 取消訂閱
- 永久性操作

### Outline
輪廓按鈕，帶有毛玻璃效果。

```jsx
<AppleButton variant="outline">
  Cancel
</AppleButton>
```

**使用場景**：
- 取消操作
- 次要選項
- 卡片操作

### Ghost
透明按鈕，懸停時顯示背景。

```jsx
<AppleButton variant="ghost">
  <Settings className="size-4" />
  Settings
</AppleButton>
```

**使用場景**：
- 導航項目
- 工具欄按鈕
- 列表項操作

### Link
鏈接樣式按鈕。

```jsx
<AppleButton variant="link">
  Learn more
</AppleButton>
```

**使用場景**：
- 內聯鏈接
- 文本中的操作
- 導航鏈接

### Filled
填充按鈕，使用 accent 顏色。

```jsx
<AppleButton variant="filled">
  Continue
</AppleButton>
```

**使用場景**：
- 表單步驟
- 流程繼續
- 中等重要性操作

### Tinted
著色按鈕，使用淺色背景。

```jsx
<AppleButton variant="tinted">
  <Download className="size-4" />
  Export
</AppleButton>
```

**使用場景**：
- 工具欄操作
- 快速操作
- 標籤式按鈕

## 尺寸 (Sizes)

### 文本按鈕尺寸

```jsx
<AppleButton size="sm">Small</AppleButton>
<AppleButton size="default">Default</AppleButton>
<AppleButton size="lg">Large</AppleButton>
```

| 尺寸 | 高度 | 圓角 | 內邊距 | 字體 |
|------|------|------|--------|------|
| sm | 32px | 8px | 12px | 14px |
| default | 40px | 12px | 16px | 14px |
| lg | 48px | 12px | 24px | 16px |

### 圖標按鈕尺寸

```jsx
<AppleButton size="icon-sm">
  <Plus className="size-4" />
</AppleButton>

<AppleButton size="icon">
  <Plus className="size-5" />
</AppleButton>

<AppleButton size="icon-lg">
  <Plus className="size-6" />
</AppleButton>
```

| 尺寸 | 尺寸 | 圓角 | 圖標 |
|------|------|------|------|
| icon-sm | 32x32px | 8px | 16px |
| icon | 40x40px | 12px | 20px |
| icon-lg | 48x48px | 12px | 24px |

## 觸覺反饋 (Haptic Feedback)

AppleButton 整合了觸覺反饋模擬系統，提供視覺反饋來模擬 iOS 的觸覺反饋。

```jsx
<AppleButton haptic="none">No Feedback</AppleButton>
<AppleButton haptic="light">Light</AppleButton>
<AppleButton haptic="medium">Medium (Default)</AppleButton>
<AppleButton haptic="heavy">Heavy</AppleButton>
```

### 觸覺級別指南

| 級別 | 使用場景 | 範例 |
|------|----------|------|
| none | 頻繁操作 | 列表滾動、導航 |
| light | 輕量操作 | 選擇、切換 |
| medium | 標準操作 | 按鈕點擊、確認 |
| heavy | 重要操作 | 刪除、提交、錯誤 |

## Spring 動畫

所有按鈕都使用 Spring Animation System 的 `snappy` 預設：

```javascript
// 自動應用
whileHover={{ scale: 1.02 }}
whileTap={{ scale: 0.98 }}
transition={getSpringConfig('snappy')}
```

### 動畫特性

- **Hover**: 放大 2%
- **Tap**: 縮小 2%
- **Spring**: Snappy 預設 (快速響應)
- **Reduced Motion**: 自動禁用動畫

## 狀態管理

### 禁用狀態

```jsx
<AppleButton disabled>
  Disabled Button
</AppleButton>
```

禁用時：
- 不透明度降至 50%
- 禁用指針事件
- 禁用動畫
- 禁用觸覺反饋

### 加載狀態

```jsx
const [loading, setLoading] = useState(false)

<AppleButton disabled={loading}>
  {loading ? (
    <>
      <Spinner className="size-4" />
      Loading...
    </>
  ) : (
    'Submit'
  )}
</AppleButton>
```

## 實際應用範例

### 表單操作

```jsx
<div className="flex gap-2">
  <AppleButton variant="primary" className="flex-1">
    <Check className="size-4" />
    Save Changes
  </AppleButton>
  <AppleButton variant="outline">
    Cancel
  </AppleButton>
</div>
```

### 確認對話框

```jsx
<div className="flex flex-col gap-2">
  <AppleButton variant="destructive" className="w-full" haptic="heavy">
    <Trash2 className="size-4" />
    Delete Account
  </AppleButton>
  <AppleButton variant="outline" className="w-full">
    Keep Account
  </AppleButton>
</div>
```

### 工具欄

```jsx
<div className="flex items-center justify-between">
  <div className="flex gap-1">
    <AppleButton variant="ghost" size="icon-sm">
      <Plus className="size-4" />
    </AppleButton>
    <AppleButton variant="ghost" size="icon-sm">
      <Share2 className="size-4" />
    </AppleButton>
  </div>
  <div className="flex gap-2">
    <AppleButton variant="outline" size="sm">Cancel</AppleButton>
    <AppleButton variant="primary" size="sm">Done</AppleButton>
  </div>
</div>
```

### 按鈕組

```jsx
<div className="inline-flex rounded-xl overflow-hidden border border-input">
  <AppleButton variant="ghost" className="rounded-none border-r">
    Option 1
  </AppleButton>
  <AppleButton variant="ghost" className="rounded-none border-r">
    Option 2
  </AppleButton>
  <AppleButton variant="ghost" className="rounded-none">
    Option 3
  </AppleButton>
</div>
```

### 導航列表

```jsx
<div className="flex flex-col gap-2">
  <AppleButton variant="ghost" className="w-full justify-between">
    Profile Settings
    <ChevronRight className="size-4" />
  </AppleButton>
  <AppleButton variant="ghost" className="w-full justify-between">
    Privacy & Security
    <ChevronRight className="size-4" />
  </AppleButton>
</div>
```

### 卡片操作

```jsx
<div className="p-6 bg-background rounded-xl border">
  <div className="flex items-start gap-4 mb-4">
    <div className="size-12 rounded-xl bg-primary/10 flex items-center justify-center">
      <Download className="size-6 text-primary" />
    </div>
    <div className="flex-1">
      <h4 className="font-semibold">Download Report</h4>
      <p className="text-sm text-muted-foreground">Export your data</p>
    </div>
  </div>
  <div className="flex gap-2">
    <AppleButton variant="tinted" size="sm">
      <Download className="size-4" />
      PDF
    </AppleButton>
    <AppleButton variant="tinted" size="sm">
      <Download className="size-4" />
      CSV
    </AppleButton>
  </div>
</div>
```

## 可訪問性

### 鍵盤導航

- **Enter/Space**: 觸發按鈕
- **Tab**: 焦點移動
- **焦點環**: 3px 環形指示器

### ARIA 屬性

```jsx
<AppleButton
  aria-label="Delete item"
  aria-describedby="delete-description"
>
  <Trash2 className="size-4" />
</AppleButton>
```

### Reduced Motion

系統自動檢測 `prefers-reduced-motion` 並禁用動畫：

```css
@media (prefers-reduced-motion: reduce) {
  /* 動畫自動禁用 */
}
```

## 最佳實踐

### ✅ 好的做法

```jsx
// 清晰的操作層級
<div className="flex gap-2">
  <AppleButton variant="primary">Save</AppleButton>
  <AppleButton variant="outline">Cancel</AppleButton>
</div>

// 適當的觸覺反饋
<AppleButton variant="destructive" haptic="heavy">
  Delete
</AppleButton>

// 圖標 + 文字
<AppleButton>
  <Download className="size-4" />
  Download
</AppleButton>
```

### ❌ 避免的做法

```jsx
// 不要：多個 primary 按鈕
<div className="flex gap-2">
  <AppleButton variant="primary">Save</AppleButton>
  <AppleButton variant="primary">Cancel</AppleButton>
</div>

// 不要：過度使用觸覺反饋
<AppleButton haptic="heavy">
  Normal Action
</AppleButton>

// 不要：圖標過大
<AppleButton size="icon">
  <Plus className="size-10" />
</AppleButton>
```

## 設計指南

### 按鈕層級

1. **Primary**: 每個視圖最多 1 個
2. **Secondary/Outline**: 次要操作
3. **Ghost**: 低優先級操作
4. **Destructive**: 破壞性操作

### 間距

- 按鈕之間：8px (gap-2)
- 按鈕組：0px (緊密排列)
- 垂直堆疊：8px (gap-2)

### 圓角

- 小按鈕：8px (rounded-lg)
- 標準/大按鈕：12px (rounded-xl)

## 與現有 Button 的區別

| 特性 | Button | AppleButton |
|------|--------|-------------|
| 動畫 | CSS transition | Framer Motion Spring |
| 觸覺反饋 | 無 | 4 級觸覺模擬 |
| 變體數量 | 6 | 8 |
| 圓角 | rounded-md | rounded-xl |
| 陰影 | shadow-xs | shadow-sm/md |
| 毛玻璃 | 無 | backdrop-blur-sm |

## 遷移指南

### 從 Button 遷移到 AppleButton

```jsx
// 之前
import { Button } from '@/components/ui/button'
<Button variant="default">Click</Button>

// 之後
import { AppleButton } from '@/components/ui/apple-button'
<AppleButton variant="primary">Click</AppleButton>
```

### 變體映射

| Button | AppleButton |
|--------|-------------|
| default | primary |
| secondary | secondary |
| destructive | destructive |
| outline | outline |
| ghost | ghost |
| link | link |
| - | filled |
| - | tinted |

## 性能考慮

- **Framer Motion**: 使用 GPU 加速動畫
- **觸覺反饋**: 輕量級 CSS 動畫
- **Tree Shaking**: 只導入使用的組件
- **Memoization**: 使用 React.useCallback 優化

## 瀏覽器支援

- Chrome/Edge: 完全支援
- Firefox: 完全支援
- Safari: 完全支援
- iOS Safari: 完全支援
- Android Chrome: 完全支援

## 相關資源

- [Apple Human Interface Guidelines - Buttons](https://developer.apple.com/design/human-interface-guidelines/buttons)
- [Spring Animation System](./SPRING_ANIMATION_SYSTEM.md)
- [Framer Motion Documentation](https://www.framer.com/motion/)
- [iOS Design Patterns](https://developer.apple.com/design/human-interface-guidelines/patterns)

## 測試檢查清單

- [ ] 所有變體正常顯示
- [ ] 所有尺寸正確
- [ ] 觸覺反饋正常工作
- [ ] Spring 動畫流暢
- [ ] 禁用狀態正確
- [ ] 鍵盤導航正常
- [ ] 焦點環可見
- [ ] Reduced motion 生效
- [ ] 深色模式正常
- [ ] 移動端觸摸正常
