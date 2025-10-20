# 設計 Token 規範

## 概述

設計 Token 是設計系統的基礎，定義了色彩、字體、間距、陰影等基本元素。Token 確保視覺一致性，並簡化設計與開發之間的溝通。

## Token 架構

### 作用域策略

為避免全域樣式污染，所有 Token 應使用作用域限制：

```css
/* ❌ 錯誤：全域污染 */
@layer base {
  * {
    border-color: rgb(var(--apple-gray-200));
  }
}

/* ✅ 正確：作用域限制 */
.theme-apple {
  --border-color: rgb(var(--apple-gray-200));
  --font-family: var(--apple-font-sans);
}
```

### 與 Tailwind 整合

Token 應與 Tailwind CSS 配置整合，避免雙源維護：

```js
// tailwind.config.js
export default {
  theme: {
    extend: {
      colors: {
        apple: {
          blue: {
            500: 'rgb(var(--apple-blue-500) / <alpha-value>)'
          }
        }
      }
    }
  }
}
```

## 色彩系統

### 主色調

```css
:root {
  /* Primary - Blue */
  --color-primary-50: 239 246 255;
  --color-primary-100: 219 234 254;
  --color-primary-200: 191 219 254;
  --color-primary-300: 147 197 253;
  --color-primary-400: 96 165 250;
  --color-primary-500: 59 130 246;   /* 主色 */
  --color-primary-600: 37 99 235;
  --color-primary-700: 29 78 216;
  --color-primary-800: 30 64 175;
  --color-primary-900: 30 58 138;

  /* Secondary - Purple */
  --color-secondary-500: 168 85 247;
  --color-secondary-600: 147 51 234;

  /* Success - Green */
  --color-success-500: 34 197 94;
  --color-success-600: 22 163 74;

  /* Warning - Yellow */
  --color-warning-500: 234 179 8;
  --color-warning-600: 202 138 4;

  /* Error - Red */
  --color-error-500: 239 68 68;
  --color-error-600: 220 38 38;
}
```

### 中性色

```css
:root {
  /* Gray Scale */
  --color-gray-50: 249 250 251;
  --color-gray-100: 243 244 246;
  --color-gray-200: 229 231 235;
  --color-gray-300: 209 213 219;
  --color-gray-400: 156 163 175;
  --color-gray-500: 107 114 128;
  --color-gray-600: 75 85 99;
  --color-gray-700: 55 65 81;
  --color-gray-800: 31 41 55;
  --color-gray-900: 17 24 39;
}
```

### 語義色

```css
:root {
  /* Text Colors */
  --color-text-primary: var(--color-gray-900);
  --color-text-secondary: var(--color-gray-600);
  --color-text-tertiary: var(--color-gray-400);
  --color-text-inverse: 255 255 255;

  /* Background Colors */
  --color-bg-primary: 255 255 255;
  --color-bg-secondary: var(--color-gray-50);
  --color-bg-tertiary: var(--color-gray-100);

  /* Border Colors */
  --color-border-primary: var(--color-gray-200);
  --color-border-secondary: var(--color-gray-300);
}
```

### 深色模式

```css
.dark {
  /* Text Colors */
  --color-text-primary: 255 255 255;
  --color-text-secondary: var(--color-gray-400);
  --color-text-tertiary: var(--color-gray-600);
  --color-text-inverse: var(--color-gray-900);

  /* Background Colors */
  --color-bg-primary: var(--color-gray-900);
  --color-bg-secondary: var(--color-gray-800);
  --color-bg-tertiary: var(--color-gray-700);

  /* Border Colors */
  --color-border-primary: var(--color-gray-700);
  --color-border-secondary: var(--color-gray-600);
}
```

### 色彩對比度

所有色彩組合必須符合 WCAG 2.1 AA 標準：

- 正常文字：對比度 ≥ 4.5:1
- 大文字 (18pt+)：對比度 ≥ 3:1
- UI 元件：對比度 ≥ 3:1

