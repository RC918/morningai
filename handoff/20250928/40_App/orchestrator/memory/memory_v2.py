"""
Memory v2 - 4-Layer Memory System

EPIC G: Memory v2 (Blueprint Section 5.1)

This module implements the 4-layer memory architecture for MorningAI:

1. Short-Term Memory (即時任務記憶)
   - Current task context and working state
   - Redis-based for fast access
   - TTL-based expiration

2. Agent Interaction Memory (代理互動記憶)
   - Cross-agent communication history
   - Debate context and decisions
   - Redis-based with longer TTL

3. Knowledge Base (長期知識記憶)
   - Persistent knowledge from past tasks
   - Vector similarity search via pgvector
   - Error-fix pairs and learned patterns

4. Governance Memory (治理記憶)
   - Safety/compliance patterns
   - Drift analysis history
   - Routing decisions and outcomes

Use Cases (from Blueprint):
- Flow v3 recovery capability
- Planner v3 long-term planning
- Debate context preservation
- Drift analysis
- Safety/Compliance pattern tracking

Dependencies:
- Redis for short-term and interaction memory
- Supabase/pgvector for knowledge base
- PostgreSQL for governance memory
"""

import json
import logging
import threading
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class MemoryLayer(Enum):
    """Memory layer identifiers"""
    SHORT_TERM = "short_term"
    AGENT_INTERACTION = "agent_interaction"
    KNOWLEDGE_BASE = "knowledge_base"
    GOVERNANCE = "governance"


class MemoryScope(Enum):
    """Memory scope for filtering"""
    TASK = "task"           # Single task context
    SESSION = "session"     # User session
    AGENT = "agent"         # Specific agent
    WORKFLOW = "workflow"   # Workflow/trace
    GLOBAL = "global"       # System-wide


