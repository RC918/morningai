# Checkpoint Degradation Response Runbook

**Document ID**: SOP-CHECKPOINT-001  
**Version**: 1.0  
**Effective Date**: 2025-12-26  
**Last Review Date**: 2025-12-26  
**Next Review Date**: 2026-03-26  
**Document Owner**: Engineering Team  
**Approver**: CTO

---

## Overview

This Standard Operating Procedure (SOP) provides step-by-step instructions for detecting, triaging, and resolving checkpoint degradation incidents in the MorningAI LangGraph orchestrator.

**What is Checkpoint Degradation?**

When the PostgreSQL checkpointer fails at runtime (SSL disconnect, connection errors, circuit breaker open), the `DegradedPersistenceCheckpointer` automatically switches to MemorySaver fallback. This is called "degraded persistence mode" or "soft landing."

**Blueprint Alignment:**
- Flow Controller v3: Fail-Fast Recovery (Section 3.2)
- Safety Governor v2: Self-Governed / Self-Healing (Section 4.4)
- Telemetry v2: Observable degradation events (Section 5.2)

**Key Behavior - Sticky Degradation:**
Once a workflow enters degraded mode, ALL subsequent checkpoint operations use MemorySaver. This prevents "write to DB, read from RAM" inconsistency that would cause agent logic errors.

**Trade-off:**
Degraded workflows complete successfully but cannot resume from checkpoint after worker restart.

