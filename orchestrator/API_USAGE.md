# Orchestrator API - Usage Guide

## Overview

The Orchestrator API provides a unified interface for task orchestration, event management, and human-in-the-loop (HITL) approvals across the MorningAI agent ecosystem.

**Production URL**: `https://morningai-orchestrator-api.onrender.com`

## Quick Start

### 1. Authentication

The API supports two authentication methods:

#### JWT Token (Recommended)
```bash
# Create a JWT token (requires ORCHESTRATOR_JWT_SECRET)
curl -X POST https://morningai-orchestrator-api.onrender.com/auth/token \
  -H "Content-Type: application/json" \
  -d '{"user_id": "your-user-id", "role": "agent"}'

# Use the token
curl -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  https://morningai-orchestrator-api.onrender.com/tasks
```

#### API Key
```bash
curl -H "X-API-Key: YOUR_API_KEY" \
  https://morningai-orchestrator-api.onrender.com/tasks
```

### 2. Check API Health

```bash
curl https://morningai-orchestrator-api.onrender.com/health
```

**Response**:
```json
{
  "status": "healthy",
  "redis": "connected",
  "queue_stats": {
    "pending_tasks": 0,
    "processing_tasks": 0,
    "total_tasks": 0
  }
}
```

## Authentication

### Roles

The API uses a role-based access control (RBAC) system:

| Role | Permissions | Use Case |
|------|-------------|----------|
| `admin` | Full access to all endpoints | System administrators |
| `agent` | Create tasks, publish events, approve requests | Dev/Ops/FAQ agents |
| `user` | Read-only access | Monitoring, dashboards |

**Role Hierarchy**: `admin` > `agent` > `user`

### Creating JWT Tokens

JWT tokens are created using the `ORCHESTRATOR_JWT_SECRET` environment variable.

**Python Example**:
```python
import jwt
from datetime import datetime, timedelta, timezone

def create_token(user_id: str, role: str, secret: str) -> str:
    payload = {
        "sub": user_id,
        "role": role,
        "exp": datetime.now(timezone.utc) + timedelta(hours=24),
        "iat": datetime.now(timezone.utc)
    }
    return jwt.encode(payload, secret, algorithm="HS256")

# Usage
token = create_token("dev-agent-1", "agent", "YOUR_SECRET")
```

**Node.js Example**:
```javascript
const jwt = require('jsonwebtoken');

function createToken(userId, role, secret) {
  const payload = {
    sub: userId,
    role: role,
    exp: Math.floor(Date.now() / 1000) + (24 * 60 * 60),
    iat: Math.floor(Date.now() / 1000)
  };
  return jwt.sign(payload, secret, { algorithm: 'HS256' });
}

// Usage
const token = createToken('dev-agent-1', 'agent', 'YOUR_SECRET');
```

### Configuring API Keys

API keys are configured via environment variables:

```bash
ORCHESTRATOR_API_KEY_DEV_AGENT=your-api-key-here:agent
ORCHESTRATOR_API_KEY_OPS_AGENT=another-key-here:agent
ORCHESTRATOR_API_KEY_ADMIN=admin-key-here:admin
```

Format: `ORCHESTRATOR_API_KEY_<NAME>=<key>:<role>`

## API Endpoints

### Task Management

#### Create Task

Create a new task and route it to the appropriate agent.

**Endpoint**: `POST /tasks`  
**Auth**: Requires `agent` role  
**Rate Limit**: 10 requests/minute

**Request**:
```json
{
  "type": "bugfix",
  "payload": {
    "issue": "123",
    "description": "Fix login bug",
    "priority": "high"
  },
  "priority": "P1",
  "source": "github",
  "sla_target": 3600,
  "metadata": {
    "repo": "morningai",
    "branch": "main"
  }
}
```

