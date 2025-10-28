# ADR-002: Orchestrator Roles and Boundaries

**Status**: Proposed  
**Date**: 2025-10-28  
**Decision Maker**: CTO  
**Stakeholders**: Engineering Team, DevOps, Product

---

## Context

The MorningAI repository contains two separate orchestrator codebases with different purposes and deployment strategies:

### 1. Root Orchestrator (`orchestrator/`)

**Purpose**: FastAPI microservice for orchestration API  
**Deployment**: Docker container on Render (render.yaml:107-146)  
**Technology Stack**:
- FastAPI 0.104.0
- uvicorn (ASGI server)
- Redis 5.0.0
- PyJWT 2.8.0
- pytest, httpx

**Structure**:
```
orchestrator/
├── api/                    # REST API endpoints
├── task_queue/             # Task queue management
├── schemas/                # Pydantic models
├── integrations/           # External integrations
├── Dockerfile              # Docker containerization
└── requirements.txt        # FastAPI dependencies
```

**Deployment Configuration** (render.yaml:107-146):
```yaml
- type: web
  name: morningai-orchestrator-api
  runtime: docker
  dockerfilePath: ./orchestrator/Dockerfile
  envVars:
    - key: ORCHESTRATOR_API_KEY
    - key: RATE_LIMIT_PER_MINUTE
```

### 2. Handoff Orchestrator (`handoff/20250928/40_App/orchestrator/`)

**Purpose**: Redis Queue (RQ) Worker for task execution  
**Deployment**: Python process on Render (render.yaml:51-90)  
**Technology Stack**:
- python-dotenv 1.0.1
- PyGithub 2.4.0
- Redis 5.2.0, rq 1.16.2
- Supabase 2.6.0
- OpenAI 1.52.2
- Sentry SDK 2.19.2

**Structure**:
```
handoff/20250928/40_App/orchestrator/
├── graph.py                    # Task graph execution (7079 bytes)
├── langgraph_orchestrator.py   # LangGraph integration (12143 bytes)
├── dev_agent_v2.py             # Dev Agent v2 (16669 bytes)
├── mcp/                        # Management Control Plane
│   ├── client.py
│   └── tools/                  # Shell, Browser, Render, Sentry tools
├── redis_queue/                # RQ worker implementation
│   └── worker.py
├── sandbox/                    # Sandbox execution
│   ├── manager.py
│   └── docker_sandbox.py
├── persistence/                # Data persistence
│   ├── db_client.py
│   └── db_writer.py
├── memory/                     # Memory management
│   └── pgvector_store.py
├── llm/                        # LLM integration
│   └── faq_generator.py
├── tools/                      # GitHub API tools
├── governance/                 # Governance module
└── utils/                      # Utility functions
```

**Deployment Configuration** (render.yaml:51-90):
```yaml
- type: worker
  name: morningai-agent-worker
  runtime: python
  buildCommand: pip install -r requirements.txt
  startCommand: cd handoff/20250928/40_App/orchestrator && python redis_queue/worker.py
  envVars:
    - key: RQ_QUEUE_NAME
      value: orchestrator
```

**Problem**:
- Two orchestrator codebases with unclear relationship
- Potential confusion about which to use for new features
- Maintenance overhead: bug fixes may need to be applied twice
- Unclear ownership and evolution path
- New developers don't know which orchestrator to modify

---

## Decision

**We maintain both orchestrator codebases with clearly defined roles and boundaries:**

1. **Root `orchestrator/` = Orchestrator API Service**
   - **Role**: Public-facing REST API for orchestration requests
   - **Responsibilities**:
     - Accept orchestration requests via HTTP
     - Validate API keys and rate limits
     - Enqueue tasks to Redis Queue
     - Return task IDs and status
     - Provide task status polling endpoints
   - **Does NOT**: Execute tasks directly

2. **Handoff `orchestrator/` = Orchestrator Worker**
   - **Role**: Task execution engine
   - **Responsibilities**:
     - Consume tasks from Redis Queue
     - Execute agent workflows (Dev, Ops, FAQ agents)
     - Interact with GitHub, Supabase, OpenAI
     - Manage sandboxes and MCP tools
     - Write results to persistence layer
   - **Does NOT**: Accept external HTTP requests

**Architecture Pattern**: Producer-Consumer with API Gateway

```
┌─────────────────┐
│   Client/UI     │
└────────┬────────┘
         │ HTTP POST /orchestrate
         ▼
┌─────────────────────────┐
│  Orchestrator API       │  (Root orchestrator/)
│  - FastAPI              │
│  - Auth/Rate Limiting   │
│  - Task Validation      │
└────────┬────────────────┘
         │ Enqueue
         ▼
┌─────────────────────────┐
│   Redis Queue           │
│   Queue: "orchestrator" │
└────────┬────────────────┘
         │ Dequeue
         ▼
┌─────────────────────────┐
│  Orchestrator Worker    │  (Handoff orchestrator/)
│  - RQ Worker            │
│  - Agent Execution      │
│  - LangGraph/MCP        │
│  - GitHub/Supabase      │
└─────────────────────────┘
```

---

## Rationale

### Why Maintain Separation:

1. **Separation of Concerns**:
   - API service handles authentication, rate limiting, validation
   - Worker handles complex agent execution logic
   - Clear boundary between request handling and task execution

