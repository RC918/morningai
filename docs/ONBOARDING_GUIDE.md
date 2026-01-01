# MorningAI Onboarding Guide

**Welcome to MorningAI!** 🎉

> 📚 **相關文件**: 
> - [術語對照表](./TERMINOLOGY.md) - 標準化的應用名稱和用戶類型定義
> - [專案結構報告](./PROJECT_STRUCTURE_REPORT.md) - 詳細的目錄組織和架構模式
> - [README](../README.md) - 專案概覽和快速導航
> - [環境變數 Schema](../config/env.schema.yaml) - 環境變數配置的單一真源

This guide will help you get started with the MorningAI project, understand the architecture, set up your development environment, and start contributing.

---

## 如何理解本專案現況 (Hierarchy of Truth)

> **重要**: 本專案迭代速度極快，文件可能會有延遲。若發生資訊衝突，請遵循以下「信任層級」：

| Level | 來源 | 說明 |
|-------|------|------|
| **Level 1** (絕對真理) | CI Workflows (`.github/workflows/*.yml`) & Tests | 如果 CI 沒跑這個功能，它就不存在 |
| **Level 2** (事實) | `CHANGELOG.md` 與最近 2 週的 Merged PRs | 反映實際已完成的變更 |
| **Level 3** (參考) | 程式碼註解 (Comments) 與 Docstrings | 可能過期但通常準確 |
| **Level 4** (僅供參考) | README 與外部文件 | 可能有延遲，以上層為準 |

**關鍵 CI Workflows**：
- [`simple-mode-guard.yml`](.github/workflows/simple-mode-guard.yml) - 防止重新引入已廢棄的 Simple Mode 代碼
- [`backend.yml`](.github/workflows/backend.yml) - Backend lint、測試、覆蓋率
- [`frontend.yml`](.github/workflows/frontend.yml) - Frontend build、typecheck、E2E

