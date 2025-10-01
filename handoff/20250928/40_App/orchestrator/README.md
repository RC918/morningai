# MorningAI Orchestrator Real Demo (20250928_2052)

This demo shows:
- GitHub API (open PR, read CI status)
- Redis Queue (RQ) for task slicing
- Supabase pgvector (long-term memory)
- LangGraph-style loop (planner → executor → CI analyzer → fixer)

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
