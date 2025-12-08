#!/usr/bin/env python3
"""
Tests for OrchestratorMetrics module

Phase 3 PR-2: Comprehensive metrics for multi-agent orchestrator flow
"""

import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime, timedelta

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from orchestrator_metrics import (
    OrchestratorMetrics,
    get_orchestrator_metrics,
    create_orchestrator_metrics,
    ORCHESTRATOR_NODES,
    DECISION_OUTCOMES,
    SEVERITY_LEVELS,
    LATENCY_BUCKETS_MS
)


class TestOrchestratorMetricsInit:
    """Tests for OrchestratorMetrics initialization"""

    def test_init_with_redis_client(self):
        """Test initialization with Redis client"""
        mock_redis = MagicMock()
        metrics = OrchestratorMetrics(redis_client=mock_redis, enabled=True)

        assert metrics.redis == mock_redis
        assert metrics.enabled is True
        assert metrics.ttl_seconds == 7200
        assert metrics.key_prefix == "metrics:orchestrator"

    def test_init_without_redis_client(self):
        """Test initialization without Redis client (disabled)"""
        metrics = OrchestratorMetrics(redis_client=None, enabled=True)

        assert metrics.redis is None
        assert metrics.enabled is False

    def test_init_with_custom_ttl(self):
        """Test initialization with custom TTL"""
        mock_redis = MagicMock()
        metrics = OrchestratorMetrics(
            redis_client=mock_redis,
            enabled=True,
            ttl_seconds=3600
        )

        assert metrics.ttl_seconds == 3600

    def test_init_with_custom_key_prefix(self):
        """Test initialization with custom key prefix"""
        mock_redis = MagicMock()
        metrics = OrchestratorMetrics(
            redis_client=mock_redis,
            enabled=True,
            key_prefix="custom:prefix"
        )

        assert metrics.key_prefix == "custom:prefix"


class TestOrchestratorMetricsNodeTracking:
    """Tests for node-level metrics tracking"""

    def test_record_node_start_enabled(self):
        """Test recording node start when enabled"""
        mock_redis = MagicMock()
        mock_pipe = MagicMock()
        mock_redis.pipeline.return_value.__enter__ = MagicMock(return_value=mock_pipe)
        mock_redis.pipeline.return_value.__exit__ = MagicMock(return_value=False)

        metrics = OrchestratorMetrics(redis_client=mock_redis, enabled=True)
        metrics.record_node_start("planner", "trace-123")

        mock_redis.pipeline.assert_called_once()

    def test_record_node_start_disabled(self):
        """Test recording node start when disabled"""
        mock_redis = MagicMock()
        metrics = OrchestratorMetrics(redis_client=mock_redis, enabled=False)
        metrics.record_node_start("planner", "trace-123")

        mock_redis.pipeline.assert_not_called()

    def test_record_node_complete_success(self):
        """Test recording node completion with success"""
        mock_redis = MagicMock()
        mock_pipe = MagicMock()
        mock_redis.pipeline.return_value.__enter__ = MagicMock(return_value=mock_pipe)
        mock_redis.pipeline.return_value.__exit__ = MagicMock(return_value=False)

        metrics = OrchestratorMetrics(redis_client=mock_redis, enabled=True)
        metrics.record_node_complete("planner", "trace-123", success=True, latency_ms=100.5)

        assert mock_redis.pipeline.call_count >= 1

    def test_record_node_complete_failure(self):
        """Test recording node completion with failure"""
        mock_redis = MagicMock()
        mock_pipe = MagicMock()
        mock_redis.pipeline.return_value.__enter__ = MagicMock(return_value=mock_pipe)
        mock_redis.pipeline.return_value.__exit__ = MagicMock(return_value=False)

        metrics = OrchestratorMetrics(redis_client=mock_redis, enabled=True)
        metrics.record_node_complete("executor", "trace-123", success=False, latency_ms=500.0)

        assert mock_redis.pipeline.call_count >= 1

    def test_track_node_execution_context_manager(self):
        """Test track_node_execution context manager"""
        mock_redis = MagicMock()
        mock_pipe = MagicMock()
        mock_redis.pipeline.return_value.__enter__ = MagicMock(return_value=mock_pipe)
        mock_redis.pipeline.return_value.__exit__ = MagicMock(return_value=False)

        metrics = OrchestratorMetrics(redis_client=mock_redis, enabled=True)

        with metrics.track_node_execution("reviewer", "trace-456"):
            pass

        assert mock_redis.pipeline.call_count >= 2


