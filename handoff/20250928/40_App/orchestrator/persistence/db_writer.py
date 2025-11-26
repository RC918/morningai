#!/usr/bin/env python3
"""
Database writer for agent_tasks table
Implements write-through strategy for task state transitions

Phase 3 Update: Automatic tenant_id resolution via user_profiles
"""
import logging
import re
import uuid
from datetime import datetime, timezone
from typing import Optional
from .db_client import get_client
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from exceptions import (  # noqa: E402
    DatabaseConnectionError,
    DatabaseReadError,
    TenantResolutionError
)

logger = logging.getLogger(__name__)


def normalize_and_validate_uuid(id_str: str, field_name: str = "id") -> str:
    """
    Extract and validate UUID from potentially prefixed strings.

    Handles cases where external tools or test scripts create task IDs with prefixes
    (e.g., "phase1-stg-test-{uuid}") that cannot be stored in PostgreSQL UUID columns.

    Args:
        id_str: String that may contain a UUID (with or without prefix)
        field_name: Name of the field being normalized (for logging)

    Returns:
        Validated UUID string in canonical format

    Raises:
        ValueError: If no valid UUID is found in the input string

    Examples:
        >>> normalize_and_validate_uuid("550e8400-e29b-41d4-a716-446655440000")
        "550e8400-e29b-41d4-a716-446655440000"

        >>> normalize_and_validate_uuid("phase1-stg-test-550e8400-e29b-41d4-a716-446655440000")
        "550e8400-e29b-41d4-a716-446655440000"
    """
    # Fast path: try as-is first (most common case)
    try:
        return str(uuid.UUID(id_str))
    except ValueError:
        pass

    # Search for UUID pattern in the string
    uuid_pattern = r'[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}'
    matches = re.findall(uuid_pattern, id_str)

    if not matches:
        raise ValueError(f"No valid UUID found in {field_name}='{id_str}'")

    # Validate the extracted UUID
    validated = uuid.UUID(matches[0])

    # Log warning if normalization occurred (indicates external prefix usage)
    if id_str != str(validated):
        logger.warning(
            f"UUID normalization: {field_name} '{id_str}' -> '{validated}'",
            extra={
                "operation": "persistence.uuid_normalization",
                "field": field_name,
                "original": id_str,
                "normalized": str(validated)
            }
        )

    return str(validated)


def fetch_user_tenant_id(user_id: str) -> Optional[str]:
    """
    Fetch user's tenant_id from user_profiles table.

    Phase 3: Used to automatically determine tenant for task operations.
    Raises exception if user_profile not found (fail loudly).

    Args:
        user_id: UUID of authenticated user (from auth.uid())

    Returns:
        Tenant UUID string

    Raises:
        TenantResolutionError: If user_profile not found for the user
        DatabaseConnectionError: If database connection fails
        DatabaseReadError: If database query fails
    """
    try:
        client = get_client()

        if client is None:
            raise DatabaseConnectionError("Failed to get database client")

        response = client.table("user_profiles") \
            .select("tenant_id") \
            .eq("id", user_id) \
            .single() \
            .execute()

        if not response.data or "tenant_id" not in response.data:
            raise TenantResolutionError(
                f"No user_profile found for user={user_id}. User must be assigned to a tenant first."
            )

        tenant_id = response.data["tenant_id"]
        logger.info(f"Fetched tenant_id={tenant_id} for user={user_id}")
        return tenant_id

    except TenantResolutionError:
        raise
    except Exception as e:
        error_msg = f"Failed to fetch tenant_id for user={user_id}: {e}"
        logger.error(error_msg)
        raise DatabaseReadError(error_msg) from e


def upsert_task_queued(
    task_id: str,
    trace_id: str,
    question: str,
    job_id: Optional[str] = None,
    tenant_id: Optional[str] = None
) -> bool:
    """
    Insert or update task when queued by API.

    Args:
        task_id: UUID task identifier (may contain prefix, will be normalized)
        trace_id: UUID trace identifier (may contain prefix, will be normalized)
        question: FAQ question text
        job_id: RQ job ID (optional)
        tenant_id: Tenant UUID for multi-tenant isolation (optional, defaults to default tenant)

    Returns:
        True if successful, False otherwise
    """
    try:
        client = get_client()
        now = datetime.now(timezone.utc).isoformat()

        # Normalize UUIDs to handle prefixed IDs from external tools
        normalized_task_id = normalize_and_validate_uuid(task_id, "task_id")
        normalized_trace_id = normalize_and_validate_uuid(trace_id, "trace_id")

        data = {
            "task_id": normalized_task_id,
            "trace_id": normalized_trace_id,
            "question": question,
            "status": "queued",
            "created_at": now,
            "updated_at": now
        }

        if job_id:
            data["job_id"] = job_id

        if tenant_id:
            data["tenant_id"] = tenant_id
        else:
            data["tenant_id"] = "00000000-0000-0000-0000-000000000001"

        client.table("agent_tasks").upsert(data, on_conflict="task_id").execute()

        logger.info(f"DB write success: task {normalized_task_id} status=queued tenant_id={data.get('tenant_id')}")
        return True

    except Exception as e:
        logger.error(f"DB write failed for task {task_id} (queued): {e}")
        return False


