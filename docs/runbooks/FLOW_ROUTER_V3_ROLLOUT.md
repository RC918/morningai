# Flow Controller v3 Rollout Runbook

**EPIC C Issue #2750**: C-7 Rollout Design (Canary/Rollback Runbook)
**Status**: Production Ready
**Last Updated**: 2026-01-01
**Owner**: MorningAI Platform Team

---

## Overview

This runbook documents the rollout strategy for Flow Controller v3 (LLM-driven Dynamic Routing). The feature replaces deterministic `conditional_edges` routing with `HybridRoutingPolicy` that uses LLM for ambiguous routing decisions.

**Feature Flag**: `ENABLE_DYNAMIC_ROUTING`
- `false` (default): 100% legacy behavior (deterministic `decision_node`)
- `true`: Hybrid Router with LLM-driven slow path

**Risk Level**: Medium
- Affects core workflow routing logic
- Has fail-safe fallback to deterministic routing
- No data mutation, only routing decisions

---

## Prerequisites

Before starting rollout, verify:

1. **Stage 0 Complete** (C-1 to C-4):
   - [x] Schema definitions (`RoutingCandidate`, `RoutingDecision`, `RoutingContext`)
   - [x] Router Node interface with decision validation
   - [x] Feature flag configuration (`ENABLE_DYNAMIC_ROUTING`)
   - [x] Router metrics and telemetry

2. **Stage 1 Complete** (C-5, C-5b, C-6):
   - [x] Review segment integration
   - [x] SimpleCoderAgent validation
   - [x] Graph wiring for Hybrid Router
   - [x] Integration tests passing

3. **Monitoring Ready**:
   - [x] `RouterMetrics` collecting latency, success/fallback rates
   - [x] Sentry alerts configured for router errors
   - [x] Log aggregation for `[ROUTER_*]` event codes

---

## Rollout Phases

### Phase 1: Staging Validation (Day 1-3)

**Objective**: Validate Hybrid Router in staging environment with real PR review tasks.

#### 1.1 Enable Feature Flag

```bash
# Staging environment
export ENABLE_DYNAMIC_ROUTING=true

# Verify configuration
curl -s https://staging-api.morning-ai.com/health | jq '.config.enable_dynamic_routing'
# Expected: true
```

#### 1.2 Execute Validation Tasks

Run 10 real PR review tasks covering all routing paths:

| Task | Expected Route | Validation |
|------|----------------|------------|
| PR with clean code | `approve -> publisher` | Fast Path |
| PR with minor issues | `request_changes (low) -> fixer` | Fast Path |
| PR with medium issues | `request_changes (medium) -> LLM -> fixer/executor` | Slow Path |
| PR with critical issues | `request_changes (critical) -> executor` | Slow Path |
| PR with blockers | `blocked -> decision + HITL` | Fast Path |
| PR with unknown verdict | `unknown -> decision + HITL` | Fast Path |

#### 1.3 Monitoring Thresholds

| Metric | Threshold | Action |
|--------|-----------|--------|
| `router_fallback_rate` | < 10% | Continue |
| `router_fallback_rate` | 10-20% | Investigate |
| `router_fallback_rate` | > 20% | **Rollback** |
| `router_latency_p99` | < 15s | Continue |
| `router_latency_p99` | 15-20s | Investigate |
| `router_latency_p99` | > 20s | **Rollback** |
| `router_error_rate` | < 5% | Continue |
| `router_error_rate` | > 5% | **Rollback** |

#### 1.4 Staging Validation Checklist

- [ ] All 10 validation tasks completed successfully
- [ ] Fallback rate < 10%
- [ ] Latency p99 < 15s
- [ ] No P0/P1 incidents
- [ ] Router metrics visible in dashboard
- [ ] Log events `[ROUTER_FAST_PATH]`, `[ROUTER_SLOW_PATH]` appearing correctly

**Exit Criteria**: All checklist items passed for 24 hours.

---

### Phase 2: Canary (5%) (Day 4-5)

**Objective**: Validate with 5% of production traffic.

#### 2.1 Enable Canary

```bash
# Production environment - Canary deployment
# Option A: Environment variable per instance
export ENABLE_DYNAMIC_ROUTING=true  # On 5% of instances

# Option B: Feature flag service (if available)
# Set ENABLE_DYNAMIC_ROUTING=true for 5% of traffic
```

#### 2.2 Monitoring (24 hours)

Monitor the following metrics continuously:

