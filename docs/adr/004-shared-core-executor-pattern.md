# ADR-004: Shared Core Executor Pattern

**Status**: Accepted  
**Date**: 2025-11-24  
**Deciders**: CTO, Engineering Team  
**Related**: ADR-001, ADR-002, PR #1520

---

## Context

MorningAI's Worker Orchestrator operates in a dual-mode architecture with two execution paths:

1. **Simple Mode** (~95% traffic)
   - Direct execution path
   - Feature-frozen (bug fixes only)
   - Stable baseline for production

2. **LangGraph Mode** (~5% traffic)
   - LangGraph-based workflow engine
   - Active development path
   - Innovation and new features

Both modes need to execute agent tasks with consistent behavior. The key architectural question is: **Should each mode have its own execution engine, or should they share a common core?**

### Current Implementation

The codebase currently uses a **shared core executor pattern**:
- `graph.execute()` function in `handoff/20250928/40_App/orchestrator/graph.py:30`
- Simple mode calls `graph.execute()` directly
- LangGraph mode calls `graph.execute()` through an executor node
- Both modes produce identical execution behavior

This pattern emerged organically during the Phase 1 canary deployment implementation but was never formally documented as an architectural decision.

### The Problem

Without formal documentation of this pattern, developers face:
- **Confusion**: Is `graph.py` the "old orchestrator" or a shared component?
- **Testing Gaps**: Developers might test only one mode when modifying `graph.execute()`
- **Refactoring Risk**: Phase 3 refactoring decisions lack historical context
- **Onboarding Difficulty**: New engineers don't understand why this pattern was chosen

---

## Decision

We formally adopt the **Shared Core Executor Pattern** for the dual-mode orchestrator architecture.

### Definition

The Shared Core Executor Pattern means:
- `graph.execute()` is the canonical execution engine for both modes
- Simple mode and LangGraph mode are **routing wrappers** around the shared core
- Modifications to `graph.execute()` affect both modes equally
- The shared core is NOT "legacy code" but an active, maintained component

### Implementation Details

**Shared Core Executor** (`graph.py:30-155`):
```python
def execute(goal: str, repo_full: str, trace_id: Optional[str] = None):
    # Core execution logic used by BOTH modes
    # - Cost tracking
    # - Reputation management
    # - Agent coordination
    # - Task execution
```

**Simple Mode** (`worker.py:399-400`):
```python
from graph import execute
logger.info(f"Using simple orchestrator for task {task_id}")
# Direct call to shared core
```

**LangGraph Mode** (`langgraph_orchestrator.py:143`):
```python
from graph import execute
# Called through executor_node in LangGraph workflow
```

**Routing Decision** (`worker.py:366-395`):
- MD5-based deterministic routing
- Controlled by `USE_LANGGRAPH_PERCENT` (0-100)
- Decision made at worker level, not API level

---

## Rationale

### Why Shared Core?

**1. Code Reuse**
- Avoids duplicating complex execution logic
- Single source of truth for core functionality
- Reduces maintenance burden

**2. Behavioral Consistency**
- Both modes produce identical execution results
- Easier to validate correctness
- Simplifies testing and debugging

**3. Migration Safety**
- Gradual migration from Simple to LangGraph mode
- Shared core ensures no behavioral regressions
- Easy rollback if LangGraph mode has issues

**4. Testing Efficiency**
- Core execution logic tested once
- Mode-specific tests focus on routing and workflow
- Reduces test duplication

### Why NOT Complete Separation?

**Alternative: Each mode has its own executor**

**Pros**:
- Complete independence between modes
- No coupling between Simple and LangGraph
- Easier to refactor one mode without affecting the other

**Cons**:
- Code duplication (2x maintenance)
- Risk of behavioral divergence
- Difficult to ensure consistency
- Higher testing burden
- Migration complexity (need to verify both executors)

**Decision**: The cons outweigh the pros for Phase 1-2. Complete separation may be reconsidered in Phase 3.

---

## Consequences

### Positive

- ✅ **Code Reuse**: Single implementation of core execution logic
- ✅ **Consistency**: Both modes behave identically
- ✅ **Testing Efficiency**: Core logic tested once
- ✅ **Migration Safety**: Gradual transition with stable baseline
- ✅ **Maintenance**: Single codebase for core functionality

### Negative

- ⚠️ **Coupling**: Modifications to `graph.execute()` affect both modes
- ⚠️ **Testing Complexity**: Must test both modes when modifying shared core
- ⚠️ **Refactoring Constraints**: Phase 3 refactoring must handle both modes
- ⚠️ **Developer Confusion**: Need clear documentation that `graph.py` is shared

