# iOS Material System - Apple-Level UI/UX

## 概述

Material System 實現了 Apple Human Interface Guidelines 中的毛玻璃效果（Frosted Glass / Vibrancy），為 UI 元素提供深度感和層次感。

## 5 種 iOS 材質

### 1. Ultra Thin Material
**最輕的模糊效果**

```css
.material-ultra-thin {
  background-color: rgba(255, 255, 255, 0.5);
  backdrop-filter: blur(10px) saturate(150%);
}
```

**適用場景**:
- 輕量級浮層
- 臨時提示
- 非關鍵信息

**範例**:
```jsx
<div className="material-ultra-thin p-4 rounded-lg">
  <p>輕量級提示信息</p>
</div>
```

### 2. Thin Material
**輕度模糊效果**

```css
.material-thin {
  background-color: rgba(255, 255, 255, 0.6);
  backdrop-filter: blur(15px) saturate(160%);
}
```

**適用場景**:
- 次要卡片
- 輔助面板
- 背景層

**範例**:
```jsx
<div className="material-thin p-6 rounded-xl">
  <h3>次要內容</h3>
</div>
```

### 3. Regular Material
**標準模糊效果（推薦）**

```css
.material-regular {
  background-color: rgba(255, 255, 255, 0.7);
  backdrop-filter: blur(20px) saturate(180%);
}
```

**適用場景**:
- 主要卡片
- 內容面板
- 對話框
- 大多數 UI 元素

**範例**:
```jsx
<div className="material-regular p-6 rounded-xl shadow-lg">
  <h2>主要內容卡片</h2>
  <p>這是最常用的材質效果</p>
</div>
```

### 4. Thick Material
**重度模糊效果**

```css
.material-thick {
  background-color: rgba(255, 255, 255, 0.8);
  backdrop-filter: blur(30px) saturate(200%);
}
```

**適用場景**:
- 重要面板
- 模態對話框
- 需要強調的內容

**範例**:
```jsx
<div className="material-thick p-8 rounded-2xl shadow-2xl">
  <h2>重要通知</h2>
  <p>需要用戶注意的內容</p>
</div>
```

### 5. Chrome Material
**最強模糊效果**

```css
.material-chrome {
  background-color: rgba(255, 255, 255, 0.9);
  backdrop-filter: blur(40px) saturate(220%);
}
```

**適用場景**:
- 導航欄
- 工具欄
- 固定頭部
- 需要最高可讀性的元素

**範例**:
```jsx
<nav className="material-chrome border-b border-gray-200">
  <div className="container mx-auto px-4 py-3">
    <h1>應用標題</h1>
  </div>
</nav>
```

## 預製組件類

### Material Card
```jsx
<div className="material-card p-6">
  <h3 className="text-lg font-semibold mb-2">卡片標題</h3>
  <p className="text-gray-600">卡片內容</p>
</div>
```

### Material Navbar
```jsx
<nav className="material-navbar sticky top-0 z-50">
  <div className="container mx-auto px-4 py-3">
    {/* 導航內容 */}
  </div>
</nav>
```

### Material Sidebar
```jsx
<aside className="material-sidebar w-64 h-screen">
  {/* 側邊欄內容 */}
</aside>
```

### Material Popover
```jsx
<div className="material-popover rounded-xl p-4">
  <p>彈出層內容</p>
</div>
```

### Material Overlay
```jsx
<div className="material-overlay fixed inset-0 z-40">
  {/* 模態背景 */}
</div>
```

## 材質陰影系統

配合材質使用的 5 級陰影系統：

```css
.material-shadow-1  /* 0 1px 2px - 最輕 */
.material-shadow-2  /* 0 2px 4px */
.material-shadow-3  /* 0 4px 8px - 標準 */
.material-shadow-4  /* 0 8px 16px */
.material-shadow-5  /* 0 16px 32px - 最重 */
```

**組合使用**:
```jsx
<div className="material-regular material-shadow-3 p-6 rounded-xl">
  <p>帶陰影的材質卡片</p>
</div>
```

## 工具類

### Backdrop Blur
```css
.backdrop-blur-sm   /* blur(10px) */
.backdrop-blur-md   /* blur(20px) */
.backdrop-blur-lg   /* blur(30px) */
.backdrop-blur-xl   /* blur(40px) */
```

### Backdrop Effects
```css
.backdrop-saturate        /* saturate(180%) */
.backdrop-brightness      /* brightness(1.1) */
.backdrop-glass           /* blur + saturate */
.backdrop-glass-vibrant   /* blur + saturate + brightness */
```

## 深色模式

所有材質自動支持深色模式：

```css
/* Light Mode */
.material-regular {
  background-color: rgba(255, 255, 255, 0.7);
}

/* Dark Mode */
.dark .material-regular {
  background-color: rgba(0, 0, 0, 0.7);
}
```

