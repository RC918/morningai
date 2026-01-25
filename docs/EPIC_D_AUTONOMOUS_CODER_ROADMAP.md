# EPIC D: Autonomous Coder Agent Family - Roadmap

> Last Updated: 2026-01-25

## Overview

EPIC D implements the complete Coder Agent family, enabling the system to autonomously complete the full cycle from "requirement understanding" to "code generation" to "self-correction". This is the main battlefield for realizing the **L2 - Execution Layer** in Wish Pool v2.

**GitHub Issue**: [#2759](https://github.com/RC918/morningai/issues/2759)

**Blueprint Alignment**: Section 3.3 - Agent Catalog V2 (Coder Family)

## Status Summary

| Stage | Status | Key Issues |
|-------|--------|------------|
| Stage 0: Pre-validation | **Completed** (via EPIC C) | #2758 (C-5b) |
| Stage 1: General Coder MVP | **Completed** | #2760, #2761 |
| Stage 2: Intelligence & Automation | **Completed** | #2762, #2764 |
| Stage 3: Advanced Capabilities | Future | D-5, D-6 |
| HITL Gate Operationalization | **Completed** | [#3487](https://github.com/RC918/morningai/issues/3487) |

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

## Stage 1: General Coder MVP (Completed)

Multi-file editing and Senior Coder reasoning capabilities.

### Items

| Issue | Description | Status |
|-------|-------------|--------|
| [#2760](https://github.com/RC918/morningai/issues/2760) | D-1: General Coder Agent (MVP) | **Completed** |
| [#2761](https://github.com/RC918/morningai/issues/2761) | D-2: Senior Coder Logic (Tier 1) | **Completed** |

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

## HITL Gate Operationalization (Completed)

> **Tracking Issue**: [#3487](https://github.com/RC918/morningai/issues/3487) - **Closed**

### Implementation Summary

The `SeniorCoder` complexity abort mechanism now properly triggers HITL (Human-in-the-Loop) gate.

| Component | Status |
|-----------|--------|
| `_attempt_senior_coder_plan()` | HITL trigger logic implemented |
| HITL Integration Tests | Abort → HITL path covered |
| Telemetry | HITL trigger events emitting |

---

## Stage 2: Intelligence & Automation (Completed)

Spec-driven development and self-correction capabilities.

### Completed Items

| Issue | Description | Status | PR |
|-------|-------------|--------|-----|
| [#2762](https://github.com/RC918/morningai/issues/2762) | D-3: Spec-Driven Development | **Completed** | #3756 |
| [#2764](https://github.com/RC918/morningai/issues/2764) | D-4: Self-Correction Loop | **Completed** | #3821 (and others) |

### D-3: Spec-Driven Development (Completed)

**Implementation**:
- `SpecParser` - Parses Planner-produced structured specs
- `SpecValidator` - Validates spec format and completeness
- SeniorCoder integration for spec-driven workflow

**Acceptance Criteria Met**:
- [x] Coder can read and understand Planner's spec
- [x] Spec format standardized and validated
- [x] Traceability from spec to implementation

### D-4: Self-Correction Loop (Completed)

**Implementation**:
- `SelfCorrectionLoop` class with retry logic
- `TestLogParser` for error extraction (pytest, jest, mocha)
- `LintErrorParser` for lint tool output (ruff, flake8, eslint, pylint) - PR #4332
- `get_check_run_logs` for direct CI log fetching - PR #4327, #4331
- CI failure webhook integration with `AUTO_FIX_ENABLED` check - PR #4323
- Loop protection with max 3 attempts
- CISignatureDeduplication for cost optimization - PR #4321

**Acceptance Criteria Met**:
- [x] Detect `npm test` / `pytest` failures automatically
- [x] Detect lint failures (ruff F401, eslint no-unused-vars, etc.)
- [x] Parse error logs and identify fix targets
- [x] Attempt self-fix without Reviewer intervention
- [x] Maximum retry limit with HITL escalation

**Verified**: 
- 2026-01-11 - D-4 successfully triggered on test PR #3823
- 2026-01-25 - D-4 successfully auto-fixed lint error (F401 unused import) on PR #4330

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

All verification signals confirmed:

- [x] HITL gate properly triggered on complexity abort ([#3487](https://github.com/RC918/morningai/issues/3487))
- [x] Multi-file editing works correctly (D-1)
- [x] Senior Coder reasoning produces valid architecture docs (D-2)
- [x] All Coders correctly routed by Flow Controller v3
- [x] Telemetry emitting for Coder decisions

---

## Acceptance Criteria (Red Lines)

- [x] D-1: Can handle multi-file editing (up to 5 files)
- [x] D-2: Senior Coder produces architecture design before coding
- [x] D-3: Coder can read and execute Planner's spec
- [x] D-4: Auto-fix on `npm test` failure (without Reviewer)
- [x] All Coders correctly routed by Flow Controller v3
- [x] HITL gate triggered on complexity abort

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
| 2026-01-25 | Devin AI | D-4 CI failure auto-fix verified:<br/>- `LintErrorParser` (#4332)<br/>- `get_check_run_logs` (#4327, #4331)<br/>- `AUTO_FIX_ENABLED` check (#4323)<br/>- CI signature deduplication (#4321)<br/>Rollback tag: `v9.5.0-d4-ci-autofix-stable` |
| 2026-01-11 | Devin AI | Mark Stage 1, Stage 2, HITL Gate as Completed; Add D-3/D-4 implementation details and PR references |
| 2026-01-02 | Ryan Chen (@RC918) with Devin AI | Initial roadmap document |
