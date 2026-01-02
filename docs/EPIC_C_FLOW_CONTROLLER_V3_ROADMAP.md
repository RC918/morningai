# EPIC C: Flow Controller v3 (LLM-driven Routing) - Roadmap

> Last Updated: 2026-01-02

## Overview

EPIC C focuses on replacing deterministic `conditional_edges` routing with a `HybridRoutingPolicy` that uses LLM for ambiguous routing decisions. This enables intelligent, context-aware workflow orchestration.

**GitHub Issue**: [#2743](https://github.com/RC918/morningai/issues/2743)

**Blueprint Alignment**: Section 3.2 - Flow Controller v3

## Status Summary

| Stage | Status | Key Issues |
|-------|--------|------------|
| Stage 0: Foundations | **Completed** | #2744, #2745, #2746, #2747 |
| Stage 1: Pilot | **Completed** (C-6 Graph Wiring) | #2748, #2758, #2749, #3182 |
| C-7: Rollout Design | **Completed** | #2750 |
| Operationalization | **Pending** | [#3486](https://github.com/RC918/morningai/issues/3486) |
| Stage 2: Expansion | Planned | #2751, #2752, #2753 |

---

## Stage 0: Foundations (Completed)

Framework and safety foundations for LLM-driven routing.

### Implemented Items

| Issue | Description | Status |
|-------|-------------|--------|
| [#2744](https://github.com/RC918/morningai/issues/2744) | Schema Definition (`RoutingCandidate`, `RoutingDecision`, `RoutingContext`) | Done |
| [#2745](https://github.com/RC918/morningai/issues/2745) | Router Node Interface + Decision Validator | Done |
| [#2746](https://github.com/RC918/morningai/issues/2746) | Feature Flag (`ENABLE_DYNAMIC_ROUTING`) | Done |
| [#2747](https://github.com/RC918/morningai/issues/2747) | Router Observability (`RouterMetrics`) | Done |

---

## Stage 1: Pilot (Completed)

Review segment integration and minimal viable routing.

### Implemented Items

| Issue | Description | Status |
|-------|-------------|--------|
| [#2748](https://github.com/RC918/morningai/issues/2748) | C-5: Review Segment Integration | Done |
| [#2758](https://github.com/RC918/morningai/issues/2758) | C-5b: SimpleCoderAgent for Flow Pilot | Done |
| [#2749](https://github.com/RC918/morningai/issues/2749) | Integration Tests / Contract Tests | Done |
| [#3182](https://github.com/RC918/morningai/issues/3182) | C-6: Graph Wiring for Hybrid Router | Done |

### C-6 Implementation Evidence

- `HybridRoutingPolicy` implemented in `core/flow/hybrid_routing_policy.py`
- `RouterNode` integrated into LangGraph orchestrator
- Feature flag `ENABLE_DYNAMIC_ROUTING` controls activation
- Fast path (deterministic) handles 70-80% of decisions
- Slow path (LLM-driven) handles ambiguous cases

---

## C-7: Rollout Design (Completed)

Canary rollout strategy and runbook documentation.

### Deliverables

| Item | Description | Status |
|------|-------------|--------|
| Rollout Runbook | `docs/runbooks/FLOW_ROUTER_V3_ROLLOUT.md` (457 lines) | Done |
| Rollback Procedures | Immediate and gradual rollback documented | Done |
| Monitoring Thresholds | Fallback rate, latency p99, error rate defined | Done |

---

## Operationalization Gap (Pending)

> **Tracking Issue**: [#3486](https://github.com/RC918/morningai/issues/3486)

### Current Gaps

| Component | Status | Notes |
|-----------|--------|-------|
| `RouterMetrics` class | Implemented | 399 lines, full API |
| Wiring to `HybridRoutingPolicy` | **Not Wired** | No calls to `record_decision()` |
| Wiring to `RouterNode` | **Not Wired** | `metrics_callback` param exists but not passed |
| API endpoint `/governance/router-metrics` | **Not Verified** | May not exist |
| `router_latency_p99` | **Not Implemented** | Only `get_average_latency()` available |
| `router_error_rate` | **Not Implemented** | No explicit method |

### Action Required Before Pilot Rollout

1. Wire `RouterMetrics` into `HybridRoutingPolicy` or `router_node`
2. Add p99 latency calculation OR update runbook to use `average_latency`
3. Verify or implement `/governance/router-metrics` API endpoint
4. Configure Grafana dashboard with actual metric names
5. Implement `get_error_rate()` OR rely on Sentry's `router_error_count`

---

## Stage 2: Expansion (Planned)

Cost optimization and extended routing coverage.

### Planned Items

| Issue | Description | Status |
|-------|-------------|--------|
| [#2751](https://github.com/RC918/morningai/issues/2751) | Candidate Set Governance | Planned |
| [#2752](https://github.com/RC918/morningai/issues/2752) | Hybrid Routing Optimization | Planned |
| [#2753](https://github.com/RC918/morningai/issues/2753) | Extend to Next Transition | Planned |

---

## Dependencies

```
Stage 0: #2744 → #2745 → #2746 → #2747 (hard dependencies)
Stage 1: #2748 → #2758 (C-5b) → #2749 → #3182 (C-6)
Stage 2: #2751 → #2752 (safety guardrails before cost optimization)

Cross-EPIC:
- EPIC B Phase 6 (B-6): ReviewOutcome schema → consumed by Router
- EPIC D: Depends on Flow Controller for routing decisions
```

---

## Feature Flag Configuration

```yaml
ENABLE_DYNAMIC_ROUTING:
  type: boolean
  default: false
  description: |
    Enable LLM-driven dynamic routing (Flow Controller v3).
    Default False = 100% old behavior (conditional_edges).
    True = Hybrid Router with LLM slow path for ambiguous cases.
```

---

## Verification Signals (Production Readiness)

Before full production rollout, verify:

- [ ] RouterMetrics wired and emitting data ([#3486](https://github.com/RC918/morningai/issues/3486))
- [ ] Fallback rate < 10% in staging
- [ ] Latency p99 < 15s (or average < 5s)
- [ ] No P0/P1 incidents during canary
- [ ] Grafana dashboard configured

---

## Blueprint Alignment

| Blueprint Guarantee | Implementation |
|--------------------|----------------|
| Deterministic | `unknown` verdict triggers fallback to rule-based routing |
| Fail-Safe | LLM timeout/error → deterministic fallback |
| Observable | RouterMetrics + Sentry + Log event codes |
| Reversible | Feature flag instant rollback |

---

## Related Documents

- [Rollout Runbook](./runbooks/FLOW_ROUTER_V3_ROLLOUT.md)
- [EPIC B Roadmap](./EPIC_B_DIFF_AWARE_REVIEW_ROADMAP.md) (ReviewOutcome schema)
- [Wish Pool v2](./north_star/ECOSYSTEM_WISHPOOL_V2.md)

---

## Changelog

| Date | Author | Changes |
|------|--------|---------|
| 2026-01-02 | Ryan Chen (@RC918) with Devin AI | Initial roadmap document |