```bash
# Query router metrics (example using curl to metrics endpoint)
curl -s https://api.morning-ai.com/governance/router-metrics | jq '
{
  fallback_rate: .fallback_rate,
  success_rate: .success_rate,
  average_latency_ms: .average_latency_ms,
  total_decisions: .total_decisions
}'
```

**Expected Values**:
- `fallback_rate` < 5%
- `success_rate` > 95%
- `average_latency_ms` < 5000
- `total_decisions` increasing steadily

#### 2.3 Canary Validation Checklist

- [ ] 24 hours of canary traffic processed
- [ ] Fallback rate < 5%
- [ ] No P0/P1 incidents
- [ ] No negative user feedback
- [ ] Router decisions match expected behavior

**Exit Criteria**: All checklist items passed.

---

### Phase 3: Gradual Rollout (Day 6-10)

**Objective**: Incrementally increase traffic to 100%.

#### 3.1 Rollout Schedule

| Day | Traffic % | Duration | Exit Criteria |
|-----|-----------|----------|---------------|
| Day 6 | 25% | 24h | Fallback < 5%, No incidents |
| Day 7 | 50% | 24h | Fallback < 5%, No incidents |
| Day 8-9 | 75% | 48h | Fallback < 5%, No incidents |
| Day 10 | 100% | - | Full rollout complete |

#### 3.2 Per-Stage Validation

At each stage, verify:

1. **Metrics**:
   ```bash
   # Check router summary
   curl -s https://api.morning-ai.com/governance/router-metrics?window_minutes=60
   ```

2. **Logs**:
   ```bash
   # Search for router events
   grep -E "\[ROUTER_(FAST_PATH|SLOW_PATH|HITL|LLM_FALLBACK)\]" /var/log/orchestrator.log | tail -100
   ```

3. **Alerts**: No new Sentry alerts related to router

#### 3.3 Full Rollout Checklist

- [ ] 100% traffic using Hybrid Router
- [ ] Fallback rate stable < 5%
- [ ] Latency p99 stable < 15s
- [ ] No P0/P1 incidents during rollout
- [ ] User feedback positive or neutral

---

## Rollback Procedures

### Immediate Rollback (< 5 minutes)

Use when: P0 incident, error rate > 5%, or critical user impact.

```bash
# Step 1: Disable feature flag immediately
export ENABLE_DYNAMIC_ROUTING=false

# Step 2: Restart affected services (if needed)
# Render: Trigger manual deploy with flag disabled
# Kubernetes: kubectl rollout restart deployment/orchestrator

# Step 3: Verify rollback
curl -s https://api.morning-ai.com/health | jq '.config.enable_dynamic_routing'
# Expected: false

# Step 4: Verify legacy routing active
grep "\[Graph\] ENABLE_DYNAMIC_ROUTING=false" /var/log/orchestrator.log | tail -5
# Should see: "[Graph] ENABLE_DYNAMIC_ROUTING=false, using legacy decision node"
```

### Gradual Rollback

Use when: Non-critical issues, performance degradation, or investigation needed.

```bash
# Step 1: Reduce traffic percentage
# 100% -> 50% -> 25% -> 5% -> 0%

# Step 2: Monitor at each stage
curl -s https://api.morning-ai.com/governance/router-metrics | jq '.fallback_rate'

# Step 3: Investigate root cause before re-enabling
```

### Post-Rollback Actions

1. **Incident Report**: Create incident report within 24 hours
2. **Root Cause Analysis**: Identify and document root cause
3. **Fix Verification**: Verify fix in staging before re-rollout
4. **Communication**: Notify stakeholders of rollback and timeline

---

## Monitoring Dashboard

### Key Metrics to Monitor

| Metric | Source | Alert Threshold |
|--------|--------|-----------------|
| `router_fallback_rate` | RouterMetrics | > 10% |
| `router_latency_p99` | RouterMetrics | > 20s |
| `router_error_count` | Sentry | > 10/hour |
| `router_success_rate` | RouterMetrics | < 90% |

### Log Event Codes

| Event Code | Meaning | Expected Frequency |
|------------|---------|-------------------|
| `[ROUTER_FAST_PATH]` | Deterministic routing used | High (70-80%) |
| `[ROUTER_SLOW_PATH]` | LLM-driven routing used | Medium (15-25%) |
| `[ROUTER_HITL]` | Human-in-the-loop required | Low (< 5%) |
| `[ROUTER_LLM_FALLBACK]` | LLM failed, using fallback | Very Low (< 2%) |

### Grafana Queries (Example)

