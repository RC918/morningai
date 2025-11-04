# 動效指南

## 概述

動效用於提升用戶體驗、提供視覺反饋、引導注意力。但過度或不當的動效會降低性能、消耗電池、影響無障礙性。本指南確保動效既美觀又高效。

## 動效原則

### 1. 目的性 (Purposeful)
每個動效都應有明確目的：
- **反饋**: 確認用戶操作 (按鈕點擊、表單提交)
- **引導**: 引導用戶注意力 (新增項目、錯誤提示)
- **轉場**: 平滑的頁面/狀態轉換
- **品牌**: 強化品牌識別 (載入動畫、Logo 動效)

### 2. 性能優先 (Performance First)
- 只使用 `transform` 與 `opacity` (避免觸發 layout reflow)
- 避免大半徑模糊 (`blur-3xl`)
- 限制同時運行的動畫數量 (≤ 3 個)
- 只在可見區域播放動畫

### 3. 可控性 (Controllable)
- 支援 `prefers-reduced-motion`
- 避免無限循環動畫
- 提供暫停/停止選項 (如輪播)
- 限制動畫重複次數

### 4. 自然性 (Natural)
- 使用緩動函數 (easing) 模擬物理運動
- 避免線性動畫 (linear)
- 保持動畫時長合理 (150-300ms)

## 動效類型

### 微互動 (Micro-interactions)

**按鈕點擊**
```jsx
<motion.button
  whileHover={{ scale: 1.05 }}
  whileTap={{ scale: 0.95 }}
  transition={{ duration: 0.15, ease: 'easeOut' }}
  className="px-4 py-2 bg-primary-500 text-white rounded-lg"
>
  點擊我
</motion.button>
```

**輸入框焦點**
```jsx
<motion.input
  whileFocus={{
    boxShadow: '0 0 0 3px rgb(59 130 246 / 0.5)',
    borderColor: 'rgb(59 130 246)'
  }}
  transition={{ duration: 0.2, ease: 'easeOut' }}
  className="px-4 py-2 border border-gray-300 rounded-lg"
/>
```

**切換開關**
```jsx
<motion.div
  animate={{ x: isOn ? 20 : 0 }}
  transition={{ type: 'spring', stiffness: 500, damping: 30 }}
  className="w-5 h-5 bg-white rounded-full"
/>
```

### 頁面轉場 (Page Transitions)

**淡入淡出**
```jsx
<motion.div
  initial={{ opacity: 0 }}
  animate={{ opacity: 1 }}
  exit={{ opacity: 0 }}
  transition={{ duration: 0.2, ease: 'easeOut' }}
>
  {children}
</motion.div>
```

**滑入滑出**
```jsx
<motion.div
  initial={{ x: -20, opacity: 0 }}
  animate={{ x: 0, opacity: 1 }}
  exit={{ x: 20, opacity: 0 }}
  transition={{ duration: 0.3, ease: 'easeOut' }}
>
  {children}
</motion.div>
```

**縮放**
```jsx
<motion.div
  initial={{ scale: 0.95, opacity: 0 }}
  animate={{ scale: 1, opacity: 1 }}
  exit={{ scale: 0.95, opacity: 0 }}
  transition={{ duration: 0.2, ease: 'easeOut' }}
>
  {children}
</motion.div>
```

### 列表動畫 (List Animations)

**交錯動畫**
```jsx
<motion.ul
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
    <motion.li
      key={item.id}
      variants={{
        hidden: { opacity: 0, y: 20 },
        visible: { opacity: 1, y: 0 }
      }}
      transition={{ duration: 0.3, ease: 'easeOut' }}
    >
      {item.name}
    </motion.li>
  ))}
</motion.ul>
```

**新增/移除項目**
```jsx
import { AnimatePresence } from 'framer-motion'

<AnimatePresence>
  {items.map((item) => (
    <motion.div
      key={item.id}
      initial={{ opacity: 0, height: 0 }}
      animate={{ opacity: 1, height: 'auto' }}
      exit={{ opacity: 0, height: 0 }}
      transition={{ duration: 0.2, ease: 'easeOut' }}
    >
      {item.name}
    </motion.div>
  ))}
</AnimatePresence>
```

### 載入動畫 (Loading Animations)

**旋轉載入**
```jsx
<motion.div
  animate={{ rotate: 360 }}
  transition={{
    duration: 1,
    repeat: Infinity,
    ease: 'linear'
  }}
  className="w-6 h-6 border-2 border-primary-500 border-t-transparent rounded-full"
/>
```

**脈衝載入**
```jsx
<motion.div
  animate={{
    scale: [1, 1.2, 1],
    opacity: [1, 0.5, 1]
  }}
  transition={{
    duration: 1.5,
    repeat: Infinity,
    ease: 'easeInOut'
  }}
  className="w-3 h-3 bg-primary-500 rounded-full"
/>
```

