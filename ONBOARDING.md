# MorningAI 新人上手指南

**歡迎加入 MorningAI！** 🎉

本文檔將引導您快速熟悉專案，並開始貢獻。請按照您的角色選擇對應的上手路徑。

---

## 📋 第一天必讀清單

**所有新成員都需要完成以下步驟**：

### 1. 了解專案概況 (15 分鐘)

- [ ] 閱讀 [README.md](README.md) - 專案概覽、架構、核心功能
- [ ] 查看 [ARCHITECTURE.md](docs/ARCHITECTURE.md) - 系統架構與技術棧
- [ ] 了解 [CTO Strategic Plan](CTO_STRATEGIC_PLAN_MVP_TO_WORLD_CLASS.md) - 專案願景與路線圖

**關鍵資訊**：
- **專案定位**: 世界級 AI Agent 編排平台
- **技術棧**: React + Vite (前端), FastAPI + Python (後端), Supabase (資料庫)
- **架構**: 三層分離（Owner Console, Tenant Dashboard, API Backend）
- **當前階段**: Phase 8 → Phase 9 (MVP to World-Class 轉型)

### 2. 設置開發環境 (30 分鐘)

- [ ] 閱讀 [本地開發設定](docs/setup_local.md)
- [ ] Clone 專案: `git clone https://github.com/RC918/morningai.git`
- [ ] 安裝依賴並啟動應用（參考 setup_local.md）
- [ ] 確認可以訪問本地開發環境

### 3. 了解貢獻規則 (10 分鐘)

- [ ] 閱讀 [CONTRIBUTING.md](CONTRIBUTING.md) - 分工規則、PR 流程、驗收標準
- [ ] 了解 Design PR vs Engineering PR 的區別
- [ ] 了解 API 變更需要先提 RFC

**重要規則**：
- **Design PR**: 只能改動 `docs/UX/**`, `docs/**.md`, `frontend/樣式與文案`
- **Engineering PR**: 只能改動 `**/api/**`, `**/src/**`, `handoff/**/30_API/openapi/**`
- **API 變更**: 必須先提 RFC Issue，經 Owner 核准後才能提交 PR

---

## 🎨 設計師上手路徑

**預計時間**: 1-2 小時

### 第一步：了解設計系統 (30 分鐘)

- [ ] 閱讀 [UI/UX 快速上手指南](docs/UI_UX_QUICKSTART.md) - 5 分鐘快速入門
- [ ] 查看 [UI/UX 速查表](docs/UI_UX_CHEATSHEET.md) - 常用資源速查
- [ ] 瀏覽 [Design Tokens](docs/UX/tokens.json) - 色彩、字體、間距系統
- [ ] 閱讀 [設計系統指南](DESIGN_SYSTEM_GUIDELINES.md) - 設計規範與最佳實踐

### 第二步：查看已完成工作 (20 分鐘)

- [ ] 閱讀 [UI/UX Issue 狀態追蹤](docs/UI_UX_ISSUE_STATUS.md) - 18/18 Issues 完成狀態
- [ ] 查看 [8-Week Roadmap 總結](docs/UX/8_WEEK_ROADMAP_FINAL_SUMMARY.md) - 完整進度追蹤
- [ ] 瀏覽 [UI/UX 資源指南](docs/UI_UX_RESOURCES.md) - 完整資源索引

### 第三步：熟悉工具與流程 (30 分鐘)

- [ ] 啟動 Storybook: `cd handoff/20250928/40_App/frontend-dashboard && npm run storybook`
- [ ] 瀏覽組件庫: `handoff/20250928/40_App/frontend-dashboard/src/components/ui/`
- [ ] 查看 Vercel 預覽環境（在 PR 中查看）
- [ ] 了解如何提交 Design PR

### 第四步：開始第一個任務 (可選)

