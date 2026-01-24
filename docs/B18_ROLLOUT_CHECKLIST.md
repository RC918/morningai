# B-18 Review Comment Feedback - Rollout Checklist

**EPIC**: B-18 Review Comment Feedback (Human-in-the-Loop Learning)  
**Status**: Implementation Complete, Ready for Rollout  
**Last Updated**: 2026-01-24

---

## Pre-Rollout Summary

EPIC B-18 implements human feedback capture for review comments, enabling the MorningAI Reviewer Agent to learn from human corrections and avoid repeating false positives.

### Implementation Status

| Phase | PR | Status |
|-------|-----|--------|
| B-18.1.1: Webhook handler for comment status | [#4313](https://github.com/RC918/morningai/pull/4313) | Merged |
| B-18.1.2: Reaction event handling | [#4318](https://github.com/RC918/morningai/pull/4318) | Merged |
| B-18.2: Negative example storage | [#4319](https://github.com/RC918/morningai/pull/4319) | Merged |
| B-18.3: Negative pattern retrieval | [#4320](https://github.com/RC918/morningai/pull/4320) | Merged |

---

## Feature Flags

### Required Environment Variables

| Flag | Default | Recommended Prod Value | Description |
|------|---------|------------------------|-------------|
| `ENABLE_MEMORY_V2` | `false` | `true` | Master switch for Memory v2 (prerequisite) |
| `ENABLE_REVIEW_COMMENT_FEEDBACK` | `false` | `true` | Enable feedback signal capture (B-18.1) |
| `ENABLE_NEGATIVE_PATTERN_RETRIEVAL` | `false` | `true` | Enable negative pattern retrieval during review (B-18.3) |
| `REVIEW_FEEDBACK_CONFIDENCE_THRESHOLD` | `0.7` | `0.7` | Minimum confidence to store feedback |
| `NEGATIVE_PATTERN_MAX_RESULTS` | `5` | `5` | Max negative patterns to retrieve per review |
| `NEGATIVE_PATTERN_SIMILARITY_THRESHOLD` | `0.6` | `0.6` | Minimum similarity for pattern matching |

### Feature Flag Dependency Chain

```
ENABLE_MEMORY_V2=true
    └── ENABLE_REVIEW_COMMENT_FEEDBACK=true
            └── ENABLE_NEGATIVE_PATTERN_RETRIEVAL=true
```

All three flags must be enabled for full B-18 functionality.

---

## Rollout Checklist

### Phase 1: Pre-Rollout Validation

- [ ] **Verify Memory v2 is operational**
  - Confirm `ENABLE_MEMORY_V2=true` in prod
  - Verify pgvector extension is available in PostgreSQL
  - Check Memory v2 read operations are working (logs show successful searches)

- [ ] **Verify webhook handler is receiving events**
  - Check GitHub webhook configuration includes:
    - `pull_request_review_thread` events
    - `pull_request_review_comment` events (for reactions)
  - Verify webhook signature validation is working

- [ ] **Review current Reviewer Agent behavior**
  - Note baseline false positive rate (if measurable)
  - Document any known recurring false positives

### Phase 2: Staged Rollout

#### Step 1: Enable Feedback Capture Only (B-18.1 + B-18.2)

```bash
# Render Dashboard / Environment Variables
ENABLE_REVIEW_COMMENT_FEEDBACK=true
ENABLE_NEGATIVE_PATTERN_RETRIEVAL=false  # Keep disabled initially
```

- [ ] Deploy with feedback capture enabled
- [ ] Monitor logs for `[ReviewCommentFeedback]` entries
- [ ] Verify feedback signals are being classified correctly:
  - `ACCEPTED` for resolved comments with code changes
  - `REJECTED` for thumbs-down reactions
  - `DISMISSED` for resolved without changes
- [ ] Verify feedback is being stored in Knowledge Base
  - Check for `review_feedback:*` keys in Memory v2

**Observation Period**: 3-5 days

#### Step 2: Enable Negative Pattern Retrieval (B-18.3)

```bash
# Render Dashboard / Environment Variables
ENABLE_REVIEW_COMMENT_FEEDBACK=true
ENABLE_NEGATIVE_PATTERN_RETRIEVAL=true
```

- [ ] Deploy with negative pattern retrieval enabled
- [ ] Monitor logs for `[NegativePatternRetrieval]` entries
- [ ] Verify review context includes "Patterns to AVOID" section
- [ ] Monitor for any performance impact (retrieval latency)

**Observation Period**: 1-2 weeks

### Phase 3: Post-Rollout Validation

- [ ] **Measure false positive reduction**
  - Compare rejected suggestion rate before/after B-18
  - Target: 50% reduction in repeat false positives

- [ ] **Verify no regression in review quality**
  - Review sample of recent PR reviews
  - Ensure legitimate suggestions are not being suppressed

- [ ] **Check storage growth**
  - Monitor Knowledge Base size growth
  - Verify TTL cleanup is working for low-confidence feedback

---

## Monitoring & Observability

### Key Log Patterns

```bash
# Feedback capture
grep "\[ReviewCommentFeedback\]" /var/log/orchestrator.log

# Feedback storage
grep "\[MemoryIntegration\] Saved review feedback" /var/log/orchestrator.log

# Negative pattern retrieval
grep "\[NegativePatternRetrieval\]" /var/log/orchestrator.log

# Review context enhancement
grep "Patterns to AVOID" /var/log/orchestrator.log
```

### Metrics to Track

| Metric | Description | Unit | Target |
|--------|-------------|------|--------|
| `review_feedback_captured_total` | Total feedback signals captured | count | Increasing |
| `review_feedback_by_classification` | Breakdown by ACCEPTED/REJECTED/etc | count | Balanced |
| `negative_patterns_retrieved_total` | Patterns retrieved per review | count | 0-5 per review |
| `negative_pattern_retrieval_latency_ms` | Retrieval latency (milliseconds) | ms | <100ms P99 |
| `repeat_false_positive_rate` | Same false positive after rejection | % | <5% |

**Note on Units**: All latency metrics in MorningAI telemetry use milliseconds (ms) as the standard unit. The `_ms` suffix in metric names explicitly indicates this. When configuring dashboards or alerts, ensure the unit matches (e.g., Grafana should display as "ms", not "s").

---

## Rollback Procedure

If issues are detected, rollback by disabling feature flags:

```bash
# Immediate rollback - disable retrieval only
ENABLE_NEGATIVE_PATTERN_RETRIEVAL=false

# Full rollback - disable all B-18
ENABLE_REVIEW_COMMENT_FEEDBACK=false
```

**Note**: Disabling flags does NOT delete stored feedback. Data remains in Knowledge Base for future use.

---

## Post-Rollout: Memory Consolidation Write Mode

After B-18 has been running successfully for 1-2 weeks:

- [ ] Review dry run logs from Memory Consolidation
- [ ] Verify feedback patterns are being captured correctly
- [ ] Enable Memory Consolidation write mode:

```bash
MEMORY_CONSOLIDATION_DRY_RUN=false
```

**Critical**: B-18 should be enabled BEFORE Memory Consolidation write mode to ensure the Knowledge Base captures both positive AND negative signals from day one.

---

## Troubleshooting

### Feedback Not Being Captured

1. Check webhook events are being received:
   ```bash
   grep "pull_request_review_thread" /var/log/orchestrator.log
   ```

2. Verify feature flag is enabled:
   ```bash
   grep "enable_review_comment_feedback" /var/log/orchestrator.log
   ```

3. Check for classification errors:
   ```bash
   grep "\[FeedbackClassification\] Error" /var/log/orchestrator.log
   ```

### Negative Patterns Not Retrieved

1. Verify patterns exist in Knowledge Base:
   ```sql
   SELECT COUNT(*) FROM memory_entries 
   WHERE metadata->>'type' = 'review_rejected';
   ```

2. Check similarity threshold:
   - If no patterns match, consider lowering `NEGATIVE_PATTERN_SIMILARITY_THRESHOLD`

3. Verify embedding generation:
   ```bash
   grep "\[MemoryV2\] Embedding generation" /var/log/orchestrator.log
   ```

### Performance Issues

1. Check retrieval latency:
   ```bash
   grep "negative_pattern_retrieval_latency" /var/log/orchestrator.log
   ```

2. If latency is high:
   - Reduce `NEGATIVE_PATTERN_MAX_RESULTS`
   - Increase `NEGATIVE_PATTERN_SIMILARITY_THRESHOLD`

---

## Related Documentation

- [EPIC B-18 Specification](./EPIC_B18_REVIEW_COMMENT_FEEDBACK.md)
- [EPIC B Roadmap](./EPIC_B_DIFF_AWARE_REVIEW_ROADMAP.md)
- [EPIC G Memory v2 Roadmap](./EPIC_G_MEMORY_V2_ROADMAP.md)
- [Memory Consolidation Analyzer](../scripts/analysis/analyze_memory_consolidation.py)

---

## Changelog

| Date | Author | Changes |
|------|--------|---------|
| 2026-01-24 | Devin AI | Initial rollout checklist |
