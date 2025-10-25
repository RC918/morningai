# iOS Spacing System - Apple-Level UI/UX

## 概述

Spacing System 實現了 Apple Human Interface Guidelines 中的精細間距系統，為 UI 元素提供一致的空間節奏和視覺呼吸感。使用 8 級間距系統，從最緊湊的 4px 到最寬鬆的 96px。

## 8 級間距系統

### XS (Extra Small) - 4px (0.25rem)
**最小間距單位**

```css
gap: 0.25rem;
padding: 0.25rem;
margin: 0.25rem;
```

**適用場景**:
- 圖標與文字之間的緊密間距
- 標籤內部的微小間距
- 按鈕內圖標與文字的間距
- 緊湊列表項的內部間距

**範例**:
```jsx
<button className="flex items-center gap-1">
  <Icon />
  <span>按鈕</span>
</button>
```

### SM (Small) - 8px (0.5rem)
**緊湊間距**

```css
gap: 0.5rem;
padding: 0.5rem;
margin: 0.5rem;
```

**適用場景**:
- 表單元素之間的間距
- 卡片內部的小間距
- 列表項之間的緊密間距
- 按鈕組內的間距

**範例**:
```jsx
<div className="space-y-2">
  <input type="text" />
  <input type="email" />
</div>
```

### MD (Medium) - 16px (1rem)
**標準間距（推薦）**

```css
gap: 1rem;
padding: 1rem;
margin: 1rem;
```

**適用場景**:
- 卡片內容的標準間距
- 段落之間的間距
- 表單組之間的間距
- 大多數 UI 元素的默認間距

**視覺效果**: 舒適的視覺呼吸感，是最常用的間距

**範例**:
```jsx
<div className="space-y-4 p-4">
  <h2>標題</h2>
  <p>內容段落</p>
  <button>操作</button>
</div>
```

### LG (Large) - 24px (1.5rem)
**寬鬆間距**

```css
gap: 1.5rem;
padding: 1.5rem;
margin: 1.5rem;
```

**適用場景**:
- 區塊之間的間距
- 卡片之間的間距
- 主要內容區域的內邊距
- 導航欄的內邊距

**範例**:
```jsx
<div className="space-y-6 p-6">
  <section>區塊 1</section>
  <section>區塊 2</section>
</div>
```

### XL (Extra Large) - 32px (2rem)
**大間距**

```css
gap: 2rem;
padding: 2rem;
margin: 2rem;
```

**適用場景**:
- 頁面主要區域之間的間距
- 大型卡片的內邊距
- 頁面頂部/底部的間距
- 重要內容的分隔

**範例**:
```jsx
<div className="space-y-8 p-8">
  <header>頁面頭部</header>
  <main>主要內容</main>
  <footer>頁面底部</footer>
</div>
```

### 2XL (2X Extra Large) - 48px (3rem)
**超大間距**

```css
gap: 3rem;
padding: 3rem;
margin: 3rem;
```

**適用場景**:
- 頁面級別的大間距
- Hero 區域的內邊距
- 主要內容區域之間的分隔
- 大型布局的間距

**範例**:
```jsx
<div className="py-12">
  <div className="container mx-auto space-y-12">
    <section>Hero</section>
    <section>Features</section>
  </div>
</div>
```

### 3XL (3X Extra Large) - 64px (4rem)
**巨大間距**

```css
gap: 4rem;
padding: 4rem;
margin: 4rem;
```

**適用場景**:
- Landing Page 的大區域間距
- 全屏布局的內邊距
- 重要內容的強調分隔
- 視覺衝擊力強的布局

**範例**:
```jsx
<div className="py-16">
  <div className="container mx-auto space-y-16">
    <section>大區域 1</section>
    <section>大區域 2</section>
  </div>
</div>
```

### 4XL (4X Extra Large) - 96px (6rem)
**最大間距**

```css
gap: 6rem;
padding: 6rem;
margin: 6rem;
```

**適用場景**:
- Landing Page 的頂級區域間距
- 全屏展示的內邊距
- 極強視覺分隔
- 特殊布局需求

