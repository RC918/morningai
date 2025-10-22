# Theme Usage Guide - Design Tokens

## 📋 概述

本指南說明如何在 Morning AI 專案中使用 Design Tokens（定義於 `src/styles/theme-apple.css`）。

**Design Tokens** 是集中管理的設計值（顏色、間距、字體等），確保整個應用程式的設計一致性，並簡化主題切換（如 Dark Mode）。

---

## 🎯 為什麼使用 Design Tokens？

### 優勢

1. **設計一致性**: 所有元件使用相同的設計值
2. **易於維護**: 修改一個 token 即可更新所有使用該 token 的元件
3. **Dark Mode 支援**: 自動切換 `.theme-apple.dark` 變數
4. **類型安全**: CSS 變數提供明確的命名規範
5. **效能優化**: CSS 變數比 JavaScript 計算更快

### 與 Tailwind CSS 的關係

目前專案使用 **Tailwind CSS** + **shadcn/ui**，這些元件使用 Tailwind 的 utility classes。Design Tokens 系統是**補充性的**，用於：

- 自訂元件（非 shadcn/ui）
- 需要精確控制的樣式
- 動態樣式（inline styles）
- 未來逐步遷移 Tailwind 元件

---

## 🚀 快速開始

### 1. 確保 Theme 已啟用

在 `App.jsx` 中，根容器必須有 `.theme-apple` class：

```jsx
// src/App.jsx
import './styles/theme-apple.css'

function App() {
  return (
    <div className="theme-apple">
      {/* 你的應用程式內容 */}
    </div>
  )
}
```

### 2. 在元件中使用 Tokens

#### 方式 1: Inline Styles（推薦用於動態樣式）

```jsx
function MyComponent() {
  return (
    <div style={{
      padding: 'var(--spacing-4)',
      backgroundColor: 'var(--bg-primary)',
      color: 'var(--text-primary)',
      borderRadius: 'var(--radius-md)',
      boxShadow: 'var(--shadow-sm)'
    }}>
      內容
    </div>
  )
}
```

#### 方式 2: CSS Modules

```css
/* MyComponent.module.css */
.container {
  padding: var(--spacing-4);
  background-color: var(--bg-primary);
  color: var(--text-primary);
  border-radius: var(--radius-md);
  box-shadow: var(--shadow-sm);
}
```

```jsx
import styles from './MyComponent.module.css'

function MyComponent() {
  return <div className={styles.container}>內容</div>
}
```

#### 方式 3: 傳統 CSS

```css
/* styles.css */
.my-component {
  padding: var(--spacing-4);
  background-color: var(--bg-primary);
  color: var(--text-primary);
}
```

---

## 📚 Token 參考

### 🎨 顏色 Tokens

#### 品牌色彩

```css
--brand-gold: #FFD700
--brand-orange: #FF6B35
--brand-warm-orange: #FF8C42
```

**使用範例**:
```jsx
<div style={{ backgroundColor: 'var(--brand-gold)' }}>品牌色彩</div>
```

#### Primary 色彩

```css
--color-primary: #FF8C42
--color-primary-hover: #FF7A2E
--color-primary-active: #FF681A
--color-primary-light: #FFE5D9
--color-primary-dark: #CC7035
```

**使用範例**:
```jsx
<button style={{
  backgroundColor: 'var(--color-primary)',
  ':hover': { backgroundColor: 'var(--color-primary-hover)' }
}}>
  按鈕
</button>
```

#### Secondary 色彩

```css
--color-secondary: #FFD700
--color-secondary-hover: #E6C200
--color-secondary-active: #CCAD00
--color-secondary-light: #FFF9E6
--color-secondary-dark: #B39700
```

#### Neutral 色彩（灰階）

```css
--color-neutral-50: #FAFAFA
--color-neutral-100: #F5F5F5
--color-neutral-200: #E5E5E5
--color-neutral-300: #D4D4D4
--color-neutral-400: #A3A3A3
--color-neutral-500: #737373
--color-neutral-600: #525252
--color-neutral-700: #404040
--color-neutral-800: #262626
--color-neutral-900: #171717
```

