# Redis Queue Integration Tests

These tests provide local development integration test coverage for the RolloutTracker and Redis Queue components. **These tests are NOT collected by CI.**

## Important Note

The CI Orchestrator Tests job runs `pytest tests/` from the orchestrator directory, which does **not** include `redis_queue/tests/`. Therefore:

- These tests do **not** affect the CI coverage gate (50% threshold)
- These tests are intended for local development verification only
- To improve CI coverage, add tests to `tests/` directory instead

## Purpose

These integration tests verify:

- RolloutTracker integration with worker.py
- Redis pipeline operations correctness
- Circuit breaker behavior with Redis persistence
- Feature flag configuration (`rollout_tracker_enabled`)
- enabled=True + Redis write verification (Issue #2641)

## Running Tests Locally

```bash
# Set REPO_ROOT to your local morningai repository path
REPO_ROOT=/path/to/morningai

cd "$REPO_ROOT" && source .venv/bin/activate && \
export PYTHONPATH="$PWD/handoff/20250928/40_App/orchestrator:$PWD/handoff/20250928/40_App/api-backend/src:$PWD:$PYTHONPATH" && \
pytest handoff/20250928/40_App/orchestrator/redis_queue/tests/ -v
```

## Test Files

| File | Description |
|------|-------------|
| `test_rollout_tracker_integration.py` | RolloutTracker integration tests including enabled=True + Redis scenarios |
| `test_meta_agent_worker.py` | Meta agent worker integration tests |

## Not Covered Yet (Known Gaps)

The following scenarios are not yet covered by automated tests and represent areas for future improvement:

| Category | Scenario | Risk Level | Notes |
|----------|----------|------------|-------|
| **Concurrency** | Multi-worker race conditions | Medium | Multiple workers updating same Redis keys simultaneously |
| **Concurrency** | Multi-process circuit breaker state | Medium | Circuit breaker state consistency across processes |
| **Redis Failures** | Connection timeout handling | High | Redis unavailable during `record_langgraph_task()` |
| **Redis Failures** | Network partition recovery | Medium | Reconnection behavior after temporary outage |
| **Redis Failures** | Pipeline partial failure | Low | Some commands succeed, others fail in pipeline |
| **Edge Cases** | Long-running job timeout | Low | Jobs exceeding expected duration |
| **Edge Cases** | Redis memory pressure | Low | Behavior when Redis approaches memory limit |
| **Edge Cases** | Clock skew between workers | Low | Time-based cooldown with unsynchronized clocks |

These gaps are tracked for future work. Contributions welcome.

## Related Issues

- Issue #2280 - Integrate RolloutTracker to worker.py
- Issue #2641 - enabled=True + Redis integration tests
- Issue #2648 - Document redis_queue/tests purpose and positioning

## See Also

- `tests/test_rollout_tracker.py` - Unit tests (collected by CI)
- `rollout_tracker.py` - RolloutTracker implementation
