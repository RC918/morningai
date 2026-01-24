# EPIC B-18: Review Comment Feedback (Human-in-the-Loop Learning)

**Issue**: TBD (to be created)
**Blueprint Reference**: Section 5.1 (Memory v2), Section 7 (Human-in-the-Loop)
**Status**: Planning
**Last Updated**: 2026-01-24

---

## Executive Summary

EPIC B-18 implements a **human feedback mechanism** for review comments, enabling the MorningAI Reviewer Agent to learn from human corrections. This addresses the root cause of "weak suggestions" - the system currently accumulates positive experience but has no mechanism to learn "what NOT to suggest."

### Problem Statement

The current Reviewer Agent (B-13 Real-time Feedback Loop) can:
- Save review outcomes to Knowledge Base
- Retrieve past review patterns for similar code

However, it **cannot**:
- Capture when a human dismisses/rejects a specific review comment
- Store negative examples ("this suggestion was wrong")
- Avoid repeating the same false positive suggestions

**Evidence**: MorningAI Reviewer Agent suggested "parse_line lacks error handling for malformed matches" on PR #4309, which is technically incorrect (Python regex guarantees all capture groups exist if match succeeds). Without a feedback mechanism, this false positive pattern will be repeated.

### Solution: Human Feedback Loop

```
                    MorningAI Review Comment
                            │
                            ▼
                    Human Response
                    ┌───────┴───────┐
                    │               │
                    ▼               ▼
               [Accept]        [Dismiss/Reject]
                    │               │
                    ▼               ▼
            Positive Example   Negative Example
                    │               │
                    └───────┬───────┘
                            ▼
                    Knowledge Base (Memory v2)
                            │
                            ▼
                    Future Reviews
                    (retrieve both positive AND negative patterns)
```

---

## Architecture Design

### B-18.1: Feedback Signal Capture

**Objective**: Capture human accept/dismiss signals from GitHub PR review comments.

**Implementation**:

1. **Webhook Handler Extension**
   - Extend `review_thread_handler.py` to detect:
     - Comment resolved/unresolved status changes
     - Emoji reactions (thumbs up = accept, thumbs down = reject)
     - Reply patterns ("good catch", "false positive", "not applicable")
   
2. **Feedback Classification**
   ```python
   class ReviewCommentFeedback(Enum):
       ACCEPTED = "accepted"           # Human agrees with suggestion
       REJECTED = "rejected"           # Human explicitly rejects
       DISMISSED = "dismissed"         # Human resolves without action
       CLARIFIED = "clarified"         # Human asked for clarification
       UNKNOWN = "unknown"             # No clear signal
   ```

3. **Signal Detection Rules**
   | Signal | Classification | Confidence |
   |--------|---------------|------------|
   | Comment resolved + code changed | ACCEPTED | High |
   | Comment resolved + no code change | DISMISSED | Medium |
   | Thumbs down reaction | REJECTED | High |
   | Reply contains "false positive" | REJECTED | High |
   | Reply contains "good catch" | ACCEPTED | High |
   | Reply contains "?" or "what do you mean" | CLARIFIED | Medium |
   | No response after 24h | UNKNOWN | Low |

### B-18.2: Negative Example Storage

**Objective**: Store rejected suggestions as negative examples in Knowledge Base.

**Implementation**:

1. **Memory Entry Schema Extension**
   ```python
   # New memory type for review feedback
   class MemoryType(Enum):
       # ... existing types ...
       REVIEW_ACCEPTED = "review_accepted"
       REVIEW_REJECTED = "review_rejected"
   ```