**骨架屏動畫**
```jsx
<motion.div
  animate={{
    backgroundPosition: ['200% 0', '-200% 0']
  }}
  transition={{
    duration: 2,
    repeat: Infinity,
    ease: 'linear'
  }}
  className="h-4 bg-gradient-to-r from-gray-200 via-gray-300 to-gray-200 bg-[length:200%_100%] rounded"
/>
```

### 通知動畫 (Notification Animations)

**滑入通知**
```jsx
<motion.div
  initial={{ x: 300, opacity: 0 }}
  animate={{ x: 0, opacity: 1 }}
  exit={{ x: 300, opacity: 0 }}
  transition={{ type: 'spring', stiffness: 300, damping: 30 }}
  className="fixed top-4 right-4 p-4 bg-white shadow-lg rounded-lg"
>
  <p>操作成功！</p>
</motion.div>
```

**彈跳通知**
```jsx
<motion.div
  initial={{ scale: 0, opacity: 0 }}
  animate={{ scale: 1, opacity: 1 }}
  exit={{ scale: 0, opacity: 0 }}
  transition={{ type: 'spring', stiffness: 500, damping: 25 }}
  className="fixed top-4 right-4 p-4 bg-success-500 text-white rounded-lg"
>
  <CheckCircle className="w-5 h-5" />
  <p>已保存變更</p>
</motion.div>
```

## 性能優化

### 只在可見時播放

```jsx
import { useInView } from 'framer-motion'

function AnimatedSection({ children }) {
  const ref = useRef(null)
  const isInView = useInView(ref, { once: true, amount: 0.3 })

  return (
    <motion.div
      ref={ref}
      initial={{ opacity: 0, y: 50 }}
      animate={isInView ? { opacity: 1, y: 0 } : {}}
      transition={{ duration: 0.5, ease: 'easeOut' }}
    >
      {children}
    </motion.div>
  )
}
```

### 使用 IntersectionObserver

```jsx
function AnimatedCard({ children }) {
  const [isVisible, setIsVisible] = useState(false)
  const ref = useRef(null)

  useEffect(() => {
    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          setIsVisible(true)
          observer.disconnect()
        }
      },
      { threshold: 0.1 }
    )

    if (ref.current) {
      observer.observe(ref.current)
    }

    return () => observer.disconnect()
  }, [])

  return (
    <motion.div
      ref={ref}
      initial={{ opacity: 0, scale: 0.95 }}
      animate={isVisible ? { opacity: 1, scale: 1 } : {}}
      transition={{ duration: 0.3, ease: 'easeOut' }}
    >
      {children}
    </motion.div>
  )
}
```

### 支援 Reduced Motion

```jsx
import { useReducedMotion } from 'framer-motion'

function AnimatedButton({ children }) {
  const prefersReducedMotion = useReducedMotion()

  return (
    <motion.button
      whileHover={prefersReducedMotion ? {} : { scale: 1.05 }}
      whileTap={prefersReducedMotion ? {} : { scale: 0.95 }}
      transition={{ duration: 0.15, ease: 'easeOut' }}
    >
      {children}
    </motion.button>
  )
}
```

### 避免大半徑模糊

```jsx
// ❌ 錯誤：大半徑模糊消耗大量 GPU
<motion.div
  className="blur-3xl"  // 24px blur
  animate={{
    scale: [1, 1.2, 1],
    opacity: [0.3, 0.5, 0.3]
  }}
  transition={{
    duration: 8,
    repeat: Infinity
  }}
/>

// ✅ 正確：小半徑模糊或無模糊
<motion.div
  className="blur-sm"  // 4px blur
  animate={{
    scale: [1, 1.1, 1],
    opacity: [0.5, 0.7, 0.5]
  }}
  transition={{
    duration: 4,
    repeat: 3  // 限制重複次數
  }}
/>
```

## 動效預算

### 時長限制

| 動效類型 | 建議時長 | 最大時長 |
|---------|---------|---------|
| 微互動 | 150ms | 200ms |
| 頁面轉場 | 200ms | 300ms |
| 列表動畫 | 300ms | 500ms |
| 載入動畫 | 1000ms | 2000ms |

### 數量限制

- 單頁同時運行動畫 ≤ 3 個
- 列表項目交錯延遲 ≤ 100ms
- 無限循環動畫 = 0 個 (禁止)

### 性能指標

- 動畫 FPS ≥ 60
- 動畫期間 CPU 使用率 < 30%
- 動畫期間 GPU 使用率 < 50%

## 緩動函數

### 標準緩動

```js
const easings = {
  // 線性 (避免使用)
  linear: [0, 0, 1, 1],

  // 緩入 (開始慢，結束快)
  easeIn: [0.4, 0, 1, 1],

  // 緩出 (開始快，結束慢) - 推薦
  easeOut: [0, 0, 0.2, 1],

  // 緩入緩出 (開始慢，中間快，結束慢)
  easeInOut: [0.4, 0, 0.2, 1],

  // 彈跳 (適用於通知、對話框)
  bounce: [0.68, -0.55, 0.265, 1.55]
}
```

