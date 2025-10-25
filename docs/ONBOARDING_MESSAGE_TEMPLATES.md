# 新人歡迎訊息模板

本文檔提供可直接使用的新人歡迎訊息模板，適用於 Slack、Email 或其他溝通工具。

---

## 📧 Email 模板

### 通用版本（所有角色）

```
主旨: 歡迎加入 MorningAI！🎉

Hi [姓名],

歡迎加入 MorningAI 團隊！我們很高興有你加入。

為了幫助你快速上手，我們準備了完整的新人指南。請按照以下步驟開始：

📋 第一天必讀（30 分鐘）：
1. 閱讀專案概覽：https://github.com/RC918/morningai/blob/main/README.md
2. 查看新人上手指南：https://github.com/RC918/morningai/blob/main/ONBOARDING.md
3. 設置本地開發環境：https://github.com/RC918/morningai/blob/main/docs/setup_local.md

🎯 根據你的角色，請特別關注：
- 設計師：UI/UX 快速上手指南 (https://github.com/RC918/morningai/blob/main/docs/UI_UX_QUICKSTART.md)
- 前端工程師：UI/UX 快速上手指南 + UI/UX 速查表
- 後端工程師：ARCHITECTURE.md + Agent Governance Framework
- 產品經理：CTO Strategic Plan + UI/UX Issue 狀態追蹤

📚 核心資源：
- GitHub Repo: https://github.com/RC918/morningai
- 貢獻指南: https://github.com/RC918/morningai/blob/main/CONTRIBUTING.md
- 團隊 Slack: [插入 Slack 連結]

如有任何問題，請隨時在 Slack 頻道詢問或直接聯繫我。

期待與你一起工作！

Best regards,
[你的名字]
```

### 設計師專用版本

```
主旨: 歡迎加入 MorningAI 設計團隊！🎨

Hi [姓名],

歡迎加入 MorningAI 設計團隊！我們剛完成 8-Week UI/UX Roadmap（18/18 Issues, 100% 完成），現在正是加入的好時機。

🚀 快速上手（1 小時）：

1. **了解設計系統**（30 分鐘）
   - UI/UX 快速上手指南: https://github.com/RC918/morningai/blob/main/docs/UI_UX_QUICKSTART.md
   - UI/UX 速查表: https://github.com/RC918/morningai/blob/main/docs/UI_UX_CHEATSHEET.md
   - Design Tokens: https://github.com/RC918/morningai/blob/main/docs/UX/tokens.json

2. **查看已完成工作**（20 分鐘）
   - UI/UX Issue 狀態: https://github.com/RC918/morningai/blob/main/docs/UI_UX_ISSUE_STATUS.md
   - 8-Week Roadmap 總結: https://github.com/RC918/morningai/blob/main/docs/UX/8_WEEK_ROADMAP_FINAL_SUMMARY.md

3. **啟動 Storybook**（10 分鐘）
   ```bash
   cd handoff/20250928/40_App/frontend-dashboard
   pnpm install
   pnpm storybook
   ```

📋 重要規則：
- Design PR 只能改動: docs/UX/**, docs/**.md, frontend/樣式與文案
- 不能改動後端與 API 相關檔案
- 詳細規則: https://github.com/RC918/morningai/blob/main/CONTRIBUTING.md

🎯 第一個任務：
查看 GitHub Issues 中標記為 "good first issue" 或 "design" 的任務：
https://github.com/RC918/morningai/issues?q=is%3Aissue+is%3Aopen+label%3A%22good+first+issue%22

如有任何問題，請在 #design 頻道詢問！

Best regards,
[你的名字]
```

### 前端工程師專用版本

