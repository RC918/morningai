# 無障礙指南

## 概述

無障礙性 (Accessibility, A11y) 確保所有用戶，包括殘障用戶，都能使用產品。MorningAI 遵循 WCAG 2.1 AA 標準，提供鍵盤導航、螢幕閱讀器支援、色彩對比度等無障礙功能。

## WCAG 2.1 AA 標準

### 四大原則 (POUR)

1. **可感知 (Perceivable)**: 用戶能感知到內容
2. **可操作 (Operable)**: 用戶能操作介面
3. **可理解 (Understandable)**: 用戶能理解內容與操作
4. **穩健 (Robust)**: 內容能被各種輔助技術解讀

## 鍵盤導航

### 基本要求

所有互動元素必須可用鍵盤訪問：

```jsx
// ✅ 正確：原生按鈕自動支援鍵盤
<button onClick={handleClick}>點擊我</button>

// ❌ 錯誤：div 不支援鍵盤
<div onClick={handleClick}>點擊我</div>

// ✅ 修正：添加 tabIndex 與鍵盤事件
<div
  role="button"
  tabIndex={0}
  onClick={handleClick}
  onKeyDown={(e) => {
    if (e.key === 'Enter' || e.key === ' ') {
      e.preventDefault()
      handleClick()
    }
  }}
>
  點擊我
</div>
```

### Tab 順序

```jsx
// 自然 Tab 順序（推薦）
<form>
  <input type="text" />      {/* Tab 1 */}
  <input type="email" />     {/* Tab 2 */}
  <button type="submit">     {/* Tab 3 */}
    提交
  </button>
</form>

// 自訂 Tab 順序（避免使用）
<div tabIndex={3}>第三個</div>
<div tabIndex={1}>第一個</div>
<div tabIndex={2}>第二個</div>
```

### 焦點可見

```css
/* 確保焦點可見 */
button:focus-visible {
  outline: 2px solid rgb(59 130 246);
  outline-offset: 2px;
}

/* 移除預設 outline 時必須提供替代樣式 */
button:focus {
  outline: none;
}

button:focus-visible {
  box-shadow: 0 0 0 3px rgb(59 130 246 / 0.5);
}
```

### 跳過導航

```jsx
// 提供跳過導航連結
<a
  href="#main-content"
  className="sr-only focus:not-sr-only focus:absolute focus:top-4 focus:left-4 focus:z-50 focus:px-4 focus:py-2 focus:bg-primary-500 focus:text-white"
>
  跳至主要內容
</a>

<nav aria-label="主導航">
  {/* 導航內容 */}
</nav>

<main id="main-content">
  {/* 主要內容 */}
</main>
```

### 快捷鍵

```jsx
function App() {
  useEffect(() => {
    const handleKeyDown = (e) => {
      // Cmd/Ctrl + K: 開啟搜尋
      if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
        e.preventDefault()
        openSearch()
      }

      // Esc: 關閉對話框
      if (e.key === 'Escape') {
        closeDialog()
      }

      // ?: 顯示快捷鍵說明
      if (e.key === '?') {
        showKeyboardShortcuts()
      }
    }

    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [])

  return (
    <div>
      {/* 快捷鍵說明 */}
      <button
        onClick={showKeyboardShortcuts}
        aria-label="顯示鍵盤快捷鍵"
      >
        <Keyboard className="w-4 h-4" />
      </button>
    </div>
  )
}
```

## 語義化 HTML

### 使用正確的元素

```jsx
// ✅ 正確：使用語義元素
<header>
  <nav aria-label="主導航">
    <ul>
      <li><a href="/dashboard">Dashboard</a></li>
      <li><a href="/strategies">策略</a></li>
    </ul>
  </nav>
</header>

<main>
  <article>
    <h1>文章標題</h1>
    <p>內容...</p>
  </article>
</main>

<aside aria-label="相關資訊">
  <h2>相關連結</h2>
  <ul>
    <li><a href="/help">幫助</a></li>
  </ul>
</aside>

<footer>
  <p>&copy; 2025 MorningAI</p>
</footer>

// ❌ 錯誤：使用 div
<div className="header">
  <div className="nav">
    <div onClick={() => navigate('/dashboard')}>Dashboard</div>
  </div>
</div>
```

### 標題層級

```jsx
// ✅ 正確：按順序使用標題
<h1>頁面標題</h1>
<section>
  <h2>章節標題</h2>
  <h3>子章節標題</h3>
  <h3>另一個子章節</h3>
</section>
<section>
  <h2>另一個章節</h2>
</section>

// ❌ 錯誤：跳過層級
<h1>頁面標題</h1>
<h3>跳過 h2</h3>  {/* ❌ 不應跳過 h2 */}
```

