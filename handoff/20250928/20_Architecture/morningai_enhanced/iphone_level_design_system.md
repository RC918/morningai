# Morning AI iPhone 級 UI/UX 設計系統

## 🎨 設計哲學

### 核心原則
**簡潔至上 (Simplicity First)**
- 每個界面專注於單一核心任務
- 移除一切不必要的視覺噪音
- 通過留白創造呼吸感和層次

**直觀交互 (Intuitive Interaction)**
- 符合用戶既有認知模型
- 一致的手勢和交互模式
- 即時的視覺反饋

**精緻細節 (Refined Details)**
- 像素級精確度
- 流暢的 60fps 動畫
- 高品質的視覺質感

## 🎯 色彩系統 (Color System)

### 主色調 (Primary Colors)
```json
{
  "primary": {
    "50": "#f0f9ff",
    "100": "#e0f2fe", 
    "200": "#bae6fd",
    "300": "#7dd3fc",
    "400": "#38bdf8",
    "500": "#0ea5e9",  // 主品牌色
    "600": "#0284c7",
    "700": "#0369a1",
    "800": "#075985",
    "900": "#0c4a6e"
  }
}
```

### 中性色 (Neutral Colors)
```json
{
  "neutral": {
    "0": "#ffffff",     // 純白
    "50": "#fafafa",    // 背景色
    "100": "#f5f5f5",   // 卡片背景
    "200": "#e5e5e5",   // 分隔線
    "300": "#d4d4d4",   // 邊框
    "400": "#a3a3a3",   // 輔助文字
    "500": "#737373",   // 次要文字
    "600": "#525252",   // 主要文字
    "700": "#404040",   // 標題
    "800": "#262626",   // 深色標題
    "900": "#171717",   // 最深文字
    "950": "#0a0a0a"    // 純黑
  }
}
```

### 語義色彩 (Semantic Colors)
```json
{
  "success": "#10b981",   // 成功綠
  "warning": "#f59e0b",   // 警告橙
  "error": "#ef4444",     // 錯誤紅
  "info": "#3b82f6"       // 信息藍
}
```

### 深色模式 (Dark Mode)
```json
{
  "dark": {
    "background": "#0a0a0a",
    "surface": "#171717",
    "card": "#262626",
    "border": "#404040",
    "text-primary": "#fafafa",
    "text-secondary": "#a3a3a3"
  }
}
```

## ✍️ 字體系統 (Typography)

### 字體族 (Font Family)
```css
/* 主要字體 - 西文 */
font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Helvetica Neue', Arial, sans-serif;

/* 中文字體 */
font-family: -apple-system, BlinkMacSystemFont, 'PingFang SC', 'Hiragino Sans GB', 'Microsoft YaHei', sans-serif;
```

### 字體尺寸階層 (Type Scale)
```json
{
  "typography": {
    "display-large": {
      "size": "57px",
      "lineHeight": "64px",
      "weight": 700,
      "letterSpacing": "-0.25px"
    },
    "display-medium": {
      "size": "45px", 
      "lineHeight": "52px",
      "weight": 700,
      "letterSpacing": "0px"
    },
    "display-small": {
      "size": "36px",
      "lineHeight": "44px", 
      "weight": 600,
      "letterSpacing": "0px"
    },
    "headline-large": {
      "size": "32px",
      "lineHeight": "40px",
      "weight": 600,
      "letterSpacing": "0px"
    },
    "headline-medium": {
      "size": "28px",
      "lineHeight": "36px",
      "weight": 600,
      "letterSpacing": "0px"
    },
    "headline-small": {
      "size": "24px",
      "lineHeight": "32px",
      "weight": 600,
      "letterSpacing": "0px"
    },
    "title-large": {
      "size": "22px",
      "lineHeight": "28px",
      "weight": 500,
      "letterSpacing": "0px"
    },
    "title-medium": {
      "size": "16px",
      "lineHeight": "24px",
      "weight": 500,
      "letterSpacing": "0.15px"
    },
    "title-small": {
      "size": "14px",
      "lineHeight": "20px",
      "weight": 500,
      "letterSpacing": "0.1px"
    },
    "body-large": {
      "size": "16px",
      "lineHeight": "24px",
      "weight": 400,
      "letterSpacing": "0.5px"
    },
    "body-medium": {
      "size": "14px",
      "lineHeight": "20px",
      "weight": 400,
      "letterSpacing": "0.25px"
    },
    "body-small": {
      "size": "12px",
      "lineHeight": "16px",
      "weight": 400,
      "letterSpacing": "0.4px"
    },
    "label-large": {
      "size": "14px",
      "lineHeight": "20px",
      "weight": 500,
      "letterSpacing": "0.1px"
    },
    "label-medium": {
      "size": "12px",
      "lineHeight": "16px",
      "weight": 500,
      "letterSpacing": "0.5px"
    },
    "label-small": {
      "size": "11px",
      "lineHeight": "16px",
      "weight": 500,
      "letterSpacing": "0.5px"
    }
  }
}
```