```
主旨: 歡迎加入 MorningAI 前端團隊！💻

Hi [姓名],

歡迎加入 MorningAI 前端團隊！我們使用 React + Vite + Tailwind CSS，並有完整的 Storybook 組件庫。

🚀 快速上手（2 小時）：

1. **設置開發環境**（30 分鐘）
   ```bash
   git clone https://github.com/RC918/morningai.git
   cd morningai/handoff/20250928/40_App/frontend-dashboard
   pnpm install
   pnpm dev          # 啟動開發伺服器
   pnpm storybook    # 啟動 Storybook
   pnpm test:e2e             # 運行測試
   ```

2. **了解架構**（30 分鐘）
   - UI/UX 快速上手指南: https://github.com/RC918/morningai/blob/main/docs/UI_UX_QUICKSTART.md
   - UI/UX 速查表: https://github.com/RC918/morningai/blob/main/docs/UI_UX_CHEATSHEET.md
   - 組件庫位置: handoff/20250928/40_App/frontend-dashboard/src/components/ui/

3. **查看已完成功能**（30 分鐘）
   - Week 7-8 完成報告: https://github.com/RC918/morningai/blob/main/docs/UX/WEEK_7_8_COMPLETION_REPORT.md
   - 瀏覽 Storybook 中的組件範例

4. **了解測試與 CI/CD**（30 分鐘）
   - CI 工作流矩陣: https://github.com/RC918/morningai/blob/main/docs/ci_matrix.md
   - 測試覆蓋率報告: https://github.com/RC918/morningai/blob/main/TEST_COVERAGE_IMPROVEMENT_REPORT.md

📋 重要規則：
- Engineering PR 只能改動: **/api/**, **/src/**
- 不能改動 docs/UX/** 設計稿資源
- 詳細規則: https://github.com/RC918/morningai/blob/main/CONTRIBUTING.md

🎯 第一個任務：
查看 GitHub Issues 中標記為 "good first issue" 或 "frontend" 的任務：
https://github.com/RC918/morningai/issues?q=is%3Aissue+is%3Aopen+label%3A%22good+first+issue%22

如有任何問題，請在 #frontend 頻道詢問！

Best regards,
[你的名字]
```

### 後端工程師專用版本

```
主旨: 歡迎加入 MorningAI 後端團隊！🔧

Hi [姓名],

歡迎加入 MorningAI 後端團隊！我們使用 FastAPI + Python + Supabase，並有完整的 Agent Governance Framework。

🚀 快速上手（2 小時）：

1. **設置開發環境**（30 分鐘）
   ```bash
   git clone https://github.com/RC918/morningai.git
   cd morningai/handoff/20250928/40_App/api-backend
   pip install -r requirements.txt
   cd src && python main.py    # 啟動 API 伺服器
   pytest                # 運行測試
   ```

2. **了解架構**（45 分鐘）
   - ARCHITECTURE.md: https://github.com/RC918/morningai/blob/main/docs/ARCHITECTURE.md
   - Agent Governance Framework: https://github.com/RC918/morningai/blob/main/docs/GOVERNANCE_FRAMEWORK.md
   - Database Schema: https://github.com/RC918/morningai/blob/main/DATABASE_SCHEMA_ANALYSIS.md

3. **了解核心功能**（30 分鐘）
   - 環境變數 Schema: https://github.com/RC918/morningai/blob/main/docs/config/env_schema.md
   - Agent Sandbox Architecture: https://github.com/RC918/morningai/blob/main/docs/agent-sandbox-architecture.md

4. **了解測試與部署**（15 分鐘）
   - CI 工作流矩陣: https://github.com/RC918/morningai/blob/main/docs/ci_matrix.md
   - 測試覆蓋率報告: https://github.com/RC918/morningai/blob/main/TEST_COVERAGE_IMPROVEMENT_REPORT.md

📋 重要規則：
- Engineering PR 只能改動: **/api/**, **/src/**, handoff/**/30_API/openapi/**
- 不能改動 docs/UX/** 設計稿資源
- API 變更需要先提 RFC Issue
- 詳細規則: https://github.com/RC918/morningai/blob/main/CONTRIBUTING.md

🎯 第一個任務：
查看 GitHub Issues 中標記為 "good first issue" 或 "backend" 的任務：
https://github.com/RC918/morningai/issues?q=is%3Aissue+is%3Aopen+label%3A%22good+first+issue%22

如有任何問題，請在 #backend 頻道詢問！

Best regards,
[你的名字]
```

### 產品經理專用版本

