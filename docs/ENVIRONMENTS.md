# MorningAI Environment Architecture

**Last Updated**: 2025-12-09  
**Document Version**: 2.8  
**Related Documents**: 
- [PROJECT_STRUCTURE_REPORT.md](PROJECT_STRUCTURE_REPORT.md) - 專案結構報告
- [PROJECT_DEEP_ANALYSIS.md](../PROJECT_DEEP_ANALYSIS.md) - 深度解析報告
- [ONBOARDING_GUIDE.md](./ONBOARDING_GUIDE.md) - 新人上手指南

---

⚠️ **SECURITY NOTICE**: This document contains references to sensitive environment variables.
- 🔒 Variables marked with lock icon are **SECRETS** - never log, commit, or share
- All example values are placeholders - generate unique secrets for each environment
- Rotate secrets immediately if exposed
- Use `python -c "import secrets; print(secrets.token_urlsafe(64))"` to generate secure secrets

---

## Overview

MorningAI uses a multi-environment deployment architecture to ensure safe development, testing, and production workflows. This document provides a comprehensive overview of all environments, their configurations, and deployment processes.

**近期重要更新** (2025-12-07 至 2025-12-09):

*DeepWiki 整合:*
- **PR #2156**: feat(deepwiki): integrate DeepWiki session insights into AutonomousExecutor
  - Path: `handoff/20250928/40_App/orchestrator/meta_agent/autonomous_executor.py`
  - 影響：DeepWiki 知識庫整合，增強 session 上下文
- **PR #2157**: feat(orchestrator): integrate DeepWiki with AutonomousExecutor
  - Path: `handoff/20250928/40_App/orchestrator/`
  - 影響：完整的 DeepWiki orchestrator 整合
- **PR #2164**: fix(deepwiki): add retry logic and rate limiting
  - Path: `handoff/20250928/40_App/orchestrator/`
  - 影響：改善 DeepWiki API 呼叫的可靠性，新增重試邏輯和速率限制
- **PR #2163**: feat(api): add DeepWiki API endpoints for knowledge base queries
  - Path: `handoff/20250928/40_App/api-backend/`
  - 影響：新增 DeepWiki 知識庫查詢 API 端點
- **PR #2169**: feat(owner-console): add SessionInsights component for DeepWiki insights
  - Path: `handoff/20250928/40_App/owner-console/src/components/`
  - 影響：顯示 DeepWiki session 洞察的 UI 元件

*Sessions UI 與 HITL 優化:*
- **PR #2170**: feat(owner-console): HITL approval UI/UX optimization
  - Path: `handoff/20250928/40_App/owner-console/src/components/`
  - 影響：改善 Human-in-the-Loop 審批工作流程 UX
- **PR #2173**: feat(i18n): add SessionInsights translation keys and unit tests
  - Path: `handoff/20250928/40_App/owner-console/src/i18n/`
  - 影響：SessionInsights 元件的國際化支援
- **PR #2175**: feat(owner-console): add SessionCommandInput for interactive session commands
  - Path: `handoff/20250928/40_App/owner-console/src/components/`
  - 影響：新增互動式命令輸入用於 session 管理
- **PR #2182**: refactor(owner-console): tidy SessionCommandInput constants and props
  - Path: `handoff/20250928/40_App/owner-console/src/components/`
  - 影響：程式碼清理和改善 prop 定義
- **PR #2188**: test(owner-console): add unit tests for SessionCommandInput
  - Path: `handoff/20250928/40_App/owner-console/src/components/`
  - 影響：SessionCommandInput 元件的測試覆蓋
- **PR #2189**: feat(owner-console): persist command history with localStorage
  - Path: `handoff/20250928/40_App/owner-console/src/components/`
  - 影響：跨 session 的命令歷史持久化
- **PR #2225**: fix(owner-console): fix ApprovalQueue TDZ error and improve auto-refresh
  - Path: `handoff/20250928/40_App/owner-console/src/components/`
  - 影響：修復 Temporal Dead Zone 錯誤並改善自動刷新行為
- **PR #2234**: fix(owner-console): fix console warnings and session card layout issues
  - Path: `handoff/20250928/40_App/owner-console/src/components/`
  - 影響：修復 console 警告並改善 session 卡片佈局
- **PR #2279**: feat(owner-console): add SessionStatusCard component with standardized design spec
  - Path: `handoff/20250928/40_App/owner-console/src/components/`
  - 影響：新增標準化 SessionStatusCard 元件以保持 UI 一致性

*CSRF Token 管理:*
- **PR #2237**: fix(owner-console): fix CSRF token sync issue causing 403 errors
  - Path: `handoff/20250928/40_App/owner-console/src/lib/csrf-token.ts`
  - 影響：修復 CSRF token 同步問題，防止 403 錯誤
- **PR #2238**: refactor(owner-console): unify CSRF token management
  - Path: `handoff/20250928/40_App/owner-console/src/lib/csrf-token.ts`
  - 影響：統一 CSRF token 管理，支援 Auth 和 API Client 模式
- **PR #2239**: docs(owner-console): add CSRF token mode selection warning
  - Path: `handoff/20250928/40_App/owner-console/src/lib/csrf-token.ts`
  - 影響：新增 CSRF token 模式選擇警告文檔
- **PR #2240**: docs(owner-console): add warning comment for CSRF token mode selection
  - Path: `handoff/20250928/40_App/owner-console/src/lib/csrf-token.ts`
  - 影響：CSRF token 模式選擇的後續文檔

*AI Reviewer 與 Comment Triage:*
- **PR #2244**: feat(orchestrator): fix AI Reviewer comment intake mechanism
  - Path: `handoff/20250928/40_App/orchestrator/nodes/review_intake.py`
  - 影響：修復 AI Reviewer bot 白名單和評論接收機制
- **PR #2246**: feat(orchestrator): implement Comment Triage Agent for AI reviewer comments
  - Path: `handoff/20250928/40_App/orchestrator/nodes/comment_triage.py`
  - 影響：新增 Comment Triage Agent 用於分類和優先處理 AI 審查評論

*Review Follow-up 與 Internal Reviewer (Phase 7):*
- **PR #2257**: feat(orchestrator): implement Review Follow-up Mode (Issue #2211)
  - Path: `handoff/20250928/40_App/orchestrator/nodes/review_follow_up.py`
  - 影響：新增 Review Follow-up Mode 追蹤和處理審查評論
- **PR #2262**: feat(orchestrator): implement Internal Reviewer Agent re-review mechanism (Issue #2212)
  - Path: `handoff/20250928/40_App/orchestrator/nodes/internal_review_node.py`
  - 影響：Internal Reviewer Agent 具備重新審查能力
- **PR #2267**: refactor(orchestrator): add required field validation in internal_review_node (Issue #2263)
  - Path: `handoff/20250928/40_App/orchestrator/nodes/internal_review_node.py`
  - 影響：新增 internal review node 的必填欄位驗證
- **PR #2268**: feat(orchestrator): add configurable PARTIAL agreement policy (Issue #2264)
  - Path: `handoff/20250928/40_App/orchestrator/nodes/internal_review_node.py`
  - 影響：可配置的 PARTIAL 同意策略用於內部審查
- **PR #2269**: docs(orchestrator): document internal_review_node vs reviewer_node responsibilities (Issue #2265)
  - Path: `handoff/20250928/40_App/orchestrator/docs/`
  - 影響：文檔化節點職責分工

*多信號觸發與 Rollout Tracker (Phase 7):*
- **PR #2275**: feat(orchestrator): implement Multi-Signal Trigger System (Issue #2213)
  - Path: `handoff/20250928/40_App/orchestrator/multi_signal_trigger.py`
  - 影響：多信號觸發系統用於自動化工作流程啟動
- **PR #2278**: feat(orchestrator): implement LangGraph 100% Rollout Tracker (Issue #2214)
  - Path: `handoff/20250928/40_App/orchestrator/rollout_tracker.py`
  - 影響：LangGraph 推出追蹤器，支援指標和儀表板
- **PR #2284**: feat(orchestrator): integrate RolloutTracker into worker.py (Issue #2280)
  - Path: `handoff/20250928/40_App/orchestrator/redis_queue/worker.py`
  - 影響：RolloutTracker 整合到 worker 用於生產監控
- **PR #2288**: docs: update milestones document with Dec 2025 progress (Issue #2215)
  - Path: `docs/MILESTONES.md`
  - 影響：更新里程碑文件，Phase 7 完成狀態

*Owner Console UI 重構:*
- **PR #2245**: refactor(owner-console): move settings and logout to user dropdown menu
  - Path: `handoff/20250928/40_App/owner-console/src/components/`
  - 影響：改善導航 UX，新增用戶下拉選單
- **PR #2256**: refactor(owner-console): DashboardHeader cleanup and testing
  - Path: `handoff/20250928/40_App/owner-console/src/components/DashboardHeader.jsx`
  - 影響：程式碼清理和改善 DashboardHeader 測試覆蓋
- **PR #2261**: refactor(owner-console): Sidebar UX optimization - single-line items and tooltips
  - Path: `handoff/20250928/40_App/owner-console/src/components/Sidebar.jsx`
  - 影響：改善 Sidebar UX，單行項目和工具提示
- **PR #2266**: refactor(owner-console): implement single-layer Header + Sidebar architecture
  - Path: `handoff/20250928/40_App/owner-console/src/components/`
  - 影響：簡化 Header 和 Sidebar 架構
- **PR #2270**: fix(shared-ui): add arrowClassName prop to Tooltip for customizable arrow styling
  - Path: `packages/shared-ui/src/components/ui/tooltip.tsx`
  - 影響：增強 Tooltip 元件，支援自訂箭頭樣式

*CI/CD 與測試基礎設施:*
- **PR #2174**: feat(ci): enable TypeScript Strict Mode baseline tracking for all packages
  - Path: `.github/workflows/`
  - 影響：所有套件的 TypeScript Strict Mode 基線追蹤
- **PR #2183**: fix(orchestrator): fix failing tests in visual_verification and project_engineer
  - Path: `handoff/20250928/40_App/orchestrator/`
  - 影響：修復 visual verification 和 project engineer 模組的失敗測試
- **PR #2190**: fix(orchestrator): increase performance test threshold for planner node
  - Path: `handoff/20250928/40_App/orchestrator/`
  - 影響：調整 planner node 的效能測試閾值
- **PR #2194**: fix(orchestrator): add rate limit mock to TestExecute tests
  - Path: `handoff/20250928/40_App/orchestrator/`
  - 影響：修復測試不穩定性，新增速率限制 mock
- **PR #2200**: test(orchestrator): add comprehensive tests for langgraph_orchestrator.py
  - Path: `handoff/20250928/40_App/orchestrator/tests/`
  - 影響：LangGraph orchestrator 的全面測試覆蓋
- **PR #2233**: test(api-backend): add comprehensive tests for sentry_integration.py
  - Path: `handoff/20250928/40_App/api-backend/`
  - 影響：Sentry 整合模組的測試覆蓋
- **PR #2235**: test(orchestrator): add security rules tests for project_engineer/agent.py
  - Path: `handoff/20250928/40_App/orchestrator/`
  - 影響：project engineer agent 的安全規則測試覆蓋
- **PR #2236**: test(owner-console): add comprehensive tests for LoginPage component
  - Path: `handoff/20250928/40_App/owner-console/src/pages/`
  - 影響：LoginPage 元件的測試覆蓋

*Backend 與基礎設施:*
- **PR #2184**: feat(api-backend): add /api/sessions/{id}/command endpoint
  - Path: `handoff/20250928/40_App/api-backend/`
  - 影響：新增 session 命令執行 API 端點