## 📐 間距系統 (Spacing System)

### 基礎間距 (Base Spacing)
```json
{
  "spacing": {
    "0": "0px",
    "1": "4px",      // 0.25rem
    "2": "8px",      // 0.5rem  
    "3": "12px",     // 0.75rem
    "4": "16px",     // 1rem - 基礎單位
    "5": "20px",     // 1.25rem
    "6": "24px",     // 1.5rem
    "8": "32px",     // 2rem
    "10": "40px",    // 2.5rem
    "12": "48px",    // 3rem
    "16": "64px",    // 4rem
    "20": "80px",    // 5rem
    "24": "96px",    // 6rem
    "32": "128px",   // 8rem
    "40": "160px",   // 10rem
    "48": "192px",   // 12rem
    "56": "224px",   // 14rem
    "64": "256px"    // 16rem
  }
}
```

### 語義間距 (Semantic Spacing)
```json
{
  "semantic-spacing": {
    "component-padding": "16px",      // 組件內邊距
    "section-gap": "48px",           // 區塊間距
    "container-padding": "24px",      // 容器邊距
    "card-padding": "20px",          // 卡片內邊距
    "button-padding": "12px 20px",   // 按鈕內邊距
    "input-padding": "12px 16px",    // 輸入框內邊距
    "nav-height": "64px",            // 導航欄高度
    "sidebar-width": "280px"         // 側邊欄寬度
  }
}
```

## 🎭 組件系統 (Component System)

### 按鈕 (Buttons)
```json
{
  "button": {
    "primary": {
      "background": "#0ea5e9",
      "color": "#ffffff",
      "border": "none",
      "borderRadius": "8px",
      "padding": "12px 20px",
      "fontSize": "14px",
      "fontWeight": 500,
      "transition": "all 150ms ease",
      "states": {
        "hover": {
          "background": "#0284c7",
          "transform": "translateY(-1px)",
          "boxShadow": "0 4px 12px rgba(14, 165, 233, 0.3)"
        },
        "active": {
          "background": "#0369a1",
          "transform": "translateY(0px)"
        },
        "disabled": {
          "background": "#d4d4d4",
          "color": "#a3a3a3",
          "cursor": "not-allowed"
        }
      }
    },
    "secondary": {
      "background": "transparent",
      "color": "#0ea5e9", 
      "border": "1px solid #0ea5e9",
      "borderRadius": "8px",
      "padding": "12px 20px",
      "fontSize": "14px",
      "fontWeight": 500,
      "transition": "all 150ms ease",
      "states": {
        "hover": {
          "background": "#f0f9ff",
          "borderColor": "#0284c7"
        }
      }
    }
  }
}
```

### 輸入框 (Input Fields)
```json
{
  "input": {
    "default": {
      "background": "#ffffff",
      "border": "1px solid #d4d4d4",
      "borderRadius": "8px",
      "padding": "12px 16px",
      "fontSize": "14px",
      "transition": "all 150ms ease",
      "states": {
        "focus": {
          "borderColor": "#0ea5e9",
          "boxShadow": "0 0 0 3px rgba(14, 165, 233, 0.1)"
        },
        "error": {
          "borderColor": "#ef4444",
          "boxShadow": "0 0 0 3px rgba(239, 68, 68, 0.1)"
        }
      }
    }
  }
}
```