**範例**:
```jsx
<div className="py-24">
  <div className="container mx-auto space-y-24">
    <section>頂級區域 1</section>
    <section>頂級區域 2</section>
  </div>
</div>
```

## Tailwind CSS 工具類

### Padding (內邊距)
```css
.p-1   /* 4px - 所有方向 */
.p-2   /* 8px */
.p-4   /* 16px */
.p-6   /* 24px */
.p-8   /* 32px */
.p-12  /* 48px */
.p-16  /* 64px */
.p-24  /* 96px */

/* 單方向 */
.pt-4  /* padding-top: 16px */
.pr-4  /* padding-right: 16px */
.pb-4  /* padding-bottom: 16px */
.pl-4  /* padding-left: 16px */

/* 水平/垂直 */
.px-4  /* padding-left + padding-right: 16px */
.py-4  /* padding-top + padding-bottom: 16px */
```

### Margin (外邊距)
```css
.m-1   /* 4px - 所有方向 */
.m-2   /* 8px */
.m-4   /* 16px */
.m-6   /* 24px */
.m-8   /* 32px */
.m-12  /* 48px */
.m-16  /* 64px */
.m-24  /* 96px */

/* 單方向 */
.mt-4  /* margin-top: 16px */
.mr-4  /* margin-right: 16px */
.mb-4  /* margin-bottom: 16px */
.ml-4  /* margin-left: 16px */

/* 水平/垂直 */
.mx-4  /* margin-left + margin-right: 16px */
.my-4  /* margin-top + margin-bottom: 16px */

/* 自動居中 */
.mx-auto  /* margin-left: auto; margin-right: auto */
```

### Gap (Flexbox/Grid 間距)
```css
.gap-1   /* 4px */
.gap-2   /* 8px */
.gap-4   /* 16px */
.gap-6   /* 24px */
.gap-8   /* 32px */
.gap-12  /* 48px */
.gap-16  /* 64px */
.gap-24  /* 96px */

/* 單方向 */
.gap-x-4  /* column-gap: 16px */
.gap-y-4  /* row-gap: 16px */
```

### Space Between (子元素間距)
```css
.space-x-1 > * + *  /* margin-left: 4px */
.space-x-2 > * + *  /* margin-left: 8px */
.space-x-4 > * + *  /* margin-left: 16px */

.space-y-1 > * + *  /* margin-top: 4px */
.space-y-2 > * + *  /* margin-top: 8px */
.space-y-4 > * + *  /* margin-top: 16px */
```

## 設計原則

### 1. 8px 基礎網格
所有間距都基於 8px 的倍數（除了 4px 的微調）：
- 4px (0.5x) - 微調
- 8px (1x) - 基礎單位
- 16px (2x) - 標準間距
- 24px (3x) - 寬鬆間距
- 32px (4x) - 大間距
- 48px (6x) - 超大間距
- 64px (8x) - 巨大間距
- 96px (12x) - 最大間距

### 2. 視覺層次
使用不同間距創建視覺層次：
```jsx
// 緊密相關的元素 - 小間距
<div className="space-y-1">
  <h3>標題</h3>
  <p className="text-sm text-gray-500">副標題</p>
</div>

// 相關的內容組 - 中等間距
<div className="space-y-4">
  <div>內容組 1</div>
  <div>內容組 2</div>
</div>

// 不同區塊 - 大間距
<div className="space-y-8">
  <section>區塊 1</section>
  <section>區塊 2</section>
</div>
```

### 3. 一致性
相同層級的元素使用相同間距：
```jsx
// ✅ 好 - 所有卡片使用相同間距
<div className="grid grid-cols-3 gap-6">
  <div className="p-6">卡片 1</div>
  <div className="p-6">卡片 2</div>
  <div className="p-6">卡片 3</div>
</div>

// ❌ 不好 - 間距不一致
<div className="grid grid-cols-3 gap-6">
  <div className="p-4">卡片 1</div>
  <div className="p-6">卡片 2</div>
  <div className="p-8">卡片 3</div>
</div>
```

