# MorningAI Orchestrator

Multi-Agent Task Orchestration and Event Bus for MorningAI platform.

## ⚠️ Status: Beta

**This module is in beta state. Security features implemented, testing in progress.**

### ✅ Implemented Security Features

- **✅ Authentication/Authorization**: JWT and API Key authentication with role-based access control (RBAC)
- **✅ CORS Configuration**: Restricted to specific origins (configurable via `CORS_ORIGINS` env var)
- **✅ Redis-Persisted HITL State**: Approval requests and history stored in Redis with 30-day retention
- **✅ Rate Limiting**: Redis-based distributed rate limiting with per-endpoint limits

### Remaining Work

- **API Endpoints Testing**: Integration tests needed for FastAPI routes (Issue #560)
- **Production Deployment Config**: Docker, CI/CD, monitoring setup needed (Issue #561)

For production deployment tracking, see:
- ~~Issue #558: Implement API Authentication~~ ✅ COMPLETED
- ~~Issue #559: Persist HITL Approval State to Redis~~ ✅ COMPLETED
- Issue #560: Add API Integration Tests
- Issue #561: Create Production Deployment Configuration

---

## Features

- **Unified Task Schema**: Standard format for inter-agent communication
- **Event Bus**: Redis-based pub/sub for agent events
- **Task Queue**: Priority-based task queueing with Redis
- **REST API**: HTTP endpoints for task submission and monitoring
- **Task Router**: Intelligent routing to Dev/Ops/FAQ agents
- **HITL Gate**: Human-in-the-loop approval for critical operations
- **SLA Tracking**: Monitor and enforce SLA compliance

## Architecture

```
┌─────────────────────────────────────────────────┐
│              Orchestrator API                    │
│  POST /tasks  │  GET /tasks/{id}  │  /events   │
└───────────────┬─────────────────────────────────┘
                │
         ┌──────▼──────┐
         │   Router    │ ──► Routes tasks to agents
         └──────┬──────┘
                │
         ┌──────▼──────────────────────────┐
         │      Redis Queue & Event Bus     │
         │  • Task Queue (Priority)         │
         │  • Event Pub/Sub (agents)        │
         └──┬────────┬────────┬─────────────┘
            │        │        │
    ┌───────▼──┐ ┌──▼─────┐ ┌▼──────────┐
    │ Dev Agent│ │Ops Agent│ │FAQ Agent  │
    └──────────┘ └─────────┘ └───────────┘
```

## Quick Start

### Installation

```bash
pip install -r requirements.txt
```

### Start Redis

```bash
docker run -d -p 6379:6379 redis:alpine
```

### Run API Server

```bash
cd /home/ubuntu/repos/morningai/orchestrator
uvicorn api.main:app --reload --port 8000
```

### Create a Task

```bash
curl -X POST http://localhost:8000/tasks \
  -H "Content-Type: application/json" \
  -d '{
    "type": "bugfix",
    "payload": {"issue_id": "123", "description": "Fix login bug"},
    "priority": "P1",
    "source": "ops"
  }'
```

## API Endpoints

### Tasks

- `POST /tasks` - Create a new task
- `GET /tasks/{task_id}` - Get task status
- `PATCH /tasks/{task_id}/status` - Update task status

### Events

- `POST /events/publish` - Publish an event to event bus

### Monitoring

- `GET /health` - Health check
- `GET /stats` - Queue statistics

## Task Types

- `faq` - FAQ/Knowledge base queries
- `bugfix` - Bug fixes
- `deploy` - Deployments
- `investigate` - Code investigation
- `monitor` - System monitoring
- `alert` - Alert management
- `refactor` - Code refactoring
- `feature` - New features
- `kb_update` - Knowledge base updates

## Priority Levels

- `P0` - Critical (requires HITL approval)
- `P1` - High (requires HITL approval)
- `P2` - Medium
- `P3` - Low

## Event Types

- `task.created`, `task.completed`, `task.failed`
- `deploy.started`, `deploy.succeeded`, `deploy.failed`
- `alert.triggered`, `alert.ack`, `alert.resolved`
- `pr.opened`, `pr.merged`
- `kb.updated`, `kb.gap_detected`
- `sla.violation`, `sla.warning`

## Testing

```bash
pytest tests/ -v --cov=. --cov-report=term-missing
```

## Integration Examples

### Recommended Import Pattern

**✅ Use top-level imports (recommended)**:
```python
from orchestrator import RedisQueue, create_redis_queue, UnifiedTask, create_task
```

**⚠️ Direct module imports (not recommended)**:
```python
# This will work but is not recommended
from orchestrator.task_queue.redis_queue import RedisQueue
```

### Migration Guide (v1.0.0 → v1.1.0)

**Breaking Change**: The `queue` module has been renamed to `task_queue` to avoid conflicts with Python's built-in `queue` module.

**If you were using**:
```python
from orchestrator.queue.redis_queue import RedisQueue  # ❌ Old (will fail)
```

**Update to**:
```python
from orchestrator import RedisQueue  # ✅ Recommended
# OR
from orchestrator.task_queue.redis_queue import RedisQueue  # ✅ Also works
```

**Impact**: Since Orchestrator has not been deployed to production yet, there are no external dependencies affected by this change.

### Dev Agent Integration

```python
from orchestrator import create_task, RedisQueue

queue = await create_redis_queue()

# Create bugfix task
task = create_task(
    task_type="bugfix",
    payload={"repo": "morningai", "issue": "#123"},
    priority="P1"
)

await queue.enqueue_task(task)
```

### Subscribe to Events

```python
async def handle_deploy_event(event):
    print(f"Deployment {event.payload['deployment_id']} started")

await queue.register_event_handler("deploy.started", handle_deploy_event)
await queue.subscribe_to_events(["deploy.started", "deploy.succeeded"])
await queue.start_event_listener()
```

## Configuration

Set environment variables:

```bash
# Redis connection
REDIS_URL=redis://localhost:6379
ORCHESTRATOR_PORT=8000

# CORS configuration (comma-separated origins)
CORS_ORIGINS=http://localhost:3000,http://localhost:5173,https://yourdomain.com

# JWT Authentication
ORCHESTRATOR_JWT_SECRET=your-secret-key-here

# API Keys (format: KEY_NAME=key_value:role)
ORCHESTRATOR_API_KEY_DEV=dev-key-123:agent
ORCHESTRATOR_API_KEY_ADMIN=admin-key-456:admin
```

## Authentication

The Orchestrator API supports two authentication methods:

### 1. JWT (Bearer Token)

```bash
# Get a JWT token (implement your own token generation)
TOKEN=$(python -c "from orchestrator.api.auth import create_jwt_token, Role; print(create_jwt_token('user123', Role.AGENT))")

# Use the token
curl -H "Authorization: Bearer $TOKEN" http://localhost:8000/tasks
```

### 2. API Key

```bash
# Use API key in header
curl -H "X-API-Key: dev-key-123" http://localhost:8000/tasks
```

### Roles

- **admin**: Full access to all endpoints
- **agent**: Can create tasks, publish events, manage approvals
- **user**: Read-only access to tasks and approvals

## HITL Approval Endpoints

### Get Pending Approvals

```bash
curl -H "Authorization: Bearer $TOKEN" http://localhost:8000/approvals/pending
```

### Get Approval Status

```bash
curl -H "Authorization: Bearer $TOKEN" http://localhost:8000/approvals/{approval_id}
```

### Approve Request

```bash
curl -X POST -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/approvals/{approval_id}/approve
```

### Reject Request

```bash
curl -X POST -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/approvals/{approval_id}/reject?reason=Not+ready
```

### Get Approval History

```bash
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/approvals/history?limit=50
```

## Rate Limiting

Rate limits are enforced per IP address and endpoint:

- Default: 60 requests/minute
- `/tasks`: 30 requests/minute
- `/events/publish`: 100 requests/minute
- `/health`: 300 requests/minute

Rate limit headers are included in responses:
- `X-RateLimit-Limit`: Maximum requests allowed
- `X-RateLimit-Remaining`: Requests remaining in current window
- `X-RateLimit-Reset`: Unix timestamp when limit resets

## License

MIT
