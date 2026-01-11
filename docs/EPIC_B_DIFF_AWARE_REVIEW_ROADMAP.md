# EPIC B: Diff-Aware Review Plumbing - Roadmap

> Last Updated: 2026-01-11

## Overview

EPIC B focuses on implementing intelligent PR review with inline comments, ensuring reviews are generated correctly and posted reliably to GitHub.

**North Star Goal**: 讓 MorningAI Reviewer Agent 達到並超越 GitHub Copilot 和 Gemini Code Assist 的審查能力，實現 Blueprint 的「自己審查」願景。

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
> **Prerequisite**: EPIC E (Safety Governor v2) should be completed first
> **Target**: Achieve feature parity with GitHub Copilot and Gemini Code Assist

### Overview

Phase 7 focuses on **integration gaps** - capabilities that already exist in `agents/dev_agent/` but are NOT integrated with the Reviewer Agent (`orchestrator/llm_reviewer_adapter.py`).

### Gap Analysis

| Capability | GitHub Copilot | Gemini Code Assist | MorningAI Current | MorningAI Target |
|------------|---------------|-------------------|-------------------|------------------|
| Codebase Context | ✓ Full repo | ✓ Full repo | ❌ PR diff only | ✓ B-7 |
| Semantic Understanding | ✓ LSP/AST | ✓ LSP/AST | ❌ None | ✓ B-8 |
| Multi-Agent Review | ✓ Multiple passes | ✓ Multiple passes | ❌ Single pass | ✓ B-9 |
| Auto-Fix Generation | ✓ One-click fix | ✓ One-click fix | ❌ Text suggestion only | ✓ B-10 |

### Existing Components (Integration Targets)

| Component | Location | Lines | Current Usage |
|-----------|----------|-------|---------------|
| CodeIndexer | `agents/dev_agent/knowledge_graph/code_indexer.py` | 385 | dev_agent only |
| KnowledgeGraphManager | `agents/dev_agent/knowledge_graph/knowledge_graph_manager.py` | 24030 | dev_agent only |
| BugFixWorkflow (LSP/AST) | `agents/dev_agent/workflows/bug_fix_workflow.py` | 975 | dev_agent only |

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

> **Type**: Integration Gap
> **Issue**: TBD
> **Effort**: Medium (3-5 days)

**Problem**: Reviewer cannot detect breaking changes, unused imports, or type mismatches.

**Solution**: Integrate LSP/AST analysis from `dev_agent/workflows/bug_fix_workflow.py`.

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

### B-9: Multi-Agent Review

> **Type**: New Capability
> **Issue**: TBD
> **Effort**: High (5-7 days)

**Problem**: Single LLM call cannot cover all review aspects (security, performance, architecture).

**Solution**: Implement multi-pass review using Debate Engine v2 (Blueprint 3.3).

**Implementation Plan**:

1. **B-9.1 Review Specialist Agents**:
   - Create `orchestrator/review_agents/security_reviewer.py`
   - Create `orchestrator/review_agents/performance_reviewer.py`
   - Create `orchestrator/review_agents/architecture_reviewer.py`
   - Each agent has specialized prompt and focus area

2. **B-9.2 Review Orchestrator**:
   - Create `orchestrator/review_agents/review_orchestrator.py`
   - Parallel execution of specialist agents
   - Aggregation of findings with deduplication

3. **B-9.3 Judge Agent Integration**:
   - Use Debate Engine v2 for conflict resolution
   - Judge synthesizes final review from specialist outputs

4. **B-9.4 Feature Flag**:
   - `USE_MULTI_AGENT_REVIEW` (default: False)
   - Gradual rollout with A/B testing

**Acceptance Criteria**:
- [ ] Three specialist reviewers implemented
- [ ] Review orchestrator aggregates findings
- [ ] Judge resolves conflicts between specialists
- [ ] Feature flag controls rollout
- [ ] Telemetry tracks multi-agent vs single-agent performance

---

### B-10: Auto-Fix Integration

> **Type**: Integration Gap
> **Issue**: TBD
> **Effort**: Medium (3-5 days)

**Problem**: Reviewer suggests fixes in text, but cannot auto-apply them.

**Solution**: Integrate reviewer → fixer flow using `dev_agent/workflows/bug_fix_workflow.py`.

**Implementation Plan**:

1. **B-10.1 Fix Generator Service**:
   - Create `orchestrator/review_context/fix_generator.py`
   - Expose `generate_fix(comment: ReviewComment) -> Optional[CodeFix]`
   - Use LLM to generate copy-paste ready code

2. **B-10.2 ReviewOutcome Extension**:
   - Add `auto_fixes: List[CodeFix]` to ReviewOutcome schema
   - Each fix includes: file, line_range, original_code, fixed_code

