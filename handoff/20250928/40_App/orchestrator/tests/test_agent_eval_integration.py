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
