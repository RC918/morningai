# Background Queue Principles

This document establishes the principles and code review checklist for ensuring long-running tasks execute in background queues without blocking the main system.

## Architecture Overview

MorningAI uses a Producer-Consumer pattern with Redis Queue (RQ) for background task processing:

```
Flask API (Producer) → Redis Queue → RQ Workers (Consumer)
```

### Key Components

| Component | Location | Purpose |
|-----------|----------|---------|
| Worker | `orchestrator/redis_queue/worker.py` | Processes background jobs |
| Queue Config | `common/config/settings.py` | Centralized timeout/queue settings |
| API Routes | `api-backend/src/routes/agent.py` | Task submission endpoints |

## Timeout Configuration Standards

All timeout values are centralized in `common/config/settings.py`:

| Setting | Default | Description |
|---------|---------|-------------|
| `RQ_JOB_TIMEOUT` | 600s (10 min) | Maximum job execution time |
| `RQ_MAX_JOBS` | 0 (unlimited) | Jobs before worker restart (memory management) |
| `RQ_RESULT_TTL` | 86400s (24h) | Result retention period |
| `RQ_FAILURE_TTL` | 3600s (1h) | Failure record retention |
| `RQ_TASK_TTL` | 600s (10 min) | Task enqueue TTL |
| `WORKER_HEARTBEAT_INTERVAL` | 60s | Heartbeat update frequency |
| `WORKER_HEARTBEAT_TTL` | 180s | Heartbeat key expiration |
| `PROJECT_ENGINEER_TASK_TIMEOUT_SECONDS` | 300s (5 min) | Agent-level task timeout |

### Timeout Hierarchy

```
RQ_JOB_TIMEOUT (600s)
    └── PROJECT_ENGINEER_TASK_TIMEOUT_SECONDS (300s)
        └── Individual operation timeouts (varies)
```

The job timeout must always be greater than any agent-level timeout to allow for graceful cleanup.

## Code Review Checklist

### For New Endpoints

- [ ] **Background Queue**: Does the endpoint enqueue work to RQ instead of executing synchronously?
- [ ] **Timeout Configuration**: Are timeouts using centralized settings (not hardcoded)?
- [ ] **TTL Values**: Are `ttl`, `result_ttl`, and `failure_ttl` specified in enqueue calls?
- [ ] **Idempotency**: Does the endpoint support idempotency keys to prevent duplicate jobs?
- [ ] **Status Tracking**: Is task status stored in Redis with appropriate TTL?
- [ ] **Error Handling**: Are Redis connection errors handled gracefully (503 response)?

### For Worker Functions

- [ ] **Decorator**: Is the function decorated with `@job` from RQ?
- [ ] **Timeout**: Is `timeout=JOB_TIMEOUT` (from settings) specified in decorator?
- [ ] **Retry Logic**: Is `retry=Retry(max=3, interval=[10, 30, 60])` configured?
- [ ] **Status Updates**: Does the function update Redis status (queued → running → done/error)?
- [ ] **DB Persistence**: Are task states persisted to database for durability?
- [ ] **Sentry Integration**: Are errors captured with appropriate breadcrumbs?
- [ ] **Metrics**: Are execution metrics recorded for monitoring?

### For Long-Running Operations

- [ ] **Agent Timeout**: Is `PROJECT_ENGINEER_TASK_TIMEOUT_SECONDS` respected?
- [ ] **Graceful Shutdown**: Does the operation handle SIGTERM for graceful shutdown?
- [ ] **Progress Updates**: Are heartbeats/progress updates sent for long operations?
- [ ] **Memory Management**: Is `RQ_MAX_JOBS` configured to prevent OOM?

## Standard Enqueue Pattern

```python
from common.config.settings import settings

# Standard TTL values from settings
job = queue.enqueue(
    worker_function,
    task_id,
    *args,
    job_id=task_id,
    ttl=settings.rq_task_ttl,           # 600s default
    result_ttl=settings.rq_result_ttl,   # 86400s default
    failure_ttl=settings.rq_failure_ttl  # 3600s default
)
```

