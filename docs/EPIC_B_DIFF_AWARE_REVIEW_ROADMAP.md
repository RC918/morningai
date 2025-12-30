# EPIC B: Diff-Aware Review Plumbing - Roadmap

> Last Updated: 2025-12-30

## Overview

EPIC B focuses on implementing intelligent PR review with inline comments, ensuring reviews are generated correctly and posted reliably to GitHub.

## Status Summary

| Phase | Status | PR |
|-------|--------|-----|
| Phase 1: Quick Wins | Completed | [#2785](https://github.com/RC918/morningai/pull/2785) |
| Phase 2: Publishing Correctness | Completed | [#2788](https://github.com/RC918/morningai/pull/2788), [#2803](https://github.com/RC918/morningai/pull/2803) |
| Phase 3: Security & Reliability | Completed | [#2809](https://github.com/RC918/morningai/pull/2809), [#2829](https://github.com/RC918/morningai/pull/2829), [#2836](https://github.com/RC918/morningai/pull/2836) |
| Phase 4: Checks API (P6) | Planned | - |
| **Phase 6: Router Interface (B-6)** | **In Progress** | [#3130](https://github.com/RC918/morningai/issues/3130) |

---

## Phase 1: Quick Wins (Completed)

Low-risk, immediate improvements to LLM reliability and comment delivery.

### Implemented Items

| Item | Description | Status |
|------|-------------|--------|
| max_tokens increase | Increased from 1000 to 4000 to prevent JSON truncation | Done |
| timeout increase | Increased from 20s to 30s for complex reviews | Done |
| fallback_reason field | Added to distinguish failure types (json_parse_failed, timeout, connection_error, api_error, unavailable) | Done |
| Log semantics fix | Changed "LLM not available" to "LLM fallback ({reason})" | Done |
| File-level delivery | File-level comments now published in review body instead of being skipped | Done |

---

## Phase 2: Publishing Correctness (Completed)

Ensuring reviews are posted correctly despite line drift between review generation and publishing.

### Implemented Items

| Item | Description | Status |
|------|-------------|--------|
| head_sha capture | `get_pr_diff()` now captures and returns `pr.head.sha` | Done |
| head_sha storage | `reviewer_node` stores `diff_head_sha` in state | Done |
| Line drift detection | `publisher_node` compares stored vs current head_sha before posting | Done |
| Conservative strategy | When drift detected, all inline comments downgraded to file-level | Done |
| Drift notification | Review body includes "New commits detected" note when drift occurs | Done |
| Fail-open behavior | If head_sha check fails, proceed with posting rather than blocking | Done |
| Metric fix | Separate `drift_downgrade_count` for accurate telemetry | Done |

### Behavior Summary

- **Normal case**: No change - inline comments posted as usual
- **Line drift detected**: Conservative strategy - all inline comments become file-level to prevent 422 errors
- **Fail-open**: If head_sha check fails, proceed with posting

---

## Phase 3: Security & Reliability (Completed)

Security improvements and additional reliability enhancements.

### Implemented Items

| Priority | Item | Description | Status |
|----------|------|-------------|--------|
| P1 | Secrets exposure mitigation | `state["diff_content"]` now sanitized before storage using `sanitize_diff_content()` | Done |
| P2 | commit_id validation | Pass `commit_id` to `post_pr_review()` to pin review to specific commit, preventing 422 errors from race conditions | Done |
| P2 | Code duplication refactor | Added `_build_file_level_appendix()` helper for unified file-level delivery. File-level comments now included in review body even when inline comments exist | Done |
| P3 | JSON repair call | Three-stage repair: direct parse → regex clean → LLM repair. Feature flag: `enable_llm_json_repair` (default: False for safer rollout) | Done |

### Security Audit Finding (Resolved)

**Issue**: `state["diff_content"]` stored the raw unsanitized diff content.

**Risk**: This content was persisted via LangGraph checkpointer (PostgreSQL/Redis), potentially exposing secrets that appear in diffs.

**Fix Applied**: Option 1 - Sanitize diff content before storing in state using existing `sanitize_diff_content()`. This preserves line numbers and diff structure while redacting potential secrets.

---

## Previously Completed Items (Pre-EPIC B Phases)

These items were completed before the Phase 1/2/3 structure was established:

| Item | Description | Status |
|------|-------------|--------|
| B-1 PR Diff Retrieval | `get_pr_diff()` with truncation and ignore list | Done |
| B-2 Review Comment Schema | Structured schema for inline comments | Done |
| B-2.5 Secrets Redaction | `sanitize_diff_content()` for LLM input | Done |
| B-2.5 Ignore List | Skip lockfiles and generated files | Done |
| B-3 GitHub Inline Comment Posting | `post_pr_review()` with inline comments | Done |
| B-3.1 Line Number Validation | Validate line numbers against diff | Done |
| B-B C-lite Telemetry | Metrics for downgrade reasons | Done |

---

## Related PRs

| PR | Description | Status |
|----|-------------|--------|
| [#2781](https://github.com/RC918/morningai/pull/2781) | Debounce mechanism fix | Merged |
| [#2782](https://github.com/RC918/morningai/pull/2782) | P2 robustness improvements | Merged |
| [#2783](https://github.com/RC918/morningai/pull/2783) | ReputationEngine UUID fix | Merged |
| [#2785](https://github.com/RC918/morningai/pull/2785) | Phase 1 Quick Wins | Merged |
| [#2788](https://github.com/RC918/morningai/pull/2788) | Phase 2 Line Drift Protection | Merged |
| [#2803](https://github.com/RC918/morningai/pull/2803) | P2 Follow-up Drift Metrics | Merged |
| [#2809](https://github.com/RC918/morningai/pull/2809) | Phase 3 P1 - Secrets Sanitization | Merged |
| [#2829](https://github.com/RC918/morningai/pull/2829) | Phase 3 P2 - commit_id validation | Merged |
| [#2831](https://github.com/RC918/morningai/pull/2831) | commit_pinning metrics logging | Merged |
| [#2834](https://github.com/RC918/morningai/pull/2834) | extra dict variables fix | Merged |
| [#2836](https://github.com/RC918/morningai/pull/2836) | Phase 3 P2/P3 - unified file-level delivery and LLM JSON repair | Open |

---

## Verification Signals (Production Readiness)

Before full production rollout, verify:

- [ ] GitHub PR reviews are visible (even if only file-level)
- [ ] 422 fallback rate < 5%
- [ ] JSON parse fail rate < 5%
- [ ] Line drift detection working (check logs for `line_drift_detected`)
- [ ] No capability regression from system self-degradation

---

## Testing Checklist

### Phase 2 E2E Test Plan

1. Create a test PR with code changes
2. Trigger a review job
3. While review is processing, push another commit
4. Verify:
   - Review is posted with file-level comments
   - Review body includes "New commits detected" note
   - `line_drift_detected` appears in logs
   - `line_drift_downgraded` metric is recorded

### Phase 2 Regression Test

1. Create a test PR with code changes
2. Trigger a review job
3. Do NOT push any new commits
4. Verify:
   - Inline comments are posted correctly
   - No drift note in review body
   - `line_drift_detected` is false in logs

---

## Phase 4: Checks API (P6) - Planned

> **Status**: Planned - Not yet started
> **Target**: 2026 Full-Auto PR Lifecycle

### Overview

Phase 4 extends the Reviewer output from PR Review Comments (human-readable) to GitHub Checks API (machine-readable), enabling automated branch protection gates and governance integration.

### Blueprint Alignment

| Blueprint Goal | P6 Relevance |
|---------------|--------------|
| "AI 自己審查" (Reviewer Agent) | Current PR Review API already satisfies |
| "可機器治理、自動管理" (Governance Layer) | Checks API is better suited - single updatable artifact, status gate support |
| "Full-Auto PR Lifecycle" (2026 Goal) | Checks API is essential - can be required by branch protection, read by automation systems |
| "可預測性、安全性" (Ecosystem Guarantees) | Both approaches satisfy |

### Prerequisites

Before implementing P6, the following must be completed:

| Prerequisite | Description | Status |
|--------------|-------------|--------|
| Integration Test | Automated "send review → receive webhook → verify no duplicate" flow | Pending |
| Monitoring & Alerts | Verify P1-P3 stability | Pending |
| GitHub App Identity Boundary | Migrate from PAT to GitHub App for proper permissions | Pending |

### Why Not Now

- **GitHub App Required**: Currently using PAT; Checks API requires GitHub App permissions
- **Branch Protection Decision**: Need to decide if AI reviewer results should be used as merge gates
- **Webhook Normalizer**: Need to confirm `check_run`/`check_suite` events won't create new loops
- **UX Location Change**: Reviews appear in Conversation/Files changed (for humans); Checks appear in Checks tab (for machines)

### Planned Items

| Item | Description | Status |
|------|-------------|--------|
| P6-1 GitHub App Setup | Create GitHub App with `checks:write` permission | Planned |
| P6-2 Checks API Integration | Implement `create_check_run()` and `update_check_run()` | Planned |
| P6-3 Dual-Write Strategy | Feature flag to write both Review (human) + Check (machine gate) | Planned |
| P6-4 Branch Protection Integration | Document how to configure branch protection with AI reviewer check | Planned |
| P6-5 Webhook Handler Update | Handle `check_run`/`check_suite` events in normalizer | Planned |

### Implementation Strategy

**Recommended Milestone Order**:

1. **Now**: Complete Integration Test + Monitoring/Alerts (verify P1-P3 stability)
2. **Next**: Establish GitHub App identity boundary (P6 prerequisite)
3. **Then**: P6 Checks API (dual-write strategy: send review for humans + check for machine gate)

### Conclusion

P6 is "Governance Interface for 2026 Full-Auto PR Lifecycle" - should be on roadmap but wait for prerequisites to be ready.

---

## Phase 6: Router Interface (B-6) - In Progress

> **Status**: In Progress
> **Issue**: [#3130](https://github.com/RC918/morningai/issues/3130)
> **Target**: EPIC C Stage 1 (C-5 Review Routing Pilot)

> **Note**: This is a **design document**. The actual schema and logic implementation will be delivered in the B-6 implementation PR. Until that PR is merged, this document defines the contract; the implementation PR will be the source of truth.

### Overview

Phase 6 defines the stable interface contract between Reviewer and Router, enabling Flow Controller v3 to make routing decisions based on review results.

### Why This Phase

EPIC C (Flow Controller v3) depends on a structured output from Reviewer to make routing decisions. Without a well-defined `ReviewOutcome` schema, the Router cannot determine whether to proceed to publisher, fixer, or escalate.

### Schema Definition (CTO Approved)

```python
from pydantic import BaseModel
from typing import Literal

class ReviewOutcome(BaseModel):
    """Reviewer → Router 穩定介面 (EPIC B-6)
    
    Schema Version: 1
    Evolution Strategy: Only additive changes (new optional fields).
    Breaking changes require version bump and Router compatibility handling.
    """
    
    # Schema version for backward-compatible evolution
    schema_version: Literal[1] = 1
    
    # 決策訊號 (Router 用)
    verdict: Literal["approve", "request_changes", "comment", "blocked", "unknown"]
    severity: Literal["low", "medium", "high", "critical"]
    summary: str  # 給 Router 的一句話摘要
    
    # 資料品質訊號 (Router 做 fail-safe 決策用)
    diff_truncated: bool = False
    schema_validated: bool = True
    blocker_count: int = 0  # count of comments where severity in {"high", "critical"}
```

### Verdict Semantics

| Verdict | Description | Router Behavior |
|---------|-------------|-----------------|
| `approve` | Review passed, no blocking issues | Proceed to publisher |
| `request_changes` | Issues found that need fixing | Route to fixer or escalate |
| `comment` | Suggestions but not blocking | Proceed to publisher (with suggestions) |
| `blocked` | Safety/Compliance block | Force escalate or abort |
| `unknown` | Reviewer runtime failure (timeout/parse error/exception) | **MUST** fallback to deterministic routing |

### Router Decision Rules (Deterministic)

The Router MUST apply the following precedence rules when reading `ReviewOutcome`:

1. **`unknown` verdict overrides all other fields**: If `verdict == "unknown"`, Router MUST ignore `severity`, `blocker_count`, and `summary`, and immediately fallback to rule-based routing. This verdict is ONLY produced when Reviewer encounters runtime failure (timeout, parse error, exception) - it is NOT a valid LLM output for "uncertain" reviews.

2. **`blocked` verdict forces escalation**: If `verdict == "blocked"`, Router MUST escalate regardless of other fields. This is reserved for Safety/Compliance blocks.

3. **`schema_validated == False` triggers fallback**: If Pydantic validation failed, the producer MUST catch the exception and explicitly construct a minimal dict with `verdict="unknown"` and `schema_validated=False`. Router MUST treat this as equivalent to `unknown`.

4. **Business verdicts follow normal routing**: `approve`, `request_changes`, `comment` are processed according to Router's LLM-driven or rule-based logic.

### Router Behavior Examples

| Scenario | ReviewOutcome | Router Action |
|----------|---------------|---------------|
| **Reviewer timeout** | `verdict="unknown", schema_validated=False` | Fallback to rule-based routing (ignore all other fields) |
| **Safety block detected** | `verdict="blocked", severity="critical"` | Force escalate to human review |
| **Clean review** | `verdict="approve", severity="low", blocker_count=0` | Proceed to publisher |
| **Issues found** | `verdict="request_changes", severity="high", blocker_count=3` | Route to fixer or escalate based on blocker_count |
| **Suggestions only** | `verdict="comment", severity="medium", blocker_count=0` | Proceed to publisher (attach suggestions) |

### Field Definitions

| Field | Definition | Source |
|-------|------------|--------|
| `blocker_count` | Count of `review_comments` where `severity in {"high", "critical"}` | Computed from `state["review_comments"]` |
| `severity` | Worst severity across all comments: `max(comment.severity for comment in review_comments)`. If no comments exist, defaults to `"low"`. | Computed from `state["review_comments"]` |
| `diff_truncated` | Whether the PR diff was truncated due to size limits | From `state["diff_truncated"]` |

**Severity Mapping Note**: The current `reviewer_node` outputs `review_severity` with possible value `"none"` when no issues are found. `ReviewOutcome.severity` does NOT include `"none"` - implementations MUST map `"none"` to `"low"` as the baseline.

### Current Implementation Evidence

As of `main` branch, `reviewer_node` (see `langgraph_orchestrator.py` lines 3583-3588) outputs:
- `review_comments: List[Dict]` where each comment contains `severity` and `message` fields
- `review_severity: "none" | "low" | "medium" | "high" | "critical"` (aggregate severity)

This confirms `blocker_count` can be deterministically computed from `state["review_comments"]`.

### Schema Evolution Strategy

This schema follows **additive-only evolution**:
- New optional fields may be added without version bump
- Existing field semantics MUST NOT change
- Breaking changes require `schema_version` bump
- Router MUST handle unknown `schema_version` by falling back to deterministic routing

### Implementation Items

| Item | Description | Status |
|------|-------------|--------|
| B-6.1 Schema Definition | Add `ReviewOutcome` to `core/flow/schema.py` | Pending |
| B-6.2 reviewer_node Integration | Wrap review result in `ReviewOutcome` before return | Pending |
| B-6.3 State Update | Add `review_outcome: dict` to `AgentState` | Pending |
| B-6.4 Unit Tests | Test all verdict scenarios | Pending |

### Blueprint Alignment

| Blueprint Guarantee | Implementation |
|--------------------|----------------|
| Deterministic | `unknown` verdict triggers fallback to rule-based routing |
| Safe by Design | `blocked` verdict forces escalate |
| Self-Governed | Router can make dynamic decisions based on verdict |

### Dependencies

- **Depends on**: Phase 3 (Security & Reliability) - Completed
- **Blocks**: EPIC C Stage 1 (C-5 Review Routing Pilot)
