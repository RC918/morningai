# 色彩系統指南

## 概述

MorningAI 的色彩系統遵循 Apple Human Interface Guidelines，確保所有色彩使用符合 WCAG AA 無障礙標準。

## 主色系統

### iOS 藍色系統

我們使用兩種藍色，分別用於不同場景：

#### 1. `--color-primary` (#007AFF) - 互動元素專用

**用途**: 按鈕、圖標、背景、圖表線條等視覺元素

**對比度**: 4.02:1（白底）

**✅ 正確使用**:
```css
/* 按鈕背景 */
.button-primary {
  background-color: var(--color-primary);
  color: white;
}

/* 圖標顏色 */
.icon-primary {
  color: var(--color-primary);
}

/* 圖表線條 */
<Line stroke="#007AFF" />
```

**❌ 錯誤使用**:
```css
/* 不要用於文字 - 對比度不足 */
.text-link {
  color: var(--color-primary); /* ❌ 4.02:1, fails WCAG AA */
}
```

#### 2. `--color-primary-text` (#0051D0) - 文字專用

**用途**: 文字、鏈接、focus ring 等需要高對比度的元素

**對比度**: 6.12:1（白底）✅ WCAG AA 合格

**✅ 正確使用**:
```css
/* 文字鏈接 */
.text-link {
  color: var(--color-primary-text);
}

/* Focus ring */
*:focus-visible {
  outline: 2px solid var(--color-primary-text);
}

/* 主要文字 */
.text-primary {
  color: var(--color-primary-text);
}
```

## 情感色彩系統

### iOS 風格情感色彩

用於傳達特定情緒和狀態，遵循 Apple Human Interface Guidelines：

| 色彩 | 色碼 (Light) | 色碼 (Dark) | 用途 | 情感 | 對比度 |
|------|-------------|------------|------|------|--------|
| **Joy** | #FF9500 | #FFB340 | 慶祝、成功、獎勵 | 快樂、興奮 | 3.8:1 ✅ |
| **Calm** | #5AC8FA | #7DD8FC | 信息、提示、平靜狀態 | 平靜、信任 | 2.9:1 ⚠️ |
| **Energy** | #FF3B30 | #FF6B63 | 警告、緊急、重要 | 活力、緊迫 | 4.5:1 ✅ |
| **Growth** | #34C759 | #5FD87F | 成長、進步、成功 | 成長、健康 | 3.5:1 ✅ |
| **Wisdom** | #5856D6 | #7B79E8 | 洞察、智慧、高級功能 | 智慧、深度 | 5.2:1 ✅ |

**注意**: Calm 色彩僅用於圖標和背景，不用於文字（對比度不足）。

### 使用範例

#### React 組件
```jsx
// 成功通知 - Joy
<Toast className="bg-joy text-white">
  🎉 操作成功！
</Toast>

// 信息提示 - Calm
<Alert className="bg-calm-10 border-calm text-gray-900">
  💡 這是一條提示信息
</Alert>

// 緊急警告 - Energy
<Banner className="bg-energy text-white">
  ⚠️ 需要立即處理
</Banner>

// 進度指示 - Growth
<ProgressBar className="bg-growth" value={75} />

// 高級功能 - Wisdom
<Badge className="bg-wisdom text-white">Pro</Badge>
```

#### CSS 工具類
```css
/* 背景色 */
.bg-joy { background-color: #FF9500; }
.bg-calm { background-color: #5AC8FA; }
.bg-energy { background-color: #FF3B30; }
.bg-growth { background-color: #34C759; }
.bg-wisdom { background-color: #5856D6; }

/* 文字色 */
.text-joy { color: #FF9500; }
.text-calm { color: #5AC8FA; }
.text-energy { color: #FF3B30; }
.text-growth { color: #34C759; }
.text-wisdom { color: #5856D6; }

/* 邊框色 */
.border-joy { border-color: #FF9500; }
.border-calm { border-color: #5AC8FA; }
.border-energy { border-color: #FF3B30; }
.border-growth { border-color: #34C759; }
.border-wisdom { border-color: #5856D6; }

/* 漸層背景 */
.bg-gradient-joy { background: linear-gradient(135deg, #FF9500 0%, #FFB340 100%); }
.bg-gradient-calm { background: linear-gradient(135deg, #5AC8FA 0%, #7DD8FC 100%); }
.bg-gradient-energy { background: linear-gradient(135deg, #FF3B30 0%, #FF6B63 100%); }
.bg-gradient-growth { background: linear-gradient(135deg, #34C759 0%, #5FD87F 100%); }
.bg-gradient-wisdom { background: linear-gradient(135deg, #5856D6 0%, #7B79E8 100%); }

/* 透明背景 (10%, 20%) */
.bg-joy-10 { background-color: rgba(255, 149, 0, 0.1); }
.bg-joy-20 { background-color: rgba(255, 149, 0, 0.2); }
.bg-calm-10 { background-color: rgba(90, 200, 250, 0.1); }
.bg-calm-20 { background-color: rgba(90, 200, 250, 0.2); }
/* ... 其他透明度變體 */
```

