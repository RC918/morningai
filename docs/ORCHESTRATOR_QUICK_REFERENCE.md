# Orchestrator Quick Reference Card

**Version**: Phase 1 (2025-11-24)  
**Complete Documentation**: [ONBOARDING_GUIDE.md](./ONBOARDING_GUIDE.md#orchestrator-architecture)

---

## 🎯 When to Use Which Mode?

| Scenario | Use Mode | Explanation |
|----------|----------|-------------|
| **New Feature Development** | LangGraph Mode | All new features MUST be implemented in LangGraph mode |
| **Bug Fixes** | Simple Mode | Simple mode only accepts bug fixes (feature-frozen) |
| **Modifying graph.execute()** | BOTH Modes | Must test both Simple and LangGraph modes |
| **Testing New Features** | LangGraph Mode | Use `USE_LANGGRAPH=true` to force routing |
| **Production Rollback** | Simple Mode | Set `USE_LANGGRAPH_PERCENT=0` for immediate rollback |

---

## ⚙️ Environment Variables Quick Reference

| Variable | Default | Purpose | Scope |
|----------|---------|---------|-------|
| `USE_LANGGRAPH` | `false` | Force 100% LangGraph routing | Worker routing decision |
| `USE_LANGGRAPH_PERCENT` | `0` | Canary percentage (0-100) | Worker routing decision |
| `USE_LLM_PLANNER` | `false` | Use LLM vs static planner | LangGraph mode only |

### Default Configuration

```bash
# Default Worker Configuration
USE_LANGGRAPH=false              # Allow canary routing
USE_LANGGRAPH_PERCENT=0          # Default: 0% (100% Simple Mode)
USE_LLM_PLANNER=false            # LangGraph uses static planner by default
```

**Environment-Specific Overrides**:
- Development: `USE_LANGGRAPH_PERCENT=0` (100% Simple Mode)
- Staging: `USE_LANGGRAPH_PERCENT=15` (15% LangGraph canary)
- Production: `USE_LANGGRAPH_PERCENT=0` (100% Simple Mode, conservative)

**Note**: For staging worker configuration, refer to [STAGING_SETUP_GUIDE.md](./ops/STAGING_SETUP_GUIDE.md). Staging worker service names are environment-specific.

### Configuration Locations

**Render Dashboard**:
1. Navigate to service (e.g., `morningai-agent-worker`)
2. Click "Environment" tab
3. Add/modify environment variables
4. Click "Save Changes" (triggers auto-redeploy)

---

## 🖥️ Service Names Quick Reference

| Service | Role | Environment | Configuration Location |
|---------|------|-------------|----------------------|
| `morningai-agent-worker` | Production Worker | Production | Render Dashboard → Production Worker → Environment |
| `morningai-backend-v2` | API Backend | Production | ❌ No routing flags needed (API layer) |

**Important**: Routing flags (`USE_LANGGRAPH*`) are set on **Worker services only**, NOT on API Backend.

**Staging Workers**: For staging worker service names and configuration, refer to [STAGING_SETUP_GUIDE.md](./ops/STAGING_SETUP_GUIDE.md). Worker services may differ by environment.

---

## 🔍 Log Search Keywords

| Keyword | Purpose | Example |
|---------|---------|---------|
| `"Using LangGraph orchestrator"` | Find LangGraph mode executions | Search in worker logs (Render Dashboard) |
| `"Using simple orchestrator"` | Find Simple mode executions | Search in worker logs (Render Dashboard) |
| `"Canary deployment"` | Find routing decisions | Search in worker logs (Render Dashboard) |
| `"task_percent"` | Find task routing percentages | Search in worker logs (Render Dashboard) |
| `planner_type` | Identify planner type (llm/static) | Search in planner logs |
| `trace_id` | Track execution across services | Search in logs by trace ID |

---

## 🧪 Local Testing Commands

### Test Simple Mode

```bash
cd handoff/20250928/40_App/orchestrator
export USE_LANGGRAPH=false
export USE_LANGGRAPH_PERCENT=0
pytest tests/test_persistence_db_writer.py -v
```

### Test LangGraph Mode

```bash
cd handoff/20250928/40_App/orchestrator
export USE_LANGGRAPH=true
pytest tests/test_langgraph_smoke.py -v
```

### Test Canary Routing

```bash
cd handoff/20250928/40_App/orchestrator
export USE_LANGGRAPH=false
export USE_LANGGRAPH_PERCENT=5
pytest tests/test_worker.py -k canary -v
```

**Note**: Canary routing tests are in `test_worker.py` (e.g., `test_canary_5_percent_distribution`, `test_canary_deterministic_same_task_id`).

### Test Both Modes (Required for graph.execute() changes)

```bash
cd handoff/20250928/40_App/orchestrator

# Test Simple Mode
export USE_LANGGRAPH=false USE_LANGGRAPH_PERCENT=0
pytest tests/test_persistence_db_writer.py -v

# Test LangGraph Mode
export USE_LANGGRAPH=true
pytest tests/test_langgraph_smoke.py -v
```

---

## 📊 Monitoring Metrics

| Metric | Location | Purpose |
|--------|----------|---------|
| `decisions.langgraph` | Redis/Logs | Count of LangGraph mode selections |
| `decisions.simple` | Redis/Logs | Count of Simple mode selections |
| `planner_runs.jsonl` | Logs | Planner execution records with timing |
| `task_execution_time` | Logs | End-to-end task duration |
| `graph_execute_time` | Logs | Time spent in shared core executor |

### Expected Ratios

Traffic split is configurable via `USE_LANGGRAPH_PERCENT`:
- Default: 100% Simple Mode (USE_LANGGRAPH_PERCENT=0)
- Staging: 85% Simple / 15% LangGraph (USE_LANGGRAPH_PERCENT=15)
- Error Rate: <5% for Simple, <20% for LangGraph (canary tolerance)

---

## 🚨 Common Pitfalls & Solutions

| Pitfall | Correct Approach |
|---------|-----------------|
| ❌ Adding new features to Simple mode | ✅ Add new features to LangGraph mode only |
| ❌ Modifying graph.py and testing only one mode | ✅ Test BOTH Simple and LangGraph modes |
| ❌ Thinking graph.py is "old orchestrator" | ✅ graph.py is the **shared core executor** used by both modes |
| ❌ Setting routing flags on API Backend | ✅ Set routing flags on **Worker services only** |
| ❌ Assuming 100% LangGraph is safe | ✅ Use gradual rollout: 5% → 25% → 50% → 100% |

---

## 🔄 Quick Rollback Procedures

### Scenario 1: LangGraph Mode Issues (Most Common)

**Symptoms**: High error rate (>20%), timeouts, incorrect results

**Immediate Rollback** (< 2 minutes):
```bash
# In Render Dashboard → morningai-agent-worker → Environment
USE_LANGGRAPH_PERCENT = 0  # Route 100% to Simple Mode
# Save and redeploy
```

**Verify**: Check worker logs in Render Dashboard for `"Using simple orchestrator"` (should be 100%)

**Recovery Time**: < 5 minutes

### Scenario 2: Shared Core Issues (Rare but Critical)

**Symptoms**: Both modes failing, graph.execute() errors

**Rollback**:
```bash
git revert <bad_commit_hash>
git push origin main
# Render auto-deploys
```

**Recovery Time**: 10-15 minutes

### Scenario 3: Complete Worker Failure

**Symptoms**: Worker crashes, Redis queue backing up

**Rollback**:
- Render Dashboard → morningai-agent-worker → Manual Deploy
- Select previous successful deployment
- Click "Deploy"

**Recovery Time**: 5-10 minutes

---

## 📐 Architecture Quick View

```
HTTP Request → API Backend → Redis Queue → Worker
                                             ↓
                                    Routing Decision (MD5 Hash)
                                    /                    \
                              Simple Mode          LangGraph Mode
                             (Feature-frozen)    (Active development)
                                    \                    /
                                     graph.execute()
                                   (Shared Core Executor)
```

**Key Insight**: Both modes use the same `graph.execute()` function. Modifications affect both modes.

---

## 📞 Need Help?

### Complete Documentation

- 📖 **Architecture Overview**: [ONBOARDING_GUIDE.md](./ONBOARDING_GUIDE.md#orchestrator-architecture)
- 📊 **System Details**: [PROJECT_STRUCTURE_REPORT.md](./PROJECT_STRUCTURE_REPORT.md#orchestrator-system)
- ⚙️ **Configuration Guide**: [ENVIRONMENTS.md](./ENVIRONMENTS.md#orchestrator-configuration)
- 📝 **Design Decisions**: [ADR-004: Shared Core Executor Pattern](./adr/004-shared-core-executor-pattern.md)
- 📝 **Historical Context**: [ADR-005: Dual Orchestrator Architecture](./adr/005-dual-orchestrator-architecture.md)

### Code Locations

- **Shared Core**: `handoff/20250928/40_App/orchestrator/graph.py:30-155`
- **Routing Logic**: `handoff/20250928/40_App/orchestrator/redis_queue/worker.py:366-395`
- **Simple Mode Call**: `handoff/20250928/40_App/orchestrator/redis_queue/worker.py:399-400`
- **LangGraph Mode**: `handoff/20250928/40_App/orchestrator/langgraph_orchestrator.py:143`
- **Settings**: `common/config/settings.py:890-908`

---

## 🎓 Development Checklist

### When Modifying graph.execute()

- [ ] Understand changes affect BOTH modes
- [ ] Test Simple mode: `USE_LANGGRAPH=false USE_LANGGRAPH_PERCENT=0`
- [ ] Test LangGraph mode: `USE_LANGGRAPH=true`
- [ ] Test canary routing: `USE_LANGGRAPH=false USE_LANGGRAPH_PERCENT=5`
- [ ] Update tests in both `test_persistence_db_writer.py` and `test_langgraph_smoke.py`
- [ ] Document behavioral changes in PR description
- [ ] Get CTO approval for major changes

### When Adding New Features

- [ ] Implement in LangGraph mode only
- [ ] Do NOT add to Simple mode (feature-frozen)
- [ ] Can call `graph.execute()` for core execution
- [ ] Test with `USE_LANGGRAPH=true`
- [ ] Document in PR description

---

**Last Updated**: 2025-11-24  
**Next Review**: 2025-12-24

---

*This is a quick reference card. For complete documentation, see [ONBOARDING_GUIDE.md](./ONBOARDING_GUIDE.md#orchestrator-architecture).*