- **PR #2197**: feat(orchestrator): add A/B testing metrics collection and analysis framework
  - Path: `handoff/20250928/40_App/orchestrator/`
  - 影響：A/B 測試指標框架用於實驗分析
- **PR #2204**: fix: reduce noisy Sentry alerts for expected error conditions
  - Path: `handoff/20250928/40_App/api-backend/`
  - 影響：減少預期錯誤的 Sentry 警報噪音
- **PR #2218**: feat(orchestrator): complete Wave 1 Phase 7 prerequisites
  - Path: `handoff/20250928/40_App/orchestrator/`
  - 影響：完成 Phase 7 的 Wave 1 先決條件
- **PR #2224**: feat(orchestrator): add retry and rate limiting to OutboundNotifier
  - Path: `handoff/20250928/40_App/orchestrator/`
  - 影響：改善出站通知的可靠性
- **PR #2231**: feat(orchestrator): Wave 3 Failure Learning Enhancement
  - Path: `handoff/20250928/40_App/orchestrator/`
  - 影響：增強失敗學習能力
- **PR #2232**: fix(api-backend): add Upstash Redis adapter for scan_iter compatibility
  - Path: `handoff/20250928/40_App/api-backend/`
  - 影響：修復 Upstash Redis scan_iter 相容性

*文檔:*
- **PR #2193**: docs: align documentation with actual implementation
  - Path: `docs/`
  - 影響：文檔與當前實作對齊

**近期重要更新** (2025-12-08 至 2025-12-09):

*Phase 7: 生態系閉環 (AI Review Closed Loop) 完成:*
- **PR #2257**: feat(orchestrator): implement Review Follow-up Mode (Issue #2211)
  - Path: `handoff/20250928/40_App/orchestrator/nodes/review_follow_up.py`
  - 影響：新增 Review Follow-up Mode 追蹤和處理審查評論
- **PR #2262**: feat(orchestrator): implement Internal Reviewer Agent re-review mechanism (Issue #2212)
  - Path: `handoff/20250928/40_App/orchestrator/nodes/internal_review_node.py`
  - 影響：Internal Reviewer Agent 具備重新審查能力
- **PR #2275**: feat(orchestrator): implement Multi-Signal Trigger System (Issue #2213)
  - Path: `handoff/20250928/40_App/orchestrator/multi_signal_trigger.py`
  - 影響：多信號觸發系統用於自動化工作流程啟動
- **PR #2278**: feat(orchestrator): implement LangGraph 100% Rollout Tracker (Issue #2214)
  - Path: `handoff/20250928/40_App/orchestrator/rollout_tracker.py`
  - 影響：LangGraph 推出追蹤器，支援指標和儀表板
- **PR #2284**: feat(orchestrator): integrate RolloutTracker into worker.py (Issue #2280)
  - Path: `handoff/20250928/40_App/orchestrator/redis_queue/worker.py`
  - 影響：RolloutTracker 整合到 worker 用於生產監控
- **PR #2288**: docs: update milestones document with Dec 2025 progress (Issue #2215)
  - Path: `docs/MILESTONES.md`
  - 影響：更新里程碑文件，Phase 7 完成狀態

*CSRF Token 管理統一:*
- **PR #2237**: fix(owner-console): fix CSRF token sync issue causing 403 errors
  - Path: `handoff/20250928/40_App/owner-console/src/lib/csrf-token.ts`
  - 影響：修復 CSRF token 同步問題，防止 403 錯誤
- **PR #2238**: refactor(owner-console): unify CSRF token management
  - Path: `handoff/20250928/40_App/owner-console/src/lib/csrf-token.ts`
  - 影響：統一 CSRF token 管理，支援 Auth 和 API Client 模式
- **PR #2239, #2240**: docs(owner-console): add CSRF token mode selection warning
  - 影響：新增 CSRF token 模式選擇警告文檔

*AI Reviewer & Comment Triage:*
- **PR #2244**: feat(orchestrator): fix AI Reviewer comment intake mechanism
  - Path: `handoff/20250928/40_App/orchestrator/nodes/review_intake.py`
  - 影響：修復 AI Reviewer bot 白名單和評論接收機制
- **PR #2246**: feat(orchestrator): implement Comment Triage Agent for AI reviewer comments
  - Path: `handoff/20250928/40_App/orchestrator/nodes/comment_triage.py`
  - 影響：新增 Comment Triage Agent 用於分類和優先處理 AI 審查評論

*Sessions UI & 基礎設施:*
- **PR #2279**: feat(owner-console): add SessionStatusCard component with standardized design spec
  - Path: `handoff/20250928/40_App/owner-console/src/components/`
  - 影響：新增標準化 SessionStatusCard 元件
- **PR #2232**: fix(api-backend): add Upstash Redis adapter for scan_iter compatibility
  - Path: `handoff/20250928/40_App/api-backend/`
  - 影響：修復 Upstash Redis scan_iter 相容性
- **PR #2204**: fix: reduce noisy Sentry alerts for expected error conditions
  - 影響：減少預期錯誤的 Sentry 警報噪音

**近期重要更新** (2025-12-06 至 2025-12-07):

*VSCode/MCP Integration & Meta-Agent Production Wiring:*
- **PR #2114**: feat(meta-agent): integrate VSCodeIDEService into production code
  - Path: `handoff/20250928/40_App/orchestrator/meta_agent/autonomous_executor.py`
  - 影響：將 VMProvisioner 和 VSCodeIDEService 整合到 AutonomousExecutor；新增 VM/IDE 生命週期管理
- **PR #2067**: feat(meta-agent): implement MCP HTTP client for cloud IDE integration
  - Path: `handoff/20250928/40_App/orchestrator/meta_agent/vscode_ide.py`
  - 影響：核心 MCP HTTP 客戶端實作
- **PR #2106**: perf(vscode-ide): share aiohttp ClientSession for connection reuse
  - 影響：TCP 連線池和 DNS 快取以提升 MCP 效能
- **PR #2102**: refactor(vscode-ide): extract constants and use exponential backoff
  - 影響：可配置的 MCP 超時、重試和錯誤日誌截斷常數
- **PR #2077**: security(vscode-ide): truncate error logs to prevent sensitive data leakage
  - 影響：錯誤日誌截斷至 500 字元以防止憑證洩漏

*VSCode/MCP Documentation & Infrastructure:*
- **PR #2101**: docs(meta-agent): add Tier 2 VSCode/VM documentation
  - Path: `handoff/20250928/40_App/orchestrator/docs/` (新目錄)
  - 新增檔案：`TERMINAL_ACCESS.md`, `VM_LOCKING_DESIGN.md`, `VM_PROVISIONER_LIFECYCLE.md`
- **PR #2115**: docs(orchestrator): add cross-process limitation note and environment settings
  - 影響：記錄 VM 佈建的跨進程限制和終端機能力環境設定
- **PR #2110**: test(vscode-ide): use mocker.patch.object() for cleaner test mocking
  - Path: `handoff/20250928/40_App/orchestrator/requirements-test.txt` (新增 pytest-mock)

*Documentation Auto-Generation Security:*
- **PR #2103**: refactor(orchestrator): improve documentation auto-generation security
  - Path: `handoff/20250928/40_App/orchestrator/`
  - 新增環境變數：`ORCHESTRATOR_DOCS_MAX_PRS_PER_HOUR` (integer, default: 3) - 每小時最大文件 PR 數量限制
  - 影響：防止衝突的 FAQ PR；新增主題 slug 生成和內容驗證

*Owner Console Sessions UI & Performance:*
- **PR #2063**: feat(owner-console): integrate ConfidenceApproval and FileDiffViewer
  - 影響：Sessions 頁面現在顯示信心分數和檔案差異
- **PR #2088**: refactor(owner-console): Sessions.jsx defensive code improvements
  - 影響：提取 `MEDIUM_CONFIDENCE_THRESHOLD` 常數；改善 null 安全性
- **PR #2089**: perf(owner-console): optimize FCP with lazy loading
  - 影響：延遲載入 TaskPlanViewer 和 TaskPlanEditor 以加快首次繪製
- **PR #2087**: a11y(owner-console): improve keyboard accessibility for drag-and-drop
  - 影響：任務重新排序的鍵盤導航支援

*Design System & Storybook:*
- **PR #2068**: fix(owner-console): add base tokens to @theme for shared-ui Switch
  - 影響：修復 Switch 元件在深色/淺色模式下的可見性
- **PR #2084**: docs(shared-ui): add Switch Storybook visual verification story
  - Path: `packages/shared-ui/src/components/ui/switch.stories.tsx` (新檔案)
- **PR #2083**: docs(owner-console): add Storybook stories for task plan components
- **PR #2061**: chore(owner-console): remove dead theme.css file
  - Path: `handoff/20250928/40_App/owner-console/src/styles/theme.css` (已移除)

*Security & Testing:*
- **PR #2052**: fix(meta-agent): add TOCTOU defense in save_state()
  - 影響：原子檔案寫入防止狀態持久化中的競爭條件
- **PR #2078**: test(owner-console): add XSS protection tests for TestResultsPanel
- **PR #2079**: test(orchestrator): add unit tests for update_error_fix_pair

**近期重要更新** (2025-12-03 至 2025-12-05):

*Refactor Agent & TS Strict Mode Automation:*
- **PR #1886**: Phase 4 - Refactor Agent for TS Strict Mode Automation
  - Path: `handoff/20250928/40_App/orchestrator/refactor_agent/`, `config/env.schema.yaml`, `.env.example`
  - 新增環境變數：`REFACTOR_AGENT_ENABLED` (boolean, default: true) - 啟用/停用 Refactor Agent
  - 新增環境變數：`REFACTOR_AGENT_ERRORS_PER_RUN` (integer, default: 10) - 每次執行修復的錯誤數量
  - 新增環境變數：`REFACTOR_AGENT_AUTO_PR` (boolean, default: true) - 自動建立 PR
  - 影響：引入自動化 TS strict mode 修復代理
- **PR #1897**: LLM Integration for Refactor Agent Code Fix Generation
  - Path: `handoff/20250928/40_App/orchestrator/refactor_agent/agent.py`
  - 影響：新增 LLM 驅動的程式碼修復生成
- **PR #1903**: File Modification Implementation for Refactor Agent
  - 影響：啟用實際檔案修改功能
- **PR #1908**: PR Automation for Refactor Agent
  - 影響：自動建立修復 PR
- **PR #1913**: Nightly Cron Job Setup + Grammar/Optimization Improvements
  - Path: `.github/workflows/refactor-agent-nightly.yml`
  - 影響：新增每日定時執行的 cron job

*Task Queue Reliability (Ops Agent):*
- **PR #1907**: Fix infinite loop for unassigned tasks
  - Path: `agents/ops_agent/worker.py`
  - 影響：修復 `assigned_to` 缺失時的無限循環問題
- **PR #1912**: Implement task status update and assigned_to validation
  - Path: `agents/ops_agent/worker.py`, `orchestrator/task_queue/redis_queue.py`
  - 影響：錯誤路由的任務標記為 FAILED 並發布 `task.failed` 事件；enqueue 時缺少 `assigned_to` 會記錄警告
- **PR #1914**: Add automated tests for task routing (#1909, #1910)
  - Path: `agents/ops_agent/tests/test_task_routing.py`
  - 影響：新增 8 個任務路由測試（4 個錯誤路由 + 3 個 enqueue 警告 + 1 個整合測試）
- **PR #1934**: Use pytest pythonpath instead of sys.path.insert
  - 影響：使用 pytest.ini pythonpath 配置取代手動路徑設定

