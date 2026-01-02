# MorningAI Ecosystem Wish Pool v2 - North Star

**Version**: 2025-Q4 Final
**Status**: Active North Star Document
**Last Updated**: 2026-01-02

---

## 30-Second Summary (North Star)

**MorningAI 的終極目標**：打造一個能**自我規劃、自我編碼、自我審查、自我測試、自我部署、自我監控、自我修復**的 AI Software Engineering Factory。

**成功指標**：
- AI 能端到端產出 PR 並自我修復
- 所有行為可透過 Telemetry + Memory 還原
- 模型、Provider、Flow、Routing 都能自動管理

---

## 5-Minute Overview (Roadmap Map)

### Architecture Layers

```
+------------------------------------------------------------+
|                MorningAI Operating System                   |
+-----------------------------+------------------------------+
|   Intelligence Layer        |   Governance & Safety Layer  |
|   (Planner / Flow / Agents) |   (Safety / Compliance /     |
|                             |    Governance / Provisioning)|
+-----------------------------+------------------------------+
|         Infrastructure Layer (Memory / Telemetry)          |
+------------------------------------------------------------+
|              Model Layer (Qwen3 Multi-Tier)                |
+------------------------------------------------------------+
```

### Current EPICs Mapping to Wish Pool v2

| Layer | Wish Pool v2 Component | Current EPIC | Status |
|-------|------------------------|--------------|--------|
| **Model Layer** | Qwen3 Multi-Tier + Multi-Provider | [EPIC A: Qwen Provider & LLM Infrastructure (#2594)](https://github.com/RC918/morningai/issues/2594) | **Completed** |
| **Intelligence Layer** | Reviewer Agent + Diff-Aware | [EPIC B: Diff-Aware Review Plumbing (#2595)](https://github.com/RC918/morningai/issues/2595) | **Phase 1-3 + B-6 Completed** |
| **Intelligence Layer** | Flow Controller v3 | [EPIC C: Flow Controller v3 (#2743)](https://github.com/RC918/morningai/issues/2743) | **Completed** (Pilot Pending: `ENABLE_DYNAMIC_ROUTING=false`); Alert Evaluator: [#3499](https://github.com/RC918/morningai/issues/3499) |
| **Intelligence Layer** | Coding Agent Family | [EPIC D: Autonomous Coder Agent Family (#2759)](https://github.com/RC918/morningai/issues/2759) | **In Progress**; HITL Gate Completed ([#3487](https://github.com/RC918/morningai/issues/3487)) |
| **Governance Layer** | Model Governance v2 + Autonomous Provisioning | [EPIC I: Runtime Governance & Immune System (#3342)](https://github.com/RC918/morningai/issues/3342) | Planning (after #3249) |

### Future EPICs (Placeholder)

| Layer | Wish Pool v2 Component | EPIC | Status |
|-------|------------------------|------|--------|
| **Governance Layer** | Safety Governor v2 + Compliance Radar v2 | [EPIC E: Safety Governor v2 + Compliance Radar v2 (#3489)](https://github.com/RC918/morningai/issues/3489) | **Planning** - [Roadmap](../EPIC_E_SAFETY_GOVERNOR_V2_ROADMAP.md) |
| **Intelligence Layer** | Planner v3 | [EPIC F: Planner v3 (#3490)](https://github.com/RC918/morningai/issues/3490) | **Planning** - [Roadmap](../EPIC_F_PLANNER_V3_ROADMAP.md) |
| **Infrastructure Layer** | Memory v2 | [EPIC G: Memory v2 (#3491)](https://github.com/RC918/morningai/issues/3491) | Placeholder |
| **Infrastructure Layer** | Simulation Suite v1 | [EPIC H: Simulation Suite v1 (#3492)](https://github.com/RC918/morningai/issues/3492) | Placeholder |

### EPIC Dependencies

```
EPIC A (Model Layer)
    |
    v
EPIC B (Reviewer Agent) ----+
    |                       |
    v                       v
EPIC C (Flow Controller) ---+
    |
    v
EPIC D (Coder Agent Family)
    |
    v
EPIC I (Runtime Governance) <-- Cross-cutting: monitors all LLM calls from A/B/C/D
```

### Model Tier Strategy (from Wish Pool v2)

| Tier | Model | Use Case | EPIC |
|------|-------|----------|------|
| Tier 0 | Qwen3-Max | Critical reasoning, Judge | Future |
| Tier 1 | Qwen3-235B | Deep reasoning, Senior Coder | EPIC A, D |
| Tier 2 | Qwen3-Next-80B | Coding / Reviewing | EPIC A, B, C |
| Tier 3 | Qwen3-14B / 7B | UI copy / Basic tasks | Future |

---

## 30-Minute Deep Dive

### 1. Model Layer (EPIC A)

**Wish Pool v2 Vision**: Multi-Provider architecture supporting AliCloud, SiliconFlow, Together AI, OpenRouter.

**Current Implementation (EPIC A #2594)**:
- Phase A-1: QwenProvider implementation
- Phase A-2: Configuration extension (QWEN_API_KEY, QWEN_BASE_URL)
- Phase A-3: Cost Tracker update
- Phase A-4: Unit tests
- Phase A-B: Staging validation
- Phase A-C: Progressive deployment

### 2. Intelligence Layer - Reviewer (EPIC B)

**Wish Pool v2 Vision**: Reviewer Agent with diff-aware capabilities, integrated with Safety/Compliance layer.

**Current Implementation (EPIC B #2595)**:

| Phase | Description | Status |
|-------|-------------|--------|
| B-1 | PR Diff Fetcher (`get_pr_diff()` with truncation/ignore list) | **Completed** |
| B-2 | Diff-Aware Prompt Builder (review comment schema, secrets redaction) | **Completed** |
| B-3 | LLM Reviewer Adapter (GitHub inline comment posting, line validation) | **Completed** |
| Phase 1 | Quick Wins (max_tokens, timeout, fallback_reason) | **Completed** |
| Phase 2 | Publishing Correctness (head_sha capture, line drift detection) | **Completed** |
| Phase 3 | Security & Reliability (secrets sanitization, commit_id validation) | **Completed** |
| Phase 4 | Checks API (GitHub App, branch protection) | Planned (2026) |
| **B-6** | Reviewer -> Router Interface (`ReviewOutcome` schema) | **Completed** ([#3130](https://github.com/RC918/morningai/issues/3130), [#3135](https://github.com/RC918/morningai/pull/3135)) |

**Telemetry 說明**: EPIC B 實作了 Reviewer 相關的 telemetry 欄位（trace_id, fallback_reason, drift metrics），這是 Blueprint 5.2 Telemetry v2 願景的一部分。完整的 Telemetry v2（執行軌跡重建、多代理回放）屬於 Infrastructure Layer，跨越多個 EPIC。

### 3. Intelligence Layer - Flow Controller (EPIC C)

**Wish Pool v2 Vision**: Dynamic state machine with multi-agent branching, auto-merge, fail-fast recovery, safety/compliance-aware routing.

**Current Implementation (EPIC C #2743)**:
- Stage 0: Schema & Interface Definition (C-1 to C-4)
- Stage 1: Pilot (C-5a, C-5b, C-6 to C-8)
- Stage 2: Full Migration (C-9, C-10)

**Key Component**: C-5b SimpleCoderAgent serves as "crash test dummy" to validate Flow Controller.

### 4. Intelligence Layer - Coder Family (EPIC D)

**Wish Pool v2 Vision**: Coding Agent with self-correction, spec-driven development, Senior/Junior differentiation.

**Current Implementation (EPIC D #2759)**:
- Stage 0: C-5b Validation (from EPIC C)
- Stage 1: D-1 General Coder MVP, D-2 Senior Coder Logic
- Stage 2: D-3 Spec-Driven Development, D-4 Self-Correction Loop
- Stage 3: Future capabilities

### 5. Governance & Safety Layer (EPIC I)

**Wish Pool v2 Vision**:
- Safety Governor v2: Risk scan, prompt injection protection, jailbreak protection
- Compliance Radar v2: PII scanning, legal/medical/financial risk assessment
- Model Governance Framework v2: Drift monitoring, provider health, cost governance
- Autonomous Provisioning v2: Self-healing model management

**Current Implementation (EPIC I #3342)**:
EPIC I 是 Blueprint 4.3 (Model Governance Framework v2) 與 4.4 (Autonomous Provisioning v2) 的落地實作。

- Phase I-1: Runtime Drift Detection (格式/Schema 驗證)
- Phase I-2: Provider Health Scoring (延遲、錯誤率、drift 頻率)
- Phase I-3: Alerting & Dashboard (Grafana/Sentry 整合)
- Phase I-4: Auto-Degradation (自動路由調整，對齊 PR #3316)

**現有基礎設施**:
- `LLMClient.generate()` - 統一 LLM 呼叫入口（Interceptor 插入點）
- `CanaryMetrics` - Redis-based 分鐘級指標系統
- `ROUTING_ALLOWED_PROVIDERS` (PR #3316) - Provider 治理 allowlist

**Status**: Planning. Will start after #3249 completion.

### 6. Infrastructure Layer (Future EPICs)

**Wish Pool v2 Vision**:
- Memory v2: 4-layer memory system (short-term, agent interaction, knowledge base, governance)
- Telemetry v2: Full execution trace reconstruction
- Multi-Agent Simulation Suite v1: End-to-end testing

**Telemetry v2 實作狀態**:
- **EPIC B 貢獻**: Reviewer telemetry 欄位（trace_id, fallback_reason, drift_downgrade_count）- **Completed**
- **完整願景**: 執行軌跡重建、多代理推理回放、Simulation Suite 整合 - **Pending** (Future EPIC)

---

## Cross-Reference: Wish Pool v2 to Current Work

| Wish Pool v2 Section | Current Status | Next Action |
|---------------------|----------------|-------------|
| 2. Model Layer | **EPIC A Completed** | Maintenance mode |
| 3.1 Planner v3 | **Planning** | [EPIC F (#3490)](https://github.com/RC918/morningai/issues/3490) - [Roadmap](../EPIC_F_PLANNER_V3_ROADMAP.md) |
| 3.2 Flow Controller v3 | **EPIC C Completed** (Pilot Pending: `ENABLE_DYNAMIC_ROUTING=false`) | Enable Pilot rollout; Alert Evaluator ([#3499](https://github.com/RC918/morningai/issues/3499)) |
| 3.3 Agent Catalog V2 | **EPIC B Phase 1-3 + B-6 Completed**, EPIC D In Progress; HITL Gate Completed ([#3487](https://github.com/RC918/morningai/issues/3487)) | Continue D |
| 4.1 Safety Governor v2 | **Planning** | [EPIC E (#3489)](https://github.com/RC918/morningai/issues/3489) - [Roadmap](../EPIC_E_SAFETY_GOVERNOR_V2_ROADMAP.md) |
| 4.2 Compliance Radar v2 | **Planning** | [EPIC E (#3489)](https://github.com/RC918/morningai/issues/3489) - [Roadmap](../EPIC_E_SAFETY_GOVERNOR_V2_ROADMAP.md) |
| 4.3 Model Governance v2 | **PR #3316 Completed** (ROUTING_ALLOWED_PROVIDERS) | **EPIC I** (#3342) |
| 4.4 Autonomous Provisioning v2 | Planning | **EPIC I** (#3342) |
| 5.1 Memory v2 | Not started | [EPIC G (#3491)](https://github.com/RC918/morningai/issues/3491) - Placeholder |
| 5.2 Telemetry v2 | **EPIC B Reviewer telemetry Completed**; Full trace reconstruction Pending | Future EPIC |
| 5.3 Simulation Suite v1 | Not started | [EPIC H (#3492)](https://github.com/RC918/morningai/issues/3492) - Placeholder |

---

## How to Use This Document

1. **Before starting any new EPIC/Issue**: Check this document to ensure alignment with Wish Pool v2
2. **When creating Issues**: Reference the relevant Wish Pool v2 section in the issue description
3. **During code review**: Verify changes align with the architectural vision
4. **When planning**: Use the EPIC dependency graph to determine priority

---

## Source Document

The complete Wish Pool v2 Blueprint is available at:
[MorningAI_Ecosystem_Blueprint_2025_Final.md](./MorningAI_Ecosystem_Blueprint_2025_Final.md)

This North Star document is a living summary that maps the vision to current implementation progress.

---

## Document Maintenance

**Primary Maintainer**: Ryan Chen (@RC918) with Devin AI assistance

**Sync Policy**:
- This summary document (`ECOSYSTEM_WISHPOOL_V2.md`) should be updated whenever EPIC status changes
- The full Blueprint (`MorningAI_Ecosystem_Blueprint_2025_Final.md`) is the authoritative source for architectural vision
- Any changes to the Blueprint should be reflected in this summary within the same PR

---

## ChangeLog

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2025-12-21 | Ryan Chen (@RC918) | Initial version with EPIC A/B/C/D mapping |
| 1.1 | 2025-12-30 | Ryan Chen (@RC918) with Devin AI | Updated EPIC status: A Completed, B Phase 1-3 Completed, D In Progress. Added Model Governance PR #3316. |
| 1.2 | 2025-12-30 | Ryan Chen (@RC918) with Devin AI | Updated EPIC C status based on code evidence: Stage 0 (C-1/C-2/C-3/C-4) + C-6 Graph Wiring Completed; Pilot Pending (ENABLE_DYNAMIC_ROUTING=false by default). |
| 1.3 | 2025-12-30 | Ryan Chen (@RC918) with Devin AI | Added EPIC I: Runtime Governance & Immune System (#3342) - Blueprint 4.3/4.4 implementation. Updated EPIC table, dependency graph, and cross-reference. |
| 1.4 | 2025-12-31 | Ryan Chen (@RC918) with Devin AI | Refined EPIC B status: Added detailed phase table (B-1 to B-6, Phase 1-4). Clarified Telemetry v2 scope: EPIC B contributes Reviewer telemetry fields; full trace reconstruction is a separate future EPIC. |
| 1.5 | 2026-01-02 | Ryan Chen (@RC918) with Devin AI | Updated EPIC B Phase 6 (B-6) status from "In Progress" to "Completed" based on EPIC_B_DIFF_AWARE_REVIEW_ROADMAP.md evidence. Synced all references in EPIC table, phase table, and cross-reference section. |
| 1.6 | 2026-01-02 | Ryan Chen (@RC918) with Devin AI | Added Operationalization Pending status for EPIC C ([#3486](https://github.com/RC918/morningai/issues/3486): RouterMetrics not wired) and EPIC D ([#3487](https://github.com/RC918/morningai/issues/3487): SeniorCoder HITL gate). Updated EPIC table and cross-reference section with Issue links. |
| 1.7 | 2026-01-02 | Ryan Chen (@RC918) with Devin AI | Added Future EPICs section with placeholder issues: EPIC E (#3489 - Safety Governor + Compliance Radar), EPIC F (#3490 - Planner v3), EPIC G (#3491 - Memory v2), EPIC H (#3492 - Simulation Suite). Created dedicated roadmap documents for EPIC C and EPIC D. Updated cross-reference section with Issue links. |
| 1.8 | 2026-01-02 | Ryan Chen (@RC918) with Devin AI | Updated EPIC C status to **Completed** (Operationalization done via #3486/#3494, Dashboard/Alerting via #3495/#3497). Updated EPIC D HITL Gate status to **Completed** (#3487/#3498). Added Alert Evaluator follow-up issue (#3499). |
| 1.9 | 2026-01-02 | Ryan Chen (@RC918) with Devin AI | Created EPIC E and EPIC F detailed roadmap documents with JSON Schema definitions. Updated EPIC E/F status from "Placeholder" to "Planning" with roadmap links. |
