# Phase 5: AI Orchestrator & Meta-Agent - Figma 設計規格

## 🎨 設計概覽

本階段的設計重點是創建一個直觀、強大的 AI 治理主控台，讓管理者能夠輕鬆監控和管理複雜的 AI Agent 協作網絡。

## 📐 核心介面設計

### 1. AI 治理主控台 (Governance Console)

#### 1.1 主儀表板 (Main Dashboard)
- **尺寸**: 1440x900px (桌面主要視窗)
- **佈局**: 左側導航 (240px) + 主內容區域 (1200px)
- **核心元素**:
  - Agent Map 視覺化區域 (800x600px)
  - 實時狀態卡片組 (4x2 網格)
  - 快速操作面板

#### 1.2 Agent Map 視覺化
```
設計規格:
- 畫布尺寸: 800x600px
- 節點設計:
  * Agent 節點: 圓形, 直徑 60px
  * 狀態顏色: 綠色(空閒), 藍色(執行中), 黃色(等待), 紅色(異常)
  * 節點標籤: 12px Inter Medium, 白色文字
- 連線設計:
  * 線條粗細: 2-4px (根據優先級)
  * 動畫效果: 流光動畫, 2秒循環
  * 顏色: #3b82f6 (活躍), #94a3b8 (非活躍)
```

#### 1.3 HITL 審批中心
- **卡片設計**: 360x200px
- **狀態指示器**: 8px 圓點 + 狀態文字
- **操作按鈕**: 主要(批准) + 次要(拒絕) + 文字(修改)
- **時間戳**: 相對時間顯示 (如 "2 分鐘前")

### 2. 對話式指令介面

#### 2.1 指令輸入框
- **尺寸**: 600x120px (多行輸入)
- **樣式**: 圓角 12px, 邊框 1px #e2e8f0
- **佔位符**: "輸入您的指令，例如：為專業版用戶開發數據導出功能"
- **發送按鈕**: 48x48px 圓形, 主色調背景

#### 2.2 指令歷史
- **列表項**: 全寬 x 80px 高度
- **內容**: 指令文字 + 時間戳 + 狀態標籤
- **交互**: hover 效果, 點擊查看詳情

### 3. 工作流詳情頁面

#### 3.1 工作流時間軸
- **設計**: 垂直時間軸, 左側時間, 右側事件
- **節點**: 16px 圓形狀態點
- **連線**: 2px 虛線
- **事件卡片**: 400x120px, 包含 Agent 信息和執行結果

#### 3.2 Agent 詳情面板
- **尺寸**: 400x600px (側邊面板)
- **內容區塊**:
  * Agent 基本信息 (頭像 + 名稱 + 狀態)
  * 當前任務詳情
  * 執行日誌 (滾動區域)
  * 性能指標圖表

## 🎯 交互設計規範

### 1. 狀態反饋
- **載入狀態**: 骨架屏 + 脈衝動畫
- **成功狀態**: 綠色勾選 + 淡入動畫
- **錯誤狀態**: 紅色警告 + 震動效果
- **空狀態**: 插圖 + 引導文字

### 2. 動畫效果
- **頁面轉場**: 300ms ease-out 滑動
- **卡片懸停**: 150ms ease 陰影變化
- **按鈕點擊**: 100ms scale(0.95) 反饋
- **Agent 狀態變更**: 500ms 顏色漸變

### 3. 響應式設計
```
斷點設計:
- 桌面: 1440px+ (主要設計)
- 平板: 768-1439px (調整佈局)
- 手機: <768px (堆疊佈局)

適配策略:
- Agent Map: 平板縮放至 600x450px, 手機隱藏
- 側邊欄: 平板收起, 手機底部導航
- 卡片網格: 桌面 4列, 平板 2列, 手機 1列
```

## 🎨 視覺風格指南

### 1. 色彩系統
- **主色調**: #6366f1 (Indigo 500)
- **輔助色**: #8b5cf6 (Purple 500)
- **成功色**: #10b981 (Emerald 500)
- **警告色**: #f59e0b (Amber 500)
- **錯誤色**: #ef4444 (Red 500)

### 2. 字體系統
- **主字體**: Inter (Google Fonts)
- **等寬字體**: JetBrains Mono (程式碼顯示)
- **字重**: Light(300), Regular(400), Medium(500), Semibold(600), Bold(700)

### 3. 圖標系統
- **圖標庫**: Heroicons v2 (Outline & Solid)
- **尺寸**: 16px, 20px, 24px, 32px
- **風格**: 簡潔線性, 2px 線寬

## 📱 組件庫規格

### 1. Agent 狀態卡片
```css
.agent-card {
  width: 280px;
  height: 160px;
  border-radius: 12px;
  padding: 20px;
  background: white;
  box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
  transition: all 150ms ease;
}

.agent-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
}
```

### 2. 工作流進度條
```css
.workflow-progress {
  height: 8px;
  background: #f1f5f9;
  border-radius: 4px;
  overflow: hidden;
}

.workflow-progress-bar {
  height: 100%;
  background: linear-gradient(90deg, #6366f1, #8b5cf6);
  transition: width 300ms ease;
}
```

### 3. HITL 審批按鈕
```css
.hitl-button-primary {
  padding: 12px 24px;
  background: #10b981;
  color: white;
  border-radius: 8px;
  font-weight: 600;
  transition: all 150ms ease;
}

.hitl-button-primary:hover {
  background: #059669;
  transform: translateY(-1px);
}
```

## 🔧 Figma 文件結構

```
Morning AI - Phase 5 Design System
├── 📄 Cover Page
├── 🎨 Design Tokens
│   ├── Colors
│   ├── Typography
│   ├── Spacing
│   └── Shadows
├── 🧩 Components
│   ├── Agent Cards
│   ├── Workflow Elements
│   ├── HITL Components
│   └── Navigation
├── 📱 Screens
│   ├── Governance Console
│   ├── Agent Map
│   ├── Workflow Details
│   └── Mobile Views
└── 🔄 Prototypes
    ├── Main User Flow
    ├── HITL Approval Flow
    └── Agent Interaction Flow
```

## 📋 設計交付清單

- [ ] 完整的 Figma 設計文件
- [ ] 設計 Token JSON 文件
- [ ] 組件庫 (React/Vue 組件)
- [ ] 圖標 SVG 資源包
- [ ] 設計規範文檔 (PDF)
- [ ] 開發者移交文檔
- [ ] 響應式設計指南
- [ ] 無障礙設計檢查清單

## 🎯 設計目標

1. **直觀性**: 複雜的 AI 協作過程一目了然
2. **效率性**: 關鍵操作 3 次點擊內完成
3. **美觀性**: 符合現代 SaaS 產品的視覺標準
4. **一致性**: 與 Morning AI 整體設計語言保持統一
5. **可擴展性**: 支持未來新 Agent 和功能的添加

