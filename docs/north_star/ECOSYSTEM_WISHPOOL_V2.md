# MorningAI Ecosystem Wish Pool v2 - North Star

**Version**: 2025-Q4 Final
**Status**: Active North Star Document
**Last Updated**: 2025-12-21

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
| **Model Layer** | Qwen3 Multi-Tier + Multi-Provider | [EPIC A: Qwen Provider & LLM Infrastructure (#2594)](https://github.com/RC918/morningai/issues/2594) | In Progress |
| **Intelligence Layer** | Reviewer Agent + Diff-Aware | [EPIC B: Diff-Aware Review Plumbing (#2595)](https://github.com/RC918/morningai/issues/2595) | In Progress |
| **Intelligence Layer** | Flow Controller v3 | [EPIC C: Flow Controller v3 (#2743)](https://github.com/RC918/morningai/issues/2743) | Planning |
| **Intelligence Layer** | Coding Agent Family | [EPIC D: Autonomous Coder Agent Family (#2759)](https://github.com/RC918/morningai/issues/2759) | Planning |

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
- Phase B-1: PR Diff Fetcher
- Phase B-2: Diff-Aware Prompt Builder
- Phase B-3: LLM Reviewer Adapter
- Phase B-4: Telemetry v2 Integration
- Phase B-5: Rollout & Monitoring
- Phase B-6: Reviewer -> Router Interface Definition

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

### 5. Governance & Safety Layer (Future EPICs)

**Wish Pool v2 Vision**:
- Safety Governor v2: Risk scan, prompt injection protection, jailbreak protection
- Compliance Radar v2: PII scanning, legal/medical/financial risk assessment
- Model Governance Framework v2: Drift monitoring, provider health, cost governance
- Autonomous Provisioning v2: Self-healing model management

**Status**: Not yet started. Will be addressed after EPIC D completion.

### 6. Infrastructure Layer (Future EPICs)

**Wish Pool v2 Vision**:
- Memory v2: 4-layer memory system (short-term, agent interaction, knowledge base, governance)
- Telemetry v2: Full execution trace reconstruction
- Multi-Agent Simulation Suite v1: End-to-end testing

**Status**: Telemetry v2 partially implemented in EPIC B. Full implementation pending.

---

## Cross-Reference: Wish Pool v2 to Current Work

| Wish Pool v2 Section | Current Status | Next Action |
|---------------------|----------------|-------------|
| 2. Model Layer | EPIC A in progress | Complete A-1 to A-4 |
| 3.1 Planner v3 | Not started | After EPIC D |
| 3.2 Flow Controller v3 | EPIC C planned | Start C-1 Schema |
| 3.3 Agent Catalog V2 | EPIC B (Reviewer), EPIC D (Coder) | Continue B, plan D |
| 4.1 Safety Governor v2 | Not started | Future EPIC E |
| 4.2 Compliance Radar v2 | Not started | Future EPIC E |
| 4.3 Model Governance v2 | Not started | Future EPIC F |
| 4.4 Autonomous Provisioning v2 | Not started | Future EPIC F |
| 5.1 Memory v2 | Not started | Future EPIC G |
| 5.2 Telemetry v2 | Partial (EPIC B) | Expand in EPIC C |
| 5.3 Simulation Suite v1 | Not started | Future EPIC H |

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
