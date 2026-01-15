"""
Memory Module - MorningAI Memory System

This module provides memory storage and retrieval capabilities:

Phase 2 (Existing):
- pgvector_store: Basic vector similarity search
- error_fix_pairs: Error-fix learning pairs

EPIC G - Memory v2 (Blueprint Section 5.1):
- memory_v2: 4-layer memory system
  1. Short-Term Memory (Redis-based)
  2. Agent Interaction Memory (Redis-based)
  3. Knowledge Base (pgvector-based)
  4. Governance Memory (PostgreSQL-based)

- memory_integration: Integration helpers for orchestrator components
  - FlowController state persistence
  - DebateEngine context persistence
  - Governance memory for safety patterns and routing decisions
"""

from memory.memory_v2 import (
    MemoryV2,
    MemoryLayer,
    MemoryScope,
    MemoryEntry,
    ShortTermMemory,
    AgentInteractionMemory,
    KnowledgeBaseMemory,
    GovernanceMemory,
    get_memory_v2,
    reset_memory_v2,
)

from memory.memory_integration import (
    save_flow_state,
    restore_flow_state,
    clear_flow_state,
    save_debate_result,
    search_past_debates,
    save_safety_pattern,
    save_drift_analysis,
    save_routing_decision,
    search_knowledge_base,
    get_memory_stats,
)

__all__ = [
    # Memory v2 (EPIC G)
    "MemoryV2",
    "MemoryLayer",
    "MemoryScope",
    "MemoryEntry",
    "ShortTermMemory",
    "AgentInteractionMemory",
    "KnowledgeBaseMemory",
    "GovernanceMemory",
    "get_memory_v2",
    "reset_memory_v2",
    # Memory Integration (EPIC G)
    "save_flow_state",
    "restore_flow_state",
    "clear_flow_state",
    "save_debate_result",
    "search_past_debates",
    "save_safety_pattern",
    "save_drift_analysis",
    "save_routing_decision",
    "search_knowledge_base",
    "get_memory_stats",
]