*Owner Console Page Standardization (Phase 1 Complete):*
- **PR #1863, #1867, #1879, #1883, #1885, #1894, #1900**: 標準化所有 Owner Console 頁面佈局
  - 影響：統一使用 PageScaffold/SectionTemplate 元件
- **PR #1906**: Move language switcher to navbar
  - 影響：改善導航 UX

*Shared UI Components:*
- **PR #1884**: Implement PageScaffold component
- **PR #1887**: Implement SectionTemplate component
- **PR #1853**: Add iotask foundation components (Phase 1)
- **PR #1856**: Phase 2 - AdminShell three-column layout support

*Security & Memory (Phase 1-2):*
- **PR #1826**: Phase 1 Security Foundation - RLS Hard Gate, Semantic Rules v3
- **PR #1830, #1831, #1836**: Phase 1-2 Follow-up Issues and Observer Node

*Orchestrator Enhancements:*
- **PR #1852**: Phase 3 P2 - LangGraph Mode Full Switchover
- **PR #1854**: Phase 3 P2 - Human-in-the-Loop High-Risk Approval Workflow
- **PR #1857**: Phase 3 P3 - PM Agent + Ops Agent
- **PR #1862**: Phase 3 P4 - Background Queue Principles Enhancement
- **PR #1866**: Phase 3 Follow-up Issues

*ESLint Spacing Rules:*
- **PR #1892**: Add ESLint rule for standardized spacing utilities
  - Path: `handoff/20250928/40_App/owner-console/eslint-rules/no-non-standard-spacing.js`
- **PR #1901**: Cleanup 29 spacing violations
- **PR #1904**: Upgrade spacing ESLint rule to error mode (Phase 3)

*Migrations & Infrastructure:*
- **PR #1871, #1895**: Unified Migration Management and DRY refactoring
- **PR #1881**: Update secrets config to use new key names
- **PR #1882**: Upgrade vulnerable packages and expand CI scanning coverage

**近期重要更新** (2025-12-02 至 2025-12-03):

*實驗與推理模式:*
- **PR #1804**: Phase 4 Production Rollout - 提高實驗百分比並新增緊急開關
  - Path: `handoff/20250928/40_App/orchestrator/experiment_manager.py`, `common/config/settings.py`
  - 新增環境變數：`DISABLE_GEMINI3` (boolean) - 緊急回滾開關，啟用時所有 Gemini 3 流量轉至 OpenAI
  - 影響：gemini3_planner_staging 從 10% 提升至 25%，gemini3_reviewer_staging 從 5% 提升至 10%
- **PR #1803**: Phase 3 Remaining Items - Gemini 3 fallback、參數化測試、CI gate
  - Path: `.github/workflows/gemini3-reviewer-gate.yml`, `handoff/20250928/40_App/orchestrator/tests/test_llm_planner_adapter.py`, `test_llm_reviewer_adapter.py`
  - 影響：新增 Gemini 3 reviewer gate CI 工作流程，整合測試模式
- **PR #1794**: Phase 3.1 Hardening - 新增 REASONING_MODE_ENABLED schema 和單元測試
  - Path: `config/env.schema.yaml`, `common/config/settings.py`
  - 新增環境變數：`REASONING_MODE_ENABLED` (boolean, default: false) - 控制 Gemini 3 的 thinking_level
- **PR #1793**: Phase 3 - 推理模式切換和 Gemini 3 reviewer 實驗
  - Path: `handoff/20250928/40_App/orchestrator/llm/adapters/llm_reviewer_adapter.py`
  - 影響：啟用 gemini3_reviewer_5pct_staging 實驗
- **PR #1792**: Redis Checkpointer - LangGraph 狀態持久化
  - Path: `handoff/20250928/40_App/orchestrator/redis_checkpointer.py`, `graph.py`
  - 影響：新增 Redis 檢查點機制，支援可配置的 TTL
- **PR #1791**: FAQ Routing - FAQ 任務走 simple path，繞過 LangGraph
  - Path: `handoff/20250928/40_App/orchestrator/graph.py`
  - 影響：FAQ 任務使用 simple mode (~95% 流量) 以加快回應速度

*配置與密鑰強化:*
- **PR #1800**: 將 os.getenv 遷移到 settings.py (Tier 1 生產代碼)
  - Path: `handoff/20250928/40_App/orchestrator/`, `common/config/settings.py`
  - 影響：透過 Pydantic settings 集中管理環境變數存取
- **PR #1798**: 將 WORKER_HEARTBEAT_INTERVAL 和 WORKER_HEARTBEAT_TTL 遷移到 settings.py
  - Path: `common/config/settings.py`, `config/env.schema.yaml`
  - 新增環境變數：`WORKER_HEARTBEAT_INTERVAL` (integer, default: 60) - Worker 心跳間隔秒數
  - 新增環境變數：`WORKER_HEARTBEAT_TTL` (integer, default: 180) - 心跳 key 過期時間
- **PR #1797**: 將 RQ_MAX_JOBS 遷移到 settings.py 並強化密鑰安全
  - Path: `common/config/settings.py`, `config/env.schema.yaml`
  - 影響：強化 `FLASK_SECRET_KEY` 和 `ENCRYPTION_MASTER_KEY` 為生產環境必需
- **PR #1795**: 移除已棄用的 SECRET_KEY 和 MASTER_KEY
  - Path: `config/env.schema.yaml`
  - 影響：改用 `FLASK_SECRET_KEY` 和 `ENCRYPTION_MASTER_KEY`
- **PR #1790**: 新增 RQ_MAX_JOBS 環境變數用於 Worker 記憶體管理
  - Path: `handoff/20250928/40_App/orchestrator/redis_queue/worker.py`, `config/env.schema.yaml`
  - 新增環境變數：`RQ_MAX_JOBS` (integer, default: 0) - Worker 處理 N 個任務後重啟以防止 OOM

*UI/UX 與設計系統:*
- **PR #1802**: 為 DashboardHeader 和 Sidebar 新增 Storybook stories
  - Path: `handoff/20250928/40_App/owner-console/src/components/DashboardHeader.stories.tsx`, `Sidebar.stories.tsx`
- **PR #1801**: Phase 3-4 完成 - iotask 元件樣式和進度條
  - Path: `packages/shared-ui/src/components/ui/button.tsx`, `badge.tsx`, `card.tsx`, `input.tsx`, `progress.tsx`
- **PR #1796**: iotask 設計系統升級 - Phase 1-4
  - Path: `packages/shared-ui/src/tokens.json`, `handoff/20250928/40_App/owner-console/src/components/`

**近期重要更新** (2025-11-29 至 2025-12-01):
- **PR #1788**: Failure Memory Integration - 失敗知識庫整合到 failure recorder (Phase 5 PR-1)
  - Path: `handoff/20250928/40_App/orchestrator/failure_recorder.py`
  - 影響：失敗記錄持久化到 Supabase `failure_memory` 表
- **PR #1787**: Sentry Error Prevention - 新增防禦性檢查實現優雅降級
  - Path: `handoff/20250928/40_App/orchestrator/persistence/db_client.py`, `db_writer.py`, `auth_middleware.py`
  - 影響：Supabase 不可用時不再導致應用崩潰
- **PR #1785**: Real Metrics Aggregation - 實驗比較的 RPC 聚合 (Tier 1)
  - Path: `handoff/20250928/40_App/orchestrator/persistence/planner_events_store.py`
  - Migration: `migrations/030_create_planner_metrics_rpc.sql`
- **PR #1781**: ORCHESTRATOR_DRY_RUN Flag - 乾跑模式跳過 PR 創建
  - Path: `handoff/20250928/40_App/orchestrator/graph.py`
  - 新增環境變數：`ORCHESTRATOR_DRY_RUN` (boolean)
- **PR #1780**: OpenAI SDK Upgrade - 修復 httpx 0.28 proxies 相容性
  - Path: `handoff/20250928/40_App/orchestrator/requirements.txt`
- **PR #1778**: 401 Retry Logic - owner-console 主動 token 過期檢查
  - Path: `handoff/20250928/40_App/owner-console/src/lib/auth.ts`, `api-client.ts`

**Gemini 3 SDK 遷移** (2025-11-29 至 2025-11-30):
- **PR #1761**: Gemini Provider Migration - 遷移到 google-genai SDK (Phase 1)
  - Path: `handoff/20250928/40_App/orchestrator/llm/providers/gemini_provider.py`
- **PR #1762**: Gemini Fallback Model Update - 從 gemini-pro 改為 gemini-2.0-flash
- **PR #1763**: Gemini 3 Phase 2 - thinking_level 支援和新實驗
  - 新增 API 參數：`thinking_level` (string: low/medium/high) - 透過 API 請求傳遞，非環境變數
- **PR #1765**: Enable gemini3_planner_10pct_staging 實驗

**AI 治理與安全** (2025-11-28 至 2025-11-29):
- **PR #1741**: Three-tier Permission Architecture (Phase 6 PR-5)
  - Path: `handoff/20250928/40_App/api-backend/src/middleware/auth_middleware.py`
  - Migration: `migrations/028_add_platform_admin_support.sql`
- **PR #1746**: SECURITY_ENFORCEMENT_MODE Configuration (PR-1)
  - Path: `common/config/settings.py`, `config/env.schema.yaml`
  - 新增環境變數：`SECURITY_ENFORCEMENT_MODE` (string: advisory/block_critical/block_all)
- **PR #1748**: LangGraph Enforcement Integration (PR-2)
- **PR #1749**: Simple Mode Policy Observability (PR-3)
- **PR #1751**: Blessed Configurations Documentation (PR-4)
  - Path: `config/blessed_configs.yaml`
- **PR #1753**: Config Validation Script and CI (PR-5)
  - Path: `scripts/validate_blessed_configs.py`, `.github/workflows/validate-blessed-configs.yml`

**CI/CD 改進** (2025-11-28 至 2025-11-29):
- **PR #1756**: Unified Migration Runner (PR-6)
  - Path: `scripts/run_migrations.sh`
- **PR #1757**: Migration Health Check CI (PR-7)
  - Path: `.github/workflows/migration-health-check.yml`
- **PR #1767**: Coverage Trend Tracking
  - Path: `.github/workflows/coverage-trend.yml`
- **PR #1766**: Migration 029 - Fix Security Advisor warnings
  - Path: `migrations/029_fix_reputation_security_warnings.sql`

**先前重要更新** (2025-11-25 至 2025-11-26):
- **PR #1548**: Frontend Dashboard 代碼分割優化 - 20% bundle 減少 + Lighthouse CI color-contrast 修復
  - Path: `handoff/20250928/40_App/frontend-dashboard/`
  - 影響：提升性能和無障礙合規性
- **PR #1562**: RQ Job Timeout 配置 - 新增 `RQ_JOB_TIMEOUT` 環境變數
  - Path: `handoff/20250928/40_App/orchestrator/redis_queue/worker.py`, `config/env.schema.yaml`
  - 影響：可配置的任務超時時間（預設：3600 秒）

**先前重要更新** (2025-11-18 至 2025-11-23):
- **PR #1350**: E2E 測試基礎設施完成 - 32 Playwright 測試通過，route handler 隔離，完整 API mocking
  - Path: `handoff/20250928/40_App/owner-console/e2e/`
  - 測試改善: 11 passed → 32 passed (修復 21 個失敗測試)
- **PR #1398**: 生產環境路徑發現機制 - 新增 `MORNINGAI_REPO_PATH` 環境變數
  - Path: `handoff/20250928/40_App/orchestrator/context_manager.py`
  - 4 層 fallback: env var → git detection → marker-based discovery
- **PR #1399**: Backend 測試環境統一 - Python 3.12, Redis service, PyJWT 衝突解決
  - Path: `.github/workflows/test-apps.yml`
  - 統一 backend.yml 和 test-apps.yml 配置
