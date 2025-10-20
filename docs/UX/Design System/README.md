# MorningAI Design System

## 概述

MorningAI Design System 是一套完整的設計規範與組件庫，旨在確保產品的一致性、可維護性與可擴展性。本設計系統涵蓋設計 Token、組件指南、動效規範、無障礙標準與文案指南。

## 目錄結構

```
docs/UX/Design System/
├── README.md                    # 本文檔
├── Tokens.md                    # 設計 Token 規範
├── Components.md                # 組件指南
├── Animation.md                 # 動效指南
├── Accessibility.md             # 無障礙指南
└── Copywriting.md               # 文案與 i18n 指南
```

## 設計原則

### 1. 一致性 (Consistency)
- 統一的視覺語言
- 可預測的互動模式
- 標準化的組件行為

### 2. 可及性 (Accessibility)
- WCAG 2.1 AA 標準
- 鍵盤導航支援
- 螢幕閱讀器友好

### 3. 性能優先 (Performance First)
- 輕量級組件
- 優化的動效
- 響應式設計

### 4. 可維護性 (Maintainability)
- 模組化設計
- 清晰的文檔
- 版本控制

## 快速開始

### 設計師

1. 閱讀 [設計 Token 規範](./Tokens.md)
2. 參考 [組件指南](./Components.md)
3. 遵循 [動效指南](./Animation.md)
4. 確保符合 [無障礙標準](./Accessibility.md)
5. 使用 [文案指南](./Copywriting.md) 撰寫文案

### 工程師

1. 安裝依賴
```bash
cd handoff/20250928/40_App/frontend-dashboard
pnpm install
```

2. 啟動開發伺服器
```bash
pnpm run dev
```

3. 查看 Storybook (如已建立)
```bash
pnpm run storybook
```

## 設計 Token

設計 Token 是設計系統的基礎，定義了色彩、字體、間距、陰影等基本元素。

詳見：[Tokens.md](./Tokens.md)

## 組件庫

組件庫基於 Radix UI 與 Tailwind CSS 構建，提供一套完整的 UI 組件。

詳見：[Components.md](./Components.md)

## 動效規範

動效用於提升用戶體驗，但需遵循性能與無障礙原則。

詳見：[Animation.md](./Animation.md)

## 無障礙標準

確保所有用戶都能使用產品，包括殘障用戶。

詳見：[Accessibility.md](./Accessibility.md)

## 文案指南

清楚、簡潔、可行動的文案，支援多語言。

詳見：[Copywriting.md](./Copywriting.md)

## 工具與資源

### 設計工具
- [Figma](https://www.figma.com/) - 高保真設計
- [FigJam](https://www.figma.com/figjam/) - 用戶流程圖
- [Stark](https://www.getstark.co/) - 無障礙檢查

### 開發工具
- [Tailwind CSS](https://tailwindcss.com/) - 樣式框架
- [Radix UI](https://www.radix-ui.com/) - 無頭組件
- [Framer Motion](https://www.framer.com/motion/) - 動效庫
- [Storybook](https://storybook.js.org/) - 組件展示

### 測試工具
- [eslint-plugin-jsx-a11y](https://github.com/jsx-eslint/eslint-plugin-jsx-a11y) - 無障礙檢查
- [axe DevTools](https://www.deque.com/axe/devtools/) - 無障礙測試
- [Lighthouse](https://developers.google.com/web/tools/lighthouse) - 性能測試

## 貢獻指南

### 設計 PR
- 只允許改動 `docs/UX/**`、`docs/UX/tokens.json`、`docs/**.md`、`frontend/樣式與文案`
- 不得改動 `handoff/**/30_API/openapi/**`、`**/api/**`、`**/src/**`

### 工程 PR
- 只允許改動 `**/api/**`、`**/src/**`、`handoff/**/30_API/openapi/**`
- 不得改動 `docs/UX/**` 與設計稿資源

詳見：[CONTRIBUTING.md](../../../CONTRIBUTING.md)

## 版本歷史

| 版本 | 日期 | 變更內容 | 作者 |
|------|------|----------|------|
| 1.0.0 | 2025-10-20 | 初版建立 | UI/UX 設計團隊 |

## 聯繫方式

如有任何問題或建議，請聯繫：
- UI/UX 設計團隊
- 專案負責人：Ryan Chen (ryan2939z@gmail.com)
