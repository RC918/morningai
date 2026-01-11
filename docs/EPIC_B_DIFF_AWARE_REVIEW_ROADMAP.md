# EPIC B: Diff-Aware Review Plumbing - Roadmap

> Last Updated: 2026-01-11

## Overview

EPIC B focuses on implementing intelligent PR review with inline comments, ensuring reviews are generated correctly and posted reliably to GitHub.

**North Star Goal**: Enable the MorningAI Reviewer Agent to achieve and surpass the review capabilities of GitHub Copilot and Gemini Code Assist, realizing the Blueprint's "self-review" vision. (讓 MorningAI Reviewer Agent 達到並超越 GitHub Copilot 和 Gemini Code Assist 的審查能力，實現 Blueprint 的「自己審查」願景。)

## Status Summary

| Phase | Status | PR/Issue |
|-------|--------|----------|
| Phase 1: Quick Wins | Completed | [#2785](https://github.com/RC918/morningai/pull/2785) |
| Phase 2: Publishing Correctness | Completed | [#2788](https://github.com/RC918/morningai/pull/2788), [#2803](https://github.com/RC918/morningai/pull/2803) |
| Phase 3: Security & Reliability | Completed | [#2809](https://github.com/RC918/morningai/pull/2809), [#2829](https://github.com/RC918/morningai/pull/2829), [#2836](https://github.com/RC918/morningai/pull/2836) |
| Phase 4: Checks API (P6) | Planned | - |
| **Phase 6: Router Interface (B-6)** | **Completed** | [#3130](https://github.com/RC918/morningai/issues/3130), [#3135](https://github.com/RC918/morningai/pull/3135) |
| **Phase 7: Copilot/Gemini Parity (B-7 to B-10)** | **Planning** | See below |
| **Phase 8: Copilot/Gemini Superiority (B-11 to B-13)** | **Planning** | See below |

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

## Phase 6: Router Interface (B-6) - Completed

> **Status**: Completed
> **Issue**: [#3130](https://github.com/RC918/morningai/issues/3130)
> **Target**: EPIC C Stage 1 (C-5 Review Routing Pilot)

> **Implementation Complete**: The `ReviewOutcome` schema is implemented in `core/routing/review_outcome.py` and integrated into `reviewer_node`, `router_node`, and `fixer_node`. See Implementation Items below for details.

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

| Item | Description | Status | Evidence |
|------|-------------|--------|----------|
| B-6.1 Schema Definition | Add `ReviewOutcome` to `core/routing/review_outcome.py` | **Done** | `core/routing/review_outcome.py` (325 lines) |
| B-6.2 reviewer_node Integration | Wrap review result in `ReviewOutcome` before return | **Done** | `langgraph_orchestrator.py:5567-5574` |
| B-6.3 State Update | Add `review_outcome: dict` to `AgentState` | **Done** | `langgraph_orchestrator.py:2421` |
| B-6.4 Unit Tests | Test all verdict scenarios | **Done** | `tests/test_review_outcome.py` (50 tests, 100% pass) |

> **Note**: Implementation location changed from `core/flow/schema.py` to `core/routing/review_outcome.py` for better module organization. The schema is consumed by `router_node` (lines 5825-5829) and `fixer_node` gate (lines 4324-4325).

### Blueprint Alignment

| Blueprint Guarantee | Implementation |
|--------------------|----------------|
| Deterministic | `unknown` verdict triggers fallback to rule-based routing |
| Safe by Design | `blocked` verdict forces escalate |
| Self-Governed | Router can make dynamic decisions based on verdict |

### Dependencies

- **Depends on**: Phase 3 (Security & Reliability) - Completed
- **Blocks**: EPIC C Stage 1 (C-5 Review Routing Pilot)

---

## Phase 7: Copilot/Gemini Parity (B-7 to B-10) - Planning

> **Status**: Planning
> **Prerequisite**: None - B-7/B-8/B-9 are READ-ONLY perception enhancements, not dangerous operations
> **Target**: Achieve feature parity with GitHub Copilot and Gemini Code Assist
> **Blueprint Note**: Safety Governor v2 (EPIC E) is a POST-PROCESSING layer for OUTPUT protection, not a gate for INPUT perception capabilities. B-7/B-8/B-9 enhance Reviewer's ability to "see" and "understand" code - they don't generate code or execute dangerous actions.

### Overview

Phase 7 focuses on **integration gaps** and **new components** to enhance Reviewer Agent capabilities:
- **B-7**: Integration gap - CodeIndexer/KnowledgeGraphManager exist but not integrated with Reviewer
- **B-8**: New component - BugFixWorkflow is NOT suitable (see Component Audit Note below), requires new SemanticAnalyzer
- **B-9**: New capability - Multi-Specialist Review

### Gap Analysis (Reviewer-Appropriate Scope)

| Capability | GitHub Copilot | Gemini Code Assist | MorningAI Current | MorningAI Target | Notes |
|------------|---------------|-------------------|-------------------|------------------|-------|
| Codebase Context | ✓ Full repo | ✓ Full repo | ❌ PR diff only | ✓ B-7 | Reviewer scope |
| Semantic Understanding | ✓ LSP/AST | ✓ LSP/AST | ❌ None | ✓ B-8 | Reviewer scope |
| Multi-Specialist Review | ✓ Multiple passes | ✓ Multiple passes | ❌ Single pass | ✓ B-9 | Reviewer scope |
| ~~Auto-Fix Generation~~ | ✓ One-click fix | ✓ One-click fix | ❌ Text only | → EPIC D | **Fixer Agent scope** |

> **Blueprint Alignment Note**: Auto-Fix Generation is NOT a Reviewer Agent capability per Blueprint Section 3.3. This belongs to Fixer Agent (EPIC D). Reviewer Agent can only suggest fixes in text form.

### Existing Components (Integration Targets)

| Component | Location | Lines | Current Usage | B-7/B-8 Suitability |
|-----------|----------|-------|---------------|---------------------|
| CodeIndexer | `agents/dev_agent/knowledge_graph/code_indexer.py` | 385 | dev_agent only | ✓ B-7 suitable (READ-ONLY) |
| KnowledgeGraphManager | `agents/dev_agent/knowledge_graph/knowledge_graph_manager.py` | 660 | dev_agent only | ✓ B-7 suitable (READ-ONLY) |
| BugFixWorkflow | `agents/dev_agent/workflows/bug_fix_workflow.py` | 975 | dev_agent only | ❌ NOT suitable for B-8 |

> **Component Audit Note (2026-01-11)**:
> - **CodeIndexer**: READ-ONLY perception component. Parses code using AST/regex, generates embeddings. Safe for Reviewer Agent integration.
> - **KnowledgeGraphManager**: READ-ONLY search/retrieval component. Handles embeddings, vector similarity search. Safe for Reviewer Agent integration.
> - **BugFixWorkflow**: ❌ **NOT suitable for B-8**. This is a full **Coder Agent workflow** (Parse Issue → Reproduce → Analyze → Generate Fix → Apply Fix → Test → Create PR). The LSP/AST capabilities are tightly coupled with fix generation. **B-8 requires a new, standalone LSP/AST component** that is READ-ONLY and respects Agent Separation Principle.

---

### B-7: Codebase Context Integration

> **Type**: Integration Gap
> **Issue**: TBD
> **Effort**: Medium (3-5 days)

**Problem**: `llm_reviewer_adapter.py` only receives PR diff, cannot understand how changes affect other files.

**Solution**: Integrate `dev_agent/knowledge_graph/code_indexer.py` with `reviewer_node`.

**Implementation Plan**:

1. **B-7.1 Context Retriever Service**:
   - Create `orchestrator/review_context/context_retriever.py`
   - Expose `get_relevant_context(changed_files: List[str]) -> List[ContextFile]`
   - Use CodeIndexer to find files that import/export from changed files

2. **B-7.2 reviewer_node Integration**:
   - Modify `reviewer_node` to call context_retriever before LLM review
   - Pass `context_files` to `generate_llm_review()`

3. **B-7.3 Prompt Enhancement**:
   - Extend `_get_diff_aware_system_prompt()` to include context awareness
   - Add "Related files that may be affected" section

4. **B-7.4 Token Budget Management**:
   - Extend `truncate_diff_for_token_budget()` to handle context files
   - Prioritize: PR diff > direct importers > indirect importers

**Acceptance Criteria**:
- [ ] reviewer_node can access codebase context
- [ ] LLM prompt includes relevant context files
- [ ] Token budget respects context file limits
- [ ] Unit tests for context retrieval

---

### B-8: Semantic Understanding Integration

> **Type**: New Component (NOT Integration Gap)
> **Issue**: TBD
> **Effort**: Medium-High (5-7 days)

**Problem**: Reviewer cannot detect breaking changes, unused imports, or type mismatches.

**Solution**: ~~Integrate LSP/AST analysis from `dev_agent/workflows/bug_fix_workflow.py`.~~ **REVISED**: Create a new, standalone `SemanticAnalyzer` component that is READ-ONLY and respects Agent Separation Principle.

> **Audit Finding (2026-01-11)**: BugFixWorkflow is NOT suitable for B-8 integration. It is a full Coder Agent workflow (Parse Issue → Reproduce → Analyze → Generate Fix → Apply Fix → Test → Create PR). The LSP/AST capabilities are tightly coupled with fix generation, violating Blueprint Section 3.3 Agent Separation Principle.

**Implementation Plan**:

1. **B-8.1 Semantic Analyzer Service**:
   - Create `orchestrator/review_context/semantic_analyzer.py`
   - Expose `analyze_breaking_changes(diff: str, context: List[ContextFile]) -> List[BreakingChange]`
   - Use AST parsing to detect: public API changes, interface mismatches, unused imports

2. **B-8.2 reviewer_node Integration**:
   - Call semantic_analyzer after context retrieval
   - Pass `breaking_changes` to LLM as structured input

3. **B-8.3 Prompt Enhancement**:
   - Add "Detected Breaking Changes" section to prompt
   - LLM validates and expands on detected issues

**Acceptance Criteria**:
- [ ] Semantic analyzer detects public API changes
- [ ] Semantic analyzer detects unused imports
- [ ] LLM prompt includes breaking change warnings
- [ ] Unit tests for semantic analysis

---

### B-9: Multi-Specialist Review (Parallel Collaboration)

> **Type**: New Capability
> **Issue**: TBD
> **Effort**: High (5-7 days)
> **Blueprint Alignment**: Section 7 "Parallel Collaboration" - Multiple agents work simultaneously

**Problem**: Single LLM call cannot cover all review aspects (security, performance, architecture).

**Solution**: Implement parallel multi-specialist review following Blueprint Section 7 "Parallel Collaboration" pattern.

> **Note**: This is NOT Debate Engine v2 (which is "Adversarial Collaboration" for Left vs Right → Judge). This is "Parallel Collaboration" where multiple specialist reviewers work simultaneously and their findings are aggregated.

**Implementation Plan**:

1. **B-9.1 Review Specialist Prompts**:
   - Create specialized prompts for security, performance, architecture review
   - Each specialist focuses on specific review aspects
   - All specialists are still Reviewer Agent instances (not separate agent types)

2. **B-9.2 Parallel Execution**:
   - Execute specialist reviews in parallel
   - Each specialist produces `ReviewFindings` for their domain

3. **B-9.3 Findings Aggregator**:
   - Aggregate findings from all specialists
   - Deduplicate overlapping issues
   - Prioritize by severity

4. **B-9.4 Feature Flag**:
   - `USE_MULTI_SPECIALIST_REVIEW` (default: False)
   - Gradual rollout with A/B testing

**Acceptance Criteria**:
- [ ] Three specialist review prompts implemented
- [ ] Parallel execution of specialist reviews
- [ ] Findings aggregator deduplicates and prioritizes
- [ ] Feature flag controls rollout
- [ ] Telemetry tracks multi-specialist vs single-pass performance

---

### ~~B-10: Auto-Fix Integration~~ → REMOVED (OUT OF SCOPE)

> **Status**: REMOVED FROM EPIC B
> **Reason**: Violates Blueprint Agent Separation Principle - Fixer capability already exists in EPIC D
> **Note**: This is NOT a "move" - EPIC D already has Self-Correction Loop (D-4) for auto-fix

**Blueprint Violation Analysis**:

Per Blueprint Section 3.3 "Agent Catalog V2" and Section 7 "Cross-Agent Collaboration Model":
- **Reviewer Agent** → Reviews code, identifies issues, provides feedback
- **Coding Agent** → Writes/modifies code
- **Sequential Collaboration**: Coding → Reviewer → Test → Deploy

Giving Reviewer Agent the ability to generate and apply code fixes violates the separation of concerns principle. The correct architecture is:

```
Reviewer Agent                    Fixer Agent (EPIC D)
     │                                 │
     ▼                                 │
識別問題 + 建議修復方向 ──────────────►  接收建議
(text description only)                │
     │                                 ▼
     ▼                            生成實際程式碼
ReviewOutcome {                        │
  verdict: "request_changes",          ▼
  suggested_fixes: [                HITL Gate
    { description: "..." }             │
  ]                                    ▼
}                                 套用修復
```

**What Reviewer Agent CAN do (within EPIC B scope)**:
- Identify issues in code
- Describe what should be fixed (text)
- Suggest fix direction (text)
- Output `suggested_fixes` as text descriptions

**What Reviewer Agent CANNOT do (belongs to Fixer Agent)**:
- Generate actual code fixes
- Apply code changes
- Use GitHub suggestion syntax with code blocks

**Recommendation**: Create follow-up issue in EPIC D for "Fixer Agent: Review-to-Fix Integration"

---

## Phase 8: Copilot/Gemini Superiority (B-11 to B-13) - Planning

> **Status**: Planning
> **Prerequisite**: Phase 7 (B-7 to B-9) should be completed first
> **Target**: Exceed GitHub Copilot and Gemini Code Assist capabilities (within Reviewer Agent scope)
> **Blueprint Alignment**: All capabilities must respect Agent Separation Principle

### Overview

Phase 8 focuses on **new capabilities** within Reviewer Agent's appropriate scope that will differentiate MorningAI from competitors.

> **Blueprint Alignment**: All Phase 8 capabilities must respect the Agent Separation Principle (Blueprint Section 3.3). Reviewer Agent can FLAG issues and SUGGEST actions, but cannot GENERATE code or APPLY fixes. Code generation belongs to Coding Agent/Fixer Agent, test generation belongs to Test Agent v2.

---

### ~~B-11: Test Generation~~ → MOVED TO Test Agent v2 Roadmap

> **Status**: REMOVED FROM EPIC B
> **Reason**: Violates Blueprint Agent Separation Principle
> **Follow-up**: See Test Agent v2 roadmap (Blueprint Section 3.3)

**Blueprint Violation Analysis**:

Per Blueprint Section 3.3 "Agent Catalog V2":
- **Reviewer Agent** → Reviews code, identifies issues, provides feedback
- **Test Agent v2** → Generates and runs tests
- **Sequential Collaboration**: Coding → Reviewer → **Test** → Deploy

Giving Reviewer Agent the ability to generate test code violates the separation of concerns principle. The correct architecture is:

```
Reviewer Agent                    Test Agent v2
     │                                 │
     ▼                                 │
識別測試覆蓋缺口 ─────────────────────►  接收覆蓋缺口報告
(flag missing coverage)                │
     │                                 ▼
     ▼                            生成測試程式碼
ReviewOutcome {                        │
  verdict: "request_changes",          ▼
  missing_test_coverage: [         執行測試
    { function: "...",                 │
      reason: "..." }                  ▼
  ]                               回報結果
}
```

**What Reviewer Agent CAN do (within EPIC B scope)**:
- Detect functions/classes without test coverage
- Flag missing test coverage in review
- Describe what tests are needed (text)

**What Reviewer Agent CANNOT do (belongs to Test Agent v2)**:
- Generate actual test code
- Execute tests
- Validate test results

**Recommendation**: Create Test Agent v2 roadmap for "Test Generation from Review Feedback"

**Alternative B-11 for EPIC B**: Test Coverage Flagging (Reviewer-appropriate scope)

> **Type**: New Capability (Reviewer-appropriate)
> **Effort**: Medium (3-5 days)

**Implementation Plan** (Reviewer-appropriate scope):

1. **B-11.1 Test Coverage Analyzer**:
   - Create `orchestrator/review_context/test_coverage_analyzer.py`
   - Detect functions/classes without test coverage
   - Parse existing test files to understand coverage patterns

2. **B-11.2 Review Integration**:
   - Add `missing_test_coverage: List[CoverageGap]` to the `ReviewOutcome` schema to formalize the agent handoff
   - Populate this structured data with uncovered code
   - Generate a "Missing Test Coverage" section in the review from this data
   - Suggest what types of tests are needed (unit, integration, etc.)

**Acceptance Criteria**:
- [ ] Test coverage analyzer detects uncovered code
- [ ] `ReviewOutcome` schema is extended with a structured `missing_test_coverage` field
- [ ] Review flags missing coverage with descriptions
- [ ] Suggestions describe what tests are needed (not actual code)

---

### B-12: Dependency Analysis (Flagging Only)

> **Type**: Integration + Extension
> **Issue**: TBD
> **Effort**: Medium (3-5 days)
> **Blueprint Alignment**: Reviewer Agent flags issues, does NOT fix them

**Problem**: Reviewer doesn't check for outdated or vulnerable dependencies.

**Solution**: Integrate dependency analysis into review flow for **flagging purposes only**.

> **Scope Clarification**: Per Blueprint Agent Separation Principle, Reviewer Agent can only FLAG dependency issues. Actual dependency updates/fixes belong to Coding Agent or dedicated Dependency Agent.

**Implementation Plan**:

1. **B-12.1 Dependency Analyzer**:
   - Create `orchestrator/review_context/dependency_analyzer.py`
   - Parse package.json, requirements.txt, pyproject.toml
   - Check for: outdated deps, known vulnerabilities, license issues

2. **B-12.2 Review Integration**:
   - If PR modifies dependency files, trigger analysis
   - Add "Dependency Issues" section to review
   - **Output is text warnings only, not code changes**

3. **B-12.3 External Service Integration**:
   - Optional: Integrate with npm audit, pip-audit, Snyk API
   - Cache results to avoid repeated API calls

**What Reviewer Agent CAN do**:
- Flag outdated dependencies
- Flag known vulnerabilities
- Flag license issues
- Recommend actions (text descriptions)

**What Reviewer Agent CANNOT do**:
- Update package.json/requirements.txt
- Run npm update/pip install
- Apply dependency fixes

**Acceptance Criteria**:
- [ ] Dependency analyzer parses common formats
- [ ] Outdated dependencies flagged (text warning)
- [ ] Known vulnerabilities flagged (text warning)
- [ ] Review includes dependency warnings (not fixes)

---

### B-13: Real-time Feedback Loop

> **Type**: New Capability
> **Issue**: TBD
> **Effort**: High (7-10 days)

**Problem**: One-shot review, no ability to respond to developer questions.

**Solution**: Implement interactive review conversation.

**Implementation Plan**:

1. **B-13.1 Review Thread Handler**:
   - Create `orchestrator/webhooks/handlers/review_thread_handler.py`
   - Handle `pull_request_review_comment` webhook events
   - Detect @mentions or replies to MorningAI comments

2. **B-13.2 Conversation Context**:
   - Store review conversation in Memory v2 (EPIC G dependency)
   - Maintain context across multiple interactions

3. **B-13.3 Response Generator**:
   - Generate contextual responses to developer questions
   - Can clarify, provide more detail, or revise suggestions

4. **B-13.4 Rate Limiting**:
   - Prevent infinite loops (max 3 responses per thread)
   - Cooldown period between responses

**Acceptance Criteria**:
- [ ] Webhook handler processes review comments
- [ ] Conversation context maintained
- [ ] Responses are contextually relevant
- [ ] Rate limiting prevents abuse

---

## Phase 7-8 Dependencies

```
Phase 7: Copilot/Gemini Parity (Reviewer-appropriate scope)
    │
    │   ✓ NO EPIC E PREREQUISITE - B-7/B-8/B-9 are READ-ONLY perception enhancements
    │   (Safety Governor v2 is POST-PROCESSING for OUTPUT, not INPUT gating)
    │
    ├── B-7 (Codebase Context) ──┬──► B-9 (Multi-Specialist Review)
    │                            │
    └── B-8 (Semantic)      ─────┘
    
    ╳ B-10 (Auto-Fix) → REMOVED (OUT OF SCOPE - already in EPIC D)
                                 │
                                 ▼
Phase 8: Copilot/Gemini Superiority (Reviewer-appropriate scope)
    │
    ├── B-11 (Test Coverage Flagging) - Reviewer flags only, Test Agent v2 generates
    │   ╳ Test Generation → MOVED TO Test Agent v2 Roadmap
    │
    ├── B-12 (Dependency Flagging) - Reviewer flags only, no fixes
    │
    └── B-13 (Feedback Loop) ──► EPIC G (Memory v2) dependency

Cross-Agent Handoffs (Blueprint Sequential Collaboration):
    Reviewer Agent ──► Fixer Agent (EPIC D) for code fixes
    Reviewer Agent ──► Test Agent v2 for test generation
```

---

## Success Metrics (Reviewer-Appropriate Scope)

| Metric | Current | Phase 7 Target | Phase 8 Target | Notes |
|--------|---------|----------------|----------------|-------|
| Review Context | PR diff only | Full codebase | Full codebase | B-7 |
| Breaking Change Detection | 0% | >80% | >90% | B-8 |
| Multi-Specialist Coverage | 0% | >70% | >85% | B-9 |
| Test Coverage Flagging | 0% | 0% | >60% | B-11 (flagging only) |
| Dependency Issue Flagging | 0% | 0% | >80% | B-12 (flagging only) |
| Developer Satisfaction | Baseline | +20% | +40% | Overall |

**Removed Metrics** (belong to other agents per Blueprint):
- ~~Auto-Fix Applicability~~ → Fixer Agent (EPIC D) metric
- ~~Test Generation Quality~~ → Test Agent v2 metric

---

## Timeline Estimate (Revised)

| Phase | Estimated Duration | Dependencies | Status | Type |
|-------|-------------------|--------------|--------|------|
| B-7 | 3-5 days | None | Planning | Integration Gap |
| B-8 | 5-7 days | B-7 | Planning | **New Component** |
| B-9 | 5-7 days | B-7, B-8 | Planning | New Capability |
| ~~B-10~~ | ~~3-5 days~~ | ~~B-7~~ | REMOVED (OUT OF SCOPE) | - |
| B-11 | 3-5 days | Phase 7 | Planning (flagging only) | New Capability |
| B-12 | 3-5 days | Phase 7 | Planning (flagging only) | New Capability |
| B-13 | 7-10 days | Phase 7, EPIC G | Planning | New Capability |

**Total Estimated Duration**: 5-8 weeks (can start immediately)

**Note**: B-8 duration increased from 3-5 to 5-7 days because it requires a **new SemanticAnalyzer component** (BugFixWorkflow is NOT suitable per Component Audit 2026-01-11). No EPIC E prerequisite - B-7/B-8/B-9 are READ-ONLY perception enhancements that don't require Safety Governor gating.

**Cross-Agent Dependencies** (for full Blueprint vision):
- EPIC D (Fixer Agent): Receives fix suggestions from Reviewer, generates actual code fixes
- Test Agent v2: Receives coverage flags from Reviewer, generates actual test code
