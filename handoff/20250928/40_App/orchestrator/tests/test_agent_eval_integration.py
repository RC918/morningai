#!/usr/bin/env python3
"""
Unit tests for Agent Evaluation Integration Module (Phase 5 PR-3)

Tests the integration between agent_eval and LangGraph orchestrator.
"""

import json
from unittest.mock import MagicMock, patch


class TestEvalMetrics:
    """Tests for EvalMetrics dataclass"""

    def test_eval_metrics_creation(self):
        """Test creating EvalMetrics with default values"""
        from agent_eval_integration import EvalMetrics

        metrics = EvalMetrics(
            trace_id="test-trace-123",
            goal="Test goal"
        )

        assert metrics.trace_id == "test-trace-123"
        assert metrics.goal == "Test goal"
        assert metrics.status == "pending"
        assert metrics.fixer_iterations == 0
        assert metrics.fixer_success is False
        assert metrics.security_risk == "info"
        assert metrics.governance_risk == "info"
        assert metrics.pr_created is False
        assert metrics.ci_passed is False
        assert metrics.code_quality_score == 100
        assert metrics.node_latencies == {}

    def test_eval_metrics_to_dict(self):
        """Test EvalMetrics.to_dict() method"""
        from agent_eval_integration import EvalMetrics

        metrics = EvalMetrics(
            trace_id="test-trace-123",
            goal="Test goal",
            status="success",
            fixer_iterations=2,
            security_risk="medium"
        )

        result = metrics.to_dict()

        assert isinstance(result, dict)
        assert result["trace_id"] == "test-trace-123"
        assert result["goal"] == "Test goal"
        assert result["status"] == "success"
        assert result["fixer_iterations"] == 2
        assert result["security_risk"] == "medium"

    def test_eval_metrics_from_dict(self):
        """Test EvalMetrics.from_dict() method"""
        from agent_eval_integration import EvalMetrics

        data = {
            "trace_id": "test-trace-456",
            "goal": "Another goal",
            "status": "error",
            "fixer_iterations": 3,
            "governance_risk": "high"
        }

        metrics = EvalMetrics.from_dict(data)

        assert metrics.trace_id == "test-trace-456"
        assert metrics.goal == "Another goal"
        assert metrics.status == "error"
        assert metrics.fixer_iterations == 3
        assert metrics.governance_risk == "high"


class TestEvalTask:
    """Tests for EvalTask dataclass"""

    def test_eval_task_creation(self):
        """Test creating EvalTask with default values"""
        from agent_eval_integration import EvalTask

        task = EvalTask(
            id="eval-task-123",
            failure_id="failure-456",
            description="Test task description"
        )

        assert task.id == "eval-task-123"
        assert task.failure_id == "failure-456"
        assert task.description == "Test task description"
        assert task.task_type == "unknown"
        assert task.difficulty == "medium"
        assert task.expected_outcome == {}
        assert task.input == {}

    def test_eval_task_to_dict(self):
        """Test EvalTask.to_dict() method"""
        from agent_eval_integration import EvalTask

        task = EvalTask(
            id="eval-task-123",
            failure_id="failure-456",
            description="Test task",
            difficulty="hard"
        )

        result = task.to_dict()

        assert isinstance(result, dict)
        assert result["id"] == "eval-task-123"
        assert result["failure_id"] == "failure-456"
        assert result["difficulty"] == "hard"


