#!/usr/bin/env python3
"""
Agent Evaluation Integration Module - Phase 5 PR-3

Connects agent_eval to LangGraph orchestrator for comprehensive metrics collection.

Features:
- Fixer iteration metrics (retry count, success rate)
- Latency metrics (per-node, end-to-end)
- Governance/Security flags tracking
- Support for generating evaluation tasks from failure records

This module bridges the gap between the orchestrator's runtime metrics
and the agent_eval evaluation harness.
"""

import logging
import json
from typing import Dict, List, Optional, Any
from datetime import datetime
from dataclasses import dataclass, asdict, field

logger = logging.getLogger(__name__)

EVAL_KEY_PREFIX = "orchestrator:eval"
EVAL_METRICS_KEY = f"{EVAL_KEY_PREFIX}:metrics"
EVAL_TASKS_KEY = f"{EVAL_KEY_PREFIX}:tasks"


@dataclass
class EvalMetrics:
    """
    Evaluation metrics for a single workflow execution

    Attributes:
        trace_id: Unique workflow identifier
        goal: Original task goal
        start_time: Workflow start timestamp
        end_time: Workflow end timestamp
        duration_ms: Total execution time in milliseconds
        status: Final workflow status (success, error, timeout)
        fixer_iterations: Number of fixer retry attempts
        fixer_success: Whether fixer successfully resolved issues
        security_risk: Security risk level from SecurityAgent
        security_findings_count: Number of security findings
        governance_risk: Governance risk level from GovernanceAgent
        governance_findings_count: Number of governance findings
        pr_created: Whether a PR was created
        ci_passed: Whether CI checks passed
        code_quality_score: Code quality score from reviewer (0-100)
        node_latencies: Per-node latency breakdown
        metadata: Additional context
    """
    trace_id: str
    goal: str
    start_time: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    end_time: Optional[str] = None
    duration_ms: float = 0.0
    status: str = "pending"
    fixer_iterations: int = 0
    fixer_success: bool = False
    security_risk: str = "info"
    security_findings_count: int = 0
    governance_risk: str = "info"
    governance_findings_count: int = 0
    pr_created: bool = False
    ci_passed: bool = False
    code_quality_score: int = 100
    node_latencies: Dict[str, float] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "EvalMetrics":
        """Create EvalMetrics from dictionary"""
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


@dataclass
class EvalTask:
    """
    Evaluation task generated from a failure record

    Attributes:
        id: Unique task identifier
        failure_id: Original failure record ID
        description: Task description (from original goal)
        task_type: Type of task (from failure record)
        difficulty: Estimated difficulty level
        expected_outcome: Expected outcome based on failure analysis
        input: Task input parameters
        created_at: Task creation timestamp
    """
    id: str
    failure_id: str
    description: str
    task_type: str = "unknown"
    difficulty: str = "medium"
    expected_outcome: Dict[str, Any] = field(default_factory=dict)
    input: Dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "EvalTask":
        """Create EvalTask from dictionary"""
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


