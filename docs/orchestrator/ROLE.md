# Orchestrator Role Documentation

## Overview

The MorningAI orchestrator system implements a **producer-consumer architecture** with two distinct components that work together to execute autonomous agent tasks.

## Architecture Components

### 1. Orchestrator API Service (Producer)

**Location**: `orchestrator/` (root directory)  
**Type**: FastAPI Web Service  
**Purpose**: Task submission endpoint  
**Deployment**: Render (morningai-orchestrator-api)  
**Port**: 8000  
**Health Check**: `/health`

#### Responsibilities

- **HTTP API Endpoint**: Receives task submissions via POST `/api/agent/faq`
- **Task Validation**: Validates incoming requests and parameters
- **Redis Enqueuing**: Pushes validated tasks to Redis queue for worker processing
- **Task ID Generation**: Creates unique task IDs and trace IDs for tracking
- **Status Endpoint**: Provides GET `/api/agent/tasks/:id` for polling task status
- **Idempotency**: Deduplicates identical tasks using Redis (1-hour TTL)

#### Lifecycle

```
1. Client sends POST /api/agent/faq with goal
2. API validates request and generates task_id
3. API enqueues task to Redis queue "orchestrator"
4. API returns task_id to client immediately (non-blocking)
5. Client polls GET /api/agent/tasks/:id for status updates
```

#### Key Files

- `orchestrator/main.py` - FastAPI application entry point
- `orchestrator/routes/agent.py` - Task submission endpoints
- `orchestrator/redis_client.py` - Redis connection and queue management

#### Deployment Configuration

See `render.yaml` lines 108-146:
```yaml
- type: web
  name: morningai-orchestrator-api
  runtime: python
  buildCommand: "pip install -r orchestrator/requirements.txt"
  startCommand: "uvicorn orchestrator.main:app --host 0.0.0.0 --port 8000"
```

---

### 2. Orchestrator Worker Engine (Consumer)

**Location**: `handoff/20250928/40_App/orchestrator/`  
**Type**: RQ Worker (Redis Queue)  
**Purpose**: Task execution engine  
**Deployment**: Render (morningai-agent-worker)  
**Queue**: `orchestrator`

#### Responsibilities

- **Task Polling**: Continuously polls Redis queue for new tasks
- **Graph Execution**: Executes tasks using LangGraph-based state machine
- **Planning**: Analyzes goals and creates execution plans
- **Execution**: Performs GitHub operations (clone, commit, PR creation)
- **CI Monitoring**: Monitors CI checks and determines success/failure
- **Auto-Fixing**: Attempts to fix CI failures automatically (up to 3 retries)
- **State Management**: Maintains task state in Redis with status updates
- **Memory Integration**: Stores/retrieves context from Supabase pgvector

#### Lifecycle

```
1. Worker polls Redis queue "orchestrator"
2. Worker receives task and updates status to "running"
3. Planner node analyzes goal and creates plan
4. Executor node executes each step sequentially
5. CI Monitor node checks PR CI status
6. Fixer node attempts repairs if CI fails (max 3 retries)
7. Finalizer node prepares final result
8. Worker updates Redis with final status ("done" or "error")
```

#### State Machine (LangGraph)

```
START
  ↓
[Planner] - Analyzes goal, creates plan
  ↓
[Executor] - Executes current step
  ↓
  ├─→ More steps? → Loop back to Executor
  ├─→ Error? → [Fixer] → Executor (max 3 retries)
  └─→ Complete? → [CI Monitor]
                     ↓
                     ├─→ CI Success? → [Finalizer] → END
                     ├─→ CI Failure? → [Fixer] → Executor
                     └─→ CI Pending? → Loop back to CI Monitor
```

#### Key Files

- `langgraph_orchestrator.py` - LangGraph state machine implementation
- `graph.py` - Task execution logic and GitHub operations
- `dev_agent_v2.py` - Agent implementation with tool access
- `tools/github_api.py` - GitHub API integration
- `persistence/supabase_memory.py` - Long-term memory storage

#### Deployment Configuration

See `render.yaml` lines 55-94:
```yaml
- type: worker
  name: morningai-agent-worker
  runtime: python
  buildCommand: "pip install -r handoff/20250928/40_App/orchestrator/requirements.txt"
  startCommand: "rq worker orchestrator -u $REDIS_URL"
```

---

## Communication Flow

### Task Submission Flow

```
Client
  ↓ POST /api/agent/faq
[Orchestrator API]
  ↓ enqueue to Redis
Redis Queue "orchestrator"
  ↓ poll
[Orchestrator Worker]
  ↓ execute task
GitHub (create PR, monitor CI)
  ↓ update status
Redis (task status)
  ↓ poll
Client (GET /api/agent/tasks/:id)
```

### Data Flow

1. **Task Creation**:
   - Client → API: `{goal: "Fix build errors", repo: "RC918/morningai"}`
   - API → Redis: `{task_id, trace_id, goal, repo, status: "queued"}`

2. **Task Execution**:
   - Worker → Redis: Update status to `"running"`
   - Worker → GitHub: Clone repo, create branch, commit changes
   - Worker → GitHub: Create PR, get PR number
   - Worker → Redis: Update with `{pr_url, pr_number}`

