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

## Fault Injection Tests (Issue #2650)

The `test_fault_injection.py` module provides comprehensive fault injection tests covering:

| Category | Test Class | Scenarios Covered |
|----------|------------|-------------------|
| **Concurrency** | `TestConcurrencyFaultInjection` | Multi-worker race conditions, concurrent circuit breaker state transitions, thread-safe reads |
| **Redis Failures** | `TestRedisFailureFaultInjection` | Connection timeout, pipeline partial failure, reconnection after outage, memory pressure (OOM) |
| **Edge Cases** | `TestEdgeCaseFaultInjection` | Long-running tasks, zero/negative latency, empty/long/unicode trace IDs |
| **Circuit Breaker** | `TestCircuitBreakerFaultInjection` | Consecutive failures, half-open probe requests, cooldown expiry |
| **Real Redis** | `TestRealRedisIntegration` | Real Redis record/retrieve, concurrent writes, circuit breaker persistence |

### Running Fault Injection Tests

```bash
# Run all fault injection tests
pytest handoff/20250928/40_App/orchestrator/redis_queue/tests/test_fault_injection.py -v

# Run specific test class
pytest handoff/20250928/40_App/orchestrator/redis_queue/tests/test_fault_injection.py::TestConcurrencyFaultInjection -v

# Run with real Redis (requires REDIS_URL)
REDIS_URL=redis://localhost:6379/0 pytest handoff/20250928/40_App/orchestrator/redis_queue/tests/test_fault_injection.py::TestRealRedisIntegration -v
```

## CI Integration (Issue #2650)

These tests are now collected by the `orchestrator-integration-tests` CI workflow:
- Runs on merge queue and push to main
- Non-blocking (doesn't fail PRs)
- Includes Redis service for real integration tests
- Results uploaded as artifacts

### Test Markers

Tests are marked for selective execution and flaky test monitoring:

| Marker | Description | Usage |
|--------|-------------|-------|
| `@pytest.mark.concurrency` | Multi-threading tests (potential flakiness) | `pytest -m concurrency` |
| `@pytest.mark.integration` | Tests requiring real Redis | `pytest -m integration` |

### Graduation Plan

The CI workflow follows a staged approach to becoming a required check:

| Stage | Status | Criteria | Target Date |
|-------|--------|----------|-------------|
| **Stage 0** | Current | Non-blocking via `continue-on-error: true` | Now |
| **Stage 1** | Pending | Remove `continue-on-error`, observable but non-required | 2025-01-15 or 10 consecutive greens |
| **Stage 2** | Pending | Add to required checks | Flake rate < 1%, 20+ consecutive greens |

**Success Criteria:**
- p95 runtime < 5 minutes
- Flake rate < 1% (< 1 failure per 100 runs)
- No blocking failures for 2 consecutive weeks

## Related Issues

- Issue #2280 - Integrate RolloutTracker to worker.py
- Issue #2641 - enabled=True + Redis integration tests
- Issue #2648 - Document redis_queue/tests purpose and positioning

## See Also

- `tests/test_rollout_tracker.py` - Unit tests (collected by CI)
- `rollout_tracker.py` - RolloutTracker implementation
