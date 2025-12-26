# Cost Tracking System Improvements

Based on deep evaluation of gemini-code-assist review and MorningAI Reviewer Agent analysis for PR #3009.

## Critical Finding: Incorrect Qwen Pricing in PR #3009

**The pricing values in PR #3009 are INCORRECT and need immediate correction.**

### Current (Wrong) Pricing in `cost_tracker.py`:
```python
'qwen-plus': 0.0016,      # $0.0016/1K tokens
'qwen-turbo': 0.0003,     # $0.0003/1K tokens
'qwen-max': 0.016,        # $0.016/1K tokens
```

### Correct Alibaba Cloud Official Pricing (Singapore Region):
| Model | Input Price | Output Price |
|-------|-------------|--------------|
| qwen-plus | $0.4/M tokens ($0.0004/1K) | $1.2/M tokens ($0.0012/1K) |
| qwen-turbo | $0.05/M tokens ($0.00005/1K) | $0.2/M tokens ($0.0002/1K) |
| qwen-max | $1.6/M tokens ($0.0016/1K) | $6.4/M tokens ($0.0064/1K) |

**Source:** https://www.alibabacloud.com/help/doc-detail/2987148.html

---

## Follow-up Issues

### Issue A: Fix Qwen Pricing Values (P0 - Critical)

**Title:** `fix(cost-tracking): correct Qwen pricing values to match Alibaba Cloud official rates`

**Problem:**
PR #3009 introduced incorrect Qwen pricing values. The current values are approximately 4x higher than actual rates, which will cause:
1. Budget enforcement to be too lenient (allowing more usage than intended)
2. Cost reports to be inaccurate

**Acceptance Criteria:**
- [ ] Update `cost_tracker.py` with correct Alibaba Cloud pricing
- [ ] Separate input/output pricing (Qwen charges differently)
- [ ] Add unit tests for all Qwen model pricing lookups
- [ ] Verify against official Alibaba Cloud documentation

**Technical Details:**
```python
# Correct pricing (per 1K tokens)
'qwen-plus': 0.0004,           # Input: $0.4/M = $0.0004/1K
'qwen-plus-output': 0.0012,    # Output: $1.2/M = $0.0012/1K
'qwen-turbo': 0.00005,         # Input: $0.05/M = $0.00005/1K
'qwen-turbo-output': 0.0002,   # Output: $0.2/M = $0.0002/1K
'qwen-max': 0.0016,            # Input: $1.6/M = $0.0016/1K
'qwen-max-output': 0.0064,     # Output: $6.4/M = $0.0064/1K
```

---

### Issue B: Make Pricing Table Configurable (P1 - High)

**Title:** `feat(cost-tracking): make pricing table configurable and add version tracking`

**Problem:**
Pricing is hardcoded in `cost_tracker.py`, making updates difficult and untrackable.

**Acceptance Criteria:**
- [ ] Move pricing table to `config/pricing.yaml` or add to `policies.yaml`
- [ ] Add `pricing_version` or `pricing_source` field to Redis cost records
- [ ] Load pricing dynamically in `CostTracker.__init__()`
- [ ] Document pricing update process in README

**Benefits:**
- Easy to update pricing without code changes
- Audit trail for which pricing version was used
- Enables A/B testing of pricing models

---

### Issue C: Fix All Hardcoded `model='gpt-4'` References (P1 - High)

**Title:** `fix(cost-tracking): replace all hardcoded gpt-4 model references with actual model`

**Problem:**
Multiple files still use `model='gpt-4'` for cost tracking, even though the actual LLM is Qwen:

```
agents/ops_agent/worker.py:281:                        model='gpt-4',
orchestrator/redis_queue/worker.py:1179:                model="gpt-4",
orchestrator/redis_queue/worker.py:1586:                model="gpt-4",
orchestrator/langgraph_orchestrator.py:1892:            model="gpt-4"
```

**Acceptance Criteria:**
- [ ] Replace all `model='gpt-4'` with actual model from settings/LLM provider
- [ ] Create a centralized `get_current_model()` function
- [ ] Add lint rule to prevent hardcoded model strings in `track_usage()` calls
- [ ] Update tests to use correct model names

---

### Issue D: Add Cost Tracking Unit Tests (P2 - Medium)

**Title:** `test(cost-tracking): add comprehensive unit tests for cost estimation`

**Problem:**
Current tests only cover GPT-4 and GPT-3.5-turbo models. No tests for:
- Qwen model pricing
- Unknown model fallback behavior
- Input vs output pricing separation
- Budget boundary cases with mixed pricing data

**Acceptance Criteria:**
- [ ] Add tests for all Qwen models (qwen-plus, qwen-turbo, qwen-max)
- [ ] Add tests for unknown model fallback
- [ ] Add tests for input/output pricing separation
- [ ] Add tests for `check_budget()` with mixed old/new pricing data
- [ ] Update `test_estimate_cost()` in `tests/test_governance.py`

---

### Issue E: Handle Redis Historical Data Inconsistency (P2 - Medium)

**Title:** `fix(cost-tracking): handle mixed pricing data in Redis gracefully`

**Problem:**
Historical Redis data was recorded with GPT-4 pricing. After PR #3009, new data uses Qwen pricing. This causes:
1. Inconsistent cost reports
2. Potential budget enforcement issues during transition

**Acceptance Criteria:**
- [ ] Add `pricing_version` field to Redis cost records
- [ ] Log warning when mixed pricing versions detected
- [ ] Consider using tokens-only for budget enforcement (usd as soft signal)
- [ ] Optional: Create migration script to recalculate historical usd values

**Technical Notes:**
- Redis keys have TTL (daily: 7 days, hourly: 24h, task: 30 days)
- Data will naturally age out, but transition period needs handling

---

### Issue F: Add Cost Monitoring and Alerting (P3 - Low)

**Title:** `feat(cost-tracking): add cost monitoring metrics and drift alerting`

**Problem:**
No visibility into cost trends or anomalies. Silent drift can occur when pricing changes.

**Acceptance Criteria:**
- [ ] Add "budget usage rate" metrics (tokens/usd per hour)
- [ ] Alert when mixed `pricing_version` detected in same period
- [ ] Alert when cost-per-token deviates significantly from expected
- [ ] Dashboard widget for cost trends

---

## Comparison: gemini-code-assist vs MorningAI Reviewer

| Aspect | gemini-code-assist | MorningAI Reviewer |
|--------|-------------------|-------------------|
| Pricing verification | Correctly identified need for verification | Did not flag pricing accuracy |
| Test coverage | Identified missing tests | Did not flag test gaps |
| Redis compatibility | Identified data inconsistency risk | Did not flag migration needs |
| Actionability | Provided general suggestions | N/A (not reviewed) |
| False positives | Some suggestions overly cautious (migration script) | N/A |

**Recommendation:** gemini-code-assist provided valuable review feedback. The suggestions about pricing verification and test coverage are particularly important and should be prioritized.

---

## Priority Order

1. **P0 (Immediate):** Issue A - Fix incorrect Qwen pricing values
2. **P1 (This Sprint):** Issue B - Make pricing configurable, Issue C - Fix hardcoded gpt-4 references
3. **P2 (Next Sprint):** Issue D - Add tests, Issue E - Handle Redis inconsistency
4. **P3 (Backlog):** Issue F - Add monitoring

---

## References

- PR #3009: https://github.com/RC918/morningai/pull/3009
- Alibaba Cloud Pricing: https://www.alibabacloud.com/help/doc-detail/2987148.html
- Devin Session: https://app.devin.ai/sessions/199f2f07612d42fd88f6b030768a3247
