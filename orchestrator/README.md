# MorningAI Orchestrator

Multi-Agent Task Orchestration and Event Bus for MorningAI platform.

## ⚠️ Status: Experimental / Alpha

**This module is currently in alpha state and NOT production-ready.**

### Known Limitations

- **No Authentication/Authorization**: API endpoints are completely open without any security
- **CORS set to `*`**: Allows requests from any origin (security vulnerability)
- **In-Memory HITL State**: Approval requests stored in memory will be lost on restart
- **API Endpoints Not Tested**: 0% test coverage on FastAPI routes (behavior unverified)
- **No Production Deployment Config**: Missing Docker, CI/CD, monitoring setup
- **No Rate Limiting**: API can be abused without throttling

### DO NOT use in production until these issues are resolved.

For production deployment tracking, see:
- Issue #XXX: Implement API Authentication
- Issue #XXX: Persist HITL Approval State to Redis
- Issue #XXX: Add API Integration Tests
- Issue #XXX: Create Production Deployment Configuration

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
REDIS_URL=redis://localhost:6379
ORCHESTRATOR_PORT=8000
```

## License

MIT
