# MorningAI - World-Class AI Agent Ecosystem

**Vision**: Building the world's most advanced autonomous AI agent orchestration platform that seamlessly integrates development, operations, and business intelligence with human-in-the-loop governance.

> **🚀 Current Phase: Transformation to World-Class (Q4 2025 - Q2 2026)**  
> We are evolving from MVP to a production-ready, enterprise-grade AI agent ecosystem.  
> See [CTO Strategic Plan](CTO_STRATEGIC_PLAN_MVP_TO_WORLD_CLASS.md) for our roadmap.
>
> **📊 Strategic Integration**: Our roadmap has been validated through integration of three comprehensive assessments:
> - CTO Strategic Plan (6-month transformation)
> - CTO Strategic Assessment (20-week MVP excellence)
> - MVP Journey Report (project history & recommendations)
>
> All three documents converge on **identical P0 priorities**, validating our strategic direction.  
> See [Integration Analysis](CTO_STRATEGIC_INTEGRATION_ANALYSIS.md) for detailed comparison and refined timeline.

> **⚠️ Development Guidelines**  
> - **UI Components**: MorningAI 使用 `@morningai/shared-ui` 作為唯一的 UI 元件庫，開發新 UI 請參考 [Shared UI 使用指南](docs/shared-ui-guide.md)
> - For API/schema changes, submit an RFC first (see [RFC Template](.github/ISSUE_TEMPLATE/rfc.md))
> - Design PRs: UI/copy/styles only
> - Engineering PRs: API/logic only
> - See [CONTRIBUTING.md](CONTRIBUTING.md) for full guidelines

## Status & Metrics