2. **Scalability**:
   - API service can scale independently (more instances for high request volume)
   - Worker can scale independently (more workers for high task volume)
   - Different resource requirements (API: low CPU, Worker: high CPU)

3. **Deployment Flexibility**:
   - API service: Docker container with health checks
   - Worker: Python process with long-running tasks
   - Different restart/recovery strategies

4. **Security**:
   - API service: Public-facing, needs strong auth
   - Worker: Internal, uses service role keys
   - Reduces attack surface by not exposing worker directly

5. **Technology Fit**:
   - FastAPI: Excellent for REST APIs with OpenAPI docs
   - RQ Worker: Excellent for background task processing
   - Each uses the right tool for its job

### Why NOT Unify:

**Option B Considered: Merge into single codebase**
- Rejected because:
  - Would mix HTTP request handling with task execution
  - Harder to scale independently
  - Deployment complexity (single service doing two jobs)
  - Loss of clear architectural boundaries
  - Would require significant refactoring with high risk

---

## Consequences

### Positive:

1. **Clarity**: Clear roles prevent confusion
2. **Scalability**: Independent scaling of API and workers
3. **Maintainability**: Each codebase has focused responsibility
4. **Security**: API gateway pattern with proper isolation
5. **Flexibility**: Can evolve each component independently

### Negative:

1. **Code Duplication**: Some utilities may be duplicated
   - Mitigation: Create shared library for common code
   
2. **Coordination**: Changes affecting both require coordination
   - Mitigation: Clear interface contract (Redis Queue message format)
   
3. **Testing**: Need integration tests across both components
   - Mitigation: E2E tests in `orchestrator-e2e.yml`

### Action Items:

1. **Documentation** (Week 1):
   - Create `orchestrator/README.md`:
     ```markdown
     # Orchestrator API Service
     
     **Role**: Public-facing REST API for orchestration requests
     
     ## Responsibilities
     - Accept orchestration requests via HTTP
     - Validate API keys and enforce rate limits
     - Enqueue tasks to Redis Queue
     - Provide task status polling
     
     ## Does NOT
     - Execute tasks directly (see handoff/.../orchestrator/)
     
     ## Deployment
     - Platform: Render (Docker)
     - Service: morningai-orchestrator-api
     - Health Check: /health
     ```
   
   - Create `handoff/20250928/40_App/orchestrator/README.md`:
     ```markdown
     # Orchestrator Worker
     
     **Role**: Task execution engine for agent workflows
     
     ## Responsibilities
     - Consume tasks from Redis Queue (queue: "orchestrator")
     - Execute agent workflows (Dev, Ops, FAQ)
     - Interact with GitHub, Supabase, OpenAI
     - Manage sandboxes and MCP tools
     
     ## Does NOT
     - Accept external HTTP requests (see root orchestrator/)
     
     ## Deployment
     - Platform: Render (Python worker)
     - Service: morningai-agent-worker
     - Queue: RQ_QUEUE_NAME=orchestrator
     ```

2. **Interface Contract** (Week 1):
   - Document Redis Queue message format:
     ```python
     # Message Schema
     {
       "task_type": "faq_update" | "pr_creation" | "ops_task",
       "goal": str,
       "repo_full": str,
       "trace_id": Optional[str],
       "metadata": dict
     }
     ```

3. **Shared Library** (Month 2):
   - Create `packages/orchestrator-common/`:
     - Redis client utilities
     - Message serialization
     - Common types/schemas
   - Update both orchestrators to use shared library

4. **Architecture Diagram** (Week 1):
   - Add to Architecture README
   - Include in team onboarding docs

5. **Monitoring** (Month 1):
   - API service metrics: request rate, latency, error rate
   - Worker metrics: queue depth, task duration, success rate
   - Alert on queue backlog > 100 tasks

---

## Compliance

This decision aligns with:
- **CTO Responsibility 1**: Technical Strategy & Architecture (clear service boundaries)
- **CTO Responsibility 2**: Engineering Management (maintainable architecture)
- **Risk Mitigation**: Addresses ARCH-002 in Risk Register (HIGH priority)
- **Best Practices**: Microservices pattern, separation of concerns

---

## References

- `orchestrator/requirements.txt` - FastAPI dependencies
- `handoff/20250928/40_App/orchestrator/requirements.txt` - RQ Worker dependencies
- `render.yaml:51-90` - Worker deployment configuration
- `render.yaml:107-146` - API service deployment configuration
- `.github/workflows/orchestrator-e2e.yml` - E2E testing
- CTO Technical Assessment Report (2025-10-28) - Section on Orchestrator Duplication

---

## Future Considerations

### Potential Evolution (6-12 months):

1. **Unified Monorepo Package**:
   - Move both to `packages/orchestrator/`
   - Separate entrypoints: `api.py` and `worker.py`
   - Shared code in `packages/orchestrator/common/`

2. **gRPC Communication**:
   - Replace Redis Queue with gRPC for lower latency
   - Maintain async pattern with streaming

3. **Kubernetes Deployment**:
   - Deploy both as separate K8s services
   - Use K8s native service discovery

---

## Approval

- [ ] CTO Review
- [ ] Engineering Lead Review
- [ ] DevOps Review
- [ ] CEO Approval
- [ ] Documented in team wiki

**Target Approval Date**: 2025-10-30  
**Implementation Start**: Upon approval  
**Review Date**: 2025-11-30 (reassess if issues arise)