**Task Types**:
- `bugfix` - Bug fixes (routed to Dev Agent)
- `feature` - New features (routed to Dev Agent)
- `refactor` - Code refactoring (routed to Dev Agent)
- `deployment` - Deployments (routed to Ops Agent)
- `monitoring` - Monitoring setup (routed to Ops Agent)
- `incident` - Incident response (routed to Ops Agent)
- `faq_update` - FAQ updates (routed to FAQ Agent)
- `documentation` - Documentation (routed to FAQ Agent)
- `knowledge_sync` - Knowledge sync (routed to FAQ Agent)

**Priority Levels**:
- `P0` - Critical (requires HITL approval)
- `P1` - High (requires HITL approval)
- `P2` - Medium
- `P3` - Low

**Response**:
```json
{
  "success": true,
  "task_id": "task_abc123",
  "message": "Task created and assigned to dev_agent",
  "task": {
    "task_id": "task_abc123",
    "type": "bugfix",
    "status": "assigned",
    "assigned_agent": "dev_agent",
    "priority": "P1",
    "created_at": "2025-10-22T06:00:00Z"
  }
}
```

**cURL Example**:
```bash
curl -X POST https://morningai-orchestrator-api.onrender.com/tasks \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "type": "bugfix",
    "payload": {"issue": "123"},
    "priority": "P2"
  }'
```

#### Get Task

Retrieve task details by ID.

**Endpoint**: `GET /tasks/{task_id}`  
**Auth**: Requires authentication  
**Rate Limit**: 30 requests/minute

**Response**:
```json
{
  "success": true,
  "task_id": "task_abc123",
  "task": {
    "task_id": "task_abc123",
    "type": "bugfix",
    "status": "in_progress",
    "assigned_agent": "dev_agent",
    "priority": "P1",
    "created_at": "2025-10-22T06:00:00Z",
    "started_at": "2025-10-22T06:05:00Z"
  }
}
```

**cURL Example**:
```bash
curl -H "Authorization: Bearer YOUR_TOKEN" \
  https://morningai-orchestrator-api.onrender.com/tasks/task_abc123
```

#### Update Task Status

Update the status of a task.

**Endpoint**: `PATCH /tasks/{task_id}/status`  
**Auth**: Requires `agent` role  
**Rate Limit**: 10 requests/minute

**Query Parameters**:
- `status` (required): New status (`in_progress`, `completed`, `failed`)
- `error` (optional): Error message (for `failed` status)

**Response**:
```json
{
  "success": true,
  "task_id": "task_abc123",
  "status": "completed"
}
```

**cURL Example**:
```bash
curl -X PATCH "https://morningai-orchestrator-api.onrender.com/tasks/task_abc123/status?status=completed" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Event Management

#### Publish Event

Publish an event to the event bus for other agents to consume.

**Endpoint**: `POST /events/publish`  
**Auth**: Requires `agent` role  
**Rate Limit**: 20 requests/minute

**Request**:
```json
{
  "event_type": "deployment.completed",
  "source_agent": "ops_agent",
  "payload": {
    "service": "api-backend",
    "version": "v1.2.3",
    "environment": "production"
  },
  "task_id": "task_abc123",
  "trace_id": "trace_xyz789",
  "priority": "P2"
}
```

**Response**:
```json
{
  "success": true,
  "event_type": "deployment.completed",
  "message": "Event published successfully"
}
```

**cURL Example**:
```bash
curl -X POST https://morningai-orchestrator-api.onrender.com/events/publish \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "event_type": "deployment.completed",
    "source_agent": "ops_agent",
    "payload": {"service": "api-backend"}
  }'
```

### HITL Approvals

#### Get Pending Approvals

Retrieve all pending approval requests.

**Endpoint**: `GET /approvals/pending`  
**Auth**: Requires authentication  
**Rate Limit**: 5 requests/minute

**Response**:
```json
{
  "success": true,
  "count": 2,
  "approvals": [
    {
      "approval_id": "approval_123",
      "task_id": "task_abc123",
      "priority": "P0",
      "reason": "Critical deployment to production",
      "status": "pending",
      "created_at": "2025-10-22T06:00:00Z"
    }
  ]
}
```

**cURL Example**:
```bash
curl -H "Authorization: Bearer YOUR_TOKEN" \
  https://morningai-orchestrator-api.onrender.com/approvals/pending
