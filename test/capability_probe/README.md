# EPIC D Capability Probe Test Suite

This directory contains test scenarios for validating D-1 (GeneralCoder multi-file editing)
and D-2 (SeniorCoder architecture-first) capabilities in staging.

## How to Use

Each probe is designed to trigger a specific code path when CI fails. The probes should be
executed sequentially by pushing commits that intentionally fail lint/type checks.

## Probe Scenarios

### Probe 0: Sanity Check (Single File)
**Purpose:** Verify the basic AutoFixer pipeline is working before testing D-1/D-2.
**File:** `probe0_sanity/missing_docstring.py`
**Expected:** SimpleCoder adds docstring, commit succeeds.
**Log Keywords:** `[Fixer]`, `[CODER_PATCH]`

### Probe 1: D-1 Multi-file Refactor (2 Files)
**Purpose:** Verify GeneralCoder can modify multiple related files atomically.
**Files:** `probe1_multifile/utils.py`, `probe1_multifile/main.py`
**Scenario:** Function `calculate_total` in utils.py is renamed but caller in main.py is not updated.
**Expected:** GeneralCoder updates both files.
**Log Keywords:** `[GENERAL_CODER_ATTEMPT]`, `[GENERAL_CODER_PATCH]`

### Probe 2: D-2 Complexity Escalation
**Purpose:** Verify SeniorCoder correctly identifies complex tasks and triggers HITL.
**File:** `probe2_complexity/hardcoded_logic.py`
**Scenario:** Request Strategy Pattern refactor (complex architectural change).
**Expected:** SeniorCoder marks as complex, triggers HITL gate.
**Log Keywords:** `[SENIOR_CODER_PLAN_ATTEMPT]`, `[SENIOR_CODER_PLAN_COMPLEX]`, `[SENIOR_CODER_HITL_ESCALATION]`

### Probe 3: Syntax Safety Guardrail
**Purpose:** Verify GeneralCoder's syntax validation prevents bad commits.
**File:** `probe3_safety/syntax_trap.py`
**Scenario:** File with subtle issue that might cause LLM to generate invalid syntax.
**Expected:** GeneralCoder skips (no bad commit), logs syntax abort.
**Log Keywords:** `[GENERAL_CODER_SKIP]`, `[CODER_SYNTAX_ABORT]`, `[GENERAL_CODER_SYNTAX_ABORT]`

## Observability

Search Render logs for these event codes:
```
[GENERAL_CODER_ATTEMPT]
[GENERAL_CODER_PATCH]
[GENERAL_CODER_SKIP]
[GENERAL_CODER_GATE_FAIL]
[SENIOR_CODER_PLAN_ATTEMPT]
[SENIOR_CODER_PLAN_SIMPLE]
[SENIOR_CODER_PLAN_MODERATE]
[SENIOR_CODER_PLAN_COMPLEX]
[SENIOR_CODER_REVIEW_APPROVED]
[SENIOR_CODER_REVIEW_REJECTED]
```

## Success Criteria

| Probe | Success | Failure |
|-------|---------|---------|
| Probe 0 | Commit with docstring added | No commit or pipeline error |
| Probe 1 | Both files updated atomically | Only one file updated or skip |
| Probe 2 | HITL gate triggered | Task proceeds without HITL |
| Probe 3 | Skip with syntax reason, no bad commit | Bad code committed |