- [ ] 在 [GitHub Issues](https://github.com/RC918/morningai/issues) 中找到標記為 `good first issue` 或 `design` 的任務
- [ ] 創建分支: `git checkout -b devin/$(date +%s)-your-feature-name`
- [ ] 完成設計變更（只改動 `docs/UX/**` 或 `frontend/樣式與文案`）
- [ ] 提交 PR 並等待審查

**設計師常用資源**：
- Design Tokens: `docs/UX/tokens.json`
- 設計系統指南: `DESIGN_SYSTEM_GUIDELINES.md`
- UI/UX 速查表: `docs/UI_UX_CHEATSHEET.md`
- Storybook: `npm run storybook`

---

## 💻 前端工程師上手路徑

**預計時間**: 2-3 小時

### 第一步：了解前端架構 (30 分鐘)

- [ ] 閱讀 [UI/UX 快速上手指南](docs/UI_UX_QUICKSTART.md) - 5 分鐘快速入門
- [ ] 查看 [UI/UX 速查表](docs/UI_UX_CHEATSHEET.md) - 常用命令與組件
- [ ] 了解前端目錄結構:
  - Owner Console: `handoff/20250928/40_App/owner-console/`
  - Tenant Dashboard: `handoff/20250928/40_App/frontend-dashboard/`
- [ ] 查看組件庫: `handoff/20250928/40_App/frontend-dashboard/src/components/ui/`

### 第二步：設置本地開發環境 (30 分鐘)

- [ ] 安裝依賴: `cd handoff/20250928/40_App/frontend-dashboard && npm install`
- [ ] 啟動開發伺服器: `npm run dev`
- [ ] 啟動 Storybook: `npm run storybook`
- [ ] 運行測試: `npm test`
- [ ] 運行 Lint: `npm run lint`

### 第三步：了解核心功能 (45 分鐘)

- [ ] 查看 [Week 7-8 完成報告](docs/UX/WEEK_7_8_COMPLETION_REPORT.md) - 最新功能實作
- [ ] 了解 Design Tokens 使用方式（查看 `docs/UX/tokens.json`）
- [ ] 查看 Storybook 中的組件範例
- [ ] 搜尋專案中的組件使用範例: `rg "import.*Button" --type tsx`

### 第四步：了解測試與 CI/CD (30 分鐘)

- [ ] 閱讀 [CI 工作流矩陣](docs/ci_matrix.md) - GitHub Actions 工作流說明
- [ ] 了解測試策略（單元測試、整合測試、E2E 測試）
- [ ] 查看 [測試覆蓋率報告](TEST_COVERAGE_IMPROVEMENT_REPORT.md)
- [ ] 了解 Vercel 自動部署流程

### 第五步：開始第一個任務 (可選)

- [ ] 在 [GitHub Issues](https://github.com/RC918/morningai/issues) 中找到標記為 `good first issue` 或 `frontend` 的任務
- [ ] 創建分支: `git checkout -b devin/$(date +%s)-your-feature-name`
- [ ] 完成功能開發（只改動 `**/src/**`）
- [ ] 運行測試並確保通過
- [ ] 提交 PR 並等待審查

**前端工程師常用資源**：
- UI/UX 速查表: `docs/UI_UX_CHEATSHEET.md`
- 組件庫: `handoff/20250928/40_App/frontend-dashboard/src/components/ui/`
- Storybook: `npm run storybook`
- 測試命令: `npm test`, `npm run lint`, `npm run typecheck`

---

## 🔧 後端工程師上手路徑

**預計時間**: 2-3 小時

### 第一步：了解後端架構 (30 分鐘)

- [ ] 閱讀 [ARCHITECTURE.md](docs/ARCHITECTURE.md) - 系統架構文檔
- [ ] 查看 [Agent Governance Framework](docs/GOVERNANCE_FRAMEWORK.md) - 多代理系統治理框架
- [ ] 了解後端目錄結構: `handoff/20250928/40_App/api-backend/`
- [ ] 查看 OpenAPI 規範: `handoff/20250928/40_App/30_API/openapi/`

### 第二步：設置本地開發環境 (30 分鐘)

- [ ] 安裝依賴: `cd handoff/20250928/40_App/api-backend && pip install -r requirements.txt`
- [ ] 設置環境變數（參考 [環境變數 Schema](docs/config/env_schema.md)）
- [ ] 啟動 API 伺服器: `python -m src.main`
- [ ] 運行測試: `pytest`
- [ ] 檢查測試覆蓋率: `pytest --cov`

### 第三步：了解核心功能 (45 分鐘)

- [ ] 查看 [Database Schema Analysis](DATABASE_SCHEMA_ANALYSIS.md) - 資料庫結構
- [ ] 了解 JWT 認證流程（查看 `src/auth/`）
- [ ] 了解 RLS (Row Level Security) 實作
- [ ] 查看 Agent Sandbox 架構（[Agent Sandbox Architecture](docs/agent-sandbox-architecture.md)）

### 第四步：了解測試與部署 (30 分鐘)

- [ ] 閱讀 [CI 工作流矩陣](docs/ci_matrix.md) - GitHub Actions 工作流說明
- [ ] 了解測試策略（單元測試、整合測試）
- [ ] 查看 [測試覆蓋率報告](TEST_COVERAGE_IMPROVEMENT_REPORT.md)
- [ ] 了解 Fly.io 部署流程

### 第五步：開始第一個任務 (可選)

- [ ] 在 [GitHub Issues](https://github.com/RC918/morningai/issues) 中找到標記為 `good first issue` 或 `backend` 的任務
- [ ] 如果涉及 API 變更，先提 RFC Issue
- [ ] 創建分支: `git checkout -b devin/$(date +%s)-your-feature-name`
- [ ] 完成功能開發（只改動 `**/api/**` 或 `**/src/**`）
- [ ] 運行測試並確保通過
- [ ] 提交 PR 並等待審查

**後端工程師常用資源**：
- ARCHITECTURE.md: `docs/ARCHITECTURE.md`
- Agent Governance Framework: `docs/GOVERNANCE_FRAMEWORK.md`
- Database Schema: `DATABASE_SCHEMA_ANALYSIS.md`
- 環境變數 Schema: `docs/config/env_schema.md`
- 測試命令: `pytest`, `pytest --cov`

---

## 📊 產品經理上手路徑

**預計時間**: 1-2 小時

### 第一步：了解產品願景 (30 分鐘)

- [ ] 閱讀 [README.md](README.md) - 專案概覽與願景
- [ ] 查看 [CTO Strategic Plan](CTO_STRATEGIC_PLAN_MVP_TO_WORLD_CLASS.md) - 6 個月轉型計畫
- [ ] 了解 [Strategic Integration Analysis](CTO_STRATEGIC_INTEGRATION_ANALYSIS.md) - 戰略整合分析
- [ ] 查看 [Milestones & Roadmap](README.md#milestones--roadmap) - 里程碑與路線圖

### 第二步：了解 UI/UX 進度 (30 分鐘)

- [ ] 閱讀 [UI/UX Issue 狀態追蹤](docs/UI_UX_ISSUE_STATUS.md) - 18/18 Issues 完成狀態
- [ ] 查看 [8-Week Roadmap 總結](docs/UX/8_WEEK_ROADMAP_FINAL_SUMMARY.md) - 完整進度追蹤
- [ ] 閱讀 [UI/UX 審查報告](docs/UX/COMPREHENSIVE_UI_UX_AUDIT_REPORT.md) - 83/100 分評估
- [ ] 查看 [可用性測試計畫](docs/UX/USABILITY_TESTING_PLAN.md) - 測試方法與流程

### 第三步：了解技術指標 (20 分鐘)

- [ ] 查看 [測試覆蓋率報告](TEST_COVERAGE_IMPROVEMENT_REPORT.md) - 當前 41%，目標 80%
- [ ] 了解 [Status & Metrics](README.md#status--metrics) - API 延遲、Uptime、測試覆蓋率
- [ ] 查看 GitHub Actions 狀態（CI/CD 健康度）
- [ ] 了解 Vercel 部署狀態

### 第四步：熟悉工作流程 (20 分鐘)

- [ ] 了解 [GitHub Issues](https://github.com/RC918/morningai/issues) 管理流程
- [ ] 查看 [Milestones](https://github.com/RC918/morningai/milestones) - 當前進度
- [ ] 了解 PR 審查流程
- [ ] 了解 RFC 流程（API 變更需要先提 RFC）

### 第五步：開始第一個任務 (可選)

- [ ] 創建新的 Issue（功能需求、Bug 報告、改進建議）
- [ ] 參與 PR 審查（提供產品視角的反饋）
- [ ] 更新文檔（如果發現過時或不清楚的內容）

**產品經理常用資源**：
- CTO Strategic Plan: `CTO_STRATEGIC_PLAN_MVP_TO_WORLD_CLASS.md`
- UI/UX Issue 狀態: `docs/UI_UX_ISSUE_STATUS.md`
- 8-Week Roadmap: `docs/UX/8_WEEK_ROADMAP_FINAL_SUMMARY.md`
- GitHub Milestones: https://github.com/RC918/morningai/milestones

---

## 🆘 常見問題

### Q: 我應該從哪裡開始？

**A**: 根據您的角色選擇對應的上手路徑：
- **設計師**: 從 [UI/UX 快速上手指南](docs/UI_UX_QUICKSTART.md) 開始
- **前端工程師**: 從 [UI/UX 快速上手指南](docs/UI_UX_QUICKSTART.md) 和 [本地開發設定](docs/setup_local.md) 開始
- **後端工程師**: 從 [ARCHITECTURE.md](docs/ARCHITECTURE.md) 和 [本地開發設定](docs/setup_local.md) 開始
- **產品經理**: 從 [README.md](README.md) 和 [CTO Strategic Plan](CTO_STRATEGIC_PLAN_MVP_TO_WORLD_CLASS.md) 開始

### Q: 如何找到適合新人的任務？

**A**: 在 [GitHub Issues](https://github.com/RC918/morningai/issues) 中搜尋標記為 `good first issue` 的任務。這些任務通常比較簡單，適合新人熟悉專案。

### Q: 我可以同時改動前端和後端嗎？

**A**: 不可以。根據 [CONTRIBUTING.md](CONTRIBUTING.md) 的規則：
- **Design PR**: 只能改動 `docs/UX/**`, `docs/**.md`, `frontend/樣式與文案`
- **Engineering PR**: 只能改動 `**/api/**`, `**/src/**`, `handoff/**/30_API/openapi/**`

如果需要同時改動前端和後端，請分成兩個 PR。

### Q: 如何提交 API 變更？

**A**: API 變更需要先提 RFC Issue：
1. 創建 RFC Issue（label: `rfc`）
2. 說明動機、影響、相容策略、逐步 rollout
3. 等待 Owner 核准
4. 核准後才可提交工程 PR

詳細流程請參考 [CONTRIBUTING.md](CONTRIBUTING.md#api-變更流程)。

### Q: 如何查看 Storybook？

**A**: 
```bash
cd handoff/20250928/40_App/frontend-dashboard
npm install
npm run storybook
```

瀏覽器會自動打開 `http://localhost:6006`。

### Q: 如何運行測試？

**A**: 
- **前端**: `cd handoff/20250928/40_App/frontend-dashboard && npm test`
- **後端**: `cd handoff/20250928/40_App/api-backend && pytest`

### Q: 我遇到問題該怎麼辦？

**A**: 
1. 查看 [本地開發設定](docs/setup_local.md) 的故障排除章節
2. 搜尋 [GitHub Issues](https://github.com/RC918/morningai/issues) 看是否有類似問題
3. 在團隊頻道詢問（Slack/Discord）
4. 創建新的 GitHub Issue 並標記為 `question`

---

## 📚 核心文檔索引

### 專案概覽
- [README.md](README.md) - 專案概覽、架構、核心功能
- [ARCHITECTURE.md](docs/ARCHITECTURE.md) - 系統架構文檔
- [CTO Strategic Plan](CTO_STRATEGIC_PLAN_MVP_TO_WORLD_CLASS.md) - 6 個月轉型計畫

### 開發指南
- [本地開發設定](docs/setup_local.md) - 快速啟動指南與常見問題排除
- [CONTRIBUTING.md](CONTRIBUTING.md) - 分工規則、API 變更流程、驗收標準
- [CI 工作流矩陣](docs/ci_matrix.md) - GitHub Actions 工作流說明

### UI/UX 資源
- [UI/UX 快速上手指南](docs/UI_UX_QUICKSTART.md) - 5 分鐘快速入門
- [UI/UX 速查表](docs/UI_UX_CHEATSHEET.md) - 常用命令與組件
- [UI/UX 資源指南](docs/UI_UX_RESOURCES.md) - 完整資源索引
- [UI/UX Issue 狀態追蹤](docs/UI_UX_ISSUE_STATUS.md) - 進度追蹤
- [設計系統指南](DESIGN_SYSTEM_GUIDELINES.md) - 設計規範與最佳實踐

### 技術文檔
- [Agent Governance Framework](docs/GOVERNANCE_FRAMEWORK.md) - 多代理系統治理框架
- [Database Schema Analysis](DATABASE_SCHEMA_ANALYSIS.md) - 資料庫結構
- [環境變數 Schema](docs/config/env_schema.md) - 環境變數配置說明
- [測試覆蓋率報告](TEST_COVERAGE_IMPROVEMENT_REPORT.md) - 測試覆蓋率分析

---

## ✅ 上手檢查清單

完成以下檢查清單，確保您已準備好開始工作：

### 所有角色必須完成
- [ ] 閱讀 README.md
- [ ] 閱讀 CONTRIBUTING.md
- [ ] 設置本地開發環境
- [ ] 了解 Design PR vs Engineering PR 的區別
- [ ] 加入團隊溝通頻道（Slack/Discord）

### 設計師額外檢查
- [ ] 閱讀 UI/UX 快速上手指南
- [ ] 查看 Design Tokens
- [ ] 啟動 Storybook 並瀏覽組件庫
- [ ] 了解如何提交 Design PR

### 前端工程師額外檢查
- [ ] 閱讀 UI/UX 快速上手指南
- [ ] 啟動前端開發伺服器
- [ ] 啟動 Storybook
- [ ] 運行測試並確保通過
- [ ] 了解如何提交 Engineering PR

### 後端工程師額外檢查
- [ ] 閱讀 ARCHITECTURE.md
- [ ] 啟動 API 伺服器
- [ ] 運行測試並確保通過
- [ ] 了解 RFC 流程
- [ ] 了解如何提交 Engineering PR

### 產品經理額外檢查
- [ ] 閱讀 CTO Strategic Plan
- [ ] 查看 UI/UX Issue 狀態追蹤
- [ ] 了解 GitHub Issues 管理流程
- [ ] 了解 Milestones 與 Roadmap

---

**歡迎加入 MorningAI！如有任何問題，請隨時在團隊頻道詢問。** 🚀
