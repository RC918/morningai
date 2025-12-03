"""
Error-Fix Pairs Store - Phase 2 Brain Layer

Stores and retrieves error-fix pairs for AI learning and recall.

This module enables the AI to learn from past mistakes by:
1. Storing pairs of errors and their fixes
2. Finding similar past errors using vector similarity
3. Suggesting fixes based on historical success rates

Features:
- Vector similarity search for finding similar errors
- Confidence scoring based on success/failure history
- Automatic embedding generation for errors and fixes

Dependencies:
- Migration 033: error_fix_pairs table
- Migration 032: match_error_fix_pairs_by_error SQL function
"""

import json
import logging
from dataclasses import dataclass
from typing import List, Dict, Any, Optional

from supabase import create_client
from openai import OpenAI
from common.config.settings import settings

logger = logging.getLogger(__name__)

ERROR_FIX_PAIRS_TABLE = "error_fix_pairs"
DEFAULT_SIMILARITY_THRESHOLD = 0.7


@dataclass
class ErrorFixPair:
    """Represents an error-fix pair for learning and recall."""

    error_text: str
    fix_text: str
    error_type: Optional[str] = None
    fix_type: Optional[str] = None
    error_context: Optional[Dict[str, Any]] = None
    fix_metadata: Optional[Dict[str, Any]] = None
    trace_id: Optional[str] = None
    task_type: Optional[str] = None
    id: Optional[int] = None
    confidence_score: float = 0.5
    success_count: int = 0
    failure_count: int = 0
    created_at: Optional[str] = None
    similarity: Optional[float] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage."""
        return {
            "error_text": self.error_text,
            "fix_text": self.fix_text,
            "error_type": self.error_type,
            "fix_type": self.fix_type,
            "error_context": self.error_context,
            "fix_metadata": self.fix_metadata,
            "trace_id": self.trace_id,
            "task_type": self.task_type,
            "confidence_score": self.confidence_score,
            "success_count": self.success_count,
            "failure_count": self.failure_count,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ErrorFixPair":
        """Create from dictionary."""
        return cls(
            id=data.get("id"),
            error_text=data.get("error_text", ""),
            fix_text=data.get("fix_text", ""),
            error_type=data.get("error_type"),
            fix_type=data.get("fix_type"),
            error_context=data.get("error_context"),
            fix_metadata=data.get("fix_metadata"),
            trace_id=data.get("trace_id"),
            task_type=data.get("task_type"),
            confidence_score=data.get("confidence_score", 0.5),
            success_count=data.get("success_count", 0),
            failure_count=data.get("failure_count", 0),
            created_at=data.get("created_at"),
            similarity=data.get("similarity"),
        )


def _get_supabase_client():
    """Get Supabase client for error-fix pairs operations."""
    try:
        supabase_url = settings.supabase_url
        supabase_key = settings.supabase_service_role_key

        if supabase_url and supabase_key:
            return create_client(supabase_url, supabase_key)
        else:
            logger.debug("[ErrorFixPairs] Supabase credentials not available")
            return None
    except Exception as e:
        logger.warning(f"[ErrorFixPairs] Failed to create Supabase client: {e}")
        return None


def _embed(text: str) -> Optional[List[float]]:
    """Generate embedding vector for text using OpenAI."""
    try:
        api_key = settings.openai_api_key
        if not api_key:
            logger.debug("[ErrorFixPairs] OpenAI API key not available")
            return None
        cl = OpenAI(api_key=api_key)
        emb = cl.embeddings.create(
            model="text-embedding-3-small",
            input=text
        ).data[0].embedding
        return emb
    except Exception as e:
        logger.warning(f"[ErrorFixPairs] Failed to get embedding: {e}")
        return None


def save_error_fix_pair(
    error_text: str,
    fix_text: str,
    error_type: Optional[str] = None,
    fix_type: Optional[str] = None,
    error_context: Optional[Dict[str, Any]] = None,
    fix_metadata: Optional[Dict[str, Any]] = None,
    trace_id: Optional[str] = None,
    task_type: Optional[str] = None,
) -> Optional[int]:
    """
    Save an error-fix pair to the database.

    This function stores a pair of error and fix information along with
    their embeddings for future similarity search.

    Args:
        error_text: The error message or context
        fix_text: The solution or fix that resolved the error
        error_type: Category of the error (e.g., "syntax_error", "timeout")
        fix_type: Category of the fix (e.g., "code_change", "config_update")
        error_context: Additional context about the error (JSONB)
        fix_metadata: Additional metadata about the fix (JSONB)
        trace_id: Workflow trace identifier
        task_type: Type of task where error occurred

    Returns:
        ID of the saved pair, or None if failed
    """
    try:
        client = _get_supabase_client()
        if client is None:
            logger.debug("[ErrorFixPairs] Supabase client not available")
            return None

        error_embedding = _embed(error_text)
        fix_embedding = _embed(fix_text)

        record_data = {
            "error_text": error_text,
            "fix_text": fix_text,
            "error_embedding": error_embedding,
            "fix_embedding": fix_embedding,
            "error_type": error_type,
            "fix_type": fix_type,
            "error_context": json.dumps(error_context) if error_context else None,
            "fix_metadata": json.dumps(fix_metadata) if fix_metadata else None,
            "trace_id": trace_id,
            "task_type": task_type,
            "confidence_score": 0.5,
            "success_count": 0,
            "failure_count": 0,
        }

        result = client.table(ERROR_FIX_PAIRS_TABLE).insert(record_data).execute()

        if result.data and len(result.data) > 0:
            pair_id = result.data[0].get("id")
            logger.info(f"[ErrorFixPairs] Saved error-fix pair: {pair_id}", extra={
                "operation": "save_error_fix_pair",
                "pair_id": pair_id,
                "error_type": error_type,
                "trace_id": trace_id
            })
            return pair_id

        return None

    except Exception as e:
        logger.warning(f"[ErrorFixPairs] Failed to save error-fix pair: {e}", extra={
            "operation": "save_error_fix_pair",
            "error": str(e)
        })
        return None


def find_similar_errors(
    error_text: str,
    limit: int = 5,
    threshold: float = DEFAULT_SIMILARITY_THRESHOLD,
    error_type_filter: Optional[str] = None,
) -> List[ErrorFixPair]:
    """
    Find similar past errors using vector similarity search.

    This function searches for errors similar to the given error text
    and returns their associated fixes.

    Args:
        error_text: The error to find similar matches for
        limit: Maximum number of results to return
        threshold: Minimum similarity score (0.0 to 1.0)
        error_type_filter: Optional filter by error type

    Returns:
        List of ErrorFixPair objects sorted by similarity
    """
    try:
        client = _get_supabase_client()
        if client is None:
            logger.debug("[ErrorFixPairs] Supabase client not available")
            return []

        error_embedding = _embed(error_text)
        if error_embedding is None:
            logger.debug("[ErrorFixPairs] Failed to generate error embedding")
            return []

        result = client.rpc(
            "match_error_fix_pairs_by_error",
            {
                "query_embedding": error_embedding,
                "match_threshold": threshold,
                "match_count": limit,
                "error_type_filter": error_type_filter
            }
        ).execute()

        pairs = []
        for row in result.data or []:
            pair = ErrorFixPair.from_dict(row)
            pairs.append(pair)

        logger.debug(f"[ErrorFixPairs] Found {len(pairs)} similar errors")
        return pairs

    except Exception as e:
        logger.warning(f"[ErrorFixPairs] Failed to find similar errors: {e}", extra={
            "operation": "find_similar_errors",
            "error": str(e)
        })
        return []


def get_fix_for_error(
    error_text: str,
    min_confidence: float = 0.5,
    error_type_filter: Optional[str] = None,
) -> Optional[ErrorFixPair]:
    """
    Get the best fix suggestion for an error.

    This function finds the most similar past error with a fix that
    has a confidence score above the minimum threshold.

    Args:
        error_text: The error to find a fix for
        min_confidence: Minimum confidence score for the fix
        error_type_filter: Optional filter by error type

    Returns:
        The best matching ErrorFixPair, or None if no good match found
    """
    try:
        similar_pairs = find_similar_errors(
            error_text=error_text,
            limit=5,
            threshold=DEFAULT_SIMILARITY_THRESHOLD,
            error_type_filter=error_type_filter
        )

        for pair in similar_pairs:
            if pair.confidence_score >= min_confidence:
                logger.info("[ErrorFixPairs] Found fix suggestion", extra={
                    "operation": "get_fix_for_error",
                    "pair_id": pair.id,
                    "similarity": pair.similarity,
                    "confidence": pair.confidence_score
                })
                return pair

        logger.debug("[ErrorFixPairs] No fix found with sufficient confidence")
        return None

    except Exception as e:
        logger.warning(f"[ErrorFixPairs] Failed to get fix for error: {e}")
        return None


def update_pair_feedback(
    pair_id: int,
    was_successful: bool
) -> Optional[float]:
    """
    Update the success/failure stats for an error-fix pair.

    Call this function after using a suggested fix to update
    the confidence score based on whether it worked.

    Args:
        pair_id: ID of the error-fix pair
        was_successful: Whether the fix was successful

    Returns:
        Updated confidence score, or None if failed
    """
    try:
        client = _get_supabase_client()
        if client is None:
            logger.debug("[ErrorFixPairs] Supabase client not available")
            return None

        result = client.rpc(
            "update_error_fix_pair_stats",
            {
                "pair_id": pair_id,
                "was_successful": was_successful
            }
        ).execute()

        new_confidence = result.data
        logger.info("[ErrorFixPairs] Updated pair feedback", extra={
            "operation": "update_pair_feedback",
            "pair_id": pair_id,
            "was_successful": was_successful,
            "new_confidence": new_confidence
        })
        return new_confidence

    except Exception as e:
        logger.warning(f"[ErrorFixPairs] Failed to update pair feedback: {e}")
        return None


def get_error_fix_pairs_by_type(
    error_type: str,
    limit: int = 20
) -> List[ErrorFixPair]:
    """
    Get error-fix pairs by error type.

    Args:
        error_type: Error type to filter by
        limit: Maximum number of results

    Returns:
        List of ErrorFixPair objects
    """
    try:
        client = _get_supabase_client()
        if client is None:
            logger.debug("[ErrorFixPairs] Supabase client not available")
            return []

        result = client.table(ERROR_FIX_PAIRS_TABLE).select("*").eq(
            "error_type", error_type
        ).order("confidence_score", desc=True).limit(limit).execute()

        pairs = []
        for row in result.data or []:
            if row.get("error_context"):
                try:
                    row["error_context"] = json.loads(row["error_context"])
                except (json.JSONDecodeError, TypeError):
                    row["error_context"] = None
            if row.get("fix_metadata"):
                try:
                    row["fix_metadata"] = json.loads(row["fix_metadata"])
                except (json.JSONDecodeError, TypeError):
                    row["fix_metadata"] = None
            pairs.append(ErrorFixPair.from_dict(row))

        return pairs

    except Exception as e:
        logger.warning(f"[ErrorFixPairs] Failed to get pairs by type: {e}")
        return []


def get_recent_error_fix_pairs(limit: int = 20) -> List[ErrorFixPair]:
    """
    Get most recent error-fix pairs.

    Args:
        limit: Maximum number of results

    Returns:
        List of ErrorFixPair objects sorted by creation time
    """
    try:
        client = _get_supabase_client()
        if client is None:
            logger.debug("[ErrorFixPairs] Supabase client not available")
            return []

        result = client.table(ERROR_FIX_PAIRS_TABLE).select("*").order(
            "created_at", desc=True
        ).limit(limit).execute()

        pairs = []
        for row in result.data or []:
            if row.get("error_context"):
                try:
                    row["error_context"] = json.loads(row["error_context"])
                except (json.JSONDecodeError, TypeError):
                    row["error_context"] = None
            if row.get("fix_metadata"):
                try:
                    row["fix_metadata"] = json.loads(row["fix_metadata"])
                except (json.JSONDecodeError, TypeError):
                    row["fix_metadata"] = None
            pairs.append(ErrorFixPair.from_dict(row))

        return pairs

    except Exception as e:
        logger.warning(f"[ErrorFixPairs] Failed to get recent pairs: {e}")
        return []


def get_error_fix_pairs_stats() -> Dict[str, Any]:
    """
    Get statistics about error-fix pairs storage.

    Returns:
        Dictionary with error-fix pairs statistics
    """
    try:
        client = _get_supabase_client()
        if client is None:
            return {"enabled": False, "error": "Supabase client not available"}

        result = client.table(ERROR_FIX_PAIRS_TABLE).select(
            "id", count="exact"
        ).execute()
        total_count = result.count if hasattr(result, "count") else len(result.data or [])

        result_with_emb = client.table(ERROR_FIX_PAIRS_TABLE).select(
            "id", count="exact"
        ).not_.is_("error_embedding", "null").execute()
        with_embedding_count = (
            result_with_emb.count
            if hasattr(result_with_emb, "count")
            else len(result_with_emb.data or [])
        )

        error_types: Dict[str, int] = {}
        recent = get_recent_error_fix_pairs(limit=100)
        for pair in recent:
            error_type = pair.error_type or "unknown"
            error_types[error_type] = error_types.get(error_type, 0) + 1

        return {
            "enabled": True,
            "total_pairs": total_count,
            "with_embeddings": with_embedding_count,
            "error_type_distribution": error_types
        }

    except Exception as e:
        logger.warning(f"[ErrorFixPairs] Failed to get stats: {e}")
        return {"enabled": True, "error": str(e)}
