# iOS Shadow System - Apple-Level UI/UX

## 概述

Shadow System 實現了 Apple Human Interface Guidelines 中的精細陰影系統，為 UI 元素提供深度感和層次感。使用 5 級陰影系統，從最輕微的提升效果到最明顯的浮動效果。

## 5 級精細陰影

### Level 1: Subtle Lift (微妙提升)
**最輕微的陰影效果**

```css
box-shadow: 0 1px 2px 0 rgb(0 0 0 / 0.04);
```

**適用場景**:
- 卡片的輕微分離
- 按鈕的默認狀態
- 輸入框
- 列表項

**視覺效果**: 幾乎不可見，僅提供最基本的深度暗示

**範例**:
```jsx
<div className="shadow-sm p-4 bg-white rounded-lg">
  <p>輕微提升的卡片</p>
</div>
```

### Level 2: Light Elevation (輕度提升)
**輕度陰影效果**

```css
box-shadow: 0 2px 4px 0 rgb(0 0 0 / 0.06);
```

**適用場景**:
- 次要卡片
- 下拉菜單
- 工具提示
- 小型彈出層

**視覺效果**: 清晰可見但不突兀，適合大多數 UI 元素

**範例**:
```jsx
<div className="shadow-md p-4 bg-white rounded-lg">
  <h3>次要卡片</h3>
  <p>輕度提升效果</p>
</div>
```

### Level 3: Medium Elevation (中度提升)
**標準陰影效果（推薦）**

```css
box-shadow: 0 4px 8px 0 rgb(0 0 0 / 0.08);
```

**適用場景**:
- 主要卡片
- 導航欄
- 側邊欄
- 內容面板
- 大多數互動元素

**視覺效果**: 明顯的深度感，是最常用的陰影級別

**範例**:
```jsx
<div className="shadow-lg p-6 bg-white rounded-xl">
  <h2>主要內容卡片</h2>
  <p>這是最常用的陰影效果</p>
</div>
```

### Level 4: High Elevation (高度提升)
**重度陰影效果**

```css
box-shadow: 0 8px 16px 0 rgb(0 0 0 / 0.10);
```

**適用場景**:
- 模態對話框
- 彈出式面板
- 浮動操作按鈕 (FAB)
- 重要通知

**視覺效果**: 強烈的浮動感，元素明顯脫離背景

**範例**:
```jsx
<div className="shadow-xl p-8 bg-white rounded-2xl">
  <h2>重要對話框</h2>
  <p>高度提升的浮動效果</p>
</div>
```

### Level 5: Maximum Elevation (最大提升)
**最強陰影效果**

```css
box-shadow: 0 16px 32px 0 rgb(0 0 0 / 0.12);
```

**適用場景**:
- 全屏模態
- 關鍵操作確認
- 拖拽中的元素
- 需要最高視覺優先級的元素

**視覺效果**: 極強的浮動感，元素完全脫離頁面

**範例**:
```jsx
<div className="shadow-2xl p-10 bg-white rounded-3xl">
  <h1>關鍵操作</h1>
  <p>最大提升效果</p>
</div>
```

## CSS 工具類

### Tailwind-style 類名
```css
.shadow-sm   /* Level 1: 0 1px 2px */
.shadow-md   /* Level 2: 0 2px 4px */
.shadow-lg   /* Level 3: 0 4px 8px */
.shadow-xl   /* Level 4: 0 8px 16px */
.shadow-2xl  /* Level 5: 0 16px 32px */
```

### Material-style 類名
```css
.material-shadow-1  /* Level 1 */
.material-shadow-2  /* Level 2 */
.material-shadow-3  /* Level 3 */
.material-shadow-4  /* Level 4 */
.material-shadow-5  /* Level 5 */
```

## 陰影與材質組合

將陰影與材質系統結合使用，創造更豐富的深度效果：

```jsx
// 材質 + 陰影 = 毛玻璃浮動效果
<div className="material-regular shadow-lg p-6 rounded-xl">
  <h3>毛玻璃卡片</h3>
  <p>結合材質和陰影</p>
</div>
```

## 動態陰影

### Hover 效果
```css
.hover-shadow {
  transition: box-shadow 0.3s ease;
}

.hover-shadow:hover {
  box-shadow: 0 12px 24px 0 rgb(0 0 0 / 0.12);
}
```

