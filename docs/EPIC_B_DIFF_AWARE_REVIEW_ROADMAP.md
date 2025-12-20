# EPIC B: Diff-Aware Review Plumbing - Roadmap

> Last Updated: 2025-12-20

## Overview

EPIC B focuses on implementing intelligent PR review with inline comments, ensuring reviews are generated correctly and posted reliably to GitHub.

## Status Summary

| Phase | Status | PR |
|-------|--------|-----|
| Phase 1: Quick Wins | Completed | [#2785](https://github.com/RC918/morningai/pull/2785) |
| Phase 2: Publishing Correctness | Completed | [#2788](https://github.com/RC918/morningai/pull/2788) |
| Phase 3: Security & Reliability | Pending | - |

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

## Phase 3: Security & Reliability (Pending)

Security improvements and additional reliability enhancements.

### Pending Items

| Priority | Item | Description | Status |
|----------|------|-------------|--------|
| P1 | Secrets exposure mitigation | `state["diff_content"]` stores raw unsanitized diff which is persisted via LangGraph checkpointer | Pending |
| P2 | commit_id validation | Verify if missing commit_id in `post_pr_review()` is root cause of 422 errors | Needs Investigation |
| P2 | Code duplication refactor | Unify file-level delivery logic in publisher_node (Gemini feedback) | Pending |
| P3 | JSON repair call | When JSON parse fails, retry with LLM to repair truncated JSON | Pending |

### Security Audit Finding

**Issue**: `state["diff_content"]` stores the raw unsanitized diff content.

**Risk**: This content is persisted via LangGraph checkpointer (PostgreSQL/Redis), potentially exposing secrets that appear in diffs.

**Recommended Fix Options**:
1. Sanitize diff content before storing in state (using existing `sanitize_diff_content()`)
2. Store only diff metadata/hash instead of full content
3. Add TTL to checkpointer data to limit exposure window

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
| [#2788](https://github.com/RC918/morningai/pull/2788) | Phase 2 Line Drift Protection | Open |

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