**使用範例**:
```jsx
<div style={{
  backgroundColor: 'var(--color-neutral-100)',
  border: '1px solid var(--color-neutral-300)'
}}>
  灰色背景
</div>
```

#### Semantic 色彩

```css
--color-success: #10B981
--color-success-light: #D1FAE5
--color-warning: #F59E0B
--color-warning-light: #FEF3C7
--color-error: #EF4444
--color-error-light: #FEE2E2
--color-info: #3B82F6
--color-info-light: #DBEAFE
```

**使用範例**:
```jsx
<span style={{
  padding: 'var(--spacing-1) var(--spacing-3)',
  backgroundColor: 'var(--color-success-light)',
  color: 'var(--color-success)',
  borderRadius: 'var(--radius-full)'
}}>
  成功
</span>
```

#### 背景色彩

```css
--bg-primary: #FFFFFF
--bg-secondary: #F9FAFB
--bg-tertiary: #F3F4F6
--bg-overlay: rgba(0, 0, 0, 0.5)
--bg-gradient-primary: linear-gradient(135deg, #FFD700 0%, #FF6B35 100%)
```

#### 文字色彩

```css
--text-primary: #171717
--text-secondary: #525252
--text-tertiary: #A3A3A3
--text-disabled: #D4D4D4
--text-inverse: #FFFFFF
--text-link: #3B82F6
--text-link-hover: #2563EB
```

#### 邊框色彩

```css
--border-primary: #E5E5E5
--border-secondary: #D4D4D4
--border-focus: #FF8C42
--border-error: #EF4444
```

### 📏 間距 Tokens

```css
--spacing-0: 0px
--spacing-1: 4px
--spacing-2: 8px
--spacing-3: 12px
--spacing-4: 16px
--spacing-5: 20px
--spacing-6: 24px
--spacing-8: 32px
--spacing-10: 40px
--spacing-12: 48px
--spacing-16: 64px
--spacing-20: 80px
--spacing-24: 96px
```

**使用範例**:
```jsx
<div style={{
  padding: 'var(--spacing-4)',
  margin: 'var(--spacing-2) 0',
  gap: 'var(--spacing-3)'
}}>
  間距範例
</div>
```

### 🔤 Typography Tokens

#### Font Family

```css
--font-family-sans: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif
--font-family-mono: 'Fira Code', 'Courier New', monospace
```

#### Font Sizes

```css
--font-size-xs: 12px
--font-size-sm: 14px
--font-size-base: 16px
--font-size-lg: 18px
--font-size-xl: 20px
--font-size-2xl: 24px
--font-size-3xl: 30px
--font-size-4xl: 36px
--font-size-5xl: 48px
--font-size-6xl: 60px
```

#### Font Weights

```css
--font-weight-light: 300
--font-weight-normal: 400
--font-weight-medium: 500
--font-weight-semibold: 600
--font-weight-bold: 700
```

#### Line Heights

```css
--line-height-tight: 1.25
--line-height-normal: 1.5
--line-height-relaxed: 1.75
```

**使用範例**:
```jsx
<h1 style={{
  fontFamily: 'var(--font-family-sans)',
  fontSize: 'var(--font-size-3xl)',
  fontWeight: 'var(--font-weight-bold)',
  lineHeight: 'var(--line-height-tight)'
}}>
  標題
</h1>
```

### 🎭 陰影 Tokens

```css
--shadow-xs: 0 1px 2px 0 rgba(0, 0, 0, 0.05)
--shadow-sm: 0 1px 3px 0 rgba(0, 0, 0, 0.1), 0 1px 2px 0 rgba(0, 0, 0, 0.06)
--shadow-md: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06)
--shadow-lg: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05)
--shadow-xl: 0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04)
--shadow-2xl: 0 25px 50px -12px rgba(0, 0, 0, 0.25)
```

