# Ops Agent Worker - Orchestrator Integration Guide

## Overview

The Ops Agent Worker connects the Ops Agent to the Orchestrator's Redis-based task queue, enabling seamless multi-agent collaboration.

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
    │  Worker  │ │ Worker  │ │  Worker   │
    └──────────┘ └─────────┘ └───────────┘
                     ▲
                     │
              ┌──────┴──────┐
              │  OODA Loop  │
              │  • Observe  │
              │  • Orient   │
              │  • Decide   │
              │  • Act      │
              └─────────────┘
```

## Features

### ✅ Implemented

1. **Task Queue Consumer**
   - Polls Redis queue for tasks assigned to 'ops' agent
   - Priority-based task processing (P0 > P1 > P2 > P3)
   - Automatic task re-queuing for wrong agent assignments

2. **OODA Loop Integration**
   - Maps UnifiedTask to Ops Agent task descriptions
   - Executes tasks using full OODA cycle
   - Returns structured results

3. **Task Lifecycle Management**
   - Marks tasks as in_progress, completed, or failed
   - Updates task status in Redis
   - Publishes lifecycle events (task.started, task.completed, task.failed)

4. **Event Bus Integration**
   - Subscribes to relevant events (task.created, deploy.started, alert.triggered)
   - Background event listener for real-time updates

5. **Error Handling**
   - Graceful exception handling
   - Task failure tracking with error messages
   - Automatic retry support (via Orchestrator)

## Installation

### Prerequisites

```bash
# Redis server
docker run -d -p 6379:6379 redis:alpine

# Python dependencies
cd /home/ubuntu/repos/morningai
pip install -r agents/ops_agent/requirements.txt
pip install -r orchestrator/requirements.txt
```

### Environment Variables

```bash
# Redis connection
export REDIS_URL="redis://localhost:6379"

# Vercel API (for deployments)
export VERCEL_TOKEN_NEW="your-vercel-token"
export VERCEL_TEAM_ID="your-team-id"  # Optional

# Orchestrator API (if using authentication)
export ORCHESTRATOR_API_KEY_OPS="ops-key-123:agent"
```

## Usage

### Starting the Worker

```bash
cd /home/ubuntu/repos/morningai/agents/ops_agent
python worker.py
```

Expected output:
```
============================================================
Ops Agent Worker - Orchestrator Integration
============================================================
2025-10-20 10:00:00 - __main__ - INFO - Starting Ops Agent Worker...
2025-10-20 10:00:00 - __main__ - INFO - ✅ Connected to Orchestrator Redis queue
2025-10-20 10:00:00 - __main__ - INFO - ✅ Initialized Ops Agent OODA Loop
2025-10-20 10:00:00 - __main__ - INFO - ✅ Subscribed to Orchestrator events
2025-10-20 10:00:00 - __main__ - INFO - 🚀 Ops Agent Worker started successfully
2025-10-20 10:00:00 - __main__ - INFO - Starting task processing loop...
```

### Submitting Tasks via Orchestrator API

#### 1. Start Orchestrator API

```bash
cd /home/ubuntu/repos/morningai/orchestrator
uvicorn api.main:app --reload --port 8000
```

#### 2. Create a Deployment Task

```bash
curl -X POST http://localhost:8000/tasks \
  -H "Content-Type: application/json" \
  -H "X-API-Key: ops-key-123" \
  -d '{
    "type": "deploy",
    "payload": {
      "project": "morningai",
      "environment": "production"
    },
    "priority": "P1",
    "source": "user"
  }'
```

Response:
```json
{
  "success": true,
  "task_id": "abc123...",
  "message": "Task created and assigned to ops",
  "task": {
    "task_id": "abc123...",
    "type": "deploy",
    "priority": "P1",
    "status": "assigned",
    "assigned_to": "ops",
    ...
  }
}
```

#### 3. Monitor Task Status

```bash
curl http://localhost:8000/tasks/abc123... \
  -H "X-API-Key: ops-key-123"
