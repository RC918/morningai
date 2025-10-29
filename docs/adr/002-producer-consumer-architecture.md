# ADR-002: Producer-Consumer Architecture for Orchestrator

**Status**: Accepted  
**Date**: 2025-10-29  
**Deciders**: CTO, Backend Team  
**Related**: Technical Debt Roadmap Phase 2

## Context

The MorningAI orchestrator system needs to handle task submissions via HTTP API while executing long-running background tasks (GitHub operations, CI analysis, code fixes). Key requirements:

- **Decoupling**: HTTP API responses must be fast (<200ms) while task execution can take minutes
- **Scalability**: Need to scale API and worker processes independently based on load
- **Reliability**: Task execution must survive API service restarts
- **Observability**: Need to track task status, queue depth, and worker health
- **Multi-tenancy**: Support concurrent task execution for multiple users/projects

Initial monolithic approach (single-process API + execution) caused:
- Timeout issues on long-running tasks
- Inability to scale API and workers independently
- Lost tasks on service restarts
- Poor observability into task execution

## Decision

Implement a **producer-consumer architecture** using Redis + RQ (Redis Queue):

### Architecture Components

1. **Producer (API Layer)**
   - Service: `morningai-orchestrator-api` (FastAPI)
   - Location: `orchestrator/` (root directory)
   - Deployment: [render.yaml#L111-L150](https://github.com/RC918/morningai/blob/b59625751e80476b6f99ec9f61ace76b8e64f2c1/render.yaml#L111-L150)
   - Responsibilities:
     - Accept HTTP task submissions
     - Validate and enqueue tasks to Redis
     - Return task IDs immediately
     - Provide task status queries
     - Handle authentication (JWT, API keys)
     - Enforce rate limiting

2. **Consumer (Worker Layer)**
   - Service: `morningai-agent-worker` (RQ Worker)
   - Location: `handoff/20250928/40_App/orchestrator/`
   - Deployment: [render.yaml#L55-L94](https://github.com/RC918/morningai/blob/b59625751e80476b6f99ec9f61ace76b8e64f2c1/render.yaml#L55-L94)
   - Responsibilities:
     - Poll Redis queue for tasks
     - Execute LangGraph orchestration workflows
     - Perform GitHub operations (PR creation, CI checks)
     - Update task status in Redis
     - Handle retries and error recovery

3. **Message Broker**
   - Technology: Redis (Upstash)
   - Queue name: `orchestrator`
   - Task TTL: 24 hours
   - Features: Priority queuing, idempotency, status tracking

### Communication Flow

```
Client → API (FastAPI) → Redis Queue → Worker (RQ) → GitHub/Supabase
         ↓                    ↓              ↓
      Task ID            Enqueued        Executing
         ↓                    ↓              ↓
      Status Query ← Redis Status ← Status Update
```

### Configuration

- **Queue Name**: `orchestrator` (shared via `RQ_QUEUE_NAME` env var)
- **Health Checks**: Both services expose `/health` endpoints
- **CORS**: API configured for frontend origins
- **Authentication**: JWT tokens and API keys for API layer
- **Rate Limiting**: Per-endpoint limits on API layer

## Alternatives Considered

### 1. Monolithic Single-Process
**Pros**: Simpler deployment, no Redis dependency  
**Cons**: Cannot scale independently, timeouts on long tasks, lost tasks on restart  
**Rejected**: Does not meet scalability and reliability requirements

### 2. Celery Instead of RQ
**Pros**: More features (periodic tasks, complex workflows)  
**Cons**: Heavier weight, more complex configuration, overkill for current needs  
**Rejected**: RQ is simpler and sufficient for current requirements

### 3. Direct HTTP Fan-out
**Pros**: No message broker needed  
**Cons**: No retry mechanism, no queue management, tight coupling  
**Rejected**: Does not provide reliability or observability

### 4. AWS SQS/Lambda
**Pros**: Fully managed, auto-scaling  
**Cons**: Vendor lock-in, higher cost, migration effort  
**Deferred**: Consider for future if scaling beyond Render

## Consequences

### Positive

- ✅ **Independent Scaling**: Can scale API and workers separately based on load
- ✅ **Fault Isolation**: API service restarts don't affect running tasks
- ✅ **Fast API Responses**: HTTP requests return immediately with task IDs
- ✅ **Task Persistence**: Tasks survive service restarts (stored in Redis)
- ✅ **Observability**: Can monitor queue depth, worker health, task status
- ✅ **Retry Logic**: Failed tasks can be retried automatically
- ✅ **Priority Queuing**: Critical tasks can be prioritized

### Negative

- ❌ **Added Infrastructure**: Requires Redis instance (Upstash)
- ❌ **Eventual Consistency**: Task status updates are asynchronous
- ❌ **Complexity**: Two services to deploy and monitor instead of one
- ❌ **Network Dependency**: API and worker must both reach Redis

### Operational Considerations

1. **Monitoring**:
   - Track queue depth (alert if >100 tasks)
   - Monitor worker health (heartbeat every 30s)
   - Alert on task failures (>5% failure rate)

2. **Scaling**:
   - Scale API horizontally for more HTTP throughput
   - Scale workers horizontally for more task execution capacity
   - Current setup: 1 API instance, 1 worker instance

3. **Disaster Recovery**:
   - Redis persistence enabled (Upstash)
   - Task TTL: 24 hours (configurable)
   - Worker restart: picks up pending tasks automatically

4. **Security**:
   - API: JWT authentication + API keys
   - Worker: No direct external access
   - Redis: TLS enabled, password protected

## Related Documentation

- [Orchestrator API README](../../orchestrator/README.md)
- [Orchestrator Worker README](../../handoff/20250928/40_App/orchestrator/README.md)
- [Technical Debt Roadmap](../TECHNICAL_DEBT_ROADMAP.md)
- [Render Deployment Configuration](../../render.yaml)

## References

- RQ Documentation: https://python-rq.org/
- FastAPI Documentation: https://fastapi.tiangolo.com/
- Redis Queue Patterns: https://redis.io/docs/manual/patterns/