### 情感色彩使用指南

#### Joy (#FF9500) - 慶祝與成功
**適用場景**:
- ✅ 成功通知
- ✅ 獎勵徽章
- ✅ 成就解鎖
- ✅ 慶祝動畫
- ✅ 正向反饋

**範例**:
```jsx
<div className="bg-joy-10 border-l-4 border-joy p-4 rounded-lg">
  <h4 className="text-joy font-semibold">恭喜！</h4>
  <p className="text-gray-700">您已完成所有任務</p>
</div>
```

#### Calm (#5AC8FA) - 信息與平靜
**適用場景**:
- ✅ 信息提示
- ✅ 幫助文檔
- ✅ 引導流程
- ✅ 平靜狀態指示
- ⚠️ 不用於文字（對比度不足）

**範例**:
```jsx
<div className="bg-calm-10 border-calm border p-4 rounded-lg">
  <div className="flex items-center gap-2">
    <InfoIcon className="text-calm" />
    <p className="text-gray-900">這是一條提示信息</p>
  </div>
</div>
```

#### Energy (#FF3B30) - 緊急與重要
**適用場景**:
- ✅ 緊急警告
- ✅ 錯誤提示
- ✅ 危險操作確認
- ✅ 重要通知
- ✅ 倒計時

**範例**:
```jsx
<div className="bg-energy text-white p-4 rounded-lg shadow-lg">
  <h4 className="font-semibold">⚠️ 緊急通知</h4>
  <p>系統將在 5 分鐘後維護</p>
  <button className="mt-2 bg-white text-energy px-4 py-2 rounded-md">
    了解詳情
  </button>
</div>
```

#### Growth (#34C759) - 成長與進步
**適用場景**:
- ✅ 進度條
- ✅ 成長指標
- ✅ 健康狀態
- ✅ 正向趨勢
- ✅ 完成狀態

**範例**:
```jsx
<div className="space-y-2">
  <div className="flex justify-between text-sm">
    <span className="text-gray-700">完成度</span>
    <span className="text-growth font-semibold">75%</span>
  </div>
  <div className="h-2 bg-gray-200 rounded-full overflow-hidden">
    <div className="h-full bg-growth" style={{ width: '75%' }} />
  </div>
</div>
```

#### Wisdom (#5856D6) - 智慧與深度
**適用場景**:
- ✅ Pro 功能
- ✅ 高級設置
- ✅ AI 功能
- ✅ 洞察報告
- ✅ 專家模式

**範例**:
```jsx
<div className="bg-gradient-wisdom text-white p-6 rounded-xl shadow-xl">
  <div className="flex items-center gap-2 mb-2">
    <SparklesIcon className="w-5 h-5" />
    <span className="text-sm font-semibold uppercase tracking-wide">Pro</span>
  </div>
  <h3 className="text-xl font-bold mb-2">AI 智能分析</h3>
  <p className="text-white/90">解鎖高級洞察功能</p>
</div>
```

## 語義色彩

### Success（成功）
- **主色**: #16a34a (success-600)
- **對比度**: 4.54:1 ✅ WCAG AA
- **用途**: 成功狀態、完成操作、正向反饋

### Warning（警告）
- **主色**: #d97706 (warning-600)
- **對比度**: 4.52:1 ✅ WCAG AA
- **用途**: 警告信息、需要注意的狀態

### Error（錯誤）
- **主色**: #dc2626 (error-600)
- **對比度**: 5.93:1 ✅ WCAG AA
- **用途**: 錯誤狀態、失敗操作、危險操作

## 中性色系統

### Gray Scale（灰階）

| 級別 | 色碼 | 用途 |
|------|------|------|
| gray-50 | #f9fafb | 背景、卡片 |
| gray-100 | #f3f4f6 | 次要背景 |
| gray-200 | #e5e7eb | 邊框、分隔線 |
| gray-300 | #d1d5db | 禁用狀態 |
| gray-400 | #9ca3af | 占位符文字 |
| gray-500 | #6b7280 | 次要文字 |
| gray-600 | #4b5563 | 主要文字 |
| gray-700 | #374151 | 標題文字 |
| gray-800 | #1f2937 | 深色背景 |
| gray-900 | #111827 | 最深背景 |

