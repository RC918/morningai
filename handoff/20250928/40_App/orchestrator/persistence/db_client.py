#!/usr/bin/env python3
"""
Database client for Supabase PostgreSQL connection
Reuses pattern from pgvector_store.py
"""
import os
import logging
from supabase import create_client, Client
from typing import Optional

logger = logging.getLogger(__name__)

_supabase_client: Optional[Client] = None

def get_client() -> Client:
    """
    Get or create Supabase client using SERVICE_ROLE_KEY for RLS bypass.
    Returns cached client if available.
    """
    global _supabase_client
    
    if _supabase_client is not None:
        return _supabase_client
    
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    
    if not supabase_url or not supabase_key:
        raise ValueError(
            "Missing required environment variables: SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY"
        )
    
    _supabase_client = create_client(supabase_url, supabase_key)
    logger.info("Supabase client initialized for agent_tasks persistence")
    
    return _supabase_client

def ensure_table_exists(client: Client) -> None:
    """
    Ensure agent_tasks table exists. Handles gracefully if already exists.
    """
    try:
        client.table("agent_tasks").select("task_id").limit(1).execute()
        logger.info("agent_tasks table verified")
    except Exception as e:
        logger.warning(f"agent_tasks table check failed: {e}. Table may not exist yet.")