**驗證工具**
- [WebAIM Contrast Checker](https://webaim.org/resources/contrastchecker/)
- [Stark Figma Plugin](https://www.getstark.co/)

## 字體系統

### 字體家族

```css
:root {
  /* Sans-serif (主要) */
  --font-sans: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 
               'Helvetica Neue', Arial, sans-serif;

  /* Monospace (代碼) */
  --font-mono: 'SF Mono', 'Monaco', 'Inconsolata', 'Fira Code', 
               'Droid Sans Mono', 'Source Code Pro', monospace;
}
```

### 字體大小

```css
:root {
  /* Font Sizes */
  --text-xs: 0.75rem;      /* 12px */
  --text-sm: 0.875rem;     /* 14px */
  --text-base: 1rem;       /* 16px */
  --text-lg: 1.125rem;     /* 18px */
  --text-xl: 1.25rem;      /* 20px */
  --text-2xl: 1.5rem;      /* 24px */
  --text-3xl: 1.875rem;    /* 30px */
  --text-4xl: 2.25rem;     /* 36px */
  --text-5xl: 3rem;        /* 48px */
  --text-6xl: 3.75rem;     /* 60px */
}
```

### 字重

```css
:root {
  --font-light: 300;
  --font-normal: 400;
  --font-medium: 500;
  --font-semibold: 600;
  --font-bold: 700;
}
```

### 行高

```css
:root {
  --leading-none: 1;
  --leading-tight: 1.25;
  --leading-snug: 1.375;
  --leading-normal: 1.5;
  --leading-relaxed: 1.625;
  --leading-loose: 2;
}
```

### 字距

```css
:root {
  --tracking-tighter: -0.05em;
  --tracking-tight: -0.025em;
  --tracking-normal: 0;
  --tracking-wide: 0.025em;
  --tracking-wider: 0.05em;
  --tracking-widest: 0.1em;
}
```

## 間距系統

### 基礎間距

使用 4px 基礎單位 (0.25rem)：

```css
:root {
  --spacing-0: 0;
  --spacing-1: 0.25rem;    /* 4px */
  --spacing-2: 0.5rem;     /* 8px */
  --spacing-3: 0.75rem;    /* 12px */
  --spacing-4: 1rem;       /* 16px */
  --spacing-5: 1.25rem;    /* 20px */
  --spacing-6: 1.5rem;     /* 24px */
  --spacing-8: 2rem;       /* 32px */
  --spacing-10: 2.5rem;    /* 40px */
  --spacing-12: 3rem;      /* 48px */
  --spacing-16: 4rem;      /* 64px */
  --spacing-20: 5rem;      /* 80px */
  --spacing-24: 6rem;      /* 96px */
}
```

### 語義間距

```css
:root {
  /* Component Spacing */
  --spacing-component-xs: var(--spacing-2);   /* 8px */
  --spacing-component-sm: var(--spacing-3);   /* 12px */
  --spacing-component-md: var(--spacing-4);   /* 16px */
  --spacing-component-lg: var(--spacing-6);   /* 24px */
  --spacing-component-xl: var(--spacing-8);   /* 32px */

  /* Layout Spacing */
  --spacing-layout-xs: var(--spacing-4);      /* 16px */
  --spacing-layout-sm: var(--spacing-6);      /* 24px */
  --spacing-layout-md: var(--spacing-8);      /* 32px */
  --spacing-layout-lg: var(--spacing-12);     /* 48px */
  --spacing-layout-xl: var(--spacing-16);     /* 64px */
}
```

## 圓角系統

```css
:root {
  --radius-none: 0;
  --radius-sm: 0.125rem;   /* 2px */
  --radius-base: 0.25rem;  /* 4px */
  --radius-md: 0.375rem;   /* 6px */
  --radius-lg: 0.5rem;     /* 8px */
  --radius-xl: 0.75rem;    /* 12px */
  --radius-2xl: 1rem;      /* 16px */
  --radius-full: 9999px;   /* 完全圓形 */
}
```

## 陰影系統

```css
:root {
  /* Elevation Shadows */
  --shadow-xs: 0 1px 2px 0 rgb(0 0 0 / 0.05);
  --shadow-sm: 0 1px 3px 0 rgb(0 0 0 / 0.1), 0 1px 2px -1px rgb(0 0 0 / 0.1);
  --shadow-md: 0 4px 6px -1px rgb(0 0 0 / 0.1), 0 2px 4px -2px rgb(0 0 0 / 0.1);
  --shadow-lg: 0 10px 15px -3px rgb(0 0 0 / 0.1), 0 4px 6px -4px rgb(0 0 0 / 0.1);
  --shadow-xl: 0 20px 25px -5px rgb(0 0 0 / 0.1), 0 8px 10px -6px rgb(0 0 0 / 0.1);
  --shadow-2xl: 0 25px 50px -12px rgb(0 0 0 / 0.25);

  /* Inner Shadow */
  --shadow-inner: inset 0 2px 4px 0 rgb(0 0 0 / 0.05);

  /* Focus Ring */
  --shadow-focus: 0 0 0 3px rgb(59 130 246 / 0.5);
}
```

## 動效 Token

### 持續時間

```css
:root {
  --duration-instant: 0ms;
  --duration-fast: 150ms;
  --duration-base: 200ms;
  --duration-slow: 300ms;
  --duration-slower: 500ms;
}
```

### 緩動函數

```css
:root {
  --ease-linear: linear;
  --ease-in: cubic-bezier(0.4, 0, 1, 1);
  --ease-out: cubic-bezier(0, 0, 0.2, 1);
  --ease-in-out: cubic-bezier(0.4, 0, 0.2, 1);
  --ease-bounce: cubic-bezier(0.68, -0.55, 0.265, 1.55);
}
```

## 斷點系統

```css
:root {
  --breakpoint-sm: 640px;    /* 手機橫向 */
  --breakpoint-md: 768px;    /* 平板直向 */
  --breakpoint-lg: 1024px;   /* 平板橫向 / 小筆電 */
  --breakpoint-xl: 1280px;   /* 桌面 */
  --breakpoint-2xl: 1536px;  /* 大螢幕 */
}
```

## Z-Index 系統

```css
:root {
  --z-base: 0;
  --z-dropdown: 1000;
  --z-sticky: 1100;
  --z-fixed: 1200;
  --z-modal-backdrop: 1300;
  --z-modal: 1400;
  --z-popover: 1500;
  --z-tooltip: 1600;
  --z-notification: 1700;
}
```

## 使用範例

### CSS 變數

```css
.button {
  background-color: rgb(var(--color-primary-500));
  color: rgb(var(--color-text-inverse));
  padding: var(--spacing-3) var(--spacing-6);
  border-radius: var(--radius-lg);
  font-size: var(--text-base);
  font-weight: var(--font-medium);
  box-shadow: var(--shadow-sm);
  transition: all var(--duration-base) var(--ease-out);
}

.button:hover {
  background-color: rgb(var(--color-primary-600));
  box-shadow: var(--shadow-md);
}
```

### Tailwind 類別

```jsx
<button className="bg-primary-500 text-white px-6 py-3 rounded-lg text-base font-medium shadow-sm hover:bg-primary-600 hover:shadow-md transition-all duration-200 ease-out">
  按鈕
</button>
```

## Token 管理

### 命名規範

```
--{category}-{property}-{variant}

範例：
--color-text-primary
--spacing-component-md
--shadow-focus
```

### 版本控制

Token 變更應遵循語義化版本：

- **Major (1.0.0 → 2.0.0)**: 破壞性變更 (移除 Token、重命名)
- **Minor (1.0.0 → 1.1.0)**: 新增 Token
- **Patch (1.0.0 → 1.0.1)**: 修正 Token 值

### 文檔更新

每次 Token 變更都應更新：
1. 本文檔
2. Figma 設計檔
3. Storybook 範例
4. 變更日誌

## 工具與資源

### 設計工具
- [Figma Tokens Plugin](https://www.figma.com/community/plugin/843461159747178978/Figma-Tokens)
- [Style Dictionary](https://amzn.github.io/style-dictionary/)

### 開發工具
- [Tailwind CSS](https://tailwindcss.com/)
- [CSS Variables](https://developer.mozilla.org/en-US/docs/Web/CSS/Using_CSS_custom_properties)

## 版本歷史

| 版本 | 日期 | 變更內容 | 作者 |
|------|------|----------|------|
| 1.0.0 | 2025-10-20 | 初版建立 | UI/UX 設計團隊 |