2. **Negative Example Entry**
   ```python
   entry = MemoryEntry(
       key=f"review_feedback:{repo}:{pr_number}:{comment_id}",
       content=json.dumps({
           "suggestion_type": "error_handling",  # Category of suggestion
           "suggestion_text": "parse_line lacks error handling...",
           "code_pattern": "if match := pattern.search(line):",
           "rejection_reason": "Python regex guarantees capture groups exist",
           "feedback": "rejected",
           "confidence": 0.9,
           "recorded_at": 1737720000,  # Unix timestamp (seconds since epoch UTC)
       }),
       layer=MemoryLayer.KNOWLEDGE_BASE,
       metadata={
           "type": "review_rejected",
           "suggestion_category": "error_handling",
           "language": "python",
           "pattern_hash": hash_of_code_pattern,
           "recorded_at": 1737720000,  # Duplicated for query efficiency
       },
   )
   ```
   
   **Note**: `recorded_at` uses Unix timestamp in seconds since epoch (UTC). This enables log correlation across services and temporal analysis of feedback patterns.

3. **Importance Scoring for Feedback**
   ```python
   # Negative examples should have HIGH importance to prevent repetition
   importance_score = (
       rejection_confidence * 0.4 +    # How certain is the rejection?
       pattern_frequency * 0.3 +       # How often does this pattern appear?
       impact_severity * 0.3           # How bad was the false positive?
   )
   ```
   
   **Variable Definitions**:
   - `rejection_confidence`: The confidence score from feedback classification (0.0-1.0)
   - `pattern_frequency`: How often this code pattern appears in the codebase, normalized to 0.0-1.0 (e.g., 0.1 = rare, 0.9 = very common). Calculated by counting similar patterns in recent PRs.
   - `impact_severity`: Based on the original suggestion's severity level, mapped to 0.0-1.0 (low=0.25, medium=0.5, high=0.75, critical=1.0). Higher severity false positives are more important to remember.

### B-18.3: Negative Pattern Retrieval

**Objective**: Retrieve negative examples during review to avoid repeating mistakes.

**Implementation**:

1. **Enhanced Pattern Retrieval**
   ```python
   def get_relevant_patterns(
       self,
       diff_snippet: str,
       file_paths: Optional[List[str]] = None,
   ) -> Tuple[List[ReviewPattern], List[NegativePattern]]:
       """
       Retrieve both positive and negative patterns.
       
       Returns:
           Tuple of (positive_patterns, negative_patterns)
       """
       positive = self._search_positive_patterns(diff_snippet, file_paths)
       negative = self._search_negative_patterns(diff_snippet, file_paths)
       return positive, negative
   ```

2. **Review Prompt Enhancement**
   ```python
   # Add negative patterns to review context
   if negative_patterns:
       context_lines.append("## Patterns to AVOID (Past False Positives)")
       context_lines.append("")
       for p in negative_patterns:
           context_lines.append(
               f"- DO NOT suggest: {p.suggestion_type}"
           )
           context_lines.append(
               f"  Reason: {p.rejection_reason}"
           )
           context_lines.append(
               f"  Code pattern: {p.code_pattern}"
           )
   ```

3. **LLM Instruction Update**
   ```
   IMPORTANT: The following suggestions have been rejected by humans in the past.
   DO NOT repeat these suggestions for similar code patterns:
   
   1. [error_handling] "parse_line lacks error handling for malformed matches"
      - Reason: Python regex guarantees all capture groups exist if match succeeds
      - Pattern: `if match := pattern.search(line):`
   ```

### B-18.4: Feature Flags

| Flag | Default | Description |
|------|---------|-------------|
| `ENABLE_REVIEW_COMMENT_FEEDBACK` | False | Master switch for B-18 |
| `ENABLE_NEGATIVE_PATTERN_RETRIEVAL` | False | Retrieve negative patterns during review |
| `REVIEW_FEEDBACK_CONFIDENCE_THRESHOLD` | 0.7 | Minimum confidence to store feedback |

---

## Implementation Plan

### Phase 1: Feedback Signal Capture (3-5 days)

| Task | Description | Effort |
|------|-------------|--------|
| B-18.1.1 | Extend webhook handler for comment status changes | 1-2 days |
| B-18.1.2 | Implement feedback classification logic | 1 day |
| B-18.1.3 | Add reaction detection (thumbs up/down) | 1 day |
| B-18.1.4 | Unit tests for feedback classification | 1 day |