### 4. 響應式間距
根據螢幕尺寸調整間距：
```jsx
<div className="p-4 md:p-6 lg:p-8">
  {/* 小螢幕: 16px, 中螢幕: 24px, 大螢幕: 32px */}
  內容
</div>

<div className="space-y-4 md:space-y-6 lg:space-y-8">
  <section>區塊 1</section>
  <section>區塊 2</section>
</div>
```

## 實際應用範例

### 卡片系統
```jsx
// 緊湊卡片
<div className="p-4 space-y-2">
  <h3 className="font-semibold">標題</h3>
  <p className="text-sm">內容</p>
</div>

// 標準卡片
<div className="p-6 space-y-4">
  <h3 className="text-lg font-semibold">標題</h3>
  <p>內容段落</p>
  <button>操作</button>
</div>

// 大型卡片
<div className="p-8 space-y-6">
  <h2 className="text-2xl font-bold">大標題</h2>
  <p className="text-lg">內容段落</p>
  <div className="flex gap-4">
    <button>主要操作</button>
    <button>次要操作</button>
  </div>
</div>
```

### 表單系統
```jsx
<form className="space-y-6">
  {/* 表單組 */}
  <div className="space-y-2">
    <label className="block font-medium">姓名</label>
    <input type="text" className="w-full px-4 py-2" />
  </div>
  
  <div className="space-y-2">
    <label className="block font-medium">電子郵件</label>
    <input type="email" className="w-full px-4 py-2" />
  </div>
  
  {/* 按鈕組 */}
  <div className="flex gap-4 pt-4">
    <button className="px-6 py-3">提交</button>
    <button className="px-6 py-3">取消</button>
  </div>
</form>
```

### 導航欄
```jsx
<nav className="px-6 py-4">
  <div className="flex items-center justify-between">
    <div className="flex items-center gap-8">
      <h1 className="text-xl font-bold">Logo</h1>
      <div className="flex gap-6">
        <a href="#">連結 1</a>
        <a href="#">連結 2</a>
        <a href="#">連結 3</a>
      </div>
    </div>
    <button className="px-4 py-2">登入</button>
  </div>
</nav>
```

### Dashboard 布局
```jsx
<div className="min-h-screen bg-gray-50">
  {/* 導航欄 */}
  <nav className="bg-white shadow-md px-6 py-4">
    <div className="container mx-auto">導航內容</div>
  </nav>
  
  {/* 主要內容 */}
  <main className="container mx-auto py-8 px-6">
    {/* 統計卡片 */}
    <div className="grid grid-cols-3 gap-6 mb-8">
      <div className="bg-white p-6 rounded-xl shadow-md">
        <h3 className="text-sm font-semibold text-gray-600 mb-2">總用戶</h3>
        <p className="text-3xl font-bold">1,234</p>
      </div>
      <div className="bg-white p-6 rounded-xl shadow-md">
        <h3 className="text-sm font-semibold text-gray-600 mb-2">活躍用戶</h3>
        <p className="text-3xl font-bold">856</p>
      </div>
      <div className="bg-white p-6 rounded-xl shadow-md">
        <h3 className="text-sm font-semibold text-gray-600 mb-2">轉換率</h3>
        <p className="text-3xl font-bold">3.2%</p>
      </div>
    </div>
    
    {/* 主要內容區域 */}
    <div className="bg-white rounded-xl shadow-lg p-8">
      <h2 className="text-2xl font-bold mb-6">最近活動</h2>
      <div className="space-y-4">
        <div className="flex items-center gap-4 p-4 rounded-lg hover:bg-gray-50">
          <div className="w-12 h-12 rounded-full bg-blue-500" />
          <div className="flex-1">
            <p className="font-medium">用戶操作 1</p>
            <p className="text-sm text-gray-500">2 分鐘前</p>
          </div>
        </div>
      </div>
    </div>
  </main>
</div>
```