class TestAgentEvalIntegration:
    """Tests for AgentEvalIntegration class"""

    def test_init_disabled_without_redis(self):
        """Test initialization without Redis client"""
        from agent_eval_integration import AgentEvalIntegration

        integration = AgentEvalIntegration(redis_client=None, enabled=True)

        assert integration.enabled is False

    def test_init_enabled_with_redis(self):
        """Test initialization with Redis client"""
        from agent_eval_integration import AgentEvalIntegration

        mock_redis = MagicMock()
        integration = AgentEvalIntegration(redis_client=mock_redis, enabled=True)

        assert integration.enabled is True
        assert integration.redis == mock_redis

    def test_start_workflow_metrics_disabled(self):
        """Test start_workflow_metrics when disabled"""
        from agent_eval_integration import AgentEvalIntegration

        integration = AgentEvalIntegration(redis_client=None, enabled=False)
        result = integration.start_workflow_metrics("trace-123", "Test goal")

        assert result is None

    def test_start_workflow_metrics_enabled(self):
        """Test start_workflow_metrics when enabled"""
        from agent_eval_integration import AgentEvalIntegration

        mock_redis = MagicMock()
        integration = AgentEvalIntegration(redis_client=mock_redis, enabled=True)

        result = integration.start_workflow_metrics("trace-123", "Test goal")

        assert result is not None
        assert result.trace_id == "trace-123"
        assert result.goal == "Test goal"
        assert "trace-123" in integration._active_metrics

    def test_record_node_latency(self):
        """Test recording node latency"""
        from agent_eval_integration import AgentEvalIntegration

        mock_redis = MagicMock()
        integration = AgentEvalIntegration(redis_client=mock_redis, enabled=True)
        integration.start_workflow_metrics("trace-123", "Test goal")

        integration.record_node_latency("trace-123", "planner", 150.5)

        metrics = integration._active_metrics["trace-123"]
        assert metrics.node_latencies["planner"] == 150.5

    def test_record_fixer_iteration(self):
        """Test recording fixer iteration"""
        from agent_eval_integration import AgentEvalIntegration

        mock_redis = MagicMock()
        integration = AgentEvalIntegration(redis_client=mock_redis, enabled=True)
        integration.start_workflow_metrics("trace-123", "Test goal")

        integration.record_fixer_iteration("trace-123", 1, False)
        metrics = integration._active_metrics["trace-123"]
        assert metrics.fixer_iterations == 1
        assert metrics.fixer_success is False

        integration.record_fixer_iteration("trace-123", 2, True)
        metrics = integration._active_metrics["trace-123"]
        assert metrics.fixer_iterations == 2
        assert metrics.fixer_success is True

    def test_record_security_advisory(self):
        """Test recording security advisory"""
        from agent_eval_integration import AgentEvalIntegration

        mock_redis = MagicMock()
        integration = AgentEvalIntegration(redis_client=mock_redis, enabled=True)
        integration.start_workflow_metrics("trace-123", "Test goal")

        integration.record_security_advisory("trace-123", "high", 3)

        metrics = integration._active_metrics["trace-123"]
        assert metrics.security_risk == "high"
        assert metrics.security_findings_count == 3

    def test_record_governance_advisory(self):
        """Test recording governance advisory"""
        from agent_eval_integration import AgentEvalIntegration

        mock_redis = MagicMock()
        integration = AgentEvalIntegration(redis_client=mock_redis, enabled=True)
        integration.start_workflow_metrics("trace-123", "Test goal")

        integration.record_governance_advisory("trace-123", "medium", 2)

        metrics = integration._active_metrics["trace-123"]
        assert metrics.governance_risk == "medium"
        assert metrics.governance_findings_count == 2

    def test_record_workflow_result(self):
        """Test recording workflow result"""
        from agent_eval_integration import AgentEvalIntegration

        mock_redis = MagicMock()
        integration = AgentEvalIntegration(redis_client=mock_redis, enabled=True)
        integration.start_workflow_metrics("trace-123", "Test goal")

        integration.record_workflow_result(
            "trace-123",
            status="success",
            pr_created=True,
            ci_passed=True,
            code_quality_score=95
        )

        metrics = integration._active_metrics["trace-123"]
        assert metrics.status == "success"
        assert metrics.pr_created is True
        assert metrics.ci_passed is True
        assert metrics.code_quality_score == 95

    def test_complete_workflow_metrics(self):
        """Test completing workflow metrics"""
        from agent_eval_integration import AgentEvalIntegration

        mock_redis = MagicMock()
        mock_pipeline = MagicMock()
        mock_redis.pipeline.return_value.__enter__ = MagicMock(return_value=mock_pipeline)
        mock_redis.pipeline.return_value.__exit__ = MagicMock(return_value=False)

        integration = AgentEvalIntegration(redis_client=mock_redis, enabled=True)
        integration.start_workflow_metrics("trace-123", "Test goal")

        result = integration.complete_workflow_metrics("trace-123")

        assert result is not None
        assert result.end_time is not None
        assert result.duration_ms > 0
        assert "trace-123" not in integration._active_metrics

    def test_generate_eval_task_from_failure(self):
        """Test generating eval task from failure record"""
        from agent_eval_integration import AgentEvalIntegration

        mock_redis = MagicMock()
        mock_pipeline = MagicMock()
        mock_redis.pipeline.return_value.__enter__ = MagicMock(return_value=mock_pipeline)
        mock_redis.pipeline.return_value.__exit__ = MagicMock(return_value=False)

        integration = AgentEvalIntegration(redis_client=mock_redis, enabled=True)

        failure_record = {
            "id": "failure-123",
            "goal": "Fix the bug in auth module",
            "task_type": "bug_fix",
            "error_type": "timeout",
            "fixer_retries": 1,
            "metadata": {"repo": "RC918/morningai"}
        }

        task = integration.generate_eval_task_from_failure(failure_record)

        assert task is not None
        assert task.failure_id == "failure-123"
        assert task.description == "Fix the bug in auth module"
        assert task.task_type == "bug_fix"
        assert task.difficulty == "medium"

    def test_generate_eval_task_difficulty_hard(self):
        """Test generating eval task with hard difficulty"""
        from agent_eval_integration import AgentEvalIntegration

        mock_redis = MagicMock()
        mock_pipeline = MagicMock()
        mock_redis.pipeline.return_value.__enter__ = MagicMock(return_value=mock_pipeline)
        mock_redis.pipeline.return_value.__exit__ = MagicMock(return_value=False)

        integration = AgentEvalIntegration(redis_client=mock_redis, enabled=True)

        failure_record = {
            "id": "failure-456",
            "goal": "Complex refactoring task",
            "task_type": "refactor",
            "error_type": "workflow_exception",
            "fixer_retries": 3,
            "metadata": {}
        }

        task = integration.generate_eval_task_from_failure(failure_record)

        assert task is not None
        assert task.difficulty == "hard"

    def test_generate_eval_task_missing_id_returns_none(self):
        """Test that generating eval task without id returns None"""
        from agent_eval_integration import AgentEvalIntegration

        mock_redis = MagicMock()
        integration = AgentEvalIntegration(redis_client=mock_redis, enabled=True)

        failure_record = {
            "goal": "Fix the bug",
            "task_type": "bug_fix",
            "error_type": "timeout",
            "fixer_retries": 1,
            "metadata": {}
        }

        task = integration.generate_eval_task_from_failure(failure_record)

        assert task is None

    def test_export_eval_tasks_jsonl(self):
        """Test exporting eval tasks in JSONL format"""
        from agent_eval_integration import AgentEvalIntegration, EvalTask

        mock_redis = MagicMock()
        integration = AgentEvalIntegration(redis_client=mock_redis, enabled=True)

        with patch.object(integration, 'list_eval_tasks') as mock_list:
            mock_list.return_value = [
                EvalTask(
                    id="task-1",
                    failure_id="fail-1",
                    description="Task 1",
                    task_type="bug_fix",
                    difficulty="easy"
                ),
                EvalTask(
                    id="task-2",
                    failure_id="fail-2",
                    description="Task 2",
                    task_type="feature",
                    difficulty="hard"
                )
            ]

            result = integration.export_eval_tasks_jsonl(limit=10)

            lines = result.strip().split("\n")
            assert len(lines) == 2

            task1 = json.loads(lines[0])
            assert task1["id"] == "task-1"
            assert task1["type"] == "bug_fix"
            assert task1["estimated_time_minutes"] == 10

            task2 = json.loads(lines[1])
            assert task2["id"] == "task-2"
            assert task2["type"] == "feature"
            assert task2["estimated_time_minutes"] == 30