class TestOrchestratorMetricsDecisionTracking:
    """Tests for decision metrics tracking"""

    def test_record_decision_approve(self):
        """Test recording approve decision"""
        mock_redis = MagicMock()
        mock_pipe = MagicMock()
        mock_redis.pipeline.return_value.__enter__ = MagicMock(return_value=mock_pipe)
        mock_redis.pipeline.return_value.__exit__ = MagicMock(return_value=False)

        metrics = OrchestratorMetrics(redis_client=mock_redis, enabled=True)
        metrics.record_decision(
            decision="approve",
            trace_id="trace-123",
            quality_score=85,
            review_severity="none"
        )

        assert mock_redis.pipeline.call_count >= 1

    def test_record_decision_needs_fix(self):
        """Test recording needs_fix decision"""
        mock_redis = MagicMock()
        mock_pipe = MagicMock()
        mock_redis.pipeline.return_value.__enter__ = MagicMock(return_value=mock_pipe)
        mock_redis.pipeline.return_value.__exit__ = MagicMock(return_value=False)

        metrics = OrchestratorMetrics(redis_client=mock_redis, enabled=True)
        metrics.record_decision(
            decision="needs_fix",
            trace_id="trace-123",
            quality_score=40,
            review_severity="high"
        )

        assert mock_redis.pipeline.call_count >= 1

    def test_record_decision_disabled(self):
        """Test recording decision when disabled"""
        mock_redis = MagicMock()
        metrics = OrchestratorMetrics(redis_client=mock_redis, enabled=False)
        metrics.record_decision(
            decision="approve",
            trace_id="trace-123",
            quality_score=85
        )

        mock_redis.pipeline.assert_not_called()


class TestOrchestratorMetricsFixerTracking:
    """Tests for fixer metrics tracking"""

    def test_record_fixer_attempt_success(self):
        """Test recording fixer attempt with success"""
        mock_redis = MagicMock()
        mock_pipe = MagicMock()
        mock_redis.pipeline.return_value.__enter__ = MagicMock(return_value=mock_pipe)
        mock_redis.pipeline.return_value.__exit__ = MagicMock(return_value=False)

        metrics = OrchestratorMetrics(redis_client=mock_redis, enabled=True)
        metrics.record_fixer_attempt("trace-123", retry_count=1, success=True)

        assert mock_redis.pipeline.call_count >= 1

    def test_record_fixer_attempt_failure(self):
        """Test recording fixer attempt with failure"""
        mock_redis = MagicMock()
        mock_pipe = MagicMock()
        mock_redis.pipeline.return_value.__enter__ = MagicMock(return_value=mock_pipe)
        mock_redis.pipeline.return_value.__exit__ = MagicMock(return_value=False)

        metrics = OrchestratorMetrics(redis_client=mock_redis, enabled=True)
        metrics.record_fixer_attempt("trace-123", retry_count=2, success=False)

        assert mock_redis.pipeline.call_count >= 1

    def test_record_fixer_attempt_max_retries(self):
        """Test recording fixer attempt at max retries"""
        mock_redis = MagicMock()
        mock_pipe = MagicMock()
        mock_redis.pipeline.return_value.__enter__ = MagicMock(return_value=mock_pipe)
        mock_redis.pipeline.return_value.__exit__ = MagicMock(return_value=False)

        metrics = OrchestratorMetrics(redis_client=mock_redis, enabled=True)
        metrics.record_fixer_attempt("trace-123", retry_count=3, success=False)

        assert mock_redis.pipeline.call_count >= 1


class TestOrchestratorMetricsWorkflowTracking:
    """Tests for workflow-level metrics tracking"""

    def test_record_workflow_start(self):
        """Test recording workflow start"""
        mock_redis = MagicMock()
        mock_pipe = MagicMock()
        mock_redis.pipeline.return_value.__enter__ = MagicMock(return_value=mock_pipe)
        mock_redis.pipeline.return_value.__exit__ = MagicMock(return_value=False)

        metrics = OrchestratorMetrics(redis_client=mock_redis, enabled=True)
        metrics.record_workflow_start("trace-123", "Fix the bug in login page")

        assert mock_redis.pipeline.call_count >= 1

    def test_record_workflow_complete_success(self):
        """Test recording workflow completion with success"""
        mock_redis = MagicMock()
        mock_pipe = MagicMock()
        mock_redis.pipeline.return_value.__enter__ = MagicMock(return_value=mock_pipe)
        mock_redis.pipeline.return_value.__exit__ = MagicMock(return_value=False)

        metrics = OrchestratorMetrics(redis_client=mock_redis, enabled=True)
        metrics.record_workflow_complete("trace-123", status="success", latency_ms=5000.0)

        assert mock_redis.pipeline.call_count >= 1

    def test_record_workflow_complete_error(self):
        """Test recording workflow completion with error"""
        mock_redis = MagicMock()
        mock_pipe = MagicMock()
        mock_redis.pipeline.return_value.__enter__ = MagicMock(return_value=mock_pipe)
        mock_redis.pipeline.return_value.__exit__ = MagicMock(return_value=False)

        metrics = OrchestratorMetrics(redis_client=mock_redis, enabled=True)
        metrics.record_workflow_complete("trace-123", status="error", latency_ms=1000.0)

        assert mock_redis.pipeline.call_count >= 1