@dataclass
class MemoryEntry:
    """
    Universal memory entry structure.

    All memory layers use this common structure for consistency.
    """
    key: str
    content: str
    layer: MemoryLayer
    scope: MemoryScope
    metadata: Dict[str, Any] = field(default_factory=dict)
    embedding: Optional[List[float]] = None
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: Optional[str] = None
    expires_at: Optional[str] = None
    trace_id: Optional[str] = None
    agent_id: Optional[str] = None
    similarity: Optional[float] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage"""
        return {
            "key": self.key,
            "content": self.content,
            "layer": self.layer.value,
            "scope": self.scope.value,
            "metadata": self.metadata,
            "embedding": self.embedding,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "expires_at": self.expires_at,
            "trace_id": self.trace_id,
            "agent_id": self.agent_id,
            "similarity": self.similarity,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MemoryEntry":
        """Create from dictionary"""
        return cls(
            key=data.get("key", ""),
            content=data.get("content", ""),
            layer=MemoryLayer(data.get("layer", "short_term")),
            scope=MemoryScope(data.get("scope", "task")),
            metadata=data.get("metadata", {}),
            embedding=data.get("embedding"),
            created_at=data.get("created_at", datetime.now(timezone.utc).isoformat()),
            updated_at=data.get("updated_at"),
            expires_at=data.get("expires_at"),
            trace_id=data.get("trace_id"),
            agent_id=data.get("agent_id"),
            similarity=data.get("similarity"),
        )


class BaseMemoryStore(ABC):
    """
    Abstract base class for memory stores.

    Each memory layer implements this interface.
    """

    @abstractmethod
    def save(self, entry: MemoryEntry) -> bool:
        """Save a memory entry"""
        pass

    @abstractmethod
    def get(self, key: str) -> Optional[MemoryEntry]:
        """Get a memory entry by key"""
        pass

    @abstractmethod
    def search(
        self,
        query: str,
        limit: int = 10,
        scope: Optional[MemoryScope] = None,
        trace_id: Optional[str] = None,
    ) -> List[MemoryEntry]:
        """Search for relevant memories"""
        pass

    @abstractmethod
    def delete(self, key: str) -> bool:
        """Delete a memory entry"""
        pass

    @abstractmethod
    def clear(
        self,
        scope: Optional[MemoryScope] = None,
        trace_id: Optional[str] = None,
    ) -> int:
        """Clear memories matching criteria, returns count deleted"""
        pass


# =============================================================================
# Layer 1: Short-Term Memory (Redis-based)
# =============================================================================

class ShortTermMemory(BaseMemoryStore):
    """
    Short-Term Memory Layer (即時任務記憶)

    Stores current task context and working state.
    Uses Redis for fast access with TTL-based expiration.

    Default TTL: 1 hour (3600 seconds)
    """

    DEFAULT_TTL = 3600  # 1 hour
    KEY_PREFIX = "memory:short_term"

    def __init__(
        self,
        redis_client: Optional[Any] = None,
        ttl: int = DEFAULT_TTL,
    ):
        self.redis_client = redis_client
        self.ttl = ttl
        self._local_cache: Dict[str, MemoryEntry] = {}
        self._lock = threading.Lock()

    def _get_redis_key(self, key: str) -> str:
        """Generate Redis key with prefix"""
        return f"{self.KEY_PREFIX}:{key}"

    def save(self, entry: MemoryEntry) -> bool:
        """Save to short-term memory"""
        try:
            entry.layer = MemoryLayer.SHORT_TERM
            entry.updated_at = datetime.now(timezone.utc).isoformat()

            # Save to Redis if available
            if self.redis_client:
                redis_key = self._get_redis_key(entry.key)
                self.redis_client.setex(
                    redis_key,
                    self.ttl,
                    json.dumps(entry.to_dict()),
                )
                logger.debug(f"[Memory:ShortTerm] Saved to Redis: {entry.key}")
            else:
                # Fallback to local cache
                with self._lock:
                    self._local_cache[entry.key] = entry
                logger.debug(f"[Memory:ShortTerm] Saved to local cache: {entry.key}")

            return True

        except Exception as e:
            logger.warning(f"[Memory:ShortTerm] Failed to save: {e}")
            return False

    def get(self, key: str) -> Optional[MemoryEntry]:
        """Get from short-term memory"""
        try:
            if self.redis_client:
                redis_key = self._get_redis_key(key)
                data = self.redis_client.get(redis_key)
                if data:
                    return MemoryEntry.from_dict(json.loads(data))
            else:
                with self._lock:
                    return self._local_cache.get(key)

            return None

        except Exception as e:
            logger.warning(f"[Memory:ShortTerm] Failed to get: {e}")
            return None

    def search(
        self,
        query: str,
        limit: int = 10,
        scope: Optional[MemoryScope] = None,
        trace_id: Optional[str] = None,
    ) -> List[MemoryEntry]:
        """Search short-term memory (simple key prefix match)"""
        try:
            results = []

            if self.redis_client:
                # Scan Redis keys matching pattern
                pattern = f"{self.KEY_PREFIX}:*{query}*"
                cursor = 0
                while True:
                    cursor, keys = self.redis_client.scan(
                        cursor=cursor,
                        match=pattern,
                        count=100,
                    )
                    for key in keys:
                        data = self.redis_client.get(key)
                        if data:
                            entry = MemoryEntry.from_dict(json.loads(data))
                            if self._matches_filter(entry, scope, trace_id):
                                results.append(entry)
                                if len(results) >= limit:
                                    return results
                    if cursor == 0:
                        break
            else:
                with self._lock:
                    for key, entry in self._local_cache.items():
                        if query.lower() in key.lower() or query.lower() in entry.content.lower():
                            if self._matches_filter(entry, scope, trace_id):
                                results.append(entry)
                                if len(results) >= limit:
                                    break

            return results[:limit]

        except Exception as e:
            logger.warning(f"[Memory:ShortTerm] Failed to search: {e}")
            return []

    def delete(self, key: str) -> bool:
        """Delete from short-term memory"""
        try:
            if self.redis_client:
                redis_key = self._get_redis_key(key)
                self.redis_client.delete(redis_key)
            else:
                with self._lock:
                    self._local_cache.pop(key, None)

            logger.debug(f"[Memory:ShortTerm] Deleted: {key}")
            return True

        except Exception as e:
            logger.warning(f"[Memory:ShortTerm] Failed to delete: {e}")
            return False

    def clear(
        self,
        scope: Optional[MemoryScope] = None,
        trace_id: Optional[str] = None,
    ) -> int:
        """Clear short-term memories.

        For safety, requires at least one filter (scope or trace_id).
        This ensures consistent behavior with database-backed layers.
        """
        try:
            # Require at least one filter for safety (consistent with database layers)
            if scope is None and trace_id is None:
                logger.warning(
                    "[Memory:ShortTerm] Clear all requires explicit scope or trace_id filter"
                )
                return 0

            count = 0

            if self.redis_client:
                pattern = f"{self.KEY_PREFIX}:*"
                cursor = 0
                keys_to_delete = []
                while True:
                    cursor, keys = self.redis_client.scan(
                        cursor=cursor,
                        match=pattern,
                        count=100,
                    )
                    for key in keys:
                        data = self.redis_client.get(key)
                        if data:
                            entry = MemoryEntry.from_dict(json.loads(data))
                            if self._matches_filter(entry, scope, trace_id):
                                keys_to_delete.append(key)
                    if cursor == 0:
                        break

                if keys_to_delete:
                    count = self.redis_client.delete(*keys_to_delete)
            else:
                with self._lock:
                    keys_to_delete = [
                        k for k, v in self._local_cache.items()
                        if self._matches_filter(v, scope, trace_id)
                    ]
                    for k in keys_to_delete:
                        del self._local_cache[k]
                    count = len(keys_to_delete)

            logger.info(f"[Memory:ShortTerm] Cleared {count} entries")
            return count

        except Exception as e:
            logger.warning(f"[Memory:ShortTerm] Failed to clear: {e}")
            return 0

    def _matches_filter(
        self,
        entry: MemoryEntry,
        scope: Optional[MemoryScope],
        trace_id: Optional[str],
    ) -> bool:
        """Check if entry matches filter criteria"""
        if scope and entry.scope != scope:
            return False
        if trace_id and entry.trace_id != trace_id:
            return False
        return True


# =============================================================================
# Layer 2: Agent Interaction Memory (Redis-based)
# =============================================================================

class AgentInteractionMemory(BaseMemoryStore):
    """
    Agent Interaction Memory Layer (代理互動記憶)

    Stores cross-agent communication history and debate context.
    Uses Redis with longer TTL than short-term memory.

    Default TTL: 24 hours (86400 seconds)
    """

    DEFAULT_TTL = 86400  # 24 hours
    KEY_PREFIX = "memory:agent_interaction"

    def __init__(
        self,
        redis_client: Optional[Any] = None,
        ttl: int = DEFAULT_TTL,
    ):
        self.redis_client = redis_client
        self.ttl = ttl
        self._local_cache: Dict[str, MemoryEntry] = {}
        self._lock = threading.Lock()

    def _get_redis_key(self, key: str) -> str:
        """Generate Redis key with prefix"""
        return f"{self.KEY_PREFIX}:{key}"

    def save(self, entry: MemoryEntry) -> bool:
        """Save agent interaction"""
        try:
            entry.layer = MemoryLayer.AGENT_INTERACTION
            entry.updated_at = datetime.now(timezone.utc).isoformat()

            if self.redis_client:
                redis_key = self._get_redis_key(entry.key)
                self.redis_client.setex(
                    redis_key,
                    self.ttl,
                    json.dumps(entry.to_dict()),
                )
                logger.debug(f"[Memory:AgentInteraction] Saved to Redis: {entry.key}")
            else:
                with self._lock:
                    self._local_cache[entry.key] = entry
                logger.debug(f"[Memory:AgentInteraction] Saved to local cache: {entry.key}")

            return True

        except Exception as e:
            logger.warning(f"[Memory:AgentInteraction] Failed to save: {e}")
            return False

    def get(self, key: str) -> Optional[MemoryEntry]:
        """Get agent interaction"""
        try:
            if self.redis_client:
                redis_key = self._get_redis_key(key)
                data = self.redis_client.get(redis_key)
                if data:
                    return MemoryEntry.from_dict(json.loads(data))
            else:
                with self._lock:
                    return self._local_cache.get(key)

            return None

        except Exception as e:
            logger.warning(f"[Memory:AgentInteraction] Failed to get: {e}")
            return None

    def search(
        self,
        query: str,
        limit: int = 10,
        scope: Optional[MemoryScope] = None,
        trace_id: Optional[str] = None,
    ) -> List[MemoryEntry]:
        """Search agent interactions"""
        try:
            results = []

            if self.redis_client:
                pattern = f"{self.KEY_PREFIX}:*"
                cursor = 0
                while True:
                    cursor, keys = self.redis_client.scan(
                        cursor=cursor,
                        match=pattern,
                        count=100,
                    )
                    for key in keys:
                        data = self.redis_client.get(key)
                        if data:
                            entry = MemoryEntry.from_dict(json.loads(data))
                            if query.lower() in entry.content.lower():
                                if self._matches_filter(entry, scope, trace_id):
                                    results.append(entry)
                                    if len(results) >= limit:
                                        return results
                    if cursor == 0:
                        break
            else:
                with self._lock:
                    for entry in self._local_cache.values():
                        if query.lower() in entry.content.lower():
                            if self._matches_filter(entry, scope, trace_id):
                                results.append(entry)
                                if len(results) >= limit:
                                    break

            return results[:limit]

        except Exception as e:
            logger.warning(f"[Memory:AgentInteraction] Failed to search: {e}")
            return []

    def delete(self, key: str) -> bool:
        """Delete agent interaction"""
        try:
            if self.redis_client:
                redis_key = self._get_redis_key(key)
                self.redis_client.delete(redis_key)
            else:
                with self._lock:
                    self._local_cache.pop(key, None)

            logger.debug(f"[Memory:AgentInteraction] Deleted: {key}")
            return True

        except Exception as e:
            logger.warning(f"[Memory:AgentInteraction] Failed to delete: {e}")
            return False

    def clear(
        self,
        scope: Optional[MemoryScope] = None,
        trace_id: Optional[str] = None,
    ) -> int:
        """Clear agent interactions.

        For safety, requires at least one filter (scope or trace_id).
        This ensures consistent behavior with database-backed layers.
        """
        try:
            # Require at least one filter for safety (consistent with database layers)
            if scope is None and trace_id is None:
                logger.warning(
                    "[Memory:AgentInteraction] Clear all requires explicit scope or trace_id filter"
                )
                return 0

            count = 0

            if self.redis_client:
                pattern = f"{self.KEY_PREFIX}:*"
                cursor = 0
                keys_to_delete = []
                while True:
                    cursor, keys = self.redis_client.scan(
                        cursor=cursor,
                        match=pattern,
                        count=100,
                    )
                    for key in keys:
                        data = self.redis_client.get(key)
                        if data:
                            entry = MemoryEntry.from_dict(json.loads(data))
                            if self._matches_filter(entry, scope, trace_id):
                                keys_to_delete.append(key)
                    if cursor == 0:
                        break

                if keys_to_delete:
                    count = self.redis_client.delete(*keys_to_delete)
            else:
                with self._lock:
                    keys_to_delete = [
                        k for k, v in self._local_cache.items()
                        if self._matches_filter(v, scope, trace_id)
                    ]
                    for k in keys_to_delete:
                        del self._local_cache[k]
                    count = len(keys_to_delete)

            logger.info(f"[Memory:AgentInteraction] Cleared {count} entries")
            return count

        except Exception as e:
            logger.warning(f"[Memory:AgentInteraction] Failed to clear: {e}")
            return 0

    def _matches_filter(
        self,
        entry: MemoryEntry,
        scope: Optional[MemoryScope],
        trace_id: Optional[str],
    ) -> bool:
        """Check if entry matches filter criteria"""
        if scope and entry.scope != scope:
            return False
        if trace_id and entry.trace_id != trace_id:
            return False
        return True

    def save_debate_context(
        self,
        debate_id: str,
        left_agent: str,
        right_agent: str,
        topic: str,
        arguments: List[Dict[str, Any]],
        decision: Optional[str] = None,
        trace_id: Optional[str] = None,
    ) -> bool:
        """
        Save debate context for Debate Engine v2.

        Args:
            debate_id: Unique debate identifier
            left_agent: Left agent ID
            right_agent: Right agent ID
            topic: Debate topic
            arguments: List of argument dictionaries
            decision: Final decision (if reached)
            trace_id: Workflow trace ID

        Returns:
            True if saved successfully
        """
        content = f"Debate: {topic}\nLeft: {left_agent}\nRight: {right_agent}"
        if decision:
            content += f"\nDecision: {decision}"

        entry = MemoryEntry(
            key=f"debate:{debate_id}",
            content=content,
            layer=MemoryLayer.AGENT_INTERACTION,
            scope=MemoryScope.WORKFLOW,
            metadata={
                "debate_id": debate_id,
                "left_agent": left_agent,
                "right_agent": right_agent,
                "topic": topic,
                "arguments": arguments,
                "decision": decision,
            },
            trace_id=trace_id,
        )

        return self.save(entry)


# =============================================================================
# Layer 3: Knowledge Base (pgvector-based)
# =============================================================================

class KnowledgeBaseMemory(BaseMemoryStore):
    """
    Knowledge Base Memory Layer (長期知識記憶)

    Stores persistent knowledge from past tasks.
    Uses pgvector for vector similarity search.

    Integrates with existing pgvector_store.py and error_fix_pairs.py.
    """

    TABLE = "memory_v2_knowledge"
    DEFAULT_SIMILARITY_THRESHOLD = 0.7

    def __init__(self):
        self._supabase_client = None
        self._client_init_failed = False

    def _get_client(self):
        """Get Supabase client lazily with failure caching"""
        if self._supabase_client is not None:
            return self._supabase_client

        # Skip repeated initialization attempts if previous attempt failed
        if self._client_init_failed:
            return None

        try:
            from supabase import create_client
            from common.config.settings import settings

            if settings.supabase_url and settings.supabase_service_role_key:
                self._supabase_client = create_client(
                    settings.supabase_url,
                    settings.supabase_service_role_key,
                )
            else:
                self._client_init_failed = True
                logger.debug("[Memory:KnowledgeBase] Supabase credentials not configured")
        except Exception as e:
            self._client_init_failed = True
            logger.debug(f"[Memory:KnowledgeBase] Supabase not available: {e}")

        return self._supabase_client

    def _embed(self, text: str) -> Optional[List[float]]:
        """Generate embedding for text"""
        try:
            from llm.embedding_client import get_embedding_client
            client = get_embedding_client()
            return client.embed(text)
        except Exception as e:
            logger.debug(f"[Memory:KnowledgeBase] Embedding failed: {e}")
            return None

    def save(self, entry: MemoryEntry) -> bool:
        """Save to knowledge base"""
        try:
            client = self._get_client()
            if client is None:
                logger.debug("[Memory:KnowledgeBase] Supabase not available")
                return False

            entry.layer = MemoryLayer.KNOWLEDGE_BASE
            entry.updated_at = datetime.now(timezone.utc).isoformat()

            # Generate embedding if not provided
            if entry.embedding is None:
                entry.embedding = self._embed(entry.content)

            record = {
                "key": entry.key,
                "content": entry.content,
                "scope": entry.scope.value,
                "metadata": json.dumps(entry.metadata),
                "embedding": entry.embedding,
                "trace_id": entry.trace_id,
                "agent_id": entry.agent_id,
                "created_at": entry.created_at,
                "updated_at": entry.updated_at,
            }

            client.table(self.TABLE).upsert(record, on_conflict="key").execute()
            logger.debug(f"[Memory:KnowledgeBase] Saved: {entry.key}")
            return True

        except Exception as e:
            logger.warning(f"[Memory:KnowledgeBase] Failed to save: {e}")
            return False

    def get(self, key: str) -> Optional[MemoryEntry]:
        """Get from knowledge base"""
        try:
            client = self._get_client()
            if client is None:
                return None

            result = client.table(self.TABLE).select("*").eq("key", key).limit(1).execute()

            if result.data and len(result.data) > 0:
                row = result.data[0]
                return self._row_to_entry(row)

            return None

        except Exception as e:
            logger.warning(f"[Memory:KnowledgeBase] Failed to get: {e}")
            return None

    def search(
        self,
        query: str,
        limit: int = 10,
        scope: Optional[MemoryScope] = None,
        trace_id: Optional[str] = None,
    ) -> List[MemoryEntry]:
        """Search knowledge base using vector similarity"""
        try:
            client = self._get_client()
            if client is None:
                return []

            # Generate query embedding
            query_embedding = self._embed(query)
            if query_embedding is None:
                # Fallback to text search
                return self._text_search(query, limit, scope, trace_id)

            # Use vector similarity search
            result = client.rpc(
                "match_memory_v2_knowledge",
                {
                    "query_embedding": query_embedding,
                    "match_threshold": self.DEFAULT_SIMILARITY_THRESHOLD,
                    "match_count": limit,
                    "scope_filter": scope.value if scope else None,
                    "trace_id_filter": trace_id,
                }
            ).execute()

            entries = []
            for row in result.data or []:
                entry = self._row_to_entry(row)
                entries.append(entry)

            logger.debug(f"[Memory:KnowledgeBase] Found {len(entries)} matches")
            return entries

        except Exception as e:
            logger.warning(f"[Memory:KnowledgeBase] Search failed: {e}")
            return self._text_search(query, limit, scope, trace_id)

    def _text_search(
        self,
        query: str,
        limit: int,
        scope: Optional[MemoryScope],
        trace_id: Optional[str],
    ) -> List[MemoryEntry]:
        """Fallback text search when vector search unavailable"""
        try:
            client = self._get_client()
            if client is None:
                return []

            q = client.table(self.TABLE).select("*")

            if scope:
                q = q.eq("scope", scope.value)
            if trace_id:
                q = q.eq("trace_id", trace_id)

            q = q.ilike("content", f"%{query}%").limit(limit)
            result = q.execute()

            return [self._row_to_entry(row) for row in result.data or []]

        except Exception as e:
            logger.warning(f"[Memory:KnowledgeBase] Text search failed: {e}")
            return []

    def delete(self, key: str) -> bool:
        """Delete from knowledge base"""
        try:
            client = self._get_client()
            if client is None:
                return False

            client.table(self.TABLE).delete().eq("key", key).execute()
            logger.debug(f"[Memory:KnowledgeBase] Deleted: {key}")
            return True

        except Exception as e:
            logger.warning(f"[Memory:KnowledgeBase] Failed to delete: {e}")
            return False

    def clear(
        self,
        scope: Optional[MemoryScope] = None,
        trace_id: Optional[str] = None,
    ) -> int:
        """Clear knowledge base entries"""
        try:
            client = self._get_client()
            if client is None:
                return 0

            q = client.table(self.TABLE).delete()

            if scope:
                q = q.eq("scope", scope.value)
            if trace_id:
                q = q.eq("trace_id", trace_id)

            # If no filters, this would delete everything - require explicit confirmation
            if scope is None and trace_id is None:
                logger.warning("[Memory:KnowledgeBase] Clear all requires explicit scope or trace_id")
                return 0

            result = q.execute()
            count = len(result.data) if result.data else 0
            logger.info(f"[Memory:KnowledgeBase] Cleared {count} entries")
            return count

        except Exception as e:
            logger.warning(f"[Memory:KnowledgeBase] Failed to clear: {e}")
            return 0

    def _row_to_entry(self, row: Dict[str, Any]) -> MemoryEntry:
        """Convert database row to MemoryEntry"""
        metadata = row.get("metadata", {})
        if isinstance(metadata, str):
            try:
                metadata = json.loads(metadata)
            except (json.JSONDecodeError, TypeError):
                metadata = {}

        return MemoryEntry(
            key=row.get("key", ""),
            content=row.get("content", ""),
            layer=MemoryLayer.KNOWLEDGE_BASE,
            scope=MemoryScope(row.get("scope", "global")),
            metadata=metadata,
            embedding=row.get("embedding"),
            created_at=row.get("created_at", ""),
            updated_at=row.get("updated_at"),
            trace_id=row.get("trace_id"),
            agent_id=row.get("agent_id"),
            similarity=row.get("similarity"),
        )


# =============================================================================
# Layer 4: Governance Memory (PostgreSQL-based)
# =============================================================================

class GovernanceMemory(BaseMemoryStore):
    """
    Governance Memory Layer (治理記憶)

    Stores safety/compliance patterns, drift analysis, and routing decisions.
    Uses PostgreSQL for structured queries and audit trails.

    Integrates with existing failure_memory.py.
    """

    TABLE = "memory_v2_governance"

    def __init__(self):
        self._supabase_client = None
        self._client_init_failed = False

    def _get_client(self):
        """Get Supabase client lazily with failure caching"""
        if self._supabase_client is not None:
            return self._supabase_client

        # Skip repeated initialization attempts if previous attempt failed
        if self._client_init_failed:
            return None

        try:
            from supabase import create_client
            from common.config.settings import settings

            if settings.supabase_url and settings.supabase_service_role_key:
                self._supabase_client = create_client(
                    settings.supabase_url,
                    settings.supabase_service_role_key,
                )
            else:
                self._client_init_failed = True
                logger.debug("[Memory:Governance] Supabase credentials not configured")
        except Exception as e:
            self._client_init_failed = True
            logger.debug(f"[Memory:Governance] Supabase not available: {e}")

        return self._supabase_client

    def save(self, entry: MemoryEntry) -> bool:
        """Save governance memory"""
        try:
            client = self._get_client()
            if client is None:
                logger.debug("[Memory:Governance] Supabase not available")
                return False

            entry.layer = MemoryLayer.GOVERNANCE
            entry.updated_at = datetime.now(timezone.utc).isoformat()

            record = {
                "key": entry.key,
                "content": entry.content,
                "scope": entry.scope.value,
                "metadata": json.dumps(entry.metadata),
                "trace_id": entry.trace_id,
                "agent_id": entry.agent_id,
                "created_at": entry.created_at,
                "updated_at": entry.updated_at,
            }

            client.table(self.TABLE).upsert(record, on_conflict="key").execute()
            logger.debug(f"[Memory:Governance] Saved: {entry.key}")
            return True

        except Exception as e:
            logger.warning(f"[Memory:Governance] Failed to save: {e}")
            return False

    def get(self, key: str) -> Optional[MemoryEntry]:
        """Get governance memory"""
        try:
            client = self._get_client()
            if client is None:
                return None

            result = client.table(self.TABLE).select("*").eq("key", key).limit(1).execute()

            if result.data and len(result.data) > 0:
                return self._row_to_entry(result.data[0])

            return None

        except Exception as e:
            logger.warning(f"[Memory:Governance] Failed to get: {e}")
            return None

    def search(
        self,
        query: str,
        limit: int = 10,
        scope: Optional[MemoryScope] = None,
        trace_id: Optional[str] = None,
    ) -> List[MemoryEntry]:
        """Search governance memory"""
        try:
            client = self._get_client()
            if client is None:
                return []

            q = client.table(self.TABLE).select("*")

            if scope:
                q = q.eq("scope", scope.value)
            if trace_id:
                q = q.eq("trace_id", trace_id)

            q = q.ilike("content", f"%{query}%").order("created_at", desc=True).limit(limit)
            result = q.execute()

            return [self._row_to_entry(row) for row in result.data or []]

        except Exception as e:
            logger.warning(f"[Memory:Governance] Search failed: {e}")
            return []

    def delete(self, key: str) -> bool:
        """Delete governance memory"""
        try:
            client = self._get_client()
            if client is None:
                return False

            client.table(self.TABLE).delete().eq("key", key).execute()
            logger.debug(f"[Memory:Governance] Deleted: {key}")
            return True

        except Exception as e:
            logger.warning(f"[Memory:Governance] Failed to delete: {e}")
            return False

    def clear(
        self,
        scope: Optional[MemoryScope] = None,
        trace_id: Optional[str] = None,
    ) -> int:
        """Clear governance memories"""
        try:
            client = self._get_client()
            if client is None:
                return 0

            q = client.table(self.TABLE).delete()

            if scope:
                q = q.eq("scope", scope.value)
            if trace_id:
                q = q.eq("trace_id", trace_id)

            if scope is None and trace_id is None:
                logger.warning("[Memory:Governance] Clear all requires explicit scope or trace_id")
                return 0

            result = q.execute()
            count = len(result.data) if result.data else 0
            logger.info(f"[Memory:Governance] Cleared {count} entries")
            return count

        except Exception as e:
            logger.warning(f"[Memory:Governance] Failed to clear: {e}")
            return 0

    def _row_to_entry(self, row: Dict[str, Any]) -> MemoryEntry:
        """Convert database row to MemoryEntry"""
        metadata = row.get("metadata", {})
        if isinstance(metadata, str):
            try:
                metadata = json.loads(metadata)
            except (json.JSONDecodeError, TypeError):
                metadata = {}

        return MemoryEntry(
            key=row.get("key", ""),
            content=row.get("content", ""),
            layer=MemoryLayer.GOVERNANCE,
            scope=MemoryScope(row.get("scope", "global")),
            metadata=metadata,
            created_at=row.get("created_at", ""),
            updated_at=row.get("updated_at"),
            trace_id=row.get("trace_id"),
            agent_id=row.get("agent_id"),
        )

    def save_safety_pattern(
        self,
        pattern_id: str,
        pattern_type: str,
        description: str,
        examples: List[str],
        action: str,
        trace_id: Optional[str] = None,
    ) -> bool:
        """
        Save a safety/compliance pattern.

        Args:
            pattern_id: Unique pattern identifier
            pattern_type: Type of pattern (e.g., "content_safety", "compliance")
            description: Pattern description
            examples: Example matches
            action: Action to take when matched (e.g., "block", "flag", "allow")
            trace_id: Workflow trace ID

        Returns:
            True if saved successfully
        """
        entry = MemoryEntry(
            key=f"safety_pattern:{pattern_id}",
            content=f"{pattern_type}: {description}",
            layer=MemoryLayer.GOVERNANCE,
            scope=MemoryScope.GLOBAL,
            metadata={
                "pattern_id": pattern_id,
                "pattern_type": pattern_type,
                "description": description,
                "examples": examples,
                "action": action,
            },
            trace_id=trace_id,
        )

        return self.save(entry)

    def save_drift_analysis(
        self,
        provider: str,
        drift_type: str,
        severity: str,
        details: Dict[str, Any],
        trace_id: Optional[str] = None,
    ) -> bool:
        """
        Save drift analysis result.

        Args:
            provider: Provider name
            drift_type: Type of drift detected
            severity: Drift severity
            details: Drift details
            trace_id: Workflow trace ID

        Returns:
            True if saved successfully
        """
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
        entry = MemoryEntry(
            key=f"drift:{provider}:{timestamp}",
            content=f"Drift detected: {provider} - {drift_type} ({severity})",
            layer=MemoryLayer.GOVERNANCE,
            scope=MemoryScope.GLOBAL,
            metadata={
                "provider": provider,
                "drift_type": drift_type,
                "severity": severity,
                "details": details,
            },
            trace_id=trace_id,
        )

        return self.save(entry)

    def save_routing_decision(
        self,
        decision_id: str,
        task_type: str,
        selected_provider: str,
        selected_model: str,
        reason: str,
        alternatives: List[Dict[str, Any]],
        trace_id: Optional[str] = None,
    ) -> bool:
        """
        Save routing decision for analysis.

        Args:
            decision_id: Unique decision identifier
            task_type: Type of task
            selected_provider: Selected provider
            selected_model: Selected model
            reason: Reason for selection
            alternatives: Alternative options considered
            trace_id: Workflow trace ID

        Returns:
            True if saved successfully
        """
        entry = MemoryEntry(
            key=f"routing:{decision_id}",
            content=f"Routing: {task_type} -> {selected_provider}/{selected_model}",
            layer=MemoryLayer.GOVERNANCE,
            scope=MemoryScope.WORKFLOW,
            metadata={
                "decision_id": decision_id,
                "task_type": task_type,
                "selected_provider": selected_provider,
                "selected_model": selected_model,
                "reason": reason,
                "alternatives": alternatives,
            },
            trace_id=trace_id,
        )

        return self.save(entry)


# =============================================================================
# Unified Memory v2 Interface
# =============================================================================

class MemoryV2:
    """
    Unified Memory v2 Interface

    EPIC G: Memory v2 (Blueprint Section 5.1)

    Provides a unified interface to all 4 memory layers:
    1. Short-Term Memory
    2. Agent Interaction Memory
    3. Knowledge Base
    4. Governance Memory

    Usage:
        memory = get_memory_v2()

        # Save to specific layer
        memory.save(entry, layer=MemoryLayer.SHORT_TERM)

        # Search across layers
        results = memory.search("query", layers=[MemoryLayer.KNOWLEDGE_BASE])

        # Access specific layer
        memory.short_term.save(entry)
        memory.knowledge_base.search("query")
    """

    def __init__(
        self,
        redis_client: Optional[Any] = None,
        enabled: bool = True,
    ):
        self.enabled = enabled
        self.redis_client = redis_client

        # Initialize all layers
        self.short_term = ShortTermMemory(redis_client=redis_client)
        self.agent_interaction = AgentInteractionMemory(redis_client=redis_client)
        self.knowledge_base = KnowledgeBaseMemory()
        self.governance = GovernanceMemory()

        self._layers: Dict[MemoryLayer, BaseMemoryStore] = {
            MemoryLayer.SHORT_TERM: self.short_term,
            MemoryLayer.AGENT_INTERACTION: self.agent_interaction,
            MemoryLayer.KNOWLEDGE_BASE: self.knowledge_base,
            MemoryLayer.GOVERNANCE: self.governance,
        }

        logger.info("[MemoryV2] Initialized 4-layer memory system")

    def save(
        self,
        entry: MemoryEntry,
        layer: Optional[MemoryLayer] = None,
    ) -> bool:
        """
        Save memory entry to specified layer.

        Args:
            entry: Memory entry to save
            layer: Target layer (uses entry.layer if not specified)

        Returns:
            True if saved successfully
        """
        if not self.enabled:
            return False

        target_layer = layer or entry.layer
        store = self._layers.get(target_layer)

        if store is None:
            logger.warning(f"[MemoryV2] Unknown layer: {target_layer}")
            return False

        return store.save(entry)

    def get(
        self,
        key: str,
        layer: MemoryLayer,
    ) -> Optional[MemoryEntry]:
        """
        Get memory entry from specified layer.

        Args:
            key: Entry key
            layer: Target layer

        Returns:
            MemoryEntry if found, None otherwise
        """
        if not self.enabled:
            return None

        store = self._layers.get(layer)
        if store is None:
            return None

        return store.get(key)

    def search(
        self,
        query: str,
        layers: Optional[List[MemoryLayer]] = None,
        limit: int = 10,
        scope: Optional[MemoryScope] = None,
        trace_id: Optional[str] = None,
    ) -> List[MemoryEntry]:
        """
        Search across memory layers.

        Args:
            query: Search query
            layers: Layers to search (all if not specified)
            limit: Maximum results per layer
            scope: Filter by scope
            trace_id: Filter by trace ID

        Returns:
            List of matching MemoryEntry objects
        """
        if not self.enabled:
            return []

        target_layers = layers or list(self._layers.keys())
        results = []

        for layer in target_layers:
            store = self._layers.get(layer)
            if store:
                layer_results = store.search(
                    query=query,
                    limit=limit,
                    scope=scope,
                    trace_id=trace_id,
                )
                results.extend(layer_results)

        return results

    def delete(
        self,
        key: str,
        layer: MemoryLayer,
    ) -> bool:
        """
        Delete memory entry from specified layer.

        Args:
            key: Entry key
            layer: Target layer

        Returns:
            True if deleted successfully
        """
        if not self.enabled:
            return False

        store = self._layers.get(layer)
        if store is None:
            return False

        return store.delete(key)

    def clear(
        self,
        layers: Optional[List[MemoryLayer]] = None,
        scope: Optional[MemoryScope] = None,
        trace_id: Optional[str] = None,
    ) -> Dict[MemoryLayer, int]:
        """
        Clear memories from specified layers.

        Args:
            layers: Layers to clear (all if not specified)
            scope: Filter by scope
            trace_id: Filter by trace ID

        Returns:
            Dictionary of layer -> count cleared
        """
        if not self.enabled:
            return {}

        target_layers = layers or list(self._layers.keys())
        results = {}

        for layer in target_layers:
            store = self._layers.get(layer)
            if store:
                count = store.clear(scope=scope, trace_id=trace_id)
                results[layer] = count

        return results

    def get_stats(self) -> Dict[str, Any]:
        """
        Get memory system statistics.

        Returns:
            Dictionary with statistics for each layer
        """
        return {
            "enabled": self.enabled,
            "layers": {
                "short_term": {"type": "redis", "ttl": ShortTermMemory.DEFAULT_TTL},
                "agent_interaction": {"type": "redis", "ttl": AgentInteractionMemory.DEFAULT_TTL},
                "knowledge_base": {"type": "pgvector"},
                "governance": {"type": "postgresql"},
            },
        }


# =============================================================================
# Global Singleton
# =============================================================================

_memory_v2: Optional[MemoryV2] = None
_memory_v2_lock = threading.Lock()


def get_memory_v2(
    redis_client: Optional[Any] = None,
) -> Optional[MemoryV2]:
    """
    Get or create global MemoryV2 instance.

    EPIC G: Memory v2 (Blueprint Section 5.1)

    Args:
        redis_client: Optional Redis client for short-term memory

    Returns:
        MemoryV2 instance or None if disabled
    """
    global _memory_v2

    if _memory_v2 is not None:
        if redis_client is not None:
            logger.warning(
                "[MemoryV2] redis_client parameter ignored - singleton already initialized. "
                "Call reset_memory_v2() first if you need to reinitialize with a different client."
            )
        return _memory_v2

    with _memory_v2_lock:
        if _memory_v2 is not None:
            return _memory_v2

        try:
            import os

            enabled = os.getenv("MEMORY_V2_ENABLED", "true").lower() == "true"

            if not enabled:
                logger.debug("[MemoryV2] Memory v2 disabled")
                return None

            _memory_v2 = MemoryV2(
                redis_client=redis_client,
                enabled=enabled,
            )

            return _memory_v2

        except Exception as e:
            logger.warning(f"[MemoryV2] Failed to initialize: {e}")
            return None


def reset_memory_v2() -> None:
    """Reset the global MemoryV2 singleton (for testing)"""
    global _memory_v2
    with _memory_v2_lock:
        _memory_v2 = None