**範例**:
```jsx
<button className="shadow-md hover:shadow-xl transition-shadow duration-300">
  懸停查看效果
</button>
```

### 按下效果
```css
.active-shadow:active {
  box-shadow: 0 2px 4px 0 rgb(0 0 0 / 0.06);
}
```

**範例**:
```jsx
<button className="shadow-lg active:shadow-md transition-shadow">
  點擊查看效果
</button>
```

### 拖拽效果
```jsx
// 使用 Framer Motion
<motion.div
  drag
  whileDrag={{ boxShadow: '0 16px 32px 0 rgb(0 0 0 / 0.12)' }}
  className="shadow-lg"
>
  拖拽我
</motion.div>
```

## 深色模式

陰影在深色模式下需要調整以保持視覺效果：

```css
/* Light Mode */
.shadow-lg {
  box-shadow: 0 4px 8px 0 rgb(0 0 0 / 0.08);
}

/* Dark Mode - 增加不透明度 */
.dark .shadow-lg {
  box-shadow: 0 4px 8px 0 rgb(0 0 0 / 0.24);
}
```

**深色模式陰影原則**:
- 不透明度提高 2-3 倍
- 保持相同的偏移和模糊半徑
- 考慮使用彩色陰影增強效果

## 彩色陰影

為特定情感色彩添加彩色陰影：

```css
/* Joy - 橙色陰影 */
.shadow-joy {
  box-shadow: 0 4px 12px 0 rgba(255, 149, 0, 0.3);
}

/* Calm - 藍色陰影 */
.shadow-calm {
  box-shadow: 0 4px 12px 0 rgba(90, 200, 250, 0.3);
}

/* Energy - 紅色陰影 */
.shadow-energy {
  box-shadow: 0 4px 12px 0 rgba(255, 59, 48, 0.3);
}

/* Growth - 綠色陰影 */
.shadow-growth {
  box-shadow: 0 4px 12px 0 rgba(52, 199, 89, 0.3);
}

/* Wisdom - 紫色陰影 */
.shadow-wisdom {
  box-shadow: 0 4px 12px 0 rgba(88, 86, 214, 0.3);
}
```

**範例**:
```jsx
<button className="bg-joy text-white shadow-joy px-6 py-3 rounded-lg">
  成功按鈕
</button>
```

## 內陰影 (Inset Shadows)

用於創造凹陷效果：

```css
.shadow-inset {
  box-shadow: inset 0 2px 4px 0 rgb(0 0 0 / 0.06);
}
```

**適用場景**:
- 輸入框（聚焦狀態）
- 按下的按鈕
- 凹陷的面板

**範例**:
```jsx
<input 
  className="shadow-inset focus:shadow-md transition-shadow" 
  placeholder="輸入文字"
/>
```

## 多層陰影

組合多個陰影創造更複雜的效果：

```css
.shadow-layered {
  box-shadow: 
    0 1px 2px 0 rgb(0 0 0 / 0.04),
    0 4px 8px 0 rgb(0 0 0 / 0.06),
    0 8px 16px 0 rgb(0 0 0 / 0.08);
}
```

**範例**:
```jsx
<div className="shadow-layered p-6 bg-white rounded-xl">
  <h3>多層陰影卡片</h3>
  <p>更豐富的深度效果</p>
</div>
```

## 性能優化

### 1. 避免過度使用
```jsx
// ❌ 不好 - 太多陰影影響性能
<div className="shadow-2xl">
  <div className="shadow-xl">
    <div className="shadow-lg">
      內容
    </div>
  </div>
</div>

// ✅ 好 - 只在需要的地方使用
<div className="shadow-lg">
  內容
</div>
```

### 2. 使用 transform 代替 box-shadow 動畫
```css
/* ❌ 不好 - 動畫 box-shadow 性能差 */
.card {
  transition: box-shadow 0.3s;
}
.card:hover {
  box-shadow: 0 12px 24px 0 rgb(0 0 0 / 0.12);
}

/* ✅ 好 - 使用 transform 提升性能 */
.card {
  box-shadow: 0 4px 8px 0 rgb(0 0 0 / 0.08);
  transition: transform 0.3s;
}
.card:hover {
  transform: translateY(-2px);
}
```

### 3. 使用 will-change
```css
.card-animated {
  will-change: box-shadow;
}
```

## 設計原則

### 1. 層次感
使用不同級別的陰影創建視覺層次：
- 背景: 無陰影或 Level 1
- 內容: Level 2-3
- 浮動元素: Level 4-5