```

Response:
```json
{
  "success": true,
  "task_id": "abc123...",
  "task": {
    "status": "completed",
    "completed_at": "2025-10-20T10:05:00Z",
    "metadata": {
      "result": {
        "success": true,
        "deployment_id": "dpl_xyz...",
        "url": "https://morningai-xyz.vercel.app"
      }
    }
  }
}
```

## Task Type Mapping

The Worker maps Orchestrator task types to Ops Agent OODA Loop tasks:

| Task Type | Payload | Ops Agent Action |
|-----------|---------|------------------|
| `deploy` | `{project, environment}` | Deploy to Vercel |
| `monitor` | `{service}` | Monitor system metrics |
| `alert` | `{alert_type}` | Manage alerts |
| `investigate` | `{issue}` | Troubleshoot and diagnose |

### Example: Deploy Task

**Input (UnifiedTask)**:
```json
{
  "type": "deploy",
  "payload": {
    "project": "morningai",
    "environment": "production"
  },
  "priority": "P1"
}
```

**Mapped to Ops Agent**:
```python
task_description = "Deploy morningai to production"
priority = "p1"
context = {
    "task_id": "abc123...",
    "payload": {"project": "morningai", "environment": "production"},
    "trace_id": "trace_xyz..."
}
```

**OODA Loop Execution**:
1. **Observe**: Gather system metrics, active alerts, recent errors
2. **Orient**: Classify as 'deployment' task, analyze system health
3. **Decide**: Action = 'deploy', reason = 'Deploy to Vercel platform'
4. **Act**: Execute deployment via DeploymentTool, wait for completion

**Output**:
```json
{
  "success": true,
  "task_id": 1,
  "result": {
    "success": true,
    "deployment_id": "dpl_xyz...",
    "url": "https://morningai-xyz.vercel.app",
    "state": "READY"
  }
}
```

## Testing

### Unit Tests

```bash
cd /home/ubuntu/repos/morningai
python -m pytest agents/ops_agent/tests/test_ops_agent_worker_simple.py -v
```

Expected output:
```
test_worker_initialization PASSED
test_map_task_to_description PASSED
test_execute_task_success PASSED
test_execute_task_failure PASSED
test_worker_stop PASSED

5 passed in 0.20s
```

### Integration Test (Manual)

1. Start Redis:
   ```bash
   docker run -d -p 6379:6379 redis:alpine
   ```

2. Start Orchestrator API:
   ```bash
   cd /home/ubuntu/repos/morningai/orchestrator
   uvicorn api.main:app --port 8000
   ```

3. Start Ops Agent Worker:
   ```bash
   cd /home/ubuntu/repos/morningai/agents/ops_agent
   python worker.py
   ```

4. Submit a test task:
   ```bash
   curl -X POST http://localhost:8000/tasks \
     -H "Content-Type: application/json" \
     -H "X-API-Key: ops-key-123" \
     -d '{
       "type": "monitor",
       "payload": {"service": "system"},
       "priority": "P2",
       "source": "test"
     }'
   ```

5. Check Worker logs for task processing

## Event Flow

### Task Creation Flow

```
1. User/Agent → POST /tasks → Orchestrator API
2. Orchestrator → Router → Assigns to 'ops' agent
3. Orchestrator → Redis Queue → Enqueues task (priority-sorted)
4. Orchestrator → Event Bus → Publishes 'task.created' event
5. Ops Agent Worker → Polls Redis Queue → Dequeues task
6. Ops Agent Worker → Validates assignment → Executes OODA Loop
7. Ops Agent Worker → Updates task status → Publishes 'task.completed' event
```

### Event Subscriptions

The Worker subscribes to:
- `task.created`: New tasks from Orchestrator
- `deploy.started`: Deployment events from other agents
- `alert.triggered`: Alert events requiring ops attention

## Configuration

### Worker Configuration

```python
worker = OpsAgentWorker(
    redis_url="redis://localhost:6379",  # Redis connection
    vercel_token="your-token",           # Vercel API token
    team_id="your-team-id",              # Optional: Vercel team ID
    poll_interval=2                      # Polling interval in seconds
)
```

### Orchestrator Configuration

See `orchestrator/README.md` for:
- Authentication setup (JWT, API Keys)
- CORS configuration
- Rate limiting
- HITL Gate configuration

## Monitoring

### Worker Health

The Worker logs all activity:
- Task processing: `📥 Processing task {task_id}`
- Task execution: `⚙️ Executing task {task_id}...`
- Task completion: `✅ Task {task_id} completed successfully`
- Task failure: `❌ Task {task_id} failed: {error}`

### Orchestrator Health

```bash
curl http://localhost:8000/health
```

Response:
```json
{
  "status": "healthy",
  "redis": "connected",
  "queue_stats": {
    "pending_tasks": 0,
    "processing_tasks": 1,
    "total_tasks": 1
  }
}
```

### Queue Statistics

```bash
curl http://localhost:8000/stats
```

Response:
```json
{
  "queue": {
    "pending_tasks": 5,
    "processing_tasks": 2,
    "total_tasks": 7
  },
  "timestamp": "2025-10-20T10:00:00Z"
}
```

## Troubleshooting

### Worker Not Processing Tasks

**Symptom**: Worker starts but doesn't process tasks

**Possible Causes**:
1. Redis connection issue
   ```bash
   # Check Redis is running
   redis-cli ping
   # Should return: PONG
   ```

2. Tasks assigned to wrong agent
   ```bash
   # Check task assignment
   curl http://localhost:8000/tasks/{task_id}
   # Verify: "assigned_to": "ops"
   ```

3. Authentication issue
   ```bash
   # Check API key is valid
   curl -H "X-API-Key: ops-key-123" http://localhost:8000/health
   ```

### Task Execution Failures

**Symptom**: Tasks marked as failed

**Debugging**:
1. Check Worker logs for error details
2. Verify Vercel token is valid (for deploy tasks)
3. Check Ops Agent tool configuration

### Redis Connection Errors

**Symptom**: `Failed to connect to Redis`

**Solution**:
```bash
# Start Redis
docker run -d -p 6379:6379 redis:alpine