### 模態對話框
```jsx
<div className="fixed inset-0 z-50 flex items-center justify-center p-6">
  {/* 背景遮罩 */}
  <div className="absolute inset-0 bg-black/40" />
  
  {/* 對話框 */}
  <div className="bg-white rounded-2xl p-8 max-w-md relative z-10 shadow-2xl">
    <h2 className="text-2xl font-bold mb-4">確認操作</h2>
    <p className="text-gray-600 mb-6">此操作無法撤銷，確定要繼續嗎？</p>
    <div className="flex gap-4">
      <button className="flex-1 px-6 py-3 bg-gray-200 rounded-lg">取消</button>
      <button className="flex-1 px-6 py-3 bg-red-600 text-white rounded-lg">確認</button>
    </div>
  </div>
</div>
```

## 負間距 (Negative Spacing)

用於重疊效果或緊湊布局：

```css
.-m-1   /* -4px */
.-m-2   /* -8px */
.-m-4   /* -16px */
.-mt-4  /* margin-top: -16px */
```

**適用場景**:
- 頭像重疊
- 標籤重疊
- 特殊視覺效果

**範例**:
```jsx
// 頭像組重疊
<div className="flex">
  <img className="w-10 h-10 rounded-full" />
  <img className="w-10 h-10 rounded-full -ml-2" />
  <img className="w-10 h-10 rounded-full -ml-2" />
</div>
```

## 容器間距

### Container Padding
```jsx
// 小螢幕: 16px, 大螢幕: 24px
<div className="container mx-auto px-4 lg:px-6">
  內容
</div>

// 響應式容器
<div className="container mx-auto px-4 sm:px-6 lg:px-8">
  內容
</div>
```

### Section Spacing
```jsx
// 標準區塊間距
<section className="py-12">
  <div className="container mx-auto">內容</div>
</section>

// 大型區塊間距
<section className="py-16 lg:py-24">
  <div className="container mx-auto">內容</div>
</section>
```

## 性能優化

### 1. 避免過度嵌套
```jsx
// ❌ 不好 - 過度嵌套
<div className="p-8">
  <div className="p-6">
    <div className="p-4">
      內容
    </div>
  </div>
</div>

// ✅ 好 - 扁平結構
<div className="p-8">
  內容
</div>
```

### 2. 使用 Space Utilities
```jsx
// ❌ 不好 - 每個元素都設置 margin
<div>
  <div className="mb-4">項目 1</div>
  <div className="mb-4">項目 2</div>
  <div className="mb-4">項目 3</div>
</div>

// ✅ 好 - 使用 space-y
<div className="space-y-4">
  <div>項目 1</div>
  <div>項目 2</div>
  <div>項目 3</div>
</div>
```

### 3. 使用 Gap 代替 Margin
```jsx
// ❌ 不好 - 使用 margin
<div className="flex">
  <div className="mr-4">項目 1</div>
  <div className="mr-4">項目 2</div>
  <div>項目 3</div>
</div>

// ✅ 好 - 使用 gap
<div className="flex gap-4">
  <div>項目 1</div>
  <div>項目 2</div>
  <div>項目 3</div>
</div>
```

## 測試檢查清單

- [ ] 所有間距都基於 8px 網格（除了 4px 微調）
- [ ] 相同層級的元素使用一致的間距
- [ ] 響應式間距在不同螢幕尺寸下正常工作
- [ ] 間距不會導致內容溢出或重疊
- [ ] 使用 space-y/space-x 或 gap 而非手動設置每個 margin
- [ ] 負間距使用得當，不會造成視覺混亂
- [ ] 容器內邊距在不同設備上都舒適

## 相關資源

- [Apple Human Interface Guidelines - Layout](https://developer.apple.com/design/human-interface-guidelines/layout)
- [Tailwind CSS - Spacing](https://tailwindcss.com/docs/customizing-spacing)
- [8-Point Grid System](https://spec.fm/specifics/8-pt-grid)
- [Material Design - Spacing](https://m3.material.io/foundations/layout/understanding-layout/spacing)
