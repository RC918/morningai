# EPIC G: Memory v2 Roadmap

**Issue**: [#3491](https://github.com/RC918/morningai/issues/3491)  
**Blueprint Reference**: Section 5.1 (Memory v2 4-Layer System) + Section 10 (Deep Memory v3)  
**Status**: Phase G-1 Complete, Phase G-2 Planning  
**Last Updated**: 2026-01-15

## Executive Summary

EPIC G implements the Memory v2 4-layer memory system that enables MorningAI to accumulate experience and learn from past interactions. This roadmap covers the storage layer, orchestrator integration, and memory consolidation mechanism.

## Architecture Vision

### 4-Layer Memory System (Blueprint Section 5.1)

| Layer | Storage | TTL | Purpose |
|-------|---------|-----|---------|
| **Short-Term** | Redis | 1 hour | Immediate task context, flow state recovery |
| **Agent Interaction** | Redis | 24 hours | Debate context, agent collaboration history |
| **Knowledge Base** | PostgreSQL + pgvector | Permanent | Long-term knowledge, solution patterns |
| **Governance** | PostgreSQL | Permanent | Safety patterns, drift analysis, routing decisions |

### Memory Flow Architecture

```
                              User Request
                                   |
                                   v
                      Short-Term Memory (1hr TTL)
                                   |
                                   v [Consolidation Agent - G-2]
                      Agent Interaction Memory (24hr TTL)
                                   |
                                   v [Consolidation Agent - G-2]
                        Knowledge Base (Permanent)
                                   |
                                   v
                      Planner v3 / Flow v3 / Agents


    [Separate Flow: Governance Memory]
    
    Routing Decisions ──────────────────────────────┐
    (routing_policy_evolver.py)                     │
                                                    v
    Safety Patterns ────────────────────> Governance Memory (Permanent)
    (safety_governor.py)                            │
                                                    v
    Drift Analysis ─────────────────────> Drift Analysis / Compliance Radar
    (heartbeat_handler.py)
```

---

## Phase Breakdown

### Phase G-1: Storage Layer + Integration (COMPLETE)

**Objective**: Implement the 4-layer memory storage infrastructure and integrate with orchestrator components.

#### G-1a: Storage Layer (PR #3962) - COMPLETE

| Component | File | Lines | Status |
|-----------|------|-------|--------|
| MemoryEntry | `memory/memory_v2.py` | 70-123 | Complete |
| ShortTermMemory | `memory/memory_v2.py` | 200-400 | Complete |
| AgentInteractionMemory | `memory/memory_v2.py` | 400-600 | Complete |
| KnowledgeBaseMemory | `memory/memory_v2.py` | 600-895 | Complete |
| GovernanceMemory | `memory/memory_v2.py` | 895-1201 | Complete |
| MemoryV2 (Unified) | `memory/memory_v2.py` | 1201-1400 | Complete |

**Key Features**:
- Redis-based hot storage (Short-Term, Agent Interaction)
- PostgreSQL + pgvector cold storage (Knowledge Base, Governance)
- Unified MemoryV2 interface
- Feature flag controlled (`ENABLE_MEMORY_V2`)

#### G-1b: Orchestrator Integration (PR #3967) - COMPLETE

| Integration Point | File | Status |
|-------------------|------|--------|
| Flow State Persistence | `flow_integration.py` | Complete |
| Debate Result Storage | `debate_engine.py` | Complete |
| Routing Decision Tracking | `routing_policy_evolver.py` | Complete |
| Integration Helpers | `memory_integration.py` | Complete |

**Feature Flags**:
- `ENABLE_MEMORY_V2`: Master switch (default: false)
- `ENABLE_MEMORY_V2_FLOW_STATE`: Flow state persistence (default: false)
- `ENABLE_MEMORY_V2_DEBATE`: Debate context persistence (default: false)
- `ENABLE_MEMORY_V2_GOVERNANCE`: Governance pattern tracking (default: false)

---

### Phase G-2: Memory Consolidation Agent (PLANNING)

**Issue**: [#3973](https://github.com/RC918/morningai/issues/3973)

**Objective**: Implement the "memory consolidation" mechanism to transfer important short-term memories to long-term knowledge base, enabling true "accumulated experience" capability.

#### Problem Statement

Without consolidation, important insights are lost after TTL expiration:
- Debate insights disappear after 24 hours
- Flow execution patterns are not preserved
- Violates Blueprint Section 9 "Predictability" guarantee

#### Solution: Consolidation Agent

```python
# Consolidation Job (runs every 6-24 hours)
class MemoryConsolidationJob:
    def run(self):
        # 1. Scan expiring memories
        expiring = self.scan_expiring_memories()
        
        # 2. Score importance
        important = self.score_importance(expiring)
        
        # 3. Summarize with LLM
        summaries = self.summarize_memories(important)
        
        # 4. Write to Knowledge Base
        self.persist_to_knowledge_base(summaries)
        
        # 5. Clean up Redis
        self.cleanup_expired()
```

#### Implementation Tasks

| Task | Description | Effort | Status |
|------|-------------|--------|--------|
| G-2.1 | ConsolidationJob infrastructure | 2-3 days | Planning |
| G-2.2 | Importance scoring engine | 1-2 days | Planning |
| G-2.3 | LLM Summarization pipeline | 2-3 days | Planning |
| G-2.4 | Metadata Schema extension | 1 day | Planning |
| G-2.5 | Integration tests + Feature Flag | 1-2 days | Planning |

#### Importance Scoring Formula

```python
importance_score = (
    debate_confidence * 0.3 +    # Debate result confidence
    outcome_impact * 0.3 +       # Impact on system
    novelty_score * 0.2 +        # Is this new knowledge?
    reference_count * 0.2        # How often referenced?
)
```

#### Metadata Schema Extension

```python
# Enhanced search with filters
results = memory.search(
    query="How to handle CI failures",
    filters={
        "project_id": "current_project",
        "memory_type": "solution_pattern",
        "confidence": ">0.8",
        "source": "debate_consolidation"
    }
)
```

---

## Related Issues

| Issue | Description | Status |
|-------|-------------|--------|
| #3491 | EPIC G: Memory v2 (Parent) | Active |
| #3962 | PR: Memory v2 Storage Layer | Merged |
| #3967 | PR: Memory v2 Orchestrator Integration | Merged |
| #3968 | PII sanitization for Memory v2 | Open |
| #3969 | Authorization checks for search functions | Open |
| #3970 | Clean up orphaned flow state on replan | Open |
| #3971 | Apply TTL configuration settings | Open |
| #3973 | G-2: Memory Consolidation Agent | Open |

---

## Blueprint Alignment

| Blueprint Section | EPIC G Coverage |
|-------------------|-----------------|
| 5.1 Memory v2 | G-1a Storage Layer (Complete) |
| 5.1 Memory v2 | G-1b Orchestrator Integration (Complete) |
| 9 Predictability | G-2 Consolidation Agent (Planning) |
| 10 Deep Memory v3 | G-2 Consolidation Agent (Planning) |

---

## Dependencies

### Upstream Dependencies
- EPIC A: Model Layer (for LLM summarization in G-2)
- EPIC I: Governance (for drift analysis storage)

### Downstream Dependencies
- EPIC B: B-13 Real-time Feedback Loop (depends on Memory v2)
- EPIC F: Planner v3 (uses Knowledge Base for planning)

---

## Changelog

| Date | Author | Changes |
|------|--------|---------|
| 2026-01-15 | Devin AI | Initial roadmap creation |
| 2026-01-15 | Devin AI | G-1a and G-1b marked complete (PR #3962, #3967) |
| 2026-01-15 | Devin AI | G-2 Memory Consolidation Agent issue created (#3973) |
