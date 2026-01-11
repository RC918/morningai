"""
Agent Task Executor - Phase F-3: Orchestrator Integration

EPIC F Phase F-3: Bridges FlowController with existing agent dispatch mechanisms.

This module provides the AgentTaskExecutor class that implements the TaskExecutor
protocol and routes tasks to the appropriate agents based on task type.

Blueprint Reference: Section 3.2 (Flow Controller v3 - Agent Dispatch)

Key Features:
- Implements TaskExecutor protocol for FlowController compatibility
- Routes tasks to appropriate agents (DevAgent, ReviewerAgent, etc.)
- Provides execution context mapping between FlowController and AgentState
- Supports dry-run mode for testing

Usage:
    from core.planner.agent_task_executor import AgentTaskExecutor

    # Create executor with state context
    executor = AgentTaskExecutor(agent_state=state)

    # Use with FlowController
    controller = FlowController(task_executor=executor)
    result = controller.execute_plan(plan)
"""

import logging
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Callable, Dict, Optional, Protocol

from .consumer import ExecutionStatus, TaskResult
from .planner_types import TaskNode, TaskType

logger = logging.getLogger(__name__)


class AgentDispatcher(Protocol):
    """
    Protocol for agent dispatch.

    Implementations should handle routing to specific agents.
    """

    def dispatch(
        self,
        task_type: TaskType,
        task: TaskNode,
        context: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Dispatch a task to the appropriate agent.

        Args:
            task_type: Type of task to dispatch
            task: The TaskNode to execute
            context: Execution context

        Returns:
            Dict with execution results
        """
        ...


@dataclass
class AgentTaskExecutorConfig:
    """
    Configuration for AgentTaskExecutor.

    Attributes:
        dry_run: If True, simulate execution without calling agents
        timeout_seconds: Maximum execution time per task
        retry_count: Number of retries on failure
        enable_metrics: Whether to record execution metrics
    """
    dry_run: bool = False
    timeout_seconds: int = 300
    retry_count: int = 0
    enable_metrics: bool = True


class DefaultAgentDispatcher:
    """
    Default agent dispatcher that routes tasks to existing agent implementations.

    This is a placeholder that will be expanded in Phase F-3b to integrate
    with actual agent implementations (DevAgent, ReviewerAgent, etc.)
    """

    def __init__(
        self,
        agent_state: Optional[Dict[str, Any]] = None,
        custom_handlers: Optional[Dict[TaskType, Callable]] = None,
    ):
        """
        Initialize the dispatcher.

        Args:
            agent_state: LangGraph AgentState for context
            custom_handlers: Optional custom handlers for specific task types
        """
        self.agent_state = agent_state or {}
        self.custom_handlers = custom_handlers or {}

    def dispatch(
        self,
        task_type: TaskType,
        task: TaskNode,
        context: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Dispatch a task to the appropriate agent.

        Currently a placeholder that logs the dispatch and returns success.
        Phase F-3b will implement actual agent routing.
        """
        # Check for custom handler first
        if task_type in self.custom_handlers:
            handler = self.custom_handlers[task_type]
            return handler(task, context)

        # Default dispatch logic (placeholder)
        logger.info(
            "[AgentDispatcher] Dispatching task to agent",
            extra={
                "task_id": task.task_id,
                "task_type": task_type.value,
                "operation": "dispatch",
            }
        )

        # Route based on task type
        # Phase F-3b will implement actual agent calls
        dispatch_map = {
            TaskType.CODE: self._dispatch_code_task,
            TaskType.REVIEW: self._dispatch_review_task,
            TaskType.TEST: self._dispatch_test_task,
            TaskType.ANALYZE: self._dispatch_analyze_task,
            TaskType.DOCUMENT: self._dispatch_document_task,
            TaskType.DEPLOY: self._dispatch_deploy_task,
            TaskType.VERIFY: self._dispatch_verify_task,
            TaskType.SETUP: self._dispatch_setup_task,
        }

        handler = dispatch_map.get(task_type, self._dispatch_default)
        return handler(task, context)

    def _dispatch_code_task(
        self, task: TaskNode, context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Dispatch CODE task to DevAgent/SeniorCoder"""
        logger.info(
            "[AgentDispatcher] CODE task - would dispatch to DevAgent",
            extra={"task_id": task.task_id}
        )
        # Phase F-3b: Call actual DevAgent/SeniorCoder
        return {"status": "completed", "agent": "DevAgent"}

    def _dispatch_review_task(
        self, task: TaskNode, context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Dispatch REVIEW task to ReviewerAgent"""
        logger.info(
            "[AgentDispatcher] REVIEW task - would dispatch to ReviewerAgent",
            extra={"task_id": task.task_id}
        )
        # Phase F-3b: Call actual ReviewerAgent
        return {"status": "completed", "agent": "ReviewerAgent"}

    def _dispatch_test_task(
        self, task: TaskNode, context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Dispatch TEST task to CI monitoring"""
        logger.info(
            "[AgentDispatcher] TEST task - would dispatch to CI monitor",
            extra={"task_id": task.task_id}
        )
        # Phase F-3b: Call actual CI monitoring
        return {"status": "completed", "agent": "CIMonitor"}

    def _dispatch_analyze_task(
        self, task: TaskNode, context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Dispatch ANALYZE task to analysis agent"""
        logger.info(
            "[AgentDispatcher] ANALYZE task - would dispatch to AnalysisAgent",
            extra={"task_id": task.task_id}
        )
        return {"status": "completed", "agent": "AnalysisAgent"}

    def _dispatch_document_task(
        self, task: TaskNode, context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Dispatch DOCUMENT task to documentation agent"""
        logger.info(
            "[AgentDispatcher] DOCUMENT task - would dispatch to DocAgent",
            extra={"task_id": task.task_id}
        )
        return {"status": "completed", "agent": "DocAgent"}

    def _dispatch_deploy_task(
        self, task: TaskNode, context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Dispatch DEPLOY task to deployment agent"""
        logger.info(
            "[AgentDispatcher] DEPLOY task - would dispatch to DeployAgent",
            extra={"task_id": task.task_id}
        )
        return {"status": "completed", "agent": "DeployAgent"}

    def _dispatch_verify_task(
        self, task: TaskNode, context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Dispatch VERIFY task to verification agent"""
        logger.info(
            "[AgentDispatcher] VERIFY task - would dispatch to VerifyAgent",
            extra={"task_id": task.task_id}
        )
        return {"status": "completed", "agent": "VerifyAgent"}

    def _dispatch_setup_task(
        self, task: TaskNode, context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Dispatch SETUP task to setup agent"""
        logger.info(
            "[AgentDispatcher] SETUP task - would dispatch to SetupAgent",
            extra={"task_id": task.task_id}
        )
        return {"status": "completed", "agent": "SetupAgent"}

    def _dispatch_default(
        self, task: TaskNode, context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Default dispatch for unknown task types"""
        logger.warning(
            f"[AgentDispatcher] Unknown task type: {task.task_type}",
            extra={"task_id": task.task_id, "task_type": task.task_type.value}
        )
        return {"status": "completed", "agent": "DefaultAgent"}


class AgentTaskExecutor:
    """
    Task executor that bridges FlowController with agent dispatch.

    Implements the TaskExecutor protocol from flow_controller.py and routes
    tasks to the appropriate agents based on task type.

    Features:
    - TaskExecutor protocol compliance for FlowController
    - Agent routing based on TaskType
    - Execution context mapping
    - Dry-run mode support
    - Metrics recording

    Usage:
        executor = AgentTaskExecutor(agent_state=state)
        controller = FlowController(task_executor=executor)
        result = controller.execute_plan(plan)
    """

    def __init__(
        self,
        agent_state: Optional[Dict[str, Any]] = None,
        dispatcher: Optional[AgentDispatcher] = None,
        config: Optional[AgentTaskExecutorConfig] = None,
    ):
        """
        Initialize the AgentTaskExecutor.

        Args:
            agent_state: LangGraph AgentState for context
            dispatcher: Custom agent dispatcher (uses DefaultAgentDispatcher if None)
            config: Executor configuration
        """
        self.agent_state = agent_state or {}
        self.config = config or AgentTaskExecutorConfig()
        self.dispatcher = dispatcher or DefaultAgentDispatcher(
            agent_state=self.agent_state
        )
        self._execution_count = 0

    def execute(self, task: TaskNode, context: Dict[str, Any]) -> TaskResult:
        """
        Execute a task by dispatching to the appropriate agent.

        This method implements the TaskExecutor protocol from flow_controller.py.

        Args:
            task: The TaskNode to execute
            context: Execution context from FlowController

        Returns:
            TaskResult with execution status and outputs
        """
        self._execution_count += 1
        started_at = datetime.now(timezone.utc)
        start_time = time.time()

        logger.info(
            "[AgentTaskExecutor] Starting task execution",
            extra={
                "task_id": task.task_id,
                "task_type": task.task_type.value,
                "execution_count": self._execution_count,
                "dry_run": self.config.dry_run,
                "operation": "execute",
            }
        )

        # Dry-run mode: simulate successful execution
        if self.config.dry_run:
            return self._create_dry_run_result(task, started_at)

        # Merge context with agent state
        merged_context = {
            **context,
            "agent_state": self.agent_state,
            "task_inputs": task.inputs,
            "task_outputs_expected": task.outputs,
        }

        try:
            # Dispatch to appropriate agent
            result = self.dispatcher.dispatch(
                task_type=task.task_type,
                task=task,
                context=merged_context,
            )

            completed_at = datetime.now(timezone.utc)
            duration_ms = (time.time() - start_time) * 1000

            logger.info(
                "[AgentTaskExecutor] Task completed",
                extra={
                    "task_id": task.task_id,
                    "status": "completed",
                    "duration_ms": duration_ms,
                    "operation": "execute",
                }
            )

            return TaskResult(
                task_id=task.task_id,
                status=ExecutionStatus.COMPLETED,
                outputs=result,
                started_at=started_at,
                completed_at=completed_at,
                actual_duration_minutes=int(duration_ms / 60000) or 1,
            )

        except Exception as e:
            completed_at = datetime.now(timezone.utc)
            duration_ms = (time.time() - start_time) * 1000

            logger.error(
                f"[AgentTaskExecutor] Task failed: {e}",
                extra={
                    "task_id": task.task_id,
                    "error": str(e),
                    "duration_ms": duration_ms,
                    "operation": "execute",
                },
                exc_info=True,
            )

            return TaskResult(
                task_id=task.task_id,
                status=ExecutionStatus.FAILED,
                outputs={},
                error_message=str(e),
                started_at=started_at,
                completed_at=completed_at,
            )

    def _create_dry_run_result(
        self, task: TaskNode, started_at: datetime
    ) -> TaskResult:
        """Create a dry-run result for testing."""
        completed_at = datetime.now(timezone.utc)

        logger.info(
            "[AgentTaskExecutor] Dry-run execution",
            extra={
                "task_id": task.task_id,
                "task_type": task.task_type.value,
                "operation": "dry_run",
            }
        )

        return TaskResult(
            task_id=task.task_id,
            status=ExecutionStatus.COMPLETED,
            outputs={
                "dry_run": True,
                "task_type": task.task_type.value,
                "description": task.description,
            },
            started_at=started_at,
            completed_at=completed_at,
            actual_duration_minutes=0,
        )

    @property
    def execution_count(self) -> int:
        """Get the number of tasks executed."""
        return self._execution_count


def create_agent_task_executor(
    agent_state: Optional[Dict[str, Any]] = None,
    dry_run: bool = False,
    custom_handlers: Optional[Dict[TaskType, Callable]] = None,
) -> AgentTaskExecutor:
    """
    Factory function to create an AgentTaskExecutor.

    Args:
        agent_state: LangGraph AgentState for context
        dry_run: If True, simulate execution without calling agents
        custom_handlers: Optional custom handlers for specific task types

    Returns:
        Configured AgentTaskExecutor instance
    """
    config = AgentTaskExecutorConfig(dry_run=dry_run)
    dispatcher = DefaultAgentDispatcher(
        agent_state=agent_state,
        custom_handlers=custom_handlers,
    )
    return AgentTaskExecutor(
        agent_state=agent_state,
        dispatcher=dispatcher,
        config=config,
    )