```
主旨: 歡迎加入 MorningAI 產品團隊！📊

Hi [姓名],

歡迎加入 MorningAI 產品團隊！我們正處於 MVP to World-Class 轉型階段，這是一個激動人心的時刻。

🚀 快速上手（1.5 小時）：

1. **了解產品願景**（30 分鐘）
   - README.md: https://github.com/RC918/morningai/blob/main/README.md
   - CTO Strategic Plan: https://github.com/RC918/morningai/blob/main/CTO_STRATEGIC_PLAN_MVP_TO_WORLD_CLASS.md
   - Strategic Integration Analysis: https://github.com/RC918/morningai/blob/main/CTO_STRATEGIC_INTEGRATION_ANALYSIS.md

2. **了解 UI/UX 進度**（30 分鐘）
   - UI/UX Issue 狀態: https://github.com/RC918/morningai/blob/main/docs/UI_UX_ISSUE_STATUS.md
   - 8-Week Roadmap 總結: https://github.com/RC918/morningai/blob/main/docs/UX/8_WEEK_ROADMAP_FINAL_SUMMARY.md
   - UI/UX 審查報告: https://github.com/RC918/morningai/blob/main/docs/UX/COMPREHENSIVE_UI_UX_AUDIT_REPORT.md

3. **了解技術指標**（20 分鐘）
   - 測試覆蓋率報告: https://github.com/RC918/morningai/blob/main/TEST_COVERAGE_IMPROVEMENT_REPORT.md
   - Status & Metrics: https://github.com/RC918/morningai/blob/main/README.md#status--metrics

4. **熟悉工作流程**（10 分鐘）
   - GitHub Issues: https://github.com/RC918/morningai/issues
   - Milestones: https://github.com/RC918/morningai/milestones
   - CONTRIBUTING.md: https://github.com/RC918/morningai/blob/main/CONTRIBUTING.md

📊 當前狀態：
- 測試覆蓋率: 41% → 目標 80%
- API 延遲 (p95): ~500ms → 目標 <100ms
- Uptime: 90% → 目標 99.9%
- UI/UX 8-Week Roadmap: 18/18 Issues (100% 完成)

🎯 第一個任務：
- 查看 GitHub Milestones 了解當前進度
- 參與 PR 審查提供產品視角的反饋
- 創建新的 Issue（功能需求、改進建議）

如有任何問題，請在 #product 頻道詢問！

Best regards,
[你的名字]
```

---

## 💬 Slack 訊息模板

### 通用版本（所有角色）

```
👋 歡迎 @[姓名] 加入 MorningAI！

為了幫助你快速上手，請先完成以下步驟：

📋 第一天必讀（30 分鐘）：
1. 專案概覽: https://github.com/RC918/morningai/blob/main/README.md
2. 新人上手指南: https://github.com/RC918/morningai/blob/main/ONBOARDING.md
3. 本地開發設定: https://github.com/RC918/morningai/blob/main/docs/setup_local.md

🎯 根據你的角色，請查看：
• 設計師 → #design 頻道 + UI/UX 快速上手指南
• 前端工程師 → #frontend 頻道 + UI/UX 速查表
• 後端工程師 → #backend 頻道 + ARCHITECTURE.md
• 產品經理 → #product 頻道 + CTO Strategic Plan

有任何問題隨時在對應頻道詢問！🚀
```

### 設計師專用版本

```
🎨 歡迎 @[姓名] 加入設計團隊！

我們剛完成 8-Week UI/UX Roadmap（18/18 Issues, 100% 完成），現在正是加入的好時機！

🚀 快速上手（1 小時）：
1. UI/UX 快速上手指南: https://github.com/RC918/morningai/blob/main/docs/UI_UX_QUICKSTART.md
2. UI/UX 速查表: https://github.com/RC918/morningai/blob/main/docs/UI_UX_CHEATSHEET.md
3. Design Tokens: https://github.com/RC918/morningai/blob/main/docs/UX/tokens.json

📋 重要：Design PR 只能改動 docs/UX/**, docs/**.md, frontend/樣式與文案

有問題隨時在 #design 頻道詢問！
```

### 前端工程師專用版本

```
💻 歡迎 @[姓名] 加入前端團隊！

我們使用 React + Vite + Tailwind CSS，並有完整的 Storybook 組件庫。

🚀 快速上手（2 小時）：
1. UI/UX 快速上手指南: https://github.com/RC918/morningai/blob/main/docs/UI_UX_QUICKSTART.md
2. UI/UX 速查表: https://github.com/RC918/morningai/blob/main/docs/UI_UX_CHEATSHEET.md
3. 啟動開發環境:
   ```
   cd handoff/20250928/40_App/frontend-dashboard
   pnpm install && pnpm dev
   pnpm storybook
   ```

📋 重要：Engineering PR 只能改動 **/api/**, **/src/**

有問題隨時在 #frontend 頻道詢問！
```