## 無障礙指南

### WCAG AA 標準

所有文字色彩必須符合以下對比度要求：

- **普通文字**: 最低 4.5:1
- **大文字** (18pt+ 或 14pt+ 粗體): 最低 3:1
- **互動元素**: 最低 3:1（與相鄰顏色）

### 對比度檢查清單

在使用色彩時，請確認：

- [ ] 文字使用 `--color-primary-text` (#0051D0) 而非 `--color-primary` (#007AFF)
- [ ] Focus ring 使用高對比度顏色（#0051D0）
- [ ] 所有語義色彩符合 WCAG AA 標準
- [ ] 深色模式下的對比度同樣符合標準
- [ ] 使用對比度檢查工具驗證（如 WebAIM Contrast Checker）

### 對比度測試工具

推薦使用以下工具檢查對比度：

1. **WebAIM Contrast Checker**: https://webaim.org/resources/contrastchecker/
2. **Chrome DevTools**: Lighthouse 無障礙審查
3. **Figma Plugins**: Stark, A11y - Color Contrast Checker

## 深色模式

### 色彩調整

在深色模式下，色彩會自動調整以保持對比度：

```css
.dark {
  --color-primary: #007AFF; /* 保持不變 */
  --color-primary-text: #5AC8FA; /* 調整為更亮的藍色 */
  --color-background: #111827;
  --color-foreground: #f9fafb;
}
```

### 深色模式對比度

確保深色模式下的對比度同樣符合 WCAG AA：

- 淺色文字在深色背景上：最低 4.5:1
- 互動元素在深色背景上：最低 3:1

## 實作範例

### React 組件

```jsx
// ✅ 正確：按鈕使用 primary，文字使用 primary-text
function PrimaryButton({ children }) {
  return (
    <button className="bg-primary text-white hover:bg-primary-600">
      {children}
    </button>
  )
}

function TextLink({ children, href }) {
  return (
    <a href={href} className="text-primary-text hover:underline">
      {children}
    </a>
  )
}
```

### CSS 變數

```css
/* ✅ 正確：區分互動元素和文字 */
.button {
  background: var(--color-primary); /* #007AFF for interactive */
}

.link {
  color: var(--color-primary-text); /* #0051D0 for text */
}

/* ❌ 錯誤：文字使用 primary */
.link-wrong {
  color: var(--color-primary); /* 對比度不足 */
}
```

## 遷移指南

### 從舊系統遷移

如果你的代碼使用了舊的藍色（#3b82f6），請按以下步驟更新：

1. **識別用途**:
   - 如果是按鈕、圖標、背景 → 使用 `#007AFF` 或 `var(--color-primary)`
   - 如果是文字、鏈接、focus ring → 使用 `#0051D0` 或 `var(--color-primary-text)`

2. **搜尋並替換**:
   ```bash
   # 搜尋所有使用舊藍色的文件
   rg "#3b82f6" --type css --type jsx
   
   # 根據用途替換為新色彩
   ```

3. **測試對比度**:
   - 使用 WebAIM Contrast Checker 驗證
   - 確保所有文字色彩 ≥ 4.5:1

## 常見問題

### Q: 為什麼需要兩種藍色？

A: iOS 藍 (#007AFF) 是 Apple 的標誌性顏色，視覺效果最佳，但對比度不足（4.02:1）。為了符合 WCAG AA 標準，我們為文字使用更深的藍色 (#0051D0, 6.12:1)。

### Q: 什麼時候使用情感色彩？

A: 當你需要傳達特定情緒或強調某種狀態時。例如：
- 慶祝成功 → Joy (#FF9500)
- 平靜信息 → Calm (#5AC8FA)
- 緊急警告 → Energy (#FF3B30)

### Q: 如何在 Tailwind 中使用這些顏色？

A: 使用 CSS 變數：
```jsx
<div className="text-primary-text">文字</div>
<button className="bg-primary">按鈕</button>
```

## 參考資料

- [Apple Human Interface Guidelines - Color](https://developer.apple.com/design/human-interface-guidelines/color)
- [WCAG 2.1 Contrast Guidelines](https://www.w3.org/WAI/WCAG21/Understanding/contrast-minimum.html)
- [WebAIM Contrast Checker](https://webaim.org/resources/contrastchecker/)
- [MorningAI Design System Enhancement Roadmap](./DESIGN_SYSTEM_ENHANCEMENT_ROADMAP.md)
- [Apple-Level UI/UX Optimization Report](./APPLE_LEVEL_UI_UX_OPTIMIZATION_REPORT.md)

---

**最後更新**: 2025-10-25  
**版本**: 1.0.0  
**維護者**: MorningAI Design Team
