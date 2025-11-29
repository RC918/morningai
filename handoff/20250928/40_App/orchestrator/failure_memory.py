#!/usr/bin/env python3
"""
Failure Memory Module - Phase 5 PR-4

Persists failure records to pgvector/Supabase for long-term storage and recall.

Features:
- save_failure_to_memory(failure) helper
- Structured key format: failure:<trace_id> or failure:<category>:<timestamp>
- Basic recall by key prefix filtering
- Does NOT include vector search (planned for future PR)

Dependencies:
- PR-1: FailureRecord dataclass from failure_recorder.py
- Supabase/pgvector for storage
"""

import logging
import json
from typing import Dict, List, Optional, Any
from datetime import datetime

logger = logging.getLogger(__name__)

FAILURE_MEMORY_TABLE = "failure_memory"
FAILURE_KEY_PREFIX = "failure"


def _get_supabase_client():
    """Get Supabase client for failure memory operations"""
    try:
        from supabase import create_client
        from common.config.settings import settings

        supabase_url = settings.supabase_url
        supabase_key = settings.supabase_service_role_key

        if supabase_url and supabase_key:
            return create_client(supabase_url, supabase_key)
        else:
            logger.debug("[FailureMemory] Supabase credentials not available")
            return None
    except ImportError as e:
        logger.debug(f"[FailureMemory] Supabase import failed: {e}")
        return None
    except Exception as e:
        logger.warning(f"[FailureMemory] Failed to create Supabase client: {e}")
        return None


def _generate_failure_key(
    trace_id: str,
    error_type: Optional[str] = None,
    timestamp: Optional[str] = None
) -> str:
    """
    Generate a structured key for failure memory storage

    Key formats:
    - failure:<trace_id> (primary key)
    - failure:<error_type>:<timestamp> (category-based key for filtering)

    Args:
        trace_id: Unique workflow identifier
        error_type: Optional error category for secondary key
        timestamp: Optional timestamp (defaults to current UTC)

    Returns:
        Structured key string
    """
    if error_type:
        ts = timestamp or datetime.utcnow().strftime("%Y%m%d%H%M%S")
        return f"{FAILURE_KEY_PREFIX}:{error_type}:{ts}"
    return f"{FAILURE_KEY_PREFIX}:{trace_id}"


def _serialize_failure_for_memory(failure_dict: Dict[str, Any]) -> str:
    """
    Serialize failure record for memory storage

    Creates a text representation suitable for embedding and recall.

    Args:
        failure_dict: Failure record dictionary

    Returns:
        Serialized text representation
    """
    parts = [
        f"Goal: {failure_dict.get('goal', 'N/A')}",
        f"Error Type: {failure_dict.get('error_type', 'unknown')}",
        f"Task Type: {failure_dict.get('task_type', 'unknown')}",
        f"Fixer Retries: {failure_dict.get('fixer_retries', 0)}",
        f"Status: {failure_dict.get('status', 'error')}",
    ]

    if failure_dict.get("error_message"):
        parts.append(f"Error Message: {failure_dict['error_message'][:200]}")

    if failure_dict.get("merge_decision"):
        parts.append(f"Merge Decision: {failure_dict['merge_decision']}")

    metadata = failure_dict.get("metadata", {})
    if metadata:
        if metadata.get("security_risk"):
            parts.append(f"Security Risk: {metadata['security_risk']}")
        if metadata.get("governance_risk"):
            parts.append(f"Governance Risk: {metadata['governance_risk']}")

    return "\n".join(parts)


def save_failure_to_memory(
    failure: Any,
    include_category_key: bool = True
) -> Optional[str]:
    """
    Save a failure record to pgvector/Supabase memory

    This function persists failure records for long-term storage and future
    recall. It creates structured keys for efficient filtering.

    Args:
        failure: FailureRecord instance or dictionary
        include_category_key: Whether to also save with category-based key

    Returns:
        Primary key if saved successfully, None otherwise
    """
    try:
        if hasattr(failure, "to_dict"):
            failure_dict = failure.to_dict()
        elif isinstance(failure, dict):
            failure_dict = failure
        else:
            logger.warning("[FailureMemory] Invalid failure type, expected FailureRecord or dict")
            return None

        trace_id = failure_dict.get("trace_id")
        if not trace_id:
            logger.warning("[FailureMemory] Failure record missing trace_id")
            return None

        client = _get_supabase_client()
        if client is None:
            logger.debug("[FailureMemory] Supabase client not available, skipping save")
            return None

        primary_key = _generate_failure_key(trace_id)
        text_content = _serialize_failure_for_memory(failure_dict)

        record_data = {
            "key": primary_key,
            "text": text_content,
            "embedding": [],
            "metadata": json.dumps({
                "failure_id": failure_dict.get("id"),
                "trace_id": trace_id,
                "error_type": failure_dict.get("error_type"),
                "task_type": failure_dict.get("task_type"),
                "created_at": failure_dict.get("created_at"),
                "env": failure_dict.get("env"),
                "fixer_retries": failure_dict.get("fixer_retries", 0),
            })
        }

        client.table(FAILURE_MEMORY_TABLE).insert(record_data).execute()

        logger.info(f"[FailureMemory] Saved failure to memory: {primary_key}", extra={
            "operation": "save_failure_to_memory",
            "key": primary_key,
            "trace_id": trace_id,
            "error_type": failure_dict.get("error_type")
        })

        if include_category_key:
            error_type = failure_dict.get("error_type")
            if error_type:
                category_key = _generate_failure_key(
                    trace_id,
                    error_type=error_type,
                    timestamp=failure_dict.get("created_at", "").replace("-", "").replace(":", "").replace("T", "")[:14]
                )
                category_record = {
                    "key": category_key,
                    "text": text_content,
                    "embedding": [],
                    "metadata": json.dumps({
                        "failure_id": failure_dict.get("id"),
                        "trace_id": trace_id,
                        "error_type": error_type,
                        "primary_key": primary_key,
                    })
                }
                try:
                    client.table(FAILURE_MEMORY_TABLE).insert(category_record).execute()
                    logger.debug(f"[FailureMemory] Saved category key: {category_key}")
                except Exception as e:
                    logger.debug(f"[FailureMemory] Failed to save category key: {e}")

        return primary_key

    except Exception as e:
        logger.warning(f"[FailureMemory] Failed to save failure to memory: {e}", extra={
            "operation": "save_failure_to_memory",
            "error": str(e)
        })
        return None


