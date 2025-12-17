# Latency Bucket Configuration

This document describes the latency bucket configuration used for LangGraph rollout metrics collection.

## Current Configuration (Phase 4A)

As of PR #2597 (Phase 4A), the latency buckets are configured as follows:

```python
LATENCY_BUCKETS_MS = [100, 250, 500, 1000, 2500, 5000, 10000, 30000]
```

These buckets are defined in `orchestrator/orchestrator_metrics.py` and used consistently across:
- `orchestrator_metrics.py` - Base metrics collection
- `rollout_tracker.py` - Rollout-specific metrics and percentile calculations
- `phase3_metrics.py` - Phase 3 canary metrics

## Previous Configuration

Before Phase 4A, the buckets were:
```python
[100, 500, 1000, 2000, 5000, 10000, 30000]
```

## Changes Made

The following buckets were modified:
- **Added**: 250ms bucket (between 100ms and 500ms)
- **Changed**: 2000ms bucket replaced with 2500ms bucket

## Impact on Downstream Systems

### Redis Metrics
- Redis metrics use 24-hour TTL (`ttl_seconds = 86400`)
- Old bucket data will naturally expire within 24 hours
- No manual cleanup required

### Dashboard Queries
If you have dashboards or alerts that reference specific bucket labels, update them:

| Old Label | New Label |
|-----------|-----------|
| `latency_bucket_2000` | `latency_bucket_2500` |
| (none) | `latency_bucket_250` |

### Grafana/Datadog Queries
Update any queries that hardcode bucket values:

```promql
# Old query (will break)
sum(rate(latency_bucket_2000[5m]))

# New query
sum(rate(latency_bucket_2500[5m]))
```

## Rationale

The new bucket configuration provides:
1. **Better granularity at low latencies**: 250ms bucket helps distinguish between fast (100-250ms) and moderate (250-500ms) responses
2. **Aligned with SLO thresholds**: 2500ms aligns better with typical P95 latency SLO targets

## Related

- PR #2597 - Phase 4A implementation
- Issue #2599 - Documentation task
- Epic #2311 - LangGraph 100% Rollout

## Contact

For questions about metrics configuration, contact the data/analytics team or refer to the Epic #2311 tracking issue.
