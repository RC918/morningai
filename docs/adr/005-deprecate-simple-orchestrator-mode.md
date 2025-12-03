# ADR-005: Deprecate Simple Orchestrator Mode

## Status

Accepted

## Date

2025-12-03

## Context

The MorningAI orchestrator currently supports two execution modes:

1. **Simple Mode** (`USE_LANGGRAPH=false`): Direct execution path without stateful workflow management. Faster response time but lacks reflection and planning capabilities.

2. **LangGraph Mode** (`USE_LANGGRAPH=true` or `USE_LANGGRAPH_PERCENT>0`): Full stateful workflow with retry logic, reflection, and planning capabilities via LangGraph.

The canary deployment infrastructure has been in place since Phase 1, using MD5 hash-based deterministic routing to gradually shift traffic from Simple Mode to LangGraph Mode. Current metrics show LangGraph Mode is stable with acceptable latency and success rates.

Maintaining two execution paths creates:
- Code divergence and maintenance burden
- Inconsistent telemetry and debugging experience
- Difficulty in adding new features that require stateful workflow

## Decision

We will deprecate Simple Mode and make LangGraph Mode the default orchestrator for all non-FAQ tasks.

### Rollout Plan

| Phase | Canary % | Duration | Success Criteria |
|-------|----------|----------|------------------|
| 1 | 5% | 1 week | Baseline metrics established |
| 2 | 15% | 1 week | Success rate > 95%, p95 < 30s |
| 3 | 25% | 1 week | No SLO breaches |
| 4 | 50% | 1 week | Stable performance |
| 5 | 100% | - | Full rollout |

### FAQ Task Exception

FAQ tasks will continue to use Simple Mode by default due to:
- Lower latency requirements for FAQ generation
- No benefit from reflection/planning for simple FAQ tasks
- 12-node LangGraph overhead not justified for FAQ workload

A new feature flag `USE_LANGGRAPH_FOR_FAQ` (default: false) will be introduced for future experimentation.

### Rollback Strategy

If SLOs regress at any phase:
1. Set `USE_LANGGRAPH_PERCENT=0` in environment
2. Redeploy service (automatic on Render)
3. Verify routing returns to Simple Mode
4. Investigate root cause before re-enabling

See `docs/runbooks/canary_rollback.md` for detailed rollback procedure.

## Consequences

### Positive

- **Unified execution path**: All tasks benefit from reflection and planning
- **Consistent telemetry**: Single code path simplifies debugging and monitoring
- **Feature enablement**: New features requiring stateful workflow can be added without mode-specific logic
- **Reduced maintenance**: No need to maintain two parallel execution paths

### Negative

- **Increased latency**: LangGraph Mode has higher baseline latency than Simple Mode
- **Resource usage**: Stateful workflow requires more memory (MemorySaver checkpoints)
- **Migration risk**: Potential for regressions during transition period

### Mitigations

- Gradual canary rollout with SLO monitoring
- `RQ_MAX_JOBS` setting to prevent OOM from MemorySaver accumulation
- FAQ tasks exempt from LangGraph to preserve low-latency path
- Rollback procedure documented and tested

## Related

- Issue: #1814 [P2] LangGraph Mode Full Switch
- Runbook: `docs/runbooks/canary_rollback.md`
- Monitoring: `tools/monitoring/canary_dashboard.py`
- Phase 3 Guide: `docs/ops/PHASE3_STAGING_ROLLOUT_GUIDE.md`