```

#### Get Approval Status

Get the status of a specific approval.

**Endpoint**: `GET /approvals/{approval_id}`  
**Auth**: Requires authentication  
**Rate Limit**: 5 requests/minute

**Response**:
```json
{
  "success": true,
  "approval": {
    "approval_id": "approval_123",
    "task_id": "task_abc123",
    "status": "approved",
    "approved_by": "admin-user",
    "approved_at": "2025-10-22T06:10:00Z"
  }
}
```

#### Approve Request

Approve a pending request.

**Endpoint**: `POST /approvals/{approval_id}/approve`  
**Auth**: Requires `agent` role  
**Rate Limit**: 5 requests/minute

**Response**:
```json
{
  "success": true,
  "approval_id": "approval_123",
  "message": "Approved by agent-user"
}
```

**cURL Example**:
```bash
curl -X POST https://morningai-orchestrator-api.onrender.com/approvals/approval_123/approve \
  -H "Authorization: Bearer YOUR_TOKEN"
```

#### Reject Request

Reject a pending request.

**Endpoint**: `POST /approvals/{approval_id}/reject`  
**Auth**: Requires `agent` role  
**Rate Limit**: 5 requests/minute

**Query Parameters**:
- `reason` (optional): Rejection reason

**Response**:
```json
{
  "success": true,
  "approval_id": "approval_123",
  "message": "Rejected by agent-user"
}
```

**cURL Example**:
```bash
curl -X POST "https://morningai-orchestrator-api.onrender.com/approvals/approval_123/reject?reason=Security+concerns" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

#### Get Approval History

Retrieve approval history.

**Endpoint**: `GET /approvals/history`  
**Auth**: Requires authentication  
**Rate Limit**: 5 requests/minute

**Query Parameters**:
- `limit` (optional): Maximum number of records (default: 100)

**Response**:
```json
{
  "success": true,
  "count": 50,
  "history": [
    {
      "approval_id": "approval_123",
      "task_id": "task_abc123",
      "status": "approved",
      "approved_by": "admin-user",
      "approved_at": "2025-10-22T06:10:00Z"
    }
  ]
}
```

### Statistics

#### Get Queue Statistics

Get current queue statistics.

**Endpoint**: `GET /stats`  
**Auth**: Public (no authentication required)  
**Rate Limit**: 30 requests/minute

**Response**:
```json
{
  "queue": {
    "pending_tasks": 5,
    "processing_tasks": 2,
    "total_tasks": 150
  },
  "timestamp": "2025-10-22T06:00:00Z"
}
```

**cURL Example**:
```bash
curl https://morningai-orchestrator-api.onrender.com/stats
```

## Rate Limiting

The API implements rate limiting per endpoint to prevent abuse.

### Rate Limit Headers

All responses include rate limit headers:

```
X-RateLimit-Limit: 10
X-RateLimit-Remaining: 8
X-RateLimit-Reset: 1634567890
```

### Rate Limits by Endpoint

| Endpoint | Limit | Window |
|----------|-------|--------|
| `POST /tasks` | 10 | 1 minute |
| `GET /tasks/{id}` | 30 | 1 minute |
| `PATCH /tasks/{id}/status` | 10 | 1 minute |
| `POST /events/publish` | 20 | 1 minute |
| `GET /approvals/*` | 5 | 1 minute |
| `POST /approvals/*/approve` | 5 | 1 minute |
| `POST /approvals/*/reject` | 5 | 1 minute |
| `GET /stats` | 30 | 1 minute |

### 429 Too Many Requests

When rate limit is exceeded:

```json
{
  "detail": "Rate limit exceeded. Try again in 45 seconds."
}
```

## Error Handling

### HTTP Status Codes