# Verify connection
redis-cli ping

# Check REDIS_URL environment variable
echo $REDIS_URL
```

## Production Deployment

### Docker Deployment

Create `Dockerfile`:
```dockerfile
FROM python:3.12-slim

WORKDIR /app

COPY agents/ops_agent/requirements.txt .
COPY orchestrator/requirements.txt orchestrator-requirements.txt
RUN pip install -r requirements.txt -r orchestrator-requirements.txt

COPY agents/ops_agent/ agents/ops_agent/
COPY orchestrator/ orchestrator/

CMD ["python", "agents/ops_agent/worker.py"]
```

Build and run:
```bash
docker build -t ops-agent-worker .
docker run -d \
  -e REDIS_URL=redis://redis:6379 \
  -e VERCEL_TOKEN_NEW=your-token \
  --name ops-agent-worker \
  ops-agent-worker
```

### Render.com Deployment

Add to `render.yaml`:
```yaml
services:
  - type: worker
    name: morningai-ops-agent-worker
    env: python
    buildCommand: pip install -r agents/ops_agent/requirements.txt -r orchestrator/requirements.txt
    startCommand: python agents/ops_agent/worker.py
    envVars:
      - key: REDIS_URL
        fromService:
          name: morningai-redis
          type: redis
          property: connectionString
      - key: VERCEL_TOKEN_NEW
        sync: false
      - key: PYTHON_VERSION
        value: 3.12.0
```

## Next Steps

1. **Implement Dev Agent Worker** (similar pattern)
2. **Implement FAQ Agent Worker** (similar pattern)
3. **Build E2E Scenarios**:
   - Bug fix closure loop (Dev → Ops collaboration)
   - Deployment pipeline (Ops → Dev feedback)
   - Knowledge base updates (FAQ → Dev/Ops)
4. **Add HITL Gate Integration** for critical operations
5. **Implement retry logic** for failed tasks
6. **Add metrics and monitoring** (Prometheus, Grafana)

## References

- Orchestrator API: `orchestrator/README.md`
- Ops Agent OODA Loop: `agents/ops_agent/README.md`
- Task Schema: `orchestrator/schemas/task_schema.py`
- Event Schema: `orchestrator/schemas/event_schema.py`

---

**Last Updated**: 2025-10-20  
**Version**: 1.0.0  
**Status**: ✅ Production Ready
