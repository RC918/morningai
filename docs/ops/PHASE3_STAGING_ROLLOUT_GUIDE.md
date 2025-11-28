# Phase 3 Staging Rollout Guide

This guide covers the staging rollout process for Phase 3 (ProjectEngineerAgent and multi-agent orchestration).

## Overview

Phase 3 introduces the ProjectEngineerAgent, a multi-agent orchestration system that can analyze code, generate documentation, create tests, and perform code fixes. This guide covers how to safely roll out Phase 3 to staging and monitor its performance.

## Prerequisites

Before starting the staging rollout, ensure:

1. **Phase 3 PRs merged**: PR-1 through PR-4 must be merged to main
2. **Staging environment ready**: Render services (backend-v2-stg, orchestrator-api-stg) deployed
3. **Redis available**: Staging Redis instance configured
4. **Feature flags configured**: Environment variables set in Render

## Environment Variables

### Required Variables

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `ENABLE_PROJECT_ENGINEER_CODEGEN` | boolean | false | Enable code generation mode |
| `ENABLE_PROJECT_ENGINEER_FIXER` | boolean | false | Enable auto-fix in fixer_node |
| `PROJECT_ENGINEER_FIXER_PERCENT` | integer | 0 | Canary percentage for auto-fix (0-100) |

### Phase 3 Metrics Variables

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `PHASE3_METRICS_ENABLED` | boolean | true | Enable Phase 3 metrics collection |
| `PHASE3_P95_MS_THRESHOLD` | integer | 300000 | P95 latency threshold (5 minutes) |
| `PHASE3_SUCCESS_RATE_THRESHOLD` | number | 95.0 | Success rate threshold (%) |
| `PHASE3_TIMEOUT_RATE_THRESHOLD` | number | 2.0 | Timeout rate threshold (%) |

## Rollout Phases

### Phase 1: Analysis-Only Mode (Week 1)

Start with analysis-only mode to validate the system without making code changes.

```bash
# Render Environment Variables
ENABLE_PROJECT_ENGINEER_CODEGEN=false
ENABLE_PROJECT_ENGINEER_FIXER=false
PROJECT_ENGINEER_FIXER_PERCENT=0
PHASE3_METRICS_ENABLED=true
```

**Validation Checklist:**
- [ ] Tasks are being processed without errors
- [ ] Metrics are being collected in Redis
- [ ] Logs show `[ProjectEngineerAgent]` entries
- [ ] No timeout errors in logs

### Phase 2: Execution Mode with 5% Canary (Week 2)

Enable execution mode with a small canary percentage.

```bash
# Render Environment Variables
ENABLE_PROJECT_ENGINEER_CODEGEN=true
ENABLE_PROJECT_ENGINEER_FIXER=true
PROJECT_ENGINEER_FIXER_PERCENT=5
```

**Validation Checklist:**
- [ ] 5% of tasks are using auto-fix
- [ ] PRs are being created successfully
- [ ] Success rate > 95%
- [ ] Timeout rate < 2%

### Phase 3: Gradual Rollout (Week 3-4)

Gradually increase the canary percentage based on metrics.

```bash
# Week 3: 10% canary
PROJECT_ENGINEER_FIXER_PERCENT=10

# Week 3.5: 25% canary (if metrics are good)
PROJECT_ENGINEER_FIXER_PERCENT=25

# Week 4: 50% canary
PROJECT_ENGINEER_FIXER_PERCENT=50

# Week 4.5: 100% rollout
PROJECT_ENGINEER_FIXER_PERCENT=100
```

**Rollout Criteria:**
- Success rate > 95%
- Timeout rate < 2%
- No critical errors in logs
- P95 latency < 5 minutes

## Monitoring

### Phase 3 Dashboard

Use the Phase 3 dashboard to monitor metrics:

```bash
cd ~/repos/morningai
source .venv/bin/activate
export REDIS_URL="your-staging-redis-url"
python tools/monitoring/phase3_dashboard.py --window 15
```

