# Apple 設計系統遷移檢查清單

## 概述

本檢查清單用於將現有頁面遷移到 Apple 設計系統。請逐項檢查並標記完成狀態。

---

## 🎯 P0 優先級（立即執行）

### 1. iOS 字體系統遷移

#### Frontend-Dashboard
- [x] Dashboard.tsx - 已完成
- [x] AgentGovernance.tsx - 已完成
- [x] LoginPage.tsx - 已完成
- [x] LandingPage.tsx - 已完成
- [x] Sidebar.tsx - 已完成
- [ ] SystemSettings.tsx
- [ ] TenantSettings.tsx
- [ ] ReportCenter.tsx
- [ ] WidgetLibrary.tsx

#### Owner-Console
- [ ] OwnerDashboard.jsx
- [ ] AgentGovernance.jsx
- [ ] TenantManagement.jsx
- [ ] SystemMonitoring.jsx
- [ ] AgentEvaluationDashboard.jsx
- [ ] PlatformSettings.jsx
- [ ] UXMetrics.jsx

### 2. Owner-Console 主題整合

- [x] App.jsx 添加 `theme-apple` class
- [x] 替換 `bg-gray-100` 為 `bg-neutral-50 dark:bg-neutral-900`
- [x] 複製 `index.css` 從 frontend-dashboard
- [ ] 測試深色模式切換
- [ ] 驗證所有頁面視覺一致性

### 3. 核心文檔建立

- [x] APPLE_DESIGN_SYSTEM_GUIDE.md - 完整使用指南
- [x] MIGRATION_CHECKLIST.md - 本檢查清單
- [ ] 在 README.md 中添加設計系統章節
- [ ] 建立 Storybook 快速入門指南

---

## 🟡 P1 優先級（本週完成）

### 4. 情感化色彩系統應用

#### 需要檢查的組件
- [ ] Dashboard.tsx - 統計卡片使用情感色彩
- [ ] AgentGovernance.tsx - 狀態指示器
- [ ] SystemSettings.tsx - 警告訊息
- [ ] TenantSettings.tsx - 成功/錯誤提示
- [ ] ReportCenter.tsx - 報告狀態

#### 色彩映射規則
```
成功/完成 → bg-growth (綠)
資訊/穩定 → bg-calm (藍)
警告/注意 → bg-joy (橙)
錯誤/危險 → bg-energy (紅)
洞察/智慧 → bg-wisdom (紫)
```

### 5. Glassmorphism 效果擴展

- [ ] Modal 組件添加毛玻璃效果
- [ ] Dropdown 組件添加毛玻璃效果
- [ ] Popover 組件添加毛玻璃效果
- [ ] Toast 通知添加毛玻璃效果
- [ ] Sidebar 懸浮狀態添加毛玻璃效果

### 6. Spring 動畫統一

- [ ] 所有按鈕添加 `whileHover` 和 `whileTap`
- [ ] 卡片組件添加懸停動畫
- [ ] 頁面切換添加 Spring 過渡
- [ ] Modal 開關使用 Spring 動畫
- [ ] Dropdown 展開使用 Spring 動畫

---

## 🟢 P2 優先級（下個 Sprint）

### 7. Shared-UI 包結構優化

- [ ] 確認 `packages/shared-ui/` 實體位置
- [ ] 統一 Apple 組件路徑
- [ ] 建立 monorepo 文檔
- [ ] 設置組件版本管理
- [ ] 建立組件發布流程

### 8. 設計 Token 自動化驗證

- [ ] 建立 ESLint 規則檢測硬編碼色彩
- [ ] 建立 Stylelint 規則檢測非 token 值
- [ ] 整合到 pre-commit hook
- [ ] 建立 CI 檢查流程
- [ ] 生成違規報告

### 9. 無障礙性增強

- [ ] 所有互動元素添加 `aria-label`
- [ ] 確保鍵盤導航完整
- [ ] 添加 `role` 屬性
- [ ] 測試螢幕閱讀器相容性
- [ ] 驗證色彩對比度（WCAG AAA）

---

## 📋 詳細遷移步驟

