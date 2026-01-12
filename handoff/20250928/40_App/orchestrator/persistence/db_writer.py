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


def _generate_deterministic_uuid(input_str: str) -> str:
    """
    Generate a deterministic UUID v5 from an arbitrary string.

    Uses UUID v5 (SHA-1 based) with DNS namespace to ensure:
    - Same input always produces same UUID (deterministic)
    - Different inputs produce different UUIDs (collision-resistant)

    Args:
        input_str: Any string to convert to UUID

    Returns:
        UUID string in canonical format

    Examples:
        >>> _generate_deterministic_uuid("test-fc-v3-2f15e600")
        '1885b3e2-8531-5129-a53e-928a47d19454'
    """
    # Use standard DNS namespace for deterministic UUID generation
    # This ensures consistent UUID generation across all instances
    return str(uuid.uuid5(uuid.NAMESPACE_DNS, input_str))


def normalize_and_validate_uuid(id_str: str, field_name: str = "id") -> str:
    """
    Extract and validate UUID from potentially prefixed strings.

    Handles cases where external tools or test scripts create task IDs with prefixes
    (e.g., "phase1-stg-test-{uuid}") that cannot be stored in PostgreSQL UUID columns.

    If no valid UUID is found, generates a deterministic UUID from the input string
    using UUID v5 (SHA-1 hash). This allows test/debug trace IDs like "test-fc-v3-2f15e600"
    to be persisted to the database while maintaining traceability.

    Args:
        id_str: String that may contain a UUID (with or without prefix)
        field_name: Name of the field being normalized (for logging)

    Returns:
        Validated UUID string in canonical format

    Raises:
        TypeError: If input is None or not a string

    Examples:
        >>> normalize_and_validate_uuid("550e8400-e29b-41d4-a716-446655440000")
        "550e8400-e29b-41d4-a716-446655440000"

        >>> normalize_and_validate_uuid("phase1-stg-test-550e8400-e29b-41d4-a716-446655440000")
        "550e8400-e29b-41d4-a716-446655440000"

        >>> normalize_and_validate_uuid("test-fc-v3-2f15e600")
        '1885b3e2-8531-5129-a53e-928a47d19454'
    """
    # Handle None and non-string inputs
    if id_str is None:
        raise TypeError(f"{field_name} cannot be None")
    if not isinstance(id_str, str):
        raise TypeError(f"{field_name} must be a string, got {type(id_str).__name__}")

    # Fast path: try as-is first (most common case)
    try:
        return str(uuid.UUID(id_str))
    except (ValueError, AttributeError):
        pass

    # Search for UUID pattern in the string
    uuid_pattern = r'[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}'
    matches = re.findall(uuid_pattern, id_str)

    if matches:
        # Validate the extracted UUID
        validated = uuid.UUID(matches[0])

        # Log warning if normalization occurred (indicates external prefix usage)
        if id_str != str(validated):
            logger.warning(
                f"UUID normalization: {field_name} '{id_str}' -> '{validated}'",
                extra={
                    "operation": "uuid_normalization",
                    "field_name": field_name,
                    "original_value": id_str,
                    "normalized_value": str(validated)
                }
            )

        return str(validated)

    # Fallback: Generate deterministic UUID from the string hash
    # This allows test/debug trace IDs to be persisted while maintaining traceability
    generated_uuid = _generate_deterministic_uuid(id_str)
    logger.warning(
        f"UUID fallback: {field_name} '{id_str}' -> '{generated_uuid}' (generated from hash)",
        extra={
            "operation": "uuid_fallback_generation",
            "field_name": field_name,
            "original_value": id_str,
            "generated_uuid": generated_uuid
        }
    )

    return generated_uuid


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
        if client is None:
            logger.warning(
                f"Supabase client unavailable, cannot upsert task {task_id} (queued)"
            )
            return False
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
        if client is None:
            logger.warning(
                f"Supabase client unavailable, cannot upsert task {task_id} (running)"
            )
            return False
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
        if client is None:
            logger.warning(
                f"Supabase client unavailable, cannot upsert task {task_id} (done)"
            )
            return False
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
        if client is None:
            logger.warning(
                f"Supabase client unavailable, cannot upsert task {task_id} (error)"
            )
            return False
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