### Phase 2: Negative Example Storage (2-3 days)

| Task | Description | Effort |
|------|-------------|--------|
| B-18.2.1 | Add REVIEW_REJECTED memory type | 0.5 days |
| B-18.2.2 | Implement save_review_comment_feedback() | 1 day |
| B-18.2.3 | Importance scoring for feedback | 0.5 days |
| B-18.2.4 | Integration tests | 1 day |

### Phase 3: Negative Pattern Retrieval (3-4 days)

| Task | Description | Effort |
|------|-------------|--------|
| B-18.3.1 | Extend get_relevant_patterns() for negative patterns | 1 day |
| B-18.3.2 | Update enhance_review_context() | 1 day |
| B-18.3.3 | Update LLM reviewer prompt | 1 day |
| B-18.3.4 | E2E tests | 1 day |

### Phase 4: Rollout (1-2 days)

| Task | Description | Effort |
|------|-------------|--------|
| B-18.4.1 | Feature flag configuration | 0.5 days |
| B-18.4.2 | Staging validation | 0.5 days |
| B-18.4.3 | Production rollout | 0.5 days |
| B-18.4.4 | Monitoring setup | 0.5 days |

**Total Estimated Duration**: 9-14 days

---

## Dependencies

### Upstream Dependencies

| Dependency | Status | Required For |
|------------|--------|--------------|
| EPIC G: Memory v2 | Complete | Storage layer |
| B-13: Real-time Feedback Loop | Complete | Pattern retrieval infrastructure |
| Webhook Handler | Complete | Signal capture |

### Downstream Dependencies

| Dependent | Impact |
|-----------|--------|
| Memory Consolidation (G-2) | Should NOT consolidate until B-18 is enabled |
| Reviewer Agent | Will use negative patterns to avoid false positives |

---

## Success Metrics

| Metric | Baseline | Target | Measurement |
|--------|----------|--------|-------------|
| False Positive Rate | Unknown | -50% | Count of rejected suggestions / total suggestions |
| Repeat False Positive Rate | Unknown | <5% | Same false positive repeated after rejection |
| Human Feedback Capture Rate | 0% | >60% | Feedback captured / total comments |
| Reviewer Satisfaction | Baseline | +30% | Developer survey |

---

## Blueprint Alignment

| Blueprint Section | B-18 Coverage |
|-------------------|---------------|
| 5.1 Memory v2 | Extends Knowledge Base with negative examples |
| 7 Human-in-the-Loop | Captures human feedback signals |
| 9 Predictability | Enables learning from corrections |
| 10 Deep Memory v3 | Contributes to accumulated experience |

---

## Risks and Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Low feedback signal rate | Limited learning | Implement multiple signal detection methods |
| False positive in feedback classification | Wrong patterns stored | High confidence threshold (0.7) |
| Storage bloat | Performance degradation | TTL for low-confidence feedback |
| Privacy concerns | Compliance issues | Only store code patterns, not full code |

---

## Relationship to Memory v2 Write Mode

**Critical Insight**: B-18 should be implemented and enabled BEFORE enabling Memory Consolidation write mode (`MEMORY_CONSOLIDATION_DRY_RUN=FALSE`).

**Rationale**:
1. Without B-18, Memory Consolidation will only accumulate positive patterns (including false positives)
2. With B-18, Memory Consolidation will accumulate BOTH positive and negative patterns
3. This ensures the Knowledge Base contains corrected knowledge from day one

**Recommended Sequence**:
1. Implement B-18 (this EPIC)
2. Enable B-18 in production
3. Collect feedback for 1-2 weeks
4. Enable Memory Consolidation write mode

---

## Changelog

| Date | Author | Changes |
|------|--------|---------|
| 2026-01-24 | Devin AI | Initial EPIC planning document |