3. **B-10.3 GitHub Suggestion Integration**:
   - Use GitHub's suggestion syntax in review comments
   - Format: ` ```suggestion\nfixed_code\n``` `
   - Users can apply fix with one click

4. **B-10.4 Fixer Node Integration**:
   - If `verdict == "request_changes"` and `auto_fixes` available
   - Router can optionally auto-apply fixes (with HITL gate)

**Acceptance Criteria**:
- [ ] Fix generator produces valid code fixes
- [ ] GitHub suggestion syntax used in comments
- [ ] ReviewOutcome includes auto_fixes
- [ ] HITL gate for auto-apply (optional)

---

## Phase 8: Copilot/Gemini Superiority (B-11 to B-13) - Planning

> **Status**: Planning
> **Prerequisite**: Phase 7 (B-7 to B-10) should be completed first
> **Target**: Exceed GitHub Copilot and Gemini Code Assist capabilities

### Overview

Phase 8 focuses on **new capabilities** that don't exist in the current codebase and will differentiate MorningAI from competitors.

---

### B-11: Test Generation

> **Type**: New Capability
> **Issue**: TBD
> **Effort**: High (5-7 days)

**Problem**: Reviewer cannot suggest missing test cases for new code.

**Solution**: Implement test generation capability.

**Implementation Plan**:

1. **B-11.1 Test Coverage Analyzer**:
   - Create `orchestrator/review_context/test_coverage_analyzer.py`
   - Detect functions/classes without test coverage
   - Parse existing test files to understand test patterns

2. **B-11.2 Test Generator**:
   - Create `orchestrator/review_context/test_generator.py`
   - Generate test cases for uncovered code
   - Follow existing test patterns in the repo

3. **B-11.3 Review Integration**:
   - Add "Missing Test Coverage" section to review
   - Include generated test code as suggestions

**Acceptance Criteria**:
- [ ] Test coverage analyzer detects uncovered code
- [ ] Test generator produces valid test code
- [ ] Generated tests follow repo conventions
- [ ] Review includes test suggestions

---

### B-12: Dependency Analysis Integration

> **Type**: Integration + Extension
> **Issue**: TBD
> **Effort**: Medium (3-5 days)

**Problem**: Reviewer doesn't check for outdated or vulnerable dependencies.

**Solution**: Integrate dependency analysis into review flow.

**Implementation Plan**:

1. **B-12.1 Dependency Analyzer**:
   - Create `orchestrator/review_context/dependency_analyzer.py`
   - Parse package.json, requirements.txt, pyproject.toml
   - Check for: outdated deps, known vulnerabilities, license issues

2. **B-12.2 Review Integration**:
   - If PR modifies dependency files, trigger analysis
   - Add "Dependency Issues" section to review

3. **B-12.3 External Service Integration**:
   - Optional: Integrate with npm audit, pip-audit, Snyk API
   - Cache results to avoid repeated API calls

**Acceptance Criteria**:
- [ ] Dependency analyzer parses common formats
- [ ] Outdated dependencies flagged
- [ ] Known vulnerabilities flagged
- [ ] Review includes dependency warnings

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
EPIC E (Safety Governor v2) - PREREQUISITE
    │
    ▼
Phase 7: Copilot/Gemini Parity
    │
    ├── B-7 (Codebase Context) ──┐
    │                            │
    ├── B-8 (Semantic)      ─────┼──► B-9 (Multi-Agent)
    │                            │
    └── B-10 (Auto-Fix) ─────────┘
                                 │
                                 ▼
Phase 8: Copilot/Gemini Superiority
    │
    ├── B-11 (Test Gen)
    │
    ├── B-12 (Deps)
    │
    └── B-13 (Feedback Loop) ──► EPIC G (Memory v2) dependency
```

---

## Success Metrics

| Metric | Current | Phase 7 Target | Phase 8 Target |
|--------|---------|----------------|----------------|
| Review Context | PR diff only | Full codebase | Full codebase |
| Breaking Change Detection | 0% | >80% | >90% |
| Auto-Fix Applicability | 0% | >50% | >70% |
| Test Coverage Suggestions | 0% | 0% | >60% |
| Developer Satisfaction | Baseline | +20% | +40% |

---

## Timeline Estimate

| Phase | Estimated Duration | Dependencies |
|-------|-------------------|--------------|
| B-7 | 3-5 days | EPIC E |
| B-8 | 3-5 days | B-7 |
| B-9 | 5-7 days | B-7, B-8 |
| B-10 | 3-5 days | B-7 |
| B-11 | 5-7 days | Phase 7 |
| B-12 | 3-5 days | Phase 7 |
| B-13 | 7-10 days | Phase 7, EPIC G |

**Total Estimated Duration**: 6-10 weeks (after EPIC E completion)
