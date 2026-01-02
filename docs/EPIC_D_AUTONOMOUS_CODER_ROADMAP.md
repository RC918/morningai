# EPIC D: Autonomous Coder Agent Family - Roadmap

> Last Updated: 2026-01-02

## Overview

EPIC D implements the complete Coder Agent family, enabling the system to autonomously complete the full cycle from "requirement understanding" to "code generation" to "self-correction". This is the main battlefield for realizing the **L2 - Execution Layer** in Wish Pool v2.

**GitHub Issue**: [#2759](https://github.com/RC918/morningai/issues/2759)

**Blueprint Alignment**: Section 3.3 - Agent Catalog V2 (Coder Family)

## Status Summary

| Stage | Status | Key Issues |
|-------|--------|------------|
| Stage 0: Pre-validation | **Completed** (via EPIC C) | #2758 (C-5b) |
| Stage 1: General Coder MVP | **In Progress** | #2760, #2761 |
| Stage 2: Intelligence & Automation | Planned | #2762, #2764 |
| Stage 3: Advanced Capabilities | Future | D-5, D-6 |
| HITL Gate Operationalization | **Pending** | [#3487](https://github.com/RC918/morningai/issues/3487) |

---

## Architecture

```
EPIC D: Coder Family

  Planner ──▶ Senior Coder ──▶ Junior Coder
  (Tier 1)     (Tier 1)        (Tier 2)
  Task Split   Architecture    Code Impl
      │            │               │
      ▼            ▼               ▼
  ┌─────────────────────────────────────┐
  │        Self-Correction Loop         │
  │     (npm test fail → auto-fix)      │
  └─────────────────────────────────────┘
```

---

## Stage 0: Pre-validation (Completed)

Completed via EPIC C - SimpleCoder validates Flow Controller routing.

### Implemented Items

| Issue | Description | Status |
|-------|-------------|--------|
| [#2758](https://github.com/RC918/morningai/issues/2758) | C-5b: SimpleCoderAgent for Flow Pilot | Done |

**SimpleCoder Specs**:
- Model: Tier 2 (Qwen3-Next-80B)
- Capability: Single-file create/modify only
- Purpose: "Crash Test Dummy" for Flow Controller v3

---

## Stage 1: General Coder MVP (In Progress)

Multi-file editing and Senior Coder reasoning capabilities.

### Items

| Issue | Description | Status |
|-------|-------------|--------|
| [#2760](https://github.com/RC918/morningai/issues/2760) | D-1: General Coder Agent (MVP) | In Progress |
| [#2761](https://github.com/RC918/morningai/issues/2761) | D-2: Senior Coder Logic (Tier 1) | In Progress |

### D-1: General Coder MVP

**Acceptance Criteria**:
- Support multi-file editing (up to 5 files)
- Proper context window management
- Integration with Flow Controller v3 routing

### D-2: Senior Coder Logic

**Acceptance Criteria**:
- Implement reasoning step (think architecture before coding)
- Produce architecture design document before code
- Tier 1 model (Qwen3-235B) for complex reasoning

---

## HITL Gate Operationalization Gap (Pending)

> **Tracking Issue**: [#3487](https://github.com/RC918/morningai/issues/3487)

### Current Gap

The `SeniorCoder` complexity abort mechanism currently falls back silently instead of triggering proper HITL (Human-in-the-Loop) gate.

| Component | Expected Behavior | Actual Behavior |
|-----------|-------------------|-----------------|
| `_attempt_senior_coder_plan()` | Abort → Trigger HITL gate | Abort → Silent fallback |
| HITL Integration Tests | Test actual abort → HITL path | Tests minimal graph only |

### Action Required

1. Add HITL trigger logic in `_attempt_senior_coder_plan()` abort path
2. Update integration tests to cover SeniorCoder abort → HITL flow
3. Add telemetry for HITL trigger events

---

## Stage 2: Intelligence & Automation (Planned)

Spec-driven development and self-correction capabilities.

### Planned Items

| Issue | Description | Status |
|-------|-------------|--------|
| [#2762](https://github.com/RC918/morningai/issues/2762) | D-3: Spec-Driven Development | Planned |
| [#2764](https://github.com/RC918/morningai/issues/2764) | D-4: Self-Correction Loop | Planned |

### D-3: Spec-Driven Development

**Acceptance Criteria**:
- Coder can read and understand Planner's spec
- Spec format standardized and validated
- Traceability from spec to implementation

### D-4: Self-Correction Loop

**Acceptance Criteria**:
- Detect `npm test` / `pytest` failures automatically
- Parse error logs and identify fix targets
- Attempt self-fix without Reviewer intervention
- Maximum retry limit with HITL escalation

---

## Stage 3: Advanced Capabilities (Future)

Planner v3 and cross-service coordination.

### Future Items

| Issue | Description | Status |
|-------|-------------|--------|
| D-5 | Planner v3 (Task Decomposition) | Future |
| D-6 | Cross-Service Coordination | Future |

### D-5: Planner v3

**Vision**:
- Decompose "login page" into "frontend task + backend task"
- Generate dependency graph for parallel execution
- Integrate with Flow Controller for orchestration

> **Note**: Planner v3 may become a separate EPIC (EPIC F) due to scope.

---

## Model Configuration

| Agent | Model Tier | Model | Purpose |
|-------|------------|-------|---------|
| SimpleCoder (C-5b) | Tier 2 | Qwen3-Next-80B | Flow Pilot validation |
| Junior Coder | Tier 2 | Qwen3-Next-80B | Simple code implementation |
| Senior Coder | Tier 1 | Qwen3-235B | Architecture design + Reasoning |
| Planner | Tier 1 | Qwen3-235B | Task decomposition |

---

## Feature Flag Configuration

```yaml
ENABLE_SENIOR_CODER:
  type: boolean
  default: false
  description: |
    Enable Senior Coder Agent (Tier 1 reasoning).
    Currently enabled in staging only for pilot testing.
    Production enablement pending HITL gate operationalization.
```

---

## Dependencies

```
EPIC C (Flow Controller v3)
    └── C-5b (#2758): SimpleCoderAgent for Flow Pilot
            │
            ▼
EPIC D (Coder Family)
    ├── D-1 (#2760): General Coder MVP (depends on C-5b)
    ├── D-2 (#2761): Senior Coder Logic (depends on D-1)
    ├── D-3 (#2762): Spec-Driven Development (depends on D-2)
    └── D-4 (#2764): Self-Correction Loop (depends on D-1)

Cross-EPIC:
- EPIC B: Reviewer validates Coder output
- EPIC C: Flow Controller routes to appropriate Coder
- EPIC I: Governance monitors Coder behavior
```

---

## Verification Signals (Production Readiness)

Before production enablement, verify:

- [ ] HITL gate properly triggered on complexity abort ([#3487](https://github.com/RC918/morningai/issues/3487))
- [ ] Multi-file editing works correctly (D-1)
- [ ] Senior Coder reasoning produces valid architecture docs (D-2)
- [ ] All Coders correctly routed by Flow Controller v3
- [ ] Telemetry emitting for Coder decisions

---

## Acceptance Criteria (Red Lines)

- [ ] D-1: Can handle multi-file editing (up to 5 files)
- [ ] D-2: Senior Coder produces architecture design before coding
- [ ] D-3: Coder can read and execute Planner's spec
- [ ] D-4: Auto-fix on `npm test` failure (without Reviewer)
- [ ] All Coders correctly routed by Flow Controller v3
- [ ] HITL gate triggered on complexity abort

---

## Risk & Rollback

- **Risk**: Coder output quality unstable
- **Mitigation**: All Coder output must pass Reviewer review
- **Rollback**: Disable Coder feature flag, fallback to manual handling

---

## Blueprint Alignment

| Blueprint Guarantee | Implementation |
|--------------------|----------------|
| Tiered Models | Junior (Tier 2) vs Senior (Tier 1) |
| Fail-Safe | Complexity abort → HITL escalation |
| Observable | Telemetry for Coder decisions |
| Reversible | Feature flag instant rollback |

---

## Related Documents

- [EPIC C Roadmap](./EPIC_C_FLOW_CONTROLLER_V3_ROADMAP.md) (Flow Controller)
- [EPIC B Roadmap](./EPIC_B_DIFF_AWARE_REVIEW_ROADMAP.md) (Reviewer)
- [Wish Pool v2](./north_star/ECOSYSTEM_WISHPOOL_V2.md)

---

## Changelog

| Date | Author | Changes |
|------|--------|---------|
| 2026-01-02 | Ryan Chen (@RC918) with Devin AI | Initial roadmap document |
