# morningai
Storage and inspection

> **⚠️ 設計優先期（Phase 1–8）：OpenAPI/資料欄位凍結中**  
> 在設計完成前，後端契約處於凍結狀態。如需異動 API 或資料庫欄位，請先提交 RFC 討論。  
> 設計 PR 僅含 UI/文案/樣式；工程 PR 僅含 API/邏輯實作。

## Verification Test
This is a simple change to verify repository access and PR creation functionality.

### Branch Protection Test
Testing Branch Protection Rules enforcement with required status checks.

## Status
![env-diagnose](https://github.com/RC918/morningai/actions/workflows/env-diagnose.yml/badge.svg)
![Coverage](https://img.shields.io/badge/coverage-41.61%25-yellow)
![Tests](https://img.shields.io/badge/tests-100%20passed-brightgreen)

## 開發貢獻流程

請參閱以下文件了解專案的開發規範與 CI/CD 流程：
- **[本地開發設定](docs/setup_local.md)** - 快速啟動指南與常見問題排除
- [貢獻規則](docs/CONTRIBUTING.md) - 分工規則、API 變更流程、驗收標準
- [CI 工作流矩陣](docs/ci_matrix.md) - 完整的 GitHub Actions 工作流說明、觸發條件、Branch Protection 規則
- [管理腳本指南](docs/scripts_overview.md) - 標準化管理腳本的使用方式與安全注意事項
- [環境變數 Schema](docs/config/env_schema.md) - 完整的環境變數配置說明（53 個變數）

## 核心文檔

- [Agent Governance Framework](docs/GOVERNANCE_FRAMEWORK.md) - 多代理系統治理框架（成本追蹤、權限管理、聲譽系統）
- [Worker Deployment Troubleshooting](docs/WORKER_DEPLOYMENT_TROUBLESHOOTING.md) - Worker 部署故障排除指南
- [Architecture](docs/ARCHITECTURE.md) - 系統架構文檔
- [Monitoring Setup](docs/MONITORING_SETUP.md) - 監控設置指南

## Milestones
- Phase 9 - Commercialization & PWA
- Phase 10 - Governance & Compliance

## Baseline Tag
- v8.0.0-handoff


## Release
[v9.0.0](https://github.com/RC918/morningai/releases/tag/v9.0.0)

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

