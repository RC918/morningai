# Database Migrations for Orchestrator

This directory contains SQL migration scripts for the orchestrator's Supabase/PostgreSQL database.

## Migrations

### 001_create_agent_tasks_table.sql
**Purpose**: Create `agent_tasks` table for Phase 11 persistence layer (Issue #184)

**Required for**: Phase 11 — Phase 1 (Task logging with Redis + DB dual-path)

**How to apply**:

1. **Via Supabase Dashboard** (Recommended):
   ```
   1. Go to https://supabase.com/dashboard
   2. Select your project (qevmlbsunnwgrsdibdoi)
   3. Navigate to "SQL Editor" in left sidebar
   4. Click "New query"
   5. Copy-paste contents of 001_create_agent_tasks_table.sql
   6. Click "Run" to execute
   7. Verify table creation: SELECT * FROM agent_tasks LIMIT 1;
   ```

2. **Via psql CLI**:
   ```bash
   export SUPABASE_DB_URL="postgresql://postgres:[password]@db.qevmlbsunnwgrsdibdoi.supabase.co:5432/postgres"
   psql $SUPABASE_DB_URL -f 001_create_agent_tasks_table.sql
   ```

3. **Via Supabase REST API** (for automation):
   ```bash
   curl -X POST "https://qevmlbsunnwgrsdibdoi.supabase.co/rest/v1/rpc/exec_sql" \
     -H "apikey: ${SUPABASE_SERVICE_ROLE_KEY}" \
     -H "Authorization: Bearer ${SUPABASE_SERVICE_ROLE_KEY}" \
     -H "Content-Type: application/json" \
     -d "{\"query\": \"$(cat 001_create_agent_tasks_table.sql)\"}"
   ```

**Verification**:
```sql
-- Check table exists
SELECT table_name, table_type 
FROM information_schema.tables 
WHERE table_name = 'agent_tasks';

-- Check indexes
SELECT indexname, indexdef 
FROM pg_indexes 
WHERE tablename = 'agent_tasks';

-- Check constraints
SELECT constraint_name, constraint_type 
FROM information_schema.table_constraints 
WHERE table_name = 'agent_tasks';
```

**Rollback** (if needed):
```sql
DROP TABLE IF EXISTS agent_tasks CASCADE;
```

## RLS (Row Level Security)

**Current status**: RLS is **disabled** for `agent_tasks` table. All writes use SERVICE_ROLE_KEY which bypasses RLS.

**Future**: Add RLS policies to restrict access based on user roles (admin, analyst, etc.). See RFC section 4.4 for design.

## Troubleshooting

### "Table already exists" error
- Normal if migration already ran
- Verify with: `SELECT COUNT(*) FROM agent_tasks;`
- If table structure wrong, drop and recreate

### "Permission denied" error
- Ensure using SERVICE_ROLE_KEY (not anon key)
- Check Supabase project permissions

### Missing environment variables
- Backend service needs: SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY
- Worker service needs: SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY
- Verify in Render dashboard → Environment tab

## Post-Migration Steps

1. **Verify table creation**:
   ```sql
   SELECT * FROM agent_tasks LIMIT 1;
   ```

2. **Redeploy services** (to pick up new table):
   - Backend: Render dashboard → morningai-backend-v2 → Manual Deploy
   - Worker: Render dashboard → morningai-worker → Manual Deploy

3. **Test end-to-end**:
   ```bash
   # Create task
   TID=$(curl -s -H "Content-Type: application/json" \
     -d '{"question":"test after migration"}' \
     "https://morningai-backend-v2.onrender.com/api/agent/faq" | jq -r '.task_id')
   
   # Wait for completion
   sleep 60
   
   # Check DB (should return data, not empty array)
   curl -s "${SUPABASE_URL}/rest/v1/agent_tasks?select=*&task_id=eq.${TID}" \
     -H "apikey: ${SUPABASE_SERVICE_ROLE_KEY}" \
     -H "Authorization: Bearer ${SUPABASE_SERVICE_ROLE_KEY}" | jq
   ```

4. **Monitor logs** for "DB write success" messages:
   ```
   # Worker logs should show:
   {"level":"INFO","message":"DB write success: task {task_id} status=running"}
   {"level":"INFO","message":"DB write success: task {task_id} status=done pr_url={url}"}
   ```
