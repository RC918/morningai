# ADR-005: Dual Orchestrator Architecture

**Status**: Accepted (Interim)  
**Date**: 2025-11-03  
**Decision Makers**: CTO, Engineering Team  
**Sunset Target**: 2026 Q1

---

## Context

MorningAI currently operates with two separate orchestrator implementations serving different purposes:

1. **New Orchestrator** (`orchestrator/` in root directory)
   - FastAPI-based API service
   - Graph-based task management
   - Does NOT include LangGraph
   - Deployed as `morningai-orchestrator-api` on Render

2. **Legacy Orchestrator** (`handoff/20250928/40_App/orchestrator/`)
   - LangGraph-based workflow engine
   - Used by RQ (Redis Queue) workers
   - Includes stateful workflow management
   - Deployed as worker instances on Render

This dual architecture emerged during the transition from Phase 4-7 implementation to Phase 8 (current MVP).

---

## Decision

We accept the dual orchestrator architecture as an **interim solution** with the following constraints:

### Current State (2025-11-04)

**API Orchestrator (Production API Layer)**:
- **Component**: API Orchestrator
- **Role**: API Layer (FastAPI)
- **Maturity**: Beta
- **Technology**: FastAPI, Redis Queue, Docker
- **Deployment**: `orchestrator/Dockerfile`, port 8000, service: `morningai-orchestrator-api`
- **Environment**: `USE_LANGGRAPH=false`
- **Responsibilities**:
  - Task queue management
  - Agent sandbox coordination
  - Management Control Plane (MCP)
  - API authentication (JWT)

**Worker Orchestrator (Task Execution Layer)**:
- **Component**: Worker Orchestrator
- **Role**: Task Execution (RQ + LangGraph)
- **Maturity**: Production
- **Technology**: LangGraph, RQ workers, Python
- **Deployment**: `handoff/20250928/40_App/orchestrator/`, service: `morningai-agent-worker`
- **Responsibilities**:
  - Stateful workflow execution
  - LangGraph-based agent coordination
  - Background task processing

### Rationale

**Why maintain both?**
1. **Risk Mitigation**: Existing RQ workers depend on legacy orchestrator
2. **Feature Parity**: New orchestrator doesn't yet have all LangGraph features
3. **Gradual Migration**: Allows incremental transition without service disruption
4. **Owner Console Priority**: Phase 8 focuses on Owner Console features, not orchestrator consolidation

**Why consolidate later?**
1. **Maintenance Burden**: Two codebases increase complexity
2. **Dependency Drift**: Different dependency sets can cause conflicts
3. **Developer Confusion**: Unclear which orchestrator to use for new features
4. **Deployment Complexity**: Two services to monitor and maintain

---

## Consequences

### Positive

- ✅ No immediate disruption to existing RQ workers
- ✅ New orchestrator can evolve independently
- ✅ Clear separation of concerns (API vs workers)
- ✅ Allows Owner Console development to proceed without orchestrator refactor

### Negative

- ⚠️ Increased maintenance burden (two codebases)
- ⚠️ Potential dependency conflicts
- ⚠️ Developer confusion about which to use
- ⚠️ Documentation must clearly distinguish both

### Mitigation Strategies

1. **Clear Documentation**: This ADR and updated PROJECT_STRUCTURE_REPORT.md
2. **Monitoring**: Track usage of both orchestrators
3. **Migration Plan**: Defined consolidation timeline (2026 Q1)
4. **Code Freeze**: No new features in legacy orchestrator

---

## Migration Plan (2026 Q1)

### Phase 1: Assessment (Week 1-2)
- [ ] Audit all RQ worker dependencies on legacy orchestrator
- [ ] Identify LangGraph features used by workers
- [ ] Evaluate if new orchestrator needs LangGraph

### Phase 2: Decision (Week 3)
- [ ] **Option A**: Add LangGraph to new orchestrator
- [ ] **Option B**: Refactor workers to not need LangGraph
- [ ] **Option C**: Keep dual architecture (extend sunset date)

### Phase 3: Implementation (Week 4-8)
- [ ] Implement chosen option
- [ ] Migrate workers to new orchestrator
- [ ] Update deployment configurations
- [ ] Update documentation

### Phase 4: Deprecation (Week 9-10)
- [ ] Remove legacy orchestrator code
- [ ] Update all references in documentation
- [ ] Archive legacy code for reference

---

## Alternatives Considered

### Alternative 1: Immediate Consolidation
**Rejected**: Too risky, would block Owner Console development

### Alternative 2: Keep Dual Architecture Permanently
**Rejected**: Maintenance burden too high long-term

### Alternative 3: Deprecate New Orchestrator
**Rejected**: New orchestrator is better architecture for API service

---

## References

- **render.yaml**: Lines 48 (`USE_LANGGRAPH=false`), 64 (worker path), 114 (orchestrator API)
- **orchestrator/requirements.txt**: No LangGraph dependency
- **handoff/.../orchestrator/langgraph_orchestrator.py**: Legacy LangGraph implementation
- **Owner Console Roadmap**: Tasks 1-26 (no orchestrator consolidation required)

---

## Related Tracking

- **GitHub Issue #1105**: [Orchestrator Consolidation Tracking](https://github.com/RC918/morningai/issues/1105)
  - Comprehensive task breakdown for 2026 Q1 consolidation
  - Based on "Option B: Unified Architecture" from this ADR
  - Acceptance criteria and testing requirements
  - Status: Open (target Q1 2026)

---

## Review Schedule

- **2025-12-01**: Review migration plan progress
- **2026-01-01**: Begin migration implementation
- **2026-03-31**: Target completion date

---

**Last Updated**: 2025-11-04  
**Next Review**: 2025-12-01