| Code | Meaning | Description |
|------|---------|-------------|
| 200 | OK | Request successful |
| 400 | Bad Request | Invalid request data |
| 401 | Unauthorized | Missing or invalid authentication |
| 403 | Forbidden | Insufficient permissions |
| 404 | Not Found | Resource not found |
| 429 | Too Many Requests | Rate limit exceeded |
| 500 | Internal Server Error | Server error |
| 503 | Service Unavailable | Service temporarily unavailable |

### Error Response Format

```json
{
  "detail": "Error message describing what went wrong"
}
```

## Best Practices

### 1. Use JWT Tokens for Production

JWT tokens are more secure and flexible than API keys:

```python
# Generate token once, reuse for 24 hours
token = create_jwt_token("my-agent", "agent", secret)

# Use token in all requests
headers = {"Authorization": f"Bearer {token}"}
```

### 2. Handle Rate Limits Gracefully

```python
import time
import requests

def make_request_with_retry(url, headers, max_retries=3):
    for attempt in range(max_retries):
        response = requests.get(url, headers=headers)
        
        if response.status_code == 429:
            retry_after = int(response.headers.get('X-RateLimit-Reset', 60))
            time.sleep(retry_after)
            continue
        
        return response
    
    raise Exception("Max retries exceeded")
```

### 3. Monitor Queue Depth

```python
def check_queue_health():
    response = requests.get("https://morningai-orchestrator-api.onrender.com/stats")
    stats = response.json()
    
    pending = stats["queue"]["pending_tasks"]
    if pending > 100:
        print(f"WARNING: High queue depth: {pending} tasks")
```

### 4. Use Trace IDs for Debugging

```python
import uuid

trace_id = str(uuid.uuid4())

# Create task with trace ID
response = requests.post(
    "https://morningai-orchestrator-api.onrender.com/tasks",
    headers=headers,
    json={
        "type": "bugfix",
        "payload": {"issue": "123"},
        "metadata": {"trace_id": trace_id}
    }
)

# Use same trace ID for related events
requests.post(
    "https://morningai-orchestrator-api.onrender.com/events/publish",
    headers=headers,
    json={
        "event_type": "task.started",
        "source_agent": "dev_agent",
        "trace_id": trace_id
    }
)
```

### 5. Implement Proper Error Handling

```python
try:
    response = requests.post(url, headers=headers, json=data, timeout=10)
    response.raise_for_status()
    return response.json()
except requests.exceptions.Timeout:
    print("Request timed out")
except requests.exceptions.HTTPError as e:
    if e.response.status_code == 401:
        print("Authentication failed - check your token")
    elif e.response.status_code == 429:
        print("Rate limit exceeded - slow down")
    else:
        print(f"HTTP error: {e}")
except Exception as e:
    print(f"Unexpected error: {e}")
```

## Integration Examples

### Python Agent Integration

```python
import requests
import jwt
from datetime import datetime, timedelta, timezone

class OrchestratorClient:
    def __init__(self, base_url, secret, agent_id, role="agent"):
        self.base_url = base_url
        self.secret = secret
        self.agent_id = agent_id
        self.role = role
        self.token = self._create_token()
    
    def _create_token(self):
        payload = {
            "sub": self.agent_id,
            "role": self.role,
            "exp": datetime.now(timezone.utc) + timedelta(hours=24),
            "iat": datetime.now(timezone.utc)
        }
        return jwt.encode(payload, self.secret, algorithm="HS256")
    
    def _headers(self):
        return {"Authorization": f"Bearer {self.token}"}
    
    def create_task(self, task_type, payload, priority="P2"):
        response = requests.post(
            f"{self.base_url}/tasks",
            headers=self._headers(),
            json={
                "type": task_type,
                "payload": payload,
                "priority": priority
            },
            timeout=10
        )
        response.raise_for_status()
        return response.json()
    
    def get_task(self, task_id):
        response = requests.get(
            f"{self.base_url}/tasks/{task_id}",
            headers=self._headers(),
            timeout=10
        )
        response.raise_for_status()
        return response.json()
    
    def update_task_status(self, task_id, status, error=None):
        params = {"status": status}
        if error:
            params["error"] = error
        
        response = requests.patch(
            f"{self.base_url}/tasks/{task_id}/status",
            headers=self._headers(),
            params=params,
            timeout=10
        )
        response.raise_for_status()
        return response.json()
    
    def publish_event(self, event_type, payload, task_id=None):
        response = requests.post(
            f"{self.base_url}/events/publish",
            headers=self._headers(),
            json={
                "event_type": event_type,
                "source_agent": self.agent_id,
                "payload": payload,
                "task_id": task_id
            },
            timeout=10
        )
        response.raise_for_status()
        return response.json()

# Usage
client = OrchestratorClient(
    base_url="https://morningai-orchestrator-api.onrender.com",
    secret="YOUR_SECRET",
    agent_id="dev-agent-1"
)

# Create task
task = client.create_task("bugfix", {"issue": "123"}, "P2")
print(f"Created task: {task['task_id']}")

# Update status
client.update_task_status(task['task_id'], "in_progress")

# Publish event
client.publish_event("task.started", {"task_id": task['task_id']})
```