### 步驟 1：字體系統遷移

#### 1.1 識別需要替換的類別

```bash
# 搜尋所有需要替換的字體類別
grep -r "text-3xl\|text-2xl\|text-xl\|text-lg\|text-base\|text-sm\|text-xs" src/components/
```

#### 1.2 替換規則

| 舊類別 | 新類別 | 用途 |
|-------|-------|------|
| `text-3xl` | `text-large-title` 或 `text-display-3` | 頁面主標題 |
| `text-2xl` | `text-title-1` | 一級標題 |
| `text-xl` | `text-title-2` | 二級標題 |
| `text-lg` | `text-title-3` | 三級標題 |
| `text-base` | `text-body` | 標準內文 |
| `text-sm` | `text-subhead` 或 `text-footnote` | 小字內文 |
| `text-xs` | `text-caption-1` 或 `text-caption-2` | 極小字 |

#### 1.3 驗證步驟

```bash
# 檢查是否還有舊類別
grep -r "text-[0-9]xl\|text-lg\|text-sm\|text-base\|text-xs" src/components/ | grep -v ".stories.tsx" | grep -v ".test.tsx"
```

### 步驟 2：色彩系統遷移

#### 2.1 識別硬編碼色彩

```bash
# 搜尋 hex 色碼
grep -r "#[0-9A-Fa-f]\{6\}" src/components/ | grep -v ".stories.tsx"
```

#### 2.2 替換規則

```tsx
// 前：硬編碼色彩
<div className="bg-green-100 text-green-800">成功</div>

// 後：情感化色彩
<div className="bg-growth text-growth-foreground">成功</div>
```

#### 2.3 驗證步驟

```bash
# 檢查是否還有硬編碼色彩
grep -r "bg-green-\|bg-blue-\|bg-red-\|bg-yellow-\|bg-purple-" src/components/ | grep -v ".stories.tsx"
```

### 步驟 3：組件遷移

#### 3.1 AppleButton 遷移

```tsx
// 前：標準按鈕
<button className="px-4 py-2 bg-blue-600 text-white rounded-lg">
  點擊
</button>

// 後：AppleButton
<AppleButton variant="primary" haptic="medium">
  點擊
</AppleButton>
```

#### 3.2 AppleInput 遷移

```tsx
// 前：標準輸入框
<input
  type="email"
  placeholder="Email"
  className="px-4 py-2 border rounded-lg"
/>

// 後：AppleInput
<AppleInput
  type="email"
  label="電子郵件"
  placeholder="your@email.com"
  leftIcon={<User className="w-4 h-4" />}
  haptic="light"
/>
```

### 步驟 4：動畫遷移

#### 4.1 添加 Spring 動畫

```tsx
import { motion } from 'framer-motion'

// 前：標準 transition
<div className="transition-all duration-200 hover:scale-105">
  內容
</div>

// 後：Spring 動畫
<motion.div
  whileHover={{ scale: 1.05 }}
  transition={{
    type: 'spring',
    stiffness: 500,
    damping: 30
  }}
>
  內容
</motion.div>
```

#### 4.2 使用 Apple Easing

```tsx
<motion.div
  initial={{ opacity: 0, y: 20 }}
  animate={{ opacity: 1, y: 0 }}
  transition={{
    duration: 0.6,
    ease: [0.22, 1, 0.36, 1] // Apple 標準 easing
  }}
>
  內容
</motion.div>
```

---

## 🧪 測試檢查清單

### 視覺測試

- [ ] 所有頁面在淺色模式下正確顯示
- [ ] 所有頁面在深色模式下正確顯示
- [ ] 字體大小階層清晰
- [ ] 色彩對比度符合 WCAG AAA
- [ ] 動畫流暢自然

### 功能測試

- [ ] 所有按鈕可點擊
- [ ] 所有輸入框可輸入
- [ ] Modal 可正常開關
- [ ] Toast 通知正常顯示
- [ ] 表單驗證正常運作

### 響應式測試

- [ ] 手機版面（< 640px）
- [ ] 平板版面（640px - 1024px）
- [ ] 桌面版面（> 1024px）
- [ ] 超寬螢幕（> 1920px）