class TestGetAgentEvalIntegration:
    """Tests for get_agent_eval_integration function"""

    def test_get_agent_eval_integration_singleton(self):
        """Test that get_agent_eval_integration returns singleton"""
        from agent_eval_integration import get_agent_eval_integration
        import agent_eval_integration

        agent_eval_integration._agent_eval = None

        mock_redis = MagicMock()
        integration1 = get_agent_eval_integration(redis_client=mock_redis, enabled=True)
        integration2 = get_agent_eval_integration()

        assert integration1 is integration2

        agent_eval_integration._agent_eval = None


class TestInitAgentEvalFromEnv:
    """Tests for init_agent_eval_from_env function"""

    def test_init_without_redis_url(self):
        """Test initialization without REDIS_URL"""
        from agent_eval_integration import init_agent_eval_from_env
        import agent_eval_integration

        agent_eval_integration._agent_eval = None

        with patch.dict('os.environ', {}, clear=True):
            with patch.dict('os.environ', {'REDIS_URL': ''}):
                integration = init_agent_eval_from_env()
                assert integration.enabled is False

        agent_eval_integration._agent_eval = None

    def test_init_with_redis_url(self):
        """Test initialization with REDIS_URL"""
        from agent_eval_integration import init_agent_eval_from_env
        import agent_eval_integration

        agent_eval_integration._agent_eval = None

        with patch.dict('os.environ', {'REDIS_URL': 'redis://localhost:6379/0'}):
            with patch('redis.from_url') as mock_from_url:
                mock_client = MagicMock()
                mock_from_url.return_value = mock_client

                integration = init_agent_eval_from_env()
                assert integration.enabled is True

        agent_eval_integration._agent_eval = None


