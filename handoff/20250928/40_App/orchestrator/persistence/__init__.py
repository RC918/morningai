"""
Persistence layer for agent tasks
"""
from .db_client import get_client, ensure_table_exists
from .db_writer import (
    upsert_task_queued,
    upsert_task_running,
    upsert_task_done,
    upsert_task_error
)

__all__ = [
    'get_client',
    'ensure_table_exists',
    'upsert_task_queued',
    'upsert_task_running',
    'upsert_task_done',
    'upsert_task_error'
]
