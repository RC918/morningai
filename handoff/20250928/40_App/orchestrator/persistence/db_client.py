#!/usr/bin/env python3
"""
Database client for Supabase PostgreSQL connection
Reuses pattern from pgvector_store.py
"""
import os
import logging
from typing import Optional, TYPE_CHECKING
from common.config.settings import settings

if TYPE_CHECKING:
    from supabase import Client

logger = logging.getLogger(__name__)

_supabase_client: Optional["Client"] = None

def get_client() -> Optional["Client"]:
    """
    Lazy initialization of Supabase client; avoids requiring external SDK at module load time.
    Returns cached client if available, or None if credentials are missing.
    
    Returns:
        Supabase Client instance, or None if credentials are not configured.
        Callers should check for None before using the client.
    """
    global _supabase_client
    
    if _supabase_client is not None:
        return _supabase_client
    
    try:
        from supabase import create_client
    except ImportError as e:
        logger.warning(
            f"[Supabase] SDK unavailable at runtime: {e}. "
            "Supabase features will be disabled."
        )
        return None
    
    supabase_url = settings.supabase_url
    supabase_key = settings.supabase_service_role_key or settings.supabase_anon_key
    
    if not supabase_url or not supabase_key:
        logger.warning(
            "[Supabase] Credentials missing (SUPABASE_URL / SUPABASE_SERVICE_ROLE_KEY or SUPABASE_ANON_KEY). "
            "Supabase features will be disabled."
        )
        return None
    
    _supabase_client = create_client(supabase_url, supabase_key)
    logger.info("Supabase client initialized for agent_tasks persistence")
    
    return _supabase_client

def ensure_table_exists(client: "Client") -> None:
    """
    Ensure agent_tasks table exists. Handles gracefully if already exists.
    """
    try:
        client.table("agent_tasks").select("task_id").limit(1).execute()
        logger.info("agent_tasks table verified")
    except Exception as e:
        logger.warning(f"agent_tasks table check failed: {e}. Table may not exist yet.")