- **PR #1480**: Pydantic 別名系統 - 新增 23 個關鍵環境變數別名 (2025-11-23)
  - Path: `common/config/settings.py`
  - 修復：`FLASK_SECRET_KEY`, `ENCRYPTION_MASTER_KEY`, `STRIPE_WEBHOOK_SECRET_KEY` 別名
  - 影響：向後相容性改進，標準化配置命名
- **PR #1452**: Redis 映射清理 - 防止 NoneType DataError (2025-11-23)
  - Path: `handoff/20250928/40_App/orchestrator/redis_queue/worker.py`
  - 新增：`sanitize_redis_mapping()` 函數過濾 None 值
  - 影響：提升 Worker 心跳和任務狀態更新的穩定性

---

## Environment Summary

> **Note**: This project uses a **trunk-based development model**. There is no persistent `develop` branch. Staging is handled via Render backend services (deploying from `main` with staging env vars) and Vercel preview deployments.

| Environment | Status | Purpose | Branch | Auto-Deploy |
|-------------|--------|---------|--------|-------------|
| **Production** | ✅ Active | Live user-facing services | `main` | Yes |
| **Staging** | ✅ Active | Pre-production testing | `main` (staging env vars) | Yes |
| **Local Development** | ✅ Active | Developer workstations | Any | No |

---

## 🚀 Production Environment

### Services

#### Backend API
- **URL**: https://morningai-backend-v2.onrender.com
- **Service Name**: `morningai-backend-v2`
- **Platform**: Render
- **Runtime**: Python 3
- **Branch**: `main`
- **Auto-Deploy**: Yes (on push to `main`)
- **Health Check**: `GET /healthz`

#### Orchestrator API
- **URL**: https://morningai-orchestrator-api.onrender.com
- **Service Name**: `morningai-orchestrator-api`
- **Platform**: Render
- **Runtime**: Docker
- **Branch**: `main`
- **Auto-Deploy**: Yes (on push to `main`)
- **Health Check**: `GET /health`

⚠️ **Orchestrator Architecture (Dual-Mode System with Shared Core)**

MorningAI uses a **dual-mode orchestrator architecture** with a shared core executor and canary routing:

```
API Backend → Redis Queue → Worker (Routing) → [Simple Mode | LangGraph Mode]
                                                       ↓              ↓
                                                  graph.execute (Shared Core)
```

**Key Insight**: `graph.py` is NOT just "legacy code" - it's the **shared execution engine** used by both modes.

| Component | Role | Traffic | Status | Path |
|-----------|------|---------|--------|------|
| **Simple Mode** | Direct execution | ~95% | Feature-frozen | `handoff/20250928/40_App/orchestrator/graph.py` |
| **LangGraph Mode** | Stateful workflows | ~5% | Active development | `handoff/20250928/40_App/orchestrator/langgraph_orchestrator.py` |
| **Shared Core** | Execution engine | 100% | Both modes | `handoff/20250928/40_App/orchestrator/graph.py:30-155` |
| **Routing Logic** | Mode selection | 100% | Canary deployment | `handoff/20250928/40_App/orchestrator/redis_queue/worker.py:366-400` |

### Execution Modes

**Simple Mode** (~95% traffic):
- ✅ Fast: Direct execution, no state machine overhead
- ✅ Stable: Battle-tested, production-proven
- ✅ Stateless: No retry logic, no CI monitoring
- ❌ Feature-frozen: Only bug fixes accepted
- Entry: `worker.py:399` → `graph.execute()`

**LangGraph Mode** (~5% traffic, Phase 1):
- ✅ Stateful: Full state machine with LangGraph
- ✅ Intelligent: LLM-powered planning (when `USE_LLM_PLANNER=true`)
- ✅ Resilient: Retry logic, error handling, CI monitoring
- ✅ Active Development: New features go here
- Entry: `worker.py:396` → `langgraph_orchestrator.run_orchestrator()` → `executor_node` → `graph.execute()`

### Routing Logic (Canary Deployment)

**Algorithm** (`worker.py:366-400`):
```python
use_langgraph = settings.use_langgraph or False
use_langgraph_percent = getattr(settings, 'use_langgraph_percent', 0)

if not use_langgraph and use_langgraph_percent > 0:
    # Canary logic: MD5 hash for deterministic routing
    task_hash = int(hashlib.md5(task_id.encode()).hexdigest(), 16)
    task_percent = task_hash % 100  # 0-99 bucket
    use_langgraph = task_percent < use_langgraph_percent
```

**Properties**:
- **Deterministic**: Same task_id always routes to same mode
- **Uniform**: MD5 ensures even distribution across 0-99 buckets
- **Controllable**: Adjust `USE_LANGGRAPH_PERCENT` to change traffic split
- **Observable**: Logs routing decision with structured logging

**Monitoring Keywords** (search in Render Dashboard logs):
- `"Canary deployment"` - Routing decision
- `"Using LangGraph orchestrator"` - LangGraph execution
- `"Using simple orchestrator"` - Simple execution
- `"Using LLM planner"` - LLM planner selection

### Environment Variable Configuration

⚠️ **注意**：本文檔描述架構設計和政策。實際環境變數配置可能因運維需求調整。請以 Render Dashboard 的實際配置為準。

**預設值說明**:
- `USE_LANGGRAPH_PERCENT` 預設值為 **0**（100% Simple mode，LangGraph 停用）
- 啟用 LangGraph 金絲雀需要明確設定 `USE_LANGGRAPH_PERCENT`（例如 Staging 環境設為 15）

**Phase 1 參考配置**（實際配置請查看 Render Dashboard）:

| 服務 | USE_LANGGRAPH | USE_LANGGRAPH_PERCENT | USE_LLM_PLANNER | 位置 |
|------|---------------|----------------------|-----------------|------|
| `morningai-agent-worker` (Production) | `false` | `0` | `false` | Render Dashboard → Production Worker → Environment |

**Note**: For staging worker configuration, refer to [STAGING_SETUP_GUIDE.md](./ops/STAGING_SETUP_GUIDE.md). Staging worker service names are environment-specific and defined in the staging setup documentation.

**配置範例**（Staging 環境）:
```bash
USE_LANGGRAPH=false              # Allow canary routing (not 100%)
USE_LANGGRAPH_PERCENT=15         # 15% traffic to LangGraph (Staging)
USE_LLM_PLANNER=true             # LangGraph uses LLM planner
```

**Kill Switch** (Emergency - 100% Simple):
```bash
USE_LANGGRAPH=false
USE_LANGGRAPH_PERCENT=0          # 0% to LangGraph (100% Simple)
```

**Full LangGraph** (Future - Phase 2+):
```bash
USE_LANGGRAPH=true               # 100% to LangGraph (overrides percent)
```

### Development Guidelines

**✅ DO**: Add new orchestrator features to LangGraph mode only
**❌ DON'T**: Add features to Simple mode (feature-frozen)
**⚠️ CRITICAL**: Changes to `graph.execute()` affect BOTH modes - test both!