### 列表

```jsx
// ✅ 正確：使用列表元素
<ul>
  <li>項目 1</li>
  <li>項目 2</li>
  <li>項目 3</li>
</ul>

<ol>
  <li>步驟 1</li>
  <li>步驟 2</li>
  <li>步驟 3</li>
</ol>

// ❌ 錯誤：使用 div
<div>
  <div>項目 1</div>
  <div>項目 2</div>
</div>
```

## ARIA 屬性

### 基本 ARIA

```jsx
// aria-label: 提供標籤
<button aria-label="關閉對話框">
  <X className="w-4 w-4" />
</button>

// aria-labelledby: 引用標籤元素
<div role="dialog" aria-labelledby="dialog-title">
  <h2 id="dialog-title">確認刪除</h2>
  <p>此操作無法復原</p>
</div>

// aria-describedby: 引用描述元素
<input
  type="email"
  aria-describedby="email-help"
/>
<p id="email-help">我們不會分享您的電子郵件</p>

// aria-hidden: 隱藏裝飾性元素
<Sparkles className="w-4 h-4" aria-hidden="true" />
```

### 狀態與屬性

```jsx
// aria-expanded: 展開/折疊狀態
<button
  aria-expanded={isOpen}
  aria-controls="menu"
  onClick={() => setIsOpen(!isOpen)}
>
  選單
</button>
<div id="menu" hidden={!isOpen}>
  {/* 選單內容 */}
</div>

// aria-selected: 選中狀態
<div role="tablist">
  <button
    role="tab"
    aria-selected={activeTab === 'tab1'}
    aria-controls="panel1"
  >
    Tab 1
  </button>
  <button
    role="tab"
    aria-selected={activeTab === 'tab2'}
    aria-controls="panel2"
  >
    Tab 2
  </button>
</div>

// aria-checked: 勾選狀態
<div
  role="checkbox"
  aria-checked={isChecked}
  tabIndex={0}
  onClick={() => setIsChecked(!isChecked)}
  onKeyDown={(e) => {
    if (e.key === ' ' || e.key === 'Enter') {
      e.preventDefault()
      setIsChecked(!isChecked)
    }
  }}
>
  {isChecked ? <CheckSquare /> : <Square />}
  接受條款
</div>

// aria-disabled: 禁用狀態
<button
  disabled
  aria-disabled="true"
>
  提交
</button>

// aria-invalid: 驗證錯誤
<input
  type="email"
  aria-invalid={hasError}
  aria-describedby="email-error"
/>
{hasError && (
  <p id="email-error" role="alert">
    請輸入有效的電子郵件
  </p>
)}
```

### Live Regions

```jsx
// aria-live: 動態內容更新
<div role="status" aria-live="polite">
  {message}
</div>

// aria-live="assertive": 緊急通知
<div role="alert" aria-live="assertive">
  {errorMessage}
</div>

// aria-atomic: 整體更新
<div role="status" aria-live="polite" aria-atomic="true">
  已保存 {savedCount} 個項目
</div>

// aria-busy: 載入狀態
<div role="status" aria-live="polite" aria-busy={isLoading}>
  {isLoading ? '載入中...' : '載入完成'}
</div>
```

### 自訂組件

```jsx
// 下拉選單
<div role="combobox" aria-expanded={isOpen} aria-haspopup="listbox">
  <input
    type="text"
    aria-autocomplete="list"
    aria-controls="listbox"
    aria-activedescendant={activeOptionId}
  />
  <ul id="listbox" role="listbox">
    {options.map((option) => (
      <li
        key={option.id}
        id={option.id}
        role="option"
        aria-selected={option.id === selectedId}
      >
        {option.label}
      </li>
    ))}
  </ul>
</div>

// 對話框
<div
  role="dialog"
  aria-modal="true"
  aria-labelledby="dialog-title"
  aria-describedby="dialog-description"
>
  <h2 id="dialog-title">對話框標題</h2>
  <p id="dialog-description">對話框描述</p>
  <button onClick={onClose}>關閉</button>
</div>

// 工具提示
<div role="tooltip" id="tooltip">
  提示內容
</div>
<button aria-describedby="tooltip">
  懸停查看提示
</button>
```

## 色彩對比度

### WCAG AA 標準

- **正常文字 (< 18pt)**: 對比度 ≥ 4.5:1
- **大文字 (≥ 18pt 或 14pt 粗體)**: 對比度 ≥ 3:1
- **UI 元件與圖形**: 對比度 ≥ 3:1

### 驗證工具

