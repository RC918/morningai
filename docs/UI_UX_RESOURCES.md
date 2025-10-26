# MorningAI UI/UX 資源指南

**最後更新**: 2025-10-26  
**維護者**: UI/UX 團隊  
**目的**: 提供團隊成員快速查找和利用 UI/UX 資源的中心化指南

---

## 🚀 新人必讀

**第一次使用 UI/UX 資源？從這裡開始**：
- **[UI/UX 快速上手指南](UI_UX_QUICKSTART.md)** - ⚡ 5 分鐘快速入門（新人必讀）
- **[UI/UX 速查表](UI_UX_CHEATSHEET.md)** - 📋 一頁速查表（常用命令、組件、Tokens）

---

## 📋 快速導航

- [核心文檔](#核心文檔)
- [已完成工作](#已完成工作-week-1-6)
- [設計系統](#設計系統)
- [組件庫](#組件庫)
- [預覽環境](#預覽環境)
- [開發指南](#開發指南)

---

## 🎯 核心文檔

### 審查與評估報告

1. **[全面 UI/UX 審查報告](UX/COMPREHENSIVE_UI_UX_AUDIT_REPORT.md)**
   - **總體評分**: 83/100（優秀）
   - **關鍵發現**: 
     - ✅ 完整的設計 Token 系統（185 行 tokens.json）
     - ✅ 優秀的移動端優化（觸控目標 44x44px，符合 WCAG）
     - ✅ 領先的國際化支援（294 個翻譯 keys，雙語完整覆蓋）
     - ✅ 業界領先的動效治理（prefers-reduced-motion、動畫預算限制）
     - ⚠️ Token 全域污染風險（P0）
     - ⚠️ Dashboard 保存狀態反饋不足（P0）
     - ⚠️ 缺少跳過導航、Live Regions（P0/P1）
   - **相關 PR**: [#644](https://github.com/RC918/morningai/pull/644)

2. **[設計系統增強路線圖](UX/DESIGN_SYSTEM_ENHANCEMENT_ROADMAP.md)**
   - **8 週執行計畫**: Week 1-8 詳細任務分解
   - **成功指標**:
     - 首次價值時間 (TTV) < 10 分鐘
     - 系統可用性 (SUS) > 80
     - NPS > 35
     - WCAG 2.1 AA 完整合規
     - Lighthouse 性能分數 > 90

3. **[UI/UX 工程進度評估報告](../UI_UX_PROGRESS_ASSESSMENT_REPORT.md)**
   - **Week 1-2 完成度**: ✅ 100% (4/4 Issues)
   - **總體進度**: 4/15 Issues (26.7%)
   - **下一階段**: Week 3-4 準備開始

### 策略與規劃

4. **[頂尖 SaaS UI/UX 計畫](UX/TOP_TIER_SAAS_UI_UX_PLAN.md)**
   - 業界最佳實踐參考
   - 競品分析與對標

5. **[SaaS UX 策略](UX/SAAS_UX_STRATEGY.md)**
   - 長期 UX 策略規劃
   - 用戶體驗優化方向

6. **[可用性測試計畫](UX/USABILITY_TESTING_PLAN.md)**
   - 測試方法與流程
   - 測試腳本與評估標準

---

## ✅ 已完成工作 (Week 1-6)

### Week 1-2: 基礎設施強化

#### Week 1: Token 作用域化與狀態反饋

**PR #690**: [Week 1-2 Infrastructure Enhancement](https://github.com/RC918/morningai/pull/690)
- ✅ Token 作用域化（`.theme-morning-ai` 容器）
- ✅ Dashboard 保存狀態反饋（已保存/保存中/未保存/錯誤）
- ✅ 跳過導航連結（符合 WCAG 2.1 AA）
- **狀態**: ✅ 已合併至 main

**PR #694**: [Week 1 Task 1.4 - Live Regions Implementation](https://github.com/RC918/morningai/pull/694)
- ✅ Live Regions 實作（`role="alert"`, `aria-live`）
- ✅ 保存狀態通知螢幕閱讀器
- ✅ 表單驗證錯誤無障礙支援
- **狀態**: ✅ 已合併至 main

#### Week 2: 撤銷/重做與全局搜尋

**PR #699**: [Week 2 - Undo/Redo & Global Search (Cmd+K)](https://github.com/RC918/morningai/pull/699)
- ✅ 撤銷/重做功能（`useUndoRedo` hook）
- ✅ 全局搜尋（Cmd+K）
- ✅ 鍵盤快捷鍵支援
- **狀態**: ✅ 已合併至 main

### Week 3-4: 組件文檔與測試

**PR #659**: [Week 3 - Storybook Setup and Component Documentation](https://github.com/RC918/morningai/pull/659)
- ✅ Storybook 8.6.14 設置
- ✅ 核心組件 stories（Button, Card, Input, Badge, etc.）
- ✅ 自動部署到 Chromatic
- **狀態**: ✅ 已合併至 main

**PR #666**: [Storybook - CostAnalysis & StrategyManagement Stories](https://github.com/RC918/morningai/pull/666)
- ✅ 業務組件 stories（CostAnalysis, StrategyManagement）
- ✅ MDX 文檔
- ✅ 自動部署流程
- **狀態**: ✅ 已合併至 main

**PR #709**: [Week 3 - Storybook Setup and Component Documentation](https://github.com/RC918/morningai/pull/709)
- ✅ 完整的組件文檔
- ✅ 互動測試
- **狀態**: ✅ 已合併至 main

**PR #730**: [Storybook - Table Stories and Edge Cases](https://github.com/RC918/morningai/pull/730)
- ✅ Table 組件 stories
- ✅ 邊界情況測試
- **狀態**: ✅ 已合併至 main

**PR #681**: [Week 4 - Usability Testing Materials and Templates](https://github.com/RC918/morningai/pull/681)
- ✅ 可用性測試材料
- ✅ 測試模板與腳本
- **狀態**: ✅ 已合併至 main

### Week 5-6: 進階功能

**PR #732**: [Week 5 - Dark Mode Implementation](https://github.com/RC918/morningai/pull/732)
- ✅ 暗色主題實作
- ✅ 主題切換器
- ✅ 系統偏好檢測
- **狀態**: ✅ 已合併至 main

**PR #735**: [Week 5 - Micro-Interactions Enhancement](https://github.com/RC918/morningai/pull/735)
- ✅ 微互動增強
- ✅ 動畫優化
- **狀態**: ✅ 已合併至 main

**PR #739**: [Week 5 - Component Documentation (Alert, Avatar, Accordion, Tabs, Tooltip)](https://github.com/RC918/morningai/pull/739)
- ✅ 5 個核心組件文檔
- ✅ 使用範例與最佳實踐
- **狀態**: ✅ 已合併至 main

**PR #746**: [Week 6 - Performance Optimization](https://github.com/RC918/morningai/pull/746)
- ✅ 圖片懶加載（LazyImage 組件）
- ✅ 字體優化（font-display: swap）
- ✅ WebP 支援
- ✅ Web Vitals 監控
- **狀態**: ✅ 已合併至 main

### Phase 1 Week 1: Apple-Level 設計系統基礎

**🎉 Phase 1 Week 1 完成！** (2025-10-25)
- ✅ **5 個核心設計系統** - 完整的 Apple-Level 設計系統基礎
- ✅ **2500+ 行文檔** - 完整的設計系統文檔
- ✅ **80+ Storybook stories** - 互動式設計系統展示
- ✅ **100% CI 通過率** - 所有 PR 品質評分 60/60

#### Task 1: 字體系統

**PR #784**: [Phase 1 Week 1 Task 1 - iOS Typography System](https://github.com/RC918/morningai/pull/784)
- ✅ 13 級字體大小（10px - 96px）
- ✅ 5 種字重（Light, Regular, Medium, Semibold, Bold）
- ✅ 3 種行高（Tight, Normal, Relaxed）
- ✅ 完整的 Storybook stories（15+ stories）
- ✅ 500+ 行文檔（TYPOGRAPHY_SYSTEM.md）
- **狀態**: ✅ 已合併至 main

#### Task 2: 色彩系統

**PR #785**: [Phase 1 Week 1 Task 2 - iOS Emotional Color System](https://github.com/RC918/morningai/pull/785)
- ✅ 5 種情感色彩（Calm, Energetic, Warm, Cool, Neutral）
- ✅ 完整的語義色彩（Success, Error, Warning, Info）
- ✅ 深色模式支援
- ✅ 完整的 Storybook stories（20+ stories）
- ✅ 450+ 行文檔（COLOR_SYSTEM.md）
- **狀態**: ✅ 已合併至 main

#### Task 3: 材質系統

**PR #786**: [Phase 1 Week 1 Task 3 - iOS Material System](https://github.com/RC918/morningai/pull/786)
- ✅ 5 級毛玻璃效果（Ultra Thin - Ultra Thick）
- ✅ 深色模式支援
- ✅ 完整的 Storybook stories（15+ stories）
- ✅ 480+ 行文檔（MATERIAL_SYSTEM.md）
- **狀態**: ✅ 已合併至 main

#### Task 4: 陰影系統

**PR #787**: [Phase 1 Week 1 Task 4 - iOS Shadow System](https://github.com/RC918/morningai/pull/787)
- ✅ 5 級陰影（XS - XL）
- ✅ 彩色陰影支援
- ✅ 深色模式支援
- ✅ 完整的 Storybook stories（17+ stories）
- ✅ 480+ 行文檔（SHADOW_SYSTEM.md）
- **狀態**: ✅ 已合併至 main

#### Task 5: 間距系統

**PR #788**: [Phase 1 Week 1 Task 5 - iOS Spacing System](https://github.com/RC918/morningai/pull/788)
- ✅ 8 級間距（4px - 96px）
- ✅ 8px 基礎網格系統
- ✅ 響應式間距支援
- ✅ 完整的 Storybook stories（18+ stories）
- ✅ 597 行文檔（SPACING_SYSTEM.md）
- **狀態**: ✅ 已合併至 main

### Phase 2 Week 6-7: Apple 組件系統

**🎉 Phase 2 Week 6-7 完成！** (2025-10-26)
- ✅ **5 個 Apple 組件** - 完整的 Apple-Level 組件系統
- ✅ **165 個單元測試** - 100% 通過率
- ✅ **60+ Storybook stories** - 互動式組件展示
- ✅ **3000+ 行文檔** - 完整的組件文檔
- ✅ **4 個 Provider 整合** - 全域 Hook 支援
- ✅ **1 個關鍵 Bug 修復** - Storybook 部署競態條件

#### Task 1: AppleLiveActivity 組件

**PR #809**: [Phase 2 Week 6-7 Task 1 - Apple Live Activity Component](https://github.com/RC918/morningai/pull/809)
- ✅ 實時活動通知組件
- ✅ 進度條支援
- ✅ 自動消失功能
- ✅ 33 個單元測試（100% 通過）
- ✅ 12 個 Storybook stories
- ✅ 600+ 行文檔（APPLE_LIVE_ACTIVITY_SYSTEM.md）
- **狀態**: ✅ 已合併至 main

#### Task 2: AppleControlCenter 組件

**PR #810**: [Phase 2 Week 6-7 Task 2 - Apple Control Center Component](https://github.com/RC918/morningai/pull/810)
- ✅ 控制中心 UI 組件
- ✅ 快速設置面板
- ✅ 滑動手勢支援
- ✅ 33 個單元測試（100% 通過）
- ✅ 12 個 Storybook stories
- ✅ 600+ 行文檔（APPLE_CONTROL_CENTER_SYSTEM.md）
- **狀態**: ✅ 已合併至 main

#### Task 3: AppleSpotlight 組件

**PR #813**: [Phase 2 Week 6-7 Task 3 - Apple Spotlight Component](https://github.com/RC918/morningai/pull/813)
- ✅ Spotlight 搜尋組件
- ✅ Cmd+K / Ctrl+K 快捷鍵
- ✅ 搜尋歷史記錄
- ✅ 33 個單元測試（100% 通過）
- ✅ 12 個 Storybook stories
- ✅ 600+ 行文檔（APPLE_SPOTLIGHT_SYSTEM.md）
- **狀態**: ✅ 已合併至 main

#### Task 4: AppleActionSheet 組件

**PR #814**: [Phase 2 Week 6-7 Task 4 - Apple Action Sheet Component](https://github.com/RC918/morningai/pull/814)
- ✅ Action Sheet 組件
- ✅ 多種操作樣式（default, destructive, cancel）
- ✅ 觸覺反饋支援
- ✅ 33 個單元測試（100% 通過）
- ✅ 12 個 Storybook stories
- ✅ 700+ 行文檔（APPLE_ACTION_SHEET_SYSTEM.md）
- **狀態**: ✅ 已合併至 main

#### Task 5: ApplePicker 組件

**PR #815**: [Phase 2 Week 6-7 Task 5 - Apple Picker Component](https://github.com/RC918/morningai/pull/815)
- ✅ iOS 風格選擇器組件
- ✅ 滾輪式選擇介面
- ✅ 多列選擇支援
- ✅ 33 個單元測試（100% 通過）
- ✅ 12 個 Storybook stories
- ✅ 600+ 行文檔（APPLE_PICKER_SYSTEM.md）
- **狀態**: ✅ 已合併至 main

#### 額外工作

**PR #816**: [fix(ci): Prevent Storybook deployment race condition](https://github.com/RC918/morningai/pull/816)
- ✅ 修復 Storybook 部署競態條件
- ✅ 防止多個部署同時運行
- ✅ 改進 CI/CD 穩定性
- **狀態**: ✅ 已合併至 main

**PR #817**: [feat(ux): Integrate all Apple component Providers into App](https://github.com/RC918/morningai/pull/817)
- ✅ 整合 4 個 Provider（ActionSheet, Spotlight, ControlCenter, LiveActivity）
- ✅ 全域 Hook 支援
- ✅ 零破壞性變更
- ✅ 運行時測試通過（8/8）
- **狀態**: ✅ 已合併至 main

---

## 🎨 設計系統

### 核心設計系統文檔（Phase 1 Week 1）

**位置**: `docs/UX/`

**5 個核心設計系統**:

1. **[字體系統](UX/TYPOGRAPHY_SYSTEM.md)** (500+ 行)
   - 13 級字體大小（10px - 96px）
   - 5 種字重（Light, Regular, Medium, Semibold, Bold）
   - 3 種行高（Tight, Normal, Relaxed）
   - 完整的使用指南和最佳實踐

2. **[色彩系統](UX/COLOR_SYSTEM.md)** (450+ 行)
   - 5 種情感色彩（Calm, Energetic, Warm, Cool, Neutral）
   - 完整的語義色彩（Success, Error, Warning, Info）
   - 深色模式支援
   - 色彩對比度指南

3. **[材質系統](UX/MATERIAL_SYSTEM.md)** (480+ 行)
   - 5 級毛玻璃效果（Ultra Thin - Ultra Thick）
   - 深色模式支援
   - 性能優化指南
   - 實際應用範例

4. **[陰影系統](UX/SHADOW_SYSTEM.md)** (480+ 行)
   - 5 級陰影（XS - XL）
   - 彩色陰影支援
   - 深色模式支援
   - 視覺層次指南

5. **[間距系統](UX/SPACING_SYSTEM.md)** (597 行)
   - 8 級間距（4px - 96px）
   - 8px 基礎網格系統
   - 響應式間距支援
   - 性能優化指南

### Design Tokens

**位置**: `docs/UX/tokens.json`

**內容**:
- **色彩系統**: 9 個層級（50-900），支援深淺主題
- **字體系統**: Inter + IBM Plex Sans/Mono
- **間距系統**: xs 到 4xl（8 個層級）
- **圓角系統**: sm 到 2xl（6 個層級）
- **陰影系統**: xs 到 2xl（5 個層級）
- **動畫系統**: 4 個時長 + 4 種緩動曲線
- **斷點系統**: mobile, tablet, desktop

**使用方式**:
```javascript
import { applyDesignTokens } from '@/lib/design-tokens'

// 在 App.jsx 中應用
<div className="theme-morning-ai">
  {/* 所有內容 */}
</div>
```

### 設計文檔

**位置**: `docs/UX/Design System/`

**內容**:
- **Tokens.md**: Token 系統完整說明
- **Components.md**: 組件庫使用指南
- **Animation.md**: 動效規範與最佳實踐
- **Accessibility.md**: 無障礙性指南
- **Responsive.md**: 響應式設計規範

---

## 🌍 國際化 (i18n)

### 技術架構

**Morning AI 使用 Tolgee + i18next 混合架構**:

- **Tolgee**: 提供 in-context 翻譯 UI 和雲端翻譯管理
- **i18next**: 提供核心翻譯引擎和 React 整合
- **react-i18next**: 提供 React hooks (`useTranslation`)

### 支援語言

| 語言 | 檔案大小 | 狀態 |
|------|---------|------|
| 英文 (en-US) | 34,591 bytes | ✅ 完整 |
| 繁體中文 (zh-TW) | 32,529 bytes | ✅ 完整 |
| 德文 (de) | 539 bytes | ⚠️ 未完整 |
| 法文 (fr) | 551 bytes | ⚠️ 未完整 |

### 使用方式

```javascript
import { useTranslation } from 'react-i18next'

function MyComponent() {
  const { t } = useTranslation()
  
  return (
    <div>
      <h1>{t('common.title')}</h1>
      <p>{t('common.description', { param: value })}</p>
    </div>
  )
}
```

### 翻譯檔案位置

```
handoff/20250928/40_App/frontend-dashboard/src/i18n/
├── config.js        # i18next 配置
├── tolgee.js        # Tolgee 配置
└── locales/
    ├── en-US.json   # 英文翻譯
    └── zh-TW.json   # 繁體中文翻譯
```

### 相關文檔

- **[I18N_STRATEGY.md](I18N_STRATEGY.md)** - 完整的國際化策略與工作流程
- **[i18n 架構分析報告](/tmp/i18n_architecture_analysis.md)** - 詳細的技術架構分析

### 關鍵特性

✅ **Tolgee 特性**:
- In-context 翻譯 UI (開發環境)
- 雲端翻譯管理
- 靜態翻譯檔案支援

✅ **i18next 特性**:
- 自訂語言偵測器 (localStorage + 瀏覽器語言)
- 參數化翻譯 (interpolation)
- 命名空間支援
- 深色模式支援

✅ **翻譯覆蓋率**:
- 支援命名空間: common, auth, sidebar, feedback, phase3Welcome, dashboard, strategy, cost, wip
- 294+ 翻譯 keys
- 雙語完整覆蓋 (en-US, zh-TW)

---

## 🧩 組件庫

### 核心組件

**位置**: `handoff/20250928/40_App/frontend-dashboard/src/components/ui/`

**組件清單** (77 個組件):

#### 表單組件
- `button.jsx` - 按鈕（6 種變體，3 種尺寸）
- `input.jsx` - 輸入框
- `textarea.jsx` - 文本域
- `select.jsx` - 下拉選單
- `checkbox.jsx` - 複選框
- `radio-group.jsx` - 單選按鈕組
- `switch.jsx` - 開關
- `slider.jsx` - 滑桿
- `label.jsx` - 標籤

#### 佈局組件
- `card.jsx` - 卡片
- `separator.jsx` - 分隔線
- `aspect-ratio.jsx` - 寬高比容器
- `resizable.jsx` - 可調整大小容器
- `scroll-area.jsx` - 滾動區域

#### 導航組件
- `navigation-menu.jsx` - 導航菜單
- `tabs.jsx` - 標籤頁
- `accordion.jsx` - 手風琴
- `breadcrumb.jsx` - 麵包屑
- `pagination.jsx` - 分頁

#### 反饋組件
- `dialog.jsx` - 對話框
- `alert-dialog.jsx` - 警告對話框
- `toaster.jsx` - 通知
- `drawer.jsx` - 抽屜
- `sheet.jsx` - 側邊欄
- `alert.jsx` - 警告
- `toast.jsx` - 輕提示
- `skeleton.jsx` - 骨架屏
- `progress.jsx` - 進度條
- `spinner.jsx` - 加載動畫

#### 數據展示組件
- `table.jsx` - 表格
- `chart.jsx` - 圖表
- `calendar.jsx` - 日曆
- `avatar.jsx` - 頭像
- `badge.jsx` - 徽章

#### 互動組件
- `popover.jsx` - 彈出框
- `hover-card.jsx` - 懸停卡片
- `tooltip.jsx` - 工具提示
- `command.jsx` - 命令面板
- `context-menu.jsx` - 右鍵菜單
- `dropdown-menu.jsx` - 下拉菜單

#### 特殊組件
- `lazy-image.jsx` - 懶加載圖片（Week 6 新增）
- `loading-states.jsx` - 加載狀態
- `empty-state.jsx` - 空狀態

### Storybook 文檔

**預覽環境**: 
- 主應用 Storybook: 透過 Chromatic 自動部署
- 查看方式: 在 PR 中查看 Chromatic 預覽連結

**本地運行**:
```bash
cd handoff/20250928/40_App/frontend-dashboard
pnpm storybook
```

---

## 🌐 預覽環境

### PR #644 預覽環境

**主應用**:
- URL: https://morningai-git-ui-ux-strategy-audit-2025-10-23-morning-ai.vercel.app
- 內容: UI/UX 審查報告與路線圖

**Owner Console**:
- URL: https://morningai-owner-console-git-ui-ux-strategy-au-1a0651-morning-ai.vercel.app
- 內容: Owner Console 預覽

### 其他預覽環境

所有 PR 都會自動部署到 Vercel，預覽連結可在 PR 頁面查看。

---

## 📚 開發指南

### 開始使用 UI/UX 資源

1. **查看審查報告**: 了解當前狀態與待改進項目
   - 閱讀 [全面 UI/UX 審查報告](UX/COMPREHENSIVE_UI_UX_AUDIT_REPORT.md)

2. **查看路線圖**: 了解計畫中的工作
   - 閱讀 [設計系統增強路線圖](UX/DESIGN_SYSTEM_ENHANCEMENT_ROADMAP.md)

3. **查看已完成工作**: 避免重複工作
   - 查看本文檔的 [已完成工作](#已完成工作-week-1-6) 章節
   - 查看相關 PR 和 commit

4. **使用組件庫**: 重用現有組件
   - 瀏覽 `src/components/ui/` 目錄
   - 查看 Storybook 文檔
   - 參考組件使用範例

5. **遵循設計規範**: 保持一致性
   - 使用 Design Tokens（`tokens.json`）
   - 遵循動效規範（`Animation.md`）
   - 遵循無障礙性指南（`Accessibility.md`）

### 貢獻指南

**設計 PR 規則**:
- 只允許改動 `docs/UX/**`, `docs/UX/tokens.json`, `docs/**.md`, `frontend/樣式與文案`
- 不得改動後端與 API 相關檔案

**工程 PR 規則**:
- 只允許改動 `**/api/**`, `**/src/**`, `handoff/**/30_API/openapi/**`
- 不得改動 `docs/UX/**` 與設計稿資源

詳細規則請參閱 [CONTRIBUTING.md](../CONTRIBUTING.md)

### 常見問題

**Q: 如何查找特定組件的使用方式？**
A: 
1. 查看 `src/components/ui/` 目錄中的組件源碼
2. 查看 Storybook 中的互動範例
3. 搜尋專案中的使用範例：`rg "import.*Button" --type tsx`

**Q: 如何確保我的改動不會破壞現有樣式？**
A:
1. 使用 Design Tokens 而非硬編碼值
2. 在 `.theme-morning-ai` 容器內工作
3. 運行視覺回歸測試（如果有）
4. 在預覽環境中測試

**Q: 如何查看已完成的 UI/UX 工作？**
A:
1. 查看本文檔的 [已完成工作](#已完成工作-week-1-6) 章節
2. 查看 GitHub PR 列表，篩選 `feat(ux):` 標籤
3. 查看 git log：`git log --oneline --grep="ux:"`

**Q: 如何避免重複工作？**
A:
1. 在開始工作前，先查看本文檔
2. 搜尋相關 GitHub Issues 和 PRs
3. 在團隊頻道詢問是否有人正在進行類似工作

---

## 🔗 相關連結

### GitHub
- [UI/UX Milestone #6](https://github.com/RC918/morningai/milestone/6)
- [UI/UX Issues (#467-#481)](https://github.com/RC918/morningai/issues?q=is%3Aissue+label%3Aux)
- [所有 UI/UX PRs](https://github.com/RC918/morningai/pulls?q=is%3Apr+label%3Aux)

### 文檔
- [ARCHITECTURE.md](../ARCHITECTURE.md) - 系統架構
- [CONTRIBUTING.md](../CONTRIBUTING.md) - 貢獻指南
- [DESIGN_SYSTEM_GUIDELINES.md](../DESIGN_SYSTEM_GUIDELINES.md) - 設計系統指南
- [I18N_STRATEGY.md](I18N_STRATEGY.md) - 國際化策略與 Tolgee + i18next 架構

### 工具
- [Vercel Dashboard](https://vercel.com/morning-ai) - 部署管理
- [Chromatic](https://www.chromatic.com/) - Storybook 部署與視覺測試

---

## 📝 維護說明

本文檔應在以下情況更新：
- 完成新的 UI/UX 工作時
- 創建新的設計文檔時
- 添加新的組件時
- 更新設計系統時
- 發現文檔錯誤或過時信息時

**維護者**: UI/UX 團隊  
**最後更新**: 2025-10-26  
**版本**: 1.2.0