class TestCapabilityRegressionDetection:
    """Tests for capability regression detection (Phase 2 PR-1813)"""

    def test_detect_regression_disabled(self):
        """Test regression detection when disabled"""
        from agent_eval_integration import AgentEvalIntegration

        integration = AgentEvalIntegration(redis_client=None, enabled=False)
        result = integration.detect_capability_regression()

        assert result["has_regression"] is False
        assert result["enabled"] is False

    def test_detect_regression_insufficient_data(self):
        """Test regression detection with insufficient data"""
        from agent_eval_integration import AgentEvalIntegration

        mock_redis = MagicMock()
        integration = AgentEvalIntegration(redis_client=mock_redis, enabled=True)

        with patch.object(integration, 'list_metrics') as mock_list:
            mock_list.return_value = []

            result = integration.detect_capability_regression()

            assert result["has_regression"] is False
            assert result["enabled"] is True
            assert "Insufficient data" in result.get("message", "")

    def test_detect_regression_no_regression(self):
        """Test regression detection with healthy metrics"""
        from agent_eval_integration import AgentEvalIntegration, EvalMetrics

        mock_redis = MagicMock()
        integration = AgentEvalIntegration(redis_client=mock_redis, enabled=True)

        healthy_metrics = [
            EvalMetrics(
                trace_id=f"trace-{i}",
                goal="Test goal",
                status="success",
                pr_created=True,
                ci_passed=True,
                fixer_iterations=1 if i % 3 == 0 else 0,
                fixer_success=True if i % 3 == 0 else False
            )
            for i in range(20)
        ]

        with patch.object(integration, 'list_metrics') as mock_list:
            mock_list.return_value = healthy_metrics

            result = integration.detect_capability_regression(
                success_rate_threshold=70.0,
                ci_pass_rate_threshold=80.0,
                fixer_success_threshold=50.0
            )

            assert result["has_regression"] is False
            assert result["enabled"] is True
            assert result["metrics"]["success_rate"] == 100.0
            assert result["metrics"]["ci_pass_rate"] == 100.0

    def test_detect_regression_with_regression(self):
        """Test regression detection with degraded metrics"""
        from agent_eval_integration import AgentEvalIntegration, EvalMetrics

        mock_redis = MagicMock()
        integration = AgentEvalIntegration(redis_client=mock_redis, enabled=True)

        degraded_metrics = [
            EvalMetrics(
                trace_id=f"trace-{i}",
                goal="Test goal",
                status="success" if i < 5 else "error",
                pr_created=i < 10,
                ci_passed=i < 3,
                fixer_iterations=1,
                fixer_success=i < 2
            )
            for i in range(20)
        ]

        with patch.object(integration, 'list_metrics') as mock_list:
            mock_list.return_value = degraded_metrics

            result = integration.detect_capability_regression(
                success_rate_threshold=70.0,
                ci_pass_rate_threshold=80.0,
                fixer_success_threshold=50.0
            )

            assert result["has_regression"] is True
            assert result["enabled"] is True
            assert len(result["regressions"]) > 0
            assert len(result["recommendations"]) > 0

    def test_detect_regression_critical_severity(self):
        """Test regression detection with critical severity"""
        from agent_eval_integration import AgentEvalIntegration, EvalMetrics

        mock_redis = MagicMock()
        integration = AgentEvalIntegration(redis_client=mock_redis, enabled=True)

        critical_metrics = [
            EvalMetrics(
                trace_id=f"trace-{i}",
                goal="Test goal",
                status="error",
                pr_created=False,
                ci_passed=False,
                fixer_iterations=0,
                fixer_success=False,
                code_changed=True,
                ci_checked=True
            )
            for i in range(20)
        ]

        with patch.object(integration, 'list_metrics') as mock_list:
            mock_list.return_value = critical_metrics

            result = integration.detect_capability_regression(
                success_rate_threshold=70.0,
                ci_pass_rate_threshold=80.0
            )

            assert result["has_regression"] is True
            assert result["has_critical_regression"] is True
            assert any(r["severity"] == "critical" for r in result["regressions"])
            assert result["metrics"]["ci_pass_rate"] == 0.0
            assert result["metrics"]["ci_observed_rate"] == 100.0
            assert result["code_changing_count"] == 20

    def test_detect_regression_workflow_combination(self):
        """
        Test regression detection with mixed workflow types (Issue #2832)

        Verifies that review-only workflows (code_changed=False) don't affect
        ci_pass_rate calculation, while code-changing workflows are correctly counted.
        """
        from agent_eval_integration import AgentEvalIntegration, EvalMetrics

        mock_redis = MagicMock()
        integration = AgentEvalIntegration(redis_client=mock_redis, enabled=True)

        mixed_metrics = [
            EvalMetrics(
                trace_id="trace-default-1",
                goal="Default workflow 1",
                task_type="default",
                status="success",
                pr_created=True,
                ci_passed=True,
                code_changed=True,
                ci_checked=True
            ),
            EvalMetrics(
                trace_id="trace-default-2",
                goal="Default workflow 2",
                task_type="default",
                status="success",
                pr_created=True,
                ci_passed=True,
                code_changed=True,
                ci_checked=True
            ),
            EvalMetrics(
                trace_id="trace-review-1",
                goal="Internal review 1",
                task_type="internal_review",
                status="success",
                pr_created=True,
                ci_passed=False,
                code_changed=False,
                ci_checked=False
            ),
            EvalMetrics(
                trace_id="trace-review-2",
                goal="Internal review 2",
                task_type="internal_review",
                status="success",
                pr_created=True,
                ci_passed=False,
                code_changed=False,
                ci_checked=False
            ),
        ] * 3

        with patch.object(integration, 'list_metrics') as mock_list:
            mock_list.return_value = mixed_metrics

            result = integration.detect_capability_regression(
                success_rate_threshold=70.0,
                ci_pass_rate_threshold=80.0
            )

            assert result["has_regression"] is False
            assert result["code_changing_count"] == 6
            assert result["metrics"]["ci_pass_rate"] == 100.0
            assert result["metrics"]["ci_observed_rate"] == 100.0

    def test_detect_regression_empty_code_changing_workflows(self):
        """
        Test regression detection when all workflows are review-only (Issue #2832)

        When code_changing_workflows is empty, ci_pass_rate should default to 100.0
        to avoid false positive regression warnings.
        """
        from agent_eval_integration import AgentEvalIntegration, EvalMetrics

        mock_redis = MagicMock()
        integration = AgentEvalIntegration(redis_client=mock_redis, enabled=True)

        review_only_metrics = [
            EvalMetrics(
                trace_id=f"trace-review-{i}",
                goal=f"Internal review {i}",
                task_type="internal_review",
                status="success",
                pr_created=True,
                ci_passed=False,
                code_changed=False,
                ci_checked=False
            )
            for i in range(15)
        ]

        with patch.object(integration, 'list_metrics') as mock_list:
            mock_list.return_value = review_only_metrics

            result = integration.detect_capability_regression(
                success_rate_threshold=70.0,
                ci_pass_rate_threshold=80.0
            )

            assert result["has_regression"] is False
            assert result["code_changing_count"] == 0
            assert result["metrics"]["ci_pass_rate"] == 100.0
            assert result["metrics"]["ci_observed_rate"] == 100.0
            assert result["metrics"]["success_rate"] == 100.0


