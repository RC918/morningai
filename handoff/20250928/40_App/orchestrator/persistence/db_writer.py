#!/usr/bin/env python3
"""
Database writer for agent_tasks table
Implements write-through strategy for task state transitions
"""
import logging
from datetime import datetime, timezone
from typing import Optional
from .db_client import get_client

logger = logging.getLogger(__name__)

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
        task_id: UUID task identifier
        trace_id: UUID trace identifier (typically same as task_id)
        question: FAQ question text
        job_id: RQ job ID (optional)
        tenant_id: Tenant UUID for multi-tenant isolation (optional, defaults to default tenant)
    
    Returns:
        True if successful, False otherwise
    """
    try:
        client = get_client()
        now = datetime.now(timezone.utc).isoformat()
        
        data = {
            "task_id": task_id,
            "trace_id": trace_id,
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
        
        logger.info(f"DB write success: task {task_id} status=queued tenant_id={data.get('tenant_id')}")
        return True
        
    except Exception as e:
        logger.error(f"DB write failed for task {task_id} (queued): {e}")
        return False

def upsert_task_running(task_id: str, trace_id: str, tenant_id: Optional[str] = None) -> bool:
    """
    Update task when worker starts processing.
    
    Args:
        task_id: UUID task identifier
        trace_id: UUID trace identifier
        tenant_id: Tenant UUID (optional, defaults to default tenant if not provided)
    
    Returns:
        True if successful, False otherwise
    """
    try:
        client = get_client()
        now = datetime.now(timezone.utc).isoformat()
        
        data = {
            "task_id": task_id,
            "trace_id": trace_id,
            "status": "running",
            "started_at": now,
            "updated_at": now,
            "tenant_id": tenant_id or "00000000-0000-0000-0000-000000000001"
        }
        
        client.table("agent_tasks").upsert(data, on_conflict="task_id").execute()
        
        logger.info(f"DB write success: task {task_id} status=running tenant_id={data['tenant_id']}")
        return True
        
    except Exception as e:
        logger.error(f"DB write failed for task {task_id} (running): {e}")
        return False

def upsert_task_done(task_id: str, trace_id: str, pr_url: str, tenant_id: Optional[str] = None) -> bool:
    """
    Update task when worker completes successfully.
    
    Args:
        task_id: UUID task identifier
        trace_id: UUID trace identifier
        pr_url: GitHub PR URL
        tenant_id: Tenant UUID (optional, defaults to default tenant if not provided)
    
    Returns:
        True if successful, False otherwise
    """
    try:
        client = get_client()
        now = datetime.now(timezone.utc).isoformat()
        
        data = {
            "task_id": task_id,
            "trace_id": trace_id,
            "status": "done",
            "pr_url": pr_url,
            "finished_at": now,
            "updated_at": now,
            "tenant_id": tenant_id or "00000000-0000-0000-0000-000000000001"
        }
        
        client.table("agent_tasks").upsert(data, on_conflict="task_id").execute()
        
        logger.info(f"DB write success: task {task_id} status=done pr_url={pr_url} tenant_id={data['tenant_id']}")
        return True
        
    except Exception as e:
        logger.error(f"DB write failed for task {task_id} (done): {e}")
        return False

def upsert_task_error(task_id: str, trace_id: str, error_msg: str, tenant_id: Optional[str] = None) -> bool:
    """
    Update task when worker encounters an error.
    
    Args:
        task_id: UUID task identifier
        trace_id: UUID trace identifier
        error_msg: Error message text
        tenant_id: Tenant UUID (optional, defaults to default tenant if not provided)
    
    Returns:
        True if successful, False otherwise
    """
    try:
        client = get_client()
        now = datetime.now(timezone.utc).isoformat()
        
        data = {
            "task_id": task_id,
            "trace_id": trace_id,
            "status": "error",
            "error_msg": error_msg[:500],
            "finished_at": now,
            "updated_at": now,
            "tenant_id": tenant_id or "00000000-0000-0000-0000-000000000001"
        }
        
        client.table("agent_tasks").upsert(data, on_conflict="task_id").execute()
        
        logger.info(f"DB write success: task {task_id} status=error tenant_id={data['tenant_id']}")
        return True
        
    except Exception as e:
        logger.error(f"DB write failed for task {task_id} (error): {e}")
        return False