**Related Documents:**
- [PR #3018](https://github.com/RC918/morningai/pull/3018) - DegradedPersistenceCheckpointer implementation
- [POST_DEPLOY_SMOKE_TEST_CHECKLIST.md](./POST_DEPLOY_SMOKE_TEST_CHECKLIST.md) - Post-incident verification

---

## Prerequisites

Before executing this runbook, ensure you have:

| Requirement | Description | How to Verify |
|-------------|-------------|---------------|
| Render Dashboard Access | Login credentials for https://dashboard.render.com | Can access service list |
| Sentry Access | Access to MorningAI Sentry project | Can view error events |
| Supabase Access | Access to Supabase dashboard | Can check PostgreSQL health |
| Log Access | Access to Render logs or log aggregator | Can search for `checkpoint_degraded` |
| Slack Access | Member of #engineering and #incidents channels | Can post messages |

---

## Detection Signals

### Primary Signals

| Signal | Log Level | Search Query | Meaning |
|--------|-----------|--------------|---------|
| `checkpoint_degraded` event | WARNING | `event="checkpoint_degraded"` | A workflow just entered degraded mode |
| `persistence_degraded=True` | INFO | `persistence_degraded=True` | A workflow completed in degraded mode |
| `circuit_breaker="opened"` | ERROR | `circuit_breaker="opened"` | ResilientPostgresSaver circuit breaker tripped |
| `checkpointer_mode="degraded"` | WARNING | `checkpointer_mode="degraded"` | Workflow is using MemorySaver fallback |

### Log Examples

**Degradation Event (WARNING):**
```
CHECKPOINT DEGRADED: Primary checkpointer failed, switching to fallback. 
trace_id=abc123 operation=put error='SSL connection has been closed' 
degraded_since=2025-12-26T10:30:00
```

**Completion Log (INFO):**
```
LangGraph orchestrator completed trace_id=abc123 status=success 
pr_url='https://github.com/...' persistence_degraded=True
```

**Circuit Breaker Open (ERROR):**
```
ResilientPostgresSaver: Circuit breaker OPENED after 3 consecutive failures
```

### Metrics to Monitor

| Metric | Formula | Alert Threshold |
|--------|---------|-----------------|
| Degradation Ratio | `count(persistence_degraded=True) / total_workflows` | > 5% |
| Consecutive Degradations | Count of sequential `checkpoint_degraded` events | > 3 |
| Circuit Breaker Opens | Count of `circuit_breaker="opened"` events | > 1 per hour |

---

## Triage Matrix

| Scenario | Degradation Ratio | PostgreSQL Status | Priority | Action |
|----------|-------------------|-------------------|----------|--------|
| Isolated incident | < 1% | Healthy | P3 | Monitor, no action |
| Intermittent issues | 1-5% | Intermittent errors | P2 | Investigate PostgreSQL |
| Widespread degradation | 5-20% | Unhealthy | P1 | Immediate PostgreSQL fix |
| Complete outage | > 20% | Down | P0 | Emergency response |

---

## Response Procedures

### Step 1: Confirm Degradation is Occurring [MUST-PASS]

**Check Logs:**
```bash
# Search for recent degradation events (Render logs)
# In Render Dashboard > morningai-agent-worker > Logs
# Search for: checkpoint_degraded

# Or via log aggregator:
# query: event="checkpoint_degraded" AND timestamp > now() - 1h
```

**Check Completion Logs:**
```bash
# Count degraded vs total completions
# query: operation="run_orchestrator" AND timestamp > now() - 1h
# Group by: persistence_degraded
```

**Expected Output:**
- If degradation is occurring: Multiple `checkpoint_degraded` events
- If healthy: No recent `checkpoint_degraded` events

**Status**: [ ] PASS / [ ] FAIL

---

### Step 2: Check PostgreSQL Health [MUST-PASS]

**Supabase Dashboard:**
- [ ] Navigate to https://supabase.com/dashboard
- [ ] Select MorningAI project
- [ ] Go to **Database** > **Health**
- [ ] Check connection count and latency

**Direct Connection Test:**
```bash
# From a machine with database access:
psql "$DATABASE_URL" -c "SELECT 1;"
```

**Common Issues:**
| Symptom | Likely Cause | Resolution |
|---------|--------------|------------|
| Connection refused | PostgreSQL down | Check Supabase status page |
| SSL handshake failed | Certificate issue | Check SSL configuration |
| Too many connections | Connection pool exhausted | Restart workers |
| Timeout | Network issue | Check Render <-> Supabase connectivity |

**Status**: [ ] PASS / [ ] FAIL

---

### Step 3: Determine Root Cause

**Check Sentry for Error Details:**
- [ ] Navigate to Sentry > MorningAI project
- [ ] Filter by: `logger:langgraph_orchestrator`
- [ ] Look for: SSL errors, connection errors, timeout errors

**Common Root Causes:**

| Error Pattern | Root Cause | Resolution |
|---------------|------------|------------|
| `SSL connection has been closed` | Supabase idle timeout | Add keepalive parameters |
| `connection reset by peer` | Network instability | Check Render region |
| `could not connect to server` | PostgreSQL down | Wait for Supabase recovery |
| `circuit breaker open` | Prolonged DB unavailability | Fix underlying DB issue |
| `all retries exhausted` | Transient errors persisting | Check DB load |

---

### Step 4: Resolution Actions

#### 4a. If PostgreSQL is Down (P0)

**Immediate Actions:**
1. **Notify stakeholders**: Post in #incidents Slack channel
2. **Check Supabase status**: https://status.supabase.com
3. **Wait for recovery**: Supabase typically auto-recovers
4. **Monitor degradation ratio**: Should decrease as DB recovers

**Post-Recovery:**
- New workflows will automatically use PostgreSQL
- Degraded workflows will complete with MemorySaver (no action needed)
- No manual intervention required for recovery

#### 4b. If Connection Pool Exhausted

**Restart Workers:**
- [ ] Navigate to Render Dashboard
- [ ] Select `morningai-agent-worker` service
- [ ] Click **Manual Deploy** > **Deploy latest commit**
- [ ] Wait for deployment to complete
- [ ] Verify degradation ratio decreases

#### 4c. If SSL/Keepalive Issues

**Update DATABASE_URL:**
Add keepalive parameters to prevent idle disconnects:
```
?keepalives=1&keepalives_idle=30&keepalives_interval=10&keepalives_count=5
```

**Steps:**
- [ ] Navigate to Render Dashboard > `morningai-agent-worker` > Environment
- [ ] Update `DATABASE_URL` with keepalive parameters
- [ ] Click **Save Changes**
- [ ] Redeploy service

---

### Step 5: Verify Recovery [MUST-PASS]

**Check Degradation Ratio:**
```bash
# Wait 15 minutes after fix
# query: operation="run_orchestrator" AND timestamp > now() - 15m
# Verify: persistence_degraded=False for new workflows
```

**Submit Test Task:**
- [ ] Submit a test task via Owner Console or API
- [ ] Check worker logs for successful PostgreSQL checkpoint operations
- [ ] Verify completion log shows `persistence_degraded=False`

**Status**: [ ] PASS / [ ] FAIL

---

## Emergency Kill Switch

If degraded mode is causing issues (e.g., worker OOM due to MemorySaver memory usage):

**Disable Checkpoint Failover:**
- [ ] Navigate to Render Dashboard > `morningai-agent-worker` > Environment
- [ ] Set `ENABLE_CHECKPOINT_FAILOVER=false`
- [ ] Click **Save Changes**
- [ ] Redeploy service

**Effect:**
- Workflows will fail-fast on checkpoint errors instead of degrading
- Use this only if degraded mode is causing worse problems than failing

**Re-enable After Fix:**
- [ ] Set `ENABLE_CHECKPOINT_FAILOVER=true`
- [ ] Redeploy service

---

## Configuration Reference

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `ENABLE_CHECKPOINT_FAILOVER` | `true` | Enable/disable degraded persistence mode |
| `USE_POSTGRES_CHECKPOINTER` | `true` | Use PostgreSQL for checkpointing |
| `DATABASE_URL` | (required) | PostgreSQL connection string |

### Transient Error Patterns

The following error patterns trigger failover to MemorySaver:

```
ssl connection has been closed
the connection is closed
connection is closed
server closed the connection
connection reset by peer
connection timed out
could not connect to server
pipeline [bad]
circuit breaker open
all retries exhausted
```

### Render Services

| Service | Purpose |
|---------|---------|
| `morningai-agent-worker` | RQ worker that runs orchestrator tasks |
| `morningai-orchestrator-api` | FastAPI for orchestrator endpoints |

---

## Post-Incident Review

After resolving a degradation incident:

1. **Document the incident**:
   - Create a post-mortem issue
   - Include timeline, root cause, and resolution
   - Tag with `incident` and `checkpoint-degradation`

2. **Update monitoring**:
   - Add any new error patterns to detection
   - Adjust alert thresholds if needed

3. **Verify safeguards**:
   - Confirm `ENABLE_CHECKPOINT_FAILOVER=true`
   - Verify PostgreSQL health monitoring is active

4. **Team communication**:
   - Share learnings in #engineering
   - Update this runbook if needed

---

## Escalation

If you cannot resolve the issue:

1. **Check Supabase Support**: https://supabase.com/support
2. **Check Render Support**: https://render.com/support
3. **Escalate to CTO**: For critical production issues

---

## Quick Reference

### Log Search Queries

```bash
# Find degradation events
event="checkpoint_degraded"

# Find degraded completions
persistence_degraded=True

# Find circuit breaker events
circuit_breaker="opened"

# Find all checkpoint errors
operation="resilient_postgres_saver" AND level=ERROR
```

### Key URLs

- **Render Dashboard**: https://dashboard.render.com
- **Supabase Dashboard**: https://supabase.com/dashboard
- **Supabase Status**: https://status.supabase.com
- **Sentry**: https://sentry.io (MorningAI project)

### Related Code

- `DegradedPersistenceCheckpointer`: `langgraph_orchestrator.py:989-1203`
- `ResilientPostgresSaver`: `langgraph_orchestrator.py:594-986`
- Feature flag: `ENABLE_CHECKPOINT_FAILOVER` in `settings.py`

---

## Execution Log

After executing this runbook, record the results below:

| Date | Trigger | Degradation Ratio | Root Cause | Resolution | Executor | Notes |
|------|---------|-------------------|------------|------------|----------|-------|
| - | - | - | - | - | - | - |

**Instructions**: After resolving an incident, add a row with:
- **Date**: YYYY-MM-DD HH:MM UTC format
- **Trigger**: `ssl_error`, `connection_timeout`, `circuit_breaker`, `db_down`, etc.
- **Degradation Ratio**: Percentage of workflows affected
- **Root Cause**: Brief description
- **Resolution**: Action taken
- **Executor**: Person name or on-call rotation
- **Notes**: Incident doc, Sentry link, etc.

---

## Version History

| Version | Date | Change | Author |
|---------|------|--------|--------|
| v1.0 | 2025-12-26 | Initial runbook created for DegradedPersistenceCheckpointer | Engineering Team |
