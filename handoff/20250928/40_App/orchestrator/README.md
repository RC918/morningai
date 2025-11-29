# MorningAI Worker Orchestrator

**Component**: Worker Orchestrator  
**Role**: Task Execution (RQ + LangGraph)  
**Maturity**: Production  
**Deployment**: Render (morningai-agent-worker)  
**Queue**: orchestrator

## Architecture

This is the **worker layer** of the orchestrator system (consumer in producer-consumer pattern). It polls Redis for tasks and executes them using the LangGraph-based orchestration engine.

**Related Components**:
- **API Orchestrator**: `orchestrator/` (root) - FastAPI service for task submission
- **Deployment**: [render.yaml#L55-L94](https://github.com/RC918/morningai/blob/b59625751e80476b6f99ec9f61ace76b8e64f2c1/render.yaml#L55-L94)
- **Architecture Decision**: [ADR-005: Dual Orchestrator Architecture](../../../../docs/adr/005-dual-orchestrator-architecture.md), [ADR-002: Producer-Consumer Architecture](../../../../docs/adr/002-producer-consumer-architecture.md)

---

## Features

This worker engine demonstrates:
- GitHub API (open PR, read CI status)
- Redis Queue (RQ) for task slicing
- Supabase pgvector (long-term memory)
- **Phase 4 LangGraph 9-Node Workflow**:
  ```
  planner → security_advisor → governance_advisor → executor → ci_monitor → reviewer → decision → fixer → finalizer
  ```

### Phase 4 Multi-Agent Flow (Current)

| Node | Description | Phase |
|------|-------------|-------|
| `planner` | Task decomposition using LLM Planner | Phase 1 |
| `security_advisor` | SecurityAgent security analysis (advisory-only) | Phase 4 PR-2 |
| `governance_advisor` | GovernanceAgent compliance analysis (advisory-only) | Phase 4 PR-3 |
| `executor` | Code generation execution via shared core `graph.execute()` | Phase 1 |
| `ci_monitor` | CI status monitoring | Phase 1 |
| `reviewer` | Code review and analysis (ReviewerAgent) | Phase 3 |
| `decision` | Merge decision logic (approve/request_changes/needs_fix) | Phase 3 |
| `fixer` | Auto-fix CI failures (AutoFixer + ReviewerAgent) | Phase 2 |
| `finalizer` | Prepare final result | Phase 1 |

**Key PRs**:
- Phase 2: #1660-1669 (Fixer Node, Safety Rules)
- Phase 3: #1681-1686 (Multi-Agent Flow, Metrics, Staging Rollout)
- Phase 4: #1688-1690 (Semantic Rules v2, SecurityAgent, GovernanceAgent)

## 0) Install (recommended in a venv)
```bash
pip install -r requirements.txt
```

## 1) Environment
Create a `.env` file with the following variables (all optional - demo mode works without these):
- `GITHUB_TOKEN` (repo: RC918/morningai or your fork) - minimal permissions: `repo`, `workflow`
- `GITHUB_REPO`  (e.g. RC918/morningai)
- `REDIS_URL`    (e.g. redis://localhost:6379/0 or Upstash URL) - for queue & idempotency
- `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY`
- `OPENAI_API_KEY` (for embeddings only)
- `MEMORY_TABLE` (default: memory)

**Redis Key Naming Convention:**
- Task status tracking: `agent:task:{task_id}` (1-hour TTL)
  - Stores JSON: `{status, question, trace_id, pr_url, created_at, updated_at, error}`
  - Status values: `queued`, `running`, `done`, `error`
- Idempotency keys: `orchestrator:job:{md5_hash}` (1-hour TTL)
  - Used internally by RQ worker for deduplication

**API Integration:**
The orchestrator can be triggered via API backend at `/api/agent/faq`:
- POST request creates a task and returns `task_id`
- GET `/api/agent/tasks/:id` polls for status
- Orchestrator executes in background and updates task status in Redis
- See `handoff/20250928/40_App/api-backend/src/routes/agent.py` for implementation

**Features:**
- **Idempotency**: Tasks with same goal are deduplicated using Redis (1-hour TTL)
- **Trace ID**: Each task gets a UUID for tracking in PR descriptions and Sentry logs
- **Demo Mode**: Orchestrator runs without credentials by simulating GitHub/Redis/Supabase operations

## 2) Create memory table (SQL for pgvector)
```sql
create table if not exists memory(
  id bigserial primary key,
  key text,
  text text,
  embedding vector(1536)
);
-- and a simple RPC or cosine search can be added depending on your setup.
```

## 3) Start Redis worker
```bash
rq worker orchestrator -u "$REDIS_URL"
```

## 4) Enqueue a long task
```bash
python graph.py --goal "修復前端 build 錯誤" --repo "$GITHUB_REPO"
```

You should see: planner → enqueue steps → worker executes → on failure, fixer attempts patch → opens PR → reads CI → success.
