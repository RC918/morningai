# Phase 1 設計規範：系統啟動與帳號註冊

## 1. 核心設計目標

- **無縫註冊體驗**：打造流暢、無干擾的註冊流程，讓使用者在 30 秒內完成
- **直觀登入介面**：提供清晰、易於操作的登入介面，支援多種登入方式
- **品牌第一印象**：建立專業、值得信賴的品牌第一印象

## 2. 介面佈局 (Layout)

### 註冊頁面
- **佈局**：單欄佈局，垂直居中
- **視覺焦點**：註冊表單
- **背景**：使用柔和的漸層背景，營造科技感
- **間距**：
  - 表單與標題間距：`48px`
  - 表單項之間距：`24px`
  - 按鈕與表單間距：`32px`

### 登入頁面
- **佈局**：與註冊頁面一致，保持視覺連貫性
- **視覺焦點**：登入表單
- **第三方登入**：置於表單下方，提供清晰的視覺分隔

## 3. 組件設計 (Component Design)

### 表單輸入框 (Input Fields)
- **樣式**：
  - `height`: `48px`
  - `border-radius`: `8px`
  - `border`: `1px solid #d4d4d4`
  - `padding`: `12px 16px`
- **狀態**：
  - **Focus**: `border-color: #0ea5e9`, `box-shadow: 0 0 0 3px rgba(14, 165, 233, 0.1)`
  - **Error**: `border-color: #ef4444`, `box-shadow: 0 0 0 3px rgba(239, 68, 68, 0.1)`
  - **Disabled**: `background-color: #f5f5f5`, `cursor: not-allowed`

### 按鈕 (Buttons)
- **主要按鈕 (Primary)**：
  - `background`: `#0ea5e9`
  - `color`: `#ffffff`
  - `height`: `48px`
  - `border-radius`: `8px`
  - `font-size`: `16px`
  - `font-weight`: `500`
- **交互**：
  - **Hover**: `background: #0284c7`, `transform: translateY(-1px)`
  - **Active**: `transform: translateY(0)`

### 第三方登入按鈕
- **樣式**：
  - `background`: `transparent`
  - `border`: `1px solid #d4d4d4`
  - `height`: `48px`
  - `border-radius`: `8px`
- **圖示**：使用官方品牌圖示 (Google, GitHub)

## 4. 動效設計 (Motion Design)

- **頁面載入**：使用 `fadeIn` 動畫，時長 `300ms`
- **表單項出現**：使用 `slideUp` 動畫，時長 `200ms`，`ease-out` 緩動
- **按鈕點擊**：使用 `scale` 動畫，`transform: scale(0.98)`，時長 `150ms`
- **錯誤提示**：使用 `shake` 動畫，時長 `300ms`

## 5. 響應式設計 (Responsive Design)

### Mobile (375px)
- **佈局**：全螢幕佈局，最大化表單可視區域
- **字體**：標題 `28px`，內文 `16px`
- **間距**：垂直間距適度縮小

### Tablet (768px)
- **佈局**：保持單欄佈局，增加左右邊距
- **字體**：標題 `36px`，內文 `18px`

### Desktop (1280px)
- **佈局**：在背景中加入 subtle 的幾何圖形，增加視覺豐富度
- **最大寬度**：表單最大寬度 `400px`

## 6. 無障礙設計 (Accessibility)

- **色彩對比**：所有文字與背景對比度 > 4.5:1
- **鍵盤導航**：確保所有可交互元素都可透過鍵盤訪問
- **語義化**：使用 `label` 標籤關聯表單項
- **焦點狀態**：提供清晰的焦點指示

這份設計規範將確保 Phase 1 的使用者體驗達到 iPhone 級的細膩度和一致！