def upsert_task_running(task_id: str, trace_id: str, tenant_id: Optional[str] = None) -> bool:
    """
    Update task when worker starts processing.

    Args:
        task_id: UUID task identifier (may contain prefix, will be normalized)
        trace_id: UUID trace identifier (may contain prefix, will be normalized)
        tenant_id: Tenant UUID (optional, defaults to default tenant if not provided)

    Returns:
        True if successful, False otherwise
    """
    try:
        client = get_client()
        now = datetime.now(timezone.utc).isoformat()

        # Normalize UUIDs to handle prefixed IDs from external tools
        normalized_task_id = normalize_and_validate_uuid(task_id, "task_id")
        normalized_trace_id = normalize_and_validate_uuid(trace_id, "trace_id")

        data = {
            "task_id": normalized_task_id,
            "trace_id": normalized_trace_id,
            "status": "running",
            "started_at": now,
            "updated_at": now,
            "tenant_id": tenant_id or "00000000-0000-0000-0000-000000000001"
        }

        client.table("agent_tasks").upsert(data, on_conflict="task_id").execute()

        logger.info(f"DB write success: task {normalized_task_id} status=running tenant_id={data['tenant_id']}")
        return True

    except Exception as e:
        logger.error(f"DB write failed for task {task_id} (running): {e}")
        return False


def upsert_task_done(task_id: str, trace_id: str, pr_url: str, tenant_id: Optional[str] = None) -> bool:
    """
    Update task when worker completes successfully.

    Args:
        task_id: UUID task identifier (may contain prefix, will be normalized)
        trace_id: UUID trace identifier (may contain prefix, will be normalized)
        pr_url: GitHub PR URL
        tenant_id: Tenant UUID (optional, defaults to default tenant if not provided)

    Returns:
        True if successful, False otherwise
    """
    try:
        client = get_client()
        now = datetime.now(timezone.utc).isoformat()

        # Normalize UUIDs to handle prefixed IDs from external tools
        normalized_task_id = normalize_and_validate_uuid(task_id, "task_id")
        normalized_trace_id = normalize_and_validate_uuid(trace_id, "trace_id")

        data = {
            "task_id": normalized_task_id,
            "trace_id": normalized_trace_id,
            "status": "done",
            "pr_url": pr_url,
            "finished_at": now,
            "updated_at": now,
            "tenant_id": tenant_id or "00000000-0000-0000-0000-000000000001"
        }

        client.table("agent_tasks").upsert(data, on_conflict="task_id").execute()

        logger.info(f"DB write success: task {normalized_task_id} status=done pr_url={pr_url} tenant_id={data['tenant_id']}")
        return True

    except Exception as e:
        logger.error(f"DB write failed for task {task_id} (done): {e}")
        return False


def upsert_task_error(task_id: str, trace_id: str, error_msg: str, tenant_id: Optional[str] = None) -> bool:
    """
    Update task when worker encounters an error.

    Args:
        task_id: UUID task identifier (may contain prefix, will be normalized)
        trace_id: UUID trace identifier (may contain prefix, will be normalized)
        error_msg: Error message text
        tenant_id: Tenant UUID (optional, defaults to default tenant if not provided)

    Returns:
        True if successful, False otherwise
    """
    try:
        client = get_client()
        now = datetime.now(timezone.utc).isoformat()

        # Normalize UUIDs to handle prefixed IDs from external tools
        normalized_task_id = normalize_and_validate_uuid(task_id, "task_id")
        normalized_trace_id = normalize_and_validate_uuid(trace_id, "trace_id")

        data = {
            "task_id": normalized_task_id,
            "trace_id": normalized_trace_id,
            "status": "error",
            "error_msg": error_msg[:500],
            "finished_at": now,
            "updated_at": now,
            "tenant_id": tenant_id or "00000000-0000-0000-0000-000000000001"
        }

        client.table("agent_tasks").upsert(data, on_conflict="task_id").execute()

        logger.info(f"DB write success: task {normalized_task_id} status=error tenant_id={data['tenant_id']}")
        return True

    except Exception as e:
        logger.error(f"DB write failed for task {task_id} (error): {e}")
        return False