class TestEvaluationReport:
    """Tests for evaluation report generation (Phase 2 PR-1813)"""

    def test_generate_report_disabled(self):
        """Test report generation when disabled"""
        from agent_eval_integration import AgentEvalIntegration

        integration = AgentEvalIntegration(redis_client=None, enabled=False)
        result = integration.generate_evaluation_report()

        assert result["enabled"] is False

    def test_generate_report_success(self):
        """Test successful report generation"""
        from agent_eval_integration import AgentEvalIntegration, EvalMetrics

        mock_redis = MagicMock()
        integration = AgentEvalIntegration(redis_client=mock_redis, enabled=True)

        test_metrics = [
            EvalMetrics(
                trace_id=f"trace-{i}",
                goal="Test goal",
                status="success",
                pr_created=True,
                ci_passed=True,
                node_latencies={"planner": 100.0, "executor": 200.0},
                metadata={"task_type": "bug_fix"}
            )
            for i in range(15)
        ]

        with patch.object(integration, 'list_metrics') as mock_list:
            mock_list.return_value = test_metrics
            with patch.object(integration, 'get_metrics_summary') as mock_summary:
                mock_summary.return_value = {"total": 15, "success": 15}
                with patch.object(integration, 'detect_capability_regression') as mock_detect:
                    mock_detect.return_value = {
                        "has_regression": False,
                        "has_critical_regression": False
                    }

                    result = integration.generate_evaluation_report(sample_size=15)

                    assert result["report_type"] == "agent_evaluation"
                    assert result["sample_size"] == 15
                    assert result["health_status"] == "healthy"
                    assert "task_type_breakdown" in result
                    assert "node_performance" in result

    def test_generate_report_degraded_status(self):
        """Test report generation with degraded health status"""
        from agent_eval_integration import AgentEvalIntegration, EvalMetrics

        mock_redis = MagicMock()
        integration = AgentEvalIntegration(redis_client=mock_redis, enabled=True)

        test_metrics = [
            EvalMetrics(
                trace_id=f"trace-{i}",
                goal="Test goal",
                status="error" if i > 10 else "success",
                pr_created=i < 10,
                ci_passed=i < 5,
                node_latencies={"planner": 100.0},
                metadata={"task_type": "feature"}
            )
            for i in range(15)
        ]

        with patch.object(integration, 'list_metrics') as mock_list:
            mock_list.return_value = test_metrics
            with patch.object(integration, 'get_metrics_summary') as mock_summary:
                mock_summary.return_value = {"total": 15, "success": 10}
                with patch.object(integration, 'detect_capability_regression') as mock_detect:
                    mock_detect.return_value = {
                        "has_regression": True,
                        "has_critical_regression": False
                    }

                    result = integration.generate_evaluation_report(sample_size=15)

                    assert result["health_status"] == "degraded"


