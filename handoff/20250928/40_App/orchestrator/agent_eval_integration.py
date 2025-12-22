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
        task_type: Type of workflow (default, review, internal_review, review_follow_up)
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
        pr_created: Whether a PR was created (legacy, kept for backward compatibility)
        pr_touched: Whether workflow touched a PR (has pr_url)
        pr_opened: Whether workflow opened a NEW PR
        code_changed: Whether workflow made code changes (executor/fixer wrote code)
        ci_checked: Whether CI state was observed (not unknown/pending)
        ci_passed: Whether CI checks passed
        code_quality_score: Code quality score from reviewer (0-100)
        node_latencies: Per-node latency breakdown
        metadata: Additional context

    Issue #2832: Enhanced metrics for accurate regression detection
    - Added task_type to distinguish workflow types
    - Added pr_touched, pr_opened, code_changed, ci_checked for semantic clarity
    - ci_pass_rate should only be calculated on code_changed=True workflows
    """
    trace_id: str
    goal: str
    task_type: str = "default"
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
    pr_touched: bool = False
    pr_opened: bool = False
    code_changed: bool = False
    ci_checked: bool = False
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

    def start_workflow_metrics(
        self,
        trace_id: str,
        goal: str,
        task_type: str = "default"
    ) -> Optional[EvalMetrics]:
        """
        Start collecting metrics for a workflow

        Args:
            trace_id: Unique workflow identifier
            goal: Original task goal
            task_type: Type of workflow (default, review, internal_review, review_follow_up)

        Returns:
            EvalMetrics instance if enabled, None otherwise

        Issue #2832: Added task_type parameter for workflow classification
        """
        if not self.enabled:
            return None

        metrics = EvalMetrics(
            trace_id=trace_id,
            goal=goal[:500],
            task_type=task_type,
            start_time=datetime.utcnow().isoformat()
        )
        self._active_metrics[trace_id] = metrics

        logger.debug(f"[AgentEval] Started metrics collection for {trace_id}, task_type={task_type}")
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
        code_quality_score: int = 100,
        pr_touched: bool = False,
        pr_opened: bool = False,
        code_changed: bool = False,
        ci_state: str = "unknown"
    ) -> None:
        """
        Record final workflow result

        Args:
            trace_id: Workflow identifier
            status: Final status (success, error, timeout)
            pr_created: Whether a PR was created (legacy, kept for backward compatibility)
            ci_passed: Whether CI checks passed
            code_quality_score: Code quality score (0-100)
            pr_touched: Whether workflow touched a PR (has pr_url)
            pr_opened: Whether workflow opened a NEW PR
            code_changed: Whether workflow made code changes (executor/fixer wrote code)
            ci_state: CI state string (success, failure, pending, unknown)

        Issue #2832: Enhanced metrics for accurate regression detection
        - Added pr_touched, pr_opened, code_changed for semantic clarity
        - Added ci_state to derive ci_checked (not unknown/pending)
        """
        if not self.enabled or trace_id not in self._active_metrics:
            return

        metrics = self._active_metrics[trace_id]
        metrics.status = status
        metrics.pr_created = pr_created
        metrics.ci_passed = ci_passed
        metrics.code_quality_score = code_quality_score
        metrics.pr_touched = pr_touched
        metrics.pr_opened = pr_opened
        metrics.code_changed = code_changed
        metrics.ci_checked = ci_state in ("success", "failure")

        logger.debug(
            f"[AgentEval] Recorded result: status={status}, pr_touched={pr_touched}, "
            f"pr_opened={pr_opened}, code_changed={code_changed}, ci_checked={metrics.ci_checked}"
        )

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

    def detect_capability_regression(
        self,
        success_rate_threshold: float = 70.0,
        ci_pass_rate_threshold: float = 80.0,
        fixer_success_threshold: float = 50.0,
        sample_size: int = 50,
        metrics_list: Optional[List["EvalMetrics"]] = None
    ) -> Dict[str, Any]:
        """
        Detect capability regression by comparing recent metrics against thresholds.

        This is the "IQ test" for the agent - detecting catastrophic forgetting
        where the agent's performance degrades over time.

        Args:
            success_rate_threshold: Minimum acceptable success rate (0-100)
            ci_pass_rate_threshold: Minimum acceptable CI pass rate (0-100)
            fixer_success_threshold: Minimum acceptable fixer success rate (0-100)
            sample_size: Number of recent metrics to analyze
            metrics_list: Optional pre-fetched metrics list to avoid redundant calls

        Returns:
            Dictionary with regression detection results:
            - has_regression: bool indicating if regression detected
            - regressions: list of specific regressions found
            - metrics: current metric values
            - thresholds: threshold values used
            - recommendations: suggested actions
        """
        if not self.enabled:
            return {
                "has_regression": False,
                "enabled": False,
                "message": "Agent evaluation disabled"
            }

        try:
            # Use provided metrics_list or fetch if not provided (Gemini #12)
            if metrics_list is None:
                metrics_list = self.list_metrics(limit=sample_size)

            if len(metrics_list) < 10:
                return {
                    "has_regression": False,
                    "enabled": True,
                    "message": "Insufficient data for regression detection",
                    "sample_count": len(metrics_list),
                    "required_minimum": 10
                }

            total = len(metrics_list)
            success_count = sum(1 for m in metrics_list if m.status == "success")
            pr_created_count = sum(1 for m in metrics_list if m.pr_created)
            fixer_success_count = sum(1 for m in metrics_list if m.fixer_success)
            tasks_with_fixer = sum(1 for m in metrics_list if m.fixer_iterations > 0)

            code_changing_workflows = [m for m in metrics_list if m.code_changed]
            ci_passed_count = sum(1 for m in code_changing_workflows if m.ci_passed)
            ci_checked_count = sum(1 for m in code_changing_workflows if m.ci_checked)

            success_rate = (success_count / total) * 100 if total > 0 else 0
            if len(code_changing_workflows) > 0:
                ci_pass_rate = (ci_passed_count / len(code_changing_workflows)) * 100
                ci_observed_rate = (ci_checked_count / len(code_changing_workflows)) * 100
            else:
                ci_pass_rate = 100.0
                ci_observed_rate = 100.0
            fixer_success_rate = (fixer_success_count / tasks_with_fixer) * 100 if tasks_with_fixer > 0 else 100

            regressions = []
            recommendations = []

            if success_rate < success_rate_threshold:
                regressions.append({
                    "type": "success_rate",
                    "current": success_rate,
                    "threshold": success_rate_threshold,
                    "severity": "critical" if success_rate < success_rate_threshold * 0.5 else "warning"
                })
                recommendations.append(
                    "Review recent failures for common patterns. "
                    "Check if there are new task types causing issues."
                )

            if ci_pass_rate < ci_pass_rate_threshold:
                regressions.append({
                    "type": "ci_pass_rate",
                    "current": ci_pass_rate,
                    "threshold": ci_pass_rate_threshold,
                    "severity": "critical" if ci_pass_rate < ci_pass_rate_threshold * 0.5 else "warning"
                })
                recommendations.append(
                    "Review CI failures for common issues. "
                    "Check if code generation quality has degraded."
                )

            if fixer_success_rate < fixer_success_threshold:
                regressions.append({
                    "type": "fixer_success_rate",
                    "current": fixer_success_rate,
                    "threshold": fixer_success_threshold,
                    "severity": "warning"
                })
                recommendations.append(
                    "Review fixer node effectiveness. "
                    "Consider updating error-fix pairs in knowledge base."
                )

            has_regression = len(regressions) > 0
            has_critical = any(r["severity"] == "critical" for r in regressions)

            result = {
                "has_regression": has_regression,
                "has_critical_regression": has_critical,
                "enabled": True,
                "sample_count": total,
                "code_changing_count": len(code_changing_workflows),
                "regressions": regressions,
                "metrics": {
                    "success_rate": round(success_rate, 2),
                    "ci_pass_rate": round(ci_pass_rate, 2),
                    "ci_observed_rate": round(ci_observed_rate, 2),
                    "fixer_success_rate": round(fixer_success_rate, 2),
                    "pr_creation_rate": round((pr_created_count / total) * 100, 2) if total > 0 else 0
                },
                "thresholds": {
                    "success_rate": success_rate_threshold,
                    "ci_pass_rate": ci_pass_rate_threshold,
                    "fixer_success_rate": fixer_success_threshold
                },
                "recommendations": recommendations,
                "timestamp": datetime.utcnow().isoformat()
            }

            if has_regression:
                logger.warning(
                    "[AgentEval] Capability regression detected",
                    extra={
                        "operation": "detect_regression",
                        "regressions": len(regressions),
                        "regression_details": regressions,
                        "has_critical": has_critical,
                        "success_rate": success_rate,
                        "ci_pass_rate": ci_pass_rate,
                        "ci_observed_rate": ci_observed_rate,
                        "code_changing_count": len(code_changing_workflows),
                        "total_count": total,
                        "metrics": result["metrics"]
                    }
                )
            else:
                logger.info(
                    "[AgentEval] No capability regression detected",
                    extra={
                        "operation": "detect_regression",
                        "success_rate": success_rate,
                        "ci_pass_rate": ci_pass_rate,
                        "ci_observed_rate": ci_observed_rate,
                        "code_changing_count": len(code_changing_workflows),
                        "total_count": total,
                        "metrics": result["metrics"]
                    }
                )

            return result

        except Exception as e:
            # Check if this is a Redis connectivity issue - treat as "eval disabled"
            # rather than an error to avoid noisy Sentry alerts for expected conditions
            error_str = str(e).lower()
            is_redis_error = (
                "redis" in error_str or
                "connection" in error_str or
                "timeout" in error_str or
                "refused" in error_str or
                hasattr(e, '__module__') and 'redis' in getattr(e, '__module__', '')
            )

            if is_redis_error:
                logger.warning(
                    "[AgentEval] Redis unavailable, skipping regression detection: %s",
                    e,
                    extra={
                        "operation": "detect_regression",
                        "error_type": type(e).__name__,
                        "error": str(e)
                    }
                )
                return {
                    "has_regression": False,
                    "enabled": False,
                    "message": "Evaluation skipped because Redis is unavailable",
                    "error": str(e)
                }

            # For non-Redis errors, log at error level as these may indicate real bugs
            logger.error(
                "[AgentEval] Failed to detect capability regression: %s",
                e,
                extra={
                    "operation": "detect_regression",
                    "error_type": type(e).__name__,
                    "error": str(e)
                }
            )
            return {
                "has_regression": False,
                "enabled": True,
                "error": str(e)
            }

    def generate_evaluation_report(self, sample_size: int = 100) -> Dict[str, Any]:
        """
        Generate a comprehensive evaluation report.

        Args:
            sample_size: Number of recent metrics to include

        Returns:
            Dictionary with evaluation report data
        """
        if not self.enabled:
            return {
                "enabled": False,
                "message": "Agent evaluation disabled"
            }

        try:
            # Fetch metrics once and reuse to avoid redundant calls (Gemini #12)
            metrics_list = self.list_metrics(limit=sample_size)
            regression = self.detect_capability_regression(
                sample_size=sample_size,
                metrics_list=metrics_list
            )
            # Note: get_metrics_summary() still calls list_metrics() internally,
            # but it uses limit=100 which may differ from sample_size.
            # For now, we keep it separate to maintain backward compatibility.
            summary = self.get_metrics_summary()

            task_type_breakdown: Dict[str, Dict[str, int]] = {}
            for m in metrics_list:
                task_type = m.metadata.get("task_type", "unknown")
                if task_type not in task_type_breakdown:
                    task_type_breakdown[task_type] = {
                        "total": 0,
                        "success": 0,
                        "pr_created": 0,
                        "ci_passed": 0
                    }
                task_type_breakdown[task_type]["total"] += 1
                if m.status == "success":
                    task_type_breakdown[task_type]["success"] += 1
                if m.pr_created:
                    task_type_breakdown[task_type]["pr_created"] += 1
                if m.ci_passed:
                    task_type_breakdown[task_type]["ci_passed"] += 1

            avg_latencies: Dict[str, List[float]] = {}
            for m in metrics_list:
                for node, latency in m.node_latencies.items():
                    if node not in avg_latencies:
                        avg_latencies[node] = []
                    avg_latencies[node].append(latency)

            node_performance = {
                node: {
                    "avg_latency_ms": round(sum(latencies) / len(latencies), 2),
                    "max_latency_ms": round(max(latencies), 2),
                    "min_latency_ms": round(min(latencies), 2),
                    "sample_count": len(latencies)
                }
                for node, latencies in avg_latencies.items()
                if latencies
            }

            report = {
                "report_type": "agent_evaluation",
                "generated_at": datetime.utcnow().isoformat(),
                "sample_size": len(metrics_list),
                "summary": summary,
                "regression_analysis": regression,
                "task_type_breakdown": task_type_breakdown,
                "node_performance": node_performance,
                "health_status": "healthy" if not regression.get("has_regression") else (
                    "critical" if regression.get("has_critical_regression") else "degraded"
                )
            }

            logger.info(
                "[AgentEval] Generated evaluation report",
                extra={
                    "operation": "generate_report",
                    "sample_size": len(metrics_list),
                    "health_status": report["health_status"]
                }
            )

            return report

        except Exception as e:
            logger.error(
                "[AgentEval] Failed to generate evaluation report: %s",
                e
            )
            return {
                "enabled": True,
                "error": str(e)
            }


@dataclass
class EvaluationResult:
    """
    Result of an evaluation node execution.

    Attributes:
        has_regression: Whether capability regression was detected
        health_status: Overall health status (healthy, degraded, critical)
        success_rate: Current success rate percentage
        ci_pass_rate: Current CI pass rate percentage
        fixer_success_rate: Current fixer success rate percentage
        regressions: List of detected regressions
        recommendations: List of recommended actions
        timestamp: Evaluation timestamp
    """
    has_regression: bool
    health_status: str
    success_rate: float
    ci_pass_rate: float
    fixer_success_rate: float
    regressions: List[Dict[str, Any]] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return asdict(self)


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