**使用範例**:
```jsx
<div style={{ boxShadow: 'var(--shadow-md)' }}>卡片</div>
```

### 🔄 圓角 Tokens

```css
--radius-none: 0px
--radius-sm: 4px
--radius-md: 8px
--radius-lg: 12px
--radius-xl: 16px
--radius-2xl: 24px
--radius-full: 9999px
```

**使用範例**:
```jsx
<button style={{ borderRadius: 'var(--radius-md)' }}>按鈕</button>
<div style={{ borderRadius: 'var(--radius-full)' }}>圓形標籤</div>
```

### ⏱️ 過渡 Tokens

```css
--transition-fast: 150ms ease-in-out
--transition-base: 200ms ease-in-out
--transition-slow: 300ms ease-in-out
```

**使用範例**:
```jsx
<button style={{
  transition: 'all var(--transition-base)',
  ':hover': { transform: 'scale(1.05)' }
}}>
  按鈕
</button>
```

### 📐 Z-Index Tokens

```css
--z-dropdown: 1000
--z-sticky: 1020
--z-fixed: 1030
--z-modal-backdrop: 1040
--z-modal: 1050
--z-popover: 1060
--z-tooltip: 1070
```

### 🧩 元件特定 Tokens

```css
--button-height-sm: 32px
--button-height-md: 40px
--button-height-lg: 48px
--input-height-sm: 32px
--input-height-md: 40px
--input-height-lg: 48px
--navbar-height: 64px
--sidebar-width: 256px
--sidebar-width-collapsed: 64px
```

### 📱 斷點 Tokens

```css
--breakpoint-sm: 640px
--breakpoint-md: 768px
--breakpoint-lg: 1024px
--breakpoint-xl: 1280px
--breakpoint-2xl: 1536px
```

**使用範例**:
```css
@media (min-width: var(--breakpoint-md)) {
  .container {
    max-width: 768px;
  }
}
```

---

## 🌓 Dark Mode 支援

### 自動切換

當根容器有 `.theme-apple.dark` class 時，所有 tokens 自動切換為 Dark Mode 值：

```jsx
function App() {
  const [isDark, setIsDark] = useState(false)

  return (
    <div className={`theme-apple ${isDark ? 'dark' : ''}`}>
      <button onClick={() => setIsDark(!isDark)}>
        切換 Dark Mode
      </button>
      {/* 所有元件自動使用 Dark Mode tokens */}
    </div>
  )
}
```

### Dark Mode Token 覆蓋

```css
.theme-apple.dark {
  --bg-primary: #171717;
  --bg-secondary: #262626;
  --bg-tertiary: #404040;
  --text-primary: #FAFAFA;
  --text-secondary: #D4D4D4;
  --text-tertiary: #A3A3A3;
  --border-primary: #404040;
  --border-secondary: #525252;
  --shadow-xs: 0 1px 2px 0 rgba(0, 0, 0, 0.3);
  --shadow-sm: 0 1px 3px 0 rgba(0, 0, 0, 0.4), 0 1px 2px 0 rgba(0, 0, 0, 0.3);
  --shadow-md: 0 4px 6px -1px rgba(0, 0, 0, 0.4), 0 2px 4px -1px rgba(0, 0, 0, 0.3);
  --shadow-lg: 0 10px 15px -3px rgba(0, 0, 0, 0.4), 0 4px 6px -2px rgba(0, 0, 0, 0.3);
  --shadow-xl: 0 20px 25px -5px rgba(0, 0, 0, 0.4), 0 10px 10px -5px rgba(0, 0, 0, 0.3);
  --shadow-2xl: 0 25px 50px -12px rgba(0, 0, 0, 0.5);
}
```

---

## 📝 常見模式範例

### 按鈕

