# MorningAI Project Structure Report

> 📚 **相關文件**: 
> - [術語對照表](./TERMINOLOGY.md) - 標準化的應用名稱和用戶類型定義
> - [Onboarding Guide](./ONBOARDING_GUIDE.md) - 新人入職指南和環境設置
> - [README](../README.md) - 專案概覽和快速導航
> - [環境變數 Schema](../config/env.schema.yaml) - 環境變數配置的單一真源

**Document Version**: 2.4.0  
**Last Updated**: 2025-12-20  
**Project Phase**: Phase 8 (v8.0.0) - MVP Foundation Complete + LangGraph 100% Rollout + EPIC B (PR_UPDATED Event Support)  
**Test Coverage**: 59.89% (Owner Console), 70%+ (Orchestrator), 74%+ (Backend)  
**Recent Activity**: 665+ commits on main (2025-11-12 至 2025-12-20，快照值截至 2025-12-20)  
**Strategic Roadmap**: [Reality Comparison Report](./STRATEGIC_ROADMAP_REALITY_COMPARE_2025_11_16.md) (Nov 16, 2025)  
**RLS Status**: TRUE tenant isolation deployed (Staging & Production, Dec 12, 2025)  
**LangGraph Status**: 100% Rollout Complete - Simple Mode removed (Dec 2025)

**Recent PRs (Dec 13 - Dec 20, 2025)** (198 PRs merged):