### Node.js Agent Integration

```javascript
const axios = require('axios');
const jwt = require('jsonwebtoken');

class OrchestratorClient {
  constructor(baseUrl, secret, agentId, role = 'agent') {
    this.baseUrl = baseUrl;
    this.secret = secret;
    this.agentId = agentId;
    this.role = role;
    this.token = this.createToken();
  }

  createToken() {
    const payload = {
      sub: this.agentId,
      role: this.role,
      exp: Math.floor(Date.now() / 1000) + (24 * 60 * 60),
      iat: Math.floor(Date.now() / 1000)
    };
    return jwt.sign(payload, this.secret, { algorithm: 'HS256' });
  }

  headers() {
    return { Authorization: `Bearer ${this.token}` };
  }

  async createTask(taskType, payload, priority = 'P2') {
    const response = await axios.post(
      `${this.baseUrl}/tasks`,
      { type: taskType, payload, priority },
      { headers: this.headers(), timeout: 10000 }
    );
    return response.data;
  }

  async getTask(taskId) {
    const response = await axios.get(
      `${this.baseUrl}/tasks/${taskId}`,
      { headers: this.headers(), timeout: 10000 }
    );
    return response.data;
  }

  async updateTaskStatus(taskId, status, error = null) {
    const params = { status };
    if (error) params.error = error;
    
    const response = await axios.patch(
      `${this.baseUrl}/tasks/${taskId}/status`,
      null,
      { headers: this.headers(), params, timeout: 10000 }
    );
    return response.data;
  }

  async publishEvent(eventType, payload, taskId = null) {
    const response = await axios.post(
      `${this.baseUrl}/events/publish`,
      {
        event_type: eventType,
        source_agent: this.agentId,
        payload,
        task_id: taskId
      },
      { headers: this.headers(), timeout: 10000 }
    );
    return response.data;
  }
}

// Usage
const client = new OrchestratorClient(
  'https://morningai-orchestrator-api.onrender.com',
  'YOUR_SECRET',
  'dev-agent-1'
);

(async () => {
  // Create task
  const task = await client.createTask('bugfix', { issue: '123' }, 'P2');
  console.log(`Created task: ${task.task_id}`);

  // Update status
  await client.updateTaskStatus(task.task_id, 'in_progress');

  // Publish event
  await client.publishEvent('task.started', { task_id: task.task_id });
})();
```

## API Documentation

- **Swagger UI**: https://morningai-orchestrator-api.onrender.com/docs
- **ReDoc**: https://morningai-orchestrator-api.onrender.com/redoc
- **OpenAPI JSON**: https://morningai-orchestrator-api.onrender.com/openapi.json

## Support

- **GitHub Issues**: https://github.com/RC918/morningai/issues
- **Label**: `orchestrator`
- **Deployment Guide**: [DEPLOYMENT.md](./DEPLOYMENT.md)