```jsx
function PrimaryButton({ children, onClick }) {
  return (
    <button
      onClick={onClick}
      style={{
        padding: 'var(--spacing-2) var(--spacing-4)',
        backgroundColor: 'var(--color-primary)',
        color: 'white',
        border: 'none',
        borderRadius: 'var(--radius-md)',
        fontSize: 'var(--font-size-sm)',
        fontWeight: 'var(--font-weight-medium)',
        cursor: 'pointer',
        transition: 'all var(--transition-base)',
        boxShadow: 'var(--shadow-sm)'
      }}
      onMouseEnter={(e) => {
        e.target.style.backgroundColor = 'var(--color-primary-hover)'
      }}
      onMouseLeave={(e) => {
        e.target.style.backgroundColor = 'var(--color-primary)'
      }}
    >
      {children}
    </button>
  )
}
```

### 卡片

```jsx
function Card({ title, children }) {
  return (
    <div style={{
      padding: 'var(--spacing-6)',
      backgroundColor: 'var(--bg-primary)',
      border: '1px solid var(--border-primary)',
      borderRadius: 'var(--radius-lg)',
      boxShadow: 'var(--shadow-md)'
    }}>
      <h3 style={{
        fontSize: 'var(--font-size-xl)',
        fontWeight: 'var(--font-weight-semibold)',
        color: 'var(--text-primary)',
        marginBottom: 'var(--spacing-4)'
      }}>
        {title}
      </h3>
      <div style={{
        fontSize: 'var(--font-size-base)',
        color: 'var(--text-secondary)',
        lineHeight: 'var(--line-height-normal)'
      }}>
        {children}
      </div>
    </div>
  )
}
```

### 輸入框

```jsx
function Input({ placeholder, value, onChange }) {
  return (
    <input
      type="text"
      placeholder={placeholder}
      value={value}
      onChange={onChange}
      style={{
        width: '100%',
        height: 'var(--input-height-md)',
        padding: '0 var(--spacing-3)',
        backgroundColor: 'var(--bg-primary)',
        border: '1px solid var(--border-primary)',
        borderRadius: 'var(--radius-md)',
        fontSize: 'var(--font-size-base)',
        color: 'var(--text-primary)',
        transition: 'all var(--transition-base)',
        outline: 'none'
      }}
      onFocus={(e) => {
        e.target.style.borderColor = 'var(--border-focus)'
        e.target.style.boxShadow = '0 0 0 3px rgba(255, 140, 66, 0.1)'
      }}
      onBlur={(e) => {
        e.target.style.borderColor = 'var(--border-primary)'
        e.target.style.boxShadow = 'none'
      }}
    />
  )
}
```

### 狀態標籤

```jsx
function Badge({ children, variant = 'info' }) {
  const variants = {
    success: {
      bg: 'var(--color-success-light)',
      color: 'var(--color-success)'
    },
    warning: {
      bg: 'var(--color-warning-light)',
      color: 'var(--color-warning)'
    },
    error: {
      bg: 'var(--color-error-light)',
      color: 'var(--color-error)'
    },
    info: {
      bg: 'var(--color-info-light)',
      color: 'var(--color-info)'
    }
  }

  const style = variants[variant]

  return (
    <span style={{
      display: 'inline-block',
      padding: 'var(--spacing-1) var(--spacing-3)',
      backgroundColor: style.bg,
      color: style.color,
      borderRadius: 'var(--radius-full)',
      fontSize: 'var(--font-size-xs)',
      fontWeight: 'var(--font-weight-medium)'
    }}>
      {children}
    </span>
  )
}
```

---

## 🧪 測試 Token 系統

### 範例元件

我們提供了 `TokenExample` 元件來展示所有 tokens 的使用：

```jsx
import TokenExample from '@/components/examples/TokenExample'

function TestPage() {
  return <TokenExample />
}
```

### 驗證 Dark Mode