3. **CI Monitoring**:
   - Worker → GitHub: Poll PR CI checks
   - Worker → Redis: Update with `{ci_state, ci_checks}`

4. **Completion**:
   - Worker → Redis: Update status to `"done"` or `"error"`
   - Worker → Redis: Store final result `{pr_url, ci_state, error}`

---

## Redis Key Naming Convention

### Task Status Keys
- **Pattern**: `agent:task:{task_id}`
- **TTL**: 1 hour
- **Format**: JSON
  ```json
  {
    "status": "queued|running|done|error",
    "question": "User's goal",
    "trace_id": "UUID for tracking",
    "pr_url": "https://github.com/...",
    "created_at": "ISO timestamp",
    "updated_at": "ISO timestamp",
    "error": "Error message if any"
  }
  ```

### Idempotency Keys
- **Pattern**: `orchestrator:job:{md5_hash}`
- **TTL**: 1 hour
- **Purpose**: Deduplication of identical tasks
- **Used by**: RQ worker internally

---

## Failure Modes

### API Service Failures

| Failure | Impact | Recovery |
|---------|--------|----------|
| Redis connection lost | Tasks cannot be enqueued | API returns 503, client retries |
| Invalid request | Task rejected | API returns 400 with error details |
| Duplicate task | Task deduplicated | API returns existing task_id |

### Worker Failures

| Failure | Impact | Recovery |
|---------|--------|----------|
| GitHub API rate limit | Task execution blocked | Worker retries with exponential backoff |
| CI check failure | PR not merged | Fixer node attempts auto-fix (max 3 retries) |
| Worker crash | Task remains in "running" | RQ automatically re-enqueues after timeout |
| Max retries exceeded | Task marked as "error" | Client notified via status endpoint |

---

## Interfaces

### API Service Interface

**Task Submission**:
```http
POST /api/agent/faq
Content-Type: application/json

{
  "goal": "Fix TypeScript errors in frontend",
  "repo": "RC918/morningai"
}

Response 200:
{
  "task_id": "uuid-here",
  "trace_id": "uuid-here",
  "status": "queued"
}
```

**Task Status**:
```http
GET /api/agent/tasks/{task_id}

Response 200:
{
  "task_id": "uuid-here",
  "status": "done",
  "pr_url": "https://github.com/RC918/morningai/pull/123",
  "ci_state": "success",
  "created_at": "2025-10-30T12:00:00Z",
  "updated_at": "2025-10-30T12:05:00Z"
}
```

### Worker Interface

**Input** (from Redis queue):
```python
{
  "goal": str,
  "repo": str,
  "trace_id": str,
  "task_id": str
}
```

**Output** (to Redis status key):
```python
{
  "status": "done" | "error",
  "pr_url": str,
  "pr_number": int,
  "ci_state": "success" | "failure" | "pending",
  "error": str | None,
  "final_result": dict
}
```

---

## Environment Variables

### API Service
- `REDIS_URL` - Redis connection string (required)
- `PORT` - HTTP port (default: 8000)
- `LOG_LEVEL` - Logging level (default: INFO)

### Worker
- `REDIS_URL` - Redis connection string (required)
- `GITHUB_TOKEN` - GitHub personal access token (required for real operations)
- `GITHUB_REPO` - Default repository (e.g., RC918/morningai)
- `SUPABASE_URL` - Supabase project URL (optional, for memory)
- `SUPABASE_SERVICE_ROLE_KEY` - Supabase service key (optional)
- `OPENAI_API_KEY` - OpenAI API key (optional, for embeddings)
- `MEMORY_TABLE` - Supabase table name (default: memory)

---

## Demo Mode

Both components support **demo mode** for development without credentials:

- **API**: Simulates Redis operations with in-memory storage
- **Worker**: Simulates GitHub/Redis/Supabase operations with mock responses

Enable demo mode by omitting environment variables.

---

## Related Documentation

- **Architecture Decision**: [ADR-002: Producer-Consumer Architecture](../adr/002-producer-consumer-architecture.md)
- **Deployment**: [render.yaml](../../render.yaml)
- **API Implementation**: [orchestrator/routes/agent.py](../../orchestrator/routes/agent.py)
- **Worker Implementation**: [handoff/20250928/40_App/orchestrator/langgraph_orchestrator.py](../../handoff/20250928/40_App/orchestrator/langgraph_orchestrator.py)
- **Phase API Documentation**: [docs/phase-api/README.md](../phase-api/README.md)

---

## Monitoring and Observability

### Logging

Both components use structured logging with trace IDs:

```python
logger.info("Task enqueued", extra={
    "operation": "enqueue_task",
    "trace_id": trace_id,
    "task_id": task_id,
    "goal": goal[:50]
})
```

### Metrics

Key metrics to monitor:
- **API**: Request rate, error rate, response time
- **Worker**: Task execution time, success rate, retry rate
- **Redis**: Queue depth, task TTL expiration rate
- **GitHub**: API rate limit usage, PR creation rate

### Health Checks

- **API**: `GET /health` returns 200 if Redis is reachable
- **Worker**: RQ provides built-in health monitoring

---

## Future Improvements

See Issue #874 for long-term refactoring plans:
- Consolidate orchestrator directories
- Improve error handling and retry logic
- Add comprehensive monitoring and alerting
- Implement task priority queues
- Add support for parallel task execution