### 無障礙測試

- [ ] 鍵盤導航完整
- [ ] 螢幕閱讀器相容
- [ ] Focus 狀態清晰
- [ ] ARIA 屬性正確
- [ ] 色彩對比度達標

### 效能測試

- [ ] 首次內容繪製（FCP）< 1.8s
- [ ] 最大內容繪製（LCP）< 2.5s
- [ ] 累積版面位移（CLS）< 0.1
- [ ] 首次輸入延遲（FID）< 100ms

---

## 📊 進度追蹤

### Frontend-Dashboard

| 頁面 | 字體系統 | 色彩系統 | 組件遷移 | 動畫 | 測試 | 狀態 |
|-----|---------|---------|---------|------|------|------|
| Dashboard.tsx | ✅ | ⏳ | ⏳ | ⏳ | ⏳ | 進行中 |
| AgentGovernance.tsx | ✅ | ⏳ | ⏳ | ⏳ | ⏳ | 進行中 |
| LoginPage.tsx | ✅ | ✅ | ✅ | ✅ | ⏳ | 進行中 |
| LandingPage.tsx | ✅ | ⏳ | ⏳ | ✅ | ⏳ | 進行中 |
| Sidebar.tsx | ✅ | ⏳ | ⏳ | ⏳ | ⏳ | 進行中 |
| SystemSettings.tsx | ⏳ | ⏳ | ⏳ | ⏳ | ⏳ | 待開始 |
| TenantSettings.tsx | ⏳ | ⏳ | ⏳ | ⏳ | ⏳ | 待開始 |

### Owner-Console

| 頁面 | 字體系統 | 色彩系統 | 組件遷移 | 動畫 | 測試 | 狀態 |
|-----|---------|---------|---------|------|------|------|
| App.jsx | ✅ | ✅ | N/A | N/A | ⏳ | 進行中 |
| OwnerDashboard.jsx | ⏳ | ⏳ | ⏳ | ⏳ | ⏳ | 待開始 |
| AgentGovernance.jsx | ⏳ | ⏳ | ⏳ | ⏳ | ⏳ | 待開始 |
| TenantManagement.jsx | ⏳ | ⏳ | ⏳ | ⏳ | ⏳ | 待開始 |

**圖例**:
- ✅ 已完成
- ⏳ 進行中
- ⏳ 待開始
- N/A 不適用

---

## 🎯 完成標準

### P0 完成標準（本週）

1. ✅ 所有主要頁面（Dashboard, AgentGovernance, LoginPage, LandingPage, Sidebar）完成字體系統遷移
2. ✅ Owner-console 整合 Apple 設計系統（theme-apple class）
3. ✅ 建立完整文檔（使用指南、遷移檢查清單）
4. ⏳ 執行 lint 檢查無錯誤
5. ⏳ 建立 PR 並通過 CI

### P1 完成標準（下週）

1. 所有頁面完成情感化色彩系統應用
2. 所有互動元素添加 Spring 動畫
3. 所有彈出元素添加 Glassmorphism 效果
4. 視覺一致性達到 8.5/10
5. 開發者滿意度達到 8/10

### P2 完成標準（下個 Sprint）

1. Shared-UI 包結構優化完成
2. 設計 Token 自動化驗證整合到 CI
3. 無障礙性測試全部通過
4. 效能指標全部達標
5. 完整的 Storybook 文檔

---

## 📝 備註

### 已知問題

1. **Owner-console 深色模式**: 需要測試所有頁面的深色模式顯示
2. **Shared-UI 路徑**: 需要確認 `packages/shared-ui/` 的實體位置
3. **TypeScript 嚴格模式**: 187 個源碼錯誤需要逐步修復

### 下一步行動

1. 完成 P0 任務的 lint 檢查
2. 建立 PR 並等待 CI 通過
3. 開始 P1 任務：情感化色彩系統應用
4. 規劃 P2 任務的時程

---

**最後更新**: 2025-11-25  
**版本**: 1.0.0  
**負責人**: MorningAI 團隊
