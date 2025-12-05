"""
Execution Policy - Safety Limits and Constraints for Meta Agent

This module defines execution policies that control the behavior and limits
of the autonomous executor, including timeouts, task limits, and allowed operations.

Issue: #1821 - Meta Agent 自主任務規劃與執行
Milestone: M5 - Meta Agent 優化
"""

import logging
from dataclasses import dataclass, field
from datetime import timedelta
from enum import Enum
from typing import FrozenSet, Set

logger = logging.getLogger(__name__)


class AllowedOperation(Enum):
    """Operations that can be allowed or restricted"""
    READ_FILE = "read_file"
    WRITE_FILE = "write_file"
    DELETE_FILE = "delete_file"
    EXECUTE_COMMAND = "execute_command"
    NETWORK_REQUEST = "network_request"
    DATABASE_READ = "database_read"
    DATABASE_WRITE = "database_write"
    DATABASE_DELETE = "database_delete"
    DEPLOY_STAGING = "deploy_staging"
    DEPLOY_PRODUCTION = "deploy_production"
    CREATE_PR = "create_pr"
    MERGE_PR = "merge_pr"
    SEND_NOTIFICATION = "send_notification"


# Default safe operations (no approval required)
DEFAULT_SAFE_OPERATIONS: FrozenSet[AllowedOperation] = frozenset([
    AllowedOperation.READ_FILE,
    AllowedOperation.WRITE_FILE,
    AllowedOperation.EXECUTE_COMMAND,
    AllowedOperation.NETWORK_REQUEST,
    AllowedOperation.DATABASE_READ,
    AllowedOperation.CREATE_PR,
    AllowedOperation.SEND_NOTIFICATION,
])

# Operations that always require approval
ALWAYS_REQUIRE_APPROVAL: FrozenSet[AllowedOperation] = frozenset([
    AllowedOperation.DELETE_FILE,
    AllowedOperation.DATABASE_DELETE,
    AllowedOperation.DEPLOY_PRODUCTION,
    AllowedOperation.MERGE_PR,
])


@dataclass
class ExecutionPolicy:
    """
    Defines execution limits and constraints for the autonomous executor.

    This policy controls:
    - Maximum execution time
    - Maximum number of tasks
    - Allowed operations
    - Retry limits
    - Timeout settings
    """

    # Time limits
    max_execution_time: timedelta = field(default_factory=lambda: timedelta(hours=1))
    max_task_timeout: timedelta = field(default_factory=lambda: timedelta(minutes=10))
    max_blocked_wait_time: timedelta = field(default_factory=lambda: timedelta(minutes=5))

    # Task limits
    max_tasks: int = 100
    max_retries_per_task: int = 3
    max_consecutive_failures: int = 5
    max_loop_iterations: int = 1000

    # Operation whitelist
    allowed_operations: Set[AllowedOperation] = field(
        default_factory=lambda: set(DEFAULT_SAFE_OPERATIONS)
    )

    # Approval settings
    require_approval_for_deployment: bool = True
    require_approval_for_database_writes: bool = False
    require_approval_for_file_deletes: bool = True

    # Safety settings
    dry_run: bool = False
    allow_production_access: bool = False

    def is_operation_allowed(self, operation: AllowedOperation) -> bool:
        """Check if an operation is allowed by this policy"""
        return operation in self.allowed_operations

    def requires_approval(self, operation: AllowedOperation) -> bool:
        """Check if an operation requires human approval"""
        if operation in ALWAYS_REQUIRE_APPROVAL:
            return True

        if self.require_approval_for_deployment:
            if operation in (AllowedOperation.DEPLOY_STAGING, AllowedOperation.DEPLOY_PRODUCTION):
                return True

        if self.require_approval_for_database_writes:
            if operation in (AllowedOperation.DATABASE_WRITE, AllowedOperation.DATABASE_DELETE):
                return True

        if self.require_approval_for_file_deletes:
            if operation == AllowedOperation.DELETE_FILE:
                return True

        return False

    def validate(self) -> None:
        """Validate policy settings"""
        if self.max_execution_time.total_seconds() <= 0:
            raise ValueError("max_execution_time must be positive")
        if self.max_tasks <= 0:
            raise ValueError("max_tasks must be positive")
        if self.max_retries_per_task < 0:
            raise ValueError("max_retries_per_task cannot be negative")
        if self.max_loop_iterations <= 0:
            raise ValueError("max_loop_iterations must be positive")

        logger.info(
            "[ExecutionPolicy] Validated: max_time=%s, max_tasks=%d, operations=%d",
            self.max_execution_time, self.max_tasks, len(self.allowed_operations))


# Preset policies
STRICT_POLICY = ExecutionPolicy(
    max_execution_time=timedelta(minutes=30),
    max_tasks=50,
    max_retries_per_task=2,
    max_consecutive_failures=3,
    require_approval_for_deployment=True,
    require_approval_for_database_writes=True,
    require_approval_for_file_deletes=True,
    allow_production_access=False,
)

PERMISSIVE_POLICY = ExecutionPolicy(
    max_execution_time=timedelta(hours=4),
    max_tasks=200,
    max_retries_per_task=5,
    max_consecutive_failures=10,
    require_approval_for_deployment=False,
    require_approval_for_database_writes=False,
    require_approval_for_file_deletes=False,
    allow_production_access=True,
)

DRY_RUN_POLICY = ExecutionPolicy(
    max_execution_time=timedelta(minutes=15),
    max_tasks=100,
    dry_run=True,
    allow_production_access=False,
)