```bash
# 使用 axe DevTools 檢查對比度
# 1. 安裝 Chrome 擴充套件
# 2. 開啟 DevTools > axe DevTools
# 3. 執行掃描
# 4. 查看 "Color Contrast" 問題
```

### 範例

```css
/* ✅ 正確：足夠對比度 */
.text-primary {
  color: #1f2937;  /* Gray 900 */
  background: #ffffff;  /* White */
  /* 對比度: 16.1:1 */
}

.text-secondary {
  color: #4b5563;  /* Gray 600 */
  background: #ffffff;  /* White */
  /* 對比度: 7.9:1 */
}

/* ❌ 錯誤：對比度不足 */
.text-tertiary {
  color: #d1d5db;  /* Gray 300 */
  background: #ffffff;  /* White */
  /* 對比度: 1.8:1 - 不符合 AA 標準 */
}

/* ✅ 修正：使用更深的顏色 */
.text-tertiary {
  color: #9ca3af;  /* Gray 400 */
  background: #ffffff;  /* White */
  /* 對比度: 2.9:1 - 符合大文字標準 */
}
```

## 表單無障礙

### 標籤與輸入

```jsx
// ✅ 正確：使用 label 元素
<div>
  <label htmlFor="email">電子郵件</label>
  <input
    id="email"
    type="email"
    required
    aria-required="true"
  />
</div>

// ✅ 正確：使用 aria-label
<input
  type="search"
  aria-label="搜尋小工具"
  placeholder="搜尋..."
/>

// ❌ 錯誤：缺少標籤
<input type="email" placeholder="電子郵件" />
```

### 錯誤訊息

```jsx
<div>
  <label htmlFor="password">密碼</label>
  <input
    id="password"
    type="password"
    aria-invalid={hasError}
    aria-describedby={hasError ? 'password-error' : undefined}
  />
  {hasError && (
    <p id="password-error" role="alert" className="text-error-500">
      密碼至少需要 8 個字元
    </p>
  )}
</div>
```

### 必填欄位

```jsx
<div>
  <label htmlFor="name">
    姓名 <span aria-label="必填">*</span>
  </label>
  <input
    id="name"
    type="text"
    required
    aria-required="true"
  />
</div>
```

### 群組與 Fieldset

```jsx
<fieldset>
  <legend>聯絡方式</legend>
  <div>
    <label htmlFor="email">電子郵件</label>
    <input id="email" type="email" />
  </div>
  <div>
    <label htmlFor="phone">電話</label>
    <input id="phone" type="tel" />
  </div>
</fieldset>
```

## 圖片與媒體

### 替代文字

```jsx
// ✅ 正確：有意義的 alt
<img src="chart.png" alt="過去 30 天的成本趨勢圖" />

// ✅ 正確：裝飾性圖片使用空 alt
<img src="decoration.png" alt="" />

// ✅ 正確：使用 aria-hidden
<img src="decoration.png" aria-hidden="true" />

// ❌ 錯誤：缺少 alt
<img src="chart.png" />

// ❌ 錯誤：無意義的 alt
<img src="chart.png" alt="圖片" />
```

### 圖示

```jsx
// ✅ 正確：裝飾性圖示
<button aria-label="關閉">
  <X className="w-4 h-4" aria-hidden="true" />
</button>

// ✅ 正確：有意義的圖示
<button>
  <Plus className="w-4 h-4" aria-hidden="true" />
  <span>新增項目</span>
</button>

// ❌ 錯誤：只有圖示無標籤
<button>
  <X className="w-4 h-4" />
</button>
```

### 影片與音訊

```jsx
// ✅ 正確：提供字幕與文字稿
<video controls>
  <source src="video.mp4" type="video/mp4" />
  <track
    kind="captions"
    src="captions.vtt"
    srclang="zh-TW"
    label="繁體中文"
  />
  <track
    kind="captions"
    src="captions-en.vtt"
    srclang="en"
    label="English"
  />
</video>

// 提供文字稿連結
<a href="/transcript.pdf">查看影片文字稿</a>
```

## 動效無障礙

### prefers-reduced-motion

```css
/* CSS 方式 */
@media (prefers-reduced-motion: reduce) {
  * {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
  }
}
```

```jsx
// React 方式
import { useReducedMotion } from 'framer-motion'

function AnimatedComponent() {
  const prefersReducedMotion = useReducedMotion()

  return (
    <motion.div
      animate={prefersReducedMotion ? {} : {
        scale: [1, 1.1, 1]
      }}
      transition={{
        duration: prefersReducedMotion ? 0 : 0.5
      }}
    >
      {children}
    </motion.div>
  )
}
```

