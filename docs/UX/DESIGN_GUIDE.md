# Phase 1–8 設計完成指南

## 設計語言系統 (Design Language System)

### 核心基調
- **未來感（AI）**：展現智能、前瞻性的科技感
- **安全感（信任）**：建立專業、可靠的品牌形象

### 色彩系統
- **基礎色**：低彩灰底 `#F5F6F7`，營造專業、簡潔的視覺環境
- **主色調**：`#0ea5e9`（天藍色），代表智能與創新
- **強調色**：
  - 藍紫 `#8b5cf6`：AI 提示、智能建議
  - 橙黃 `#f59e0b`：警告、重要通知
- **語義色**：
  - 成功 `#10b981`
  - 錯誤 `#ef4444`
  - 警告 `#f59e0b`
  - 資訊 `#0ea5e9`

### 字體系統
- **主字體**：Inter，現代、清晰、易讀
- **輔助字體**：IBM Plex Sans，專業、技術感
- **字階**：
  - Display: 48px/60px (標題)
  - Heading 1: 36px/44px
  - Heading 2: 28px/36px
  - Body: 16px/24px
  - Small: 14px/20px
  - Caption: 12px/16px

### 間距系統
基於 8px 網格系統：
- `xs`: 4px
- `sm`: 8px
- `md`: 16px
- `lg`: 24px
- `xl`: 32px
- `2xl`: 48px
- `3xl`: 64px

### 圓角系統
- `sm`: 4px（小元件）
- `md`: 8px（按鈕、輸入框）
- `lg`: 12px（卡片）
- `xl`: 16px（模態框）
- `2xl`: 24px（大型容器）

## 元件庫 (Component Library)

### 基礎元件
所有元件對齊 **Tailwind CSS** 和 **Shadcn/UI**，確保工程實作一致性：

1. **Button**
   - Primary: 主要操作（藍色背景）
   - Secondary: 次要操作（灰色邊框）
   - Ghost: 輕量操作（透明背景）
   - Destructive: 危險操作（紅色）

2. **Card**
   - 資訊展示的基本容器
   - 支援 header, content, footer 結構

3. **Form**
   - Input: 文字輸入框
   - Select: 下拉選單
   - Checkbox: 多選框
   - Radio: 單選框
   - Switch: 開關

4. **Table**
   - 資料列表展示
   - 支援排序、篩選、分頁

5. **Toast / Alert**
   - 即時通知與警告訊息

6. **Empty State**
   - 空白狀態友好提示

## 核心頁面設計 (Phase 1–8)

### 1. Dashboard（儀表板）
**目標**：讓使用者快速啟動第一個 agent，立即感受價值

**關鍵模組**：
- **今日焦點 (Today's Focus)**
  - 待辦任務卡片
  - 即將到來的會議
  - AI 智能建議
  - 系統提醒
  
- **AI Agent 狀態面板**
  - 正在運行的 Agents
  - 最近的任務執行結果
  - 快速啟動按鈕

- **專案看板 (Project Board)**
  - 類似 Notion / Linear 的卡片式管理
  - 拖拉排序
  - AI 作為「共作者」標記

**響應式設計**：
- 桌機：三欄佈局（焦點、狀態、看板）
- 平板：兩欄佈局
- 手機：單欄堆疊，優先顯示今日焦點

### 2. Checkout（訂閱與金流）
**目標**：30 秒內完成訂閱，流程順暢無干擾

**關鍵流程**：
1. **方案選擇**
   - 清晰的定價表
   - 功能對比
   - Trial 提示

2. **表單填寫**
   - 最小化必填欄位
   - 即時驗證與友好錯誤提示
   - 支援多種支付方式（Stripe, TapPay）

3. **確認與完成**
   - 訂單摘要
   - 一鍵確認
   - 成功動畫與引導

**錯誤處理**：
- 支付失敗：清晰說明原因，提供解決方案
- 網路錯誤：保存進度，提示重試

### 3. Settings（系統設定）
**目標**：清晰的資訊層次，易於管理多租戶與個人設定

**關鍵模組**：
- **個人資料 (Profile)**
  - 頭像、姓名、Email
  - 密碼修改
  - 雙因素認證

- **多租戶管理 (Tenants)**
  - 租戶列表（名稱、角色、狀態）
  - 權限管理（可視化顯示）
  - 邀請新成員

- **系統偏好 (Preferences)**
  - 語言設定
  - 通知偏好
  - 主題模式（亮色/暗色）

## 設計原則

### 1. 用戶體驗 (User Experience)
- **無縫 Onboarding**：引導使用者快速上手
- **即時反饋**：150ms 快速反饋，300ms 場景過渡
- **智能提示**：AI 輔助決策，減少選擇負擔
- **錯誤友好**：清晰的錯誤說明，提供解決方案

### 2. 響應式設計 (Responsive Design)
- **桌機優先**：主要工作場景在桌面端
- **手機精簡**：提供核心功能（任務 + 對話）
- **斷點**：375px / 768px / 1280px

### 3. 無障礙 (Accessibility)
- **高對比**：文字與背景對比度 > 4.5:1
- **鍵盤操作**：所有功能可透過鍵盤完成
- **ARIA 標籤**：語義化 HTML，支援螢幕閱讀器
- **焦點指示**：清晰的焦點狀態

### 4. 性能 (Performance)
- **60fps 動畫**：流暢的微動效
- **延遲載入**：優化首屏載入時間
- **漸進式增強**：核心功能優先，附加功能延後

## 資料模擬 (Mock Data)

Phase 1–8 期間，**不依賴真實 API**，使用以下方式模擬資料：

- **JSON 檔案**：`src/mocks/*.json`
- **Mock Service Worker (MSW)**：攔截 API 請求
- **Storybook**：獨立展示元件狀態

## 設計交付物

1. **Design Tokens** (`tokens.json`)
   - 色彩、字體、間距、圓角、陰影

2. **元件庫 (Component Library)**
   - Storybook 展示
   - 所有交互狀態（hover, active, disabled）
   - 微動效定義

3. **頁面原型 (Prototypes)**
   - Dashboard
   - Checkout
   - Settings
   - 支援 RWD、PWA

4. **設計規範文件**
   - Figma 設計檔連結
   - Redlines（標注間距、色彩）
   - 動效規範（timing, easing）

## 工程協作

### Design Tokens → Code
```javascript
// tokens.json 可直接被 Tailwind 使用
module.exports = {
  theme: {
    extend: {
      colors: require('./tokens.json').color,
      fontFamily: require('./tokens.json').font,
      spacing: require('./tokens.json').space,
    }
  }
}
```

### Component Mapping
| 設計元件 | 前端實作 |
|---------|---------|
| Button | `@/components/ui/button` (shadcn) |
| Card | `@/components/ui/card` (shadcn) |
| Input | `@/components/ui/input` (shadcn) |
| Dialog | `@/components/ui/dialog` (shadcn) |

### 設計 → 開發交接
1. 設計師完成 Figma 設計，標注 Design Tokens
2. 前端工程師依照 tokens.json 和 shadcn/ui 實作
3. 使用 Storybook 驗證元件一致性
4. 使用 Mock 資料測試頁面流程

---

**這份設計指南將確保 Phase 1–8 的設計工作達到 iPhone 級的細膩度和一致性，並充分支援工程團隊的高效實作！**
