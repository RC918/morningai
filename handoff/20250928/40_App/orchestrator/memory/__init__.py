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
]