## Standard Worker Pattern

```python
from rq.decorators import job
from rq import Retry
from common.config.settings import settings

JOB_TIMEOUT = settings.rq_job_timeout

@job(
    settings.rq_queue_name,
    connection=redis_client_rq,
    retry=Retry(max=3, interval=[10, 30, 60]),
    timeout=JOB_TIMEOUT
)
def my_worker_task(task_id: str, *args):
    """Worker function with standard patterns."""
    # 1. Update status to running
    redis.hset(f"agent:task:{task_id}", mapping={"status": "running", ...})
    
    try:
        # 2. Execute task with agent-level timeout
        result = execute_with_timeout(
            timeout_seconds=settings.project_engineer_task_timeout_seconds
        )
        
        # 3. Update status to done
        redis.hset(f"agent:task:{task_id}", mapping={"status": "done", ...})
        
        # 4. Persist to DB
        upsert_task_done(task_id=task_id, ...)
        
        return result
        
    except Exception as e:
        # 5. Update status to error
        redis.hset(f"agent:task:{task_id}", mapping={"status": "error", ...})
        
        # 6. Persist error to DB
        upsert_task_error(task_id=task_id, error_msg=str(e))
        
        # 7. Capture in Sentry
        if sentry_sdk:
            sentry_sdk.capture_exception(e)
        
        raise
```

## Audited Endpoints

The following endpoints have been audited for background queue compliance:

### Compliant Endpoints

| Endpoint | Worker Function | Timeout | Status |
|----------|-----------------|---------|--------|
| `POST /api/agent/faq` | `run_orchestrator_task` | 600s | Compliant |
| `POST /api/agent/project-engineer/task` | `run_project_engineer_task` | 600s | Compliant |

### Compliance Details

1. **`/api/agent/faq`**: Enqueues to `run_orchestrator_task` with proper TTLs and status tracking.

2. **`/api/agent/project-engineer/task`**: Enqueues to `run_project_engineer_task` with agent-level timeout (300s) within job timeout (600s).

## Anti-Patterns to Avoid

### 1. Synchronous Long Operations

```python
# BAD: Blocks the request
@app.route("/api/long-task")
def long_task():
    result = expensive_operation()  # Blocks for minutes
    return jsonify(result)

# GOOD: Enqueue to background
@app.route("/api/long-task")
def long_task():
    task_id = str(uuid.uuid4())
    queue.enqueue(expensive_operation, task_id, ...)
    return jsonify({"task_id": task_id, "status": "queued"}), 202
```

### 2. Hardcoded Timeouts

```python
# BAD: Hardcoded timeout
@job("orchestrator", timeout=600)
def my_task(): ...

# GOOD: Use centralized settings
@job(settings.rq_queue_name, timeout=settings.rq_job_timeout)
def my_task(): ...
```

### 3. Missing Error Handling

```python
# BAD: No Redis error handling
def create_task():
    queue.enqueue(...)  # Can throw RedisConnectionError

# GOOD: Handle Redis errors
def create_task():
    try:
        queue.enqueue(...)
    except RedisConnectionError:
        return jsonify({"error": "Service unavailable"}), 503
```

## Monitoring and Alerting

### Worker Health

- Heartbeat monitoring via `worker:heartbeat:{worker_id}` keys
- TTL-based detection of dead workers
- Graceful shutdown state tracking

### Queue Metrics

- Pending task count
- Processing task count
- Job success/failure rates
- Latency percentiles (p50, p95, p99)

## References

- Issue: [#1817](https://github.com/RC918/morningai/issues/1817) - Background Queue Principles
- Worker Implementation: `orchestrator/redis_queue/worker.py`
- Settings: `common/config/settings.py`
- API Routes: `api-backend/src/routes/agent.py`
