# Orchestrator Quick Reference Card

**Version**: Phase 8 (2025-12-20) - LangGraph Only  
**Complete Documentation**: [ONBOARDING_GUIDE.md](./ONBOARDING_GUIDE.md#orchestrator-architecture)

---

> **Important**: As of December 2025 (Issue #2651), Simple Mode has been removed. LangGraph is now the only orchestrator mode. This document has been updated to reflect the current architecture.

---

## Architecture Overview

```
HTTP Request → API Backend → Redis Queue → Worker
                                             ↓
                                    LangGraph Orchestrator
                                             ↓
                                      graph.execute()
                                    (Core Executor)
```

**Key Insight**: LangGraph is the sole orchestration mode. All tasks are processed through the LangGraph orchestrator.

---

## Environment Variables Quick Reference

| Variable | Default | Purpose | Scope |
|----------|---------|---------|-------|
| `USE_LLM_PLANNER` | `false` | Use LLM vs static planner | LangGraph orchestrator |
| `USE_LLM_REVIEWER` | `false` | Enable LLM-powered code reviewer | LangGraph orchestrator |
| `USE_POSTGRES_CHECKPOINTER` | `false` (prod: `true`) | PostgreSQL state persistence | LangGraph orchestrator |
| `ENABLE_CHECKPOINT_FAILOVER` | `true` | Failover to MemorySaver on error | LangGraph orchestrator |

### Default Configuration

```bash
# Default Worker Configuration (Production)
USE_LLM_PLANNER=false            # Static planner by default
USE_LLM_REVIEWER=false           # CI-only reviewer by default
USE_POSTGRES_CHECKPOINTER=true   # PostgreSQL checkpointer in production
```

### Configuration Locations

**Render Dashboard**:
1. Navigate to service (e.g., `morningai-agent-worker`)
2. Click "Environment" tab
3. Add/modify environment variables
4. Click "Save Changes" (triggers auto-redeploy)

---

## Service Names Quick Reference

| Service | Role | Environment | Configuration Location |
|---------|------|-------------|----------------------|
| `morningai-agent-worker` | Production Worker | Production | Render Dashboard → Production Worker → Environment |
| `morningai-backend-v2` | API Backend | Production | Render Dashboard → Backend → Environment |
| `morningai-orchestrator-api` | Orchestrator API | Production | Render Dashboard → Orchestrator API → Environment |

---

## Log Search Keywords

| Keyword | Purpose | Example |
|---------|---------|---------|
| `"Using LangGraph orchestrator"` | Find LangGraph executions | Search in worker logs (Render Dashboard) |
| `"Using PostgreSQL checkpointer"` | Verify checkpointer type | Search in worker logs |
| `"CHECKPOINT DEGRADED"` | Detect checkpointer failover events | Search in worker logs |
| `planner_type` | Identify planner type (llm/static) | Search in planner logs |
| `trace_id` | Track execution across services | Search in logs by trace ID |
| `[I-4-ADVISORY]` | Degradation advisor recommendations | Search in governance logs |

---

## Local Testing Commands

### Test LangGraph Mode

```bash
cd handoff/20250928/40_App/orchestrator
pytest tests/test_langgraph_smoke.py -v
```

### Test with LLM Planner

```bash
cd handoff/20250928/40_App/orchestrator
export USE_LLM_PLANNER=true
pytest tests/test_langgraph_smoke.py -v
```

### Test Checkpointer Failover

```bash
cd handoff/20250928/40_App/orchestrator
export USE_POSTGRES_CHECKPOINTER=true
export ENABLE_CHECKPOINT_FAILOVER=true
pytest tests/test_checkpointer.py -v
```

---

## Monitoring Metrics

| Metric | Location | Purpose |
|--------|----------|---------|
| `planner_runs.jsonl` | Logs | Planner execution records with timing |
| `task_execution_time` | Logs | End-to-end task duration |
| `graph_execute_time` | Logs | Time spent in core executor |
| `checkpoint_failover_count` | Logs | Number of failovers to MemorySaver |

---

## Common Pitfalls & Solutions

| Pitfall | Correct Approach |
|---------|-----------------|
| Assuming USE_LANGGRAPH flags still exist | USE_LANGGRAPH flags were removed in Issue #2651 |
| Not setting USE_POSTGRES_CHECKPOINTER in prod | Set to `true` in production for state persistence |
| Ignoring checkpoint failover logs | Monitor `CHECKPOINT DEGRADED` logs for degradation |
| Not testing with LLM planner before enabling | Test locally with `USE_LLM_PLANNER=true` first |

---

## Quick Rollback Procedures

### Scenario 1: LLM Planner Issues

**Symptoms**: High error rate, incorrect planning, timeouts

**Immediate Rollback** (< 2 minutes):
```bash
# In Render Dashboard → morningai-agent-worker → Environment
USE_LLM_PLANNER = false  # Revert to static planner
# Save and redeploy
```

**Verify**: Check worker logs for `planner_type: static`

**Recovery Time**: < 5 minutes

### Scenario 2: Checkpointer Issues

**Symptoms**: Persistent state persistence failures, workflow interruptions, or repeated `CHECKPOINT DEGRADED` logs

**Context**: The system has automatic failover to an in-memory checkpointer for transient database errors. Use this manual rollback if PostgreSQL issues are persistent or if the automatic failover mechanism is causing problems.

**Immediate Rollback**:
```bash
# In Render Dashboard → morningai-agent-worker → Environment
USE_POSTGRES_CHECKPOINTER = false  # Fallback to in-memory MemorySaver
# Save and redeploy
```

**Impact**: This reverts to in-memory state management. Workflows in progress will lose state if the worker restarts.

### Scenario 3: Complete Worker Failure

**Symptoms**: Worker crashes, Redis queue backing up

**Rollback**:
- Render Dashboard → morningai-agent-worker → Manual Deploy
- Select previous successful deployment
- Click "Deploy"

**Recovery Time**: 5-10 minutes

---

## Need Help?

### Complete Documentation

- **Architecture Overview**: [ONBOARDING_GUIDE.md](./ONBOARDING_GUIDE.md#orchestrator-architecture)
- **System Details**: [PROJECT_STRUCTURE_REPORT.md](./PROJECT_STRUCTURE_REPORT.md#orchestrator-system)
- **Configuration Guide**: [ENVIRONMENTS.md](./ENVIRONMENTS.md#orchestrator-configuration)
- **Design Decisions**: [ADR-004: Shared Core Executor Pattern](./adr/004-shared-core-executor-pattern.md)
- **Historical Context**: [ADR-005: Deprecate Simple Orchestrator Mode](./adr/005-deprecate-simple-orchestrator-mode.md)

### Code Locations

- **Core Executor**: `handoff/20250928/40_App/orchestrator/graph.py`
- **LangGraph Orchestrator**: `handoff/20250928/40_App/orchestrator/langgraph_orchestrator.py`
- **Worker**: `handoff/20250928/40_App/orchestrator/redis_queue/worker.py`
- **Settings**: `common/config/settings.py`
- **Routing Engine**: `handoff/20250928/40_App/orchestrator/core/routing/engine.py`

---

## Development Checklist

### When Modifying graph.execute()

- [ ] Understand changes affect all LangGraph workflows
- [ ] Test with `pytest tests/test_langgraph_smoke.py -v`
- [ ] Test checkpointer integration
- [ ] Update tests in `test_langgraph_smoke.py`
- [ ] Document behavioral changes in PR description
- [ ] Get CTO approval for major changes

### When Adding New Features

- [ ] Implement in LangGraph orchestrator
- [ ] Can call `graph.execute()` for core execution
- [ ] Test with various planner configurations
- [ ] Document in PR description

### When Enabling LLM Features (Canary)

- [ ] Test locally with feature flag enabled
- [ ] Start with low percentage in staging
- [ ] Monitor error rates and latency
- [ ] Gradually increase percentage
- [ ] Document rollback procedure

---

**Last Updated**: 2025-12-20  
**Next Review**: 2026-01-20

---

*This is a quick reference card. For complete documentation, see [ONBOARDING_GUIDE.md](./ONBOARDING_GUIDE.md#orchestrator-architecture).*