class TestOrchestratorMetricsQualityScoreBuckets:
    """Tests for quality score bucket calculation"""

    def test_quality_score_bucket_excellent(self):
        """Test excellent quality score bucket (90-100)"""
        metrics = OrchestratorMetrics(redis_client=None, enabled=False)
        assert metrics._get_quality_score_bucket(95) == "excellent_90_100"
        assert metrics._get_quality_score_bucket(90) == "excellent_90_100"
        assert metrics._get_quality_score_bucket(100) == "excellent_90_100"

    def test_quality_score_bucket_good(self):
        """Test good quality score bucket (70-89)"""
        metrics = OrchestratorMetrics(redis_client=None, enabled=False)
        assert metrics._get_quality_score_bucket(85) == "good_70_89"
        assert metrics._get_quality_score_bucket(70) == "good_70_89"
        assert metrics._get_quality_score_bucket(89) == "good_70_89"

    def test_quality_score_bucket_fair(self):
        """Test fair quality score bucket (50-69)"""
        metrics = OrchestratorMetrics(redis_client=None, enabled=False)
        assert metrics._get_quality_score_bucket(60) == "fair_50_69"
        assert metrics._get_quality_score_bucket(50) == "fair_50_69"
        assert metrics._get_quality_score_bucket(69) == "fair_50_69"

    def test_quality_score_bucket_poor(self):
        """Test poor quality score bucket (30-49)"""
        metrics = OrchestratorMetrics(redis_client=None, enabled=False)
        assert metrics._get_quality_score_bucket(40) == "poor_30_49"
        assert metrics._get_quality_score_bucket(30) == "poor_30_49"
        assert metrics._get_quality_score_bucket(49) == "poor_30_49"

    def test_quality_score_bucket_critical(self):
        """Test critical quality score bucket (0-29)"""
        metrics = OrchestratorMetrics(redis_client=None, enabled=False)
        assert metrics._get_quality_score_bucket(20) == "critical_0_29"
        assert metrics._get_quality_score_bucket(0) == "critical_0_29"
        assert metrics._get_quality_score_bucket(29) == "critical_0_29"


class TestOrchestratorMetricsSummary:
    """Tests for metrics summary methods"""

    def test_get_window_count_disabled(self):
        """Test get_window_count when disabled"""
        metrics = OrchestratorMetrics(redis_client=None, enabled=False)
        result = metrics.get_window_count("node.planner.success", window_minutes=15)
        assert result == 0

    def test_get_node_summary_disabled(self):
        """Test get_node_summary when disabled"""
        metrics = OrchestratorMetrics(redis_client=None, enabled=False)
        result = metrics.get_node_summary(window_minutes=15)
        assert result == {"enabled": False}

    def test_get_decision_summary_disabled(self):
        """Test get_decision_summary when disabled"""
        metrics = OrchestratorMetrics(redis_client=None, enabled=False)
        result = metrics.get_decision_summary(window_minutes=15)
        assert result == {"enabled": False}

    def test_get_fixer_summary_disabled(self):
        """Test get_fixer_summary when disabled"""
        metrics = OrchestratorMetrics(redis_client=None, enabled=False)
        result = metrics.get_fixer_summary(window_minutes=15)
        assert result == {"enabled": False}

    def test_get_workflow_summary_disabled(self):
        """Test get_workflow_summary when disabled"""
        metrics = OrchestratorMetrics(redis_client=None, enabled=False)
        result = metrics.get_workflow_summary(window_minutes=15)
        assert result == {"enabled": False}

    def test_get_comprehensive_summary_disabled(self):
        """Test get_comprehensive_summary when disabled"""
        metrics = OrchestratorMetrics(redis_client=None, enabled=False)
        result = metrics.get_comprehensive_summary(window_minutes=15)
        assert result["enabled"] is False
        assert "message" in result