![env-diagnose](https://github.com/RC918/morningai/actions/workflows/env-diagnose.yml/badge.svg)
![Coverage](https://img.shields.io/badge/coverage-41.61%25-yellow)
![Tests](https://img.shields.io/badge/tests-100%20passed-brightgreen)
![Phase](https://img.shields.io/badge/phase-8.0.0-blue)
![Uptime](https://img.shields.io/badge/uptime-90%25-yellow)

**Current State** (as of Oct 2025):
- **Test Coverage**: 41% → Target: 80% by Q2 2026
- **API Latency (p95)**: ~500ms → Target: <100ms by Q2 2026
- **Uptime**: 90% → Target: 99.9% by Q2 2026
- **Agent Capabilities**: Template-based → Target: LLM-driven autonomous agents

**Strategic Priorities** (Next 6 Months):
1. 🔒 **Security First**: Implement RLS, secret scanning, multi-instance deployment
2. 💰 **Commercialization**: Launch Stripe integration, usage tracking, billing
3. 🤖 **AI Enhancement**: Replace templates with GPT-4, enable multi-agent collaboration
4. 📊 **Production Excellence**: Achieve 99.9% uptime, <100ms latency, 80% test coverage
5. ✅ **Compliance**: Prepare for SOC2 Type II certification

## 架構概覽

MorningAI 採用三層分離架構，確保 Owner 和租戶的權限明確分割：

### 前端應用

1. **Owner Console（所有者後台）** (`handoff/20250928/40_App/owner-console/`)
   - 獨立的平台管理控制台
   - 僅 Owner 角色可訪問
   - 功能：Agent Governance、Tenant Management、System Monitoring、Platform Settings
   - 部署 URL: https://admin.gm365.me

2. **Tenant Dashboard（租戶端）** (`handoff/20250928/40_App/frontend-dashboard/`)
   - 租戶用戶使用的主要界面
   - 租戶用戶可訪問
   - 功能：Dashboard、Strategies、Approvals、History、Costs
   - 部署 URL: https://app.gm365.me

### 後端 API

- **API Backend** (`handoff/20250928/40_App/api-backend/`)
  - 共享後端服務
  - 基於角色的權限控制 (RLS)
  - Owner 專屬 endpoints: `/api/governance/*`, `/api/tenants/*`, `/api/monitoring/*`

詳細架構文檔：[Owner Console README](handoff/20250928/40_App/owner-console/README.md)

## 環境架構

MorningAI 採用多環境部署架構，確保開發、測試和生產環境的隔離：

### 🚀 Production Environment (生產環境)
- **Backend API**: https://morningai-backend-v2.onrender.com
- **Orchestrator API**: https://morningai-orchestrator-api.onrender.com
- **Tenant Dashboard**: https://app.gm365.me
- **Owner Console**: https://admin.gm365.me
- **Database**: Supabase PostgreSQL (production)
  - Project: `morningai` (qevmlbsunnwgrsdibdoi)
  - URL: https://qevmlbsunnwgrsdibdoi.supabase.co
  - Schema: Full production schema
- **Branch**: `main`

### 🧪 Staging Environment (測試環境) ✅
- **Backend API**: https://morningai-backend-v2-stg.onrender.com
- **Orchestrator API**: https://morningai-orchestrator-api-stg.onrender.com
- **Database**: Supabase PostgreSQL (staging)
  - Project: `morningai-staging` (dckisglnlemvpvmyvnut)
  - URL: https://dckisglnlemvpvmyvnut.supabase.co
  - Schema: Minimal test schema (tenants, user_profiles, agent_tasks)
  - Purpose: RLS testing and security validation
- **Redis**: Upstash (shared, key prefix: `stg:`)
- **Branch**: `develop`
- **Status**: ✅ Fully Operational
- **文檔**: [Staging Setup Guide](docs/ops/STAGING_SETUP_GUIDE.md)

⚠️ **Database Architecture Note**: MorningAI uses two separate Supabase databases for production and staging. Staging has a minimal schema focused on P0 security testing (RLS policies). This is intentional to keep the staging environment lightweight. See [docs/ENVIRONMENTS.md](docs/ENVIRONMENTS.md) for complete details.

### 💻 Local Development (本地開發)
- **Backend**: `http://localhost:8000`
- **Frontend**: `http://localhost:5173`
- **文檔**: [本地開發設定](docs/setup_local.md)

**部署流程**: Feature Branch → `develop` (Staging) → `main` (Production)

---

## 資料庫遷移 (Database Migrations)

MorningAI 使用 **Alembic 1.13.1** 進行資料庫 schema 版本管理。

### 快速開始

```bash
cd handoff/20250928/40_App/api-backend

# 設置 DATABASE_URL (開發環境使用 SQLite)
export DATABASE_URL="sqlite:////absolute/path/to/dev.db"

# 執行 migrations
alembic upgrade head

# 創建新 migration
alembic revision --autogenerate -m "描述變更"
```

### 關鍵資訊

- **Baseline Migration**: `91b9a61fcafa` (Initial baseline migration)
- **開發環境**: SQLite (使用絕對路徑避免 "no such table" 錯誤)
- **生產環境**: PostgreSQL (Supabase)
- **CI 驗證**: 每次 PR 自動測試 PostgreSQL 和 SQLite migrations

### Enum 值政策 ⚠️

**重要**: 所有 enum 必須使用小寫值並配置 `values_callable`:

```python
# ✅ 正確
agent_type = db.Column(
    db.Enum(AgentTypeDB, values_callable=lambda e: [i.value for i in e], name='agenttypedb'),
    nullable=False
)
```

### 相關文檔

- **[Database Migrations Guide](docs/database/MIGRATIONS.md)** - 完整的 Alembic 工作流程、最佳實踐和故障排除
- **[Onboarding Guide](docs/ONBOARDING_GUIDE.md)** - 包含 Alembic 設置說明
- **輔助腳本**: `scripts/run_alembic_migrations.sh`
- **整合測試**: `scripts/test_migration_data_insertion.py`

---

## Python 依賴管理

MorningAI 採用服務分離的依賴管理策略，確保每個服務只安裝所需的依賴：

### 📦 Requirements 結構

```
requirements.txt                                    # 共享開發/測試依賴（pytest, flake8, python-dotenv）
handoff/20250928/40_App/api-backend/requirements.txt    # Flask 後端服務依賴
orchestrator/requirements.txt                       # FastAPI Orchestrator 服務依賴
agents/*/requirements.txt                           # 各 Agent 服務依賴
```

### 🔧 安裝依賴

**Backend API 服務**:
```bash
cd handoff/20250928/40_App/api-backend
pip install -r requirements.txt
```

**Orchestrator 服務**:
```bash
cd orchestrator
pip install -r requirements.txt
pip install -e .  # 安裝 orchestrator 套件
```

**開發/測試工具** (root):
```bash
pip install -r requirements.txt  # pytest, flake8, python-dotenv
```

### ⚠️ 重要提示

- **不要**在 root 目錄直接 `pip install -r requirements.txt` 來運行服務
- 每個服務有獨立的 requirements.txt，包含該服務所需的所有依賴
- Root requirements.txt 僅用於開發/測試工具（pytest, flake8 等）
- CI/CD 會自動為每個服務安裝正確的依賴

---

## LHCI 資訊模式（非阻塞）

MorningAI 使用 Lighthouse CI 進行前端效能監控，目前處於「資訊模式」（非阻塞信號蒐集階段）。

### 🎯 目的

在高風險重構期間（如 Orchestrator 重構），LHCI 以非阻塞模式運行，持續蒐集效能信號但不阻塞開發流程。

### ⏰ 觸發條件

- **Nightly Schedule**: 每日 UTC 00:00 自動執行
- **Manual Trigger**: 透過 GitHub Actions 手動觸發 `workflow_dispatch`

### 🔧 執行限制

- **Timeout**: 12 分鐘（防止長時間掛起）
- **Number of Runs**: 1 次（加速執行）
- **Continue on Error**: 失敗不影響 workflow 狀態
- **Artifacts**: 始終上傳 LHCI 報告供分析

### 📊 手動觸發方式

1. 前往 [GitHub Actions](https://github.com/RC918/morningai/actions/workflows/lhci.yml)
2. 點擊 "Run workflow" 按鈕
3. 選擇 branch（通常是 `main`）
4. 點擊 "Run workflow" 確認

### 📁 查看結果

**方式 1: GitHub Artifacts**
1. 前往 [Actions 頁面](https://github.com/RC918/morningai/actions/workflows/lhci.yml)
2. 點擊最近的 workflow run
3. 下載 `lhci-artifacts-main` artifact
4. 解壓縮後查看 `.lighthouseci/` 目錄中的 HTML/JSON 報告

**方式 2: Tracking Issue**
- 查看 [LHCI Stabilization Tracking Issue #911](https://github.com/RC918/morningai/issues/911) 中的每日執行記錄

### 🎯 穩定化退出條件（2 週觀察期）

**階段 1: 穩定性驗證**
- ✅ 連續 5 次 nightly 執行成功（綠燈）
- ✅ Performance 中位數分數 ≥ 90

**階段 2: 恢復 PR 檢查（首週仍 continue-on-error: true）**
- 在 PR 上執行 LHCI，但失敗不阻塞合併
- 觀察 1 週，收集 flake 率數據

**階段 3: 完全恢復阻塞檢查**
- Flake 率 < 5%
- 移除 `continue-on-error: true`
- LHCI 失敗將阻塞 PR 合併

### 🔍 故障排除

**常見問題**:
- **Preview server 啟動失敗**: 檢查 `VITE_*` 環境變數是否正確設定
- **Port 衝突**: 確認 4173 port 未被佔用（已在 PR #894 修復）
- **Authentication 失敗**: 檢查 `TEST_EMAIL` 和 `TEST_PASSWORD` secrets
- **FCP timeout**: 檢查 CSS 是否有 `visibility: hidden` 或 `opacity: 0` 導致延遲

**相關文檔**:
- [Lighthouse CI 完整指南](docs/LIGHTHOUSE_CI_GUIDE.md)
- [LHCI Stabilization Tracking Issue #911](https://github.com/RC918/morningai/issues/911)

---

## 📚 相關文件 (Related Documentation)

### 🚀 新人必讀 (Getting Started)

**首次接觸專案？從這裡開始：**
1. **[Onboarding Guide](docs/ONBOARDING_GUIDE.md)** - 完整的新人入職指南，包含環境設置、開發流程、常見任務
2. **[Project Structure Report](docs/PROJECT_STRUCTURE_REPORT.md)** - 專案結構詳解，了解目錄組織和架構模式
3. **[Terminology Standards](docs/TERMINOLOGY.md)** - 術語對照表，統一中英文技術術語（必讀）

### 🔧 開發與部署 (Development & Deployment)

**開發貢獻流程：**
- **[本地開發設定](docs/setup_local.md)** - 快速啟動指南與常見問題排除
- **[Staging 環境指南](docs/ops/STAGING_SETUP_GUIDE.md)** - 完整的 staging 環境設置與使用指南
- **[貢獻規則](docs/CONTRIBUTING.md)** - 分工規則、API 變更流程、驗收標準
- **[環境變數 Schema](config/env.schema.yaml)** - 環境變數配置的單一真源（53 個變數）

**CI/CD 與腳本：**
- [CI 工作流矩陣](docs/ci_matrix.md) - 完整的 GitHub Actions 工作流說明、觸發條件、Branch Protection 規則
- [管理腳本指南](docs/scripts_overview.md) - 標準化管理腳本的使用方式與安全注意事項
- [驗證腳本](scripts/verify_system_state.sh) - 系統狀態驗證腳本（30 項檢查）

### 🏗️ 架構與設計 (Architecture & Design)

**系統架構：**
- [Architecture](docs/ARCHITECTURE.md) - 系統架構文檔
- [Architecture Decision Records (ADRs)](docs/adr/README.md) - 重要架構決策記錄
  - [ADR-001: Dual Orchestrator Architecture](docs/adr/001-dual-orchestrator-architecture.md)
  - [ADR-002: Producer-Consumer Architecture](docs/adr/002-producer-consumer-architecture.md)
  - [ADR-003: Backend of Record](docs/adr/003-backend-of-record.md)

**治理與監控：**
- [Agent Governance Framework](docs/GOVERNANCE_FRAMEWORK.md) - 多代理系統治理框架（成本追蹤、權限管理、聲譽系統）
- [Monitoring Setup](docs/MONITORING_SETUP.md) - 監控設置指南

### 🔒 安全與合規 (Security & Compliance)

- **[Secret Rotation Policy](docs/SECRET_ROTATION_POLICY.md)** - 季度密鑰輪換程序、SLO、演練
- **[Secret Scanning Guide](docs/SECRET_SCANNING_GUIDE.md)** - 防止代碼中暴露密鑰
- **[Redis 安全要求](docs/REDIS_SECURITY.md)** - CVE-2025-49844 (RediShell) 防護指南
- [Security Advisor 修復指南](SECURITY_ADVISOR_FIXES.md) - Supabase 安全警告處理說明

### 📊 測試與品質 (Testing & Quality)

- **[Test Statistics Explanation](docs/TEST_STATISTICS_EXPLANATION.md)** - 測試統計數據說明（487 vs 926 vs 23）
- [Test Coverage Improvement Plan](docs/TEST_COVERAGE_IMPROVEMENT_PLAN.md) - 12 週路線圖達到 60%+ 覆蓋率
- [Testing Documentation](docs/TESTING.md) - 測試文檔

### 🎨 UI/UX 設計系統 (Design System)

- **[UI/UX 快速上手指南](docs/UI_UX_QUICKSTART.md)** - ⚡ 5 分鐘快速入門（新人必讀）
- **[UI/UX 速查表](docs/UI_UX_CHEATSHEET.md)** - 📋 一頁速查表（常用命令、組件、Tokens）
- **[UI/UX 資源指南](docs/UI_UX_RESOURCES.md)** - 🎨 中心化資源索引（設計系統、組件庫、預覽環境）
- [設計系統指南](DESIGN_SYSTEM_GUIDELINES.md) - 設計規範與最佳實踐

### 📈 戰略與路線圖 (Strategy & Roadmap)

- [CTO Strategic Plan](CTO_STRATEGIC_PLAN_MVP_TO_WORLD_CLASS.md) - 6 個月轉型計畫（MVP → World-Class）
- [CTO Technical Assessment](CTO_TECHNICAL_ASSESSMENT_REPORT.md) - 技術評估報告
- [Strategic Integration Analysis](CTO_STRATEGIC_INTEGRATION_ANALYSIS.md) - 戰略整合分析
- [Strategic Roadmap](.github/projects/cto-strategic-roadmap-q4-2025-q2-2026.yml) - Q4 2025 - Q2 2026 詳細時間表

---

## 核心文檔

### 架構與治理
- [Agent Governance Framework](docs/GOVERNANCE_FRAMEWORK.md) - 多代理系統治理框架（成本追蹤、權限管理、聲譽系統）
- [Architecture](docs/ARCHITECTURE.md) - 系統架構文檔
- [Monitoring Setup](docs/MONITORING_SETUP.md) - 監控設置指南

### UI/UX 設計系統

**🎉 8-Week Roadmap 已完成！** (2025-10-24)
- ✅ **18/18 Issues 完成** - 100% 完成率
- ✅ **16 個 PRs 合併** - 10,000+ 行代碼
- ✅ **完整測試框架** - 可用性測試、A/B 測試、指標分析

**🎨 Phase 1 Week 1-3 完成！** (2025-10-25)
- ✅ **5 個核心設計系統** - Apple-Level 設計系統基礎
- ✅ **Spring 動畫系統** - iOS 風格彈性動畫
- ✅ **2500+ 行文檔** - 完整的設計系統文檔
- ✅ **80+ Storybook stories** - 互動式設計系統展示
- ✅ **100% CI 通過率** - 所有 PR 品質評分 60/60

**🎉 Phase 2 Week 4-7 完成！** (2025-10-26)
- ✅ **12 個 Apple 組件** - 完整的 Apple-Level 組件系統
- ✅ **完整遷移** - 所有頁面遷移至新組件
- ✅ **165 個單元測試** - 100% 通過率
- ✅ **60+ Storybook stories** - 互動式組件展示
- ✅ **3000+ 行文檔** - 完整的組件文檔
- ✅ **4 個 Provider 整合** - 全域 Hook 支援

**🎉 Phase 3 Week 8-10 完成！** (2025-10-26)
- ✅ **WCAG AAA 合規** - 完整的無障礙支援
- ✅ **10 個組件增強** - 所有 Apple 組件無障礙優化
- ✅ **自動化測試** - axe-core 整合
- ✅ **2,500+ 行測試文檔** - 螢幕閱讀器與鍵盤導航測試指南
- ✅ **4,643 行 Week 10 文檔** - 性能優化、UX 測試、視覺一致性、跨平台兼容性

**核心設計系統**:
1. **[字體系統](docs/UX/TYPOGRAPHY_SYSTEM.md)** - 13 級字體大小，5 種字重，3 種行高
2. **[色彩系統](docs/UX/COLOR_SYSTEM.md)** - 5 種情感色彩，完整語義色彩，深色模式
3. **[材質系統](docs/UX/MATERIAL_SYSTEM.md)** - 5 級毛玻璃效果，深色模式支援
4. **[陰影系統](docs/UX/SHADOW_SYSTEM.md)** - 5 級陰影，彩色陰影，深色模式支援
5. **[間距系統](docs/UX/SPACING_SYSTEM.md)** - 8 級間距，8px 網格，響應式支援

**🚀 新人快速上手**:
- **[UI/UX 快速上手指南](docs/UI_UX_QUICKSTART.md)** - ⚡ 5 分鐘快速入門（新人必讀）
- **[UI/UX 速查表](docs/UI_UX_CHEATSHEET.md)** - 📋 一頁速查表（常用命令、組件、Tokens）

**核心文檔**:
- **[UI/UX 資源指南](docs/UI_UX_RESOURCES.md)** - 🎨 中心化資源索引（設計系統、組件庫、預覽環境）
- **[UI/UX Issue 狀態追蹤](docs/UI_UX_ISSUE_STATUS.md)** - 📊 完整進度追蹤（100% 完成）
- [全面 UI/UX 審查報告](docs/UX/COMPREHENSIVE_UI_UX_AUDIT_REPORT.md) - 83/100 分評估報告
- [設計系統增強路線圖](docs/UX/DESIGN_SYSTEM_ENHANCEMENT_ROADMAP.md) - 8 週執行計畫
- [Week 7-8 完成報告](docs/UX/WEEK_7_8_COMPLETION_REPORT.md) - 測試與分析框架實作報告
- [設計系統指南](DESIGN_SYSTEM_GUIDELINES.md) - 設計規範與最佳實踐

**Phase 3 文檔** (Week 8-10):
- [WCAG AAA 合規文檔](handoff/20250928/40_App/frontend-dashboard/docs/WCAG_AAA_COMPLIANCE.md) - 完整的無障礙規範
- [Phase 3 完成報告](handoff/20250928/40_App/frontend-dashboard/docs/PHASE3_COMPLETION_REPORT.md) - 1,005 行完整總結
- [路線圖完成狀態](handoff/20250928/40_App/frontend-dashboard/docs/ROADMAP_COMPLETION_STATUS.md) - 10 週路線圖總結
- [性能優化建議](handoff/20250928/40_App/frontend-dashboard/docs/PHASE3_WEEK10_PERFORMANCE_OPTIMIZATION.md) - 616 行優化指南
- [UX 測試清單](handoff/20250928/40_App/frontend-dashboard/docs/PHASE3_WEEK10_UX_TESTING_CHECKLIST.md) - 691 行測試清單
- [視覺一致性審查](handoff/20250928/40_App/frontend-dashboard/docs/PHASE3_WEEK10_VISUAL_CONSISTENCY_AUDIT.md) - 785 行審查報告
- [跨平台兼容性指南](handoff/20250928/40_App/frontend-dashboard/docs/PHASE3_WEEK10_CROSS_PLATFORM_COMPATIBILITY.md) - 854 行兼容性指南

**已實現功能**:
- ✅ Landing Page & SEO 優化
- ✅ 空狀態與骨架屏
- ✅ 移動端優化
- ✅ 動效治理
- ✅ Token 作用域化
- ✅ Storybook 文檔系統
- ✅ 撤銷/重做功能
- ✅ 全局搜尋 (Cmd+K)
- ✅ 暗色主題
- ✅ 微互動增強
- ✅ 性能優化（圖片懶加載、字體優化、WebP 支援）
- ✅ 可用性測試框架（SUS/NPS 問卷）
- ✅ A/B 測試系統（統計分析）
- ✅ 指標分析框架（Web Vitals 監控）
- ✅ Apple 組件系統（12 個組件：Button、Input、Toast、Modal、Sheet、TabBar、SegmentedControl、LiveActivity、ControlCenter、Spotlight、ActionSheet、Picker）
- ✅ WCAG AAA 無障礙合規（10 個組件增強、axe-core 自動化測試、無障礙設定面板）
- ✅ 手動測試指南（2,500+ 行：螢幕閱讀器測試、鍵盤導航測試）

### 安全與決策
- [Security Advisor 修復指南](SECURITY_ADVISOR_FIXES.md) - Supabase 安全警告處理說明
- [技術決策記錄](docs/TECHNICAL_DECISIONS.md) - 重要技術決策的背景、理由和後果
- **[Redis 安全要求](docs/REDIS_SECURITY.md)** - CVE-2025-49844 (RediShell) 防護指南

### 故障排除
- [Worker Deployment Troubleshooting](docs/WORKER_DEPLOYMENT_TROUBLESHOOTING.md) - Worker 部署故障排除指南

## Milestones & Roadmap

**Current Phase**: Phase 8 (v8.0.0-handoff) - MVP Foundation Complete

**Transformation Roadmap** (Q4 2025 - Q2 2026):
- **Q4 2025**: Security hardening, Stripe integration, AI enhancement foundations
- **Q1 2026**: Multi-agent collaboration, production excellence, compliance preparation
- **Q2 2026**: Advanced AI capabilities, scale to 99.9% uptime, SOC2 Type I certification

**Key Milestones**:
- ✅ Phase 8: Multi-tenant architecture, agent sandboxes, governance framework
- 🚧 Phase 9: Commercialization (Stripe), PWA, advanced agent intelligence
- 📋 Phase 10: Governance maturity, compliance (SOC2), enterprise features

See [Strategic Roadmap](.github/projects/cto-strategic-roadmap-q4-2025-q2-2026.yml) for detailed timeline.

## Releases
- **Latest**: [v9.0.0](https://github.com/RC918/morningai/releases/tag/v9.0.0)
- **Baseline**: v8.0.0-handoff

## Agent Sandbox 部署狀態

Morning AI 已部署兩個 AI Agent Sandbox 到 Fly.io，提供安全隔離的開發和運維能力：

### Dev_Agent Sandbox
- **URL**: https://morningai-sandbox-dev-agent.fly.dev/
- **功能**: VSCode Server、LSP、Git、IDE、FileSystem 工具
- **用途**: 自動化代碼開發、Bug 修復、PR 創建
- **文檔**: [Dev_Agent README](agents/dev_agent/README.md)

### Ops_Agent Sandbox
- **URL**: https://morningai-sandbox-ops-agent.fly.dev/
- **功能**: 性能監控、容量分析、系統運維
- **用途**: 自動化運維、事件響應、性能優化
- **文檔**: [Ops_Agent README](agents/ops_agent/README.md)

**架構文檔**: [Agent Sandbox Architecture](docs/agent-sandbox-architecture.md)  
**總成本**: ~$4/月（閒置時自動縮放至 $0）