def recall_failures_by_prefix(
    prefix: str,
    limit: int = 50
) -> List[Dict[str, Any]]:
    """
    Recall failure records by key prefix

    This provides basic filtering by key prefix without vector search.
    Useful for retrieving failures by:
    - trace_id: prefix="failure:<trace_id>"
    - error_type: prefix="failure:<error_type>:"

    Args:
        prefix: Key prefix to filter by
        limit: Maximum number of records to return

    Returns:
        List of failure memory records
    """
    try:
        client = _get_supabase_client()
        if client is None:
            logger.debug("[FailureMemory] Supabase client not available")
            return []

        result = client.table(FAILURE_MEMORY_TABLE).select("*").like(
            "key", f"{prefix}%"
        ).order("id", desc=True).limit(limit).execute()

        records = result.data or []

        parsed_records = []
        for record in records:
            parsed = {
                "id": record.get("id"),
                "key": record.get("key"),
                "text": record.get("text"),
            }
            if record.get("metadata"):
                try:
                    parsed["metadata"] = json.loads(record["metadata"])
                except (json.JSONDecodeError, TypeError):
                    parsed["metadata"] = {}
            else:
                parsed["metadata"] = {}
            parsed_records.append(parsed)

        logger.debug(f"[FailureMemory] Recalled {len(parsed_records)} records with prefix: {prefix}")
        return parsed_records

    except Exception as e:
        logger.warning(f"[FailureMemory] Failed to recall failures: {e}", extra={
            "operation": "recall_failures_by_prefix",
            "prefix": prefix,
            "error": str(e)
        })
        return []


def recall_failures_by_trace_id(trace_id: str) -> List[Dict[str, Any]]:
    """
    Recall failure records by trace_id

    Args:
        trace_id: Workflow trace identifier

    Returns:
        List of failure memory records for the given trace_id
    """
    prefix = _generate_failure_key(trace_id)
    return recall_failures_by_prefix(prefix, limit=10)


def recall_failures_by_error_type(
    error_type: str,
    limit: int = 50
) -> List[Dict[str, Any]]:
    """
    Recall failure records by error type category

    Args:
        error_type: Error type category (e.g., "timeout", "ci_failure")
        limit: Maximum number of records to return

    Returns:
        List of failure memory records for the given error type
    """
    prefix = f"{FAILURE_KEY_PREFIX}:{error_type}:"
    return recall_failures_by_prefix(prefix, limit=limit)


def recall_recent_failures(limit: int = 50) -> List[Dict[str, Any]]:
    """
    Recall most recent failure records

    Args:
        limit: Maximum number of records to return

    Returns:
        List of recent failure memory records
    """
    try:
        client = _get_supabase_client()
        if client is None:
            logger.debug("[FailureMemory] Supabase client not available")
            return []

        result = client.table(FAILURE_MEMORY_TABLE).select("*").like(
            "key", f"{FAILURE_KEY_PREFIX}:%"
        ).order("id", desc=True).limit(limit).execute()

        records = result.data or []

        parsed_records = []
        for record in records:
            parsed = {
                "id": record.get("id"),
                "key": record.get("key"),
                "text": record.get("text"),
            }
            if record.get("metadata"):
                try:
                    parsed["metadata"] = json.loads(record["metadata"])
                except (json.JSONDecodeError, TypeError):
                    parsed["metadata"] = {}
            else:
                parsed["metadata"] = {}
            parsed_records.append(parsed)

        logger.debug(f"[FailureMemory] Recalled {len(parsed_records)} recent failures")
        return parsed_records

    except Exception as e:
        logger.warning(f"[FailureMemory] Failed to recall recent failures: {e}", extra={
            "operation": "recall_recent_failures",
            "error": str(e)
        })
        return []


def get_failure_memory_stats() -> Dict[str, Any]:
    """
    Get statistics about failure memory storage

    Returns:
        Dictionary with failure memory statistics
    """
    try:
        client = _get_supabase_client()
        if client is None:
            return {"enabled": False, "error": "Supabase client not available"}

        result = client.table(FAILURE_MEMORY_TABLE).select(
            "key", count="exact"
        ).like("key", f"{FAILURE_KEY_PREFIX}:%").execute()

        total_count = result.count if hasattr(result, "count") else len(result.data or [])

        error_types: Dict[str, int] = {}
        recent = recall_recent_failures(limit=100)
        for record in recent:
            metadata = record.get("metadata", {})
            error_type = metadata.get("error_type", "unknown")
            if ":" not in record.get("key", "").split(":", 2)[-1]:
                error_types[error_type] = error_types.get(error_type, 0) + 1

        return {
            "enabled": True,
            "total_records": total_count,
            "recent_count": len(recent),
            "error_type_distribution": error_types
        }

    except Exception as e:
        logger.warning(f"[FailureMemory] Failed to get stats: {e}")
        return {"enabled": True, "error": str(e)}
