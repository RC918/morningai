"""
Agent Protocol - Interface Definitions for Dev and Ops Agents

This module defines strict Protocol interfaces for dev_agent and ops_agent,
ensuring type safety and consistent behavior across agent implementations.

Issue: #1821 - Meta Agent 自主任務規劃與執行
Milestone: M5 - Meta Agent 優化
"""

from abc import abstractmethod  # noqa: F401 - kept for future use in base classes
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Protocol, runtime_checkable


class AgentCapability(Enum):
    """Capabilities that agents can have"""
    CODE_ANALYSIS = "code_analysis"
    CODE_WRITING = "code_writing"
    CODE_REVIEW = "code_review"
    TEST_WRITING = "test_writing"
    TEST_EXECUTION = "test_execution"
    DOCUMENTATION = "documentation"
    DEPLOYMENT = "deployment"
    MONITORING = "monitoring"
    INCIDENT_RESPONSE = "incident_response"
    DATABASE_OPERATIONS = "database_operations"


@dataclass
class AgentTask:
    """A task to be executed by an agent"""
    task_id: str
    action: str
    inputs: Dict[str, Any] = field(default_factory=dict)
    context: Dict[str, Any] = field(default_factory=dict)
    timeout_seconds: int = 300
    requires_approval: bool = False


@dataclass
class AgentResult:
    """Result from an agent task execution"""
    task_id: str
    success: bool
    outputs: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None
    duration_seconds: float = 0
    metadata: Dict[str, Any] = field(default_factory=dict)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "task_id": self.task_id,
            "success": self.success,
            "outputs": self.outputs,
            "error": self.error,
            "duration_seconds": self.duration_seconds,
            "metadata": self.metadata,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
        }


@runtime_checkable
class DevAgentProtocol(Protocol):
    """
    Protocol for Development Agent implementations.

    Dev agents handle code-related tasks including analysis, writing,
    testing, and review.
    """

    @property
    def capabilities(self) -> List[AgentCapability]:
        """Return list of agent capabilities"""
        ...

    @property
    def is_available(self) -> bool:
        """Check if agent is available for tasks"""
        ...

    async def analyze_code(
        self,
        task: AgentTask,
    ) -> AgentResult:
        """
        Analyze code structure and identify issues.

        Args:
            task: The analysis task with inputs containing:
                - repo: Repository path or URL
                - files: Optional list of files to analyze
                - analysis_type: Type of analysis (structure, security, performance)

        Returns:
            AgentResult with analysis findings
        """
        ...

    async def write_code(
        self,
        task: AgentTask,
    ) -> AgentResult:
        """
        Write or modify code based on requirements.

        Args:
            task: The code writing task with inputs containing:
                - description: What code to write
                - target_files: Files to create or modify
                - constraints: Any constraints or requirements

        Returns:
            AgentResult with files modified and changes made
        """
        ...

    async def write_test(
        self,
        task: AgentTask,
    ) -> AgentResult:
        """
        Write tests for existing code.

        Args:
            task: The test writing task with inputs containing:
                - target_files: Files to write tests for
                - test_type: Type of tests (unit, integration, e2e)
                - coverage_target: Target coverage percentage

        Returns:
            AgentResult with test files created
        """
        ...

    async def run_test(
        self,
        task: AgentTask,
    ) -> AgentResult:
        """
        Execute tests and return results.

        Args:
            task: The test execution task with inputs containing:
                - test_files: Optional specific test files to run
                - test_command: Optional custom test command

        Returns:
            AgentResult with test results and coverage
        """
        ...

    async def review_code(
        self,
        task: AgentTask,
    ) -> AgentResult:
        """
        Review code changes and provide feedback.

        Args:
            task: The code review task with inputs containing:
                - changes: Diff or list of changed files
                - review_criteria: What to look for

        Returns:
            AgentResult with review comments and suggestions
        """
        ...


