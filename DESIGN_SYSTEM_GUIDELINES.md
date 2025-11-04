# Morning AI 設計系統指南
**Design System Guidelines & Documentation**

**版本**: 1.0  
**日期**: 2025-10-21  
**維護團隊**: UI/UX策略長 + 設計團隊

---

## 目錄

1. [設計原則](#設計原則)
2. [視覺語言](#視覺語言)
3. [色彩系統](#色彩系統)
4. [字體系統](#字體系統)
5. [間距與佈局](#間距與佈局)
6. [組件庫](#組件庫)
7. [互動模式](#互動模式)
8. [動畫指南](#動畫指南)
9. [可訪問性](#可訪問性)
10. [響應式設計](#響應式設計)
11. [內容指南](#內容指南)

---

## 設計原則

### 核心價值觀

#### 1. 使用者中心 (User-Centric)
**原則**: 所有設計決策以使用者需求為優先考量

**實踐**:
- 進行使用者研究與測試
- 收集並分析使用者反饋
- 持續優化使用者體驗
- 建立使用者旅程地圖

**範例**:
✅ **好的實踐**: Dashboard Widget可自訂排列，符合不同使用者需求  
❌ **避免**: 固定佈局，無法調整

#### 2. 一致性 (Consistency)
**原則**: 維持視覺與互動的一致性，降低學習成本

**實踐**:
- 使用統一的Design Tokens
- 遵循既定的組件模式
- 保持命名規範一致
- 統一的錯誤處理方式

**範例**:
✅ **好的實踐**: 所有主要操作按鈕使用相同的藍色漸層  
❌ **避免**: 不同頁面使用不同的按鈕樣式

#### 3. 簡潔性 (Simplicity)
**原則**: 保持介面簡潔，避免不必要的複雜度

**實踐**:
- 移除冗餘元素
- 清晰的視覺層次
- 漸進式揭露資訊
- 專注於核心功能

**範例**:
✅ **好的實踐**: 空狀態提供明確的下一步行動  
❌ **避免**: 過多的選項讓使用者困惑

#### 4. 可訪問性 (Accessibility)
**原則**: 確保所有使用者都能使用產品

**實踐**:
- 符合WCAG 2.1 AA標準
- 支持鍵盤導航
- 提供替代文字
- 尊重使用者偏好 (prefers-reduced-motion)

**範例**:
✅ **好的實踐**: 所有互動元素可用鍵盤操作  
❌ **避免**: 僅支持滑鼠操作

#### 5. 性能優先 (Performance First)
**原則**: 快速響應，流暢體驗

**實踐**:
- 優化載入時間
- 使用骨架屏
- 漸進式載入
- 動畫性能優化

**範例**:
✅ **好的實踐**: 使用Skeleton載入狀態  
❌ **避免**: 長時間空白畫面

---

## 視覺語言

### 品牌個性

**專業 (Professional)**: 企業級SaaS產品，值得信賴  
**現代 (Modern)**: 採用最新設計趨勢，科技感  
**友善 (Friendly)**: 易於使用，不令人生畏  
**智能 (Intelligent)**: AI驅動，自動化

### 設計風格

**風格參考**: Apple Human Interface Guidelines + Material Design 3

**特色**:
- 大量留白 (Generous Whitespace)
- 柔和的圓角 (Soft Rounded Corners)
- 微妙的陰影 (Subtle Shadows)
- 流暢的動畫 (Smooth Animations)
- 漸層色彩 (Gradient Colors)

### 視覺層次

**層級系統**:
1. **背景層** (Background): 白色/灰色背景
2. **內容層** (Content): 卡片、面板
3. **互動層** (Interactive): 按鈕、輸入框
4. **覆蓋層** (Overlay): Modal、Dropdown
5. **通知層** (Notification): Toast、Alert

**實現方式**:
- 使用陰影建立深度
- 色彩對比區分層級
- Z-index管理堆疊順序

---

## 色彩系統

### Design Tokens

所有色彩定義於 `public/tokens.json`，透過 `src/lib/design-tokens.js` 載入。

### 主色調 (Primary Color)

**Blue (#3b82f6 - Blue 500)**

**用途**:
- 主要操作按鈕
- 連結
- 活躍狀態
- 品牌元素

**色彩階梯**:
```
50:  #eff6ff  // 極淺藍 - 背景
100: #dbeafe  // 淺藍 - Hover背景
200: #bfdbfe  // 淺藍
300: #93c5fd  // 中淺藍
400: #60a5fa  // 中藍
500: #3b82f6  // 主色 ⭐
600: #2563eb  // 中深藍 - Hover
700: #1d4ed8  // 深藍
800: #1e40af  // 更深藍
900: #1e3a8a  // 最深藍 - 文字
```

**使用範例**:
```jsx
// 主要按鈕
<Button className="bg-blue-500 hover:bg-blue-600">
  開始使用
</Button>

// 連結
<a className="text-blue-600 hover:text-blue-700">
  了解更多
</a>

// 活躍狀態
<div className="border-l-4 border-blue-500 bg-blue-50">
  當前頁面
</div>
```

### 輔助色 (Accent Color)

**Cyan (#0ea5e9 - Sky 500)**

**用途**:
- 次要操作
- 資訊提示
- 裝飾元素
- 漸層配色

**使用範例**:
```jsx
// 漸層按鈕
<Button className="bg-gradient-to-r from-blue-600 to-cyan-500">
  立即體驗
</Button>

// 資訊Badge
<Badge className="bg-cyan-100 text-cyan-700">
  新功能
</Badge>
```

### 語義色彩 (Semantic Colors)

#### Success (成功) - Green

**色彩**: #22c55e (Green 500)

**用途**:
- 成功訊息
- 完成狀態
- 正向指標

**範例**:
```jsx
<Alert variant="success">
  <CheckCircle className="text-green-500" />
  操作成功完成
</Alert>
```

#### Warning (警告) - Amber

**色彩**: #f59e0b (Amber 500)

**用途**:
- 警告訊息
- 需要注意的狀態
- 中等風險操作

**範例**:
```jsx
<Alert variant="warning">
  <AlertTriangle className="text-amber-500" />
  此操作無法復原
</Alert>
```

#### Error (錯誤) - Red

**色彩**: #ef4444 (Red 500)

**用途**:
- 錯誤訊息
- 失敗狀態
- 高風險操作

**範例**:
```jsx
<Alert variant="error">
  <XCircle className="text-red-500" />
  操作失敗，請重試
</Alert>
```

### 中性色 (Neutral Colors)

**Gray Scale (50-900)**

**用途**:
- 文字色彩
- 背景色彩
- 邊框色彩
- 陰影色彩

**文字色彩指南**:
```css
/* 主要文字 */
.text-primary {
  color: #111827; /* gray-900 */
}

/* 次要文字 */
.text-secondary {
  color: #6b7280; /* gray-500 */
}

/* 輔助文字 */
.text-tertiary {
  color: #9ca3af; /* gray-400 */
}

/* 禁用文字 */
.text-disabled {
  color: #d1d5db; /* gray-300 */
}
```

**背景色彩指南**:
```css
/* 主背景 */
.bg-primary {
  background-color: #ffffff; /* white */
}

/* 次背景 */
.bg-secondary {
  background-color: #f9fafb; /* gray-50 */
}

/* 卡片背景 */
.bg-card {
  background-color: #ffffff;
  border: 1px solid #e5e7eb; /* gray-200 */
}
```

### 深色模式 (Dark Mode)

**實現狀態**: 部分實現，需完善

**色彩映射**:
```css
/* Light Mode → Dark Mode */
white → gray-900
gray-50 → gray-800
gray-100 → gray-700
gray-900 → white
blue-500 → blue-400 (稍微提亮)
```

**使用方式**:
```jsx
<div className="bg-white dark:bg-gray-900 text-gray-900 dark:text-white">
  內容
</div>
```

### 色彩對比度

**WCAG 2.1 AA標準**:
- 一般文字: 4.5:1
- 大文字 (18pt+): 3:1
- UI元素: 3:1

**測試工具**:
- [WebAIM Contrast Checker](https://webaim.org/resources/contrastchecker/)
- Chrome DevTools Accessibility Panel

**常見組合**:
✅ **通過**: 
- `text-gray-900` on `bg-white` (21:1)
- `text-blue-600` on `bg-white` (8.6:1)
- `text-white` on `bg-blue-500` (8.6:1)

⚠️ **需要檢查**:
- `text-gray-400` on `bg-white` (2.5:1) - 不通過
- `text-blue-300` on `bg-white` (3.2:1) - 僅大文字通過

---

## 字體系統

### 字體家族

#### Primary Font: Inter

**特性**:
- 現代無襯線字體
- 優秀的螢幕可讀性
- 支持多種字重
- 開源免費

**載入方式**:
```html
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
```

**CSS設定**:
```css
body {
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', 
               'Roboto', 'Helvetica Neue', Arial, sans-serif;
}
```

#### Secondary Font: JetBrains Mono

**用途**: 代碼、等寬文字

**特性**:
- 等寬字體
- 程式設計優化
- 清晰的字符區分

**使用範例**:
```jsx
<code className="font-mono text-sm bg-gray-100 px-2 py-1 rounded">
  npm install
</code>
```

### 字體大小階梯

**Design Tokens** (`tokens.json`):
```json
{
  "xs":   "0.75rem",   // 12px - 小標籤
  "sm":   "0.875rem",  // 14px - 次要文字
  "base": "1rem",      // 16px - 主要文字 ⭐
  "lg":   "1.125rem",  // 18px - 強調文字
  "xl":   "1.25rem",   // 20px - 小標題
  "2xl":  "1.5rem",    // 24px - 中標題
  "3xl":  "1.875rem",  // 30px - 大標題
  "4xl":  "2.25rem"    // 36px - 超大標題
}
```

**使用指南**:

| 元素 | 大小 | 字重 | 用途 |
|------|------|------|------|
| H1 | 4xl (36px) | Bold (700) | 頁面主標題 |
| H2 | 3xl (30px) | Semibold (600) | 區塊標題 |
| H3 | 2xl (24px) | Semibold (600) | 子標題 |
| H4 | xl (20px) | Medium (500) | 小標題 |
| Body | base (16px) | Normal (400) | 主要內容 |
| Small | sm (14px) | Normal (400) | 次要資訊 |
| Caption | xs (12px) | Normal (400) | 標籤、提示 |

**範例**:
```jsx
<h1 className="text-4xl font-bold text-gray-900">
  歡迎使用 Morning AI
</h1>

<p className="text-base text-gray-600">
  AI驅動的智能決策管理系統
</p>

<span className="text-sm text-gray-500">
  最後更新: 2025-10-21
</span>
```

### 字重 (Font Weight)

**可用字重**:
```css
.font-light    { font-weight: 300; }  // 輕量
.font-normal   { font-weight: 400; }  // 正常 ⭐
.font-medium   { font-weight: 500; }  // 中等
.font-semibold { font-weight: 600; }  // 半粗
.font-bold     { font-weight: 700; }  // 粗體
```

**使用建議**:
- **標題**: Semibold (600) 或 Bold (700)
- **正文**: Normal (400)
- **強調**: Medium (500) 或 Semibold (600)
- **輕量**: Light (300) - 謹慎使用

### 行高 (Line Height)

**建議值**:
```css
/* 標題 */
.leading-tight { line-height: 1.25; }  // 緊湊

/* 正文 */
.leading-normal { line-height: 1.5; }  // 標準 ⭐

/* 寬鬆 */
.leading-relaxed { line-height: 1.625; }  // 舒適閱讀
```

**使用指南**:
- **標題**: 1.25 (緊湊)
- **正文**: 1.5-1.6 (標準)
- **長文**: 1.625-1.75 (寬鬆)

### 中文字體優化

**當前問題**: 缺少中文字體fallback優化

**建議改善**:
```css
body {
  font-family: 
    'Inter',
    /* 中文字體 */
    'Noto Sans TC',           // Google Noto Sans 繁體中文
    'Microsoft JhengHei',     // 微軟正黑體 (Windows)
    'PingFang TC',            // 蘋方 (macOS)
    /* 系統字體 */
    -apple-system,
    BlinkMacSystemFont,
    'Segoe UI',
    sans-serif;
}
```

**載入Noto Sans TC**:
```html
<link href="https://fonts.googleapis.com/css2?family=Noto+Sans+TC:wght@300;400;500;700&display=swap" rel="stylesheet">
```

---

## 間距與佈局

### 間距系統

**8px基礎網格**

所有間距為8px的倍數，確保視覺一致性。

**Design Tokens**:
```json
{
  "xs":  "0.25rem",  // 4px  - 極小間距
  "sm":  "0.5rem",   // 8px  - 小間距 ⭐
  "md":  "1rem",     // 16px - 標準間距 ⭐
  "lg":  "1.5rem",   // 24px - 大間距
  "xl":  "2rem",     // 32px - 超大間距
  "2xl": "3rem",     // 48px - 區塊間距
  "3xl": "4rem",     // 64px - 大區塊間距
  "4xl": "6rem"      // 96px - 超大區塊間距
}
```

### 間距使用指南

**內部間距 (Padding)**:
```jsx
// 按鈕
<Button className="px-4 py-2">  // 16px x 8px
  按鈕
</Button>

// 卡片
<Card className="p-6">  // 24px 全方向
  內容
</Card>

// 輸入框
<Input className="px-3 py-2" />  // 12px x 8px
```

**外部間距 (Margin)**:
```jsx
// 段落間距
<p className="mb-4">段落一</p>  // 16px 下方間距
<p className="mb-4">段落二</p>

// 區塊間距
<section className="mb-12">  // 48px 下方間距
  區塊內容
</section>
```

**元素間距 (Gap)**:
```jsx
// Flex佈局
<div className="flex gap-4">  // 16px 間距
  <div>項目1</div>
  <div>項目2</div>
</div>

// Grid佈局
<div className="grid grid-cols-3 gap-6">  // 24px 間距
  <div>項目1</div>
  <div>項目2</div>
  <div>項目3</div>
</div>
```

### 佈局系統

#### Container

**最大寬度**:
```jsx
<div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
  內容
</div>
```

**斷點對應**:
- `max-w-7xl`: 1280px (主要容器)
- `max-w-6xl`: 1152px
- `max-w-5xl`: 1024px
- `max-w-4xl`: 896px
- `max-w-3xl`: 768px (文章內容)

#### Grid系統

**12欄網格**:
```jsx
<div className="grid grid-cols-12 gap-6">
  <div className="col-span-8">主要內容</div>
  <div className="col-span-4">側邊欄</div>
</div>
```

**響應式Grid**:
```jsx
<div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
  <div>項目1</div>
  <div>項目2</div>
  <div>項目3</div>
</div>
```

#### Flexbox

**水平排列**:
```jsx
<div className="flex items-center justify-between">
  <div>左側</div>
  <div>右側</div>
</div>
```

**垂直排列**:
```jsx
<div className="flex flex-col gap-4">
  <div>項目1</div>
  <div>項目2</div>
</div>
```

---

## 組件庫

### 按鈕 (Button)

**位置**: `src/components/ui/button.jsx`

**變體 (Variants)**:

#### Default (預設)
```jsx
<Button variant="default">
  預設按鈕
</Button>
```
- 背景: `bg-blue-500`
- Hover: `hover:bg-blue-600`
- 文字: `text-white`

#### Destructive (危險操作)
```jsx
<Button variant="destructive">
  刪除
</Button>
```
- 背景: `bg-red-500`
- Hover: `hover:bg-red-600`
- 文字: `text-white`

#### Outline (輪廓)
```jsx
<Button variant="outline">
  取消
</Button>
```
- 背景: 透明
- 邊框: `border border-gray-300`
- Hover: `hover:bg-gray-100`

#### Ghost (幽靈)
```jsx
<Button variant="ghost">
  次要操作
</Button>
```
- 背景: 透明
- Hover: `hover:bg-gray-100`

#### Link (連結)
```jsx
<Button variant="link">
  了解更多
</Button>
```
- 樣式: 連結樣式
- 顏色: `text-blue-600`

**大小 (Sizes)**:
```jsx
<Button size="sm">小按鈕</Button>
<Button size="default">標準按鈕</Button>
<Button size="lg">大按鈕</Button>
<Button size="icon"><Icon /></Button>
```

**使用指南**:
- **主要操作**: Default variant, lg size
- **次要操作**: Outline variant
- **危險操作**: Destructive variant
- **輕量操作**: Ghost variant

### 卡片 (Card)

**結構**:
```jsx
<Card>
  <CardHeader>
    <CardTitle>標題</CardTitle>
    <CardDescription>描述</CardDescription>
  </CardHeader>
  <CardContent>
    內容
  </CardContent>
  <CardFooter>
    <Button>操作</Button>
  </CardFooter>
</Card>
```

**樣式**:
- 背景: `bg-white`
- 邊框: `border border-gray-200`
- 圓角: `rounded-lg` (8px)
- 陰影: `shadow-sm`

**使用場景**:
- Dashboard Widget
- 設定面板
- 資訊展示

### 輸入框 (Input)

**基礎輸入**:
```jsx
<Input
  type="text"
  placeholder="請輸入..."
  value={value}
  onChange={handleChange}
/>
```

**帶標籤**:
```jsx
<div className="space-y-2">
  <Label htmlFor="email">電子郵件</Label>
  <Input
    id="email"
    type="email"
    placeholder="your@email.com"
  />
</div>
```

**錯誤狀態**:
```jsx
<Input
  aria-invalid="true"
  className="border-red-500"
/>
<p className="text-sm text-red-500 mt-1">
  此欄位為必填
</p>
```

### 對話框 (Dialog)

**結構**:
```jsx
<Dialog open={open} onOpenChange={setOpen}>
  <DialogTrigger asChild>
    <Button>開啟對話框</Button>
  </DialogTrigger>
  <DialogContent>
    <DialogHeader>
      <DialogTitle>標題</DialogTitle>
      <DialogDescription>描述</DialogDescription>
    </DialogHeader>
    <div>內容</div>
    <DialogFooter>
      <Button variant="outline" onClick={() => setOpen(false)}>
        取消
      </Button>
      <Button onClick={handleConfirm}>
        確認
      </Button>
    </DialogFooter>
  </DialogContent>
</Dialog>
```

**使用場景**:
- 確認操作
- 表單輸入
- 資訊展示

### 通知 (Toast)

**使用Sonner**:
```jsx
import { toast } from 'sonner'

// 成功通知
toast.success('操作成功')

// 錯誤通知
toast.error('操作失敗')

// 警告通知
toast.warning('請注意')

// 資訊通知
toast.info('提示訊息')
```

**自訂內容**:
```jsx
toast.custom((t) => (
  <div className="flex items-center gap-3 bg-white p-4 rounded-lg shadow-lg">
    <CheckCircle className="text-green-500" />
    <div>
      <p className="font-medium">成功</p>
      <p className="text-sm text-gray-600">操作已完成</p>
    </div>
  </div>
))
```

---

## 互動模式

### Hover狀態

**按鈕Hover**:
```jsx
<Button className="transition-colors duration-200 hover:bg-blue-600">
  Hover我
</Button>
```

**卡片Hover**:
```jsx
<Card className="transition-all duration-200 hover:shadow-md hover:border-blue-500">
  Hover我
</Card>
```

### Focus狀態

**鍵盤焦點**:
```jsx
<Button className="focus-visible:ring-2 focus-visible:ring-blue-500 focus-visible:ring-offset-2">
  Tab到我
</Button>
```

**輸入框焦點**:
```jsx
<Input className="focus:border-blue-500 focus:ring-2 focus:ring-blue-500 focus:ring-opacity-50" />
```

### Active狀態

**按鈕按下**:
```jsx
<Button className="active:scale-95 transition-transform">
  按我
</Button>
```

### Disabled狀態

**禁用按鈕**:
```jsx
<Button disabled className="opacity-50 cursor-not-allowed">
  禁用
</Button>
```

**禁用輸入框**:
```jsx
<Input disabled className="bg-gray-100 cursor-not-allowed" />
```

---

## 動畫指南

### 動畫原則

#### 1. 有目的的動畫
**原則**: 動畫應該有明確的目的，不是為了動畫而動畫

**用途**:
- 引導注意力
- 提供反饋
- 展示關係
- 增強理解

#### 2. 性能優先
**原則**: 動畫應該流暢，不影響性能

**實踐**:
- 使用GPU加速屬性 (transform, opacity)
- 避免動畫layout屬性 (width, height, top, left)
- 限制同時動畫數量
- 移動端移除昂貴效果

#### 3. 尊重使用者偏好
**原則**: 尊重prefers-reduced-motion設定

**實現**:
```jsx
const prefersReducedMotion = window.matchMedia(
  '(prefers-reduced-motion: reduce)'
).matches

const animationProps = prefersReducedMotion
  ? {}
  : {
      initial: { opacity: 0, y: 20 },
      animate: { opacity: 1, y: 0 },
      transition: { duration: 0.3 }
    }

<motion.div {...animationProps}>
  內容
</motion.div>
```

### 動畫時長

**Design Tokens**:
```json
{
  "fast": "150ms",    // 快速 - 小元素
  "normal": "300ms",  // 標準 - 大多數動畫 ⭐
  "slow": "500ms"     // 慢速 - 大元素
}
```

**使用指南**:
- **Hover/Focus**: 150ms (fast)
- **頁面過渡**: 300ms (normal)
- **Modal開關**: 300ms (normal)
- **大型佈局變化**: 500ms (slow)

### 緩動函數 (Easing)

**Design Tokens**:
```json
{
  "ease": "cubic-bezier(0.4, 0, 0.2, 1)",      // 標準
  "easeIn": "cubic-bezier(0.4, 0, 1, 1)",      // 進入
  "easeOut": "cubic-bezier(0, 0, 0.2, 1)",     // 離開
  "easeInOut": "cubic-bezier(0.4, 0, 0.2, 1)"  // 進出
}
```

**使用場景**:
- **ease**: 大多數動畫
- **easeIn**: 元素離開畫面
- **easeOut**: 元素進入畫面
- **easeInOut**: 元素移動

### 常見動畫模式

#### Fade In (淡入)
```jsx
<motion.div
  initial={{ opacity: 0 }}
  animate={{ opacity: 1 }}
  transition={{ duration: 0.3 }}
>
  內容
</motion.div>
```

#### Slide Up (向上滑入)
```jsx
<motion.div
  initial={{ opacity: 0, y: 20 }}
  animate={{ opacity: 1, y: 0 }}
  transition={{ duration: 0.3 }}
>
  內容
</motion.div>
```

#### Scale In (縮放進入)
```jsx
<motion.div
  initial={{ opacity: 0, scale: 0.95 }}
  animate={{ opacity: 1, scale: 1 }}
  transition={{ duration: 0.3 }}
>
  內容
</motion.div>
```

#### Stagger Children (交錯動畫)
```jsx
<motion.div
  initial="hidden"
  animate="visible"
  variants={{
    visible: {
      transition: {
        staggerChildren: 0.1
      }
    }
  }}
>
  {items.map((item) => (
    <motion.div
      key={item.id}
      variants={{
        hidden: { opacity: 0, y: 20 },
        visible: { opacity: 1, y: 0 }
      }}
    >
      {item.content}
    </motion.div>
  ))}
</motion.div>
```

### 動畫治理

**規則** (`motion-governance.css`):

1. **限制無限循環**:
   - pulse: 最多3次
   - spin: 最多1次

2. **移除昂貴效果**:
   - 移動端移除blur效果

3. **動畫預算**:
   - 最多3個同時動畫

4. **prefers-reduced-motion**:
   - 動畫時長降至0.01ms
   - 過渡時長降至0.01ms

---

## 可訪問性

### WCAG 2.1 AA標準

#### 1. 可感知 (Perceivable)

**色彩對比度**:
- 一般文字: 4.5:1
- 大文字: 3:1
- UI元素: 3:1

**替代文字**:
```jsx
// 圖片
<img src="logo.png" alt="Morning AI Logo" />

// 裝飾性圖片
<img src="decoration.png" alt="" aria-hidden="true" />

// 圖示按鈕
<Button aria-label="關閉">
  <X />
</Button>
```

**文字大小**:
- 最小: 16px (1rem)
- 可縮放: 支持200%縮放

#### 2. 可操作 (Operable)

**鍵盤導航**:
```jsx
// 可聚焦
<div tabIndex={0} onKeyDown={handleKeyDown}>
  可聚焦元素
</div>

// 跳過導航
<a href="#main-content" className="sr-only focus:not-sr-only">
  跳到主要內容
</a>
```

**觸控目標**:
- 最小: 44x44px (WCAG 2.1)
- 建議: 48x48px

**焦點指示**:
```jsx
<Button className="focus-visible:ring-2 focus-visible:ring-blue-500">
  清晰的焦點
</Button>
```

#### 3. 可理解 (Understandable)

**表單標籤**:
```jsx
<Label htmlFor="email">電子郵件</Label>
<Input id="email" type="email" />
```

**錯誤訊息**:
```jsx
<Input
  id="email"
  aria-invalid="true"
  aria-describedby="email-error"
/>
<p id="email-error" className="text-red-500">
  請輸入有效的電子郵件
</p>
```

**必填欄位**:
```jsx
<Label htmlFor="name">
  姓名 <span aria-label="必填">*</span>
</Label>
<Input id="name" required aria-required="true" />
```

#### 4. 穩健 (Robust)

**語義化HTML**:
```jsx
<main>
  <section>
    <h1>標題</h1>
    <article>
      <h2>子標題</h2>
      <p>內容</p>
    </article>
  </section>
</main>
```

**ARIA標籤**:
```jsx
// 按鈕狀態
<Button aria-pressed={isActive}>
  切換
</Button>

// 載入狀態
<div aria-busy="true" aria-live="polite">
  載入中...
</div>

// 展開/收合
<Button
  aria-expanded={isExpanded}
  aria-controls="content"
>
  展開
</Button>
<div id="content" hidden={!isExpanded}>
  內容
</div>
```

### 螢幕閱讀器支持

**僅螢幕閱讀器可見**:
```jsx
<span className="sr-only">
  僅螢幕閱讀器可見的文字
</span>
```

**動態內容更新**:
```jsx
<div aria-live="polite" aria-atomic="true">
  {message}
</div>
```

---

## 響應式設計

### 斷點系統

**Design Tokens**:
```json
{
  "sm":  "640px",   // 手機橫向
  "md":  "768px",   // 平板直向
  "lg":  "1024px",  // 平板橫向/小筆電
  "xl":  "1280px",  // 桌面
  "2xl": "1536px"   // 大螢幕
}
```

### Mobile First

**原則**: 從小螢幕開始設計，逐步增強

**實踐**:
```jsx
<div className="
  text-sm          // 預設 (mobile)
  md:text-base     // 平板
  lg:text-lg       // 桌面
">
  響應式文字
</div>
```

### 常見模式

#### 響應式Grid
```jsx
<div className="
  grid
  grid-cols-1      // Mobile: 1欄
  md:grid-cols-2   // Tablet: 2欄
  lg:grid-cols-3   // Desktop: 3欄
  gap-4
  md:gap-6
">
  {items.map(item => <Card key={item.id}>{item.content}</Card>)}
</div>
```

#### 響應式導航
```jsx
// Mobile: Hamburger Menu
// Desktop: Horizontal Nav

<nav className="
  fixed md:static
  inset-0 md:inset-auto
  bg-white md:bg-transparent
  z-50 md:z-auto
">
  {/* 導航項目 */}
</nav>
```

#### 響應式間距
```jsx
<div className="
  p-4              // Mobile: 16px
  md:p-6           // Tablet: 24px
  lg:p-8           // Desktop: 32px
">
  內容
</div>
```

### 移動端優化

**觸控目標**:
```css
/* mobile-optimizations.css */
@media (max-width: 640px) {
  button, a, input, select {
    min-height: 44px;
    min-width: 44px;
  }
}
```

**字體大小**:
```css
@media (max-width: 640px) {
  html {
    font-size: 14px;  // 減小基礎字體
  }
}
```

**防止縮放**:
```css
input, select, textarea {
  font-size: 16px;  // 防止iOS自動縮放
}
```

---

## 內容指南

### 文案風格

#### 語氣與語調

**專業但友善**:
✅ 「讓我們開始設定您的帳戶」  
❌ 「開始設定帳戶」(過於生硬)

**簡潔明確**:
✅ 「儲存變更」  
❌ 「儲存您剛才所做的所有變更」(冗長)

**積極正向**:
✅ 「您的設定已成功更新」  
❌ 「設定更新完成」(中性)

#### 按鈕文案

**動作導向**:
✅ 「開始使用」  
❌ 「點擊這裡」

**明確具體**:
✅ 「下載報表」  
❌ 「下載」

**第一人稱**:
✅ 「建立我的帳戶」  
❌ 「建立帳戶」

#### 錯誤訊息

**說明問題**:
✅ 「電子郵件格式不正確」  
❌ 「錯誤」

**提供解決方案**:
✅ 「密碼至少需要8個字元，請重新輸入」  
❌ 「密碼太短」

**避免責怪**:
✅ 「找不到此帳戶，請檢查電子郵件是否正確」  
❌ 「您輸入的帳戶不存在」

### 微文案範例

**空狀態**:
```
還沒有任何資料
開始建立您的第一個專案吧！
[建立專案]
```

**載入狀態**:
```
正在載入您的資料...
```

**成功訊息**:
```
✓ 變更已儲存
```

**確認對話框**:
```
確定要刪除此項目嗎？
此操作無法復原。
[取消] [刪除]
```

---

## 實施檢查清單

### 設計階段
- [ ] 遵循設計原則
- [ ] 使用Design Tokens
- [ ] 檢查色彩對比度
- [ ] 確保觸控目標大小
- [ ] 設計響應式佈局
- [ ] 考慮可訪問性

### 開發階段
- [ ] 使用設計系統組件
- [ ] 實現響應式設計
- [ ] 添加ARIA標籤
- [ ] 支持鍵盤導航
- [ ] 尊重prefers-reduced-motion
- [ ] 優化動畫性能

### 測試階段
- [ ] 螢幕閱讀器測試
- [ ] 鍵盤導航測試
- [ ] 色彩對比度測試
- [ ] 響應式測試 (多設備)
- [ ] 性能測試
- [ ] 可用性測試

### 上線前
- [ ] Lighthouse分數 > 90
- [ ] WCAG 2.1 AA合規
- [ ] 跨瀏覽器測試
- [ ] 文案審查
- [ ] 設計審查

---

## 工具與資源

### 設計工具
- **Figma**: 設計稿與原型
- **Storybook**: 組件展示 (待建立)
- **Tokens Studio**: Design Tokens管理

### 開發工具
- **Tailwind CSS**: 樣式框架
- **Radix UI**: 無障礙組件
- **Framer Motion**: 動畫庫
- **CVA**: 組件變體管理

### 測試工具
- **WAVE**: 可訪問性測試
- **axe DevTools**: 可訪問性檢查
- **Lighthouse**: 性能與可訪問性
- **WebAIM Contrast Checker**: 對比度測試

### 參考資源
- [Tailwind CSS文檔](https://tailwindcss.com/docs)
- [Radix UI文檔](https://www.radix-ui.com/)
- [WCAG 2.1指南](https://www.w3.org/WAI/WCAG21/quickref/)
- [Material Design 3](https://m3.material.io/)
- [Apple HIG](https://developer.apple.com/design/human-interface-guidelines/)

---

## 維護與更新

### 版本控制
- 主版本: 重大變更 (破壞性)
- 次版本: 新功能 (向後兼容)
- 修訂版本: Bug修復

### 更新流程
1. 提出變更建議
2. 設計團隊審查
3. 更新文檔
4. 通知開發團隊
5. 實施變更
6. 測試驗證

### 反饋機制
- 定期設計審查會議
- 使用者反饋收集
- 可用性測試
- 數據分析

---

**文件版本**: 1.0  
**最後更新**: 2025-10-21  
**下次審查**: 2025-11-21  
**維護團隊**: UI/UX策略長 + 設計團隊

---

**附註**: 本設計系統指南為活文檔，將隨專案發展持續更新。所有團隊成員應遵循此指南，確保產品的一致性與品質。