class TestOrchestratorMetricsFactoryFunctions:
    """Tests for factory functions"""

    def test_create_orchestrator_metrics(self):
        """Test create_orchestrator_metrics factory function"""
        mock_redis = MagicMock()
        metrics = create_orchestrator_metrics(redis_client=mock_redis, enabled=True)

        assert isinstance(metrics, OrchestratorMetrics)
        assert metrics.redis == mock_redis
        assert metrics.enabled is True

    def test_create_orchestrator_metrics_disabled(self):
        """Test create_orchestrator_metrics with disabled flag"""
        mock_redis = MagicMock()
        metrics = create_orchestrator_metrics(redis_client=mock_redis, enabled=False)

        assert isinstance(metrics, OrchestratorMetrics)
        assert metrics.enabled is False


class TestOrchestratorMetricsConstants:
    """Tests for module constants"""

    def test_orchestrator_nodes_defined(self):
        """Test ORCHESTRATOR_NODES constant is defined correctly"""
        expected_nodes = [
            "planner",
            "executor",
            "ci_monitor",
            "reviewer",
            "decision",
            "fixer",
            "finalizer"
        ]
        assert ORCHESTRATOR_NODES == expected_nodes

    def test_decision_outcomes_defined(self):
        """Test DECISION_OUTCOMES constant is defined correctly"""
        expected_outcomes = ["approve", "needs_fix", "request_changes", "pending"]
        assert DECISION_OUTCOMES == expected_outcomes

    def test_severity_levels_defined(self):
        """Test SEVERITY_LEVELS constant is defined correctly"""
        expected_levels = ["none", "low", "medium", "high", "critical", "unknown"]
        assert SEVERITY_LEVELS == expected_levels

    def test_latency_buckets_defined(self):
        """Test LATENCY_BUCKETS_MS constant is defined correctly"""
        assert len(LATENCY_BUCKETS_MS) > 0
        assert all(isinstance(b, int) for b in LATENCY_BUCKETS_MS)
        assert LATENCY_BUCKETS_MS == sorted(LATENCY_BUCKETS_MS)


class TestOrchestratorMetricsMinuteKey:
    """Tests for minute key generation"""

    def test_get_minute_key_format(self):
        """Test minute key format"""
        metrics = OrchestratorMetrics(redis_client=None, enabled=False)
        timestamp = datetime(2025, 11, 28, 12, 30, 45)
        key = metrics._get_minute_key("test.metric", timestamp)

        assert key == "metrics:orchestrator:test.metric:202511281230"

    def test_get_minute_key_custom_prefix(self):
        """Test minute key with custom prefix"""
        metrics = OrchestratorMetrics(
            redis_client=None,
            enabled=False,
            key_prefix="custom:prefix"
        )
        timestamp = datetime(2025, 11, 28, 12, 30, 45)
        key = metrics._get_minute_key("test.metric", timestamp)

        assert key == "custom:prefix:test.metric:202511281230"


class TestOrchestratorMetricsTransitionTracking:
    """Tests for graph transition tracking"""

    def test_record_transition(self):
        """Test recording graph transition"""
        mock_redis = MagicMock()
        mock_pipe = MagicMock()
        mock_redis.pipeline.return_value.__enter__ = MagicMock(return_value=mock_pipe)
        mock_redis.pipeline.return_value.__exit__ = MagicMock(return_value=False)

        metrics = OrchestratorMetrics(redis_client=mock_redis, enabled=True)
        metrics.record_transition("planner", "executor", "trace-123")

        assert mock_redis.pipeline.call_count >= 1

    def test_record_transition_disabled(self):
        """Test recording transition when disabled"""
        mock_redis = MagicMock()
        metrics = OrchestratorMetrics(redis_client=mock_redis, enabled=False)
        metrics.record_transition("planner", "executor", "trace-123")

        mock_redis.pipeline.assert_not_called()