```jsx
function DarkModeTest() {
  const [isDark, setIsDark] = useState(false)

  return (
    <div className={`theme-apple ${isDark ? 'dark' : ''}`}>
      <button onClick={() => setIsDark(!isDark)}>
        切換 Dark Mode
      </button>
      <TokenExample />
    </div>
  )
}
```

---

## 📚 最佳實踐

### ✅ 推薦做法

1. **優先使用 Semantic Tokens**: 使用 `--text-primary` 而非 `--color-neutral-900`
2. **使用 Spacing Scale**: 使用 `--spacing-4` 而非 `16px`
3. **使用 Transition Tokens**: 使用 `var(--transition-base)` 而非 `200ms ease-in-out`
4. **組合 Tokens**: 組合多個 tokens 創建複雜樣式

```jsx
// ✅ 好的做法
<div style={{
  padding: 'var(--spacing-4)',
  backgroundColor: 'var(--bg-primary)',
  color: 'var(--text-primary)',
  borderRadius: 'var(--radius-md)',
  boxShadow: 'var(--shadow-sm)',
  transition: 'all var(--transition-base)'
}}>
  內容
</div>

// ❌ 不好的做法
<div style={{
  padding: '16px',
  backgroundColor: '#FFFFFF',
  color: '#171717',
  borderRadius: '8px',
  boxShadow: '0 1px 3px rgba(0,0,0,0.1)',
  transition: '200ms ease-in-out'
}}>
  內容
</div>
```

### ❌ 避免做法

1. **不要硬編碼顏色值**: 使用 tokens 而非 hex/rgb 值
2. **不要硬編碼間距**: 使用 spacing scale
3. **不要混用 Tailwind 和 Tokens**: 選擇一種方式並保持一致
4. **不要在 tokens 中使用 `!important`**: 依賴 CSS 特異性

---

## 🔄 遷移策略

### 從 Tailwind 遷移到 Tokens

**階段 1: 新元件使用 Tokens**
- 所有新建元件優先使用 Design Tokens
- 保持現有 shadcn/ui 元件不變

**階段 2: 漸進式遷移**
- 識別高頻使用的自訂元件
- 逐步將 Tailwind classes 替換為 CSS 變數
- 優先遷移：Buttons, Cards, Forms

**階段 3: 完全遷移**
- 所有自訂元件使用 Tokens
- shadcn/ui 元件保持 Tailwind（除非需要深度自訂）

---

## 🐛 常見問題

### Q: Token 沒有生效？

**A**: 檢查以下項目：
1. 確保 `theme-apple.css` 已在 `App.jsx` 中 import
2. 確保根容器有 `.theme-apple` class
3. 檢查 CSS 變數語法：`var(--token-name)`
4. 使用瀏覽器 DevTools 檢查 computed styles

### Q: Dark Mode 沒有切換？

**A**: 檢查：
1. 根容器是否有 `.theme-apple.dark` class
2. 使用的 token 是否有 dark variant 定義
3. 檢查 CSS 特異性（`.theme-apple.dark` 必須覆蓋 `.theme-apple`）

### Q: 可以混用 Tailwind 和 Tokens 嗎？

**A**: 可以，但不推薦。建議：
- shadcn/ui 元件：保持 Tailwind
- 自訂元件：使用 Design Tokens
- 避免在同一元件中混用

### Q: 如何新增自訂 Token？

**A**: 編輯 `src/styles/theme-apple.css`：

```css
.theme-apple {
  /* 新增你的 token */
  --my-custom-color: #FF0000;
}

.theme-apple.dark {
  /* Dark mode variant */
  --my-custom-color: #CC0000;
}
```

---

## 📖 相關資源

- **Token 定義**: `src/styles/theme-apple.css`
- **範例元件**: `src/components/examples/TokenExample.jsx`
- **Token 遷移計劃**: `TOKEN_MIGRATION_PLAN.md`
- **品牌資產**: `public/assets/brand/README.md`

---

**最後更新**: 2025-10-21  
**維護者**: Devin (AI Assistant)  
**版本**: 1.0.0