**Dashboard Output:**
```
======================================================================
Phase 3 Dashboard - ProjectEngineerAgent Metrics
Time: 2025-01-15 10:30:00 UTC
Window: Last 15 minutes
======================================================================

Task Execution Summary
----------------------------------------
  Success:      45
  Failed:        2
  Timeout:       1
  Skipped:       5
  Total:        53

  Success Rate:  84.91% (target: > 95%) [WARN]
  Failure Rate:   3.77% (target: < 5%)  [PASS]
  Timeout Rate:   1.89% (target: < 2%)  [PASS]

Execution Mode Distribution
----------------------------------------
  Analysis Only:    30
  Execution:        23
  Execution %:    43.4%

Latency (milliseconds)
----------------------------------------
  P50:      30000 ms
  P90:     120000 ms
  P95:     180000 ms (target: < 300000 ms) [PASS]
  P99:     240000 ms

Semantic Rule Violations
----------------------------------------
  Repo Whitelist:       0
  Directory Whitelist:  0
  Task Type Whitelist:  0
  Total Violations:     0 [PASS]

SLO Status Summary
----------------------------------------
  [WARN] Success rate too low: 84.91%
  [PASS] Failure rate OK: 3.77%
  [PASS] Timeout rate OK: 1.89%
  [PASS] No rule violations
  [PASS] P95 latency OK: 180000 ms

Some SLOs failing - investigate!
======================================================================
```

### Log Queries

Search for Phase 3 logs in Render:

```bash
# All ProjectEngineerAgent logs
[ProjectEngineerAgent]

# Task completion logs
[ProjectEngineerAgent] Task completed

# Timeout logs
[ProjectEngineerAgent] Task timed out

# Metrics logs
[Phase3Metrics]
```

### Redis Metrics Keys

Phase 3 metrics are stored in Redis with the following key patterns:

```
metrics:phase3:pe.task.success:{YYYYMMDDHHMM}
metrics:phase3:pe.task.failed:{YYYYMMDDHHMM}
metrics:phase3:pe.task.timeout:{YYYYMMDDHHMM}
metrics:phase3:pe.task.skipped:{YYYYMMDDHHMM}
metrics:phase3:pe.mode.analysis_only:{YYYYMMDDHHMM}
metrics:phase3:pe.mode.execution:{YYYYMMDDHHMM}
metrics:phase3:pe.latency.bucket_{ms}:{YYYYMMDDHHMM}
metrics:phase3:pe.rule_violation.{type}:{YYYYMMDDHHMM}
```

## Troubleshooting

### High Timeout Rate

If timeout rate exceeds 2%:

1. Check task complexity - are tasks too large?
2. Review `PROJECT_ENGINEER_TASK_TIMEOUT` setting (default: 300s)
3. Check for external API rate limiting
4. Review logs for specific timeout patterns

### Low Success Rate

If success rate drops below 95%:

1. Check for import errors in logs
2. Review semantic rule violations
3. Check DevAgent availability
4. Review specific task types that are failing

### No Metrics Data

If dashboard shows no data:

1. Verify `PHASE3_METRICS_ENABLED=true`
2. Check Redis connectivity
3. Verify tasks are being submitted
4. Check for `[Phase3Metrics] Failed to initialize` in logs

## Rollback Procedure

If issues are detected, rollback by disabling execution mode:

```bash
# Immediate rollback - disable execution
ENABLE_PROJECT_ENGINEER_CODEGEN=false
ENABLE_PROJECT_ENGINEER_FIXER=false
PROJECT_ENGINEER_FIXER_PERCENT=0
```

This will revert to analysis-only mode while preserving the ability to process tasks.

## Production Rollout

After successful staging validation (2+ weeks with good metrics), proceed to production:

1. **Week 1**: Analysis-only mode in production
2. **Week 2**: 5% canary with execution mode
3. **Week 3-4**: Gradual rollout (10% -> 25% -> 50% -> 100%)

Follow the same monitoring and validation procedures as staging.

## Related Documentation

- [ENVIRONMENTS.md](../ENVIRONMENTS.md) - Environment variable reference
- [STAGING_SETUP_GUIDE.md](STAGING_SETUP_GUIDE.md) - Staging environment setup
- [PHASE_2_PRODUCTION_MONITORING_GUIDE.md](PHASE_2_PRODUCTION_MONITORING_GUIDE.md) - Phase 2 monitoring guide
