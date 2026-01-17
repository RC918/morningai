# Safety Governance Runbook

**EPIC E Phase E-5: Observability & Ops Readiness**

This runbook provides operational procedures for the MorningAI Safety Governor v2 system, including emergency override procedures, false positive handling, and policy update procedures.

## Table of Contents

1. [Overview](#overview)
2. [Emergency Override Procedure](#emergency-override-procedure)
3. [False Positive Handling](#false-positive-handling)
4. [Policy Update Procedure](#policy-update-procedure)
5. [Monitoring and Alerting](#monitoring-and-alerting)
6. [Troubleshooting](#troubleshooting)

## Overview

The Safety Governor v2 system provides content safety scanning for:
- Prompt Injection detection
- Jailbreak attempt detection
- Harmful content detection

### Key Components

| Component | Location | Purpose |
|-----------|----------|---------|
| ContentSafetyScanner | `governance/content_safety_scanner.py` | Pattern-based content scanning |
| SafetyMetricsCollector | `governance/safety_metrics.py` | Metrics collection and alerting |
| Safety API | `routes/governance.py` | REST API endpoints |

### Feature Flags

| Flag | Default | Description |
|------|---------|-------------|
| `CONTENT_SAFETY_ENABLED` | `true` | Enable/disable content safety scanning |
| `CONTENT_SAFETY_STRICT_MODE` | `false` | Enable strict mode (lower confidence threshold) |
| `CONTENT_SAFETY_BLOCK_ON_CRITICAL` | `true` | Block on CRITICAL risk findings |
| `SAFETY_METRICS_ENABLED` | `true` | Enable safety metrics collection |
| `SAFETY_BLOCK_RATE_THRESHOLD` | `10.0` | Block rate % that triggers alerts |

## Emergency Override Procedure

### When to Use

Use emergency override when:
- A legitimate request is being incorrectly blocked
- Business-critical operations are impacted
- False positive rate is unacceptably high

### Procedure

#### Step 1: Assess the Situation

1. Check the Safety Dashboard for current block rate:
   ```bash
   curl -H "Authorization: Bearer $TOKEN" \
     https://api.morningai.com/api/governance/safety/metrics
   ```

2. Review recent blocked decisions:
   ```bash
   curl -H "Authorization: Bearer $TOKEN" \
     "https://api.morningai.com/api/governance/safety/decisions?action=block&limit=20"
   ```

#### Step 2: Create Override Request

1. Submit an override request via API:
   ```bash
   curl -X POST -H "Authorization: Bearer $TOKEN" \
     -H "Content-Type: application/json" \
     -d '{
       "trace_id": "<trace_id_of_blocked_request>",
       "original_action": "block",
       "requested_action": "allow",
       "reason": "False positive - legitimate business request"
     }' \
     https://api.morningai.com/api/governance/safety/overrides
   ```

2. Or use the Owner Console Dashboard to submit the request.

#### Step 3: Approve Override (Owner Only)

1. Review the override request in the Owner Console
2. Approve via API:
   ```bash
   curl -X POST -H "Authorization: Bearer $TOKEN" \
     https://api.morningai.com/api/governance/safety/overrides/<trace_id>/approve
   ```

#### Step 4: Temporary Disable (Last Resort)

If the situation is critical and requires immediate action:

1. Set `CONTENT_SAFETY_ENABLED=false` in Dashboard
2. Document the reason and expected duration
3. Create a follow-up issue to investigate root cause
4. Re-enable within 24 hours maximum

### Rollback

To rollback an override:
1. Reject the override request if still pending
2. If already approved, create a new policy rule to block the pattern

## False Positive Handling

### Identification

False positives can be identified through:
1. User reports of legitimate content being blocked
2. High block rate alerts (>10% default threshold)
3. Manual review of blocked decisions

### Investigation Steps

#### Step 1: Gather Evidence

1. Get the blocked decision details:
   ```bash
   curl -H "Authorization: Bearer $TOKEN" \
     "https://api.morningai.com/api/governance/safety/decisions?trace_id=<trace_id>"
   ```

2. Note the following:
   - `category`: Which scanner triggered (prompt_injection, jailbreak, harmful_content)
   - `pattern_id`: Which specific pattern matched
   - `confidence`: Confidence score of the match
   - `matched_text`: The text that triggered the detection

#### Step 2: Analyze the Pattern

1. Review the pattern definition in `content_safety_scanner.py`
2. Determine if the pattern is too broad
3. Check if the confidence threshold is appropriate

#### Step 3: Resolution Options

**Option A: Adjust Confidence Threshold**
- Increase the confidence threshold for the specific pattern
- Requires code change and deployment

**Option B: Add Exception Rule**
- Add a whitelist pattern for known safe content
- Can be done via policy configuration

**Option C: Disable Specific Pattern**
- Temporarily disable the problematic pattern
- Use feature flag: `CONTENT_SAFETY_DISABLE_PATTERNS=pattern_id1,pattern_id2`

#### Step 4: Document and Track

1. Create a GitHub issue for the false positive
2. Label with `safety-false-positive`
3. Include:
   - Trace ID
   - Pattern ID
   - Matched text (sanitized)
   - Resolution applied

### Metrics to Monitor

| Metric | Threshold | Action |
|--------|-----------|--------|
| Block Rate | >10% | Investigate patterns |
| False Positive Reports | >5/day | Review scanner rules |
| Override Requests | >10/day | Adjust thresholds |

## Policy Update Procedure

### Adding New Patterns

#### Step 1: Define the Pattern

1. Create pattern definition:
   ```python
   {
       "id": "pi_new_pattern_001",
       "pattern": r"your_regex_pattern_here",
       "title": "New Pattern Detection",
       "risk_level": ContentRiskLevel.HIGH,
       "category": ContentSafetyCategory.PROMPT_INJECTION,
   }
   ```

2. Test the pattern against known samples:
   - True positive samples (should match)
   - True negative samples (should not match)

#### Step 2: Deploy to Staging

1. Add pattern to `content_safety_scanner.py`
2. Deploy to Staging environment
3. Monitor for 24-48 hours

#### Step 3: Production Deployment

1. Review Staging metrics
2. Confirm no unexpected false positives
3. Deploy to Production
4. Monitor block rate for 24 hours

### Modifying Existing Patterns

1. Document the reason for modification
2. Test changes in Staging first
3. Use feature flags for gradual rollout if possible

### Removing Patterns

1. Disable pattern first (don't delete immediately)
2. Monitor for 7 days to ensure no security impact
3. Remove pattern code after confirmation

## Monitoring and Alerting

### Dashboard Endpoints

| Endpoint | Purpose |
|----------|---------|
| `GET /api/governance/safety/metrics` | All safety metrics |
| `GET /api/governance/safety/decisions` | Decision event stream |
| `GET /api/governance/safety/overrides` | Override requests |

### Key Metrics

1. **safety_decisions_total**: Total decisions by action and category
2. **safety_scan_latency_seconds**: Scan performance
3. **safety_override_requests_total**: Override request counts
4. **safety_block_rate**: Current block rate percentage

### Alert Thresholds

| Alert | Condition | Severity |
|-------|-----------|----------|
| High Block Rate | >10% | Warning |
| Very High Block Rate | >25% | Critical |
| Scan Latency | >500ms p95 | Warning |
| Override Backlog | >10 pending | Warning |

### Alert Response

1. **High Block Rate Alert**
   - Check for new attack patterns
   - Review recent pattern changes
   - Consider temporary threshold adjustment

2. **Latency Alert**
   - Check system resources
   - Review pattern complexity
   - Consider pattern optimization

## Troubleshooting

### Scanner Not Working

1. Check if `CONTENT_SAFETY_ENABLED=true`
2. Verify module imports in logs
3. Check for pattern compilation errors

### Metrics Not Collecting

1. Check if `SAFETY_METRICS_ENABLED=true`
2. Verify Redis connection (if using distributed mode)
3. Check for thread safety issues

### Override Not Processing

1. Verify user has Owner role
2. Check if request is still in "pending" status
3. Review API response for error messages

### High Memory Usage

1. Check `_max_events` setting (default: 1000)
2. Consider reducing event retention
3. Enable Redis persistence for distributed storage

## Contact

For escalation:
- Slack: #safety-governance
- On-call: See PagerDuty rotation
- GitHub: Create issue with `safety-urgent` label

## Changelog

| Date | Version | Change |
|------|---------|--------|
| 2026-01-17 | 1.0 | Initial runbook creation (EPIC E E-5) |
