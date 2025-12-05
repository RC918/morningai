"""
Meta Agent - Autonomous Task Planning and Execution

This module implements the Meta Agent for autonomous task planning and execution,
enabling natural language goal parsing, automatic subtask decomposition, and
end-to-end task execution.

Issue: #1821 - Meta Agent 自主任務規劃與執行
Milestone: M5 - Meta Agent 優化
"""

from .agent_protocol import (
    AgentCapability,
    AgentResult,
    AgentTask,
    BaseDevAgent,
    BaseOpsAgent,
    DevAgentProtocol,
    OpsAgentProtocol,
)
from .audit_log import AuditEvent, AuditEventType, AuditLogger
from .autonomous_executor import (
    AutonomousExecutor,
    ExecutionError,
    ExecutionResult,
    ExecutionStatus,
    PolicyViolationError,
    SafetyLimitError,
)
from .execution_policy import (
    AllowedOperation,
    ExecutionPolicy,
    STRICT_POLICY,
    PERMISSIVE_POLICY,
    DRY_RUN_POLICY,
)
from .goal_parser import GoalParser, GoalPriority, GoalType, ParsedGoal
from .state_persistence import (
    ExecutionCheckpoint,
    ExecutionStateManager,
    create_checkpoint_from_execution,
)
from .task_planner import SubTask, SubTaskStatus, SubTaskType, TaskPlan, TaskPlanner
from .confidence_scorer import (
    ConfidenceLevel,
    ConfidenceScore,
    ConfidenceScorer,
    Question,
    QuestionCategory,
    ScoredPlan,
)
from .vm_provisioner import (
    TaskVM,
    VMConfig,
    VMProvider,
    VMProvisioner,
    VMStatus,
    vm_provisioner,
)

__all__ = [
    # Goal Parser
    "GoalParser",
    "GoalType",
    "GoalPriority",
    "ParsedGoal",
    # Task Planner
    "TaskPlanner",
    "TaskPlan",
    "SubTask",
    "SubTaskType",
    "SubTaskStatus",
    # Autonomous Executor
    "AutonomousExecutor",
    "ExecutionResult",
    "ExecutionStatus",
    "ExecutionError",
    "SafetyLimitError",
    "PolicyViolationError",
    # Execution Policy
    "ExecutionPolicy",
    "AllowedOperation",
    "STRICT_POLICY",
    "PERMISSIVE_POLICY",
    "DRY_RUN_POLICY",
    # Audit Logging
    "AuditLogger",
    "AuditEvent",
    "AuditEventType",
    # Agent Protocols
    "DevAgentProtocol",
    "OpsAgentProtocol",
    "BaseDevAgent",
    "BaseOpsAgent",
    "AgentTask",
    "AgentResult",
    "AgentCapability",
    # State Persistence
    "ExecutionStateManager",
    "ExecutionCheckpoint",
    "create_checkpoint_from_execution",
    # Confidence Scorer
    "ConfidenceScorer",
    "ConfidenceScore",
    "ConfidenceLevel",
    "ScoredPlan",
    "Question",
    "QuestionCategory",
    # VM Provisioner
    "VMProvisioner",
    "VMProvider",
    "VMStatus",
    "VMConfig",
    "TaskVM",
    "vm_provisioner",
]
