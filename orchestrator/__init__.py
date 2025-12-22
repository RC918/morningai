"""
MorningAI Orchestrator
Multi-Agent Task Orchestration and Event Bus

This package uses pkgutil.extend_path to support namespace-style package merging.
When both repo-root/orchestrator and 40_App/orchestrator exist on sys.path,
this allows submodules like orchestrator.governance and orchestrator.webhooks
(which only exist in 40_App/orchestrator) to be importable even if this
repo-root orchestrator package is imported first.
"""
from pkgutil import extend_path
__path__ = extend_path(__path__, __name__)

__version__ = "1.0.0"

# Lazy imports to avoid import errors when submodules don't exist in this location
# The actual implementations may be in 40_App/orchestrator via extend_path
try:
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
except ImportError:
    # Submodules not available in this location, they may be in 40_App/orchestrator
    __all__ = []
