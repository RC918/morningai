"""
Project Engineer Agent - Phase 2 Step A

Devin-like Meta-Agent that accepts natural language commands
and orchestrates task execution.
"""

from .agent import ProjectEngineerAgent, TaskResult
from .safe_tasks import is_safe_task, get_safe_task_metadata, SAFE_TASK_TYPES

__all__ = [
    "ProjectEngineerAgent",
    "TaskResult",
    "is_safe_task",
    "get_safe_task_metadata",
    "SAFE_TASK_TYPES",
]