@runtime_checkable
class OpsAgentProtocol(Protocol):
    """
    Protocol for Operations Agent implementations.

    Ops agents handle deployment, monitoring, and operational tasks.
    """

    @property
    def capabilities(self) -> List[AgentCapability]:
        """Return list of agent capabilities"""
        ...

    @property
    def is_available(self) -> bool:
        """Check if agent is available for tasks"""
        ...

    async def deploy(
        self,
        task: AgentTask,
    ) -> AgentResult:
        """
        Deploy application to target environment.

        Args:
            task: The deployment task with inputs containing:
                - environment: Target environment (staging, production)
                - version: Version or commit to deploy
                - rollback_on_failure: Whether to auto-rollback

        Returns:
            AgentResult with deployment status and URL
        """
        ...

    async def monitor(
        self,
        task: AgentTask,
    ) -> AgentResult:
        """
        Monitor application health and metrics.

        Args:
            task: The monitoring task with inputs containing:
                - metrics: List of metrics to check
                - duration: How long to monitor
                - thresholds: Alert thresholds

        Returns:
            AgentResult with monitoring data
        """
        ...

    async def rollback(
        self,
        task: AgentTask,
    ) -> AgentResult:
        """
        Rollback to a previous deployment.

        Args:
            task: The rollback task with inputs containing:
                - environment: Target environment
                - target_version: Version to rollback to

        Returns:
            AgentResult with rollback status
        """
        ...

    async def scale(
        self,
        task: AgentTask,
    ) -> AgentResult:
        """
        Scale application resources.

        Args:
            task: The scaling task with inputs containing:
                - environment: Target environment
                - replicas: Target number of replicas
                - resources: Resource limits

        Returns:
            AgentResult with scaling status
        """
        ...


class BaseDevAgent:
    """Base implementation for DevAgent with common functionality"""

    def __init__(self) -> None:
        self._capabilities = [
            AgentCapability.CODE_ANALYSIS,
            AgentCapability.CODE_WRITING,
            AgentCapability.CODE_REVIEW,
            AgentCapability.TEST_WRITING,
            AgentCapability.TEST_EXECUTION,
        ]
        self._available = True

    @property
    def capabilities(self) -> List[AgentCapability]:
        return self._capabilities

    @property
    def is_available(self) -> bool:
        return self._available

    async def analyze_code(self, task: AgentTask) -> AgentResult:
        raise NotImplementedError("Subclass must implement analyze_code")

    async def write_code(self, task: AgentTask) -> AgentResult:
        raise NotImplementedError("Subclass must implement write_code")

    async def write_test(self, task: AgentTask) -> AgentResult:
        raise NotImplementedError("Subclass must implement write_test")

    async def run_test(self, task: AgentTask) -> AgentResult:
        raise NotImplementedError("Subclass must implement run_test")

    async def review_code(self, task: AgentTask) -> AgentResult:
        raise NotImplementedError("Subclass must implement review_code")


class BaseOpsAgent:
    """Base implementation for OpsAgent with common functionality"""

    def __init__(self) -> None:
        self._capabilities = [
            AgentCapability.DEPLOYMENT,
            AgentCapability.MONITORING,
            AgentCapability.INCIDENT_RESPONSE,
        ]
        self._available = True

    @property
    def capabilities(self) -> List[AgentCapability]:
        return self._capabilities

    @property
    def is_available(self) -> bool:
        return self._available

    async def deploy(self, task: AgentTask) -> AgentResult:
        raise NotImplementedError("Subclass must implement deploy")

    async def monitor(self, task: AgentTask) -> AgentResult:
        raise NotImplementedError("Subclass must implement monitor")

    async def rollback(self, task: AgentTask) -> AgentResult:
        raise NotImplementedError("Subclass must implement rollback")

    async def scale(self, task: AgentTask) -> AgentResult:
        raise NotImplementedError("Subclass must implement scale")


def validate_dev_agent(agent: Any) -> bool:
    """Validate that an object implements DevAgentProtocol"""
    return isinstance(agent, DevAgentProtocol)


def validate_ops_agent(agent: Any) -> bool:
    """Validate that an object implements OpsAgentProtocol"""
    return isinstance(agent, OpsAgentProtocol)