*EPIC B: PR_UPDATED Event Support & Phase BB Robustness:*
- **[PR #2789](https://github.com/RC918/morningai/pull/2789)** (Merged): feat(phase-bb): P2 technical debt - extract helper, narrow exceptions, add tests
  - Path: `handoff/20250928/40_App/orchestrator/`
- **[PR #2788](https://github.com/RC918/morningai/pull/2788)** (Merged): feat(epic-b): Phase 2 - Line drift protection with head_sha tracking
  - Path: `handoff/20250928/40_App/orchestrator/`
- **[PR #2786](https://github.com/RC918/morningai/pull/2786)** (Merged): feat(phase-bb): add REDIS_KEY_PREFIX to pr_updated keys for environment isolation
  - Path: `handoff/20250928/40_App/orchestrator/`
  - New env var: `REDIS_KEY_PREFIX` for multi-environment Redis key isolation
- **[PR #2785](https://github.com/RC918/morningai/pull/2785)** (Merged): feat(epic-b): Phase 1 Quick Wins - LLM reliability and file-level comments delivery
  - Path: `handoff/20250928/40_App/orchestrator/`
- **[PR #2769](https://github.com/RC918/morningai/pull/2769)** (Merged): feat(phase-bb): add PR_UPDATED event support with debounce/throttle
  - Path: `handoff/20250928/40_App/orchestrator/`
- **[PR #2768](https://github.com/RC918/morningai/pull/2768)** (Merged): feat(phase-bb): add 422 fault injection for fallback verification
  - Path: `handoff/20250928/40_App/orchestrator/`
- **[PR #2741](https://github.com/RC918/morningai/pull/2741)** (Merged): feat(phase-bb): add C-lite telemetry for EPIC B KPIs
  - Path: `handoff/20250928/40_App/orchestrator/`

*LangGraph 100% Rollout & Simple Mode Removal:*
- **[PR #2767](https://github.com/RC918/morningai/pull/2767)** (Merged): chore: remove Simple Mode code after LangGraph 100% rollout (#2651)
  - Path: `handoff/20250928/40_App/orchestrator/`
  - **MAJOR**: Complete removal of Simple Mode code - LangGraph is now the only orchestration mode
- **[PR #2771](https://github.com/RC918/morningai/pull/2771)** (Merged): feat(checkpointer): add PostgreSQL checkpointer support for LangGraph
  - Path: `handoff/20250928/40_App/orchestrator/`
- **[PR #2766](https://github.com/RC918/morningai/pull/2766)** (Merged): chore: remove deprecated rollout API endpoints
  - Path: `handoff/20250928/40_App/api-backend/`
- **[PR #2742](https://github.com/RC918/morningai/pull/2742)** (Merged): test(orchestrator): add E2E and circuit breaker tests for LangGraph-only mode (#2736)
  - Path: `handoff/20250928/40_App/orchestrator/`
- **[PR #2740](https://github.com/RC918/morningai/pull/2740)** (Merged): test(orchestrator): remove obsolete Simple Mode tests (#2738)
  - Path: `handoff/20250928/40_App/orchestrator/`
- **[PR #2720](https://github.com/RC918/morningai/pull/2720)** (Merged): feat(orchestrator): remove Simple Mode - LangGraph only (#2651)
  - Path: `handoff/20250928/40_App/orchestrator/`

*EPIC B: Inline Code Review (Phase B-1 to B-3):*
- **[PR #2714](https://github.com/RC918/morningai/pull/2714)** (Merged): feat(publisher): add inline comment validation and line number semantics (Phase B-3.1)
  - Path: `handoff/20250928/40_App/orchestrator/nodes/publisher_node.py`
- **[PR #2710](https://github.com/RC918/morningai/pull/2710)** (Merged): feat(diff): add ignore list and secrets redaction (Phase B-2.5)
  - Path: `handoff/20250928/40_App/orchestrator/`
- **[PR #2701](https://github.com/RC918/morningai/pull/2701)** (Merged): feat(publisher): add GitHub inline comment posting (EPIC B Phase B-3)
  - Path: `handoff/20250928/40_App/orchestrator/nodes/publisher_node.py`
- **[PR #2693](https://github.com/RC918/morningai/pull/2693)** (Merged): feat(reviewer): add review comment schema with start_line/end_line support (EPIC B Phase B-2)
  - Path: `handoff/20250928/40_App/orchestrator/`
- **[PR #2692](https://github.com/RC918/morningai/pull/2692)** (Merged): feat(reviewer): implement diff-aware code review (EPIC B Phase B-1)
  - Path: `handoff/20250928/40_App/orchestrator/`

*Agent Architecture & Routing:*
- **[PR #2783](https://github.com/RC918/morningai/pull/2783)** (Merged): fix(governance): resolve agent_type to UUID for ReputationEngine DB operations
  - Path: `handoff/20250928/40_App/orchestrator/governance/reputation_engine.py`
- **[PR #2674](https://github.com/RC918/morningai/pull/2674)** (Merged): feat(agents): implement BaseAgent with dynamic routing and Telemetry v2
  - Path: `handoff/20250928/40_App/orchestrator/`
- **[PR #2665](https://github.com/RC918/morningai/pull/2665)** (Merged): feat(routing): implement Routing Policy v1.1 for multi-model LLM selection
  - Path: `handoff/20250928/40_App/orchestrator/`
- **[PR #2659](https://github.com/RC918/morningai/pull/2659)** (Merged): feat(llm): add Qwen3 provider adapters for AliCloud and SiliconFlow
  - Path: `handoff/20250928/40_App/orchestrator/`

*CI/CD Infrastructure & Qwen Workflow:*
- **[PR #2779](https://github.com/RC918/morningai/pull/2779)** (Merged): feat(tests): add CI integration tests and fault injection tests (#2650)
  - Path: `handoff/20250928/40_App/orchestrator/redis_queue/tests/`
- **[PR #2774](https://github.com/RC918/morningai/pull/2774)** (Merged): refactor(ci): extract CI Guard to testable script with resource limits
  - Path: `.github/workflows/`, `scripts/ci/`
- **[PR #2593](https://github.com/RC918/morningai/pull/2593)** (Merged): feat(typescript): add strict mode baseline system (TS-1, TS-2)
  - Path: `scripts/`, `.github/workflows/`
- **[PR #2583](https://github.com/RC918/morningai/pull/2583)** (Merged): feat(ci): add lockfile sync check to prevent dev/CI/prod drift
  - Path: `.github/workflows/`
- **[PR #2540](https://github.com/RC918/morningai/pull/2540)** (Merged): feat: add Qwen AI code review workflow for all PRs
  - Path: `.github/workflows/qwen-pr-review.yml`

*Design System & UI Components (Epic #2304):*
- **[PR #2508](https://github.com/RC918/morningai/pull/2508)** (Merged): feat(governance): establish design system governance rules (#2303)
  - Path: `docs/`, `packages/shared-ui/`
- **[PR #2434](https://github.com/RC918/morningai/pull/2434)** (Merged): feat(shared-ui): Issue #2296 - Add SettingsCard component
  - Path: `packages/shared-ui/`
- **[PR #2426](https://github.com/RC918/morningai/pull/2426)** (Merged): feat(shared-ui): Issue #2295 - Add MetricCard component
  - Path: `packages/shared-ui/`
- **[PR #2402](https://github.com/RC918/morningai/pull/2402)** (Merged): feat(shared-ui): Issue #2293 - Add StatusCard component
  - Path: `packages/shared-ui/`
- **[PR #2359](https://github.com/RC918/morningai/pull/2359)** (Merged): feat(design-system): Implement Epic #2304 Phase 0-1 (UI/UX Foundation + Core)
  - Path: `packages/shared-ui/`

*Backend Refactoring (api-backend main.py):*
- **[PR #2489](https://github.com/RC918/morningai/pull/2489)** (Merged): [PR1.5] Extract App Factory Pattern to create_app()
  - Path: `handoff/20250928/40_App/api-backend/src/main.py`
- **[PR #2485](https://github.com/RC918/morningai/pull/2485)** (Merged): [PR1f] Extract Sentry initialization to src/extensions/sentry.py
  - Path: `handoff/20250928/40_App/api-backend/src/extensions/sentry.py`
- **[PR #2481](https://github.com/RC918/morningai/pull/2481)** (Merged): [PR1e] Extract Database Initialization to src/extensions/database.py
  - Path: `handoff/20250928/40_App/api-backend/src/extensions/database.py`
- **[PR #2448](https://github.com/RC918/morningai/pull/2448)** (Merged): [PR1b] Extract CORS middleware to src/middleware/cors.py
  - Path: `handoff/20250928/40_App/api-backend/src/middleware/cors.py`

*Owner Console Features:*
- **[PR #2569](https://github.com/RC918/morningai/pull/2569)** (Merged): feat(sessions): add IDE Activity panel for real-time file monitoring (#2241)
  - Path: `handoff/20250928/40_App/owner-console/src/components/`
- **[PR #2563](https://github.com/RC918/morningai/pull/2563)** (Merged): feat(dx): implement multiple PR templates (#2477)
  - Path: `.github/PULL_REQUEST_TEMPLATE/`

*Dependency Updates (28 PRs):*
- Major updates: sentry-sdk 2.48.0, aiohttp 3.13.2, openai <3.0.0, redis <7.0.0
- GitHub Actions: actions/checkout@6, actions/setup-node@6, actions/upload-artifact@6
- npm packages: 40 updates in owner-console, 25 updates in shared-ui

**Recent PRs (Dec 10 - Dec 12, 2025)**:

*RLS & Deployment:*
- **[PR #2336](https://github.com/RC918/morningai/pull/2336)** (Merged): fix(api-backend): make Sentry initialization conditional based on SENTRY_DSN
  - Path: `handoff/20250928/40_App/api-backend/src/sentry_integration.py`
- **[PR #2339](https://github.com/RC918/morningai/pull/2339)** (Merged): docs: add MorningAI deep analysis report and update RLS deployment status
  - Path: `docs/MORNINGAI_深度解析報告_2025-12-12.md`, `docs/RLS_DEPLOYMENT_STATUS.md`
  - RLS TRUE tenant isolation deployed to Staging and Production

**Recent PRs (Dec 7 - Dec 9, 2025)**:

*DeepWiki Integration:*
- **[PR #2156](https://github.com/RC918/morningai/pull/2156)** (Merged): feat(deepwiki): integrate DeepWiki session insights into AutonomousExecutor
  - Path: `handoff/20250928/40_App/orchestrator/meta_agent/autonomous_executor.py`
- **[PR #2157](https://github.com/RC918/morningai/pull/2157)** (Merged): feat(orchestrator): integrate DeepWiki with AutonomousExecutor
  - Path: `handoff/20250928/40_App/orchestrator/`
- **[PR #2164](https://github.com/RC918/morningai/pull/2164)** (Merged): fix(deepwiki): add retry logic and rate limiting
  - Path: `handoff/20250928/40_App/orchestrator/`
- **[PR #2163](https://github.com/RC918/morningai/pull/2163)** (Merged): feat(api): add DeepWiki API endpoints for knowledge base queries
  - Path: `handoff/20250928/40_App/api-backend/`
- **[PR #2169](https://github.com/RC918/morningai/pull/2169)** (Merged): feat(owner-console): add SessionInsights component for DeepWiki insights
  - Path: `handoff/20250928/40_App/owner-console/src/components/`

*Sessions UI & HITL Optimization:*
- **[PR #2170](https://github.com/RC918/morningai/pull/2170)** (Merged): feat(owner-console): HITL approval UI/UX optimization
  - Path: `handoff/20250928/40_App/owner-console/src/components/`
- **[PR #2173](https://github.com/RC918/morningai/pull/2173)** (Merged): feat(i18n): add SessionInsights translation keys and unit tests
  - Path: `handoff/20250928/40_App/owner-console/src/i18n/`
- **[PR #2175](https://github.com/RC918/morningai/pull/2175)** (Merged): feat(owner-console): add SessionCommandInput for interactive session commands
  - Path: `handoff/20250928/40_App/owner-console/src/components/`
- **[PR #2182](https://github.com/RC918/morningai/pull/2182)** (Merged): refactor(owner-console): tidy SessionCommandInput constants and props
  - Path: `handoff/20250928/40_App/owner-console/src/components/`
- **[PR #2188](https://github.com/RC918/morningai/pull/2188)** (Merged): test(owner-console): add unit tests for SessionCommandInput
  - Path: `handoff/20250928/40_App/owner-console/src/components/`
- **[PR #2189](https://github.com/RC918/morningai/pull/2189)** (Merged): feat(owner-console): persist command history with localStorage
  - Path: `handoff/20250928/40_App/owner-console/src/components/`
- **[PR #2225](https://github.com/RC918/morningai/pull/2225)** (Merged): fix(owner-console): fix ApprovalQueue TDZ error and improve auto-refresh
  - Path: `handoff/20250928/40_App/owner-console/src/components/`
- **[PR #2234](https://github.com/RC918/morningai/pull/2234)** (Merged): fix(owner-console): fix console warnings and session card layout issues
  - Path: `handoff/20250928/40_App/owner-console/src/components/`
- **[PR #2279](https://github.com/RC918/morningai/pull/2279)** (Merged): feat(owner-console): add SessionStatusCard component with standardized design spec
  - Path: `handoff/20250928/40_App/owner-console/src/components/`

*CSRF Token Management:*
- **[PR #2237](https://github.com/RC918/morningai/pull/2237)** (Merged): fix(owner-console): fix CSRF token sync issue causing 403 errors
  - Path: `handoff/20250928/40_App/owner-console/src/lib/csrf-token.ts`
- **[PR #2238](https://github.com/RC918/morningai/pull/2238)** (Merged): refactor(owner-console): unify CSRF token management
  - Path: `handoff/20250928/40_App/owner-console/src/lib/csrf-token.ts`
- **[PR #2239](https://github.com/RC918/morningai/pull/2239)** (Merged): docs(owner-console): add CSRF token mode selection warning
  - Path: `handoff/20250928/40_App/owner-console/src/lib/csrf-token.ts`
- **[PR #2240](https://github.com/RC918/morningai/pull/2240)** (Merged): docs(owner-console): add warning comment for CSRF token mode selection
  - Path: `handoff/20250928/40_App/owner-console/src/lib/csrf-token.ts`

*AI Reviewer & Comment Triage:*
- **[PR #2244](https://github.com/RC918/morningai/pull/2244)** (Merged): feat(orchestrator): fix AI Reviewer comment intake mechanism
  - Path: `handoff/20250928/40_App/orchestrator/nodes/review_intake.py`
- **[PR #2246](https://github.com/RC918/morningai/pull/2246)** (Merged): feat(orchestrator): implement Comment Triage Agent for AI reviewer comments
  - Path: `handoff/20250928/40_App/orchestrator/nodes/comment_triage.py` (new file)

*Review Follow-up & Internal Reviewer (Phase 7):*
- **[PR #2257](https://github.com/RC918/morningai/pull/2257)** (Merged): feat(orchestrator): implement Review Follow-up Mode (Issue #2211)
  - Path: `handoff/20250928/40_App/orchestrator/nodes/review_follow_up.py` (new file)
- **[PR #2262](https://github.com/RC918/morningai/pull/2262)** (Merged): feat(orchestrator): implement Internal Reviewer Agent re-review mechanism (Issue #2212)
  - Path: `handoff/20250928/40_App/orchestrator/nodes/internal_review_node.py` (new file)
- **[PR #2267](https://github.com/RC918/morningai/pull/2267)** (Merged): refactor(orchestrator): add required field validation in internal_review_node (Issue #2263)
  - Path: `handoff/20250928/40_App/orchestrator/nodes/internal_review_node.py`
- **[PR #2268](https://github.com/RC918/morningai/pull/2268)** (Merged): feat(orchestrator): add configurable PARTIAL agreement policy (Issue #2264)
  - Path: `handoff/20250928/40_App/orchestrator/nodes/internal_review_node.py`
- **[PR #2269](https://github.com/RC918/morningai/pull/2269)** (Merged): docs(orchestrator): document internal_review_node vs reviewer_node responsibilities (Issue #2265)
  - Path: `handoff/20250928/40_App/orchestrator/docs/` (new documentation)

*Multi-Signal Trigger & Rollout Tracker (Phase 7):*
- **[PR #2275](https://github.com/RC918/morningai/pull/2275)** (Merged): feat(orchestrator): implement Multi-Signal Trigger System (Issue #2213)
  - Path: `handoff/20250928/40_App/orchestrator/multi_signal_trigger.py` (new file)
- **[PR #2278](https://github.com/RC918/morningai/pull/2278)** (Merged): feat(orchestrator): implement LangGraph 100% Rollout Tracker (Issue #2214)
  - Path: `handoff/20250928/40_App/orchestrator/rollout_tracker.py` (new file)
- **[PR #2284](https://github.com/RC918/morningai/pull/2284)** (Merged): feat(orchestrator): integrate RolloutTracker into worker.py (Issue #2280)
  - Path: `handoff/20250928/40_App/orchestrator/redis_queue/worker.py`
- **[PR #2288](https://github.com/RC918/morningai/pull/2288)** (Merged): docs: update milestones document with Dec 2025 progress (Issue #2215)
  - Path: `docs/MILESTONES.md`

*Owner Console UI Refactoring:*
- **[PR #2245](https://github.com/RC918/morningai/pull/2245)** (Merged): refactor(owner-console): move settings and logout to user dropdown menu
  - Path: `handoff/20250928/40_App/owner-console/src/components/`
- **[PR #2256](https://github.com/RC918/morningai/pull/2256)** (Merged): refactor(owner-console): DashboardHeader cleanup and testing
  - Path: `handoff/20250928/40_App/owner-console/src/components/DashboardHeader.jsx`
- **[PR #2261](https://github.com/RC918/morningai/pull/2261)** (Merged): refactor(owner-console): Sidebar UX optimization - single-line items and tooltips
  - Path: `handoff/20250928/40_App/owner-console/src/components/Sidebar.jsx`
- **[PR #2266](https://github.com/RC918/morningai/pull/2266)** (Merged): refactor(owner-console): implement single-layer Header + Sidebar architecture
  - Path: `handoff/20250928/40_App/owner-console/src/components/`
- **[PR #2270](https://github.com/RC918/morningai/pull/2270)** (Merged): fix(shared-ui): add arrowClassName prop to Tooltip for customizable arrow styling
  - Path: `packages/shared-ui/src/components/ui/tooltip.tsx`

*CI/CD & Testing Infrastructure:*
- **[PR #2174](https://github.com/RC918/morningai/pull/2174)** (Merged): feat(ci): enable TypeScript Strict Mode baseline tracking for all packages
  - Path: `.github/workflows/`
- **[PR #2183](https://github.com/RC918/morningai/pull/2183)** (Merged): fix(orchestrator): fix failing tests in visual_verification and project_engineer
  - Path: `handoff/20250928/40_App/orchestrator/`
- **[PR #2190](https://github.com/RC918/morningai/pull/2190)** (Merged): fix(orchestrator): increase performance test threshold for planner node
  - Path: `handoff/20250928/40_App/orchestrator/`
- **[PR #2194](https://github.com/RC918/morningai/pull/2194)** (Merged): fix(orchestrator): add rate limit mock to TestExecute tests
  - Path: `handoff/20250928/40_App/orchestrator/`
- **[PR #2200](https://github.com/RC918/morningai/pull/2200)** (Merged): test(orchestrator): add comprehensive tests for langgraph_orchestrator.py
  - Path: `handoff/20250928/40_App/orchestrator/tests/`
- **[PR #2233](https://github.com/RC918/morningai/pull/2233)** (Merged): test(api-backend): add comprehensive tests for sentry_integration.py
  - Path: `handoff/20250928/40_App/api-backend/`
- **[PR #2235](https://github.com/RC918/morningai/pull/2235)** (Merged): test(orchestrator): add security rules tests for project_engineer/agent.py
  - Path: `handoff/20250928/40_App/orchestrator/`
- **[PR #2236](https://github.com/RC918/morningai/pull/2236)** (Merged): test(owner-console): add comprehensive tests for LoginPage component
  - Path: `handoff/20250928/40_App/owner-console/src/pages/`

*Backend & Infrastructure:*
- **[PR #2184](https://github.com/RC918/morningai/pull/2184)** (Merged): feat(api-backend): add /api/sessions/{id}/command endpoint
  - Path: `handoff/20250928/40_App/api-backend/`
- **[PR #2197](https://github.com/RC918/morningai/pull/2197)** (Merged): feat(orchestrator): add A/B testing metrics collection and analysis framework
  - Path: `handoff/20250928/40_App/orchestrator/`
- **[PR #2204](https://github.com/RC918/morningai/pull/2204)** (Merged): fix: reduce noisy Sentry alerts for expected error conditions
  - Path: `handoff/20250928/40_App/api-backend/`
- **[PR #2218](https://github.com/RC918/morningai/pull/2218)** (Merged): feat(orchestrator): complete Wave 1 Phase 7 prerequisites
  - Path: `handoff/20250928/40_App/orchestrator/`
- **[PR #2224](https://github.com/RC918/morningai/pull/2224)** (Merged): feat(orchestrator): add retry and rate limiting to OutboundNotifier
  - Path: `handoff/20250928/40_App/orchestrator/`
- **[PR #2231](https://github.com/RC918/morningai/pull/2231)** (Merged): feat(orchestrator): Wave 3 Failure Learning Enhancement
  - Path: `handoff/20250928/40_App/orchestrator/`
- **[PR #2232](https://github.com/RC918/morningai/pull/2232)** (Merged): fix(api-backend): add Upstash Redis adapter for scan_iter compatibility
  - Path: `handoff/20250928/40_App/api-backend/`

*Documentation:*
- **[PR #2193](https://github.com/RC918/morningai/pull/2193)** (Merged): docs: align documentation with actual implementation
  - Path: `docs/`

**Recent PRs (Dec 6 - Dec 7, 2025)**:

*VSCode/MCP Integration & Meta-Agent Production Wiring:*
- **[PR #2114](https://github.com/RC918/morningai/pull/2114)** (Merged): feat(meta-agent): integrate VSCodeIDEService into production code
  - Path: `handoff/20250928/40_App/orchestrator/meta_agent/autonomous_executor.py` (major update)
  - New: VM/IDE lifecycle management integrated into AutonomousExecutor
- **[PR #2067](https://github.com/RC918/morningai/pull/2067)** (Merged): feat(meta-agent): implement MCP HTTP client for cloud IDE integration
  - Path: `handoff/20250928/40_App/orchestrator/meta_agent/vscode_ide.py` (core implementation)
- **[PR #2106](https://github.com/RC918/morningai/pull/2106)** (Merged): perf(vscode-ide): share aiohttp ClientSession for connection reuse
- **[PR #2102](https://github.com/RC918/morningai/pull/2102)** (Merged): refactor(vscode-ide): extract constants and use exponential backoff
- **[PR #2077](https://github.com/RC918/morningai/pull/2077)** (Merged): security(vscode-ide): truncate error logs to prevent sensitive data leakage

*VSCode/MCP Documentation & Infrastructure:*
- **[PR #2101](https://github.com/RC918/morningai/pull/2101)** (Merged): docs(meta-agent): add Tier 2 VSCode/VM documentation
  - Path: `handoff/20250928/40_App/orchestrator/docs/` (new directory)
  - New files: `TERMINAL_ACCESS.md`, `VM_LOCKING_DESIGN.md`, `VM_PROVISIONER_LIFECYCLE.md`
- **[PR #2115](https://github.com/RC918/morningai/pull/2115)** (Merged): docs(orchestrator): add cross-process limitation note and environment settings
- **[PR #2110](https://github.com/RC918/morningai/pull/2110)** (Merged): test(vscode-ide): use mocker.patch.object() for cleaner test mocking
  - Path: `handoff/20250928/40_App/orchestrator/requirements-test.txt` (added pytest-mock)

*Documentation Auto-Generation Security:*
- **[PR #2103](https://github.com/RC918/morningai/pull/2103)** (Merged): refactor(orchestrator): improve documentation auto-generation security
  - New env var: `ORCHESTRATOR_DOCS_MAX_PRS_PER_HOUR` (integer, default: 3)

*Owner Console Sessions UI & Performance:*
- **[PR #2063](https://github.com/RC918/morningai/pull/2063)** (Merged): feat(owner-console): integrate ConfidenceApproval and FileDiffViewer
- **[PR #2088](https://github.com/RC918/morningai/pull/2088)** (Merged): refactor(owner-console): Sessions.jsx defensive code improvements
- **[PR #2089](https://github.com/RC918/morningai/pull/2089)** (Merged): perf(owner-console): optimize FCP with lazy loading
- **[PR #2087](https://github.com/RC918/morningai/pull/2087)** (Merged): a11y(owner-console): improve keyboard accessibility for drag-and-drop

*Design System & Storybook:*
- **[PR #2068](https://github.com/RC918/morningai/pull/2068)** (Merged): fix(owner-console): add base tokens to @theme for shared-ui Switch
- **[PR #2084](https://github.com/RC918/morningai/pull/2084)** (Merged): docs(shared-ui): add Switch Storybook visual verification story
  - Path: `packages/shared-ui/src/components/ui/switch.stories.tsx` (new file)
- **[PR #2083](https://github.com/RC918/morningai/pull/2083)** (Merged): docs(owner-console): add Storybook stories for task plan components
- **[PR #2061](https://github.com/RC918/morningai/pull/2061)** (Merged): chore(owner-console): remove dead theme.css file
  - Path: `handoff/20250928/40_App/owner-console/src/styles/theme.css` (removed)

*Security & Testing:*
- **[PR #2052](https://github.com/RC918/morningai/pull/2052)** (Merged): fix(meta-agent): add TOCTOU defense in save_state()
- **[PR #2078](https://github.com/RC918/morningai/pull/2078)** (Merged): test(owner-console): add XSS protection tests for TestResultsPanel
- **[PR #2079](https://github.com/RC918/morningai/pull/2079)** (Merged): test(orchestrator): add unit tests for update_error_fix_pair

**Recent PRs (Dec 8 - Dec 9, 2025)**:

*DeepWiki Integration:*
- **[PR #2156](https://github.com/RC918/morningai/pull/2156)** (Merged): feat(deepwiki): integrate DeepWiki session insights into AutonomousExecutor
  - Path: `handoff/20250928/40_App/orchestrator/meta_agent/autonomous_executor.py`
- **[PR #2157](https://github.com/RC918/morningai/pull/2157)** (Merged): feat(orchestrator): integrate DeepWiki with AutonomousExecutor
- **[PR #2164](https://github.com/RC918/morningai/pull/2164)** (Merged): fix(deepwiki): add retry logic and rate limiting
- **[PR #2163](https://github.com/RC918/morningai/pull/2163)** (Merged): feat(api): add DeepWiki API endpoints for knowledge base queries
  - Path: `handoff/20250928/40_App/api-backend/`
- **[PR #2169](https://github.com/RC918/morningai/pull/2169)** (Merged): feat(owner-console): add SessionInsights component for DeepWiki insights
  - Path: `handoff/20250928/40_App/owner-console/src/components/`

*Sessions UI & HITL Optimization:*
- **[PR #2170](https://github.com/RC918/morningai/pull/2170)** (Merged): feat(owner-console): HITL approval UI/UX optimization
- **[PR #2173](https://github.com/RC918/morningai/pull/2173)** (Merged): feat(i18n): add SessionInsights translation keys and unit tests
- **[PR #2175](https://github.com/RC918/morningai/pull/2175)** (Merged): feat(owner-console): add SessionCommandInput for interactive session commands
- **[PR #2182](https://github.com/RC918/morningai/pull/2182)** (Merged): refactor(owner-console): tidy SessionCommandInput constants and props
- **[PR #2188](https://github.com/RC918/morningai/pull/2188)** (Merged): test(owner-console): add unit tests for SessionCommandInput
- **[PR #2189](https://github.com/RC918/morningai/pull/2189)** (Merged): feat(owner-console): persist command history with localStorage
- **[PR #2225](https://github.com/RC918/morningai/pull/2225)** (Merged): fix(owner-console): fix ApprovalQueue TDZ error and improve auto-refresh
- **[PR #2234](https://github.com/RC918/morningai/pull/2234)** (Merged): fix(owner-console): fix console warnings and session card layout issues
- **[PR #2279](https://github.com/RC918/morningai/pull/2279)** (Merged): feat(owner-console): add SessionStatusCard component with standardized design spec
  - Path: `handoff/20250928/40_App/owner-console/src/components/`

*CSRF Token Management:*
- **[PR #2237](https://github.com/RC918/morningai/pull/2237)** (Merged): fix(owner-console): fix CSRF token sync issue causing 403 errors
  - Path: `handoff/20250928/40_App/owner-console/src/lib/csrf-token.ts`
- **[PR #2238](https://github.com/RC918/morningai/pull/2238)** (Merged): refactor(owner-console): unify CSRF token management
- **[PR #2239](https://github.com/RC918/morningai/pull/2239)** (Merged): docs(owner-console): add CSRF token mode selection warning
- **[PR #2240](https://github.com/RC918/morningai/pull/2240)** (Merged): docs(owner-console): add warning comment for CSRF token mode selection

*AI Reviewer & Comment Triage:*
- **[PR #2244](https://github.com/RC918/morningai/pull/2244)** (Merged): feat(orchestrator): fix AI Reviewer comment intake mechanism
  - Path: `handoff/20250928/40_App/orchestrator/nodes/review_intake.py`
- **[PR #2246](https://github.com/RC918/morningai/pull/2246)** (Merged): feat(orchestrator): implement Comment Triage Agent for AI reviewer comments
  - Path: `handoff/20250928/40_App/orchestrator/nodes/comment_triage.py` (new file)

*Review Follow-up & Internal Reviewer (Phase 7 - Issue #2211, #2212):*
- **[PR #2257](https://github.com/RC918/morningai/pull/2257)** (Merged): feat(orchestrator): implement Review Follow-up Mode (Issue #2211)
  - Path: `handoff/20250928/40_App/orchestrator/nodes/review_follow_up.py` (new file)
- **[PR #2262](https://github.com/RC918/morningai/pull/2262)** (Merged): feat(orchestrator): implement Internal Reviewer Agent re-review mechanism (Issue #2212)
  - Path: `handoff/20250928/40_App/orchestrator/nodes/internal_review_node.py` (new file)
- **[PR #2267](https://github.com/RC918/morningai/pull/2267)** (Merged): refactor(orchestrator): add required field validation in internal_review_node (Issue #2263)
- **[PR #2268](https://github.com/RC918/morningai/pull/2268)** (Merged): feat(orchestrator): add configurable PARTIAL agreement policy (Issue #2264)
- **[PR #2269](https://github.com/RC918/morningai/pull/2269)** (Merged): docs(orchestrator): document internal_review_node vs reviewer_node responsibilities (Issue #2265)
  - Path: `handoff/20250928/40_App/orchestrator/docs/` (new documentation)

*Multi-Signal Trigger & Rollout Tracker (Phase 7 - Issue #2213, #2214):*
- **[PR #2275](https://github.com/RC918/morningai/pull/2275)** (Merged): feat(orchestrator): implement Multi-Signal Trigger System (Issue #2213)
  - Path: `handoff/20250928/40_App/orchestrator/multi_signal_trigger.py` (new file)
- **[PR #2278](https://github.com/RC918/morningai/pull/2278)** (Merged): feat(orchestrator): implement LangGraph 100% Rollout Tracker (Issue #2214)
  - Path: `handoff/20250928/40_App/orchestrator/rollout_tracker.py` (new file)
- **[PR #2284](https://github.com/RC918/morningai/pull/2284)** (Merged): feat(orchestrator): integrate RolloutTracker into worker.py (Issue #2280)
  - Path: `handoff/20250928/40_App/orchestrator/redis_queue/worker.py`
- **[PR #2288](https://github.com/RC918/morningai/pull/2288)** (Merged): docs: update milestones document with Dec 2025 progress (Issue #2215)
  - Path: `docs/MILESTONES.md`

*Owner Console UI Refactoring:*
- **[PR #2245](https://github.com/RC918/morningai/pull/2245)** (Merged): refactor(owner-console): move settings and logout to user dropdown menu
- **[PR #2256](https://github.com/RC918/morningai/pull/2256)** (Merged): refactor(owner-console): DashboardHeader cleanup and testing
  - Path: `handoff/20250928/40_App/owner-console/src/components/DashboardHeader.jsx`
- **[PR #2261](https://github.com/RC918/morningai/pull/2261)** (Merged): refactor(owner-console): Sidebar UX optimization - single-line items and tooltips
  - Path: `handoff/20250928/40_App/owner-console/src/components/Sidebar.jsx`
- **[PR #2266](https://github.com/RC918/morningai/pull/2266)** (Merged): refactor(owner-console): implement single-layer Header + Sidebar architecture
- **[PR #2270](https://github.com/RC918/morningai/pull/2270)** (Merged): fix(shared-ui): add arrowClassName prop to Tooltip for customizable arrow styling
  - Path: `packages/shared-ui/src/components/ui/tooltip.tsx`

*CI/CD & Testing Infrastructure:*
- **[PR #2174](https://github.com/RC918/morningai/pull/2174)** (Merged): feat(ci): enable TypeScript Strict Mode baseline tracking for all packages
  - Path: `.github/workflows/`
- **[PR #2183](https://github.com/RC918/morningai/pull/2183)** (Merged): fix(orchestrator): fix failing tests in visual_verification and project_engineer
- **[PR #2190](https://github.com/RC918/morningai/pull/2190)** (Merged): fix(orchestrator): increase performance test threshold for planner node
- **[PR #2194](https://github.com/RC918/morningai/pull/2194)** (Merged): fix(orchestrator): add rate limit mock to TestExecute tests
- **[PR #2200](https://github.com/RC918/morningai/pull/2200)** (Merged): test(orchestrator): add comprehensive tests for langgraph_orchestrator.py
  - Path: `handoff/20250928/40_App/orchestrator/tests/`
- **[PR #2233](https://github.com/RC918/morningai/pull/2233)** (Merged): test(api-backend): add comprehensive tests for sentry_integration.py
- **[PR #2235](https://github.com/RC918/morningai/pull/2235)** (Merged): test(orchestrator): add security rules tests for project_engineer/agent.py
- **[PR #2236](https://github.com/RC918/morningai/pull/2236)** (Merged): test(owner-console): add comprehensive tests for LoginPage component

*Backend & Infrastructure:*
- **[PR #2184](https://github.com/RC918/morningai/pull/2184)** (Merged): feat(api-backend): add /api/sessions/{id}/command endpoint
  - Path: `handoff/20250928/40_App/api-backend/`
- **[PR #2197](https://github.com/RC918/morningai/pull/2197)** (Merged): feat(orchestrator): add A/B testing metrics collection and analysis framework
- **[PR #2204](https://github.com/RC918/morningai/pull/2204)** (Merged): fix: reduce noisy Sentry alerts for expected error conditions
- **[PR #2218](https://github.com/RC918/morningai/pull/2218)** (Merged): feat(orchestrator): complete Wave 1 Phase 7 prerequisites
- **[PR #2224](https://github.com/RC918/morningai/pull/2224)** (Merged): feat(orchestrator): add retry and rate limiting to OutboundNotifier
- **[PR #2231](https://github.com/RC918/morningai/pull/2231)** (Merged): feat(orchestrator): Wave 3 Failure Learning Enhancement
- **[PR #2232](https://github.com/RC918/morningai/pull/2232)** (Merged): fix(api-backend): add Upstash Redis adapter for scan_iter compatibility
  - Path: `handoff/20250928/40_App/api-backend/`

*Documentation:*
- **[PR #2193](https://github.com/RC918/morningai/pull/2193)** (Merged): docs: align documentation with actual implementation

**Recent PRs (Dec 3 - Dec 5, 2025)**:

*Refactor Agent & TS Strict Mode Automation:*
- **[PR #1886](https://github.com/RC918/morningai/pull/1886)** (Merged): Phase 4 - Refactor Agent for TS Strict Mode Automation
  - Path: `handoff/20250928/40_App/orchestrator/refactor_agent/` (new directory)
  - New env vars: `REFACTOR_AGENT_ENABLED`, `REFACTOR_AGENT_ERRORS_PER_RUN`, `REFACTOR_AGENT_AUTO_PR`
- **[PR #1897](https://github.com/RC918/morningai/pull/1897)** (Merged): LLM Integration for Refactor Agent Code Fix Generation
- **[PR #1903](https://github.com/RC918/morningai/pull/1903)** (Merged): File Modification Implementation for Refactor Agent
- **[PR #1908](https://github.com/RC918/morningai/pull/1908)** (Merged): PR Automation for Refactor Agent
- **[PR #1913](https://github.com/RC918/morningai/pull/1913)** (Merged): Nightly Cron Job Setup + Grammar/Optimization Improvements
  - Path: `.github/workflows/refactor-agent-nightly.yml` (new workflow)

*Task Queue Reliability (Ops Agent):*
- **[PR #1907](https://github.com/RC918/morningai/pull/1907)** (Merged): Fix infinite loop for unassigned tasks
  - Path: `agents/ops_agent/worker.py`
- **[PR #1912](https://github.com/RC918/morningai/pull/1912)** (Merged): Implement task status update and assigned_to validation
  - Path: `agents/ops_agent/worker.py`, `orchestrator/task_queue/redis_queue.py`
- **[PR #1914](https://github.com/RC918/morningai/pull/1914)** (Merged): Add automated tests for task routing (#1909, #1910)
  - Path: `agents/ops_agent/tests/test_task_routing.py` (new file)
- **[PR #1934](https://github.com/RC918/morningai/pull/1934)** (Merged): Use pytest pythonpath instead of sys.path.insert

*Owner Console Page Standardization (Phase 1 Complete):*
- **[PR #1863](https://github.com/RC918/morningai/pull/1863)** (Merged): Standardize AgentGovernance page layout
- **[PR #1867](https://github.com/RC918/morningai/pull/1867)** (Merged): Standardize TenantManagement page layout
- **[PR #1879](https://github.com/RC918/morningai/pull/1879)** (Merged): Standardize SystemMonitoring page layout
- **[PR #1883](https://github.com/RC918/morningai/pull/1883)** (Merged): Standardize UXMetrics page layout
- **[PR #1885](https://github.com/RC918/morningai/pull/1885)** (Merged): Standardize AIPolicies page layout
- **[PR #1894](https://github.com/RC918/morningai/pull/1894)** (Merged): Standardize ApprovalQueue page layout
- **[PR #1900](https://github.com/RC918/morningai/pull/1900)** (Merged): Standardize FailureExperimentDashboard and PlatformSettings pages
- **[PR #1906](https://github.com/RC918/morningai/pull/1906)** (Merged): Move language switcher to navbar

*Shared UI Components:*
- **[PR #1884](https://github.com/RC918/morningai/pull/1884)** (Merged): Implement PageScaffold component
- **[PR #1887](https://github.com/RC918/morningai/pull/1887)** (Merged): Implement SectionTemplate component
- **[PR #1853](https://github.com/RC918/morningai/pull/1853)** (Merged): Add iotask foundation components (Phase 1)
- **[PR #1856](https://github.com/RC918/morningai/pull/1856)** (Merged): Phase 2 - AdminShell three-column layout support

*Security & Memory (Phase 1-2):*
- **[PR #1826](https://github.com/RC918/morningai/pull/1826)** (Merged): Phase 1 Security Foundation - RLS Hard Gate, Semantic Rules v3
- **[PR #1830](https://github.com/RC918/morningai/pull/1830)** (Merged): Phase 1 Follow-up Issues
- **[PR #1831](https://github.com/RC918/morningai/pull/1831)** (Merged): Phase 2 P0 - pgvector Similarity Search and Error-Fix Pairs
- **[PR #1836](https://github.com/RC918/morningai/pull/1836)** (Merged): Phase 2 P1 - Observer Node for Failure Knowledge Base

*Orchestrator Enhancements:*
- **[PR #1852](https://github.com/RC918/morningai/pull/1852)** (Merged): Phase 3 P2 - LangGraph Mode Full Switchover
- **[PR #1854](https://github.com/RC918/morningai/pull/1854)** (Merged): Phase 3 P2 - Human-in-the-Loop High-Risk Approval Workflow
- **[PR #1857](https://github.com/RC918/morningai/pull/1857)** (Merged): Phase 3 P3 - PM Agent + Ops Agent
- **[PR #1862](https://github.com/RC918/morningai/pull/1862)** (Merged): Phase 3 P4 - Background Queue Principles Enhancement
- **[PR #1866](https://github.com/RC918/morningai/pull/1866)** (Merged): Phase 3 Follow-up Issues

*ESLint Spacing Rules:*
- **[PR #1892](https://github.com/RC918/morningai/pull/1892)** (Merged): Add ESLint rule for standardized spacing utilities
  - Path: `handoff/20250928/40_App/owner-console/eslint-rules/no-non-standard-spacing.js` (new file)
- **[PR #1901](https://github.com/RC918/morningai/pull/1901)** (Merged): Cleanup 29 spacing violations
- **[PR #1904](https://github.com/RC918/morningai/pull/1904)** (Merged): Upgrade spacing ESLint rule to error mode (Phase 3)

*Migrations & Infrastructure:*
- **[PR #1871](https://github.com/RC918/morningai/pull/1871)** (Merged): Phase 4 - Unified Migration Management
- **[PR #1895](https://github.com/RC918/morningai/pull/1895)** (Merged): DRY refactoring for run_migrations.sh
- **[PR #1881](https://github.com/RC918/morningai/pull/1881)** (Merged): Update secrets config to use new key names
- **[PR #1882](https://github.com/RC918/morningai/pull/1882)** (Merged): Upgrade vulnerable packages and expand CI scanning coverage

**Recent PRs (Dec 2 - Dec 3, 2025)**:

*Experimentation & Reasoning Mode:*
- **[PR #1804](https://github.com/RC918/morningai/pull/1804)** (Merged): Phase 4 Production Rollout - Increase experiment percentages and add kill switch
  - Path: `handoff/20250928/40_App/orchestrator/experiment_manager.py`, `common/config/settings.py`
  - New env var: `DISABLE_GEMINI3` (boolean) - Emergency kill switch
- **[PR #1803](https://github.com/RC918/morningai/pull/1803)** (Merged): Phase 3 Remaining Items - Gemini 3 fallback, parametrize tests, CI gate
  - Path: `.github/workflows/gemini3-reviewer-gate.yml` (new workflow)
- **[PR #1794](https://github.com/RC918/morningai/pull/1794)** (Merged): Phase 3.1 Hardening - Add REASONING_MODE_ENABLED schema and unit tests
  - Path: `config/env.schema.yaml`, `common/config/settings.py`
  - New env var: `REASONING_MODE_ENABLED` (boolean)
- **[PR #1793](https://github.com/RC918/morningai/pull/1793)** (Merged): Phase 3 - Reasoning mode toggle and Gemini 3 reviewer experiment
  - Path: `handoff/20250928/40_App/orchestrator/llm/adapters/llm_reviewer_adapter.py`
- **[PR #1792](https://github.com/RC918/morningai/pull/1792)** (Merged): Redis Checkpointer - LangGraph state persistence
  - Path: `handoff/20250928/40_App/orchestrator/redis_checkpointer.py` (new file), `graph.py`
- **[PR #1791](https://github.com/RC918/morningai/pull/1791)** (Merged): FAQ Routing - Route FAQ tasks via simple path, bypass LangGraph
  - Path: `handoff/20250928/40_App/orchestrator/graph.py`

*Configuration & Secrets Hardening:*
- **[PR #1800](https://github.com/RC918/morningai/pull/1800)** (Merged): Migrate os.getenv to settings.py for Tier 1 production code
  - Path: `handoff/20250928/40_App/orchestrator/`, `common/config/settings.py`
- **[PR #1798](https://github.com/RC918/morningai/pull/1798)** (Merged): Migrate WORKER_HEARTBEAT_INTERVAL and WORKER_HEARTBEAT_TTL to settings.py
  - Path: `common/config/settings.py`, `config/env.schema.yaml`
  - New env vars: `WORKER_HEARTBEAT_INTERVAL` (60s), `WORKER_HEARTBEAT_TTL` (180s)
- **[PR #1797](https://github.com/RC918/morningai/pull/1797)** (Merged): Migrate RQ_MAX_JOBS to settings.py and add secrets hardening
  - Path: `common/config/settings.py`, `config/env.schema.yaml`
- **[PR #1795](https://github.com/RC918/morningai/pull/1795)** (Merged): Remove deprecated SECRET_KEY and MASTER_KEY
  - Path: `config/env.schema.yaml`
- **[PR #1790](https://github.com/RC918/morningai/pull/1790)** (Merged): Add RQ_MAX_JOBS env var for worker memory management
  - Path: `handoff/20250928/40_App/orchestrator/redis_queue/worker.py`, `config/env.schema.yaml`
  - New env var: `RQ_MAX_JOBS` (integer, default 0)

*UI/UX & Design System:*
- **[PR #1802](https://github.com/RC918/morningai/pull/1802)** (Merged): Storybook Stories for DashboardHeader and Sidebar
  - Path: `handoff/20250928/40_App/owner-console/src/components/DashboardHeader.stories.tsx`, `Sidebar.stories.tsx`
- **[PR #1801](https://github.com/RC918/morningai/pull/1801)** (Merged): Phase 3-4 Completion - iotask Component Styling and Progress Bars
  - Path: `packages/shared-ui/src/components/ui/button.tsx`, `badge.tsx`, `card.tsx`, `input.tsx`, `progress.tsx`
- **[PR #1796](https://github.com/RC918/morningai/pull/1796)** (Merged): iotask Design System Upgrade - Phase 1-4
  - Path: `packages/shared-ui/src/tokens.json`, `handoff/20250928/40_App/owner-console/src/components/`

**Recent PRs (Nov 29 - Dec 1, 2025)**:
- **[PR #1788](https://github.com/RC918/morningai/pull/1788)** (Merged): Failure Memory Integration - Wire failure knowledge base into failure recorder (Phase 5 PR-1)
  - Path: `handoff/20250928/40_App/orchestrator/failure_recorder.py`
- **[PR #1787](https://github.com/RC918/morningai/pull/1787)** (Merged): Sentry Error Prevention - Add defensive checks for graceful degradation
  - Path: `handoff/20250928/40_App/orchestrator/persistence/db_client.py`, `db_writer.py`, `auth_middleware.py`
- **[PR #1785](https://github.com/RC918/morningai/pull/1785)** (Merged): Real Metrics Aggregation - Implement experiment comparison (Tier 1)
  - Path: `handoff/20250928/40_App/orchestrator/persistence/planner_events_store.py`
  - Migration: `migrations/030_create_planner_metrics_rpc.sql`
- **[PR #1781](https://github.com/RC918/morningai/pull/1781)** (Merged): ORCHESTRATOR_DRY_RUN Flag - Skip PR creation in dry run mode
  - Path: `handoff/20250928/40_App/orchestrator/graph.py`
- **[PR #1780](https://github.com/RC918/morningai/pull/1780)** (Merged): OpenAI SDK Upgrade - Fix httpx 0.28 proxies compatibility
  - Path: `handoff/20250928/40_App/orchestrator/requirements.txt`
- **[PR #1778](https://github.com/RC918/morningai/pull/1778)** (Merged): 401 Retry Logic - Proactive token expiry check for owner-console
  - Path: `handoff/20250928/40_App/owner-console/src/lib/auth.ts`, `api-client.ts`

**Gemini 3 SDK Migration (Nov 29-30, 2025)**:
- **[PR #1761](https://github.com/RC918/morningai/pull/1761)** (Merged): Gemini Provider Migration - Migrate to google-genai SDK (Phase 1)
  - Path: `handoff/20250928/40_App/orchestrator/llm/providers/gemini_provider.py`
- **[PR #1762](https://github.com/RC918/morningai/pull/1762)** (Merged): Gemini Fallback Model Update - Change from gemini-pro to gemini-2.0-flash
- **[PR #1763](https://github.com/RC918/morningai/pull/1763)** (Merged): Gemini 3 Phase 2 - thinking_level support and new experiments
- **[PR #1765](https://github.com/RC918/morningai/pull/1765)** (Merged): Enable gemini3_planner_10pct_staging experiment

**AI Governance & Security (Nov 28-29, 2025)**:
- **[PR #1741](https://github.com/RC918/morningai/pull/1741)** (Merged): Three-tier Permission Architecture (Phase 6 PR-5)
  - Path: `handoff/20250928/40_App/api-backend/src/middleware/auth_middleware.py`
  - Migration: `migrations/028_add_platform_admin_support.sql`
- **[PR #1746](https://github.com/RC918/morningai/pull/1746)** (Merged): SECURITY_ENFORCEMENT_MODE Configuration (PR-1)
- **[PR #1748](https://github.com/RC918/morningai/pull/1748)** (Merged): LangGraph Enforcement Integration (PR-2)
- **[PR #1749](https://github.com/RC918/morningai/pull/1749)** (Merged): Simple Mode Policy Observability (PR-3)
- **[PR #1751](https://github.com/RC918/morningai/pull/1751)** (Merged): Blessed Configurations Documentation (PR-4)
  - Path: `config/blessed_configs.yaml`
- **[PR #1753](https://github.com/RC918/morningai/pull/1753)** (Merged): Config Validation Script and CI (PR-5)
  - Path: `scripts/validate_blessed_configs.py`, `.github/workflows/validate-blessed-configs.yml`

**CI/CD Improvements (Nov 28-29, 2025)**:
- **[PR #1756](https://github.com/RC918/morningai/pull/1756)** (Merged): Unified Migration Runner (PR-6)
  - Path: `scripts/run_migrations.sh`
- **[PR #1757](https://github.com/RC918/morningai/pull/1757)** (Merged): Migration Health Check CI (PR-7)
  - Path: `.github/workflows/migration-health-check.yml`
- **[PR #1767](https://github.com/RC918/morningai/pull/1767)** (Merged): Coverage Trend Tracking
  - Path: `.github/workflows/coverage-trend.yml`

**Previous PRs (Nov 25-26, 2025)**:
- **[PR #1548](https://github.com/RC918/morningai/pull/1548)** (Merged): Frontend Dashboard Code Splitting - 20% bundle reduction + Lighthouse CI color-contrast fix
  - Path: `handoff/20250928/40_App/frontend-dashboard/`
- **[PR #1562](https://github.com/RC918/morningai/pull/1562)** (Merged): RQ Job Timeout Configuration - Added `RQ_JOB_TIMEOUT` environment variable
  - Path: `handoff/20250928/40_App/orchestrator/redis_queue/worker.py`, `config/env.schema.yaml`

**Previous PRs (Nov 18-23, 2025)**:
- **[PR #1350](https://github.com/RC918/morningai/pull/1350)** (Merged): E2E Testing Infrastructure - 32 Playwright tests, route handler isolation, API mocking
- **[PR #1398](https://github.com/RC918/morningai/pull/1398)** (Merged): Production Path Discovery - `MORNINGAI_REPO_PATH` env var, 4-layer fallback
- **[PR #1399](https://github.com/RC918/morningai/pull/1399)** (Merged): Backend Test Environment - Python 3.12, Redis service, PyJWT conflict resolution
- **[PR #1480](https://github.com/RC918/morningai/pull/1480)** (Merged): Pydantic Alias System - 23 critical environment variable aliases (Nov 23)
- **[PR #1452](https://github.com/RC918/morningai/pull/1452)** (Merged): Redis Mapping Sanitization - Prevent NoneType DataError (Nov 23)
- **[PR #1455](https://github.com/RC918/morningai/pull/1455)** (Merged): AgentExecutionLogs Accessibility - 6 critical a11y violations resolved (Nov 23)
- **[PR #1437](https://github.com/RC918/morningai/pull/1437)** (Merged): i18n Error Fixes - 10 i18n errors fixed in owner-console (Nov 23)

---

## Executive Summary

This document provides a comprehensive overview of the MorningAI project structure, including directory organization, key files, architecture patterns, and deployment configurations. This report is updated to reflect the latest staging environment setup completed on 2025-10-28.

---

## Table of Contents

1. [Repository Overview](#repository-overview)
2. [Directory Structure](#directory-structure)
3. [Core Systems](#core-systems)
4. [Environment Configuration](#environment-configuration)
5. [Deployment Architecture](#deployment-architecture)
6. [Key Files Reference](#key-files-reference)
7. [Development Workflows](#development-workflows)
8. [Testing Infrastructure](#testing-infrastructure)
9. [Documentation Structure](#documentation-structure)
10. [Maintenance Guidelines](#maintenance-guidelines)

---

## Repository Overview

### Basic Information

- **Repository**: https://github.com/RC918/morningai
- **Primary Language**: Python (Backend), TypeScript (Frontend)
- **Package Manager**: pnpm 9.15.1 (Frontend), pip (Backend)
- **Monorepo**: Yes (using pnpm workspaces + Turbo 2.5.8)
- **License**: Proprietary
- **Team Size**: Small (1-3 developers)

### Repository Statistics

- **Total Lines of Code**: ~100,000+
- **Documentation Files**: 50+
- **GitHub Actions Workflows**: 15+
- **Test Coverage**: 
  - **Owner Console**: 59.89% lines, 45.76% branches (32 E2E tests, 218 unit tests)
  - **Backend**: 74%+ (超過目標，CI 環境已修復)
  - **Target**: 80% by Q2 2026
- **Active Branches**: `main` (production) - trunk-based development model
- **Recent Activity**: 116 commits in past 9 days (2025-11-12 至 2025-11-21)
- **CI Status**: All workflows passing (backend.yml, test-apps.yml unified)

### Technology Stack

**Backend**:
- Python 3.12 (unified across all CI workflows as of [PR #1399](https://github.com/RC918/morningai/pull/1399))
- Flask
- SQLAlchemy
- PostgreSQL (Supabase)
- Redis (Upstash, with health checks in CI)
- RQ (Redis Queue)
- pytest + pytest-cov (74%+ coverage)

**Frontend**:
- React 19.1.0
- TypeScript 5.9
- Vite 6
- Tailwind CSS 4.1.7
- Custom Design System
- Playwright (E2E testing, 32 tests passing)
- Vitest + React Testing Library (unit testing)

**Infrastructure**:
- Render (Backend hosting)
- Vercel (Frontend hosting)
- Fly.io (Agent sandboxes)
- Supabase (Database)
- Upstash (Redis)
- GitHub Actions (CI/CD)

---

## Directory Structure

### Root Level

```
morningai/
├── .github/                    # GitHub configuration
├── .fly-web/                   # Fly.io deployment config
├── agents/                     # AI agent implementations
├── orchestrator/               # Task orchestration system (FastAPI)
├── handoff/                    # Handoff deliverables (⚠️ DO NOT IMPORT - vendor/design only)
├── docs/                       # Documentation
├── config/                     # Configuration files (env.schema.yaml is SSOT)
├── scripts/                    # Utility scripts (env generation, drift check, secret verification, system state verification)
├── packages/                   # Shared packages (shared-ui for cross-app components)
├── tests/                      # Root-level tests
├── tools/                      # Development tools
│   └── agent_eval/            # Agent evaluation harness (NEW: 2025-11-16)
├── phase4_meta_agent_api.py   # Phase 4 API module (imported by backend)
├── phase5_data_intelligence_api.py  # Phase 5 API module (imported by backend)
├── phase6_security_governance_api.py  # Phase 6 API module (imported by backend)
├── phase6_startup.py          # Phase 6 initialization (imported by backend)
├── phase7_startup.py          # Phase 7 initialization (imported by backend)
├── .env.example               # Environment variables template
├── .gitignore                 # Git ignore rules
├── package.json               # Root package.json (pnpm workspace)
├── pnpm-workspace.yaml        # pnpm workspace configuration
├── requirements.txt           # Python dependencies
├── README.md                  # Project overview
└── turbo.json                 # Turbo configuration
```

### Phase API Modules (Root Directory)

**Location**: Root directory (`/`)

**Status**: ✅ **Intentional Cross-Cutting Architecture - Actively Used**

The following 18 production backend modules are located in the root directory as cross-cutting concerns shared across multiple services:

**Core Managers** (Shared Infrastructure):
- **`persistent_state_manager.py`** (495 lines): State management across services
  - Location: `/persistent_state_manager.py`
  - Imported by: `handoff/20250928/40_App/api-backend/src/main.py`, multiple test files
  
- **`security_manager.py`** (364 lines): Security operations and governance
  - Location: `/security_manager.py`
  - Imported by: `handoff/20250928/40_App/api-backend/tests/`, orchestrator services
  
- **`knowledge_graph_manager.py`** (1,018 lines): Knowledge graph operations
  - Location: `/knowledge_graph_manager.py`
  - Imported by: agent services, test files

**Phase API Modules** (Feature Implementations):
- **`phase4_meta_agent_api.py`** (16,874 bytes): Meta-agent coordination API
  - Implements OODA loop (Observe, Orient, Decide, Act)
  - LangGraph workflow engine integration
  - AI governance console
  - Imported by: `main.py`, test files
  
- **`phase5_data_intelligence_api.py`** (21,472 bytes): Data intelligence and BI API
  - QuickSight integration
  - Growth marketing engine
  - Referral programs
  - Business intelligence dashboards
  - Imported by: `main.py`, test files
  
- **`phase6_security_governance_api.py`** (18,234 bytes): Security and governance API
  - Zero Trust security model
  - SecurityReviewer Agent
  - HITL (Human-in-the-Loop) security analysis
  - Security audit system
  - Imported by: `main.py`, test files
  
- **`phase6_startup.py`**: Phase 6 initialization script
  - Imported by: test files, initialization sequences
  
- **`phase7_startup.py`**: Phase 7 initialization script
  - Imported by: `main.py:450`, test files

**Import Evidence** (16+ locations):
- `handoff/20250928/40_App/api-backend/src/main.py` - Main application imports
- `handoff/20250928/40_App/api-backend/tests/test_*.py` - 16+ test files import these modules
- `handoff/20250928/40_App/orchestrator/` - Orchestrator services use managers

**Architecture Rationale**: Root-level placement enables shared access across multiple services (api-backend, orchestrator, agents) without circular dependencies. This is an intentional design pattern for cross-cutting concerns that need to be imported by multiple independent services. Moving these to a subdirectory would require complex PYTHONPATH management or package restructuring.

**Verification**: Run `grep -r "from persistent_state_manager\|from security_manager\|from phase[4-7]" handoff/20250928/40_App/` to see active imports.

### GitHub Configuration (`.github/`)

```
.github/
├── workflows/                 # CI/CD workflows
│   ├── backend.yml           # Backend CI (pytest + coverage, Python 3.12, Redis service)
│   ├── test-apps.yml         # App Tests (API Backend, Orchestrator, Frontend - unified with backend.yml as of [PR #1399](https://github.com/RC918/morningai/pull/1399))
│   ├── frontend.yml          # Frontend CI (build + lint + E2E tests)
│   ├── staging-deploy.yml    # Staging deployment
│   ├── agent-mvp-e2e.yml     # Agent E2E tests
│   ├── ops-agent-sandbox-e2e.yml  # Ops agent E2E tests
│   ├── post-deploy-health-assertions.yml  # Health checks
│   ├── auto-merge-faq.yml    # Auto-merge FAQ PRs
│   ├── pr-guard.yml          # Design/Engineering PR separation
│   ├── dependency-check.yml  # Dependency validation
│   └── ...                   # 15+ workflows total
│
├── ISSUE_TEMPLATE/           # Issue templates
│   ├── rfc.md               # RFC template for API changes
│   ├── phase1-session-state-ooda.md
│   ├── phase2-ops-agent-enhancement.md
│   └── phase3-security-documentation.md
│
├── projects/                 # GitHub Projects
│   ├── phase9-10-mvp.yml    # Phase 9-10 roadmap
│   └── cto-strategic-roadmap-q4-2025-q2-2026.yml
│
└── scripts/                  # Automation scripts
    ├── audit_workflows.sh    # Workflow security audit
    └── check_heartbeat.py    # Redis worker health check
```

### Agents Directory (`agents/`)

```
agents/
├── dev_agent/               # Development agent
│   ├── __init__.py
│   ├── dev_agent.py        # Bug fixing and PR creation
│   └── README.md           # Dev agent documentation
│
├── ops_agent/              # Operations agent
│   ├── __init__.py
│   ├── ops_agent.py        # Incident response and monitoring
│   └── README.md           # Ops agent documentation
│
├── pm_agent.py             # Project management agent
├── growth_strategist.py    # Business strategy agent
└── meta_agent_decision_hub.py  # Agent orchestration (OODA loop)
```

### Orchestrator Directory (`orchestrator/`)

```
orchestrator/
├── api/                    # FastAPI application
│   ├── __init__.py
│   ├── main.py            # Application entry point
│   └── auth.py            # JWT authentication
│
├── task_queue/            # Task queue management
│   ├── __init__.py
│   └── redis_queue.py     # Redis queue implementation
│
├── sandbox/               # Agent sandbox
│   └── ops_agent_sandbox.py
│
├── mcp/                   # Management Control Plane
│   ├── server.py          # MCP server
│   └── mcp_client.py      # MCP client
│
├── graph.py               # Task graph orchestration
├── Dockerfile             # Docker configuration
├── requirements.txt       # Python dependencies
├── setup.py              # Package setup
└── .env.example          # Environment variables template
```

### Handoff Directory (`handoff/20250928/40_App/`)

⚠️ **IMPORTANT**: The `handoff/` directory contains vendor deliverables and design assets from the initial project handoff. **DO NOT import or run code from this directory**. It is excluded from CI paths-ignore and should be treated as reference/archive material only.

The production applications are located within this directory but are the only active code:

```
handoff/20250928/40_App/
├── api-backend/           # Backend API
│   ├── src/              # Source code
│   │   ├── main.py       # Flask application
│   │   ├── database.py   # Database connection
│   │   ├── models/       # SQLAlchemy models
│   │   ├── routers/      # API routers
│   │   └── ...           # Other modules
│   │
│   ├── alembic/          # Database migrations (Alembic 1.13.1)
│   │   ├── versions/     # Migration files
│   │   │   └── 91b9a61fcafa_initial_baseline_migration.py
│   │   ├── env.py        # Alembic environment config
│   │   ├── script.py.mako  # Migration template
│   │   └── README        # Alembic documentation
│   │
│   ├── scripts/          # Utility scripts
│   │   ├── run_alembic_migrations.sh  # Migration helper
│   │   └── test_migration_data_insertion.py  # Integration test
│   │
│   ├── tests/            # Test suite
│   │   ├── test_database_connection.py
│   │   ├── test_phase4_6_comprehensive.py
│   │   └── ...           # 20+ test files
│   │
│   ├── alembic.ini       # Alembic configuration
│   ├── requirements.txt  # Python dependencies (includes Alembic==1.13.1)
│   ├── pytest.ini        # pytest configuration
│   └── .env.example      # Environment variables
│
├── frontend-dashboard/    # Frontend application
│   ├── src/              # Source code
│   │   ├── App.tsx       # Main application
│   │   ├── components/   # React components
│   │   │   ├── apple/    # Apple-inspired components
│   │   │   ├── ui/       # UI components
│   │   │   └── ...       # Other components
│   │   ├── pages/        # Page components
│   │   ├── hooks/        # Custom hooks
│   │   ├── utils/        # Utility functions
│   │   └── ...           # Other modules
│   │
│   ├── public/           # Static assets
│   ├── docs/             # Frontend documentation
│   ├── package.json      # Node.js dependencies
│   ├── vite.config.ts    # Vite configuration
│   ├── tsconfig.json     # TypeScript configuration
│   └── tailwind.config.js  # Tailwind CSS configuration
│
├── owner-console/        # Owner management console
│   ├── src/             # Source code
│   ├── e2e/             # E2E tests (Playwright, 32 tests - added [PR #1350](https://github.com/RC918/morningai/pull/1350))
│   │   ├── auth.setup.ts           # Authentication setup
│   │   ├── agent-execution-logs.spec.ts  # 10 test cases
│   │   ├── system-monitoring.spec.ts     # 8 test cases
│   │   ├── trace-link-integration.spec.ts
│   │   └── utils/fixtures.ts       # API mocking and test utilities
│   ├── public/          # Static assets
│   ├── package.json     # Node.js dependencies
│   └── README.md        # Owner console documentation
│
└── orchestrator/        # Legacy orchestrator (⚠️ STILL USED BY WORKERS)
    └── ...              # Contains LangGraph implementation, used by RQ workers
```

### Tools Directory (`tools/`)

**NEW: 2025-11-16** - Development and evaluation tools

```
tools/
└── agent_eval/          # Agent evaluation harness
    ├── README.md        # Evaluation harness documentation
    ├── __init__.py      # Package initialization
    ├── dataset.jsonl    # Test cases (10 tasks: bug_fix, feature, refactor, test)
    ├── runner.py        # Evaluation runner (executable)
    ├── metrics.py       # Metrics calculator (executable)
    └── results/         # Evaluation results (gitignored)
```

**Purpose**: Provides measurable success rates for AI agent performance:
- **Task Completion Rate**: Percentage of tasks completed
- **Correctness Rate**: Percentage of correct solutions
- **CI Pass Rate**: Percentage of PRs passing CI
- **Time Efficiency**: Actual vs estimated time
- **Overall Success Rate**: Weighted combination

**Status**: ✅ Framework created, ✅ Dashboard integrated (Phase 1.5 #1337)
**Path**: `/home/ubuntu/repos/morningai/tools/agent_eval/`
**Dashboard**: `handoff/20250928/40_App/owner-console/src/pages/AgentEvaluationDashboard.jsx`

**Usage**:
```bash
# Run evaluation
cd tools/agent_eval
python runner.py --dataset dataset.jsonl --output results/latest.json

# View metrics
python metrics.py --results results/latest.json
```

**Integration**: Planned for Milestone 1 (Nov 23 - Dec 6, 2025). See [Strategic Roadmap Reality Comparison](./STRATEGIC_ROADMAP_REALITY_COMPARE_2025_11_16.md).

### Documentation Directory (`docs/`)

```
docs/
├── ops/                  # Operations documentation
│   ├── STAGING_SETUP_GUIDE.md  # Staging setup guide
│   ├── staging-environment-plan.md
│   └── staging-backend-env-template.txt
│
├── architecture/         # Architecture documentation
│   └── decisions/       # Architecture Decision Records (ADRs)
│       ├── ADR-001-frontend-of-record.md
│       ├── ADR-002-orchestrator-roles.md
│       └── ADR-003-database-of-record.md
│
├── UX/                  # UI/UX documentation
│   ├── TYPOGRAPHY_SYSTEM.md
│   ├── COLOR_SYSTEM.md
│   ├── MATERIAL_SYSTEM.md
│   ├── SHADOW_SYSTEM.md
│   ├── SPACING_SYSTEM.md
│   └── ...              # 30+ UX documents
│
├── config/              # Configuration documentation
│   └── env_schema.md    # Environment variables schema
│
├── database/            # Database documentation
│   ├── MIGRATIONS.md    # Alembic migration guide (comprehensive)
│   └── migrations/      # Legacy migration documentation
│
├── faq/                 # FAQ documentation
├── coverage/            # Coverage reports
├── adr/                 # Architecture Decision Records
├── rfcs/                # Request for Comments
├── sandbox/             # Sandbox documentation
├── policy/              # Policy documentation
│
├── STRATEGIC_ROADMAP_REALITY_COMPARE_2025_11_16.md  # Strategic roadmap comparison (2025-11-16)
├── BACKEND_TEST_ENVIRONMENT_FIX.md  # Backend test fix documentation (2025-11-16)
├── ENVIRONMENTS.md      # Environment architecture (Updated: 2025-11-19)
├── PROJECT_STRUCTURE_REPORT.md  # Project structure report (Updated: 2025-11-19)
├── PROJECT_DEEP_ANALYSIS.md  # Deep analysis report (Updated: 2025-11-19)
├── ONBOARDING_GUIDE.md  # Onboarding guide (Updated: 2025-11-19)
├── ARCHITECTURE.md      # System architecture
├── CONTRIBUTING.md      # Contribution guidelines
├── GOVERNANCE_FRAMEWORK.md  # Agent governance
├── MONITORING_SETUP.md  # Monitoring setup
├── TESTING.md           # Testing documentation
├── setup_local.md       # Local setup guide
├── ci_matrix.md         # CI/CD workflows
└── ...                  # 50+ documentation files
```

### Configuration Directory (`config/`)

```
config/
└── env.schema.yaml      # Environment variables schema
```

---

## Core Systems

### 1. Agent System

**Location**: `agents/`

**Components**:
- **Dev_Agent** (`agents/dev_agent/dev_agent.py`)
  - Auto-reproduces bugs via LSP
  - Generates code fixes
  - Creates pull requests
  - Target: >85% fix success rate

- **Ops_Agent** (`agents/ops_agent/ops_agent.py`)
  - Handles incidents via runbooks
  - Performs log analysis
  - Root cause analysis
  - Predictive scaling
  - Target: >70% self-healing

- **PM_Agent** (`agents/pm_agent.py`)
  - Task tracking
  - Priority management
  - Agent coordination

- **Growth_Strategist** (`agents/growth_strategist.py`)
  - Business strategy
  - Growth metrics analysis

- **Meta_Agent** (`agents/meta_agent_decision_hub.py`)
  - Orchestrates all agents
  - Implements OODA loop
  - Routes tasks to appropriate agents

**Key Concepts**:
- **OODA Loop**: Observe → Orient → Decide → Act
- **Session State**: Long-term memory in PostgreSQL
- **Knowledge Graph**: Semantic search with pgvector embeddings (dimension 1536)
- **Learned Patterns**: Coding styles, bug patterns, fix patterns

**Vector Storage (pgvector)**: ✅ **IMPLEMENTED**
- **Location**: 
  - `migrations/010_create_embeddings_tables.sql` - Main embeddings tables
  - `agents/dev_agent/migrations/001_create_knowledge_graph_tables.sql` - Dev agent knowledge graph (136 lines)
  - `agents/faq_agent/migrations/001_create_faq_tables.sql` - FAQ agent embeddings (136 lines)
- **Migration Execution**:
  - **dev_agent**: Python runner at `agents/dev_agent/migrations/run_migration.py` with pre-checks and validation
  - **faq_agent**: Shell script at `agents/faq_agent/deploy.sh:32` executes `psql -f migrations/001_create_faq_tables.sql`
- **Runtime Usage**: `src/routes/vectors.py` - Vector visualization API (t-SNE, PCA, clustering, drift detection)
- **Dimension**: 1536 (OpenAI text-embedding-ada-002)
- **Status**: Production-ready with full API implementation

### 2. Backend API System

**Location**: `handoff/20250928/40_App/api-backend/`

**Architecture**: Phase-based API structure (Phases 4-8)

**Key Files**:
- `src/main.py`: Flask application entry point
- `src/database.py`: Database connection and session management
- `src/models/`: SQLAlchemy models
- `src/routers/`: API route handlers

**API Phases**:
- **Phase 4**: Meta-agent coordination
- **Phase 5**: Data intelligence and BI
- **Phase 6**: Security and governance
- **Phase 7**: Startup initialization
- **Phase 8**: Current production backend (v8.0.0)

**Endpoints**:
- `/healthz`: Health check with phase/version validation
- `/api/agent/faq`: FAQ generation (async task)
- `/api/agent/tasks/{task_id}`: Task status polling
- `/api/billing/plans`: Payment tier management
- `/api/security/reviews/pending`: JWT-protected security reviews
- `/api/phase7/monitoring/dashboard`: Real-time monitoring dashboard (public, no auth)
- `/api/dashboard/data`: Legacy dashboard endpoint (⚠️ deprecated)

**Monitoring API Surface**:
- **Primary Handler**: `src/main.py:574` (`get_monitoring_dashboard`) - Public endpoint registration
- **Core Logic**: `src/routes/dashboard.py:35` (`get_dashboard_data`) - Metrics collection with degradation
- **Test Seam**: `src/routes/dashboard.py:17` (`check_db_health`) - Mockable DB health check
- **Degradation Semantics**: 
  - Redis failure → 200 with fallback metrics (`available: false`, `source: 'fallback'`)
  - DB failure → 200 with degraded status + critical alert
  - Both failures → 503 ServiceUnavailableError
- **Integration Tests**: `tests/test_dashboard_503_integration.py` - Dual failure and degradation scenarios
- **OpenAPI Contract**: `owner-console/src/lib/openapi.yaml` (canonical API schema)
- **Generated Types**: `owner-console/src/lib/generated/owner-console-api.ts` (auto-generated via orval)

### 3. Orchestrator System

⚠️ **DUAL-MODE ORCHESTRATOR ARCHITECTURE** - Critical for understanding code organization

**Current State**: Single worker orchestrator with two execution modes sharing a common core.

#### Architecture Overview

The orchestrator uses a **dual-mode architecture** with a shared core executor:

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

**Architecture**: Producer-consumer pattern with canary routing. API Backend enqueues tasks to Redis. Worker polls Redis and routes to Simple or LangGraph mode based on MD5 hash of task_id.

**Phase 1 參考配置**（實際配置請查看 Render Dashboard）:

| 服務 | USE_LANGGRAPH | USE_LANGGRAPH_PERCENT | USE_LLM_PLANNER |
|------|---------------|----------------------|-----------------|
| Staging Worker | `false` | `5` | `true` |
| Production Worker | `false` | `5` | `true` |

⚠️ **注意**：本文檔描述架構設計和政策。實際環境變數配置可能因運維需求調整。請以 Render Dashboard 的實際配置為準。

**Key Documentation**:
- [ONBOARDING_GUIDE.md - Orchestrator Architecture](./ONBOARDING_GUIDE.md#orchestrator-architecture) - Comprehensive guide for developers
- [ADR-005: Dual Orchestrator Architecture](./adr/005-dual-orchestrator-architecture.md) - Historical context
- [ADR-002: Producer-Consumer Architecture](./adr/002-producer-consumer-architecture.md) - Technical architecture
- [ADR-004: Shared Core Executor Pattern](./adr/004-shared-core-executor-pattern.md) - Design decision for shared execution engine
- [render.yaml](../render.yaml) - Deployment configuration

**Migration Roadmap**:
- **Phase 1** (Current): 5% LangGraph canary validation
- **Phase 2** (Q1 2026): Gradually increase to 100% LangGraph
- **Phase 3** (Q2 2026): Refactor `graph.py` to `core_executor.py` (Option A - Recommended)

#### 3.1 Mode 1: Simple Mode (Feature-Frozen, ~95% Traffic)

**Location**: `handoff/20250928/40_App/orchestrator/`

**Entry Point**: `redis_queue/worker.py:399` → `graph.py:execute()`

**Characteristics**:
- ✅ **Fast**: Direct execution, no state machine overhead
- ✅ **Stable**: Battle-tested, production-proven since 2025-Q3
- ✅ **Stateless**: No retry logic, no CI monitoring
- ❌ **Feature-frozen**: Only bug fixes accepted

**When Used**:
- `USE_LANGGRAPH=false` (default)
- Task's MD5 hash % 100 >= `USE_LANGGRAPH_PERCENT`

**Key Files**:
```
handoff/20250928/40_App/orchestrator/
├── redis_queue/worker.py:399        # Entry point: from graph import execute
├── graph.py:30-155                  # Shared executor (used by both modes!)
└── tests/test_graph.py              # Simple mode tests
```

**Development Policy**: **No new features**. All new orchestrator features must be implemented in LangGraph mode.

#### 3.2 Mode 2: LangGraph Mode (Active Development, ~5% Traffic)

**Location**: `handoff/20250928/40_App/orchestrator/`

**Entry Point**: `redis_queue/worker.py:396` → `langgraph_orchestrator.py:run_orchestrator()`

**Characteristics**:
- ✅ **Stateful**: Full state machine with LangGraph
- ✅ **Intelligent**: LLM-powered planning (when `USE_LLM_PLANNER=true`)
- ✅ **Resilient**: Retry logic, error handling, CI monitoring
- ✅ **Active Development**: New features go here

**When Used**:
- `USE_LANGGRAPH=true` (100% routing), OR
- `USE_LANGGRAPH=false` + Task's MD5 hash % 100 < `USE_LANGGRAPH_PERCENT`

**Workflow**:
```
Worker → langgraph_orchestrator.run_orchestrator()
  → planner_node (LLM or static)
  → executor_node → graph.execute()  # ← Uses shared core!
  → ci_monitor_node
  → fixer_node (if needed)
  → finalizer_node
```

**Key Files**:
```
handoff/20250928/40_App/orchestrator/
├── redis_queue/worker.py:396        # Entry point: from langgraph_orchestrator import run_orchestrator
├── langgraph_orchestrator.py        # LangGraph state machine
│   ├── planner_node (lines 76-104)  # LLM/static planner selection
│   └── executor_node (line 143)     # Calls graph.execute()
├── graph.py:30-155                  # Shared executor (used by both modes!)
└── tests/test_langgraph_ci.py       # LangGraph tests
```

**Development Policy**: **All new orchestrator features go here**. This is the active development path.

#### 3.3 Shared Core: graph.execute()

**Location**: `handoff/20250928/40_App/orchestrator/graph.py:30-155`

**Critical Understanding**: This is **NOT** just the "old Simple orchestrator" - it's the **shared execution engine** for both modes!

**Used By**:
1. **Simple Mode**: Direct call from `worker.py:399`
   ```python
   from graph import execute
   pr_url, state, trace_id = execute(goal, repo, trace_id)
   ```

2. **LangGraph Mode**: Called by `executor_node` in `langgraph_orchestrator.py:143`
   ```python
   def executor_node(state: AgentState) -> AgentState:
       from graph import execute
       pr_url, ci_state, trace_id = execute(goal, repo, trace_id=trace_id)
       # ...
   ```

**What It Does**:
- Cost tracking and budget enforcement (`cost_tracker.py`)
- Rate limiting (10 PRs/hour via `rate_limit.py`)
- FAQ content generation with GPT-4 (`llm/faq_generator.py`)
- Git branch creation and PR opening (`tools/github_api.py`)
- CI check monitoring (`get_pr_checks()`)
- Test mode auto-cleanup (draft PR cleanup)

**⚠️ Critical Development Rule**: Changes to `graph.execute()` affect **BOTH** modes. Always:
1. Test with both Simple and LangGraph modes
2. Add tests in `test_graph.py` AND `test_langgraph_ci.py`
3. State in PR description: "This change affects both orchestrator modes"

#### 3.4 Routing Logic (Canary Deployment)

**Location**: `handoff/20250928/40_App/orchestrator/redis_queue/worker.py:366-400`

**Algorithm**:
```python
use_langgraph = settings.use_langgraph or False
use_langgraph_percent = getattr(settings, 'use_langgraph_percent', 0)

if not use_langgraph and use_langgraph_percent > 0:
    # Canary logic: MD5 hash for deterministic routing
    task_hash = int(hashlib.md5(task_id.encode()).hexdigest(), 16)
    task_percent = task_hash % 100  # 0-99 bucket
    use_langgraph = task_percent < use_langgraph_percent
    
    logger.info(f"Canary deployment: task_percent={task_percent}, "
                f"threshold={use_langgraph_percent}, use_langgraph={use_langgraph}")

if use_langgraph:
    from langgraph_orchestrator import run_orchestrator
    logger.info(f"Using LangGraph orchestrator for task {task_id}")
else:
    from graph import execute
    logger.info(f"Using simple orchestrator for task {task_id}")
```

**Properties**:
- **Deterministic**: Same task_id always routes to same mode
- **Uniform**: MD5 ensures even distribution across 0-99 buckets
- **Controllable**: Adjust `USE_LANGGRAPH_PERCENT` to change traffic split
- **Observable**: Logs routing decision with structured logging

**Monitoring**:
```bash
# Search in Render Dashboard → Worker Logs (see STAGING_SETUP_GUIDE.md for staging service names)
"Canary deployment"           # Routing decision
"Using LangGraph orchestrator" # LangGraph execution
"Using simple orchestrator"    # Simple execution
```

#### 3.5 Deployment Configuration

**Worker Service** (Render):
- Service: `morningai-agent-worker` (Production); for staging, see [STAGING_SETUP_GUIDE.md](./ops/STAGING_SETUP_GUIDE.md)
- Runtime: Python (not Docker)
- Path: `handoff/20250928/40_App/orchestrator`
- Start Command: `python redis_queue/worker.py`

**Environment Variables**:

⚠️ **注意**：以下為參考配置。實際環境變數請查看 Render Dashboard。

```bash
# Phase 1 Reference Configuration
USE_LANGGRAPH=false              # Allow canary (not 100%)
USE_LANGGRAPH_PERCENT=5          # 5% to LangGraph
USE_LLM_PLANNER=true             # LangGraph uses LLM planner

# Kill Switch (Emergency)
USE_LANGGRAPH=false
USE_LANGGRAPH_PERCENT=0          # 0% to LangGraph (100% Simple)

# Full LangGraph (Future)
USE_LANGGRAPH=true               # 100% to LangGraph
```

**Dependencies** (`handoff/20250928/40_App/orchestrator/requirements.txt`):
- LangGraph + LangChain (for LangGraph mode)
- OpenAI SDK (for LLM planner)
- Redis Queue (RQ) for worker
- All dependencies for both modes (shared environment)

### 4. Frontend System

MorningAI has two separate frontend applications with distinct purposes and boundaries:

#### 4.1 Frontend Dashboard (End-User Application)

**Location**: `handoff/20250928/40_App/frontend-dashboard/`

**Purpose**: End-user analytics and monitoring interface

**Architecture**: React 19.1.0 + Vite 6 + TypeScript 5.9

**Key Components**:
- **Design System**: Apple-inspired components
- **Components**: 12 Apple components (Button, Input, Toast, Modal, etc.)
- **Pages**: Dashboard, Strategies, Approvals, History, Costs
- **Hooks**: Custom React hooks for state management
- **Utils**: Utility functions and helpers

**Design System**:
- Typography: 13 sizes, 5 weights, 3 line heights
- Colors: 5 emotional colors, semantic colors, dark mode
- Material: 5 levels of glass effects
- Shadows: 5 levels, colored shadows
- Spacing: 8 levels, 8px grid

**Testing**:
- Unit Tests: Vitest + React Testing Library
- E2E Tests: Playwright (planned)
- Accessibility: WCAG AAA compliance

**Deployment**:
- Production: https://app.gm365.me
- Vercel deployment

#### 4.2 Owner Console (Admin/Governance Application)

**Location**: `handoff/20250928/40_App/owner-console/`

**Purpose**: Owner management, governance, and system administration

**Architecture**: React 19.1.0 + Vite 6 + TypeScript 5.9

**Styling**: Tailwind CSS 4.1.7 with custom design system
- Design tokens: `packages/shared-ui/src/tokens.json` (single source of truth)
- Theme configuration: `src/styles/theme.css` (Tailwind v4 @theme syntax)
- Container width tokens: `--max-width-*` (separate from spacing tokens)
- Regression test: `e2e/max-width-regression.spec.ts` (prevents layout collapse)

**Development Status** (Updated 2025-11-15):
- ✅ **P0 (Week 1)**: Token security (credentials + CSRF + 401 retry) - COMPLETE
- ✅ **P1 (Week 2)**: 2FA system (10 components + 11 tests + enforcement), Test coverage 59.89% lines (as reported) - COMPLETE
- 🟡 **P1 (Week 3)**: Mock cleanup (complete), Agent Logs (60% - missing Trace links/drawer/skeleton), SystemMonitoring (60% - missing skeleton/empty states/charts) - PARTIAL
- 🔴 **P2 (Week 4)**: Billing/Subscription/Alerting - NOT STARTED
- ✅ **P2 (Design System)**: Tailwind v4 theme integration + design token replacement - COMPLETE

**Key Features**:
- ✅ System Monitoring (health checks, metrics, logs, real API integration)
- ✅ Agent Governance (agent management, execution tracking, reputation)
- ✅ Tenant Management (real API integration)
- ✅ 2FA Settings (enrollment, challenge, backup codes, trusted devices)
- ✅ Admin controls with enhanced security
- 🟡 Agent Execution Logs (filtering, pagination, sorting - missing Trace ID links, detail drawer, skeleton loading)
- 🔴 Billing Dashboard (not started)
- 🔴 Subscription Management (not started)
- 🔴 Alerting System (not started)

**Test Coverage**:
- 59.89% lines, 45.76% branches (as reported in CI on 2025-11-16; exceeds 30% target)
- 47 tests passing
- Key test files: `auth-2fa.test.tsx` (11 tests), `2fa-api.test.ts` (7 tests)

**Security Features**:
- ✅ HttpOnly cookies with credentials: 'include'
- ✅ CSRF token protection (automatic injection)
- ✅ 401 automatic refresh retry mechanism
- ✅ 403 CSRF failure automatic retry
- ✅ Open redirect prevention (sanitizeRedirect)
- ✅ Mandatory 2FA for owner role
- ✅ Generated clients use secured apiClient

**Deployment**:
- Production: https://admin.gm365.me
- Vercel deployment

**Related Documentation**:
- Phase Plan: `docs/OWNER_CONSOLE_PHASE_PLAN.md`
- Investigation Report: `docs/WEEK_3_4_INVESTIGATION_REPORT.md`

⚠️ **Cross-Import Restrictions**: ESLint enforces `no-restricted-imports` to prevent accidental imports between frontend-dashboard and owner-console. Use `packages/shared-ui` for shared components.

#### 4.3 Frontend Boundaries and Separation

**IMPORTANT**: The two frontend applications are completely separate and should NOT share code or cross-import from each other.

**Boundary Rules**:
1. **No Cross-Imports**: `frontend-dashboard` MUST NOT import from `owner-console` and vice versa
2. **Shared Code**: Common code should be extracted to `packages/shared-ui` or `packages/*`
3. **API Clients**: Each app has its own API client configuration
4. **Authentication**: Each app has its own auth flow (though both use the same backend)
5. **Deployment**: Each app deploys independently to different domains

**Enforcement**:
- ESLint `no-restricted-imports` rules enforce boundaries
- CI checks prevent cross-imports
- Separate package.json dependencies

**Why Separate Apps?**
- **frontend-dashboard**: End-user facing, analytics focus, public access
- **owner-console**: Admin facing, governance focus, restricted access
- Different user personas, different security requirements, different deployment cadences

---

## Environment Configuration

### Environment Schema (Single Source of Truth)

**Location**: `config/env.schema.yaml`

**Purpose**: Canonical definition of all environment variables across the entire application

**Key Features**:
- 56 total variables (19 required, 37 optional)
- Categorized by purpose (Authentication, Security, Database, Cloud Services, etc.)
- Type validation (secret, url, string, boolean, integer)
- Security level classification (critical, secret, public)
- Comprehensive descriptions and examples

**Generator Script**: `scripts/generate-env-examples.py`
- Generates `.env.example` files from schema
- Ensures consistency across all components
- Run after modifying `config/env.schema.yaml`

**Drift Checker**: `scripts/check-env-drift.py`
- Validates `.env.example` files match schema
- Runs in CI to prevent drift
- Exit code 1 if drift detected

**Workflow**:
1. Modify `config/env.schema.yaml` (single source of truth)
2. Run `python scripts/generate-env-examples.py` to regenerate `.env.example` files
3. Run `python scripts/check-env-drift.py` to verify no drift
4. Commit all changes together
### Production URLs

**Frontend Applications** (see [TERMINOLOGY.md](./TERMINOLOGY.md#域名映射-domain-mapping) for domain mapping details):
- **Tenant Dashboard**: https://app.gm365.me (租戶用戶)
- **Owner Console**: https://admin.gm365.me (平台所有者)
- **Legacy URL**: https://morningai.vercel.app (still active, redirects to app.gm365.me)

**Backend Services**:
- Backend API: https://morningai-backend-v2.onrender.com
- Orchestrator API: https://morningai-orchestrator-api.onrender.com

### Production Environment

**Services**:
- Backend: https://morningai-backend-v2.onrender.com
- Orchestrator: https://morningai-orchestrator-api.onrender.com
- Tenant Dashboard: https://app.gm365.me
- Owner Console: https://admin.gm365.me

**Infrastructure**:
- Database: Supabase PostgreSQL (production)
- Redis: Upstash (TLS enabled)
- Monitoring: Sentry (environment: production)

**Branch**: `main`

**Environment Variables** (`.env.example`):
```bash
ENVIRONMENT=production
DATABASE_URL=postgresql://...
REDIS_URL=rediss://...
JWT_SECRET_KEY=<production-secret>
SECRET_KEY=<production-secret>
MASTER_ENCRYPTION_KEY=<production-secret>
ORCHESTRATOR_JWT_SECRET=<production-secret>
SENTRY_DSN=<production-dsn>
SENTRY_ENVIRONMENT=production
```

### Staging Environment

**Services**:
- Backend: https://morningai-backend-v2-stg.onrender.com
- Orchestrator: https://morningai-orchestrator-api-stg.onrender.com
- Frontend (Dashboard): https://staging.morningai.me
- Frontend (Owner Console): https://staging-owner.morningai.me

**Infrastructure**:
- Database: Supabase PostgreSQL (staging: dckisglnlemvpvmyvnut)
- Redis: Upstash (shared, key prefix: `stg:`)
- Monitoring: Sentry (environment: staging)

**Branch**: `main` (with `ENVIRONMENT=staging` for backend services)

> **Note**: This project uses a trunk-based development model. There is no persistent `develop` branch. Staging is handled via Render backend services (deploying from `main` with staging env vars) and Vercel preview deployments.

**Status**: ✅ Fully Operational (as of 2025-11-04)

**Environment Variables**:
```bash
ENVIRONMENT=staging
DATABASE_URL=postgresql://postgres.[PROJECT_ID]:[PASSWORD]@aws-0-ap-southeast-1.pooler.supabase.com:6543/postgres
REDIS_URL=rediss://default:[PASSWORD]@[HOST].upstash.io:6379
REDIS_KEY_PREFIX=stg:
RQ_QUEUE_NAME=orchestrator-staging
ORCHESTRATOR_JWT_SECRET=<staging-secret-48-chars>
SENTRY_ENVIRONMENT=staging
```

**Documentation**: [docs/ops/STAGING_SETUP_GUIDE.md](ops/STAGING_SETUP_GUIDE.md)

### Local Development

**Services**:
- Backend: http://localhost:8000
- Orchestrator: http://localhost:8001
- Frontend: http://localhost:5173

**Infrastructure**:
- Database: Local PostgreSQL or Staging Supabase
- Redis: Local Redis or Staging Redis

**Environment Variables**:
```bash
ENVIRONMENT=development
DATABASE_URL=postgresql://localhost:5432/morningai
REDIS_URL=redis://localhost:6379/0
TESTING=false
```

---

## Deployment Architecture

### Deployment Platforms

**Render** (Backend + Orchestrator):
- **Production Backend**: `morningai-backend-v2`
- **Production Orchestrator**: `morningai-orchestrator-api`
- **Staging Backend**: `morningai-backend-v2-stg`
- **Staging Orchestrator**: `morningai-orchestrator-api-stg`
- **Cost**: $7/month per service (Starter plan)

**Vercel** (Frontend):
- **Production**: `app.gm365.me` (dashboard), `admin.gm365.me` (owner console)
- **Staging**: `staging.morningai.me` (dashboard), `staging-owner.morningai.me` (owner console)
- **Preview**: Auto-deploy for `feature/*`, `fix/*`, `devin/*` branches
- **Branch Policy**: `main` → production, `feature/*|fix/*|devin/*` → preview
- **Ignore Script**: `scripts/vercel-ignore.sh` (skips docs-only changes)
- **Documentation**: [docs/deployment/VERCEL_DEPLOYMENT_STRATEGY.md](deployment/VERCEL_DEPLOYMENT_STRATEGY.md)
- **Cost**: $0/month (Free tier)

**Fly.io** (Agent Sandboxes):
- **Dev Agent Sandbox**: `morningai-sandbox-dev-agent`
- **Ops Agent Sandbox**: `morningai-sandbox-ops-agent`
- **Cost**: ~$4/month (auto-scale to $0 when idle)

**Supabase** (Database):
- **Production**: Production project
- **Staging**: `dckisglnlemvpvmyvnut`
- **Cost**: $0/month (Free tier) or $25/month (Pro)

**Upstash** (Redis):
- **Shared**: Same Redis for all environments
- **Isolation**: Key prefixes (`stg:` for staging)
- **Cost**: $0/month (Free tier) or $10/month (Pay-as-you-go)

### Deployment Workflow (Trunk-Based)

```mermaid
graph LR
    A[Feature Branch] -->|PR| B[main]
    B -->|Auto-deploy| C[Production]
    A -->|Preview Deploy| D[Staging Test]
    D -->|Manual Test| E{Tests Pass?}
    E -->|Yes| B
    E -->|No| A
```

**CI/CD Workflows** (`.github/workflows/backend.yml`, etc.):
- **Trigger**: Push/PR to `main` branch
- **Tests**: Backend (pytest + coverage 74%+), Frontend (build), E2E tests
- **Deploy**: Auto-deploy to production services on merge to `main`
- **Validation**: Post-deploy health checks (90% SLA)

### Docker Configuration

**Orchestrator Dockerfile** (`orchestrator/Dockerfile`):
```dockerfile
FROM python:3.12-slim
WORKDIR /app
RUN apt-get update && apt-get install -y gcc && rm -rf /var/lib/apt/lists/*
COPY orchestrator/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt
COPY orchestrator/ ./orchestrator/
RUN pip install --no-cache-dir -e ./orchestrator
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health', timeout=5)"
CMD ["uvicorn", "orchestrator.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**Fly.io Configuration** (`.fly-web/fly.toml`):
```toml
app = "morningai-web"
primary_region = "nrt"

[http_service]
  internal_port = 3000
  force_https = true
  auto_stop_machines = true
  auto_start_machines = true
  min_machines_running = 0

[[services.ports]]
  port = 80
  handlers = ["http"]
  force_https = true

[[services.ports]]
  port = 443
  handlers = ["tls", "http"]
```

---

## Key Files Reference

### Configuration Files

| File | Purpose | Location |
|------|---------|----------|
| `.env.example` | Environment variables template | Root |
| `config/env.schema.yaml` | Environment variables schema | `config/` |
| `package.json` | Root Node.js configuration | Root |
| `pnpm-workspace.yaml` | pnpm workspace configuration | Root |
| `turbo.json` | Turbo build configuration | Root |
| `requirements.txt` | Root Python dependencies | Root |

### Backend Files

| File | Purpose | Location |
|------|---------|----------|
| `src/main.py` | Flask application | `handoff/.../api-backend/src/` |
| `src/database.py` | Database connection | `handoff/.../api-backend/src/` |
| `requirements.txt` | Python dependencies | `handoff/.../api-backend/` |
| `pytest.ini` | pytest configuration | `handoff/.../api-backend/` |

### Orchestrator Files

| File | Purpose | Location |
|------|---------|----------|
| `api/main.py` | FastAPI application | `orchestrator/api/` |
| `api/auth.py` | JWT authentication | `orchestrator/api/` |
| `task_queue/redis_queue.py` | Redis queue | `orchestrator/task_queue/` |
| `Dockerfile` | Docker configuration | `orchestrator/` |
| `requirements.txt` | Python dependencies | `orchestrator/` |

### Frontend Files

| File | Purpose | Location |
|------|---------|----------|
| `src/App.tsx` | Main application | `handoff/.../frontend-dashboard/src/` |
| `package.json` | Node.js dependencies | `handoff/.../frontend-dashboard/` |
| `vite.config.ts` | Vite configuration | `handoff/.../frontend-dashboard/` |
| `tsconfig.json` | TypeScript configuration | `handoff/.../frontend-dashboard/` |
| `tailwind.config.js` | Tailwind CSS configuration | `handoff/.../frontend-dashboard/` |

### Documentation Files

| File | Purpose | Location |
|------|---------|----------|
| `README.md` | Project overview | Root |
| `ENVIRONMENTS.md` | Environment architecture | `docs/` |
| `ONBOARDING_GUIDE.md` | Onboarding guide | `docs/` |
| `STAGING_SETUP_GUIDE.md` | Staging setup | `docs/ops/` |
| `ARCHITECTURE.md` | System architecture | `docs/` |
| `CONTRIBUTING.md` | Contribution guidelines | `docs/` |

---

## Development Workflows

### Git Workflow (Trunk-Based)

**Branches**:
- `main`: Production branch (single long-lived branch)
- `feature/*`: Feature branches
- `fix/*`: Bug fix branches
- `hotfix/*`: Hotfix branches
- `devin/*`: AI-assisted development branches

> **Note**: This project uses a trunk-based development model. There is no persistent `develop` branch.

**Workflow**:
1. Create feature branch from `main`
2. Develop and commit changes
3. Create PR to `main`
4. Vercel creates preview deployment for testing
5. Test on staging backend + preview frontend
6. Get PR approval
7. Merge to `main`
8. Auto-deploy to production

### PR Guidelines

**Design PRs**:
- UI/copy/styles only
- Cannot include API/logic changes
- Enforced by `pr-guard.yml`

**Engineering PRs**:
- API/logic only
- Cannot include UI/copy/styles changes
- Enforced by `pr-guard.yml`

**RFC Required**:
- OpenAPI/schema changes
- Database schema changes
- Breaking changes
- Template: `.github/ISSUE_TEMPLATE/rfc.md`

### Code Review Process

1. **Self-Review**: Review your own code before requesting review
2. **Automated Checks**: Ensure CI passes
3. **Peer Review**: Request review from team members
4. **Address Feedback**: Make requested changes
5. **Approval**: Get approval from reviewers
6. **Merge**: Merge to target branch

---

## Testing Infrastructure

### Test Coverage

**Current**: 41%  
**Target**: 80% by Q2 2026

**Coverage Database**: `.coverage` (SQLite)

### Test Suites

**Backend Tests** (`handoff/.../api-backend/tests/`):
- `test_database_connection.py`: Database connection tests
- `test_phase4_6_comprehensive.py`: Phase 4-6 API tests
- `test_unit_comprehensive.py`: Unit tests
- `test_zero_coverage_modules.py`: Targets uncovered code
- `test_ops_agent_sandbox.py`: E2E tests

**Frontend Tests** (`handoff/.../frontend-dashboard/src/`):
- Unit tests: Vitest + React Testing Library
- Component tests: Storybook stories (26 stories in `handoff/20250928/40_App/frontend-dashboard/.storybook/`)
- Accessibility tests: axe-core integration

**Storybook Architecture**:
- **Location**: 
  - Application Layer: `handoff/20250928/40_App/frontend-dashboard/.storybook/`
  - Owner Console: `handoff/20250928/40_App/owner-console/.storybook/` (added November 2025)
  - Shared UI: `packages/shared-ui/.storybook/` (added November 2025)
- **Configuration**: 
  - Frontend Dashboard: `handoff/20250928/40_App/frontend-dashboard/.storybook/main.ts:1-53`
  - Owner Console: `handoff/20250928/40_App/owner-console/.storybook/main.ts` (Storybook 8.6.14)
    - **P1 Improvements** (November 2025): MSW addon, dark mode, test runner
    - MSW Config: `.storybook/msw-config.ts` - Wildcard host matching (`*/api/...`)
    - Preview Config: `.storybook/preview.tsx` - MSW initialization, dark mode sync
    - Test Runner: `.storybook/test-runner.ts` - a11y checks with axe-playwright
  - Shared UI: `packages/shared-ui/.storybook/main.ts` (Storybook 8.6.14)
- **Stories**: 52+ total (26 in frontend-dashboard, 13 in owner-console, 13 in shared-ui, 5 in tools/frontend-lab)
  - Owner Console Stories:
    - `src/pages/SystemMonitoring.stories.jsx` - 7 variants (Loading, Healthy, Degraded, Unhealthy, Empty states, Error)
    - `src/components/AgentExecutionLogs.stories.tsx` - 6 variants (Loading, Successful, Mixed statuses, Empty, Error, Pagination)
- **Components Documented**: Apple-style components, design system showcase, color/spacing/typography systems, shared UI components (Card, Button, Badge, Alert, Avatar, Progress, Tabs, Dialog), Owner Console pages (SystemMonitoring, AgentExecutionLogs)
- **Running Storybook**:
  - Owner Console: `cd handoff/20250928/40_App/owner-console && pnpm storybook` (port 6007)
  - Shared UI: `pnpm --filter @morningai/shared-ui storybook` (port 6006)
  - Frontend Dashboard: `pnpm --filter frontend-dashboard storybook` (port 6006)
- **Testing Storybook**:
  - Owner Console: `cd handoff/20250928/40_App/owner-console && pnpm test-storybook` (a11y checks)
  - Shared UI: `pnpm --filter @morningai/shared-ui test-storybook:ci`
- **Design Tokens**: Single source of truth at `packages/shared-ui/src/tokens.json`

### CI/CD Testing

**Staging CI** (`.github/workflows/staging-deploy.yml`):
- Backend: pytest + coverage (74%+ required)
- Frontend: build + lint
- Smoke tests

**Production CI**:
- Full test suite
- E2E tests
- Post-deploy health checks (90% SLA)

### Test Commands

**Backend**:
```bash
cd handoff/20250928/40_App/api-backend
pytest -v
pytest --cov=src --cov-report=html
```

**Frontend**:
```bash
cd handoff/20250928/40_App/frontend-dashboard
pnpm test
pnpm test:coverage
```

---

## Documentation Structure

### Documentation Categories

**Getting Started**:
- `README.md`: Project overview
- `docs/ONBOARDING_GUIDE.md`: Onboarding guide
- `docs/setup_local.md`: Local setup guide

**Architecture**:
- `docs/ARCHITECTURE.md`: System architecture
- `docs/ENVIRONMENTS.md`: Environment architecture
- `docs/agent-sandbox-architecture.md`: Sandbox architecture
- `docs/architecture/decisions/`: ADRs

**Development**:
- `docs/CONTRIBUTING.md`: Contribution guidelines
- `docs/ci_matrix.md`: CI/CD workflows
- `docs/config/env_schema.md`: Environment variables

**Operations**:
- `docs/ops/STAGING_SETUP_GUIDE.md`: Staging setup
- `docs/ops/staging-environment-plan.md`: Staging plan
- `docs/MONITORING_SETUP.md`: Monitoring setup

**UI/UX**:
- `docs/UI_UX_QUICKSTART.md`: Quick start
- `docs/UI_UX_CHEATSHEET.md`: Cheat sheet
- `docs/UI_UX_RESOURCES.md`: Resources
- `docs/UX/`: Design system documentation

**Security**:
- `docs/REDIS_SECURITY.md`: Redis security
- `docs/RLS_IMPLEMENTATION_GUIDE.md`: Row-level security
- `docs/SECRET_SCANNING_GUIDE.md`: Secret management

**Testing**:
- `docs/TESTING.md`: Testing documentation
- `docs/PHASE3_TESTING_GUIDE.md`: Phase 3 testing

### Documentation Standards

**Format**: Markdown (`.md`)

**Structure**:
- Clear headings (H1, H2, H3)
- Table of contents for long documents
- Code examples with syntax highlighting
- Links to related documentation
- Last updated date

**Maintenance**:
- Update documentation with code changes
- Review documentation quarterly
- Archive outdated documentation

---

## Maintenance Guidelines

### Regular Maintenance Tasks

**Weekly**:
- Check staging service health
- Review CI/CD failures
- Monitor test coverage

**Monthly**:
- Clean up staging database
- Review and update documentation
- Check dependency updates
- Review Sentry errors

**Quarterly**:
- Rotate production secrets
- Review and update ADRs
- Audit GitHub Actions workflows
- Review cost optimization

### Code Quality Standards

**Python**:
- Follow PEP 8 style guide
- Use type hints
- Write docstrings
- Maintain test coverage >40%

**TypeScript**:
- Follow ESLint rules
- Use strict TypeScript
- Write JSDoc comments
- Maintain test coverage >40%

**Git Commits**:
- Use conventional commits
- Write clear commit messages
- Reference issues/PRs

### Security Best Practices

**Secrets**:
- Never commit secrets to repository
- Use different secrets for each environment
- Rotate secrets quarterly (production)
- Use strong secrets (32+ characters)

**Dependencies**:
- Keep dependencies up to date
- Review security advisories
- Use dependency scanning

**Access Control**:
- Use principle of least privilege
- Review access permissions regularly
- Enable 2FA for all accounts

---

## Appendix

### Quick Reference

**Service URLs**:
- Production Backend: https://morningai-backend-v2.onrender.com
- Production Orchestrator: https://morningai-orchestrator-api.onrender.com
- Production Frontend: https://morningai.vercel.app
- Staging Backend: https://morningai-backend-v2-stg.onrender.com
- Staging Orchestrator: https://morningai-orchestrator-api-stg.onrender.com

**Dashboards**:
- Render: https://dashboard.render.com/
- Vercel: https://vercel.com/dashboard
- Supabase: https://supabase.com/dashboard
- Sentry: https://sentry.io/organizations/morningai/issues/
- GitHub: https://github.com/RC918/morningai

**Documentation**:
- Environments: [docs/ENVIRONMENTS.md](ENVIRONMENTS.md)
- Onboarding: [docs/ONBOARDING_GUIDE.md](ONBOARDING_GUIDE.md)
- Staging Setup: [docs/ops/STAGING_SETUP_GUIDE.md](ops/STAGING_SETUP_GUIDE.md)
- Architecture: [docs/ARCHITECTURE.md](ARCHITECTURE.md)
- Contributing: [docs/CONTRIBUTING.md](CONTRIBUTING.md)

### Glossary

**ADR**: Architecture Decision Record  
**CI/CD**: Continuous Integration/Continuous Deployment  
**E2E**: End-to-End  
**JWT**: JSON Web Token  
**LSP**: Language Server Protocol  
**MCP**: Management Control Plane  
**OODA**: Observe, Orient, Decide, Act  
**PR**: Pull Request  
**RFC**: Request for Comments  
**RLS**: Row-Level Security  
**SLA**: Service Level Agreement  
**TLS**: Transport Layer Security

---

**Document Version**: 1.4.0  
**Last Updated**: 2025-11-16  
**Maintained By**: CTO / DevOps Team  
**Status**: ✅ Complete and Current

**Changelog**:
- 2025-11-16 (v1.4.0): Added agent evaluation harness, strategic roadmap comparison, backend test fix documentation
- 2025-11-15 (v1.3.0): Updated Owner Console status
- 2025-10-28 (v1.0.0): Initial version