### 2. 一致性
相同層級的元素使用相同陰影：
```jsx
// ✅ 所有卡片使用相同陰影
<div className="grid grid-cols-3 gap-4">
  <div className="shadow-lg">卡片 1</div>
  <div className="shadow-lg">卡片 2</div>
  <div className="shadow-lg">卡片 3</div>
</div>
```

### 3. 漸進式
陰影應該隨著交互逐漸增強：
```jsx
<button className="shadow-md hover:shadow-lg active:shadow-md">
  按鈕
</button>
```

## 實際應用範例

### 卡片系統
```jsx
// 基礎卡片
<div className="shadow-md p-4 bg-white rounded-lg">
  <p>基礎內容</p>
</div>

// 重要卡片
<div className="shadow-lg p-6 bg-white rounded-xl">
  <h3>重要內容</h3>
</div>

// 浮動卡片
<div className="shadow-xl p-8 bg-white rounded-2xl">
  <h2>浮動內容</h2>
</div>
```

### 按鈕系統
```jsx
// 主要按鈕
<button className="bg-primary text-white shadow-md hover:shadow-lg active:shadow-sm px-6 py-3 rounded-lg transition-shadow">
  主要操作
</button>

// 次要按鈕
<button className="bg-gray-200 shadow-sm hover:shadow-md active:shadow-sm px-6 py-3 rounded-lg transition-shadow">
  次要操作
</button>

// 浮動操作按鈕 (FAB)
<button className="fixed bottom-8 right-8 w-14 h-14 bg-primary text-white shadow-xl hover:shadow-2xl rounded-full transition-shadow">
  +
</button>
```

### 模態對話框
```jsx
<div className="fixed inset-0 z-50 flex items-center justify-center">
  {/* 背景遮罩 */}
  <div className="absolute inset-0 bg-black/40" />
  
  {/* 對話框 */}
  <div className="shadow-2xl bg-white rounded-2xl p-8 max-w-md relative z-10">
    <h2 className="text-2xl font-bold mb-4">確認操作</h2>
    <p className="text-gray-600 mb-6">此操作無法撤銷</p>
    <div className="flex gap-3">
      <button className="flex-1 shadow-sm hover:shadow-md">取消</button>
      <button className="flex-1 shadow-md hover:shadow-lg">確認</button>
    </div>
  </div>
</div>
```

### 導航欄
```jsx
<nav className="sticky top-0 z-50 bg-white shadow-md">
  <div className="container mx-auto px-4 py-3">
    <div className="flex items-center justify-between">
      <h1 className="text-xl font-bold">MorningAI</h1>
      <div className="flex gap-4">
        <a href="#" className="hover:text-primary">Dashboard</a>
        <a href="#" className="hover:text-primary">Analytics</a>
      </div>
    </div>
  </div>
</nav>
```

### 下拉菜單
```jsx
<div className="relative">
  <button className="shadow-sm hover:shadow-md px-4 py-2 rounded-lg">
    選單
  </button>
  
  <div className="absolute top-full mt-2 shadow-xl bg-white rounded-lg py-2 min-w-[200px]">
    <a href="#" className="block px-4 py-2 hover:bg-gray-100">選項 1</a>
    <a href="#" className="block px-4 py-2 hover:bg-gray-100">選項 2</a>
    <a href="#" className="block px-4 py-2 hover:bg-gray-100">選項 3</a>
  </div>
</div>
```

## 測試檢查清單

- [ ] 所有陰影在 Light Mode 下正常顯示
- [ ] 所有陰影在 Dark Mode 下正常顯示且對比度足夠
- [ ] 陰影不會影響頁面性能（60fps）
- [ ] Hover/Active 狀態的陰影過渡流暢
- [ ] 陰影與其他設計系統元素（色彩、材質）協調
- [ ] 不同層級的元素使用適當的陰影級別
- [ ] 陰影在不同背景色上都清晰可見

## 相關資源

- [Apple Human Interface Guidelines - Depth](https://developer.apple.com/design/human-interface-guidelines/depth)
- [Material Design - Elevation](https://m3.material.io/styles/elevation/overview)
- [CSS box-shadow - MDN](https://developer.mozilla.org/en-US/docs/Web/CSS/box-shadow)
- [Box Shadow Generator](https://cssgenerator.org/box-shadow-css-generator.html)