class AgentEvalIntegration:
    """
    Integration layer between LangGraph orchestrator and agent_eval

    Collects metrics during workflow execution and supports
    generating evaluation tasks from failure records.
    """

    def __init__(
        self,
        redis_client: Optional[Any] = None,
        enabled: bool = True,
        key_prefix: str = EVAL_KEY_PREFIX
    ):
        """
        Initialize agent eval integration

        Args:
            redis_client: Redis client instance (optional, disabled if None)
            enabled: Whether metrics collection is enabled
            key_prefix: Prefix for all Redis keys
        """
        self.redis = redis_client
        self.enabled = enabled and redis_client is not None
        self.key_prefix = key_prefix
        self.metrics_key = f"{key_prefix}:metrics"
        self.tasks_key = f"{key_prefix}:tasks"
        self._active_metrics: Dict[str, EvalMetrics] = {}

    def start_workflow_metrics(self, trace_id: str, goal: str) -> Optional[EvalMetrics]:
        """
        Start collecting metrics for a workflow

        Args:
            trace_id: Unique workflow identifier
            goal: Original task goal

        Returns:
            EvalMetrics instance if enabled, None otherwise
        """
        if not self.enabled:
            return None

        metrics = EvalMetrics(
            trace_id=trace_id,
            goal=goal[:500],
            start_time=datetime.utcnow().isoformat()
        )
        self._active_metrics[trace_id] = metrics

        logger.debug(f"[AgentEval] Started metrics collection for {trace_id}")
        return metrics

    def record_node_latency(
        self,
        trace_id: str,
        node_name: str,
        latency_ms: float
    ) -> None:
        """
        Record latency for a specific node

        Args:
            trace_id: Workflow identifier
            node_name: Name of the node
            latency_ms: Latency in milliseconds
        """
        if not self.enabled or trace_id not in self._active_metrics:
            return

        metrics = self._active_metrics[trace_id]
        metrics.node_latencies[node_name] = latency_ms

        logger.debug(f"[AgentEval] Recorded {node_name} latency: {latency_ms:.2f}ms")

    def record_fixer_iteration(
        self,
        trace_id: str,
        iteration: int,
        success: bool
    ) -> None:
        """
        Record a fixer iteration

        Args:
            trace_id: Workflow identifier
            iteration: Current iteration number
            success: Whether this iteration was successful
        """
        if not self.enabled or trace_id not in self._active_metrics:
            return

        metrics = self._active_metrics[trace_id]
        metrics.fixer_iterations = iteration
        if success:
            metrics.fixer_success = True

        logger.debug(f"[AgentEval] Recorded fixer iteration {iteration}, success={success}")

    def record_security_advisory(
        self,
        trace_id: str,
        risk_level: str,
        findings_count: int
    ) -> None:
        """
        Record security advisory results

        Args:
            trace_id: Workflow identifier
            risk_level: Security risk level (critical, high, medium, low, info)
            findings_count: Number of security findings
        """
        if not self.enabled or trace_id not in self._active_metrics:
            return

        metrics = self._active_metrics[trace_id]
        metrics.security_risk = risk_level
        metrics.security_findings_count = findings_count

        logger.debug(f"[AgentEval] Recorded security: risk={risk_level}, findings={findings_count}")

    def record_governance_advisory(
        self,
        trace_id: str,
        risk_level: str,
        findings_count: int
    ) -> None:
        """
        Record governance advisory results

        Args:
            trace_id: Workflow identifier
            risk_level: Governance risk level (critical, high, medium, low, info)
            findings_count: Number of governance findings
        """
        if not self.enabled or trace_id not in self._active_metrics:
            return

        metrics = self._active_metrics[trace_id]
        metrics.governance_risk = risk_level
        metrics.governance_findings_count = findings_count

        logger.debug(f"[AgentEval] Recorded governance: risk={risk_level}, findings={findings_count}")

    def record_workflow_result(
        self,
        trace_id: str,
        status: str,
        pr_created: bool = False,
        ci_passed: bool = False,
        code_quality_score: int = 100
    ) -> None:
        """
        Record final workflow result

        Args:
            trace_id: Workflow identifier
            status: Final status (success, error, timeout)
            pr_created: Whether a PR was created
            ci_passed: Whether CI checks passed
            code_quality_score: Code quality score (0-100)
        """
        if not self.enabled or trace_id not in self._active_metrics:
            return

        metrics = self._active_metrics[trace_id]
        metrics.status = status
        metrics.pr_created = pr_created
        metrics.ci_passed = ci_passed
        metrics.code_quality_score = code_quality_score

        logger.debug(f"[AgentEval] Recorded result: status={status}, pr={pr_created}, ci={ci_passed}")

    def complete_workflow_metrics(self, trace_id: str) -> Optional[EvalMetrics]:
        """
        Complete metrics collection and persist to Redis

        Args:
            trace_id: Workflow identifier

        Returns:
            Completed EvalMetrics if successful, None otherwise
        """
        if not self.enabled or trace_id not in self._active_metrics:
            return None

        metrics = self._active_metrics[trace_id]
        metrics.end_time = datetime.utcnow().isoformat()

        start = datetime.fromisoformat(metrics.start_time)
        end = datetime.fromisoformat(metrics.end_time)
        metrics.duration_ms = (end - start).total_seconds() * 1000

        try:
            record_key = f"{self.metrics_key}:{trace_id}"
            record_data = json.dumps(metrics.to_dict())

            with self.redis.pipeline(transaction=True) as pipe:
                pipe.set(record_key, record_data, ex=86400 * 30)
                pipe.lpush(f"{self.metrics_key}:list", trace_id)
                pipe.ltrim(f"{self.metrics_key}:list", 0, 9999)
                pipe.execute()

            logger.info(f"[AgentEval] Completed metrics for {trace_id}", extra={
                "operation": "complete_workflow_metrics",
                "trace_id": trace_id,
                "duration_ms": metrics.duration_ms,
                "status": metrics.status,
                "fixer_iterations": metrics.fixer_iterations
            })

            del self._active_metrics[trace_id]
            return metrics

        except Exception as e:
            logger.warning(f"[AgentEval] Failed to persist metrics: {e}")
            return None

    def get_metrics(self, trace_id: str) -> Optional[EvalMetrics]:
        """
        Get metrics for a specific workflow

        Args:
            trace_id: Workflow identifier

        Returns:
            EvalMetrics if found, None otherwise
        """
        if not self.enabled:
            return None

        try:
            record_key = f"{self.metrics_key}:{trace_id}"
            record_data = self.redis.get(record_key)

            if record_data:
                data = json.loads(record_data)
                return EvalMetrics.from_dict(data)

            return None

        except Exception as e:
            logger.warning(f"[AgentEval] Failed to get metrics: {e}")
            return None

    def list_metrics(
        self,
        limit: int = 50,
        offset: int = 0
    ) -> List[EvalMetrics]:
        """
        List recent workflow metrics

        Args:
            limit: Maximum number of records to return
            offset: Number of records to skip

        Returns:
            List of EvalMetrics instances
        """
        if not self.enabled:
            return []

        try:
            trace_ids = self.redis.lrange(
                f"{self.metrics_key}:list",
                offset,
                offset + limit - 1
            )

            metrics_list = []
            if not trace_ids:
                return metrics_list

            record_keys = [
                f"{self.metrics_key}:{tid.decode('utf-8') if isinstance(tid, bytes) else tid}"
                for tid in trace_ids
            ]
            records_data = self.redis.mget(record_keys)

            for record_data in records_data:
                if record_data:
                    try:
                        data = json.loads(record_data)
                        metrics_list.append(EvalMetrics.from_dict(data))
                    except (json.JSONDecodeError, TypeError) as e:
                        logger.warning(f"[AgentEval] Failed to parse metric data: {e}")

            return metrics_list

        except Exception as e:
            logger.warning(f"[AgentEval] Failed to list metrics: {e}")
            return []

    def get_metrics_summary(self) -> Dict[str, Any]:
        """
        Get summary statistics for recent metrics

        Returns:
            Dictionary with summary statistics
        """
        if not self.enabled:
            return {"enabled": False}

        try:
            metrics_list = self.list_metrics(limit=100)

            if not metrics_list:
                return {
                    "enabled": True,
                    "total": 0,
                    "recent_count": 0
                }

            success_count = sum(1 for m in metrics_list if m.status == "success")
            error_count = sum(1 for m in metrics_list if m.status == "error")
            pr_created_count = sum(1 for m in metrics_list if m.pr_created)
            ci_passed_count = sum(1 for m in metrics_list if m.ci_passed)

            total_fixer_iterations = sum(m.fixer_iterations for m in metrics_list)
            fixer_success_count = sum(1 for m in metrics_list if m.fixer_success)

            security_risk_counts: Dict[str, int] = {}
            governance_risk_counts: Dict[str, int] = {}

            for m in metrics_list:
                security_risk_counts[m.security_risk] = security_risk_counts.get(m.security_risk, 0) + 1
                governance_risk_counts[m.governance_risk] = governance_risk_counts.get(m.governance_risk, 0) + 1

            avg_duration_ms = sum(m.duration_ms for m in metrics_list) / len(metrics_list)
            avg_code_quality = sum(m.code_quality_score for m in metrics_list) / len(metrics_list)

            return {
                "enabled": True,
                "total": self.redis.llen(f"{self.metrics_key}:list"),
                "recent_count": len(metrics_list),
                "success_rate": (success_count / len(metrics_list)) * 100 if metrics_list else 0,
                "error_rate": (error_count / len(metrics_list)) * 100 if metrics_list else 0,
                "pr_creation_rate": (pr_created_count / len(metrics_list)) * 100 if metrics_list else 0,
                "ci_pass_rate": (ci_passed_count / len(metrics_list)) * 100 if metrics_list else 0,
                "avg_duration_ms": avg_duration_ms,
                "avg_code_quality_score": avg_code_quality,
                "fixer_metrics": {
                    "total_iterations": total_fixer_iterations,
                    "avg_iterations": total_fixer_iterations / len(metrics_list) if metrics_list else 0,
                    "success_rate": (fixer_success_count / len(metrics_list)) * 100 if metrics_list else 0
                },
                "security_risk_distribution": security_risk_counts,
                "governance_risk_distribution": governance_risk_counts
            }

        except Exception as e:
            logger.warning(f"[AgentEval] Failed to get summary: {e}")
            return {"enabled": True, "error": str(e)}

    def generate_eval_task_from_failure(
        self,
        failure_record: Dict[str, Any]
    ) -> Optional[EvalTask]:
        """
        Generate an evaluation task from a failure record

        Args:
            failure_record: Failure record dictionary from FailureRecorder

        Returns:
            EvalTask if successful, None otherwise
        """
        if not self.enabled:
            return None

        try:
            import uuid

            failure_id = failure_record.get("id")
            if not failure_id:
                logger.error(
                    "[AgentEval] Failure record is missing 'id' field",
                    extra={"failure_record_keys": list(failure_record.keys())}
                )
                return None

            goal = failure_record.get("goal", "")
            task_type = failure_record.get("task_type", "unknown")
            error_type = failure_record.get("error_type", "unknown")
            fixer_retries = failure_record.get("fixer_retries", 0)

            difficulty = "easy"
            if fixer_retries >= 3:
                difficulty = "hard"
            elif fixer_retries >= 1:
                difficulty = "medium"

            if error_type in ["workflow_exception", "ci_failure"]:
                difficulty = "hard"

            expected_outcome = {
                "pr_created": True,
                "ci_passed": True,
                "correctness_criteria": [
                    "code_compiles",
                    "tests_pass",
                    "no_security_issues"
                ]
            }

            task = EvalTask(
                id=f"eval-{failure_id[:8]}-{str(uuid.uuid4())[:8]}",
                failure_id=failure_id,
                description=goal,
                task_type=task_type or "unknown",
                difficulty=difficulty,
                expected_outcome=expected_outcome,
                input={
                    "repo": failure_record.get("metadata", {}).get("repo"),
                    "affected_files": [],
                    "original_error_type": error_type,
                    "original_fixer_retries": fixer_retries
                }
            )

            record_key = f"{self.tasks_key}:{task.id}"
            record_data = json.dumps(task.to_dict())

            with self.redis.pipeline(transaction=True) as pipe:
                pipe.set(record_key, record_data, ex=86400 * 30)
                pipe.lpush(f"{self.tasks_key}:list", task.id)
                pipe.ltrim(f"{self.tasks_key}:list", 0, 999)
                pipe.execute()

            logger.info("[AgentEval] Generated eval task from failure", extra={
                "operation": "generate_eval_task",
                "task_id": task.id,
                "failure_id": failure_id,
                "difficulty": difficulty
            })

            return task

        except Exception as e:
            logger.warning(f"[AgentEval] Failed to generate eval task: {e}")
            return None

    def list_eval_tasks(
        self,
        limit: int = 50,
        offset: int = 0
    ) -> List[EvalTask]:
        """
        List generated evaluation tasks

        Args:
            limit: Maximum number of tasks to return
            offset: Number of tasks to skip

        Returns:
            List of EvalTask instances
        """
        if not self.enabled:
            return []

        try:
            task_ids = self.redis.lrange(
                f"{self.tasks_key}:list",
                offset,
                offset + limit - 1
            )

            tasks = []
            if not task_ids:
                return tasks

            record_keys = [
                f"{self.tasks_key}:{tid.decode('utf-8') if isinstance(tid, bytes) else tid}"
                for tid in task_ids
            ]
            records_data = self.redis.mget(record_keys)

            for record_data in records_data:
                if record_data:
                    try:
                        data = json.loads(record_data)
                        tasks.append(EvalTask.from_dict(data))
                    except (json.JSONDecodeError, TypeError) as e:
                        logger.warning(f"[AgentEval] Failed to parse eval task data: {e}")

            return tasks

        except Exception as e:
            logger.warning(f"[AgentEval] Failed to list eval tasks: {e}")
            return []

    def export_eval_tasks_jsonl(self, limit: int = 100) -> str:
        """
        Export evaluation tasks in JSONL format for agent_eval runner

        Args:
            limit: Maximum number of tasks to export

        Returns:
            JSONL string with evaluation tasks
        """
        tasks = self.list_eval_tasks(limit=limit)

        lines = []
        for task in tasks:
            task_dict = {
                "id": task.id,
                "type": task.task_type,
                "description": task.description,
                "difficulty": task.difficulty,
                "estimated_time_minutes": 10 if task.difficulty == "easy" else (20 if task.difficulty == "medium" else 30),
                "input": task.input,
                "expected_outcome": task.expected_outcome
            }
            lines.append(json.dumps(task_dict))

        return "\n".join(lines)


_agent_eval: Optional[AgentEvalIntegration] = None


def get_agent_eval_integration(
    redis_client: Optional[Any] = None,
    enabled: bool = True
) -> AgentEvalIntegration:
    """
    Get or create the global agent eval integration instance

    Args:
        redis_client: Redis client (uses existing if not provided)
        enabled: Whether integration is enabled

    Returns:
        AgentEvalIntegration instance
    """
    global _agent_eval

    if _agent_eval is None:
        _agent_eval = AgentEvalIntegration(
            redis_client=redis_client,
            enabled=enabled
        )

    return _agent_eval


def init_agent_eval_from_env() -> AgentEvalIntegration:
    """
    Initialize agent eval integration from environment variables

    Returns:
        AgentEvalIntegration instance configured from REDIS_URL env var
    """
    import os
    try:
        import redis
        redis_url = os.environ.get("REDIS_URL")
        if redis_url:
            redis_client = redis.from_url(redis_url)
            return get_agent_eval_integration(redis_client=redis_client, enabled=True)
        return get_agent_eval_integration(redis_client=None, enabled=False)
    except Exception as e:
        logger.warning(f"Failed to initialize agent eval integration: {e}")
        return get_agent_eval_integration(redis_client=None, enabled=False)
