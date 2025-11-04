# Worker Deployment Troubleshooting Guide

**Last Updated**: 2025-10-23  
**Applies To**: ops-agent-worker (Render deployment)

## Overview

This guide provides comprehensive troubleshooting steps for ops-agent-worker deployment and governance integration issues. It's based on real production issues encountered and resolved in PR #632.

## Table of Contents

1. [Quick Diagnostic Checklist](#quick-diagnostic-checklist)
2. [Common Issues](#common-issues)
3. [Degraded Mode Troubleshooting](#degraded-mode-troubleshooting)
4. [Environment Variable Verification](#environment-variable-verification)
5. [Dependency Issues](#dependency-issues)
6. [Database Connection Testing](#database-connection-testing)
7. [Module Import Testing](#module-import-testing)
8. [Log Analysis](#log-analysis)
9. [Known Issues](#known-issues)

---

## Quick Diagnostic Checklist

Use this checklist to quickly identify the issue category:

- [ ] Worker starts successfully
- [ ] "Governance modules initialized" appears in logs
- [ ] "Registered with Governance" appears in logs (not degraded mode)
- [ ] No import errors in logs
- [ ] No database constraint violations in logs
- [ ] Environment variables are set correctly
- [ ] Dependencies are installed (PyYAML, supabase)

**If all checked**: Worker is healthy ✅  
**If some unchecked**: See specific sections below

---

## Common Issues

### Issue 1: Worker Degraded Mode

**Symptom**:
```
⚠️ Could not register with Governance (degraded mode)
```

**Impact**: Worker operates without governance features (no cost tracking, permissions, reputation)

**Root Causes**:
1. Module import path mismatch
2. Agent type constraint violation
3. Missing dependencies
4. Environment variables not set

**See**: [Degraded Mode Troubleshooting](#degraded-mode-troubleshooting)

---

### Issue 2: Module Import Errors

**Symptom**:
```
ModuleNotFoundError: No module named 'orchestrator.persistence'
```

**Root Cause**: Python sys.path configuration causes import path mismatch

**Solution**: Verify fallback import logic exists in `reputation_engine.py`:

```python
try:
    from orchestrator.persistence.db_client import get_client
    return get_client()
except (ImportError, ModuleNotFoundError):
    try:
        from persistence.db_client import get_client
        return get_client()
    except Exception as e:
        print(f"[ReputationEngine] Supabase unavailable: {e}")
        return None
```

**Related**: PR #632

---

### Issue 3: Database Constraint Violation

**Symptom**:
```
agent_reputation_agent_type_check constraint violation
```

**Root Cause**: Using incorrect agent_type (e.g., `'ops'` instead of `'ops_agent'`)

**Solution**: Verify `worker.py` line 103:

```python
# ✅ Correct
self.agent_id = self.reputation_engine.get_or_create_agent('ops_agent')

# ❌ Wrong
self.agent_id = self.reputation_engine.get_or_create_agent('ops')
```

**Valid Agent Types**:
- `'ops_agent'`
- `'dev_agent'`
- `'pm_agent'`
- `'growth_strategist'`
- `'meta_agent'`

**Related**: PR #632

---

### Issue 4: Missing Dependencies

**Symptom**:
```
ModuleNotFoundError: No module named 'yaml'
ModuleNotFoundError: No module named 'supabase'
```

**Solution**: Verify `agents/ops_agent/requirements.txt` includes:

```
PyYAML>=6.0
supabase==2.6.0
redis==5.0.1
```

**Check Render Build Logs**:
```
Successfully installed ... PyYAML-6.0.3 ... supabase-2.6.0 ...
```

**Related**: PR #624 (PyYAML), PR #628 (Supabase)

---

### Issue 5: Environment Variables Not Set

**Symptom**:
```
[ReputationEngine] Supabase unavailable: Connection timeout
```

**Solution**: Verify environment variables in Render dashboard:

**Required Variables**:
- `SUPABASE_URL`: Full URL (e.g., `https://xxx.supabase.co`)
- `SUPABASE_SERVICE_ROLE_KEY`: Complete key (starts with `eyJ...`)
- `REDIS_URL`: Redis connection string
- `VERCEL_TOKEN`: Vercel API token
- `VERCEL_TEAM_ID`: Vercel team ID

**See**: [Environment Variable Verification](#environment-variable-verification)

---

## Degraded Mode Troubleshooting

### Step 1: Check Logs

Look for these patterns in Render logs:

**Success Pattern**:
```
✅ Governance modules initialized
✅ Registered with Governance (agent_id: 7df3273c-1c9c-49cf-9fb3-41d8494768d8)
   Permission Level: sandbox_only, Reputation Score: 100
🚀 Ops Agent Worker started successfully
```

**Failure Pattern**:
```
✅ Governance modules initialized
⚠️ Could not register with Governance (degraded mode)
```

### Step 2: Identify Root Cause

Check logs for specific error messages:

1. **Import Error**:
   ```
   ModuleNotFoundError: No module named 'orchestrator.persistence'
   ```
   → See [Module Import Testing](#module-import-testing)

2. **Database Error**:
   ```
   agent_reputation_agent_type_check constraint violation
   ```
   → Check agent_type in worker.py

3. **Connection Error**:
   ```
   [ReputationEngine] Supabase unavailable: Connection timeout
   ```
   → See [Database Connection Testing](#database-connection-testing)

4. **Missing Dependency**:
   ```
   ModuleNotFoundError: No module named 'yaml'
   ```
   → See [Dependency Issues](#dependency-issues)

### Step 3: Apply Fix

Based on root cause:

| Root Cause | Fix | PR Reference |
|-----------|-----|--------------|
| Import path | Add fallback import logic | #632 |
| Agent type | Change to `'ops_agent'` | #632 |
| PyYAML missing | Add to requirements.txt | #624 |
| Supabase SDK missing | Add to requirements.txt | #628 |
| Env vars not set | Configure in Render | N/A |

### Step 4: Verify Fix

After deploying fix:

1. Check Render logs for success pattern
2. Verify no degraded mode warning
3. Confirm governance features working:
   - Cost tracking
   - Permission checking
   - Reputation events

---

## Environment Variable Verification

### Method 1: Render Dashboard

1. Go to Render dashboard
2. Select `ops-agent-worker` service
3. Click "Environment" tab
4. Verify all required variables exist

**Common Issue**: Truncated values in UI

**Solution**: Click "Edit" to see full value

### Method 2: Test Connection

Create a test script to verify Supabase connection:

```python
# test_supabase_connection.py
from supabase import create_client
import os

try:
    client = create_client(
        os.getenv('SUPABASE_URL'),
        os.getenv('SUPABASE_SERVICE_ROLE_KEY')
    )
    
    # Test query
    response = client.table('agent_reputation').select('*').execute()
    print(f"✅ Connection successful! Found {len(response.data)} agents")
    
    for agent in response.data:
        print(f"  - {agent['agent_type']}: score={agent['reputation_score']}, level={agent['permission_level']}")
        
except Exception as e:
    print(f"❌ Connection failed: {e}")
```

**Expected Output**:
```
✅ Connection successful! Found 5 agents
  - ops_agent: score=100, level=sandbox_only
  - dev_agent: score=100, level=sandbox_only
  - pm_agent: score=100, level=sandbox_only
  - growth_strategist: score=100, level=sandbox_only
  - meta_agent: score=130, level=prod_low_risk
```

---

## Dependency Issues

### Check Installed Dependencies

**In Render Build Logs**:

Look for:
```
Successfully installed ... PyYAML-6.0.3 ... supabase-2.6.0 ... redis-5.0.1 ...
```

### Verify requirements.txt

```bash
cd /home/ubuntu/repos/morningai
cat agents/ops_agent/requirements.txt
```

**Should include**:
```
aiohttp==3.9.1
psutil==5.9.6
pytest==8.4.2
pytest-asyncio==1.2.0
redis==5.0.1
requests==2.31.0
pydantic>=2.10.0
PyYAML>=6.0
supabase==2.6.0
```

### Test Import Locally

```python
# test_imports.py
try:
    import yaml
    print("✅ PyYAML imported successfully")
except ImportError as e:
    print(f"❌ PyYAML import failed: {e}")

try:
    from supabase import create_client
    print("✅ Supabase SDK imported successfully")
except ImportError as e:
    print(f"❌ Supabase SDK import failed: {e}")

try:
    import redis
    print("✅ Redis imported successfully")
except ImportError as e:
    print(f"❌ Redis import failed: {e}")
```

---

## Database Connection Testing

### Test 1: Basic Connection

```python
from supabase import create_client
import os

client = create_client(
    os.getenv('SUPABASE_URL'),
    os.getenv('SUPABASE_SERVICE_ROLE_KEY')
)

# Should not raise exception
print("✅ Client created successfully")
```

### Test 2: Table Access

```python
# Test agent_reputation table
response = client.table('agent_reputation').select('*').execute()
print(f"✅ agent_reputation table accessible: {len(response.data)} rows")

# Test reputation_events table
response = client.table('reputation_events').select('*').limit(10).execute()
print(f"✅ reputation_events table accessible: {len(response.data)} rows")
```

### Test 3: Agent Creation

```python
from governance import get_reputation_engine

engine = get_reputation_engine()

# Test agent creation
agent_id = engine.get_or_create_agent('ops_agent')

if agent_id:
    print(f"✅ Agent created/retrieved: {agent_id}")
    score = engine.get_reputation_score(agent_id)
    level = engine.get_permission_level(agent_id)
    print(f"   Score: {score}, Level: {level}")
else:
    print("❌ Agent creation failed")
```

---

## Module Import Testing

### Test Worker Import Context

```python
# test_worker_imports.py
import os
import sys

# Simulate worker sys.path setup
project_root = os.path.abspath('.')
sys.path.insert(0, project_root)

governance_path = os.path.join(project_root, 'handoff/20250928/40_App/orchestrator')
sys.path.insert(0, governance_path)

print(f"sys.path includes:")
for path in sys.path[:5]:
    print(f"  - {path}")

# Test imports
try:
    from governance import get_reputation_engine
    print("✅ governance module imported")
except ImportError as e:
    print(f"❌ governance import failed: {e}")

try:
    from persistence.db_client import get_client
    print("✅ persistence.db_client imported (relative path)")
except ImportError as e:
    print(f"❌ persistence.db_client import failed: {e}")

try:
    from orchestrator.persistence.db_client import get_client
    print("✅ orchestrator.persistence.db_client imported (absolute path)")
except ImportError as e:
    print(f"❌ orchestrator.persistence.db_client import failed: {e}")
```

### Expected Behavior

**With Fix (PR #632)**:
- Relative import (`from persistence.db_client`) should work ✅
- Absolute import may fail but fallback handles it ✅

**Without Fix**:
- Both imports may fail ❌
- Worker enters degraded mode ❌

---

## Log Analysis

### Success Indicators

Look for these patterns in order:

1. **Initialization**:
   ```
   INFO:__main__:============================================================
   INFO:__main__:Ops Agent Worker - Orchestrator Integration
   INFO:__main__:============================================================
   ```

2. **Worker Setup**:
   ```
   INFO:__main__:Initialized Ops Agent Worker (Redis: redis://...)
   INFO:__main__:✅ Governance modules initialized
   ```

3. **Redis Connection**:
   ```
   INFO:orchestrator.task_queue.redis_queue:Connected to Redis at redis://...
   INFO:__main__:✅ Connected to Orchestrator Redis queue
   ```

4. **OODA Loop**:
   ```
   INFO:__main__:✅ Initialized Ops Agent OODA Loop
   ```

5. **Supabase Connection**:
   ```
   INFO:persistence.db_client:Supabase client initialized for agent_tasks persistence
   ```

6. **Governance Registration**:
   ```
   INFO:httpx:HTTP Request: GET https://...supabase.co/rest/v1/agent_reputation?select=%2A&agent_type=eq.ops_agent "HTTP/2 200 OK"
   INFO:__main__:✅ Registered with Governance (agent_id: ...)
   INFO:__main__:   Permission Level: sandbox_only, Reputation Score: 100
   ```

7. **Event Subscription**:
   ```
   INFO:orchestrator.task_queue.redis_queue:Subscribed to events: ['task.created', 'deploy.started', 'alert.triggered']
   INFO:__main__:✅ Subscribed to Orchestrator events
   ```

8. **Worker Started**:
   ```
   INFO:__main__:🚀 Ops Agent Worker started successfully
   INFO:__main__:Starting task processing loop...
   INFO:__main__:Starting event listener...
   ```

### Failure Indicators

**Degraded Mode**:
```
INFO:__main__:✅ Governance modules initialized
INFO:__main__:⚠️ Could not register with Governance (degraded mode)
```

**Import Error**:
```
ModuleNotFoundError: No module named 'orchestrator.persistence'
```

**Database Error**:
```
agent_reputation_agent_type_check constraint violation
```

**Connection Error**:
```
[ReputationEngine] Supabase unavailable: Connection timeout
```

---

## Known Issues

### Issue: Policies.yaml Path Error (Non-blocking)

**Symptom**:
```
[ReputationEngine] Error loading policies: [Errno 2] No such file or directory: '.../config/policies.yaml'
```

**Impact**: Low - policies are loaded but path resolution differs between local and production

**Status**: Expected in local testing, should work in production

**Workaround**: Ignore in local testing, verify in production logs

---

### Issue: Agent Type vs Task Routing Identifier

**Observation**:
- Task routing uses: `assigned_to = "ops"` (line 153 in worker.py)
- Governance uses: `agent_type = "ops_agent"`

**Question**: Is this intentional design?
- Task routing: short identifier
- Governance: full type name

**Status**: Needs clarification or documentation

**Workaround**: Keep both identifiers as-is for now

---

### Issue: Environment Variable Truncation in Render UI

**Symptom**: Long environment variables appear truncated in Render dashboard

**Impact**: May cause confusion during verification

**Workaround**: Click "Edit" to see full value

**Status**: UI limitation, not a functional issue

---

## Escalation Path

If issue persists after following this guide:

1. **Check Related PRs**:
   - PR #618: Agent Governance Framework Integration
   - PR #624: PyYAML dependency fix
   - PR #628: Supabase SDK dependency fix
   - PR #632: Import path and agent_type fix

2. **Review Documentation**:
   - [Governance Framework](GOVERNANCE_FRAMEWORK.md)
   - [Ops Agent README](../agents/ops_agent/README.md)

3. **Create Issue**:
   - Label: `governance`, `ops-agent`, `deployment`
   - Include: Render logs, environment variable screenshot, error messages
   - Reference: This troubleshooting guide

4. **Contact**:
   - Open GitHub issue with detailed reproduction steps
   - Include link to Devin session if applicable

---

## Appendix: Diagnostic Commands

### Check Worker Status

```bash
# In Render dashboard
# 1. Go to ops-agent-worker service
# 2. Click "Logs" tab
# 3. Look for success/failure indicators
```

### Test Governance Locally

```bash
cd /home/ubuntu/repos/morningai

# Test governance import
python3 << 'EOF'
import os
import sys

project_root = os.path.abspath('.')
sys.path.insert(0, project_root)

governance_path = os.path.join(project_root, 'handoff/20250928/40_App/orchestrator')
sys.path.insert(0, governance_path)

from governance import get_reputation_engine

engine = get_reputation_engine()
agent_id = engine.get_or_create_agent('ops_agent')

if agent_id:
    print(f"✅ Success: {agent_id}")
else:
    print("❌ Failed")
EOF
```

### Verify Database Schema

```sql
-- Connect to Supabase
-- Check agent_reputation table
SELECT agent_type, COUNT(*) 
FROM agent_reputation 
GROUP BY agent_type;

-- Check reputation_events
SELECT event_type, COUNT(*) 
FROM reputation_events 
GROUP BY event_type 
ORDER BY COUNT(*) DESC 
LIMIT 10;
```

---

**Document Version**: 1.0  
**Last Updated**: 2025-10-23  
**Maintained By**: Engineering Team  
**Related**: PR #632, GOVERNANCE_FRAMEWORK.md