```promql
# Fallback rate over time
sum(rate(router_fallback_total[5m])) / sum(rate(router_decisions_total[5m]))

# Latency p99
histogram_quantile(0.99, sum(rate(router_latency_bucket[5m])) by (le))

# Success rate by node
sum(rate(router_success_total[5m])) by (chosen_node) / sum(rate(router_decisions_total[5m])) by (chosen_node)
```

---

## Troubleshooting

### High Fallback Rate (> 10%)

**Symptoms**: `router_fallback_rate` exceeds threshold

**Investigation**:
1. Check fallback reason distribution:
   ```bash
   curl -s https://api.morning-ai.com/governance/router-metrics | jq '.fallback_distribution'
   ```

2. Common causes:
   - `timeout`: LLM response too slow -> Check LLM provider health
   - `json_parse_error`: LLM output malformed -> Check prompt template
   - `invalid_next_node`: LLM returning invalid nodes -> Check candidate list
   - `validation_error`: Schema validation failed -> Check RoutingDecision schema

**Resolution**:
- If LLM provider issue: Consider temporary rollback
- If prompt issue: Fix prompt and redeploy
- If schema issue: Update validation logic

### High Latency (> 15s p99)

**Symptoms**: `router_latency_p99` exceeds threshold

**Investigation**:
1. Check LLM provider latency:
   ```bash
   curl -s https://api.morning-ai.com/governance/provider-health | jq '.providers[].latency_ms'
   ```

2. Check slow path frequency:
   ```bash
   grep "\[ROUTER_SLOW_PATH\]" /var/log/orchestrator.log | wc -l
   ```

**Resolution**:
- If LLM slow: Consider switching provider or increasing timeout
- If too many slow paths: Adjust severity thresholds in HybridRoutingPolicy

### Unexpected Routing Decisions

**Symptoms**: Tasks routed to wrong nodes

**Investigation**:
1. Check recent routing decisions:
   ```bash
   grep "\[HybridRouter\]" /var/log/orchestrator.log | tail -50
   ```

2. Verify ReviewOutcome fields:
   - `verdict`: approve/request_changes/comment/blocked/unknown
   - `severity`: low/medium/high/critical
   - `blocker_count`: integer

**Resolution**:
- If LLM decision wrong: Review prompt and add examples
- If fast path wrong: Check severity threshold logic
- If HITL wrong: Verify blocked/unknown handling

---

## Contacts

| Role | Contact | Escalation |
|------|---------|------------|
| Platform Team | #platform-oncall | P0/P1 incidents |
| LLM Infrastructure | #llm-infra | Provider issues |
| Product | #product | User feedback |

---

## Appendix

### A. Feature Flag Configuration

```yaml
# config/env.schema.yaml
ENABLE_DYNAMIC_ROUTING:
  type: boolean
  default: false
  description: |
    Enable LLM-driven dynamic routing (Flow Controller v3).
    Default False = 100% old behavior (conditional_edges).
    True = Hybrid Router with LLM slow path for ambiguous cases.
```

### B. Related Issues

- #2743: EPIC C: Flow Controller v3
- #2744: C-1 Schema Definition
- #2745: C-2 Router Node Interface
- #2746: C-3 Feature Flag
- #2747: C-4 Router Observability
- #2748: C-5 Review Segment Integration
- #2758: C-5b SimpleCoderAgent
- #3182: C-6 Graph Wiring

### C. Architecture Diagram

```
                    ENABLE_DYNAMIC_ROUTING=false (Legacy)
                    ┌─────────────────────────────────────┐
                    │  reviewer → decision → hitl_gate    │
                    └─────────────────────────────────────┘

                    ENABLE_DYNAMIC_ROUTING=true (Hybrid Router)
                    ┌─────────────────────────────────────┐
                    │  reviewer → router → hitl_gate      │
                    │              │                      │
                    │              ├── Fast Path (70-80%) │
                    │              │   (deterministic)    │
                    │              │                      │
                    │              └── Slow Path (20-30%) │
                    │                  (LLM-driven)       │
                    └─────────────────────────────────────┘
```

### D. Routing Rules Summary

| Verdict | Severity | Route | Path Type |
|---------|----------|-------|-----------|
| approve | - | publisher | Fast |
| blocked | - | decision + HITL | Fast |
| unknown | - | decision + HITL | Fast |
| comment | - | fixer | Fast |
| request_changes | low | fixer | Fast |
| request_changes | medium | LLM decides | Slow |
| request_changes | high | LLM decides | Slow |
| request_changes | critical | LLM decides | Slow |

---

## Changelog

| Date | Author | Changes |
|------|--------|---------|
| 2026-01-01 | Devin AI | Initial version for C-7 |
