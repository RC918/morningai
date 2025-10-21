"""
MorningAI Orchestrator
Multi-Agent Task Orchestration and Event Bus
"""

__version__ = "1.0.0"

from orchestrator.schemas.task_schema import UnifiedTask, TaskType, TaskPriority, TaskSource, TaskStatus, create_task
from orchestrator.schemas.event_schema import AgentEvent, EventType, EventPriority, create_task_event, create_deploy_event, create_alert_event
from orchestrator.task_queue.redis_queue import RedisQueue, create_redis_queue
from orchestrator.api.router import OrchestratorRouter
from orchestrator.api.hitl_gate import HITLGate, ApprovalStatus

__all__ = [
    "UnifiedTask",
    "TaskType",
    "TaskPriority",
    "TaskSource",
    "TaskStatus",
    "create_task",
    "AgentEvent",
    "EventType",
    "EventPriority",
    "create_task_event",
    "create_deploy_event",
    "create_alert_event",
    "RedisQueue",
    "create_redis_queue",
    "OrchestratorRouter",
    "HITLGate",
    "ApprovalStatus",
]