### 卡片 (Cards)
```json
{
  "card": {
    "default": {
      "background": "#ffffff",
      "border": "1px solid #e5e5e5",
      "borderRadius": "12px",
      "padding": "20px",
      "boxShadow": "0 1px 3px rgba(0, 0, 0, 0.1)",
      "transition": "all 200ms ease",
      "states": {
        "hover": {
          "boxShadow": "0 4px 12px rgba(0, 0, 0, 0.15)",
          "transform": "translateY(-2px)"
        }
      }
    }
  }
}
```

## 🎬 動效系統 (Motion System)

### 動畫時長 (Duration)
```json
{
  "duration": {
    "instant": "0ms",
    "fast": "150ms",      // 快速交互
    "normal": "200ms",    // 標準動畫
    "slow": "300ms",      // 複雜動畫
    "slower": "500ms"     // 頁面轉場
  }
}
```

### 緩動函數 (Easing)
```json
{
  "easing": {
    "linear": "linear",
    "ease": "ease",
    "ease-in": "cubic-bezier(0.4, 0, 1, 1)",
    "ease-out": "cubic-bezier(0, 0, 0.2, 1)",
    "ease-in-out": "cubic-bezier(0.4, 0, 0.2, 1)",
    "spring": "cubic-bezier(0.175, 0.885, 0.32, 1.275)"
  }
}
```

### 常用動畫 (Common Animations)
```css
/* 淡入淡出 */
@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

/* 滑入效果 */
@keyframes slideUp {
  from { 
    opacity: 0;
    transform: translateY(20px);
  }
  to { 
    opacity: 1;
    transform: translateY(0);
  }
}

/* 縮放效果 */
@keyframes scaleIn {
  from { 
    opacity: 0;
    transform: scale(0.95);
  }
  to { 
    opacity: 1;
    transform: scale(1);
  }
}

/* 彈性效果 */
@keyframes bounce {
  0%, 20%, 53%, 80%, 100% {
    transform: translate3d(0,0,0);
  }
  40%, 43% {
    transform: translate3d(0, -8px, 0);
  }
  70% {
    transform: translate3d(0, -4px, 0);
  }
  90% {
    transform: translate3d(0, -2px, 0);
  }
}
```

## 📱 響應式設計 (Responsive Design)

### 斷點系統 (Breakpoints)
```json
{
  "breakpoints": {
    "xs": "320px",    // iPhone SE
    "sm": "375px",    // iPhone 13 mini
    "md": "768px",    // iPad mini
    "lg": "1024px",   // iPad Pro
    "xl": "1280px",   // Desktop
    "2xl": "1536px"   // Large Desktop
  }
}
```

### 響應式規則 (Responsive Rules)
```css
/* 移動端優先 */
.container {
  padding: 16px;
  max-width: 100%;
}

/* 平板 */
@media (min-width: 768px) {
  .container {
    padding: 24px;
    max-width: 768px;
    margin: 0 auto;
  }
}

/* 桌面端 */
@media (min-width: 1024px) {
  .container {
    padding: 32px;
    max-width: 1200px;
  }
}
```

## ♿ 無障礙設計 (Accessibility)

### 色彩對比 (Color Contrast)
- 正常文字：至少 4.5:1 對比度
- 大文字：至少 3:1 對比度
- 非文字元素：至少 3:1 對比度

### 焦點指示 (Focus Indicators)
```css
.focusable:focus {
  outline: 2px solid #0ea5e9;
  outline-offset: 2px;
  border-radius: 4px;
}
```

### 語義化標記 (Semantic Markup)
- 使用適當的 HTML 語義標籤
- 提供 alt 文字和 aria-label
- 確保鍵盤導航順序合理

## 🌍 國際化支援 (Internationalization)

### 支援語言
- 繁體中文 (zh-TW)
- 簡體中文 (zh-CN)  
- 英文 (en-US)

### 文字方向支援
- 從左到右 (LTR)
- 從右到左 (RTL) - 預留支援

這套設計系統將確保 Morning AI 達到 iPhone 級別的用戶體驗品質！