**Documentation**: 
- [ONBOARDING_GUIDE.md - Orchestrator Architecture](./ONBOARDING_GUIDE.md#orchestrator-architecture) - Comprehensive developer guide
- [PROJECT_STRUCTURE_REPORT.md - Orchestrator System](./PROJECT_STRUCTURE_REPORT.md#3-orchestrator-system) - Technical details
- [ADR-005: Dual Orchestrator Architecture](adr/005-dual-orchestrator-architecture.md) - Historical context
- [ADR-002: Producer-Consumer Architecture](adr/002-producer-consumer-architecture.md) - Technical architecture
- [ADR-004: Shared Core Executor Pattern](adr/004-shared-core-executor-pattern.md) - Design decision for shared execution engine

**Migration Roadmap**:
- **Phase 1** (Current): LangGraph canary validation (configurable via USE_LANGGRAPH_PERCENT)
- **Phase 2** (Q1 2026): Gradually increase to 100% LangGraph
- **Phase 3** (Q2 2026): Refactor `graph.py` to `core_executor.py`

#### Frontend Dashboard
- **URL**: https://morningai.vercel.app
- **Platform**: Vercel
- **Framework**: Vite + React
- **Branch**: `main`
- **Auto-Deploy**: Yes (on push to `main`)

### Infrastructure

#### Database
- **Provider**: Supabase PostgreSQL
- **Project Name**: `morningai` (production)
- **Project ID**: `qevmlbsunnwgrsdibdoi`
- **URL**: https://qevmlbsunnwgrsdibdoi.supabase.co
- **Type**: Production instance
- **Connection**: Pooler (port 6543)
- **Backups**: Automatic daily backups
- **Schema**: Full production schema with all tables

#### Redis
- **Provider**: Upstash
- **Type**: Production instance
- **Protocol**: `rediss://` (TLS enabled)
- **Key Prefix**: None (production)

#### Monitoring
- **Error Tracking**: Sentry
- **Environment Tag**: `production`
- **Uptime Target**: 99.9%

### Environment Variables

**Schema Definition**: `config/env.schema.yaml` (Single Source of Truth)
- **Total Defined**: 122 variables (20 required, 102 optional)
- **Schema Version**: 1.3 (Phase 1-2 + Feature Flags + Deployment)
- **Auto-Generated**: `.env.example` is generated from schema via `scripts/generate-env-examples.py`
- **CI Validation**: `tests/lint/test_env_vars_defined.py` validates all `os.getenv()` calls against schema
- **Deprecation**: Root `env_schema.yaml` is deprecated; use `config/env.schema.yaml` only
- **Path**: `/home/ubuntu/repos/morningai/config/env.schema.yaml`

**Recent Additions (PR #1398)**:
- **Deployment Category**: New category for deployment-specific variables
  - `MORNINGAI_REPO_PATH`: Repository root path for production/staging
    - Required in Render.com: `/opt/render/project/src`
    - Falls back to git detection or marker-based discovery
    - Replaces hardcoded `~/repos/morningai` path

**Phase 1-2 New Variables** (Added 2025-11):
- **2FA/Authentication**: 
  - `FEATURE_2FA_PREAUTH` (boolean, safe to log)
  - `PREAUTH_TOKEN_TTL` (integer seconds, safe to log)
  - 🔒 `TOTP_ENCRYPTION_KEY` (**SECRET** - DO NOT LOG/COMMIT - 32 bytes base64 encoded)
- **AI Orchestration** (Phase 1-2):
  - `LLM_PROVIDER` (string: openai/gemini/auto) - LLM provider for text generation (Phase 2 Extra)
    - **Default**: `openai`
    - **Options**: `openai`, `gemini`, `auto`
    - **Purpose**: Controls which LLM provider is used for text generation
    - **Auto Mode**: Automatically selects available provider (OpenAI first, then Gemini)
    - **Requires**: Corresponding API key (`OPENAI_API_KEY` or `GEMINI_API_KEY`)
  - 🔒 `GEMINI_API_KEY` (**SECRET**) - Google Gemini API key for LLM operations (Phase 2 Extra)
    - **Required when**: `LLM_PROVIDER=gemini` or `LLM_PROVIDER=auto`
    - **Get API key**: https://makersuite.google.com/app/apikey
  - `USE_LLM_PLANNER` (boolean) - Enable LLM-based task planning (Phase 1)
  - `USE_CODEGEN_WORKFLOW_PERCENT` (integer 0-100) - Percentage rollout for code generation workflow (Phase 2)
  - `USE_LANGGRAPH` (boolean) - Enable LangGraph orchestrator mode
  - `USE_LANGGRAPH_PERCENT` (integer 0-100) - Percentage rollout for LangGraph
  - ⚠️ `ENABLE_PROJECT_ENGINEER_CODEGEN` (boolean) - **PRIVILEGED SWITCH** - Enable ProjectEngineerAgent code generation execution mode (Phase 2 Step B-1)
    - **Default**: `false` (analysis-only mode)
    - **Security Level**: High-risk feature flag
    - **Production Use**: ⚠️ **DO NOT enable in production except for controlled rollouts with monitoring**
    - **Purpose**: Controls whether ProjectEngineerAgent can execute code generation for safe tasks
    - **Requires**: `dev_agent` instance must be provided to ProjectEngineerAgent
    - **Safe Tasks Only**: Only affects whitelisted safe tasks (documentation_update, test_generation, etc.)
    - **Unsafe Tasks**: Always skipped regardless of this setting
    - **Documentation**: See `PHASE_2_STEP_C_FEATURE_FLAG.md` for detailed implementation guide
  - ⚠️ `ENABLE_PROJECT_ENGINEER_FIXER` (boolean) - **PRIVILEGED SWITCH** - Enable AutoFixer in fixer_node (Phase 2 Step C Fixer Node)
    - **Default**: `false` (no auto-fix)
    - **Security Level**: High-risk feature flag
    - **Production Use**: ⚠️ **DO NOT enable in production - staging only at first**
    - **Purpose**: Controls whether fixer_node can use ReviewerAgent + ProjectEngineerAgent for auto-fix
    - **Requires**: `ENABLE_PROJECT_ENGINEER_CODEGEN=true` to actually execute fixes
    - **Canary Rollout**: Use `PROJECT_ENGINEER_FIXER_PERCENT` for gradual rollout
    - **Recommended Values**:
      - Staging: `true` (with `PROJECT_ENGINEER_FIXER_PERCENT=5-10`)
      - Production: `false` initially, then `true` after staging validation
    - **Documentation**: See `handoff/20250928/40_App/orchestrator/project_engineer/fixer_integration.py`
  - `PROJECT_ENGINEER_FIXER_PERCENT` (integer 0-100) - Percentage rollout for auto-fix in fixer_node (Phase 2 Step C Fixer Node)
    - **Default**: `0` (no auto-fix)
    - **Purpose**: Canary rollout mechanism for auto-fix in fixer_node
    - **Algorithm**: MD5 hash routing based on pr_number or trace_id for deterministic task assignment
    - **Only effective when**: `ENABLE_PROJECT_ENGINEER_FIXER=true`
    - **Recommended Values**:
      - Staging: `5-10` (start with 5-10% canary)
      - Production: `0` initially, then gradually increase (`5 → 10 → 25 → 50 → 100`)
    - **Max Retries**: Fixer node will retry up to `MAX_FIXER_RETRIES` (default 3) times before giving up
    - **Observability**: When max retries reached, logs `autofixer_max_retries_reached=true` with `last_error` for monitoring
    - **Safety**: AutoFixer uses Phase 2 Step B `safe_tasks` whitelist via ProjectEngineerAgent - logs `autofixer_safety_check` key
- **Rate Limiting**: `RATE_LIMIT_REQUESTS`, `RATE_LIMIT_WINDOW`, `RATE_LIMIT_BY_USER`, `RATE_LIMIT_FAIL_FAST`, `RATE_LIMIT_REDIS_MAX_RETRIES`, `RATE_LIMIT_REDIS_RETRY_DELAY`
- **Testing** (⚠️ **TEST ENVIRONMENTS ONLY** - NEVER SET IN PRODUCTION):
  - `TESTING` (boolean) - Enables test mode behaviors
  - 🚫 `FORCE_ENABLE_2FA_IN_TESTS` (boolean) - **DANGEROUS** - Can bypass security controls
    - ⚠️ **CRITICAL**: This flag MUST ONLY be set in test environments
    - ⚠️ Setting in production/staging can disable 2FA enforcement
    - ⚠️ CI should fail if this is set in production/staging environments
- **Database**: `DB_POOL_MAX`, `DB_POOL_SIZE`, `DB_POOL_RECYCLE`, `DB_POOL_PRE_PING`
- **Redis**: `REDIS_KEY_PREFIX`, `RQ_QUEUE_NAME`
- **Security**: `COOKIE_DOMAIN`, `COOKIE_PATH`, `FEATURE_COOKIE_AUTH`
- **Operations**: `DEBUG`, `FAQ_CACHE_TTL`, `ORCHESTRATOR_PATH`, `OPENAI_MAX_DAILY_COST`
- **Deployment**: `GIT_COMMIT`, `RENDER_GIT_COMMIT`, `SENTRY_ENVIRONMENT`
- **Governance**: `ALLOW_GOVERNANCE_MOCK`, `ENABLE_MOCK_USERS`

**Redis Requirements**:
- **Minimum Version**: Redis 2.6+ (required for Lua EVAL support used in atomic pre-auth token consumption)
- **Recommended**: Upstash Redis or self-hosted Redis 8.2.2+ with TLS (`rediss://`)
- **Security**: CVE-2025-49844 protection requires TLS-enabled connections

**Critical Variables**:
```bash
# ⚠️ EXAMPLE CONFIGURATION - NEVER USE THESE PLACEHOLDER VALUES IN PRODUCTION
# Generate secure secrets: python -c "import secrets; print(secrets.token_urlsafe(64))"

ENVIRONMENT=production
DATABASE_URL=postgresql://...
REDIS_URL=rediss://...

# 🔒 SECRETS - Minimum 64 characters, cryptographically random
JWT_SECRET_KEY=CHANGEME_GENERATE_RANDOM_64_CHAR_STRING           # 🔒 SECRET - DO NOT LOG
SECRET_KEY=CHANGEME_GENERATE_RANDOM_64_CHAR_STRING               # 🔒 SECRET - DO NOT LOG
MASTER_ENCRYPTION_KEY=CHANGEME_GENERATE_RANDOM_64_CHAR_STRING    # 🔒 SECRET - DO NOT LOG
ENCRYPTION_MASTER_KEY=CHANGEME_GENERATE_RANDOM_64_CHAR_STRING    # 🔒 SECRET - Alias for MASTER_ENCRYPTION_KEY
TOTP_ENCRYPTION_KEY=CHANGEME_GENERATE_RANDOM_32_BYTES_BASE64     # 🔒 SECRET - 32 bytes base64 - Required for 2FA
ORCHESTRATOR_JWT_SECRET=CHANGEME_GENERATE_RANDOM_64_CHAR_STRING  # 🔒 SECRET - DO NOT LOG
```

**Monitoring**:
```bash
SENTRY_DSN=<production-dsn>
SENTRY_ENVIRONMENT=production
```

**Orchestrator Configuration** (Phase 1-2):

⚠️ **注意**：以下為參考配置。實際環境變數請查看 Render Dashboard。

```bash
# Dual-Mode Orchestrator with Canary Routing
USE_LANGGRAPH=false                     # Allow canary routing (false = use percent, true = 100%)
USE_LANGGRAPH_PERCENT=5                 # 5% traffic to LangGraph mode (0-100)

# Phase 1-2 Feature Flags
USE_LLM_PLANNER=true                    # Enable LLM-based task planning (Phase 1)
USE_CODEGEN_WORKFLOW_PERCENT=0          # Percentage rollout for code generation (Phase 2, 0-100)
ENABLE_PROJECT_ENGINEER_CODEGEN=false   # ⚠️ PRIVILEGED - ProjectEngineerAgent execution mode (Phase 2 Step B-1)
                                        # DO NOT enable in production without controlled rollout

# Phase 2 Step C Fixer Node (Auto-Fix)
ENABLE_PROJECT_ENGINEER_FIXER=false     # ⚠️ PRIVILEGED - AutoFixer in fixer_node (Phase 2 Step C)
PROJECT_ENGINEER_FIXER_PERCENT=0        # Percentage rollout for auto-fix (0-100)
                                        # Uses MD5 hash routing for deterministic task assignment

# Configuration Examples:
# - Kill Switch (100% Simple):    USE_LANGGRAPH=false, USE_LANGGRAPH_PERCENT=0
# - 5% Canary (Phase 1 Reference): USE_LANGGRAPH=false, USE_LANGGRAPH_PERCENT=5
# - 50% Split Testing:            USE_LANGGRAPH=false, USE_LANGGRAPH_PERCENT=50
# - 100% LangGraph (Future):      USE_LANGGRAPH=true (overrides percent)
```

**Rate Limiting**:
```bash
# Rate limiting configuration (optional, defaults shown)
RATE_LIMIT_REQUESTS=60                  # Maximum requests per window
RATE_LIMIT_WINDOW=60                    # Time window in seconds
RATE_LIMIT_FAIL_FAST=true               # Fail on startup if Redis unavailable (production only)
RATE_LIMIT_BY_USER=false                # Use user_id instead of IP for rate limiting
RATE_LIMIT_REDIS_MAX_RETRIES=3          # Maximum Redis connection retry attempts
RATE_LIMIT_REDIS_RETRY_DELAY=1.0        # Delay between retries in seconds (exponential backoff)
```

**Logging Configuration**:
```bash
# Application logging level (case-insensitive, normalized to uppercase)
# Used by: Python logging configuration (common/config/settings.py)
LOG_LEVEL=INFO                          # Options: DEBUG, INFO, WARNING, ERROR, CRITICAL
                                        # Supports any case: info/INFO/Info all work

# Gunicorn logging level (case-insensitive, normalized to lowercase)
# Used by: Gunicorn configuration (gunicorn.conf.py)
GUNICORN_LOG_LEVEL=info                 # Options: debug, info, warning, error, critical
                                        # Supports any case: INFO/info/Info all work

# Note: As of PR #1499, both LOG_LEVEL and GUNICORN_LOG_LEVEL support case-insensitive
# input. The validators automatically normalize to the correct case before validation.
# This prevents ValidationError when environment variables use different casing.
# See config/env.schema.yaml for default values and allowed choices.
```

**Troubleshooting**:
- If you provide an invalid value (not in the list above), the application will fail to start with a Pydantic `ValidationError` on the `log_level` or `gunicorn_log_level` field.
- Check startup logs for details and update the environment variable to one of the supported values.
- Example error: `ValidationError: 1 validation error for Settings log_level Input should be 'DEBUG', 'INFO', 'WARNING', 'ERROR' or 'CRITICAL'`

---

## 環境變數別名系統（Pydantic Aliases）

**Added**: 2025-11-23 (PR #1480)  
**Path**: `common/config/settings.py:47-722`

從 2025-11-23 起，配置系統通過 Pydantic BaseSettings 支援環境變數別名，確保向後相容性並標準化命名規範。這允許使用舊的環境變數名稱，同時逐步遷移到標準化的命名約定。

### 別名系統概述

MorningAI 使用 Pydantic 的 `Field(alias=...)` 功能來支援多個環境變數名稱映射到同一個配置屬性。這確保了：

1. **向後相容性**：現有部署可以繼續使用舊的環境變數名稱
2. **標準化命名**：新部署應使用正式的標準化名稱
3. **逐步遷移**：團隊可以按自己的節奏遷移到新名稱
4. **CI 驗證**：別名覆蓋率由 CI 自動檢查（`scripts/ci/check_settings_aliases.py`）

### 關鍵別名映射

以下是已修復和標準化的關鍵環境變數別名：

| 正式名稱（推薦） | 舊名稱（別名） | 狀態 | 安全等級 | 說明 |
|-----------------|---------------|------|----------|------|
| `FLASK_SECRET_KEY` | `SECRET_KEY` | ⚠️ 已棄用 | 🔒 CRITICAL | Flask 應用程式會話密鑰 |
| `ENCRYPTION_MASTER_KEY` | `MASTER_KEY` | ⚠️ 已棄用 | 🔒 CRITICAL | 主加密密鑰 |
| `STRIPE_WEBHOOK_SECRET_KEY` | `STRIPE_WEBHOOK_SECRET` | ⚠️ 已棄用 | 🔒 SECRET | Stripe Webhook 驗證密鑰 |

**重要提示**：
- 🔒 標記為 CRITICAL 的變數必須至少 64 字符，使用加密隨機生成
- ⚠️ 已棄用的名稱仍然有效，但建議遷移到正式名稱
- 在生產環境中，優先使用正式名稱以避免混淆

### 新增別名（2025-11-23）

以下 23 個環境變數現在支援通過 Pydantic 別名加載：

#### 認證與安全
- `ACCESS_TOKEN_EXPIRY_MINUTES` - JWT 訪問令牌過期時間（分鐘）
- `LOG_TOKEN_EXPIRY_ON_STARTUP` - 啟動時記錄令牌過期配置
- `FEATURE_2FA_ENABLED` - 啟用 2FA/TOTP 功能
- `FEATURE_2FA_PREAUTH` - 啟用預認證令牌流程
- `PREAUTH_TOKEN_TTL` - 預認證令牌 TTL（秒）

#### 測試與開發
- `RLS_TESTS_ALLOWED` - 允許 RLS 測試（僅測試環境）
- `TEST_SUPABASE_URL` - 測試環境 Supabase URL
- `ENABLE_MOCK_USERS` - 啟用模擬用戶（⚠️ 生產環境必須為 false）
- `STAGING_API_URL` - Staging 環境 API URL
- `STAGING_TEST_EMAIL` - Staging 測試用戶郵箱

#### 基礎設施與監控
- `REDIS_KEY_PREFIX` - Redis 鍵前綴（例如：`stg:` 用於 staging）
- `RQ_QUEUE_NAME` - Redis Queue 隊列名稱（默認：`orchestrator`）
- `RQ_JOB_TIMEOUT` - RQ worker job timeout 秒數（默認：`600`）- 控制 LLM Planner 等長時間運行任務的超時時間
- `DB_POOL_MAX` - 數據庫連接池最大連接數
- `SENTRY_DSN` - Sentry 錯誤追蹤 DSN
- `SENTRY_ENVIRONMENT` - Sentry 環境標識（production/staging/development）
- `PORT` - 應用程式監聽端口
- `LOG_LEVEL` - 日誌級別（DEBUG/INFO/WARNING/ERROR）
- `DEBUG` - 調試模式開關

#### Cookie 與會話
- `COOKIE_SECURE` - Cookie Secure 標誌（生產環境應為 true）
- `COOKIE_SAMESITE` - Cookie SameSite 屬性（Strict/Lax/None）
- `COOKIE_DOMAIN` - Cookie 域名
- `COOKIE_PATH` - Cookie 路徑

#### 其他
- `MEMORY_TABLE` - 記憶體表名稱（用於 pgvector 存儲）

### 別名驗證與 CI

**驗證腳本**：`scripts/ci/check_settings_aliases.py`

此腳本檢查 `config/env.schema.yaml` 中定義的所有環境變數是否在 `common/config/settings.py` 中有對應的 Pydantic 別名。

**CI 工作流**：[`.github/workflows/settings-alias-audit.yml`](../.github/workflows/settings-alias-audit.yml)

自動運行別名覆蓋率檢查（warn-only 模式，不阻擋合併），確保配置系統的一致性。

**目前別名狀態（快照）***：

- 總變數數量：148（來自 `config/env.schema.yaml`）
- 排除項目：11 個（前端專用 / 已棄用等）
- 必要變數：137
- 已有別名：約 109 個（約 80% 覆蓋率）
- 缺少別名：28 個

\* 根據 2025-11-23 執行的 `scripts/ci/check_settings_aliases.py` 稽核結果。可透過運行 `python scripts/ci/check_settings_aliases.py` 重新計算。

**目標**：100% 覆蓋率（所有 `env.schema.yaml` 中的必要變數都應在 `settings.py` 中有別名）

### 使用建議

1. **新部署**：使用正式名稱（表格中的"正式名稱"列）
2. **現有部署**：可以繼續使用舊名稱，但建議逐步遷移
3. **遷移策略**：
   ```bash
   # 步驟 1: 在 .env 中同時設置新舊名稱
   FLASK_SECRET_KEY=your_secret_key
   SECRET_KEY=your_secret_key  # 保留以確保相容性
   
   # 步驟 2: 驗證應用程式正常運行
   # 步驟 3: 移除舊名稱
   FLASK_SECRET_KEY=your_secret_key
   ```
4. **安全考慮**：
   - 🚫 **絕對不要**在生產環境中設置 `ENABLE_MOCK_USERS=true`
   - 🚫 **絕對不要**在生產/staging 環境中設置 `RLS_TESTS_ALLOWED=true`
   - ✅ 在生產環境中始終使用 `COOKIE_SECURE=true`

### 技術實現

別名通過 Pydantic 的 `Field` 定義實現：

```python
# common/config/settings.py 示例
class Settings(BaseSettings):
    flask_secret_key_secret: Optional[SecretStr] = Field(
        None,
        alias="FLASK_SECRET_KEY",  # 正式名稱
        description="Flask application secret key for sessions",
        repr=False
    )
    
    # 舊名稱通過 Pydantic 的環境變數加載自動支援
    # 如果同時設置了新舊名稱，新名稱（alias）優先
```

**加載優先級**：
1. 環境變數（使用 alias 名稱）
2. .env 文件（使用 alias 名稱）
3. 默認值

### 相關文檔

- **配置 Schema**：`config/env.schema.yaml` - 所有環境變數的單一真實來源
- **Pydantic 設置**：`common/config/settings.py` - 類型安全的配置類
- **別名檢查腳本**：`scripts/ci/check_settings_aliases.py` - CI 驗證工具
- **環境變數生成**：`scripts/generate-env-examples.py` - 生成 .env.example 文件

---

## 🧪 Staging Environment

### Services

#### Backend API Staging
- **URL**: https://morningai-backend-v2-stg.onrender.com
- **Service Name**: `morningai-backend-v2-stg`
- **Platform**: Render
- **Runtime**: Python 3
- **Branch**: `main` (with `ENVIRONMENT=staging`)
- **Auto-Deploy**: Yes (on push to `main`)
- **Health Check**: `GET /healthz`
- **Status**: ✅ Healthy

**Health Check Response**:
```json
{
  "database": "connected",
  "phase": "Phase 8: Self-service Dashboard & Reporting Center",
  "redis": {
    "protocol": "rediss",
    "status": "connected",
    "tls_enabled": true,
    "type": "redis",
    "url": "main-gull-14059.upstash.io:6379"
  },
  "services": {
    "backend_services": "available",
    "phase4_apis": "available",
    "phase5_apis": "available",
    "phase6_apis": "available",
    "security_manager": "available"
  },
  "status": "healthy",
  "timestamp": "2025-10-28T08:18:16.548126",
  "version": "8.0.0"
}
```

#### Orchestrator API Staging
- **URL**: https://morningai-orchestrator-api-stg.onrender.com
- **Service Name**: `morningai-orchestrator-api-stg`
- **Platform**: Render
- **Runtime**: Docker
- **Dockerfile**: `orchestrator/Dockerfile`
- **Branch**: `main` (with `ENVIRONMENT=staging`)
- **Auto-Deploy**: Yes (on push to `main`)
- **Health Check**: `GET /health`
- **Status**: ✅ Healthy

**Health Check Response**:
```json
{
  "status": "healthy",
  "redis": "connected",
  "queue_stats": {
    "pending_tasks": 292,
    "processing_tasks": 62,
    "total_tasks": 354
  }
}
```

#### Frontend Dashboard Staging
- **URL**: https://staging.morningai.me (or use Vercel preview URLs)
- **Platform**: Vercel
- **Framework**: Vite + React
- **Branch**: Preview deployments from `feature/*`, `fix/*`, `devin/*`
- **Auto-Deploy**: Yes (on PR creation)
- **Status**: ✅ Healthy

#### Owner Console Staging
- **URL**: https://staging-owner.morningai.me (or use Vercel preview URLs)
- **Platform**: Vercel
- **Framework**: Vite + React
- **Branch**: Preview deployments from `feature/*`, `fix/*`, `devin/*`
- **Auto-Deploy**: Yes (on PR creation)
- **Status**: ✅ Healthy

**Deployment Strategy** (Trunk-Based):
- **Branch Policy**: `main` → production, `feature/*|fix/*|devin/*` → preview
- **Ignore Script**: `scripts/vercel-ignore.sh` (skips docs-only changes)
- **Documentation**: See [docs/deployment/VERCEL_DEPLOYMENT_STRATEGY.md](deployment/VERCEL_DEPLOYMENT_STRATEGY.md) for complete setup and troubleshooting

### Infrastructure

#### Database
- **Provider**: Supabase PostgreSQL
- **Project Name**: `morningai-staging`
- **Project ID**: `dckisglnlemvpvmyvnut`
- **URL**: https://dckisglnlemvpvmyvnut.supabase.co
- **Connection**: Pooler (port 6543)
- **Data**: Separate from production
- **Schema**: Minimal test schema (tenants, user_profiles, agent_tasks)
- **Purpose**: RLS testing and security validation

⚠️ **Important**: Staging database has a minimal schema for security testing. Not all production tables exist in staging. This is intentional to keep the staging environment lightweight and focused on P0 security testing.

#### Redis
- **Provider**: Upstash (shared with production)
- **Protocol**: `rediss://` (TLS enabled)
- **Key Prefix**: `stg:` (isolates staging data)
- **Queue Name**: `orchestrator-staging`

#### Monitoring
- **Error Tracking**: Sentry
- **Environment Tag**: `staging`
- **Cost**: ~$14/month (Render Starter plans)

### Environment Variables

**Backend Staging**:
```bash
# Environment
ENVIRONMENT=staging

# Database (Staging Supabase)
DATABASE_URL=postgresql://postgres.[PROJECT_ID]:[PASSWORD]@aws-0-ap-southeast-1.pooler.supabase.com:6543/postgres
SUPABASE_URL=https://dckisglnlemvpvmyvnut.supabase.co
SUPABASE_ANON_KEY=<staging-anon-key>
SUPABASE_SERVICE_ROLE_KEY=<staging-service-role-key>

# Redis (Shared with production, isolated by prefix)
REDIS_URL=rediss://default:[PASSWORD]@[HOST].upstash.io:6379
REDIS_KEY_PREFIX=stg:
RQ_QUEUE_NAME=orchestrator-staging
RQ_JOB_TIMEOUT=600                      # Job timeout in seconds (default: 600 = 10 minutes)

# Database Connection Pool
DB_POOL_SIZE=5
DB_POOL_MAX_OVERFLOW=5
DB_POOL_RECYCLE=3600
DB_POOL_PRE_PING=true

# Security (Different from production)
JWT_SECRET_KEY=<staging-secret>
SECRET_KEY=<staging-secret>
MASTER_ENCRYPTION_KEY=<staging-secret>

# Monitoring
SENTRY_DSN=<same-as-production>
SENTRY_ENVIRONMENT=staging

# Rate Limiting (optional, defaults shown)
RATE_LIMIT_REQUESTS=60                  # Maximum requests per window
RATE_LIMIT_WINDOW=60                    # Time window in seconds
RATE_LIMIT_FAIL_FAST=false              # Allow startup without Redis (staging)
RATE_LIMIT_BY_USER=false                # Use user_id instead of IP for rate limiting
RATE_LIMIT_REDIS_MAX_RETRIES=3          # Maximum Redis connection retry attempts
RATE_LIMIT_REDIS_RETRY_DELAY=1.0        # Delay between retries in seconds (exponential backoff)
```

**Orchestrator Staging**:
```bash
# Environment
ENVIRONMENT=staging
PORT=8000

# Security (REQUIRED)
ORCHESTRATOR_JWT_SECRET=<staging-orchestrator-secret-48-chars>

# Redis (REQUIRED)
REDIS_URL=rediss://default:[PASSWORD]@[HOST].upstash.io:6379
REDIS_KEY_PREFIX=stg:
RQ_QUEUE_NAME=orchestrator-staging
RQ_JOB_TIMEOUT=600                      # Job timeout in seconds (default: 600 = 10 minutes)

# Optional
ORCHESTRATOR_CORS_ORIGINS=https://morningai-staging.vercel.app,http://localhost:5173
SENTRY_ENVIRONMENT=staging
LOG_LEVEL=INFO
```

### Setup Documentation

For complete staging environment setup instructions, see:
- **[Staging Setup Guide](ops/STAGING_SETUP_GUIDE.md)** - Comprehensive setup guide with step-by-step instructions

---

## 💻 Local Development Environment

### Services

#### Backend API
- **URL**: http://localhost:8000
- **Runtime**: Python 3.12+
- **Framework**: Flask
- **Start Command**: 
  ```bash
  # Option 1: Flask CLI (recommended for development)
  export FLASK_APP=src.main
  flask run --port 8000
  
  # Option 2: Gunicorn (production-like)
  gunicorn "src.main:app" --bind 0.0.0.0:8000 --reload
  
  # Quick one-liner (equivalent to Option 1)
  export FLASK_APP=src.main && flask run --port 8000
  ```
- **Working Directory**: `handoff/20250928/40_App/api-backend`

#### Orchestrator API
- **URL**: http://localhost:8001
- **Runtime**: Python 3.12+
- **Framework**: FastAPI
- **Start Command**: `uvicorn orchestrator.api.main:app --port 8001 --reload`
- **Working Directory**: Repository root

#### Frontend Dashboard
- **URL**: http://localhost:5173
- **Runtime**: Node.js 20+
- **Start Command**: `npm run dev`
- **Working Directory**: `handoff/20250928/40_App/frontend-dashboard`

### Infrastructure

#### Database
- **Option 1**: Local PostgreSQL
- **Option 2**: Staging Supabase (recommended for testing)
- **Option 3**: Production Supabase (read-only, for debugging)

#### Redis
- **Option 1**: Local Redis (`redis://localhost:6379/0`)
- **Option 2**: Staging Redis (recommended for testing)

### Environment Variables

Create `.env` file in each service directory:

**Backend `.env`**:
```bash
ENVIRONMENT=development
DATABASE_URL=postgresql://localhost:5432/morningai
REDIS_URL=redis://localhost:6379/0
TESTING=false

# Or use staging infrastructure
DATABASE_URL=<staging-database-url>
REDIS_URL=<staging-redis-url>
REDIS_KEY_PREFIX=dev:

# Rate Limiting (optional, defaults shown)
RATE_LIMIT_REQUESTS=60                  # Maximum requests per window
RATE_LIMIT_WINDOW=60                    # Time window in seconds
RATE_LIMIT_FAIL_FAST=false              # Allow startup without Redis (development)
RATE_LIMIT_BY_USER=false                # Use user_id instead of IP for rate limiting
RATE_LIMIT_REDIS_MAX_RETRIES=3          # Maximum Redis connection retry attempts
RATE_LIMIT_REDIS_RETRY_DELAY=1.0        # Delay between retries in seconds (exponential backoff)
```

**Testing Flags** (⚠️ **DEVELOPMENT/TEST ONLY** - Added Nov 2025):
```bash
# Enable rate limiting in test environment (default: false)
ENABLE_RATE_LIMIT_IN_TESTS=false

# Enable Playwright browser E2E tests (requires staging credentials)
RUN_PY_BROWSER_E2E=false

# Flask environment mode (now accepts 'testing' for test environments)
FLASK_ENV=testing  # Options: development, staging, production, testing (default: development)
```

**⚠️ CRITICAL:** These flags MUST ONLY be set in test/development environments. Never set in production/staging.

**Schema:** See `config/env.schema.yaml` for complete definitions and constraints.

**Frontend `.env.local`**:
```bash
VITE_API_URL=http://localhost:8000
VITE_ORCHESTRATOR_URL=http://localhost:8001
VITE_ENVIRONMENT=development

# Or point to staging backend
VITE_API_URL=https://morningai-backend-v2-stg.onrender.com
VITE_ORCHESTRATOR_URL=https://morningai-orchestrator-api-stg.onrender.com
```

**VITE_API_BASE_URL** (Frontend - Added/Updated Nov 2025):
```bash
# For Vercel preview/production deployments (uses Vercel proxy)
VITE_API_BASE_URL=/api

# For local development or direct backend access
VITE_API_BASE_URL=http://localhost:8000/api
# or
VITE_API_BASE_URL=https://morningai-backend-v2-stg.onrender.com/api
```

**Important:** The value must include the `/api` suffix. For Vercel deployments, use `/api` (relative path) to leverage Vercel's proxy. For direct backend access, use the full URL with `/api` suffix.

**Schema:** See `config/env.schema.yaml` for complete definition.

**VITE_TRACE_VIEWER_URL** (Frontend - Added Nov 2025):
```bash
# Optional: URL for observability platform trace viewer
# Used to link trace IDs in Agent Execution Logs to detailed trace views
# Leave empty or unset to disable trace links

# Jaeger
VITE_TRACE_VIEWER_URL=https://jaeger.gm365.me

# Tempo (Grafana)
VITE_TRACE_VIEWER_URL=https://tempo.gm365.me

# Grafana Explore
VITE_TRACE_VIEWER_URL=https://grafana.gm365.me/explore

# For testing (any URL)
VITE_TRACE_VIEWER_URL=https://example.com
```

**Behavior:**
- When set: External link icon appears next to trace IDs in Agent Execution Logs
- When unset or empty: Only copy button appears (no external link)
- Link format: `{VITE_TRACE_VIEWER_URL}/trace/{encoded_trace_id}`
- Security: Trace IDs are automatically URL-encoded using `encodeURIComponent()`

**Usage Locations:**
- Owner Console → Agent Governance → Agent Execution Logs (desktop table view)
- Owner Console → Agent Governance → Agent Execution Logs (mobile card view)
- Owner Console → Agent Governance → Agent Execution Logs (execution details drawer)

**Testing:**
1. Set `VITE_TRACE_VIEWER_URL` in `.env.local` or Vercel environment variables
2. Navigate to Agent Governance page in Owner Console
3. Verify external link icon appears next to trace IDs
4. Click link to verify it opens in new tab with correct URL format

**Schema:** See `config/env.schema.yaml` for complete definition.

### Setup Documentation

For complete local development setup instructions, see:
- **[Local Development Setup](setup_local.md)** - Quick start guide and troubleshooting

---

## 🔔 Monitor Orchestrator Behavior

The monitor orchestrator (`scripts/monitor_orchestrator.py`) performs health checks and queue monitoring for the Orchestrator API.

### Slack Notifications

**Graceful Degradation** (Default Behavior):
- **Optional**: If `SLACK_WEBHOOK_URL` is not configured, the monitor will continue to run
- **Console Fallback**: Alerts are printed to console instead of sent to Slack
- **Use Case**: Allows CI/CD workflows (GitHub Actions) to succeed even without Slack integration
- **Exit Code**: Monitor exit code reflects health/queue check results, not Slack notification status

**Production Recommendations**:
- ✅ **Recommended**: Configure `SLACK_WEBHOOK_URL` in GitHub Secrets for real-time alerts
- ✅ Monitor GitHub Actions logs for console output when Slack is not configured
- ⚠️ **Warning**: If Slack webhook is accidentally removed, alerts will only appear in logs

**Configuration**:
```bash
# Optional - enables Slack notifications
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK/URL

# Optional - override default Orchestrator API URL
ORCHESTRATOR_API_URL=https://morningai-orchestrator-api.onrender.com
```

**Behavior Examples**:

*With Slack configured*:
```bash
$ python scripts/monitor_orchestrator.py
Checking health: https://morningai-orchestrator-api.onrender.com/health
✓ Health check passed (response time: 0.23s)
✓ Queue stats: pending=5, processing=2, total=7
✓ All checks passed
# Slack alert sent to channel
```

*Without Slack configured*:
```bash
$ python scripts/monitor_orchestrator.py
[WARNING] SLACK_WEBHOOK_URL not configured - Slack alerts disabled
[INFO] Continuing with health checks only (no Slack notifications)
Checking health: https://morningai-orchestrator-api.onrender.com/health
✓ Health check passed (response time: 0.23s)
✓ Queue stats: pending=5, processing=2, total=7
✓ All checks passed
# No Slack alert sent - alerts printed to console only
```

*When critical issues detected (without Slack)*:
```bash
$ python scripts/monitor_orchestrator.py
[WARNING] SLACK_WEBHOOK_URL not configured - Slack alerts disabled
[INFO] Continuing with health checks only (no Slack notifications)
Checking health: https://morningai-orchestrator-api.onrender.com/health
[CRITICAL] Health Check Failed - Connection Error
Unable to connect to the API.
URL: https://morningai-orchestrator-api.onrender.com/health
Possible causes: Service is down, network issue, or DNS problem
✗ Some checks failed
# Exit code: 1 (failure)
```

**GitHub Actions Integration**:

The monitor runs every 5 minutes via GitHub Actions workflow (`.github/workflows/monitor-orchestrator.yml`). The workflow will:
- ✅ **Succeed** if health checks pass (even without Slack configured)
- ❌ **Fail** if health checks fail (alerts visible in workflow logs)
- 📊 Alerts are visible in GitHub Actions logs regardless of Slack configuration

---

## 🔧 Import Path Configuration

Services that import the `common` module use a multi-tier fallback mechanism to ensure imports work across all environments.

### Priority Order

| Priority | Mechanism | Use Case | Example |
|----------|-----------|----------|---------|
| 1 | REPO_ROOT | Explicit control | `REPO_ROOT=/app` |
| 2 | PYTHONPATH | Standard Python | `PYTHONPATH=/app:/other` |
| 3 | Marker files | Auto-discovery | `.git`, `pyproject.toml`, `env.schema.yaml` or `env_schema.yaml` |

### Configuration by Environment

**Docker Containers**:
```dockerfile
ENV REPO_ROOT=/app
ENV PYTHONPATH=/app
```

**Render Services**:
```yaml
envVars:
  - key: REPO_ROOT
    value: /app
  - key: PYTHONPATH
    value: /app
  - key: DEBUG_IMPORTS
    value: "false"  # Set to "true" for troubleshooting
```

**Local Development**:
```bash
export REPO_ROOT=/path/to/morningai
export DEBUG_IMPORTS=true
```

### Debugging Import Issues

**Enable import debugging**:
```bash
DEBUG_IMPORTS=true python monitoring/braintrust_processor.py
```

**Expected output**:
```
✅ sys.path bootstrap: REPO_ROOT=/app
Final sys.path (first 3): ['', '/app', '/usr/local/lib/python311.zip']
```

**Verify configuration in Docker**:
```bash
# Check environment variables
docker exec <container> env | grep -E 'REPO_ROOT|PYTHONPATH'

# Check sys.path
docker exec <container> python -c "import sys; print(sys.path[:5])"

# Test import
docker exec <container> python -c "from common.config.settings import settings; print('✅ Import successful')"
```

### Affected Services

- **Braintrust Processor** (`monitoring/braintrust_processor.py`)
- **API Backend** (`handoff/20250928/40_App/api-backend/gunicorn.conf.py`)

### Troubleshooting

See [monitoring/DEPLOYMENT.md](../monitoring/DEPLOYMENT.md#troubleshooting) for detailed troubleshooting steps.

---

## 🔄 Deployment Workflow

### Development Flow (Trunk-Based)

```mermaid
graph LR
    A[Feature Branch] -->|PR| B[main]
    B -->|Auto-deploy| C[Production]
    A -->|Preview Deploy| D[Staging Test]
    D -->|Manual Test| E{Tests Pass?}
    E -->|Yes| B
    E -->|No| A
```

### Step-by-Step Process

#### 1. Feature Development
```bash
# Create feature branch from main
git checkout main
git pull origin main
git checkout -b feature/my-feature

# Develop and commit
git add .
git commit -m "feat: add new feature"
git push origin feature/my-feature
```

#### 2. Staging Test (Preview Deployment)
```bash
# Create PR to main
# GitHub Actions will:
# - Run CI checks
# - Vercel creates preview deployment for testing

# Test on staging backend
curl https://morningai-backend-v2-stg.onrender.com/healthz
# Test frontend via Vercel preview URL
```

#### 3. Production Deployment
```bash
# After PR approval and merge to main
# Auto-deploys to production services
```

### CI/CD Workflows

#### CI (`.github/workflows/backend.yml`, etc.)
- **Trigger**: Push/PR to `main` branch
- **Tests**: Backend (pytest + coverage 74%+), Frontend (build), E2E tests, Smoke tests
- **Deploy**: Auto-deploy to production services on merge to `main`
- **Environment**: `ENVIRONMENT=production`
- **Validation**: Post-deploy health checks (90% SLA)

---

## 🧪 Testing Environments

### Health Check Commands

**Production**:
```bash
# Backend
curl https://morningai-backend-v2.onrender.com/healthz

# Orchestrator
curl https://morningai-orchestrator-api.onrender.com/health

# Monitoring Dashboard
curl https://morningai-backend-v2.onrender.com/api/phase7/monitoring/dashboard
```

**Staging**:
```bash
# Backend
curl https://morningai-backend-v2-stg.onrender.com/healthz

# Orchestrator
curl https://morningai-orchestrator-api-stg.onrender.com/health

# Monitoring Dashboard
curl https://morningai-backend-v2-stg.onrender.com/api/phase7/monitoring/dashboard
```

**Local**:
```bash
# Backend
curl http://localhost:8000/healthz

# Orchestrator
curl http://localhost:8001/health

# Monitoring Dashboard
curl http://localhost:8000/api/phase7/monitoring/dashboard
```

### Monitoring Dashboard Endpoints

**Primary Endpoint** (Recommended):
- **Path**: `/api/phase7/monitoring/dashboard`
- **Method**: GET
- **Auth**: Public (no JWT required)
- **Status**: ✅ Production Ready

**Legacy Endpoint** (Deprecated):
- **Path**: `/api/dashboard/data`
- **Method**: GET
- **Auth**: Public (no JWT required)
- **Status**: ⚠️ **DEPRECATED** - Use `/api/phase7/monitoring/dashboard` instead
- **Deprecation Timeline**: TBD (tracked in future release notes)

**Degradation Behavior**:

| Scenario | HTTP Status | Response Behavior |
|----------|-------------|-------------------|
| All services healthy | 200 OK | Full metrics with real data |
| Redis unavailable | 200 OK | Fallback metrics with `available: false`, `source: 'fallback'`, `error: 'Redis unavailable'` |
| Database unavailable | 200 OK | `overall_status: 'degraded'` with critical alert |
| Both Redis + DB unavailable | 503 Service Unavailable | `ServiceUnavailableError` response |

**Environment Variables**:
- `REDIS_URL`: Required for queue metrics
- `DATABASE_URL`: Required for health checks
- `BACKEND_SERVICES_AVAILABLE`: Gate flag (auto-set by backend)

**Documentation**: See [Monitoring Troubleshooting Guide](deployment/troubleshooting-monitoring.md) for 503 error diagnosis

### Expected Responses

**Backend `/healthz`**:
```json
{
  "status": "healthy",
  "phase": "Phase 8",
  "version": "8.0.0",
  "database": "connected",
  "redis": {
    "status": "connected",
    "protocol": "rediss",
    "tls_enabled": true
  },
  "services": {
    "backend_services": "available",
    "phase4_apis": "available",
    "phase5_apis": "available",
    "phase6_apis": "available",
    "security_manager": "available"
  }
}
```

**Orchestrator `/health`**:
```json
{
  "status": "healthy",
  "redis": "connected",
  "queue_stats": {
    "pending_tasks": 0,
    "processing_tasks": 0,
    "total_tasks": 0
  }
}
```

---

## 🔐 Security & Secrets

### Secret Management

**Production Secrets**:
- Stored in Render dashboard (encrypted)
- Different from staging secrets
- Minimum 32 characters for JWT/encryption keys
- Rotated quarterly

**Staging Secrets**:
- Stored in Render dashboard (encrypted)
- Different from production secrets
- Can use weaker secrets (but still 32+ chars)
- Rotated as needed

**Local Secrets**:
- Stored in `.env` files (gitignored)
- Can use test/dummy values
- Never commit to repository

### Secret Generation

```bash
# Generate JWT secret (48 characters recommended)
python3 -c "import secrets; print(secrets.token_urlsafe(48))"

# Generate encryption key (32 characters minimum)
openssl rand -hex 32

# Generate API key
python3 -c "import secrets; print(secrets.token_urlsafe(32))"
```

---

## 📊 Monitoring & Observability

### Sentry Error Tracking

**Production**:
- Environment: `production`
- Dashboard: https://sentry.io/organizations/morningai/issues/?environment=production
- Alerts: Enabled for critical errors

**Staging**:
- Environment: `staging`
- Dashboard: https://sentry.io/organizations/morningai/issues/?environment=staging
- Alerts: Disabled (testing environment)

### Render Monitoring

**Production Services**:
- Dashboard: https://dashboard.render.com/
- Metrics: CPU, Memory, Request count
- Logs: Real-time log streaming
- Alerts: Enabled for downtime

**Staging Services**:
- Dashboard: https://dashboard.render.com/
- Auto-suspend: Enabled (15 minutes inactivity)
- Cost optimization: ~50% savings

### Supabase Monitoring

**Production Database**:
- Dashboard: https://supabase.com/dashboard/project/[production-id]
- Metrics: Connection pool, Query performance
- Backups: Daily automatic backups

**Staging Database**:
- Dashboard: https://supabase.com/dashboard/project/dckisglnlemvpvmyvnut
- Metrics: Connection pool, Query performance
- Data cleanup: Monthly manual cleanup

---

## 💰 Cost Breakdown

### Production
- **Render Backend**: $7/month (Starter)
- **Render Orchestrator**: $7/month (Starter)
- **Vercel Frontend**: $0/month (Free tier)
- **Supabase Database**: $0/month (Free tier) or $25/month (Pro)
- **Upstash Redis**: $0/month (Free tier) or $10/month (Pay-as-you-go)
- **Total**: ~$14-49/month

### Staging
- **Render Backend**: $7/month (Starter, auto-suspend enabled)
- **Render Orchestrator**: $7/month (Starter, auto-suspend enabled)
- **Supabase Database**: $0/month (Free tier)
- **Upstash Redis**: $0/month (Shared with production)
- **Total**: ~$14/month (effective ~$7/month with auto-suspend)

### Local Development
- **Cost**: $0/month
- **Infrastructure**: Developer workstation only

---

## 🚨 Troubleshooting

### Common Issues

#### Issue: Service won't start
**Check**:
1. Build logs in Render dashboard
2. All required environment variables are set
3. `DATABASE_URL` format is correct
4. `REDIS_URL` is accessible

**Fix**:
```bash
# Test DATABASE_URL locally
python -c "from sqlalchemy import create_engine; engine = create_engine('$DATABASE_URL'); print(engine.connect())"

# Test REDIS_URL locally
python -c "import redis; r = redis.from_url('$REDIS_URL'); print(r.ping())"
```

#### Issue: Database connection fails
**Check**:
1. Supabase project is running (not paused)
2. `DATABASE_URL` includes correct password
3. Connection pooler is enabled (port 6543)
4. IP allowlist includes Render IPs (if configured)

**Fix**:
- Get fresh `DATABASE_URL` from Supabase dashboard → Settings → Database → Connection string (Pooler)

#### Issue: Redis connection fails
**Check**:
1. `REDIS_URL` uses `rediss://` (double s) for TLS
2. Upstash Redis is accessible
3. Password is correct

**Fix**:
- Get fresh `REDIS_URL` from Upstash dashboard
- Ensure `rediss://` scheme (not `redis://`)

#### Issue: ORCHESTRATOR_JWT_SECRET error
**Error**: `CRITICAL SECURITY ERROR: ORCHESTRATOR_JWT_SECRET environment variable is not set`

**Fix**:
```bash
# Generate new secret (48 characters)
python3 -c "import secrets; print(secrets.token_urlsafe(48))"

# Add to Render environment variables
# Key: ORCHESTRATOR_JWT_SECRET
# Value: <generated-secret>
```

#### Issue: Staging auto-suspend too aggressive
**Fix**:
- Disable auto-suspend in Render dashboard
- Or: Set up cron job to ping `/healthz` every 10 minutes

---

## 📝 Best Practices

### Development
1. **Always test on staging first** before merging to `main`
2. **Use feature branches** for all development
3. **Run tests locally** before pushing
4. **Keep staging data separate** from production

### Deployment
1. **Review staging deployment** before production
2. **Monitor health checks** after deployment
3. **Check Sentry** for errors after deployment
4. **Have rollback plan** ready

### Security
1. **Never commit secrets** to repository
2. **Use different secrets** for each environment
3. **Rotate secrets** quarterly (production) or as needed (staging)
4. **Use TLS** for all external connections (`rediss://`, `https://`)

### Cost Optimization
1. **Enable auto-suspend** for staging services
2. **Clean up staging data** monthly
3. **Monitor usage** in Render/Supabase dashboards
4. **Use free tiers** where possible

---

## 🔗 Quick Links

### Production
- **Backend**: https://morningai-backend-v2.onrender.com
- **Orchestrator**: https://morningai-orchestrator-api.onrender.com
- **Tenant Dashboard**: https://app.gm365.me
- **Owner Console**: https://admin.gm365.me
- **Render Dashboard**: https://dashboard.render.com/

### Staging
- **Backend**: https://morningai-backend-v2-stg.onrender.com
- **Orchestrator**: https://morningai-orchestrator-api-stg.onrender.com
- **Supabase**: https://supabase.com/dashboard/project/dckisglnlemvpvmyvnut
- **Setup Guide**: [docs/ops/STAGING_SETUP_GUIDE.md](ops/STAGING_SETUP_GUIDE.md)

### Documentation
- **Local Setup**: [docs/setup_local.md](setup_local.md)
- **Contributing**: [docs/CONTRIBUTING.md](CONTRIBUTING.md)
- **CI/CD**: [docs/ci_matrix.md](ci_matrix.md)
- **Architecture**: [docs/ARCHITECTURE.md](ARCHITECTURE.md)
- **Authentication API**: [docs/openapi.auth.yaml](openapi.auth.yaml) - 2FA/TOTP endpoints (OpenAPI 3.0.3)

---

**Last Updated**: 2025-10-28  
**Maintained By**: CTO / DevOps Team  
**Status**: ✅ All environments operational
