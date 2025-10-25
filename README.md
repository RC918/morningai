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

1. **Owner Console** (`handoff/20250928/40_App/owner-console/`)
   - 獨立的平台管理控制台
   - 僅 Owner 角色可訪問
   - 功能：Agent Governance、Tenant Management、System Monitoring、Platform Settings
   - 部署 URL: `admin.morningai.com` 或 `owner.morningai.com`

2. **Tenant Dashboard** (`handoff/20250928/40_App/frontend-dashboard/`)
   - 租戶使用的主要界面
   - 租戶用戶可訪問
   - 功能：Dashboard、Strategies、Approvals、History、Costs
   - 部署 URL: `dashboard.morningai.com` 或 `app.morningai.com`

### 後端 API

- **API Backend** (`handoff/20250928/40_App/api-backend/`)
  - 共享後端服務
  - 基於角色的權限控制 (RLS)
  - Owner 專屬 endpoints: `/api/governance/*`, `/api/tenants/*`, `/api/monitoring/*`

詳細架構文檔：[Owner Console README](handoff/20250928/40_App/owner-console/README.md)

## 開發貢獻流程

請參閱以下文件了解專案的開發規範與 CI/CD 流程：
- **[本地開發設定](docs/setup_local.md)** - 快速啟動指南與常見問題排除
- [貢獻規則](docs/CONTRIBUTING.md) - 分工規則、API 變更流程、驗收標準
- [CI 工作流矩陣](docs/ci_matrix.md) - 完整的 GitHub Actions 工作流說明、觸發條件、Branch Protection 規則
- [管理腳本指南](docs/scripts_overview.md) - 標準化管理腳本的使用方式與安全注意事項
- [環境變數 Schema](docs/config/env_schema.md) - 完整的環境變數配置說明（53 個變數）

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

**🎨 Phase 1 Week 1 完成！** (2025-10-25)
- ✅ **5 個核心設計系統** - Apple-Level 設計系統基礎
- ✅ **2500+ 行文檔** - 完整的設計系統文檔
- ✅ **80+ Storybook stories** - 互動式設計系統展示
- ✅ **100% CI 通過率** - 所有 PR 品質評分 60/60

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
- **文檔**: [Ops_Agent README](agents/ops_agent/)

**架構文檔**: [Agent Sandbox Architecture](docs/agent-sandbox-architecture.md)  
**總成本**: ~$4/月（閒置時自動縮放至 $0）