### 避免閃爍

```jsx
// ❌ 錯誤：快速閃爍可能觸發癲癇
<motion.div
  animate={{
    opacity: [1, 0, 1, 0, 1]
  }}
  transition={{
    duration: 0.5,
    repeat: Infinity
  }}
/>

// ✅ 正確：緩慢漸變
<motion.div
  animate={{
    opacity: [1, 0.7, 1]
  }}
  transition={{
    duration: 2,
    repeat: 3
  }}
/>
```

## 螢幕閱讀器

### 隱藏內容

```jsx
// 視覺隱藏但螢幕閱讀器可讀
<span className="sr-only">
  載入中...
</span>

// CSS 實作
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

// 焦點時顯示
.sr-only:focus {
  position: static;
  width: auto;
  height: auto;
  padding: inherit;
  margin: inherit;
  overflow: visible;
  clip: auto;
  white-space: normal;
}
```

### 跳過重複內容

```jsx
<a
  href="#main-content"
  className="sr-only focus:not-sr-only"
>
  跳至主要內容
</a>

<nav aria-label="主導航">
  {/* 導航 */}
</nav>

<main id="main-content">
  {/* 主要內容 */}
</main>
```

## 測試

### 自動化測試

```jsx
// 使用 jest-axe
import { render } from '@testing-library/react'
import { axe, toHaveNoViolations } from 'jest-axe'

expect.extend(toHaveNoViolations)

test('should not have accessibility violations', async () => {
  const { container } = render(<App />)
  const results = await axe(container)
  expect(results).toHaveNoViolations()
})
```

### 手動測試

**鍵盤導航**
1. 使用 Tab 鍵瀏覽所有互動元素
2. 使用 Enter/Space 啟動按鈕與連結
3. 使用方向鍵導航選單與列表
4. 使用 Esc 關閉對話框與選單

**螢幕閱讀器**
1. macOS: VoiceOver (Cmd + F5)
2. Windows: NVDA (免費) 或 JAWS
3. 測試所有主要流程
4. 確認所有內容都能被讀取

**色彩對比度**
1. 使用 axe DevTools 檢查
2. 使用 WebAIM Contrast Checker
3. 測試所有文字與背景組合

**縮放**
1. 放大至 200%
2. 確認內容不會溢出或重疊
3. 確認所有功能仍可用

## 檢查清單

### 開發階段

- [ ] 所有互動元素可用鍵盤訪問
- [ ] 焦點可見且順序合理
- [ ] 使用語義化 HTML
- [ ] 所有圖片有替代文字
- [ ] 表單有標籤與錯誤訊息
- [ ] 色彩對比度符合 WCAG AA
- [ ] 支援 prefers-reduced-motion
- [ ] 動態內容使用 ARIA live regions
- [ ] 自訂組件有適當的 ARIA 屬性

### 測試階段

- [ ] 通過 axe DevTools 掃描
- [ ] 通過鍵盤導航測試
- [ ] 通過螢幕閱讀器測試
- [ ] 通過色彩對比度檢查
- [ ] 通過 200% 縮放測試
- [ ] 通過自動化無障礙測試

### 部署階段

- [ ] Lighthouse 無障礙分數 ≥ 90
- [ ] 無 WCAG AA 違規
- [ ] 文檔包含無障礙說明
- [ ] 提供無障礙反饋管道

## 工具與資源

### 測試工具
- [axe DevTools](https://www.deque.com/axe/devtools/) - 瀏覽器擴充套件
- [Lighthouse](https://developers.google.com/web/tools/lighthouse) - 自動化測試
- [WAVE](https://wave.webaim.org/) - 網頁無障礙評估工具
- [jest-axe](https://github.com/nickcolley/jest-axe) - Jest 測試整合

### 螢幕閱讀器
- [NVDA](https://www.nvaccess.org/) - Windows (免費)
- [JAWS](https://www.freedomscientific.com/products/software/jaws/) - Windows
- [VoiceOver](https://www.apple.com/accessibility/voiceover/) - macOS/iOS (內建)
- [TalkBack](https://support.google.com/accessibility/android/answer/6283677) - Android (內建)

### 參考資源
- [WCAG 2.1 Guidelines](https://www.w3.org/WAI/WCAG21/quickref/)
- [A11y Project](https://www.a11yproject.com/)
- [WebAIM](https://webaim.org/)
- [Inclusive Components](https://inclusive-components.design/)

## 版本歷史

| 版本 | 日期 | 變更內容 | 作者 |
|------|------|----------|------|
| 1.0.0 | 2025-10-20 | 初版建立 | UI/UX 設計團隊 |