**實際案例**：
- [PR #2767](https://github.com/RC918/morningai/pull/2767) - Simple Mode 移除。即使當時 README 仍描述「雙模式架構」，CI Guard (`simple-mode-guard.yml`) 已阻擋 Simple Mode 代碼，證明 CI 是真相來源。
- [Issue #2651](https://github.com/RC918/morningai/issues/2651) - LangGraph 100% Rollout 決策記錄

**範例**：如果 README 說「支援雙模式架構」，但 [`simple-mode-guard.yml`](.github/workflows/simple-mode-guard.yml) CI workflow 會阻擋 Simple Mode 代碼，則以 CI 為準 — Simple Mode 已被移除。

**調查順序建議**：
1. 先查 `CHANGELOG.md` 和最近的 merged PRs
2. 檢查相關的 CI workflows（如 [`simple-mode-guard.yml`](.github/workflows/simple-mode-guard.yml)）
3. 再看 README 和其他文件做補充理解

---

## Table of Contents

1. [Project Overview](#project-overview)
2. [Environment Architecture](#environment-architecture)
3. [Orchestrator Architecture](#orchestrator-architecture)
4. [Getting Started](#getting-started)
5. [Development Workflow](#development-workflow)
6. [Key Technologies](#key-technologies)
7. [Project Structure](#project-structure)
8. [Important Documentation](#important-documentation)
9. [Common Tasks](#common-tasks)
10. [Troubleshooting](#troubleshooting)
11. [Getting Help](#getting-help)

---

## Project Overview

### What is MorningAI?

MorningAI is an intelligent agent orchestration platform that automates software development, operations, and project management tasks. The system employs multiple specialized AI agents that work collaboratively to handle bug fixes, create pull requests, manage infrastructure, respond to incidents, and make strategic decisions.

### Vision

Building the world's most advanced autonomous AI agent orchestration platform that seamlessly integrates development, operations, and business intelligence with human-in-the-loop governance.

### Current Status (Updated: 2025-12-20)

- **Phase**: Phase 8 (v8.0.0) - MVP Foundation Complete + LangGraph 100% Rollout
- **Test Coverage**: 
  - Owner Console: **59.89% lines, 45.76% branches** (32 E2E tests passing, 218 unit tests)
  - Orchestrator: **70%+** (超過 50% 門檻)
  - Backend: **74%+** (CI environment fixed, all tests passing)
  - Target: 80% by Q2 2026
- **Uptime**: 90% (Target: 99.9% by Q2 2026)
- **Transformation**: Q4 2025 - Q2 2026 (MVP to World-Class)
- **Latest Roadmap**: [Strategic Roadmap Reality Comparison](./STRATEGIC_ROADMAP_REALITY_COMPARE_2025_11_16.md) (Nov 16, 2025)
- **LangGraph Status**: 100% Rollout Complete - Simple Mode removed (Dec 2025)

**Recent Improvements (Dec 13 - Dec 20, 2025)** (198 PRs merged):

*EPIC B: PR_UPDATED Event Support & Phase BB Robustness (21 PRs):*
- **[PR #2789](https://github.com/RC918/morningai/pull/2789)**: feat(phase-bb): P2 technical debt - extract helper, narrow exceptions, add tests
  - Path: `handoff/20250928/40_App/orchestrator/`
  - Impact: Technical debt reduction with helper extraction and narrowed exception handling
- **[PR #2788](https://github.com/RC918/morningai/pull/2788)**: feat(epic-b): Phase 2 - Line drift protection with head_sha tracking
  - Path: `handoff/20250928/40_App/orchestrator/`
  - Impact: Prevents stale comments by tracking head_sha for line drift detection
- **[PR #2787](https://github.com/RC918/morningai/pull/2787)**: refactor(epic-b): P2/P3 follow-up improvements for Phase 1 Quick Wins
  - Path: `handoff/20250928/40_App/orchestrator/`
  - Impact: Follow-up improvements for LLM reliability and file-level comments
- **[PR #2786](https://github.com/RC918/morningai/pull/2786)**: feat(phase-bb): add REDIS_KEY_PREFIX to pr_updated keys for environment isolation
  - Path: `handoff/20250928/40_App/orchestrator/`
  - Impact: New env var `REDIS_KEY_PREFIX` for multi-environment Redis key isolation
- **[PR #2785](https://github.com/RC918/morningai/pull/2785)**: feat(epic-b): Phase 1 Quick Wins - LLM reliability and file-level comments delivery
  - Path: `handoff/20250928/40_App/orchestrator/`
  - Impact: Improved LLM reliability and file-level comment delivery
- **[PR #2784](https://github.com/RC918/morningai/pull/2784)**: fix(phase-bb): use consistent queue_name pattern with None handling in worker.py
  - Path: `handoff/20250928/40_App/orchestrator/redis_queue/worker.py`
  - Impact: Consistent queue naming pattern with proper None handling
- **[PR #2782](https://github.com/RC918/morningai/pull/2782)**: feat(phase-bb): add P2 robustness improvements for debounce mechanism
  - Path: `handoff/20250928/40_App/orchestrator/`
  - Impact: Enhanced debounce mechanism robustness
- **[PR #2781](https://github.com/RC918/morningai/pull/2781)**: refactor(phase-bb): implement non-blocking debounce with self-rescheduling
  - Path: `handoff/20250928/40_App/orchestrator/`
  - Impact: Non-blocking debounce implementation with self-rescheduling
- **[PR #2776](https://github.com/RC918/morningai/pull/2776)**: feat(phase-bb): implement PR_UPDATED delayed job integration
  - Path: `handoff/20250928/40_App/orchestrator/`
  - Impact: Delayed job integration for PR_UPDATED events
- **[PR #2769](https://github.com/RC918/morningai/pull/2769)**: feat(phase-bb): add PR_UPDATED event support with debounce/throttle
  - Path: `handoff/20250928/40_App/orchestrator/`
  - Impact: Core PR_UPDATED event support with debounce and throttle mechanisms
- **[PR #2768](https://github.com/RC918/morningai/pull/2768)**: feat(phase-bb): add 422 fault injection for fallback verification
  - Path: `handoff/20250928/40_App/orchestrator/`
  - Impact: Fault injection for testing fallback behavior
- **[PR #2770](https://github.com/RC918/morningai/pull/2770)**: feat: restrict 422 fault injection to internal repos only (P2 follow-up)
  - Path: `handoff/20250928/40_App/orchestrator/`
  - Impact: Security restriction for fault injection to internal repos only
- **[PR #2763](https://github.com/RC918/morningai/pull/2763)**: feat(phase-bb): enable internal repo dogfooding in Staging
  - Path: `handoff/20250928/40_App/orchestrator/`
  - Impact: Internal repo dogfooding enabled in Staging environment
- **[PR #2741](https://github.com/RC918/morningai/pull/2741)**: feat(phase-bb): add C-lite telemetry for EPIC B KPIs
  - Path: `handoff/20250928/40_App/orchestrator/`
  - Impact: C-lite telemetry for EPIC B key performance indicators
- **[PR #2735](https://github.com/RC918/morningai/pull/2735)**: fix(phase-bb): fix header case-sensitivity, empty string trap, and add automation bot allowlist
  - Path: `handoff/20250928/40_App/orchestrator/`
  - Impact: Header case-sensitivity fix and automation bot allowlist
- **[PR #2732](https://github.com/RC918/morningai/pull/2732)**: fix(phase-bb): add context observability fields to diagnose pr_number=0
  - Path: `handoff/20250928/40_App/orchestrator/`
  - Impact: Enhanced observability for debugging pr_number=0 issues
- **[PR #2730](https://github.com/RC918/morningai/pull/2730)**: fix(phase-bb): use single quotes for pr_url to preserve JSON format
  - Path: `handoff/20250928/40_App/orchestrator/`
  - Impact: JSON format preservation for pr_url
- **[PR #2726](https://github.com/RC918/morningai/pull/2726)**: fix(phase-bb): put key fields in log message for observability
  - Path: `handoff/20250928/40_App/orchestrator/`
  - Impact: Improved log observability with key fields
- **[PR #2721](https://github.com/RC918/morningai/pull/2721)**: fix(phase-bb): pass PR context from webhook to LangGraph orchestrator
  - Path: `handoff/20250928/40_App/orchestrator/`
  - Impact: PR context passing from webhook to orchestrator
- **[PR #2716](https://github.com/RC918/morningai/pull/2716)**: feat(telemetry): add Phase B-B staging verification fields
  - Path: `handoff/20250928/40_App/orchestrator/`
  - Impact: Staging verification telemetry fields

*LangGraph 100% Rollout & Simple Mode Removal (14 PRs):*
- **[PR #2767](https://github.com/RC918/morningai/pull/2767)**: chore: remove Simple Mode code after LangGraph 100% rollout (#2651)
  - Path: `handoff/20250928/40_App/orchestrator/`
  - Impact: **MAJOR**: Complete removal of Simple Mode code - LangGraph is now the only orchestration mode
- **[PR #2771](https://github.com/RC918/morningai/pull/2771)**: feat(checkpointer): add PostgreSQL checkpointer support for LangGraph
  - Path: `handoff/20250928/40_App/orchestrator/`
  - Impact: PostgreSQL checkpointer support for LangGraph state persistence
- **[PR #2772](https://github.com/RC918/morningai/pull/2772)**: test(checkpointer): add unit tests for get_checkpointer priority and fallback
  - Path: `handoff/20250928/40_App/orchestrator/`
  - Impact: Checkpointer priority and fallback test coverage
- **[PR #2775](https://github.com/RC918/morningai/pull/2775)**: test(checkpointer): add P3 success path and fallback tests
  - Path: `handoff/20250928/40_App/orchestrator/`
  - Impact: P3 success path and fallback test coverage
- **[PR #2766](https://github.com/RC918/morningai/pull/2766)**: chore: remove deprecated rollout API endpoints
  - Path: `handoff/20250928/40_App/api-backend/`
  - Impact: Deprecated rollout API endpoints removed
- **[PR #2765](https://github.com/RC918/morningai/pull/2765)**: fix(rollout): remove obsolete use_langgraph_percent reference
  - Path: `handoff/20250928/40_App/orchestrator/`
  - Impact: Cleanup of obsolete rollout percentage references
- **[PR #2757](https://github.com/RC918/morningai/pull/2757)**: fix(worker): remove obsolete use_langgraph settings reference
  - Path: `handoff/20250928/40_App/orchestrator/redis_queue/worker.py`
  - Impact: Cleanup of obsolete settings references
- **[PR #2754](https://github.com/RC918/morningai/pull/2754)**: feat(orchestrator): add FAQ latency monitoring (#2737)
  - Path: `handoff/20250928/40_App/orchestrator/`
  - Impact: FAQ latency monitoring for performance tracking
- **[PR #2742](https://github.com/RC918/morningai/pull/2742)**: test(orchestrator): add E2E and circuit breaker tests for LangGraph-only mode (#2736)
  - Path: `handoff/20250928/40_App/orchestrator/`
  - Impact: E2E and circuit breaker tests for LangGraph-only mode
- **[PR #2740](https://github.com/RC918/morningai/pull/2740)**: test(orchestrator): remove obsolete Simple Mode tests (#2738)
  - Path: `handoff/20250928/40_App/orchestrator/`
  - Impact: Cleanup of obsolete Simple Mode tests
- **[PR #2720](https://github.com/RC918/morningai/pull/2720)**: feat(orchestrator): remove Simple Mode - LangGraph only (#2651)
  - Path: `handoff/20250928/40_App/orchestrator/`
  - Impact: **MAJOR**: Simple Mode removal - LangGraph becomes the only mode
- **[PR #2644](https://github.com/RC918/morningai/pull/2644)**: feat(tests): add RolloutTracker enabled=True + Redis integration tests (#2641)
  - Path: `handoff/20250928/40_App/orchestrator/`
  - Impact: RolloutTracker integration tests
- **[PR #2611](https://github.com/RC918/morningai/pull/2611)**: refactor(rollout): adopt helper functions in endpoints (#2605)
  - Path: `handoff/20250928/40_App/api-backend/`
  - Impact: Rollout endpoint refactoring with helper functions
- **[PR #2597](https://github.com/RC918/morningai/pull/2597)**: feat(phase4a): implement LangGraph rollout pre-rollout telemetry and controls (#2285, #2282, #2281, #2283)
  - Path: `handoff/20250928/40_App/orchestrator/`
  - Impact: Pre-rollout telemetry and controls for LangGraph

*EPIC B: Inline Code Review (Phase B-1 to B-3) (8 PRs):*
- **[PR #2714](https://github.com/RC918/morningai/pull/2714)**: feat(publisher): add inline comment validation and line number semantics (Phase B-3.1)
  - Path: `handoff/20250928/40_App/orchestrator/nodes/publisher_node.py`
  - Impact: Inline comment validation with line number semantics
- **[PR #2710](https://github.com/RC918/morningai/pull/2710)**: feat(diff): add ignore list and secrets redaction (Phase B-2.5)
  - Path: `handoff/20250928/40_App/orchestrator/`
  - Impact: Diff ignore list and secrets redaction for security
- **[PR #2707](https://github.com/RC918/morningai/pull/2707)**: test(publisher): add comprehensive unit tests for post_pr_review and publisher_node (Issue #2706)
  - Path: `handoff/20250928/40_App/orchestrator/`
  - Impact: Comprehensive publisher node test coverage
- **[PR #2701](https://github.com/RC918/morningai/pull/2701)**: feat(publisher): add GitHub inline comment posting (EPIC B Phase B-3)
  - Path: `handoff/20250928/40_App/orchestrator/nodes/publisher_node.py`
  - Impact: GitHub inline comment posting capability
- **[PR #2698](https://github.com/RC918/morningai/pull/2698)**: feat(reviewer): add schema versioning and reduce log noise (#2696, #2697)
  - Path: `handoff/20250928/40_App/orchestrator/`
  - Impact: Schema versioning and reduced log noise
- **[PR #2693](https://github.com/RC918/morningai/pull/2693)**: feat(reviewer): add review comment schema with start_line/end_line support (EPIC B Phase B-2)
  - Path: `handoff/20250928/40_App/orchestrator/`
  - Impact: Review comment schema with line range support
- **[PR #2692](https://github.com/RC918/morningai/pull/2692)**: feat(reviewer): implement diff-aware code review (EPIC B Phase B-1)
  - Path: `handoff/20250928/40_App/orchestrator/`
  - Impact: Diff-aware code review implementation

*Agent Architecture & Routing (12 PRs):*
- **[PR #2783](https://github.com/RC918/morningai/pull/2783)**: fix(governance): resolve agent_type to UUID for ReputationEngine DB operations
  - Path: `handoff/20250928/40_App/orchestrator/governance/reputation_engine.py`
  - Impact: UUID resolution for ReputationEngine DB operations
- **[PR #2680](https://github.com/RC918/morningai/pull/2680)**: feat(agents): add RefactorAgentV2 migration validation
  - Path: `handoff/20250928/40_App/orchestrator/`
  - Impact: RefactorAgentV2 migration validation
- **[PR #2674](https://github.com/RC918/morningai/pull/2674)**: feat(agents): implement BaseAgent with dynamic routing and Telemetry v2
  - Path: `handoff/20250928/40_App/orchestrator/`
  - Impact: BaseAgent with dynamic routing and Telemetry v2
- **[PR #2666](https://github.com/RC918/morningai/pull/2666)**: feat(refactor-agent): Add TS2307 environment health check
  - Path: `handoff/20250928/40_App/orchestrator/`
  - Impact: TypeScript TS2307 environment health check
- **[PR #2665](https://github.com/RC918/morningai/pull/2665)**: feat(routing): implement Routing Policy v1.1 for multi-model LLM selection
  - Path: `handoff/20250928/40_App/orchestrator/`
  - Impact: Routing Policy v1.1 for multi-model LLM selection
- **[PR #2659](https://github.com/RC918/morningai/pull/2659)**: feat(llm): add Qwen3 provider adapters for AliCloud and SiliconFlow
  - Path: `handoff/20250928/40_App/orchestrator/`
  - Impact: Qwen3 provider adapters for AliCloud and SiliconFlow
- **[PR #2657](https://github.com/RC918/morningai/pull/2657)**: fix: Improve Refactor Agent reliability with environment setup and validation gates
  - Path: `handoff/20250928/40_App/orchestrator/`
  - Impact: Refactor Agent reliability improvements
- **[PR #2691](https://github.com/RC918/morningai/pull/2691)**: test(routing): add direct unit tests for _adjust_tier_for_context()
  - Path: `handoff/20250928/40_App/orchestrator/`
  - Impact: Routing tier adjustment test coverage
- **[PR #2688](https://github.com/RC918/morningai/pull/2688)**: test(routing): add type error handling and multi-threading safety tests
  - Path: `handoff/20250928/40_App/orchestrator/`
  - Impact: Routing type error and multi-threading safety tests
- **[PR #2683](https://github.com/RC918/morningai/pull/2683)**: test(routing): add context size boundary and edge case tests
  - Path: `handoff/20250928/40_App/orchestrator/`
  - Impact: Routing context size boundary tests
- **[PR #2682](https://github.com/RC918/morningai/pull/2682)**: test(routing): add routing_policy.json loading and error handling tests
  - Path: `handoff/20250928/40_App/orchestrator/`
  - Impact: Routing policy loading tests
- **[PR #2684](https://github.com/RC918/morningai/pull/2684)**: test(agents): add E2E tests and TelemetryEvent JSON schema validation
  - Path: `handoff/20250928/40_App/orchestrator/`
  - Impact: Agent E2E tests and telemetry validation

*CI/CD Infrastructure & Qwen Workflow (25 PRs):*
- **[PR #2779](https://github.com/RC918/morningai/pull/2779)**: feat(tests): add CI integration tests and fault injection tests (#2650)
  - Path: `handoff/20250928/40_App/orchestrator/redis_queue/tests/`
  - Impact: CI integration tests and fault injection tests
- **[PR #2774](https://github.com/RC918/morningai/pull/2774)**: refactor(ci): extract CI Guard to testable script with resource limits
  - Path: `.github/workflows/`, `scripts/ci/`
  - Impact: CI Guard extraction to testable script
- **[PR #2598](https://github.com/RC918/morningai/pull/2598)**: ci(pr8): add PR title convention check and documentation
  - Path: `.github/workflows/`
  - Impact: PR title convention enforcement
- **[PR #2596](https://github.com/RC918/morningai/pull/2596)**: perf(typescript): implement batch baseline updates for efficiency
  - Path: `scripts/`
  - Impact: Batch baseline updates for TypeScript strict mode
- **[PR #2593](https://github.com/RC918/morningai/pull/2593)**: feat(typescript): add strict mode baseline system (TS-1, TS-2)
  - Path: `scripts/`, `.github/workflows/`
  - Impact: TypeScript strict mode baseline system
- **[PR #2583](https://github.com/RC918/morningai/pull/2583)**: feat(ci): add lockfile sync check to prevent dev/CI/prod drift
  - Path: `.github/workflows/`
  - Impact: Lockfile sync check to prevent environment drift
- **[PR #2577](https://github.com/RC918/morningai/pull/2577)**: test(env-reference): add unit tests and CI sync check
  - Path: `scripts/`, `.github/workflows/`
  - Impact: ENV_REFERENCE.md sync check
- **[PR #2572](https://github.com/RC918/morningai/pull/2572)**: fix(ci): resolve Playwright version mismatch in computed-style-check job
  - Path: `.github/workflows/`
  - Impact: Playwright version mismatch fix
- **[PR #2561](https://github.com/RC918/morningai/pull/2561)**: feat: add Qwen workflow tests, docs, and disable automatic review
  - Path: `.github/workflows/qwen-pr-review.yml`
  - Impact: Qwen workflow tests and documentation
- **[PR #2565](https://github.com/RC918/morningai/pull/2565)**: fix(ci): Fix YAML syntax error in qwen-pr-review.yml
  - Path: `.github/workflows/qwen-pr-review.yml`
  - Impact: YAML syntax fix
- **[PR #2553](https://github.com/RC918/morningai/pull/2553)**: fix(ci): Handle Dependabot PR permissions and update shared-ui baseline to 0
  - Path: `.github/workflows/`
  - Impact: Dependabot PR permissions handling
- **[PR #2550](https://github.com/RC918/morningai/pull/2550)**: feat(ci): add Storybook coverage detection CI (#2512)
  - Path: `.github/workflows/`
  - Impact: Storybook coverage detection
- **[PR #2540](https://github.com/RC918/morningai/pull/2540)**: feat: add Qwen AI code review workflow for all PRs
  - Path: `.github/workflows/qwen-pr-review.yml`
  - Impact: Qwen AI code review workflow
- **[PR #2541](https://github.com/RC918/morningai/pull/2541)**: feat(ci): add legacy component detection CI (#2513)
  - Path: `.github/workflows/`
  - Impact: Legacy component detection
- **[PR #2538](https://github.com/RC918/morningai/pull/2538)**: feat(ci): add bundle size script fallback coverage tests (#2476)
  - Path: `.github/workflows/`
  - Impact: Bundle size script fallback tests
- **[PR #2536](https://github.com/RC918/morningai/pull/2536)**: fix(ci): Improve Dependabot PR Compatibility
  - Path: `.github/workflows/`
  - Impact: Dependabot PR compatibility improvements
- **[PR #2515](https://github.com/RC918/morningai/pull/2515)**: feat(ci): add PR template path validation CI (#2514)
  - Path: `.github/workflows/`
  - Impact: PR template path validation
- **[PR #2511](https://github.com/RC918/morningai/pull/2511)**: [P2] Improve Ruff lint infrastructure with official action and auto-upgrade
  - Path: `.github/workflows/`
  - Impact: Ruff lint infrastructure improvements
- **[PR #2507](https://github.com/RC918/morningai/pull/2507)**: [P2] Pin Ruff Version to 0.8.6 for CI Stability
  - Path: `.github/workflows/`
  - Impact: Ruff version pinning for stability
- **[PR #2503](https://github.com/RC918/morningai/pull/2503)**: [P1] Add Ruff Lint Gate to CI Workflow (Blocking Mode)
  - Path: `.github/workflows/`
  - Impact: Ruff lint gate in blocking mode

*Design System & UI Components (Epic #2304) (30 PRs):*
- **[PR #2508](https://github.com/RC918/morningai/pull/2508)**: feat(governance): establish design system governance rules (#2303)
  - Path: `docs/`, `packages/shared-ui/`
  - Impact: Design system governance rules
- **[PR #2506](https://github.com/RC918/morningai/pull/2506)**: docs: update UI/UX documentation with card archetypes and Apple Kit guide (#2302)
  - Path: `docs/`
  - Impact: UI/UX documentation with card archetypes
- **[PR #2504](https://github.com/RC918/morningai/pull/2504)**: test(shared-ui): add unit tests for dashboard components (#2301)
  - Path: `packages/shared-ui/`
  - Impact: Dashboard component tests
- **[PR #2499](https://github.com/RC918/morningai/pull/2499)**: feat(shared-ui): add Storybook stories for dashboard and UI components (#2300)
  - Path: `packages/shared-ui/`
  - Impact: Storybook stories for dashboard components
- **[PR #2492](https://github.com/RC918/morningai/pull/2492)**: feat(owner-console): Phase 2-2c - Migrate UXMetrics summary cards to StatCard
  - Path: `handoff/20250928/40_App/owner-console/`
  - Impact: UXMetrics migration to StatCard
- **[PR #2487](https://github.com/RC918/morningai/pull/2487)**: refactor(owner-console): data-driven StatCards in AgentEvaluationDashboard (#2486)
  - Path: `handoff/20250928/40_App/owner-console/`
  - Impact: Data-driven StatCards
- **[PR #2484](https://github.com/RC918/morningai/pull/2484)**: feat(owner-console): Phase 2-1d - Cleanup unused Card imports and migrate AgentEvaluationDashboard
  - Path: `handoff/20250928/40_App/owner-console/`
  - Impact: Card import cleanup
- **[PR #2482](https://github.com/RC918/morningai/pull/2482)**: feat(owner-console): Phase 2-1c - Migrate FailureExperimentDashboard + SectionCard icon prop
  - Path: `handoff/20250928/40_App/owner-console/`
  - Impact: FailureExperimentDashboard migration
- **[PR #2480](https://github.com/RC918/morningai/pull/2480)**: feat(owner-console): Phase 2-1b - Migrate PlatformSettings to SettingsCard
  - Path: `handoff/20250928/40_App/owner-console/`
  - Impact: PlatformSettings migration
- **[PR #2478](https://github.com/RC918/morningai/pull/2478)**: feat(frontend-dashboard): Phase 2-1a - Migrate TwoFAStatusCard to SettingsCard
  - Path: `handoff/20250928/40_App/owner-console/`
  - Impact: TwoFAStatusCard migration
- **[PR #2434](https://github.com/RC918/morningai/pull/2434)**: feat(shared-ui): Issue #2296 - Add SettingsCard component for settings sections
  - Path: `packages/shared-ui/`
  - Impact: SettingsCard component
- **[PR #2426](https://github.com/RC918/morningai/pull/2426)**: feat(shared-ui): Issue #2295 - Add MetricCard component for entity summary metrics
  - Path: `packages/shared-ui/`
  - Impact: MetricCard component
- **[PR #2403](https://github.com/RC918/morningai/pull/2403)**: feat(design-tokens): Issue #2294 - Define card icon specification tokens
  - Path: `packages/shared-ui/`
  - Impact: Card icon specification tokens
- **[PR #2402](https://github.com/RC918/morningai/pull/2402)**: feat(shared-ui): Issue #2293 - Add StatusCard component for Phase 1
  - Path: `packages/shared-ui/`
  - Impact: StatusCard component
- **[PR #2399](https://github.com/RC918/morningai/pull/2399)**: refactor(design-system): replace hardcoded colors in spring-animations.css and micro-interactions.css (Phase 4 #2393)
  - Path: `packages/shared-ui/`
  - Impact: Hardcoded color replacement
- **[PR #2398](https://github.com/RC918/morningai/pull/2398)**: refactor(design-system): replace hardcoded colors in materials.css and motion-governance.css (Phase 3 #2393)
  - Path: `packages/shared-ui/`
  - Impact: Hardcoded color replacement
- **[PR #2395](https://github.com/RC918/morningai/pull/2395)**: feat(storybook): add stories for 10 missing components to improve coverage
  - Path: `packages/shared-ui/`
  - Impact: Storybook coverage improvement
- **[PR #2394](https://github.com/RC918/morningai/pull/2394)**: refactor(design-system): replace hardcoded colors with CSS variables (Phase 2 #2393)
  - Path: `packages/shared-ui/`
  - Impact: CSS variable adoption
- **[PR #2392](https://github.com/RC918/morningai/pull/2392)**: refactor(a11y): reduce hardcoded colors in accessibility.css and theme-apple.css
  - Path: `packages/shared-ui/`
  - Impact: Accessibility color improvements
- **[PR #2390](https://github.com/RC918/morningai/pull/2390)**: refactor(a11y): Issue #2387 - Improve accessibility test quality
  - Path: `packages/shared-ui/`
  - Impact: Accessibility test quality
- **[PR #2384](https://github.com/RC918/morningai/pull/2384)**: feat(a11y): Epic #2304 Phase 2-3 - Add 3+ accessibility test files
  - Path: `packages/shared-ui/`
  - Impact: Accessibility test files
- **[PR #2372](https://github.com/RC918/morningai/pull/2372)**: feat(a11y): Issue #2292 - Define missing CSS variables for Accessibility Tokens
  - Path: `packages/shared-ui/`
  - Impact: Accessibility CSS variables
- **[PR #2369](https://github.com/RC918/morningai/pull/2369)**: fix(a11y): Issue #2367 & #2368 - Replace white colors and resolve focus-visible conflict
  - Path: `packages/shared-ui/`
  - Impact: Accessibility color and focus fixes
- **[PR #2362](https://github.com/RC918/morningai/pull/2362)**: feat(design-tokens): Issue #2291 - Design Token source unification
  - Path: `packages/shared-ui/`
  - Impact: Design token unification
- **[PR #2359](https://github.com/RC918/morningai/pull/2359)**: feat(design-system): Implement Epic #2304 Phase 0-1 (UI/UX Foundation + Core)
  - Path: `packages/shared-ui/`
  - Impact: UI/UX foundation implementation

*Backend Refactoring (api-backend main.py) (15 PRs):*
- **[PR #2500](https://github.com/RC918/morningai/pull/2500)**: [PR1.7] Cleanup: Remove _register_inline_routes() empty function
  - Path: `handoff/20250928/40_App/api-backend/src/main.py`
  - Impact: Empty function cleanup
- **[PR #2498](https://github.com/RC918/morningai/pull/2498)**: [PR1.6d] Extract Health/Static routes to src/routes/health_static.py
  - Path: `handoff/20250928/40_App/api-backend/src/routes/health_static.py`
  - Impact: Health/Static routes extraction
- **[PR #2496](https://github.com/RC918/morningai/pull/2496)**: [PR1.6c] Extract Dashboard/Reports/Settings routes to src/routes/dashboard_reports.py
  - Path: `handoff/20250928/40_App/api-backend/src/routes/dashboard_reports.py`
  - Impact: Dashboard routes extraction
- **[PR #2493](https://github.com/RC918/morningai/pull/2493)**: [PR1.6b] Extract Phase 7 routes to src/routes/phase7.py
  - Path: `handoff/20250928/40_App/api-backend/src/routes/phase7.py`
  - Impact: Phase 7 routes extraction
- **[PR #2491](https://github.com/RC918/morningai/pull/2491)**: [PR1.6a] Extract Phase 4-6 routes to src/routes/phase456.py
  - Path: `handoff/20250928/40_App/api-backend/src/routes/phase456.py`
  - Impact: Phase 4-6 routes extraction
- **[PR #2489](https://github.com/RC918/morningai/pull/2489)**: [PR1.5] Extract App Factory Pattern to create_app()
  - Path: `handoff/20250928/40_App/api-backend/src/main.py`
  - Impact: App factory pattern extraction
- **[PR #2485](https://github.com/RC918/morningai/pull/2485)**: [PR1f] Extract Sentry initialization to src/extensions/sentry.py
  - Path: `handoff/20250928/40_App/api-backend/src/extensions/sentry.py`
  - Impact: Sentry initialization extraction
- **[PR #2481](https://github.com/RC918/morningai/pull/2481)**: [PR1e] Extract Database Initialization to src/extensions/database.py
  - Path: `handoff/20250928/40_App/api-backend/src/extensions/database.py`
  - Impact: Database initialization extraction
- **[PR #2479](https://github.com/RC918/morningai/pull/2479)**: [PR1d] Extract Error handlers to src/middleware/error_handlers.py
  - Path: `handoff/20250928/40_App/api-backend/src/middleware/error_handlers.py`
  - Impact: Error handlers extraction
- **[PR #2466](https://github.com/RC918/morningai/pull/2466)**: [PR1c] Extract Blueprint registration to src/routes/__init__.py
  - Path: `handoff/20250928/40_App/api-backend/src/routes/__init__.py`
  - Impact: Blueprint registration extraction
- **[PR #2448](https://github.com/RC918/morningai/pull/2448)**: [PR1b] Extract CORS middleware to src/middleware/cors.py
  - Path: `handoff/20250928/40_App/api-backend/src/middleware/cors.py`
  - Impact: CORS middleware extraction
- **[PR #2447](https://github.com/RC918/morningai/pull/2447)**: [PR1a] Extract _as_bool to src/utils/helpers.py
  - Path: `handoff/20250928/40_App/api-backend/src/utils/helpers.py`
  - Impact: Helper function extraction
- **[PR #2446](https://github.com/RC918/morningai/pull/2446)**: [Phase 1 Pre-work] Add contract tests for main.py refactoring
  - Path: `handoff/20250928/40_App/api-backend/`
  - Impact: Contract tests for refactoring
- **[PR #2444](https://github.com/RC918/morningai/pull/2444)**: [Phase 1] Add main.py refactoring plan document
  - Path: `docs/`
  - Impact: Refactoring plan documentation
- **[PR #2437](https://github.com/RC918/morningai/pull/2437)**: [PR0] Add regression guards: route-map test, settings reload fixture (#2375)
  - Path: `handoff/20250928/40_App/api-backend/`
  - Impact: Regression guards

*Dependency Updates (28 PRs):*
- **[PR #2638](https://github.com/RC918/morningai/pull/2638)**: chore(deps): Bump actions/setup-node from 4 to 6
- **[PR #2637](https://github.com/RC918/morningai/pull/2637)**: chore(deps): Bump actions/checkout from 4 to 6
- **[PR #2618](https://github.com/RC918/morningai/pull/2618)**: chore(deps): Bump sentry-sdk from 2.19.2 to 2.48.0 in api-backend
- **[PR #2617](https://github.com/RC918/morningai/pull/2617)**: chore(deps): Bump pyjwt from 2.8.0 to 2.10.1 in api-backend
- **[PR #2616](https://github.com/RC918/morningai/pull/2616)**: chore(deps): Bump alembic from 1.13.1 to 1.17.2 in api-backend
- **[PR #2639](https://github.com/RC918/morningai/pull/2639)**: chore(deps): Bump tj-actions/changed-files from 44 to 47
- **[PR #2636](https://github.com/RC918/morningai/pull/2636)**: chore(deps): Bump peter-evans/create-pull-request from 6 to 8
- **[PR #2635](https://github.com/RC918/morningai/pull/2635)**: chore(deps): Bump stefanzweifel/git-auto-commit-action from 5 to 7
- **[PR #2621](https://github.com/RC918/morningai/pull/2621)**: chore(deps): Update redis requirement from <6.0.0 to <7.0.0 in api-backend
- **[PR #2624](https://github.com/RC918/morningai/pull/2624)**: chore(deps): Bump aiohttp from 3.9.1 to 3.13.2 in orchestrator
- **[PR #2623](https://github.com/RC918/morningai/pull/2623)**: chore(deps): Update openai requirement from <2.0.0 to <3.0.0 in orchestrator
- **[PR #2622](https://github.com/RC918/morningai/pull/2622)**: chore(deps): Bump sentry-sdk from 2.19.2 to 2.48.0 in orchestrator
- **[PR #2615](https://github.com/RC918/morningai/pull/2615)**: chore(deps): Bump click from 8.2.1 to 8.3.1 in api-backend
- **[PR #2620](https://github.com/RC918/morningai/pull/2620)**: chore(deps): Bump requests from 2.32.3 to 2.32.5 in orchestrator
- **[PR #2619](https://github.com/RC918/morningai/pull/2619)**: chore(deps): Bump python-dotenv from 1.0.1 to 1.2.1 in orchestrator
- **[PR #2613](https://github.com/RC918/morningai/pull/2613)**: chore(deps): add orchestrator to Dependabot configuration
- **[PR #2578](https://github.com/RC918/morningai/pull/2578)**: fix(deps): align React versions with pnpm overrides (single source of truth)
- **[PR #2519](https://github.com/RC918/morningai/pull/2519)**: chore(deps): Bump playwright from 1.48.0 to 1.57.0 in api-backend
- **[PR #2516](https://github.com/RC918/morningai/pull/2516)**: chore(deps): Bump argon2-cffi from 23.1.0 to 25.1.0 in api-backend
- **[PR #2530](https://github.com/RC918/morningai/pull/2530)**: chore(deps): Bump actions/upload-artifact from 4 to 6
- **[PR #2531](https://github.com/RC918/morningai/pull/2531)**: chore(deps): Bump npm-minor-patch group in owner-console with 40 updates
- **[PR #2529](https://github.com/RC918/morningai/pull/2529)**: chore(deps): Bump dawidd6/action-download-artifact from 3 to 11
- **[PR #2528](https://github.com/RC918/morningai/pull/2528)**: chore(deps): Bump pnpm/action-setup from 2 to 4
- **[PR #2521](https://github.com/RC918/morningai/pull/2521)**: chore(deps): Bump npm-minor-patch group in shared-ui with 25 updates
- **[PR #2526](https://github.com/RC918/morningai/pull/2526)**: chore(deps): Bump trufflesecurity/trufflehog from 3.82.13 to 3.92.3
- **[PR #2517](https://github.com/RC918/morningai/pull/2517)**: chore(deps): Bump flask-cors from 6.0.0 to 6.0.2 in api-backend
- **[PR #2640](https://github.com/RC918/morningai/pull/2640)**: fix(deps): Epic #2427 P2 items - dev dependencies and jwt guard
- **[PR #2649](https://github.com/RC918/morningai/pull/2649)**: feat(tests): add black-box circuit breaker tests and document redis_queue/tests

*Orchestrator Infrastructure & Task Storage (10 PRs):*
- **[PR #2391](https://github.com/RC918/morningai/pull/2391)**: feat(orchestrator): add Redis integration tests and env schema for Task Storage (#2259)
  - Path: `handoff/20250928/40_App/orchestrator/`
  - Impact: Redis integration tests for Task Storage
- **[PR #2385](https://github.com/RC918/morningai/pull/2385)**: feat(orchestrator): implement Task Storage Migration with Repository pattern (#2259)
  - Path: `handoff/20250928/40_App/orchestrator/`
  - Impact: Task Storage Migration with Repository pattern
- **[PR #2373](https://github.com/RC918/morningai/pull/2373)**: feat(orchestrator): implement P3 enhancements (#2248, #2249, #2250, #2255)
  - Path: `handoff/20250928/40_App/orchestrator/`
  - Impact: P3 enhancements
- **[PR #2370](https://github.com/RC918/morningai/pull/2370)**: refactor(orchestrator): extract _create_base_initial_state helper (#2260)
  - Path: `handoff/20250928/40_App/orchestrator/`
  - Impact: Initial state helper extraction
- **[PR #2401](https://github.com/RC918/morningai/pull/2401)**: refactor(orchestrator): calculate elapsed_ms once for metrics (Issue #2286)
  - Path: `handoff/20250928/40_App/orchestrator/`
  - Impact: Metrics calculation optimization
- **[PR #2396](https://github.com/RC918/morningai/pull/2396)**: feat(api): add review_follow_up metrics to /metrics endpoint (#2259)
  - Path: `handoff/20250928/40_App/api-backend/`
  - Impact: Review follow-up metrics

*VSCode IDE Integration (6 PRs):*
- **[PR #2366](https://github.com/RC918/morningai/pull/2366)**: docs(vscode): add CI config, OS matrix, and cross-references (#2363, #2364, #2365)
  - Path: `handoff/20250928/40_App/orchestrator/docs/`
  - Impact: VSCode CI documentation
- **[PR #2361](https://github.com/RC918/morningai/pull/2361)**: docs(orchestrator): add VSCode IDE test strategy and edge case coverage (#2352)
  - Path: `handoff/20250928/40_App/orchestrator/docs/`
  - Impact: VSCode IDE test strategy
- **[PR #2360](https://github.com/RC918/morningai/pull/2360)**: feat(orchestrator): add Resource monitoring for VSCode IDE (#2353)
  - Path: `handoff/20250928/40_App/orchestrator/`
  - Impact: VSCode IDE resource monitoring
- **[PR #2358](https://github.com/RC918/morningai/pull/2358)**: feat(orchestrator): add Extension auto-install for VSCode IDE (#2353)
  - Path: `handoff/20250928/40_App/orchestrator/`
  - Impact: VSCode extension auto-install
- **[PR #2357](https://github.com/RC918/morningai/pull/2357)**: feat(orchestrator): add CORS / iframe support for VSCode IDE (#2353)
  - Path: `handoff/20250928/40_App/orchestrator/`
  - Impact: VSCode CORS/iframe support

*Documentation & Architecture (12 PRs):*
- **[PR #2658](https://github.com/RC918/morningai/pull/2658)**: feat(docs): add architecture manifest and verification (Epic #2465 Phase 0+1)
  - Path: `docs/`
  - Impact: Architecture manifest and verification
- **[PR #2664](https://github.com/RC918/morningai/pull/2664)**: docs(cleanup): fix 12 pre-existing documentation errors (Issue #2661)
  - Path: `docs/`
  - Impact: Documentation error fixes
- **[PR #2681](https://github.com/RC918/morningai/pull/2681)**: docs: document DashScope regional endpoints (China vs International)
  - Path: `docs/`
  - Impact: DashScope regional endpoint documentation
- **[PR #2668](https://github.com/RC918/morningai/pull/2668)**: test: add unit tests for verify_architecture_manifest.py exclusion patterns (Issue #2667)
  - Path: `scripts/`
  - Impact: Architecture manifest verification tests
- **[PR #2589](https://github.com/RC918/morningai/pull/2589)**: docs(pr7-followup): add migration records, README checker, and CHANGELOG update
  - Path: `docs/`
  - Impact: Migration records and README checker
- **[PR #2587](https://github.com/RC918/morningai/pull/2587)**: docs(pr7): move coverage and other reports to docs/reports/ directory
  - Path: `docs/reports/`
  - Impact: Report directory organization
- **[PR #2584](https://github.com/RC918/morningai/pull/2584)**: docs(pr6): move CTO reports to docs/reports/cto/ directory
  - Path: `docs/reports/cto/`
  - Impact: CTO report organization
- **[PR #2575](https://github.com/RC918/morningai/pull/2575)**: feat(docs): add auto-generated ENV_REFERENCE.md from env.schema.yaml (#2406)
  - Path: `docs/ENV_REFERENCE.md`
  - Impact: Auto-generated environment reference
- **[PR #2574](https://github.com/RC918/morningai/pull/2574)**: chore(phase3b): complete Phase 3B - Coverage Gate and Compliance docs
  - Path: `docs/`
  - Impact: Coverage gate and compliance documentation
- **[PR #2501](https://github.com/RC918/morningai/pull/2501)**: [Phase 1.7 Follow-up] Documentation updates and lint configuration recommendations
  - Path: `docs/`
  - Impact: Documentation updates
- **[PR #2495](https://github.com/RC918/morningai/pull/2495)**: docs: add frontend-dashboard carve-out rules for Phase 2 completion
  - Path: `docs/`
  - Impact: Frontend dashboard carve-out rules
- **[PR #2400](https://github.com/RC918/morningai/pull/2400)**: docs: clarify Epic #2304 Phase structure to prevent confusion
  - Path: `docs/`
  - Impact: Epic phase structure clarification

*Settings & Environment Configuration (6 PRs):*
- **[PR #2570](https://github.com/RC918/morningai/pull/2570)**: feat(settings): convert auth_service.py import-time constants to use-time accessors (#2380)
  - Path: `handoff/20250928/40_App/api-backend/src/services/auth_service.py`
  - Impact: Import-time to use-time accessor conversion
- **[PR #2568](https://github.com/RC918/morningai/pull/2568)**: feat(settings): unify os.getenv calls with centralized settings (#2379)
  - Path: `handoff/20250928/40_App/api-backend/`
  - Impact: Centralized settings unification
- **[PR #2435](https://github.com/RC918/morningai/pull/2435)**: [PR0d] CORS single authority source refactor
  - Path: `handoff/20250928/40_App/api-backend/`
  - Impact: CORS single authority source
- **[PR #2425](https://github.com/RC918/morningai/pull/2425)**: [PR0a] PyJWT/jwt dependency consistency guard (#2404)
  - Path: `handoff/20250928/40_App/api-backend/`
  - Impact: JWT dependency consistency
- **[PR #2414](https://github.com/RC918/morningai/pull/2414)**: [PR0b] Docs corrections and CORS_DEBUG documentation
  - Path: `docs/`
  - Impact: CORS_DEBUG documentation
- **[PR #2412](https://github.com/RC918/morningai/pull/2412)**: [PR0c] Gate CORS DEBUG logging with env flag and sanitize output
  - Path: `handoff/20250928/40_App/api-backend/`
  - Impact: CORS DEBUG logging gate

*Owner Console Features (8 PRs):*
- **[PR #2569](https://github.com/RC918/morningai/pull/2569)**: feat(sessions): add IDE Activity panel for real-time file monitoring (#2241)
  - Path: `handoff/20250928/40_App/owner-console/src/components/`
  - Impact: IDE Activity panel for real-time file monitoring
- **[PR #2563](https://github.com/RC918/morningai/pull/2563)**: feat(dx): implement multiple PR templates (#2477)
  - Path: `.github/PULL_REQUEST_TEMPLATE/`
  - Impact: Multiple PR templates
- **[PR #2562](https://github.com/RC918/morningai/pull/2562)**: fix(vercel): disable deployments for gh-pages-storybook branch
  - Path: `vercel.json`
  - Impact: Vercel deployment configuration
- **[PR #2544](https://github.com/RC918/morningai/pull/2544)**: [Tech Debt] Fix shared-ui TypeScript strict errors - Reduce baseline to 0
  - Path: `packages/shared-ui/`
  - Impact: TypeScript strict error fixes
- **[PR #2539](https://github.com/RC918/morningai/pull/2539)**: [Tech Debt] Fix owner-console TypeScript strict errors - Achieve baseline 0
  - Path: `handoff/20250928/40_App/owner-console/`
  - Impact: TypeScript strict error fixes
- **[PR #2449](https://github.com/RC918/morningai/pull/2449)**: feat(phase2): Phase 2-0 Plumbing PR - audit scripts and templates
  - Path: `scripts/`
  - Impact: Audit scripts and templates
- **[PR #2463](https://github.com/RC918/morningai/pull/2463)**: feat(audit): improve audit script robustness (#2454, #2456, #2460)
  - Path: `scripts/`
  - Impact: Audit script robustness
- **[PR #2445](https://github.com/RC918/morningai/pull/2445)**: feat(audit): implement match-based counting and cross-platform docs (#2440, #2441)
  - Path: `scripts/`
  - Impact: Match-based counting

*Refactor Agent & TypeScript Tooling (10 PRs):*
- **[PR #2606](https://github.com/RC918/morningai/pull/2606)**: feat(refactor-agent): TS-3 follow-up improvements - unit tests, duplicate PR check, and refactoring
  - Path: `handoff/20250928/40_App/orchestrator/`
  - Impact: Refactor Agent TS-3 improvements
- **[PR #2607](https://github.com/RC918/morningai/pull/2607)**: fix(workflow): pass REFACTOR_AGENT_AUTO_PR env var to Python script
  - Path: `.github/workflows/`
  - Impact: Refactor Agent workflow fix
- **[PR #2603](https://github.com/RC918/morningai/pull/2603)**: fix(refactor-agent): enable PR creation in run_refactor (TS-3)
  - Path: `handoff/20250928/40_App/orchestrator/`
  - Impact: Refactor Agent PR creation
- **[PR #2601](https://github.com/RC918/morningai/pull/2601)**: fix(critical): add missing current_percent parameter to rollout API endpoints
  - Path: `handoff/20250928/40_App/api-backend/`
  - Impact: Critical rollout API fix
- **[PR #2604](https://github.com/RC918/morningai/pull/2604)**: feat(rollout): implement follow-up issues #2602, #2599, #2600
  - Path: `handoff/20250928/40_App/api-backend/`
  - Impact: Rollout follow-up issues
- **[PR #2592](https://github.com/RC918/morningai/pull/2592)**: feat(scripts): parameterize update_workspace_version and add library tests (#2590, #2591)
  - Path: `scripts/`
  - Impact: Workspace version script parameterization
- **[PR #2588](https://github.com/RC918/morningai/pull/2588)**: feat(scripts): add automated React version sync tool (#2580)
  - Path: `scripts/`
  - Impact: Automated React version sync
- **[PR #2586](https://github.com/RC918/morningai/pull/2586)**: feat(tests): add regression tests for verify_system_state.sh (#2581)
  - Path: `tests/`
  - Impact: System state verification tests
- **[PR #2612](https://github.com/RC918/morningai/pull/2612)**: fix(ts): Automated TS strict mode fixes (1 error) - 2025-12-17
  - Path: `handoff/20250928/40_App/owner-console/`
  - Impact: Automated TypeScript strict mode fix
- **[PR #2614](https://github.com/RC918/morningai/pull/2614)**: feat(tests): complete Phase 4B - fix test assertion and add integration tests (#2280, #2287)
  - Path: `handoff/20250928/40_App/orchestrator/`
  - Impact: Phase 4B test completion

*Other Notable PRs:*
- **[PR #2780](https://github.com/RC918/morningai/pull/2780)**: fix(planner-events): add UUID normalization for trace_id DB compatibility
  - Path: `handoff/20250928/40_App/orchestrator/`
  - Impact: UUID normalization for trace_id
- **[PR #2777](https://github.com/RC918/morningai/pull/2777)**: fix(webhooks): use full UUID in task_id for DB compatibility
  - Path: `handoff/20250928/40_App/orchestrator/`
  - Impact: Full UUID in task_id
- **[PR #2733](https://github.com/RC918/morningai/pull/2733)**: fix: harden Redis resilience against ReadOnlyError during maintenance
  - Path: `handoff/20250928/40_App/orchestrator/`
  - Impact: Redis resilience hardening
- **[PR #2689](https://github.com/RC918/morningai/pull/2689)**: fix(render): use sync:false for CORS_ORIGINS to prevent Dashboard override
  - Path: `render.yaml`
  - Impact: CORS_ORIGINS sync configuration
- **[PR #2690](https://github.com/RC918/morningai/pull/2690)**: test(telemetry): improve validator with timestamp format and bool exclusion
  - Path: `handoff/20250928/40_App/orchestrator/`
  - Impact: Telemetry validator improvements
- **[PR #2645](https://github.com/RC918/morningai/pull/2645)**: fix(test): explicitly extend jest-dom matchers for CI compatibility
  - Path: `handoff/20250928/40_App/owner-console/`
  - Impact: Jest-dom matchers extension
- **[PR #2646](https://github.com/RC918/morningai/pull/2646)**: test(orchestrator): add tests to reach 50% coverage (Issue #2423)
  - Path: `handoff/20250928/40_App/orchestrator/`
  - Impact: Orchestrator coverage improvement
- **[PR #2397](https://github.com/RC918/morningai/pull/2397)**: fix(shared-ui): slider accessibility labeling
  - Path: `packages/shared-ui/`
  - Impact: Slider accessibility fix
- **[PR #2415](https://github.com/RC918/morningai/pull/2415)**: refactor: use small icons without containers and add deltaPositive neutral option
  - Path: `packages/shared-ui/`
  - Impact: Icon and delta display improvements
- **[PR #2424](https://github.com/RC918/morningai/pull/2424)**: [P2] Docs and test improvements (#2419, #2420, #2421, #2422)
  - Path: `docs/`
  - Impact: Documentation and test improvements

**Recent Improvements (Dec 6 - Dec 7, 2025)**:

*VSCode/MCP Integration & Meta-Agent Production Wiring:*
- **[PR #2114](https://github.com/RC918/morningai/pull/2114)**: feat(meta-agent): integrate VSCodeIDEService into production code
  - Path: `handoff/20250928/40_App/orchestrator/meta_agent/autonomous_executor.py`
  - Impact: Wires VMProvisioner and VSCodeIDEService into AutonomousExecutor; adds VM/IDE lifecycle management with 11 integration tests
  - Merged: 2025-12-07
- **[PR #2067](https://github.com/RC918/morningai/pull/2067)**: feat(meta-agent): implement MCP HTTP client for cloud IDE integration
  - Path: `handoff/20250928/40_App/orchestrator/meta_agent/vscode_ide.py`
  - Impact: Core MCP HTTP client implementation for VSCode IDE integration
  - Merged: 2025-12-06
- **[PR #2106](https://github.com/RC918/morningai/pull/2106)**: perf(vscode-ide): share aiohttp ClientSession for connection reuse
  - Path: `handoff/20250928/40_App/orchestrator/meta_agent/vscode_ide.py`
  - Impact: TCP connection pooling and DNS caching for improved MCP performance
  - Merged: 2025-12-07
- **[PR #2102](https://github.com/RC918/morningai/pull/2102)**: refactor(vscode-ide): extract constants and use exponential backoff
  - Path: `handoff/20250928/40_App/orchestrator/meta_agent/vscode_ide.py`
  - Impact: Configurable MCP timeouts, retries, and error log truncation constants
  - Merged: 2025-12-07
- **[PR #2077](https://github.com/RC918/morningai/pull/2077)**: security(vscode-ide): truncate error logs to prevent sensitive data leakage
  - Path: `handoff/20250928/40_App/orchestrator/meta_agent/vscode_ide.py`
  - Impact: Error logs truncated to 500 chars to prevent credential leakage
  - Merged: 2025-12-06

*VSCode/MCP Documentation & Infrastructure:*
- **[PR #2101](https://github.com/RC918/morningai/pull/2101)**: docs(meta-agent): add Tier 2 VSCode/VM documentation and infrastructure
  - Path: `handoff/20250928/40_App/orchestrator/docs/` (new directory)
  - Impact: Adds `TERMINAL_ACCESS.md`, `VM_LOCKING_DESIGN.md`, `VM_PROVISIONER_LIFECYCLE.md`
  - Merged: 2025-12-07
- **[PR #2115](https://github.com/RC918/morningai/pull/2115)**: docs(orchestrator): add cross-process limitation note and environment settings
  - Path: `handoff/20250928/40_App/orchestrator/meta_agent/vm_provisioner.py`, `orchestrator/docs/TERMINAL_ACCESS.md`
  - Impact: Documents VM provisioning cross-process limitations and terminal capability environment settings
  - Merged: 2025-12-07
- **[PR #2110](https://github.com/RC918/morningai/pull/2110)**: test(vscode-ide): use mocker.patch.object() for cleaner test mocking
  - Path: `handoff/20250928/40_App/orchestrator/meta_agent/tests/test_vscode_ide.py`
  - Impact: Improved test isolation with pytest-mock; added to `requirements-test.txt`
  - Merged: 2025-12-07

*Documentation Auto-Generation Security:*
- **[PR #2103](https://github.com/RC918/morningai/pull/2103)**: refactor(orchestrator): improve documentation auto-generation security and quality control
  - Path: `handoff/20250928/40_App/orchestrator/`
  - Impact: Adds `ORCHESTRATOR_DOCS_MAX_PRS_PER_HOUR` env var (default 3); prevents conflicting FAQ PRs with topic slug generation and content validation
  - Merged: 2025-12-07

*Owner Console Sessions UI & Performance:*
- **[PR #2063](https://github.com/RC918/morningai/pull/2063)**: feat(owner-console): integrate ConfidenceApproval and FileDiffViewer into Sessions UI
  - Path: `handoff/20250928/40_App/owner-console/src/pages/Sessions.jsx`
  - Impact: Sessions page now displays confidence scores and file diffs
  - Merged: 2025-12-06
- **[PR #2088](https://github.com/RC918/morningai/pull/2088)**: refactor(owner-console): Sessions.jsx defensive code improvements
  - Path: `handoff/20250928/40_App/owner-console/src/pages/Sessions.jsx`
  - Impact: Extracts `MEDIUM_CONFIDENCE_THRESHOLD` constant; improves null safety
  - Merged: 2025-12-07
- **[PR #2089](https://github.com/RC918/morningai/pull/2089)**: perf(owner-console): optimize FCP with lazy loading for task plan components
  - Path: `handoff/20250928/40_App/owner-console/src/pages/Sessions.jsx`
  - Impact: Lazy-loaded TaskPlanViewer and TaskPlanEditor for faster initial paint
  - Merged: 2025-12-07
- **[PR #2087](https://github.com/RC918/morningai/pull/2087)**: a11y(owner-console): improve keyboard accessibility for drag-and-drop task reordering
  - Path: `handoff/20250928/40_App/owner-console/src/components/`
  - Impact: Keyboard navigation support for task reordering
  - Merged: 2025-12-07

*Design System & Storybook:*
- **[PR #2068](https://github.com/RC918/morningai/pull/2068)**: fix(owner-console): add base tokens to @theme and @source for shared-ui Switch
  - Path: `handoff/20250928/40_App/owner-console/src/index.css`
  - Impact: Fixes Switch component visibility in dark/light modes
  - Merged: 2025-12-07
- **[PR #2084](https://github.com/RC918/morningai/pull/2084)**: docs(shared-ui): add Switch Storybook visual verification story
  - Path: `packages/shared-ui/src/components/ui/switch.stories.tsx`
  - Impact: Visual regression testing for Switch component states
  - Merged: 2025-12-07
- **[PR #2083](https://github.com/RC918/morningai/pull/2083)**: docs(owner-console): add Storybook stories for task plan components
  - Path: `handoff/20250928/40_App/owner-console/src/components/`
  - Impact: Storybook coverage for TaskPlanViewer and TaskPlanEditor
  - Merged: 2025-12-07
- **[PR #2061](https://github.com/RC918/morningai/pull/2061)**: chore(owner-console): remove dead theme.css file
  - Path: `handoff/20250928/40_App/owner-console/src/styles/theme.css` (removed)
  - Impact: Cleanup of unused CSS file
  - Merged: 2025-12-06

*Security & Testing:*
- **[PR #2052](https://github.com/RC918/morningai/pull/2052)**: fix(meta-agent): add TOCTOU defense in save_state()
  - Path: `handoff/20250928/40_App/orchestrator/meta_agent/state_persistence.py`
  - Impact: Atomic file writes prevent race conditions in state persistence
  - Merged: 2025-12-06
- **[PR #2078](https://github.com/RC918/morningai/pull/2078)**: test(owner-console): add XSS protection tests for TestResultsPanel
  - Path: `handoff/20250928/40_App/owner-console/src/components/`
  - Impact: Security tests for XSS prevention in test results display
  - Merged: 2025-12-07
- **[PR #2079](https://github.com/RC918/morningai/pull/2079)**: test(orchestrator): add unit tests for update_error_fix_pair
  - Path: `handoff/20250928/40_App/orchestrator/`
  - Impact: Improved test coverage for error-fix pair functionality
  - Merged: 2025-12-07

**Recent Improvements (Dec 7 - Dec 9, 2025)**:

*DeepWiki Integration:*
- **[PR #2156](https://github.com/RC918/morningai/pull/2156)**: feat(deepwiki): integrate DeepWiki session insights into AutonomousExecutor
  - Path: `handoff/20250928/40_App/orchestrator/meta_agent/autonomous_executor.py`
  - Impact: DeepWiki knowledge base integration for enhanced session context
  - Merged: 2025-12-07
- **[PR #2157](https://github.com/RC918/morningai/pull/2157)**: feat(orchestrator): integrate DeepWiki with AutonomousExecutor
  - Path: `handoff/20250928/40_App/orchestrator/`
  - Impact: Full DeepWiki orchestrator integration
  - Merged: 2025-12-07
- **[PR #2164](https://github.com/RC918/morningai/pull/2164)**: fix(deepwiki): add retry logic and rate limiting
  - Path: `handoff/20250928/40_App/orchestrator/`
  - Impact: Improved reliability with retry logic and rate limiting for DeepWiki API calls
  - Merged: 2025-12-07
- **[PR #2163](https://github.com/RC918/morningai/pull/2163)**: feat(api): add DeepWiki API endpoints for knowledge base queries
  - Path: `handoff/20250928/40_App/api-backend/`
  - Impact: New API endpoints for DeepWiki knowledge base queries
  - Merged: 2025-12-07
- **[PR #2169](https://github.com/RC918/morningai/pull/2169)**: feat(owner-console): add SessionInsights component for DeepWiki insights
  - Path: `handoff/20250928/40_App/owner-console/src/components/`
  - Impact: UI component for displaying DeepWiki session insights
  - Merged: 2025-12-07

*Sessions UI & HITL Optimization:*
- **[PR #2170](https://github.com/RC918/morningai/pull/2170)**: feat(owner-console): HITL approval UI/UX optimization
  - Path: `handoff/20250928/40_App/owner-console/src/components/`
  - Impact: Improved Human-in-the-Loop approval workflow UX
  - Merged: 2025-12-07
- **[PR #2173](https://github.com/RC918/morningai/pull/2173)**: feat(i18n): add SessionInsights translation keys and unit tests
  - Path: `handoff/20250928/40_App/owner-console/src/i18n/`
  - Impact: Internationalization support for SessionInsights component
  - Merged: 2025-12-08
- **[PR #2175](https://github.com/RC918/morningai/pull/2175)**: feat(owner-console): add SessionCommandInput for interactive session commands
  - Path: `handoff/20250928/40_App/owner-console/src/components/`
  - Impact: New interactive command input for session management
  - Merged: 2025-12-08
- **[PR #2182](https://github.com/RC918/morningai/pull/2182)**: refactor(owner-console): tidy SessionCommandInput constants and props
  - Path: `handoff/20250928/40_App/owner-console/src/components/`
  - Impact: Code cleanup and improved prop definitions
  - Merged: 2025-12-08
- **[PR #2188](https://github.com/RC918/morningai/pull/2188)**: test(owner-console): add unit tests for SessionCommandInput
  - Path: `handoff/20250928/40_App/owner-console/src/components/`
  - Impact: Test coverage for SessionCommandInput component
  - Merged: 2025-12-08
- **[PR #2189](https://github.com/RC918/morningai/pull/2189)**: feat(owner-console): persist command history with localStorage
  - Path: `handoff/20250928/40_App/owner-console/src/components/`
  - Impact: Command history persistence across sessions
  - Merged: 2025-12-08
- **[PR #2225](https://github.com/RC918/morningai/pull/2225)**: fix(owner-console): fix ApprovalQueue TDZ error and improve auto-refresh
  - Path: `handoff/20250928/40_App/owner-console/src/components/`
  - Impact: Fixed Temporal Dead Zone error and improved auto-refresh behavior
  - Merged: 2025-12-08
- **[PR #2234](https://github.com/RC918/morningai/pull/2234)**: fix(owner-console): fix console warnings and session card layout issues
  - Path: `handoff/20250928/40_App/owner-console/src/components/`
  - Impact: Fixed console warnings and improved session card layout
  - Merged: 2025-12-08
- **[PR #2279](https://github.com/RC918/morningai/pull/2279)**: feat(owner-console): add SessionStatusCard component with standardized design spec
  - Path: `handoff/20250928/40_App/owner-console/src/components/`
  - Impact: New standardized SessionStatusCard component for consistent UI
  - Merged: 2025-12-09

*CSRF Token Management:*
- **[PR #2237](https://github.com/RC918/morningai/pull/2237)**: fix(owner-console): fix CSRF token sync issue causing 403 errors
  - Path: `handoff/20250928/40_App/owner-console/src/lib/csrf-token.ts`
  - Impact: Fixed CSRF token synchronization preventing 403 errors
  - Merged: 2025-12-08
- **[PR #2238](https://github.com/RC918/morningai/pull/2238)**: refactor(owner-console): unify CSRF token management
  - Path: `handoff/20250928/40_App/owner-console/src/lib/csrf-token.ts`
  - Impact: Unified CSRF token management with Auth and API Client modes
  - Merged: 2025-12-08
- **[PR #2239](https://github.com/RC918/morningai/pull/2239)**: docs(owner-console): add CSRF token mode selection warning
  - Path: `handoff/20250928/40_App/owner-console/src/lib/csrf-token.ts`
  - Impact: Added documentation warning for CSRF token mode selection
  - Merged: 2025-12-09
- **[PR #2240](https://github.com/RC918/morningai/pull/2240)**: docs(owner-console): add warning comment for CSRF token mode selection
  - Path: `handoff/20250928/40_App/owner-console/src/lib/csrf-token.ts`
  - Impact: Follow-up documentation for CSRF token mode selection
  - Merged: 2025-12-09

*AI Reviewer & Comment Triage:*
- **[PR #2244](https://github.com/RC918/morningai/pull/2244)**: feat(orchestrator): fix AI Reviewer comment intake mechanism
  - Path: `handoff/20250928/40_App/orchestrator/nodes/review_intake.py`
  - Impact: Fixed AI Reviewer bot whitelist and comment intake mechanism
  - Merged: 2025-12-09
- **[PR #2246](https://github.com/RC918/morningai/pull/2246)**: feat(orchestrator): implement Comment Triage Agent for AI reviewer comments
  - Path: `handoff/20250928/40_App/orchestrator/nodes/comment_triage.py`
  - Impact: New Comment Triage Agent for categorizing and prioritizing AI reviewer comments
  - Merged: 2025-12-09

*Review Follow-up & Internal Reviewer:*
- **[PR #2257](https://github.com/RC918/morningai/pull/2257)**: feat(orchestrator): implement Review Follow-up Mode (Issue #2211)
  - Path: `handoff/20250928/40_App/orchestrator/nodes/review_follow_up.py`
  - Impact: New Review Follow-up Mode for tracking and addressing review comments
  - Merged: 2025-12-09
- **[PR #2262](https://github.com/RC918/morningai/pull/2262)**: feat(orchestrator): implement Internal Reviewer Agent re-review mechanism (Issue #2212)
  - Path: `handoff/20250928/40_App/orchestrator/nodes/internal_review_node.py`
  - Impact: Internal Reviewer Agent with re-review capability for quality assurance
  - Merged: 2025-12-09
- **[PR #2267](https://github.com/RC918/morningai/pull/2267)**: refactor(orchestrator): add required field validation in internal_review_node (Issue #2263)
  - Path: `handoff/20250928/40_App/orchestrator/nodes/internal_review_node.py`
  - Impact: Added required field validation for internal review node
  - Merged: 2025-12-09
- **[PR #2268](https://github.com/RC918/morningai/pull/2268)**: feat(orchestrator): add configurable PARTIAL agreement policy (Issue #2264)
  - Path: `handoff/20250928/40_App/orchestrator/nodes/internal_review_node.py`
  - Impact: Configurable PARTIAL agreement policy for internal reviews
  - Merged: 2025-12-09
- **[PR #2269](https://github.com/RC918/morningai/pull/2269)**: docs(orchestrator): document internal_review_node vs reviewer_node responsibilities (Issue #2265)
  - Path: `handoff/20250928/40_App/orchestrator/docs/`
  - Impact: Documentation clarifying node responsibilities
  - Merged: 2025-12-09

*Multi-Signal Trigger & Rollout Tracker (Phase 7 Completion):*
- **[PR #2275](https://github.com/RC918/morningai/pull/2275)**: feat(orchestrator): implement Multi-Signal Trigger System (Issue #2213)
  - Path: `handoff/20250928/40_App/orchestrator/multi_signal_trigger.py`
  - Impact: Multi-signal trigger system for automated workflow initiation
  - Merged: 2025-12-09
- **[PR #2278](https://github.com/RC918/morningai/pull/2278)**: feat(orchestrator): implement LangGraph 100% Rollout Tracker (Issue #2214)
  - Path: `handoff/20250928/40_App/orchestrator/rollout_tracker.py`
  - Impact: LangGraph rollout tracking with metrics and dashboard support
  - Merged: 2025-12-09
- **[PR #2284](https://github.com/RC918/morningai/pull/2284)**: feat(orchestrator): integrate RolloutTracker into worker.py (Issue #2280)
  - Path: `handoff/20250928/40_App/orchestrator/redis_queue/worker.py`
  - Impact: RolloutTracker integration into worker for production monitoring
  - Merged: 2025-12-09
- **[PR #2288](https://github.com/RC918/morningai/pull/2288)**: docs: update milestones document with Dec 2025 progress (Issue #2215)
  - Path: `docs/MILESTONES.md`
  - Impact: Updated milestones document with Phase 7 completion status
  - Merged: 2025-12-09

*Owner Console UI Refactoring:*
- **[PR #2245](https://github.com/RC918/morningai/pull/2245)**: refactor(owner-console): move settings and logout to user dropdown menu
  - Path: `handoff/20250928/40_App/owner-console/src/components/`
  - Impact: Improved navigation UX with user dropdown menu
  - Merged: 2025-12-09
- **[PR #2256](https://github.com/RC918/morningai/pull/2256)**: refactor(owner-console): DashboardHeader cleanup and testing
  - Path: `handoff/20250928/40_App/owner-console/src/components/DashboardHeader.jsx`
  - Impact: Code cleanup and improved test coverage for DashboardHeader
  - Merged: 2025-12-09
- **[PR #2261](https://github.com/RC918/morningai/pull/2261)**: refactor(owner-console): Sidebar UX optimization - single-line items and tooltips
  - Path: `handoff/20250928/40_App/owner-console/src/components/Sidebar.jsx`
  - Impact: Improved Sidebar UX with single-line items and tooltips
  - Merged: 2025-12-09
- **[PR #2266](https://github.com/RC918/morningai/pull/2266)**: refactor(owner-console): implement single-layer Header + Sidebar architecture
  - Path: `handoff/20250928/40_App/owner-console/src/components/`
  - Impact: Simplified Header and Sidebar architecture
  - Merged: 2025-12-09
- **[PR #2270](https://github.com/RC918/morningai/pull/2270)**: fix(shared-ui): add arrowClassName prop to Tooltip for customizable arrow styling
  - Path: `packages/shared-ui/src/components/ui/tooltip.tsx`
  - Impact: Enhanced Tooltip component with customizable arrow styling
  - Merged: 2025-12-09

*CI/CD & Testing Infrastructure:*
- **[PR #2174](https://github.com/RC918/morningai/pull/2174)**: feat(ci): enable TypeScript Strict Mode baseline tracking for all packages
  - Path: `.github/workflows/`
  - Impact: TypeScript Strict Mode baseline tracking across all packages
  - Merged: 2025-12-08
- **[PR #2183](https://github.com/RC918/morningai/pull/2183)**: fix(orchestrator): fix failing tests in visual_verification and project_engineer
  - Path: `handoff/20250928/40_App/orchestrator/`
  - Impact: Fixed failing tests in visual verification and project engineer modules
  - Merged: 2025-12-08
- **[PR #2190](https://github.com/RC918/morningai/pull/2190)**: fix(orchestrator): increase performance test threshold for planner node
  - Path: `handoff/20250928/40_App/orchestrator/`
  - Impact: Adjusted performance test thresholds for planner node
  - Merged: 2025-12-08
- **[PR #2194](https://github.com/RC918/morningai/pull/2194)**: fix(orchestrator): add rate limit mock to TestExecute tests
  - Path: `handoff/20250928/40_App/orchestrator/`
  - Impact: Fixed test flakiness with rate limit mocking
  - Merged: 2025-12-08
- **[PR #2200](https://github.com/RC918/morningai/pull/2200)**: test(orchestrator): add comprehensive tests for langgraph_orchestrator.py
  - Path: `handoff/20250928/40_App/orchestrator/tests/`
  - Impact: Comprehensive test coverage for LangGraph orchestrator
  - Merged: 2025-12-08
- **[PR #2233](https://github.com/RC918/morningai/pull/2233)**: test(api-backend): add comprehensive tests for sentry_integration.py
  - Path: `handoff/20250928/40_App/api-backend/`
  - Impact: Test coverage for Sentry integration module
  - Merged: 2025-12-08
- **[PR #2235](https://github.com/RC918/morningai/pull/2235)**: test(orchestrator): add security rules tests for project_engineer/agent.py
  - Path: `handoff/20250928/40_App/orchestrator/`
  - Impact: Security rules test coverage for project engineer agent
  - Merged: 2025-12-08
- **[PR #2236](https://github.com/RC918/morningai/pull/2236)**: test(owner-console): add comprehensive tests for LoginPage component
  - Path: `handoff/20250928/40_App/owner-console/src/pages/`
  - Impact: Test coverage for LoginPage component
  - Merged: 2025-12-08

*Backend & Infrastructure:*
- **[PR #2184](https://github.com/RC918/morningai/pull/2184)**: feat(api-backend): add /api/sessions/{id}/command endpoint
  - Path: `handoff/20250928/40_App/api-backend/`
  - Impact: New API endpoint for session command execution
  - Merged: 2025-12-08
- **[PR #2197](https://github.com/RC918/morningai/pull/2197)**: feat(orchestrator): add A/B testing metrics collection and analysis framework
  - Path: `handoff/20250928/40_App/orchestrator/`
  - Impact: A/B testing metrics framework for experiment analysis
  - Merged: 2025-12-08
- **[PR #2204](https://github.com/RC918/morningai/pull/2204)**: fix: reduce noisy Sentry alerts for expected error conditions
  - Path: `handoff/20250928/40_App/api-backend/`
  - Impact: Reduced Sentry noise by filtering expected errors
  - Merged: 2025-12-08
- **[PR #2218](https://github.com/RC918/morningai/pull/2218)**: feat(orchestrator): complete Wave 1 Phase 7 prerequisites
  - Path: `handoff/20250928/40_App/orchestrator/`
  - Impact: Completed Wave 1 prerequisites for Phase 7
  - Merged: 2025-12-08
- **[PR #2224](https://github.com/RC918/morningai/pull/2224)**: feat(orchestrator): add retry and rate limiting to OutboundNotifier
  - Path: `handoff/20250928/40_App/orchestrator/`
  - Impact: Improved reliability for outbound notifications
  - Merged: 2025-12-08
- **[PR #2231](https://github.com/RC918/morningai/pull/2231)**: feat(orchestrator): Wave 3 Failure Learning Enhancement
  - Path: `handoff/20250928/40_App/orchestrator/`
  - Impact: Enhanced failure learning capabilities
  - Merged: 2025-12-08
- **[PR #2232](https://github.com/RC918/morningai/pull/2232)**: fix(api-backend): add Upstash Redis adapter for scan_iter compatibility
  - Path: `handoff/20250928/40_App/api-backend/`
  - Impact: Fixed Redis scan_iter compatibility for Upstash
  - Merged: 2025-12-08

*Documentation:*
- **[PR #2193](https://github.com/RC918/morningai/pull/2193)**: docs: align documentation with actual implementation
  - Path: `docs/`
  - Impact: Documentation alignment with current implementation
  - Merged: 2025-12-08

**Recent Improvements (Dec 3 - Dec 5, 2025)**:

*Refactor Agent & TS Strict Mode Automation:*
- **[PR #1886](https://github.com/RC918/morningai/pull/1886)**: Phase 4 - Refactor Agent for TS Strict Mode Automation
  - Path: `handoff/20250928/40_App/orchestrator/refactor_agent/`, `config/env.schema.yaml`, `.env.example`
  - Impact: Introduces Refactor Agent with automated TS strict-mode fixes; adds `REFACTOR_AGENT_ENABLED`, `REFACTOR_AGENT_ERRORS_PER_RUN`, `REFACTOR_AGENT_AUTO_PR` env vars
  - Merged: 2025-12-04
- **[PR #1897](https://github.com/RC918/morningai/pull/1897)**: LLM Integration for Refactor Agent Code Fix Generation
  - Path: `handoff/20250928/40_App/orchestrator/refactor_agent/agent.py`
  - Impact: Adds LLM-powered code fix generation for TS strict mode violations
  - Merged: 2025-12-04
- **[PR #1903](https://github.com/RC918/morningai/pull/1903)**: File Modification Implementation for Refactor Agent
  - Path: `handoff/20250928/40_App/orchestrator/refactor_agent/agent.py`
  - Impact: Enables actual file modifications for automated fixes
  - Merged: 2025-12-04
- **[PR #1908](https://github.com/RC918/morningai/pull/1908)**: PR Automation for Refactor Agent
  - Path: `handoff/20250928/40_App/orchestrator/refactor_agent/agent.py`
  - Impact: Automatically creates PRs for refactor fixes
  - Merged: 2025-12-05
- **[PR #1913](https://github.com/RC918/morningai/pull/1913)**: Nightly Cron Job Setup + Grammar/Optimization Improvements
  - Path: `.github/workflows/refactor-agent-nightly.yml`
  - Impact: Adds nightly cron job for automated TS strict mode fixes
  - Merged: 2025-12-05

*Task Queue Reliability (Ops Agent):*
- **[PR #1907](https://github.com/RC918/morningai/pull/1907)**: Fix infinite loop for unassigned tasks
  - Path: `agents/ops_agent/worker.py`
  - Impact: Prevents busy-loop when `assigned_to` is missing; tasks without assignment are now skipped with warning
  - Merged: 2025-12-05
- **[PR #1912](https://github.com/RC918/morningai/pull/1912)**: Implement task status update and assigned_to validation
  - Path: `agents/ops_agent/worker.py`, `orchestrator/task_queue/redis_queue.py`
  - Impact: Misrouted tasks marked FAILED with `task.failed` event; enqueue without `assigned_to` logs warning
  - Merged: 2025-12-05
- **[PR #1914](https://github.com/RC918/morningai/pull/1914)**: Add automated tests for task routing (#1909, #1910)
  - Path: `agents/ops_agent/tests/test_task_routing.py`
  - Impact: 8 new tests for task routing behavior (4 misrouted + 3 enqueue warning + 1 integration)
  - Merged: 2025-12-05
- **[PR #1934](https://github.com/RC918/morningai/pull/1934)**: Use pytest pythonpath instead of sys.path.insert
  - Path: `agents/ops_agent/tests/test_task_routing.py`
  - Impact: Cleaner test setup using pytest.ini pythonpath configuration
  - Merged: 2025-12-05

*Owner Console Page Standardization (Phase 1 Complete):*
- **[PR #1863](https://github.com/RC918/morningai/pull/1863)**: Standardize AgentGovernance page layout & fix Dashboard title i18n
  - Path: `handoff/20250928/40_App/owner-console/src/pages/AgentGovernance.jsx`
  - Impact: Unified layout with PageScaffold/SectionTemplate
  - Merged: 2025-12-04
- **[PR #1867](https://github.com/RC918/morningai/pull/1867)**: Standardize TenantManagement page layout
  - Path: `handoff/20250928/40_App/owner-console/src/pages/TenantManagement.jsx`
  - Merged: 2025-12-04
- **[PR #1879](https://github.com/RC918/morningai/pull/1879)**: Standardize SystemMonitoring page layout
  - Path: `handoff/20250928/40_App/owner-console/src/pages/SystemMonitoring.jsx`
  - Merged: 2025-12-04
- **[PR #1883](https://github.com/RC918/morningai/pull/1883)**: Standardize UXMetrics page layout
  - Path: `handoff/20250928/40_App/owner-console/src/pages/UXMetrics.jsx`
  - Merged: 2025-12-04
- **[PR #1885](https://github.com/RC918/morningai/pull/1885)**: Standardize AIPolicies page layout
  - Path: `handoff/20250928/40_App/owner-console/src/pages/AIPolicies.jsx`
  - Merged: 2025-12-04
- **[PR #1894](https://github.com/RC918/morningai/pull/1894)**: Standardize ApprovalQueue page layout
  - Path: `handoff/20250928/40_App/owner-console/src/pages/ApprovalQueue.jsx`
  - Merged: 2025-12-04
- **[PR #1900](https://github.com/RC918/morningai/pull/1900)**: Standardize FailureExperimentDashboard and PlatformSettings pages
  - Path: `handoff/20250928/40_App/owner-console/src/pages/FailureExperimentDashboard.jsx`, `PlatformSettings.jsx`
  - Merged: 2025-12-04
- **[PR #1906](https://github.com/RC918/morningai/pull/1906)**: Move language switcher to navbar and remove duplicate user info
  - Path: `handoff/20250928/40_App/owner-console/src/components/Sidebar.jsx`, `DashboardHeader.jsx`
  - Impact: Improved navigation UX with language switcher in navbar
  - Merged: 2025-12-04

*Shared UI Components:*
- **[PR #1884](https://github.com/RC918/morningai/pull/1884)**: Implement PageScaffold component
  - Path: `packages/shared-ui/src/components/`
  - Impact: Canonical layout primitive for Owner Console pages
  - Merged: 2025-12-04
- **[PR #1887](https://github.com/RC918/morningai/pull/1887)**: Implement SectionTemplate component
  - Path: `packages/shared-ui/src/components/`
  - Impact: Standardized section layout for dashboard cards
  - Merged: 2025-12-04
- **[PR #1853](https://github.com/RC918/morningai/pull/1853)**: Add iotask foundation components (Phase 1)
  - Path: `packages/shared-ui/src/components/`
  - Merged: 2025-12-04
- **[PR #1856](https://github.com/RC918/morningai/pull/1856)**: Phase 2 - AdminShell three-column layout support
  - Path: `packages/shared-ui/src/components/`
  - Merged: 2025-12-04

*Security & Memory (Phase 1-2):*
- **[PR #1826](https://github.com/RC918/morningai/pull/1826)**: Phase 1 Security Foundation - RLS Hard Gate, Semantic Rules v3, Monitoring & E2E Tests
  - Path: `handoff/20250928/40_App/api-backend/`, `migrations/`
  - Impact: Enhanced RLS enforcement and security monitoring
  - Merged: 2025-12-03
- **[PR #1830](https://github.com/RC918/morningai/pull/1830)**: Phase 1 Follow-up Issues - Settings, validate_task(), False Positive Evaluation
  - Path: `common/config/settings.py`, `handoff/20250928/40_App/orchestrator/`
  - Merged: 2025-12-03
- **[PR #1831](https://github.com/RC918/morningai/pull/1831)**: Phase 2 P0 - pgvector Similarity Search and Error-Fix Pairs
  - Path: `handoff/20250928/40_App/orchestrator/persistence/`
  - Impact: Vector similarity search for failure knowledge base
  - Merged: 2025-12-03
- **[PR #1836](https://github.com/RC918/morningai/pull/1836)**: Phase 2 P1 - Observer Node for Failure Knowledge Base
  - Path: `handoff/20250928/40_App/orchestrator/`
  - Impact: Observes and records failures for knowledge base
  - Merged: 2025-12-03

*Orchestrator Enhancements:*
- **[PR #1852](https://github.com/RC918/morningai/pull/1852)**: Phase 3 P2 - LangGraph Mode Full Switchover
  - Path: `handoff/20250928/40_App/orchestrator/langgraph_orchestrator.py`, `graph.py`
  - Impact: Full LangGraph mode support with canary routing
  - Merged: 2025-12-04
- **[PR #1854](https://github.com/RC918/morningai/pull/1854)**: Phase 3 P2 - Human-in-the-Loop High-Risk Approval Workflow
  - Path: `handoff/20250928/40_App/orchestrator/`
  - Impact: HITL approval for high-risk operations
  - Merged: 2025-12-04
- **[PR #1857](https://github.com/RC918/morningai/pull/1857)**: Phase 3 P3 - PM Agent + Ops Agent
  - Path: `handoff/20250928/40_App/orchestrator/`
  - Impact: PM Agent and Ops Agent integration
  - Merged: 2025-12-04
- **[PR #1862](https://github.com/RC918/morningai/pull/1862)**: Phase 3 P4 - Background Queue Principles Enhancement
  - Path: `handoff/20250928/40_App/orchestrator/`, `docs/BACKGROUND_QUEUE_PRINCIPLES.md`
  - Impact: Enhanced queue principles documentation
  - Merged: 2025-12-04
- **[PR #1866](https://github.com/RC918/morningai/pull/1866)**: Phase 3 Follow-up Issues (#1858, #1859, #1860, #1861, #1864, #1865)
  - Path: `handoff/20250928/40_App/orchestrator/`, `config/env.schema.yaml`
  - Impact: Multiple orchestrator improvements and fixes
  - Merged: 2025-12-04

*ESLint Spacing Rules:*
- **[PR #1892](https://github.com/RC918/morningai/pull/1892)**: Add ESLint rule for standardized spacing utilities
  - Path: `handoff/20250928/40_App/owner-console/eslint-rules/no-non-standard-spacing.js`
  - Impact: Custom ESLint rule to enforce design system spacing tokens
  - Merged: 2025-12-04
- **[PR #1901](https://github.com/RC918/morningai/pull/1901)**: Cleanup 29 spacing violations to match design system scale
  - Path: `handoff/20250928/40_App/owner-console/src/`
  - Impact: Fixed 29 spacing violations across Owner Console
  - Merged: 2025-12-04
- **[PR #1904](https://github.com/RC918/morningai/pull/1904)**: Upgrade spacing ESLint rule to error mode (Phase 3)
  - Path: `handoff/20250928/40_App/owner-console/eslint.config.js`
  - Impact: Spacing violations now block builds
  - Merged: 2025-12-04

*Migrations & Infrastructure:*
- **[PR #1871](https://github.com/RC918/morningai/pull/1871)**: Phase 4 - Unified Migration Management
  - Path: `scripts/run_migrations.sh`
  - Impact: DRY refactoring for migration runner
  - Merged: 2025-12-04
- **[PR #1895](https://github.com/RC918/morningai/pull/1895)**: DRY refactoring for run_migrations.sh
  - Path: `scripts/run_migrations.sh`
  - Impact: Cleaner migration script with better error handling
  - Merged: 2025-12-04
- **[PR #1881](https://github.com/RC918/morningai/pull/1881)**: Update secrets config to use new key names (FLASK_SECRET_KEY, ENCRYPTION_MASTER_KEY)
  - Path: `config/env.schema.yaml`
  - Impact: Standardized secret key naming
  - Merged: 2025-12-04
- **[PR #1882](https://github.com/RC918/morningai/pull/1882)**: Upgrade vulnerable packages and expand CI scanning coverage
  - Path: `agents/*/requirements.txt`, `.github/workflows/secret-scanning.yml`
  - Impact: Security vulnerability fixes and expanded CI scanning
  - Merged: 2025-12-04

**Recent Improvements (Dec 2 - Dec 3, 2025)**:

*Experimentation & Reasoning Mode:*
- **[PR #1804](https://github.com/RC918/morningai/pull/1804)**: Phase 4 Production Rollout - Increase experiment percentages and add kill switch
  - Path: `handoff/20250928/40_App/orchestrator/experiment_manager.py`, `common/config/settings.py`, `config/env.schema.yaml`
  - Impact: Raises gemini3_planner_staging from 10% to 25%, gemini3_reviewer_staging from 5% to 10%; adds `DISABLE_GEMINI3` kill switch for emergency rollback
  - Merged: 2025-12-03
- **[PR #1803](https://github.com/RC918/morningai/pull/1803)**: Phase 3 Remaining Items - Gemini 3 fallback, parametrize tests, CI gate
  - Path: `.github/workflows/gemini3-reviewer-gate.yml`, `handoff/20250928/40_App/orchestrator/tests/test_llm_planner_adapter.py`, `test_llm_reviewer_adapter.py`
  - Impact: Adds Gemini 3 reviewer gate CI workflow and consolidates test patterns
  - Merged: 2025-12-03
- **[PR #1794](https://github.com/RC918/morningai/pull/1794)**: Phase 3.1 Hardening - Add REASONING_MODE_ENABLED schema and unit tests
  - Path: `config/env.schema.yaml`, `common/config/settings.py`
  - Impact: Adds `REASONING_MODE_ENABLED` env var for controlling Gemini 3 thinking_level
  - Merged: 2025-12-02
- **[PR #1793](https://github.com/RC918/morningai/pull/1793)**: Phase 3 - Reasoning mode toggle and Gemini 3 reviewer experiment
  - Path: `handoff/20250928/40_App/orchestrator/llm/adapters/llm_reviewer_adapter.py`
  - Impact: Enables reasoning mode toggle and gemini3_reviewer_5pct_staging experiment
  - Merged: 2025-12-02
- **[PR #1792](https://github.com/RC918/morningai/pull/1792)**: Redis Checkpointer - LangGraph state persistence
  - Path: `handoff/20250928/40_App/orchestrator/redis_checkpointer.py`, `graph.py`
  - Impact: Adds Redis-based checkpointer for LangGraph state persistence with configurable TTL
  - Merged: 2025-12-02
- **[PR #1791](https://github.com/RC918/morningai/pull/1791)**: FAQ Routing - Route FAQ tasks via simple path, bypass LangGraph
  - Path: `handoff/20250928/40_App/orchestrator/graph.py`
  - Impact: FAQ tasks now use simple mode (~95% traffic) for faster response
  - Merged: 2025-12-02

*Configuration & Secrets Hardening:*
- **[PR #1800](https://github.com/RC918/morningai/pull/1800)**: Migrate os.getenv to settings.py for Tier 1 production code
  - Path: `handoff/20250928/40_App/orchestrator/`, `common/config/settings.py`
  - Impact: Centralizes environment variable access through Pydantic settings
  - Merged: 2025-12-03
- **[PR #1798](https://github.com/RC918/morningai/pull/1798)**: Migrate WORKER_HEARTBEAT_INTERVAL and WORKER_HEARTBEAT_TTL to settings.py
  - Path: `common/config/settings.py`, `config/env.schema.yaml`
  - Impact: Adds `WORKER_HEARTBEAT_INTERVAL` (60s) and `WORKER_HEARTBEAT_TTL` (180s) env vars
  - Merged: 2025-12-02
- **[PR #1797](https://github.com/RC918/morningai/pull/1797)**: Migrate RQ_MAX_JOBS to settings.py and add secrets hardening
  - Path: `common/config/settings.py`, `config/env.schema.yaml`
  - Impact: Adds `RQ_MAX_JOBS` env var for worker memory management; hardens `FLASK_SECRET_KEY` and `ENCRYPTION_MASTER_KEY`
  - Merged: 2025-12-02
- **[PR #1795](https://github.com/RC918/morningai/pull/1795)**: Remove deprecated SECRET_KEY and MASTER_KEY
  - Path: `config/env.schema.yaml`
  - Impact: Removes legacy `SECRET_KEY` and `MASTER_KEY` in favor of `FLASK_SECRET_KEY` and `ENCRYPTION_MASTER_KEY`
  - Merged: 2025-12-02
- **[PR #1790](https://github.com/RC918/morningai/pull/1790)**: Add RQ_MAX_JOBS env var for worker memory management
  - Path: `handoff/20250928/40_App/orchestrator/redis_queue/worker.py`, `config/env.schema.yaml`
  - Impact: Worker restarts after processing N jobs to prevent OOM from LangGraph checkpoints
  - Merged: 2025-12-02

*UI/UX & Design System:*
- **[PR #1802](https://github.com/RC918/morningai/pull/1802)**: Storybook Stories for DashboardHeader and Sidebar
  - Path: `handoff/20250928/40_App/owner-console/src/components/DashboardHeader.stories.tsx`, `Sidebar.stories.tsx`
  - Impact: Adds 21 Storybook stories for visual documentation of layout components
  - Merged: 2025-12-03
- **[PR #1801](https://github.com/RC918/morningai/pull/1801)**: Phase 3-4 Completion - iotask Component Styling and Progress Bars
  - Path: `packages/shared-ui/src/components/ui/button.tsx`, `badge.tsx`, `card.tsx`, `input.tsx`, `progress.tsx`
  - Impact: Updates Button, Badge, Card, Input, Progress components with iotask design system
  - Merged: 2025-12-03
- **[PR #1796](https://github.com/RC918/morningai/pull/1796)**: iotask Design System Upgrade - Phase 1-4
  - Path: `packages/shared-ui/src/tokens.json`, `handoff/20250928/40_App/owner-console/src/components/`
  - Impact: Updates design tokens to iotask color palette; adds DashboardHeader component; dark theme Sidebar
  - Merged: 2025-12-02

**Recent Improvements (Nov 29 - Dec 1, 2025)**:
- **[PR #1788](https://github.com/RC918/morningai/pull/1788)**: Failure Memory Integration - Wire failure knowledge base into failure recorder (Phase 5 PR-1)
  - Path: `handoff/20250928/40_App/orchestrator/failure_recorder.py`
  - Impact: Failures now persist to Supabase `failure_memory` table for long-term knowledge base
  - Merged: 2025-12-01
- **[PR #1787](https://github.com/RC918/morningai/pull/1787)**: Sentry Error Prevention - Add defensive checks for graceful degradation
  - Path: `handoff/20250928/40_App/orchestrator/persistence/db_client.py`, `db_writer.py`, `auth_middleware.py`
  - Impact: Supabase unavailability no longer crashes the application
  - Merged: 2025-12-01
- **[PR #1785](https://github.com/RC918/morningai/pull/1785)**: Real Metrics Aggregation - Implement experiment comparison (Tier 1)
  - Path: `handoff/20250928/40_App/orchestrator/persistence/planner_events_store.py`
  - Impact: RPC-based metrics aggregation for experiment comparison
  - Migration: `migrations/030_create_planner_metrics_rpc.sql`
  - Merged: 2025-12-01
- **[PR #1784](https://github.com/RC918/morningai/pull/1784)**: Remove Stale egg-info - Fix old openai version reference
  - Path: `handoff/20250928/40_App/orchestrator/morningai_orchestrator.egg-info/` (deleted)
  - Impact: Clean up stale package metadata
  - Merged: 2025-12-01
- **[PR #1781](https://github.com/RC918/morningai/pull/1781)**: ORCHESTRATOR_DRY_RUN Flag - Skip PR creation in dry run mode
  - Path: `handoff/20250928/40_App/orchestrator/graph.py`
  - Impact: Enable testing without creating actual PRs
  - Merged: 2025-11-30
- **[PR #1780](https://github.com/RC918/morningai/pull/1780)**: OpenAI SDK Upgrade - Fix httpx 0.28 proxies compatibility
  - Path: `handoff/20250928/40_App/orchestrator/requirements.txt`
  - Impact: Resolve SDK compatibility issues
  - Merged: 2025-11-30
- **[PR #1778](https://github.com/RC918/morningai/pull/1778)**: 401 Retry Logic - Proactive token expiry check for owner-console
  - Path: `handoff/20250928/40_App/owner-console/src/lib/auth.ts`, `api-client.ts`
  - Impact: Auto-refresh token when in-memory token is lost after page reload
  - Merged: 2025-11-30

**Gemini 3 SDK Migration (Nov 29-30, 2025)**:
- **[PR #1761](https://github.com/RC918/morningai/pull/1761)**: Gemini Provider Migration - Migrate to google-genai SDK (Phase 1)
  - Path: `handoff/20250928/40_App/orchestrator/llm/providers/gemini_provider.py`
  - Impact: Use official Google GenAI SDK instead of legacy API
- **[PR #1762](https://github.com/RC918/morningai/pull/1762)**: Gemini Fallback Model Update - Change from gemini-pro to gemini-2.0-flash
  - Path: `handoff/20250928/40_App/orchestrator/llm/providers/gemini_provider.py`
  - Impact: Use latest Gemini model as fallback
- **[PR #1763](https://github.com/RC918/morningai/pull/1763)**: Gemini 3 Phase 2 - thinking_level support and new experiments
  - Path: `handoff/20250928/40_App/orchestrator/llm/providers/gemini_provider.py`, `experiment_manager.py`
  - Impact: Enable thinking_level=high for complex reasoning tasks (API parameter, not env var)
- **[PR #1765](https://github.com/RC918/morningai/pull/1765)**: Enable gemini3_planner_10pct_staging experiment
  - Path: `handoff/20250928/40_App/orchestrator/experiment_manager.py`
  - Impact: 10% staging traffic uses Gemini 3 planner

**AI Governance & Security (Nov 28-29, 2025)**:
- **[PR #1741](https://github.com/RC918/morningai/pull/1741)**: Three-tier Permission Architecture (Phase 6 PR-5)
  - Path: `handoff/20250928/40_App/api-backend/src/middleware/auth_middleware.py`
  - Migration: `migrations/028_add_platform_admin_support.sql`
  - Impact: Platform admin, tenant admin, user permission levels
- **[PR #1746](https://github.com/RC918/morningai/pull/1746)**: SECURITY_ENFORCEMENT_MODE Configuration (PR-1)
  - Path: `common/config/settings.py`, `config/env.schema.yaml`
  - Impact: Configurable security enforcement (advisory/block_critical/block_all)
- **[PR #1748](https://github.com/RC918/morningai/pull/1748)**: LangGraph Enforcement Integration (PR-2)
  - Path: `handoff/20250928/40_App/orchestrator/langgraph_orchestrator.py`
  - Impact: Security policy enforcement in LangGraph workflows
- **[PR #1749](https://github.com/RC918/morningai/pull/1749)**: Simple Mode Policy Observability (PR-3)
  - Path: `handoff/20250928/40_App/orchestrator/graph.py`
  - Impact: Policy violation logging in Simple mode
- **[PR #1751](https://github.com/RC918/morningai/pull/1751)**: Blessed Configurations Documentation (PR-4)
  - Path: `config/blessed_configs.yaml`
  - Impact: Documented approved configuration combinations
- **[PR #1753](https://github.com/RC918/morningai/pull/1753)**: Config Validation Script and CI (PR-5)
  - Path: `scripts/validate_blessed_configs.py`, `.github/workflows/validate-blessed-configs.yml`
  - Impact: CI validation of configuration against blessed configs

**CI/CD Improvements (Nov 28-29, 2025)**:
- **[PR #1756](https://github.com/RC918/morningai/pull/1756)**: Unified Migration Runner (PR-6)
  - Path: `scripts/run_migrations.sh`
  - Impact: Single script for running all migrations
- **[PR #1757](https://github.com/RC918/morningai/pull/1757)**: Migration Health Check CI (PR-7)
  - Path: `.github/workflows/migration-health-check.yml`
  - Impact: CI workflow to validate migration health
- **[PR #1767](https://github.com/RC918/morningai/pull/1767)**: Coverage Trend Tracking
  - Path: `.github/workflows/coverage-trend.yml`
  - Impact: Track coverage trends over time
- **[PR #1766](https://github.com/RC918/morningai/pull/1766)**: Migration 029 - Fix Security Advisor warnings
  - Path: `migrations/029_fix_reputation_security_warnings.sql`
  - Impact: Fix reputation system security warnings

**Documentation (Nov 29, 2025)**:
- **[PR #1759](https://github.com/RC918/morningai/pull/1759)**: Gemini 3 Integration Design Document
  - Path: `docs/gemini3_integration.md`
  - Impact: Comprehensive design document for Gemini 3 integration
- **[PR #1760](https://github.com/RC918/morningai/pull/1760)**: /config/summary Endpoint (PR-10)
  - Path: `handoff/20250928/40_App/api-backend/src/routes/experiments.py`
  - Impact: Configuration visibility endpoint

**Previous Improvements (Nov 25-26, 2025)**:
- **[PR #1548](https://github.com/RC918/morningai/pull/1548)**: Frontend Dashboard Code Splitting - 20% bundle reduction + Lighthouse CI color-contrast fix
  - Path: `handoff/20250928/40_App/frontend-dashboard/`
  - Impact: Improved performance and accessibility compliance
- **[PR #1562](https://github.com/RC918/morningai/pull/1562)**: RQ Job Timeout Configuration - Added `RQ_JOB_TIMEOUT` environment variable
  - Path: `handoff/20250928/40_App/orchestrator/redis_queue/worker.py`, `config/env.schema.yaml`
  - Impact: Configurable job timeout for long-running tasks (default: 3600s)

**Previous Improvements (Nov 18-23, 2025)**:
- **[PR #1350](https://github.com/RC918/morningai/pull/1350)**: E2E Testing Infrastructure - Fixed 21 failing tests, implemented route handler isolation, added comprehensive API mocking
  - Path: `handoff/20250928/40_App/owner-console/e2e/`
  - Result: 32 E2E tests passing (11→32), 55/55 CI checks passing
- **[PR #1398](https://github.com/RC918/morningai/pull/1398)**: Production Path Discovery - Replaced hardcoded repo path with 4-layer fallback mechanism
  - Path: `handoff/20250928/40_App/orchestrator/context_manager.py`
  - Added: `MORNINGAI_REPO_PATH` environment variable for production/staging
- **[PR #1399](https://github.com/RC918/morningai/pull/1399)**: Backend Test Environment - Unified Python 3.12, added Redis service, fixed PyJWT conflicts
  - Path: `.github/workflows/test-apps.yml`
  - Result: Backend tests now consistent across all CI workflows
- **[PR #1480](https://github.com/RC918/morningai/pull/1480)**: Pydantic Alias System - Added 23 critical environment variable aliases (Nov 23)
  - Path: `common/config/settings.py`
  - Fixed: `FLASK_SECRET_KEY`, `ENCRYPTION_MASTER_KEY`, `STRIPE_WEBHOOK_SECRET_KEY` aliases
  - Impact: Backward compatibility improvements, standardized configuration naming
- **[PR #1452](https://github.com/RC918/morningai/pull/1452)**: Redis Mapping Sanitization - Prevent NoneType DataError (Nov 23)
  - Path: `handoff/20250928/40_App/orchestrator/redis_queue/worker.py`
  - Added: `sanitize_redis_mapping()` function to filter None values
  - Impact: Improved worker heartbeat and task status update stability
- **[PR #1455](https://github.com/RC918/morningai/pull/1455)**: AgentExecutionLogs Accessibility Fixes - Resolved 6 critical a11y violations (Nov 23)
  - Path: `handoff/20250928/40_App/owner-console/src/components/AgentExecutionLogs.tsx`
  - Fixed: Pagination controls, table headers, ARIA labels
  - Impact: Enhanced Owner Console accessibility standards
- **[PR #1437](https://github.com/RC918/morningai/pull/1437)**: i18n Error Fixes - Fixed 10 i18n errors in owner-console (Nov 23)
  - Path: `handoff/20250928/40_App/owner-console/src/components/`
  - Enabled: ESLint blocking to prevent future i18n regressions
  - Impact: Improved internationalization quality and consistency

### Key Features

**Infrastructure & Security (Completed):**
- ✅ **RLS Implementation**: Row-level security with 70 policies across 6 migrations
- ✅ **Secret Scanning**: Gitleaks + TruffleHog in CI, blocks PRs with secrets
- ✅ **2FA**: Complete TOTP implementation with 10 components, enforced login
- ✅ **Storybook**: Owner Console with MSW, dark mode, a11y checks
- ✅ **E2E Testing**: 32 Playwright tests with route handler isolation and API mocking
- ✅ **CI/CD**: Unified backend test environment (Python 3.12, Redis service, 74%+ coverage)

**AI Agents (In Development):**
- **Dev_Agent**: Automated bug fixing and PR creation (target: >85% success rate)
- **Ops_Agent**: Automated incident response and self-healing (target: >70% automation)
- **PM_Agent**: Project management and task tracking
- **Growth_Strategist**: Business strategy and optimization
- **Meta_Agent**: Agent orchestration and OODA loop coordination

**Note**: Agent success rates are aspirational targets. Evaluation harness created but not yet integrated. See [Agent Evaluation Guide](../tools/agent_eval/README.md).

---

## Environment Architecture

MorningAI uses a multi-environment deployment architecture to ensure safe development, testing, and production workflows.

### 🚀 Production Environment

**Services**:
- **Backend API**: https://morningai-backend-v2.onrender.com
- **Orchestrator API**: https://morningai-orchestrator-api.onrender.com
- **Frontend**: https://morningai.vercel.app

⚠️ **Orchestrator Architecture (Dual System)**

MorningAI uses a producer-consumer architecture with two orchestrator implementations:

| Component | Role | Maturity | Service | Path |
|-----------|------|----------|---------|------|
| **API Orchestrator** | API Layer (FastAPI) | Beta | `morningai-orchestrator-api` | `orchestrator/` |
| **Worker Orchestrator** | Task Execution (RQ) | Production | `morningai-agent-worker` | `handoff/20250928/40_App/orchestrator/` |

**Execution Mode**:
- **LangGraph Mode** (Production): `handoff/20250928/40_App/orchestrator/langgraph_orchestrator.py` - Full state machine with retry logic, CI monitoring, PostgreSQL checkpointing
- **Core Executor**: `handoff/20250928/40_App/orchestrator/graph.py` - Shared execution logic called by LangGraph nodes

**See**: [ADR-005](adr/005-deprecate-simple-orchestrator-mode.md), [ADR-002](adr/002-producer-consumer-architecture.md), [ADR-004](adr/004-shared-core-executor-pattern.md)

**Infrastructure**:
- **Database**: Supabase PostgreSQL (production)
- **Redis**: Upstash (TLS enabled)
- **Branch**: `main`
- **Auto-Deploy**: Yes

### 🧪 Staging Environment ✅

**Services**:
- **Backend API**: https://morningai-backend-v2-stg.onrender.com
- **Orchestrator API**: https://morningai-orchestrator-api-stg.onrender.com
- **Frontend (Dashboard)**: https://staging.morningai.me
- **Frontend (Owner Console)**: https://staging-owner.morningai.me

**Infrastructure**:
- **Database**: Supabase PostgreSQL (staging: dckisglnlemvpvmyvnut)
- **Redis**: Upstash (shared, key prefix: `stg:`)
- **Branch**: `main` (with `ENVIRONMENT=staging` for backend services)
- **Auto-Deploy**: Yes
- **Status**: ✅ Fully Operational

> **Note**: This project uses a trunk-based development model. There is no persistent `develop` branch. Staging is handled via Render backend services (deploying from `main` with staging env vars) and Vercel preview deployments.

**Frontend Deployment** (Vercel):
- **Branch Policy**: `main` → production, `feature/*|fix/*|devin/*` → preview
- **Ignore Script**: Skips deployment for docs-only changes
- **Documentation**: [docs/deployment/VERCEL_DEPLOYMENT_STRATEGY.md](../deployment/VERCEL_DEPLOYMENT_STRATEGY.md)

**Purpose**:
- Pre-production testing
- Integration testing
- Feature validation before production

### 💻 Local Development

**Services**:
- **Backend**: `http://localhost:8000`
- **Orchestrator**: `http://localhost:8001`
- **Frontend**: `http://localhost:5173`

**Infrastructure**:
- **Database**: Local PostgreSQL or Staging Supabase
- **Redis**: Local Redis or Staging Redis

### Deployment Flow (Trunk-Based)

```
Feature Branch → PR → main (Production)
                ↓
         Preview Deploy (Staging Test)
```

**Detailed Documentation**: [docs/ENVIRONMENTS.md](ENVIRONMENTS.md)

---

## Orchestrator Architecture

> **重要**: Simple Mode 已於 2025-12-15 移除，LangGraph 是唯一的執行模式。詳見 [ADR-005](adr/005-deprecate-simple-orchestrator-mode.md)。

### Overview: LangGraph Single Mode Architecture

MorningAI's orchestrator uses **LangGraph as the sole execution engine** (100% rollout completed 2025-12-14). All tasks flow through the LangGraph state machine.

```
┌─────────────────────────────────────────────────────────────┐
│ HTTP Request: POST /faq                                      │
│ Body: {"question": "..."}                                    │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│ API Backend (agent.py)                                       │
│ - Generate task_id = UUID()                                 │
│ - Enqueue: run_orchestrator_task(task_id, question, repo)  │
│ - Return 202 Accepted                                       │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│ Redis Queue (orchestrator)                                   │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│ Worker (worker.py) → LangGraph Orchestrator                  │
│                                                              │
│ All tasks use LangGraph (Simple Mode removed #2651)         │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│ LangGraph StateGraph (12 nodes)                              │
│                                                              │
│   planner_node → executor_node → ci_monitor_node            │
│        ↓              ↓               ↓                      │
│   (LLM/static)   graph.execute()   (CI check)               │
│                       ↓               ↓                      │
│                  fixer_node ← (if CI fails)                  │
│                       ↓                                      │
│                 finalizer_node → Task Complete               │
└─────────────────────────────────────────────────────────────┘
```

### LangGraph Execution Flow

**Files**:
- Entry: `handoff/20250928/40_App/orchestrator/redis_queue/worker.py`
- Orchestrator: `handoff/20250928/40_App/orchestrator/langgraph_orchestrator.py`
- Core Executor: `handoff/20250928/40_App/orchestrator/graph.py`

**Characteristics**:
- ✅ **Stateful**: Full state machine with LangGraph StateGraph
- ✅ **Intelligent**: LLM-powered planning (when `USE_LLM_PLANNER=true`)
- ✅ **Resilient**: Retry logic, error handling, CI monitoring
- ✅ **Checkpointed**: Redis MemorySaver for pause/resume support
- ✅ **Circuit Breaker**: Automatic degradation protection

**Flow**:
```
Worker → langgraph_orchestrator.run_orchestrator()
  → planner_node (LLM or static)
  → executor_node → graph.execute()
  → ci_monitor_node
  → fixer_node (if needed)
  → finalizer_node
```

### Core Executor: graph.execute()

**File**: `handoff/20250928/40_App/orchestrator/graph.py`

**What It Does**:
- Cost tracking and budget enforcement
- Rate limiting (10 PRs/hour)
- FAQ content generation with GPT-4
- Git branch creation and PR opening
- CI check monitoring
- Test mode auto-cleanup

**⚠️ Important**: Changes to `graph.execute()` affect all task types. Always test thoroughly.

### Environment Variables

| Variable | Default | Purpose |
|----------|---------|---------|
| `USE_LLM_PLANNER` | `false` | Use LLM vs static planner |
| `USE_LLM_REVIEWER` | `false` | Enable LLM-powered code review |
| `ENABLE_PROJECT_ENGINEER_FIXER` | `false` | Enable auto-fix mode |

### CI Guard: Preventing Simple Mode Reintroduction

The `simple-mode-guard.yml` workflow blocks PRs that introduce deprecated Simple Mode symbols:
- `record_simple_task` method references
- "Simple Mode" string literals (except in historical context)
- `USE_LANGGRAPH_PERCENT` / `use_langgraph_percent` settings

### Feature Flags (Implemented but Default Disabled)

The following features are fully implemented but disabled by default. Enable them via environment variables when ready:

| Flag | Default | Purpose | Status |
|------|---------|---------|--------|
| `FEATURE_2FA_PREAUTH` | `false` | Pre-auth token flow for 2FA enrollment | Implemented, requires explicit enablement |
| `USE_LLM_PLANNER` | `false` | LLM-powered task planning in LangGraph | Implemented, enable for intelligent planning |
| `USE_LLM_REVIEWER` | `false` | LLM-powered code review in LangGraph | Implemented, enable for automated review |
| `ENABLE_PROJECT_ENGINEER_FIXER` | `false` | Auto-fix mode in fixer_node | Implemented, enable for automatic CI fix attempts |
| `ENABLE_PROJECT_ENGINEER_CODEGEN` | `false` | Code generation execution mode | Implemented, enable for ProjectEngineerAgent codegen |

**Why Default Disabled?**
- These features are production-ready but require careful rollout
- Enable in staging first to validate behavior
- Gradual production rollout recommended (feature flags allow instant rollback)

**Note**: `USE_LANGGRAPH`, `USE_LANGGRAPH_PERCENT`, and `USE_LANGGRAPH_FOR_FAQ` flags were removed in Issue #2651. LangGraph is now the only orchestration mode.

### Development Guidelines

#### ✅ DO: Adding New Orchestrator Features

**Implement in LangGraph mode only**:
```python
# handoff/20250928/40_App/orchestrator/langgraph_orchestrator.py

def new_feature_node(state: AgentState) -> AgentState:
    """New orchestrator feature"""
    # Your implementation here
    return state

# Add to workflow
workflow.add_node("new_feature", new_feature_node)
workflow.add_edge("planner", "new_feature")
```

**Why**: All orchestrator logic should be in LangGraph nodes for proper state management.

#### ✅ DO: Modifying Shared Executor

**When changing `graph.execute()`**:
1. Test thoroughly with LangGraph mode
2. Add tests in `test_graph.py` AND `test_langgraph_ci.py`
3. **Clearly state in PR description**: "This change affects the core executor"

**Example PR description**:
```markdown
## Changes to Shared Executor

This PR modifies `graph.execute()` which is called by LangGraph executor_node.

**Testing**: Verified in staging.
```

#### ❌ DON'T: Bypass LangGraph State Management

**Bad assumption**: "I'll just add logic directly to graph.execute()"

**Good practice**: "I'll add a new LangGraph node for this feature"

### Monitoring & Observability

**Orchestrator Logs** (search in Render Dashboard):
```
"Using LangGraph orchestrator" # LangGraph execution
"Using LLM planner"           # LLM planner selection
"node_complete"               # Node execution metrics
```

**Metrics** (`worker.py`):
```python
metrics.record_node_complete(node_name, trace_id, success, latency_ms)
```

**Structured Logging**:
```json
{
  "operation": "langgraph_execution",
  "task_id": "...",
  "node_name": "planner_node",
  "latency_ms": 1234
}
```

### Current Architecture Status

**LangGraph 100% Rollout Complete** (Dec 2025):
- LangGraph is now the only orchestration mode (Issue #2651)
- Simple Mode code has been removed (PR #2767)
- `USE_LANGGRAPH`, `USE_LANGGRAPH_PERCENT` flags removed from settings.py
- CI Guard (`simple-mode-guard.yml`) prevents reintroduction of deprecated code

**Current Configuration**:
| 服務 | USE_POSTGRES_CHECKPOINTER | USE_LLM_PLANNER | USE_LLM_REVIEWER |
|------|---------------------------|-----------------|------------------|
| Production Worker | `true` | `false` | `false` |
| Staging Worker | `true` | `false` | `false` |

查看位置: Render Dashboard → Service → Environment Tab

**Multi-Model Routing** (EPIC #2594):
- Routing Policy v1.2 with Cross-Generation Fallback
- See: [Routing Policy Documentation](./ROUTING_POLICY.md)

**Future Roadmap** (Q1-Q2 2026):
- 🎯 Enable `USE_LLM_PLANNER` for intelligent task planning
- 🎯 Enable `USE_LLM_REVIEWER` for automated code review
- 🎯 Refactor `graph.py`:
  - **Option A** (Recommended): Rename to `core_executor.py`, keep only `execute()` function
  - **Option B**: Integrate executor logic into `langgraph_orchestrator.py`, remove `graph.py`
- 🎯 Update all documentation and tests

### Testing Both Modes

**Local Testing**:
```bash
# Test Simple mode
export USE_LANGGRAPH=false
export USE_LANGGRAPH_PERCENT=0
python -m pytest tests/test_graph.py

# Test LangGraph mode
export USE_LANGGRAPH=true
export USE_LLM_PLANNER=false  # Use static planner for faster tests
python -m pytest tests/test_langgraph_ci.py

# Test canary routing
export USE_LANGGRAPH=false
export USE_LANGGRAPH_PERCENT=50
python -m pytest tests/test_worker.py::TestCanaryDeployment
```

**Staging Testing**:
```bash
# Check current routing distribution
# In Render Dashboard → Worker Logs (see STAGING_SETUP_GUIDE.md for service names)
# Search: "Canary deployment"

# Expected: ~5% show use_langgraph=True, ~95% show use_langgraph=False
```

### Running LangGraph E2E Tests

The LangGraph E2E tests verify the fixer_node integration, AutoFixer canary rollout, safety rules enforcement, and async wrapper optimization. These tests are located in `handoff/20250928/40_App/orchestrator/tests/test_langgraph_fixer_e2e.py`.

**Prerequisites**:
- Python 3.12+ with virtual environment activated
- PYTHONPATH configured to include orchestrator and api-backend paths

**Running All E2E Tests**:
```bash
cd ~/repos/morningai
source .venv/bin/activate
export PYTHONPATH="$PWD/handoff/20250928/40_App/orchestrator:$PWD/handoff/20250928/40_App/api-backend/src:$PYTHONPATH"
pytest handoff/20250928/40_App/orchestrator/tests/test_langgraph_fixer_e2e.py -v
```

**Running Specific Test Classes**:
```bash
# Fixer node routing tests
pytest handoff/20250928/40_App/orchestrator/tests/test_langgraph_fixer_e2e.py::TestFixerNodeRouting -v

# AutoFixer canary rollout tests
pytest handoff/20250928/40_App/orchestrator/tests/test_langgraph_fixer_e2e.py::TestAutoFixerCanaryRollout -v

# Safety rules enforcement tests
pytest handoff/20250928/40_App/orchestrator/tests/test_langgraph_fixer_e2e.py::TestSafetyRulesEnforcement -v

# Async wrapper optimization tests
pytest handoff/20250928/40_App/orchestrator/tests/test_langgraph_fixer_e2e.py::TestAsyncWrapperOptimization -v

# Logging and observability tests
pytest handoff/20250928/40_App/orchestrator/tests/test_langgraph_fixer_e2e.py::TestLoggingAndObservability -v

# Smoke tests for full graph execution
pytest handoff/20250928/40_App/orchestrator/tests/test_langgraph_fixer_e2e.py::TestSmokeTestGraphExecution -v
```

**Test Coverage Summary**:
- **TestFixerNodeRouting**: Verifies fixer_node is in the graph and routing logic works correctly
- **TestFixerNodeBehavior**: Tests retry count increment, max retries, AutoFixer integration
- **TestAutoFixerCanaryRollout**: Tests canary deployment with deterministic bucket assignment
- **TestMaxRetriesEnforcement**: Ensures MAX_FIXER_RETRIES constant is used consistently
- **TestStateTransitions**: Verifies state preservation and message handling
- **TestOrchestratorWorkflowPaths**: Tests workflow paths (success, failure, fixer, max retries)
- **TestErrorRecovery**: Tests error recovery from AutoFixer errors and missing settings
- **TestLoggingAndObservability**: Tests structured logging with autofixer_disabled_reason
- **TestSafetyRulesEnforcement**: Verifies whitelist enforcement and codegen flag respect
- **TestAsyncWrapperOptimization**: Tests async-to-sync bridging with thread-safe executor
- **TestRealIntegrationScenarios**: Tests GitHub API errors, CI failures, PR creation failures
- **TestConstantSynchronization**: Ensures MAX_FIXER_RETRIES is synchronized across all logic
- **TestSmokeTestGraphExecution**: Verifies full graph compilation and routing functions

**Related Environment Variables**:
```bash
# Enable/disable AutoFixer
ENABLE_PROJECT_ENGINEER_FIXER=true

# Canary percentage (0-100)
PROJECT_ENGINEER_FIXER_PERCENT=5

# Enable code generation (required for AutoFixer to run)
ENABLE_PROJECT_ENGINEER_CODEGEN=true
```

### Common Pitfalls

1. **❌ Modifying `graph.py` without testing LangGraph**
   - `graph.execute()` is called by LangGraph executor_node!

2. **❌ Bypassing LangGraph state management**
   - All orchestrator features should be implemented as LangGraph nodes.

3. **❌ Searching for wrong log keywords**
   - Use "node_complete" for node execution metrics

### Quick Reference

**Files to Know**:
```
handoff/20250928/40_App/orchestrator/
├── redis_queue/worker.py            # Worker entry point
├── graph.py                         # Core executor (called by LangGraph)
├── langgraph_orchestrator.py        # LangGraph state machine
├── core/routing/routing_policy.json # Multi-model routing config
├── core/routing/engine.py           # Routing engine
└── tests/
    ├── test_graph.py                # Core executor tests
    ├── test_langgraph_ci.py         # LangGraph tests
    └── test_worker.py               # Worker tests
```

**Architecture**:
- **LangGraph Mode**: Production orchestration with state machine
- **Core Executor**: Shared execution logic called by LangGraph nodes
- **Routing Engine**: Multi-model LLM selection based on task_type/risk_level

**Questions?** See Orchestrator ADRs ([ADR-005](adr/005-deprecate-simple-orchestrator-mode.md), [ADR-002](adr/002-producer-consumer-architecture.md), [ADR-004](adr/004-shared-core-executor-pattern.md)) or ask in #engineering.

---

## Getting Started

### Prerequisites

**Required**:
- **Git**: Version control
- **Python**: 3.12+ (for backend and orchestrator)
- **Node.js**: 20+ (for frontend)
- **pnpm**: 9.15.1+ (package manager)
- **Docker**: For orchestrator development (optional)

**Recommended**:
- **VS Code**: IDE with Python and TypeScript extensions
- **PostgreSQL**: Local database (or use staging)
- **Redis**: Local cache (or use staging)

### Step 1: Clone Repository

```bash
git clone https://github.com/RC918/morningai.git
cd morningai
```

### Step 2: Set Up Python Environment

```bash
# Create virtual environment
python3 -m venv .venv

# Activate virtual environment
source .venv/bin/activate  # On macOS/Linux
# or
.venv\Scripts\activate  # On Windows

# Install dependencies
pip install -r requirements.txt
```

### Step 3: Set Up Frontend Environment

```bash
cd handoff/20250928/40_App/frontend-dashboard

# Install dependencies
pnpm install

# Return to root
cd ../../../..
```

### Step 4: Configure Environment Variables

**Environment Schema Workflow** (Single Source of Truth):

MorningAI uses `config/env.schema.yaml` as the canonical source for all environment variables. This ensures consistency across all services and environments.

```bash
# 1. View canonical environment variable definitions
cat config/env.schema.yaml

# 2. Generate .env.example files from schema (auto-updates all services)
python scripts/generate-env-examples.py

# 3. Check for drift between schema and .env.example files
python scripts/check-env-drift.py

# 4. Verify secret inventory matches schema (security operations)
python scripts/verify_secret_inventory.py  # (Added in [PR #1084](https://github.com/RC918/morningai/pull/1084))
```

**Key Points**:
- ✅ Always update `config/env.schema.yaml` first when adding/changing variables
- ✅ Run `generate-env-examples.py` to propagate changes to all `.env.example` files
- ✅ CI automatically checks for drift on every PR
- ✅ See [Secret Rotation Policy](./SECRET_ROTATION_POLICY.md) for security operations

**Recent Additions ([PR #1398](https://github.com/RC918/morningai/pull/1398))**:
- `MORNINGAI_REPO_PATH`: Repository root path for production/staging environments
  - Required in Render.com deployments: `/opt/render/project/src`
  - Falls back to git detection or marker-based discovery in development
  - Path: `config/env.schema.yaml` (Deployment category)

**Backend** (`handoff/20250928/40_App/api-backend/.env`):
```bash
ENVIRONMENT=development
DATABASE_URL=postgresql://localhost:5432/morningai
REDIS_URL=redis://localhost:6379/0

# Or use staging infrastructure (recommended)
DATABASE_URL=<staging-database-url>
REDIS_URL=<staging-redis-url>
REDIS_KEY_PREFIX=dev:
```

**Frontend Dashboard** (`handoff/20250928/40_App/frontend-dashboard/.env.local`):
```bash
VITE_API_URL=http://localhost:8000
VITE_ORCHESTRATOR_URL=http://localhost:8001
VITE_ENVIRONMENT=development

# Or point to staging backend (recommended)
VITE_API_URL=https://morningai-backend-v2-stg.onrender.com
VITE_ORCHESTRATOR_URL=https://morningai-orchestrator-api-stg.onrender.com
```

**Owner Console** (`handoff/20250928/40_App/owner-console/.env.local`):
```bash
VITE_API_URL=http://localhost:8000
VITE_ENVIRONMENT=development

# Or point to staging backend (recommended)
VITE_API_URL=https://morningai-backend-v2-stg.onrender.com
```

**Note**: Contact your team lead for staging credentials. See `config/env.schema.yaml` for complete list of all environment variables.

### Step 5: Run Services Locally

**Backend** (Flask):
```bash
cd handoff/20250928/40_App/api-backend
source ../../../../../../.venv/bin/activate

# Option 1: Flask CLI (recommended for development)
export FLASK_APP=src.main
flask run --port 8000

# Option 2: Gunicorn (production-like)
gunicorn "src.main:app" --bind 0.0.0.0:8000 --reload

# Access at http://localhost:8000
```

**Orchestrator**:
```bash
cd orchestrator
source ../.venv/bin/activate
uvicorn orchestrator.api.main:app --port 8001 --reload
# Access at http://localhost:8001
```

**Frontend**:
```bash
cd handoff/20250928/40_App/frontend-dashboard
pnpm dev
# Access at http://localhost:5173
```

### Step 6: Verify Setup

**Test Backend**:
```bash
curl http://localhost:8000/healthz
# Should return: {"status": "healthy", ...}
```

**Test Orchestrator**:
```bash
curl http://localhost:8001/health
# Should return: {"status": "healthy", ...}
```

**Test Frontend**:
- Open http://localhost:5173 in browser
- Should see MorningAI dashboard

### Step 7: Run Storybook (Optional)

**Owner Console**:
```bash
cd handoff/20250928/40_App/owner-console
pnpm storybook
# Access at http://localhost:6007
```

**Features**:
- MSW addon for API mocking with wildcard host matching
- Dark mode toggle in toolbar (synced with next-themes)
- Test runner with a11y checks: `pnpm test-storybook`
- 13 stories covering SystemMonitoring and AgentExecutionLogs

**Adding MSW Handlers:**
```typescript
export const MyStory = {
  parameters: {
    msw: {
      handlers: [
        http.get('*/api/your-endpoint', () => {
          return HttpResponse.json({ data: 'mock response' });
        }),
      ],
    },
  },
};
```

**Shared UI Components**:
```bash
cd packages/shared-ui
pnpm storybook
# Access at http://localhost:6006
```

**What is Storybook?**
- Interactive component documentation and testing environment
- View and test UI components in isolation
- Added November 2025 (Storybook 8.6.14)
- Core components documented in `packages/shared-ui` (Card, Button, Badge, Alert, Avatar, Progress, Tabs, Dialog, Input, Form, Table, Pagination, Select, StatusBadge)

**Adding New Stories:**
1. Create `*.stories.tsx` file next to your component
2. Follow existing patterns in `packages/shared-ui/src/components/ui/*.stories.tsx`
3. Stories are automatically discovered by Storybook

**Documentation:** See [Storybook Documentation](https://storybook.js.org/docs/react/get-started/introduction)

---

## Development Workflow

### Branch Strategy (Trunk-Based)

```
main (production)
  ↑
feature/your-feature (development) → PR → main
                                     ↓
                              Preview Deploy (Staging Test)
```

> **Note**: This project uses a trunk-based development model. There is no persistent `develop` branch.

### Creating a Feature

```bash
# 1. Start from main
git checkout main
git pull origin main

# 2. Create feature branch
git checkout -b feature/your-feature-name

# 3. Make changes and commit
git add .
git commit -m "feat: add your feature"

# 4. Push to remote
git push origin feature/your-feature-name

# 5. Create PR to main
# Go to GitHub and create Pull Request to main branch
# Vercel will create a preview deployment for testing
```

### Testing on Staging

```bash
# 1. Create PR to main
# Vercel creates preview deployment for frontend testing
# Backend staging: https://morningai-backend-v2-stg.onrender.com

# 2. Test on staging backend
curl https://morningai-backend-v2-stg.onrender.com/healthz

# 3. Test frontend via Vercel preview URL
```

### Deploying to Production

```bash
# 1. Get PR approval and merge to main
# GitHub Actions will automatically deploy to production

# 2. Monitor production deployment
curl https://morningai-backend-v2.onrender.com/healthz
```

### PR Guidelines

**Design PRs** (UI/copy/styles only):
- Cannot include API/logic changes
- Enforced by `pr-guard.yml` workflow

**Engineering PRs** (API/logic only):
- Cannot include UI/copy/styles changes
- Enforced by `pr-guard.yml` workflow

**RFC Required** for:
- OpenAPI/schema changes
- Database schema changes
- Breaking changes

**Template**: [.github/ISSUE_TEMPLATE/rfc.md](../.github/ISSUE_TEMPLATE/rfc.md)

---

## Key Technologies

### Backend

- **Framework**: Flask (Python 3.12)
- **Database**: PostgreSQL (Supabase)
- **ORM**: SQLAlchemy
- **Cache**: Redis (Upstash)
- **Task Queue**: RQ (Redis Queue)
- **Testing**: pytest, pytest-cov
- **Deployment**: Render (Web Services)

### Orchestrator

- **Framework**: FastAPI (Python 3.12)
- **Task Management**: Graph-based orchestration
- **Sandbox**: Docker containers on Fly.io
- **MCP**: Management Control Plane
- **Deployment**: Render (Docker)

### Frontend

- **Framework**: React 19.1.0 + Vite 6
- **Language**: TypeScript 5.9
- **Styling**: Tailwind CSS 4.1.7 + Custom Design System
- **State Management**: React Context + Hooks
- **UI Components**: Apple-inspired design system
- **Testing**: Vitest + React Testing Library (planned)
- **Deployment**: Vercel

### Infrastructure

- **Database**: Supabase PostgreSQL
- **Cache**: Upstash Redis
- **Hosting**: Render (backend), Vercel (frontend), Fly.io (sandboxes)
- **CI/CD**: GitHub Actions
- **Monitoring**: Sentry
- **Version Control**: Git + GitHub

---

## Project Structure

```
morningai/
├── .github/                          # GitHub configuration
│   ├── workflows/                    # CI/CD workflows
│   │   ├── backend.yml              # Backend CI
│   │   ├── frontend.yml             # Frontend CI
│   │   ├── staging-deploy.yml       # Staging deployment
│   │   └── ...                      # 15+ workflows
│   └── ISSUE_TEMPLATE/              # Issue templates (RFC, etc.)
│
├── agents/                          # AI Agent implementations
│   ├── dev_agent.py                # Bug fixing agent
│   ├── ops_agent.py                # Operations agent
│   ├── pm_agent.py                 # Project management agent
│   ├── growth_strategist.py        # Business strategy agent
│   └── meta_agent_decision_hub.py  # Agent orchestration
│
├── orchestrator/                    # Task orchestration system
│   ├── api/                        # FastAPI application
│   │   ├── main.py                 # Application entry point
│   │   └── auth.py                 # Authentication
│   ├── task_queue/                 # Redis queue management
│   │   └── redis_queue.py          # Queue implementation
│   ├── Dockerfile                  # Docker configuration
│   └── requirements.txt            # Python dependencies
│
├── phase4_meta_agent_api.py       # Phase 4 API (imported by backend)
├── phase5_data_intelligence_api.py # Phase 5 API (imported by backend)
├── phase6_security_governance_api.py # Phase 6 API (imported by backend)
├── phase6_startup.py              # Phase 6 initialization
├── phase7_startup.py              # Phase 7 initialization
│
├── handoff/20250928/40_App/
│   ├── api-backend/                # Backend API
│   │   ├── src/                    # Source code
│   │   │   ├── main.py            # Flask application (imports phase*.py)
│   │   │   ├── database.py        # Database connection
│   │   │   └── ...                # API modules
│   │   ├── tests/                 # Test suite
│   │   └── requirements.txt       # Python dependencies
│   │
│   ├── frontend-dashboard/         # Frontend application
│   │   ├── src/                   # Source code
│   │   │   ├── App.tsx           # Main application
│   │   │   ├── components/       # React components
│   │   │   └── ...               # Frontend modules
│   │   ├── package.json          # Node.js dependencies
│   │   └── vite.config.ts        # Vite configuration
│   │
│   └── owner-console/             # Owner management console
│       ├── src/components/AgentExecutionLogs.tsx  # Agent execution history (added Nov 2025)
│       ├── src/pages/AgentGovernance.jsx          # Agent governance dashboard
│       └── ...                    # Owner console files
│
**Owner Console Features** (Admin Interface):
- **Agent Governance** (`/governance`) - Agent reputation, permissions, violations
- **Agent Execution Logs** (`/governance` → Execution Logs tab) - **NEW Nov 2025**
  - Detailed task execution history with status, timestamps, and trace IDs
  - Filter by agent type, status, and time range
  - API endpoint: `GET /api/admin/agent-execution-logs`
- **Tenant Management** (`/tenants`) - Multi-tenant account management
- **System Monitoring** (`/monitoring`) - System health and metrics

├── docs/                           # Documentation
│   ├── ENVIRONMENTS.md            # Environment architecture
│   ├── ops/
│   │   └── STAGING_SETUP_GUIDE.md # Staging setup guide
│   ├── ARCHITECTURE.md            # System architecture
│   ├── CONTRIBUTING.md            # Contribution guidelines
│   ├── setup_local.md             # Local setup guide
│   └── ...                        # 50+ documentation files
│
├── config/
│   └── env.schema.yaml            # Environment variable schema
│
├── .env.example                   # Environment variables template
├── requirements.txt               # Root Python dependencies
├── package.json                   # Root Node.js configuration
└── README.md                      # Project overview
```

**Detailed Structure**: See [PROJECT_STRUCTURE_REPORT.md](PROJECT_STRUCTURE_REPORT.md)

### Phase API Modules (Root Directory)

**Status**: ✅ **Intentional Cross-Cutting Architecture**

The following 18 production backend modules are located in the root directory as cross-cutting concerns:

**Core Managers**:
- **`persistent_state_manager.py`** (495 lines): State management across services
- **`security_manager.py`** (364 lines): Security operations and governance
- **`knowledge_graph_manager.py`** (1,018 lines): Knowledge graph operations

**Phase API Modules**:
- **`phase4_meta_agent_api.py`** (16,874 bytes): Meta-agent coordination (OODA loop, AI governance)
- **`phase5_data_intelligence_api.py`** (21,472 bytes): Data intelligence (QuickSight, growth marketing, BI dashboards)
- **`phase6_security_governance_api.py`** (18,234 bytes): Security & governance (Zero Trust, SecurityReviewer Agent, HITL analysis)
- **`phase6_startup.py`**, **`phase7_startup.py`**: Phase initialization

**Import Evidence**: These modules are actively imported in:
- `handoff/20250928/40_App/api-backend/src/main.py` (main application)
- `handoff/20250928/40_App/api-backend/tests/` (16+ test files)
- `handoff/20250928/40_App/orchestrator/` (orchestrator services)

**Architecture Rationale**: Root-level placement enables shared access across multiple services (api-backend, orchestrator, agents) without circular dependencies. This is an intentional design pattern for cross-cutting concerns, not a code organization issue.

---

## Important Documentation

### Core Documentation

- **[Project Structure Report](./PROJECT_STRUCTURE_REPORT.md)**: Comprehensive overview of repository structure
- **[Environments Guide](./ENVIRONMENTS.md)**: Environment architecture and deployment
- **[Contributing Guide](./CONTRIBUTING.md)**: Contribution guidelines and workflows
- **[Terminology Standards](./TERMINOLOGY.md)**: Standardized application names and user types

### Security & Operations

- **[Secret Rotation Policy](./SECRET_ROTATION_POLICY.md)**: Quarterly secret rotation procedures, SLOs, and drills
- **[Secret Scanning Guide](./SECRET_SCANNING_GUIDE.md)**: Prevention of secret exposure in code
- **[Test Coverage Improvement Plan](./TEST_COVERAGE_IMPROVEMENT_PLAN.md)**: 12-week roadmap to 60%+ coverage

### Quick Reference

**Environment Schema Operations**:
```bash
# Generate .env.example files from schema
python scripts/generate-env-examples.py

# Check for drift
python scripts/check-env-drift.py

# Verify secret inventory
python scripts/verify_secret_inventory.py
```

**Testing & Coverage**:
```bash
# Backend tests with coverage
cd handoff/20250928/40_App/api-backend
pytest --cov=src --cov-report=term-missing

# Frontend tests with coverage
cd handoff/20250928/40_App/frontend-dashboard
pnpm test:coverage
```

### Getting Started
- **[Local Setup Guide](setup_local.md)** - Quick start and troubleshooting
- **[Environment Architecture](ENVIRONMENTS.md)** - Complete environment documentation
- **[Staging Setup Guide](ops/STAGING_SETUP_GUIDE.md)** - Staging environment setup

### Development
- **[Contributing Guidelines](CONTRIBUTING.md)** - Development rules and workflows
- **[CI/CD Matrix](ci_matrix.md)** - GitHub Actions workflows
- **[Environment Variables](config/env_schema.md)** - Configuration documentation

### Architecture
- **[System Architecture](ARCHITECTURE.md)** - Overall system design
- **[Agent Sandbox Architecture](agent-sandbox-architecture.md)** - Sandbox design
- **[Governance Framework](GOVERNANCE_FRAMEWORK.md)** - Multi-agent governance

### UI/UX
- **[UI/UX Quick Start](UI_UX_QUICKSTART.md)** - 5-minute quick start
- **[UI/UX Cheat Sheet](UI_UX_CHEATSHEET.md)** - One-page reference
- **[UI/UX Resources](UI_UX_RESOURCES.md)** - Design system resources

### Security
- **[Redis Security](REDIS_SECURITY.md)** - Redis security requirements
- **[RLS Implementation](RLS_IMPLEMENTATION_GUIDE.md)** - Row-level security
- **[Secret Scanning](SECRET_SCANNING_GUIDE.md)** - Secret management
- **[Authentication API](openapi.auth.yaml)** - 2FA/TOTP endpoints (OpenAPI 3.0.3)

### Testing
- **[Testing Guide](TESTING.md)** - Comprehensive testing documentation
- **[Phase 3 Testing](PHASE3_TESTING_GUIDE.md)** - Phase 3 testing guide

#### Visual Regression Testing (VRT)

**Status:** ✅ Re-enabled November 2025 ([PR #1288](https://github.com/RC918/morningai/pull/1288); related: #1287 frontend tests, #1293 Storybook test-runner)

**What is VRT?**
- Automated visual comparison of UI screenshots
- Detects unintended visual changes
- Uses Playwright for browser automation

**Running VRT Tests:**
```bash
cd handoff/20250928/40_App/frontend-dashboard

# Run VRT tests
pnpm test:vrt

# Update snapshots (after intentional UI changes)
pnpm test:vrt --update-snapshots
```

**CI Integration:**
- VRT runs automatically on PRs via `.github/workflows/frontend.yml`
- Snapshots stored in `tests/vrt.spec.ts-snapshots/`
- Failures indicate visual regressions - review carefully before updating

**Configuration:** `playwright.config.ts` - VRT-specific settings

**Troubleshooting:**
- If VRT fails after intentional UI changes, update snapshots locally and commit
- Ensure consistent browser/OS for snapshot generation (CI uses Ubuntu + Chromium)

---

## Observability & Monitoring

### Monitoring Dashboard v2

MorningAI provides a real-time monitoring dashboard with intelligent degradation handling and graceful fallback behavior. The dashboard displays system health, metrics, and alerts with explicit markers when services are unavailable.

**Key Features**:
- Real-time metrics from Redis and Database
- Graceful degradation with explicit fallback markers
- 503 Service Unavailable when both Redis and DB fail
- Public endpoint (no authentication required)

### API Endpoints

#### Primary Endpoint (Recommended)
- **Path**: `/api/phase7/monitoring/dashboard`
- **Method**: GET
- **Auth**: Public (no JWT required)
- **Status**: ✅ Production Ready
- **Documentation**: [OpenAPI Schema](../handoff/20250928/40_App/owner-console/src/lib/openapi.yaml)

#### Legacy Endpoint (Deprecated)
- **Path**: `/api/dashboard/data`
- **Method**: GET
- **Auth**: Public (no JWT required)
- **Status**: ⚠️ **DEPRECATED** - Use `/api/phase7/monitoring/dashboard` instead
- **Migration**: Update API calls to use new endpoint for real-time metrics with degradation markers

### Degradation Behavior

The monitoring dashboard implements intelligent degradation semantics:

| Scenario | HTTP Status | Response Behavior |
|----------|-------------|-------------------|
| **All services healthy** | 200 OK | Full metrics with real data from Redis and DB |
| **Redis unavailable** | 200 OK | Fallback metrics with `available: false`, `source: 'fallback'`, `error: 'Redis unavailable'` |
| **Database unavailable** | 200 OK | `overall_status: 'degraded'` with critical alert |
| **Both Redis + DB unavailable** | 503 Service Unavailable | `ServiceUnavailableError` response |

**Example Response (Normal)**:
```json
{
  "system_health": {
    "overall_status": "healthy",
    "error_rate": 0.01,
    "avg_latency": 0.15,
    "open_circuit_breakers": 0
  },
  "metrics": {
    "queue_depth": {
      "current": 5,
      "unit": "tasks",
      "trend": "stable"
    }
  },
  "agents": [],
  "alerts": []
}
```

**Example Response (Redis Degraded)**:
```json
{
  "system_health": {
    "overall_status": "healthy"
  },
  "metrics": {
    "queue_depth": {
      "current": 0,
      "unit": "tasks",
      "trend": "unknown",
      "available": false,
      "source": "fallback",
      "error": "Redis unavailable"
    }
  },
  "alerts": [
    {
      "id": "redis_error",
      "severity": "warning",
      "message": "Redis connection unavailable",
      "timestamp": "2025-11-04T16:45:58.648953"
    }
  ]
}
```

**Example Response (503 Dual Failure)**:
```json
{
  "error": "Core services unavailable",
  "message": "Both Redis and Database connections failed",
  "status": "service_unavailable",
  "request_id": "optional-trace-id"
}
```

### Error Schema

**ServiceUnavailableError** (503 responses):
```typescript
{
  error: string;        // Error message
  message?: string;     // Detailed message
  status: 'service_unavailable';
  request_id?: string;  // Optional trace ID for observability
}
```

See [OpenAPI Schema](../handoff/20250928/40_App/owner-console/src/lib/openapi.yaml) for complete API contract.

### Code Locations

**Backend Implementation**:
- **Main Route**: `handoff/20250928/40_App/api-backend/src/main.py:574` (`get_monitoring_dashboard`)
- **Core Logic**: `handoff/20250928/40_App/api-backend/src/routes/dashboard.py:35` (`get_dashboard_data`)
- **DB Health Check**: `handoff/20250928/40_App/api-backend/src/routes/dashboard.py:17` (`check_db_health`)

**Frontend & Types**:
- **OpenAPI Schema**: `handoff/20250928/40_App/owner-console/src/lib/openapi.yaml`
- **Generated Types**: `handoff/20250928/40_App/owner-console/src/lib/generated/owner-console-api.ts`
- **Type Generation**: `npm run generate:api` (uses orval)

**Tests**:
- **Integration Tests**: `handoff/20250928/40_App/api-backend/tests/test_dashboard_503_integration.py`
- **Test Seam**: `check_db_health()` function enables mocking DB failures without Flask app context issues

### Developer Workflows

**Regenerating TypeScript Types**:
```bash
cd handoff/20250928/40_App/owner-console
npm run generate:api
```

**Note**: The generated types include `@deprecated` markers for the legacy endpoint. These are manually added post-generation. If you regenerate types, ensure deprecated markers are preserved.

**Running Integration Tests**:
```bash
cd handoff/20250928/40_App/api-backend
pytest tests/test_dashboard_503_integration.py -v
```

### Environment Variables

The monitoring dashboard requires:
- `REDIS_URL`: Redis connection string (for queue metrics)
- `DATABASE_URL`: PostgreSQL connection string (for health checks)
- `BACKEND_SERVICES_AVAILABLE`: Gate flag (set by `src/main.py`)

See [Environment Variables Schema](../config/env.schema.yaml) for complete list.

### Troubleshooting

For monitoring-specific troubleshooting, see:
- **[Monitoring Troubleshooting Guide](deployment/troubleshooting-monitoring.md)** - 503 error diagnosis and recovery

**Quick Checks**:
```bash
# Test monitoring endpoint
curl https://morningai-backend-v2-stg.onrender.com/api/phase7/monitoring/dashboard

# Expected: 200 OK with metrics or 503 if both services down
```

---

## Testing

MorningAI 採用**雙層測試架構**，將單元測試和 API 整合測試分離。

### 測試架構概覽

| 層級 | 位置 | 目的 | 覆蓋率 | CI Workflow |
|------|------|------|--------|-------------|
| **層級 1** | `/tests/` | 單元測試（業務邏輯） | 21% | test-apps.yml |
| **層級 2** | `/handoff/.../api-backend/tests/` | API 整合測試 | 74% | backend.yml |

**詳細說明**: 見 [TESTING_ARCHITECTURE.md](./TESTING_ARCHITECTURE.md)

### 運行根目錄單元測試

```bash
# 在專案根目錄
pytest tests/ -v

# 帶覆蓋率
pytest tests/ --cov=src --cov-report=html

# 特定測試
pytest tests/test_utils_redis_client.py -v
```

### 運行後端 API 測試

```bash
# 1. 進入後端目錄
cd handoff/20250928/40_App/api-backend

# 2. 安裝依賴（如果還沒安裝）
pip install -r requirements.txt
pip install pytest pytest-cov

# 3. 設置環境變數
export TESTING=true
export JWT_SECRET_KEY=test-secret

# 4. 運行測試
python -m pytest tests/ -v

# 5. 帶覆蓋率
python -m pytest tests/ --cov=src --cov-report=html
```

### 為什麼測試分離？

1. **依賴隔離**: 根目錄只需最小依賴，後端需要完整依賴（Flask, rq, numpy 等）
2. **覆蓋率基準分離**: 21% 單元測試 vs 74% API 測試
3. **測試速度**: 單元測試快速（< 1 秒），API 測試較慢（1-5 秒）

**常見問題**: 見 [TESTING_ARCHITECTURE.md](./TESTING_ARCHITECTURE.md#常見問題)

---

## Common Tasks

### Running Tests

#### Backend Tests

**Prerequisites**:

The project uses **PyJWT** for JWT token handling. Make sure you have the correct package installed:

```bash
# Install PyJWT (NOT jwt==1.4.0)
pip install PyJWT
```

**Important:** Do NOT install `jwt==1.4.0` as it conflicts with PyJWT. If you have `jwt` installed, uninstall it first:

```bash
pip uninstall jwt
pip install PyJWT
```

**Running Unit Tests**:

```bash
cd handoff/20250928/40_App/api-backend
source ../../../../.venv/bin/activate

# Run all unit tests
pytest -v

# Run specific test files
pytest tests/test_middleware_auth.py -v
pytest tests/test_middleware_auth_decorators.py -v

# Run with coverage
pytest tests/test_middleware_auth*.py --cov=handoff/20250928/40_App/api-backend/src/middleware/auth_middleware.py --cov-report=term

# Run all unit tests with coverage
pytest tests/test_middleware_auth*.py tests/test_scripts_*.py --cov=src --cov-report=term --cov-report=xml --cov-report=json
```

**Test Environment Variables**:

For unit tests, set:
```bash
export TESTING=true
```

For migration idempotency tests:
```bash
export IDEMPOTENCY_TESTS_ALLOWED=true
```

**Note:** RLS tests require Supabase credentials and should not be run by default. See [DATABASE_ARCHITECTURE.md](DATABASE_ARCHITECTURE.md) for details.

**Coverage Targets**:
- **Overall**: 74% (enforced by CI)
- **Security-critical modules** (auth_middleware.py): ≥70%

**Frontend Tests**:
```bash
cd handoff/20250928/40_App/frontend-dashboard
pnpm test
```

**Coverage Report**:
```bash
pytest --cov=src --cov-report=html
# Open htmlcov/index.html in browser
```

### Linting and Formatting

**Backend**:
```bash
# Lint
flake8 .

# Format
black .
```

**Frontend**:
```bash
# Lint
pnpm lint

# Format
pnpm format
```

### Database Migrations

✅ **Alembic Migration Framework**: MorningAI uses Alembic for database schema version control and migrations.

**Quick Start**:
```bash
cd handoff/20250928/40_App/api-backend

# Run all pending migrations
alembic upgrade head

# Check current migration version
alembic current

# View migration history
alembic history --verbose

# Create new migration (auto-generate from model changes)
alembic revision --autogenerate -m "Description of changes"
```

**Helper Script**:
```bash
# Use the migration helper script
./scripts/run_alembic_migrations.sh upgrade    # Apply migrations
./scripts/run_alembic_migrations.sh current    # Check version
./scripts/run_alembic_migrations.sh history    # View history
./scripts/run_alembic_migrations.sh revision "Add new table"  # Create migration
```

**Configuration**:
- **Alembic Config**: `alembic.ini`
- **Environment Setup**: `alembic/env.py` (auto-loads DATABASE_URL from environment)
- **Migrations Directory**: `alembic/versions/`
- **Models**: `src/models/` (SQLAlchemy models)

**CI/CD Integration**:
- Migrations are automatically validated in CI against PostgreSQL
- GitHub Actions workflow: `.github/workflows/alembic-check.yml`
- Both PostgreSQL and SQLite migrations are tested

**Legacy Migrations**:
Manual SQL files in `migrations/` directory are for historical reference only. All new schema changes should use Alembic.

### Checking Service Health

**Production**:
```bash
curl https://morningai-backend-v2.onrender.com/healthz
curl https://morningai-orchestrator-api.onrender.com/health
```

**Staging**:
```bash
curl https://morningai-backend-v2-stg.onrender.com/healthz
curl https://morningai-orchestrator-api-stg.onrender.com/health
```

**Local**:
```bash
curl http://localhost:8000/healthz
curl http://localhost:8001/health
```

### Viewing Logs

**Render Logs**:
- Go to https://dashboard.render.com/
- Select service
- Click "Logs" tab

**Sentry Errors**:
- Go to https://sentry.io/organizations/morningai/issues/
- Filter by environment (production/staging)

**Local Logs**:
- Check terminal output where services are running

---

## Troubleshooting

### Issue: Backend won't start

**Symptoms**: `ModuleNotFoundError`, `ImportError`

**Solutions**:
```bash
# Ensure virtual environment is activated
source .venv/bin/activate

# Reinstall dependencies
pip install -r requirements.txt

# Check Python version
python --version  # Should be 3.12+
```

### Issue: Frontend won't start

**Symptoms**: `Cannot find module`, build errors

**Solutions**:
```bash
# Reinstall dependencies
pnpm install

# Clear cache
rm -rf node_modules .next
pnpm install

# Check Node version
node --version  # Should be 20+
```

### Issue: Database connection fails

**Symptoms**: `Connection refused`, `Authentication failed`

**Solutions**:
```bash
# Check DATABASE_URL format
echo $DATABASE_URL
# Should be: postgresql://user:pass@host:port/db

# Test connection
python -c "from sqlalchemy import create_engine; engine = create_engine('$DATABASE_URL'); print(engine.connect())"

# Use staging database instead
# Get DATABASE_URL from team lead
```

### Issue: Redis connection fails

**Symptoms**: `Connection refused`, `WRONGPASS`

**Solutions**:
```bash
# Check REDIS_URL format
echo $REDIS_URL
# Should be: redis://localhost:6379/0 or rediss://...

# Test connection
python -c "import redis; r = redis.from_url('$REDIS_URL'); print(r.ping())"

# Use staging Redis instead
# Get REDIS_URL from team lead
```

### Issue: Tests failing

**Symptoms**: Test failures, coverage below threshold

**Solutions**:
```bash
# Run tests with verbose output
pytest -v

# Check specific test
pytest tests/test_specific.py -v

# Update test data/fixtures
# Check test documentation
```

### Issue: CI/CD failing

**Symptoms**: GitHub Actions workflow fails

**Solutions**:
1. Check workflow logs in GitHub Actions tab
2. Verify all required secrets are set in repository settings
3. Check if tests pass locally
4. Review recent commits for breaking changes

### Issue: Tailwind v4 max-w-* utilities not working correctly

**Symptoms**: 
- Container widths collapse to 16px instead of expected rem values (e.g., max-w-md should be 28rem/448px but renders as 16px)
- All `max-w-*` utilities affected (sm, md, lg, xl, 2xl, 3xl, 4xl, 5xl, 6xl, 7xl)
- Layout appears vertically compressed and unusable
- Issue only appears on Vercel preview deployments (not local dev due to different build optimizations)

**Root Cause**: Tailwind v4's `@theme` syntax incorrectly maps `max-w-*` utilities to `--spacing-*` tokens which are intended for padding/margin, not container widths.

**Technical Details**:
In `theme.css`, we defined:
```css
--spacing-md: var(--space-md);  /* 16px from shared-ui */
```

Tailwind v4 then incorrectly generated:
```css
.max-w-md { max-width: var(--spacing-md); }  /* 16px - WRONG! */
```

But `max-w-md` should be:
```css
.max-w-md { max-width: 28rem; }  /* 448px - CORRECT */
```

**Solution**: The fix is already implemented in `owner-console/src/styles/theme.css`:
- Separate `--max-width-*` tokens are defined (lines 24-35)
- These tokens use correct rem values:
  - `--max-width-sm: 24rem` (384px)
  - `--max-width-md: 28rem` (448px)
  - `--max-width-lg: 32rem` (512px)
  - `--max-width-xl: 36rem` (576px)
  - `--max-width-2xl: 42rem` (672px)
  - `--max-width-3xl: 48rem` (768px)
  - `--max-width-4xl: 56rem` (896px)
  - `--max-width-5xl: 64rem` (1024px)
  - `--max-width-6xl: 72rem` (1152px)
  - `--max-width-7xl: 80rem` (1280px)
- Tailwind v4 now uses these dedicated tokens instead of spacing tokens
- Clean separation of concerns: spacing tokens (padding/margin) vs. container width tokens

**Verification**:
```bash
# 1. Run the regression test
cd handoff/20250928/40_App/owner-console
npm run test:e2e -- max-width-regression.spec.ts

# 2. Build and check compiled CSS
npm run build
grep "max-w-md" dist/assets/index-*.css
# Should show: .max-w-md{max-width:var(--max-width-md)}

# 3. Check computed styles in browser DevTools
# Open login page, inspect element with max-w-md class
# Computed maxWidth should be 448px (not 16px)
```

**If Issue Persists**:
1. Clear build cache: `rm -rf dist node_modules/.vite`
2. Reinstall dependencies: `pnpm install`
3. Rebuild: `pnpm build`
4. Check that `theme.css` contains `--max-width-*` tokens
5. Verify no CSS overrides in `index.css` (hotfix was removed in [PR #1308](https://github.com/RC918/morningai/pull/1308))

**Related Documentation**:
- **Detailed tracking doc**: `docs/TAILWIND_V4_MAX_WIDTH_ISSUE.md` (comprehensive 259-line analysis)
- **[PR #1303](https://github.com/RC918/morningai/pull/1303)**: Initial hotfix with CSS overrides
- **[PR #1308](https://github.com/RC918/morningai/pull/1308)**: Root cause fix with dedicated --max-width-* tokens
- **Regression test**: `e2e/max-width-regression.spec.ts`

**Risk Note**: Tailwind v4 token resolution behavior is based on observation, not official documentation. Future Tailwind v4 versions may change this behavior. Monitor for updates when upgrading Tailwind.

---

## Getting Help

### Internal Resources

**Documentation**:
- Check the `docs/` directory for comprehensive documentation
- Search for specific topics in documentation

**Team Communication**:
- **Slack**: #morningai-dev channel
- **GitHub Issues**: Report bugs or request features
- **GitHub Discussions**: Ask questions or share ideas

**Code Review**:
- Request review from team members on PRs
- Tag specific reviewers for domain expertise

### External Resources

**Technologies**:
- **Flask**: https://flask.palletsprojects.com/
- **React**: https://react.dev/
- **Supabase**: https://supabase.com/docs
- **Render**: https://render.com/docs

**Learning**:
- **Python**: https://docs.python.org/3/
- **TypeScript**: https://www.typescriptlang.org/docs/
- **PostgreSQL**: https://www.postgresql.org/docs/

### Contact

**Team Lead**: Ryan Chen (@RC918)
**Email**: ryan2939z@gmail.com
**GitHub**: https://github.com/RC918/morningai

---

## Next Steps

After completing this onboarding guide, you should:

1. ✅ **Set up your local development environment**
2. ✅ **Run all services locally and verify they work**
3. ✅ **Read the key documentation** (ENVIRONMENTS.md, CONTRIBUTING.md)
4. ✅ **Create your first feature branch**
5. ✅ **Make a small change and create a PR to main**
6. ✅ **Test your change via Vercel preview deployment**
7. ✅ **Join team communication channels**
8. ✅ **Review open issues and pick your first task**

**Welcome to the team! Happy coding!** 🚀

---

**Last Updated**: 2025-11-16  
**Version**: 1.2.0  
**Maintained By**: CTO / DevOps Team

**Changelog**:
- 2025-11-16 (v1.2.0): Updated current status with test coverage numbers, added agent evaluation harness documentation, linked to strategic roadmap reality comparison
- 2025-11-03 (v1.1.0): Previous update