class TestEvaluationResult:
    """Tests for EvaluationResult dataclass (Phase 2 PR-1813)"""

    def test_evaluation_result_creation(self):
        """Test creating EvaluationResult with default values"""
        from agent_eval_integration import EvaluationResult

        result = EvaluationResult(
            has_regression=False,
            health_status="healthy",
            success_rate=95.0,
            ci_pass_rate=90.0,
            fixer_success_rate=80.0
        )

        assert result.has_regression is False
        assert result.health_status == "healthy"
        assert result.success_rate == 95.0
        assert result.ci_pass_rate == 90.0
        assert result.fixer_success_rate == 80.0
        assert result.regressions == []
        assert result.recommendations == []

    def test_evaluation_result_to_dict(self):
        """Test EvaluationResult.to_dict() method"""
        from agent_eval_integration import EvaluationResult

        result = EvaluationResult(
            has_regression=True,
            health_status="degraded",
            success_rate=60.0,
            ci_pass_rate=70.0,
            fixer_success_rate=40.0,
            regressions=[{"type": "success_rate", "severity": "warning"}],
            recommendations=["Review recent failures"]
        )

        result_dict = result.to_dict()

        assert isinstance(result_dict, dict)
        assert result_dict["has_regression"] is True
        assert result_dict["health_status"] == "degraded"
        assert result_dict["success_rate"] == 60.0
        assert len(result_dict["regressions"]) == 1
        assert len(result_dict["recommendations"]) == 1
