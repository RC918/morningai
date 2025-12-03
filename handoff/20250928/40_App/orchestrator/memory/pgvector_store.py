"""
PGVector Memory Store - Phase 2 Brain Layer

Provides vector similarity search for agent memory storage.

Features:
- True vector similarity search using cosine distance
- HNSW index support for fast queries
- Embedding generation using EmbeddingClient abstraction (#1812)
- Fallback to recent items when embeddings unavailable

Dependencies:
- Migration 023: memory table
- Migration 032: match_memory_by_similarity SQL function
"""

import logging
from typing import List, Dict, Any, Optional

from supabase import create_client
from common.config.settings import settings
from llm.embedding_client import get_embedding_client

logger = logging.getLogger(__name__)

SUPABASE_URL = settings.supabase_url
SUPABASE_SERVICE_ROLE_KEY = settings.supabase_service_role_key
TABLE = settings.memory_table or "memory"

DEFAULT_SIMILARITY_THRESHOLD = 0.7


def get_client():
    """Get Supabase client, creating it only when needed"""
    try:
        if SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY:
            return create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)
        else:
            logger.debug("[Memory] Supabase credentials not available")
            return None
    except Exception as e:
        logger.warning(f"[Memory] Failed to create Supabase client: {e}")
        return None


def embed(text: str) -> Optional[List[float]]:
    """
    Generate embedding vector for text using EmbeddingClient.

    Uses the EmbeddingClient abstraction layer (#1812) for
    provider-agnostic embedding generation.

    Args:
        text: Text to embed

    Returns:
        List of floats (1536 dimensions) or None if failed
    """
    embedding_client = get_embedding_client()
    return embedding_client.embed(text)


def save_text(key: str, text: str) -> bool:
    """
    Save text with embedding to memory table.

    Args:
        key: Unique key for the memory entry
        text: Text content to save

    Returns:
        True if saved successfully, False otherwise
    """
    try:
        client = get_client()
        if client is None:
            logger.debug("[Memory] Supabase client not available")
            return False
        vec = embed(text)
        client.table(TABLE).insert({
            "key": key,
            "text": text,
            "embedding": vec
        }).execute()
        logger.debug(f"[Memory] Saved text with key: {key}")
        return True
    except Exception as e:
        logger.warning(f"[Memory] Failed to save text: {e}")
        return False


def search_similar(
    query_text: str,
    limit: int = 5,
    threshold: float = DEFAULT_SIMILARITY_THRESHOLD,
    key_filter: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Search for similar memories using vector similarity.

    This function uses the match_memory_by_similarity SQL function
    to perform true cosine similarity search on embeddings.

    Args:
        query_text: Text to search for similar memories
        limit: Maximum number of results to return
        threshold: Minimum similarity score (0.0 to 1.0)
        key_filter: Optional key prefix filter

    Returns:
        List of memory records with similarity scores, sorted by similarity
    """
    try:
        client = get_client()
        if client is None:
            logger.debug("[Memory] Supabase client not available")
            return []

        query_embedding = embed(query_text)
        if query_embedding is None:
            logger.debug("[Memory] Failed to generate query embedding, falling back to recent")
            return recall_recent(limit)

        result = client.rpc(
            "match_memory_by_similarity",
            {
                "query_embedding": query_embedding,
                "match_threshold": threshold,
                "match_count": limit,
                "key_filter": key_filter
            }
        ).execute()

        memories = result.data or []
        logger.debug(f"[Memory] Found {len(memories)} similar memories")
        return memories

    except Exception as e:
        logger.warning(f"[Memory] Vector search failed, falling back to recent: {e}")
        return recall_recent(limit)


def recall_top(keywords: str, limit: int = 5) -> List[Dict[str, Any]]:
    """
    Recall top memories by similarity to keywords.

    This is the main entry point for memory recall. It attempts vector
    similarity search first, falling back to recent items if unavailable.

    Args:
        keywords: Search keywords/query text
        limit: Maximum number of results to return

    Returns:
        List of memory records, sorted by relevance
    """
    try:
        client = get_client()
        if client is None:
            logger.debug("[Memory] Supabase client not available")
            return []

        query_embedding = embed(keywords)
        if query_embedding is not None:
            try:
                result = client.rpc(
                    "match_memory_by_similarity",
                    {
                        "query_embedding": query_embedding,
                        "match_threshold": DEFAULT_SIMILARITY_THRESHOLD,
                        "match_count": limit,
                        "key_filter": None
                    }
                ).execute()

                if result.data:
                    logger.debug(f"[Memory] Vector search returned {len(result.data)} results")
                    return result.data
            except Exception as e:
                logger.debug(f"[Memory] Vector search RPC failed: {e}")

        logger.debug("[Memory] Falling back to recent items")
        return recall_recent(limit)

    except Exception as e:
        logger.warning(f"[Memory] Failed to recall memories: {e}")
        return []


def recall_recent(limit: int = 5) -> List[Dict[str, Any]]:
    """
    Recall most recent memories (fallback when vector search unavailable).

    Args:
        limit: Maximum number of results to return

    Returns:
        List of recent memory records, sorted by creation time (newest first)
    """
    try:
        client = get_client()
        if client is None:
            logger.debug("[Memory] Supabase client not available")
            return []

        res = client.table(TABLE).select("*").order(
            "id", desc=True
        ).limit(limit).execute()

        return res.data or []
    except Exception as e:
        logger.warning(f"[Memory] Failed to recall recent memories: {e}")
        return []


def search_by_key_prefix(
    prefix: str,
    limit: int = 10
) -> List[Dict[str, Any]]:
    """
    Search memories by key prefix.

    Args:
        prefix: Key prefix to filter by
        limit: Maximum number of results to return

    Returns:
        List of memory records matching the prefix
    """
    try:
        client = get_client()
        if client is None:
            logger.debug("[Memory] Supabase client not available")
            return []

        res = client.table(TABLE).select("*").like(
            "key", f"{prefix}%"
        ).order("id", desc=True).limit(limit).execute()

        return res.data or []
    except Exception as e:
        logger.warning(f"[Memory] Failed to search by key prefix: {e}")
        return []


def delete_by_key(key: str) -> bool:
    """
    Delete a memory entry by key.

    Args:
        key: Key of the memory entry to delete

    Returns:
        True if deleted successfully, False otherwise
    """
    try:
        client = get_client()
        if client is None:
            logger.debug("[Memory] Supabase client not available")
            return False

        client.table(TABLE).delete().eq("key", key).execute()
        logger.debug(f"[Memory] Deleted memory with key: {key}")
        return True
    except Exception as e:
        logger.warning(f"[Memory] Failed to delete memory: {e}")
        return False


def get_memory_stats() -> Dict[str, Any]:
    """
    Get statistics about memory storage.

    Returns:
        Dictionary with memory statistics
    """
    try:
        client = get_client()
        if client is None:
            return {"enabled": False, "error": "Supabase client not available"}

        result = client.table(TABLE).select("id", count="exact").execute()
        total_count = result.count if hasattr(result, "count") else len(result.data or [])

        result_with_emb = client.table(TABLE).select(
            "id", count="exact"
        ).not_.is_("embedding", "null").execute()
        with_embedding_count = (
            result_with_emb.count
            if hasattr(result_with_emb, "count")
            else len(result_with_emb.data or [])
        )

        return {
            "enabled": True,
            "total_records": total_count,
            "with_embeddings": with_embedding_count,
            "table": TABLE
        }

    except Exception as e:
        logger.warning(f"[Memory] Failed to get stats: {e}")
        return {"enabled": True, "error": str(e)}