## 瀏覽器兼容性

### 支持 backdrop-filter
- Safari 9+
- Chrome 76+
- Edge 79+
- Firefox 103+

### Fallback 處理
```css
@supports not (backdrop-filter: blur(20px)) {
  .material-regular {
    background-color: rgba(255, 255, 255, 0.95);
  }
}
```

不支持 `backdrop-filter` 的瀏覽器會使用更不透明的背景色作為降級方案。

## 性能優化

### 1. 避免過度使用
```jsx
// ❌ 不好 - 嵌套太多材質
<div className="material-regular">
  <div className="material-thin">
    <div className="material-ultra-thin">
      內容
    </div>
  </div>
</div>

// ✅ 好 - 只在需要的地方使用
<div className="material-regular">
  內容
</div>
```

### 2. 使用 will-change
```css
.material-animated {
  will-change: backdrop-filter;
}
```

### 3. 減少動畫材質
```jsx
// ❌ 避免在動畫元素上使用材質
<motion.div className="material-regular" animate={{ x: 100 }}>
  內容
</motion.div>

// ✅ 使用固定材質，動畫內部元素
<div className="material-regular">
  <motion.div animate={{ x: 100 }}>
    內容
  </motion.div>
</div>
```

## 設計原則

### 1. 層次感
使用不同強度的材質創建視覺層次：
- 背景: Ultra Thin / Thin
- 內容: Regular
- 強調: Thick / Chrome

### 2. 對比度
確保材質上的文字有足夠對比度：
- Light Mode: 深色文字 (#1F2937)
- Dark Mode: 淺色文字 (#F9FAFB)

### 3. 一致性
在相同層級的元素使用相同材質：
```jsx
// ✅ 所有卡片使用相同材質
<div className="grid grid-cols-3 gap-4">
  <div className="material-regular">卡片 1</div>
  <div className="material-regular">卡片 2</div>
  <div className="material-regular">卡片 3</div>
</div>
```

## 實際應用範例

### Dashboard 卡片
```jsx
<div className="material-card material-shadow-3 p-6">
  <div className="flex items-center justify-between mb-4">
    <h3 className="text-lg font-semibold">總收入</h3>
    <TrendingUpIcon className="text-growth" />
  </div>
  <p className="text-3xl font-bold">$12,345</p>
  <p className="text-sm text-gray-500 mt-2">+12.5% 較上月</p>
</div>
```

### 模態對話框
```jsx
<div className="fixed inset-0 z-50 flex items-center justify-center">
  {/* 背景遮罩 */}
  <div className="material-overlay absolute inset-0" />
  
  {/* 對話框 */}
  <div className="material-thick material-shadow-5 rounded-2xl p-8 max-w-md relative z-10">
    <h2 className="text-2xl font-bold mb-4">確認操作</h2>
    <p className="text-gray-600 mb-6">此操作無法撤銷，確定要繼續嗎？</p>
    <div className="flex gap-3">
      <button className="flex-1 bg-gray-200 hover:bg-gray-300 px-4 py-2 rounded-lg">
        取消
      </button>
      <button className="flex-1 bg-energy text-white px-4 py-2 rounded-lg">
        確認
      </button>
    </div>
  </div>
</div>
```

### 固定導航欄
```jsx
<nav className="material-navbar sticky top-0 z-50">
  <div className="container mx-auto px-4 py-3 flex items-center justify-between">
    <div className="flex items-center gap-8">
      <h1 className="text-xl font-bold">MorningAI</h1>
      <nav className="flex gap-6">
        <a href="#" className="text-gray-700 hover:text-primary">Dashboard</a>
        <a href="#" className="text-gray-700 hover:text-primary">Analytics</a>
        <a href="#" className="text-gray-700 hover:text-primary">Settings</a>
      </nav>
    </div>
    <button className="bg-primary text-white px-4 py-2 rounded-lg">
      升級 Pro
    </button>
  </div>
</nav>
```

## 測試檢查清單

- [ ] 所有材質在 Light Mode 下正常顯示
- [ ] 所有材質在 Dark Mode 下正常顯示
- [ ] 材質上的文字有足夠對比度
- [ ] 不支持 backdrop-filter 的瀏覽器有合理降級
- [ ] 材質不會影響頁面性能（60fps）
- [ ] 材質與其他設計系統元素（色彩、陰影）協調

## 相關資源

- [Apple Human Interface Guidelines - Materials](https://developer.apple.com/design/human-interface-guidelines/materials)
- [CSS backdrop-filter - MDN](https://developer.mozilla.org/en-US/docs/Web/CSS/backdrop-filter)
- [Can I Use - backdrop-filter](https://caniuse.com/css-backdrop-filter)