class TestOrchestratorMetricsFailureLearning:
    """Tests for failure learning metrics (Issue #2124)"""

    def test_record_failure_observation_enabled(self):
        """Test recording failure observation when enabled"""
        mock_redis = MagicMock()
        mock_pipe = MagicMock()
        mock_redis.pipeline.return_value.__enter__ = MagicMock(return_value=mock_pipe)
        mock_redis.pipeline.return_value.__exit__ = MagicMock(return_value=False)

        metrics = OrchestratorMetrics(redis_client=mock_redis, enabled=True)
        metrics.record_failure_observation(
            trace_id="trace-123",
            error_type="ci_failure",
            saved_to_pgvector=True,
            latency_ms=150.5
        )

        assert mock_redis.pipeline.call_count >= 1

    def test_record_failure_observation_disabled(self):
        """Test recording failure observation when disabled"""
        mock_redis = MagicMock()
        metrics = OrchestratorMetrics(redis_client=mock_redis, enabled=False)
        metrics.record_failure_observation(
            trace_id="trace-123",
            error_type="ci_failure",
            saved_to_pgvector=True,
            latency_ms=150.5
        )

        mock_redis.pipeline.assert_not_called()

    def test_record_failure_observation_not_saved(self):
        """Test recording failure observation when not saved to pgvector"""
        mock_redis = MagicMock()
        mock_pipe = MagicMock()
        mock_redis.pipeline.return_value.__enter__ = MagicMock(return_value=mock_pipe)
        mock_redis.pipeline.return_value.__exit__ = MagicMock(return_value=False)

        metrics = OrchestratorMetrics(redis_client=mock_redis, enabled=True)
        metrics.record_failure_observation(
            trace_id="trace-123",
            error_type="timeout",
            saved_to_pgvector=False,
            latency_ms=50.0
        )

        assert mock_redis.pipeline.call_count >= 1

    def test_record_failure_query_enabled(self):
        """Test recording failure query when enabled"""
        mock_redis = MagicMock()
        mock_pipe = MagicMock()
        mock_redis.pipeline.return_value.__enter__ = MagicMock(return_value=mock_pipe)
        mock_redis.pipeline.return_value.__exit__ = MagicMock(return_value=False)

        metrics = OrchestratorMetrics(redis_client=mock_redis, enabled=True)
        metrics.record_failure_query(
            trace_id="trace-123",
            results_count=3,
            latency_ms=200.0,
            query_type="similar_errors"
        )

        assert mock_redis.pipeline.call_count >= 1

    def test_record_failure_query_disabled(self):
        """Test recording failure query when disabled"""
        mock_redis = MagicMock()
        metrics = OrchestratorMetrics(redis_client=mock_redis, enabled=False)
        metrics.record_failure_query(
            trace_id="trace-123",
            results_count=3,
            latency_ms=200.0
        )

        mock_redis.pipeline.assert_not_called()

    def test_record_failure_query_empty_results(self):
        """Test recording failure query with empty results"""
        mock_redis = MagicMock()
        mock_pipe = MagicMock()
        mock_redis.pipeline.return_value.__enter__ = MagicMock(return_value=mock_pipe)
        mock_redis.pipeline.return_value.__exit__ = MagicMock(return_value=False)

        metrics = OrchestratorMetrics(redis_client=mock_redis, enabled=True)
        metrics.record_failure_query(
            trace_id="trace-123",
            results_count=0,
            latency_ms=100.0
        )

        assert mock_redis.pipeline.call_count >= 1

    def test_record_failure_query_many_results(self):
        """Test recording failure query with many results"""
        mock_redis = MagicMock()
        mock_pipe = MagicMock()
        mock_redis.pipeline.return_value.__enter__ = MagicMock(return_value=mock_pipe)
        mock_redis.pipeline.return_value.__exit__ = MagicMock(return_value=False)

        metrics = OrchestratorMetrics(redis_client=mock_redis, enabled=True)
        metrics.record_failure_query(
            trace_id="trace-123",
            results_count=10,
            latency_ms=300.0
        )

        assert mock_redis.pipeline.call_count >= 1

    def test_record_learning_context_generation_enabled(self):
        """Test recording learning context generation when enabled"""
        mock_redis = MagicMock()
        mock_pipe = MagicMock()
        mock_redis.pipeline.return_value.__enter__ = MagicMock(return_value=mock_pipe)
        mock_redis.pipeline.return_value.__exit__ = MagicMock(return_value=False)

        metrics = OrchestratorMetrics(redis_client=mock_redis, enabled=True)
        metrics.record_learning_context_generation(
            trace_id="trace-123",
            has_past_failures=True,
            has_kg_patterns=True,
            latency_ms=250.0
        )

        assert mock_redis.pipeline.call_count >= 1

    def test_record_learning_context_generation_disabled(self):
        """Test recording learning context generation when disabled"""
        mock_redis = MagicMock()
        metrics = OrchestratorMetrics(redis_client=mock_redis, enabled=False)
        metrics.record_learning_context_generation(
            trace_id="trace-123",
            has_past_failures=True,
            has_kg_patterns=False,
            latency_ms=250.0
        )

        mock_redis.pipeline.assert_not_called()

    def test_record_learning_context_generation_no_context(self):
        """Test recording learning context generation with no context"""
        mock_redis = MagicMock()
        mock_pipe = MagicMock()
        mock_redis.pipeline.return_value.__enter__ = MagicMock(return_value=mock_pipe)
        mock_redis.pipeline.return_value.__exit__ = MagicMock(return_value=False)

        metrics = OrchestratorMetrics(redis_client=mock_redis, enabled=True)
        metrics.record_learning_context_generation(
            trace_id="trace-123",
            has_past_failures=False,
            has_kg_patterns=False,
            latency_ms=50.0
        )

        assert mock_redis.pipeline.call_count >= 1

    def test_record_fix_update_success(self):
        """Test recording fix update with success"""
        mock_redis = MagicMock()
        mock_pipe = MagicMock()
        mock_redis.pipeline.return_value.__enter__ = MagicMock(return_value=mock_pipe)
        mock_redis.pipeline.return_value.__exit__ = MagicMock(return_value=False)

        metrics = OrchestratorMetrics(redis_client=mock_redis, enabled=True)
        metrics.record_fix_update(
            trace_id="trace-123",
            was_successful=True,
            latency_ms=100.0
        )

        assert mock_redis.pipeline.call_count >= 1

    def test_record_fix_update_failure(self):
        """Test recording fix update with failure"""
        mock_redis = MagicMock()
        mock_pipe = MagicMock()
        mock_redis.pipeline.return_value.__enter__ = MagicMock(return_value=mock_pipe)
        mock_redis.pipeline.return_value.__exit__ = MagicMock(return_value=False)

        metrics = OrchestratorMetrics(redis_client=mock_redis, enabled=True)
        metrics.record_fix_update(
            trace_id="trace-123",
            was_successful=False,
            latency_ms=100.0
        )

        assert mock_redis.pipeline.call_count >= 1

    def test_record_fix_update_disabled(self):
        """Test recording fix update when disabled"""
        mock_redis = MagicMock()
        metrics = OrchestratorMetrics(redis_client=mock_redis, enabled=False)
        metrics.record_fix_update(
            trace_id="trace-123",
            was_successful=True,
            latency_ms=100.0
        )

        mock_redis.pipeline.assert_not_called()

    def test_track_failure_learning_operation_context_manager(self):
        """Test track_failure_learning_operation context manager"""
        mock_redis = MagicMock()
        mock_pipe = MagicMock()
        mock_redis.pipeline.return_value.__enter__ = MagicMock(return_value=mock_pipe)
        mock_redis.pipeline.return_value.__exit__ = MagicMock(return_value=False)

        metrics = OrchestratorMetrics(redis_client=mock_redis, enabled=True)

        with metrics.track_failure_learning_operation("query", "trace-456"):
            pass

        assert mock_redis.pipeline.call_count >= 1

    def test_get_failure_learning_summary_disabled(self):
        """Test get_failure_learning_summary when disabled"""
        metrics = OrchestratorMetrics(redis_client=None, enabled=False)
        result = metrics.get_failure_learning_summary(window_minutes=15)
        assert result == {"enabled": False}

    def test_get_failure_learning_summary_enabled(self):
        """Test get_failure_learning_summary when enabled"""
        mock_redis = MagicMock()
        mock_redis.get.return_value = None

        metrics = OrchestratorMetrics(redis_client=mock_redis, enabled=True)
        result = metrics.get_failure_learning_summary(window_minutes=15)

        assert "observations" in result
        assert "pgvector_saved" in result
        assert "pgvector_skipped" in result
        assert "save_rate" in result
        assert "queries" in result
        assert "context_generations" in result
        assert "fix_updates" in result
        assert "fix_success_rate" in result
        assert "context_with_past_failures" in result
        assert "context_with_kg_patterns" in result

    def test_comprehensive_summary_includes_failure_learning(self):
        """Test that comprehensive summary includes failure learning metrics"""
        mock_redis = MagicMock()
        mock_redis.get.return_value = None

        metrics = OrchestratorMetrics(redis_client=mock_redis, enabled=True)
        result = metrics.get_comprehensive_summary(window_minutes=15)

        assert "failure_learning" in result
        assert result["enabled"] is True
