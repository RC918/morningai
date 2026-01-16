# EPIC I: Runtime Governance & Immune System Roadmap

**Issue**: [#3342](https://github.com/RC918/morningai/issues/3342)
**Blueprint Reference**: Section 4.3 (Model Governance Framework v2) + Section 4.4 (Autonomous Provisioning v2)
ˇ**Status**: Phase I-1 Complete, Phase I-2a Complete (observe-only), Phase I-2b Complete (disabled by default)
**Last Updated**: 2026-01-16

## Recent Updates

### 2026-01-16: Phase I-2b Complete (Drift-Triggered Retry)

**Gate Lifted**: #3249 merged (test refactor complete)

| Component | File | Lines | Status |
|-----------|------|-------|--------|
| `DriftRetryPolicy` | `governance/drift_retry.py` | 399 | **COMPLETE** - Policy configuration with all options |
| `DriftRetryDecision` | `governance/drift_retry.py` | 131-291 | **COMPLETE** - Decision engine with safety guards |
| `should_retry_on_drift()` | `governance/drift_retry.py` | 367-390 | **COMPLETE** - Convenience function |
| Settings Integration | `common/config/settings.py` | 664-702 | **COMPLETE** - All env vars defined |
| LLMClient Wiring | `llm/client.py` | 490-542 | **COMPLETE** - Retry logic integrated |

**Feature Flags** (disabled by default):
- `DRIFT_RETRY_ENABLED=false` - Master switch
- `DRIFT_RETRY_MAX_RETRIES=1` - Max retry attempts
- `DRIFT_RETRY_MODEL_TIER=higher` - Escalation strategy
- `DRIFT_RETRY_COST_CAP_MULTIPLIER=2.0` - Cost protection

**To Enable**: Set `DRIFT_RETRY_ENABLED=true` in Render Dashboard (staging first).

---

### 2026-01-15: Encapsulation Improvements (PR #4009)

**Issues Closed**: #3958, #3961
**Tag**: `week3-pr3-epic-i-encapsulation`

| Component | Change | Benefit |
|-----------|--------|---------|
| `CapabilityScoreManager` | Added `_extract_task_type()` helper with validation | Robust task_id parsing, handles edge cases |
| `DegradationAdvisor` | Added `set_provider_state()` public method | Clean encapsulation, no direct private attribute access |
| `RoutingPolicyEvolver` | Uses public method instead of `_provider_states` | Better maintainability, follows Blueprint Section 4.4 |

**Code Quality**:
- Structured logging with `extra={}` fields for programmatic log parsing
- Comprehensive validation for malformed task_id inputs
- Thread-safe state updates via existing `_lock` mechanism

## Executive Summary

EPIC I transforms MorningAI from a "static code system" to a "dynamic governance system" with self-healing capabilities. This roadmap operationalizes the existing governance code (drift detection, health scoring, alerting, degradation advisory) into a living immune system that monitors, detects, and responds to model/provider degradation in real-time.

## Architecture Vision

### From "Library" to "Service"

| Layer | Current State | Target State | Key Change |
|-------|---------------|--------------|------------|
| Drift Detection | Code exists, wired to LLMClient | Active monitoring with metrics | Already operational |
| Health Scoring | CanaryMetrics in Redis | Periodic evaluation with alerting | **COMPLETE** - heartbeat_handler.py |
| Alerting | HealthAlertService library | Scheduled checks with Slack/webhook | **COMPLETE** - heartbeat_handler.py |
| Degradation | DegradationAdvisor observe-only | Soft weighting affects routing | **COMPLETE** (observe-only) - needs DEGRADATION_ENFORCEMENT_ENABLED=true |

### Existing Components Analysis

| Component | File | Lines | Current Status |
|-----------|------|-------|----------------|
| DriftDetector | `governance/drift_detector.py` | 450 | Wired to LLMClient, observe-only |
| CanaryMetrics | `metrics.py` | 1000+ | Redis-based, health scoring active |
| HealthAlertService | `governance/health_alerter.py` | 530 | **COMPLETE** - scheduled via heartbeat_handler.py |
| DegradationAdvisor | `governance/degradation_advisor.py` | 792 | **Phase A+B-1 complete** - hard gating in llm/client.py |
| DegradationTypes | `governance/degradation_types.py` | 150 | Data structures defined |
| HeartbeatHandler | `governance/heartbeat_handler.py` | 519 | **NEW** - distributed lock + health snapshot |

**Key Finding**: ~~Substantial code exists but is not fully "activated" - the system has muscles but no heartbeat.~~ **UPDATE 2026-01-09**: The heartbeat is now implemented in `heartbeat_handler.py` with distributed locking and health snapshot publishing.

---

## Phase Breakdown

### Phase I-1: Operationalization (The Heartbeat)

**Objective**: Transform governance libraries into active services by implementing a scheduled heartbeat that periodically evaluates provider health and triggers alerts.

**Implementation Location**: `redis_queue/worker.py` - existing heartbeat thread

**Deliverables**:

1. **Governance Heartbeat Integration**:

```python
# In redis_queue/worker.py - update_worker_heartbeat()

from governance.health_alerter import get_health_alert_service
from governance.degradation_advisor import get_degradation_advisor
from meta_agent.distributed_vm_lock import DistributedLock

GOVERNANCE_LOCK_KEY = "governance_evaluator_lock"
GOVERNANCE_LOCK_TTL = 50  # seconds (less than heartbeat interval)

def run_governance_heartbeat():
    """
    EPIC I-1: Governance Heartbeat

    Runs health checks and degradation advisory with distributed lock
    to prevent multiple workers from executing simultaneously.
    """
    try:
        # Acquire distributed lock to prevent duplicate execution
        lock = DistributedLock(
            lock_key=GOVERNANCE_LOCK_KEY,
            ttl_seconds=GOVERNANCE_LOCK_TTL
        )

        if not lock.acquire():
            logger.debug("[I-1-HEARTBEAT] Another worker holds governance lock, skipping")
            return

        try:
            # Health Alerting
            alert_service = get_health_alert_service()
            if alert_service and alert_service.enabled:
                result = alert_service.check_all_providers()
                if result.get("alerts_sent", 0) > 0:
                    logger.info(f"[I-1-HEARTBEAT] Sent {result['alerts_sent']} health alerts")

            # Degradation Advisory
            advisor = get_degradation_advisor()
            if advisor and advisor.enabled:
                result = advisor.compute_all_advisories()
                if result.get("advisories_logged", 0) > 0:
                    logger.info(f"[I-1-HEARTBEAT] Logged {result['advisories_logged']} advisories")

            # Update global health snapshot (for routing engine consumption)
            _update_global_health_snapshot()

        finally:
            lock.release()

    except Exception as e:
        logger.warning(f"[I-1-HEARTBEAT] Governance heartbeat failed: {e}")
```

2. **Distributed Lock Contract**:

| Parameter | Value | Rationale |
|-----------|-------|-----------|
| Lock Key | `governance_evaluator_lock` | Unique namespace for governance |
| TTL | 50 seconds | Less than 60s heartbeat interval |
| Retry | No | Skip if locked, next heartbeat will try |

3. **Global Health Snapshot Schema**:

```json
{
  "$schema": "https://json-schema.org/draft-07/schema#",
  "title": "GlobalHealthSnapshot",
  "type": "object",
  "required": ["timestamp", "providers", "version"],
  "properties": {
    "timestamp": {
      "type": "string",
      "format": "date-time",
      "description": "Snapshot creation time in UTC (ISO 8601)"
    },
    "version": {
      "type": "string",
      "default": "1.0.0",
      "description": "Schema version for forward compatibility"
    },
    "providers": {
      "type": "object",
      "additionalProperties": {
        "type": "object",
        "properties": {
          "health_score": {
            "type": "number",
            "minimum": 0,
            "maximum": 100,
            "description": "Provider health score (0-100 scale)"
          },
          "severity": {
            "type": "string",
            "enum": ["healthy", "degraded", "critical", "avoid"],
            "description": "Degradation severity level"
          },
          "score_multiplier": {
            "type": "number",
            "minimum": 0,
            "maximum": 1,
            "description": "Routing weight multiplier based on severity"
          },
          "last_updated": {
            "type": "string",
            "format": "date-time",
            "description": "Last update time for this provider"
          }
        }
      }
    },
    "ttl_seconds": {
      "type": "integer",
      "default": 120,
      "description": "Snapshot validity period (2x heartbeat interval)"
    }
  }
}
```

4. **Redis Key Design**:

| Key | TTL | Purpose |
|-----|-----|---------|
| `governance:health_snapshot` | 120s | Global health state for routing |
| `governance:last_evaluation` | 300s | Timestamp of last successful evaluation |
| `governance:alert_cooldown:{provider}` | configurable | Per-provider alert cooldown |

**Acceptance Criteria**:
- [x] Governance heartbeat runs every 60 seconds *(implemented in `heartbeat_handler.py:295-484`)*
- [x] Distributed lock prevents duplicate execution across workers *(implemented in `heartbeat_handler.py:92-227`)*
- [x] Health alerts sent to Slack when thresholds breached *(implemented in `health_alerter.py:190-230`)*
- [x] Global health snapshot updated in Redis *(implemented in `heartbeat_handler.py:230-292`)*
- [x] Metrics emitted: `governance_heartbeat_success_total`, `governance_heartbeat_duration_seconds`

**Success Metric**: Slack receives first automated "Provider Latency Warning" alert.

> **Implementation Note (2026-01-09)**: Phase I-1 is fully implemented. The heartbeat runs via `run_governance_cycle()` with distributed lock (`governance:evaluator_lock`, 50s TTL) and publishes health snapshots to `governance:health_snapshot` (120s TTL). Health alerting requires `HEALTH_ALERTING_ENABLED=true` to activate.

---

### Phase I-2a: Defensive Gating (Soft Weighting Activation)

**Objective**: Enable the routing engine to consume degradation state and apply soft weighting to provider selection.

**Prerequisite**: Phase I-1 complete (health snapshot being updated)

**Deliverables**:

1. **Feature Flag Definition**:

```python
# Environment variable
DEGRADATION_ENFORCEMENT_ENABLED = os.getenv("DEGRADATION_ENFORCEMENT_ENABLED", "false").lower() == "true"
```

| Environment | Value | Rationale |
|-------------|-------|-----------|
| Development | `false` | Safe default |
| Staging | `true` | Validation environment |
| Production | `false` initially | Enable after staging validation |

2. **Routing Engine Integration** (already exists, needs activation):

```python
# In core/routing/engine.py - _apply_soft_weighting()

def _apply_soft_weighting(self, provider: str) -> float:
    """
    EPIC I-4 Phase B-2: Soft Weighting based on degradation state.

    Returns a multiplier (0.0-1.0) to apply to provider's base score.
    """
    if not settings.degradation_enforcement_enabled:
        return 1.0  # No adjustment when disabled

    advisor = get_degradation_advisor()
    if advisor is None:
        return 1.0

    state = advisor.get_provider_state(provider)
    multiplier = SEVERITY_MULTIPLIERS.get(state, 1.0)

    if multiplier < 1.0:
        logger.info(
            f"[I-4-SOFT-WEIGHTING] Provider {provider} has {state.value} state, "
            f"applying multiplier {multiplier}"
        )

    return multiplier
```

3. **Severity Multipliers** (already defined in `degradation_types.py`):

| Severity | Multiplier | Effect |
|----------|------------|--------|
| HEALTHY | 1.0 | No change |
| DEGRADED | 0.7 | 30% score reduction |
| CRITICAL | 0.3 | 70% score reduction |
| AVOID | 0.1 | 90% score reduction (floor protection) |

4. **Shadow-to-Active Transition Criteria**:

| Criterion | Threshold | Measurement |
|-----------|-----------|-------------|
| Heartbeat Stability | 7 days | No missed heartbeats |
| Alert Accuracy | >90% | Manual review of alerts |
| False Positive Rate | <10% | Alerts that didn't indicate real issues |
| #3249 Status | Merged | Test refactor complete |

**Acceptance Criteria**:
- [x] `DEGRADATION_ENFORCEMENT_ENABLED` flag implemented *(in `llm/client.py:139` - controls Hard Gating only)*
- [x] Routing engine consumes degradation state from the governance heartbeat *(via `degradation_advisor.py`)*
- [x] Soft weighting applied to provider scores *(in `core/routing/engine.py:564-616` - `_get_degradation_multiplier()`)*
- [x] Floor provider protection prevents total provider exclusion *(in `llm/client.py:145-269` - `_apply_hard_gating()`)*
- [ ] Metrics emitted: `routing_soft_weighting_applied_total` *(pending - needs follow-up issue)*

> **Implementation Note (2026-01-09)**: Phase I-2a has two distinct mechanisms:
> 1. **Soft Weighting** (`core/routing/engine.py:_get_degradation_multiplier`): Always active, applies score multipliers based on `DegradationAdvisor` state. Currently returns 1.0 (no effect) because `DegradationAdvisor` operates in observe-only mode (`dry_run=True`).
> 2. **Hard Gating** (`llm/client.py:_apply_hard_gating`): Controlled by `DEGRADATION_ENFORCEMENT_ENABLED`. When enabled, filters out AVOID providers with floor protection.
>
> To fully activate degradation enforcement, set `DEGRADATION_ENFORCEMENT_ENABLED=true` in staging first.

---

### Phase I-2b: Active Recovery (Drift-Triggered Retry)

**Objective**: Implement intelligent retry logic that uses a higher-tier model when drift is detected.

**Prerequisite**: Phase I-2a complete, #3249 merged (test stability confirmed)

**Deliverables**:

1. **Drift-Triggered Retry Schema**:

```json
{
  "$schema": "https://json-schema.org/draft-07/schema#",
  "title": "DriftRetryPolicy",
  "type": "object",
  "required": ["enabled", "max_retries", "eligible_drift_types"],
  "properties": {
    "enabled": {
      "type": "boolean",
      "default": false,
      "description": "Whether drift-triggered retry is enabled"
    },
    "max_retries": {
      "type": "integer",
      "default": 1,
      "minimum": 0,
      "maximum": 2,
      "description": "Maximum retry attempts per request"
    },
    "eligible_drift_types": {
      "type": "array",
      "items": {
        "type": "string",
        "enum": ["json_parse_error", "schema_violation", "empty_response"]
      },
      "description": "Drift types that trigger retry (excludes unexpected_format)"
    },
    "retry_model_tier": {
      "type": "string",
      "enum": ["same", "higher", "highest"],
      "default": "higher",
      "description": "Model tier to use for retry"
    },
    "cost_cap_multiplier": {
      "type": "number",
      "default": 2.0,
      "minimum": 1.0,
      "maximum": 5.0,
      "description": "Maximum cost increase allowed for retry"
    },
    "eligible_task_types": {
      "type": "array",
      "items": { "type": "string" },
      "default": ["code_generation", "code_review"],
      "description": "Task types eligible for retry (excludes low-value tasks)"
    }
  }
}
```

2. **Retry Decision Logic**:

```python
class DriftRetryDecision:
    """
    EPIC I-2b: Drift-Triggered Retry Decision Engine

    Decides whether to retry a request after drift detection.
    """

    def should_retry(
        self,
        drift_result: DriftValidationResult,
        task_context: TaskContext,
        attempt_count: int
    ) -> RetryDecision:
        """
        Determine if retry should be attempted.

        Safety Guards:
        1. Max retry limit (default: 1)
        2. Eligible drift types only (not unexpected_format)
        3. Cost cap enforcement
        4. Task type eligibility
        """
        if not self.policy.enabled:
            return RetryDecision(should_retry=False, reason="retry_disabled")

        if attempt_count >= self.policy.max_retries:
            return RetryDecision(should_retry=False, reason="max_retries_exceeded")

        if drift_result.drift_type not in self.policy.eligible_drift_types:
            return RetryDecision(should_retry=False, reason="drift_type_not_eligible")

        if task_context.task_type not in self.policy.eligible_task_types:
            return RetryDecision(should_retry=False, reason="task_type_not_eligible")

        # Calculate retry cost
        retry_model = self._select_retry_model(task_context)
        estimated_cost = self._estimate_retry_cost(retry_model, task_context)

        if estimated_cost > task_context.original_cost * self.policy.cost_cap_multiplier:
            return RetryDecision(should_retry=False, reason="cost_cap_exceeded")

        return RetryDecision(
            should_retry=True,
            retry_model=retry_model,
            reason="drift_detected_eligible_for_retry"
        )
```

3. **Risk Mitigation**:

| Risk | Mitigation | Implementation |
|------|------------|----------------|
| Cost explosion | Cost cap multiplier (default 2x) | Reject retry if cost > 2x original |
| Latency spike | Timeout inheritance | Retry uses remaining timeout |
| Feedback loop | Drift type filtering | Only retry for parse/schema errors |
| Low-value retry | Task type filtering | Only retry code generation tasks |

**Acceptance Criteria**:
- [x] Drift retry policy configurable via environment *(implemented in `common/config/settings.py:664-702`)*
- [x] Retry only triggers for eligible drift types *(implemented in `governance/drift_retry.py:182-193`)*
- [x] Cost cap prevents runaway spending *(implemented in `governance/drift_retry.py:206-218`)*
- [x] Retry uses higher-tier model from same provider family *(implemented in `governance/drift_retry.py:251-271`)*
- [ ] Metrics emitted: `drift_retry_total`, `drift_retry_success_total` *(pending - needs follow-up issue)*

> **Implementation Note (2026-01-16)**: Phase I-2b is fully implemented. The drift retry logic is wired into `llm/client.py:490-542` and triggers when drift is detected. Feature is disabled by default (`DRIFT_RETRY_ENABLED=false`). To enable, set `DRIFT_RETRY_ENABLED=true` in Render Dashboard (staging first).

---

### Phase I-3: Autonomous Evolution (Benchmark & Capability Scoring)

**Objective**: Implement periodic benchmark evaluation and automatic capability score updates, enabling the system to self-evolve based on real performance data.

**Prerequisite**: Phase I-2a/2b complete and stable for 30 days

**Deliverables**:

1. **Benchmark Task Schema**:

```json
{
  "$schema": "https://json-schema.org/draft-07/schema#",
  "title": "BenchmarkTask",
  "type": "object",
  "required": ["task_id", "task_type", "prompt", "expected_output_schema"],
  "properties": {
    "task_id": {
      "type": "string",
      "description": "Unique identifier for benchmark task"
    },
    "task_type": {
      "type": "string",
      "enum": ["code_generation", "code_review", "bug_fix", "refactor"],
      "description": "Type of coding task"
    },
    "prompt": {
      "type": "string",
      "description": "Standardized prompt for benchmark"
    },
    "expected_output_schema": {
      "type": "object",
      "description": "JSON Schema for expected output format"
    },
    "evaluation_criteria": {
      "type": "object",
      "properties": {
        "correctness_weight": { "type": "number", "default": 0.4 },
        "format_compliance_weight": { "type": "number", "default": 0.3 },
        "latency_weight": { "type": "number", "default": 0.2 },
        "cost_weight": { "type": "number", "default": 0.1 }
      }
    }
  }
}
```

2. **Capability Score Update Schema**:

```json
{
  "$schema": "https://json-schema.org/draft-07/schema#",
  "title": "ProviderCapabilityScore",
  "type": "object",
  "required": ["provider", "model", "task_type", "score", "sample_size", "last_updated"],
  "properties": {
    "provider": { "type": "string" },
    "model": { "type": "string" },
    "task_type": { "type": "string" },
    "score": {
      "type": "number",
      "minimum": 0,
      "maximum": 100,
      "description": "Capability score (0-100 scale)"
    },
    "sample_size": {
      "type": "integer",
      "minimum": 1,
      "description": "Number of benchmark runs contributing to score"
    },
    "confidence": {
      "type": "number",
      "minimum": 0,
      "maximum": 1,
      "description": "Statistical confidence in score"
    },
    "trend": {
      "type": "string",
      "enum": ["improving", "stable", "degrading"],
      "description": "Score trend over last 4 weeks"
    },
    "last_updated": {
      "type": "string",
      "format": "date-time"
    }
  }
}
```

3. **Benchmark Scheduler**:

| Schedule | Task | Purpose |
|----------|------|---------|
| Weekly (Sunday 02:00 UTC) | Full benchmark suite | Comprehensive evaluation |
| Daily (02:00 UTC) | Smoke test subset | Early degradation detection |
| On-demand | Specific provider | Post-incident validation |

4. **Auto-Update Rules**:

| Condition | Action | Safety Guard |
|-----------|--------|--------------|
| Score drops >10% | Alert + flag for review | No auto-downgrade without review |
| Score drops >20% | Auto-downgrade severity | Floor provider protection |
| Score improves >10% | Flag for review | No auto-upgrade without review |
| New model available | Schedule benchmark | Compare before enabling |

**Acceptance Criteria**:
- [ ] Benchmark suite defined for code generation tasks
- [ ] Weekly benchmark runs automatically
- [ ] Capability scores updated in database
- [ ] Trend analysis identifies degrading providers
- [ ] Alerts sent for significant score changes
- [ ] No auto-upgrade without human review

**North Star Hook**: This phase implements Blueprint 4.4 "MorningAI has self-evolution capability."

---

## Cross-EPIC Integration: RuntimeTrustScore

### E + I + F Closed Loop

```
EPIC E (Safety) ──┐
                  ├──> RuntimeTrustScore ──> EPIC F (Planner)
EPIC I (Health) ──┘
```

### TrustScore Schema

```json
{
  "$schema": "https://json-schema.org/draft-07/schema#",
  "title": "RuntimeTrustScore",
  "type": "object",
  "required": ["trust_score", "safety_score", "health_score", "timestamp"],
  "properties": {
    "trust_score": {
      "type": "number",
      "minimum": 0,
      "maximum": 1,
      "description": "Combined trust score: min(safety_score, health_score)"
    },
    "safety_score": {
      "type": "number",
      "minimum": 0,
      "maximum": 1,
      "description": "From EPIC E SafetyDecision (allow=1.0, needs_review=0.6, block=0.0)"
    },
    "health_score": {
      "type": "number",
      "minimum": 0,
      "maximum": 1,
      "description": "From EPIC I CanaryMetrics (health_score / 100)"
    },
    "timestamp": {
      "type": "string",
      "format": "date-time"
    },
    "components": {
      "type": "object",
      "properties": {
        "safety_decision": { "type": "string", "enum": ["allow", "block", "needs_review"] },
        "provider_severity": { "type": "string", "enum": ["healthy", "degraded", "critical", "avoid"] },
        "drift_detected": { "type": "boolean" }
      }
    }
  }
}
```

### TrustScore Calculation

```python
def calculate_trust_score(
    safety_decision: SafetyDecision,
    health_data: ProviderHealthData
) -> RuntimeTrustScore:
    """
    Calculate RuntimeTrustScore using "weakest link" principle.

    Formula: trust = min(safety_score, health_score)

    Rationale: A system with 100% health but 0% safety (PII leak risk)
    should have 0% trust. The weakest link determines overall trust.
    """
    # Map SafetyDecision to numeric score
    safety_score_map = {
        "allow": 1.0,
        "needs_review": 0.6,
        "block": 0.0
    }
    safety_score = safety_score_map.get(safety_decision.action, 0.5)

    # Normalize health score to 0-1 range
    health_score = health_data.health_score / 100.0

    # Apply "weakest link" principle
    trust_score = min(safety_score, health_score)

    return RuntimeTrustScore(
        trust_score=trust_score,
        safety_score=safety_score,
        health_score=health_score,
        timestamp=datetime.now(timezone.utc),
        components={
            "safety_decision": safety_decision.action,
            "provider_severity": health_data.severity,
            "drift_detected": health_data.drift_rate > 0
        }
    )
```

### Planner Integration

| Trust Score | Planner Behavior | Rationale |
|-------------|------------------|-----------|
| >= 0.8 | Normal execution | High confidence |
| 0.6 - 0.8 | Add monitoring step | Elevated caution |
| < 0.6 | Force `human_approval_node` | Low confidence requires HITL |
| < 0.3 | Block execution | Critical risk |

**Hysteresis**: Trust threshold has 0.1 recovery buffer to prevent oscillation.

---

## Quality Gate: #3249 Dependency

### Current Status

Issue [#3249](https://github.com/RC918/morningai/issues/3249) is a test refactoring task, NOT a functional blocker.

### Interpretation

| Phase | #3249 Requirement | Rationale |
|-------|-------------------|-----------|
| I-1 (Heartbeat) | Not required | Observe-only, no routing impact |
| I-2a (Soft Weighting) | Not required | Can enable in staging without test stability |
| I-2b (Drift Retry) | **Required** | Retry decisions need validated drift detection |
| I-3 (Benchmark) | **Required** | Benchmark accuracy depends on stable tests |

### Transition Criteria

Phase I-2b and I-3 are gated until:
1. #3249 is merged
2. Drift detection false positive rate < 5% (measured over 14 days)
3. Manual review confirms drift alerts are actionable

---

## MVP Scope Guardrail (Non-Goals)

The following are explicitly OUT OF SCOPE for MVP:

- Full Autonomous Provisioning (auto-enable new models without review)
- Cross-provider failover (automatic switch to different provider on failure)
- Cost optimization routing (choosing cheapest provider that meets quality threshold)
- Real-time model performance comparison dashboard
- Automated incident response (auto-rollback on degradation)

These will be tracked as follow-up issues after MVP completion.

---

## Dependencies

| Dependency | Type | Status |
|------------|------|--------|
| EPIC C (Flow Controller v3) | Integration | Completed |
| EPIC D (Autonomous Coder) | Integration | Completed |
| EPIC E (Safety Governor v2) | Future Integration | Planning |
| EPIC F (Planner v3) | Future Integration | Planning |
| #3249 (Test Refactor) | Quality Gate | Open |
| CanaryMetrics | Existing | Available |
| DistributedLock | Existing | Available |

---

## Success Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| Heartbeat Uptime | >99.9% | No missed heartbeats in 7 days |
| Alert Accuracy | >90% | Alerts indicate real issues |
| False Positive Rate | <10% | Alerts that didn't need action |
| MTTR (Mean Time to Recovery) | <15 min | Time from degradation to routing adjustment |
| Drift Detection Recall | >95% | Actual drifts detected |

---

## Timeline Estimate

| Phase | Estimated Duration | Dependencies |
|-------|-------------------|--------------|
| I-1 | 3-5 days | None |
| I-2a | 2-3 days | I-1 |
| I-2b | 5-7 days | I-2a, #3249 |
| I-3 | 10-14 days | I-2b, 30-day stability |

**Total Estimated Duration**: 4-6 weeks (excluding stability waiting periods)

---

## Operational Runbook

### Emergency Procedures

1. **Disable Governance Heartbeat**:
   ```bash
   # Set in Render environment
   GOVERNANCE_HEARTBEAT_ENABLED=false
   ```

2. **Disable Soft Weighting**:
   ```bash
   DEGRADATION_ENFORCEMENT_ENABLED=false
   ```

3. **Clear Health Snapshot**:
   ```bash
   redis-cli DEL governance:health_snapshot
   ```

4. **Force Provider Recovery**:
   ```python
   advisor = get_degradation_advisor()
   advisor.clear_state(provider="openai")
   ```

### Monitoring Queries

| Query | Purpose |
|-------|---------|
| `governance_heartbeat_success_total` | Heartbeat health |
| `governance_alert_sent_total{channel="slack"}` | Alert volume |
| `routing_soft_weighting_applied_total` | Weighting activity |
| `drift_detected_total{severity="high"}` | Drift frequency |

---

## References

- [Blueprint Section 4.3: Model Governance Framework v2](../north_star/MorningAI_Ecosystem_Blueprint_2025_Final.md)
- [Blueprint Section 4.4: Autonomous Provisioning v2](../north_star/MorningAI_Ecosystem_Blueprint_2025_Final.md)
- [Wish Pool v2: EPIC I](../north_star/ECOSYSTEM_WISHPOOL_V2.md)
- [DriftDetector](../../handoff/20250928/40_App/orchestrator/governance/drift_detector.py)
- [HealthAlertService](../../handoff/20250928/40_App/orchestrator/governance/health_alerter.py)
- [DegradationAdvisor](../../handoff/20250928/40_App/orchestrator/governance/degradation_advisor.py)
- [CanaryMetrics](../../handoff/20250928/40_App/orchestrator/metrics.py)