### Mitigation Strategies

1. **Documentation**: This ADR + updated ONBOARDING_GUIDE.md (PR #1520)
2. **Testing Requirements**: Explicit requirement to test both modes when modifying `graph.execute()`
3. **Code Comments**: Clear comments in `graph.py` indicating shared usage
4. **PR Guidelines**: Reviewers check for dual-mode testing
5. **Phase 3 Planning**: Document refactoring options with trade-offs

---

## Alternatives Considered

### Alternative 1: Complete Separation

**Description**: Simple mode and LangGraph mode each have their own execution engine.

**Pros**:
- Complete independence
- No coupling between modes
- Easier to refactor one mode

**Cons**:
- Code duplication
- Behavioral divergence risk
- Higher maintenance burden
- Complex migration validation

**Decision**: **Rejected** for Phase 1-2. May reconsider in Phase 3 if LangGraph mode reaches 100% traffic and proves stable.

---

### Alternative 2: LangGraph 100% Replacement

**Description**: Remove Simple mode entirely, use only LangGraph mode.

**Pros**:
- Single execution path
- No dual-mode complexity
- Simplified architecture

**Cons**:
- High risk (no stable baseline)
- Difficult rollback
- Requires LangGraph mode to be production-ready
- No gradual migration path

**Decision**: **Rejected**. Canary deployment requires a stable baseline (Simple mode) for comparison and rollback.

---

### Alternative 3: Abstract Executor Interface

**Description**: Define `ExecutorInterface`, both modes implement it.

**Pros**:
- Clean abstraction
- Flexible implementation
- Supports multiple executors

**Cons**:
- Over-engineering for current needs
- Adds complexity without clear benefit
- Still requires shared logic (duplication or composition)

**Decision**: **Rejected**. YAGNI (You Aren't Gonna Need It). Current shared core pattern is simpler and sufficient.

---

### Alternative 4: Shared Core (Current Choice) ✅

**Description**: `graph.execute()` as shared core, modes are routing wrappers.

**Pros**:
- Code reuse
- Behavioral consistency
- Testing efficiency
- Migration safety

**Cons**:
- Coupling between modes
- Testing complexity (must test both)

**Decision**: **Accepted**. Best balance of simplicity, safety, and maintainability for Phase 1-2.

---

## Phase 3 Refactoring Options

When LangGraph mode reaches 100% traffic and runs stably for 3+ months, consider:

### Option 1: Keep Shared Core

**When**: If `graph.execute()` still meets all requirements

**Action**: No refactoring needed

**Pros**:
- Zero risk
- No migration cost
- Proven stability

**Cons**:
- Maintains dual-mode complexity
- Long-term maintenance burden

---

### Option 2: Migrate to LangGraph Native

**When**: LangGraph mode is stable and proven at 100% traffic

**Action**: 
1. Migrate `graph.execute()` logic into LangGraph native nodes
2. Remove Simple mode code
3. Remove routing logic

**Pros**:
- Simplified architecture (single mode)
- Remove dual-mode complexity
- Full LangGraph feature utilization

**Cons**:
- High refactoring cost
- Extensive testing required
- Risk of regressions

**Estimated Effort**: 4-6 weeks

---

### Option 3: Abstract Executor Interface

**When**: Need to support multiple execution engines

**Action**:
1. Define `ExecutorInterface`
2. Implement `GraphExecutor` (current `graph.execute()`)
3. Implement `LangGraphNativeExecutor`
4. Support runtime switching

**Pros**:
- Maximum flexibility
- Support multiple executors
- Clean abstraction

**Cons**:
- Over-engineering risk
- Increased complexity
- Higher maintenance burden

**Estimated Effort**: 6-8 weeks

---

### Recommendation for Phase 3

**Start with Option 1** (Keep Shared Core):
- If `graph.execute()` works well, don't fix what isn't broken
- Evaluate after 3 months at 100% LangGraph traffic
- Only refactor if there's a clear business need

**Consider Option 2** if:
- LangGraph native features provide significant value
- Maintenance burden of dual-mode becomes too high
- Team has bandwidth for 4-6 week refactoring

**Avoid Option 3** unless:
- Clear requirement for multiple execution engines emerges
- Current architecture becomes a bottleneck

---

## Development Guidelines

### When Modifying `graph.execute()`

**Required Steps**:
1. ✅ Understand that changes affect BOTH modes
2. ✅ Test Simple mode: `USE_LANGGRAPH=false USE_LANGGRAPH_PERCENT=0`
3. ✅ Test LangGraph mode: `USE_LANGGRAPH=true`
4. ✅ Test canary routing: `USE_LANGGRAPH=false USE_LANGGRAPH_PERCENT=5`
5. ✅ Update tests in both `test_persistence_db_writer.py` and `test_langgraph_smoke.py`
6. ✅ Document behavioral changes in PR description

**Common Mistakes**:
- ❌ Assuming `graph.py` is "legacy" or "old orchestrator"
- ❌ Testing only one mode
- ❌ Adding mode-specific logic to shared core
- ❌ Modifying without understanding dual-mode impact

---

### When Adding New Features

**Simple Mode** (Feature-Frozen):
- ❌ Do NOT add new features
- ✅ Bug fixes only
- ✅ Security patches only

**LangGraph Mode** (Active Development):
- ✅ Add new features here
- ✅ Implement in LangGraph workflow nodes
- ✅ Can call `graph.execute()` for core execution

**Shared Core** (`graph.execute()`):
- ⚠️ Only modify if needed by BOTH modes
- ⚠️ Requires testing both modes
- ⚠️ Requires CTO approval for major changes

---

## Monitoring and Observability

### Key Metrics

**Routing Decisions**:
- `decisions.langgraph`: Count of LangGraph mode selections
- `decisions.simple`: Count of Simple mode selections
- Target ratio: ~5:95 (Phase 1)

**Execution Behavior**:
- `trace_id`: Track execution across both modes
- `planner_type`: Identify which planner was used (llm/static)
- `planning_time_ms`: Compare performance between modes

### Log Search Keywords

| Keyword | Purpose |
|---------|---------|
| `"Using LangGraph orchestrator"` | Find LangGraph mode executions |
| `"Using simple orchestrator"` | Find Simple mode executions |
| `"Canary deployment"` | Find routing decisions |
| `"task_percent"` | Find task routing percentages |

---

## Testing Strategy

### Unit Tests

**Shared Core Tests** (`test_persistence_db_writer.py`):
- Test `graph.execute()` directly
- Mock external dependencies
- Focus on core execution logic

**LangGraph Tests** (`test_langgraph_smoke.py`):
- Test LangGraph workflow
- Verify executor node calls `graph.execute()`
- Test LangGraph-specific features

**Observability Tests**:
- Verify `trace_id` propagation in integration tests
- Verify `planner_type` recording in LangGraph tests
- Test metrics collection in worker tests

### Integration Tests

**Canary Routing Tests**:
- Verify MD5-based routing
- Test percentage thresholds (0%, 5%, 50%, 100%)
- Verify deterministic behavior (same task_id → same mode)

**End-to-End Tests**:
- Test complete request flow (API → Redis → Worker → Execution)
- Verify both modes produce identical results
- Test rollback scenarios

---

## Related Documentation

- [ONBOARDING_GUIDE.md - Orchestrator Architecture](../ONBOARDING_GUIDE.md#orchestrator-architecture)
- [PROJECT_STRUCTURE_REPORT.md - Orchestrator System](../PROJECT_STRUCTURE_REPORT.md#orchestrator-system)
- [ENVIRONMENTS.md - Orchestrator Configuration](../ENVIRONMENTS.md#orchestrator-configuration)
- [ADR-005: Dual Orchestrator Architecture](./005-dual-orchestrator-architecture.md)
- [ADR-002: Producer-Consumer Architecture](./002-producer-consumer-architecture.md)
- [PR #1520: Document Orchestrator Architecture](https://github.com/RC918/morningai/pull/1520)

---

## References

**Code Locations**:
- Shared Core: `handoff/20250928/40_App/orchestrator/graph.py:30-155`
- Routing Logic: `handoff/20250928/40_App/orchestrator/redis_queue/worker.py:366-395`
- Simple Mode Call: `handoff/20250928/40_App/orchestrator/redis_queue/worker.py:399-400`
- LangGraph Mode Call: `handoff/20250928/40_App/orchestrator/langgraph_orchestrator.py:143`
- Settings: `common/config/settings.py:890-908`

**Environment Variables**:
- `USE_LANGGRAPH`: Master switch (default: `false`)
- `USE_LANGGRAPH_PERCENT`: Canary percentage 0-100 (default: `0`)
- `USE_LLM_PLANNER`: LLM vs static planner (default: `false`, LangGraph only)

---

## Review Schedule

- **2025-12-24**: Review Phase 1 metrics (1 month after ADR)
- **2026-02-24**: Review Phase 2 progress (3 months after ADR)
- **2026-05-24**: Evaluate Phase 3 refactoring options (6 months after ADR)

---

**Last Updated**: 2025-11-24  
**Next Review**: 2025-12-24
