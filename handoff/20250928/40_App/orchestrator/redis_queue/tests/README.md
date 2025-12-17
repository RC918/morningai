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

## Related Issues

- Issue #2280 - Integrate RolloutTracker to worker.py
- Issue #2641 - enabled=True + Redis integration tests
- Issue #2648 - Document redis_queue/tests purpose and positioning

## See Also

- `tests/test_rollout_tracker.py` - Unit tests (collected by CI)
- `rollout_tracker.py` - RolloutTracker implementation