### 使用建議

| 場景 | 緩動函數 | 原因 |
|------|---------|------|
| 按鈕點擊 | easeOut | 快速反饋 |
| 頁面轉場 | easeOut | 自然流暢 |
| 對話框開啟 | easeOut | 快速出現 |
| 通知彈出 | bounce | 吸引注意 |
| 載入動畫 | linear | 持續旋轉 |

## 無障礙性

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
        scale: [1, 1.1, 1],
        opacity: [0.5, 0.7, 0.5]
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

### 提供控制選項

```jsx
function Carousel({ items }) {
  const [autoPlay, setAutoPlay] = useState(true)
  const prefersReducedMotion = useReducedMotion()

  // 自動停用自動播放
  useEffect(() => {
    if (prefersReducedMotion) {
      setAutoPlay(false)
    }
  }, [prefersReducedMotion])

  return (
    <div>
      <button onClick={() => setAutoPlay(!autoPlay)}>
        {autoPlay ? '暫停' : '播放'}
      </button>
      <AnimatePresence mode="wait">
        {/* 輪播內容 */}
      </AnimatePresence>
    </div>
  )
}
```

## 常見錯誤

### ❌ 無限循環動畫

```jsx
// 錯誤：無限循環消耗資源
<motion.div
  animate={{
    scale: [1, 1.2, 1],
    opacity: [0.3, 0.5, 0.3]
  }}
  transition={{
    duration: 8,
    repeat: Infinity  // ❌ 無限循環
  }}
/>
```

### ❌ 大半徑模糊

```jsx
// 錯誤：大半徑模糊消耗大量 GPU
<motion.div className="blur-3xl">  {/* ❌ 24px blur */}
  {children}
</motion.div>
```

### ❌ 觸發 Layout Reflow

```jsx
// 錯誤：改變 width/height 觸發 reflow
<motion.div
  animate={{
    width: [100, 200, 100],  // ❌ 觸發 reflow
    height: [100, 200, 100]  // ❌ 觸發 reflow
  }}
/>

// 正確：使用 scale
<motion.div
  animate={{
    scale: [1, 2, 1]  // ✅ 只觸發 composite
  }}
/>
```

### ❌ 不支援 Reduced Motion

```jsx
// 錯誤：未檢查 prefers-reduced-motion
<motion.div
  animate={{ scale: [1, 1.2, 1] }}
  transition={{ repeat: Infinity }}
/>

// 正確：支援 reduced motion
const prefersReducedMotion = useReducedMotion()

<motion.div
  animate={prefersReducedMotion ? {} : { scale: [1, 1.2, 1] }}
  transition={{ repeat: prefersReducedMotion ? 0 : 3 }}
/>
```

## 測試

### 性能測試

```js
// 使用 Chrome DevTools Performance
// 1. 開啟 Performance 面板
// 2. 錄製動畫播放
// 3. 檢查 FPS、CPU、GPU 使用率

// 目標：
// - FPS ≥ 60
// - CPU < 30%
// - GPU < 50%
```

### 無障礙測試

```js
// 測試 prefers-reduced-motion
// 1. 開啟系統設定 > 輔助使用 > 顯示 > 減少動態效果
// 2. 重新載入頁面
// 3. 確認動畫已停用或大幅簡化
```

### 視覺回歸測試

```js
// 使用 Playwright 截圖對比
import { test, expect } from '@playwright/test'

test('button hover animation', async ({ page }) => {
  await page.goto('/components/button')
  const button = page.locator('button').first()
  
  // 初始狀態
  await expect(button).toHaveScreenshot('button-initial.png')
  
  // Hover 狀態
  await button.hover()
  await page.waitForTimeout(200)  // 等待動畫完成
  await expect(button).toHaveScreenshot('button-hover.png')
})
```

## 工具與資源

### 開發工具
- [Framer Motion](https://www.framer.com/motion/) - React 動效庫
- [React Spring](https://www.react-spring.dev/) - 物理動畫庫
- [GSAP](https://greensock.com/gsap/) - 高性能動畫庫

### 設計工具
- [Figma Smart Animate](https://help.figma.com/hc/en-us/articles/360039818874-Create-advanced-animations-with-Smart-Animate)
- [Principle](https://principleformac.com/)
- [ProtoPie](https://www.protopie.io/)

### 參考資源
- [Material Motion](https://material.io/design/motion/)
- [Apple Human Interface Guidelines - Motion](https://developer.apple.com/design/human-interface-guidelines/motion)
- [Web Animation API](https://developer.mozilla.org/en-US/docs/Web/API/Web_Animations_API)

## 版本歷史

| 版本 | 日期 | 變更內容 | 作者 |
|------|------|----------|------|
| 1.0.0 | 2025-10-20 | 初版建立 | UI/UX 設計團隊 |