### 後端工程師專用版本

```
🔧 歡迎 @[姓名] 加入後端團隊！

我們使用 FastAPI + Python + Supabase，並有完整的 Agent Governance Framework。

🚀 快速上手（2 小時）：
1. ARCHITECTURE.md: https://github.com/RC918/morningai/blob/main/docs/ARCHITECTURE.md
2. Agent Governance Framework: https://github.com/RC918/morningai/blob/main/docs/GOVERNANCE_FRAMEWORK.md
3. 啟動開發環境:
   ```
   cd handoff/20250928/40_App/api-backend
   pip install -r requirements.txt
   cd src && python main.py
   ```

📋 重要：API 變更需要先提 RFC Issue

有問題隨時在 #backend 頻道詢問！
```

### 產品經理專用版本

```
📊 歡迎 @[姓名] 加入產品團隊！

我們正處於 MVP to World-Class 轉型階段，這是一個激動人心的時刻。

🚀 快速上手（1.5 小時）：
1. CTO Strategic Plan: https://github.com/RC918/morningai/blob/main/CTO_STRATEGIC_PLAN_MVP_TO_WORLD_CLASS.md
2. UI/UX Issue 狀態: https://github.com/RC918/morningai/blob/main/docs/UI_UX_ISSUE_STATUS.md
3. 8-Week Roadmap 總結: https://github.com/RC918/morningai/blob/main/docs/UX/8_WEEK_ROADMAP_FINAL_SUMMARY.md

📊 當前狀態：測試覆蓋率 41% → 目標 80%, UI/UX 18/18 Issues (100% 完成)

有問題隨時在 #product 頻道詢問！
```

---

## 📋 快速參考卡（可列印）

### 新人必讀清單

```
┌─────────────────────────────────────────────────────────┐
│           MorningAI 新人必讀清單                          │
├─────────────────────────────────────────────────────────┤
│                                                           │
│ □ 閱讀 README.md - 專案概覽                               │
│ □ 閱讀 ONBOARDING.md - 新人上手指南                       │
│ □ 閱讀 CONTRIBUTING.md - 貢獻規則                         │
│ □ 設置本地開發環境                                         │
│ □ 加入團隊 Slack/Discord                                  │
│                                                           │
│ 設計師額外檢查：                                           │
│ □ 閱讀 UI/UX 快速上手指南                                 │
│ □ 查看 Design Tokens                                     │
│ □ 啟動 Storybook                                         │
│                                                           │
│ 前端工程師額外檢查：                                       │
│ □ 閱讀 UI/UX 快速上手指南                                 │
│ □ 啟動開發伺服器                                          │
│ □ 運行測試                                                │
│                                                           │
│ 後端工程師額外檢查：                                       │
│ □ 閱讀 ARCHITECTURE.md                                   │
│ □ 啟動 API 伺服器                                         │
│ □ 運行測試                                                │
│                                                           │
│ 產品經理額外檢查：                                         │
│ □ 閱讀 CTO Strategic Plan                                │
│ □ 查看 UI/UX Issue 狀態                                  │
│ □ 了解 Milestones                                        │
│                                                           │
└─────────────────────────────────────────────────────────┘
```

---

## 使用說明

1. **選擇合適的模板**: 根據新成員的角色選擇對應的 Email 或 Slack 模板
2. **自定義內容**: 將 `[姓名]`, `[你的名字]`, `[插入 Slack 連結]` 等佔位符替換為實際內容
3. **發送訊息**: 複製模板內容並發送給新成員
4. **後續跟進**: 在新成員加入後的第 1 天、第 3 天、第 7 天進行跟進，確保他們順利上手

## 跟進時間表

- **第 1 天**: 發送歡迎訊息 + 新人上手指南
- **第 3 天**: 確認是否完成環境設置，是否有遇到問題
- **第 7 天**: 確認是否已開始第一個任務，提供必要的支援
- **第 14 天**: 收集反饋，了解上手過程中的痛點

---

**提示**: 將此文檔加入書籤，每次有新成員加入時可快速找到合適的模板！
